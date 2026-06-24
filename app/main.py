from pathlib import Path
from datetime import date

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from app.config import get_settings
from app.models.application import Application, Job
from app.services.application_service import ApplicationService
from app.services.database import DatabaseService
from app.services.job_input_service import JobInputService
from app.services.preparation_service import PreparationService
from app.services.storage_service import StorageService

api = FastAPI(title="Agentic Application Manager")
templates = Jinja2Templates(directory="app/templates")


def db() -> DatabaseService:
    settings = get_settings()
    StorageService(settings).ensure_base_dirs()
    database = DatabaseService(settings)
    database.init_db()
    return database


def app_rows() -> list[tuple[Application, Job]]:
    database = db()
    with database.session() as session:
        application_rows = session.exec(select(Application)).all()
        return [
            (app, session.exec(select(Job).where(Job.id == app.job_id)).one())
            for app in application_rows
        ]


def dashboard_stats(rows: list[tuple[Application, Job]]) -> dict[str, int]:
    today = date.today()
    return {
        "total_jobs": len(rows),
        "prepared_today": sum(
            1
            for app, _ in rows
            if app.application_date is not None and app.application_date.date() == today
        ),
        "submitted_today": sum(
            1 for app, _ in rows if app.submitted_at is not None and app.submitted_at.date() == today
        ),
        "needs_review": sum(1 for app, _ in rows if app.status == "needs_review"),
        "followups_due": sum(1 for app, _ in rows if app.status == "follow_up_needed"),
    }


@api.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    rows = app_rows()
    stats = dashboard_stats(rows)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"stats": stats, "rows": rows[-20:]},
    )


@api.get("/dashboard/applications", response_class=HTMLResponse)
def dashboard_applications(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "applications.html", {"rows": app_rows()})


@api.get("/dashboard/applications/{application_id}", response_class=HTMLResponse)
def dashboard_application_detail(request: Request, application_id: int) -> HTMLResponse:
    database = db()
    with database.session() as session:
        application = session.exec(select(Application).where(Application.id == application_id)).first()
        if application is None:
            raise HTTPException(status_code=404, detail="Application not found")
        job = session.exec(select(Job).where(Job.id == application.job_id)).one()
    folder = Path(application.folder_path)
    files = {
        "job_description": folder / "00_job-posting" / "job_description.md",
        "fit_score": folder / "01_analysis" / "fit_score.json",
        "requirements": folder / "01_analysis" / "extracted_requirements.json",
        "strategy": folder / "01_analysis" / "tailoring_strategy.md",
        "answers": folder / "04_application" / "application_answers.generated.json",
        "approved_answers": folder / "04_application" / "application_answers.approved.json",
        "review": folder / "04_application" / "submission_review.md",
        "metadata": folder / "metadata.json",
        "audit_log": folder / "audit_log.md",
    }
    previews = {
        name: path.read_text(encoding="utf-8") if path.exists() else ""
        for name, path in files.items()
    }
    return templates.TemplateResponse(
        request,
        "application_detail.html",
        {"application": application, "job": job, "previews": previews},
    )


@api.get("/applications")
def applications() -> list[dict[str, object]]:
    rows = app_rows()
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


@api.post("/applications/{application_id}/approve-answers")
def approve_answers(application_id: int) -> dict[str, str]:
    settings = get_settings()
    path = ApplicationService(settings, db()).approve_answers(application_id)
    return {"path": str(path)}


@api.post("/applications/{application_id}/mark-submitted")
def mark_submitted(application_id: int) -> dict[str, object]:
    settings = get_settings()
    application = ApplicationService(settings, db()).mark_submitted(application_id)
    return application.model_dump()


@api.post("/applications/{application_id}/status")
def update_status(application_id: int, payload: dict[str, str]) -> dict[str, object]:
    settings = get_settings()
    application = ApplicationService(settings, db()).set_status(application_id, payload["status"])
    return application.model_dump()


app = api
