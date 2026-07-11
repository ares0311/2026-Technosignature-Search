#!/usr/bin/env bash
# patch_turbo_seti_numpy2_compat.sh
#
# turbo_seti==2.3.2 (the exact version pinned in pyproject.toml's `radio`
# extra, and the newest release on PyPI as of 2026-07-11 -- there is no
# newer upstream version to bump to) has a real off-by-one bug in
# find_doppler.py: a debug-log line formats `max_val.total_n_hits` (a
# length-1 numpy array, by design -- three other call sites in the same
# file correctly index it as `total_n_hits[0]`) directly with `%i`,
# omitting the `[0]` index used everywhere else. Older numpy silently
# coerced a length-1 array in `%` string formatting; numpy>=2.0 (which pip
# resolves to by default, since turbo_seti declares no numpy upper bound)
# no longer does, so the run crashes on this trailing debug-log statement
# -- after the real hit-finding work for that coarse channel is already
# done and written to file.
#
# This lives in .venv/site-packages, which is never committed to git and
# is wiped on every fresh venv/extras install, so the one-line fix does
# not survive a venv rebuild on its own. Run this script once after any
# `pip install -e ".[radio]"` (or equivalent) to reapply it. Idempotent --
# safe to run repeatedly.
#
# Usage:
#   bash scripts/patch_turbo_seti_numpy2_compat.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export MPLCONFIGDIR="${REPO_ROOT}/data_cache/mplconfig"
mkdir -p "${MPLCONFIGDIR}"
TARGET_FILE="$(
  "${REPO_ROOT}/.venv/bin/python" -c "import turbo_seti.find_doppler.find_doppler as m; print(m.__file__)" 2>/dev/null | tail -1
)" || {
  echo "[ERROR] turbo_seti is not importable in this venv -- install the 'radio' extra first:" >&2
  echo "  .venv/bin/python -m pip install -e '.[radio]'" >&2
  exit 1
}

BUGGY_LINE='str(datah5_obj.header['"'"'cchan_id'"'"']) + " is: %i" % max_val.total_n_hits)'
FIXED_LINE='str(datah5_obj.header['"'"'cchan_id'"'"']) + " is: %i" % max_val.total_n_hits[0])'

if grep -qF "${FIXED_LINE}" "${TARGET_FILE}"; then
  echo "[OK] Already patched: ${TARGET_FILE}"
  exit 0
fi

if ! grep -qF "${BUGGY_LINE}" "${TARGET_FILE}"; then
  echo "[ERROR] Expected buggy line not found in ${TARGET_FILE}." >&2
  echo "[ERROR] turbo_seti's source may have changed; inspect find_doppler.py around" >&2
  echo "[ERROR] 'Total number of candidates for coarse channel' manually before patching." >&2
  exit 1
fi

python3 -c "
import pathlib
path = pathlib.Path('${TARGET_FILE}')
text = path.read_text(encoding='utf-8')
buggy = '''${BUGGY_LINE}'''
fixed = '''${FIXED_LINE}'''
if buggy not in text:
    raise SystemExit('buggy line vanished between grep check and patch -- aborting')
path.write_text(text.replace(buggy, fixed, 1), encoding='utf-8')
"

echo "[OK] Patched ${TARGET_FILE} (added missing [0] index on total_n_hits)."
