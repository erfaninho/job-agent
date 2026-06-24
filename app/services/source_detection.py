from urllib.parse import urlparse


def detect_source_site(url: str) -> str:
    hostname = (urlparse(url).hostname or "").lower()
    if "indeed." in hostname:
        return "indeed"
    if "linkedin.com" in hostname:
        return "linkedin"
    if "greenhouse.io" in hostname:
        return "greenhouse"
    if "lever.co" in hostname:
        return "lever"
    if "myworkdayjobs.com" in hostname or "workdayjobs.com" in hostname:
        return "workday"
    if "ashbyhq.com" in hostname:
        return "ashby"
    if "smartrecruiters.com" in hostname:
        return "smartrecruiters"
    if "teamtailor.com" in hostname:
        return "teamtailor"
    if "workable.com" in hostname:
        return "workable"
    if "recruitee.com" in hostname:
        return "recruitee"
    if "bamboohr.com" in hostname:
        return "bamboohr"
    return "default"


def infer_source_from_url(url: str | None) -> str:
    if not url:
        return "unknown"
    detected = detect_source_site(url)
    return "unknown" if detected == "default" else detected
