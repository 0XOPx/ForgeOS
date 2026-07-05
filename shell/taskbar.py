"""
Taskbar: a fixed panel docked to the bottom of the primary screen.
Owns the launcher button, running-window list, clock, and settings button.
Reserves a strip of screen space on the right for stalonetray.
"""
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon

import config
from launcher import LauncherPopup


class WindowButton(QPushButton):
    """A taskbar entry representing one open window."""

    def __init__(self, window_id: str, title: str, parent=None):
        super().__init__(title, parent)
        self.window_id = window_id
        self.setCheckable(True)
        self.setFlat(True)
        self.setMaximumWidth(220)
        self.clicked.connect(self.activate)

    def activate(self):
        subprocess.Popen(["wmctrl", "-ia", self.window_id])


class Taskbar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Taskbar")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_X11NetWmWindowTypeDock, True)

        screen_geo = self._primary_screen_geometry()
        self.setGeometry(
            0,
            screen_geo.height() - config.TASKBAR_HEIGHT,
            screen_geo.width(),
            config.TASKBAR_HEIGHT,
        )

        self._build_ui()

        self._window_buttons = {}
        self._launcher_popup = LauncherPopup(self)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_window_list)
        self._refresh_timer.start(1000)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

        self.refresh_window_list()
        self._update_clock()

    def _primary_screen_geometry(self):
        from PyQt5.QtWidgets import QApplication
        return QApplication.primaryScreen().geometry()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)

        self.launcher_btn = QPushButton()
        self.launcher_btn.setObjectName("LauncherButton")
        self.launcher_btn.setIcon(QIcon(config.icon_path("launcher.svg")))
        self.launcher_btn.setIconSize(QSize(24, 24))
        self.launcher_btn.setFixedSize(36, 32)
        self.launcher_btn.clicked.connect(self.toggle_launcher)
        layout.addWidget(self.launcher_btn)

        self.window_list_container = QWidget()
        self.window_list_layout = QHBoxLayout(self.window_list_container)
        self.window_list_layout.setContentsMargins(0, 0, 0, 0)
        self.window_list_layout.setSpacing(4)
        self.window_list_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        layout.addWidget(self.window_list_container, 1)

        # Reserved space where stalonetray docks itself (positioned via
        # its own geometry config in theme/stalonetrayrc).
        tray_spacer = QWidget()
        tray_spacer.setFixedWidth(config.TRAY_RESERVED_WIDTH)
        layout.addWidget(tray_spacer)

        self.clock_label = QLabel("--:--")
        self.clock_label.setObjectName("ClockLabel")
        layout.addWidget(self.clock_label)

        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("SettingsButton")
        self.settings_btn.setIcon(QIcon(config.icon_path("settings.svg")))
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)

    def toggle_launcher(self):
        if self._launcher_popup.isVisible():
            self._launcher_popup.hide()
        else:
            btn_pos = self.launcher_btn.mapToGlobal(
                self.launcher_btn.rect().topLeft()
            )
            self._launcher_popup.show_at(
                btn_pos.x(), btn_pos.y() - self._launcher_popup.height()
            )

    def open_settings(self):
        subprocess.Popen(["python3", f"{config.SHELL_ROOT}/settings.py"])

    def refresh_window_list(self):
        try:
            output = subprocess.check_output(
                ["wmctrl", "-l"], text=True, timeout=2
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return

        current_ids = set()
        for line in output.strip().splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            win_id, desktop, host, title = parts
            if desktop == "-1":
                continue  # sticky/system window, skip
            current_ids.add(win_id)
            if win_id not in self._window_buttons:
                btn = WindowButton(win_id, title[:28])
                self.window_list_layout.addWidget(btn)
                self._window_buttons[win_id] = btn
            else:
                self._window_buttons[win_id].setText(title[:28])

        for win_id in list(self._window_buttons.keys()):
            if win_id not in current_ids:
                btn = self._window_buttons.pop(win_id)
                btn.setParent(None)
                btn.deleteLater()

    def _update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M  %Y-%m-%d"))
