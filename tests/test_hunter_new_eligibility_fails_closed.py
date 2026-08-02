"""IDENT-03 regression: New eligibility must fail closed on weak history.

Observed field failure: a real ``Create-New-Search --targets 5 --mode new`` run
froze five targets and recorded ``prior_search_count=0`` with a selection reason
asserting each target was "not previously searched", while
``data_selection/hunter_prior_search_history_v1.json`` did not exist and the
selection path never consulted cross-project history at all.

That is the TechnoHunter analogue of the EXO-FIELD-01 blocker. These are its
negative controls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search import hunter_cross_project_history, hunter_search
from techno_search.hunter_cross_project_history import (
    CROSS_PROJECT_DECISION_STATES,
    CROSS_PROJECT_HISTORY_SCHEMA_VERSION,
)
from techno_search.hunter_search import (
    CROSS_PROJECT_HISTORY_PATH_ENV,
    SearchLifecycleError,
    _require_decision_grade_history,
    cross_project_history_validity,
)

FIXTURE = (
    Path(__file__).parent / "fixtures" / "cross_project"
    / "hunter_prior_search_history_v1.json"
)


class TestValidityResolution:
    def test_absent_export_is_unknown_not_valid(self, tmp_path: Path) -> None:
        """An absent export must never resolve to a decision-grade state."""
        state, detail, payload = cross_project_history_validity(tmp_path / "nope.json")
        assert state == "unknown"
        assert "absent" in detail
        assert payload is None
        assert state not in CROSS_PROJECT_DECISION_STATES

    def test_malformed_export_is_invalid(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        path.write_text("{not json", encoding="utf-8")
        state, _, _ = cross_project_history_validity(path)
        assert state == "invalid"
        assert state not in CROSS_PROJECT_DECISION_STATES

    def test_wrong_schema_version_is_invalid(self, tmp_path: Path) -> None:
        path = tmp_path / "history.json"
        path.write_text(json.dumps({"schema_version": 999, "sources": []}), "utf-8")
        state, _, _ = cross_project_history_validity(path)
        assert state == "invalid"

    def test_committed_fixture_is_decision_grade(self) -> None:
        """The real export the suite runs against must actually qualify."""
        state, detail, payload = cross_project_history_validity(FIXTURE)
        assert state in CROSS_PROJECT_DECISION_STATES, detail
        assert payload is not None

    def test_one_degraded_source_degrades_the_export(self, tmp_path: Path) -> None:
        """An export is only as trustworthy as its weakest source."""
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        loaded = cross_project_history_validity(FIXTURE)[2]
        assert loaded is not None
        degraded = json.loads(json.dumps(loaded))
        degraded["sources"][0]["validity_state"] = "refresh-required"
        assert payload["schema_version"] == degraded["schema_version"]

        states = [s.get("validity_state") for s in degraded["sources"]]
        assert any(state not in CROSS_PROJECT_DECISION_STATES for state in states)


class TestFailsClosed:
    def test_absent_history_refuses_new_selection(self, tmp_path: Path) -> None:
        """The decisive control: no history means no novelty claim."""
        with pytest.raises(SearchLifecycleError) as excinfo:
            _require_decision_grade_history(tmp_path / "absent.json")
        message = str(excinfo.value)
        assert "fails closed" in message
        assert "IDENT-03" in message
        # DUR-04: concise and actionable, not a raw traceback dump.
        assert "Traceback" not in message
        assert "refresh" in message or "Publish" in message

    def test_decision_grade_history_permits_new_selection(
        self, siblings: dict[str, Path]
    ) -> None:
        """Positive control. Takes ``siblings`` because a decision-grade OWN
        export is no longer sufficient on its own — novelty is a claim about
        all three projects, so all three must be decision-grade."""
        state, _ = _require_decision_grade_history(FIXTURE)
        assert state in CROSS_PROJECT_DECISION_STATES

    def test_environment_override_changes_location_not_the_rule(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The override may relocate the export; it cannot waive validation."""
        weak = tmp_path / "weak.json"
        weak.write_text("{}", encoding="utf-8")
        monkeypatch.setenv(CROSS_PROJECT_HISTORY_PATH_ENV, str(weak))
        with pytest.raises(SearchLifecycleError):
            _require_decision_grade_history()


def _publish_sibling(root: Path, project: str) -> Path:
    """Lay out a sibling repo the way sibling_history_export_path expects."""
    export = root / project / "data_selection" / "hunter_prior_search_history_v1.json"
    export.parent.mkdir(parents=True, exist_ok=True)
    export.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    return export


@pytest.fixture
def siblings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Both siblings checked out and publishing a decision-grade export.

    Redirects discovery at tmp_path rather than the real sibling repos so the
    suite never depends on what is checked out beside it — and, critically,
    never writes into a real sibling repository (WS-01).
    """
    paths = {
        project: _publish_sibling(tmp_path, project)
        for project in hunter_search.CROSS_PROJECT_ROOT_NAMES
    }
    monkeypatch.setattr(
        hunter_search, "sibling_history_export_path", lambda project: paths[project]
    )
    return paths


class TestFederationSpansAllThreeProjects:
    """The known gap: proving 'not searched HERE' is not proving novelty.

    Before this, cross_project_history_validity() consulted only this repo's
    own published export, so a target already searched by EXO-Hunter or
    NEO-Hunter was still reported as novel.
    """

    def test_all_three_present_permits_new_selection(
        self, siblings: dict[str, Path]
    ) -> None:
        state, detail, per_project = (
            hunter_search.cross_project_history_federation_validity(FIXTURE)
        )
        assert state in CROSS_PROJECT_DECISION_STATES, detail
        # Own project plus both siblings — not just our own export.
        assert set(per_project) == {"techno_hunter", "exo_hunter", "neo_hunter"}
        assert all(
            s in CROSS_PROJECT_DECISION_STATES for s, _ in per_project.values()
        ), detail
        gate_state, _ = _require_decision_grade_history(FIXTURE)
        assert gate_state in CROSS_PROJECT_DECISION_STATES

    @pytest.mark.parametrize("missing", ["exo_hunter", "neo_hunter"])
    def test_absent_sibling_export_is_unknown_and_fails_closed(
        self, siblings: dict[str, Path], missing: str
    ) -> None:
        """A sibling that never published cannot be read as evidence of novelty."""
        siblings[missing].unlink()
        state, detail, per_project = (
            hunter_search.cross_project_history_federation_validity(FIXTURE)
        )
        assert per_project[missing][0] == "unknown"
        assert state not in CROSS_PROJECT_DECISION_STATES

        with pytest.raises(SearchLifecycleError) as excinfo:
            _require_decision_grade_history(FIXTURE)
        message = str(excinfo.value)
        assert missing in message, message
        assert "fails closed" in message
        assert "IDENT-03" in message
        assert "Traceback" not in message

    @pytest.mark.parametrize("broken", ["exo_hunter", "neo_hunter"])
    def test_malformed_sibling_export_fails_closed(
        self, siblings: dict[str, Path], broken: str
    ) -> None:
        siblings[broken].write_text("{not json", encoding="utf-8")
        state, _, per_project = hunter_search.cross_project_history_federation_validity(
            FIXTURE
        )
        assert per_project[broken][0] == "invalid"
        assert state not in CROSS_PROJECT_DECISION_STATES
        with pytest.raises(SearchLifecycleError):
            _require_decision_grade_history(FIXTURE)

    @pytest.mark.parametrize("broken", ["exo_hunter", "neo_hunter"])
    def test_wrong_schema_version_sibling_fails_closed(
        self, siblings: dict[str, Path], broken: str
    ) -> None:
        """Deliberately schema_version=2: an unversioned/wrong export is not
        decision-grade, even though it parses as JSON."""
        payload = json.loads(siblings[broken].read_text(encoding="utf-8"))
        payload["schema_version"] = CROSS_PROJECT_HISTORY_SCHEMA_VERSION + 1
        siblings[broken].write_text(json.dumps(payload), encoding="utf-8")
        state, _, per_project = hunter_search.cross_project_history_federation_validity(
            FIXTURE
        )
        assert per_project[broken][0] == "invalid"
        assert state not in CROSS_PROJECT_DECISION_STATES
        with pytest.raises(SearchLifecycleError):
            _require_decision_grade_history(FIXTURE)

    def test_one_degraded_source_degrades_the_federation(
        self, siblings: dict[str, Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The federation is only as strong as its weakest project."""
        real = hunter_search.cross_project_history_validity

        def degraded(path: Path | None = None):  # type: ignore[no-untyped-def]
            if path == siblings["neo_hunter"]:
                return "refresh-required", f"{path}: refresh-required source(s)", None
            return real(path)

        monkeypatch.setattr(hunter_search, "cross_project_history_validity", degraded)
        state, _, per_project = hunter_search.cross_project_history_federation_validity(
            FIXTURE
        )
        assert per_project["exo_hunter"][0] in CROSS_PROJECT_DECISION_STATES
        assert state == "refresh-required"
        with pytest.raises(SearchLifecycleError):
            _require_decision_grade_history(FIXTURE)

    def test_discovery_is_repo_relative_not_hardcoded(self) -> None:
        """WS-03: siblings are found relative to this repo, with no symlink,
        no copied-in file, and no absolute personal path baked into source."""
        source = Path(hunter_cross_project_history.__file__).read_text(encoding="utf-8")
        assert "/Users/" not in source
        assert "Dropbox" not in source
        for project in ("exo_hunter", "neo_hunter"):
            resolved = hunter_cross_project_history.sibling_history_export_path(project)
            assert not resolved.is_symlink()
            assert resolved.name == "hunter_prior_search_history_v1.json"
            assert resolved.parent.name == "data_selection"
            # Computed from this repo's own location, hence a real sibling of it.
            repo_root = Path(hunter_search.__file__).resolve().parents[2]
            assert resolved.parent.parent.parent == repo_root.parent
