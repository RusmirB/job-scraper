"""RemoteJobs.org public API (free, no key) — https://remotejobs.org/api-access
Has explicit salary fields, so it's a good salary source. The search is loose,
so we query several QA terms and rely on the title filter downstream."""
from __future__ import annotations

from dateutil import parser as dateparser

from . import get
from ..models import Job

URL = "https://remotejobs.org/api/v1/jobs"
SOURCE = "RemoteJobs.org"
QUERIES = ["qa", "sdet", "tester", "quality assurance", "test automation"]


def _salary(item: dict) -> str:
    if item.get("salary_text"):
        return item["salary_text"]
    lo, hi = item.get("salary_min"), item.get("salary_max")
    if lo and hi:
        return f"${lo:,}–${hi:,}"
    if lo:
        return f"from ${lo:,}"
    return ""


def fetch() -> list[Job]:
    seen_ids: set[str] = set()
    jobs: list[Job] = []
    for q in QUERIES:
        data = get(URL, params={"q": q, "limit": 100}).json()
        for item in data.get("data", []):
            jid = item.get("id")
            if jid in seen_ids:
                continue
            seen_ids.add(jid)
            posted = None
            if item.get("posted_at"):
                try:
                    posted = dateparser.parse(item["posted_at"])
                except (ValueError, TypeError):
                    posted = None
            company = item.get("company") or {}
            jobs.append(
                Job(
                    title=item.get("title", ""),
                    company=company.get("name", "") if isinstance(company, dict) else str(company),
                    url=item.get("apply_url") or item.get("url", ""),
                    source=SOURCE,
                    location=item.get("location", "Remote"),
                    description=item.get("description", ""),
                    salary=_salary(item),
                    posted=posted,
                )
            )
    return jobs
