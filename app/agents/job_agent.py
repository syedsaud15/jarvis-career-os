from __future__ import annotations

import re
from typing import Any

import httpx

from app.config import Settings
from app.store import Store


class JobAgent:
    """Fetches permitted listings from Adzuna and retains a local, inspectable cache."""

    def __init__(self, store: Store, settings: Settings) -> None:
        self.store = store
        self.settings = settings

    @staticmethod
    def _search_terms(message: str) -> tuple[str, str | None]:
        query = re.sub(r"\b(find|search|show|latest|jobs?|vacancies|openings?)\b", "", message, flags=re.I)
        location_match = re.search(r"\s+in\s+(.+)$", query, flags=re.I)
        location = location_match.group(1).strip(" :,-") if location_match else None
        if location_match:
            query = query[:location_match.start()]
        return query.strip(" :,-") or "data engineer", location

    def _save(self, query: str, jobs: list[dict[str, Any]]) -> None:
        with self.store.connection() as con:
            for job in jobs:
                con.execute(
                    "INSERT INTO job_listings(source, source_id, query, title, company, location, description, "
                    "salary_min, salary_max, redirect_url, posted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(source, source_id) DO UPDATE SET query=excluded.query, title=excluded.title, "
                    "company=excluded.company, location=excluded.location, description=excluded.description, "
                    "salary_min=excluded.salary_min, salary_max=excluded.salary_max, redirect_url=excluded.redirect_url, "
                    "posted_at=excluded.posted_at, fetched_at=CURRENT_TIMESTAMP",
                    (
                        "adzuna", str(job["id"]), query, job.get("title", "Untitled role"),
                        job.get("company", {}).get("display_name"), job.get("location", {}).get("display_name"),
                        job.get("description"), job.get("salary_min"), job.get("salary_max"),
                        job.get("redirect_url"), job.get("created"),
                    ),
                )

    def handle(self, message: str, sender: str) -> tuple[str, list[str]]:
        if not self.settings.adzuna_app_id or not self.settings.adzuna_app_key:
            return (
                "Live job search is ready to connect. Add ADZUNA_APP_ID and ADZUNA_APP_KEY to your local .env file, "
                "then restart the API.",
                ["job_provider_not_configured"],
            )
        query, location = self._search_terms(message)
        url = f"https://api.adzuna.com/v1/api/jobs/{self.settings.adzuna_country}/search/1"
        params = {
            "app_id": self.settings.adzuna_app_id,
            "app_key": self.settings.adzuna_app_key,
            "what": query,
            "results_per_page": 10,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location
        try:
            response = httpx.get(url, params=params, headers={"Accept": "application/json"}, timeout=30.0)
            response.raise_for_status()
            jobs = response.json().get("results", [])
        except (httpx.HTTPError, ValueError):
            return "I could not retrieve live jobs right now. Your request was not lost; please try again shortly.", ["job_search_failed"]

        self._save(query, jobs)
        if not jobs:
            return f"No live matches found for {query}. Try a broader role or location.", ["job_search_completed"]
        summaries = "\n".join(
            f"- {job.get('title', 'Untitled role')} — {job.get('company', {}).get('display_name', 'Company not listed')} "
            f"({job.get('location', {}).get('display_name', 'Location not listed')})"
            for job in jobs[:5]
        )
        return f"Found {len(jobs)} live listings for {query}:\n{summaries}", ["job_search_completed", "job_listings_cached"]
