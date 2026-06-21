import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import select

from app.agents.interview_prep import InterviewPrepAgent
from app.agents.job_parser import JobParserAgent
from app.config import Settings
from app.models.application import Application, ApplicationStatus, Job, utc_now
from app.services.database import DatabaseService
from app.services.model_provider import ModelProviderError, get_model_provider
from app.services.storage_service import StorageService


class ApplicationService:
    def __init__(self, settings: Settings, database: DatabaseService):
        self.settings = settings
        self.database = database

    def approve_answers(self, application_id: int) -> Path:
        application = self.get_application(application_id)
        folder = Path(application.folder_path)
        generated_path = folder / "04_application" / "application_answers.generated.json"
        approved_path = folder / "04_application" / "application_answers.approved.json"
        generated = json.loads(generated_path.read_text(encoding="utf-8"))
        safe_answers = [
            answer
            for answer in generated
            if not answer.get("requires_user_review") and answer.get("auto_fill_allowed")
        ]
        approved_path.write_text(json.dumps(safe_answers, indent=2), encoding="utf-8")
        self.database.add_event(application_id, "answers_approved", str(approved_path))
        return approved_path

    def set_status(self, application_id: int, status: str) -> Application:
        valid = {item.value for item in ApplicationStatus}
        if status not in valid:
            raise ValueError(f"Invalid status: {status}")
        with self.database.session() as session:
            application = session.exec(select(Application).where(Application.id == application_id)).one()
            application.status = status
            application.updated_at = utc_now()
            session.add(application)
            session.commit()
            session.refresh(application)
        self.database.add_event(application_id, "status_changed", status)
        return application

    def mark_submitted(self, application_id: int) -> Application:
        with self.database.session() as session:
            application = session.exec(select(Application).where(Application.id == application_id)).one()
            application.status = ApplicationStatus.submitted.value
            application.submitted_at = utc_now()
            application.follow_up_date = self._business_days_after(application.submitted_at, 5)
            application.updated_at = utc_now()
            session.add(application)
            session.commit()
            session.refresh(application)
        self.database.add_event(application_id, "submitted", "User confirmed manual submission.")
        return application

    def create_follow_up_email(self, application_id: int) -> Path:
        application, job = self.get_application_and_job(application_id)
        folder = Path(application.folder_path)
        profile = StorageService(self.settings).load_profile()
        email = (
            f"Subject: Follow-up on {job.title} application\n\n"
            f"Dear {job.company} hiring team,\n\n"
            f"I hope you are well. I wanted to follow up on my application for {job.title}. "
            "I remain interested in the role and would welcome the opportunity to discuss how my "
            "background fits your needs.\n\n"
            f"Kind regards,\n{profile.name or '[Your name]'}\n"
        )
        path = folder / "05_follow-up" / "follow_up_email.md"
        path.write_text(email, encoding="utf-8")
        self.database.add_event(application_id, "follow_up_created", str(path))
        return path

    def create_interview_prep(self, application_id: int) -> Path:
        application, job = self.get_application_and_job(application_id)
        folder = Path(application.folder_path)
        parsed = JobParserAgent().parse(job.description_text)
        try:
            provider = get_model_provider(self.settings)
            content = provider.generate_text(
                "Generate concise interview preparation notes from the job post and approved facts.",
                f"Job:\n{job.description_text}\n\nParsed:\n{parsed.model_dump_json()}",
            )
        except ModelProviderError:
            content = ""
        if not content.strip():
            content = InterviewPrepAgent().generate(job.company, job.title, parsed)
        path = folder / "05_follow-up" / "interview_prep.md"
        path.write_text(content, encoding="utf-8")
        self.database.add_event(application_id, "interview_prep_created", str(path))
        return path

    def get_application(self, application_id: int) -> Application:
        with self.database.session() as session:
            return session.exec(select(Application).where(Application.id == application_id)).one()

    def get_application_and_job(self, application_id: int) -> tuple[Application, Job]:
        with self.database.session() as session:
            application = session.exec(select(Application).where(Application.id == application_id)).one()
            job = session.exec(select(Job).where(Job.id == application.job_id)).one()
            return application, job

    @staticmethod
    def _business_days_after(start: datetime, days: int) -> datetime:
        current = start
        remaining = days
        while remaining:
            current += timedelta(days=1)
            if current.weekday() < 5:
                remaining -= 1
        return current.astimezone(timezone.utc)
