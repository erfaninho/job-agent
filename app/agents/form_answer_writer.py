from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.models.job_parser import ParsedJob
from app.models.profile import CandidateProfile
from app.services.model_provider import ModelProvider, ModelProviderError


class ApplicationQuestionType(StrEnum):
    why_this_role = "why_this_role"
    why_this_company = "why_this_company"
    tell_us_about_yourself = "tell_us_about_yourself"
    salary_expectation = "salary_expectation"
    notice_period = "notice_period"
    work_authorisation = "work_authorisation"
    visa_sponsorship = "visa_sponsorship"
    relocation = "relocation"
    experience_question = "experience_question"
    technical_stack_question = "technical_stack_question"
    availability = "availability"
    portfolio_link = "portfolio_link"
    unknown = "unknown"


SENSITIVE_TYPES = {
    ApplicationQuestionType.salary_expectation,
    ApplicationQuestionType.notice_period,
    ApplicationQuestionType.work_authorisation,
    ApplicationQuestionType.visa_sponsorship,
    ApplicationQuestionType.relocation,
    ApplicationQuestionType.availability,
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
    if "visa" in text or "sponsor" in text:
        return ApplicationQuestionType.visa_sponsorship
    if "work author" in text or "right to work" in text:
        return ApplicationQuestionType.work_authorisation
    if "relocat" in text:
        return ApplicationQuestionType.relocation
    if "start" in text or "available" in text:
        return ApplicationQuestionType.availability
    if any(term in text for term in ("github", "portfolio", "linkedin", "website")):
        return ApplicationQuestionType.portfolio_link
    if any(term in text for term in ("python", "django", "postgres", "redis", "technical")):
        return ApplicationQuestionType.technical_stack_question
    if "experience" in text or "describe" in text:
        return ApplicationQuestionType.experience_question
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


class ApplicationAnswerAgent:
    COMMON_QUESTIONS = (
        "Why this role?",
        "Why this company?",
        "Tell us about yourself.",
        "What are your salary expectations?",
        "What is your notice period?",
        "Do you have the right to work?",
        "Do you require visa sponsorship?",
        "Are you willing to relocate?",
        "When can you start?",
        "Describe your experience with the relevant technical stack.",
        "Portfolio/GitHub/LinkedIn links",
    )

    def __init__(self, provider: ModelProvider | None = None):
        self.provider = provider

    def generate_answers(
        self,
        parsed: ParsedJob,
        profile: CandidateProfile,
        questions: list[str] | None = None,
        approved_facts: list[str] | None = None,
    ) -> list[GeneratedAnswer]:
        labels = list(dict.fromkeys([*(questions or []), *parsed.questions_to_answer, *self.COMMON_QUESTIONS]))
        facts = approved_facts or [*profile.skills, *profile.experience, *profile.projects]
        return [self.generate_answer(label, parsed, profile, facts) for label in labels if label.strip()]

    def generate_answer(
        self, label: str, parsed: ParsedJob, profile: CandidateProfile, facts: list[str]
    ) -> GeneratedAnswer:
        question_type = classify_application_question(label)
        if self.provider is not None:
            try:
                data = self.provider.generate_json(
                    "Generate a truthful application answer. Use only provided approved facts. "
                    "Return JSON with keys answer, source_facts_used, confidence_score, risk_notes.",
                    (
                        f"Question: {label}\nQuestion type: {question_type.value}\n"
                        f"Job: {parsed.model_dump_json()}\nProfile: {profile.model_dump_json()}\n"
                        f"Approved facts: {facts}"
                    ),
                    {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string"},
                            "source_facts_used": {"type": "array", "items": {"type": "string"}},
                            "confidence_score": {"type": "number"},
                            "risk_notes": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                )
                return self._from_model_data(label, question_type, data)
            except (ModelProviderError, ValueError, TypeError):
                pass
        return build_generated_answer(label, self._fallback_answer(label, question_type, parsed, profile), facts)

    @staticmethod
    def _from_model_data(
        label: str, question_type: ApplicationQuestionType, data: dict[str, object]
    ) -> GeneratedAnswer:
        answer = str(data.get("answer") or "").strip()
        raw_source_facts = data.get("source_facts_used", [])
        raw_risk_notes = data.get("risk_notes", [])
        source_facts = [str(item) for item in raw_source_facts] if isinstance(raw_source_facts, list) else []
        risk_notes = [str(item) for item in raw_risk_notes] if isinstance(raw_risk_notes, list) else []
        raw_confidence: Any = data.get("confidence_score", 0.7)
        sensitive = question_type in SENSITIVE_TYPES
        return GeneratedAnswer(
            question_label=label,
            normalized_question_type=question_type.value,
            answer=answer,
            source_facts_used=source_facts,
            confidence_score=float(raw_confidence or 0.7),
            requires_user_review=sensitive,
            risk_notes=(["Manual confirmation required for sensitive answer."] if sensitive else []) + risk_notes,
            character_count=len(answer),
            word_count=len(answer.split()),
            created_at=datetime.now().isoformat(),
            auto_fill_allowed=not sensitive,
        )

    @staticmethod
    def _fallback_answer(
        label: str, question_type: ApplicationQuestionType, parsed: ParsedJob, profile: CandidateProfile
    ) -> str:
        role = parsed.title or "this role"
        company = parsed.company or "the company"
        skills = ", ".join(profile.skills[:5]) or "my approved skills and experience"
        if question_type == ApplicationQuestionType.why_this_role:
            return f"I am interested in {role} because it matches my approved background in {skills} and the responsibilities described in the job post."
        if question_type == ApplicationQuestionType.why_this_company:
            return f"I am interested in {company} because the role appears to offer practical product work where my approved experience can contribute. I do not want to invent company-specific details beyond the job post."
        if question_type == ApplicationQuestionType.tell_us_about_yourself:
            return f"I am a software developer with experience reflected in my approved profile, including {skills}. I enjoy building reliable, user-focused systems and learning quickly."
        if question_type == ApplicationQuestionType.portfolio_link:
            return "LinkedIn: {linkedin} GitHub: {github} Portfolio: {portfolio}".format(
                linkedin=profile.linkedin_url,
                github=profile.github_url,
                portfolio=profile.portfolio_url,
            ).strip()
        if question_type in SENSITIVE_TYPES:
            return "Suggested answer requires manual confirmation from the user before use."
        if question_type == ApplicationQuestionType.technical_stack_question:
            return f"My relevant technical background includes {skills}, where supported by my CV and approved profile."
        if question_type == ApplicationQuestionType.experience_question:
            return "My relevant experience should be answered using the approved CV/profile facts and tailored to the job requirements."
        return f"This answer should be reviewed manually for: {label}"
