"""The Muse public API — https://www.themuse.com/developers/api/v2
Free, no key. No keyword search, so we page through engineering categories and
let the title filter keep QA/SDET roles."""
from __future__ import annotations

from dateutil import parser as dateparser

from . import get
from ..models import Job

URL = "https://www.themuse.com/api/public/jobs"
SOURCE = "TheMuse"
CATEGORIES = ["Software Engineering", "Data and Analytics"]
MAX_PAGES = 5


def fetch() -> list[Job]:
    jobs: list[Job] = []
    for category in CATEGORIES:
        for page in range(1, MAX_PAGES + 1):
            data = get(
                URL, params={"category": category, "page": page}
            ).json()
            results = data.get("results", [])
            if not results:
                break
            for item in results:
                posted = None
                if item.get("publication_date"):
                    try:
                        posted = dateparser.parse(item["publication_date"])
                    except (ValueError, TypeError):
                        posted = None
                locs = ", ".join(l.get("name", "") for l in item.get("locations", []))
                jobs.append(
                    Job(
                        title=item.get("name", ""),
                        company=(item.get("company") or {}).get("name", ""),
                        url=(item.get("refs") or {}).get("landing_page", ""),
                        source=SOURCE,
                        location=locs or "See listing",
                        description=item.get("contents", ""),
                        posted=posted,
                    )
                )
    return jobs
