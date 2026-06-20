import hashlib
import re
from pathlib import Path
from urllib.request import Request, urlopen

from sqlmodel import select

from app.models.application import Job
from app.services.database import DatabaseService


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def description_hash(text: str) -> str:
    return hashlib.sha256(normalize_whitespace(text).lower().encode("utf-8")).hexdigest()


class JobInputService:
    def __init__(self, database: DatabaseService):
        self.database = database

    def add_from_file(self, path: Path) -> Job:
        return self.add_from_text(path.read_text(encoding="utf-8"), source=f"file:{path}")

    def add_from_text(self, text: str, source: str = "manual", source_url: str | None = None) -> Job:
        normalized = normalize_whitespace(text)
        if not normalized:
            raise ValueError("Job description cannot be empty.")
        digest = description_hash(normalized)
        duplicate = self.database.find_duplicate_job(digest, source_url)
        if duplicate:
            return duplicate
        job = Job(description_text=normalized, description_hash=digest, source=source, source_url=source_url)
        with self.database.session() as session:
            session.add(job)
            session.commit()
            session.refresh(job)
            self.database.add_event(None, "job_added", f"Added job {job.id} from {source}")
            return job

    def add_from_url(self, url: str) -> Job:
        request = Request(url, headers={"User-Agent": "jobagent-local-assistant/0.1"})
        with urlopen(request, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = normalize_whitespace(title_match.group(1)) if title_match else "URL job posting"
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        job = self.add_from_text(f"{title}\n\n{text}", source="url", source_url=url)
        with self.database.session() as session:
            stored = session.exec(select(Job).where(Job.id == job.id)).one()
            if stored.title == "Unknown role":
                stored.title = title
            session.add(stored)
            session.commit()
            session.refresh(stored)
            return stored
