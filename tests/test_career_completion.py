from pathlib import Path

from app import main
from app.store import Store
from app.types import UserSettingsUpdate


def use_store(tmp_path: Path) -> Store:
    store = Store(tmp_path / "jarvis-test.db")
    store.initialize()
    main.store = store
    main.approvals.store = store
    return store


def test_settings_round_trip(tmp_path):
    use_store(tmp_path)
    saved = main.update_user_settings(UserSettingsUpdate(display_name="Syed", target_role="Senior Data Engineer", target_location="Pune", minimum_fit=60), "tester")
    assert saved["display_name"] == "Syed"
    assert saved["minimum_fit"] == 60
    assert main.get_user_settings("tester")["target_role"] == "Senior Data Engineer"


def test_notifications_include_due_followup_and_approval(tmp_path):
    store = use_store(tmp_path)
    with store.connection() as con:
        job_id = con.execute("INSERT INTO job_listings(source,source_id,query,title,company) VALUES('test','1','data','Data Engineer','Example')").lastrowid
        application_id = con.execute("INSERT INTO applications(sender,job_listing_id) VALUES('tester',?)", (job_id,)).lastrowid
        con.execute("INSERT INTO follow_ups(application_id,due_on) VALUES(?,'2020-01-01')", (application_id,))
        con.execute("INSERT INTO approvals(sender,tool_name,summary) VALUES('tester','email.send','Send message')")
    items = main.notifications("tester")
    assert {item["type"] for item in items} == {"APPROVAL", "FOLLOW_UP"}


def test_interview_prep_and_weekly_report(tmp_path):
    store = use_store(tmp_path)
    with store.connection() as con:
        job_id = con.execute("INSERT INTO job_listings(source,source_id,query,title,company,description) VALUES('test','1','data','Data Engineer','Example','python sql spark')").lastrowid
        application_id = con.execute("INSERT INTO applications(sender,job_listing_id,status) VALUES('tester',?,'INTERVIEW')", (job_id,)).lastrowid
        con.execute("INSERT INTO career_profiles(sender,resume_text,skills_json) VALUES('tester','Python and SQL data engineering','[\"python\", \"sql\"]')")
    prep = main.interview_prep(application_id)
    assert prep["questions"] and "python" in prep["matched_strengths"]
    report = main.weekly_report("tester")
    assert report["new_applications"] == 1
    assert report["interviews_moved"] == 1
