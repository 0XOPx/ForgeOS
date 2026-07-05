#!/usr/bin/env python3
"""
ForgeOS shell entry point.
Launches the taskbar (which owns the launcher popup and settings trigger)
and keeps the process alive for the duration of the X session.
"""
import sys
import os

from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from taskbar import Taskbar


def load_stylesheet(app: QApplication) -> None:
    try:
        with open(config.STYLE_SHEET_PATH, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        # Stylesheet is optional at runtime; shell still functions unstyled.
        pass


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    load_stylesheet(app)

    taskbar = Taskbar()
    taskbar.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
