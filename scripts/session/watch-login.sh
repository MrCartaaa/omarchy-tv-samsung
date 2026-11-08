#!/bin/bash
# Watch the disposable Remote PC lab for a new TV login or a rejected password.
#
# A person sitting at a terminal does not need this. It exists so a session
# that cannot see the TV can notice "login successful" or AUTHFAIL and then
# append CONNECTED to the gate file itself.
#
# The lab's own self-test already produces one successful login and one
# AUTHFAIL. This script records that baseline and reports only a later change.
# The xrdp_wm_log_msg duplicate line is not counted. The counted line is:
#   [INFO ] login successful for user owner on display <number>

set -u

PID_FILE=/tmp/un43tu7000-session.pid
if [[ ! -f "$PID_FILE" ]]; then
  echo "FAILED: no session pid at $PID_FILE"
  exit 1
fi
PID=$(cat "$PID_FILE")
base_logins=
base_fails=

while :; do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "FAILED: session exited before a new RDP login"
    exit 1
  fi
  name=$(docker ps --format '{{.Names}}' | grep -E '^tizenpwn-cifs-[0-9a-f]+$' | head -1 || true)
  if [[ -n "$name" ]]; then
    logs=$(docker exec "$name" /usr/bin/tail -c 262144 /var/log/xrdp.log /var/log/xrdp-sesman.log 2>/dev/null || true)
    logins=$(printf '%s\n' "$logs" | grep -Ec '\[INFO \] login successful for user owner on display [0-9]+$' || true)
    fails=$(printf '%s\n' "$logs" | grep -c 'AUTHFAIL: user=owner' || true)
    if [[ -z "$base_logins" ]]; then
      base_logins=$logins
      base_fails=$fails
    elif [[ "${fails:-0}" -gt "${base_fails:-0}" ]]; then
      echo "ACTION_REQUIRED: password rejected container=$name authfail=$fails"
      exit 0
    elif [[ "${logins:-0}" -gt "${base_logins:-0}" ]]; then
      echo "ACTION_REQUIRED: RDP login ready container=$name logins=$logins"
      exit 0
    fi
  fi
  sleep 5
done
