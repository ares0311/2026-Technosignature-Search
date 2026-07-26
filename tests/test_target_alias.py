from __future__ import annotations

import pytest

from techno_search.target_alias import TargetAliasResolver


def test_alias_resolver_is_boundary_safe_and_prefers_longest_real_id() -> None:
    resolver = TargetAliasResolver.build(("HIP1", "HIP123", "TIC281731203"))

    assert resolver.resolve("capture_HIP123_0001") == "HIP123"
    assert resolver.resolve("capture_TIC281731203_0001") == "TIC281731203"
    assert resolver.resolve("capture_XHIP123Y_0001") is None


def test_alias_resolver_fails_closed_on_casefold_ambiguity() -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        TargetAliasResolver.build(("Tic123", "TIC123"))
