import json

import pandas as pd
import pytest

from techno_search.track_a_replay import (
    run_historical_replay,
    save_historical_replay_report,
)


def _write_catalog(tmp_path, *, name, rows):
    pytest.importorskip("pyarrow")
    out_dir = tmp_path / "data_cache" / "normalized"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out_dir / f"{name}.parquet", index=False)


def test_replay_recovers_sampled_real_catalog_rows(tmp_path) -> None:
    _write_catalog(
        tmp_path,
        name="atnf",
        rows=[
            {
                "source_id": "J0534+2200",
                "ra_deg": 83.633208,
                "dec_deg": 22.014472,
                "object_class": "pulsar",
                "catalog_name": "atnf",
            }
        ],
    )

    report = run_historical_replay(project_root=tmp_path)

    assert report["catalogs_available"] == ["atnf"]
    assert report["case_count"] == 2  # 1 sampled row + negative control
    assert report["all_recovered"] is True
    atnf_case = next(r for r in report["results"] if r["case"]["catalog_name"] == "atnf")
    assert atnf_case["classification"] == "known_pulsar"
    assert atnf_case["recovered"] is True


def test_replay_negative_control_reports_no_known_match_when_all_catalogs_loaded(
    tmp_path,
) -> None:
    for name in ("atnf", "chime_frb", "romabzcat", "fermi_4fgl"):
        _write_catalog(
            tmp_path,
            name=name,
            rows=[
                {
                    "source_id": "J0534+2200",
                    "ra_deg": 83.633208,
                    "dec_deg": 22.014472,
                    "object_class": "pulsar",
                    "catalog_name": name,
                }
            ],
        )

    report = run_historical_replay(project_root=tmp_path)

    control_case = next(
        r for r in report["results"] if r["case"]["case_id"] == "negative-control-south-pole"
    )
    assert control_case["classification"] == "no_known_match"
    assert control_case["recovered"] is True


def test_replay_negative_control_reports_low_confidence_with_partial_catalogs(
    tmp_path,
) -> None:
    _write_catalog(
        tmp_path,
        name="atnf",
        rows=[
            {
                "source_id": "J0534+2200",
                "ra_deg": 83.633208,
                "dec_deg": 22.014472,
                "object_class": "pulsar",
                "catalog_name": "atnf",
            }
        ],
    )

    report = run_historical_replay(project_root=tmp_path)

    control_case = next(
        r for r in report["results"] if r["case"]["case_id"] == "negative-control-south-pole"
    )
    assert control_case["classification"] == "low_confidence"
    assert control_case["recovered"] is True


def test_replay_reports_no_cases_when_no_catalogs_acquired(tmp_path) -> None:
    report = run_historical_replay(project_root=tmp_path)

    assert report["catalogs_available"] == []
    assert report["case_count"] == 1  # negative control only
    assert report["all_recovered"] is True


def test_replay_flags_unrecovered_case(tmp_path, monkeypatch) -> None:
    _write_catalog(
        tmp_path,
        name="atnf",
        rows=[
            {
                "source_id": "J0534+2200",
                "ra_deg": 83.633208,
                "dec_deg": 22.014472,
                "object_class": "pulsar",
                "catalog_name": "atnf",
            }
        ],
    )

    def _broken_crossmatch(*_args, **_kwargs):
        return {"classification": "no_known_match"}

    monkeypatch.setattr(
        "techno_search.track_a_replay.cross_match_known_sources", _broken_crossmatch
    )

    report = run_historical_replay(project_root=tmp_path)

    assert report["all_recovered"] is False
    assert report["recovered_count"] < report["case_count"]


def test_save_historical_replay_report_writes_json(tmp_path) -> None:
    report = run_historical_replay(project_root=tmp_path)

    saved_path = save_historical_replay_report(report, project_root=tmp_path)

    assert saved_path.exists()
    loaded = json.loads(saved_path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == report["schema_version"]
