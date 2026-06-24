import shutil
import sys
import json
from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import select

from app.config import Settings, get_settings
from app.logging_config import configure_logging
from app.models.application import Application, Job
from app.services.application_service import ApplicationService
from app.services.auth_session_service import AuthSessionService
from app.services.browser_service import BrowserService
from app.services.daily_summary_service import DailySummaryService
from app.services.database import DatabaseService
from app.services.job_input_service import JobInputService
from app.services.preparation_service import PreparationService
from app.services.storage_service import StorageService

app = typer.Typer(help="Local supervised job application manager.")
profile_app = typer.Typer(help="Candidate profile commands.")
db_app = typer.Typer(help="Database commands.")
auth_app = typer.Typer(help="Authentication session commands.")
app.add_typer(profile_app, name="profile")
app.add_typer(db_app, name="db")
app.add_typer(auth_app, name="auth")
console = Console()


def services() -> tuple[Settings, DatabaseService]:
    settings = get_settings()
    configure_logging(settings)
    database = DatabaseService(settings)
    database.init_db()
    StorageService(settings).ensure_base_dirs()
    return settings, database


@app.command()
def init() -> None:
    settings, _ = services()
    StorageService(settings).setup_profile()
    console.print("Initialized storage, profile files, answer bank, logs, and SQLite database.")


@app.command()
def doctor() -> None:
    settings, database = services()
    table = Table("Check", "Status", "Detail")
    table.add_row("Python", "ok", sys.version.split()[0])
    for folder in settings.required_folders():
        table.add_row(f"Folder {folder}", "ok" if folder.exists() else "missing", str(folder))
    try:
        database.init_db()
        table.add_row("Database", "ok", settings.database_url)
    except Exception as exc:
        table.add_row("Database", "error", str(exc))
    table.add_row(
        "LaTeX compiler",
        "ok" if shutil.which(settings.latex_compiler) else "missing",
        settings.latex_compiler,
    )
    model_errors = settings.validate_model_settings()
    if model_errors:
        for error in model_errors:
            table.add_row("Model settings", "error", error)
    else:
        table.add_row("Model settings", "ok", f"{settings.model_provider}:{settings.selected_model}")
    if settings.model_provider == "ollama":
        try:
            import httpx

            response = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                names = {str(model.get("name", "")) for model in models if isinstance(model, dict)}
                model_found = any(settings.ollama_model in name for name in names)
                detail = settings.ollama_base_url
                if not model_found:
                    detail = f"Install the default model: ollama pull {settings.ollama_model}"
                table.add_row("Ollama", "ok" if model_found else "warning", detail)
            else:
                table.add_row("Ollama", "error", "Ollama is not responding. Start it with: ollama serve")
        except Exception as exc:
            table.add_row("Ollama", "warning", f"Ollama is not responding. Start it with: ollama serve ({exc})")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            chromium_path = Path(playwright.chromium.executable_path)
        table.add_row(
            "Playwright browser",
            "ok" if chromium_path.exists() else "missing",
            str(chromium_path)
            if chromium_path.exists()
            else "Install Chromium: pixi run python -m playwright install chromium",
        )
    except Exception as exc:
        table.add_row("Playwright browser", "warning", str(exc))
    auth = AuthSessionService(settings)
    for site in ("indeed", "linkedin"):
        status = auth.auth_status(site)
        table.add_row(
            f"Auth {site}",
            "ok" if status["auth_state_exists"] else "warning",
            str(status["auth_state_path"]),
        )
    console.print(table)


@auth_app.command("login")
def auth_login(site: str) -> None:
    settings, _ = services()
    console.print(
        "A browser will open.\n"
        "Log in manually.\n"
        "Complete any 2FA/CAPTCHA manually.\n"
        "When the site shows you are logged in, return to the terminal and press Enter.\n"
        "The app will save the browser session locally.\n"
        "No password will be stored."
    )
    path = AuthSessionService(settings).login(site)
    console.print(f"Saved local auth session to {path}")


@auth_app.command("status")
def auth_status(site: str | None = typer.Argument(None)) -> None:
    settings, _ = services()
    auth = AuthSessionService(settings)
    statuses = [auth.auth_status(site)] if site else auth.all_statuses()
    table = Table("Site", "State File Exists", "Last Modified", "Path")
    for item in statuses:
        table.add_row(
            str(item["site"]),
            "yes" if item["auth_state_exists"] else "no",
            str(item["last_modified"] or "-"),
            str(item["auth_state_path"]),
        )
    console.print(table)


@auth_app.command("logout")
def auth_logout(site: str, delete_profile: bool = typer.Option(False, "--delete-profile")) -> None:
    settings, _ = services()
    if not typer.confirm(f"Delete saved auth state for {site}?"):
        raise typer.Exit()
    AuthSessionService(settings).logout(site, delete_profile=delete_profile)
    console.print(f"Deleted saved auth state for {site}.")


@db_app.command("init")
def db_init() -> None:
    _, database = services()
    database.init_db()
    console.print("Database initialized.")


@db_app.command("reset")
def db_reset(force: bool = typer.Option(False, "--force")) -> None:
    if not force:
        raise typer.BadParameter("Use --force to reset the development database.")
    _, database = services()
    database.reset_db()
    console.print("Database reset.")


@profile_app.command("setup")
def profile_setup() -> None:
    settings, _ = services()
    StorageService(settings).setup_profile()
    console.print(f"Profile created at {settings.profile_path}")


@profile_app.command("validate")
def profile_validate() -> None:
    settings, _ = services()
    missing = StorageService(settings).validate_profile()
    if missing:
        console.print("Profile is incomplete. Missing:")
        for item in missing:
            console.print(f"- {item}")
        raise typer.Exit(code=1)
    console.print("Profile files are valid.")


@profile_app.command("show")
def profile_show() -> None:
    settings, _ = services()
    console.print(StorageService(settings).load_profile().model_dump())


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
    console.print(f"Next: pixi run jobagent prepare {job.id}")


@app.command("jobs")
def jobs(
    status: str | None = typer.Option(None, "--status"),
    source: str | None = typer.Option(None, "--source"),
    unprepared: bool = typer.Option(False, "--unprepared"),
) -> None:
    _, database = services()
    table = Table("Job ID", "Company", "Title", "Source", "Source URL", "Status", "Created At", "Prepared?")
    with database.session() as session:
        jobs_list = session.exec(select(Job)).all()
        applications = session.exec(select(Application)).all()
    prepared_job_ids = {application.job_id for application in applications}
    for job in jobs_list:
        prepared = job.id in prepared_job_ids
        if status and job.status != status:
            continue
        if source and source.lower() not in job.source.lower():
            continue
        if unprepared and prepared:
            continue
        table.add_row(
            str(job.id),
            job.company,
            job.title,
            job.source,
            job.source_url or "",
            job.status,
            job.created_at.isoformat(),
            "yes" if prepared else "no",
        )
    console.print(table)


@app.command("job")
def job_detail(job_id: int) -> None:
    _, database = services()
    with database.session() as session:
        job = session.exec(select(Job).where(Job.id == job_id)).one()
        application = session.exec(select(Application).where(Application.job_id == job_id)).first()
    console.print(
        {
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "source": job.source,
            "source_url": job.source_url,
            "final_application_url": job.final_application_url,
            "status": job.status,
            "description_preview": job.description_text[:300],
            "application_id": application.id if application else None,
        }
    )


@app.command("list")
def list_applications(
    status: str | None = typer.Option(None, "--status"),
    date_filter: str | None = typer.Option(None, "--date"),
    company: str | None = typer.Option(None, "--company"),
) -> None:
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
        parsed_date = datetime.strptime(date_filter, "%Y-%m-%d").date() if date_filter else None
        if parsed_date and application_record.application_date.date() != parsed_date:
            continue
        if company and company.lower() not in job.company.lower():
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


@app.command("daily-summary")
def daily_summary(target_date: str | None = None) -> None:
    settings, database = services()
    parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else date.today()
    console.print(DailySummaryService(settings, database).write_summary(parsed_date))


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


@app.command("approve-answers")
def approve_answers(application_id: int) -> None:
    settings, database = services()
    application = ApplicationService(settings, database).get_application(application_id)
    generated_path = Path(application.folder_path) / "04_application" / "application_answers.generated.json"
    generated = json.loads(generated_path.read_text(encoding="utf-8"))
    decisions: dict[str, str] = {}
    edits: dict[str, str] = {}
    for index, answer in enumerate(generated):
        key = str(answer.get("question_label") or index)
        console.rule(key)
        console.print(f"Question type: {answer.get('normalized_question_type')}")
        console.print(f"Generated answer:\n{answer.get('answer')}")
        console.print(f"Source facts: {answer.get('source_facts_used')}")
        console.print(f"Sensitive: {'yes' if answer.get('requires_user_review') else 'no'}")
        console.print(f"Risk notes: {answer.get('risk_notes')}")
        console.print(f"Confidence: {answer.get('confidence_score')}")
        choice = typer.prompt("[A] approve [E] edit [R] reject [S] skip [Q] quit", default="S")
        decisions[key] = choice
        if choice.lower().startswith("e"):
            edits[key] = typer.prompt("Edited answer")
        if choice.lower().startswith("q"):
            break
    path = ApplicationService(settings, database).approve_answers(application_id, decisions, edits)
    console.print(f"Approved safe answers saved to {path}")


@app.command("status")
def status(application_id: int, new_status: str) -> None:
    settings, database = services()
    application = ApplicationService(settings, database).set_status(application_id, new_status)
    console.print(f"Application {application.id} status set to {application.status}")


@app.command("mark-submitted")
def mark_submitted(application_id: int) -> None:
    settings, database = services()
    application = ApplicationService(settings, database).mark_submitted(application_id)
    console.print(
        f"Application {application.id} marked submitted. Follow-up date: {application.follow_up_date}"
    )


@app.command("follow-up-email")
def follow_up_email(application_id: int) -> None:
    settings, database = services()
    path = ApplicationService(settings, database).create_follow_up_email(application_id)
    console.print(f"Follow-up email written to {path}")


@app.command("interview-prep")
def interview_prep(application_id: int) -> None:
    settings, database = services()
    path = ApplicationService(settings, database).create_interview_prep(application_id)
    console.print(f"Interview prep written to {path}")


@app.command("apply-assist")
def apply_assist(application_id: int) -> None:
    settings, database = services()
    summary = BrowserService(settings, database).apply_assist(application_id)
    table = Table("Field", "Value")
    for key, value in summary.items():
        if key == "fill_review":
            continue
        table.add_row(key, str(value))
    console.print(table)
    review = summary.get("fill_review")
    if isinstance(review, list):
        review_table = Table("Detected field", "Inferred type", "Classification", "Proposed value", "Source file", "Will fill?")
        for row in review:
            if isinstance(row, dict):
                review_table.add_row(
                    str(row.get("detected_field") or ""),
                    str(row.get("inferred_type") or ""),
                    str(row.get("classification") or ""),
                    str(row.get("proposed_value") or ""),
                    str(row.get("source_file") or ""),
                    "yes" if row.get("will_fill") else "no",
                )
        console.print(review_table)


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
    table.add_row("next_command", f"pixi run jobagent show {summary.get('application_id')}")
    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
