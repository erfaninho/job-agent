from datetime import datetime, timezone
from enum import StrEnum

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApplicationStatus(StrEnum):
    found = "found"
    analyzed = "analyzed"
    prepared = "prepared"
    needs_review = "needs_review"
    ready_to_apply = "ready_to_apply"
    applied = "applied"
    submitted = "submitted"
    follow_up_needed = "follow_up_needed"
    interview = "interview"
    rejected = "rejected"
    offer = "offer"
    archived = "archived"


class Job(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company: str = "Unknown company"
    title: str = "Unknown role"
    location: str | None = None
    remote_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    source: str = "manual"
    source_url: str | None = None
    description_text: str
    description_html_path: str | None = None
    description_hash: str = Field(index=True)
    date_found: datetime = Field(default_factory=utc_now)
    deadline: datetime | None = None
    status: str = ApplicationStatus.found.value
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Application(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(index=True, foreign_key="job.id")
    folder_path: str
    status: str = ApplicationStatus.found.value
    fit_score: float | None = None
    cv_tex_path: str | None = None
    cv_pdf_path: str | None = None
    cover_letter_path: str | None = None
    submitted_at: datetime | None = None
    follow_up_date: datetime | None = None
    notes: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GeneratedDocument(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    application_id: int = Field(index=True, foreign_key="application.id")
    document_type: str
    path: str
    model_name: str = "local-rules"
    created_at: datetime = Field(default_factory=utc_now)


class ApplicationEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    application_id: int | None = Field(default=None, index=True, foreign_key="application.id")
    event_type: str
    message: str
    created_at: datetime = Field(default_factory=utc_now)
