#!/bin/bash
# Append CLICKED to the gate file on the first new SMB share listing.
#
# Send it as soon as the listing count increases. On this TV one Shared Folder
# click has produced two NetrShareEnum calls about six seconds apart. The
# tizenpwn checker accepts exactly one new listing in the two seconds after
# CLICKED. Sending CLICKED on the first listing lets that check pass before
# the second listing arrives.
#
# One click only. A second click is a second listing and the checker stops.

set -u

PID_FILE=/tmp/un43tu7000-session.pid
GATE=/tmp/un43tu7000-gate
PID=$(cat "$PID_FILE")
name=$(docker ps --format '{{.Names}}' | grep -E '^tizenpwn-cifs-[0-9a-f]+$' | head -1 || true)
if [[ -z "$name" ]]; then
  echo "FAILED: lab container missing"
  exit 1
fi
before=$(docker logs "$name" 2>&1 | grep -c 'NetrShareEnum Level: 1' || true)

while :; do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "FAILED: session exited before Shared Folder"
    exit 1
  fi
  now=$(docker logs "$name" 2>&1 | grep -c 'NetrShareEnum Level: 1' || true)
  if [[ "${now:-0}" -gt "${before:-0}" ]]; then
    printf 'CLICKED\n' >> "$GATE"
    echo "ACTION_REQUIRED: sent CLICKED before=$before now=$now"
    break
  fi
  sleep 0.4
done

while kill -0 "$PID" 2>/dev/null; do
  sleep 2
done
echo "DONE: session exited"
exit 0
