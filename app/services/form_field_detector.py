from dataclasses import asdict, dataclass

from bs4 import BeautifulSoup

from app.agents.form_answer_writer import SENSITIVE_TYPES, classify_application_question


@dataclass
class DetectedFormField:
    tag: str
    input_type: str
    label: str
    name: str
    safe_to_fill: bool
    sensitive: bool

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
            question_type = classify_application_question(text)
            sensitive = question_type in SENSITIVE_TYPES or any(
                term in text.lower()
                for term in ("captcha", "assessment", "test", "gender", "ethnicity", "disability")
            )
            safe = (not sensitive) and input_type.lower() not in {"submit", "button", "hidden"}
            fields.append(
                DetectedFormField(
                    tag=tag,
                    input_type=str(input_type),
                    label=label,
                    name=str(name),
                    safe_to_fill=safe,
                    sensitive=sensitive,
                )
            )
        return fields

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
