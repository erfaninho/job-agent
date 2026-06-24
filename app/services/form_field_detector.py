from dataclasses import asdict, dataclass
from enum import StrEnum

from bs4 import BeautifulSoup

from app.agents.form_answer_writer import SENSITIVE_TYPES, classify_application_question


class FieldSafety(StrEnum):
    SAFE = "safe"
    SENSITIVE = "sensitive"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass
class DetectedFormField:
    tag: str
    input_type: str
    label: str
    name: str
    safe_to_fill: bool
    sensitive: bool
    safety: str = FieldSafety.UNKNOWN.value

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class FormFieldDetector:
    def detect_from_html(self, html: str) -> list[DetectedFormField]:
        soup = BeautifulSoup(html, "html.parser")
        fields: list[DetectedFormField] = []
        for element in soup.select("input, textarea, select"):
            tag = element.name or ""
            input_type = str(element.get("type", tag))
            label = self._label_for(soup, element)
            name = element.get("name") or element.get("id") or ""
            text = f"{label} {name} {input_type}"
            safety = self.classify_field_safety(text, input_type)
            sensitive = safety == FieldSafety.SENSITIVE
            safe = safety == FieldSafety.SAFE
            fields.append(
                DetectedFormField(
                    tag=tag,
                    input_type=str(input_type),
                    label=label,
                    name=str(name),
                    safe_to_fill=safe,
                    sensitive=sensitive,
                    safety=safety.value,
                )
            )
        return fields

    @staticmethod
    def classify_field_safety(label_or_name: str, input_type: str = "") -> FieldSafety:
        text = f"{label_or_name} {input_type}".lower()
        if any(
            term in text
            for term in (
                "captcha",
                "assessment",
                "coding test",
                "technical test",
                "personality",
                "submit",
                "criminal",
                "disability",
                "gender",
                "ethnicity",
                "reference",
            )
        ):
            return FieldSafety.BLOCKED
        question_type = classify_application_question(text)
        if question_type in SENSITIVE_TYPES or any(
            term in text
            for term in (
                "salary",
                "notice",
                "right to work",
                "work author",
                "visa",
                "sponsor",
                "relocat",
            )
        ):
            return FieldSafety.SENSITIVE
        if any(
            term in text
            for term in (
                "first name",
                "last name",
                "full name",
                "name",
                "email",
                "phone",
                "location",
                "city",
                "country",
                "linkedin",
                "github",
                "portfolio",
                "website",
                "resume",
                "cv",
                "cover letter",
            )
        ):
            return FieldSafety.SAFE
        if input_type.lower() in {"submit", "button", "hidden", "password"}:
            return FieldSafety.BLOCKED
        if input_type.lower() in {"text", "email", "tel", "url", "textarea", "file"}:
            return FieldSafety.SAFE
        return FieldSafety.UNKNOWN

    @staticmethod
    def _label_for(soup: BeautifulSoup, element: object) -> str:
        element_id = getattr(element, "get", lambda _name: None)("id")
        if element_id:
            label = soup.find("label", attrs={"for": element_id})
            if label:
                return str(label.get_text(" ", strip=True))
        parent = getattr(element, "parent", None)
        if parent and getattr(parent, "name", "") == "label":
            return str(parent.get_text(" ", strip=True))
        placeholder = getattr(element, "get", lambda _name: None)("placeholder")
        return str(placeholder or "")
