"""Normalized job model shared by every source."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    # strip HTML tags and collapse whitespace
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Job:
    title: str
    company: str
    url: str
    source: str
    location: str = ""
    description: str = ""
    salary: str = ""
    tags: list[str] = field(default_factory=list)
    posted: Optional[datetime] = None

    # filled in by the pipeline
    score: int = 0
    reasons: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = _clean(self.title)
        self.company = _clean(self.company)
        self.location = _clean(self.location)
        self.description = _clean(self.description)
        self.salary = _clean(self.salary)

    @property
    def haystack(self) -> str:
        """All searchable text, lower-cased, for filtering + scoring."""
        parts = [self.title, self.company, self.location, self.description, " ".join(self.tags)]
        return " ".join(p for p in parts if p).lower()

    @property
    def posted_utc(self) -> Optional[datetime]:
        """`posted` as timezone-aware UTC — sources mix naive and aware datetimes,
        which cannot be compared to each other when sorting."""
        if self.posted is None:
            return None
        if self.posted.tzinfo is None:
            return self.posted.replace(tzinfo=timezone.utc)
        return self.posted.astimezone(timezone.utc)

    @property
    def fingerprint(self) -> str:
        """Stable id for dedup + seen-tracking. Prefer URL; fall back to title+company."""
        key = self.url.strip().lower() or f"{self.title.lower()}|{self.company.lower()}"
        return hashlib.sha1(key.encode("utf-8")).hexdigest()
