"""SQLite-backed candidate store for scored candidates.

Stores scored candidate results indexed by track, pathway, and score for
efficient triage and review. This is a local provenance and scheduling aid —
stored records do not authorize external submission, do not constitute
detection claims, and do not modify pathway routing.
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.schemas import ScoredCandidate

CANDIDATE_STORE_DISCLAIMER = (
    "Candidate store records are local triage and provenance records only. "
    "Stored records do not authorize external submission, do not constitute "
    "detection claims, and do not modify pathway routing."
)

_STORE_ENV_VAR = "TECHNO_SEARCH_CANDIDATE_STORE_PATH"
_DEFAULT_STORE_PATH = Path("data") / "candidates.db"


def default_store_path() -> Path:
    override = os.environ.get(_STORE_ENV_VAR, "").strip()
    if override:
        return Path(override)
    return _DEFAULT_STORE_PATH


_DDL = """
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL UNIQUE,
    track TEXT NOT NULL,
    pathway TEXT NOT NULL,
    signal_reality REAL NOT NULL,
    false_positive_prob REAL NOT NULL,
    review_readiness REAL NOT NULL,
    followup_value REAL NOT NULL,
    created_at TEXT NOT NULL,
    source_file TEXT,
    candidate_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pathway ON candidates (pathway);
CREATE INDEX IF NOT EXISTS idx_track ON candidates (track);
CREATE INDEX IF NOT EXISTS idx_signal_reality ON candidates (signal_reality DESC);
"""


@dataclass
class CandidateStoreEntry:
    candidate_id: str
    track: str
    pathway: str
    signal_reality: float
    false_positive_prob: float
    review_readiness: float
    followup_value: float
    created_at: str
    source_file: str | None
    candidate_json: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "track": self.track,
            "pathway": self.pathway,
            "signal_reality": self.signal_reality,
            "false_positive_prob": self.false_positive_prob,
            "review_readiness": self.review_readiness,
            "followup_value": self.followup_value,
            "created_at": self.created_at,
            "source_file": self.source_file,
        }


class CandidateStore:
    """SQLite-backed store for scored candidates."""

    DISCLAIMER = CANDIDATE_STORE_DISCLAIMER

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)

    def init_schema(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_DDL)

    def insert(
        self,
        scored: ScoredCandidate,
        *,
        source_file: str | None = None,
    ) -> CandidateStoreEntry:
        from techno_search.reporting import candidate_packet_json

        created_at = datetime.now(UTC).isoformat()
        candidate_json_str = candidate_packet_json(scored)
        scores = scored.scores.as_dict()
        entry = CandidateStoreEntry(
            candidate_id=scored.candidate.candidate_id,
            track=scored.candidate.track.value,
            pathway=scored.recommended_pathway.value,
            signal_reality=float(scores.get("signal_reality_confidence", 0.0)),
            false_positive_prob=float(scores.get("false_positive_probability", 1.0)),
            review_readiness=float(scores.get("review_readiness", 0.0)),
            followup_value=float(scores.get("followup_value", 0.0)),
            created_at=created_at,
            source_file=source_file,
            candidate_json=candidate_json_str,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO candidates
                  (candidate_id, track, pathway, signal_reality, false_positive_prob,
                   review_readiness, followup_value, created_at, source_file, candidate_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.candidate_id,
                    entry.track,
                    entry.pathway,
                    entry.signal_reality,
                    entry.false_positive_prob,
                    entry.review_readiness,
                    entry.followup_value,
                    entry.created_at,
                    entry.source_file,
                    entry.candidate_json,
                ),
            )
        return entry

    def get(self, candidate_id: str) -> CandidateStoreEntry | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT candidate_id, track, pathway, signal_reality, false_positive_prob, "
                "review_readiness, followup_value, created_at, source_file, candidate_json "
                "FROM candidates WHERE candidate_id = ?",
                (candidate_id,),
            ).fetchone()
        return _row_to_entry(row) if row else None

    def list_all(self) -> list[CandidateStoreEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT candidate_id, track, pathway, signal_reality, false_positive_prob, "
                "review_readiness, followup_value, created_at, source_file, candidate_json "
                "FROM candidates ORDER BY signal_reality DESC"
            ).fetchall()
        return [_row_to_entry(r) for r in rows]

    def list_by_pathway(self, pathway: str) -> list[CandidateStoreEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT candidate_id, track, pathway, signal_reality, false_positive_prob, "
                "review_readiness, followup_value, created_at, source_file, candidate_json "
                "FROM candidates WHERE pathway = ? ORDER BY signal_reality DESC",
                (pathway,),
            ).fetchall()
        return [_row_to_entry(r) for r in rows]

    def list_by_track(self, track: str) -> list[CandidateStoreEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT candidate_id, track, pathway, signal_reality, false_positive_prob, "
                "review_readiness, followup_value, created_at, source_file, candidate_json "
                "FROM candidates WHERE track = ? ORDER BY signal_reality DESC",
                (track,),
            ).fetchall()
        return [_row_to_entry(r) for r in rows]

    def summary(self) -> dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
            by_pathway = {
                row[0]: row[1]
                for row in conn.execute(
                    "SELECT pathway, COUNT(*) FROM candidates GROUP BY pathway"
                ).fetchall()
            }
            by_track = {
                row[0]: row[1]
                for row in conn.execute(
                    "SELECT track, COUNT(*) FROM candidates GROUP BY track"
                ).fetchall()
            }
        return {
            "disclaimer": self.DISCLAIMER,
            "db_path": str(self._db_path),
            "total": total,
            "by_pathway": by_pathway,
            "by_track": by_track,
        }

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)


def _row_to_entry(row: tuple[Any, ...]) -> CandidateStoreEntry:
    return CandidateStoreEntry(
        candidate_id=row[0],
        track=row[1],
        pathway=row[2],
        signal_reality=float(row[3]),
        false_positive_prob=float(row[4]),
        review_readiness=float(row[5]),
        followup_value=float(row[6]),
        created_at=row[7],
        source_file=row[8],
        candidate_json=row[9],
    )
