"""Ashby public job board API — one board per company slug.
https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true
Bonus: exposes compensation, so it's a good salary source.
"""
from __future__ import annotations

from dateutil import parser as dateparser

from . import get, parallel
from ..models import Job

SOURCE = "Ashby"


def _salary(comp: dict | None) -> str:
    if not comp:
        return ""
    return comp.get("scrapeableCompensationSalarySummary") or comp.get(
        "compensationTierSummary", ""
    )


def _one(slug: str) -> list[Job]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        data = get(url, params={"includeCompensation": "true"}).json()
    except Exception as exc:  # noqa: BLE001
        print(f"  [ashby] {slug} failed: {exc}")
        return []
    jobs: list[Job] = []
    for item in data.get("jobs", []):
        posted = None
        if item.get("publishedAt"):
            try:
                posted = dateparser.parse(item["publishedAt"])
            except (ValueError, TypeError):
                posted = None
        loc = item.get("location", "")
        if item.get("isRemote"):
            loc = f"{loc} (remote)" if loc else "Remote"
        jobs.append(
            Job(
                title=item.get("title", ""),
                company=slug.title(),
                url=item.get("jobUrl") or item.get("applyUrl", ""),
                source=SOURCE,
                location=loc,
                description=item.get("descriptionPlain", ""),
                salary=_salary(item.get("compensation")),
                posted=posted,
            )
        )
    return jobs


def fetch(slugs: list[str]) -> list[Job]:
    return parallel(_one, slugs)
