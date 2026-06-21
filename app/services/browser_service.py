import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from sqlmodel import select

from app.config import Settings
from app.models.application import Application, ApplicationStatus, Job
from app.services.ats_detector_service import ATSDetectorService
from app.services.database import DatabaseService
from app.services.form_field_detector import FormFieldDetector


class BrowserService:
    def __init__(self, settings: Settings, database: DatabaseService):
        self.settings = settings
        self.database = database
        self.ats_detector = ATSDetectorService()
        self.field_detector = FormFieldDetector()

    def apply_assist(self, application_id: int) -> dict[str, object]:
        application, job = self._load(application_id)
        if not job.source_url:
            raise ValueError("Job has no source_url to open.")
        folder = Path(application.folder_path)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.settings.browser_headless)
            page = browser.new_page()
            page.goto(job.source_url, wait_until="domcontentloaded")
            source_shot = folder / "00_job-posting" / "screenshots" / "source_page.png"
            page.screenshot(path=str(source_shot), full_page=True)
            self._try_follow_apply_redirect(page)
            final_url = page.url
            destination_shot = folder / "00_job-posting" / "screenshots" / "destination_page.png"
            page.screenshot(path=str(destination_shot), full_page=True)
            html = page.content()
            fields = [field.to_dict() for field in self.field_detector.detect_from_html(html)]
            (folder / "04_application" / "form_fields_detected.json").write_text(
                json.dumps(fields, indent=2), encoding="utf-8"
            )
            (folder / "00_job-posting" / "final_application_url.txt").write_text(
                final_url, encoding="utf-8"
            )
            ats = self.ats_detector.detect(final_url, html)
            browser.close()
        with self.database.session() as session:
            stored_job = session.exec(select(Job).where(Job.id == job.id)).one()
            stored_app = session.exec(select(Application).where(Application.id == application_id)).one()
            stored_job.final_application_url = final_url
            stored_job.ats_platform = ats
            stored_app.status = ApplicationStatus.browser_assist_started.value
            session.add(stored_job)
            session.add(stored_app)
            session.commit()
        self.database.add_event(application_id, "browser_assist_started", final_url)
        return {
            "source_url": job.source_url,
            "final_application_url": final_url,
            "ats_platform": ats,
            "detected_fields": len(fields),
            "message": "Review the application in the browser. Submit manually only if everything is correct.",
        }

    def fill_safe_fields_preview_only(self, page: Page, approved_answers: list[dict[str, object]]) -> int:
        submit_selectors = ("button[type=submit]", "input[type=submit]", "button:has-text('Submit')")
        for selector in submit_selectors:
            if page.locator(selector).count():
                pass
        return len(approved_answers)

    @staticmethod
    def _try_follow_apply_redirect(page: Page) -> None:
        selectors = [
            "a:has-text('Apply')",
            "button:has-text('Apply')",
            "a:has-text('Apply now')",
            "button:has-text('Apply now')",
        ]
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if locator.count():
                    locator.click(timeout=2000)
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                    return
            except Exception:
                continue

    def _load(self, application_id: int) -> tuple[Application, Job]:
        with self.database.session() as session:
            application = session.exec(select(Application).where(Application.id == application_id)).one()
            job = session.exec(select(Job).where(Job.id == application.job_id)).one()
            return application, job
