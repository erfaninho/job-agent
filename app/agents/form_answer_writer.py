from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum


class ApplicationQuestionType(StrEnum):
    why_this_role = "why_this_role"
    why_this_company = "why_this_company"
    tell_us_about_yourself = "tell_us_about_yourself"
    salary_expectation = "salary_expectation"
    notice_period = "notice_period"
    work_authorisation = "work_authorisation"
    availability_start_date = "availability_start_date"
    unknown = "unknown"


SENSITIVE_TYPES = {
    ApplicationQuestionType.salary_expectation,
    ApplicationQuestionType.notice_period,
    ApplicationQuestionType.work_authorisation,
    ApplicationQuestionType.availability_start_date,
}


@dataclass
class GeneratedAnswer:
    question_label: str
    normalized_question_type: str
    answer: str
    source_facts_used: list[str]
    confidence_score: float
    requires_user_review: bool
    risk_notes: list[str]
    character_count: int
    word_count: int
    created_at: str
    auto_fill_allowed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def classify_application_question(label: str, helper_text: str | None = None) -> ApplicationQuestionType:
    text = f"{label} {helper_text or ''}".lower()
    if "why" in text and "role" in text:
        return ApplicationQuestionType.why_this_role
    if "why" in text and ("company" in text or "joining" in text or "us" in text):
        return ApplicationQuestionType.why_this_company
    if "tell us about yourself" in text or "introduce yourself" in text:
        return ApplicationQuestionType.tell_us_about_yourself
    if "salary" in text:
        return ApplicationQuestionType.salary_expectation
    if "notice" in text:
        return ApplicationQuestionType.notice_period
    if "work author" in text or "visa" in text or "sponsor" in text:
        return ApplicationQuestionType.work_authorisation
    if "start" in text or "available" in text:
        return ApplicationQuestionType.availability_start_date
    return ApplicationQuestionType.unknown


def build_generated_answer(label: str, base_answer: str, facts: list[str]) -> GeneratedAnswer:
    question_type = classify_application_question(label)
    sensitive = question_type in SENSITIVE_TYPES
    answer = base_answer.strip()
    return GeneratedAnswer(
        question_label=label,
        normalized_question_type=question_type.value,
        answer=answer,
        source_facts_used=facts,
        confidence_score=0.75 if question_type != ApplicationQuestionType.unknown else 0.35,
        requires_user_review=sensitive,
        risk_notes=["Manual confirmation required for sensitive answer."] if sensitive else [],
        character_count=len(answer),
        word_count=len(answer.split()),
        created_at=datetime.now().isoformat(),
        auto_fill_allowed=not sensitive,
    )
