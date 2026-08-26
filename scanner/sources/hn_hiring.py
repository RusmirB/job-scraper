"""Hacker News monthly "Ask HN: Who is hiring?" thread via the free Algolia API.
Great for startups hiring their first QA. Each top-level comment is one job post.
We keep comments that read as remote; the title filter downstream keeps QA ones.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from . import get
from ..models import Job

SEARCH = "https://hn.algolia.com/api/v1/search_by_date"
ITEM = "https://hn.algolia.com/api/v1/items/{id}"
SOURCE = "HackerNews"


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("&#x2F;", "/").replace("&#x27;", "'").replace("&amp;", "&")
    text = text.replace("&gt;", ">").replace("&lt;", "<").replace("&quot;", '"')
    return re.sub(r"\s+", " ", text).strip()


def _latest_thread_id() -> str | None:
    data = get(
        SEARCH,
        params={"query": '"Ask HN: Who is hiring"', "tags": "story", "hitsPerPage": 10},
    ).json()
    for hit in data.get("hits", []):
        # the monthly thread is titled: "Ask HN: Who is hiring? (Month Year)"
        if re.match(r"ask hn: who is hiring\? \(", hit.get("title", "").lower()):
            return hit.get("objectID")
    return None


def fetch() -> list[Job]:
    thread_id = _latest_thread_id()
    if not thread_id:
        return []
    data = get(ITEM.format(id=thread_id)).json()
    jobs: list[Job] = []
    for child in data.get("children", []):
        text = _strip_html(child.get("text", ""))
        if not text or "remote" not in text.lower():
            continue
        # first line is usually "Company | Role | Location | Remote"
        first = text.split("|")[0].strip() if "|" in text else text[:90]
        parts = [p.strip() for p in text.split("|")]
        company = parts[0] if len(parts) > 1 else ""
        # title: the segment most likely to hold the role, else the first line
        title = parts[1] if len(parts) > 1 else first
        posted = None
        if child.get("created_at_i"):
            posted = datetime.fromtimestamp(child["created_at_i"], tz=timezone.utc)
        jobs.append(
            Job(
                title=title[:120],
                company=company[:80],
                url=f"https://news.ycombinator.com/item?id={child.get('id')}",
                source=SOURCE,
                location="Remote",
                description=text,
                posted=posted,
            )
        )
    return jobs
