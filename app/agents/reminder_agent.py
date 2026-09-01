from __future__ import annotations

from app.store import Store


class ReminderAgent:
    def __init__(self, store: Store):
        self.store = store

    def handle(self, message: str, sender: str) -> tuple[str, list[str]]:
        lowered = message.lower()
        if lowered.startswith(("list", "show")):
            with self.store.connection() as con:
                rows = con.execute(
                    "SELECT id, task, due_at FROM reminders WHERE sender=? AND completed=0 ORDER BY id DESC", (sender,)
                ).fetchall()
            if not rows:
                return "You have no open reminders.", []
            return "Open reminders:\n" + "\n".join(f"{r['id']}. {r['task']}" for r in rows), []
        task = message.replace("remind me", "", 1).strip(" :") or message
        with self.store.connection() as con:
            cur = con.execute("INSERT INTO reminders(sender, task) VALUES (?, ?)", (sender, task))
        return f"Reminder #{cur.lastrowid} saved: {task}", ["reminder_created"]

