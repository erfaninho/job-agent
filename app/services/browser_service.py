import json
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, sync_playwright
from sqlmodel import select

from app.config import Settings
from app.models.application import Application, ApplicationStatus, Job
from app.models.application import utc_now
from app.services.auth_session_service import AuthSessionService
from app.services.ats_detector_service import ATSDetectorService
from app.services.database import DatabaseService
from app.services.form_field_detector import FormFieldDetector
from app.services.form_field_detector import FieldSafety
from app.services.folder_service import FolderService
from app.services.source_detection import detect_source_site
from app.services.storage_service import StorageService


class BrowserService:
    def __init__(self, settings: Settings, database: DatabaseService):
        self.settings = settings
        self.database = database
        self.ats_detector = ATSDetectorService()
        self.field_detector = FormFieldDetector()

    def apply_assist(
        self,
        application_id: int,
        input_func: Callable[[str], str] = input,
    ) -> dict[str, object]:
        application, job = self._load(application_id)
        folder = Path(application.folder_path)
        metadata_path = folder / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
        source_url = job.source_url or str(metadata.get("source_url") or "")
        if not source_url:
            raise ValueError("Job has no source_url to open.")
        auth = AuthSessionService(self.settings)
        source_site = detect_source_site(source_url)
        auth_state_path = auth.get_auth_state_path(source_site)
        if source_site in {"linkedin", "indeed"} and not auth_state_path.exists():
            raise RuntimeError(
                f"No saved auth session found for {source_site}.\n"
                f"Run:\npixi run jobagent auth login {source_site}\nThen retry apply-assist."
            )
        metadata.update(
            {
                "auth_site": source_site,
                "auth_state_used": auth_state_path.exists(),
                "auth_state_path": str(auth_state_path) if auth_state_path.exists() else "",
                "browser_assist_started_at": self._now(),
                "manual_submit_confirmed": False,
            }
        )
        FolderService.write_metadata(folder, metadata)
        FolderService.append_audit_log(folder, "Auth session checked.")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.settings.browser_headless)
            if auth_state_path.exists():
                context = browser.new_context(storage_state=str(auth_state_path))
            else:
                context = browser.new_context()
            page = context.new_page()
            if auth_state_path.exists():
                FolderService.append_audit_log(folder, "Auth session loaded.")
            page.goto(source_url, wait_until="domcontentloaded")
            if source_site in {"linkedin", "indeed"} and not auth_state_path.exists():
                input_func("Log in manually if needed, then press Enter to continue.")
            FolderService.append_audit_log(folder, "Source page opened.")
            source_shot = folder / "00_job-posting" / "screenshots" / "source_page.png"
            page.screenshot(path=str(source_shot), full_page=True)
            if input_func("Click detected Apply button if safe? yes/no: ").strip().lower() in {"y", "yes"}:
                self._try_follow_apply_redirect(page)
            final_url = page.url
            if final_url != source_url:
                FolderService.append_audit_log(folder, "Apply redirection detected.")
            destination_shot = folder / "00_job-posting" / "screenshots" / "destination_page.png"
            page.screenshot(path=str(destination_shot), full_page=True)
            html = page.content()
            fields = [field.to_dict() for field in self.field_detector.detect_from_html(html)]
            FolderService.append_audit_log(folder, "Fields detected.")
            (folder / "04_application" / "form_fields_detected.json").write_text(
                json.dumps(fields, indent=2), encoding="utf-8"
            )
            approved_path = folder / "04_application" / "application_answers.approved.json"
            approved_answers = (
                json.loads(approved_path.read_text(encoding="utf-8"))
                if approved_path.exists()
                else []
            )
            fill_review = self._build_fill_review(fields, approved_path, bool(approved_answers))
            if input_func("Fill safe fields now? yes/no: ").strip().lower() in {"y", "yes"}:
                filled_count = self.fill_safe_fields(page, fields, approved_answers, folder)
            else:
                filled_count = 0
            if input_func("Upload tailored CV if a safe file field exists? yes/no: ").strip().lower() in {
                "y",
                "yes",
            }:
                FolderService.append_audit_log(folder, "CV upload confirmed.")
            if input_func("Upload cover letter if a safe file field exists? yes/no: ").strip().lower() in {
                "y",
                "yes",
            }:
                FolderService.append_audit_log(folder, "Cover letter upload confirmed.")
            (folder / "00_job-posting" / "final_application_url.txt").write_text(
                final_url, encoding="utf-8"
            )
            ats = self.ats_detector.detect(final_url, html)
            FolderService.append_audit_log(folder, "ATS platform detected.")
            metadata.update(
                {
                    "source_url": source_url,
                    "final_application_url": final_url,
                    "ats_platform": ats,
                    "browser_assist_completed_at": self._now(),
                }
            )
            FolderService.write_metadata(folder, metadata)
            console_message = (
                "Review the application in the browser.\n"
                "Submit manually if everything is correct.\n"
                "After submitting, return here and type SUBMITTED.\n"
                "Type CANCEL if you did not submit.\n"
            )
            result = input_func(console_message).strip().upper()
            submitted = result == "SUBMITTED"
            if submitted:
                confirmation_shot = folder / "04_application" / "confirmation_screenshot.png"
                submitted_copy = folder / "04_application" / "submitted_copy.html"
                page.screenshot(path=str(confirmation_shot), full_page=True)
                submitted_copy.write_text(page.content(), encoding="utf-8")
                FolderService.append_audit_log(folder, "User confirmed manual submission.")
                FolderService.append_audit_log(folder, "Confirmation screenshot saved.")
                metadata["manual_submit_confirmed"] = True
                metadata["submitted"] = True
                metadata["submitted_at"] = self._now()
                FolderService.write_metadata(folder, metadata)
            else:
                metadata["manual_submit_confirmed"] = False
                FolderService.write_metadata(folder, metadata)
            context.close()
            browser.close()
        with self.database.session() as session:
            stored_job = session.exec(select(Job).where(Job.id == job.id)).one()
            stored_app = session.exec(select(Application).where(Application.id == application_id)).one()
            stored_job.final_application_url = final_url
            stored_job.ats_platform = ats
            stored_app.status = (
                ApplicationStatus.submitted.value
                if submitted
                else ApplicationStatus.needs_review.value
            )
            if submitted:
                from app.services.application_service import ApplicationService

                stored_app.submitted_at = utc_now()
                stored_app.follow_up_date = ApplicationService._business_days_after(
                    stored_app.submitted_at, 5
                )
            session.add(stored_job)
            session.add(stored_app)
            session.commit()
        self.database.add_event(application_id, "browser_assist_started", final_url)
        return {
            "source_url": source_url,
            "final_application_url": final_url,
            "ats_platform": ats,
            "detected_fields": len(fields),
            "filled_fields": filled_count,
            "fill_review": fill_review,
            "auth_site": source_site,
            "auth_state_used": auth_state_path.exists(),
            "message": "Review the application in the browser. Submit manually only if everything is correct.",
        }

    def build_fill_review(self, application_id: int) -> list[dict[str, object]]:
        application, _job = self._load(application_id)
        folder = Path(application.folder_path)
        fields_path = folder / "04_application" / "form_fields_detected.json"
        approved_path = folder / "04_application" / "application_answers.approved.json"
        fields = json.loads(fields_path.read_text(encoding="utf-8")) if fields_path.exists() else []
        approved = json.loads(approved_path.read_text(encoding="utf-8")) if approved_path.exists() else []
        return self._build_fill_review(fields, approved_path, bool(approved))

    @staticmethod
    def _build_fill_review(
        fields: list[dict[str, object]], approved_path: Path, has_approved_answers: bool
    ) -> list[dict[str, object]]:
        return [
            {
                "detected_field": field.get("label") or field.get("name"),
                "inferred_type": field.get("input_type"),
                "classification": "sensitive"
                if field.get("sensitive")
                else "safe"
                if field.get("safe_to_fill")
                else "blocked",
                "proposed_value": "",
                "source_file": str(approved_path),
                "will_fill": bool(field.get("safe_to_fill") and has_approved_answers),
            }
            for field in fields
        ]

    def fill_safe_fields_preview_only(self, page: Page, approved_answers: list[dict[str, object]]) -> int:
        submit_selectors = ("button[type=submit]", "input[type=submit]", "button:has-text('Submit')")
        for selector in submit_selectors:
            if page.locator(selector).count():
                pass
        return len(approved_answers)

    def fill_safe_fields(
        self,
        page: Page,
        fields: list[dict[str, object]],
        approved_answers: list[dict[str, object]],
        folder: Path,
    ) -> int:
        values = self._approved_answer_values(approved_answers)
        values.update(self._profile_values())
        values.update(self._document_values(folder))
        filled = 0
        for field in fields:
            label = str(field.get("label") or field.get("name") or "")
            safety = FieldSafety(str(field.get("safety") or "unknown"))
            if safety != FieldSafety.SAFE:
                continue
            proposed = self._value_for_field(label, values)
            if not proposed:
                continue
            selector = self._selector_for_field(field)
            try:
                locator = page.locator(selector).first
                if locator.count():
                    input_type = str(field.get("input_type") or "").lower()
                    tag = str(field.get("tag") or "").lower()
                    if input_type == "file":
                        locator.set_input_files(proposed)
                    elif tag == "select":
                        locator.select_option(label=proposed)
                    else:
                        locator.fill(proposed)
                    filled += 1
            except Exception:
                continue
        if filled:
            FolderService.append_audit_log(folder, "Safe fields filled.")
        return filled

    @staticmethod
    def _approved_answer_values(approved_answers: list[dict[str, object]]) -> dict[str, str]:
        values: dict[str, str] = {}
        for answer in approved_answers:
            key = str(answer.get("normalized_question_type") or answer.get("question_label") or "").lower()
            value = str(answer.get("answer") or "")
            if key and value:
                values[key] = value
        return values

    @staticmethod
    def _value_for_field(label: str, values: dict[str, str]) -> str:
        lowered = label.lower()
        if "first name" in lowered:
            return values.get("first_name", "")
        if "last name" in lowered:
            return values.get("last_name", "")
        if "full name" in lowered or lowered == "name" or " name" in lowered:
            return values.get("name", "")
        if "email" in lowered:
            return values.get("email", "")
        if "phone" in lowered or "mobile" in lowered:
            return values.get("phone", "")
        if "location" in lowered or "city" in lowered or "country" in lowered:
            return values.get("location", "")
        if "linkedin" in lowered:
            return values.get("linkedin", "")
        if "github" in lowered:
            return values.get("github", "")
        if "portfolio" in lowered or "website" in lowered:
            return values.get("portfolio", "")
        if "resume" in lowered or "cv" in lowered:
            return values.get("cv_pdf", "")
        if "cover letter" in lowered:
            return values.get("cover_letter_pdf", "") or values.get("cover_letter", "")
        if "why" in lowered and "company" in lowered:
            return values.get("why_this_company", "")
        if "why" in lowered and "role" in lowered:
            return values.get("why_this_role", "")
        if "tell us" in lowered or "about yourself" in lowered:
            return values.get("tell_us_about_yourself", "")
        return ""

    def _profile_values(self) -> dict[str, str]:
        try:
            profile = StorageService(self.settings).load_profile()
        except Exception:
            return {}
        parts = profile.name.split()
        return {
            "name": profile.name,
            "first_name": parts[0] if parts else "",
            "last_name": parts[-1] if len(parts) > 1 else "",
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "linkedin": profile.linkedin_url,
            "github": profile.github_url,
            "portfolio": profile.portfolio_url,
        }

    @staticmethod
    def _document_values(folder: Path) -> dict[str, str]:
        cv_pdf = folder / "02_cv" / "cv_tailored.pdf"
        cover_letter_pdf = folder / "03_cover-letter" / "cover_letter.pdf"
        return {
            "cv_pdf": str(cv_pdf) if cv_pdf.exists() else "",
            "cover_letter_pdf": str(cover_letter_pdf) if cover_letter_pdf.exists() else "",
        }

    @staticmethod
    def _selector_for_field(field: dict[str, object]) -> str:
        name = str(field.get("name") or "")
        if name:
            return f"[name='{name}']"
        label = str(field.get("label") or "")
        return f"textarea[placeholder='{label}'], input[placeholder='{label}']"

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

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
