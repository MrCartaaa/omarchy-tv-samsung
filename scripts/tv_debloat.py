#!/usr/bin/env python3
"""Check, deactivate, or uninstall packages on this TV.

The set this was written for is a Samsung UN43TU7000FXZC running firmware
T-KTSU2AKUC-2743.0 (build T-KTSU2AKUC-REL-202607021959), Tizen 5.5.

check
    Read the app list over SDB. No root and no Remote PC session. Exit 0 when
    every id in packages.txt and removed.txt is absent and every id in
    kept.txt is still present. Exit 1 when a listed id is still present or a
    kept id is missing. Exit 2 when the TV cannot be read.

deactivate
    One-shot root through rackrot/tizenpwn's reviewed TU7000 CIFS route.
    The click runs pkgcmd -D for packages.txt only. Deactivate leaves the
    install directory on disk.

remove
    Uninstall each package named in removed.txt with pkgcmd -u. No Remote PC
    session. The developer user can run pkgcmd -u for these ids. A package
    that is already gone is left alone, and the command then runs check.

settle
    The command a boot cycle can run from this PC. No Remote PC session.
    Read the app list. When the TV is off, exit 0. When every targeted id is
    already absent, exit 0 without running pkgcmd. When a boot has listed
    one again, deactivate that packages.txt id and uninstall that removed.txt
    package as the developer user, then run check. org.tizen.tv-viewer is
    refused. It is the picture.

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
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
RESULT_LOG = "/home/owner/share/tmp/debloat-result"


def _untracked_env() -> dict[str, str]:
    """Read gitignored local.env. Addresses stay on this computer."""
    path = ROOT / "local.env"
    found: dict[str, str] = {}
    if not path.is_file():
        return found
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        found[key.strip()] = value.strip().strip("\"'")
    return found


_LOCAL = _untracked_env()


def _pick(*names: str) -> str | None:
    for name in names:
        chosen = os.environ.get(name) or _LOCAL.get(name)
        if chosen:
            return chosen
    return None


def _path_pick(*names: str) -> Path | None:
    chosen = _pick(*names)
    if not chosen:
        return None
    return Path(chosen)


# Applist id -> extra package name that does not appear as its own app id.
PACKAGE_ALIASES = {"adplatform.ADPlayer": "adplatform"}

_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_KINDS = {"tpk", "wgt"}


@dataclass(frozen=True)
class Removal:
    """One applist id, the package pkgcmd -u must name, and that package's type."""

    app_id: str
    package_id: str
    kind: str


def load_ids(path: Path) -> tuple[str, ...]:
    """Return ids from a line-oriented list. Comments and blanks are skipped."""
    ids: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            ids.append(line)
    if not ids:
        raise SystemExit(f"{path} has no package ids")
    odd = [pkg for pkg in ids if not _ID.fullmatch(pkg)]
    if odd:
        raise SystemExit(f"{path} has an id that is not a package id: {odd[0]}")
    return tuple(ids)


def load_removals(path: Path) -> tuple[Removal, ...]:
    """Return uninstall rows. Each data line is `applist-id package-id tpk|wgt`."""
    rows: list[Removal] = []
    kinds: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 3 or parts[2] not in _KINDS:
            raise SystemExit(
                f"{path}:{number}: expected 'applist-id package-id tpk|wgt'"
            )
        app_id, package_id, kind = parts
        if not _ID.fullmatch(app_id) or not _ID.fullmatch(package_id):
            raise SystemExit(f"{path}:{number}: id has unexpected characters")
        previous = kinds.get(package_id)
        if previous is not None and previous != kind:
            raise SystemExit(
                f"{path}:{number}: {package_id} is listed as both {previous} and {kind}"
            )
        kinds[package_id] = kind
        rows.append(Removal(app_id, package_id, kind))
    if not rows:
        raise SystemExit(f"{path} has no package ids")
    return tuple(rows)


def uninstall_groups(rows: tuple[Removal, ...]) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """One pkgcmd -u per package, with every applist id that package contains."""
    order: list[str] = []
    apps: dict[str, list[str]] = {}
    kinds: dict[str, str] = {}
    for row in rows:
        if row.package_id not in apps:
            order.append(row.package_id)
            apps[row.package_id] = []
            kinds[row.package_id] = row.kind
        if row.app_id not in apps[row.package_id]:
            apps[row.package_id].append(row.app_id)
    return tuple((pkg, kinds[pkg], tuple(apps[pkg])) for pkg in order)


def uninstall_shell(package: str, kind: str, app_ids: tuple[str, ...]) -> str:
    """Remote pkgcmd -u. The caller writes this to a file and sources it.

    A direct SDB injection of this text is closed by this TV. Pushing the
    file and sourcing it is the path that returns the pkgcmd result.
    """
    kills = "; ".join(f"pkgcmd -k -n {app_id} >/dev/null 2>&1" for app_id in app_ids)
    return (
        f"{kills}; pkgcmd -u -t {kind} -n {package} --global >/tmp/pkg-one.txt 2>&1; "
        f"echo {package}:$?; tail -c 180 /tmp/pkg-one.txt"
    )


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


def cmd_check(
    sdb: Path,
    tv: str,
    packages: tuple[str, ...],
    kept: tuple[str, ...],
    removals: tuple[Removal, ...],
) -> int:
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
    for row in removals:
        status = "present" if row.app_id in found else "absent"
        if status == "present":
            problems += 1
        print(f"CHECK list=remove id={row.app_id} status={status}")
    for pkg in kept:
        status = "present" if pkg in found else "absent"
        if status == "absent":
            problems += 1
        print(f"CHECK list=kept id={pkg} status={status}")
    print(
        f"SUMMARY tv={tv} deactivate={len(packages)} remove={len(removals)} "
        f"kept={len(kept)} problems={problems}"
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


def capture_staged(client, command: str, bind: str, timeout: int = 60):
    """Push a script, then source it. Direct injection of pkgcmd -u is closed."""
    token = os.urandom(8).hex()
    remote = PurePosixPath(f"/home/owner/share/tmp/sdk_tools/.un43-remove-{token}.sh")
    with tempfile.TemporaryDirectory(prefix="un43-remove-") as directory:
        local = Path(directory) / "remove.sh"
        local.write_text(f"{command}\nrm -f {remote}\n", encoding="utf-8")
        client.push(local, remote)
    return client.capture(
        f". {remote}",
        callback_host=bind,
        bind_host=bind,
        timeout=timeout,
    )


def deactivate_shell(package: str) -> str:
    """Remote pkgcmd -D for one id. Try tpk, then app. Stop it first."""
    return (
        f"pkgcmd -k -n {package} >/dev/null 2>&1 || true; "
        f"pkgcmd -D -t tpk -n {package} --global >/tmp/pkg-one.txt 2>&1; "
        f"st=$?; "
        f"if [ \"$st\" -ne 0 ]; then pkgcmd -D -t app -n {package} --global "
        f">/tmp/pkg-one.txt 2>&1; st=$?; fi; "
        f"echo DEACTIVATE {package}:$st; tail -c 160 /tmp/pkg-one.txt; echo"
    )


def cmd_settle(
    args: argparse.Namespace,
    packages: tuple[str, ...],
    kept: tuple[str, ...],
    removals: tuple[Removal, ...],
) -> int:
    """Re-apply the lists as the developer user. A powered-off TV exits 0.

    Only ids that the app list shows are sent to pkgcmd. A clean list does
    not open a package-command session.
    """
    if "org.tizen.tv-viewer" in packages or any(
        row.app_id == "org.tizen.tv-viewer" or row.package_id == "org.tizen.tv-viewer"
        for row in removals
    ):
        print("refusing: org.tizen.tv-viewer is the picture", file=sys.stderr)
        return 2
    try:
        found = present_ids(connect_and_applist(args.sdb, args.tv))
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as error:
        print(f"SETTLE tv={args.tv} status=off error={error}")
        return 0
    back = [pkg for pkg in packages if pkg in found]
    aliases = [
        alias
        for pkg, alias in PACKAGE_ALIASES.items()
        if pkg in found and alias not in back
    ]
    groups = [
        group
        for group in uninstall_groups(removals)
        if any(app_id in found for app_id in group[2])
    ]
    if not back and not aliases and not groups:
        print(f"SETTLE tv={args.tv} status=clean")
        return 0
    source = args.tizenpwn / "src"
    if not (source / "tizenpwn" / "sdb.py").is_file():
        print(f"tizenpwn source not found at {source}", file=sys.stderr)
        return 2
    os.environ["SDB"] = str(args.sdb)
    sys.path.insert(0, str(source))
    from tizenpwn.sdb import SdbClient, SdbError

    parts = [deactivate_shell(pkg) for pkg in back]
    parts.extend(deactivate_shell(alias) for alias in aliases)
    parts.extend(uninstall_shell(pkg, kind, app_ids) for pkg, kind, app_ids in groups)
    print(
        f"SETTLE tv={args.tv} status=apply deactivate={','.join(back) or '-'} "
        f"remove={','.join(group[0] for group in groups) or '-'}",
        flush=True,
    )
    try:
        client = SdbClient(args.sdb, args.tv, timeout=30)
        client.connect()
        result = capture_staged(client, "\n".join(parts) + "\n", args.bind_host, timeout=120)
    except (SdbError, OSError) as error:
        print(f"SETTLE tv={args.tv} status=error error={error}")
        return 2
    print(result.output.strip(), flush=True)
    return cmd_check(args.sdb, args.tv, packages, kept, removals)


def cmd_remove(args: argparse.Namespace, removals: tuple[Removal, ...], packages: tuple[str, ...], kept: tuple[str, ...]) -> int:
    """Uninstall removed.txt as the developer user, then check the app list.

    pkgcmd -u of a package that is already absent returns an error and does
    not reinstall it. The check after the attempts is the result that matters.
    """
    source = args.tizenpwn / "src"
    if not (source / "tizenpwn" / "sdb.py").is_file():
        print(f"tizenpwn source not found at {source}", file=sys.stderr)
        return 2
    os.environ["SDB"] = str(args.sdb)
    sys.path.insert(0, str(source))
    from tizenpwn.sdb import SdbClient, SdbError

    try:
        client = SdbClient(args.sdb, args.tv, timeout=20)
        client.connect()
    except (SdbError, OSError) as error:
        print(f"REMOVE tv={args.tv} status=unreachable error={error}")
        return 2
    failed = 0
    for package, kind, app_ids in uninstall_groups(removals):
        print(f"REMOVE package={package} type={kind} apps={','.join(app_ids)}", flush=True)
        result = None
        error = None
        # This image sometimes closes the first injection while a package
        # command is still finishing. One retry is the same command.
        for _attempt in (1, 2):
            try:
                result = capture_staged(
                    client,
                    uninstall_shell(package, kind, app_ids),
                    args.bind_host,
                )
                error = None
                break
            except SdbError as caught:
                error = caught
                time.sleep(1)
        if error is not None or result is None:
            failed += 1
            print(f"REMOVE package={package} status=error error={error}", flush=True)
            continue
        print(result.output.strip(), flush=True)
    code = cmd_check(args.sdb, args.tv, packages, kept, removals)
    if code != 0:
        return code
    return 2 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    # Shared flags sit on each subcommand so `check --tv … --sdb …` works.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tv", default=_pick("TV_ADDR"), help="TV LAN address")
    common.add_argument("--sdb", type=Path, default=_path_pick("SDB_BIN"), help="path to sdb")
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
    common.add_argument(
        "--removed",
        type=Path,
        default=ROOT / "removed.txt",
        help="applist ids to uninstall",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("check", parents=[common], help="read the app list and report each id")
    off = sub.add_parser(
        "deactivate",
        parents=[common],
        help="one-shot root deactivate of packages.txt",
    )
    off.add_argument("--tizenpwn", type=Path, default=_path_pick("TIZENPWN"))
    off.add_argument("--bind-host", default=_pick("BIND_HOST"))
    off.add_argument("--accept-timeout", type=int, default=1200)
    off.add_argument("--agent-timeout", type=int, default=180)
    uninstall = sub.add_parser(
        "remove",
        parents=[common],
        help="uninstall removed.txt as the developer user",
    )
    uninstall.add_argument("--tizenpwn", type=Path, default=_path_pick("TIZENPWN"))
    uninstall.add_argument("--bind-host", default=_pick("BIND_HOST"))
    settle = sub.add_parser(
        "settle",
        parents=[common],
        help="re-disable packages a boot listed again, as the developer user",
    )
    settle.add_argument("--tizenpwn", type=Path, default=_path_pick("TIZENPWN"))
    settle.add_argument("--bind-host", default=_pick("BIND_HOST"))
    return parser


def list_conflicts(
    packages: tuple[str, ...],
    kept: tuple[str, ...],
    removals: tuple[Removal, ...],
) -> list[str]:
    """Refuse a list that asks for two operations on one id, or touches a kept id."""
    problems: list[str] = []
    kept_ids = set(kept)
    package_ids = set(packages)
    both = [pkg for pkg in packages if pkg in kept_ids]
    if both:
        problems.append("in packages.txt and kept.txt: " + ", ".join(both))
    for row in removals:
        named = {row.app_id, row.package_id}
        if named & kept_ids:
            problems.append(f"removed id is kept: {row.app_id}")
        if named & package_ids:
            problems.append(f"removed id is also in packages.txt: {row.app_id}")
    return problems


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.tv or args.sdb is None:
        print("pass --tv and --sdb", file=sys.stderr)
        return 2
    if args.action != "check" and (not args.bind_host or args.tizenpwn is None):
        print("pass --bind-host and --tizenpwn", file=sys.stderr)
        return 2
    packages = load_ids(args.packages)
    kept = load_ids(args.kept)
    removals = load_removals(args.removed)
    if not args.sdb.is_file():
        print(f"sdb not found at {args.sdb}", file=sys.stderr)
        return 2
    conflicts = list_conflicts(packages, kept, removals)
    if conflicts:
        print("refusing: " + "; ".join(conflicts), file=sys.stderr)
        return 2
    if args.action == "check":
        return cmd_check(args.sdb, args.tv, packages, kept, removals)
    if args.action == "remove":
        return cmd_remove(args, removals, packages, kept)
    if args.action == "settle":
        return cmd_settle(args, packages, kept, removals)
    return cmd_deactivate(args, packages)


if __name__ == "__main__":
    raise SystemExit(main())
