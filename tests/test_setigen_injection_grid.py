from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "setigen_injection_grid.py"


def _load_script_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("setigen_injection_grid", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeFrame:
    df = 2.5

    def __init__(self) -> None:
        self.added_signal: dict[str, object] | None = None
        self.saved_path: str | None = None

    def get_frequency(self, index: int) -> float:
        assert index == 0
        return 1_420_000_000.0

    def get_intensity(self, *, snr: float) -> float:
        return snr * 10.0

    def add_signal(self, **kwargs: object) -> None:
        self.added_signal = kwargs

    def save_h5(self, output_path: str) -> None:
        self.saved_path = output_path
        Path(output_path).write_text("fake h5", encoding="utf-8")


def test_inject_signal_uses_setigen_top_level_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_script_module()
    frame = _FakeFrame()

    fake_setigen = types.SimpleNamespace(
        Frame=lambda waterfall: frame,
        constant_path=lambda **kwargs: ("path", kwargs),
        constant_t_profile=lambda **kwargs: ("t_profile", kwargs),
        gaussian_f_profile=lambda **kwargs: ("f_profile", kwargs),
        constant_bp_profile=lambda **kwargs: ("bp_profile", kwargs),
    )
    monkeypatch.setitem(sys.modules, "setigen", fake_setigen)

    output_h5 = tmp_path / "injected.h5"

    assert module.inject_signal(
        tmp_path / "input.h5",
        snr=50.0,
        drift_rate_hz_s=1.5,
        freq_offset_mhz=0.25,
        output_h5_path=output_h5,
    )

    assert frame.added_signal is not None
    assert frame.added_signal["path"] == (
        "path",
        {"f_start": 1_420_250_000.0, "drift_rate": 1.5},
    )
    assert frame.added_signal["t_profile"] == ("t_profile", {"level": 500.0})
    assert frame.added_signal["f_profile"] == ("f_profile", {"width": 2.5})
    assert frame.added_signal["bp_profile"] == ("bp_profile", {"level": 1.0})
    assert output_h5.read_text(encoding="utf-8") == "fake h5"


def test_main_exits_nonzero_when_no_injections_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_script_module()
    h5_path = tmp_path / "input.h5"
    h5_path.write_text("fake h5", encoding="utf-8")
    output_dir = tmp_path / "grid"

    monkeypatch.setattr(module, "_check_dependencies", lambda: True)
    monkeypatch.setattr(module, "inject_signal", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "setigen_injection_grid.py",
            "--h5-file",
            str(h5_path),
            "--output-dir",
            str(output_dir),
            "--snr-values",
            "50",
            "--drift-rates",
            "1.0",
            "--n-freq-offsets",
            "1",
        ],
    )

    with pytest.raises(SystemExit) as excinfo:
        module.main()

    assert excinfo.value.code == 1
    manifest = json.loads(
        (output_dir / "injection_grid_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["total_injections"] == 1
    assert manifest["completed_injections"] == 0
    assert manifest["failed_injection_count"] == 1
    assert manifest["recovered_count"] == 0
