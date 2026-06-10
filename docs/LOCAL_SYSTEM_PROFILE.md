# LOCAL SYSTEM PROFILE

## Purpose

Record the local development machine profile so agents and contributors can choose sensible defaults for tests, synthetic workloads, caching, and parallel processing.

This document describes the primary local workstation. It should guide performance defaults, not scientific interpretation. All code must still be reproducible on other systems by exposing configuration overrides.

---

## Captured

Date: 2026-05-01

Sources:

- macOS About This Mac screenshot provided by the project owner
- `system_profiler SPHardwareDataType SPSoftwareDataType`
- `system_profiler SPDisplaysDataType`
- `df -h .`
- `.venv/bin/python`

Unique local identifiers such as serial number, hardware UUID, and provisioning UDID are intentionally omitted.

---

## Hardware

| Component | Value |
|---|---|
| Machine | MacBook Pro |
| Model | 16-inch, Nov 2024 |
| Model identifier | Mac16,5 |
| Chip | Apple M4 Max |
| CPU cores | 16 total: 12 performance, 4 efficiency |
| GPU cores | 40 |
| Memory | 64 GB unified memory |
| Architecture | arm64 / Apple Silicon |
| Metal support | Supported |
| Startup disk | Phi |

---

## Software

| Component | Value |
|---|---|
| macOS | 26.4.1 |
| Build | 25E253 |
| Kernel | Darwin 25.4.0 |
| Local virtual environment Python | Python 3.14.3 (updated 2026-06-10) |
| Python-reported CPU count | 16 |
| Project filesystem free space at capture | 439 GiB available on a 926 GiB volume |
| Power state at capture | AC power attached |

---

## Optimization Guidance

Use this system profile when choosing local defaults:

- **Always use `.venv/bin/python` (or `.venv/bin/techno-search`) for all Python invocations. Never use system `python3`.** The system Python version may differ from the project venv (currently 3.14.3 after the 2026-06-10 upgrade).
- Default CPU-bound worker pools should leave headroom for the OS and interactive use.
- Use up to 12 workers for CPU-heavy synthetic search, scoring calibration, or test parametrization unless benchmarks show a better value.
- Use up to 16 workers only for light I/O-bound tasks or explicitly requested full-machine runs.
- Keep default memory budgets conservative. A good default ceiling is 48 GB, reserving roughly 16 GB for the OS, IDEs, browser sessions, and Dropbox sync.
- Avoid writing large intermediate products into the repository. Use ignored data/cache locations described in `docs/DATA_POLICY.md`.
- Prefer chunked processing over loading full survey-scale arrays or catalogs into memory.
- Treat GPU/Metal acceleration as optional. Code should run correctly on CPU-only systems unless a feature is explicitly documented as requiring Apple Silicon GPU support.
- Make performance-sensitive worker counts, batch sizes, memory limits, and cache paths configurable through config files or CLI options.
- Do not hard-code this hardware profile into scientific logic, thresholds, candidate scores, or report claims.

---

## Reproducibility Rules

Local optimization must not reduce scientific reproducibility.

- Default tests must still use synthetic fixtures and mocked services.
- Live-data tests must remain opt-in and marked separately.
- Benchmark results should record the hardware profile, command, input size, config version, and git commit.
- Candidate outputs must preserve provenance independent of local hardware.
- Performance shortcuts must not skip false-positive checks, negative evidence, blocking issues, or provenance capture.

---

## Python Version History

| Date | Version | Notes |
|---|---|---|
| 2026-05-01 | 3.13.12 | Initial profile capture |
| 2026-06-10 | 3.14.3 | Upgraded by project owner; tested turboSETI integration |

---

## When To Update

Update this file when:

- the primary development machine changes
- macOS or Python runtime changes in a way that affects development
- a benchmark establishes better default worker counts or memory budgets
- project code adds GPU, multiprocessing, cache, or large-array behavior
