"""RemoteOK public JSON API — https://remoteok.com/api"""
from __future__ import annotations

from dateutil import parser as dateparser

from . import get
from ..models import Job

URL = "https://remoteok.com/api"
SOURCE = "RemoteOK"


def fetch() -> list[Job]:
    jobs: list[Job] = []
    data = get(URL).json()
    for item in data:
        # first element is a legal/metadata notice, not a job
        if not isinstance(item, dict) or "position" not in item:
            continue
        posted = None
        if item.get("date"):
            try:
                posted = dateparser.parse(item["date"])
            except (ValueError, TypeError):
                posted = None
        jobs.append(
            Job(
                title=item.get("position", ""),
                company=item.get("company", ""),
                url=item.get("url", ""),
                source=SOURCE,
                location=item.get("location", "Remote"),
                description=item.get("description", ""),
                salary=(
                    f"${item['salary_min']:,}–${item['salary_max']:,}"
                    if item.get("salary_min") and item.get("salary_max")
                    else ""
                ),
                tags=item.get("tags", []) or [],
                posted=posted,
            )
        )
    return jobs
