#!/bin/bash
# Claude Code statusLine script for the 2026 Technosignatures repo.
# Reads the statusLine JSON payload from stdin and emits one compact,
# color-coded line plus a working/idle indicator.
#
# Fields and behavior verified against the official docs at
# code.claude.com/docs/en/statusline (fetched via Context7, 2026-07-11):
#   - ANSI escape codes for color are explicitly supported by the status
#     line renderer ("What your script can output").
#   - There is no literal busy/idle field in the stdin payload. The docs'
#     "When it updates" section says the script normally re-runs only after
#     assistant messages / compact / mode changes (debounced 300ms), and
#     recommends `refreshInterval` (settings.json, minimum 1000ms) to keep
#     it re-running on a timer during idle waits. Combined with `stat`-ing
#     `transcript_path`'s mtime, that gives a real (if heuristic) working
#     vs idle signal: the transcript is actively being appended to while
#     Claude is generating/using tools, and goes quiet the moment a turn
#     ends. settings.json sets refreshInterval: 1000 to drive this.

input=$(cat)

# Converts a rate-limit reset Unix-epoch timestamp (may be a float) to a
# short local time string. Tries BSD date (macOS) first, then GNU date.
format_reset_epoch() {
  local raw="$1"
  [ -z "$raw" ] && return 0
  local epoch
  epoch=$(printf '%.0f' "$raw" 2>/dev/null) || return 0
  date -r "$epoch" "+%a %-I:%M%p" 2>/dev/null || date -d "@$epoch" "+%a %-I:%M%p" 2>/dev/null
}

# mtime of a file as a Unix epoch integer. Tries BSD stat (macOS) first,
# then GNU stat.
file_mtime_epoch() {
  local f="$1"
  [ -z "$f" ] && return 0
  stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null
}

# ANSI color codes. Claude Code's status line renderer interprets these
# directly (per the docs cited above) — this isn't a raw terminal, so no
# NO_COLOR / isatty gating is needed.
RESET='\033[0m'
DIM='\033[2m'
BOLD='\033[1m'
CYAN='\033[1;36m'
MAGENTA='\033[35m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
GREY='\033[90m'

# Green under 70%, yellow 70-89%, red 90%+ — same thresholds the official
# multi-line context-bar example uses.
color_for_pct() {
  local pct="$1"
  local pct_int
  pct_int=$(printf '%.0f' "$pct" 2>/dev/null) || pct_int=0
  if [ "$pct_int" -ge 90 ]; then
    printf '%s' "$RED"
  elif [ "$pct_int" -ge 70 ]; then
    printf '%s' "$YELLOW"
  else
    printf '%s' "$GREEN"
  fi
}

version=$(echo "$input" | jq -r '.version // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
project_dir=$(echo "$input" | jq -r '.workspace.project_dir // .cwd // empty')
cwd=$(echo "$input" | jq -r '.cwd // empty')
output_style=$(echo "$input" | jq -r '.output_style.name // empty')
vim_mode=$(echo "$input" | jq -r '.vim.mode // empty')
transcript_path=$(echo "$input" | jq -r '.transcript_path // empty')

project_name=$(basename "$project_dir")

# Git branch for the current working directory (skip optional locks so this
# never blocks on a concurrent git operation elsewhere in the repo).
branch=""
branch_color="$GREEN"
if git -C "${cwd:-$project_dir}" --no-optional-locks rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "${cwd:-$project_dir}" --no-optional-locks branch --show-current 2>/dev/null)
  [ -z "$branch" ] && branch="detached"
  if ! git -C "${cwd:-$project_dir}" --no-optional-locks diff --quiet 2>/dev/null || \
     ! git -C "${cwd:-$project_dir}" --no-optional-locks diff --cached --quiet 2>/dev/null; then
    branch_color="$YELLOW"
  fi
fi

# Context-window usage percentage (pre-calculated by Claude Code).
ctx_used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Claude.ai subscription rate limits, when present (only appears after the
# first API response of a session, and only for accounts with visible
# rate-limit data). Each window's usage and reset time are independently
# optional — a window can be absent even when the other is present.
five_hour=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
seven_day=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
five_hour_resets_raw=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
seven_day_resets_raw=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')
five_hour_resets=$(format_reset_epoch "$five_hour_resets_raw")
seven_day_resets=$(format_reset_epoch "$seven_day_resets_raw")

# Working/idle indicator: "working" if the transcript was written to within
# the last 10s, else "idle". 10s comfortably spans the 300ms update debounce
# and normal tool-call gaps without flickering, while still flipping to idle
# promptly after a turn actually ends.
work_indicator=""
if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  now_epoch=$(date +%s)
  mtime_epoch=$(file_mtime_epoch "$transcript_path")
  if [ -n "$mtime_epoch" ] && [ $((now_epoch - mtime_epoch)) -le 10 ]; then
    work_indicator="${GREEN}${BOLD}● working${RESET}"
  else
    work_indicator="${GREY}○ idle${RESET}"
  fi
fi

parts=()
[ -n "$work_indicator" ] && parts+=("$work_indicator")
[ -n "$version" ] && parts+=("${DIM}v${version}${RESET}")
[ -n "$model" ] && parts+=("${CYAN}${model}${RESET}")
[ -n "$project_name" ] && parts+=("${BOLD}${project_name}${RESET}")
[ -n "$branch" ] && parts+=("${branch_color}git:${branch}${RESET}")
[ -n "$output_style" ] && [ "$output_style" != "default" ] && parts+=("${MAGENTA}style:${output_style}${RESET}")
[ -n "$vim_mode" ] && parts+=("${MAGENTA}${vim_mode}${RESET}")
if [ -n "$ctx_used" ]; then
  ctx_color=$(color_for_pct "$ctx_used")
  parts+=("${ctx_color}$(printf 'ctx:%.0f%%' "$ctx_used")${RESET}")
fi
if [ -n "$five_hour" ]; then
  five_hour_color=$(color_for_pct "$five_hour")
  five_hour_part="${five_hour_color}$(printf '5h:%.0f%%' "$five_hour")${RESET}"
  [ -n "$five_hour_resets" ] && five_hour_part="${five_hour_part}${DIM} (↻${five_hour_resets})${RESET}"
  parts+=("$five_hour_part")
fi
if [ -n "$seven_day" ]; then
  seven_day_color=$(color_for_pct "$seven_day")
  seven_day_part="${seven_day_color}$(printf '7d:%.0f%%' "$seven_day")${RESET}"
  [ -n "$seven_day_resets" ] && seven_day_part="${seven_day_part}${DIM} (↻${seven_day_resets})${RESET}"
  parts+=("$seven_day_part")
fi

out=""
sep=""
for p in "${parts[@]}"; do
  out="${out}${sep}${p}"
  sep="${DIM} | ${RESET}"
done

echo -e "$out"
