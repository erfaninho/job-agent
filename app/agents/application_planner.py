from app.models.job_parser import ParsedJob
from app.models.profile import CandidateProfile
from app.services.scoring_service import FitScore


class ApplicationPlannerAgent:
    def plan(self, parsed: ParsedJob, profile: CandidateProfile, fit: FitScore) -> str:
        matches = ", ".join(fit.strong_matches) or "approved experience from the master CV"
        missing = ", ".join(fit.missing_requirements) or "none identified"
        projects = "; ".join(profile.projects[:2]) or "relevant existing projects from the CV"
        return "\n".join(
            [
                "# Tailoring Strategy",
                "",
                f"- Main selling points: emphasize {matches}.",
                f"- Skills to emphasize: {matches}.",
                f"- Projects to emphasize: {projects}.",
                "- Experience bullets to prioritize: backend, reliability, data, and user-facing impact where supported.",
                f"- Keywords to include only if supported: {', '.join(parsed.keywords) or 'none'}.",
                "- Things to avoid: unsupported years of experience, invented employers, invented seniority.",
                f"- Missing skills to handle carefully: {missing}.",
                f"- Cover letter angle: connect profile strengths to {parsed.title or 'the role'}.",
                "- Salary guidance notes: use only manually approved salary expectations.",
            ]
        )
