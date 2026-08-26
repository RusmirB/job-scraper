"""Score a job against your profile weights."""
from __future__ import annotations

from .models import Job


def score_job(job: Job, weights: dict[str, int]) -> None:
    """Set job.score and job.reasons in place."""
    hay = job.haystack
    total = 0
    reasons: list[str] = []
    for phrase, weight in weights.items():
        if phrase.lower() in hay:
            total += weight
            sign = "+" if weight >= 0 else ""
            reasons.append(f"{sign}{weight} {phrase}")
    job.score = total
    job.reasons = reasons
