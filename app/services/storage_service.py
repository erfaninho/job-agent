import json
import shutil
from pathlib import Path
from typing import Any

from app.config import Settings
from app.models.profile import CandidateProfile, DEFAULT_ANSWER_BANK


class StorageService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def ensure_base_dirs(self) -> None:
        for path in (
            self.settings.storage_path,
            self.settings.storage_path / "master_cv",
            self.settings.storage_path / "profile",
            self.settings.applications_path,
            Path("drafts"),
        ):
            path.mkdir(parents=True, exist_ok=True)

    def setup_profile(self) -> CandidateProfile:
        self.ensure_base_dirs()
        profile = CandidateProfile(master_cv_tex_path=self.settings.master_cv_path)
        if not self.settings.profile_path.exists():
            self.write_json(self.settings.profile_path, profile.model_dump(mode="json"))
        if not self.settings.answer_bank_path.exists():
            self.write_json(
                self.settings.answer_bank_path,
                [item.model_dump(mode="json") for item in DEFAULT_ANSWER_BANK],
            )
        return profile

    def import_cv(self, source_path: Path) -> Path:
        self.ensure_base_dirs()
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        shutil.copyfile(source_path, self.settings.master_cv_path)
        profile = self.load_profile()
        profile.master_cv_tex_path = self.settings.master_cv_path
        self.write_json(self.settings.profile_path, profile.model_dump(mode="json"))
        return self.settings.master_cv_path

    def load_profile(self) -> CandidateProfile:
        if not self.settings.profile_path.exists():
            return self.setup_profile()
        return CandidateProfile.model_validate(self.read_json(self.settings.profile_path))

    def require_master_cv(self) -> Path:
        if not self.settings.master_cv_path.exists():
            raise RuntimeError("Master CV missing. Run: pixi run jobagent import-cv ./path/to/cv.tex")
        return self.settings.master_cv_path

    @staticmethod
    def read_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def write_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
