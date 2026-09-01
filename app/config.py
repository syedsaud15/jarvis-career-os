from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_path: Path
    timezone: str
    bridge_url: str
    groq_api_key: str | None
    groq_model: str
    adzuna_app_id: str | None
    adzuna_app_key: str | None
    adzuna_country: str
    api_key: str | None
    google_client_id: str | None
    google_client_secret: str | None
    google_redirect_uri: str


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        database_path=Path(os.getenv("JARVIS_DB_PATH", "data/jarvis.db")),
        timezone=os.getenv("JARVIS_TIMEZONE", "Asia/Kolkata"),
        bridge_url=os.getenv("BRIDGE_URL", "http://localhost:3000"),
        groq_api_key=os.getenv("GROQ_API_KEY") or None,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        adzuna_app_id=os.getenv("ADZUNA_APP_ID") or None,
        adzuna_app_key=os.getenv("ADZUNA_APP_KEY") or None,
        adzuna_country=os.getenv("ADZUNA_COUNTRY", "in").lower(),
        api_key=os.getenv("JARVIS_API_KEY") or None,
        google_client_id=os.getenv("GOOGLE_CLIENT_ID") or None,
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET") or None,
        google_redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/integrations/google/callback"),
    )
