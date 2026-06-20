from app.agents.form_answer_writer import (
    ApplicationQuestionType,
    build_generated_answer,
    classify_application_question,
)
from app.agents.job_parser import JobParserAgent
from app.models.profile import CandidateProfile
from app.services.scoring_service import ScoringService


def test_parser_and_scoring() -> None:
    parsed = JobParserAgent().parse(
        "Company: Acme\nRole: Backend Developer\nLocation: Remote\nRequired Python Django SQL"
    )
    profile = CandidateProfile(skills=["Python", "Django", "SQL"], experience=["Backend work"])
    fit = ScoringService().score(parsed, profile)
    assert parsed.company == "Acme"
    assert "Python" in parsed.required_skills
    assert fit.score >= 75
    assert fit.recommendation == "apply"


def test_question_classification_and_sensitive_review() -> None:
    assert classify_application_question("Why do you want this role?") == ApplicationQuestionType.why_this_role
    answer = build_generated_answer("What are your salary expectations?", "Open to discuss.", [])
    assert answer.requires_user_review is True
    assert answer.auto_fill_allowed is False
