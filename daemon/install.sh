#!/usr/bin/env bash
# Install the user timer that re-applies the debloat lists.
#
# Run this on the computer that can reach the television, after
# daemon/settle.env exists. It writes user systemd units under
# ~/.config/systemd/user and enables the timer. It does not print the
# addresses in settle.env.

set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_FILE=$HERE/settle.env
SCRIPT=$HERE/tv-debloat-settle.sh
UNIT_DIR=${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user

if [[ ! -f $ENV_FILE ]]; then
  echo "Copy daemon/settle.env.example to daemon/settle.env and set the four paths." >&2
  exit 1
fi
if [[ ! -x $SCRIPT ]]; then
  chmod 755 "$SCRIPT"
fi

mkdir -p "$UNIT_DIR"
python3 - "$HERE/tv-debloat-settle.service" "$UNIT_DIR/tv-debloat-settle.service" "$SCRIPT" << 'PY'
import pathlib, sys
src, dest, script = sys.argv[1:]
text = pathlib.Path(src).read_text()
if "@SETTLE_SCRIPT@" not in text:
    raise SystemExit("service file is missing @SETTLE_SCRIPT@")
pathlib.Path(dest).write_text(text.replace("@SETTLE_SCRIPT@", script))
PY
cp "$HERE/tv-debloat-settle.timer" "$UNIT_DIR/tv-debloat-settle.timer"

systemctl --user daemon-reload
systemctl --user enable --now tv-debloat-settle.timer
echo "Timer enabled. Log: ${XDG_STATE_HOME:-$HOME/.local/state}/tv-debloat-settle/settle.log"
echo "A user timer stops at logout unless linger is on: loginctl enable-linger \"\$USER\""
