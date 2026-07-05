"""
Central configuration for the ForgeOS shell.
All paths assume the shell is installed at /opt/forgeos/shell
and the theme lives at /opt/forgeos/theme, matching build/build-iso.sh.
"""
import os

SHELL_ROOT = os.path.dirname(os.path.abspath(__file__))
FORGEOS_ROOT = os.path.dirname(SHELL_ROOT)
THEME_ROOT = os.path.join(FORGEOS_ROOT, "theme")
ICON_DIR = os.path.join(THEME_ROOT, "icons")
STYLE_SHEET_PATH = os.path.join(THEME_ROOT, "style.qss")

TASKBAR_HEIGHT = 40
TRAY_RESERVED_WIDTH = 140  # space reserved on the taskbar for stalonetray

# Applications shown in the launcher grid: (display name, icon file, command)
APPLICATIONS = [
    ("Terminal",     "terminal.svg", "xterm"),
    ("File Manager", "folder.svg",   "python3 {shell_root}/filemanager.py"),
    ("Settings",     "settings.svg", "python3 {shell_root}/settings.py"),
]

def resolve_command(cmd_template: str) -> str:
    return cmd_template.format(shell_root=SHELL_ROOT)

def icon_path(name: str) -> str:
    return os.path.join(ICON_DIR, name)
