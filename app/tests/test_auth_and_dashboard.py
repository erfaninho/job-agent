from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import Settings
from app.main import dashboard_stats
from app.models.application import Application, Job
from app.services.auth_session_service import AuthSessionService
from app.services.source_detection import detect_source_site


def test_auth_paths_and_status(tmp_path: Path) -> None:
    settings = Settings(
        STORAGE_DIR=tmp_path / "storage",
        AUTH_DIR=tmp_path / "storage" / "auth",
        BROWSER_PROFILES_DIR=tmp_path / "storage" / "browser_profiles",
        INDEED_AUTH_STATE=tmp_path / "storage" / "auth" / "indeed_storage_state.json",
        LINKEDIN_AUTH_STATE=tmp_path / "storage" / "auth" / "linkedin_storage_state.json",
        INDEED_BROWSER_PROFILE=tmp_path / "storage" / "browser_profiles" / "indeed",
        LINKEDIN_BROWSER_PROFILE=tmp_path / "storage" / "browser_profiles" / "linkedin",
        DEFAULT_BROWSER_PROFILE=tmp_path / "storage" / "browser_profiles" / "default",
    )
    service = AuthSessionService(settings)
    assert service.get_auth_state_path("indeed").name == "indeed_storage_state.json"
    assert service.get_browser_profile_path("linkedin").name == "linkedin"
    assert service.auth_status("indeed")["auth_state_exists"] is False
    state = service.get_auth_state_path("indeed")
    state.parent.mkdir(parents=True)
    state.write_text("{}", encoding="utf-8")
    assert service.auth_status("indeed")["auth_state_exists"] is True


def test_auth_login_save_behavior_mocked(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(
        STORAGE_DIR=tmp_path / "storage",
        AUTH_DIR=tmp_path / "storage" / "auth",
        BROWSER_PROFILES_DIR=tmp_path / "storage" / "browser_profiles",
        INDEED_AUTH_STATE=tmp_path / "storage" / "auth" / "indeed_storage_state.json",
        INDEED_BROWSER_PROFILE=tmp_path / "storage" / "browser_profiles" / "indeed",
    )

    class Page:
        def goto(self, url: str) -> None:
            assert url == "https://uk.indeed.com/"

    class Context:
        def new_page(self) -> Page:
            return Page()

        def storage_state(self, path: str) -> None:
            Path(path).write_text("{}", encoding="utf-8")

        def close(self) -> None:
            pass

    class Chromium:
        def launch_persistent_context(self, user_data_dir: str, headless: bool) -> Context:
            assert "indeed" in user_data_dir
            assert headless is False
            return Context()

    class Playwright:
        chromium = Chromium()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    monkeypatch.setattr("app.services.auth_session_service.sync_playwright", lambda: Playwright())
    state = AuthSessionService(settings).login("indeed", input_func=lambda _prompt: "")
    assert state.exists()


def test_source_site_detection() -> None:
    assert detect_source_site("https://uk.indeed.com/viewjob?jk=1") == "indeed"
    assert detect_source_site("https://www.linkedin.com/jobs/view/1") == "linkedin"
    assert detect_source_site("https://jobs.lever.co/acme") == "lever"
    assert detect_source_site("https://example.com/job") == "default"


def test_dashboard_stats_today_only() -> None:
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    today_app = Application(job_id=1, folder_path="a", application_date=now, submitted_at=now)
    old_app = Application(job_id=2, folder_path="b", application_date=yesterday, submitted_at=yesterday)
    rows = [
        (today_app, Job(description_text="today", description_hash="a")),
        (old_app, Job(description_text="old", description_hash="b")),
    ]
    stats = dashboard_stats(rows)
    assert stats["prepared_today"] == 1
    assert stats["submitted_today"] == 1


def test_private_files_ignored() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "storage/auth/" in gitignore
    assert "storage/browser_profiles/" in gitignore
    assert "storage/profile/profile.json" in gitignore
    assert "storage/master_cv/master_cv.tex" in gitignore
