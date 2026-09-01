from __future__ import annotations

import re
from datetime import date
from app.store import Store


class ExpenseAgent:
    CATEGORIES = {
        "food": ("food", "restaurant", "swiggy", "zomato", "cafe"),
        "travel": ("uber", "ola", "metro", "fuel", "travel"),
        "subscriptions": ("netflix", "spotify", "subscription"),
    }

    def __init__(self, store: Store):
        self.store = store

    def _category(self, text: str) -> str:
        lower = text.lower()
        return next((name for name, words in self.CATEGORIES.items() if any(w in lower for w in words)), "other")

    def handle(self, message: str, sender: str) -> tuple[str, list[str]]:
        match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)", message, re.I)
        if not match:
            return "Send an expense like `spent ₹250 on lunch` and I will record it locally.", []
        amount = float(match.group(1))
        category = self._category(message)
        with self.store.connection() as con:
            con.execute(
                "INSERT INTO expenses(sender, amount, category, note, occurred_on) VALUES (?, ?, ?, ?, ?)",
                (sender, amount, category, message, date.today().isoformat()),
            )
        return f"Recorded ₹{amount:.2f} under {category}.", ["expense_recorded"]

