#!/bin/sh
# Raise the running OmarchyTV process once when Exit opens the live picture.
#
# On this set, Exit resumes org.tizen.tv-viewer. Samsung TV Plus then tunes a
# channel on that picture. aul_test get_status stays STATUS_BG while that
# channel is up, so a focus poll never sees the visit and the picture stays
# on screen. The scenario log names the visible app as soon as it changes:
#
#   [FG:org.tizen.tv-viewer]
#   [FG:com.samsung.tv.tvplus]
#
# The Samsung TV Plus button on this remote opens the guide, org.tizen.epg,
# and leaves it there. That id is not the Exit picture. Without it in this
# list the set stayed on the guide until a power cycle. Power-on still opens
# org.tizen.tv-viewer, and this script still raises once for that picture.
# A visit that moves from the guide to the picture does not launch again.
#
# The first such line of a visit runs:
#
#   aul_test launch OmarchyTV0.OmarchyTV omarchy_nav home
#
# On a process that is already running, that keeps the same pid. The page
# reads omarchy_nav=home and moves to the dock (workspace 0).
#
# Launch once per visit. Another line for the same picture must not launch
# again. A launch on every line suspends whatever was in front, and a
# streaming app can come back stuck on its loading page.
#
# Netflix, Spotify, and Omarchy itself are not a visit. Volume can leave
# those apps visible with no focused app. A line that does not name the
# picture is ignored.
#
# The physical Home key is Linux code 63 (KEY_F5) on this remote. The
# platform consumes it before /dev/input sees it, so this script does not
# read input devices. Mapping Home is a separate edit of
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
LOG=/tmp/omarchy-exit-hook.log
LOCK=/tmp/omarchy-exit-hook.pid
FG=/tmp/omarchy-fg.txt
CHUNK=/tmp/omarchy-fg.chunk
STATE=/tmp/omarchy-fg.state

if [ -f "$LOCK" ]; then
  old=$(cat "$LOCK" 2>/dev/null)
  if [ -n "$old" ] && kill -0 "$old" 2>/dev/null; then
    echo "already running pid $old" >>"$LOG"
    exit 0
  fi
fi
echo $$ >"$LOCK"

stamp() {
  date '+%H:%M:%S'
}

# wc on this image pads its count. Arithmetic rejects the spaces.
count_of() {
  n=$(wc "$1" <"$2" 2>/dev/null | tr -d ' \n')
  case $n in
    ''|*[!0-9]*) n=0 ;;
  esac
  printf '%s' "$n"
}

cleanup() {
  if [ -n "$dlog_pid" ]; then
    kill "$dlog_pid" 2>/dev/null
  fi
  rm -f "$LOCK" "$CHUNK"
}
trap cleanup EXIT INT TERM

# One scenario follower. The ring buffer is replayed into the file first.
# Skip those bytes so an old visit does not raise the app at startup.
: >"$FG"
dlogutil -v time SCENARIO_MGR_TV:I '*:S' >"$FG" 2>>"$LOG" 3>&- &
dlog_pid=$!

# The replay is the bytes already in the file once its size sits still.
# An empty file is not the replay. Leaving the offset at 0 made the next
# burst, including an old guide line, count as a new visit.
last=-1
stable=0
i=0
while [ "$stable" -lt 2 ]; do
  if ! kill -0 "$dlog_pid" 2>/dev/null; then
    : >"$FG"
    dlogutil -v time SCENARIO_MGR_TV:I '*:S' >"$FG" 2>>"$LOG" 3>&- &
    dlog_pid=$!
    last=-1
    stable=0
  fi
  size=$(count_of -c "$FG" || echo 0)
  if [ "$size" = "$last" ] && [ "$size" -gt 0 ]; then
    stable=$((stable + 1))
  else
    stable=0
    last=$size
  fi
  i=$((i + 1))
  [ "$i" -ge 80 ] && break
  sleep 0.3
done
offset=$(count_of -c "$FG" || echo 0)
echo "$(stamp) watch pid $$ scenario $dlog_pid skip $offset" >>"$LOG"
printf '%s\n' "0" >"$STATE"
rest=""
WORK=/tmp/omarchy-fg.work
LINES=/tmp/omarchy-fg.lines

picture() {
  case $1 in
    *org.tizen.tv-viewer*|*com.samsung.tv.tvplus*|*com.samsung.tv.tvPlus*|*org.tizen.epg*)
      return 0
      ;;
  esac
  return 1
}

take_lines() {
  # Keep the bytes in files. A command substitution would drop a trailing newline.
  printf '%s' "$rest" >"$WORK"
  cat "$CHUNK" >>"$WORK"
  if [ ! -s "$WORK" ]; then
    : >"$LINES"
    return
  fi
  if tail -c 1 "$WORK" | grep -q .; then
    rest=$(tail -n 1 "$WORK")
    count=$(count_of -l "$WORK")
    head -n "$count" "$WORK" >"$LINES"
  else
    rest=""
    cat "$WORK" >"$LINES"
  fi
}

while :; do
  if ! kill -0 "$dlog_pid" 2>/dev/null; then
    echo "$(stamp) scenario log stopped; start again" >>"$LOG"
    : >"$FG"
    dlogutil -v time SCENARIO_MGR_TV:I '*:S' >"$FG" 2>>"$LOG" 3>&- &
    dlog_pid=$!
    offset=0
    rest=""
    sleep 0.5
    offset=$(count_of -c "$FG" || echo 0)
  fi

  size=$(count_of -c "$FG" || echo 0)
  if [ "$size" -lt "$offset" ]; then
    offset=0
    rest=""
  fi
  if [ "$size" -le "$offset" ]; then
    sleep 0.25
    continue
  fi

  dd if="$FG" bs=1 skip="$offset" count=$((size - offset)) 2>/dev/null >"$CHUNK"
  offset=$size
  take_lines
  while IFS= read -r line; do
    case $line in
      *'[FG:'*) ;;
      *) continue ;;
    esac
    fg=${line#*'[FG:'}
    fg=${fg%%']'*}
    held=$(cat "$STATE" 2>/dev/null || echo 0)
    if picture "$fg"; then
      if [ "$held" -eq 0 ]; then
        echo 1 >"$STATE"
        echo "$(stamp) picture $fg; raise once" >>"$LOG"
        aul_test launch "$APP" omarchy_nav home >>"$LOG" 2>&1
      fi
    elif [ "$held" -eq 1 ]; then
      echo 0 >"$STATE"
      echo "$(stamp) picture released $fg" >>"$LOG"
    fi
  done <"$LINES"
  sleep 0.25
done
