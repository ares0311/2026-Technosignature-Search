"""Tests for SQLite-backed candidate store (techno_search.candidate_store)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.candidate_store import (
    _STORE_ENV_VAR,
    CANDIDATE_STORE_DISCLAIMER,
    CandidateStore,
    CandidateStoreEntry,
    default_store_path,
)
from techno_search.schemas import Candidate, Track
from techno_search.scoring import score_candidate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candidate(
    cid: str = "test-001", track: Track = Track.RADIO, snr: float = 60.0
) -> Candidate:
    return Candidate(
        candidate_id=cid,
        track=track,
        features={"max_snr": snr, "drift_rate": 0.5, "on_source_fraction": 0.8},
        source_ids=["HIP99427"],
        provenance={"source_file": "test.dat", "reader_type": "turboSETI_csv"},
    )


def _scored(cid: str = "test-001", track: Track = Track.RADIO, snr: float = 60.0):
    return score_candidate(_make_candidate(cid, track, snr))


@pytest.fixture()
def store(tmp_path: Path) -> CandidateStore:
    db = tmp_path / "candidates.db"
    s = CandidateStore(db)
    s.init_schema()
    return s


# ---------------------------------------------------------------------------
# default_store_path
# ---------------------------------------------------------------------------

class TestDefaultStorePath:
    def test_default_is_data_candidates_db(self, monkeypatch):
        monkeypatch.delenv(_STORE_ENV_VAR, raising=False)
        p = default_store_path()
        assert str(p).endswith("candidates.db")

    def test_env_var_override(self, monkeypatch, tmp_path):
        override = str(tmp_path / "custom.db")
        monkeypatch.setenv(_STORE_ENV_VAR, override)
        assert default_store_path() == Path(override)


# ---------------------------------------------------------------------------
# Schema initialization
# ---------------------------------------------------------------------------

class TestInitSchema:
    def test_creates_file(self, tmp_path):
        db = tmp_path / "test.db"
        store = CandidateStore(db)
        store.init_schema()
        assert db.exists()

    def test_idempotent(self, tmp_path):
        db = tmp_path / "test.db"
        store = CandidateStore(db)
        store.init_schema()
        store.init_schema()  # Second call must not raise
        assert db.exists()

    def test_creates_parent_dirs(self, tmp_path):
        db = tmp_path / "nested" / "deep" / "candidates.db"
        store = CandidateStore(db)
        store.init_schema()
        assert db.exists()


# ---------------------------------------------------------------------------
# insert
# ---------------------------------------------------------------------------

class TestInsert:
    def test_insert_returns_entry(self, store):
        entry = store.insert(_scored())
        assert isinstance(entry, CandidateStoreEntry)
        assert entry.candidate_id == "test-001"

    def test_insert_populates_track(self, store):
        entry = store.insert(_scored(track=Track.INFRARED))
        assert entry.track == "infrared"

    def test_insert_populates_signal_reality(self, store):
        entry = store.insert(_scored(snr=60.0))
        assert 0.0 <= entry.signal_reality <= 1.0

    def test_insert_populates_false_positive_prob(self, store):
        entry = store.insert(_scored())
        assert 0.0 <= entry.false_positive_prob <= 1.0

    def test_insert_with_source_file(self, store):
        entry = store.insert(_scored(), source_file="data/obs.dat")
        assert entry.source_file == "data/obs.dat"

    def test_insert_without_source_file(self, store):
        entry = store.insert(_scored())
        assert entry.source_file is None

    def test_insert_replace_on_duplicate_id(self, store):
        store.insert(_scored("dup-001", snr=30.0))
        store.insert(_scored("dup-001", snr=80.0))
        # Should not raise; last insert wins
        entry = store.get("dup-001")
        assert entry is not None

    def test_candidate_json_stored(self, store):
        store.insert(_scored())
        entry = store.get("test-001")
        assert entry is not None
        parsed = json.loads(entry.candidate_json)
        assert "candidate_id" in parsed


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

class TestGet:
    def test_get_existing(self, store):
        store.insert(_scored("get-001"))
        entry = store.get("get-001")
        assert entry is not None
        assert entry.candidate_id == "get-001"

    def test_get_missing_returns_none(self, store):
        assert store.get("nonexistent-999") is None

    def test_entry_as_dict_has_required_keys(self, store):
        store.insert(_scored("dict-001"))
        entry = store.get("dict-001")
        d = entry.as_dict()
        required_keys = (
            "candidate_id", "track", "pathway", "signal_reality",
            "false_positive_prob", "review_readiness", "followup_value", "created_at",
        )
        for key in required_keys:
            assert key in d


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------

class TestListAll:
    def test_list_all_empty(self, store):
        assert store.list_all() == []

    def test_list_all_returns_entries(self, store):
        store.insert(_scored("a-001", snr=60.0))
        store.insert(_scored("b-001", snr=80.0))
        entries = store.list_all()
        assert len(entries) == 2

    def test_list_all_sorted_by_signal_reality_desc(self, store):
        store.insert(_scored("low-001", snr=30.0))
        store.insert(_scored("high-001", snr=100.0))
        entries = store.list_all()
        realities = [e.signal_reality for e in entries]
        assert realities == sorted(realities, reverse=True)


# ---------------------------------------------------------------------------
# list_by_pathway / list_by_track
# ---------------------------------------------------------------------------

class TestListByFilters:
    def test_list_by_pathway_filters(self, store):
        scored = _scored("p-001", snr=60.0)
        store.insert(scored)
        pathway = scored.recommended_pathway.value
        entries = store.list_by_pathway(pathway)
        assert all(e.pathway == pathway for e in entries)

    def test_list_by_pathway_empty_for_missing(self, store):
        store.insert(_scored("p-002"))
        entries = store.list_by_pathway("nonexistent_pathway")
        assert entries == []

    def test_list_by_track_filters_radio(self, store):
        store.insert(_scored("r-001", track=Track.RADIO))
        store.insert(_scored("i-001", track=Track.INFRARED))
        radio_entries = store.list_by_track("radio")
        assert all(e.track == "radio" for e in radio_entries)
        assert len(radio_entries) == 1

    def test_list_by_track_empty_for_missing(self, store):
        entries = store.list_by_track("nonexistent_track")
        assert entries == []


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

class TestSummary:
    def test_summary_total(self, store):
        store.insert(_scored("s-001"))
        store.insert(_scored("s-002"))
        summary = store.summary()
        assert summary["total"] == 2

    def test_summary_by_track(self, store):
        store.insert(_scored("radio-001", track=Track.RADIO))
        store.insert(_scored("ir-001", track=Track.INFRARED))
        summary = store.summary()
        assert "radio" in summary["by_track"] or "infrared" in summary["by_track"]

    def test_summary_has_disclaimer(self, store):
        summary = store.summary()
        assert "disclaimer" in summary
        assert len(summary["disclaimer"]) > 10

    def test_summary_empty_store(self, store):
        summary = store.summary()
        assert summary["total"] == 0

    def test_disclaimer_constant(self):
        assert (
            "detection claims" in CANDIDATE_STORE_DISCLAIMER
            or "do not constitute" in CANDIDATE_STORE_DISCLAIMER
        )


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestCandidateStoreCLI:
    def test_init_creates_db(self, tmp_path, capsys):
        from techno_search.cli import main

        db = tmp_path / "cli_test.db"
        ret = main(["candidate-store-init", "--db-path", str(db)])
        assert ret == 0
        assert db.exists()

    def test_summary_nonexistent_db_returns_error(self, tmp_path):
        import io

        from techno_search.cli import main

        out = io.StringIO()
        db = tmp_path / "missing.db"
        ret = main(["candidate-store-summary", "--db-path", str(db)], stdout=out)
        assert ret == 1

    def test_list_nonexistent_db_returns_error(self, tmp_path):
        import io

        from techno_search.cli import main

        out = io.StringIO()
        db = tmp_path / "missing.db"
        ret = main(["candidate-store-list", "--db-path", str(db)], stdout=out)
        assert ret == 1

    def test_summary_after_init(self, tmp_path):
        import io

        from techno_search.cli import main

        db = tmp_path / "cli_test2.db"
        main(["candidate-store-init", "--db-path", str(db)])
        out = io.StringIO()
        ret = main(["candidate-store-summary", "--db-path", str(db)], stdout=out)
        assert ret == 0
        result = json.loads(out.getvalue())
        assert result["total"] == 0
