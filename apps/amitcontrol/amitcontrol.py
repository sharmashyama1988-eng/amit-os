#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AmitControl Panel - System Control Center for Amit OS
A GTK3-based control panel providing system information and settings management.
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")

from gi.repository import Gtk, GLib, GdkPixbuf, Pango
import os
import platform
import subprocess
import socket
import psutil
import datetime
import threading
import sys


APP_NAME    = "AmitControl"
APP_VERSION = "1.0.0"
APP_ID      = "org.amitos.amitcontrol"


# ─────────────────────────── helpers ────────────────────────────

def run_cmd(cmd: list[str], default: str = "N/A") -> str:
    """Run a shell command and return stdout, or *default* on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() or default
    except Exception:
        return default


def bytes_to_human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def make_section_label(text: str) -> Gtk.Label:
    lbl = Gtk.Label()
    lbl.set_markup(f"<b><span font_size='large'>{text}</span></b>")
    lbl.set_xalign(0)
    return lbl


def make_separator() -> Gtk.Separator:
    sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sep.set_margin_top(4)
    sep.set_margin_bottom(8)
    return sep


def info_row(label: str, value: str) -> Gtk.Box:
    """Two-column row: bold label + selectable value."""
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    key = Gtk.Label()
    key.set_markup(f"<b>{label}:</b>")
    key.set_xalign(0)
    key.set_size_request(180, -1)

    val = Gtk.Label(label=value)
    val.set_xalign(0)
    val.set_selectable(True)
    val.set_line_wrap(True)
    val.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

    row.pack_start(key, False, False, 0)
    row.pack_start(val, True,  True,  0)
    return row


# ════════════════════════════════════════════════════════════════
# TAB 1 – System Info
# ════════════════════════════════════════════════════════════════

class SystemInfoTab(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._box.set_margin_top(16)
        self._box.set_margin_bottom(16)
        self._box.set_margin_start(20)
        self._box.set_margin_end(20)
        self.add(self._box)

        self._cpu_bar   = None
        self._ram_bar   = None
        self._swap_bar  = None
        self._disk_bar  = None
        self._uptime_lbl = None

        self._build_static()
        self._build_live()
        self._refresh()
        GLib.timeout_add_seconds(3, self._refresh)

    # ── static (doesn't change) ──────────────────────────────────
    def _build_static(self):
        b = self._box
        b.pack_start(make_section_label("🖥  OS & Hardware"), False, False, 0)
        b.pack_start(make_separator(), False, False, 0)

        uname = platform.uname()
        rows = [
            ("Operating System",   f"{uname.system} {uname.release}"),
            ("Kernel Version",     uname.version[:80] if len(uname.version) > 80 else uname.version),
            ("Architecture",       uname.machine),
            ("Hostname",           uname.node),
            ("Python Version",     sys.version.split()[0]),
            ("CPU Model",          platform.processor() or run_cmd(
                                       ["cat", "/proc/cpuinfo"],
                                       "Unknown"
                                   ).split("\n")[0][:60]),
            ("CPU Logical Cores",  str(psutil.cpu_count(logical=True))),
            ("CPU Physical Cores", str(psutil.cpu_count(logical=False))),
            ("Total RAM",          bytes_to_human(psutil.virtual_memory().total)),
            ("Total Swap",         bytes_to_human(psutil.swap_memory().total)),
        ]
        # Disk info
        try:
            disk = psutil.disk_usage("/")
            rows.append(("Root Disk Total", bytes_to_human(disk.total)))
        except Exception:
            pass

        for lbl, val in rows:
            b.pack_start(info_row(lbl, val), False, False, 2)

    # ── live (updated every 3 s) ─────────────────────────────────
    def _build_live(self):
        b = self._box
        b.pack_start(Gtk.Label(label=""), False, False, 4)
        b.pack_start(make_section_label("📊  Live Resource Usage"), False, False, 0)
        b.pack_start(make_separator(), False, False, 0)

        def _bar_row(label):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            lbl = Gtk.Label()
            lbl.set_markup(f"<b>{label}:</b>")
            lbl.set_xalign(0)
            lbl.set_size_request(140, -1)
            bar = Gtk.ProgressBar()
            bar.set_show_text(True)
            bar.set_hexpand(True)
            row.pack_start(lbl, False, False, 0)
            row.pack_start(bar, True, True, 0)
            b.pack_start(row, False, False, 2)
            return bar

        self._cpu_bar  = _bar_row("CPU Usage")
        self._ram_bar  = _bar_row("RAM Usage")
        self._swap_bar = _bar_row("Swap Usage")
        self._disk_bar = _bar_row("Root Disk")

        # Uptime
        up_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        up_key = Gtk.Label()
        up_key.set_markup("<b>System Uptime:</b>")
        up_key.set_xalign(0)
        up_key.set_size_request(140, -1)
        self._uptime_lbl = Gtk.Label(label="–")
        self._uptime_lbl.set_xalign(0)
        up_row.pack_start(up_key, False, False, 0)
        up_row.pack_start(self._uptime_lbl, True, True, 0)
        b.pack_start(up_row, False, False, 2)

    def _refresh(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            swp = psutil.swap_memory()
            dsk = psutil.disk_usage("/")

            self._cpu_bar.set_fraction(cpu / 100)
            self._cpu_bar.set_text(f"{cpu:.1f}%")

            self._ram_bar.set_fraction(ram.percent / 100)
            self._ram_bar.set_text(
                f"{bytes_to_human(ram.used)} / {bytes_to_human(ram.total)} ({ram.percent:.1f}%)"
            )

            self._swap_bar.set_fraction(swp.percent / 100)
            self._swap_bar.set_text(
                f"{bytes_to_human(swp.used)} / {bytes_to_human(swp.total)} ({swp.percent:.1f}%)"
            )

            self._disk_bar.set_fraction(dsk.percent / 100)
            self._disk_bar.set_text(
                f"{bytes_to_human(dsk.used)} / {bytes_to_human(dsk.total)} ({dsk.percent:.1f}%)"
            )

            boot = datetime.datetime.fromtimestamp(psutil.boot_time())
            delta = datetime.datetime.now() - boot
            h, rem = divmod(int(delta.total_seconds()), 3600)
            m, s   = divmod(rem, 60)
            self._uptime_lbl.set_text(f"{h}h {m}m {s}s")
        except Exception as e:
            print(f"[SystemInfo] refresh error: {e}")
        return True   # keep repeating


# ════════════════════════════════════════════════════════════════
# TAB 2 – Display Settings
# ════════════════════════════════════════════════════════════════

class DisplaySettingsTab(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(20)
        box.set_margin_end(20)
        self.add(box)

        box.pack_start(make_section_label("🖥  Display Information"), False, False, 0)
        box.pack_start(make_separator(), False, False, 0)

        # ── monitor info via xrandr ──────────────────────────────
        xrandr = run_cmd(["xrandr", "--current"])
        if xrandr and xrandr != "N/A":
            lines = [l for l in xrandr.splitlines() if " connected" in l or l.startswith("Screen")]
            for line in lines[:6]:
                lbl = Gtk.Label(label=line.strip())
                lbl.set_xalign(0)
                lbl.set_selectable(True)
                box.pack_start(lbl, False, False, 1)
        else:
            box.pack_start(
                Gtk.Label(label="xrandr not available – running on non-X environment."),
                False, False, 0
            )

        box.pack_start(Gtk.Label(label=""), False, False, 4)
        box.pack_start(make_section_label("🌗  Appearance"), False, False, 0)
        box.pack_start(make_separator(), False, False, 0)

        # ── Scale / DPI ──────────────────────────────────────────
        scale_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        scale_lbl = Gtk.Label()
        scale_lbl.set_markup("<b>UI Scale Factor:</b>")
        scale_lbl.set_xalign(0)
        scale_lbl.set_size_request(180, -1)
        scale_spin = Gtk.SpinButton()
        scale_spin.set_adjustment(Gtk.Adjustment(value=1.0, lower=0.5, upper=3.0,
                                                 step_increment=0.25, page_increment=0.5))
        scale_spin.set_digits(2)
        scale_row.pack_start(scale_lbl,  False, False, 0)
        scale_row.pack_start(scale_spin, False, False, 0)
        box.pack_start(scale_row, False, False, 2)

        # ── Dark / Light theme ───────────────────────────────────
        theme_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        theme_lbl = Gtk.Label()
        theme_lbl.set_markup("<b>Prefer Dark Theme:</b>")
        theme_lbl.set_xalign(0)
        theme_lbl.set_size_request(180, -1)
        theme_switch = Gtk.Switch()
        theme_switch.connect("notify::active", self._on_dark_toggle)
        # detect current preference
        settings = Gtk.Settings.get_default()
        if settings:
            theme_switch.set_active(settings.get_property("gtk-application-prefer-dark-theme"))
        theme_row.pack_start(theme_lbl,    False, False, 0)
        theme_row.pack_start(theme_switch, False, False, 0)
        box.pack_start(theme_row, False, False, 2)

        # ── Font ─────────────────────────────────────────────────
        font_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        font_lbl = Gtk.Label()
        font_lbl.set_markup("<b>Interface Font:</b>")
        font_lbl.set_xalign(0)
        font_lbl.set_size_request(180, -1)
        font_btn = Gtk.FontButton()
        font_btn.set_use_font(True)
        font_row.pack_start(font_lbl, False, False, 0)
        font_row.pack_start(font_btn, True,  True,  0)
        box.pack_start(font_row, False, False, 2)

        # ── Apply button ─────────────────────────────────────────
        apply_btn = Gtk.Button(label="  Apply Display Settings")
        apply_btn.get_style_context().add_class("suggested-action")
        apply_btn.set_halign(Gtk.Align.START)
        apply_btn.connect("clicked", lambda _: self._show_toast(box))
        box.pack_start(apply_btn, False, False, 10)

        self._toast_lbl = Gtk.Label()
        self._toast_lbl.set_xalign(0)
        box.pack_start(self._toast_lbl, False, False, 0)

    def _on_dark_toggle(self, switch, _param):
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", switch.get_active())

    def _show_toast(self, _box):
        self._toast_lbl.set_markup(
            "<span foreground='green'>✔ Settings applied (session-level only).</span>"
        )
        GLib.timeout_add_seconds(4, lambda: self._toast_lbl.set_text("") or False)


# ════════════════════════════════════════════════════════════════
# TAB 3 – Network
# ════════════════════════════════════════════════════════════════

class NetworkTab(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._box.set_margin_top(16)
        self._box.set_margin_bottom(16)
        self._box.set_margin_start(20)
        self._box.set_margin_end(20)
        self.add(self._box)

        self._build()

    def _build(self):
        b = self._box
        # clear previous
        for child in b.get_children():
            b.remove(child)

        b.pack_start(make_section_label("🌐  Network Interfaces"), False, False, 0)
        b.pack_start(make_separator(), False, False, 0)

        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for iface, addr_list in addrs.items():
                iface_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                iface_box.set_margin_start(8)
                iface_box.set_margin_bottom(8)

                stat = stats.get(iface)
                up_str = "UP" if (stat and stat.isup) else "DOWN"
                speed  = f"{stat.speed} Mbps" if (stat and stat.speed) else "unknown"

                hdr = Gtk.Label()
                hdr.set_markup(
                    f"<b>🔌 {iface}</b>  "
                    f"<span foreground='{'green' if up_str=='UP' else 'red'}'>[{up_str}]</span>"
                    f"  <small>speed: {speed}</small>"
                )
                hdr.set_xalign(0)
                iface_box.pack_start(hdr, False, False, 0)

                import socket as _sock
                AF_INET  = _sock.AF_INET
                AF_INET6 = _sock.AF_INET6

                for addr in addr_list:
                    if addr.family == AF_INET:
                        iface_box.pack_start(
                            info_row("  IPv4", f"{addr.address}  (mask: {addr.netmask})"),
                            False, False, 1
                        )
                    elif addr.family == AF_INET6:
                        iface_box.pack_start(
                            info_row("  IPv6", addr.address),
                            False, False, 1
                        )
                    else:
                        iface_box.pack_start(
                            info_row("  MAC", addr.address),
                            False, False, 1
                        )

                b.pack_start(iface_box, False, False, 0)
        except Exception as e:
            b.pack_start(Gtk.Label(label=f"Could not read interfaces: {e}"), False, False, 0)

        b.pack_start(Gtk.Label(label=""), False, False, 4)
        b.pack_start(make_section_label("📡  Connectivity"), False, False, 0)
        b.pack_start(make_separator(), False, False, 0)

        # Ping test
        ping_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ping_entry = Gtk.Entry()
        ping_entry.set_placeholder_text("Host to ping (e.g. 8.8.8.8)")
        ping_entry.set_text("8.8.8.8")
        ping_btn = Gtk.Button(label="Ping")
        self._ping_result = Gtk.Label(label="")
        self._ping_result.set_selectable(True)
        ping_row.pack_start(ping_entry, True, True, 0)
        ping_row.pack_start(ping_btn,   False, False, 0)
        b.pack_start(ping_row, False, False, 0)
        b.pack_start(self._ping_result, False, False, 2)

        ping_btn.connect("clicked", lambda _, e=ping_entry: self._do_ping(e.get_text()))

        # Refresh button
        refresh_btn = Gtk.Button(label="  ↻  Refresh Interfaces")
        refresh_btn.set_halign(Gtk.Align.START)
        refresh_btn.set_margin_top(12)
        refresh_btn.connect("clicked", lambda _: self._build())
        b.pack_start(refresh_btn, False, False, 0)
        b.show_all()

    def _do_ping(self, host: str):
        host = host.strip()
        if not host:
            return
        self._ping_result.set_text("Pinging…")

        def _worker():
            result = run_cmd(["ping", "-c", "4", "-W", "2", host])
            GLib.idle_add(self._ping_result.set_text, result)

        threading.Thread(target=_worker, daemon=True).start()


# ════════════════════════════════════════════════════════════════
# TAB 4 – Users
# ════════════════════════════════════════════════════════════════

class UsersTab(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(20)
        box.set_margin_end(20)
        self.add(box)

        box.pack_start(make_section_label("👤  Current User"), False, False, 0)
        box.pack_start(make_separator(), False, False, 0)

        current_user = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
        home_dir     = os.path.expanduser("~")
        shell        = os.environ.get("SHELL", "unknown")
        uid          = os.getuid() if hasattr(os, "getuid") else "N/A"

        for label, val in [
            ("Username",    current_user),
            ("UID",         str(uid)),
            ("Home Dir",    home_dir),
            ("Shell",       shell),
        ]:
            box.pack_start(info_row(label, val), False, False, 2)

        box.pack_start(Gtk.Label(label=""), False, False, 4)
        box.pack_start(make_section_label("👥  Logged-in Users"), False, False, 0)
        box.pack_start(make_separator(), False, False, 0)

        # TreeView for logged-in users
        store = Gtk.ListStore(str, str, str, str)
        try:
            for u in psutil.users():
                login_time = datetime.datetime.fromtimestamp(u.started).strftime("%Y-%m-%d %H:%M")
                store.append([u.name, u.terminal or "–", u.host or "local", login_time])
        except Exception:
            store.append(["(unavailable)", "", "", ""])

        tv = Gtk.TreeView(model=store)
        for i, col_name in enumerate(["User", "Terminal", "Host", "Login Time"]):
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(col_name, renderer, text=i)
            col.set_resizable(True)
            tv.append_column(col)

        tv_scroll = Gtk.ScrolledWindow()
        tv_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        tv_scroll.set_min_content_height(120)
        tv_scroll.add(tv)
        box.pack_start(tv_scroll, False, False, 0)

        box.pack_start(Gtk.Label(label=""), False, False, 4)
        box.pack_start(make_section_label("🔐  Password Management"), False, False, 0)
        box.pack_start(make_separator(), False, False, 0)

        note = Gtk.Label(
            label="Use the passwd command in a terminal to change your password."
        )
        note.set_xalign(0)
        note.set_line_wrap(True)
        box.pack_start(note, False, False, 0)

        open_term_btn = Gtk.Button(label="  Open Terminal")
        open_term_btn.set_halign(Gtk.Align.START)
        open_term_btn.set_margin_top(6)
        open_term_btn.connect("clicked", self._open_terminal)
        box.pack_start(open_term_btn, False, False, 0)

    @staticmethod
    def _open_terminal(_btn):
        for terminal in ["x-terminal-emulator", "gnome-terminal", "xterm", "konsole", "alacritty"]:
            try:
                subprocess.Popen([terminal])
                return
            except FileNotFoundError:
                continue


# ════════════════════════════════════════════════════════════════
# TAB 5 – About
# ════════════════════════════════════════════════════════════════

class AboutTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(30)
        self.set_margin_bottom(30)
        self.set_margin_start(40)
        self.set_margin_end(40)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        # Title
        title = Gtk.Label()
        title.set_markup(
            "<span font_size='xx-large' font_weight='bold'>⚙  AmitControl</span>"
        )
        self.pack_start(title, False, False, 0)

        subtitle = Gtk.Label()
        subtitle.set_markup(
            f"<span font_size='large' foreground='gray'>System Control Center for Amit OS</span>"
        )
        self.pack_start(subtitle, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(8)
        sep.set_margin_bottom(8)
        self.pack_start(sep, False, False, 0)

        for label, val in [
            ("Version",   APP_VERSION),
            ("App ID",    APP_ID),
            ("Toolkit",   f"GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"),
            ("Python",    sys.version.split()[0]),
            ("Platform",  platform.platform()),
            ("Author",    "Amit OS Project"),
            ("License",   "MIT"),
        ]:
            row = info_row(label, val)
            row.set_halign(Gtk.Align.CENTER)
            self.pack_start(row, False, False, 2)

        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_margin_top(8)
        self.pack_start(sep2, False, False, 0)

        about_btn = Gtk.Button(label="  About GTK")
        about_btn.set_halign(Gtk.Align.CENTER)
        about_btn.connect("clicked", self._show_about)
        self.pack_start(about_btn, False, False, 0)

    def _show_about(self, _btn):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("AmitControl")
        dialog.set_version(APP_VERSION)
        dialog.set_comments("System Control Center for Amit OS")
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.set_website("https://github.com/amit-os")
        dialog.set_website_label("Amit OS on GitHub")
        dialog.set_authors(["Amit OS Project"])
        dialog.run()
        dialog.destroy()


# ════════════════════════════════════════════════════════════════
# Main Application Window
# ════════════════════════════════════════════════════════════════

class AmitControlWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="AmitControl — System Control Center")
        self.set_default_size(820, 620)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("preferences-system")

        self._apply_css()
        self._build_ui()

    # ── CSS ───────────────────────────────────────────────────────
    def _apply_css(self):
        css = b"""
        window {
            background-color: #1e1e2e;
        }
        notebook tab {
            padding: 6px 14px;
            font-weight: bold;
        }
        notebook tab:checked {
            color: #cba6f7;
            border-bottom: 2px solid #cba6f7;
        }
        .suggested-action {
            background: linear-gradient(135deg, #7c3aed, #a855f7);
            color: white;
            border-radius: 6px;
            padding: 6px 14px;
            border: none;
        }
        .suggested-action:hover {
            background: linear-gradient(135deg, #6d28d9, #9333ea);
        }
        label {
            color: #cdd6f4;
        }
        progressbar trough {
            border-radius: 4px;
            background-color: #313244;
        }
        progressbar progress {
            background: linear-gradient(90deg, #7c3aed, #a855f7);
            border-radius: 4px;
        }
        entry {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 4px 8px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # ── UI skeleton ───────────────────────────────────────────────
    def _build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # Header bar
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title("AmitControl")
        header.set_subtitle("System Control Center")
        self.set_titlebar(header)

        # Refresh button in header
        refresh_btn = Gtk.Button()
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_btn.set_image(refresh_icon)
        refresh_btn.set_tooltip_text("Refresh all data")
        refresh_btn.connect("clicked", lambda _: self._on_refresh())
        header.pack_end(refresh_btn)

        # Notebook (tabs)
        self._notebook = Gtk.Notebook()
        self._notebook.set_tab_pos(Gtk.PositionType.LEFT)
        vbox.pack_start(self._notebook, True, True, 0)

        tabs = [
            ("🖥  System Info",       SystemInfoTab()),
            ("🖥  Display",           DisplaySettingsTab()),
            ("🌐  Network",           NetworkTab()),
            ("👤  Users",             UsersTab()),
            ("ℹ  About",              AboutTab()),
        ]
        self._tabs = {}
        for title, widget in tabs:
            lbl = Gtk.Label(label=title)
            lbl.set_xalign(0)
            lbl.set_size_request(150, -1)
            self._notebook.append_page(widget, lbl)
            self._tabs[title] = widget

        # Status bar
        self._statusbar = Gtk.Statusbar()
        self._statusbar.set_margin_start(4)
        vbox.pack_start(self._statusbar, False, False, 0)
        self._ctx = self._statusbar.get_context_id("main")
        self._update_status()
        GLib.timeout_add_seconds(60, self._update_status)

    def _update_status(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._statusbar.pop(self._ctx)
        self._statusbar.push(self._ctx, f"  Amit OS  |  {now}  |  AmitControl v{APP_VERSION}")
        return True

    def _on_refresh(self):
        """Rebuild the network tab and let GLib handle system-info refresh."""
        net_tab = self._tabs.get("🌐  Network")
        if net_tab:
            net_tab._build()
        self._update_status()


# ════════════════════════════════════════════════════════════════
# GTK Application
# ════════════════════════════════════════════════════════════════

class AmitControlApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", self._on_activate)

    def _on_activate(self, _app):
        win = AmitControlWindow(self)
        win.show_all()


def main():
    app = AmitControlApp()
    exit_code = app.run(sys.argv)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
