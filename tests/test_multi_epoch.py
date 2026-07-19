"""Tests for multi-epoch hit-table comparison (techno_search.multi_epoch)."""

from __future__ import annotations

from pathlib import Path

import pytest

from techno_search.multi_epoch import (
    MultiEpochGroup,
    MultiEpochHit,
    compare_epochs,
    multi_epoch_summary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_hit_csv(path: Path, rows: list[dict]) -> None:
    """Write a minimal turboSETI-format .dat file for testing.

    Uses the real turboSETI TAB-separated format with the '# Top_Hit_#' header
    so that read_hit_table_csv() can parse it correctly.
    """
    if not rows:
        path.write_text(
            "# Source:TEST\n"
            "# Top_Hit_#\tDrift_Rate\tSNR\tUncorrected_Frequency\tCorrected_Frequency\tscan_role\n"
        )
        return
    header = (
        "# Source:TEST\n"
        "# Top_Hit_#\tDrift_Rate\tSNR\tUncorrected_Frequency\tCorrected_Frequency\tscan_role\n"
    )
    lines = [header]
    for i, row in enumerate(rows, start=1):
        freq_mhz = row["Corrected_Frequency"]
        snr_val = row["SNR"]
        drift_val = row["Drift_Rate"]
        role = row.get("scan_role", "ON")
        lines.append(f"{i}\t{drift_val}\t{snr_val}\t{freq_mhz}\t{freq_mhz}\t{role}\n")
    path.write_text("".join(lines))


def _make_hit_rows(
    freq_hz: float, snr: float = 25.0, drift: float = 0.0, role: str = "ON"
) -> list[dict]:
    freq_mhz = freq_hz / 1e6
    return [
        {
            "Corrected_Frequency": str(freq_mhz),
            "SNR": str(snr),
            "Drift_Rate": str(drift),
            "scan_role": role,
        }
    ]


# ---------------------------------------------------------------------------
# MultiEpochHit dataclass
# ---------------------------------------------------------------------------

class TestMultiEpochHit:
    def test_fields(self):
        hit = MultiEpochHit(
            frequency_mhz=1420.0,
            snr=30.0,
            drift_rate_hz_s=0.5,
            epoch_id="epoch_001",
            mjd=None,
            scan_role="ON",
        )
        assert hit.frequency_mhz == pytest.approx(1420.0)
        assert hit.snr == pytest.approx(30.0)
        assert hit.epoch_id == "epoch_001"
        assert hit.mjd is None
        assert hit.scan_role == "ON"


# ---------------------------------------------------------------------------
# MultiEpochGroup properties
# ---------------------------------------------------------------------------

class TestMultiEpochGroup:
    def _make_group(self, n_epochs: int, total: int) -> MultiEpochGroup:
        hits = [
            MultiEpochHit(1420.0, 25.0, 0.0, f"epoch_{i:03d}", None, "ON")
            for i in range(n_epochs)
        ]
        epoch_ids = [h.epoch_id for h in hits]
        return MultiEpochGroup(
            frequency_mhz=1420.0,
            tolerance_hz=1000.0,
            total_epochs_checked=total,
            hits=hits,
            epoch_ids=epoch_ids,
        )

    def test_epoch_count_unique(self):
        grp = self._make_group(3, 5)
        assert grp.epoch_count == 3

    def test_persistence_score_partial(self):
        grp = self._make_group(2, 4)
        assert grp.persistence_score == pytest.approx(0.5)

    def test_persistence_score_full(self):
        grp = self._make_group(5, 5)
        assert grp.persistence_score == pytest.approx(1.0)

    def test_persistence_score_single(self):
        grp = self._make_group(1, 5)
        assert grp.persistence_score == pytest.approx(0.2)

    def test_mean_snr(self):
        grp = self._make_group(3, 5)
        # All hits have snr=25.0
        assert grp.mean_snr == pytest.approx(25.0)

    def test_mean_snr_empty(self):
        grp = MultiEpochGroup(1420.0, 1000.0, 5, hits=[], epoch_ids=[])
        assert grp.mean_snr == pytest.approx(0.0)

    def test_as_dict_keys(self):
        grp = self._make_group(2, 4)
        d = grp.as_dict()
        for key in (
            "frequency_mhz", "epoch_count", "total_epochs_checked",
            "persistence_score", "mean_snr", "epoch_ids",
        ):
            assert key in d

    def test_epoch_ids_deduped_in_as_dict(self):
        # Duplicate epoch_ids should be counted once
        hits = [MultiEpochHit(1420.0, 25.0, 0.0, "epoch_001", None, "ON")] * 3
        grp = MultiEpochGroup(1420.0, 1000.0, 5, hits=hits, epoch_ids=["epoch_001"] * 3)
        d = grp.as_dict()
        assert grp.epoch_count == 1
        assert d["epoch_ids"] == ["epoch_001"]


# ---------------------------------------------------------------------------
# compare_epochs: integration over actual CSV files
# ---------------------------------------------------------------------------

class TestCompareEpochs:
    def test_single_file_no_cross_epoch(self, tmp_path):
        f = tmp_path / "epoch1.dat"
        _write_hit_csv(f, _make_hit_rows(1420.0e6, snr=30.0))
        result = compare_epochs([f])
        assert result.epoch_count == 1
        assert result.total_hits == 1
        assert len(result.groups) == 1
        # Only one file → no multi-epoch groups
        assert result.multi_epoch_groups == []

    def test_two_files_same_freq_grouped(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        f2 = tmp_path / "epoch2.dat"
        _write_hit_csv(f1, _make_hit_rows(1420.0e6, snr=30.0))
        _write_hit_csv(f2, _make_hit_rows(1420.0e6, snr=28.0))
        result = compare_epochs([f1, f2])
        assert result.epoch_count == 2
        assert result.total_hits == 2
        assert len(result.groups) == 1
        grp = result.groups[0]
        assert grp.epoch_count == 2
        assert grp.persistence_score == pytest.approx(1.0)

    def test_two_files_different_freq_not_grouped(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        f2 = tmp_path / "epoch2.dat"
        _write_hit_csv(f1, _make_hit_rows(1420.0e6, snr=30.0))
        _write_hit_csv(f2, _make_hit_rows(1500.0e6, snr=28.0))
        result = compare_epochs([f1, f2])
        assert len(result.groups) == 2
        # Different frequencies → each group has only 1 epoch
        assert all(g.epoch_count == 1 for g in result.groups)
        assert result.multi_epoch_groups == []

    def test_tolerance_controls_grouping(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        f2 = tmp_path / "epoch2.dat"
        # 500 Hz apart
        _write_hit_csv(f1, _make_hit_rows(1420_000_000.0, snr=30.0))
        _write_hit_csv(f2, _make_hit_rows(1420_000_500.0, snr=28.0))
        # Within 1000 Hz → grouped
        result_wide = compare_epochs([f1, f2], freq_tolerance_hz=1000.0)
        assert len(result_wide.groups) == 1
        # Within 100 Hz → not grouped
        result_narrow = compare_epochs([f1, f2], freq_tolerance_hz=100.0)
        assert len(result_narrow.groups) == 2

    def test_empty_files_skipped(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        f2 = tmp_path / "epoch2.dat"
        _write_hit_csv(f1, [])
        _write_hit_csv(f2, _make_hit_rows(1420.0e6, snr=30.0))
        result = compare_epochs([f1, f2])
        assert result.total_hits == 1
        assert result.epoch_count == 2

    def test_max_persistence_score(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        f2 = tmp_path / "epoch2.dat"
        _write_hit_csv(f1, _make_hit_rows(1420.0e6, snr=30.0))
        _write_hit_csv(f2, _make_hit_rows(1420.0e6, snr=28.0))
        result = compare_epochs([f1, f2])
        assert result.max_persistence_score == pytest.approx(1.0)

    def test_as_dict_keys(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        _write_hit_csv(f1, _make_hit_rows(1420.0e6))
        result = compare_epochs([f1])
        d = result.as_dict()
        for key in (
            "epoch_count", "total_hits", "group_count",
            "multi_epoch_group_count", "max_persistence_score", "groups", "disclaimer",
            "failed_epoch_count", "failed_epoch_ids",
        ):
            assert key in d

    def test_unreadable_epoch_is_reported_not_silently_dropped(self, tmp_path):
        """A .dat file that raises while being read/normalized must be surfaced.

        Previously the per-file `except Exception: pass` silently discarded
        the whole epoch's hits *and* still counted it toward
        `total_epochs_checked` (which came from `len(dat_files)`, not from
        how many files were actually read successfully). That silently
        biased `persistence_score` downward for a real recurring signal
        whenever any one epoch's file happened to be corrupt/unreadable,
        with no visible sign anything had gone wrong.
        """
        f1 = tmp_path / "epoch1.dat"
        f2 = tmp_path / "epoch2.dat"
        _write_hit_csv(f1, _make_hit_rows(1420.0e6, snr=30.0))
        # A directory, not a file: read_hit_table_csv's Path.read_text() call
        # raises IsADirectoryError, exercising the real failure path rather
        # than a mocked one.
        f2.mkdir()

        result = compare_epochs([f1, f2])

        assert result.failed_epoch_ids == ["epoch2"]
        assert result.as_dict()["failed_epoch_count"] == 1
        # Only the one real, successfully-read epoch should count toward
        # "checked" -- the unreadable epoch must not silently deflate the
        # persistence score of the signal actually found in epoch1.
        assert result.epoch_count == 1
        assert result.groups[0].total_epochs_checked == 1
        assert result.groups[0].persistence_score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# multi_epoch_summary convenience wrapper
# ---------------------------------------------------------------------------

class TestMultiEpochSummaryFunction:
    def test_returns_dict(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        _write_hit_csv(f1, _make_hit_rows(1420.0e6))
        summary = multi_epoch_summary([f1])
        assert isinstance(summary, dict)
        assert "epoch_count" in summary

    def test_two_epoch_persistence(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        f2 = tmp_path / "epoch2.dat"
        _write_hit_csv(f1, _make_hit_rows(1420.0e6, snr=30.0))
        _write_hit_csv(f2, _make_hit_rows(1420.0e6, snr=28.0))
        summary = multi_epoch_summary([f1, f2])
        assert summary["multi_epoch_group_count"] >= 1
        assert summary["max_persistence_score"] == pytest.approx(1.0)

    def test_disclaimer_present(self, tmp_path):
        f1 = tmp_path / "epoch1.dat"
        _write_hit_csv(f1, _make_hit_rows(1420.0e6))
        summary = multi_epoch_summary([f1])
        assert "disclaimer" in summary
        disc = summary["disclaimer"].lower()
        assert "detection claim" in disc or "evidence factor" in disc
