# JARVIS Career OS

A production-deployed career intelligence and human-in-the-loop automation product. Explore the synthetic, read-only public experience at **`/demo`**; the owner's real workspace remains separately password protected.

## Completion features

- Explainable job ranking with resume skill matches and gaps
- Application pipeline, notes, follow-up reminders and duplicate-safe capture
- Tailored cover-letter drafts and role-specific interview preparation
- Approval-gated Gmail and Google Calendar execution with audit history
- Career preferences, notifications, activity timeline and weekly command brief
- Resume versioning and CSV application export
- India-wide remote/hybrid, experience, freshness, location and salary filters
- Duplicate and expired-role detection with deterministic quality scoring
- Resume suggestions, recruiter email copilot and skill-gap roadmap
- Synthetic public demo with zero access to private APIs, Gmail or Calendar
- PostgreSQL migration registry and secret-free JSON backup/export
- Password login, signed bearer tokens, API-key compatibility and rate limiting
- Health/metrics endpoints, Docker/NGINX Render deployment and automated CI

## Portfolio links

- Public demo: `https://jarvis-career-os.onrender.com/demo`
- Private workspace: `https://jarvis-career-os.onrender.com/`
- Health: `https://jarvis-career-os.onrender.com/api/health`

The public demo contains synthetic data and is read-only. It performs no private API requests. Gmail, Calendar, OAuth tokens and personal resume data exist only behind the private access boundary.

## Architecture

```text
WhatsApp Web (optional) → Node bridge → FastAPI orchestrator
                                      ├─ Job agent
                                      ├─ Email draft agent
                                      ├─ Calendar agent
                                      ├─ Expense agent → SQLite
                                      └─ Reminder agent → SQLite
                                             ↓
                                      Storage → SQLite or Neon PostgreSQL
```

## Quick start

1. Create a virtual environment and install dependencies: `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and set only the integrations you need.
3. Start the API: `uvicorn app.main:app --reload --port 8000`.
4. Open `http://localhost:8000/docs` and call `POST /process`, or run `pytest`.
5. For WhatsApp, run `npm install && npm start` inside `whatsapp-bridge`, then scan the QR code from WhatsApp Linked Devices.

## Sample messages

- `find data engineer jobs in Pune`
- `draft an email to my recruiter`
- `spent ₹250 on lunch`
- `remind me to submit assignment`
- `show my reminders`

## Live job search setup

1. Create a local `.env` file from `.env.example`.
2. Add your `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`; never commit or share them.
3. Restart the API and ask: `find data engineer jobs in Pune`.

Results are fetched from Adzuna and cached in SQLite for auditability. Recent cached records are available at `GET /jobs`.

## Resume-aware ranking

From the dashboard, use **Connect Resume** to upload a text-based PDF or TXT resume. JARVIS extracts supported Data Engineering skills locally, stores the profile in SQLite, and uses those skills to personalize the job-fit score. The raw resume never leaves the local API.

See `DEPLOYMENT.md` for the deployment and security runbook. A secret-free personal backup is available from `GET /backup/export.json`, or locally with `python scripts/export_backup.py`.

## Career intelligence workspace

The dashboard also provides:

- Explainable role-fit scoring, matched skills, and visible skill gaps.
- Saved application pipeline with recruiter/interview notes and follow-up dates.
- A tailored cover-letter draft for each captured role.
- Local resume-version snapshots and interview-conversion analytics.
- An integration control surface showing job-data, Gmail, and Calendar readiness.

Gmail and Calendar remain intentionally unavailable until Google OAuth is connected. Every external action continues through the Approval Queue first.

## Design decisions

- **Deterministic router first:** the system works without an LLM key and is easy to test. A Groq/Ollama classifier can be added behind `Orchestrator.route` without changing the API.
- **Portable persistence:** SQLite supports local development; Neon PostgreSQL provides durable production storage.
- **No brittle scraping by default:** add approved APIs or RSS feeds to the job agent instead of silently scraping job boards.
- **Human approval for real-world effects:** email and outbound messaging remain draft/approval workflows.
- **Audit trail:** approval creation and every approve/reject decision are stored locally and can be read from `GET /audit-logs`.

## Tests

Run `pytest`. CI also lints/builds the React dashboard and builds the production Docker image.

## Branding and disclaimer

JARVIS Career OS uses an original vector intelligence-core mark and an engineering HUD visual language. It is an independent portfolio project with no affiliation with Marvel, Iron Man, employers, or job platforms. Job availability, salary and fit scores are informational and should be independently verified.
