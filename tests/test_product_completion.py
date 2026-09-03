from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import main
from app.job_ranking import normalized_job_key, rank_job
from app.store import Store


def configured_store(tmp_path: Path) -> Store:
    store = Store(tmp_path / "completion.db")
    store.initialize()
    main.store = store
    main.approvals.store = store
    return store


def test_ranking_classifies_quality_freshness_and_duplicates():
    posted = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    job = rank_job({"title": "Senior Data Engineer", "company": "Example", "location": "Remote India", "description": "Python SQL hybrid", "redirect_url": "https://example.test", "posted_at": posted}, ["python", "sql"])
    assert job["quality_score"] >= 70
    assert job["work_mode"] == "REMOTE"
    assert job["experience_level"] == "SENIOR"
    assert job["is_expired"] is False
    assert normalized_job_key(job) == normalized_job_key({**job, "title": "Senior  Data-Engineer"})


def test_migration_copilot_analytics_and_safe_backup(tmp_path):
    store = configured_store(tmp_path)
    with store.connection() as con:
        assert con.execute("SELECT version FROM schema_migrations").fetchone()["version"] == 1
        job_id = con.execute("INSERT INTO job_listings(source,source_id,query,title,company,location,description) VALUES('test','j1','data','Data Engineer','Acme','India','python sql spark')").lastrowid
        app_id = con.execute("INSERT INTO applications(sender,job_listing_id,status) VALUES('tester',?,'APPLIED')", (job_id,)).lastrowid
        con.execute("INSERT INTO career_profiles(sender,resume_text,skills_json) VALUES('tester','Python SQL experience','[\"python\",\"sql\"]')")
    copilot = main.application_copilot(app_id)
    assert copilot["resume_suggestions"] and "Subject:" in copilot["recruiter_email"]
    analytics = main.career_analytics("tester")
    assert analytics["funnel"][1] == {"stage": "APPLIED", "total": 1}
    response = main.export_backup("tester")
    assert response.media_type == "application/json"


def test_public_demo_contract_is_api_isolated():
    root = Path(__file__).parents[1]
    nginx = (root / "deploy" / "render-nginx.conf").read_text(encoding="utf-8")
    app_source = (root / "dashboard" / "src" / "App.rebuild.jsx").read_text(encoding="utf-8")
    for location in ("location = /demo", "location ^~ /demo/"):
        block = nginx.split(location, 1)[1].split("}", 1)[0]
        assert "auth_basic off" in block
        assert "try_files /index.html =404;" in block
        assert "$uri" not in block
    assert "if (isDemo)" in app_source
    assert "100% synthetic sample data" in app_source
    assert "Simulation online · private APIs isolated" in app_source
    assert "useState(() => isDemo ? demoData.settings" in app_source
    demo_load = app_source.split("const loadData = useCallback", 1)[1].split("setSyncing(true)", 1)[0]
    assert "setSettings(demoData.settings)" in demo_load
    assert "return" in demo_load
    assert "fetch(" not in demo_load and "apiRequest(" not in demo_load
