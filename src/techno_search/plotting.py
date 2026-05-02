"""Dependency-free synthetic diagnostic plot artifact helpers."""

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
    "Synthetic illustrative diagnostic for review context only; not evidence of a "
    "confirmed technosignature."
)


@dataclass(frozen=True)
class PlotArtifact:
    """A generated report plot artifact."""

    path: Path
    kind: str
    track: str
    media_type: str
    description: str
    synthetic: bool = True

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


def write_synthetic_plot_artifacts(
    scored: ScoredCandidate,
    output_dir: Path | str,
    *,
    filename_prefix: str,
) -> tuple[PlotArtifact, ...]:
    """Write lightweight SVG diagnostics for the candidate track."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    track = scored.candidate.track
    if track == Track.RADIO:
        path = destination / f"{filename_prefix}-radio-waterfall.svg"
        path.write_text(_radio_waterfall_svg(scored), encoding="utf-8")
        return (
            PlotArtifact(
                path=path,
                kind="synthetic_radio_waterfall",
                track=track.value,
                media_type="image/svg+xml",
                description="Synthetic radio waterfall-style diagnostic placeholder.",
            ),
        )
    if track == Track.INFRARED:
        path = destination / f"{filename_prefix}-infrared-sed.svg"
        path.write_text(_infrared_sed_svg(scored), encoding="utf-8")
        return (
            PlotArtifact(
                path=path,
                kind="synthetic_infrared_sed",
                track=track.value,
                media_type="image/svg+xml",
                description="Synthetic infrared SED-style diagnostic placeholder.",
            ),
        )
    if track == Track.ANOMALY:
        path = destination / f"{filename_prefix}-anomaly-crossmatch.svg"
        path.write_text(_anomaly_crossmatch_svg(scored), encoding="utf-8")
        return (
            PlotArtifact(
                path=path,
                kind="synthetic_anomaly_crossmatch",
                track=track.value,
                media_type="image/svg+xml",
                description="Synthetic archival crossmatch diagnostic placeholder.",
            ),
        )
    return ()


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


def _radio_waterfall_svg(scored: ScoredCandidate) -> str:
    features = scored.candidate.features
    snr = _float_feature(features, "snr", 12.0)
    drift = _float_feature(features, "drift_rate_hz_per_sec", 0.0)
    intensity = min(max(snr / 50.0, 0.12), 1.0)
    line_end = 260 + max(min(drift * 18.0, 80.0), -80.0)
    return _svg(
        title="Synthetic Radio Waterfall Diagnostic",
        body=f"""
  <rect x="40" y="52" width="320" height="180" fill="#101820"/>
  {_waterfall_rows(intensity)}
  <line x1="120" y1="210" x2="{line_end:.1f}" y2="76" stroke="#f6c85f" stroke-width="5"/>
  <text x="48" y="258" class="small">SNR proxy: {snr:.2f}</text>
  <text x="210" y="258" class="small">Drift proxy: {drift:.2f} Hz/s</text>
""",
    )


def _infrared_sed_svg(scored: ScoredCandidate) -> str:
    features = scored.candidate.features
    excess = _float_feature(features, "ir_excess_significance", 1.0)
    confusion = _float_feature(features, "source_confusion_score", 0.0)
    points = (
        (70, 204 - min(excess * 8.0, 90.0)),
        (130, 172 - min(excess * 5.0, 70.0)),
        (190, 145 - min(excess * 2.0, 45.0)),
        (250, 118 - min(excess * 4.0, 65.0)),
        (310, 94 - min(excess * 6.0, 85.0)),
    )
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    markers = "\n  ".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#3b82f6"/>' for x, y in points
    )
    return _svg(
        title="Synthetic Infrared SED Diagnostic",
        body=f"""
  <line x1="48" y1="228" x2="352" y2="228" stroke="#334155" stroke-width="2"/>
  <line x1="48" y1="44" x2="48" y2="228" stroke="#334155" stroke-width="2"/>
  <polyline points="{polyline}" fill="none" stroke="#3b82f6" stroke-width="4"/>
  {markers}
  <text x="58" y="258" class="small">IR excess proxy: {excess:.2f}</text>
  <text x="220" y="258" class="small">Confusion proxy: {confusion:.2f}</text>
""",
    )


def _anomaly_crossmatch_svg(scored: ScoredCandidate) -> str:
    features = scored.candidate.features
    confidence = _float_feature(features, "crossmatch_confidence", 0.5)
    artifact = _float_feature(features, "artifact_score", 0.2)
    offset = max(min((1.0 - confidence) * 90.0, 90.0), 8.0)
    modern_x = 150 + offset
    modern_y = 132 - offset / 3
    return _svg(
        title="Synthetic Archival Crossmatch Diagnostic",
        body=f"""
  <circle cx="150" cy="132" r="42" fill="none" stroke="#64748b" stroke-width="3"/>
  <circle cx="{modern_x:.1f}" cy="{modern_y:.1f}" r="28" fill="none"
    stroke="#14b8a6" stroke-width="4"/>
  <line x1="150" y1="132" x2="{modern_x:.1f}" y2="{modern_y:.1f}"
    stroke="#f97316" stroke-dasharray="5 5" stroke-width="3"/>
  <text x="72" y="222" class="small">Historical source</text>
  <text x="220" y="222" class="small">Modern match</text>
  <text x="58" y="258" class="small">Crossmatch confidence: {confidence:.2f}</text>
  <text x="250" y="258" class="small">Artifact proxy: {artifact:.2f}</text>
""",
    )


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
    .note {{ font: 11px sans-serif; fill: #475569; }}
  </style>
  <rect x="0" y="0" width="400" height="300" fill="#f8fafc"/>
  <text x="24" y="28" class="title">{escaped_title}</text>
{body}
  <text x="24" y="284" class="note">{escaped_disclaimer}</text>
</svg>
"""


def _waterfall_rows(intensity: float) -> str:
    rows = []
    for index in range(9):
        shade = int(35 + 120 * intensity + index * 4)
        rows.append(
            f'<rect x="48" y="{62 + index * 18}" width="304" height="10" '
            f'fill="rgb(20,{shade},180)" opacity="0.72"/>'
        )
    return "\n  ".join(rows)


def _artifact_entries(manifest: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    artifacts = manifest.get("plot_artifacts", [])
    if not isinstance(artifacts, list):
        return ()
    return tuple(artifact for artifact in artifacts if isinstance(artifact, Mapping))


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _float_feature(features: Mapping[str, Any], key: str, default: float) -> float:
    value = features.get(key, default)
    if isinstance(value, int | float):
        return float(value)
    return default
