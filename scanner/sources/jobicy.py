"""Jobicy public API — https://jobicy.com/api/v2/remote-jobs"""
from __future__ import annotations

from dateutil import parser as dateparser

from . import get
from ..models import Job

URL = "https://jobicy.com/api/v2/remote-jobs"
SOURCE = "Jobicy"


def fetch() -> list[Job]:
    jobs: list[Job] = []
    # 'count' is the only widely-accepted filter; we re-filter for QA locally
    data = get(URL, params={"count": 50}).json()
    for item in data.get("jobs", []):
        posted = None
        if item.get("pubDate"):
            try:
                posted = dateparser.parse(item["pubDate"])
            except (ValueError, TypeError):
                posted = None
        jobs.append(
            Job(
                title=item.get("jobTitle", ""),
                company=item.get("companyName", ""),
                url=item.get("url", ""),
                source=SOURCE,
                location=item.get("jobGeo", "Remote"),
                description=item.get("jobExcerpt", "") or item.get("jobDescription", ""),
                tags=item.get("jobIndustry", []) or [],
                posted=posted,
            )
        )
    return jobs
