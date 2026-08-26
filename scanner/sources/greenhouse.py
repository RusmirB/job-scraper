"""Greenhouse public board API — one board per company slug.
https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
"""
from __future__ import annotations

from dateutil import parser as dateparser

from . import get, parallel
from ..models import Job

SOURCE = "Greenhouse"


def _one(slug: str) -> list[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        data = get(url, params={"content": "true"}).json()
    except Exception as exc:  # noqa: BLE001 - one bad slug shouldn't kill the run
        print(f"  [greenhouse] {slug} failed: {exc}")
        return []
    jobs: list[Job] = []
    for item in data.get("jobs", []):
        # first_published is the real posting date; updated_at is the last edit and
        # runs a month newer on half the board (years, on some), so it only serves
        # as a fallback.
        posted = None
        for key in ("first_published", "updated_at"):
            if item.get(key):
                try:
                    posted = dateparser.parse(item[key])
                    break
                except (ValueError, TypeError):
                    posted = None
        loc = (item.get("location") or {}).get("name", "")
        jobs.append(
            Job(
                title=item.get("title", ""),
                company=slug.title(),
                url=item.get("absolute_url", ""),
                source=SOURCE,
                location=loc,
                description=item.get("content", ""),
                posted=posted,
            )
        )
    return jobs


def fetch(slugs: list[str]) -> list[Job]:
    return parallel(_one, slugs)
