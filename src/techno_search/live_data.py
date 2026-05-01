"""Opt-in live-data integration scaffold.

Default tests and workflows must not contact external services. This module only
provides a guarded interface for future live integrations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

LIVE_DATA_ENV_VAR = "TECHNO_SEARCH_ENABLE_LIVE_DATA"


@dataclass(frozen=True)
class LiveDataRequest:
    """Minimal request descriptor for future live-data adapters."""

    source_name: str
    query: str
    purpose: str


class LiveDataDisabledError(RuntimeError):
    """Raised when live-data access is requested without explicit opt-in."""


def live_data_enabled() -> bool:
    """Return whether live-data integrations are explicitly enabled."""

    return os.environ.get(LIVE_DATA_ENV_VAR) == "1"


def require_live_data_enabled() -> None:
    """Require explicit live-data opt-in before any external access is attempted."""

    if not live_data_enabled():
        msg = (
            f"Live-data integrations are disabled. Set {LIVE_DATA_ENV_VAR}=1 only for "
            "explicitly marked integration_live runs."
        )
        raise LiveDataDisabledError(msg)


class LiveDataClient:
    """Base scaffold for future live-data clients."""

    def fetch_metadata(self, request: LiveDataRequest) -> dict[str, str]:
        """Fetch metadata for a live-data request.

        The base implementation never performs network access. Concrete adapters must
        implement provider-specific behavior behind `require_live_data_enabled()`.
        """

        require_live_data_enabled()
        msg = f"No live-data adapter is implemented for {request.source_name!r}."
        raise NotImplementedError(msg)
