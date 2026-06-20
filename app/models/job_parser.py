from pydantic import BaseModel, Field


class ParsedJob(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    remote_type: str | None = None
    salary_range: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    experience_level: str | None = None
    keywords: list[str] = Field(default_factory=list)
    application_deadline: str | None = None
    red_flags: list[str] = Field(default_factory=list)
    questions_to_answer: list[str] = Field(default_factory=list)
