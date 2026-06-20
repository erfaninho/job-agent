from fastapi import FastAPI, HTTPException
from sqlmodel import select

from app.config import get_settings
from app.models.application import Application, Job
from app.services.database import DatabaseService
from app.services.job_input_service import JobInputService
from app.services.preparation_service import PreparationService
from app.services.storage_service import StorageService

api = FastAPI(title="Agentic Application Manager")


def db() -> DatabaseService:
    settings = get_settings()
    StorageService(settings).ensure_base_dirs()
    database = DatabaseService(settings)
    database.init_db()
    return database


@api.get("/applications")
def applications() -> list[dict[str, object]]:
    database = db()
    with database.session() as session:
        application_rows = session.exec(select(Application)).all()
        rows = [
            (app, session.exec(select(Job).where(Job.id == app.job_id)).one())
            for app in application_rows
        ]
    return [
        {
            "id": app.id,
            "company": job.company,
            "title": job.title,
            "status": app.status,
            "fit_score": app.fit_score,
            "folder_path": app.folder_path,
        }
        for app, job in rows
    ]


@api.get("/applications/{application_id}")
def application_detail(application_id: int) -> dict[str, object]:
    database = db()
    with database.session() as session:
        app = session.exec(select(Application).where(Application.id == application_id)).first()
        if app is None:
            raise HTTPException(status_code=404, detail="Application not found")
        job = session.exec(select(Job).where(Job.id == app.job_id)).one()
    return {"application": app.model_dump(), "job": job.model_dump()}


@api.post("/jobs")
def create_job(payload: dict[str, str]) -> dict[str, object]:
    database = db()
    job = JobInputService(database).add_from_text(payload["description"], source="api")
    return job.model_dump()


@api.post("/applications/{job_id}/prepare")
def prepare_job(job_id: int) -> dict[str, object]:
    settings = get_settings()
    return PreparationService(settings, db()).prepare(job_id)


app = api
