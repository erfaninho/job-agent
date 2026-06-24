import json
from pathlib import Path

from typer.testing import CliRunner

import app.cli as cli
from app.config import Settings
from app.services.database import DatabaseService
from app.services.job_input_service import JobInputService
from app.services.job_input_service import extract_source_url_from_text
from app.services.preparation_service import PreparationService
from app.services.source_detection import infer_source_from_url
from app.services.storage_service import StorageService


def make_services(tmp_path: Path) -> tuple[Settings, DatabaseService]:
    settings = Settings(
        STORAGE_DIR=tmp_path / "storage",
        DATABASE_URL=f"sqlite:///{tmp_path / 'job_agent.db'}",
        MODEL_PROVIDER="local",
    )
    database = DatabaseService(settings)
    database.init_db()
    StorageService(settings).ensure_base_dirs()
    return settings, database


def test_extract_source_url_formats() -> None:
    assert (
        extract_source_url_from_text("Source URL:\nhttps://uk.indeed.com/viewjob?jk=1")
        == "https://uk.indeed.com/viewjob?jk=1"
    )
    assert (
        extract_source_url_from_text("Source URL: https://www.linkedin.com/jobs/view/1")
        == "https://www.linkedin.com/jobs/view/1"
    )
    assert extract_source_url_from_text("Original URL:\nhttps://jobs.lever.co/acme") == "https://jobs.lever.co/acme"


def test_source_inference() -> None:
    assert infer_source_from_url("https://uk.indeed.com/viewjob?jk=1") == "indeed"
    assert infer_source_from_url("https://www.linkedin.com/jobs/view/1") == "linkedin"
    assert infer_source_from_url("https://boards.greenhouse.io/acme") == "greenhouse"
    assert infer_source_from_url("https://jobs.lever.co/acme") == "lever"
    assert infer_source_from_url("https://acme.myworkdayjobs.com/job/1") == "workday"


def test_add_from_file_source_url_and_override(tmp_path: Path) -> None:
    _settings, database = make_services(tmp_path)
    job_file = tmp_path / "job.txt"
    job_file.write_text(
        "Source URL:\nhttps://uk.indeed.com/viewjob?jk=file\nCompany: Acme\nRole: Engineer",
        encoding="utf-8",
    )
    service = JobInputService(database)
    override = service.add_from_file(
        job_file,
        source_url="https://www.linkedin.com/jobs/view/override",
        source="linkedin",
    )
    assert override.source_url == "https://www.linkedin.com/jobs/view/override"
    assert override.source == "linkedin"


def test_add_job_cli_source_url(monkeypatch, tmp_path: Path) -> None:
    settings, database = make_services(tmp_path)
    monkeypatch.setattr(cli, "services", lambda: (settings, database))
    job_file = tmp_path / "job.txt"
    job_file.write_text("Company: CGI\nRole: Developer", encoding="utf-8")
    result = CliRunner().invoke(
        cli.app,
        [
            "add-job",
            "--file",
            str(job_file),
            "--source-url",
            "https://uk.indeed.com/viewjob?jk=1",
            "--source",
            "indeed",
        ],
    )
    assert result.exit_code == 0
    assert "Next: pixi run jobagent prepare" in result.output
    jobs = JobInputService(database).database.find_duplicate_job("", "https://uk.indeed.com/viewjob?jk=1")
    assert jobs is not None


def test_set_source_url_updates_existing_job(tmp_path: Path) -> None:
    _settings, database = make_services(tmp_path)
    service = JobInputService(database)
    job = service.add_from_text("Company: Acme\nRole: Engineer")
    updated = service.set_source_url(job.id or 0, "https://jobs.lever.co/acme/1")
    assert updated.source_url == "https://jobs.lever.co/acme/1"
    assert updated.source == "lever"


def test_prepare_writes_source_url_and_metadata(tmp_path: Path) -> None:
    settings, database = make_services(tmp_path)
    storage = StorageService(settings)
    storage.setup_profile()
    cv = tmp_path / "cv.tex"
    cv.write_text(r"\documentclass{article}\begin{document}CV\end{document}", encoding="utf-8")
    storage.import_cv(cv)
    job = JobInputService(database).add_from_text(
        "Company: Acme\nRole: Engineer",
        source_url="https://uk.indeed.com/viewjob?jk=1",
        source="indeed",
    )
    summary = PreparationService(settings, database).prepare(job.id or 0)
    folder = Path(str(summary["application_folder_path"]))
    assert (folder / "00_job-posting" / "source_url.txt").read_text(encoding="utf-8") == "https://uk.indeed.com/viewjob?jk=1"
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["source_url"] == "https://uk.indeed.com/viewjob?jk=1"
    assert metadata["source"] == "indeed"
