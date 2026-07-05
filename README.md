# ForgeOS

A minimal Debian-based Linux distribution with no preinstalled desktop
environment. All desktop UI (taskbar, launcher, tray, settings, file
manager) is provided by a single custom PyQt5 application, `forgeos-shell`,
running on top of a bare, decoration-free Openbox window manager.

## Layout on target system

| Path                          | Purpose                                   |
|--------------------------------|-------------------------------------------|
| /opt/forgeos/shell/            | Python shell application                  |
| /opt/forgeos/theme/            | Stylesheet, fonts, icons, stalonetray cfg |
| /etc/xdg/openbox/rc.xml        | Openbox config (no titlebars/menus)       |
| /usr/local/bin/forgeos-start-ui| Boot entry point (started from .xinitrc)  |
| /etc/skel/.xinitrc             | Xorg session launcher (copied to users)   |

## Build locally

```
sudo ./build/build-iso.sh
```

Produces `live-image-amd64.hybrid.iso` in `live-build-workdir/`.
Requires a Debian/Ubuntu host (or VM) with `live-build` installed and
several GB of free disk space. **This will not run on Windows or macOS
directly** — use a Linux VM, a cloud VM, or the GitHub Actions workflow
below.

## Build via GitHub Actions (no Linux machine needed)

This repo includes `.github/workflows/build-iso.yml`, which:

- Runs on every push to `main` that touches project files, and can also
  be triggered manually from the Actions tab (`workflow_dispatch`).
- Builds the ISO on an `ubuntu-latest` runner using `live-build`.
- Uploads the ISO as a workflow artifact on every run.
- **On pushes to `main`**, additionally creates/updates a GitHub Release
  (tagged `nightly`) with the ISO attached, so you always have a
  downloadable link to the latest build without touching a terminal.

To use it:

1. Push this repository to GitHub with the default branch named `main`.
2. Go to the **Actions** tab, or just push a commit — the workflow
   triggers automatically.
3. Once it finishes, grab the ISO from the workflow's **Artifacts**
   section, or from the **Releases** page (tag `nightly`).

## Boot flow

1. systemd reaches `getty@tty1` with autologin enabled (see
   `scripts/getty-autologin.conf`).
2. The user's shell profile (`scripts/bash_profile.append`) detects tty1
   and no running X server, and calls `startx`.
3. `startx` reads `~/.xinitrc` (installed from `scripts/xinitrc`), which:
   - starts `openbox` (window manager only, no decorations/menus)
   - starts `stalonetray` (docked system tray, themed to match the shell)
   - execs `forgeos-start-ui`, which launches `forgeos-shell` (`main.py`)
4. X server lifetime is tied to the shell process; killing the shell ends
   the session.

## Default credentials

The build creates a user `forgeos` with password `forgeos`. **Change
this** (edit `FORGEOS_USER`/`chpasswd` line in `build/build-iso.sh`)
before using the image for anything beyond local testing.
