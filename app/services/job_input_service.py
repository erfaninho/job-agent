import hashlib
import re
from pathlib import Path
from urllib.request import Request, urlopen

from sqlmodel import select

from app.agents.job_parser import JobParserAgent
from app.models.application import Job
from app.services.database import DatabaseService
from app.services.source_detection import infer_source_from_url


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def description_hash(text: str) -> str:
    return hashlib.sha256(normalize_whitespace(text).lower().encode("utf-8")).hexdigest()


def extract_source_url_from_text(text: str) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        match = re.match(r"(?i)^(source url|original url|url)\s*:\s*(https?://\S+)?\s*$", stripped)
        if not match:
            continue
        inline_url = match.group(2)
        if inline_url:
            return inline_url.strip()
        if stripped.rstrip().endswith(":"):
            for next_line in lines[index + 1 : index + 4]:
                candidate = next_line.strip()
                if re.match(r"(?i)^https?://\S+$", candidate):
                    return candidate
    generic = re.search(r"(?im)^\s*(https?://\S+)\s*$", text)
    return generic.group(1).strip() if generic else None


class JobInputService:
    def __init__(self, database: DatabaseService):
        self.database = database

    def add_from_file(
        self,
        path: Path,
        source_url: str | None = None,
        source: str | None = None,
    ) -> Job:
        text = path.read_text(encoding="utf-8")
        resolved_url = source_url or extract_source_url_from_text(text)
        resolved_source = source or infer_source_from_url(resolved_url)
        return self.add_from_text(text, source=resolved_source, source_url=resolved_url)

    def add_from_text(
        self,
        text: str,
        source_url: str | None = None,
        source: str | None = None,
    ) -> Job:
        normalized = normalize_whitespace(text)
        if not normalized:
            raise ValueError("Job description cannot be empty.")
        resolved_url = source_url or extract_source_url_from_text(text)
        resolved_source = source or infer_source_from_url(resolved_url)
        digest = description_hash(normalized)
        duplicate = self.database.find_duplicate_job(digest, resolved_url)
        if duplicate:
            return duplicate
        parsed = JobParserAgent().parse(text)
        duplicate_by_name = self._find_duplicate_by_company_title(parsed.company, parsed.title)
        if duplicate_by_name:
            return duplicate_by_name
        job = Job(
            company=parsed.company or "Unknown company",
            title=parsed.title or "Unknown role",
            location=parsed.location,
            remote_type=parsed.remote_type,
            description_text=normalized,
            description_hash=digest,
            source=resolved_source,
            source_url=resolved_url,
        )
        with self.database.session() as session:
            session.add(job)
            session.commit()
            session.refresh(job)
            self.database.add_event(None, "job_added", f"Added job {job.id} from {resolved_source}")
            return job

    def add_from_url(self, url: str) -> Job:
        request = Request(url, headers={"User-Agent": "jobagent-local-assistant/0.1"})
        with urlopen(request, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = normalize_whitespace(title_match.group(1)) if title_match else "URL job posting"
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        job = self.add_from_text(
            f"{title}\n\n{text}", source=infer_source_from_url(url), source_url=url
        )
        with self.database.session() as session:
            stored = session.exec(select(Job).where(Job.id == job.id)).one()
            if stored.title == "Unknown role":
                stored.title = title
            session.add(stored)
            session.commit()
            session.refresh(stored)
            return stored

    def set_source_url(self, job_id: int, source_url: str, source: str | None = None) -> Job:
        with self.database.session() as session:
            job = session.exec(select(Job).where(Job.id == job_id)).one()
            job.source_url = source_url
            job.source = source or infer_source_from_url(source_url)
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def _find_duplicate_by_company_title(self, company: str | None, title: str | None) -> Job | None:
        if not company or not title:
            return None
        with self.database.session() as session:
            return session.exec(
                select(Job).where(Job.company == company).where(Job.title == title)
            ).first()
