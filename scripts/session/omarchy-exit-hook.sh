#!/bin/sh
# Raise the running OmarchyTV process once when Exit opens the live picture.
#
# On this set, Exit focuses org.tizen.tv-viewer. Samsung TV Plus can focus
# com.samsung.tv.tvplus instead. Either focus is the signal. The launch is:
#
#   aul_test launch OmarchyTV0.OmarchyTV omarchy_nav home
#
# On a process that is already running, that keeps the same pid. The page
# reads omarchy_nav=home and moves to the dock (workspace 0).
#
# Launch once per visit. While the picture stays focused, further polls must
# not call aul_test again. A launch on every tick suspends whatever was in
# front, and a streaming app can come back stuck on its loading page.
#
# "Nobody focused" is not Exit. Volume can leave Netflix or Spotify visible
# with no focused app. This script does not look at those apps.
#
# The physical Home key is Linux code 63 (KEY_F5) on this remote. The
# platform consumes it before /dev/input sees it, so this script does not
# read input devices. Those readers never saw a physical Home press, and
# dd from a dead parent was left behind. Mapping Home is a separate edit of
# /usr/share/enlightenment/data/config/tizen-tv/module.keyrouter.cfg, which
# is root-owned on a read-only filesystem.
#
# This file is not a signed executable. UEP rejects `sh this-file`. Source
# it, and close fd 3 so an sdb callback socket is not inherited:
#
#   setsid sh -c '. /home/owner/share/tmp/sdk_tools/omarchy-exit-hook.sh' \
#     </dev/null >/tmp/omarchy-exit-hook.log 2>&1 3>&- &
#
# Start it by hand after each power-on. It does not survive a power cycle.
APP=OmarchyTV0.OmarchyTV
VIEWER=org.tizen.tv-viewer
PLUS=com.samsung.tv.tvplus
LOG=/tmp/omarchy-exit-hook.log
LOCK=/tmp/omarchy-exit-hook.pid

if [ -f "$LOCK" ]; then
  old=$(cat "$LOCK" 2>/dev/null)
  if [ -n "$old" ] && kill -0 "$old" 2>/dev/null; then
    echo "already running pid $old" >>"$LOG"
    exit 0
  fi
fi
echo $$ >"$LOCK"
trap 'rm -f "$LOCK"' EXIT INT TERM

# One aul_test get_status. Return 0 when that app is the focused one.
focused() {
  aul_test get_status "$1" 2>/dev/null | grep -q STATUS_FOCUS
}

# Picture focus is a visit. Raise Omarchy on the rising edge only.
# front_held stays 1 until both picture apps have given up focus, so a
# failed or slow launch cannot be retried every poll.
front_held=0
echo "watch pid $$" >>"$LOG"
while :; do
  if focused "$VIEWER" || focused "$PLUS"; then
    if [ "$front_held" -eq 0 ]; then
      front_held=1
      if focused "$APP"; then
        echo "picture focused; omarchy already focused" >>"$LOG"
      else
        echo "picture focused; raise once" >>"$LOG"
        aul_test launch "$APP" omarchy_nav home >>"$LOG" 2>&1
      fi
    fi
  else
    if [ "$front_held" -eq 1 ]; then
      echo "picture released" >>"$LOG"
    fi
    front_held=0
  fi
  sleep 2
done
