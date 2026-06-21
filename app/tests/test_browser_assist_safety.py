from typing import cast

from playwright.sync_api import Page as PlaywrightPage

from app.services.ats_detector_service import ATSDetectorService
from app.services.browser_service import BrowserService
from app.services.form_field_detector import FormFieldDetector


def test_ats_detection_common_platforms() -> None:
    detector = ATSDetectorService()
    assert detector.detect("https://jobs.lever.co/example") == "lever"
    assert detector.detect("https://boards.greenhouse.io/example") == "greenhouse"
    assert detector.detect("https://company.example/jobs") == "unknown_custom"


def test_form_field_detector_marks_submit_not_safe() -> None:
    fields = FormFieldDetector().detect_from_html(
        """
        <form>
          <label for="name">Name</label><input id="name" name="name">
          <label for="salary">Salary</label><input id="salary" name="salary">
          <button type="submit">Submit application</button>
          <input type="submit" value="Submit">
        </form>
        """
    )
    by_name = {field.name or field.input_type: field for field in fields}
    assert by_name["name"].safe_to_fill is True
    assert by_name["salary"].sensitive is True
    assert by_name["submit"].safe_to_fill is False


def test_browser_service_preview_never_clicks_submit() -> None:
    class Locator:
        def count(self) -> int:
            return 1

        def click(self) -> None:
            raise AssertionError("Submit must never be clicked")

    class Page:
        def locator(self, selector: str) -> Locator:
            assert "submit" in selector.lower() or "Submit" in selector
            return Locator()

    count = BrowserService.fill_safe_fields_preview_only(
        BrowserService.__new__(BrowserService), cast(PlaywrightPage, Page()), [{"answer": "ok"}]
    )
    assert count == 1
