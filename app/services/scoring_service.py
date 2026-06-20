from dataclasses import asdict, dataclass

from app.models.job_parser import ParsedJob
from app.models.profile import CandidateProfile


@dataclass
class FitScore:
    score: int
    recommendation: str
    explanation: str
    missing_requirements: list[str]
    strong_matches: list[str]
    risky_requirements: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ScoringService:
    def score(self, parsed: ParsedJob, profile: CandidateProfile) -> FitScore:
        profile_skills = {skill.lower() for skill in profile.skills}
        must = parsed.required_skills
        preferred = parsed.preferred_skills
        must_matches = [skill for skill in must if skill.lower() in profile_skills]
        preferred_matches = [skill for skill in preferred if skill.lower() in profile_skills]
        must_ratio = len(must_matches) / len(must) if must else 0.7
        preferred_ratio = len(preferred_matches) / len(preferred) if preferred else 0.7
        experience_score = 1.0 if profile.experience else 0.4
        domain_score = 1.0 if any(parsed.keywords) else 0.6
        location_score = 1.0
        salary_score = 0.8 if parsed.salary_range else 0.6
        score = round(
            must_ratio * 45
            + preferred_ratio * 20
            + experience_score * 15
            + domain_score * 10
            + location_score * 5
            + salary_score * 5
        )
        missing = [skill for skill in must if skill.lower() not in profile_skills]
        recommendation = "apply" if score >= 75 else "maybe" if score >= 50 else "skip"
        explanation = (
            f"Matched {len(must_matches)} of {len(must)} required skills and "
            f"{len(preferred_matches)} of {len(preferred)} preferred skills."
        )
        return FitScore(
            score=score,
            recommendation=recommendation,
            explanation=explanation,
            missing_requirements=missing,
            strong_matches=must_matches + preferred_matches,
            risky_requirements=missing,
        )
