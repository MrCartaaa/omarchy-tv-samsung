#!/usr/bin/env python3
"""Check or deactivate the ad, ACR, analytics, and Pisa packages on this TV.

The set this was written for is a Samsung UN43TU7000FXZC running firmware
T-KTSU2AKUC-2743.0 (build T-KTSU2AKUC-REL-202607021959), Tizen 5.5.

check
    Read the app list over SDB. No root and no Remote PC session. Exit 0 when
    every id in packages.txt is absent and every id in kept.txt is still
    present. Exit 1 when a listed id is still present or a kept id is missing.
    Exit 2 when the TV cannot be read.

deactivate
    One-shot root through rackrot/tizenpwn's reviewed TU7000 CIFS route.
    The click runs pkgcmd -D, which deactivates a package and leaves its
    files on disk. This script does not call pkgcmd -u.

On this firmware, pkgcmd -D without -t is rejected as an invalid argument.
The form that returned ok is:

    pkgcmd -D -t tpk -n <id> --global

When that fails, the script tries -t app. adplatform.ADPlayer is an app id
inside the package named adplatform, so that package name is deactivated too.

The tpk progress callback on this image prints val[uninstall] for -D. That
word is the callback label. The install directory stayed in place, and the
id left the app list. Turn one back on with:

    pkgcmd -A -t tpk -n <id> --global

com.samsung.tv.coba.adagent is its own package (CoBA Advertise.dll). The
other com.samsung.tv.coba.* packages are Home, Source, Apps, Search,
Settings, and Live TV. They are in kept.txt and are not deactivated.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TV = "<tv-ip>"
DEFAULT_SDB = Path.home() / "local/tv-tools/sdb/data/tools/sdb"
DEFAULT_TIZENPWN = Path.home() / "local/tv-tools/tizenpwn"
DEFAULT_BIND = "<pc-ip>"
RESULT_LOG = "/home/owner/share/tmp/debloat-result"

# Applist id -> extra package name that does not appear as its own app id.
PACKAGE_ALIASES = {"adplatform.ADPlayer": "adplatform"}


def load_ids(path: Path) -> tuple[str, ...]:
    """Return ids from a line-oriented list. Comments and blanks are skipped."""
    ids: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            ids.append(line)
    if not ids:
        raise SystemExit(f"{path} has no package ids")
    return tuple(ids)


def quoted_fields(line: str) -> list[str]:
    """Return the single-quoted fields on one applist row."""
    fields: list[str] = []
    rest = line
    while "'" in rest:
        _, _, rest = rest.partition("'")
        value, sep, rest = rest.partition("'")
        if not sep:
            break
        fields.append(value)
    return fields


def connect_and_applist(sdb: Path, tv: str) -> str:
    """Return `sdb shell 0 applist` text. Connect first if the serial is missing."""
    serial = f"{tv}:26101"
    listed = subprocess.run(
        [str(sdb), "devices"],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if serial not in listed.stdout:
        subprocess.run(
            [str(sdb), "connect", serial],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    result = subprocess.run(
        [str(sdb), "-s", serial, "shell", "0", "applist"],
        check=False,
        capture_output=True,
        text=True,
        timeout=40,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = (result.stderr or result.stdout or "empty applist").strip()
        raise RuntimeError(detail)
    return result.stdout


def present_ids(applist: str) -> set[str]:
    """Collect the app-id field from each applist row."""
    found: set[str] = set()
    for line in applist.splitlines():
        fields = quoted_fields(line)
        if len(fields) >= 2:
            found.add(fields[-1])
    return found


def cmd_check(sdb: Path, tv: str, packages: tuple[str, ...], kept: tuple[str, ...]) -> int:
    """Print one CHECK line per id. Return 1 when the desired state is wrong."""
    try:
        found = present_ids(connect_and_applist(sdb, tv))
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as error:
        print(f"CHECK tv={tv} status=unreachable error={error}")
        return 2
    problems = 0
    for pkg in packages:
        status = "present" if pkg in found else "absent"
        if status == "present":
            problems += 1
        print(f"CHECK list=deactivate id={pkg} status={status}")
    for pkg in kept:
        status = "present" if pkg in found else "absent"
        if status == "absent":
            problems += 1
        print(f"CHECK list=kept id={pkg} status={status}")
    print(
        f"SUMMARY tv={tv} deactivate={len(packages)} kept={len(kept)} "
        f"problems={problems}"
    )
    return 1 if problems else 0


def deactivate_prefix(packages: tuple[str, ...]) -> str:
    """Shell that runs on the TV, as root, when Shared Folder is clicked.

    The commands are in this script rather than in `cifs command --command`
    because this set can emit two NetrShareEnum calls for one click. The
    stock checker then returns before it would send --command. The click
    still executes the staged file.
    """
    lines = [
        f"log={RESULT_LOG}",
        "umask 022",
        'printf "\\nBEGIN %s\\n" "$(/usr/bin/id)" >> "$log"',
        'if [ -x /usr/bin/pkgcmd ]; then PKG=/usr/bin/pkgcmd; else PKG=pkgcmd; fi',
        'printf "PKGCMD %s\\n" "$PKG" >> "$log"',
    ]
    extra: list[str] = []
    for pkg in packages:
        lines.append(f'printf "PKG {pkg}\\n" >> "$log"')
        # Stop a running instance first. -k does not uninstall the package.
        lines.append(f'"$PKG" -k -n {pkg} >> "$log" 2>&1')
        lines.append(f'printf "KILL {pkg} %s\\n" "$?" >> "$log"')
        lines.append(f'"$PKG" -D -t tpk -n {pkg} --global >> "$log" 2>&1')
        lines.append("st=$?")
        lines.append(f'printf "EXIT tpk {pkg} %s\\n" "$st" >> "$log"')
        lines.append(
            f'if [ "$st" -ne 0 ]; then "$PKG" -D -t app -n {pkg} --global >> "$log" 2>&1; '
            f'printf "EXIT app {pkg} %s\\n" "$?" >> "$log"; fi'
        )
        alias = PACKAGE_ALIASES.get(pkg)
        if alias and alias not in extra:
            extra.append(alias)
    for alias in extra:
        lines.append(f'printf "PKG {alias}\\n" >> "$log"')
        lines.append(f'"$PKG" -D -t tpk -n {alias} --global >> "$log" 2>&1')
        lines.append(f'printf "EXIT tpk {alias} %s\\n" "$?" >> "$log"')
    lines.append('printf "END\\n" >> "$log"')
    lines.append('chmod 644 "$log" 2>/dev/null || true')
    return "\n".join(lines) + "\n"


def cmd_deactivate(args: argparse.Namespace, packages: tuple[str, ...]) -> int:
    """Stage the deactivate script and run one tizenpwn cifs command."""
    if not sys.stdin.isatty():
        print(
            "deactivate needs a terminal so you can type CONNECTED and CLICKED.",
            file=sys.stderr,
        )
        print(
            "From an assistant session, run scripts/supervise.py instead.",
            file=sys.stderr,
        )
        return 2
    source = args.tizenpwn / "src"
    if not (source / "tizenpwn" / "tu7000.py").is_file():
        print(f"tizenpwn source not found at {source}", file=sys.stderr)
        return 2
    os.environ["SDB"] = str(args.sdb)
    sys.path.insert(0, str(source))
    import tizenpwn.tu7000 as tu
    from tizenpwn.sdb import SdbClient, SdbError

    original = tu.agent_code

    def patched(identity, callback_host: str, callback_port: int) -> str:
        # pkgcmd runs first. The original agent then connects back so the
        # host can cat the result log when the share-listing check passes.
        return deactivate_prefix(packages) + original(
            identity, callback_host, callback_port
        )

    tu.agent_code = patched
    try:
        client = SdbClient(tu.find_sdb(), args.tv, timeout=20)
        client.connect()
        client.inject(f"/bin/rm -f {RESULT_LOG}", timeout=20)
    except (SdbError, OSError) as error:
        print(f"LOG_CLEAR_SKIPPED {error}", flush=True)
    try:
        evidence = tu.execute_command(
            args.tv,
            confirm=tu.CONFIRMATION,
            accept_saved_profile=True,
            commands=(f"cat {RESULT_LOG}",),
            callback_host=args.bind_host,
            bind_host=args.bind_host,
            accept_timeout=args.accept_timeout,
            agent_timeout=args.agent_timeout,
        )
    except tu.CifsRouteError as error:
        print(f"ROUTE_ERROR {error}", flush=True)
        return 2
    print("EVIDENCE_OK")
    print(f"uid={evidence.get('uid')}")
    print(f"classification={evidence.get('classification')}")
    output = evidence.get("command_output") or evidence.get("output") or ""
    if isinstance(output, str) and output:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    # Shared flags sit on each subcommand so `check --tv … --sdb …` works.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tv", default=DEFAULT_TV, help="TV LAN address")
    common.add_argument("--sdb", type=Path, default=DEFAULT_SDB, help="path to sdb")
    common.add_argument(
        "--packages",
        type=Path,
        default=ROOT / "packages.txt",
        help="ids to deactivate",
    )
    common.add_argument(
        "--kept",
        type=Path,
        default=ROOT / "kept.txt",
        help="ids that must remain listed",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("check", parents=[common], help="read the app list and report each id")
    off = sub.add_parser(
        "deactivate",
        parents=[common],
        help="one-shot root deactivate",
    )
    off.add_argument("--tizenpwn", type=Path, default=DEFAULT_TIZENPWN)
    off.add_argument("--bind-host", default=DEFAULT_BIND)
    off.add_argument("--accept-timeout", type=int, default=1200)
    off.add_argument("--agent-timeout", type=int, default=180)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    packages = load_ids(args.packages)
    kept = load_ids(args.kept)
    if not args.sdb.is_file():
        print(f"sdb not found at {args.sdb}", file=sys.stderr)
        return 2
    if args.action == "check":
        return cmd_check(args.sdb, args.tv, packages, kept)
    return cmd_deactivate(args, packages)


if __name__ == "__main__":
    raise SystemExit(main())
