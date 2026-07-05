"""
System tray integration.

Implementing the freedesktop XEmbed system tray protocol natively in
PyQt5 is heavy (Qt removed QX11EmbedContainer in Qt5), so ForgeOS uses
`stalonetray` as a dedicated tray-icon host process, docked in the
reserved strip on the right of the taskbar (see config.TRAY_RESERVED_WIDTH
and theme/stalonetrayrc for exact geometry/colors).

This module is responsible for starting and supervising that process
so the rest of the shell doesn't need to know tray icons aren't rendered
by Qt itself.
"""
import subprocess
import shutil

import config


class TrayManager:
    def __init__(self):
        self._proc = None

    def start(self):
        stalonetray_bin = shutil.which("stalonetray")
        if not stalonetray_bin:
            raise RuntimeError(
                "stalonetray is not installed; install it via the "
                "ForgeOS package list (config/package-list.txt)."
            )
        rc_path = f"{config.THEME_ROOT}/stalonetrayrc"
        self._proc = subprocess.Popen(
            [stalonetray_bin, "--config", rc_path]
        )
        return self._proc

    def stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()


if __name__ == "__main__":
    # Allows scripts/xinitrc to start the tray independently of main.py.
    manager = TrayManager()
    proc = manager.start()
    proc.wait()
