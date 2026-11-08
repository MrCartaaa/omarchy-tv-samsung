#!/usr/bin/env bash
# Put packages.txt and removed.txt back after the television lists them again.
#
# A boot of this set can turn the deactivated ids back on and can copy the
# AirPlay preload back. The television does not run this job. A computer on
# the same network runs it, on a timer, while that computer is on.
#
# No Remote PC click. A television whose developer port is closed counts as
# off and exits 0. Ids that are still listed are written to the log and do
# not fail the timer. A missing tool, or a settle error, exits 2.
#
# Configuration is settle.env beside this file. See settle.env.example.

set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/.." && pwd)
ENV_FILE=$HERE/settle.env

if [[ ! -f $ENV_FILE ]]; then
  echo "SETTLE status=skipped reason=settle.env-missing" >&2
  exit 2
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${TV_ADDR:?TV_ADDR is empty in settle.env}"
: "${BIND_HOST:?BIND_HOST is empty in settle.env}"
: "${SDB_BIN:?SDB_BIN is empty in settle.env}"
: "${TIZENPWN:?TIZENPWN is empty in settle.env}"
TV_PORT=${TV_PORT:-26101}

STATE_DIR=${XDG_STATE_HOME:-$HOME/.local/state}/tv-debloat-settle
LOG_FILE=$STATE_DIR/settle.log
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"

# Print from this process. Piping each line into tee makes a short-lived
# process per line, and a journal often keeps only the last of those.
record() {
  local stamped
  stamped="$(date -u '+%Y-%m-%dT%H:%M:%SZ') ${1}"
  printf '%s\n' "$stamped" >>"$LOG_FILE"
  printf '%s\n' "$stamped"
}

if [[ ! -f $REPO/scripts/tv_debloat.py || ! -f $SDB_BIN ]]; then
  record "SETTLE status=skipped reason=script-or-sdb-missing"
  exit 2
fi

# Do not open SDB when the developer port is closed. A dark TV is not a failure.
if ! timeout 3 bash -c "echo >/dev/tcp/${TV_ADDR}/${TV_PORT}" 2>/dev/null; then
  record "SETTLE status=off"
  exit 0
fi

set +e
report=$(python3 "$REPO/scripts/tv_debloat.py" settle \
  --tv "$TV_ADDR" \
  --sdb "$SDB_BIN" \
  --bind-host "$BIND_HOST" \
  --tizenpwn "$TIZENPWN" 2>&1)
rc=$?
set -e

# The last line is the result, with the disable counts first.
# already + newly equals required when nothing is still listed.
if [[ -n ${report// } ]]; then
  while IFS= read -r line; do
    record "$line"
  done <<< "$report"
else
  record "SETTLE status=empty exit=${rc}"
fi

# Exit 1 means an id is still listed after the attempt. The next timer run
# tries again. Exit 2 means the command could not run.
if [[ $rc -eq 2 ]]; then
  exit 2
fi
exit 0
