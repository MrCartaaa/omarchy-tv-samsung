# PC daemon

The debloat lists do not stick on their own. A boot of this television can list the turned-off packages again, and it can copy the AirPlay preload back. The set has no timer that turns them off. A computer on the same network has to run `settle` while that computer is on.

`settle` is `python3 scripts/tv_debloat.py settle`. It reads the app list as the developer user. The television being off is a success. A list that is already clean does not run `pkgcmd`. An id that came back is deactivated, or uninstalled when it is in `removed.txt`. `org.tizen.tv-viewer` is refused. It is the picture. This job does not start the Exit hook. Source [scripts/session/omarchy-exit-hook.sh](../scripts/session/omarchy-exit-hook.sh) on the television after each power-on.

## What you need

- Developer mode on the television, pointed at this computer.
- Samsung's `sdb` binary on this computer.
- A checkout of [rackrot/tizenpwn](https://github.com/rackrot/tizenpwn) at the commit named in the main README. `settle` imports that checkout's SDB client only when a package has come back.
- This clone, with `packages.txt`, `removed.txt`, and `kept.txt` as you want them applied.

## Install

From the clone:

```bash
cp daemon/settle.env.example daemon/settle.env
```

Edit `daemon/settle.env`. `TV_ADDR` is the television. `BIND_HOST` is this computer's LAN address, the same one developer mode lists. `SDB_BIN` is the `sdb` binary. `TIZENPWN` is the tizenpwn checkout. `daemon/settle.env` is gitignored so those addresses stay on this computer.

```bash
daemon/install.sh
```

That writes user units to `~/.config/systemd/user/`, fills in the path of `daemon/tv-debloat-settle.sh`, and enables `tv-debloat-settle.timer`. The timer waits two minutes after boot, then runs every five minutes. One missed run is made up after the computer was off.

The log is `~/.local/state/tv-debloat-settle/settle.log` (or `$XDG_STATE_HOME/tv-debloat-settle/settle.log`).

A user timer stops when you log out. On a machine that should keep the lists applied with nobody logged in:

```bash
loginctl enable-linger "$USER"
```

## What a run means

`status=off` means the developer port did not open. The television is off or developer mode is not accepting this computer. `status=clean` means nothing had come back. `status=apply` means `pkgcmd` ran for the ids that were listed. Exit 2 from the service means `sdb`, tizenpwn, or the callback failed. An id that is still listed after the attempt is logged, the service exits 0, and the next run tries again.

Check the timer:

```bash
systemctl --user status tv-debloat-settle.timer
systemctl --user start tv-debloat-settle.service
```
