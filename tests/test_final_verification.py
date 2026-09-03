import json
import os
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from app import main
from app.backup import build_backup, restore_backup
from app.store import Store
from app.trends import weekly_trends


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = Store(tmp_path / 'source.db')
    store.initialize()
    monkeypatch.setattr(main, 'store', store)
    monkeypatch.setattr(main.approvals, 'store', store)
    monkeypatch.setattr(main, 'settings', replace(main.settings, api_key='test-key', database_url=None))
    main.request_window.clear()
    with store.connection() as con:
        con.execute("INSERT INTO job_listings(source,source_id,query,title,company,description) VALUES('test','1','data','Data Engineer','Example','python sql kafka')")
        con.execute("INSERT INTO oauth_connections(provider,sender,encrypted_token) VALUES('google','dashboard-user','NEVER-EXPORT-THIS')")
    with TestClient(main.app, headers={'X-API-Key': 'test-key'}) as api:
        yield api, store


def test_http_career_workflow_and_restore(client, tmp_path):
    api, store = client
    assert api.post('/profile', json={'resume_text': 'Python SQL pipelines with measured production results'}).status_code == 200
    assert api.put('/settings', json={'display_name': 'Test Candidate', 'target_role': 'Data Engineer', 'target_location': 'India'}).status_code == 200
    application = api.post('/applications', json={'job_listing_id': 1}).json()
    app_id = application['id']
    assert api.post(f'/applications/{app_id}/notes', json={'body': 'Prepare data-quality story'}).status_code == 201
    assert api.post(f'/applications/{app_id}/follow-ups', json={'due_on': '2030-01-01'}).status_code == 201
    assert api.post('/resume-versions/from-profile?label=First').status_code == 201
    result = api.get(f'/applications/{app_id}/copilot').json()
    assert 'Test Candidate' in result['cover_letter']
    assert 'kafka' in result['interview_prep']['skill_gaps']
    assert 'Subject:' in result['recruiter_email']
    assert api.get('/profile/skill-roadmap').json()['roadmap'][0]['skill'] == 'kafka'
    for status in ('APPLIED', 'INTERVIEW', 'INTERVIEW'):
        assert api.post(f'/applications/{app_id}/status', json={'status': status}).status_code == 200
    weeks = api.get('/analytics/trends').json()['weeks']
    assert weeks[-1]['applied'] == 1 and weeks[-1]['interviews'] == 1
    assert len(weeks) == 8
    exported = api.get('/backup/export.json').json()
    assert 'NEVER-EXPORT-THIS' not in json.dumps(exported)
    restored = restore_backup(exported, tmp_path / 'restored.db')
    assert build_backup(restored)['tables'] == exported['tables']
    with restored.connection() as con:
        assert con.execute('SELECT COUNT(*) FROM oauth_connections').fetchone()[0] == 0
        assert con.execute('SELECT COUNT(*) FROM approvals').fetchone()[0] == 0
    with pytest.raises(FileExistsError):
        restore_backup(exported, tmp_path / 'restored.db')
    assert 'Data Engineer' in api.get('/applications/export.csv').text
    assert api.get('/applications/9999/copilot').status_code == 404
    assert api.get('/analytics', headers={'X-API-Key':'wrong'}).status_code == 401


def test_trends_week_boundaries_and_sender_isolation(tmp_path):
    store = Store(tmp_path / 'history.db'); store.initialize()
    with store.connection() as con:
        con.execute("INSERT INTO job_listings(source,source_id,query,title) VALUES('test','1','data','Engineer')")
        con.execute("INSERT INTO applications(sender,job_listing_id,created_at) VALUES('one',1,'2026-08-30 23:59:00')")
        for sender, date, stage in [('one','2026-08-31 00:00:00','APPLIED'), ('one','2026-09-01 12:00:00','INTERVIEW'), ('other','2026-09-01 12:00:00','INTERVIEW')]:
            con.execute("INSERT INTO audit_logs(sender,event_type,entity_type,details,created_at) VALUES(?,'application.status_changed','application',?,?)", (sender,json.dumps({'to': stage}),date))
    weeks = weekly_trends(store, 'one', datetime(2026,9,2,tzinfo=timezone.utc))['weeks']
    assert weeks[-2]['captured'] == 1 and weeks[-1]['captured'] == 0
    assert weeks[-1]['applied'] == weeks[-1]['interviews'] == 1


def test_restore_rejects_unsupported_backup_before_creating_file(tmp_path):
    destination = tmp_path / 'no.db'
    with pytest.raises(ValueError):
        restore_backup({'version':1}, destination)
    assert not destination.exists()


@pytest.mark.skipif(not os.getenv('JARVIS_TEST_DATABASE_URL'), reason='Dedicated CI PostgreSQL service not configured')
def test_postgres_backup_restores_to_sqlite(tmp_path):
    # Only the explicitly named TEST database is used; never DATABASE_URL.
    store = Store(tmp_path / 'unused.db', os.environ['JARVIS_TEST_DATABASE_URL'])
    store.initialize()
    store.initialize()  # schema creation is idempotent
    with store.connection() as con:
        job_id = con.execute("INSERT INTO job_listings(source,source_id,query,title) VALUES('pg-test','pg1','data','Postgres recovery role')").lastrowid
        app_id = con.execute("INSERT INTO applications(sender,job_listing_id,status) VALUES('recovery-test',?,'APPLIED')", (job_id,)).lastrowid
        con.execute("INSERT INTO application_notes(application_id,body) VALUES(?,'Portable note')", (app_id,))
        con.execute("INSERT INTO follow_ups(application_id,due_on) VALUES(?,'2030-01-01')", (app_id,))
    payload = json.loads(json.dumps(build_backup(store, 'recovery-test'), default=str))
    restored = restore_backup(payload, tmp_path / 'from-postgres.db')
    assert build_backup(restored, 'recovery-test')['tables'] == payload['tables']
