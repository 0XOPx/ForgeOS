"""
Application launcher: a popup grid of app icons anchored above the
launcher button in the taskbar.
"""
import shlex
import subprocess

from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QLabel, QVBoxLayout
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

import config


class LauncherPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("LauncherPopup")
        self.setFixedWidth(260)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Applications")
        title.setObjectName("LauncherTitle")
        outer.addWidget(title)

        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setSpacing(12)

        row, col = 0, 0
        for name, icon_file, cmd_template in config.APPLICATIONS:
            btn = self._make_app_button(name, icon_file, cmd_template)
            grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        outer.addWidget(grid_container)

    def _make_app_button(self, name, icon_file, cmd_template):
        btn = QPushButton(name)
        btn.setObjectName("AppTile")
        btn.setIcon(QIcon(config.icon_path(icon_file)))
        btn.setIconSize(QSize(32, 32))
        btn.setFixedSize(76, 76)
        btn.clicked.connect(lambda: self.launch(cmd_template))
        return btn

    def launch(self, cmd_template: str):
        command = config.resolve_command(cmd_template)
        subprocess.Popen(shlex.split(command))
        self.hide()

    def show_at(self, x: int, y: int):
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
