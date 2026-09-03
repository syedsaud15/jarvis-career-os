"""Calendar-week career trends, calculated without database-specific date functions."""
import json
from datetime import datetime, timedelta, timezone


def utc_date(value):
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return (parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)).date()


def weekly_trends(store, sender, now=None):
    today = (now or datetime.now(timezone.utc)).date()
    monday = today - timedelta(days=today.weekday())
    weeks = [{"week_start": (monday - timedelta(weeks=i)).isoformat(), "captured": 0,
              "applied": 0, "interviews": 0, "rejected": 0} for i in reversed(range(8))]
    by_week = {row["week_start"]: row for row in weeks}
    with store.connection() as con:
        captures = con.execute("SELECT created_at FROM applications WHERE sender=?", (sender,)).fetchall()
        events = con.execute("SELECT details,created_at FROM audit_logs WHERE sender=? AND event_type='application.status_changed' ORDER BY created_at", (sender,)).fetchall()
    def bucket(value):
        day = utc_date(value)
        return by_week.get((day - timedelta(days=day.weekday())).isoformat()) if day <= today else None
    for row in captures:
        week = bucket(row["created_at"])
        if week is not None:
            week["captured"] += 1
    for row in events:
        try:
            stage = {"APPLIED": "applied", "INTERVIEW": "interviews", "REJECTED": "rejected"}.get(json.loads(row["details"])["to"])
        except (ValueError, KeyError, TypeError):
            continue
        week = bucket(row["created_at"])
        if week is not None and stage:
            week[stage] += 1
    return {"weeks": weeks, "timezone": "UTC", "current_week_partial": True,
            "coverage_note": "Captures use saved dates. Stage changes are counted only since history tracking was added; earlier transitions are not reconstructed. Repeat transitions count as separate events."}
