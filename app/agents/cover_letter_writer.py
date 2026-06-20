from app.models.job_parser import ParsedJob
from app.models.profile import CandidateProfile
from app.services.scoring_service import FitScore


class CoverLetterWriterAgent:
    def write(self, parsed: ParsedJob, profile: CandidateProfile, fit: FitScore) -> str:
        company = parsed.company or "your team"
        role = parsed.title or "this role"
        skills = ", ".join(fit.strong_matches[:5]) or ", ".join(profile.skills[:5])
        return (
            f"Dear {company} hiring team,\n\n"
            f"I am interested in {role} because it aligns with my approved background in {skills}. "
            "I enjoy building practical, reliable software and working on systems where engineering "
            "quality has a direct effect on users. The responsibilities described in the job posting "
            "match the kind of focused backend and product work I am looking for next.\n\n"
            "I would welcome the chance to discuss how my experience, projects, and working style fit "
            "the role. Thank you for considering my application.\n\n"
            f"Kind regards,\n{profile.name or '[Your name]'}\n"
        )
