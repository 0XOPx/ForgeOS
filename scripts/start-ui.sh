#!/bin/bash
# Installed as /usr/local/bin/forgeos-start-ui
# Boot/session entry point for the ForgeOS shell, called from .xinitrc.

set -euo pipefail

SHELL_DIR="/opt/forgeos/shell"
LOG_DIR="$HOME/.local/share/forgeos"
mkdir -p "$LOG_DIR"

export QT_QPA_PLATFORM=xcb
export QT_AUTO_SCREEN_SCALE_FACTOR=1

exec python3 "$SHELL_DIR/main.py" >> "$LOG_DIR/shell.log" 2>&1
