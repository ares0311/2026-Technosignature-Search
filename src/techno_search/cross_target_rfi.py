"""Cross-target RFI filter: flag signals at same frequency across targets."""

from __future__ import annotations

from typing import Any

CROSS_TARGET_RFI_DISCLAIMER = (
    "Cross-target frequency matches are flagged as likely RFI. "
    "This does not confirm absence of a real signal at the matched frequency."
)

CROSS_TARGET_RFI_SCHEMA_VERSION = "cross_target_rfi_v1"


def flag_cross_target_rfi(
    candidate_lists: list[list[dict[str, Any]]],
    freq_tolerance_hz: float = 500.0,
) -> dict[str, dict[str, Any]]:
    """Flag candidates whose frequency appears in >=2 independent targets.

    Args:
        candidate_lists: List of lists of candidate dicts. Each dict must
            have ``frequency_hz``, ``candidate_id``, and ``target_name``.
        freq_tolerance_hz: Frequency window (Hz) within which two signals
            are considered the same frequency. Default 500 Hz.

    Returns:
        Dict mapping candidate_id → flag info for flagged candidates.
        Candidates from only one target are never flagged.
    """
    # Flatten scored signal candidates, preserving their source.  Zero-frequency
    # observation-only records are negative evidence, not RFI-bearing hits.
    flat: list[dict[str, Any]] = []
    for clist in candidate_lists:
        for cand in clist:
            if bool(cand.get("observation_only")):
                continue
            if float(cand.get("frequency_hz", 0.0) or 0.0) <= 0.0:
                continue
            flat.append(cand)

    if not flat:
        return {}

    # Sort by frequency for efficient grouping
    sorted_cands = sorted(flat, key=lambda c: float(c.get("frequency_hz", 0.0)))

    # Group candidates within freq_tolerance_hz of each other
    groups: list[list[dict[str, Any]]] = []
    current_group: list[dict[str, Any]] = [sorted_cands[0]]

    for cand in sorted_cands[1:]:
        # Use the first element of the current group as the reference
        ref_freq = float(current_group[0].get("frequency_hz", 0.0))
        cand_freq = float(cand.get("frequency_hz", 0.0))
        if abs(cand_freq - ref_freq) <= freq_tolerance_hz:
            current_group.append(cand)
        else:
            groups.append(current_group)
            current_group = [cand]

    groups.append(current_group)

    flagged: dict[str, dict[str, Any]] = {}

    for group in groups:
        # Collect unique target names in this group
        unique_targets = {str(c.get("target_name", "")) for c in group}
        if len(unique_targets) >= 2:
            matched_freqs = sorted(
                {float(c.get("frequency_hz", 0.0)) for c in group}
            )
            matched_candidate_ids = sorted(str(c.get("candidate_id", "")) for c in group)
            for cand in group:
                cid = str(cand.get("candidate_id", ""))
                flagged[cid] = {
                    "flagged": True,
                    "reason": "cross_target_rfi",
                    "match_count": len(unique_targets),
                    "matched_frequencies": matched_freqs,
                    "matched_target_names": sorted(unique_targets),
                    "matched_candidate_ids": matched_candidate_ids,
                    "frequency_tolerance_hz": float(freq_tolerance_hz),
                }

    return flagged


def cross_target_rfi_summary(
    candidate_lists: list[list[dict[str, Any]]],
    freq_tolerance_hz: float = 500.0,
) -> dict[str, Any]:
    """Return a summary of cross-target RFI flagging.

    Args:
        candidate_lists: List of lists of candidate dicts.
        freq_tolerance_hz: Frequency tolerance in Hz. Default 500.

    Returns:
        Summary dict with flagged_count, total_candidates, flag_rate,
        disclaimer, and schema_version.
    """
    total = sum(len(cl) for cl in candidate_lists)
    flagged = flag_cross_target_rfi(candidate_lists, freq_tolerance_hz)
    flagged_count = len(flagged)
    flag_rate = flagged_count / total if total > 0 else 0.0

    return {
        "schema_version": CROSS_TARGET_RFI_SCHEMA_VERSION,
        "disclaimer": CROSS_TARGET_RFI_DISCLAIMER,
        "total_candidates": total,
        "flagged_count": flagged_count,
        "flag_rate": round(flag_rate, 4),
    }
