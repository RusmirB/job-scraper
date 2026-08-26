"""Remove duplicate postings that appear on multiple boards."""
from __future__ import annotations

import re

from .models import Job


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def dedupe(jobs: list[Job]) -> list[Job]:
    seen: set[str] = set()
    out: list[Job] = []
    for job in jobs:
        # match on url fingerprint OR normalized title+company
        keys = {job.fingerprint, _norm(job.title) + "|" + _norm(job.company)}
        if keys & seen:
            continue
        seen |= keys
        out.append(job)
    return out
