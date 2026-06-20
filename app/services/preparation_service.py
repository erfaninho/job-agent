import json
from pathlib import Path

from sqlmodel import select

from app.agents.application_planner import ApplicationPlannerAgent
from app.agents.cover_letter_writer import CoverLetterWriterAgent
from app.agents.cv_tailor import CVTailorAgent
from app.agents.form_answer_writer import build_generated_answer
from app.agents.job_parser import JobParserAgent
from app.agents.reviewer import ReviewerAgent
from app.config import Settings
from app.models.application import Application, ApplicationStatus, GeneratedDocument, Job
from app.services.database import DatabaseService
from app.services.folder_service import FolderService
from app.services.latex_service import LatexService
from app.services.scoring_service import ScoringService
from app.services.storage_service import StorageService


class PreparationService:
    def __init__(self, settings: Settings, database: DatabaseService):
        self.settings = settings
        self.database = database
        self.storage = StorageService(settings)
        self.folders = FolderService(settings)

    def prepare(self, job_id: int, no_cover_letter: bool = False, dry_run: bool = False) -> dict[str, object]:
        self.storage.require_master_cv()
        profile = self.storage.load_profile()
        with self.database.session() as session:
            job = session.exec(select(Job).where(Job.id == job_id)).one()
        parsed = JobParserAgent().parse(job.description_text)
        company = parsed.company or job.company
        title = parsed.title or job.title
        if dry_run:
            fit = ScoringService().score(parsed, profile)
            return {
                "company": company,
                "role": title,
                "fit_score": fit.score,
                "recommendation": fit.recommendation,
                "writes": "none (dry run)",
            }

        with self.database.session() as session:
            job = session.exec(select(Job).where(Job.id == job_id)).one()
            job.company = company
            job.title = title
            job.location = parsed.location
            job.remote_type = parsed.remote_type
            job.status = ApplicationStatus.analyzed.value
            session.add(job)
            session.commit()
            session.refresh(job)

        folder = self.folders.create_application_folder(job)
        application = Application(job_id=job.id or 0, folder_path=str(folder))
        with self.database.session() as session:
            session.add(application)
            session.commit()
            session.refresh(application)
            app_id = application.id or 0
        self.folders.initialize_files(folder, job, application)
        self.database.add_event(app_id, "folder_created", str(folder))

        analysis_path = folder / "01_analysis" / "extracted_requirements.json"
        analysis_path.write_text(parsed.model_dump_json(indent=2), encoding="utf-8")
        fit = ScoringService().score(parsed, profile)
        (folder / "01_analysis" / "fit_score.json").write_text(
            json.dumps(fit.to_dict(), indent=2), encoding="utf-8"
        )
        strategy = ApplicationPlannerAgent().plan(parsed, profile, fit)
        (folder / "01_analysis" / "tailoring_strategy.md").write_text(strategy, encoding="utf-8")

        cv_path = CVTailorAgent().tailor(
            self.settings.master_cv_path, folder / "02_cv" / "cv_tailored.tex", parsed, profile
        )
        pdf_path = LatexService(self.settings.latex_compiler).compile(cv_path)
        cover_letter_path: Path | None = None
        if not no_cover_letter:
            cover_letter_path = folder / "03_cover-letter" / "cover_letter.md"
            cover_letter_path.write_text(
                CoverLetterWriterAgent().write(parsed, profile, fit), encoding="utf-8"
            )

        answers = [
            build_generated_answer(
                "Why this role?",
                (
                    f"I am interested in {title} because it aligns with my approved experience "
                    f"and skills including {', '.join(fit.strong_matches[:4]) or 'the strengths in my CV'}."
                ),
                fit.strong_matches,
            ).to_dict()
        ]
        answers_json = folder / "04_application" / "application_answers.json"
        answers_json.write_text(json.dumps(answers, indent=2), encoding="utf-8")
        (folder / "04_application" / "application_answers.md").write_text(
            "\n\n".join(f"## {a['question_label']}\n\n{a['answer']}" for a in answers),
            encoding="utf-8",
        )

        review = ReviewerAgent().review(has_cv=cv_path.exists(), has_cover_letter=bool(cover_letter_path), unsupported_claims=[])
        (folder / "04_application" / "submission_review.md").write_text(
            "# Submission Review\n\n" + json.dumps(review.to_dict(), indent=2), encoding="utf-8"
        )

        with self.database.session() as session:
            app = session.exec(select(Application).where(Application.id == app_id)).one()
            app.status = (
                ApplicationStatus.ready_to_apply.value
                if review.approved
                else ApplicationStatus.needs_review.value
            )
            app.fit_score = fit.score
            app.cv_tex_path = str(cv_path)
            app.cv_pdf_path = str(pdf_path) if pdf_path else None
            app.cover_letter_path = str(cover_letter_path) if cover_letter_path else None
            session.add(app)
            session.add(GeneratedDocument(application_id=app_id, document_type="cv_tex", path=str(cv_path)))
            if cover_letter_path:
                session.add(
                    GeneratedDocument(
                        application_id=app_id,
                        document_type="cover_letter",
                        path=str(cover_letter_path),
                    )
                )
            session.commit()
        metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        metadata.update(
            {
                "status": review.final_recommendation,
                "fit_score": fit.score,
                "recommendation": fit.recommendation,
                "cv_tex_path": str(cv_path),
                "cv_pdf_path": str(pdf_path) if pdf_path else None,
                "cover_letter_path": str(cover_letter_path) if cover_letter_path else None,
            }
        )
        self.folders.write_metadata(folder, metadata)
        return {
            "application_id": app_id,
            "company": company,
            "role": title,
            "location": parsed.location or parsed.remote_type,
            "fit_score": fit.score,
            "recommendation": fit.recommendation,
            "cv_path": str(cv_path),
            "cv_pdf_path": str(pdf_path) if pdf_path else "not compiled",
            "cover_letter_path": str(cover_letter_path) if cover_letter_path else "not generated",
            "application_folder_path": str(folder),
            "status": review.final_recommendation,
            "warnings": [] if pdf_path else ["CV PDF was not compiled; see latex_compile_error.log."],
        }
