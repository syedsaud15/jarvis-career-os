from __future__ import annotations

from app.agents import CalendarAgent, EmailAgent, ExpenseAgent, JobAgent, ReminderAgent
from app.approvals import ApprovalService
from app.config import Settings, get_settings
from app.memory import Memory
from app.store import Store
from app.types import Intent, ProcessResponse


class Orchestrator:
    def __init__(self, store: Store, settings: Settings | None = None):
        settings = settings or get_settings()
        self.memory = Memory(store)
        self.approvals = ApprovalService(store)
        self.agents = {
            Intent.JOB_SEARCH: JobAgent(store, settings), Intent.EMAIL: EmailAgent(),
            Intent.CALENDAR: CalendarAgent(store), Intent.EXPENSE: ExpenseAgent(store),
            Intent.REMINDER: ReminderAgent(store),
        }

    @staticmethod
    def route(message: str) -> Intent:
        text = message.lower()
        if any(w in text for w in ("job", "hiring", "vacancy", "opening")): return Intent.JOB_SEARCH
        if any(w in text for w in ("email", "mail", "inbox")): return Intent.EMAIL
        if any(w in text for w in ("calendar", "meeting", "schedule", "event")): return Intent.CALENDAR
        if any(w in text for w in ("spent", "expense", "paid", "₹", "inr", "rs.")): return Intent.EXPENSE
        if any(w in text for w in ("remind", "reminder", "task", "todo")): return Intent.REMINDER
        return Intent.GENERAL

    def process(self, message: str, sender: str) -> ProcessResponse:
        intent = self.route(message)
        self.memory.remember(sender, message)
        if intent is Intent.GENERAL:
            context = self.memory.recall(sender, message)
            suffix = f" I remember: {context[0]}" if context else ""
            return ProcessResponse(reply="I can help with jobs, email drafts, calendar, expenses, and reminders." + suffix, intent=intent)
        reply, actions = self.agents[intent].handle(message, sender)
        text = message.lower()
        if intent is Intent.EMAIL and "send" in text:
            approval_id = self.approvals.create(sender, "email.send", "Send the requested email after Gmail is connected.")
            reply += f"\n\nApproval #{approval_id} created. Review it in the dashboard before any send action."
            actions.append("approval_requested")
        if intent is Intent.CALENDAR and any(word in text for word in ("add", "create", "schedule", "book")):
            approval_id = self.approvals.create(sender, "calendar.create", "Create the requested calendar event after Google Calendar is connected.")
            reply += f"\n\nApproval #{approval_id} created. Review it in the dashboard before any event is created."
            actions.append("approval_requested")
        return ProcessResponse(reply=reply, intent=intent, actions=actions)
