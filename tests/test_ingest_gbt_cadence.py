from __future__ import annotations

import sys
import warnings
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import ingest_gbt_cadence  # noqa: E402


def test_pkg_resources_probe_suppresses_deprecation_warning() -> None:
    saved = sys.modules.pop("pkg_resources", None)
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ingest_gbt_cadence._install_pkg_resources_compatibility()
    finally:
        if saved is not None:
            sys.modules["pkg_resources"] = saved
        else:
            sys.modules.pop("pkg_resources", None)

    assert not [
        item
        for item in caught
        if "pkg_resources is deprecated as an API" in str(item.message)
    ]
