#!/usr/bin/env python3
"""Run scripts/tv_debloat.py deactivate on a pseudo-terminal.

tizenpwn's Remote PC prompt refuses to continue unless stdin is a terminal,
and it asks for two exact lines: CONNECTED, then CLICKED. This wrapper gives
the tool a terminal and forwards new text appended to the gate file.

A person at a keyboard does not need this. Run tv_debloat.py deactivate in
a terminal and type the two words when asked.

Gate file: /tmp/un43tu7000-gate
    Append "CONNECTED\\n" only after the TV has opened the lab window.
    Append "CLICKED\\n" only after one Shared Folder click.
    Do not replace the file while a session is running. This process sends
    only the newly appended suffix.

Log: /tmp/un43tu7000-session.log
"""

from __future__ import annotations

import os
import select
import sys
from pathlib import Path

LOG = Path("/tmp/un43tu7000-session.log")
GATE = Path("/tmp/un43tu7000-gate")
PID = Path("/tmp/un43tu7000-session.pid")
DEBLOAT = Path(__file__).resolve().parent / "tv_debloat.py"


def main() -> int:
    LOG.write_bytes(b"")
    GATE.write_text("")
    os.chmod(LOG, 0o600)
    os.chmod(GATE, 0o600)
    master, slave = os.openpty()
    pid = os.fork()
    if pid == 0:
        os.close(master)
        os.setsid()
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        if slave > 2:
            os.close(slave)
        os.execv(
            sys.executable,
            [sys.executable, str(DEBLOAT), "deactivate", *sys.argv[1:]],
        )
    os.close(slave)
    PID.write_text(str(pid))
    os.chmod(PID, 0o600)
    sent = ""
    with LOG.open("ab", buffering=0) as log:
        while True:
            readable, _, _ = select.select([master], [], [], 0.2)
            if readable:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    data = b""
                if not data:
                    break
                log.write(data)
            current = GATE.read_text() if GATE.exists() else ""
            if current.startswith(sent) and len(current) > len(sent):
                extra = current[len(sent) :]
                sent = current
                os.write(master, extra.encode())
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited == pid:
                while True:
                    readable, _, _ = select.select([master], [], [], 0.2)
                    if not readable:
                        break
                    try:
                        data = os.read(master, 65536)
                    except OSError:
                        break
                    if not data:
                        break
                    log.write(data)
                return os.waitstatus_to_exitcode(status)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
