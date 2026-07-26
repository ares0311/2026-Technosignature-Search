"""Shared real-known-target-ID alias matching.

Resolves a raw observation/target-history string back to a real target_id by
matching against the caller's own known-ID set, instead of a hardcoded
pattern for one naming scheme (e.g. HIP-only) -- a live discovery expansion
surfaced real TIC-named (TESS) queue rows a HIP-only pattern could never
match, and a real cross-project history export uses TIC/KIC/EPIC IDs this
project doesn't natively catalog. Used by both ``target_priority_queue.py``
(scan-history novelty scoring) and ``hunter_cross_project_history.py``
(cross-project search-history export), kept here to avoid a circular import
between them.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class TargetAliasResolver:
    """Resolve observation text against one precompiled real-target index."""

    canonical_by_casefold: dict[str, str]
    pattern: re.Pattern[str] | None

    @classmethod
    def build(cls, known_target_ids: Iterable[str]) -> TargetAliasResolver:
        canonical_by_casefold: dict[str, str] = {}
        for target_id in known_target_ids:
            canonical = str(target_id).strip()
            if not canonical:
                continue
            key = canonical.casefold()
            previous = canonical_by_casefold.get(key)
            if previous is not None and previous != canonical:
                raise ValueError(
                    "target IDs are ambiguous under case-insensitive matching: "
                    f"{previous!r} and {canonical!r}"
                )
            canonical_by_casefold[key] = canonical
        ids = sorted(canonical_by_casefold.values(), key=len, reverse=True)
        pattern = (
            re.compile(
                r"(?<![0-9A-Za-z])("
                + "|".join(re.escape(target_id) for target_id in ids)
                + r")(?![0-9A-Za-z])",
                re.IGNORECASE,
            )
            if ids
            else None
        )
        return cls(canonical_by_casefold=canonical_by_casefold, pattern=pattern)

    def resolve(self, value: str) -> str | None:
        if self.pattern is None:
            return None
        match = self.pattern.search(value)
        if match is None:
            return None
        return self.canonical_by_casefold[match.group(1).casefold()]


def known_target_alias_pattern(known_target_ids: Iterable[str]) -> re.Pattern[str] | None:
    """Compile one alternation regex over every real known target ID.

    A single compiled pattern keeps matching O(text length) instead of
    O(known IDs x text length). IDs are escaped, sorted longest-first, and
    boundary-anchored so a short ID cannot spuriously match inside a longer
    one (e.g. "HIP1" inside "HIP12345").

    New production callers should retain a :class:`TargetAliasResolver`
    rather than rebuilding this compatibility pattern for each row.
    """
    return TargetAliasResolver.build(known_target_ids).pattern
