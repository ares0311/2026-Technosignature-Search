from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ingest_meerkat_hits.py"
SPEC = importlib.util.spec_from_file_location("ingest_meerkat_hits", SCRIPT_PATH)
assert SPEC is not None
ingest_meerkat_hits = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ingest_meerkat_hits)


def _atlas_hit(**overrides: object) -> dict[str, object]:
    hit: dict[str, object] = {
        "frequency": 924.9910576790571,
        "index": 81977,
        "driftSteps": 12,
        "driftRate": 0.06052830194730198,
        "snr": 15.208671,
        "coarseChannel": 10,
        "beam": 0,
        "power": 4.6325947e16,
        "incoherentPower": 0.0,
        "sourceName": "Atlas",
        "fch1": 924.9909939020872,
        "foff": 0.0000015944242477416992,
        "tstart": 60984.176537959574,
        "tsamp": 5.017485158878505,
        "ra": 13.255836111111112,
        "dec": -5.825555555555555,
        "telescopeId": 64,
        "numTimesteps": 57,
        "numChannels": 91,
        "startChannel": 81937,
        "fileindex": 1,
        "hostname": "blpn37",
        "filename": (
            "/scratch/data/20251105T041412Z-20251027-0004/"
            "seticore_search/guppi_60984_15252_001942_Atlas_0001.hits"
        ),
    }
    hit.update(overrides)
    return hit


def test_ingest_hits_normalizes_verified_atlas_seticore_schema(tmp_path: Path) -> None:
    json_path = tmp_path / "atlas_hits_sample.json"
    rows = [
        _atlas_hit(frequency=924.9910576790571, snr=15.208671),
        _atlas_hit(frequency=924.9910576790571, snr=30.0, beam=1),
        _atlas_hit(frequency=925.25, snr=10.0, driftRate=-0.2, coarseChannel=11),
    ]
    json_path.write_text(json.dumps(rows), encoding="utf-8")

    out_path = ingest_meerkat_hits.ingest_hits(json_path, tmp_path, max_hits=3)

    normalized = [
        json.loads(line)
        for line in out_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(normalized) == 3
    first = normalized[0]
    assert first["corpus_source"] == "meerkat_bluse_seticore_atlas_2025_11"
    assert first["frequency_hz"] == pytest.approx(924_991_057.6790571)
    assert first["drift_rate_hz_per_sec"] == pytest.approx(0.06052830194730198)
    assert first["snr"] == pytest.approx(15.208671)
    assert first["bandwidth_hz"] == pytest.approx(
        0.0000015944242477416992 * 91 * 1_000_000
    )
    assert first["normalized_drift_hz_s_per_ghz"] == pytest.approx(
        0.06052830194730198 / 0.9249910576790571
    )
    assert first["relative_snr"] == pytest.approx(15.208671 / 15.208671)
    assert first["frequency_persistence_score"] == pytest.approx(0.5)
    assert first["target_id"] == "Atlas"
    assert first["beam"] == 0
    assert first["coarse_channel"] == 10
    assert first["backend_host"] == "blpn37"
    assert first["source_artifact"].endswith(".hits")


def test_ingest_hits_fails_loudly_when_atlas_schema_is_missing(tmp_path: Path) -> None:
    json_path = tmp_path / "bad_atlas_hits.json"
    bad_hit = _atlas_hit()
    del bad_hit["driftRate"]
    json_path.write_text(json.dumps([bad_hit]), encoding="utf-8")

    with pytest.raises(ValueError, match="verified ATLAS MeerKAT BLUSE/SETICORE schema"):
        ingest_meerkat_hits.ingest_hits(json_path, tmp_path, max_hits=1)


def test_dry_run_allows_verified_atlas_source_without_network(
    capsys: pytest.CaptureFixture[str],
) -> None:
    ingest_meerkat_hits.main([
        "--use-verified-atlas-source",
        "--dry-run",
        "--max-hits",
        "5",
    ])

    out = capsys.readouterr().out
    assert ingest_meerkat_hits.VERIFIED_ATLAS_MEERKAT_URL in out
    assert ingest_meerkat_hits.VERIFIED_ATLAS_SHA256 in out
