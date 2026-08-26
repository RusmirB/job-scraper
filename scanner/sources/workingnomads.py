"""Working Nomads public feed — https://www.workingnomads.com/api/exposed_jobs/
Free, no key. Small but fresh remote-jobs set; title filter keeps the QA ones."""
from __future__ import annotations

from dateutil import parser as dateparser

from . import get
from ..models import Job

URL = "https://www.workingnomads.com/api/exposed_jobs/"
SOURCE = "WorkingNomads"


def fetch() -> list[Job]:
    jobs: list[Job] = []
    for item in get(URL).json():
        posted = None
        if item.get("pub_date"):
            try:
                posted = dateparser.parse(item["pub_date"])
            except (ValueError, TypeError):
                posted = None
        tags = item.get("tags", "")
        jobs.append(
            Job(
                title=item.get("title", ""),
                company=item.get("company_name", ""),
                url=item.get("url", ""),
                source=SOURCE,
                location=item.get("location", "Remote"),
                description=item.get("description", ""),
                tags=[t.strip() for t in tags.split(",")] if isinstance(tags, str) else tags,
                posted=posted,
            )
        )
    return jobs
