"""pytest configuration: skip integration_live tests unless opt-in env var is set."""
from __future__ import annotations

import os

import pytest

from techno_search.log_store import init_sqlite_log_db


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if os.environ.get("TECHNO_SEARCH_ENABLE_LIVE_DATA") != "1":
        skip_live = pytest.mark.skip(
            reason="Live integration test (set TECHNO_SEARCH_ENABLE_LIVE_DATA=1 to run)."
        )
        for item in items:
            if item.get_closest_marker("integration_live"):
                item.add_marker(skip_live)


@pytest.fixture(scope="session", autouse=True)
def ensure_sqlite_log_initialized() -> None:
    """Ensure the top-level SQLite log is initialized before consistency tests run."""
    import contextlib
    with contextlib.suppress(Exception):
        init_sqlite_log_db()
