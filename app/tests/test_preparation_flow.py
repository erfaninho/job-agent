from pathlib import Path

from app.config import Settings
from app.services.database import DatabaseService
from app.services.job_input_service import JobInputService
from app.services.preparation_service import PreparationService
from app.services.storage_service import StorageService


def test_prepare_flow_creates_application_package(tmp_path: Path) -> None:
    settings = Settings(
        JOBAGENT_STORAGE_PATH=tmp_path / "storage",
        JOBAGENT_DATABASE_URL=f"sqlite:///{tmp_path / 'jobagent.db'}",
    )
    database = DatabaseService(settings)
    database.init_db()
    storage = StorageService(settings)
    storage.setup_profile()
    cv = tmp_path / "cv.tex"
    cv.write_text(r"\documentclass{article}\begin{document}Python Django SQL\end{document}", encoding="utf-8")
    storage.import_cv(cv)
    job = JobInputService(database).add_from_text(
        "Company: Acme\nRole: Python Developer\nLocation: Remote\nRequired Python Django SQL"
    )
    summary = PreparationService(settings, database).prepare(job.id or 0)
    folder = Path(str(summary["application_folder_path"]))
    assert (folder / "01_analysis" / "fit_score.json").exists()
    assert "prompt_version" in (folder / "01_analysis" / "model_usage.json").read_text(
        encoding="utf-8"
    )
    assert (folder / "02_cv" / "cv_tailored.tex").exists()
    assert (folder / "03_cover-letter" / "cover_letter.md").exists()
    assert (folder / "04_application" / "application_answers.generated.json").exists()
