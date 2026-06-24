from pathlib import Path

from typer.testing import CliRunner
from sqlmodel import select

from app.cli import app
from app.config import Settings
from app.models.application import Application, Job
from app.services.database import DatabaseService


def test_raw_jobs_listing_data(tmp_path: Path) -> None:
    settings = Settings(
        STORAGE_DIR=tmp_path / "storage",
        DATABASE_URL=f"sqlite:///{tmp_path / 'job_agent.db'}",
    )
    database = DatabaseService(settings)
    database.init_db()
    with database.session() as session:
        job = Job(
            company="Acme",
            title="Backend Developer",
            source="indeed",
            source_url="https://uk.indeed.com/viewjob?jk=1",
            description_text="Job",
            description_hash="hash",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        jobs = session.exec(select(Job)).all()
        prepared_job_ids = {app.job_id for app in session.exec(select(Application)).all()}
    assert jobs[0].company == "Acme"
    assert jobs[0].id not in prepared_job_ids


def test_auth_status_cli_output() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["auth", "status", "indeed"])
    assert result.exit_code == 0
    assert "indeed" in result.output.lower()
    assert "State File Exists" in result.output


def test_doctor_has_fix_messages() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Ollama" in result.output
    assert "Playwright browser" in result.output
