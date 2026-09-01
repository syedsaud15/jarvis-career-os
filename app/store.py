from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Store:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def initialize(self) -> None:
        with self.connection() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                  id INTEGER PRIMARY KEY, sender TEXT NOT NULL, text TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS reminders (
                  id INTEGER PRIMARY KEY, sender TEXT NOT NULL, task TEXT NOT NULL,
                  due_at TEXT, completed INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS expenses (
                  id INTEGER PRIMARY KEY, sender TEXT NOT NULL, amount REAL NOT NULL,
                  category TEXT NOT NULL, note TEXT NOT NULL,
                  occurred_on TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY, sender TEXT NOT NULL, title TEXT NOT NULL,
                  starts_at TEXT NOT NULL, ends_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS approvals (
                  id INTEGER PRIMARY KEY, sender TEXT NOT NULL, tool_name TEXT NOT NULL,
                  summary TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING',
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  resolved_at TEXT, decision_note TEXT
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                  id INTEGER PRIMARY KEY,
                  sender TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  entity_type TEXT NOT NULL,
                  entity_id INTEGER,
                  details TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS job_listings (
                  id INTEGER PRIMARY KEY,
                  source TEXT NOT NULL,
                  source_id TEXT NOT NULL,
                  query TEXT NOT NULL,
                  title TEXT NOT NULL,
                  company TEXT,
                  location TEXT,
                  description TEXT,
                  salary_min REAL,
                  salary_max REAL,
                  redirect_url TEXT,
                  posted_at TEXT,
                  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  UNIQUE(source, source_id)
                );
                CREATE TABLE IF NOT EXISTS applications (
                  id INTEGER PRIMARY KEY,
                  sender TEXT NOT NULL,
                  job_listing_id INTEGER NOT NULL,
                  status TEXT NOT NULL DEFAULT 'SAVED',
                  notes TEXT,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  UNIQUE(sender, job_listing_id),
                  FOREIGN KEY(job_listing_id) REFERENCES job_listings(id)
                );
                CREATE TABLE IF NOT EXISTS career_profiles (
                  sender TEXT PRIMARY KEY,
                  resume_text TEXT NOT NULL,
                  skills_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS application_notes (
                  id INTEGER PRIMARY KEY,
                  application_id INTEGER NOT NULL,
                  body TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(application_id) REFERENCES applications(id)
                );
                CREATE TABLE IF NOT EXISTS follow_ups (
                  id INTEGER PRIMARY KEY,
                  application_id INTEGER NOT NULL,
                  due_on TEXT NOT NULL,
                  completed INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(application_id) REFERENCES applications(id)
                );
                CREATE TABLE IF NOT EXISTS resume_versions (
                  id INTEGER PRIMARY KEY,
                  sender TEXT NOT NULL,
                  label TEXT NOT NULL,
                  resume_text TEXT NOT NULL,
                  skills_json TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS oauth_states (
                  state TEXT PRIMARY KEY, sender TEXT NOT NULL, expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS oauth_connections (
                  provider TEXT NOT NULL, sender TEXT NOT NULL, encrypted_token TEXT NOT NULL,
                  connected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY(provider, sender)
                );
                CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS user_settings (
                  sender TEXT PRIMARY KEY,
                  display_name TEXT NOT NULL DEFAULT 'Syed Saud',
                  target_role TEXT NOT NULL DEFAULT 'Data Engineer',
                  target_location TEXT NOT NULL DEFAULT 'Pune',
                  minimum_fit INTEGER NOT NULL DEFAULT 45,
                  weekly_digest INTEGER NOT NULL DEFAULT 1,
                  follow_up_reminders INTEGER NOT NULL DEFAULT 1,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_notes_application ON application_notes(application_id, id DESC);
                CREATE INDEX IF NOT EXISTS idx_follow_ups_application ON follow_ups(application_id, completed, due_on);
                CREATE INDEX IF NOT EXISTS idx_resume_versions_sender ON resume_versions(sender, id DESC);
                CREATE INDEX IF NOT EXISTS idx_approvals_status_id ON approvals(status, id DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id, id DESC);
                CREATE INDEX IF NOT EXISTS idx_job_listings_query ON job_listings(query, id DESC);
                CREATE INDEX IF NOT EXISTS idx_applications_sender_status ON applications(sender, status, id DESC);
                """
            )
            columns = {row["name"] for row in con.execute("PRAGMA table_info(approvals)").fetchall()}
            if "action_payload" not in columns:
                con.execute("ALTER TABLE approvals ADD COLUMN action_payload TEXT")
