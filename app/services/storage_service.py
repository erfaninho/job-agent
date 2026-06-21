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
        for path in [*self.settings.required_folders(), Path("drafts"), Path("scripts"), Path("tests")]:
            path.mkdir(parents=True, exist_ok=True)

    def setup_profile(self) -> CandidateProfile:
        self.ensure_base_dirs()
        profile = CandidateProfile(master_cv_tex_path=self.settings.master_cv_path)
        if not self.settings.profile_path.exists():
            self.write_json(self.settings.profile_path, profile.model_dump(mode="json"))
        if not self.settings.answer_bank_path.exists():
            self.write_json(self.settings.answer_bank_path, self.default_answer_bank_dict())
        self._write_json_if_missing(
            self.settings.facts_path,
            {
                "approved_facts": [],
                "blocked_claims": [
                    "Do not claim skills that are not in the CV or approved profile.",
                    "Do not claim work authorization unless confirmed by the user.",
                    "Do not claim years of experience unless explicitly stated.",
                    "Do not claim leadership experience unless explicitly confirmed.",
                ],
            },
        )
        self._write_json_if_missing(
            self.settings.preferences_path,
            {
                "target_roles": [],
                "preferred_locations": [],
                "remote_preference": "",
                "preferred_industries": [],
                "minimum_salary": None,
                "avoid": [],
            },
        )
        self._write_json_if_missing(
            self.settings.links_path,
            {"linkedin": "", "github": "", "portfolio": "", "personal_website": ""},
        )
        self._write_json_if_missing(
            self.settings.documents_path,
            {
                "master_cv_tex": str(self.settings.master_cv_path),
                "master_cv_pdf": str(self.settings.master_cv_pdf_path),
                "default_cover_letter_template": None,
                "transcript": None,
                "degree_certificate": None,
                "right_to_work_document": None,
                "references": None,
            },
        )
        self._write_json_if_missing(
            self.settings.sensitive_answers_example_path,
            {
                "salary_expectation": "",
                "notice_period": "",
                "work_authorisation": "",
                "visa_sponsorship": "",
                "requires_manual_approval": True,
            },
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

    def validate_profile(self) -> list[str]:
        missing = []
        for path in (
            self.settings.profile_path,
            self.settings.facts_path,
            self.settings.answer_bank_path,
            self.settings.preferences_path,
            self.settings.links_path,
            self.settings.documents_path,
        ):
            if not path.exists():
                missing.append(str(path))
        if not self.settings.master_cv_path.exists():
            missing.append(str(self.settings.master_cv_path))
        return missing

    @staticmethod
    def default_answer_bank_dict() -> dict[str, dict[str, object]]:
        return {
            item.key: {
                "base_answer": item.base_answer,
                "can_be_tailored": item.can_be_tailored,
                "requires_manual_confirmation": item.requires_manual_confirmation,
            }
            for item in DEFAULT_ANSWER_BANK
        }

    @staticmethod
    def read_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def write_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _write_json_if_missing(self, path: Path, data: Any) -> None:
        if not path.exists():
            self.write_json(path, data)
