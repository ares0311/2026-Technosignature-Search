from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / (
    "download_bl_extended_corpus.sh"
)


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_extended_corpus_downloader_discovers_current_bl_urls() -> None:
    script = _script_text()

    assert "breakthroughinitiatives.org/opendatasearch" in script
    assert "bldata\\.berkeley\\.edu" in script
    assert "file_type=HDF5" in script
    assert "blpd0.ssl.berkeley.edu" not in script


def test_extended_corpus_downloader_bounds_curl_connection_time() -> None:
    """Regression test: the discovery curl call had no --connect-timeout/
    --max-time, so a slow or unresponsive breakthroughinitiatives.org left
    the whole script hanging indefinitely with no error and no visible
    progress. The download curl call had no --connect-timeout either
    (though --max-time is intentionally omitted there since large real HDF5
    transfers legitimately take a long time once connected)."""
    script = _script_text()

    assert (
        "curl -fsSL --connect-timeout 15 --max-time 60 --retry 3 --retry-delay 5 "
        '--location "${search_url}"'
    ) in script
    assert "--continue-at - \\\n       --connect-timeout 15 \\\n       --retry 3" in script


def test_extended_corpus_downloader_fails_closed_on_zero_evidence() -> None:
    script = _script_text()

    assert "downloaded=0" in script
    assert 'if [[ "$((downloaded + reused))" -eq 0 ]]' in script
    assert "empty directories are not evidence" in script
    assert "exit 1" in script


def test_extended_corpus_downloader_has_non_networked_inspection_mode() -> None:
    script = _script_text()

    assert "--dry-run" in script
    assert "-h|--help" in script
    assert "Dry run complete; no network download attempted" in script


def test_extended_corpus_downloader_has_discovery_only_availability_mode() -> None:
    script = _script_text()

    assert "--discover-only" in script
    assert "--availability-report" in script
    assert "Discovery complete; no HDF5 payloads downloaded" in script
    assert "URL-available HDF5 targets" in script


def test_extended_corpus_downloader_limits_url_available_targets() -> None:
    script = _script_text()

    assert "URL-available target limit reached" in script
    assert "New-download target limit reached" in script
    assert 'if ! url="$(discover_hdf5_url "${name}")"; then' in script
    assert 'available=$((available + 1))' in script
    assert '"${downloaded}" -ge "${MAX_TARGETS}"' in script


def test_extended_corpus_downloader_reads_stratified_manifest() -> None:
    script = _script_text()

    assert "--manifest" in script
    assert "data/target_sample_manifest.json" in script
    assert "load_manifest_targets" in script
    assert 'manifest.get("targets", [])' in script
    assert 'f"HIP{hip}"' in script


def test_extended_corpus_downloader_keeps_legacy_targets_as_fallback_only() -> None:
    script = _script_text()

    assert "Falling back to legacy 5-target list" in script
    assert "Production runs should use the stratified manifest" in script


def test_extended_corpus_downloader_preserves_scientific_guardrails() -> None:
    script = _script_text()

    assert "No file or hit table entry constitutes a" in script
    assert "technosignature detection" in script
    assert "authorizes external submission" in script


def test_extended_corpus_downloader_enforces_data_storage_policy() -> None:
    script = _script_text()

    assert "ACQUISITION_ROLE=\"live_search_bootstrap_cache\"" in script
    assert "ACQUISITION_MODE=\"targeted_batch_pull\"" in script
    assert "RAW_RETENTION_POLICY=\"public_raw_archive_cache_not_pinned\"" in script
    assert "TECHNO_EXTENDED_CORPUS_FREE_SPACE_RESERVE_GB" in script
    assert "ensure_projected_free_space" in script
    assert "free_space_reserve_not_met" in script
    assert "\"policy_blocked\"" in script


def test_extended_corpus_downloader_does_not_misstate_decision_134_status() -> None:
    script = _script_text()

    assert "DECISION-134 remains blocked" not in script
    assert "This command did not add usable extended-corpus evidence" in script


def test_extended_corpus_available_target_limit_skips_unavailable_manifest_rows(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "targets": [
                    {"hip": "111"},
                    {"hip": "222"},
                    {"hip": "333"},
                ]
            }
        ),
        encoding="utf-8",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
url="${@: -1}"
case "${url}" in
  *target=HIP111*) printf '<html>No HDF5 here</html>' ;;
  *target=HIP222*) printf 'https://bldata.berkeley.edu/test/HIP222.gpuspec.0002.h5' ;;
  *target=HIP333*) printf 'https://bldata.berkeley.edu/test/HIP333.gpuspec.0002.h5' ;;
  *) printf 'unexpected-url=%s' "${url}" >&2; exit 22 ;;
esac
""",
        encoding="utf-8",
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["TECHNO_EXTENDED_CORPUS_MAX_TARGETS"] = "2"
    env["TECHNO_EXTENDED_CORPUS_PYTHON"] = sys.executable
    availability_output = tmp_path / "availability.tsv"

    result = subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest),
            "--discover-only",
            "--availability-output",
            str(availability_output),
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    assert "HIP111" not in result.stdout
    assert "HIP222\thttps://bldata.berkeley.edu/test/HIP222.gpuspec.0002.h5" in result.stdout
    assert "HIP333\thttps://bldata.berkeley.edu/test/HIP333.gpuspec.0002.h5" in result.stdout
    assert "URL-available HDF5 targets: 2" in result.stderr
    assert "Targets without a discovered HDF5 URL: 1" in result.stderr
    assert availability_output.read_text(encoding="utf-8").splitlines() == [
        "HIP222\thttps://bldata.berkeley.edu/test/HIP222.gpuspec.0002.h5",
        "HIP333\thttps://bldata.berkeley.edu/test/HIP333.gpuspec.0002.h5",
    ]


def test_extended_corpus_downloader_passes_through_non_numeric_identifiers(
    tmp_path: Path,
) -> None:
    """Regression test: the real HPRC catalog's '60 nearest stars' subset uses
    Gliese/GJ-format identifiers (e.g. GJ1002), not bare HIP numbers. A bare
    numeric hip value still gets the real 'HIP' prefix, but a real
    already-complete identifier must be used verbatim, not mangled into
    'HIPGJ1002'."""

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"targets": [{"hip": "8102"}, {"hip": "GJ1002"}]}),
        encoding="utf-8",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
url="${@: -1}"
case "${url}" in
  *target=HIP8102*) printf 'https://bldata.berkeley.edu/test/HIP8102.gpuspec.0002.h5' ;;
  *target=GJ1002*) printf 'https://bldata.berkeley.edu/test/GJ1002.gpuspec.0002.h5' ;;
  *) printf 'unexpected-url=%s' "${url}" >&2; exit 22 ;;
esac
""",
        encoding="utf-8",
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["TECHNO_EXTENDED_CORPUS_PYTHON"] = sys.executable

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--manifest", str(manifest), "--discover-only"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    assert "HIP8102\thttps://bldata.berkeley.edu/test/HIP8102.gpuspec.0002.h5" in result.stdout
    assert "GJ1002\thttps://bldata.berkeley.edu/test/GJ1002.gpuspec.0002.h5" in result.stdout
    assert "HIPGJ1002" not in result.stdout


def test_extended_corpus_download_limit_skips_existing_hdf5_targets(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "targets": [
                    {"hip": "111"},
                    {"hip": "222"},
                    {"hip": "333"},
                ]
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "extended_corpus"
    existing_dir = out_dir / "HIP111"
    existing_dir.mkdir(parents=True)
    existing_file = existing_dir / "HIP111.gpuspec.0002.h5"
    existing_file.write_text("existing evidence\n", encoding="utf-8")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
url="${@: -1}"
if [[ "${url}" == *breakthroughinitiatives.org* ]]; then
  case "${url}" in
    *target=HIP111*) printf 'https://bldata.berkeley.edu/test/HIP111.gpuspec.0002.h5' ;;
    *target=HIP222*) printf 'https://bldata.berkeley.edu/test/HIP222.gpuspec.0002.h5' ;;
    *target=HIP333*) printf 'https://bldata.berkeley.edu/test/HIP333.gpuspec.0002.h5' ;;
    *) printf 'unexpected-discovery-url=%s' "${url}" >&2; exit 22 ;;
  esac
  exit 0
fi
out_path=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) out_path="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ "${url}" == *HIP111.gpuspec.0002.h5 ]]; then
  printf 'unexpected redownload of HIP111' >&2
  exit 44
fi
if [[ -z "${out_path}" ]]; then
  printf 'missing --output for %s' "${url}" >&2
  exit 45
fi
printf 'downloaded %s\n' "${url}" > "${out_path}"
""",
        encoding="utf-8",
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["TECHNO_EXTENDED_CORPUS_MAX_TARGETS"] = "1"
    env["TECHNO_EXTENDED_CORPUS_OUT_DIR"] = str(out_dir)
    env["TECHNO_EXTENDED_CORPUS_PYTHON"] = sys.executable
    env["TECHNO_EXTENDED_CORPUS_FREE_SPACE_RESERVE_GB"] = "0"
    # Regression guard: this test runs the real script end-to-end (with a
    # faked curl), which reaches the real record-data-collection-status
    # call on success. Without redirecting the manifest path, this test
    # would write to (and, without the branch-safety guard, previously
    # auto-committed and pushed to) this project's own real tracked
    # docs/data_collection_status.json -- caught in this session.
    env["TECHNO_DATA_COLLECTION_STATUS_PATH"] = str(tmp_path / "data_collection_status.json")

    result = subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest),
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    assert existing_file.read_text(encoding="utf-8") == "existing evidence\n"
    assert not (out_dir / "HIP333" / "HIP333.gpuspec.0002.h5").exists()
    assert (
        out_dir / "HIP222" / "HIP222.gpuspec.0002.h5"
    ).read_text(encoding="utf-8").startswith(
        "downloaded https://bldata.berkeley.edu/test/HIP222"
    )
    assert "Reused existing HDF5 targets: 1" in result.stderr
    assert "Successful new downloads: 1" in result.stderr
    assert "New-download target limit reached (1)" in result.stderr

    real_status_path = Path(__file__).resolve().parents[1] / "docs" / "data_collection_status.json"
    real_status_before = real_status_path.read_text(encoding="utf-8")
    redirected_status_path = tmp_path / "data_collection_status.json"
    assert redirected_status_path.exists(), "status manifest should be at the redirected path"
    status = json.loads(redirected_status_path.read_text(encoding="utf-8"))
    run_status = status["runs"]["download_bl_extended_corpus"]
    assert run_status["ok"] is True
    assert run_status["downloaded"] == 1
    assert run_status["reused"] == 1
    assert run_status["downloaded_targets"] == ["HIP222"]
    assert run_status["reused_targets"] == ["HIP111"]
    assert real_status_path.read_text(encoding="utf-8") == real_status_before, (
        "this test must never write to the real tracked status manifest"
    )
