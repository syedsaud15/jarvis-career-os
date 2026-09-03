from __future__ import annotations

from contextlib import asynccontextmanager
import json
import base64
import hashlib
import secrets
import csv
import io
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse
from cryptography.fernet import Fernet
from pypdf import PdfReader
from app.approvals import ApprovalService
from app.config import get_settings
from app.job_ranking import extract_skills, normalized_job_key, rank_job
from app.google_actions import GoogleActionExecutor
from app.auth import create_token, hash_password, verify_password, verify_token
from app.orchestrator import Orchestrator
from app.store import Store
from app.backup import build_backup
from app.trends import weekly_trends
from app.types import (
    ApplicationCreate, ApplicationNoteCreate, ApplicationStatusUpdate, ApprovalDecision,
    FollowUpCreate, ProcessRequest, ProcessResponse, ProfileTextUpdate, ResumeVersionCreate, EmailApprovalRequest, CalendarApprovalRequest, UserLogin, UserRegister, UserSettingsUpdate,
)

settings = get_settings()
store = Store(settings.database_path, settings.database_url)
orchestrator = Orchestrator(store, settings)
approvals = ApprovalService(store)
request_window: dict[str, deque[float]] = defaultdict(deque)


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    yield


app = FastAPI(title="JARVIS Agent", version="0.1.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, error: RequestValidationError):
    fields = [".".join(str(part) for part in item["loc"][1:]) for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": "Invalid request", "fields": fields})


@app.exception_handler(Exception)
async def safe_server_error(_: Request, __: Exception):
    return JSONResponse(status_code=500, content={"detail": "JARVIS could not complete the request safely."})


@app.middleware("http")
async def optional_api_key(request: Request, call_next):
    public_paths = {"/health", "/metrics", "/docs", "/openapi.json", "/integrations/google/callback", "/auth/register", "/auth/login"}
    client = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc).timestamp(); bucket = request_window[client]
    while bucket and bucket[0] < now - 60: bucket.popleft()
    if len(bucket) >= 120:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again shortly."})
    bucket.append(now)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 5 * 1024 * 1024:
        return JSONResponse(status_code=413, content={"detail": "Request is larger than the 5 MB limit."})
    if settings.api_key and request.url.path not in public_paths:
        authorization = request.headers.get("Authorization", "")
        bearer = authorization.removeprefix("Bearer ").strip() if authorization.startswith("Bearer ") else ""
        if request.headers.get("X-API-Key") != settings.api_key and not verify_token(bearer, settings.api_key):
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local-first", "job_provider": "configured" if settings.adzuna_app_id else "not_configured"}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    with store.connection() as con:
        users = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        approvals_pending = con.execute("SELECT COUNT(*) FROM approvals WHERE status='PENDING'").fetchone()[0]
    return PlainTextResponse(f"jarvis_users_total {users}\njarvis_pending_approvals {approvals_pending}\n")


@app.post("/auth/register", status_code=201)
def register_user(payload: UserRegister) -> dict[str, str]:
    try:
        with store.connection() as con:
            con.execute("INSERT INTO users(email, password_hash) VALUES (?, ?)", (payload.email.lower(), hash_password(payload.password)))
    except Exception as error:
        raise HTTPException(status_code=409, detail="Account already exists") from error
    return {"status": "created"}


@app.post("/auth/login")
def login_user(payload: UserLogin) -> dict[str, str]:
    with store.connection() as con:
        row = con.execute("SELECT password_hash FROM users WHERE email=?", (payload.email.lower(),)).fetchone()
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not settings.api_key:
        raise HTTPException(status_code=503, detail="Authentication signing key is not configured")
    return {"access_token": create_token(payload.email.lower(), settings.api_key), "token_type": "bearer"}


@app.post("/process", response_model=ProcessResponse)
def process_message(payload: ProcessRequest) -> ProcessResponse:
    return orchestrator.process(payload.message, payload.sender)


@app.get("/approvals")
def list_approvals(status: str = "PENDING", sender: str = "dashboard-user") -> list[dict[str, object]]:
    return approvals.list(status, sender)


@app.post("/approvals/{approval_id}/decision")
def decide_approval(approval_id: int, payload: ApprovalDecision) -> dict[str, object]:
    result = approvals.decide(approval_id, payload.decision, payload.note)
    if result is None:
        raise HTTPException(status_code=404, detail="Pending approval not found")
    if result["status"] == "APPROVED" and result["tool_name"] in {"email.send", "calendar.create"}:
        try:
            details = GoogleActionExecutor(store, google_cipher, settings).execute(result["sender"], result["tool_name"], json.loads(result.get("action_payload") or "{}"))
            with store.connection() as con:
                con.execute("INSERT INTO audit_logs(sender,event_type,entity_type,entity_id,details) VALUES(?, 'action.executed', 'approval', ?, ?)", (result["sender"], approval_id, details))
            result["execution"] = details
        except Exception as error:
            with store.connection() as con:
                con.execute("INSERT INTO audit_logs(sender,event_type,entity_type,entity_id,details) VALUES(?, 'action.failed', 'approval', ?, ?)", (result["sender"], approval_id, str(error)))
            result["execution"] = "Approved, but execution failed. Review audit logs."
    return result


@app.post("/actions/email/request", status_code=201)
def request_email_action(payload: EmailApprovalRequest) -> dict[str, object]:
    approval_id = approvals.create(payload.sender, "email.send", f"Send email to {payload.to}: {payload.subject}", payload.model_dump(exclude={"sender"}))
    return {"approval_id": approval_id, "status": "PENDING"}


@app.post("/actions/calendar/request", status_code=201)
def request_calendar_action(payload: CalendarApprovalRequest) -> dict[str, object]:
    approval_id = approvals.create(payload.sender, "calendar.create", f"Create calendar event: {payload.title}", payload.model_dump(exclude={"sender"}))
    return {"approval_id": approval_id, "status": "PENDING"}


@app.get("/audit-logs")
def list_audit_logs(limit: int = 50, sender: str = "dashboard-user") -> list[dict[str, object]]:
    safe_limit = max(1, min(limit, 200))
    return approvals.audit_log(safe_limit, sender)


@app.get("/settings")
def get_user_settings(sender: str = "dashboard-user") -> dict[str, object]:
    with store.connection() as con:
        row = con.execute("SELECT * FROM user_settings WHERE sender=?", (sender,)).fetchone()
    if not row:
        return {"sender": sender, "display_name": "Syed Saud", "target_role": "Data Engineer", "target_location": "Pune", "minimum_fit": 45, "weekly_digest": True, "follow_up_reminders": True}
    result = dict(row)
    result["weekly_digest"] = bool(result["weekly_digest"])
    result["follow_up_reminders"] = bool(result["follow_up_reminders"])
    return result


@app.put("/settings")
def update_user_settings(payload: UserSettingsUpdate, sender: str = "dashboard-user") -> dict[str, object]:
    with store.connection() as con:
        con.execute(
            "INSERT INTO user_settings(sender,display_name,target_role,target_location,minimum_fit,weekly_digest,follow_up_reminders) VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(sender) DO UPDATE SET display_name=excluded.display_name,target_role=excluded.target_role,target_location=excluded.target_location,minimum_fit=excluded.minimum_fit,weekly_digest=excluded.weekly_digest,follow_up_reminders=excluded.follow_up_reminders,updated_at=CURRENT_TIMESTAMP",
            (sender, payload.display_name.strip(), payload.target_role.strip(), payload.target_location.strip(), payload.minimum_fit, int(payload.weekly_digest), int(payload.follow_up_reminders)),
        )
        con.execute("INSERT INTO audit_logs(sender,event_type,entity_type,details) VALUES(?,'settings.updated','settings',?)", (sender, payload.model_dump_json()))
    return get_user_settings(sender)


@app.get("/activity")
def activity_timeline(sender: str = "dashboard-user", limit: int = 40) -> list[dict[str, object]]:
    safe_limit = max(1, min(limit, 100))
    with store.connection() as con:
        rows = con.execute(
            "SELECT event_type AS type, entity_type, details, created_at FROM audit_logs WHERE sender=? "
            "UNION ALL SELECT 'application.updated', 'application', status || ': ' || COALESCE(job_listings.title,''), applications.updated_at FROM applications JOIN job_listings ON job_listings.id=applications.job_listing_id WHERE applications.sender=? "
            "ORDER BY created_at DESC LIMIT ?", (sender, sender, safe_limit),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/notifications")
def notifications(sender: str = "dashboard-user") -> list[dict[str, object]]:
    today = datetime.now(timezone.utc).date().isoformat()
    with store.connection() as con:
        followups = con.execute(
            "SELECT follow_ups.id, follow_ups.due_on, job_listings.title, job_listings.company FROM follow_ups JOIN applications ON applications.id=follow_ups.application_id JOIN job_listings ON job_listings.id=applications.job_listing_id WHERE applications.sender=? AND follow_ups.completed=0 AND follow_ups.due_on<=? ORDER BY follow_ups.due_on", (sender, today),
        ).fetchall()
        pending = con.execute("SELECT COUNT(*) AS total FROM approvals WHERE sender=? AND status='PENDING'", (sender,)).fetchone()["total"]
    items = [{"id": f"followup-{row['id']}", "type": "FOLLOW_UP", "title": f"Follow up: {row['title']}", "detail": row["company"] or "Application", "due_on": row["due_on"]} for row in followups]
    if pending:
        items.insert(0, {"id": "pending-approvals", "type": "APPROVAL", "title": f"{pending} action{'s' if pending != 1 else ''} need approval", "detail": "Review before JARVIS executes."})
    return items


@app.get("/jobs")
def list_cached_jobs(limit: int = 20, sender: str = "dashboard-user") -> list[dict[str, object]]:
    safe_limit = max(1, min(limit, 100))
    with store.connection() as con:
        rows = con.execute(
            "SELECT id, source, query, title, company, location, description, salary_min, salary_max, redirect_url, posted_at, fetched_at "
            "FROM job_listings ORDER BY id DESC LIMIT ?", (100,)
        ).fetchall()
    with store.connection() as con:
        profile = con.execute("SELECT skills_json FROM career_profiles WHERE sender=?", (sender,)).fetchone()
    skills = json.loads(profile["skills_json"]) if profile else None
    ranked = sorted((rank_job(dict(row), skills) for row in rows), key=lambda job: (int(job["match_score"]), int(job["quality_score"])), reverse=True)
    unique: dict[str, dict[str, object]] = {}
    for job in ranked:
        if job["is_expired"]:
            continue
        unique.setdefault(normalized_job_key(job), job)
    return list(unique.values())[:safe_limit]


def save_profile(sender: str, resume_text: str) -> dict[str, object]:
    skills = extract_skills(resume_text)
    with store.connection() as con:
        con.execute(
            "INSERT INTO career_profiles(sender, resume_text, skills_json) VALUES (?, ?, ?) "
            "ON CONFLICT(sender) DO UPDATE SET resume_text=excluded.resume_text, skills_json=excluded.skills_json, updated_at=CURRENT_TIMESTAMP",
            (sender, resume_text, json.dumps(skills)),
        )
    return {"sender": sender, "skills": skills, "resume_connected": True}


@app.get("/profile")
def get_profile(sender: str = "dashboard-user") -> dict[str, object]:
    with store.connection() as con:
        row = con.execute("SELECT skills_json, updated_at FROM career_profiles WHERE sender=?", (sender,)).fetchone()
    if not row:
        return {"sender": sender, "skills": [], "resume_connected": False}
    return {"sender": sender, "skills": json.loads(row["skills_json"]), "resume_connected": True, "updated_at": row["updated_at"]}


@app.post("/profile")
def update_profile(payload: ProfileTextUpdate) -> dict[str, object]:
    return save_profile(payload.sender, payload.resume_text)


@app.post("/profile/upload")
async def upload_profile(file: UploadFile = File(...), sender: str = "dashboard-user") -> dict[str, object]:
    suffix = (file.filename or "").lower().rsplit(".", 1)[-1]
    if suffix not in {"pdf", "txt"}:
        raise HTTPException(status_code=415, detail="Upload a PDF or TXT resume")
    if suffix == "pdf":
        reader = PdfReader(file.file)
        resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        resume_text = (await file.read()).decode("utf-8", errors="ignore")
    if len(resume_text.strip()) < 20:
        raise HTTPException(status_code=422, detail="The uploaded resume has no readable text")
    return save_profile(sender, resume_text)


@app.get("/applications")
def list_applications(sender: str = "dashboard-user") -> list[dict[str, object]]:
    with store.connection() as con:
        rows = con.execute(
            "SELECT applications.id, applications.status, applications.created_at, applications.updated_at, "
            "job_listings.id AS job_listing_id, job_listings.title, job_listings.company, job_listings.location, job_listings.redirect_url "
            "FROM applications JOIN job_listings ON job_listings.id=applications.job_listing_id "
            "WHERE applications.sender=? ORDER BY applications.updated_at DESC, applications.id DESC", (sender,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_application_or_404(application_id: int):
    with store.connection() as con:
        row = con.execute(
            "SELECT applications.id, applications.sender, applications.status, job_listings.title, job_listings.company, "
            "job_listings.location, job_listings.description, job_listings.redirect_url "
            "FROM applications JOIN job_listings ON job_listings.id=applications.job_listing_id WHERE applications.id=?",
            (application_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    return dict(row)


@app.post("/applications", status_code=201)
def save_application(payload: ApplicationCreate) -> dict[str, object]:
    with store.connection() as con:
        job = con.execute("SELECT id FROM job_listings WHERE id=?", (payload.job_listing_id,)).fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job listing not found")
        con.execute(
            "INSERT INTO applications(sender, job_listing_id) VALUES (?, ?) "
            "ON CONFLICT(sender, job_listing_id) DO UPDATE SET updated_at=CURRENT_TIMESTAMP",
            (payload.sender, payload.job_listing_id),
        )
        row = con.execute(
            "SELECT id, status, job_listing_id, created_at, updated_at FROM applications "
            "WHERE sender=? AND job_listing_id=?", (payload.sender, payload.job_listing_id),
        ).fetchone()
    return dict(row)


@app.post("/applications/{application_id}/status")
def update_application_status(application_id: int, payload: ApplicationStatusUpdate) -> dict[str, object]:
    with store.connection() as con:
        previous = con.execute("SELECT sender,status FROM applications WHERE id=?", (application_id,)).fetchone()
        if not previous:
            raise HTTPException(status_code=404, detail="Application not found")
        cursor = con.execute(
            "UPDATE applications SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (payload.status, application_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Application not found")
        row = con.execute("SELECT id, status, job_listing_id, created_at, updated_at FROM applications WHERE id=?", (application_id,)).fetchone()
        if previous["status"] != payload.status:
            con.execute("INSERT INTO audit_logs(sender,event_type,entity_type,entity_id,details) VALUES(?,'application.status_changed','application',?,?)",
                        (previous["sender"], application_id, json.dumps({"from": previous["status"], "to": payload.status})))
    return dict(row)


@app.get("/applications/{application_id}/notes")
def list_application_notes(application_id: int) -> list[dict[str, object]]:
    get_application_or_404(application_id)
    with store.connection() as con:
        rows = con.execute("SELECT id, body, created_at FROM application_notes WHERE application_id=? ORDER BY id DESC", (application_id,)).fetchall()
    return [dict(row) for row in rows]


@app.post("/applications/{application_id}/notes", status_code=201)
def create_application_note(application_id: int, payload: ApplicationNoteCreate) -> dict[str, object]:
    get_application_or_404(application_id)
    with store.connection() as con:
        cursor = con.execute("INSERT INTO application_notes(application_id, body) VALUES (?, ?)", (application_id, payload.body.strip()))
        row = con.execute("SELECT id, body, created_at FROM application_notes WHERE id=?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@app.get("/applications/{application_id}/follow-ups")
def list_follow_ups(application_id: int) -> list[dict[str, object]]:
    get_application_or_404(application_id)
    with store.connection() as con:
        rows = con.execute(
            "SELECT id, due_on, completed, created_at FROM follow_ups WHERE application_id=? ORDER BY completed, due_on, id DESC", (application_id,)
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/applications/{application_id}/follow-ups", status_code=201)
def create_follow_up(application_id: int, payload: FollowUpCreate) -> dict[str, object]:
    get_application_or_404(application_id)
    with store.connection() as con:
        cursor = con.execute("INSERT INTO follow_ups(application_id, due_on) VALUES (?, ?)", (application_id, payload.due_on))
        row = con.execute("SELECT id, due_on, completed, created_at FROM follow_ups WHERE id=?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@app.post("/follow-ups/{follow_up_id}/complete")
def complete_follow_up(follow_up_id: int) -> dict[str, object]:
    with store.connection() as con:
        cursor = con.execute("UPDATE follow_ups SET completed=1 WHERE id=?", (follow_up_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        row = con.execute("SELECT id, application_id, due_on, completed FROM follow_ups WHERE id=?", (follow_up_id,)).fetchone()
    return dict(row)


@app.get("/applications/{application_id}/cover-letter")
def draft_cover_letter(application_id: int) -> dict[str, str]:
    application = get_application_or_404(application_id)
    with store.connection() as con:
        profile = con.execute("SELECT skills_json FROM career_profiles WHERE sender=?", (application["sender"],)).fetchone()
    skills = json.loads(profile["skills_json"]) if profile else []
    company = application["company"] or "your team"
    role = application["title"]
    skills_line = ", ".join(skills[:6]) or "[add skills supported by your resume]"
    name = get_user_settings(application["sender"])["display_name"]
    body = (
        f"Dear Hiring Team,\n\nI am writing to express my interest in the {role} role at {company}. "
        f"My data-engineering background includes {skills_line}, and I enjoy building reliable data products that turn complex information into useful decisions.\n\n"
        f"I would welcome the opportunity to discuss how my technical experience and ownership mindset can contribute to {company}. "
        f"Thank you for your time and consideration.\n\nSincerely,\n{name}"
    )
    return {"application_id": str(application_id), "draft": body}


@app.get("/applications/{application_id}/interview-prep")
def interview_prep(application_id: int) -> dict[str, object]:
    application = get_application_or_404(application_id)
    with store.connection() as con:
        profile = con.execute("SELECT skills_json FROM career_profiles WHERE sender=?", (application["sender"],)).fetchone()
    skills = json.loads(profile["skills_json"]) if profile else []
    ranked = rank_job({"title": application["title"], "company": application["company"], "location": application["location"], "description": application["description"] or ""}, skills)
    missing = ranked.get("missing_skills", [])[:5]
    matched = ranked.get("matched_skills", [])[:5]
    company = application["company"] or "the company"
    questions = [
        f"Walk me through a data pipeline you designed that is relevant to {application['title']}.",
        f"How would you ensure data quality, observability and recovery in production at {company}?",
        "Describe a difficult stakeholder trade-off and how you measured the result.",
        "How do you diagnose a slow or unreliable data workflow?",
    ]
    if missing:
        questions.append(f"How would you ramp up on {missing[0]} during your first month?")
    return {"application_id": application_id, "matched_strengths": matched, "skill_gaps": missing, "questions": questions, "preparation_plan": ["Prepare two STAR stories with measurable outcomes", "Review the job description and map each requirement to evidence", "Prepare architecture and debugging examples", "Write three thoughtful questions for the interviewer"]}


@app.get("/applications/{application_id}/copilot")
def application_copilot(application_id: int) -> dict[str, object]:
    application = get_application_or_404(application_id)
    prep = interview_prep(application_id)
    strengths = prep["matched_strengths"]
    gaps = prep["skill_gaps"]
    evidence = ", ".join(strengths[:4]) or "reliable data delivery and ownership"
    return {
        "resume_suggestions": [
            f"Lead with measurable {application['title']} outcomes and evidence in {evidence}.",
            "Mirror the role's language only where your resume contains truthful project evidence.",
            f"For {gaps[0] if gaps else 'production reliability'}, add evidence only if you have it; otherwise use the learning roadmap, not a claimed skill.",
        ],
        "recruiter_email": (
            f"Subject: Interest in {application['title']} at {application['company']}\n\n"
            f"Hello, I am exploring the {application['title']} opportunity at {application['company']}. "
            f"My background includes {evidence}. I would value a brief conversation about the team's priorities and how I could contribute."
        ),
        "cover_letter": draft_cover_letter(application_id)["draft"],
        "interview_prep": prep,
    }


@app.get("/profile/skill-roadmap")
def skill_roadmap(sender: str = "dashboard-user") -> dict[str, object]:
    with store.connection() as con:
        profile = con.execute("SELECT skills_json FROM career_profiles WHERE sender=?", (sender,)).fetchone()
    jobs = list_cached_jobs(100, sender)
    owned = set(json.loads(profile["skills_json"])) if profile else set()
    demand: dict[str, int] = defaultdict(int)
    for row in jobs:
        for skill in extract_skills(f"{row['title']} {row['description'] or ''}"):
            if skill not in owned:
                demand[skill] += 1
    ranked = sorted(demand.items(), key=lambda item: (-item[1], item[0]))[:6]
    detected = any(extract_skills(f"{row['title']} {row['description'] or ''}") for row in jobs)
    status = 'resume_required' if not profile else 'no_roles' if not jobs else 'insufficient_job_skills' if not detected else 'gaps_found' if ranked else 'no_detected_gaps'
    return {"status": status, "current_skills": sorted(owned), "roadmap": [{"skill": skill, "demand_signals": count, "project": f"Build one production-style {skill} project with tests, observability and a measurable outcome."} for skill, count in ranked] if profile else []}


@app.get("/applications/export.csv")
def export_applications(sender: str = "dashboard-user") -> StreamingResponse:
    rows = list_applications(sender)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["id", "status", "title", "company", "location", "redirect_url", "created_at", "updated_at"], extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    filename = f"jarvis-applications-{datetime.now(timezone.utc).date().isoformat()}.csv"
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/reports/weekly")
def weekly_report(sender: str = "dashboard-user") -> dict[str, object]:
    analytics = career_analytics(sender)
    alerts = high_signal_alerts(sender, 3)
    with store.connection() as con:
        recent = con.execute("SELECT COUNT(*) AS total FROM applications WHERE sender=? AND created_at>=datetime('now','-7 days')", (sender,)).fetchone()["total"]
        interviews = con.execute("SELECT COUNT(*) AS total FROM applications WHERE sender=? AND status='INTERVIEW' AND updated_at>=datetime('now','-7 days')", (sender,)).fetchone()["total"]
    return {"period_days": 7, "new_applications": recent, "interviews_moved": interviews, "interview_rate": analytics["interview_rate"], "open_follow_ups": analytics["open_follow_ups"], "top_opportunities": alerts, "recommended_focus": alerts[0]["next_step"] if alerts else "Run a fresh market scan and capture the strongest role."}


@app.get("/analytics/trends")
def career_trends(sender: str = "dashboard-user") -> dict[str, object]:
    return weekly_trends(store, sender)


@app.get("/analytics")
def career_analytics(sender: str = "dashboard-user") -> dict[str, object]:
    with store.connection() as con:
        status_rows = con.execute("SELECT status, COUNT(*) AS total FROM applications WHERE sender=? GROUP BY status", (sender,)).fetchall()
        follow_up_rows = con.execute(
            "SELECT follow_ups.id, follow_ups.due_on, job_listings.title, job_listings.company FROM follow_ups "
            "JOIN applications ON applications.id=follow_ups.application_id JOIN job_listings ON job_listings.id=applications.job_listing_id "
            "WHERE applications.sender=? AND follow_ups.completed=0 ORDER BY follow_ups.due_on LIMIT 10", (sender,)
        ).fetchall()
        total = con.execute("SELECT COUNT(*) AS total FROM applications WHERE sender=?", (sender,)).fetchone()["total"]
    by_status = {row["status"]: row["total"] for row in status_rows}
    interviews = by_status.get("INTERVIEW", 0)
    applied = by_status.get("APPLIED", 0) + interviews
    funnel = [{"stage": stage, "total": by_status.get(stage, 0)} for stage in ("SAVED", "APPLIED", "INTERVIEW", "REJECTED")]
    return {
        "total_applications": total,
        "by_status": by_status,
        "interview_rate": round((interviews / applied) * 100) if applied else 0,
        "open_follow_ups": [dict(row) for row in follow_up_rows],
        "funnel": funnel,
        "conversion": {"saved_to_applied": round((applied / total) * 100) if total else 0, "applied_to_interview": round((interviews / applied) * 100) if applied else 0},
    }


@app.get("/backup/export.json")
def export_backup(sender: str = "dashboard-user") -> StreamingResponse:
    data = build_backup(store, sender)
    filename = f"jarvis-backup-{datetime.now(timezone.utc).date().isoformat()}.json"
    return StreamingResponse(iter([json.dumps(data, default=str, indent=2)]), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@app.get("/alerts")
def high_signal_alerts(sender: str = "dashboard-user", limit: int = 5) -> list[dict[str, object]]:
    safe_limit = max(1, min(limit, 20))
    with store.connection() as con:
        captured = {row["job_listing_id"] for row in con.execute("SELECT job_listing_id FROM applications WHERE sender=?", (sender,)).fetchall()}
    ranked = [job for job in list_cached_jobs(100, sender) if job['id'] not in captured]
    high_signal = [job for job in sorted(ranked, key=lambda job: int(job["match_score"]), reverse=True) if job["match_score"] >= 45]
    return [{"type": "HIGH_FIT_ROLE", "title": job["title"], "company": job["company"], "match_score": job["match_score"], "next_step": job["next_step"]} for job in high_signal[:safe_limit]]


@app.get("/resume-versions")
def list_resume_versions(sender: str = "dashboard-user") -> list[dict[str, object]]:
    with store.connection() as con:
        rows = con.execute("SELECT id, label, skills_json, created_at FROM resume_versions WHERE sender=? ORDER BY id DESC", (sender,)).fetchall()
    return [{**dict(row), "skills": json.loads(row["skills_json"])} for row in rows]


@app.post("/resume-versions", status_code=201)
def create_resume_version(payload: ResumeVersionCreate) -> dict[str, object]:
    skills = extract_skills(payload.resume_text)
    with store.connection() as con:
        cursor = con.execute(
            "INSERT INTO resume_versions(sender, label, resume_text, skills_json) VALUES (?, ?, ?, ?)",
            (payload.sender, payload.label.strip(), payload.resume_text, json.dumps(skills)),
        )
        row = con.execute("SELECT id, label, skills_json, created_at FROM resume_versions WHERE id=?", (cursor.lastrowid,)).fetchone()
    return {**dict(row), "skills": json.loads(row["skills_json"])}


@app.post("/resume-versions/from-profile", status_code=201)
def save_current_profile_as_version(label: str, sender: str = "dashboard-user") -> dict[str, object]:
    clean_label = label.strip()
    if not clean_label or len(clean_label) > 100:
        raise HTTPException(status_code=422, detail="Provide a resume version label under 100 characters")
    with store.connection() as con:
        profile = con.execute("SELECT resume_text, skills_json FROM career_profiles WHERE sender=?", (sender,)).fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Connect a resume before saving a version")
        cursor = con.execute(
            "INSERT INTO resume_versions(sender, label, resume_text, skills_json) VALUES (?, ?, ?, ?)",
            (sender, clean_label, profile["resume_text"], profile["skills_json"]),
        )
        row = con.execute("SELECT id, label, skills_json, created_at FROM resume_versions WHERE id=?", (cursor.lastrowid,)).fetchone()
    return {**dict(row), "skills": json.loads(row["skills_json"])}


@app.get("/integrations")
def integrations() -> list[dict[str, str]]:
    with store.connection() as con:
        google = con.execute("SELECT 1 FROM oauth_connections WHERE provider='google' AND sender='dashboard-user'").fetchone()
    return [
        {"name": "Adzuna job data", "status": "CONNECTED" if settings.adzuna_app_id else "NOT_CONNECTED", "capability": "Live job discovery and ranking"},
        {"name": "Gmail", "status": "CONNECTED" if google else "OAUTH_REQUIRED", "capability": "Approved recruiter emails only"},
        {"name": "Google Calendar", "status": "CONNECTED" if google else "OAUTH_REQUIRED", "capability": "Approved interview events only"},
    ]


def google_cipher() -> Fernet:
    # A dedicated API key is preferred in production. The Google client secret
    # provides a secure local fallback so a local OAuth connection is not blocked.
    seed = settings.api_key or settings.google_client_secret
    if not seed:
        raise HTTPException(status_code=503, detail="Configure an encryption secret before connecting Google")
    key = base64.urlsafe_b64encode(hashlib.sha256(seed.encode()).digest())
    return Fernet(key)


@app.get("/integrations/google/start")
def start_google_connection(sender: str = "dashboard-user") -> dict[str, str]:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth credentials are not configured")
    google_cipher()
    state = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    with store.connection() as con:
        con.execute("DELETE FROM oauth_states WHERE expires_at < ?", (datetime.now(timezone.utc).isoformat(),))
        con.execute("INSERT INTO oauth_states(state, sender, expires_at) VALUES (?, ?, ?)", (state, sender, expires))
    query = urlencode({"client_id": settings.google_client_id, "redirect_uri": settings.google_redirect_uri, "response_type": "code", "access_type": "offline", "prompt": "consent", "state": state, "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar.events"})
    return {"authorization_url": f"https://accounts.google.com/o/oauth2/v2/auth?{query}"}


@app.get("/integrations/google/callback")
def google_callback(code: str, state: str) -> HTMLResponse:
    with store.connection() as con:
        row = con.execute("SELECT sender, expires_at FROM oauth_states WHERE state=?", (state,)).fetchone()
        con.execute("DELETE FROM oauth_states WHERE state=?", (state,))
    if not row or row["expires_at"] < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    payload = urlencode({"code": code, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret, "redirect_uri": settings.google_redirect_uri, "grant_type": "authorization_code"}).encode()
    try:
        with urlopen(UrlRequest("https://oauth2.googleapis.com/token", data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=15) as response:
            token = json.loads(response.read().decode())
    except Exception as error:
        raise HTTPException(status_code=502, detail="Google token exchange failed") from error
    encrypted = google_cipher().encrypt(json.dumps(token).encode()).decode()
    with store.connection() as con:
        con.execute("INSERT INTO oauth_connections(provider, sender, encrypted_token) VALUES ('google', ?, ?) ON CONFLICT(provider, sender) DO UPDATE SET encrypted_token=excluded.encrypted_token, connected_at=CURRENT_TIMESTAMP", (row["sender"], encrypted))
    return HTMLResponse("<h2>JARVIS connected to Google.</h2><p>You may close this tab and return to the dashboard.</p>")
