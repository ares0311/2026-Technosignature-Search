from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from techno_search.cli import main
from techno_search.meerkat_frequency_neighbors import (
    iter_json_array_records,
    meerkat_frequency_neighbor_summary,
)


def _hit(
    frequency_mhz: float,
    *,
    target: str,
    artifact: str,
    beam: int,
) -> dict[str, object]:
    return {
        "frequency": frequency_mhz,
        "sourceName": target,
        "filename": artifact,
        "hostname": "blpn37",
        "beam": beam,
        "coarseChannel": 10,
        "tstart": 60984.1,
        "driftRate": 0.1,
        "snr": 12.0,
    }


def test_frequency_neighbor_summary_streams_and_deduplicates(tmp_path: Path) -> None:
    first = _hit(1000.0, target="A", artifact="a.hits", beam=1)
    rows = [
        first,
        dict(first),
        _hit(1000.0003, target="B", artifact="b.hits", beam=2),
        _hit(1000.002, target="C", artifact="c.hits", beam=3),
        {"frequency": None, "sourceName": "INVALID"},
    ]
    path = tmp_path / "hits.json"
    path.write_text(json.dumps(rows), encoding="utf-8")

    result = meerkat_frequency_neighbor_summary(
        path,
        [1_000_000_000.0],
        tolerance_hz=500.0,
        sample_limit=5,
    )

    assert result["streaming_read"] is True
    assert result["materialized_output_created"] is False
    assert result["scanned_hit_count"] == 5
    assert result["invalid_frequency_row_count"] == 1
    query = result["query_summaries"][0]
    assert query["raw_match_count"] == 3
    assert query["unique_match_count"] == 2
    assert query["duplicate_match_count"] == 1
    assert query["unique_target_count"] == 2
    assert query["cross_target_recurrence_present"] is True
    assert query["cross_artifact_recurrence_present"] is True
    assert query["same_artifact_multibeam_present"] is False
    assert len(query["sample_matches"]) == 3


def test_iter_json_array_records_supports_gzip_and_small_chunks(tmp_path: Path) -> None:
    rows = [
        _hit(900.0, target="A", artifact="shared.hits", beam=1),
        _hit(900.0001, target="B", artifact="shared.hits", beam=2),
    ]
    path = tmp_path / "hits.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(rows, handle)

    streamed = list(iter_json_array_records(path, chunk_size_bytes=17))
    result = meerkat_frequency_neighbor_summary(path, [900_000_000.0])

    assert streamed == rows
    query = result["query_summaries"][0]
    assert query["same_artifact_multibeam_present"] is True
    assert query["cross_artifact_recurrence_present"] is False


def test_iter_json_array_records_rejects_non_array(tmp_path: Path) -> None:
    path = tmp_path / "not_array.json"
    path.write_text('{"frequency": 1000.0}', encoding="utf-8")

    with pytest.raises(ValueError, match="top-level JSON array"):
        list(iter_json_array_records(path))


def test_iter_json_array_records_rejects_unterminated_array(tmp_path: Path) -> None:
    path = tmp_path / "unterminated.json"
    path.write_text('[{"frequency": 1000.0}', encoding="utf-8")

    with pytest.raises(ValueError, match="Unterminated top-level JSON array"):
        list(iter_json_array_records(path, chunk_size_bytes=5))


def test_cli_meerkat_frequency_neighbor_summary(tmp_path: Path, capsys) -> None:
    path = tmp_path / "hits.json"
    path.write_text(
        json.dumps([_hit(1000.0, target="A", artifact="a.hits", beam=1)]),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "meerkat-frequency-neighbor-summary",
            "--raw-json",
            str(path),
            "--frequency-hz",
            "1000000000",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert result["schema_version"] == "meerkat_frequency_neighbors_v1"
    assert result["query_summaries"][0]["raw_match_count"] == 1
