"""Dependency-free candidate evidence visualization helpers."""

from __future__ import annotations

import html
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.schemas import ScoredCandidate, Track

PLOT_ARTIFACT_DISCLAIMER = (
    "Deterministic rendering of persisted candidate feature values for review context "
    "only; not evidence of a confirmed technosignature."
)

_FEATURE_KEYS_BY_TRACK = {
    Track.RADIO: (
        "snr",
        "drift_rate_hz_per_sec",
        "normalized_drift_hz_s_per_ghz",
        "abacab_cadence_score",
        "on_off_consistency_score",
        "rfi_band_overlap_score",
        "instrumental_artifact_score",
        "frequency_persistence_score",
        "semisupervised_anomaly_score",
    ),
    Track.INFRARED: (
        "ir_excess_significance",
        "source_confusion_score",
        "agn_color_score",
        "data_quality_score",
        "metadata_completeness_score",
        "provenance_completeness_score",
    ),
    Track.ANOMALY: (
        "crossmatch_confidence",
        "artifact_score",
        "data_quality_score",
        "metadata_completeness_score",
        "provenance_completeness_score",
    ),
}

_ARTIFACT_CONFIG_BY_TRACK = {
    Track.RADIO: (
        "radio-feature-summary",
        "radio_scored_feature_summary",
        "Radio Scored Feature Summary",
        "Persisted radio candidate feature summary.",
    ),
    Track.INFRARED: (
        "infrared-feature-summary",
        "infrared_scored_feature_summary",
        "Infrared Scored Feature Summary",
        "Persisted infrared candidate feature summary.",
    ),
    Track.ANOMALY: (
        "anomaly-feature-summary",
        "anomaly_scored_feature_summary",
        "Anomaly Scored Feature Summary",
        "Persisted anomaly candidate feature summary.",
    ),
}


@dataclass(frozen=True)
class PlotArtifact:
    """A generated report plot artifact."""

    path: Path
    kind: str
    track: str
    media_type: str
    description: str
    synthetic: bool = False

    def as_manifest_entry(self) -> dict[str, object]:
        """Return a JSON-serializable manifest entry."""

        return {
            "path": str(self.path),
            "kind": self.kind,
            "track": self.track,
            "media_type": self.media_type,
            "description": self.description,
            "synthetic": self.synthetic,
            "disclaimer": PLOT_ARTIFACT_DISCLAIMER,
        }


def write_evidence_plot_artifacts(
    scored: ScoredCandidate,
    output_dir: Path | str,
    *,
    filename_prefix: str,
) -> tuple[PlotArtifact, ...]:
    """Write an SVG summary using only persisted numeric candidate features."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    track = scored.candidate.track
    artifact_config = _ARTIFACT_CONFIG_BY_TRACK.get(track)
    feature_rows = _persisted_feature_rows(scored)
    if artifact_config is None or not feature_rows:
        return ()
    suffix, kind, title, description = artifact_config
    path = destination / f"{filename_prefix}-{suffix}.svg"
    path.write_text(_feature_summary_svg(title, feature_rows), encoding="utf-8")
    return (
        PlotArtifact(
            path=path,
            kind=kind,
            track=track.value,
            media_type="image/svg+xml",
            description=description,
        ),
    )


def plot_artifact_summary(report_dir: Path | str) -> dict[str, object]:
    """Summarize plot artifact manifest entries in a generated report directory."""

    directory = Path(report_dir)
    manifest_paths = sorted(directory.glob("*.manifest.json"))
    artifacts: list[dict[str, object]] = []
    missing_paths: list[str] = []
    for manifest_path in manifest_paths:
        with manifest_path.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        if not isinstance(manifest, dict):
            continue
        candidate_id = str(manifest.get("candidate_id", manifest_path.stem))
        for artifact in _artifact_entries(manifest):
            path = Path(str(artifact.get("path", "")))
            artifacts.append(
                {
                    "candidate_id": candidate_id,
                    "path": str(path),
                    "kind": str(artifact.get("kind", "unknown")),
                    "track": str(artifact.get("track", "unknown")),
                    "media_type": str(artifact.get("media_type", "unknown")),
                    "synthetic": bool(artifact.get("synthetic", False)),
                }
            )
            if not path.exists():
                missing_paths.append(str(path))

    return {
        "report_dir": str(directory),
        "manifest_count": len(manifest_paths),
        "plot_artifact_count": len(artifacts),
        "by_track": _counter_to_dict(Counter(str(artifact["track"]) for artifact in artifacts)),
        "by_kind": _counter_to_dict(Counter(str(artifact["kind"]) for artifact in artifacts)),
        "media_types": sorted({str(artifact["media_type"]) for artifact in artifacts}),
        "synthetic_count": sum(1 for artifact in artifacts if artifact["synthetic"]),
        "missing_path_count": len(missing_paths),
        "missing_paths": sorted(missing_paths),
        "artifacts": artifacts,
    }


def _persisted_feature_rows(scored: ScoredCandidate) -> tuple[tuple[str, float], ...]:
    features = scored.candidate.features
    preferred_keys = _FEATURE_KEYS_BY_TRACK.get(scored.candidate.track, ())
    rows: list[tuple[str, float]] = []
    for key in preferred_keys:
        value = features.get(key)
        if isinstance(value, bool) or not isinstance(value, int | float):
            continue
        rows.append((key, float(value)))
    return tuple(rows[:7])


def _feature_summary_svg(title: str, rows: tuple[tuple[str, float], ...]) -> str:
    body_rows: list[str] = []
    for index, (key, value) in enumerate(rows):
        y = 66 + index * 27
        fill = "#e2e8f0" if index % 2 == 0 else "#f1f5f9"
        body_rows.extend(
            (
                f'  <rect x="30" y="{y - 18}" width="340" height="25" fill="{fill}"/>',
                (
                    f'  <text x="42" y="{y}" class="small">'
                    f"{html.escape(key)}</text>"
                ),
                (
                    f'  <text x="350" y="{y}" text-anchor="end" class="value">'
                    f"{html.escape(format(value, '.8g'))}</text>"
                ),
            )
        )
    return _svg(title=title, body="\n".join(body_rows))


def _svg(*, title: str, body: str) -> str:
    escaped_title = html.escape(title)
    escaped_disclaimer = html.escape(PLOT_ARTIFACT_DISCLAIMER)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"
  viewBox="0 0 400 300" role="img" aria-labelledby="title desc">
  <title id="title">{escaped_title}</title>
  <desc id="desc">{escaped_disclaimer}</desc>
  <style>
    .title {{ font: 700 17px sans-serif; fill: #0f172a; }}
    .small {{ font: 12px sans-serif; fill: #334155; }}
    .value {{ font: 600 12px monospace; fill: #0f172a; }}
    .note {{ font: 11px sans-serif; fill: #475569; }}
  </style>
  <rect x="0" y="0" width="400" height="300" fill="#f8fafc"/>
  <text x="24" y="28" class="title">{escaped_title}</text>
{body}
  <text x="24" y="284" class="note">{escaped_disclaimer}</text>
</svg>
"""
def _artifact_entries(manifest: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    artifacts = manifest.get("plot_artifacts", [])
    if not isinstance(artifacts, list):
        return ()
    return tuple(artifact for artifact in artifacts if isinstance(artifact, Mapping))


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
