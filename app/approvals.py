from __future__ import annotations

import json
from app.store import Store


class ApprovalService:
    def __init__(self, store: Store):
        self.store = store

    def create(self, sender: str, tool_name: str, summary: str, payload: dict[str, object] | None = None) -> int:
        with self.store.connection() as con:
            cursor = con.execute(
                "INSERT INTO approvals(sender, tool_name, summary, action_payload) VALUES (?, ?, ?, ?)",
                (sender, tool_name, summary, json.dumps(payload or {})),
            )
            approval_id = int(cursor.lastrowid)
            con.execute(
                "INSERT INTO audit_logs(sender, event_type, entity_type, entity_id, details) "
                "VALUES (?, 'approval.created', 'approval', ?, ?)",
                (sender, approval_id, f"Approval requested for {tool_name}"),
            )
            return approval_id

    def list(self, status: str = "PENDING", sender: str | None = None) -> list[dict[str, object]]:
        with self.store.connection() as con:
            query = "SELECT id, sender, tool_name, summary, status, created_at, resolved_at, decision_note FROM approvals WHERE status=?"
            params: tuple[object, ...] = (status.upper(),)
            if sender:
                query += " AND sender=?"
                params += (sender,)
            rows = con.execute(query + " ORDER BY id DESC", params).fetchall()
        return [dict(row) for row in rows]

    def decide(self, approval_id: int, decision: str, note: str | None = None) -> dict[str, object] | None:
        normalized = decision.upper()
        if normalized not in {"APPROVED", "REJECTED"}:
            raise ValueError("Decision must be APPROVED or REJECTED")
        with self.store.connection() as con:
            cursor = con.execute(
                "UPDATE approvals SET status=?, resolved_at=CURRENT_TIMESTAMP, decision_note=? "
                "WHERE id=? AND status='PENDING'", (normalized, note, approval_id),
            )
            if cursor.rowcount == 0:
                return None
            row = con.execute(
                "SELECT id, sender, tool_name, summary, status, created_at, resolved_at, decision_note, action_payload "
                "FROM approvals WHERE id=?", (approval_id,)
            ).fetchone()
            if row:
                con.execute(
                    "INSERT INTO audit_logs(sender, event_type, entity_type, entity_id, details) "
                    "VALUES (?, ?, 'approval', ?, ?)",
                    (row["sender"], f"approval.{normalized.lower()}", approval_id, f"Approval {normalized.lower()}"),
                )
        return dict(row) if row else None

    def audit_log(self, limit: int = 50, sender: str | None = None) -> list[dict[str, object]]:
        with self.store.connection() as con:
            query = "SELECT id, sender, event_type, entity_type, entity_id, details, created_at FROM audit_logs"
            params: tuple[object, ...]
            if sender:
                query += " WHERE sender=?"
                params = (sender, limit)
            else:
                params = (limit,)
            rows = con.execute(query + " ORDER BY id DESC LIMIT ?", params).fetchall()
        return [dict(row) for row in rows]
