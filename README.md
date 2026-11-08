# UN43TU7000FXZC debloat

This is a write-up of one Samsung television and the scripts that put it in the state described here. The set is a 2020 7 Series, 43 inches, model code UN43TU7000FXZC. It runs Tizen 5.5, which is Samsung's smart-TV system, on firmware `T-KTSU2AKUC-2743.0`.

Out of the box the set shows Samsung's own screens, plays ads around them, and keeps background programs that recognize what is on screen and report usage. The work on this TV turned those programs off, removed AirPlay, and installed a different front page called OmarchyTV. Netflix, Spotify, Prime Video, and the Samsung app store stayed.

Nothing here flashes new firmware. The step that needs root is one click at the TV, from a PC. No root program was left running on the set.

## The lists do not stick by themselves

Turning a package off on this set is not permanent. A boot can list those packages again, and it can copy the AirPlay preload back. The television has no daemon that turns them off. A computer on the same network has to keep running the timer in [daemon/](daemon/README.md). While that computer is off, a boot can bring the packages back, and they stay until the computer is on again and the timer runs. Setup is [Keep the lists from a PC](#keep-the-lists-from-a-pc).

## What you will see on the TV

OmarchyTV is the front page. Its dock is three tiles: Netflix, Spotify, and Prime Video. The top-right corner opens this set's own Bluetooth, Internet, network, and volume screens.

Exit, from a show or from live TV, comes back to that dock. The OmarchyTV process was already running. The remote's Samsung TV Plus button opens Samsung's guide, and the same path brings the dock back. The volume rocker changes the volume and leaves you in the show. On the dock it changes the volume and the page stays still.

A few things are still the stock TV. The physical Home button, pressed inside Netflix, does not open the dock. The Source button does not open OmarchyTV's second page. Power-on still shows Samsung's picture for a moment before the dock. If OmarchyTV crashes, nothing starts it again. Those rows are marked open in [Where the work stands](#where-the-work-stands).

## On this page

- [The lists do not stick by themselves](#the-lists-do-not-stick-by-themselves) is why a computer has to keep the timer running.
- [What you will see on the TV](#what-you-will-see-on-the-tv) is the result, without the package names.
- [If you are going to run this](#if-you-are-going-to-run-this) is the short path, with the files each step uses.
- [Deactivate, do not uninstall](#deactivate-do-not-uninstall) is the safety rule for the lists below.
- [Where the work stands](#where-the-work-stands) is the scorecard: done, partial, and still open.
- [The television](#the-television) is the model and the firmware.
- [What left the app list](#what-left-the-app-list) is every id that was turned off or removed, and why.
- [What stays](#what-stays) is Netflix, Spotify, Prime Video, the store, and the Samsung menus that have to remain.
- [Repositories this work depends on](#repositories-this-work-depends-on) is the other projects, and the commit that was actually used.
- [pkgcmd on this firmware](#pkgcmd-on-this-firmware) is how this Tizen version turns a package off.
- [Check the list](#check-the-list) reads the TV and compares it with the files in this repo.
- [Remove AirPlay](#remove-airplay) uninstalls AirPlay.
- [Keep the lists from a PC](#keep-the-lists-from-a-pc) is the timer that puts the lists back after a boot. The files are in [daemon/](daemon/README.md).
- [Repeat a deactivate](#repeat-a-deactivate) is the one-time root click, done at the TV.
- [Layout](#layout) is the file tree.
- [docs/omarchytv.md](docs/omarchytv.md) is the home-screen install: the certificate, the widget patch, Exit, and the volume rocker.

## If you are going to run this

Confirm the model code on the TV before you run anything. A different Samsung year or size is a different firmware, and these lists were checked on this image only.

1. Read [The television](#the-television) and match the model and the firmware label.
2. Read [Deactivate, do not uninstall](#deactivate-do-not-uninstall). The turn-off list is [packages.txt](packages.txt). The delete list is [removed.txt](removed.txt), and it is AirPlay only. The keep list is [kept.txt](kept.txt).
3. Connect a PC with Samsung's SDB tool. [Check the list](#check-the-list) is `python3 scripts/tv_debloat.py check --tv <tv-ip> --sdb /path/to/sdb`. It only reads. The television's address and this computer's address stay on that computer.
4. The first turn-off needs someone at the TV. Follow [Repeat a deactivate](#repeat-a-deactivate). The root tool is [rackrot/tizenpwn](https://github.com/rackrot/tizenpwn) plus [patches/tizenpwn-un43-allowlist.patch](patches/tizenpwn-un43-allowlist.patch), which adds this 43-inch model to a tool that otherwise names the 65-inch only.
5. Install the home screen from [docs/omarchytv.md](docs/omarchytv.md). The widget changes are [patches/omarchytv-un43.patch](patches/omarchytv-un43.patch). The certificate is created for that TV and is not in this repository.
6. After each power-on, source [scripts/session/omarchy-exit-hook.sh](scripts/session/omarchy-exit-hook.sh) once. That script is what sends Exit and the TV Plus button back to the dock, and what ignores the volume rocker. A second source leaves the running copy in place. The PC timer does not start this script.
7. Install the PC timer in [Keep the lists from a PC](#keep-the-lists-from-a-pc). Without it, the next boot can put the turned-off packages back.

## Keep the lists from a PC

The timer runs on a computer, not on the television. It calls `python3 scripts/tv_debloat.py settle` every five minutes while that computer is on. `settle` reads the app list. An id that came back is deactivated, or uninstalled when it is AirPlay. A clean list does not run `pkgcmd`. The television being off is a success. There is no Remote PC click.

On the computer:

1. Install Samsung's `sdb`, and clone [rackrot/tizenpwn](https://github.com/rackrot/tizenpwn) at the commit in [Repositories this work depends on](#repositories-this-work-depends-on).
2. Turn on developer mode on the television and set its host to this computer's LAN address.
3. From this clone, copy [daemon/settle.env.example](daemon/settle.env.example) to `daemon/settle.env`. Set `TV_ADDR` to the television, `BIND_HOST` to this computer, `SDB_BIN` to the `sdb` binary, and `TIZENPWN` to that checkout. `daemon/settle.env` is not committed.
4. Run [daemon/install.sh](daemon/install.sh). It installs a user systemd timer and enables it.
5. If the computer should keep the lists applied with nobody logged in, run `loginctl enable-linger "$USER"`.

The log is under `~/.local/state/tv-debloat-settle/`. File by file notes are in [daemon/README.md](daemon/README.md).

## Deactivate, do not uninstall

Most of the cleanup turns a package off. It does not delete it.

[packages.txt](packages.txt) is **deactivate** (`pkgcmd -D`). Deactivate leaves the install directory on disk. The same id can be turned back on with `pkgcmd -A`. There is no package backup on this TV, so that list does not uninstall `org.tizen.*` or `com.samsung.*` packages. Those names are Samsung's own system. Deleting one of them can take the picture or the menus with it, and the way back is a factory reset or a USB firmware reflash.

[removed.txt](removed.txt) is **uninstall** (`pkgcmd -u`). AirPlay is the only group on that list. Deactivate left it on disk, and a boot listed the native package again. The Apple AirPlay widget is not a preload. `com.samsung.tv.airplay-app` is a removable preload, so a later boot may copy that one package back. `python3 scripts/tv_debloat.py remove` uninstalls the list again. It does not uninstall the rest of `com.samsung.*`.

The picture itself is `org.tizen.tv-viewer`. It stays. Exit works by noticing that picture and bringing OmarchyTV forward. Removing the picture removes the screen.

A firmware update, Smart Hub reset, or factory reset can put the preloaded packages back. After any of those, run the check again.

## Where the work stands

Someone with this same model can follow this repository and reach the result this set has today. Open rows are still open on this television.

| Goal | Result |
| --- | --- |
| Root this model without flashing firmware | Met. One Remote PC click runs one root command through [rackrot/tizenpwn](https://github.com/rackrot/tizenpwn) and `patches/tizenpwn-un43-allowlist.patch`. No root listener is left behind. |
| Take ads, ACR, analytics, Pisa, and `com.samsung.tv.coba.adagent` off the app list, and keep Netflix, Spotify, Prime Video, the store, the CoBA shells, and the picture | Met. `packages.txt` is deactivate. `kept.txt` is the keep list. A boot can list some deactivated ids again. `check`, then `deactivate` while you are at the TV, clears them. |
| Delete AirPlay, including after a boot brings the preload back | Met. `removed.txt` and `python3 scripts/tv_debloat.py remove`. The Apple web app is not a preload. `com.samsung.tv.airplay-app` is, so a later boot may copy that package back. Run `remove` again when `check` shows it. |
| Install OmarchyTV as a normal app | Met. App id `OmarchyTV0.OmarchyTV`. Signing uses a Samsung certificate for that TV's own DUID. The certificate is not in this repository. |
| Boot into OmarchyTV and skip the Samsung page | Partial. `db/first_screen/type` is `OmarchyTV0.OmarchyTV`. The tile page `com.samsung.tv.csfs` is deactivated. Firmware still rewrites `db/appfw/booting_appid_backup` to `org.tizen.tv-viewer`, so the picture still appears. The sideloaded widget is not in the Apps grid. |
| Exit and Return land on the OmarchyTV dock without restarting the process | Exit from the live picture raises the same pid to workspace 0. [scripts/session/omarchy-exit-hook.sh](scripts/session/omarchy-exit-hook.sh) follows the scenario log, because Samsung TV Plus stays `STATUS_BG` while its channel is on screen. It raises when the line is only the picture or the guide. Volume while Netflix or another app is open keeps that app on the line. Volume on the dock keeps OmarchyTV on the line. Those lines do not raise. Return and Back do that while OmarchyTV itself is in front. Source the hook once after every power-on. A second source leaves the running copy in place. |
| The Samsung TV Plus button returns to OmarchyTV | The button opens `org.tizen.epg` and leaves it there. The same hook raises once for that guide, then waits until the visit ends. Power-on, power-off, and the Exit picture path are unchanged. A guide visit that continues into the picture does not launch a second time. |
| The dock uses the upstream OmarchyTV tiles for Netflix, Spotify, and Prime Video | The Tizen build was replacing those tiles with Samsung store icons. The dock is the three upstream wordmark tiles, in that order. Disney+, Plex, YouTube, and the other upstream tiles stay in the source list and are not on this dock. |
| Home from Netflix opens the OmarchyTV dock | Open. The physical Home key is Linux code 63 and the platform consumes it. The change is a root edit of `module.keyrouter.cfg` while someone is at the TV. |
| Source opens OmarchyTV page 2 | Open. Page 2 is workspace index 1, the TV and HDMI page. The remote Source key is not mapped. The Inputs icon inside the app already switches to that workspace. |
| Bluetooth, Internet, network and Wi-Fi, and Volume on the top right | Met on this set, and in `patches/omarchytv-un43.patch`. The four screens are `org.tizen.btaudiolist`, `com.samsung.tv.knox-browser` (the app labeled Internet), `org.tizen.NetworkSetting-Tizen` (network and Wi-Fi), and `org.tizen.volume-setting`. |
| A crash relaunches OmarchyTV at most twice, then leaves the picture up | Open. No watcher does that. |

Spotify sitting on its loading page was the picture, and then AirPlay, covering a process that was still running. Spotify stays installed. AirPlay is on the uninstall list, and the Exit hook launches once per visit.

The volume rocker stays in the app that is already open. On this set it inserts `org.tizen.tv-viewer` beside Netflix, Spotify, Prime Video, or whatever else is in front, and the scenario stays that app. The same press on the OmarchyTV dock inserts the picture beside `OmarchyTV0.OmarchyTV`. [scripts/session/omarchy-exit-hook.sh](scripts/session/omarchy-exit-hook.sh) ignores both lines. Exit is the next line, the picture with that app gone. Launching on the dock line redraws the page that is already up.

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

`sdb capability` on this image reports `sdbd_rootperm: disabled`, `intershell: disabled`, `rootonoff_support: disabled`, and `pkgcmd_debugmode: enabled`. `sdb shell id` and `sdb shell 0 pkgcmd -l` return empty. `sdb shell 0 applist` works and is the check this repo uses.

Developer mode must list the PC that opens SDB, and the CIFS lab must bind that same PC address. This repository does not record the television's address, the computer's address, the wired MAC, or the DUID. A certificate is created for the television you are signing, and that certificate stays on the computer.

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
| `org.tizen.rm-survey` | Remote-management survey | deactivated, directory kept |
| `com.samsung.tv.preview-downloader` | Preview download | deactivated, directory kept |
| `com.samsung.tv.preview-updater` | Preview update | deactivated, directory kept |
| `com.samsung.tv.contents-recognition-dbmgr` | Content-recognition database | deactivated, directory kept |
| `NRi6kdBYJ0.AirPlayWebApp` | Apple AirPlay web app, package `NRi6kdBYJ0`, type `wgt` | uninstalled. In `removed.txt`. Directory removed |
| `com.samsung.tv.airplay-app` | AirPlay app, type `tpk` | uninstalled. In `removed.txt`. Removable preload, so a boot may copy it back |
| `com.samsung.tv.airplay-service` | AirPlay service inside `com.samsung.tv.airplay-app` | uninstalled with that package. Listed in `removed.txt` so check sees it |
| `com.samsung.tv.context-aware-agent` | Context-aware agent | deactivated, directory kept |
| `com.samsung.tv.slive-daemon` | Samsung TV Plus daemon | deactivated. The picture is `org.tizen.tv-viewer`, which stays |
| `org.tizen.hbbtv` | HbbTV | deactivated, directory kept |
| `org.tizen.hbbtv-service` | HbbTV service | deactivated, directory kept |
| `ug-hbbtv-efl` | HbbTV UI | deactivated, directory kept |
| `com.samsung.tv.csfs` | Samsung tile home | deactivated. `com.samsung.tv.coba.home` stays |

`com.samsung.tv.coba.adagent` is the only CoBA package in the deactivate list. Home, Source, Apps, Search, Settings, and Live TV are separate packages and stay listed. See `kept.txt`.

A power cycle can list some of these ids again. On 2026-11-08 it listed the ad packages, `com.samsung.tv.airplay-app`, and `com.samsung.tv.slive-daemon`. `pkgcmd -D -t tpk -n <id> --global` as the developer user turned them off again, with no Remote PC click. `com.samsung.tv.adagent-service` and `org.tizen.pisa-control-service` returned exit 25 on their own and left the list with `pisa-service`. Run `python3 scripts/tv_debloat.py check` after a later boot. `com.samsung.tv.preview-downloader` stayed off, and a caller still tries to launch it about every 5 seconds. The launch fails.

One store package was uninstalled earlier, and it is not in either list: `WykOS4t4F0` (`WykOS4t4F0.cmsWebApp`) via `sdb uninstall`. AirPlay is the uninstall list. See `removed.txt`.

## What stays

The default apps stay, and they are named in `kept.txt`: `org.tizen.netflix-app`, `rJeHak5zRg.Spotify`, `rJeHak5zRg.SpotifyService`, `org.tizen.primevideo`, and `com.samsung.tv.store`. The store stays so more apps can be installed. That is a default, not a required removal. The browser, DRM, and Privacy Choices stay. So do `com.samsung.tv.coba.home`, `com.samsung.tv.coba.source`, `com.samsung.tv.coba.apps`, `com.samsung.tv.coba.search`, `com.samsung.tv.coba.setting`, and `com.samsung.tv.coba.livetv`. `org.tizen.tv-viewer` stays. It is the picture.

Do not apply an S90C profile, `s90c.json`, or a script that uninstalls every `com.samsung.*` id. Do not flash firmware.

## Repositories this work depends on

| Repository | What it is for here | Commit or version used |
| --- | --- | --- |
| [rackrot/tizenpwn](https://github.com/rackrot/tizenpwn) | The root route that worked. Remote PC plus the TV's privileged CIFS helper runs one bounded root command. | `d62f8bcc5759a97dc00b630a52a0e788bb957bd1` |
| [chris-ritsen/samsung-tv-root](https://github.com/chris-ritsen/samsung-tv-root) | Tried first, from its QUICKSTART. `doctor` was Ready. `archive-root` stopped because `/usr/bin/dotnet` has no `SETGID` or `SYS_ADMIN` capability. | release `0.0.12` |
| Samsung SDB | `applist` and the tizenpwn transport. | `4.2.36` ubuntu-64 |
| [DemonKingSwarn/samsung-tv-tizen-root](https://github.com/DemonKingSwarn/samsung-tv-tizen-root) `docs/DEBLOAT.md` | The idea of `pkgcmd -D` instead of uninstall. Written for a Tizen 9 QA55, not this image. | docs only, not that repo's apply script |
| [ardazeytin/samsung-tizen-tv-debloat](https://github.com/ardazeytin/samsung-tizen-tv-debloat) | The constraint against `sdb uninstall` of `org.tizen.*` and `com.samsung.*`. | not applied as a profile |
| [piermark/omarchytv](https://github.com/piermark/omarchytv) | Installed as a normal app. See [docs/omarchytv.md](docs/omarchytv.md). | `v2.14.0-beta`, signed locally |

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

Use `-t app` when the id is an app inside another package. Netflix, Spotify, Prime Video, and the store were turned back on with `pkgcmd -A` after a mistaken deactivate. The ids in `packages.txt` have not been restored.

## Check the list

From this repository, with SDB able to see the TV:

```bash
python3 scripts/tv_debloat.py check --tv <tv-ip> --sdb /path/to/sdb
```

There is no default address in the script. Copy [local.env.example](local.env.example) to `local.env` if you want `TV_ADDR`, `BIND_HOST`, `SDB_BIN`, and `TIZENPWN` filled in on a computer you use yourself. `local.env` is gitignored. Do not commit it.

The command prints one line per id. `list=deactivate` and `list=remove` should be `absent`. `list=kept` should be `present`. Exit 0 means that is true. Exit 1 means a removed or deactivated id came back, or a kept id disappeared. Exit 2 means the app list could not be read.

## Remove AirPlay

No Remote PC session. Developer mode has to name this PC. The command runs `pkgcmd -u` as the developer user for each package in `removed.txt`, then runs the same check:

```bash
python3 scripts/tv_debloat.py remove
```

A package that is already gone makes `pkgcmd -u` print an error and does not come back from that command. The check after it is the result. Run it again when a boot has copied the AirPlay preload back and `check` reports that id present.

A boot can list the deactivated ids and the AirPlay preload again. The timer in [daemon/](daemon/README.md) runs `settle` and puts them back. `org.tizen.tv-viewer` is refused. It is the picture. One run by hand, with the same flags the timer uses:

```bash
python3 scripts/tv_debloat.py settle --tv <tv-ip> --sdb /path/to/sdb --bind-host <pc-ip> --tizenpwn /path/to/tizenpwn
```

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

5. Free TCP `3389` and `445` on the developer-host address. A process already listening on `3389` has to be stopped for the lab and started again afterward. Binding `445` needs a process that may bind privileged ports. `tizenpwn` starts that lab in Docker.
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
removed.txt                  AirPlay ids to uninstall
kept.txt                     Home and the other screens that must stay listed
scripts/tv_debloat.py        check, deactivate, remove, and settle
local.env.example            optional local addresses, copied to gitignored local.env
scripts/supervise.py         terminal gate for an unattended session
scripts/session/watch-login.sh
scripts/session/arm-click.sh
scripts/session/omarchy-exit-hook.sh
daemon/                      PC timer that re-applies the lists after a boot
daemon/settle.env.example    addresses and tool paths, copied to settle.env
daemon/install.sh            installs the user systemd timer
patches/tizenpwn-un43-allowlist.patch
patches/omarchytv-un43.patch    top-right bar, Exit stays in the same process
docs/omarchytv.md            install notes, the widget patch, and the Exit hook
```

OmarchyTV is installed as app id `OmarchyTV0.OmarchyTV`. It is not part of the deactivate command. `db/first_screen/type` is `OmarchyTV0.OmarchyTV`. The tile page `com.samsung.tv.csfs` is deactivated, so there is no Samsung tile home, and this sideloaded widget does not appear in the Apps grid. Exit from the live picture raises the same OmarchyTV process. The hook that does that is [scripts/session/omarchy-exit-hook.sh](scripts/session/omarchy-exit-hook.sh). It has to be sourced after each power-on. The physical Home key is still taken by the platform before that script can see it. Another set of this model builds the same widget from [docs/omarchytv.md](docs/omarchytv.md) and `patches/omarchytv-un43.patch`. Certificates and the built widget stay off this repository.
