import re

from app.models.job_parser import ParsedJob


KNOWN_SKILLS = [
    "Python",
    "Django",
    "FastAPI",
    "SQL",
    "PostgreSQL",
    "Redis",
    "JavaScript",
    "TypeScript",
    "React",
    "Docker",
    "AWS",
    "Azure",
    "GCP",
    "Git",
    "Linux",
    "Go",
    "Flutter",
]


class JobParserAgent:
    def parse(self, description: str) -> ParsedJob:
        lines = [line.strip() for line in description.splitlines() if line.strip()]
        text = " ".join(lines) if lines else description
        company = self._match_field(description, ("company", "organisation", "organization"))
        title = self._match_field(description, ("title", "role", "position"))
        location = self._match_field(description, ("location",))
        remote_type = self._remote_type(text)
        salary = self._salary(text)
        required = self._skills(text)
        preferred = self._preferred_skills(text, required)
        responsibilities = self._bullets(description, ("responsibil", "you will", "duties"))
        questions = re.findall(r"(?i)(why .+?\?|tell us .+?\?|what .+?\?)", description)
        return ParsedJob(
            company=company,
            title=title,
            location=location,
            remote_type=remote_type,
            salary_range=salary,
            required_skills=required,
            preferred_skills=preferred,
            responsibilities=responsibilities,
            experience_level=self._experience_level(text),
            keywords=sorted(set(required + preferred)),
            questions_to_answer=questions,
        )

    @staticmethod
    def _match_field(text: str, names: tuple[str, ...]) -> str | None:
        for name in names:
            match = re.search(rf"(?im)^\s*{name}\s*[:\-]\s*([^.;\n]+)", text)
            if match:
                return match.group(1).strip()[:120]
        return None

    @staticmethod
    def _remote_type(text: str) -> str | None:
        lower = text.lower()
        if "hybrid" in lower:
            return "hybrid"
        if "remote" in lower:
            return "remote"
        if "on-site" in lower or "onsite" in lower:
            return "onsite"
        return None

    @staticmethod
    def _salary(text: str) -> str | None:
        match = re.search(r"([$£€]\s?\d[\d,]*(?:\s?[-–]\s?[$£€]?\s?\d[\d,]*)?)", text)
        return match.group(1) if match else None

    @staticmethod
    def _skills(text: str) -> list[str]:
        lower = text.lower()
        return [skill for skill in KNOWN_SKILLS if skill.lower() in lower]

    @staticmethod
    def _preferred_skills(text: str, required: list[str]) -> list[str]:
        preferred_region = ""
        match = re.search(r"(?is)(preferred|nice to have|desirable)(.*)", text)
        if match:
            preferred_region = match.group(2)
        return [skill for skill in KNOWN_SKILLS if skill in required and skill.lower() in preferred_region.lower()]

    @staticmethod
    def _experience_level(text: str) -> str | None:
        lower = text.lower()
        if "senior" in lower or "lead" in lower:
            return "senior"
        if "junior" in lower or "entry" in lower:
            return "junior"
        if "mid" in lower:
            return "mid"
        return None

    @staticmethod
    def _bullets(description: str, hints: tuple[str, ...]) -> list[str]:
        bullets = []
        for line in description.splitlines():
            clean = line.strip(" -•\t")
            if clean and any(hint in clean.lower() for hint in hints):
                bullets.append(clean[:240])
        return bullets[:10]
