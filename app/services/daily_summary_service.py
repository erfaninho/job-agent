from datetime import date, datetime

from sqlmodel import select

from app.config import Settings
from app.models.application import Application, Job
from app.services.database import DatabaseService


class DailySummaryService:
    def __init__(self, settings: Settings, database: DatabaseService):
        self.settings = settings
        self.database = database

    def write_summary(self, target_date: date | None = None) -> str:
        target = target_date or date.today()
        day_dir = self.settings.applications_path / target.isoformat()
        day_dir.mkdir(parents=True, exist_ok=True)
        applications = self._applications_for_date(target)
        prepared = [app for app, _ in applications if app.status in {"prepared", "ready_to_apply"}]
        submitted = [app for app, _ in applications if app.status == "submitted"]
        lines = [
            f"# Daily Summary - {target.isoformat()}",
            "",
            f"- Jobs added: {len(applications)}",
            f"- Applications prepared: {len(prepared)}",
            f"- Applications submitted: {len(submitted)}",
            "",
            "| Company | Role | Status | Follow-up |",
            "| --- | --- | --- | --- |",
        ]
        for app, job in applications:
            lines.append(
                f"| {job.company} | {job.title} | {app.status} | {app.follow_up_date or ''} |"
            )
        output = "\n".join(lines) + "\n"
        (day_dir / "daily_summary.md").write_text(output, encoding="utf-8")
        return output

    def _applications_for_date(self, target: date) -> list[tuple[Application, Job]]:
        with self.database.session() as session:
            apps = session.exec(select(Application)).all()
            rows: list[tuple[Application, Job]] = []
            for app in apps:
                app_date = app.application_date
                if isinstance(app_date, datetime) and app_date.date() == target:
                    job = session.exec(select(Job).where(Job.id == app.job_id)).one()
                    rows.append((app, job))
            return rows
