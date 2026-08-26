"""Adzuna aggregator API — salary-rich, broad coverage (Indeed-style listings).
Free, but needs credentials from https://developer.adzuna.com/ :
    set env vars  ADZUNA_APP_ID  and  ADZUNA_APP_KEY
If they're missing, this source is skipped cleanly (returns []).
"""
from __future__ import annotations

import os

from dateutil import parser as dateparser

from . import get, scrub
from ..models import Job

SOURCE = "Adzuna"
COUNTRIES = ["us", "gb"]
QUERIES = ["QA automation", "SDET", "software tester", "test automation engineer"]


def _salary(item: dict) -> str:
    lo, hi = item.get("salary_min"), item.get("salary_max")
    if lo and hi:
        if int(lo) == int(hi):
            return f"~${int(lo):,} (est.)"
        return f"${int(lo):,}–${int(hi):,}"
    return ""


def _is_remote(item: dict) -> bool:
    blob = " ".join(
        str(x)
        for x in (
            item.get("title", ""),
            item.get("description", ""),
            (item.get("location") or {}).get("display_name", ""),
        )
    ).lower()
    return "remote" in blob or "work from home" in blob


def _parse(item: dict) -> Job:
    posted = None
    if item.get("created"):
        try:
            posted = dateparser.parse(item["created"])
        except (ValueError, TypeError):
            posted = None
    return Job(
        title=item.get("title", ""),
        company=(item.get("company") or {}).get("display_name", ""),
        url=item.get("redirect_url", ""),
        source=SOURCE,
        location=(item.get("location") or {}).get("display_name", ""),
        description=item.get("description", ""),
        salary=_salary(item),
        posted=posted,
    )


def _query(country: str, what: str, app_id: str, app_key: str) -> list[dict]:
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    try:
        return get(
            url,
            params={
                "app_id": app_id,
                "app_key": app_key,
                "results_per_page": 50,
                "what": what,
                "content-type": "application/json",
            },
        ).json().get("results", [])
    except Exception as exc:  # noqa: BLE001
        print(f"  [adzuna] {country}/{what} failed: {scrub(str(exc))}")
        return []


def fetch() -> list[Job]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        print("  [adzuna] skipped (set ADZUNA_APP_ID / ADZUNA_APP_KEY to enable)")
        return []

    seen: set[str] = set()
    jobs: list[Job] = []
    for country in COUNTRIES:
        for what in QUERIES:
            for item in _query(country, what, app_id, app_key):
                url_ = item.get("redirect_url", "")
                if url_ in seen or not _is_remote(item):
                    continue
                seen.add(url_)
                jobs.append(_parse(item))
    return jobs
