from pathlib import Path

from app.models.job_parser import ParsedJob
from app.models.profile import CandidateProfile


class CVTailorAgent:
    def tailor(self, master_cv_path: Path, output_path: Path, parsed: ParsedJob, profile: CandidateProfile) -> Path:
        master = master_cv_path.read_text(encoding="utf-8")
        supported = {skill.lower() for skill in profile.skills}
        keywords = [skill for skill in parsed.required_skills if skill.lower() in supported]
        summary = "% Tailored emphasis: " + (", ".join(keywords) or "general approved profile facts")
        tailored = summary + "\n" + master
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(tailored, encoding="utf-8")
        diff_path = output_path.with_name("cv_diff.md")
        diff_path.write_text(
            "# CV Tailoring Notes\n\n"
            f"- Added a LaTeX comment describing supported emphasis: {', '.join(keywords) or 'none'}.\n"
            "- Did not add unsupported employers, education, dates, or skills.\n",
            encoding="utf-8",
        )
        return output_path
