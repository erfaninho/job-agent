from app.models.job_parser import ParsedJob
from app.models.profile import CandidateProfile
from app.services.model_provider import ModelProvider, ModelProviderError
from app.services.scoring_service import FitScore


class CoverLetterWriterAgent:
    def __init__(self, provider: ModelProvider | None = None):
        self.provider = provider

    def write(self, parsed: ParsedJob, profile: CandidateProfile, fit: FitScore) -> str:
        if self.provider is not None:
            try:
                return self.provider.generate_text(
                    "Write a concise 250-400 word cover letter. Use only approved profile facts "
                    "and job-post facts. Do not invent company facts.",
                    (
                        f"Parsed job:\n{parsed.model_dump_json()}\n\n"
                        f"Profile:\n{profile.model_dump_json()}\n\n"
                        f"Fit score:\n{fit.to_dict()}"
                    ),
                )
            except ModelProviderError:
                pass
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
