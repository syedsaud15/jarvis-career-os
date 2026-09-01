from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Intent(str, Enum):
    EMAIL = "EMAIL"
    CALENDAR = "CALENDAR"
    JOB_SEARCH = "JOB_SEARCH"
    EXPENSE = "EXPENSE"
    REMINDER = "REMINDER"
    GENERAL = "GENERAL"


class ProcessRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    sender: str = Field(default="local-user", max_length=128)


class ProcessResponse(BaseModel):
    reply: str
    intent: Intent
    actions: list[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(APPROVED|REJECTED)$")
    note: str | None = Field(default=None, max_length=500)


class ApplicationCreate(BaseModel):
    job_listing_id: int = Field(gt=0)
    sender: str = Field(default="dashboard-user", max_length=128)


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(pattern="^(SAVED|APPLIED|INTERVIEW|REJECTED)$")


class ProfileTextUpdate(BaseModel):
    resume_text: str = Field(min_length=20, max_length=100000)
    sender: str = Field(default="dashboard-user", max_length=128)


class ApplicationNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class FollowUpCreate(BaseModel):
    due_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class ResumeVersionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    resume_text: str = Field(min_length=20, max_length=100000)
    sender: str = Field(default="dashboard-user", max_length=128)


class EmailApprovalRequest(BaseModel):
    to: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)
    sender: str = Field(default="dashboard-user", max_length=128)


class CalendarApprovalRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    starts_at: str = Field(min_length=16, max_length=40)
    ends_at: str = Field(min_length=16, max_length=40)
    sender: str = Field(default="dashboard-user", max_length=128)


class UserRegister(BaseModel):
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=12, max_length=200)


class UserLogin(UserRegister):
    pass


class UserSettingsUpdate(BaseModel):
    display_name: str = Field(default="Syed Saud", min_length=1, max_length=100)
    target_role: str = Field(default="Data Engineer", min_length=1, max_length=120)
    target_location: str = Field(default="Pune", min_length=1, max_length=120)
    minimum_fit: int = Field(default=45, ge=0, le=100)
    weekly_digest: bool = True
    follow_up_reminders: bool = True
