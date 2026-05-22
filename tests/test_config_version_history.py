from __future__ import annotations

from techno_search.config_version_history import (
    ALLOWED_CHANGE_KINDS,
    CONFIG_VERSION_HISTORY_DISCLAIMER,
    CONFIG_VERSION_HISTORY_SCHEMA_VERSION,
    ConfigVersionHistoryEntry,
    config_version_history_summary,
    load_config_history_entries,
)


def test_schema_version() -> None:
    assert CONFIG_VERSION_HISTORY_SCHEMA_VERSION == "config_version_history_v1"


def test_disclaimer_append_only() -> None:
    assert "append-only" in CONFIG_VERSION_HISTORY_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in CONFIG_VERSION_HISTORY_DISCLAIMER


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in CONFIG_VERSION_HISTORY_DISCLAIMER


def test_disclaimer_no_re_route() -> None:
    assert "re-run or re-route" in CONFIG_VERSION_HISTORY_DISCLAIMER


def test_allowed_change_kinds() -> None:
    assert "created" in ALLOWED_CHANGE_KINDS
    assert "promoted" in ALLOWED_CHANGE_KINDS
    assert "updated" in ALLOWED_CHANGE_KINDS
    assert "deprecated" in ALLOWED_CHANGE_KINDS


def test_load_entries_count() -> None:
    entries = load_config_history_entries()
    assert len(entries) == 4


def test_load_entries_types() -> None:
    entries = load_config_history_entries()
    for e in entries:
        assert isinstance(e, ConfigVersionHistoryEntry)


def test_first_entry_fields() -> None:
    entries = load_config_history_entries()
    e = entries[0]
    assert e.history_id == "cfg-hist-001"
    assert e.config_id == "pcfg-001"
    assert e.change_kind == "created"
    assert e.changed_by == "operator-alpha"
    assert e.prior_config_id is None


def test_promoted_entry_present() -> None:
    entries = load_config_history_entries()
    promoted = [e for e in entries if e.change_kind == "promoted"]
    assert len(promoted) == 1
    assert promoted[0].history_id == "cfg-hist-002"


def test_deprecated_entry_present() -> None:
    entries = load_config_history_entries()
    deprecated = [e for e in entries if e.change_kind == "deprecated"]
    assert len(deprecated) == 1
    assert deprecated[0].history_id == "cfg-hist-004"


def test_prior_config_id_populated() -> None:
    entries = load_config_history_entries()
    with_prior = [e for e in entries if e.prior_config_id is not None]
    assert len(with_prior) >= 1
    assert with_prior[0].prior_config_id == "pcfg-001"


def test_as_dict_keys() -> None:
    entries = load_config_history_entries()
    d = entries[0].as_dict()
    expected = {
        "history_id", "config_id", "change_kind",
        "effective_utc", "changed_by", "prior_config_id", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_config_history_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["history_id"] == e.history_id
    assert d["config_id"] == e.config_id
    assert d["prior_config_id"] == e.prior_config_id


def test_summary_entry_count() -> None:
    s = config_version_history_summary()
    assert s["entry_count"] == 4


def test_summary_deprecated_count() -> None:
    s = config_version_history_summary()
    assert s["deprecated_count"] == 1


def test_summary_promoted_count() -> None:
    s = config_version_history_summary()
    assert s["promoted_count"] == 1


def test_summary_by_kind() -> None:
    s = config_version_history_summary()
    bk = s["by_kind"]
    assert bk.get("created", 0) == 2
    assert bk.get("promoted", 0) == 1
    assert bk.get("deprecated", 0) == 1


def test_summary_configs_tracked() -> None:
    s = config_version_history_summary()
    ct = s["configs_tracked"]
    assert "pcfg-001" in ct
    assert "pcfg-002" in ct
    assert "pcfg-003" in ct


def test_summary_schema_version() -> None:
    s = config_version_history_summary()
    assert s["schema_version"] == CONFIG_VERSION_HISTORY_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = config_version_history_summary()
    assert "disclaimer" in s
    assert "detection claim" in s["disclaimer"]
