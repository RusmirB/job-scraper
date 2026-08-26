"""Lever public postings API — one board per company slug.
https://api.lever.co/v0/postings/{slug}?mode=json
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import get, parallel
from ..models import Job

SOURCE = "Lever"


def _one(slug: str) -> list[Job]:
    url = f"https://api.lever.co/v0/postings/{slug}"
    try:
        data = get(url, params={"mode": "json"}).json()
    except Exception as exc:  # noqa: BLE001 - one bad slug shouldn't kill the run
        print(f"  [lever] {slug} failed: {exc}")
        return []
    jobs: list[Job] = []
    for item in data:
        posted = None
        ts = item.get("createdAt")
        if isinstance(ts, (int, float)):
            posted = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        cats = item.get("categories", {}) or {}
        jobs.append(
            Job(
                title=item.get("text", ""),
                company=slug.title(),
                url=item.get("hostedUrl", ""),
                source=SOURCE,
                location=cats.get("location", ""),
                description=item.get("descriptionPlain", "") or item.get("description", ""),
                tags=[cats.get("team", ""), cats.get("commitment", "")],
                posted=posted,
            )
        )
    return jobs


def fetch(slugs: list[str]) -> list[Job]:
    return parallel(_one, slugs)
