"""QA/SDET remote-job scanner — Phase 1.

Fetch many remote-job sources -> normalize -> filter -> score -> dedupe ->
drop already-seen -> write CSV + HTML report of NEW matches only.

Run:  python main.py
"""
from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import yaml

from scanner.database import SeenStore
from scanner.dedup import dedupe
from scanner.filters import passes
from scanner.models import Job
from scanner.notify import write_csv, write_html
from scanner.scoring import score_job
from scanner.sources import (
    adzuna,
    arbeitnow,
    ashby,
    greenhouse,
    himalayas,
    hn_hiring,
    jobicy,
    lever,
    remotejobs,
    remoteok,
    remotive,
    smartrecruiters,
    themuse,
    weworkremotely,
    workingnomads,
)

ROOT = Path(__file__).parent
CONFIG = ROOT / "config"


def load_env() -> None:
    """Load KEY=VALUE lines from a local .env into os.environ (no dependency)."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_yaml(name: str) -> dict:
    return yaml.safe_load((CONFIG / name).read_text(encoding="utf-8")) or {}


def collect(companies: dict) -> list[Job]:
    """Run every source; a failure in one never aborts the others."""
    tasks = [
        ("Remotive", remotive.fetch),
        ("Arbeitnow", arbeitnow.fetch),
        ("WeWorkRemotely", weworkremotely.fetch),
        ("RemoteOK", remoteok.fetch),
        ("Jobicy", jobicy.fetch),
        ("Himalayas", himalayas.fetch),
        ("WorkingNomads", workingnomads.fetch),
        ("TheMuse", themuse.fetch),
        ("RemoteJobs.org", remotejobs.fetch),
        ("HackerNews", hn_hiring.fetch),
        ("Adzuna", adzuna.fetch),
        ("Greenhouse", lambda: greenhouse.fetch(companies.get("greenhouse", []))),
        ("Lever", lambda: lever.fetch(companies.get("lever", []))),
        ("Ashby", lambda: ashby.fetch(companies.get("ashby", []))),
        ("SmartRecruiters", lambda: smartrecruiters.fetch(companies.get("smartrecruiters", []))),
    ]
    def run(task: tuple[str, object]) -> list[Job]:
        name, fn = task
        started = time.monotonic()
        try:
            found = fn()
            print(f"  {name:<16} {len(found):>4} jobs  ({time.monotonic() - started:.0f}s)")
            return found
        except Exception as exc:  # noqa: BLE001
            print(f"  {name:<16} FAILED after {time.monotonic() - started:.0f}s: {exc}")
            return []

    jobs: list[Job] = []
    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        for found in pool.map(run, tasks):
            jobs.extend(found)
    return jobs


def sort_key(job: Job) -> tuple[date, int]:
    """Newest posting day first; best score first within the same day.
    Jobs with no known date sink to the bottom."""
    posted = job.posted_utc
    return (posted.date() if posted else date.min, job.score)


def main() -> None:
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="jobs.db")
    ap.add_argument("--out", default="report", help="output basename (writes .html and .csv)")
    ap.add_argument("--all", action="store_true", help="include already-seen jobs in report")
    args = ap.parse_args()

    profile = load_yaml("profile.yaml")
    companies = load_yaml("companies.yaml")
    title_must_match = profile.get("title_must_match", [])
    required = profile.get("required_any", [])
    excluded = profile.get("excluded", [])
    weights = profile.get("weights", {})
    min_score = profile.get("min_score", 40)

    print("Fetching sources...")
    jobs = collect(companies)
    print(f"Total fetched: {len(jobs)}")

    jobs = [j for j in jobs if passes(j, title_must_match, excluded, required)]
    print(f"After keyword filter: {len(jobs)}")

    for job in jobs:
        score_job(job, weights)
    jobs = [j for j in jobs if j.score >= min_score]
    jobs = dedupe(jobs)
    print(f"After scoring (>= {min_score}) + dedupe: {len(jobs)}")

    store = SeenStore(args.db)
    fresh = [j for j in jobs if args.all or store.is_new(j)]
    for job in jobs:
        store.remember(job)
    store.close()

    fresh.sort(key=sort_key, reverse=True)
    print(f"NEW matches: {len(fresh)}")

    write_html(fresh, f"{args.out}.html")
    write_csv(fresh, f"{args.out}.csv")
    print(f"Wrote {args.out}.html and {args.out}.csv")


if __name__ == "__main__":
    main()
