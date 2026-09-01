from __future__ import annotations


class EmailAgent:
    def handle(self, message: str, sender: str) -> tuple[str, list[str]]:
        return (
            "Email actions are draft-only until Gmail OAuth is connected. "
            "Tell me the recipient and what you want to say, and I will prepare a draft for approval.",
            ["email_draft_only"],
        )

