"""Metadata-first live-search target priority queue construction."""

from __future__ import annotations

import csv
import hashlib
import json
import ssl
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.background_search import BackgroundTarget, target_priority_score
from techno_search.schemas import Track

TARGET_PRIORITY_QUEUE_SCHEMA_VERSION = "target_priority_queue_v1"
TARGET_PRIORITY_QUEUE_DISCLAIMER = (
    "Target priority queues are metadata-first scheduling aids for local search "
    "planning. They are not detections, discovery claims, expert review, external "
    "validation, or authorization for external submission."
)
TARGET_PRIORITY_MANIFEST_SCHEMA_VERSION = "target_priority_manifest_v1"
TARGET_PRIORITY_SIZE_PREFLIGHT_SCHEMA_VERSION = "target_priority_size_preflight_v1"
DEFAULT_PROJECT = "2026 Technosignature Search"
DEFAULT_SOURCE = "Breakthrough Listen HPRC full target catalog"
DEFAULT_CITATIONS = (
    "docs/bl_hprc_target_list_research.md; "
    "docs/astrometrics_data_selection_policy.md; "
    "docs/SYSTEMATIC_SEARCH_PLAN.md"
)

TARGET_PRIORITY_QUEUE_FIELDS = [
    "target_id",
    "project",
    "source",
    "catalog_ids",
    "ra_deg",
    "dec_deg",
    "data_products_available",
    "estimated_download_gb",
    "search_category",
    "scientific_novelty",
    "prior_significance",
    "followup_leverage",
    "data_quality",
    "method_advantage",
    "publication_value",
    "community_integration",
    "new_followup_balance",
    "storage_cost_penalty",
    "total_priority",
    "status",
    "notes",
    "citations",
    "local_coverage_status",
    "background_target_priority_score",
    "source_hdf5_url",
]


@dataclass(frozen=True)
class _CoverageState:
    reused_or_downloaded_targets: frozenset[str]
    discovered_hdf5_urls: dict[str, str]
    size_preflight_targets: dict[str, dict[str, Any]]
    skipped_targets: dict[str, str]


def _target_id_from_row(row: dict[str, str]) -> str:
    name = row.get("name") or row.get("Star") or ""
    if name.strip():
        return name.strip()
    hip = (row.get("hip") or row.get("HIP") or "").strip()
    return f"HIP{hip}" if hip else ""


def _aliases_for_row(row: dict[str, str]) -> frozenset[str]:
    aliases: set[str] = set()
    target_id = _target_id_from_row(row)
    if target_id:
        aliases.add(target_id)
    for key in ("hip", "HIP", "name", "Star", "SimbadName"):
        value = (row.get(key) or "").strip()
        if not value:
            continue
        aliases.add(value)
        if value.isdigit():
            aliases.add(f"HIP{value}")
        if value.upper().startswith("HIP") and value[3:].isdigit():
            aliases.add(f"HIP{value[3:]}")
    return frozenset(aliases)


def _catalog_ids_for_row(row: dict[str, str]) -> str:
    values: list[str] = []
    raw_hip = (row.get("hip") or row.get("HIP") or "").strip()
    if raw_hip:
        values.append(f"HIP {raw_hip}" if raw_hip.isdigit() else raw_hip)
    name = (row.get("name") or row.get("Star") or "").strip()
    if name and name not in values:
        values.append(name)
    return "; ".join(values) if values else _target_id_from_row(row)


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _format_score(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _format_coord(value: str | None) -> str:
    number = _float_or_none(value)
    if number is None:
        return ""
    return f"{number:.6f}".rstrip("0").rstrip(".")


def _load_seed_targets(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_coverage_state(
    path: Path,
    *,
    size_preflight_report_paths: Sequence[Path] = (),
) -> _CoverageState:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    run = payload.get("runs", {}).get("download_bl_extended_corpus", {})
    reused = {str(target) for target in run.get("reused_targets", [])}
    downloaded = {str(target) for target in run.get("downloaded_targets", [])}
    skipped: dict[str, str] = {}
    for item in run.get("skipped_targets", []):
        if not isinstance(item, dict):
            continue
        target = str(item.get("target", "")).strip()
        reason = str(item.get("reason", "")).strip() or "skipped_without_reason"
        if target:
            skipped[target] = reason
    discovery_run = payload.get("runs", {}).get("download_bl_extended_corpus_discovery", {})
    discovered_hdf5_urls: dict[str, str] = {}
    for item in discovery_run.get("available_targets", []):
        if not isinstance(item, dict):
            continue
        target = str(item.get("target", "")).strip()
        url = str(item.get("url", "")).strip()
        if target and url:
            discovered_hdf5_urls[target] = url
    for item in discovery_run.get("skipped_targets", []):
        if not isinstance(item, dict):
            continue
        target = str(item.get("target", "")).strip()
        reason = str(item.get("reason", "")).strip() or "skipped_without_reason"
        if target and target not in discovered_hdf5_urls:
            skipped[target] = reason
    size_preflight_targets: dict[str, dict[str, Any]] = {}
    for report_path in dict.fromkeys(size_preflight_report_paths):
        if report_path is None or not report_path.exists():
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for item in report.get("targets", []):
            if not isinstance(item, dict):
                continue
            target = str(item.get("target_id", "")).strip()
            url = str(item.get("url", "")).strip()
            if target and url and item.get("ok") is True:
                size_preflight_targets[target] = item
    return _CoverageState(
        reused_or_downloaded_targets=frozenset(reused | downloaded),
        discovered_hdf5_urls=discovered_hdf5_urls,
        size_preflight_targets=size_preflight_targets,
        skipped_targets=skipped,
    )


def _prior_significance(row: dict[str, str]) -> float:
    score = 0.75
    distance_pc = _float_or_none(row.get("dist_pc") or row.get("Dist"))
    if distance_pc is not None:
        if distance_pc <= 10:
            score += 1.5
        elif distance_pc <= 25:
            score += 1.0
        elif distance_pc <= 50:
            score += 0.5
    if (row.get("exoplanet") or "").strip() in {"1", "true", "True", "yes"}:
        score += 0.75
    spectral_type = (row.get("spec_type") or row.get("SpType") or "").strip().upper()
    if spectral_type.startswith(("F", "G", "K", "M")):
        score += 0.25
    return min(score, 3.0)


def _publication_value(row: dict[str, str]) -> float:
    score = 1.0
    distance_pc = _float_or_none(row.get("dist_pc") or row.get("Dist"))
    if distance_pc is not None:
        if distance_pc <= 10:
            score += 1.0
        elif distance_pc <= 25:
            score += 0.5
    if (row.get("exoplanet") or "").strip() in {"1", "true", "True", "yes"}:
        score += 0.75
    return min(score, 3.0)


def _data_quality(row: dict[str, str], data_products_available: str) -> float:
    score = 0.0
    if _float_or_none(row.get("ra_deg") or row.get("RAJ2000")) is not None:
        score += 0.75
    if _float_or_none(row.get("dec_deg") or row.get("DEJ2000")) is not None:
        score += 0.75
    if _float_or_none(row.get("dist_pc") or row.get("Dist")) is not None:
        score += 0.5
    if (row.get("spec_type") or row.get("SpType") or "").strip():
        score += 0.5
    if data_products_available in {
        "local_cache_present",
        "hdf5_url_discovered",
        "hdf5_size_preflight_ok",
    }:
        score += 0.5
    elif data_products_available == "requires_product_metadata_discovery":
        score += 0.25
    return min(score, 3.0)


def _classification_for_aliases(
    aliases: frozenset[str], coverage: _CoverageState
) -> tuple[str, str, str, str, str, float, float, str]:
    if aliases & coverage.reused_or_downloaded_targets:
        return (
            "local_cache_present",
            "",
            "control_live_run",
            "already_acquired_local_cache",
            "searched_by_project",
            0.5,
            1.0,
            "",
        )
    size_preflight_aliases = sorted(
        alias for alias in aliases if alias in coverage.size_preflight_targets
    )
    if size_preflight_aliases:
        preflight = coverage.size_preflight_targets[size_preflight_aliases[0]]
        size_gb = preflight.get("content_length_gb")
        estimated_download_gb = (
            f"{float(size_gb):.6f}".rstrip("0").rstrip(".")
            if isinstance(size_gb, (int, float))
            else ""
        )
        return (
            "hdf5_size_preflight_ok",
            estimated_download_gb,
            "new_parameter_space",
            "raw_download_approval_required",
            "not_searched_size_preflight_ok",
            2.75,
            2.75,
            str(preflight.get("url", "")).strip(),
        )
    discovered_aliases = sorted(
        alias for alias in aliases if alias in coverage.discovered_hdf5_urls
    )
    if discovered_aliases:
        return (
            "hdf5_url_discovered",
            "",
            "new_parameter_space",
            "size_preflight_required",
            "not_searched_hdf5_url_discovered",
            2.75,
            2.75,
            coverage.discovered_hdf5_urls[discovered_aliases[0]],
        )
    skipped_aliases = sorted(
        alias for alias in aliases if alias in coverage.skipped_targets
    )
    if skipped_aliases:
        reason = coverage.skipped_targets[skipped_aliases[0]]
        return (
            reason,
            "",
            "new_parameter_space",
            "metadata_discovery_required",
            "not_searched_product_discovery_failed",
            2.5,
            2.0,
            "",
        )
    return (
        "requires_product_metadata_discovery",
        "",
        "new_parameter_space",
        "queued_metadata_discovery",
        "not_searched_by_project",
        3.0,
        3.0,
        "",
    )


def _queue_row(row: dict[str, str], coverage: _CoverageState) -> dict[str, str]:
    target_id = _target_id_from_row(row)
    aliases = _aliases_for_row(row)
    (
        data_products_available,
        estimated_download_gb,
        search_category,
        status,
        local_coverage_status,
        scientific_novelty,
        new_followup_balance,
        source_hdf5_url,
    ) = _classification_for_aliases(aliases, coverage)
    prior_significance = _prior_significance(row)
    followup_leverage = 0.0
    data_quality = _data_quality(row, data_products_available)
    method_advantage = (
        2.5
        if status
        in {
            "queued_metadata_discovery",
            "size_preflight_required",
            "raw_download_approval_required",
        }
        else 1.5
    )
    if status == "already_acquired_local_cache":
        method_advantage = 1.0
    publication_value = _publication_value(row)
    community_integration = 3.0
    storage_cost_penalty = 0.0
    total_priority = (
        scientific_novelty
        + prior_significance
        + followup_leverage
        + data_quality
        + method_advantage
        + publication_value
        + community_integration
        + new_followup_balance
        - storage_cost_penalty
    )
    background_target = BackgroundTarget(
        target_id=target_id,
        track=Track.RADIO,
        source_id=DEFAULT_SOURCE,
        followup_value=followup_leverage / 3.0,
        novelty_score=scientific_novelty / 3.0,
        data_quality_score=data_quality / 3.0,
        observability_score=publication_value / 3.0,
        false_positive_probability=0.0,
        blocking_issue_count=0 if status != "metadata_discovery_required" else 1,
    )
    notes = (
        "Metadata-first queue row. Raw download not authorized until product "
        "metadata supplies product type, size, cadence, URI, and storage estimate."
    )
    if status == "already_acquired_local_cache":
        notes = (
            "Already present in local extended-corpus evidence; keep as control or "
            "reanalysis target, not as a novel acquisition."
        )
    elif status == "metadata_discovery_required":
        notes = (
            "Previous BL extended-corpus discovery did not find an HDF5 URL; retry "
            "metadata discovery before any raw acquisition."
        )
    elif status == "size_preflight_required":
        notes = (
            "Current BL HDF5 URL discovered. Run size/checksum/storage preflight "
            "before any raw acquisition."
        )
    elif status == "raw_download_approval_required":
        notes = (
            "Current BL HDF5 URL passed HEAD-only size preflight. Raw download "
            "still requires explicit operator approval and storage-reserve check."
        )
    return {
        "target_id": target_id,
        "project": DEFAULT_PROJECT,
        "source": DEFAULT_SOURCE,
        "catalog_ids": _catalog_ids_for_row(row),
        "ra_deg": _format_coord(row.get("ra_deg") or row.get("RAJ2000")),
        "dec_deg": _format_coord(row.get("dec_deg") or row.get("DEJ2000")),
        "data_products_available": data_products_available,
        "estimated_download_gb": estimated_download_gb,
        "search_category": search_category,
        "scientific_novelty": _format_score(scientific_novelty),
        "prior_significance": _format_score(prior_significance),
        "followup_leverage": _format_score(followup_leverage),
        "data_quality": _format_score(data_quality),
        "method_advantage": _format_score(method_advantage),
        "publication_value": _format_score(publication_value),
        "community_integration": _format_score(community_integration),
        "new_followup_balance": _format_score(new_followup_balance),
        "storage_cost_penalty": _format_score(storage_cost_penalty),
        "total_priority": _format_score(total_priority),
        "status": status,
        "notes": notes,
        "citations": DEFAULT_CITATIONS,
        "local_coverage_status": local_coverage_status,
        "background_target_priority_score": _format_score(
            target_priority_score(background_target)
        ),
        "source_hdf5_url": source_hdf5_url,
    }


def build_target_priority_queue(
    *,
    seed_csv_path: Path = Path("data/bl_hprc_full_seed_targets.csv"),
    data_status_path: Path = Path("docs/data_collection_status.json"),
    size_preflight_report_path: Path = Path(
        "data_selection/batch_manifests/local_coverage_top25_size_preflight_report.json"
    ),
    extra_size_preflight_report_paths: Sequence[Path] = (),
) -> list[dict[str, str]]:
    """Build sorted target-priority rows from committed metadata and status.

    Every committed size-preflight report is a separate acquisition batch
    (e.g. ``local_coverage_top25_size_preflight_report.json``,
    ``local_coverage_next25_size_preflight_report.json``). All of them must be
    merged, not just the single default/legacy report, or promoting a later
    batch to ``raw_download_approval_required`` would silently regress an
    earlier batch's promotion back to an unresolved status.
    """

    coverage = _load_coverage_state(
        data_status_path,
        size_preflight_report_paths=(
            size_preflight_report_path,
            *extra_size_preflight_report_paths,
        ),
    )
    queue_rows = [
        _queue_row(row, coverage)
        for row in _load_seed_targets(seed_csv_path)
        if _target_id_from_row(row)
    ]
    rows_by_target: dict[str, dict[str, str]] = {}
    for queue_row in queue_rows:
        previous = rows_by_target.get(queue_row["target_id"])
        if previous is None or float(queue_row["total_priority"]) > float(
            previous["total_priority"]
        ):
            rows_by_target[queue_row["target_id"]] = queue_row
    rows = list(rows_by_target.values())
    rows.sort(
        key=lambda item: (
            -float(item["total_priority"]),
            item["status"] != "queued_metadata_discovery",
            item["target_id"],
        )
    )
    return rows


def write_target_priority_queue(
    output_path: Path,
    *,
    seed_csv_path: Path = Path("data/bl_hprc_full_seed_targets.csv"),
    data_status_path: Path = Path("docs/data_collection_status.json"),
    size_preflight_report_path: Path = Path(
        "data_selection/batch_manifests/local_coverage_top25_size_preflight_report.json"
    ),
    extra_size_preflight_report_paths: Sequence[Path] = (),
) -> dict[str, Any]:
    """Write a target-priority queue CSV and return a compact summary."""

    rows = build_target_priority_queue(
        seed_csv_path=seed_csv_path,
        data_status_path=data_status_path,
        size_preflight_report_path=size_preflight_report_path,
        extra_size_preflight_report_paths=extra_size_preflight_report_paths,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TARGET_PRIORITY_QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return target_priority_queue_summary(output_path)


def read_target_priority_queue(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_target_priority_manifest(
    *,
    queue_path: Path = Path("data_selection/target_priority_queue.csv"),
    max_targets: int = 25,
    include_statuses: tuple[str, ...] = ("queued_metadata_discovery",),
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build a downloader-compatible manifest from top priority queue rows."""

    if max_targets <= 0:
        raise ValueError("max_targets must be positive")
    rows = [
        row
        for row in read_target_priority_queue(queue_path)
        if row.get("status") in include_statuses
    ]
    selected = rows[:max_targets]
    generated_at = generated_at_utc or datetime.now(UTC).isoformat()
    priorities = [float(row["total_priority"]) for row in selected]
    return {
        "schema_version": TARGET_PRIORITY_MANIFEST_SCHEMA_VERSION,
        "disclaimer": TARGET_PRIORITY_QUEUE_DISCLAIMER,
        "generated_at_utc": generated_at,
        "source_queue": {
            "path": str(queue_path),
            "sha256": _file_sha256(queue_path),
            "schema_version": TARGET_PRIORITY_QUEUE_SCHEMA_VERSION,
        },
        "selection": {
            "max_targets": max_targets,
            "include_statuses": list(include_statuses),
            "selected_count": len(selected),
            "min_total_priority": min(priorities) if priorities else None,
            "max_total_priority": max(priorities) if priorities else None,
        },
        "targets": [
            {
                "hip": row["target_id"],
                "name": row["target_id"],
                "ra_deg": float(row["ra_deg"]) if row["ra_deg"] else None,
                "dec_deg": float(row["dec_deg"]) if row["dec_deg"] else None,
                "search_category": row["search_category"],
                "queue_status": row["status"],
                "local_coverage_status": row["local_coverage_status"],
                "total_priority": float(row["total_priority"]),
                "background_target_priority_score": float(
                    row["background_target_priority_score"]
                ),
                "data_products_available": row["data_products_available"],
                "estimated_download_gb": float(row["estimated_download_gb"])
                if row.get("estimated_download_gb")
                else None,
                "source_hdf5_url": row.get("source_hdf5_url", ""),
                "notes": row["notes"],
            }
            for row in selected
        ],
    }


def write_target_priority_manifest(
    output_path: Path,
    *,
    queue_path: Path = Path("data_selection/target_priority_queue.csv"),
    max_targets: int = 25,
    include_statuses: tuple[str, ...] = ("queued_metadata_discovery",),
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Write a downloader-compatible manifest from top priority queue rows."""

    manifest = build_target_priority_manifest(
        queue_path=queue_path,
        max_targets=max_targets,
        include_statuses=include_statuses,
        generated_at_utc=generated_at_utc,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema_version": TARGET_PRIORITY_MANIFEST_SCHEMA_VERSION,
        "ok": True,
        "disclaimer": TARGET_PRIORITY_QUEUE_DISCLAIMER,
        "output_path": str(output_path),
        "source_queue_path": str(queue_path),
        "selected_count": manifest["selection"]["selected_count"],
        "include_statuses": list(include_statuses),
        "top_targets": [
            {
                "rank": index,
                "target_id": target["hip"],
                "total_priority": target["total_priority"],
            }
            for index, target in enumerate(manifest["targets"][:10], start=1)
        ],
    }


def _default_head_metadata(url: str, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(
            request,
            context=_make_ssl_context(),
            timeout=timeout_seconds,
        ) as response:
            return {
                "ok": True,
                "status_code": int(response.status),
                "headers": {key.lower(): value for key, value in response.headers.items()},
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status_code": int(exc.code),
            "headers": {key.lower(): value for key, value in exc.headers.items()},
            "error": str(exc),
        }
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        return {"ok": False, "status_code": None, "headers": {}, "error": str(exc)}


def _make_ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _int_header(headers: dict[str, str], key: str) -> int | None:
    value = headers.get(key, "").strip()
    if not value or not value.isdigit():
        return None
    return int(value)


def _checksum_headers(headers: dict[str, str]) -> dict[str, str]:
    checksum_keys = (
        "content-md5",
        "digest",
        "x-amz-checksum-sha256",
        "x-amz-checksum-sha1",
        "x-amz-checksum-crc32",
        "x-amz-meta-md5",
    )
    return {
        key: headers[key]
        for key in checksum_keys
        if headers.get(key, "").strip()
    }


def build_target_priority_size_preflight(
    manifest_path: Path = Path(
        "data_selection/batch_manifests/local_coverage_top25_size_preflight_manifest.json"
    ),
    *,
    timeout_seconds: float = 30.0,
    head_fn: Any | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """HEAD-probe URL-discovered target rows before raw acquisition."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    targets = manifest.get("targets", [])
    fn = head_fn or _default_head_metadata
    rows: list[dict[str, Any]] = []
    total_bytes = 0
    sized_count = 0
    ok_count = 0
    checksum_header_count = 0
    for index, target in enumerate(targets, start=1):
        url = str(target.get("source_hdf5_url", "")).strip()
        target_id = str(target.get("hip", "")).strip()
        if not url:
            rows.append(
                {
                    "rank": index,
                    "target_id": target_id,
                    "url": url,
                    "ok": False,
                    "status_code": None,
                    "content_length_bytes": None,
                    "content_length_gb": None,
                    "accept_ranges": "",
                    "etag": "",
                    "last_modified": "",
                    "content_type": "",
                    "checksum_headers": {},
                    "error": "missing source_hdf5_url",
                }
            )
            continue
        result = fn(url, timeout_seconds)
        headers = {
            str(key).lower(): str(value)
            for key, value in dict(result.get("headers", {})).items()
        }
        size_bytes = _int_header(headers, "content-length")
        checksum_headers = _checksum_headers(headers)
        if size_bytes is not None:
            sized_count += 1
            total_bytes += size_bytes
        if bool(result.get("ok")):
            ok_count += 1
        if checksum_headers:
            checksum_header_count += 1
        rows.append(
            {
                "rank": index,
                "target_id": target_id,
                "url": url,
                "ok": bool(result.get("ok")),
                "status_code": result.get("status_code"),
                "content_length_bytes": size_bytes,
                "content_length_gb": round(size_bytes / 1_000_000_000, 6)
                if size_bytes is not None
                else None,
                "accept_ranges": headers.get("accept-ranges", ""),
                "etag": headers.get("etag", ""),
                "last_modified": headers.get("last-modified", ""),
                "content_type": headers.get("content-type", ""),
                "checksum_headers": checksum_headers,
                "error": str(result.get("error", "")),
            }
        )
    return {
        "schema_version": TARGET_PRIORITY_SIZE_PREFLIGHT_SCHEMA_VERSION,
        "disclaimer": TARGET_PRIORITY_QUEUE_DISCLAIMER,
        "generated_at_utc": generated_at_utc or datetime.now(UTC).isoformat(),
        "source_manifest": {
            "path": str(manifest_path),
            "sha256": _file_sha256(manifest_path),
            "schema_version": manifest.get("schema_version"),
        },
        "target_count": len(rows),
        "ok_target_count": ok_count,
        "sized_target_count": sized_count,
        "checksum_header_count": checksum_header_count,
        "all_targets_ok": ok_count == len(rows),
        "all_targets_sized": sized_count == len(rows),
        "total_content_length_bytes": total_bytes,
        "total_content_length_gb": round(total_bytes / 1_000_000_000, 6),
        "max_allowed_download_gb": 250.0,
        "download_within_default_batch_limit": (total_bytes / 1_000_000_000) <= 250.0,
        "raw_download_authorized": False,
        "raw_download_authorization_note": (
            "Header preflight is planning evidence only. Raw download still requires "
            "operator approval, storage-reserve check, and policy-compliant role."
        ),
        "targets": rows,
    }


def write_target_priority_size_preflight(
    output_path: Path,
    *,
    manifest_path: Path = Path(
        "data_selection/batch_manifests/local_coverage_top25_size_preflight_manifest.json"
    ),
    timeout_seconds: float = 30.0,
    head_fn: Any | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Write URL HEAD preflight output for a size-preflight target manifest."""

    preflight = build_target_priority_size_preflight(
        manifest_path,
        timeout_seconds=timeout_seconds,
        head_fn=head_fn,
        generated_at_utc=generated_at_utc,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(preflight, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema_version": TARGET_PRIORITY_SIZE_PREFLIGHT_SCHEMA_VERSION,
        "ok": bool(preflight["all_targets_ok"] and preflight["all_targets_sized"]),
        "disclaimer": TARGET_PRIORITY_QUEUE_DISCLAIMER,
        "output_path": str(output_path),
        "source_manifest_path": str(manifest_path),
        "target_count": preflight["target_count"],
        "ok_target_count": preflight["ok_target_count"],
        "sized_target_count": preflight["sized_target_count"],
        "checksum_header_count": preflight["checksum_header_count"],
        "total_content_length_gb": preflight["total_content_length_gb"],
        "raw_download_authorized": False,
    }


def target_priority_queue_summary(
    queue_path: Path = Path("data_selection/target_priority_queue.csv"),
) -> dict[str, Any]:
    """Summarize the acquisition-level target-priority queue."""

    rows = read_target_priority_queue(queue_path)
    by_status = Counter(row.get("status", "") for row in rows)
    by_category = Counter(row.get("search_category", "") for row in rows)
    top_targets = rows[:10]
    return {
        "schema_version": TARGET_PRIORITY_QUEUE_SCHEMA_VERSION,
        "ok": bool(rows),
        "disclaimer": TARGET_PRIORITY_QUEUE_DISCLAIMER,
        "queue_path": str(queue_path),
        "target_count": len(rows),
        "field_count": len(TARGET_PRIORITY_QUEUE_FIELDS),
        "required_fields_present": all(
            field in rows[0] for field in TARGET_PRIORITY_QUEUE_FIELDS
        )
        if rows
        else False,
        "by_status": dict(sorted(by_status.items())),
        "by_search_category": dict(sorted(by_category.items())),
        "top_targets": [
            {
                "rank": index,
                "target_id": row["target_id"],
                "total_priority": float(row["total_priority"]),
                "status": row["status"],
                "search_category": row["search_category"],
                "local_coverage_status": row["local_coverage_status"],
            }
            for index, row in enumerate(top_targets, start=1)
        ],
    }
