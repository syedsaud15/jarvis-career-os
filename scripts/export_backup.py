"""Export a private JARVIS backup without exposing OAuth tokens or secrets."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.store import Store


def build_backup(sender: str = "dashboard-user") -> dict[str, object]:
    settings = get_settings()
    store = Store(settings.database_path, settings.database_url)
    store.initialize()
    with store.connection() as con:
        applications = [dict(row) for row in con.execute(
            "SELECT applications.id,applications.status,applications.created_at,applications.updated_at,job_listings.title,job_listings.company,job_listings.location,job_listings.redirect_url FROM applications JOIN job_listings ON job_listings.id=applications.job_listing_id WHERE applications.sender=? ORDER BY applications.id DESC",
            (sender,),
        ).fetchall()]
        return {
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "applications": applications,
            "profile": [dict(row) for row in con.execute("SELECT sender,resume_text,skills_json,updated_at FROM career_profiles WHERE sender=?", (sender,)).fetchall()],
            "settings": [dict(row) for row in con.execute("SELECT * FROM user_settings WHERE sender=?", (sender,)).fetchall()],
        }


if __name__ == "__main__":
    destination = Path(f"jarvis-backup-{datetime.now(timezone.utc).date().isoformat()}.json")
    destination.write_text(json.dumps(build_backup(), default=str, indent=2), encoding="utf-8")
    print(f"Private backup written to {destination.resolve()}")
