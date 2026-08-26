"""We Work Remotely RSS feed (programming category covers QA/SDET)."""
from __future__ import annotations

import feedparser
from dateutil import parser as dateparser

from . import get
from ..models import Job

FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]
SOURCE = "WeWorkRemotely"


def _entries(feed_url: str) -> list:
    """Fetch through get() rather than letting feedparser do its own urlopen --
    feedparser has no timeout and would hang the run on a stalled feed."""
    try:
        return feedparser.parse(get(feed_url).content).entries
    except Exception as exc:  # noqa: BLE001 - one dead feed shouldn't kill the rest
        print(f"  [wwr] {feed_url} failed: {exc}")
        return []


def fetch() -> list[Job]:
    jobs: list[Job] = []
    for feed_url in FEEDS:
        for entry in _entries(feed_url):
            # WWR titles look like "Company: Job Title"
            raw = entry.get("title", "")
            company, _, title = raw.partition(":")
            if not title:
                title, company = company, ""
            posted = None
            if entry.get("published"):
                try:
                    posted = dateparser.parse(entry["published"])
                except (ValueError, TypeError):
                    posted = None
            jobs.append(
                Job(
                    title=title.strip() or raw,
                    company=company.strip(),
                    url=entry.get("link", ""),
                    source=SOURCE,
                    location=entry.get("region", "Remote"),
                    description=entry.get("summary", ""),
                    posted=posted,
                )
            )
    return jobs
