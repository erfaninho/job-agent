from pathlib import Path

from app.config import Settings
from app.models.application import Application
from app.services.database import DatabaseService
from app.services.folder_service import FolderService
from app.services.job_input_service import JobInputService, description_hash, normalize_whitespace


def test_normalize_and_hash_stable() -> None:
    assert normalize_whitespace("hello\n\n world") == "hello world"
    assert description_hash("hello world") == description_hash("hello   world")


def test_add_job_and_create_folder(tmp_path: Path) -> None:
    settings = Settings(
        JOBAGENT_STORAGE_PATH=tmp_path / "storage",
        JOBAGENT_DATABASE_URL=f"sqlite:///{tmp_path / 'jobagent.db'}",
    )
    database = DatabaseService(settings)
    database.init_db()
    job = JobInputService(database).add_from_text("Company: Acme\nRole: Python Developer\nRemote")
    folder = FolderService(settings).create_application_folder(job)
    application = Application(job_id=job.id or 0, folder_path=str(folder))
    FolderService(settings).initialize_files(folder, job, application)
    assert (folder / "00_job-posting" / "job_description.md").exists()
    assert (folder / "metadata.json").exists()
