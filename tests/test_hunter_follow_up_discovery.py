from __future__ import annotations

import json
from pathlib import Path

from techno_search.hunter_follow_up_discovery import (
    cadence_as_gbt_manifest,
    discover_follow_up_targets,
    parse_archive_products,
)


def _row(
    *,
    utc: str,
    mjd: float,
    target: str,
    size: int,
    md5: str,
    url: str,
) -> str:
    cells = [
        utc,
        f"{mjd:.4f}",
        "GBT",
        target,
        "302.7",
        "77.2",
        "2269.62890625",
        "HDF5",
        str(size),
        md5,
    ]
    return (
        "<tr>"
        + "".join(f"<td>{cell}</td>" for cell in cells)
        + f'<td><a href="{url}">Download</a></td></tr>'
    )


def _product_row(
    sequence: int,
    target: str,
    mjd: float,
    *,
    seconds: int,
) -> str:
    directory = "https://bldata.berkeley.edu/pipeline/AGBT17A_999_64/holding"
    filename = (
        "spliced_blc3031323334353637_guppi_57885_"
        f"{seconds}_{target}_{sequence:04d}.gpuspec.0002.h5"
    )
    return _row(
        utc=f"2017-05-12 08:{34 + sequence:02d}:00",
        mjd=mjd,
        target=target,
        size=241_000_000 + sequence,
        md5=f"{sequence:032x}",
        url=f"{directory}/{filename}",
    )


def _prior_cadence(tmp_path: Path) -> Path:
    path = tmp_path / "GBT_HIP99427_2016-12-30_ABACAD.csv"
    path.write_text("frequency\n", encoding="utf-8")
    artifacts = []
    for sequence, seconds in enumerate(
        (83026, 83371, 83716, 84066, 84416, 84766), 33
    ):
        artifacts.append(
            {
                "artifact_filename": (
                    "spliced_blc0001020304050607_guppi_57752_"
                    f"{seconds}_HIP99427_{sequence:04d}.gpuspec.0002.dat"
                )
            }
        )
    sidecar = path.with_name(path.name + ".provenance.json")
    sidecar.write_text(
        json.dumps(
            {
                "classification": "derived_real_observation_cadence",
                "source_artifacts": artifacts,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_parse_archive_products_keeps_exact_0002_hdf5_product() -> None:
    exact = _product_row(2, "HIP99427", 57885.3570, seconds=30844)
    other = exact.replace(".gpuspec.0002.h5", ".gpuspec.0000.h5")

    products = parse_archive_products(f"<table>{other}{exact}</table>")

    assert len(products) == 1
    assert products[0].target_name == "HIP99427"
    assert products[0].sequence == 2
    assert products[0].size_bytes == 241_000_002


def test_discovery_freezes_latest_complete_later_epoch_cadence(
    tmp_path: Path,
) -> None:
    prior_path = _prior_cadence(tmp_path)
    session_rows = [
        _product_row(2, "HIP99427", 57885.3570, seconds=30844),
        _product_row(3, "HIP100670", 57885.3608, seconds=31177),
        _product_row(4, "HIP99427", 57885.3647, seconds=31509),
        _product_row(5, "HIP99560", 57885.3686, seconds=31845),
        _product_row(6, "HIP99427", 57885.3725, seconds=32181),
        _product_row(7, "HIP99759", 57885.3763, seconds=32517),
    ]

    def fetcher(parameters: dict[str, str]) -> str:
        if "target" in parameters:
            return f"<table>{session_rows[0]}{session_rows[2]}{session_rows[4]}</table>"
        return f"<table>{''.join(session_rows)}</table>"

    targets, report = discover_follow_up_targets(
        [
            {
                "hip": "HIP99427",
                "recommended_next_action": (
                    "repeat an ON/OFF cadence at a later epoch and compare persistence"
                ),
                "source_data_path": str(prior_path),
            }
        ],
        fetcher=fetcher,
        retrieved_at_utc="2026-07-26T00:00:00Z",
    )

    target = targets[0]
    cadence = target["follow_up_cadence"]
    assert target["source_hdf5_url"] == ""
    assert target["estimated_download_gb"] == 1.446
    assert cadence["cadence_id"] == "GBT_HIP99427_2017-05-12_ABACAD"
    assert [scan["scan_role"] for scan in cadence["scans"]] == [
        "on",
        "off",
        "on",
        "off",
        "on",
        "off",
    ]
    assert [scan["source_name"] for scan in cadence["scans"]] == [
        "HIP99427",
        "HIP100670",
        "HIP99427",
        "HIP99560",
        "HIP99427",
        "HIP99759",
    ]
    assert cadence["follow_up_observation_min_mjd"] > cadence[
        "prior_observation_max_mjd"
    ]
    assert cadence["human_approval_status"] == "pending"
    assert report["cadence_discovery_count"] == 1

    approved = cadence_as_gbt_manifest(
        cadence, approved_at_utc="2026-07-26T00:01:00Z"
    )
    assert approved["schema_version"] == "gbt_observation_cadence_v1"
    assert approved["approved_for_local_real_data"] is True
    assert approved["hunter_acquisition_approval"]["method"].startswith(
        "Run-New-Search"
    )


def test_discovery_uses_authenticated_history_when_cadence_path_is_empty(
    tmp_path: Path,
) -> None:
    candidate_id = (
        "spliced_blc02030405_2bit_guppi_57457_48006_GJ699_0003.gpuspec.0002"
    )
    ledger_path = tmp_path / "follow_ups.json"
    ledger_path.write_text(
        json.dumps(
            {
                "run_id": "RUN-GJ699",
                "entries": [
                    {
                        "candidate_id": candidate_id,
                        "follow_up_id": "FU-GJ699",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    session_rows = [
        _product_row(2, "GJ699", 57885.3570, seconds=30844),
        _product_row(3, "HIP100670", 57885.3608, seconds=31177),
        _product_row(4, "GJ699", 57885.3647, seconds=31509),
        _product_row(5, "HIP99560", 57885.3686, seconds=31845),
        _product_row(6, "GJ699", 57885.3725, seconds=32181),
        _product_row(7, "HIP99759", 57885.3763, seconds=32517),
    ]

    def fetcher(parameters: dict[str, str]) -> str:
        if "target" in parameters:
            return f"<table>{session_rows[0]}{session_rows[2]}{session_rows[4]}</table>"
        return f"<table>{''.join(session_rows)}</table>"

    targets, report = discover_follow_up_targets(
        [
            {
                "hip": "GJ699",
                "recommended_next_action": (
                    "repeat an ON/OFF cadence at a later epoch and compare persistence"
                ),
                "source_data_path": "",
                "prior_search_provenance": [
                    {
                        "candidate_id": candidate_id,
                        "follow_up_id": "FU-GJ699",
                        "ledger_path": str(ledger_path),
                        "run_id": "RUN-GJ699",
                    }
                ],
            }
        ],
        target_count=1,
        fetcher=fetcher,
        retrieved_at_utc="2026-07-27T00:00:00Z",
    )

    assert targets[0]["hip"] == "GJ699"
    assert targets[0]["follow_up_cadence"]["prior_observation_max_mjd"] > 57457
    assert report["examined_target_count"] == 1
    assert report["unavailable_candidates"] == []


def test_discovery_expands_past_candidate_with_invalid_prior_history(
    tmp_path: Path,
) -> None:
    prior_path = _prior_cadence(tmp_path)
    session_rows = [
        _product_row(2, "HIP99427", 57885.3570, seconds=30844),
        _product_row(3, "HIP100670", 57885.3608, seconds=31177),
        _product_row(4, "HIP99427", 57885.3647, seconds=31509),
        _product_row(5, "HIP99560", 57885.3686, seconds=31845),
        _product_row(6, "HIP99427", 57885.3725, seconds=32181),
        _product_row(7, "HIP99759", 57885.3763, seconds=32517),
    ]

    def fetcher(parameters: dict[str, str]) -> str:
        if "target" in parameters:
            return f"<table>{session_rows[0]}{session_rows[2]}{session_rows[4]}</table>"
        return f"<table>{''.join(session_rows)}</table>"

    targets, report = discover_follow_up_targets(
        [
            {
                "hip": "INVALID",
                "recommended_next_action": "repeat at a later epoch",
                "source_data_path": "",
                "prior_search_provenance": [],
            },
            {
                "hip": "HIP99427",
                "recommended_next_action": "repeat at a later epoch",
                "source_data_path": str(prior_path),
            },
        ],
        target_count=1,
        fetcher=fetcher,
        retrieved_at_utc="2026-07-27T00:00:00Z",
    )

    assert [target["hip"] for target in targets] == ["HIP99427"]
    assert report["examined_target_count"] == 2
    assert report["unavailable_candidates"][0]["target_id"] == "INVALID"
