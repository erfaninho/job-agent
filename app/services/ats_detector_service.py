from urllib.parse import urlparse


class ATSDetectorService:
    ATS_PATTERNS = {
        "greenhouse": ("greenhouse.io", "boards.greenhouse.io"),
        "lever": ("lever.co", "jobs.lever.co"),
        "workday": ("myworkdayjobs.com", "workdayjobs.com"),
        "ashby": ("ashbyhq.com",),
        "smartrecruiters": ("smartrecruiters.com",),
        "teamtailor": ("teamtailor.com",),
        "workable": ("workable.com",),
        "recruitee": ("recruitee.com",),
        "bamboohr": ("bamboohr.com",),
    }

    def detect(self, url: str, page_text: str = "") -> str:
        hostname = urlparse(url).hostname or ""
        haystack = f"{hostname} {page_text}".lower()
        for platform, patterns in self.ATS_PATTERNS.items():
            if any(pattern in haystack for pattern in patterns):
                return platform
        return "unknown_custom"
