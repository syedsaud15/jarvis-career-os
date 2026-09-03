"""Portable career-data backups. Credentials and executable approvals are excluded."""
import json
from datetime import datetime, timezone
from pathlib import Path

from app.store import Store

TABLES = {
    "job_listings": "id source source_id query title company location description salary_min salary_max redirect_url posted_at fetched_at",
    "career_profiles": "sender resume_text skills_json updated_at",
    "user_settings": "sender display_name target_role target_location minimum_fit weekly_digest follow_up_reminders updated_at",
    "applications": "id sender job_listing_id status notes created_at updated_at",
    "application_notes": "id application_id body created_at",
    "follow_ups": "id application_id due_on completed created_at",
    "resume_versions": "id sender label resume_text skills_json created_at",
    "audit_logs": "id sender event_type entity_type entity_id details created_at",
}


def build_backup(store, sender="dashboard-user"):
    data = {}
    with store.connection() as con:
        con.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY" if store.database_url else "BEGIN")
        for table, columns in TABLES.items():
            if table == "job_listings":
                where = "id IN (SELECT job_listing_id FROM applications WHERE sender=?)"
            elif table in {"application_notes", "follow_ups"}:
                where = "application_id IN (SELECT id FROM applications WHERE sender=?)"
            elif table == "audit_logs":
                where = "sender=? AND event_type IN ('application.created','application.status_changed')"
            else:
                where = "sender=?"
            data[table] = [dict(row) for row in con.execute(
                f"SELECT {','.join(columns.split())} FROM {table} WHERE {where}", (sender,)
            ).fetchall()]
    return {"version": 2, "sender": sender, "exported_at": datetime.now(timezone.utc).isoformat(),
            "scope": "career data only; reconnect Google separately; uncaptured jobs and action history excluded",
            "tables": data}


def restore_backup(payload, destination):
    """Restore only to a NEW SQLite file, never a configured/production database."""
    if payload.get("version") != 2 or set(payload.get("tables", {})) != set(TABLES):
        raise ValueError("Expected a version 2 career backup with all tables")
    for table, rows in payload["tables"].items():
        if not isinstance(rows, list) or any(set(row) != set(TABLES[table].split()) for row in rows):
            raise ValueError(f"Invalid backup columns for {table}")
    destination = Path(destination).resolve()
    with destination.open("xb"):
        pass
    restored = Store(destination)
    restored.initialize()
    with restored.connection() as con:
        con.execute("PRAGMA foreign_keys=ON")
        for table, columns in TABLES.items():
            names = columns.split()
            for row in payload["tables"][table]:
                con.execute(f"INSERT INTO {table} ({','.join(names)}) VALUES ({','.join('?' for _ in names)})",
                            tuple(row[name] for name in names))
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Database integrity check failed")
    return restored


def write_backup(payload, destination):
    with Path(destination).open("x", encoding="utf-8") as output:
        json.dump(payload, output, default=str, indent=2)
