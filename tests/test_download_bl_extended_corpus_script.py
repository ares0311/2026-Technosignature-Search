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
        "curl -fsSL --connect-timeout 15 --max-time 60 --retry 3 --retry-delay 5 \\\n"
        "      --location -G \\\n"
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
    assert "download_bl_extended_corpus_discovery" in script
    assert "metadata_only_discovery" in script


def test_extended_corpus_downloader_limits_url_available_targets() -> None:
    script = _script_text()

    assert "URL-available target limit reached" in script
    assert "New-download target limit reached" in script
    assert 'if url="$(discover_hdf5_url "${name}")"; then' in script
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
    assert "TECHNO_LOCAL_STORAGE_CAP_GB" in script
    assert "ensure_within_local_storage_cap" in script
    assert "local_storage_cap_exceeded" in script
    assert "\"local_storage_cap_gb\"" in script


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
args="$*"
case "${args}" in
  *target=HIP111*) printf '<html>No HDF5 here</html>' ;;
  *target=HIP222*) printf 'https://bldata.berkeley.edu/test/HIP222.gpuspec.0002.h5' ;;
  *target=HIP333*) printf 'https://bldata.berkeley.edu/test/HIP333.gpuspec.0002.h5' ;;
  *) printf 'unexpected-args=%s' "${args}" >&2; exit 22 ;;
esac
""",
        encoding="utf-8",
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["TECHNO_EXTENDED_CORPUS_MAX_TARGETS"] = "2"
    env["TECHNO_EXTENDED_CORPUS_PYTHON"] = sys.executable
    env["TECHNO_DATA_COLLECTION_STATUS_PATH"] = str(tmp_path / "status.json")
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
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    run_status = status["runs"]["download_bl_extended_corpus_discovery"]
    assert run_status["ok"] is True
    assert run_status["mode"] == "discover_only"
    assert run_status["available"] == 2
    assert run_status["skipped"] == 1
    assert run_status["available_targets"] == [
        {
            "target": "HIP222",
            "url": "https://bldata.berkeley.edu/test/HIP222.gpuspec.0002.h5",
        },
        {
            "target": "HIP333",
            "url": "https://bldata.berkeley.edu/test/HIP333.gpuspec.0002.h5",
        },
    ]
    assert run_status["skipped_targets"] == [
        {"target": "HIP111", "reason": "no_hdf5_url_discovered"}
    ]


def test_extended_corpus_downloader_url_encodes_target_names_with_spaces(
    tmp_path: Path,
) -> None:
    """Regression test, 2026-07-11: a real target-priority queue row named
    'DENIS-P J1048.0-3956' broke the discovery curl call with 'curl: (3)
    URL rejected: Malformed input to a URL function', because the target
    name was interpolated raw into the query string instead of being
    percent-encoded. Real curl encodes '-G --data-urlencode' arguments
    itself, so this fake curl only has to prove the raw (unencoded) target
    name reaches it as its own argument rather than corrupting the URL."""

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"targets": [{"hip": "DENIS-P J1048.0-3956"}]}),
        encoding="utf-8",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
args="$*"
case "${args}" in
  *"target=DENIS-P J1048.0-3956"*)
    printf 'https://bldata.berkeley.edu/test/DENIS.gpuspec.0002.h5' ;;
  *) printf 'unexpected-args=%s' "${args}" >&2; exit 22 ;;
esac
""",
        encoding="utf-8",
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["TECHNO_EXTENDED_CORPUS_PYTHON"] = sys.executable
    env["TECHNO_DATA_COLLECTION_STATUS_PATH"] = str(tmp_path / "status.json")

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--manifest", str(manifest), "--discover-only"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    assert (
        "DENIS-P J1048.0-3956\thttps://bldata.berkeley.edu/test/DENIS.gpuspec.0002.h5"
        in result.stdout
    )
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    run_status = status["runs"]["download_bl_extended_corpus_discovery"]
    assert run_status["skipped"] == 0


def test_extended_corpus_downloader_distinguishes_request_failure_from_no_match(
    tmp_path: Path,
) -> None:
    """Regression test, 2026-07-11: before this fix, both a curl transport
    failure and a genuine 'no HDF5 file for this target' response were
    recorded under the identical 'no_hdf5_url_discovered' reason, silently
    conflating a technical failure with confirmed negative evidence."""

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"targets": [{"hip": "111"}, {"hip": "222"}]}),
        encoding="utf-8",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
args="$*"
case "${args}" in
  *target=HIP111*) printf 'connection reset' >&2; exit 7 ;;
  *target=HIP222*) printf '<html>No HDF5 here</html>' ;;
  *) printf 'unexpected-args=%s' "${args}" >&2; exit 22 ;;
esac
""",
        encoding="utf-8",
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["TECHNO_EXTENDED_CORPUS_PYTHON"] = sys.executable
    env["TECHNO_DATA_COLLECTION_STATUS_PATH"] = str(tmp_path / "status.json")

    # Not check=True: both targets are intentionally unavailable here (that's
    # the point of this test), and a zero-available discovery run correctly
    # exits 1 -- the status manifest is still written before that exit, which
    # is what this test verifies.
    subprocess.run(
        ["bash", str(SCRIPT_PATH), "--manifest", str(manifest), "--discover-only"],
        env=env,
        capture_output=True,
        text=True,
    )

    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    run_status = status["runs"]["download_bl_extended_corpus_discovery"]
    skipped_by_target = {
        item["target"]: item["reason"] for item in run_status["skipped_targets"]
    }
    assert skipped_by_target["HIP111"] == "discovery_request_failed"
    assert skipped_by_target["HIP222"] == "no_hdf5_url_discovered"


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
args="$*"
case "${args}" in
  *target=HIP8102*) printf 'https://bldata.berkeley.edu/test/HIP8102.gpuspec.0002.h5' ;;
  *target=GJ1002*) printf 'https://bldata.berkeley.edu/test/GJ1002.gpuspec.0002.h5' ;;
  *) printf 'unexpected-args=%s' "${args}" >&2; exit 22 ;;
esac
""",
        encoding="utf-8",
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["TECHNO_EXTENDED_CORPUS_PYTHON"] = sys.executable
    env["TECHNO_DATA_COLLECTION_STATUS_PATH"] = str(tmp_path / "status.json")

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
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    run_status = status["runs"]["download_bl_extended_corpus_discovery"]
    assert [item["target"] for item in run_status["available_targets"]] == [
        "HIP8102",
        "GJ1002",
    ]


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
  args="$*"
  case "${args}" in
    *target=HIP111*) printf 'https://bldata.berkeley.edu/test/HIP111.gpuspec.0002.h5' ;;
    *target=HIP222*) printf 'https://bldata.berkeley.edu/test/HIP222.gpuspec.0002.h5' ;;
    *target=HIP333*) printf 'https://bldata.berkeley.edu/test/HIP333.gpuspec.0002.h5' ;;
    *) printf 'unexpected-discovery-args=%s' "${args}" >&2; exit 22 ;;
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


def test_extended_corpus_downloader_enforces_local_storage_cap(tmp_path: Path) -> None:
    """Regression test: this project has no external SSD or cloud storage, so
    the total local data footprint must never exceed TECHNO_LOCAL_STORAGE_CAP_GB,
    independent of the underlying disk's free space (which the pre-existing
    free-space-reserve check measures instead)."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"targets": [{"hip": "999999"}]}),
        encoding="utf-8",
    )
    out_dir = tmp_path / "extended_corpus"
    usage_dir = tmp_path / "usage"
    usage_dir.mkdir()

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
url="${@: -1}"
if [[ "${url}" == *breakthroughinitiatives.org* ]]; then
  args="$*"
  case "${args}" in
    *target=HIP999999*) printf 'https://bldata.berkeley.edu/test/HIP999999.gpuspec.0002.h5' ;;
    *) printf 'unexpected-discovery-args=%s' "${args}" >&2; exit 22 ;;
  esac
  exit 0
fi
out_path=""
head_only=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) out_path="$2"; shift 2 ;;
    -fsSI) head_only=1; shift ;;
    *) shift ;;
  esac
done
if [[ "${head_only}" -eq 1 ]]; then
  printf 'HTTP/1.1 200 OK\\r\\nContent-Length: 5368709120\\r\\n\\r\\n'
  exit 0
fi
if [[ -z "${out_path}" ]]; then
  printf 'missing --output for %s' "${url}" >&2
  exit 45
fi
printf 'unexpected download past the storage cap check' >&2
exit 46
""",
        encoding="utf-8",
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["TECHNO_EXTENDED_CORPUS_OUT_DIR"] = str(out_dir)
    env["TECHNO_EXTENDED_CORPUS_PYTHON"] = sys.executable
    env["TECHNO_EXTENDED_CORPUS_FREE_SPACE_RESERVE_GB"] = "0"
    env["TECHNO_LOCAL_STORAGE_CAP_GB"] = "1"
    env["TECHNO_LOCAL_STORAGE_USAGE_DIRS"] = str(usage_dir)
    env["TECHNO_DATA_COLLECTION_STATUS_PATH"] = str(tmp_path / "data_collection_status.json")

    result = subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest),
        ],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not (out_dir / "HIP999999" / "HIP999999.gpuspec.0002.h5").exists()
    assert "Local storage cap would be exceeded" in result.stderr
    assert "No external SSD or cloud storage is available" in result.stderr
    assert "Data/storage policy blocked this run" in result.stderr

    status = json.loads((tmp_path / "data_collection_status.json").read_text(encoding="utf-8"))
    run_status = status["runs"]["download_bl_extended_corpus"]
    assert run_status["ok"] is False
    assert run_status["policy_blocked"] is True
    assert run_status["local_storage_cap_gb"] == 1.0
    assert run_status["skipped_targets"] == [
        {"target": "HIP999999", "reason": "local_storage_cap_exceeded"}
    ]
