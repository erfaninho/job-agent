from dataclasses import dataclass


SAFETY_RULES = (
    "Do not build an unattended mass-application bot.",
    "Do not bypass CAPTCHA.",
    "Do not auto-submit applications.",
    "Do not answer sensitive questions without user-approved data.",
    "Always show a review screen before filling sensitive fields.",
    "The user must manually confirm submission.",
    "Never evade platform rate limits.",
    "Never scrape LinkedIn or Indeed at scale.",
    "Never fabricate skills, education, experience, dates, or work authorization.",
    "Always pause before final application submission.",
    "Always store the generated CV and cover letter used for each application.",
    "Always keep the original job description.",
)


@dataclass(frozen=True)
class SafetyPolicy:
    rules: tuple[str, ...] = SAFETY_RULES

    def require_manual_submission(self) -> bool:
        return True

    def validate_claims(self, generated_text: str, allowed_facts: list[str]) -> list[str]:
        lower_facts = {fact.lower() for fact in allowed_facts if fact.strip()}
        warnings: list[str] = []
        risky_phrases = ("years of experience", "expert in", "authorized to work", "led a team")
        for phrase in risky_phrases:
            if phrase in generated_text.lower() and not any(phrase in fact for fact in lower_facts):
                warnings.append(f"Potentially unsupported claim: {phrase}")
        return warnings
