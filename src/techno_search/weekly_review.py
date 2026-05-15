"""Operator weekly review template assembler."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

WEEKLY_REVIEW_SCHEMA_VERSION = "weekly_review_v1"

WEEKLY_REVIEW_DISCLAIMER = (
    "This weekly review template is an operational scheduling summary only. "
    "It is not a discovery claim, not an external submission, and not a "
    "confirmation of any technosignature candidate. All candidate signals "
    "remain unconfirmed and require external, independent validation before "
    "any claim can be made."
)


@dataclass
class WeeklyReviewTemplate:
    schema_version: str
    disclaimer: str
    generated_at_utc: str
    window_days: int
    digest: dict[str, Any]
    cross_track_summary: dict[str, Any]
    network_access_confirmed_zero: bool
    external_submission_confirmed_zero: bool
    recommended_next_actions: list[str]
    operator_notes: str = ""
    sections: dict[str, Any] = field(default_factory=dict)
    watchlist_elevated_count: int = 0
    watchlist_blocked_count: int = 0
    watchlist_prioritized_targets: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "disclaimer": self.disclaimer,
            "generated_at_utc": self.generated_at_utc,
            "window_days": self.window_days,
            "network_access_confirmed_zero": self.network_access_confirmed_zero,
            "external_submission_confirmed_zero": self.external_submission_confirmed_zero,
            "watchlist_elevated_count": self.watchlist_elevated_count,
            "watchlist_blocked_count": self.watchlist_blocked_count,
            "watchlist_prioritized_targets": self.watchlist_prioritized_targets,
            "digest": self.digest,
            "cross_track_summary": self.cross_track_summary,
            "recommended_next_actions": self.recommended_next_actions,
            "operator_notes": self.operator_notes,
            "sections": self.sections,
        }

    def as_markdown(self) -> str:
        lines: list[str] = []
        lines.append("# Weekly Review Template")
        lines.append("")
        lines.append(f"**Generated:** {self.generated_at_utc}")
        lines.append(f"**Window:** {self.window_days} days")
        lines.append("")
        lines.append(f"> {self.disclaimer}")
        lines.append("")

        lines.append("## Gate Confirmations")
        lines.append("")
        _ok = "✓ confirmed zero"
        _nok = "⚠ NON-ZERO — investigate"
        net_ok = _ok if self.network_access_confirmed_zero else _nok
        sub_ok = _ok if self.external_submission_confirmed_zero else _nok
        lines.append(f"- Network access allowed count: {net_ok}")
        lines.append(f"- External submission approved count: {sub_ok}")
        lines.append("")

        lines.append("## Run Summary")
        lines.append("")
        digest = self.digest
        lines.append(f"- Total runs: {digest.get('run_count', 0)}")
        lines.append(f"- Reviewed outcomes: {digest.get('reviewed_count', 0)}")
        lines.append(f"- Needs-follow-up outcomes: {digest.get('needs_follow_up_count', 0)}")
        lines.append(f"- Blocking issues: {digest.get('blocking_issue_total', 0)}")
        lines.append(f"- Window start: {digest.get('window_start_utc', 'N/A')}")
        lines.append("")

        lines.append("## Watchlist Status")
        lines.append("")
        lines.append(f"- Elevated targets: {self.watchlist_elevated_count}")
        lines.append(f"- Blocked targets: {self.watchlist_blocked_count}")
        if self.watchlist_prioritized_targets:
            lines.append(
                f"- Priority order: {', '.join(self.watchlist_prioritized_targets)}"
            )
        lines.append("")

        lines.append("## Cross-Track References")
        lines.append("")
        ct = self.cross_track_summary
        lines.append(f"- Total references: {ct.get('reference_count', 0)}")
        lines.append(f"- Multi-track references: {ct.get('multi_track_reference_count', 0)}")
        lines.append(f"- Blocking issues across tracks: {ct.get('blocking_issue_total', 0)}")
        lines.append("")

        lines.append("## Recommended Next Actions")
        lines.append("")
        for action in self.recommended_next_actions:
            lines.append(f"- {action}")
        lines.append("")

        if self.operator_notes:
            lines.append("## Operator Notes")
            lines.append("")
            lines.append(self.operator_notes)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(
            "*This template is for local operational review only. "
            "Do not treat any item above as a confirmed detection.*"
        )
        lines.append("")
        return "\n".join(lines)


def _default_next_actions(
    digest: dict[str, Any],
    ct_summary: dict[str, Any],
    watchlist_elevated_count: int = 0,
) -> list[str]:
    actions: list[str] = []
    if digest.get("needs_follow_up_count", 0) > 0:
        actions.append(
            f"Review {digest['needs_follow_up_count']} needs-follow-up outcome(s) "
            "and decide whether to schedule follow-up observations."
        )
    if ct_summary.get("blocking_issue_total", 0) > 0:
        actions.append(
            f"Investigate {ct_summary['blocking_issue_total']} blocking issue(s) "
            "in cross-track references before considering any submission."
        )
    if digest.get("blocking_issue_total", 0) > 0:
        actions.append(
            f"Resolve {digest['blocking_issue_total']} blocking issue(s) "
            "recorded in background run outcomes."
        )
    if watchlist_elevated_count > 0:
        actions.append(
            f"Review {watchlist_elevated_count} elevated watchlist target(s) "
            "before the next observation cycle."
        )
    if not actions:
        actions.append(
            "No immediate follow-up actions required. Continue scheduled background runs."
        )
    actions.append(
        "Run `techno-search validate-all` to confirm local health before the next run cycle."
    )
    return actions


def build_weekly_review_template(
    digest: dict[str, Any],
    ct_summary: dict[str, Any],
    window_days: int = 7,
    operator_notes: str = "",
    generated_at_utc: str | None = None,
    watchlist_summary: dict[str, Any] | None = None,
) -> WeeklyReviewTemplate:
    if generated_at_utc is None:
        generated_at_utc = datetime.now(UTC).isoformat()

    net_zero = digest.get("network_access_allowed_count", 0) == 0
    sub_zero = digest.get("external_submission_approved_count", 0) == 0
    wl = watchlist_summary or {}
    elevated = int(wl.get("elevated_count", 0))
    blocked = int(wl.get("blocked_count", 0))
    prioritized = list(wl.get("prioritized_target_ids", []))

    return WeeklyReviewTemplate(
        schema_version=WEEKLY_REVIEW_SCHEMA_VERSION,
        disclaimer=WEEKLY_REVIEW_DISCLAIMER,
        generated_at_utc=generated_at_utc,
        window_days=window_days,
        digest=digest,
        cross_track_summary=ct_summary,
        network_access_confirmed_zero=net_zero,
        external_submission_confirmed_zero=sub_zero,
        recommended_next_actions=_default_next_actions(digest, ct_summary, elevated),
        operator_notes=operator_notes,
        watchlist_elevated_count=elevated,
        watchlist_blocked_count=blocked,
        watchlist_prioritized_targets=prioritized,
    )


def write_weekly_review_template(
    template: WeeklyReviewTemplate,
    output_dir: Path,
    filename_stem: str | None = None,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = filename_stem or f"weekly_review_{template.generated_at_utc[:10]}"
    md_path = output_dir / f"{stem}.md"
    json_path = output_dir / f"{stem}.json"
    md_path.write_text(template.as_markdown(), encoding="utf-8")
    json_path.write_text(
        json.dumps(template.as_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return md_path, json_path
