from __future__ import annotations

from datetime import datetime
from app.store import Store


class CalendarAgent:
    def __init__(self, store: Store):
        self.store = store

    def handle(self, message: str, sender: str) -> tuple[str, list[str]]:
        if message.lower().startswith(("list", "show", "what")):
            with self.store.connection() as con:
                rows = con.execute(
                    "SELECT title, starts_at FROM events WHERE sender=? ORDER BY starts_at LIMIT 10", (sender,)
                ).fetchall()
            if not rows:
                return "Your local calendar is empty.", []
            return "Upcoming local events:\n" + "\n".join(f"- {r['starts_at']}: {r['title']}" for r in rows), []
        return (
            "I can create local calendar events after Google Calendar OAuth is connected. "
            "Use: calendar add <title> at YYYY-MM-DD HH:MM.",
            ["calendar_connection_needed"],
        )

