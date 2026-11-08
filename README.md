# UN43TU7000FXZC debloat

Notes and scripts for one Samsung UN43TU7000FXZC (2020 7 Series, 43-inch) running firmware `T-KTSU2AKUC-2743.0`. The work takes ad, ACR, analytics, and Pisa packages off the app list, including the home-screen ad package `com.samsung.tv.coba.adagent`.

The operation is **deactivate** (`pkgcmd -D`). It is not uninstall (`pkgcmd -u`). Deactivate leaves the install directory on disk. The same id can be turned back on with `pkgcmd -A`. There is no package backup on this TV, so this repository does not uninstall `org.tizen.*` or `com.samsung.*` packages.

A firmware update, Smart Hub reset, or factory reset can put the preloaded packages back. After any of those, run the check again.

## The television

| Field | Value |
| --- | --- |
| Model | UN43TU7000FXZC |
| Name | [TV] Samsung 7 Series (43) |
| Year | 2020 |
| Platform | 20_KANTSU2_UHD_BASIC |
| Firmware label | T-KTSU2AKUC-2743.0 |
| Build id | T-KTSU2AKUC-REL-202607021959 |
| Tizen | 5.5.0, armv7l |
| Kernel | 4.1.10 |
| SDB | 4.2.36, serial `UN43TU7000FXZC`, port 26101 |
| DUID | <duid> |
| Wired MAC | <wired-mac> |

`sdb capability` on this image reports `sdbd_rootperm: disabled`, `intershell: disabled`, `rootonoff_support: disabled`, and `pkgcmd_debugmode: enabled`. `sdb shell id` and `sdb shell 0 pkgcmd -l` return empty. `sdb shell 0 applist` works and is the check this repo uses.

On the network where this was done, the TV was `<tv-ip>` and the developer-mode host was `<pc-ip>`. Those are private addresses for that LAN. Another network uses its own addresses. Developer mode must list the PC that opens SDB, and the CIFS lab must bind that same PC address.

## What left the app list

Checked with `scripts/tv_debloat.py check` against `sdb shell 0 applist`. Install directories were still present after deactivate.

| Id | Role | Result on this TV |
| --- | --- | --- |
| `com.samsung.tv.adplayer` | Ad player | deactivated, directory kept |
| `adplatform.ADPlayer` | Ad player app | deactivated. The package name is `adplatform`, which was deactivated as well |
| `com.samsung.tv.ad-web-framework` | Ad web framework | deactivated, directory kept |
| `com.samsung.tv.adagent-service` | Ad agent service | deactivated. It is an app inside `com.samsung.tv.pisa-service` |
| `org.tizen.acr-service-app` | ACR | deactivated, directory kept |
| `com.samsung.tv.canalysis-service` | Channel analysis | deactivated, directory kept |
| `com.samsung.tizen.samsung-analytics` | Samsung analytics | deactivated, directory kept |
| `com.samsung.tv.pisa-service` | Pisa | deactivated, directory kept |
| `org.tizen.pisa-control-service` | Pisa control | direct `pkgcmd` returned exit 25. The id then left the app list with `pisa-service` |
| `com.samsung.tv.vd-sc-client-service` | Viewing-data client | deactivated, directory kept |
| `com.samsung.tv.coba.adagent` | Home-screen ad library (`Com.Samsung.TV.CoBA.Advertise.dll`) | deactivated. Its own package. Directory `/opt/usr/apps/com.samsung.tv.coba.adagent` kept |

`com.samsung.tv.coba.adagent` is the only CoBA package in the deactivate list. Home, Source, Apps, Search, Settings, and Live TV are separate packages and stay listed. See `kept.txt`.

One store package was uninstalled earlier, and only that one: `WykOS4t4F0` (`WykOS4t4F0.cmsWebApp`) via `sdb uninstall`. That is not what `packages.txt` does.

## What stays

Streaming apps, the store, the browser, DRM, and Privacy Choices stay. So do `com.samsung.tv.coba.home`, `com.samsung.tv.coba.source`, `com.samsung.tv.coba.apps`, `com.samsung.tv.coba.search`, `com.samsung.tv.coba.setting`, and `com.samsung.tv.coba.livetv`.

Do not apply an S90C profile, `s90c.json`, or a script that uninstalls every `com.samsung.*` id. Do not flash firmware.

## Repositories this work depends on

| Repository | What it is for here | Commit or version used |
| --- | --- | --- |
| [rackrot/tizenpwn](https://github.com/rackrot/tizenpwn) | The root route that worked. Remote PC plus the TV's privileged CIFS helper runs one bounded root command. | `d62f8bcc5759a97dc00b630a52a0e788bb957bd1` |
| [chris-ritsen/samsung-tv-root](https://github.com/chris-ritsen/samsung-tv-root) | Tried first, from its QUICKSTART. `doctor` was Ready. `archive-root` stopped because `/usr/bin/dotnet` has no `SETGID` or `SYS_ADMIN` capability. | release `0.0.12` |
| Samsung SDB | `applist` and the tizenpwn transport. | `4.2.36` ubuntu-64 |
| [DemonKingSwarn/samsung-tv-tizen-root](https://github.com/DemonKingSwarn/samsung-tv-tizen-root) `docs/DEBLOAT.md` | The idea of `pkgcmd -D` instead of uninstall. Written for a Tizen 9 QA55, not this image. | docs only, not that repo's apply script |
| [ardazeytin/samsung-tizen-tv-debloat](https://github.com/ardazeytin/samsung-tizen-tv-debloat) | The constraint against `sdb uninstall` of `org.tizen.*` and `com.samsung.*`. | not applied as a profile |
| [piermark/omarchytv](https://github.com/piermark/omarchytv) | Not installed. See [docs/omarchytv.md](docs/omarchytv.md). | `v2.14.0-beta` inspected, not downloaded |

`tizenpwn` as published accepts `UN65TU7000FXZA` only. This 43-inch set uses the same build id, and the four reviewed helper files matched that commit's hashes:

- `/usr/apps/privileged-service/bin/mount.smb.sh`
- `/usr/apps/privileged-service/bin/ps_agent`
- `/usr/apps/org.tizen.remotepc/bin/remotepc_rdp`
- `/usr/apps/org.tizen.remotepc/bin/remotepc_uilauncher`

`patches/tizenpwn-un43-allowlist.patch` adds `UN43TU7000FXZC` when those checks still pass. Apply it to a checkout of `d62f8bc`. Do not point this patch at a later commit without reading the context.

Issue [chris-ritsen/samsung-tv-root#40](https://github.com/chris-ritsen/samsung-tv-root/issues/40) is the same archive-root failure on a EU TU7000 (`UE55TU7092`, `T-KTSU2DEUC`). No public issue found for debloat of `UN43TU7000FXZC` / `T-KTSU2AKUC`.

These do not apply to this television: CleanYourTV, TV Detox, and DumbTV (Android and Fire TV), and `invaliddayta/samsung-tv-tools` `s90c.json`.

`tizenpwn` persistence notes and its JS SSH service are for a different set. They were not deployed. This TV does not keep a root listener.

## pkgcmd on this firmware

`pkgcmd -h` on the TV shows:

```text
pkgcmd -D -t <pkg type> -n <pkgid> (--global) (--uid <uid>)
```

`pkgcmd -D -n <id>` with no `-t` returns `Invalid argument [-2]` and changes nothing. `--global` is required so the deactivate is not limited to the root user. `-k -n <id>` stops a running instance and does not uninstall it.

Success for a tpk is exit 0 and `key[end] val[ok]`. The start callback's `val[uninstall]` is the progress label this `pkgcmd` prints for `-D`. Confirm with the app list and with the directory under `/opt/usr/apps` or `/usr/apps`.

Re-enable one id:

```text
pkgcmd -A -t tpk -n <id> --global
```

Use `-t app` when the id is an app inside another package. That restore has not been run on this TV.

## Check the list

From this repository, with SDB able to see the TV:

```bash
python3 scripts/tv_debloat.py check
```

Defaults are this LAN: TV `<tv-ip>`, SDB `~/local/tv-tools/sdb/data/tools/sdb`. Override them when the addresses differ:

```bash
python3 scripts/tv_debloat.py check --tv <tv-ip> --sdb /path/to/sdb
```

The command prints one line per id. `list=deactivate` should be `absent`. `list=kept` should be `present`. Exit 0 means that is true. Exit 1 means a deactivated id came back or a kept id disappeared. Exit 2 means the app list could not be read.

The PC in this lab also runs `~/.config/bash_custom/scripts/telemetry-probe.sh` once a day. That script calls this check and records the lines. A TV that is off does not fail the PC job.

## Repeat a deactivate

Do this only while you are at the TV. One click. Deactivate is still a root action.

1. Developer mode is on, and its host is this PC's LAN address.
2. `sdb connect <tv>:26101` shows the serial `UN43TU7000FXZC`.
3. Apply `patches/tizenpwn-un43-allowlist.patch` to tizenpwn `d62f8bc`.
4. Confirm the read-only preflight:

```bash
python3 -m tizenpwn --sdb /path/to/sdb cifs preflight <tv-ip>
```

`Compatibility: tested` is the expected line. `dotnet lacks effective SETGID/SYS_ADMIN` is the archive-root failure. Do not retry archive-root with `--runtime`.

5. Free TCP `3389` and `445` on the developer-host address. On this PC a Windows container (`local-container`) was publishing `3389`, and it had to be stopped for the lab and started again afterward. Binding `445` needs a process that may bind privileged ports. `tizenpwn` starts that lab in Docker.
6. Allow inbound TCP from the TV to the PC. A default-deny firewall drops the SDB callback and the root agent's connection.
7. In a terminal:

```bash
python3 scripts/tv_debloat.py deactivate \
  --tv <tv-ip> \
  --bind-host <pc-lan-ip> \
  --sdb /path/to/sdb \
  --tizenpwn /path/to/tizenpwn
```

8. The tool prints a one-time Remote PC form. On the TV: **Source → Remote Access → Remote PC**. Protocol **RDP**, not VNC. Type the password exactly, including `$`, quotes, and `$(`. The on-screen keyboard drops those characters. Leave persistent certificate trust unchecked. Do not run the password in a shell on the PC.
9. When the window titled `tizenpwn disposable RDP lab` is up, type `CONNECTED`.
10. Move a USB mouse to the physical top edge of the picture until the thin bar appears. The remote cannot open that bar. Click **Shared Folder** once. Type `CLICKED`. If the window closes, do not click again.
11. Delete that temporary Remote PC profile when the session ends.
12. Run `python3 scripts/tv_debloat.py check` and look at the Home screen.

This set has emitted two SMB share listings for one click, about six seconds apart. `tizenpwn` accepts the click only when it sees exactly one new listing. The deactivate commands are inside the script the click runs, so they do not depend on that check. `scripts/session/arm-click.sh` sends `CLICKED` on the first new listing so the check can still pass. A person at the keyboard can type `CLICKED` as soon as they have clicked once.

`scripts/supervise.py` is the same prompt with a pseudo-terminal and a gate file. It is how a session without its own keyboard drives `CONNECTED` and `CLICKED`. Append those words to `/tmp/un43tu7000-gate`. Do not replace the file mid-session.

## Layout

```text
packages.txt                 ids to deactivate, including coba.adagent
kept.txt                     Home and the other screens that must stay listed
scripts/tv_debloat.py        check and deactivate
scripts/supervise.py         terminal gate for an unattended session
scripts/session/watch-login.sh
scripts/session/arm-click.sh
patches/tizenpwn-un43-allowlist.patch
docs/omarchytv.md            not installed; Tizen 5.5 still needs a build
```

OmarchyTV is the next piece of work and is not part of the deactivate command. The notes for a backwards-compatible build are in [docs/omarchytv.md](docs/omarchytv.md).
