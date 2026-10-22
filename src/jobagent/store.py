import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import JobRef

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  company TEXT, location TEXT,
  description TEXT,
  state TEXT NOT NULL DEFAULT 'discovered',
  filter_reason TEXT,
  source_msg_id TEXT,
  discovered_at TEXT NOT NULL,
  fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS seen_messages (msg_id TEXT PRIMARY KEY, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS views (day TEXT NOT NULL, job_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, started TEXT, stats_json TEXT);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: Path | str = "data/jobs.db"):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def message_seen(self, msg_id: str) -> bool:
        return self.db.execute(
            "SELECT 1 FROM seen_messages WHERE msg_id=?", (msg_id,)
        ).fetchone() is not None

    def mark_message(self, msg_id: str) -> None:
        self.db.execute(
            "INSERT OR IGNORE INTO seen_messages VALUES (?,?)", (msg_id, _now())
        )
        self.db.commit()

    def add_job(self, j: JobRef, state: str = "discovered", reason: str | None = None) -> bool:
        """Insert if new. Returns True when inserted (dedupe by job_id)."""
        cur = self.db.execute(
            "INSERT OR IGNORE INTO jobs (job_id,url,title,company,location,state,"
            "filter_reason,source_msg_id,discovered_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (j.job_id, j.url, j.title, j.company, j.location, state, reason,
             j.source_msg_id, _now()),
        )
        self.db.commit()
        return cur.rowcount == 1

    def jobs_in_state(self, state: str, limit: int = 1000) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM jobs WHERE state=? ORDER BY discovered_at LIMIT ?",
            (state, limit),
        ).fetchall()

    def set_description(self, job_id: str, description: str) -> None:
        self.db.execute(
            "UPDATE jobs SET description=?, state='extracted', fetched_at=? WHERE job_id=?",
            (description, _now(), job_id),
        )
        self.db.commit()

    def record_view(self, job_id: str) -> None:
        self.db.execute(
            "INSERT INTO views VALUES (date('now'),?)", (job_id,)
        )
        self.db.commit()

    def views_today(self) -> int:
        return self.db.execute(
            "SELECT COUNT(*) FROM views WHERE day=date('now')"
        ).fetchone()[0]

    def counts(self) -> dict[str, int]:
        rows = self.db.execute("SELECT state, COUNT(*) c FROM jobs GROUP BY state")
        return {r["state"]: r["c"] for r in rows}
