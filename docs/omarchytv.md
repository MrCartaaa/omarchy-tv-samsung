# OmarchyTV on this UN43TU7000

Not installed. The deactivate work does not install it, and it must not replace Home.

Upstream is [piermark/omarchytv](https://github.com/piermark/omarchytv). The build inspected for this TV was `v2.14.0-beta`.

## Why it is not on the TV yet

- The published package is an unsigned HTML5 widget, `OmarchyTV0`, `required_version` 2.3, public privileges. It does not take the Home key.
- Install needs Tizen Studio, the Samsung certificate extension, and a certificate profile for this set's DUID `<duid>`. This PC has SDB and no `tizen` CLI certificate profile.
- The project's published test set is a Tizen 9 `UN55U7900`, not this Tizen 5.5 `UN43TU7000FXZC`. The manifest allows 2.3, so a package can target 5.5, but that does not mean this TV's web engine runs the current widget.
- The GitHub release file `OmarchyTV-tizen-2.14.0-unsigned.wgt` was downloaded. Its SHA-256 is `5d12bd2ad82098d674f0217d61d71adfb5dda62c0e996b04b337b2282a30977c`, which matches the release table. `tizen/INSTALL-TIZEN.md` prints a different hash, `5916dd07d8e20ec1fa78dd8f927dc63283d2899257a27c0eca4a91c79a391174`, and that hash is not this file.
- The TV refused the unsigned widget. `pkgcmd -i -t wgt -p <file>` returned `Check certificate error [-12]` for package `OmarchyTV0`. The app is not on the app list. The staged file was removed. A Samsung author and distributor certificate for DUID `<duid>` has to sign the widget before another install. This PC has SDB and no `tizen` certificate profile. The Home key was not changed.

## What a backwards-compatible version has to cover

A later change in this repository should add a widget that installs on Tizen 5.5 / platform `20_KANTSU2_UHD_BASIC` as a normal app:

- Same public privileges the current widget uses. No partner privilege and no attempt to become Home.
- A Samsung author and distributor certificate for DUID `<duid>`.
- A fresh download whose SHA-256 is recorded in this file after the file is hashed locally.
- An install through `tizen package` and `tizen install` against SDB, then a launch from the app list on this TV.
- A note of what the Tizen 5.5 web engine rejects, if the current upstream widget fails here, and the smallest source change that fixes that without raising `required_version` above 5.5.

Root is not required for that install. Do not sign the widget with an Android keystore. Do not sideload the unsigned file.
