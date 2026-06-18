"""Tests for parallel candidate scoring (score_candidates_parallel)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.schemas import Candidate, Track
from techno_search.scoring import score_candidates_parallel

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_candidate(name: str) -> Candidate:
    p = Path(__file__).parent.parent / "examples" / "candidates" / name
    data = json.loads(p.read_text())
    return Candidate(
        candidate_id=str(data["candidate_id"]),
        track=Track(data["track"]),
        features={k: v for k, v in data.get("features", {}).items() if v is not None},
        source_ids=list(data.get("source_ids", [])),
        provenance=dict(data.get("provenance", {})),
    )


def _make_candidate(cid: str, snr: float = 30.0) -> Candidate:
    return Candidate(
        candidate_id=cid,
        track=Track.RADIO,
        features={"max_snr": snr, "drift_rate": 0.5, "on_source_fraction": 0.8},
        source_ids=[],
        provenance={},
    )


# ---------------------------------------------------------------------------
# score_candidates_parallel vs serial consistency
# ---------------------------------------------------------------------------

class TestParallelVsSerial:
    def _example_candidates(self) -> list[Candidate]:
        return [
            _load_candidate("radio_clean_candidate.json"),
            _load_candidate("infrared_clean_candidate.json"),
            _load_candidate("anomaly_clean_candidate.json"),
        ]

    def test_serial_fallback_when_workers_one(self):
        candidates = self._example_candidates()
        results = score_candidates_parallel(candidates, workers=1)
        assert len(results) == 3

    def test_parallel_same_count_as_serial(self):
        candidates = self._example_candidates()
        serial = score_candidates_parallel(candidates, workers=1)
        parallel = score_candidates_parallel(candidates, workers=2)
        assert len(serial) == len(parallel)

    def test_parallel_same_pathways_as_serial(self):
        candidates = self._example_candidates()
        serial = score_candidates_parallel(candidates, workers=1)
        parallel = score_candidates_parallel(candidates, workers=2)
        serial_pathways = [s.recommended_pathway for s in serial]
        parallel_pathways = [p.recommended_pathway for p in parallel]
        assert serial_pathways == parallel_pathways

    def test_parallel_same_scores_as_serial(self):
        candidates = self._example_candidates()
        serial = score_candidates_parallel(candidates, workers=1)
        parallel = score_candidates_parallel(candidates, workers=2)
        for s, p in zip(serial, parallel, strict=True):
            assert s.scores.as_dict() == pytest.approx(p.scores.as_dict(), rel=1e-6)

    def test_none_workers_falls_back_to_serial(self):
        candidates = self._example_candidates()
        results = score_candidates_parallel(candidates, workers=None)
        assert len(results) == 3

    def test_single_candidate_no_executor(self):
        c = _make_candidate("solo", snr=80.0)
        results = score_candidates_parallel([c], workers=4)
        assert len(results) == 1

    def test_empty_list_returns_empty(self):
        results = score_candidates_parallel([], workers=4)
        assert results == []

    def test_workers_zero_falls_back_to_serial(self):
        candidates = self._example_candidates()
        results = score_candidates_parallel(candidates, workers=0)
        assert len(results) == 3

    def test_process_pool_setup_failure_falls_back_to_serial(self, monkeypatch):
        import concurrent.futures

        class FailingExecutor:
            def __init__(self, *args, **kwargs):
                raise PermissionError("semaphore probe denied")

        monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", FailingExecutor)

        candidates = self._example_candidates()
        serial = score_candidates_parallel(candidates, workers=1)
        fallback = score_candidates_parallel(candidates, workers=2)

        assert [s.recommended_pathway for s in fallback] == [
            s.recommended_pathway for s in serial
        ]

    def test_parallel_preserves_candidate_ids(self):
        candidates = [_make_candidate(f"cand_{i}", snr=30.0 + i) for i in range(5)]
        results = score_candidates_parallel(candidates, workers=2)
        result_ids = {r.candidate.candidate_id for r in results}
        expected_ids = {c.candidate_id for c in candidates}
        assert result_ids == expected_ids

    def test_parallel_deterministic(self):
        candidates = self._example_candidates()
        run1 = score_candidates_parallel(candidates, workers=2)
        run2 = score_candidates_parallel(candidates, workers=2)
        for r1, r2 in zip(run1, run2, strict=True):
            assert r1.recommended_pathway == r2.recommended_pathway
