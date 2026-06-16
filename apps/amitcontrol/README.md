# AmitControl Panel

> System Control Center for **Amit OS** — built with GTK 3 and Python 3.

---

## Overview

AmitControl is the native settings and diagnostics application for Amit OS.
It provides a clean, tabbed interface to monitor live system metrics, tweak
display preferences, inspect network interfaces, manage users, and learn more
about the running environment — all without opening a terminal.

---

## Features

| Tab | What it does |
|-----|-------------|
| 🖥 **System Info** | OS/kernel details, CPU model, RAM/Swap/Disk totals, live progress bars updated every 3 s, system uptime |
| 🖥 **Display** | xrandr output, dark-theme toggle (live), UI scale factor, font picker |
| 🌐 **Network** | All network interfaces with IPv4/IPv6/MAC addresses, link state & speed, built-in ping tester |
| 👤 **Users** | Current user info (name, UID, home, shell), logged-in users table, quick-launch terminal |
| ℹ **About** | App version, toolkit info, platform, licence, standard GTK About dialog |

---

## Requirements

| Package | Purpose |
|---------|---------|
| Python ≥ 3.10 | Runtime |
| PyGObject (`gi`) | GTK 3 bindings |
| `psutil` | System metrics (CPU, RAM, disk, users) |
| GTK 3 runtime | GUI toolkit |

### Install dependencies

```bash
# Debian / Ubuntu / Amit OS
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

pip install psutil          # or: sudo apt install python3-psutil
```

---

## Running

```bash
# From the project root
python3 apps/amitcontrol/amitcontrol.py

# Or (after installing to /opt/amit-os)
amitcontrol
```

---

## File Structure

```
apps/amitcontrol/
├── __init__.py          # Package marker
├── amitcontrol.py       # Main application (GTK 3)
├── amitcontrol.desktop  # XDG desktop entry
└── README.md            # This file
```

---

## Installing the Desktop Entry

```bash
# System-wide (requires sudo)
sudo cp amitcontrol.desktop /usr/share/applications/

# Per-user
cp amitcontrol.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

---

## Architecture

```
AmitControlApp (Gtk.Application)
└── AmitControlWindow (Gtk.ApplicationWindow)
    ├── Gtk.HeaderBar  — title, refresh button
    ├── Gtk.Notebook   — tab container (LEFT tabs)
    │   ├── SystemInfoTab     (Gtk.ScrolledWindow)
    │   ├── DisplaySettingsTab(Gtk.ScrolledWindow)
    │   ├── NetworkTab        (Gtk.ScrolledWindow)
    │   ├── UsersTab          (Gtk.ScrolledWindow)
    │   └── AboutTab          (Gtk.Box)
    └── Gtk.Statusbar  — clock + version
```

Live data in **SystemInfoTab** is refreshed via `GLib.timeout_add_seconds(3, …)`.
The ping test in **NetworkTab** runs in a background thread so the UI stays responsive.

---

## Customisation

All CSS is injected via `Gtk.CssProvider` in `AmitControlWindow._apply_css()`.
The colour palette follows the [Catppuccin Mocha](https://github.com/catppuccin/catppuccin)
scheme — edit the CSS bytes in that method to change colours.

---

## Licence

MIT — © Amit OS Project
