from dataclasses import asdict, dataclass


@dataclass
class ReviewResult:
    approved: bool
    required_fixes: list[str]
    suggested_improvements: list[str]
    risk_notes: list[str]
    final_recommendation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ReviewerAgent:
    def review(self, has_cv: bool, has_cover_letter: bool, unsupported_claims: list[str]) -> ReviewResult:
        required_fixes = []
        if not has_cv:
            required_fixes.append("Tailored CV is missing.")
        if unsupported_claims:
            required_fixes.extend(unsupported_claims)
        return ReviewResult(
            approved=not required_fixes,
            required_fixes=required_fixes,
            suggested_improvements=[] if has_cover_letter else ["Consider generating a cover letter."],
            risk_notes=unsupported_claims,
            final_recommendation="ready_to_apply" if not required_fixes else "needs_review",
        )
