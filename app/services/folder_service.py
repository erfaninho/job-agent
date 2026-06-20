import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import Settings
from app.models.application import Application, Job


def slugify(value: str | None, fallback: str) -> str:
    text = (value or fallback).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:40] or fallback


class FolderService:
    SUBDIRS = (
        "00_job-posting/screenshots",
        "01_analysis",
        "02_cv",
        "03_cover-letter",
        "04_application",
        "05_follow-up",
    )

    def __init__(self, settings: Settings):
        self.settings = settings

    def create_application_folder(self, job: Job) -> Path:
        date = datetime.now().strftime("%Y-%m-%d")
        base_name = "_".join(
            [
                date,
                slugify(job.company, "unknown-company"),
                slugify(job.title, "unknown-role"),
                slugify(job.location or job.remote_type, "unspecified"),
            ]
        )
        folder = self.settings.applications_path / base_name
        suffix = 1
        while folder.exists():
            suffix += 1
            folder = self.settings.applications_path / f"{base_name}-{suffix}"
        for subdir in self.SUBDIRS:
            (folder / subdir).mkdir(parents=True, exist_ok=False)
        return folder

    def initialize_files(self, folder: Path, job: Job, application: Application) -> None:
        (folder / "00_job-posting" / "job_description.md").write_text(
            job.description_text, encoding="utf-8"
        )
        (folder / "00_job-posting" / "source_url.txt").write_text(
            job.source_url or "", encoding="utf-8"
        )
        (folder / "05_follow-up" / "notes.md").write_text("", encoding="utf-8")
        self.write_metadata(
            folder,
            {
                "application_id": application.id,
                "job_id": job.id,
                "company": job.company,
                "title": job.title,
                "status": application.status,
                "created_at": datetime.now().isoformat(),
            },
        )

    @staticmethod
    def write_metadata(folder: Path, data: dict[str, Any]) -> None:
        (folder / "metadata.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
