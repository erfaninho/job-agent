from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import Settings
from app.models.application import Application, ApplicationEvent, Job, utc_now


def create_db_engine(settings: Settings) -> Engine:
    if settings.database_url.startswith("sqlite:///"):
        db_path = Path(settings.database_url.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(settings.database_url, echo=False)


class DatabaseService:
    def __init__(self, settings: Settings):
        self.engine = create_db_engine(settings)

    def init_db(self) -> None:
        SQLModel.metadata.create_all(self.engine)

    def session(self) -> Session:
        return Session(self.engine)

    def add_event(self, application_id: int | None, event_type: str, message: str) -> None:
        with self.session() as session:
            event = ApplicationEvent(
                application_id=application_id, event_type=event_type, message=message
            )
            session.add(event)
            session.commit()

    def find_duplicate_job(self, description_hash: str, source_url: str | None) -> Job | None:
        with self.session() as session:
            if source_url:
                by_url = session.exec(select(Job).where(Job.source_url == source_url)).first()
                if by_url:
                    return by_url
            return session.exec(select(Job).where(Job.description_hash == description_hash)).first()

    def touch_application(self, application: Application) -> None:
        application.updated_at = utc_now()
