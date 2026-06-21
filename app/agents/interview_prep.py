from app.models.job_parser import ParsedJob


class InterviewPrepAgent:
    def generate(self, company: str, title: str, parsed: ParsedJob) -> str:
        return "\n".join(
            [
                f"# Interview Prep - {company} / {title}",
                "",
                "## Role Requirements",
                ", ".join(parsed.required_skills) or "Review the job description.",
                "",
                "## Matching Strengths",
                "Use approved CV/profile examples that match the listed requirements.",
                "",
                "## Weak Spots To Prepare",
                "Prepare concise explanations for missing or less familiar requirements.",
                "",
                "## Likely Technical Questions",
                "- Discuss relevant systems and projects from the approved CV.",
                "- Explain tradeoffs in prior backend or full-stack work.",
                "",
                "## Likely Behavioral Questions",
                "- Describe a difficult technical problem.",
                "- Explain how you learn unfamiliar tools.",
                "",
                "## Questions To Ask Recruiter",
                "- What would success look like in the first 90 days?",
                "- How does the team review and ship changes?",
                "",
                "## Salary Discussion Notes",
                "Use only manually approved salary expectations.",
            ]
        )
