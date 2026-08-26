"""SQLite store so you only ever get alerted about a job once."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Job


class SeenStore:
    def __init__(self, path: str = "jobs.db") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen (
                fingerprint TEXT PRIMARY KEY,
                title       TEXT,
                company     TEXT,
                url         TEXT,
                source      TEXT,
                score       INTEGER,
                first_seen  TEXT
            )
            """
        )
        self.conn.commit()

    def is_new(self, job: Job) -> bool:
        cur = self.conn.execute("SELECT 1 FROM seen WHERE fingerprint = ?", (job.fingerprint,))
        return cur.fetchone() is None

    def remember(self, job: Job) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO seen VALUES (?,?,?,?,?,?,?)",
            (
                job.fingerprint,
                job.title,
                job.company,
                job.url,
                job.source,
                job.score,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
