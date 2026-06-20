from pathlib import Path

from app.config import Settings
from app.services.storage_service import StorageService


def test_profile_setup_and_cv_import(tmp_path: Path) -> None:
    settings = Settings(
        JOBAGENT_STORAGE_PATH=tmp_path / "storage",
        JOBAGENT_DATABASE_URL=f"sqlite:///{tmp_path / 'jobagent.db'}",
    )
    service = StorageService(settings)
    profile = service.setup_profile()
    assert profile.master_cv_tex_path == settings.master_cv_path
    cv = tmp_path / "cv.tex"
    cv.write_text(r"\documentclass{article}\begin{document}CV\end{document}", encoding="utf-8")
    imported = service.import_cv(cv)
    assert imported.exists()
    assert settings.answer_bank_path.exists()
