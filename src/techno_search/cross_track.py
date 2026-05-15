"""Cross-track candidate cross-reference loader and summary helper.

Cross-track references are operational cross-reference metadata only. They
identify candidate IDs that share the same target across more than one search
track (radio, infrared, archival anomaly). They never modify posteriors,
false-positive probability, or the recommended pathway. Each entry must
preserve the false-positive evidence and blocking issues from each
contributing track.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

CROSS_TRACK_REFERENCE_SCHEMA_VERSION = "cross_track_references_v1"
CROSS_TRACK_REFERENCE_DISCLAIMER = (
    "Cross-track references are operational cross-reference metadata only. "
    "They do not modify candidate posteriors, false-positive probability, or "
    "pathway routing, and they are not detections, discoveries, or external "
    "validation."
)


@dataclass(frozen=True)
class CrossTrackReference:
    """A single cross-track candidate cross-reference record."""

    reference_id: str
    target_id: str
    contributing_tracks: tuple[str, ...]
    candidate_packet_ids: tuple[str, ...]
    recommended_pathway: str
    blocking_issues: tuple[str, ...] = field(default_factory=tuple)
    negative_evidence: tuple[str, ...] = field(default_factory=tuple)
    cross_reference_kind: str = "operational_cross_reference"
    notes: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "reference_id": self.reference_id,
            "target_id": self.target_id,
            "contributing_tracks": list(self.contributing_tracks),
            "candidate_packet_ids": list(self.candidate_packet_ids),
            "recommended_pathway": self.recommended_pathway,
            "blocking_issues": list(self.blocking_issues),
            "negative_evidence": list(self.negative_evidence),
            "cross_reference_kind": self.cross_reference_kind,
            "notes": self.notes,
        }


def default_cross_track_reference_path() -> Path:
    """Return the committed cross-track reference fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "cross_track_references.json"
    )


def load_cross_track_references(
    path: Path | None = None,
) -> tuple[CrossTrackReference, ...]:
    """Load and validate the cross-track reference fixture."""

    fixture_path = path or default_cross_track_reference_path()
    with Path(fixture_path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    schema_version = str(data.get("schema_version", ""))
    if schema_version != CROSS_TRACK_REFERENCE_SCHEMA_VERSION:
        msg = (
            f"Unsupported cross-track reference schema version "
            f"{schema_version!r}; expected "
            f"{CROSS_TRACK_REFERENCE_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)
    references = []
    for raw in data.get("references", []):
        references.append(
            CrossTrackReference(
                reference_id=str(raw["reference_id"]),
                target_id=str(raw["target_id"]),
                contributing_tracks=tuple(str(track) for track in raw["contributing_tracks"]),
                candidate_packet_ids=tuple(
                    str(packet_id) for packet_id in raw.get("candidate_packet_ids", [])
                ),
                recommended_pathway=str(raw["recommended_pathway"]),
                blocking_issues=tuple(str(issue) for issue in raw.get("blocking_issues", [])),
                negative_evidence=tuple(
                    str(item) for item in raw.get("negative_evidence", [])
                ),
                cross_reference_kind=str(
                    raw.get("cross_reference_kind", "operational_cross_reference")
                ),
                notes=str(raw.get("notes", "")),
            )
        )
    return tuple(references)


def cross_track_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize cross-track candidate cross-reference fixture coverage."""

    references = load_cross_track_references(path)
    blocking_issue_total = sum(len(ref.blocking_issues) for ref in references)
    negative_evidence_total = sum(len(ref.negative_evidence) for ref in references)
    track_combinations = Counter(
        " + ".join(sorted(set(ref.contributing_tracks))) for ref in references
    )
    by_pathway = Counter(ref.recommended_pathway for ref in references)
    by_kind = Counter(ref.cross_reference_kind for ref in references)
    multi_track_count = sum(
        1 for ref in references if len(set(ref.contributing_tracks)) >= 2
    )
    return {
        "schema_version": CROSS_TRACK_REFERENCE_SCHEMA_VERSION,
        "disclaimer": CROSS_TRACK_REFERENCE_DISCLAIMER,
        "reference_count": len(references),
        "multi_track_reference_count": multi_track_count,
        "blocking_issue_total": blocking_issue_total,
        "negative_evidence_total": negative_evidence_total,
        "by_track_combination": dict(sorted(track_combinations.items())),
        "by_recommended_pathway": dict(sorted(by_pathway.items())),
        "by_cross_reference_kind": dict(sorted(by_kind.items())),
        "reference_ids": sorted(ref.reference_id for ref in references),
        "target_ids": sorted({ref.target_id for ref in references}),
        "uncertainty_and_limitations": [
            "Cross-references are operational metadata only.",
            "They never modify posteriors, scores, or pathway routing.",
            "Each contributing track preserves its own evidence independently.",
        ],
    }
