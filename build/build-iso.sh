#!/bin/bash
# Builds a bootable ForgeOS ISO using live-build.
# Run as root on a Debian/Ubuntu build host with live-build installed:
#   sudo apt install live-build
#
# Usage: sudo ./build/build-iso.sh

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root." >&2
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/live-build-workdir"
FORGEOS_USER="forgeos"

echo "==> Preparing build directory at ${BUILD_DIR}"
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

echo "==> Configuring live-build (Debian minimal, amd64, no DE)"
# --mode debian is required even when running live-build ON a Debian host,
# but it is CRITICAL when the build host itself is Ubuntu (e.g. GitHub
# Actions' ubuntu-latest runners): lb_config otherwise auto-detects the
# *host* distro and tries to bootstrap "bookworm" from archive.ubuntu.com,
# which does not exist and fails with a Release-file 404. Explicit
# mirrors below make the target independent of whatever /etc/apt on the
# build host happens to point at.
lb config \
    --mode debian \
    --distribution bookworm \
    --archive-areas "main contrib non-free non-free-firmware" \
    --binary-images iso-hybrid \
    --architecture amd64 \
    --debian-installer none \
    --memtest none \
    --mirror-bootstrap "http://deb.debian.org/debian/" \
    --mirror-binary "http://deb.debian.org/debian/" \
    --mirror-chroot-security "http://security.debian.org/debian-security/" \
    --mirror-binary-security "http://security.debian.org/debian-security/" \
    --apt-recommends false


echo "==> Installing package list"
mkdir -p config/package-lists
cp "${PROJECT_ROOT}/config/package-list.txt" \
   config/package-lists/forgeos.list.chroot

echo "==> Embedding ForgeOS shell, theme, and WM config into the image"
mkdir -p config/includes.chroot/opt/forgeos
cp -r "${PROJECT_ROOT}/shell" config/includes.chroot/opt/forgeos/shell
cp -r "${PROJECT_ROOT}/theme" config/includes.chroot/opt/forgeos/theme

mkdir -p config/includes.chroot/etc/xdg/openbox
cp "${PROJECT_ROOT}/wm/openbox-rc.xml" \
   config/includes.chroot/etc/xdg/openbox/rc.xml

mkdir -p config/includes.chroot/usr/local/bin
cp "${PROJECT_ROOT}/scripts/start-ui.sh" \
   config/includes.chroot/usr/local/bin/forgeos-start-ui

mkdir -p config/includes.chroot/etc/skel
cp "${PROJECT_ROOT}/scripts/xinitrc" \
   config/includes.chroot/etc/skel/.xinitrc

# Append autostart snippet to a fresh skeleton bash_profile
touch config/includes.chroot/etc/skel/.bash_profile
cat "${PROJECT_ROOT}/scripts/bash_profile.append" \
    >> config/includes.chroot/etc/skel/.bash_profile

mkdir -p "config/includes.chroot/etc/systemd/system/getty@tty1.service.d"
sed "s/FORGEOS_USER/${FORGEOS_USER}/" \
    "${PROJECT_ROOT}/scripts/getty-autologin.conf" \
    > "config/includes.chroot/etc/systemd/system/getty@tty1.service.d/override.conf"

echo "==> Adding post-install hook: create user, fix permissions, mask any DM"
mkdir -p config/hooks/live
cat > config/hooks/live/9010-forgeos-setup.hook.chroot <<EOF
#!/bin/bash
set -e

# Create the default ForgeOS account if it doesn't already exist.
if ! id -u ${FORGEOS_USER} >/dev/null 2>&1; then
    useradd -m -s /bin/bash -G sudo,plugdev,netdev ${FORGEOS_USER}
    echo "${FORGEOS_USER}:forgeos" | chpasswd
fi

chmod +x /usr/local/bin/forgeos-start-ui
chmod +x /etc/skel/.xinitrc
chown -R ${FORGEOS_USER}:${FORGEOS_USER} /home/${FORGEOS_USER}

# Defensive: mask any display manager unit in case one slips in via
# a transitive dependency, so we never race a DM against our getty
# autologin + startx flow.
systemctl mask gdm.service gdm3.service lightdm.service sddm.service 2>/dev/null || true

systemctl enable NetworkManager.service
EOF
chmod +x config/hooks/live/9010-forgeos-setup.hook.chroot

echo "==> Running lb build (this will take a while)"
lb build

echo "==> Build complete. ISO located in: ${BUILD_DIR}"
ls -la "${BUILD_DIR}"/*.iso 2>/dev/null || \
    echo "Warning: no ISO found — check live-build output above for errors."
