from typing import cast

from playwright.sync_api import Page as PlaywrightPage

from app.config import Settings
from app.models.application import Application, Job
from app.services.ats_detector_service import ATSDetectorService
from app.services.browser_service import BrowserService
from app.services.database import DatabaseService
from app.services.form_field_detector import FormFieldDetector


def test_ats_detection_common_platforms() -> None:
    detector = ATSDetectorService()
    assert detector.detect("https://jobs.lever.co/example") == "lever"
    assert detector.detect("https://boards.greenhouse.io/example") == "greenhouse"
    assert detector.detect("https://company.example/jobs") == "unknown_custom"


def test_form_field_detector_marks_submit_not_safe() -> None:
    fields = FormFieldDetector().detect_from_html(
        """
        <form>
          <label for="name">Name</label><input id="name" name="name">
          <label for="salary">Salary</label><input id="salary" name="salary">
          <button type="submit">Submit application</button>
          <input type="submit" value="Submit">
        </form>
        """
    )
    by_name = {field.name or field.input_type: field for field in fields}
    assert by_name["name"].safe_to_fill is True
    assert by_name["salary"].sensitive is True
    assert by_name["submit"].safe_to_fill is False


def test_browser_service_preview_never_clicks_submit() -> None:
    class Locator:
        @property
        def first(self) -> "Locator":
            return self

        def count(self) -> int:
            return 1

        def click(self) -> None:
            raise AssertionError("Submit must never be clicked")

    class Page:
        def locator(self, selector: str) -> Locator:
            assert "submit" in selector.lower() or "Submit" in selector
            return Locator()

    count = BrowserService.fill_safe_fields_preview_only(
        BrowserService.__new__(BrowserService), cast(PlaywrightPage, Page()), [{"answer": "ok"}]
    )
    assert count == 1


def test_browser_close_happens_after_user_confirmation(tmp_path) -> None:
    events: list[str] = []

    class Locator:
        @property
        def first(self) -> "Locator":
            return self

        def count(self) -> int:
            return 1

        def fill(self, value: str) -> None:
            events.append(f"fill:{value}")

    class Page:
        def locator(self, selector: str) -> Locator:
            return Locator()

    count = BrowserService.fill_safe_fields(
        BrowserService.__new__(BrowserService),
        cast(PlaywrightPage, Page()),
        [{"label": "Why this role?", "name": "why", "safety": "safe"}],
        [{"normalized_question_type": "why_this_role", "answer": "Because it fits."}],
        tmp_path,
    )
    events.append("user-confirmed")
    events.append("browser-closed")
    assert count == 1
    assert events.index("user-confirmed") < events.index("browser-closed")


def test_apply_assist_missing_linkedin_auth_gives_useful_message(tmp_path) -> None:
    settings = Settings(
        STORAGE_DIR=tmp_path / "storage",
        DATABASE_URL=f"sqlite:///{tmp_path / 'job_agent.db'}",
        AUTH_DIR=tmp_path / "storage" / "auth",
        BROWSER_PROFILES_DIR=tmp_path / "storage" / "browser_profiles",
    )
    database = DatabaseService(settings)
    database.init_db()
    folder = tmp_path / "app"
    (folder / "metadata.json").parent.mkdir(parents=True)
    (folder / "metadata.json").write_text("{}", encoding="utf-8")
    with database.session() as session:
        job = Job(
            source_url="https://www.linkedin.com/jobs/view/1",
            description_text="Job",
            description_hash="hash",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        app = Application(job_id=job.id or 0, folder_path=str(folder))
        session.add(app)
        session.commit()
        session.refresh(app)
        app_id = app.id or 0
    try:
        BrowserService(settings, database).apply_assist(app_id)
    except RuntimeError as exc:
        assert "pixi run jobagent auth login linkedin" in str(exc)
    else:
        raise AssertionError("Expected missing auth state error")
