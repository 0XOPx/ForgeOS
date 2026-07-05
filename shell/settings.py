#!/usr/bin/env python3
"""
Settings panel: appearance, display, and session controls.
Runs as a standalone process launched from the taskbar or launcher.
"""
import sys
import os
import subprocess

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QComboBox, QPushButton, QSlider, QMessageBox
)
from PyQt5.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


class AppearanceTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("UI scale"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(80, 150)
        self.scale_slider.setValue(100)
        self.scale_slider.setTickInterval(10)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        layout.addWidget(self.scale_slider)

        layout.addWidget(QLabel("Font"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["DejaVu Sans", "Noto Sans"])
        layout.addWidget(self.font_combo)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)
        layout.addStretch(1)

    def apply_settings(self):
        # Writes user-level fontconfig override; picked up on next
        # shell/app launch without rebuilding the image.
        home = os.path.expanduser("~")
        conf_dir = os.path.join(home, ".config", "fontconfig")
        os.makedirs(conf_dir, exist_ok=True)
        font_name = self.font_combo.currentText()
        content = f"""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <match target="pattern">
    <edit name="family" mode="prepend"><string>{font_name}</string></edit>
  </match>
</fontconfig>
"""
        with open(os.path.join(conf_dir, "fonts.conf"), "w") as f:
            f.write(content)
        QMessageBox.information(self, "Appearance", "Font preference saved.")


class DisplayTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Resolution"))

        self.res_combo = QComboBox()
        self.res_combo.addItems(self._detect_resolutions())
        layout.addWidget(self.res_combo)

        apply_btn = QPushButton("Apply Resolution")
        apply_btn.clicked.connect(self.apply_resolution)
        layout.addWidget(apply_btn)
        layout.addStretch(1)

    def _detect_resolutions(self):
        try:
            output = subprocess.check_output(["xrandr"], text=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            return ["1920x1080", "1280x720"]
        modes = []
        for line in output.splitlines():
            line = line.strip()
            if line and line[0].isdigit() and "x" in line.split()[0]:
                modes.append(line.split()[0])
        return modes or ["1920x1080"]

    def apply_resolution(self):
        mode = self.res_combo.currentText()
        try:
            output_name = subprocess.check_output(
                ["bash", "-c", "xrandr | grep ' connected' | cut -d' ' -f1 | head -n1"],
                text=True,
            ).strip()
            subprocess.run(["xrandr", "--output", output_name, "--mode", mode])
        except subprocess.SubprocessError as exc:
            QMessageBox.warning(self, "Display", f"Failed to apply mode: {exc}")


class SessionTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        logout_btn = QPushButton("Log Out")
        logout_btn.clicked.connect(self.logout)
        restart_btn = QPushButton("Restart")
        restart_btn.clicked.connect(self.restart)
        shutdown_btn = QPushButton("Shut Down")
        shutdown_btn.clicked.connect(self.shutdown)

        for b in (logout_btn, restart_btn, shutdown_btn):
            row.addWidget(b)
        layout.addLayout(row)
        layout.addStretch(1)

    def _confirm(self, action_label: str) -> bool:
        reply = QMessageBox.question(
            self, "Confirm", f"{action_label} now?",
            QMessageBox.Yes | QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def logout(self):
        if self._confirm("Log out"):
            subprocess.run(["pkill", "-KILL", "-u", os.environ.get("USER", "")])

    def restart(self):
        if self._confirm("Restart"):
            subprocess.run(["systemctl", "reboot"])

    def shutdown(self):
        if self._confirm("Shut down"):
            subprocess.run(["systemctl", "poweroff"])


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ForgeOS Settings")
        self.resize(420, 320)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(AppearanceTab(), "Appearance")
        tabs.addTab(DisplayTab(), "Display")
        tabs.addTab(SessionTab(), "Session")
        layout.addWidget(tabs)


def main():
    app = QApplication(sys.argv)
    try:
        with open(config.STYLE_SHEET_PATH) as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass
    win = SettingsWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
