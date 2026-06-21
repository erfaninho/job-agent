from pathlib import Path

from app.models.job_parser import ParsedJob
from app.models.profile import CandidateProfile
from app.services.model_provider import ModelProvider, ModelProviderError


class CVTailorAgent:
    def __init__(self, provider: ModelProvider | None = None):
        self.provider = provider

    def tailor(
        self, master_cv_path: Path, output_path: Path, parsed: ParsedJob, profile: CandidateProfile
    ) -> Path:
        master = master_cv_path.read_text(encoding="utf-8")
        tailored = self._tailor_with_model(master, parsed, profile) if self.provider else None
        if tailored is None:
            tailored = self._tailor_with_rules(master, parsed, profile)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(tailored, encoding="utf-8")
        diff_path = output_path.with_name("cv_diff.md")
        diff_path.write_text(
            "# CV Tailoring Notes\n\n"
            "- Generated from the approved master CV.\n"
            "- Model output is used only when available and falls back to safe local tailoring.\n"
            "- Do not add unsupported employers, education, dates, or skills.\n",
            encoding="utf-8",
        )
        return output_path

    def _tailor_with_model(
        self, master: str, parsed: ParsedJob, profile: CandidateProfile
    ) -> str | None:
        if self.provider is None:
            return None
        try:
            return self.provider.generate_text(
                "Tailor this LaTeX CV truthfully. Preserve LaTeX validity. "
                "Only reorder, shorten, and emphasize facts already present in the CV/profile. "
                "Return only complete LaTeX.",
                (
                    f"Profile facts:\n{profile.model_dump_json()}\n\n"
                    f"Parsed job:\n{parsed.model_dump_json()}\n\n"
                    f"Master CV:\n{master}"
                ),
            )
        except ModelProviderError:
            return None

    @staticmethod
    def _tailor_with_rules(master: str, parsed: ParsedJob, profile: CandidateProfile) -> str:
        supported = {skill.lower() for skill in profile.skills}
        keywords = [skill for skill in parsed.required_skills if skill.lower() in supported]
        summary = "% Tailored emphasis: " + (", ".join(keywords) or "general approved profile facts")
        return summary + "\n" + master
