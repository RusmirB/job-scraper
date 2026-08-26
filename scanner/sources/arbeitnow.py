"""Arbeitnow public job board API — https://www.arbeitnow.com/api/job-board-api"""
from __future__ import annotations

from datetime import datetime, timezone

from . import get
from ..models import Job

URL = "https://www.arbeitnow.com/api/job-board-api"
SOURCE = "Arbeitnow"


def fetch(max_pages: int = 3) -> list[Job]:
    jobs: list[Job] = []
    url = URL
    for _ in range(max_pages):
        payload = get(url).json()
        for item in payload.get("data", []):
            posted = None
            ts = item.get("created_at")
            if isinstance(ts, (int, float)):
                posted = datetime.fromtimestamp(ts, tz=timezone.utc)
            jobs.append(
                Job(
                    title=item.get("title", ""),
                    company=item.get("company_name", ""),
                    url=item.get("url", ""),
                    source=SOURCE,
                    location=item.get("location", "")
                    + (" (remote)" if item.get("remote") else ""),
                    description=item.get("description", ""),
                    tags=item.get("tags", []) or [],
                    posted=posted,
                )
            )
        url = payload.get("links", {}).get("next")
        if not url:
            break
    return jobs
