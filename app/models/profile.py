from pathlib import Path

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    work_authorisation: str = ""
    notice_period: str = ""
    salary_expectation: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    master_cv_tex_path: Path | None = None


class AnswerBankItem(BaseModel):
    key: str
    base_answer: str = ""
    tone: str = "professional_friendly"
    requires_manual_confirmation: bool = False
    can_be_tailored: bool = True
    approved_facts_only: bool = True


DEFAULT_ANSWER_BANK: list[AnswerBankItem] = [
    AnswerBankItem(key="why_this_role"),
    AnswerBankItem(key="why_this_company"),
    AnswerBankItem(key="tell_us_about_yourself"),
    AnswerBankItem(key="salary_expectation", requires_manual_confirmation=True),
    AnswerBankItem(key="notice_period", requires_manual_confirmation=True),
    AnswerBankItem(key="work_authorisation", requires_manual_confirmation=True),
    AnswerBankItem(key="visa_sponsorship", requires_manual_confirmation=True),
    AnswerBankItem(key="remote_work_preference"),
    AnswerBankItem(key="relocation_preference", requires_manual_confirmation=True),
    AnswerBankItem(key="availability_start_date", requires_manual_confirmation=True),
    AnswerBankItem(key="preferred_work_style"),
]
