"""Remotive public API — https://remotive.com/api/remote-jobs"""
from __future__ import annotations

from datetime import datetime

from dateutil import parser as dateparser

from . import get
from ..models import Job

URL = "https://remotive.com/api/remote-jobs"
SOURCE = "Remotive"


def fetch() -> list[Job]:
    jobs: list[Job] = []
    # category filter narrows to QA on the server side; we still re-filter later
    data = get(URL, params={"category": "qa"}).json()
    for item in data.get("jobs", []):
        posted = None
        if item.get("publication_date"):
            try:
                posted = dateparser.parse(item["publication_date"])
            except (ValueError, TypeError):
                posted = None
        jobs.append(
            Job(
                title=item.get("title", ""),
                company=item.get("company_name", ""),
                url=item.get("url", ""),
                source=SOURCE,
                location=item.get("candidate_required_location", ""),
                description=item.get("description", ""),
                salary=item.get("salary", ""),
                tags=item.get("tags", []) or [],
                posted=posted,
            )
        )
    return jobs
