from __future__ import annotations

from app.store import Store


class Memory:
    """Small, inspectable local memory. Chroma can be added later without API changes."""
    def __init__(self, store: Store):
        self.store = store

    def remember(self, sender: str, text: str) -> None:
        with self.store.connection() as con:
            con.execute("INSERT INTO memories(sender, text) VALUES (?, ?)", (sender, text))

    def recall(self, sender: str, query: str, limit: int = 3) -> list[str]:
        tokens = [word for word in query.lower().split() if len(word) > 3][:3]
        if not tokens:
            return []
        pattern = "%" + "%".join(tokens) + "%"
        with self.store.connection() as con:
            rows = con.execute(
                "SELECT text FROM memories WHERE sender=? AND lower(text) LIKE ? "
                "ORDER BY id DESC LIMIT ?", (sender, pattern, limit)
            ).fetchall()
        return [row["text"] for row in rows]

