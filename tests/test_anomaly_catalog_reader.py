"""Tests for archival/catalog anomaly CSV reader."""

from __future__ import annotations

from pathlib import Path

import pytest

from techno_search.anomalies.catalog_reader import (
    anomaly_rows_to_candidate_dicts,
    read_anomaly_csv,
)
from techno_search.anomalies.prototype import build_anomaly_candidate

FIXTURE = Path(__file__).parent / "fixtures" / "anomaly" / "sample_archival_anomaly.csv"


def test_read_anomaly_csv_returns_rows() -> None:
    rows = read_anomaly_csv(FIXTURE)
    assert len(rows) == 2


def test_read_anomaly_csv_coerces_numeric_values() -> None:
    row = read_anomaly_csv(FIXTURE)[0]
    assert row["historical_epoch"] == pytest.approx(1954.2)
    assert row["modern_limit_magnitude"] == pytest.approx(19.8)
    assert row["modern_magnitude"] is None


def test_anomaly_rows_feed_candidate_builder() -> None:
    row = anomaly_rows_to_candidate_dicts(FIXTURE)[0]
    candidate = build_anomaly_candidate(
        "anomaly-reader-test",
        row,
        provenance={"source_file": str(FIXTURE)},
    )
    assert candidate.track.value == "anomaly"
    assert candidate.features["historical_source_id"] == "hist-synth-001"
    assert candidate.features["modern_non_detection_score"] > 0
