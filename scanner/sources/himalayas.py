"""Himalayas public API — https://himalayas.app/jobs/api"""
from __future__ import annotations

from datetime import datetime, timezone

from . import get
from ..models import Job

URL = "https://himalayas.app/jobs/api"
SOURCE = "Himalayas"


def fetch() -> list[Job]:
    jobs: list[Job] = []
    data = get(URL, params={"limit": 100}).json()
    for item in data.get("jobs", []):
        posted = None
        ts = item.get("pubDate")
        if isinstance(ts, (int, float)):
            posted = datetime.fromtimestamp(ts, tz=timezone.utc)
        locations = item.get("locationRestrictions") or []
        jobs.append(
            Job(
                title=item.get("title", ""),
                company=item.get("companyName", ""),
                url=item.get("applicationLink") or item.get("guid", ""),
                source=SOURCE,
                location=", ".join(locations) if locations else "Worldwide",
                description=item.get("excerpt", "") or item.get("description", ""),
                tags=item.get("categories", []) or [],
                posted=posted,
            )
        )
    return jobs
