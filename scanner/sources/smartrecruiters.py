"""SmartRecruiters public postings API — one company per slug.
https://api.smartrecruiters.com/v1/companies/{slug}/postings
The list endpoint is lightweight (no description), so we score on title + location.
"""
from __future__ import annotations

from dateutil import parser as dateparser

from . import get, parallel
from ..models import Job

SOURCE = "SmartRecruiters"


def _one(slug: str) -> list[Job]:
    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    try:
        data = get(url, params={"limit": 100}).json()
    except Exception as exc:  # noqa: BLE001
        print(f"  [smartrecruiters] {slug} failed: {exc}")
        return []
    jobs: list[Job] = []
    for item in data.get("content", []):
        posted = None
        if item.get("releasedDate"):
            try:
                posted = dateparser.parse(item["releasedDate"])
            except (ValueError, TypeError):
                posted = None
        loc = item.get("location", {}) or {}
        loc_str = ", ".join(
            v for v in (loc.get("city"), loc.get("country")) if v
        ) or ("Remote" if loc.get("remote") else "")
        uuid = item.get("uuid") or item.get("id", "")
        jobs.append(
            Job(
                title=item.get("name", ""),
                company=slug,
                url=f"https://jobs.smartrecruiters.com/{slug}/{uuid}",
                source=SOURCE,
                location=loc_str,
                posted=posted,
            )
        )
    return jobs


def fetch(slugs: list[str]) -> list[Job]:
    return parallel(_one, slugs)
