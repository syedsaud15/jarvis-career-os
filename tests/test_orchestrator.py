from app.orchestrator import Orchestrator
from app.job_ranking import rank_job
from app.store import Store
from app.types import Intent


def make_orchestrator(tmp_path):
    store = Store(tmp_path / "test.db")
    store.initialize()
    return Orchestrator(store)


def test_routes_intents():
    assert Orchestrator.route("find data engineer jobs") is Intent.JOB_SEARCH
    assert Orchestrator.route("show my email inbox") is Intent.EMAIL
    assert Orchestrator.route("schedule a meeting") is Intent.CALENDAR
    assert Orchestrator.route("I spent ₹250 on lunch") is Intent.EXPENSE
    assert Orchestrator.route("remind me to call mom") is Intent.REMINDER


def test_expense_is_persisted(tmp_path):
    result = make_orchestrator(tmp_path).process("spent ₹250 on lunch", "me")
    assert result.intent is Intent.EXPENSE
    assert "₹250.00" in result.reply


def test_reminder_is_persisted(tmp_path):
    result = make_orchestrator(tmp_path).process("remind me to submit assignment", "me")
    assert result.intent is Intent.REMINDER
    assert "saved" in result.reply


def test_send_email_creates_approval(tmp_path):
    jarvis = make_orchestrator(tmp_path)
    result = jarvis.process("send an email to my recruiter", "me")
    assert "approval_requested" in result.actions
    assert len(jarvis.approvals.list()) == 1


def test_approval_decision_is_audited(tmp_path):
    jarvis = make_orchestrator(tmp_path)
    jarvis.process("send an email to my recruiter", "me")
    approval = jarvis.approvals.list()[0]
    resolved = jarvis.approvals.decide(approval["id"], "APPROVED")
    assert resolved is not None
    assert resolved["status"] == "APPROVED"
    events = [event["event_type"] for event in jarvis.approvals.audit_log()]
    assert events[:2] == ["approval.approved", "approval.created"]


def test_mnc_data_engineering_job_scores_highly():
    ranked = rank_job({
        "title": "Senior Data Engineer", "company": "Deutsche Bank",
        "description": "Python SQL Spark Airflow ETL AWS Databricks", "salary_min": 2000000,
    })
    assert ranked["mnc_priority"] is True
    assert "spark" in ranked["matched_skills"]
    assert ranked["match_score"] >= 80


def test_rank_explains_profile_gap():
    ranked = rank_job(
        {"title": "Data Engineer", "company": "Example", "description": "Python SQL Spark Airflow"},
        profile_skills=["python", "sql"],
    )
    assert ranked["matched_skills"] == ["python", "sql"]
    assert "spark" in ranked["missing_skills"]
    assert "Matched skills" in ranked["match_explanation"]


def test_career_workspace_tables_are_initialized(tmp_path):
    store = Store(tmp_path / "career.db")
    store.initialize()
    with store.connection() as con:
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert {"application_notes", "follow_ups", "resume_versions"}.issubset(tables)
