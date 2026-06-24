from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from playwright.sync_api import sync_playwright

from app.config import Settings


SUPPORTED_AUTH_SITES = {
    "indeed": "https://uk.indeed.com/",
    "linkedin": "https://www.linkedin.com/",
    "greenhouse": "https://boards.greenhouse.io/",
    "lever": "https://jobs.lever.co/",
    "workday": "https://www.myworkdayjobs.com/",
    "default": "about:blank",
}


class AuthSessionService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_auth_state_path(self, site: str) -> Path:
        normalized = self._normalize_site(site)
        if normalized == "linkedin":
            return self.settings.linkedin_auth_state
        if normalized == "indeed":
            return self.settings.indeed_auth_state
        return self.settings.auth_dir / f"{normalized}_storage_state.json"

    def get_browser_profile_path(self, site: str) -> Path:
        normalized = self._normalize_site(site)
        if normalized == "linkedin":
            return self.settings.linkedin_browser_profile
        if normalized == "indeed":
            return self.settings.indeed_browser_profile
        if normalized == "default":
            return self.settings.default_browser_profile
        return self.settings.browser_profiles_dir / normalized

    def login(self, site: str, input_func: Callable[[str], str] = input) -> Path:
        normalized = self._normalize_site(site)
        state_path = self.get_auth_state_path(normalized)
        profile_path = self.get_browser_profile_path(normalized)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),
                headless=False,
            )
            page = context.new_page()
            page.goto(SUPPORTED_AUTH_SITES.get(normalized, SUPPORTED_AUTH_SITES["default"]))
            input_func(
                "Log in manually in the opened browser. Complete any 2FA/CAPTCHA manually. "
                "When logged in, return here and press Enter. No password will be stored."
            )
            context.storage_state(path=str(state_path))
            context.close()
        return state_path

    def auth_status(self, site: str) -> dict[str, object]:
        normalized = self._normalize_site(site)
        path = self.get_auth_state_path(normalized)
        last_modified = None
        if path.exists():
            last_modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        return {
            "site": normalized,
            "auth_state_exists": path.exists(),
            "auth_state_path": str(path),
            "last_modified": last_modified,
        }

    def all_statuses(self) -> list[dict[str, object]]:
        return [self.auth_status(site) for site in SUPPORTED_AUTH_SITES]

    def logout(self, site: str, delete_profile: bool = False) -> None:
        normalized = self._normalize_site(site)
        state_path = self.get_auth_state_path(normalized)
        if state_path.exists():
            state_path.unlink()
        if delete_profile:
            profile_path = self.get_browser_profile_path(normalized)
            if profile_path.exists():
                for child in sorted(profile_path.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink()
                    elif child.is_dir():
                        child.rmdir()
                profile_path.rmdir()

    @staticmethod
    def _normalize_site(site: str) -> str:
        normalized = site.strip().lower()
        if normalized not in SUPPORTED_AUTH_SITES:
            return "default" if normalized in {"", "unknown"} else normalized
        return normalized
