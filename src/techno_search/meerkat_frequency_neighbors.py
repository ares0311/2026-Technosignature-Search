"""Stream full MeerKAT hit tables for candidate-frequency neighbors."""

from __future__ import annotations

import gzip
import json
import math
from bisect import bisect_left
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, TextIO

MEERKAT_FREQUENCY_NEIGHBOR_SCHEMA_VERSION = "meerkat_frequency_neighbors_v1"
MEERKAT_FREQUENCY_NEIGHBOR_DISCLAIMER = (
    "Frequency-neighbor matches are deterministic full-corpus triage evidence only. "
    "They are not labels, detections, discoveries, proof of RFI origin, or external-"
    "submission authorization."
)
DEFAULT_FREQUENCY_TOLERANCE_HZ = 500.0
DEFAULT_CHUNK_SIZE_BYTES = 4 * 1024 * 1024


def iter_json_array_records(
    path: Path,
    *,
    chunk_size_bytes: int = DEFAULT_CHUNK_SIZE_BYTES,
) -> Iterator[dict[str, Any]]:
    """Yield objects from a top-level JSON array without loading it into memory."""
    source = Path(path)
    if chunk_size_bytes <= 0:
        raise ValueError("chunk_size_bytes must be positive")
    if not source.is_file():
        raise FileNotFoundError(f"MeerKAT hit table does not exist: {source}")

    opener = gzip.open if source.suffix == ".gz" else open
    with opener(source, "rt", encoding="utf-8") as handle:
        yield from _iter_json_array_handle(handle, chunk_size_bytes=chunk_size_bytes)


def meerkat_frequency_neighbor_summary(
    path: Path,
    query_frequencies_hz: Sequence[float],
    *,
    tolerance_hz: float = DEFAULT_FREQUENCY_TOLERANCE_HZ,
    sample_limit: int = 20,
) -> dict[str, Any]:
    """Summarize full-table frequency neighbors for explicit query frequencies."""
    source = Path(path)
    queries = _validated_queries(query_frequencies_hz)
    tolerance = float(tolerance_hz)
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance_hz must be finite and non-negative")
    if sample_limit < 0:
        raise ValueError("sample_limit must be non-negative")

    accumulators = {query: _new_accumulator() for query in queries}
    scanned_hit_count = 0
    invalid_frequency_row_count = 0
    for row_index, row in enumerate(iter_json_array_records(source), start=1):
        scanned_hit_count += 1
        frequency_hz = _positive_float(row.get("frequency"), scale=1_000_000.0)
        if frequency_hz is None:
            invalid_frequency_row_count += 1
            continue
        for query in _matching_queries(queries, frequency_hz, tolerance):
            _record_match(
                accumulators[query],
                row,
                row_index=row_index,
                frequency_hz=frequency_hz,
                query_frequency_hz=query,
                sample_limit=sample_limit,
            )

    query_summaries = [
        _finalize_query_summary(query, tolerance, accumulators[query])
        for query in queries
    ]
    return {
        "schema_version": MEERKAT_FREQUENCY_NEIGHBOR_SCHEMA_VERSION,
        "disclaimer": MEERKAT_FREQUENCY_NEIGHBOR_DISCLAIMER,
        "ok": True,
        "source_path": str(source),
        "source_size_bytes": source.stat().st_size,
        "streaming_read": True,
        "materialized_output_created": False,
        "frequency_unit_in_source": "MHz",
        "query_frequency_count": len(queries),
        "frequency_tolerance_hz": tolerance,
        "scanned_hit_count": scanned_hit_count,
        "invalid_frequency_row_count": invalid_frequency_row_count,
        "query_summaries": query_summaries,
        "query_count_with_cross_target_recurrence": sum(
            bool(item["cross_target_recurrence_present"])
            for item in query_summaries
        ),
        "query_count_with_cross_artifact_recurrence": sum(
            bool(item["cross_artifact_recurrence_present"])
            for item in query_summaries
        ),
    }


def _iter_json_array_handle(
    handle: TextIO,
    *,
    chunk_size_bytes: int,
) -> Iterator[dict[str, Any]]:
    decoder = json.JSONDecoder()
    buffer = ""
    position = 0
    eof = False
    array_started = False

    while True:
        if position >= len(buffer) and not eof:
            buffer = handle.read(chunk_size_bytes)
            position = 0
            eof = not buffer

        if not array_started:
            position = _skip_whitespace(buffer, position)
            if position >= len(buffer):
                if eof:
                    raise ValueError("MeerKAT hit table is empty")
                chunk = handle.read(chunk_size_bytes)
                buffer += chunk
                eof = not chunk
                continue
            if buffer[position] != "[":
                raise ValueError("MeerKAT hit table must contain a top-level JSON array")
            array_started = True
            position += 1

        position = _skip_delimiters(buffer, position)
        if position >= len(buffer):
            if eof:
                raise ValueError("Unterminated top-level JSON array")
            chunk = handle.read(chunk_size_bytes)
            buffer = buffer[position:] + chunk
            position = 0
            eof = not chunk
            continue
        if buffer[position] == "]":
            return

        try:
            value, end = decoder.raw_decode(buffer, position)
        except json.JSONDecodeError as exc:
            if eof:
                raise ValueError("Malformed or unterminated JSON array record") from exc
            chunk = handle.read(chunk_size_bytes)
            buffer = buffer[position:] + chunk
            position = 0
            eof = not chunk
            continue
        if not isinstance(value, dict):
            raise ValueError("Every MeerKAT hit-table array item must be an object")
        yield value
        position = end


def _skip_whitespace(buffer: str, position: int) -> int:
    while position < len(buffer) and buffer[position].isspace():
        position += 1
    return position


def _skip_delimiters(buffer: str, position: int) -> int:
    while position < len(buffer) and (
        buffer[position].isspace() or buffer[position] == ","
    ):
        position += 1
    return position


def _validated_queries(values: Sequence[float]) -> tuple[float, ...]:
    queries = tuple(sorted({float(value) for value in values}))
    if not queries:
        raise ValueError("At least one query frequency is required")
    if any(not math.isfinite(value) or value <= 0 for value in queries):
        raise ValueError("Query frequencies must be finite positive values")
    return queries


def _matching_queries(
    queries: tuple[float, ...],
    frequency_hz: float,
    tolerance_hz: float,
) -> Iterator[float]:
    index = bisect_left(queries, frequency_hz - tolerance_hz)
    while index < len(queries) and queries[index] <= frequency_hz + tolerance_hz:
        yield queries[index]
        index += 1


def _new_accumulator() -> dict[str, Any]:
    return {
        "raw_match_count": 0,
        "signatures": set(),
        "targets": set(),
        "source_artifacts": set(),
        "beams": set(),
        "backend_hosts": set(),
        "artifact_beams": {},
        "sample_matches": [],
    }


def _record_match(
    accumulator: dict[str, Any],
    row: dict[str, Any],
    *,
    row_index: int,
    frequency_hz: float,
    query_frequency_hz: float,
    sample_limit: int,
) -> None:
    target = str(row.get("sourceName") or "")
    source_artifact = str(row.get("filename") or "")
    backend_host = str(row.get("hostname") or "")
    beam = _integer(row.get("beam"), default=-1)
    tstart_mjd = _number(row.get("tstart"))
    drift_rate = _number(row.get("driftRate"))
    signature = (
        frequency_hz,
        target,
        source_artifact,
        beam,
        tstart_mjd,
        drift_rate,
    )

    accumulator["raw_match_count"] += 1
    accumulator["signatures"].add(signature)
    if target:
        accumulator["targets"].add(target)
    if source_artifact:
        accumulator["source_artifacts"].add(source_artifact)
        accumulator["artifact_beams"].setdefault(source_artifact, set()).add(beam)
    if beam >= 0:
        accumulator["beams"].add(beam)
    if backend_host:
        accumulator["backend_hosts"].add(backend_host)
    if len(accumulator["sample_matches"]) < sample_limit:
        accumulator["sample_matches"].append(
            {
                "row_index": row_index,
                "query_frequency_hz": query_frequency_hz,
                "frequency_hz": frequency_hz,
                "residual_hz": abs(frequency_hz - query_frequency_hz),
                "target_name": target,
                "source_artifact": source_artifact,
                "backend_host": backend_host,
                "beam": beam,
                "coarse_channel": _integer(row.get("coarseChannel"), default=-1),
                "tstart_mjd": tstart_mjd,
                "drift_rate_hz_per_sec": drift_rate,
                "snr": _number(row.get("snr")),
            }
        )


def _finalize_query_summary(
    query_frequency_hz: float,
    tolerance_hz: float,
    accumulator: dict[str, Any],
) -> dict[str, Any]:
    raw_match_count = int(accumulator["raw_match_count"])
    unique_match_count = len(accumulator["signatures"])
    targets = sorted(accumulator["targets"])
    source_artifacts = sorted(accumulator["source_artifacts"])
    beams = sorted(accumulator["beams"])
    multi_beam_artifacts = sorted(
        artifact
        for artifact, artifact_beams in accumulator["artifact_beams"].items()
        if len({beam for beam in artifact_beams if beam >= 0}) > 1
    )
    return {
        "query_frequency_hz": query_frequency_hz,
        "frequency_tolerance_hz": tolerance_hz,
        "raw_match_count": raw_match_count,
        "unique_match_count": unique_match_count,
        "duplicate_match_count": raw_match_count - unique_match_count,
        "unique_target_count": len(targets),
        "targets": targets[:20],
        "unique_source_artifact_count": len(source_artifacts),
        "sample_source_artifacts": source_artifacts[:10],
        "unique_beam_count": len(beams),
        "beams": beams[:20],
        "unique_backend_host_count": len(accumulator["backend_hosts"]),
        "backend_hosts": sorted(accumulator["backend_hosts"])[:20],
        "cross_target_recurrence_present": len(targets) > 1,
        "cross_artifact_recurrence_present": len(source_artifacts) > 1,
        "same_artifact_multibeam_present": bool(multi_beam_artifacts),
        "sample_multibeam_artifacts": multi_beam_artifacts[:10],
        "sample_matches": accumulator["sample_matches"],
    }


def _positive_float(value: Any, *, scale: float = 1.0) -> float | None:
    try:
        result = float(value) * scale
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result) or result <= 0:
        return None
    return result


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _integer(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
