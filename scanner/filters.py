"""Keyword gates: drop jobs that are clearly not for you before scoring."""
from __future__ import annotations

import re

from .models import Job


def _has_word(text: str, phrase: str) -> bool:
    """Whole-word match so 'test' doesn't hit 'latest' and 'qa' doesn't hit 'quay'."""
    return re.search(rf"\b{re.escape(phrase.lower())}\b", text.lower()) is not None


def passes(
    job: Job,
    title_must_match: list[str],
    excluded: list[str],
    required_any: list[str] | None = None,
) -> bool:
    hay = job.haystack

    # 1) hard exclusions (checked across the whole posting)
    if excluded and any(_has_word(hay, bad) for bad in excluded):
        return False

    # 2) the TITLE must announce a QA role -- this is what stops DevOps / PM / Data
    #    Engineer roles that merely *mention* testing in their description.
    if title_must_match and not any(_has_word(job.title, kw) for kw in title_must_match):
        return False

    # 3) optional extra safety net on the whole posting (kept for backward compat)
    if required_any and not any(_has_word(hay, req) for req in required_any):
        return False

    return True
