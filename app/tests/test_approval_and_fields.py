import json
from pathlib import Path

from app.config import Settings
from app.models.application import Application
from app.services.application_service import ApplicationService
from app.services.database import DatabaseService
from app.services.form_field_detector import FieldSafety, FormFieldDetector


def test_answer_approval_decisions_and_edits() -> None:
    generated = [
        {
            "question_label": "Why this role?",
            "answer": "Good answer",
            "requires_user_review": False,
            "auto_fill_allowed": True,
        },
        {
            "question_label": "Salary?",
            "answer": "100",
            "requires_user_review": True,
            "auto_fill_allowed": False,
        },
        {
            "question_label": "Unsupported",
            "answer": "I led a team of 50",
            "requires_user_review": False,
            "auto_fill_allowed": True,
            "unsupported_claims": ["leadership"],
        },
        {
            "question_label": "Edit me",
            "answer": "Risky",
            "requires_user_review": False,
            "auto_fill_allowed": True,
            "risk_notes": ["risky"],
        },
    ]
    approved = ApplicationService.review_generated_answers(
        generated,
        {
            "Why this role?": "approve",
            "Salary?": "skip",
            "Unsupported": "approve",
            "Edit me": "edit",
        },
        {"Edit me": "Edited safe answer"},
    )
    assert [answer["question_label"] for answer in approved] == ["Why this role?", "Edit me"]
    assert approved[1]["answer"] == "Edited safe answer"


def test_sensitive_answers_are_never_auto_approved() -> None:
    approved = ApplicationService.review_generated_answers(
        [
            {
                "question_label": "Work authorization",
                "answer": "Yes",
                "requires_user_review": True,
                "auto_fill_allowed": False,
            }
        ],
        {},
        {},
    )
    assert approved == []


def test_approve_answers_writes_review_status(tmp_path: Path) -> None:
    settings = Settings(
        STORAGE_DIR=tmp_path / "storage",
        DATABASE_URL=f"sqlite:///{tmp_path / 'job_agent.db'}",
    )
    database = DatabaseService(settings)
    database.init_db()
    folder = tmp_path / "application"
    app_dir = folder / "04_application"
    app_dir.mkdir(parents=True)
    (app_dir / "application_answers.generated.json").write_text(
        json.dumps(
            [
                {
                    "question_label": "Why this role?",
                    "answer": "Good",
                    "requires_user_review": False,
                    "auto_fill_allowed": True,
                }
            ]
        ),
        encoding="utf-8",
    )
    (app_dir / "submission_review.md").write_text("# Review\n", encoding="utf-8")
    with database.session() as session:
        app = Application(job_id=1, folder_path=str(folder))
        session.add(app)
        session.commit()
        session.refresh(app)
        app_id = app.id or 0
    path = ApplicationService(settings, database).approve_answers(
        app_id, {"Why this role?": "approve"}, {}
    )
    assert path.exists()
    assert "Answer Approval" in (app_dir / "submission_review.md").read_text(encoding="utf-8")


def test_field_safety_classification() -> None:
    detector = FormFieldDetector()
    assert detector.classify_field_safety("Email", "email") == FieldSafety.SAFE
    assert detector.classify_field_safety("Salary expectation", "text") == FieldSafety.SENSITIVE
    assert detector.classify_field_safety("CAPTCHA", "text") == FieldSafety.BLOCKED
