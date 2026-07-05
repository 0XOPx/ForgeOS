#!/usr/bin/env python3
"""
Minimal file manager integrated with the ForgeOS shell.
Supports: browse, open (via xdg-open), copy, paste, delete (to trash),
and rename. Launched from the launcher grid as a standalone window.
"""
import sys
import os
import shutil
import subprocess

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QLineEdit, QMessageBox,
    QInputDialog
)
from PyQt5.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


class FileManager(QWidget):
    def __init__(self, start_path: str = None):
        super().__init__()
        self.setWindowTitle("ForgeOS File Manager")
        self.resize(640, 420)

        self.current_path = os.path.abspath(start_path or os.path.expanduser("~"))
        self.clipboard_path = None
        self.clipboard_mode = None  # "copy" or "cut"

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        path_row = QHBoxLayout()
        self.path_field = QLineEdit(self.current_path)
        self.path_field.returnPressed.connect(self._navigate_from_field)
        up_btn = QPushButton("Up")
        up_btn.clicked.connect(self.go_up)
        path_row.addWidget(up_btn)
        path_row.addWidget(self.path_field)
        layout.addLayout(path_row)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_activated)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected)
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(self.copy_selected)
        cut_btn = QPushButton("Cut")
        cut_btn.clicked.connect(self.cut_selected)
        paste_btn = QPushButton("Paste")
        paste_btn.clicked.connect(self.paste)
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self.rename_selected)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_selected)

        for b in (open_btn, copy_btn, cut_btn, paste_btn, rename_btn, delete_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def refresh(self):
        self.list_widget.clear()
        self.path_field.setText(self.current_path)
        try:
            entries = sorted(
                os.listdir(self.current_path),
                key=lambda e: (
                    not os.path.isdir(os.path.join(self.current_path, e)),
                    e.lower(),
                ),
            )
        except PermissionError:
            self.status_label.setText("Permission denied.")
            return

        for entry in entries:
            full = os.path.join(self.current_path, entry)
            label = entry + ("/" if os.path.isdir(full) else "")
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, full)
            self.list_widget.addItem(item)

        self.status_label.setText(f"{len(entries)} items")

    def _selected_path(self):
        item = self.list_widget.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _on_item_activated(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if os.path.isdir(path):
            self.current_path = path
            self.refresh()
        else:
            self._open_path(path)

    def _navigate_from_field(self):
        target = self.path_field.text().strip()
        if os.path.isdir(target):
            self.current_path = target
            self.refresh()
        else:
            QMessageBox.warning(self, "Navigate", "Not a valid directory.")

    def go_up(self):
        parent = os.path.dirname(self.current_path.rstrip("/"))
        if parent:
            self.current_path = parent
            self.refresh()

    # --- Open ---
    def _open_path(self, path: str):
        subprocess.Popen(["xdg-open", path])

    def open_selected(self):
        path = self._selected_path()
        if path:
            self._open_path(path)

    # --- Copy / Cut / Paste ---
    def copy_selected(self):
        path = self._selected_path()
        if path:
            self.clipboard_path = path
            self.clipboard_mode = "copy"
            self.status_label.setText(f"Copied: {os.path.basename(path)}")

    def cut_selected(self):
        path = self._selected_path()
        if path:
            self.clipboard_path = path
            self.clipboard_mode = "cut"
            self.status_label.setText(f"Cut: {os.path.basename(path)}")

    def paste(self):
        if not self.clipboard_path:
            return
        src = self.clipboard_path
        dst = os.path.join(self.current_path, os.path.basename(src))
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst) if self.clipboard_mode == "copy" else shutil.move(src, dst)
            else:
                shutil.copy2(src, dst) if self.clipboard_mode == "copy" else shutil.move(src, dst)
            if self.clipboard_mode == "cut":
                self.clipboard_path = None
                self.clipboard_mode = None
            self.refresh()
        except (shutil.Error, OSError) as exc:
            QMessageBox.warning(self, "Paste failed", str(exc))

    # --- Rename ---
    def rename_selected(self):
        path = self._selected_path()
        if not path:
            return
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
                self.refresh()
            except OSError as exc:
                QMessageBox.warning(self, "Rename failed", str(exc))

    # --- Delete ---
    def delete_selected(self):
        path = self._selected_path()
        if not path:
            return
        reply = QMessageBox.question(
            self, "Delete", f"Move '{os.path.basename(path)}' to trash?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            # trash-cli (installed via package list) sends to XDG trash
            # instead of permanent deletion.
            subprocess.run(["trash-put", path], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to permanent delete if trash-cli isn't available.
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        self.refresh()


def main():
    app = QApplication(sys.argv)
    try:
        with open(config.STYLE_SHEET_PATH) as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass
    start = sys.argv[1] if len(sys.argv) > 1 else None
    win = FileManager(start)
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
