from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Iterator

from .core import ProjectionIndicator, normalize_value


SCHEMA = """
CREATE TABLE IF NOT EXISTS indicators (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  indicator_type TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  display_value TEXT NOT NULL,
  risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
  confidence TEXT NOT NULL,
  status TEXT NOT NULL,
  report_count INTEGER NOT NULL DEFAULT 1,
  independent_sources INTEGER NOT NULL DEFAULT 1,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  scam_types_json TEXT NOT NULL DEFAULT '[]',
  summary TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(indicator_type, normalized_value)
);

CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  indicator_type TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  source_url TEXT,
  description TEXT NOT NULL,
  has_evidence INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: str):
        self.path = path
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with self.connection() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def upsert(self, indicator: ProjectionIndicator) -> None:
        payload = asdict(indicator)
        payload["scam_types_json"] = json.dumps(payload.pop("scam_types"), ensure_ascii=False)
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO indicators (
                  indicator_type, normalized_value, display_value, risk_score,
                  confidence, status, report_count, independent_sources,
                  first_seen, last_seen, scam_types_json, summary, source_ref, updated_at
                ) VALUES (
                  :indicator_type, :normalized_value, :display_value, :risk_score,
                  :confidence, :status, :report_count, :independent_sources,
                  :first_seen, :last_seen, :scam_types_json, :summary, :source_ref, :updated_at
                )
                ON CONFLICT(indicator_type, normalized_value) DO UPDATE SET
                  display_value=excluded.display_value,
                  risk_score=excluded.risk_score,
                  confidence=excluded.confidence,
                  status=excluded.status,
                  report_count=excluded.report_count,
                  independent_sources=excluded.independent_sources,
                  first_seen=excluded.first_seen,
                  last_seen=excluded.last_seen,
                  scam_types_json=excluded.scam_types_json,
                  summary=excluded.summary,
                  source_ref=excluded.source_ref,
                  updated_at=excluded.updated_at
                """,
                payload,
            )

    def lookup(self, indicator_type: str, raw_value: str) -> dict | None:
        normalized = normalize_value(indicator_type, raw_value)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM indicators WHERE indicator_type=? AND normalized_value=?",
                (indicator_type, normalized),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["scam_types"] = json.loads(result.pop("scam_types_json"))
        result.pop("normalized_value", None)
        return result

    def add_report(self, payload: dict) -> int:
        now = datetime.now(timezone.utc).isoformat()
        normalized = normalize_value(payload["type"], payload["value"])
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reports (
                  indicator_type, normalized_value, source_url, description,
                  has_evidence, status, created_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    payload["type"], normalized, payload.get("source_url"),
                    payload["description"], int(payload.get("has_evidence", False)), now,
                ),
            )
            return int(cursor.lastrowid)

    def counts(self) -> dict[str, int]:
        with self.connection() as connection:
            indicator_count = connection.execute("SELECT COUNT(*) FROM indicators").fetchone()[0]
            pending_count = connection.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0]
        return {"indicators": indicator_count, "pending_reports": pending_count}
