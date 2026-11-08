# OmarchyTV on this UN43TU7000

Installed as a normal app. It does not replace Home.

Upstream is [piermark/omarchytv](https://github.com/piermark/omarchytv). The build installed on this TV is `v2.14.0-beta`.

## What was installed

- The published package is an HTML5 widget, package `OmarchyTV0`, app id `OmarchyTV0.OmarchyTV`, `required_version` 2.3, public privileges. It does not take the Home key.
- The GitHub release file `OmarchyTV-tizen-2.14.0-unsigned.wgt` was downloaded. Its SHA-256 is `5d12bd2ad82098d674f0217d61d71adfb5dda62c0e996b04b337b2282a30977c`, which matches the release table. `tizen/INSTALL-TIZEN.md` prints a different hash, `5916dd07d8e20ec1fa78dd8f927dc63283d2899257a27c0eca4a91c79a391174`, and that hash is not this file.
- The unsigned widget was refused with `Check certificate error [-12]`. A Samsung public author and distributor certificate for DUID `<duid>` was created in a local profile named `<profile>`. Those certificate files stay on the PC and are not in this repository.
- Tizen Studio 6.0 CLI signed the unpacked widget with `tizen package -t wgt -s <profile>`. The certificate chain checked out as privilege level `PUBLIC`.
- `pkgcmd -i -t wgt -p <file>` without `--global` copied the app under `/var/lib/empty/apps_rw` and failed with `Security error [-22]` (`Unexpected path` in `security_registration.cc`). The SDB command user on this set has that empty home. `pkgcmd -i -t wgt -p <file> --global` finished at 100 percent with `end ok`.
- `sdb shell 0 applist` lists `'OmarchyTV' 'OmarchyTV0.OmarchyTV'`. The staged widget was removed. `device-profile.xml` remains in `/home/owner/share/tmp/sdk_tools/`.
- Home routing was not changed. `db/appfw/booting_appid_backup` is still `org.tizen.tv-viewer`, and `db/first_screen/type` is still `com.samsung.tv.csfs`.
- The app was not launched, so this Tizen 5.5 web engine has not been seen running the widget yet. The project's published test set is a Tizen 9 `UN55U7900`.

## What a backwards-compatible version has to cover

A later change in this repository should add a widget that installs on Tizen 5.5 / platform `20_KANTSU2_UHD_BASIC` as a normal app:

- Same public privileges the current widget uses. No partner privilege and no attempt to become Home.
- A Samsung author and distributor certificate for DUID `<duid>`.
- A fresh download whose SHA-256 is recorded in this file after the file is hashed locally.
- An install through `tizen package` and `tizen install` against SDB, then a launch from the app list on this TV.
- A note of what the Tizen 5.5 web engine rejects, if the current upstream widget fails here, and the smallest source change that fixes that without raising `required_version` above 5.5.

Root is not required for that install. Do not sign the widget with an Android keystore. Do not sideload the unsigned file.
