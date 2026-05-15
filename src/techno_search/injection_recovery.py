"""Synthetic injection-recovery fixture summaries."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from techno_search.schemas import Pathway, Track

INJECTION_RECOVERY_SCHEMA_VERSION = "synthetic_injection_recovery_v1"
INJECTION_RECOVERY_DISCLAIMER = (
    "Synthetic injection-recovery fixtures are development diagnostics only; they are "
    "not calibrated survey sensitivity estimates."
)


@dataclass(frozen=True)
class InjectionRecoveryCase:
    """One synthetic injection-recovery fixture case."""

    case_id: str
    track: Track
    injection_type: str
    outcome: str
    expected_pathway: Pathway
    injected_signal_strength: float
    recovery_score: float
    false_alarm: bool


def default_injection_recovery_fixture_path() -> Path:
    """Return the repository-local synthetic injection-recovery fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "injection_recovery_summary.json"
    )


def load_injection_recovery_cases(
    path: Path | str | None = None,
) -> tuple[InjectionRecoveryCase, ...]:
    """Load and validate synthetic injection-recovery fixture cases."""

    fixture_path = default_injection_recovery_fixture_path() if path is None else Path(path)
    with fixture_path.open(encoding="utf-8") as handle:
        fixture = json.load(handle)
    if not isinstance(fixture, dict):
        msg = f"Injection-recovery fixture is not an object: {fixture_path}"
        raise ValueError(msg)
    if fixture.get("schema_version") != INJECTION_RECOVERY_SCHEMA_VERSION:
        msg = f"Unsupported injection-recovery fixture schema: {fixture_path}"
        raise ValueError(msg)
    cases = fixture.get("cases")
    if not isinstance(cases, list):
        msg = f"Injection-recovery fixture missing cases: {fixture_path}"
        raise ValueError(msg)
    return tuple(_case_from_mapping(case) for case in cases)


def injection_recovery_summary(path: Path | str | None = None) -> dict[str, object]:
    """Summarize synthetic injection-recovery fixture coverage."""

    fixture_path = default_injection_recovery_fixture_path() if path is None else Path(path)
    cases = load_injection_recovery_cases(fixture_path)
    recovered_or_missed = [
        case for case in cases if case.outcome in {"recovered", "missed"}
    ]
    recovered_count = sum(1 for case in recovered_or_missed if case.outcome == "recovered")
    false_alarm_count = sum(1 for case in cases if case.false_alarm)
    return {
        "fixture_path": str(fixture_path),
        "schema_version": INJECTION_RECOVERY_SCHEMA_VERSION,
        "disclaimer": INJECTION_RECOVERY_DISCLAIMER,
        "case_count": len(cases),
        "by_track": _counter_to_dict(Counter(case.track.value for case in cases)),
        "by_outcome": _counter_to_dict(Counter(case.outcome for case in cases)),
        "by_injection_type": _counter_to_dict(
            Counter(case.injection_type for case in cases)
        ),
        "by_expected_pathway": _counter_to_dict(
            Counter(case.expected_pathway.value for case in cases)
        ),
        "recovered_count": recovered_count,
        "missed_count": sum(1 for case in cases if case.outcome == "missed"),
        "false_alarm_count": false_alarm_count,
        "synthetic_recovery_rate": _safe_ratio(recovered_count, len(recovered_or_missed)),
        "synthetic_false_alarm_fraction": _safe_ratio(false_alarm_count, len(cases)),
        "case_ids": sorted(case.case_id for case in cases),
    }


def false_negative_summary(path: Path | str | None = None) -> dict[str, object]:
    """Summarize missed injections (false negatives) from the injection-recovery fixture.

    False negatives are injection cases with outcome 'missed' — signals that were
    injected but not recovered. A high missed-injection rate suggests the scoring
    model or baseline classifier has low sensitivity for that track or signal type.
    All rates are synthetic development diagnostics only.
    """
    fixture_path = default_injection_recovery_fixture_path() if path is None else Path(path)
    cases = load_injection_recovery_cases(fixture_path)

    missed_cases = [case for case in cases if case.outcome == "missed"]
    total_injected = [case for case in cases if not case.false_alarm]

    by_track_total: Counter[str] = Counter()
    by_track_missed: Counter[str] = Counter()
    for case in total_injected:
        by_track_total[case.track.value] += 1
    for case in missed_cases:
        by_track_missed[case.track.value] += 1

    track_missed_rates: dict[str, float] = {}
    for track, total in by_track_total.items():
        track_missed_rates[track] = _safe_ratio(by_track_missed.get(track, 0), total)

    total_injected_count = len(total_injected)
    missed_count = len(missed_cases)
    overall_missed_rate = _safe_ratio(missed_count, total_injected_count)

    by_type_missed: dict[str, int] = {}
    for case in missed_cases:
        by_type_missed[case.injection_type] = by_type_missed.get(case.injection_type, 0) + 1

    return {
        "schema_version": INJECTION_RECOVERY_SCHEMA_VERSION,
        "disclaimer": INJECTION_RECOVERY_DISCLAIMER,
        "total_injected_cases": total_injected_count,
        "missed_count": missed_count,
        "false_alarm_count": len(cases) - total_injected_count,
        "synthetic_missed_injection_rate": overall_missed_rate,
        "by_track_missed_count": _counter_to_dict(by_track_missed),
        "by_track_missed_rate": track_missed_rates,
        "by_injection_type_missed": dict(sorted(by_type_missed.items())),
        "missed_case_ids": sorted(case.case_id for case in missed_cases),
    }


def _case_from_mapping(data: object) -> InjectionRecoveryCase:
    if not isinstance(data, dict):
        msg = "Injection-recovery case must be an object"
        raise ValueError(msg)
    return InjectionRecoveryCase(
        case_id=str(data["case_id"]),
        track=Track(str(data["track"])),
        injection_type=str(data["injection_type"]),
        outcome=str(data["outcome"]),
        expected_pathway=Pathway(str(data["expected_pathway"])),
        injected_signal_strength=float(data["injected_signal_strength"]),
        recovery_score=float(data["recovery_score"]),
        false_alarm=bool(data["false_alarm"]),
    )


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
