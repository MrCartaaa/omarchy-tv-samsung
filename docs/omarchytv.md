# OmarchyTV on this UN43TU7000

Installed as a normal app. Exit from the live picture raises this same process. The physical Home key does not.

Upstream is [piermark/omarchytv](https://github.com/piermark/omarchytv). The build installed on this TV is `v2.14.0-beta` plus [patches/omarchytv-un43.patch](../patches/omarchytv-un43.patch).

## What was installed

- The published package is an HTML5 widget, package `OmarchyTV0`, app id `OmarchyTV0.OmarchyTV`, `required_version` 2.3, public privileges. It does not take the Home key.
- The GitHub release file `OmarchyTV-tizen-2.14.0-unsigned.wgt` was downloaded. Its SHA-256 is `5d12bd2ad82098d674f0217d61d71adfb5dda62c0e996b04b337b2282a30977c`, which matches the release table. `tizen/INSTALL-TIZEN.md` prints a different hash, `5916dd07d8e20ec1fa78dd8f927dc63283d2899257a27c0eca4a91c79a391174`, and that hash is not this file.
- The unsigned widget was refused with `Check certificate error [-12]`. A Samsung public author and distributor certificate for this television's DUID was created in a local signing profile. Those certificate files stay on the PC and are not in this repository.
- Tizen Studio 6.0 CLI signed the unpacked widget with `tizen package -t wgt -s <profile>`. The certificate chain checked out as privilege level `PUBLIC`.
- `pkgcmd -i -t wgt -p <file>` without `--global` copied the app under `/var/lib/empty/apps_rw` and failed with `Security error [-22]` (`Unexpected path` in `security_registration.cc`). The SDB command user on this set has that empty home. `pkgcmd -i -t wgt -p <file> --global` finished at 100 percent with `end ok`.
- `sdb shell 0 applist` lists `'OmarchyTV' 'OmarchyTV0.OmarchyTV'`. The staged widget was removed. `device-profile.xml` remains in `/home/owner/share/tmp/sdk_tools/`.
- The widget runs on this Tizen 5.5 set. The project's published test set is a Tizen 9 `UN55U7900`.
- `db/first_screen/type` is `OmarchyTV0.OmarchyTV`. On boot, the firmware rewrites `db/appfw/booting_appid_backup` back to `org.tizen.tv-viewer`. That id is the picture. Leave it installed. Deactivating it can black-screen the panel, and there is no package backup. Do not point boot at OmarchyTV while `memory/boot/cold_poweroff_request_pkg` names `stability-monitor`.
- `com.samsung.tv.csfs`, the Samsung tile page, is deactivated. `com.samsung.tv.coba.home` stays. The sideloaded widget is not listed in the Apps grid.

## Exit returns to the dock

Exit resumes `org.tizen.tv-viewer`, and Samsung TV Plus tunes a channel on that picture. While the channel is up, `aul_test get_status` stays `STATUS_BG`, so a focus poll does not see it. The Samsung TV Plus button on this remote is a different foreground: `org.tizen.epg`, the guide. It stays there, and a power cycle was the way out. `scripts/session/omarchy-exit-hook.sh` follows the scenario log and raises OmarchyTV on the first line of a visit whose foreground is only `org.tizen.tv-viewer`, `com.samsung.tv.tvplus`, or `org.tizen.epg`. Power-on still opens the picture, and that picture is still one raise. A volume press while Netflix, Spotify, Prime Video, or another app is open leaves that app on the same line as the picture. Volume on the dock leaves OmarchyTV on that line. Those lines are ignored. Exit removes the app, and the next line is the picture alone. A visit that moves from the guide to the picture does not launch a second time. On that edge it runs:

```text
aul_test launch OmarchyTV0.OmarchyTV omarchy_nav home
```

That keeps the pid that is already running, and the page moves to workspace 0. The hook does not launch again until that picture has given up focus and taken it again. A launch on every poll suspends the app that was in front.

The physical Home key on this remote is Linux code 63 (`KEY_F5`). The platform consumes it before `/dev/input` sees it. The hook does not read input devices. Changing Home means editing `module.keyrouter.cfg` as root, on a read-only filesystem, with one Remote PC click.

UEP rejects `sh` of the unsigned file. Source it once after each power-on. A second source sees the running shell and leaves that copy in place. Close fd 3. It does not survive a power cycle:

```text
setsid sh -c '. /home/owner/share/tmp/sdk_tools/omarchy-exit-hook.sh' \
  </dev/null >/tmp/omarchy-exit-hook.log 2>&1 3>&- &
```

## Build the same widget

`patches/omarchytv-un43.patch` is the difference between the published `v2.14.0-beta` widget and the package installed on this TV. Apply it to an unpacked copy of that exact file. The patch keeps `required_version` at `2.3` and the same public privileges.

It does seven things:

- The top-right cluster opens this set's own screens. Bluetooth is `org.tizen.btaudiolist`. Internet is `com.samsung.tv.knox-browser`, the package this TV labels Internet. Network is `org.tizen.NetworkSetting-Tizen`, the network and Wi-Fi screen. Volume is `org.tizen.volume-setting`. Upstream sent that cluster to `com.palm.app.settings`.
- The dock is Netflix, Spotify, and Prime Video, using the upstream wordmark tiles (the gradient and the name). The Tizen shim used to replace that list with every installed app and Samsung's store PNG. Those store icons are not used. The other upstream tiles stay in `DEFAULT_APPS` and are not placed on this dock.
- Exit, Return, and Back while this app is in front move to workspace 0 in the same page. `background-support` is `enable`. Becoming visible again calls `OMARCHY_GO_HOME` unless the app itself just launched the tuner or another app.
- `aul_test launch OmarchyTV0.OmarchyTV omarchy_nav home` on the running process reads `omarchy_nav=home` and calls `OMARCHY_GO_HOME`. `reload` is `disable` on the main and `eden_resume` app-controls, so that launch does not load the page again.
- `tizen:category` is `http://tizen.org/category/tv`. The Apps grid on this set still does not list the widget.
- The boot sequence waits until the page is visible. A power-on can load the page while the panel is still on the Samsung logo. Time spent hidden does not advance the script, and the power key does not skip it until the tube has opened.
- A theme picked on the TV is posted to the paired PC at `/v1/theme/set` with no Grok ask code. Saying “change my theme to nord” in the companion applies it on the TV and sends that same request. It does not open the TV browser. The companion agent “Grok on grok.com” is the choice that opens the browser. A PC bridge that still requires the ask code on `/v1/theme/set` will refuse the change. Themes that exist only in the widget stay on the TV.

Another UN43TU7000 uses its own DUID. The certificate that signed this set is not in the repository.

1. Download `OmarchyTV-tizen-2.14.0-unsigned.wgt` from the `v2.14.0-beta` release. Its SHA-256 must be `5d12bd2ad82098d674f0217d61d71adfb5dda62c0e996b04b337b2282a30977c`.
2. Unpack it. `app.js` is in the top directory of the archive.
3. From that directory:

```bash
patch -p1 < /path/to/omarchy-tv-samsung/patches/omarchytv-un43.patch
```

4. Create a Samsung author and distributor certificate whose distributor certificate contains this television's DUID. Tizen Studio 6.0's `tizen` command runs under the bundled Java 8, not a newer system Java. Sign with `tizen package -t wgt -s <profile>`.
5. Install with `pkgcmd -i -t wgt -p <signed.wgt> --global`. Without `--global` this image returns `Security error [-22]`.
6. Copy `scripts/session/omarchy-exit-hook.sh` to `/home/owner/share/tmp/sdk_tools/` and source it with the command in the Exit section. Do that again after every power-on.

Do not raise `required_version`. Do not sign with an Android keystore. Do not sideload the unsigned file. Do not commit the certificate, the password, `device-profile.xml`, or the built widget. `build/` is gitignored for that reason.

The physical Home key and the remote Source key are outside this patch. Home still needs `module.keyrouter.cfg`. Source is still unmapped. Nothing in this repository relaunches OmarchyTV after a crash. A crash policy of at most two relaunches, then the normal picture, is still open.
