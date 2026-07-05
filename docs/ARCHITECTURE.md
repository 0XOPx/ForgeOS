# ForgeOS Architecture

## Why Openbox is still present

"No preinstalled desktop environment" means no GNOME/KDE/XFCE stack and no
panel/launcher/settings provided by a DE. It does not mean "no window
manager at all" — X11 clients still need something to map windows, handle
focus, and implement the EWMH/ICCCM protocols (_NET_ACTIVE_WINDOW,
_NET_CLIENT_LIST, etc.) that the taskbar needs to enumerate and control
windows.

Openbox is configured with:
- no titlebars/borders (`<decor>no</decor>` for internal windows the shell
  manages itself; default apps get borders since we don't reskin every
  app)
- no root menu, no desktop right-click menu
- minimal keybindings (terminal, launcher toggle, close window)

This makes Openbox invisible to the user — it never draws anything the
custom shell doesn't already own. The user experiences the ForgeOS shell
as "the desktop."

## Component responsibilities

| Component        | Responsibility                                         |
|-------------------|--------------------------------------------------------|
| Openbox           | Window placement, focus, move/resize, EWMH state       |
| forgeos-shell      | Taskbar, launcher grid, settings panel, session control |
| stalonetray        | XEmbed system tray icons (docked into taskbar area)     |
| wmctrl / xdotool  | CLI bridge the shell uses to query/control Openbox      |

## Window management integration

The shell never talks to Xlib/XCB directly. It shells out to `wmctrl` and
`xdotool`, which is the same approach used by many lightweight WM
panels (tint2, lxpanel with openbox). This keeps the Python codebase free
of C extension dependencies and keeps window-manager logic decoupled from
UI logic — Openbox could be swapped for i3 or another EWMH WM with no
shell code changes.

- Listing windows: `wmctrl -l`
- Activating a window: `wmctrl -ia <id>`
- Closing a window: `wmctrl -ic <id>`
- Active window tracking: polling `xdotool getactivewindow` every 300ms

## CI/CD build pipeline

`.github/workflows/build-iso.yml` runs the exact same `build/build-iso.sh`
script used for local builds, inside a fresh `ubuntu-latest` runner. This
guarantees the CI-built ISO and a locally-built ISO are produced by
identical logic — the workflow does not duplicate or reimplement any
packaging steps, it just installs `live-build` and invokes the script.
