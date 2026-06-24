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
        day_folder = self.settings.applications_path / date
        day_folder.mkdir(parents=True, exist_ok=True)
        base_name = "_".join(
            [
                slugify(job.company, "unknown-company"),
                slugify(job.title, "unknown-role"),
                slugify(job.location or job.remote_type, "unspecified"),
            ]
        )
        folder = day_folder / base_name
        suffix = 1
        while folder.exists():
            suffix += 1
            folder = day_folder / f"{base_name}_{suffix:03d}"
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
        if not job.source_url:
            self.append_audit_log(
                folder,
                "Warning: source_url missing. Browser assist cannot open the original job page.",
            )
        (folder / "00_job-posting" / "final_application_url.txt").write_text(
            job.final_application_url or "", encoding="utf-8"
        )
        (folder / "00_job-posting" / "job_description.html").write_text("", encoding="utf-8")
        (folder / "01_analysis" / "model_usage.json").write_text("[]", encoding="utf-8")
        (folder / "02_cv" / "compile_log.txt").write_text("", encoding="utf-8")
        (folder / "04_application" / "application_answers.approved.json").write_text(
            "[]", encoding="utf-8"
        )
        (folder / "04_application" / "form_fields_detected.json").write_text("[]", encoding="utf-8")
        (folder / "05_follow-up" / "notes.md").write_text("", encoding="utf-8")
        self.write_metadata(
            folder,
            {
                "application_id": application.id,
                "job_id": job.id,
                "company": job.company,
                "title": job.title,
                "location": job.location,
                "source": job.source,
                "source_url": job.source_url,
                "final_application_url": job.final_application_url,
                "ats_platform": job.ats_platform,
                "status": application.status,
                "fit_score": application.fit_score,
                "documents": {
                    "cv_tex": "",
                    "cv_pdf": "",
                    "cover_letter_md": "",
                    "cover_letter_pdf": "",
                    "answers_generated": "",
                    "answers_approved": str(
                        folder / "04_application" / "application_answers.approved.json"
                    ),
                },
                "manual_review_required": True,
                "submitted": False,
                "submitted_at": None,
                "follow_up_date": None,
                "created_at": datetime.now().isoformat(),
            },
        )
        self.append_audit_log(folder, "Application folder created.")

    @staticmethod
    def write_metadata(folder: Path, data: dict[str, Any]) -> None:
        (folder / "metadata.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def append_audit_log(folder: Path, message: str) -> None:
        path = folder / "audit_log.md"
        existing = path.read_text(encoding="utf-8") if path.exists() else "# Audit Log\n\n"
        path.write_text(existing + f"- {datetime.now().isoformat()} - {message}\n", encoding="utf-8")
