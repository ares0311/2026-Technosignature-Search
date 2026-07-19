"""Multi-epoch observation support for technosignature search.

Compares hits across multiple turboSETI .dat files from different observation
epochs (time-separated sessions) for the same target to identify signals that
persist across time.

Scientific guardrail: Multi-epoch persistence is an evidence factor only.
Persistent signals may be persistent RFI. This analysis does not constitute
a detection claim, does not authorize external submission, and does not
override the false-positive-first hypothesis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MULTI_EPOCH_DISCLAIMER = (
    "Multi-epoch persistence is an evidence factor only. Persistent signals may be "
    "persistent RFI. This analysis does not constitute a detection claim or authorize "
    "external submission."
)


@dataclass
class MultiEpochHit:
    """A single hit from one observation epoch."""

    frequency_mhz: float
    snr: float
    drift_rate_hz_s: float
    epoch_id: str
    mjd: float | None
    scan_role: str


@dataclass
class MultiEpochGroup:
    """Hits at similar frequency across one or more epochs."""

    frequency_mhz: float
    tolerance_hz: float
    total_epochs_checked: int
    hits: list[MultiEpochHit] = field(default_factory=list)
    epoch_ids: list[str] = field(default_factory=list)

    @property
    def epoch_count(self) -> int:
        return len(set(self.epoch_ids))

    @property
    def persistence_score(self) -> float:
        raw = self.epoch_count / max(1, self.total_epochs_checked)
        return max(0.0, min(1.0, raw))

    @property
    def mean_snr(self) -> float:
        if not self.hits:
            return 0.0
        return sum(h.snr for h in self.hits) / len(self.hits)

    def as_dict(self) -> dict[str, Any]:
        return {
            "frequency_mhz": self.frequency_mhz,
            "tolerance_hz": self.tolerance_hz,
            "epoch_count": self.epoch_count,
            "total_epochs_checked": self.total_epochs_checked,
            "persistence_score": self.persistence_score,
            "mean_snr": self.mean_snr,
            "epoch_ids": sorted(set(self.epoch_ids)),
            "hit_count": len(self.hits),
        }


@dataclass
class MultiEpochResult:
    """Result of comparing hits across multiple observation epochs."""

    epoch_count: int
    total_hits: int
    groups: list[MultiEpochGroup]
    disclaimer: str = MULTI_EPOCH_DISCLAIMER
    failed_epoch_ids: list[str] = field(default_factory=list)

    @property
    def multi_epoch_groups(self) -> list[MultiEpochGroup]:
        return [g for g in self.groups if g.epoch_count >= 2]

    @property
    def max_persistence_score(self) -> float:
        if not self.groups:
            return 0.0
        return max(g.persistence_score for g in self.groups)

    def as_dict(self) -> dict[str, Any]:
        return {
            "epoch_count": self.epoch_count,
            "total_hits": self.total_hits,
            "group_count": len(self.groups),
            "multi_epoch_group_count": len(self.multi_epoch_groups),
            "max_persistence_score": self.max_persistence_score,
            "groups": [g.as_dict() for g in self.groups],
            "failed_epoch_count": len(self.failed_epoch_ids),
            "failed_epoch_ids": list(self.failed_epoch_ids),
            "disclaimer": self.disclaimer,
        }


def compare_epochs(
    dat_files: list[Path],
    *,
    freq_tolerance_hz: float = 1000.0,
) -> MultiEpochResult:
    """Compare hits across multiple dat files from different observation epochs.

    Groups hits that fall within freq_tolerance_hz of each other across files.
    Each file is treated as one epoch; epoch_id = file stem.

    Args:
        dat_files: Paths to turboSETI .dat files (one per epoch).
        freq_tolerance_hz: Frequency grouping tolerance in Hz.

    Returns:
        MultiEpochResult with grouped hits and per-group persistence scores.
    """
    from techno_search.radio.hit_table_reader import read_hit_table_csv

    all_hits: list[MultiEpochHit] = []
    failed_epoch_ids: list[str] = []

    for dat_file in dat_files:
        epoch_id = dat_file.stem
        try:
            rows = read_hit_table_csv(dat_file)
            for r in rows:
                freq_hz = float(r.get("frequency_hz") or 0.0)
                freq_mhz = freq_hz / 1e6
                hit = MultiEpochHit(
                    frequency_mhz=freq_mhz,
                    snr=float(r.get("snr") or 0.0),
                    drift_rate_hz_s=float(r.get("drift_rate_hz_per_sec") or 0.0),
                    epoch_id=epoch_id,
                    mjd=r.get("mjd"),
                    scan_role=str(r.get("scan_role") or "unknown"),
                )
                all_hits.append(hit)
        except Exception:  # noqa: BLE001
            # This epoch's hit table could not be read or parsed -- it was
            # NOT actually checked, so it must not silently count toward
            # total_epochs_checked (that would understate persistence_score
            # for a real recurring signal without any visible sign the
            # epoch was skipped). Surfaced explicitly in the result instead
            # of being dropped, per AGENTS.md's FAIL LOUDLY directive.
            failed_epoch_ids.append(epoch_id)

    total_epochs = len(dat_files) - len(failed_epoch_ids)
    freq_tolerance_mhz = freq_tolerance_hz / 1e6
    groups: list[MultiEpochGroup] = []

    for hit in all_hits:
        matched = False
        for grp in groups:
            if abs(hit.frequency_mhz - grp.frequency_mhz) <= freq_tolerance_mhz:
                grp.hits.append(hit)
                grp.epoch_ids.append(hit.epoch_id)
                matched = True
                break
        if not matched:
            groups.append(
                MultiEpochGroup(
                    frequency_mhz=hit.frequency_mhz,
                    tolerance_hz=freq_tolerance_hz,
                    total_epochs_checked=total_epochs,
                    hits=[hit],
                    epoch_ids=[hit.epoch_id],
                )
            )

    return MultiEpochResult(
        epoch_count=total_epochs,
        total_hits=len(all_hits),
        groups=groups,
        failed_epoch_ids=failed_epoch_ids,
    )


def multi_epoch_summary(
    dat_files: list[Path],
    *,
    freq_tolerance_hz: float = 1000.0,
) -> dict[str, Any]:
    """Return a compact summary dict of multi-epoch comparison."""
    result = compare_epochs(dat_files, freq_tolerance_hz=freq_tolerance_hz)
    return result.as_dict()
