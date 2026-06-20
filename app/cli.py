from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import select

from app.config import get_settings
from app.config import Settings
from app.models.application import Application, Job
from app.services.database import DatabaseService
from app.services.job_input_service import JobInputService
from app.services.preparation_service import PreparationService
from app.services.storage_service import StorageService

app = typer.Typer(help="Local supervised job application manager.")
profile_app = typer.Typer(help="Candidate profile commands.")
app.add_typer(profile_app, name="profile")
console = Console()


def services() -> tuple[Settings, DatabaseService]:
    settings = get_settings()
    database = DatabaseService(settings)
    database.init_db()
    StorageService(settings).ensure_base_dirs()
    return settings, database


@app.command()
def init() -> None:
    settings, database = services()
    StorageService(settings).setup_profile()
    console.print("Initialized storage, profile files, answer bank, and SQLite database.")


@profile_app.command("setup")
def profile_setup() -> None:
    settings, _ = services()
    StorageService(settings).setup_profile()
    console.print(f"Profile created at {settings.profile_path}")


@app.command("import-cv")
def import_cv(path: Path) -> None:
    settings, _ = services()
    imported = StorageService(settings).import_cv(path)
    console.print(f"Imported master CV to {imported}")


@app.command("add-job")
def add_job(
    file: Path | None = typer.Option(None, "--file"),
    text: str | None = typer.Option(None, "--text"),
    url: str | None = typer.Option(None, "--url"),
) -> None:
    _, database = services()
    service = JobInputService(database)
    if file:
        job = service.add_from_file(file)
    elif text:
        job = service.add_from_text(text)
    elif url:
        job = service.add_from_url(url)
    else:
        raise typer.BadParameter("Provide --file, --text, or --url.")
    console.print(f"Job {job.id}: {job.company} - {job.title}")


@app.command("list")
def list_applications(status: str | None = typer.Option(None, "--status")) -> None:
    _, database = services()
    table = Table("ID", "Company", "Role", "Status", "Fit", "Folder")
    with database.session() as session:
        applications = session.exec(select(Application)).all()
        rows = [
            (application, session.exec(select(Job).where(Job.id == application.job_id)).one())
            for application in applications
        ]
    for application_record, job in rows:
        if status and application_record.status != status:
            continue
        table.add_row(
            str(application_record.id),
            job.company,
            job.title,
            application_record.status,
            "" if application_record.fit_score is None else str(application_record.fit_score),
            application_record.folder_path,
        )
    console.print(table)


@app.command("show")
def show(application_id: int) -> None:
    _, database = services()
    with database.session() as session:
        application = session.exec(select(Application).where(Application.id == application_id)).one()
        job = session.exec(select(Job).where(Job.id == application.job_id)).one()
    console.print(
        {
            "application_id": application.id,
            "job_id": job.id,
            "company": job.company,
            "role": job.title,
            "status": application.status,
            "fit_score": application.fit_score,
            "folder": application.folder_path,
            "cv": application.cv_tex_path,
            "cover_letter": application.cover_letter_path,
        }
    )


@app.command("prepare")
def prepare(
    job_id: int,
    no_cover_letter: bool = typer.Option(False, "--no-cover-letter"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    settings, database = services()
    summary = PreparationService(settings, database).prepare(
        job_id, no_cover_letter=no_cover_letter, dry_run=dry_run
    )
    table = Table("Field", "Value")
    for key, value in summary.items():
        table.add_row(key, str(value))
    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
