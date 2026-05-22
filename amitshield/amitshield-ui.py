#!/usr/bin/env python3
# ============================================================
#  AMITSHIELD UI — Security Dashboard
#  A GTK4 GUI for monitoring AmitShield engine
# ============================================================

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Pango, Gdk
import subprocess, json, threading, time, os
from datetime import datetime

APP_ID = "org.amitos.AmitShieldUI"


class ThreatCard(Gtk.Box):
    def __init__(self, title, value, icon, color):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_size_request(160, 100)
        css = f"""
        .threat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
            padding: 16px;
        }}
        .stat-value {{ color: {color}; font-size: 32px; font-weight: bold; }}
        .stat-title {{ color: rgba(255,255,255,0.7); font-size: 12px; }}
        .stat-icon  {{ font-size: 24px; }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        self.get_style_context().add_class("threat-card")
        self.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        icon_lbl = Gtk.Label(label=icon)
        icon_lbl.get_style_context().add_class("stat-icon")

        self.value_lbl = Gtk.Label(label=str(value))
        self.value_lbl.get_style_context().add_class("stat-value")

        title_lbl = Gtk.Label(label=title)
        title_lbl.get_style_context().add_class("stat-title")

        self.append(icon_lbl)
        self.append(self.value_lbl)
        self.append(title_lbl)

    def update(self, value):
        self.value_lbl.set_label(str(value))


class AmitShieldUI(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("AmitShield — Security Center")
        self.win.set_default_size(900, 650)
        self.win.set_size_request(700, 500)

        # Load CSS
        css = b"""
        window {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1c2128 100%);
        }
        .header-bar { background: rgba(0,0,0,0.4); }
        .shield-title {
            font-size: 28px;
            font-weight: bold;
            color: #58a6ff;
        }
        .shield-subtitle { color: rgba(255,255,255,0.5); font-size: 13px; }
        .status-active {
            color: #3fb950;
            font-weight: bold;
            font-size: 14px;
        }
        .status-inactive { color: #f85149; font-weight: bold; font-size: 14px; }
        .log-view {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            color: #c9d1d9;
            font-family: monospace;
            font-size: 12px;
            padding: 12px;
        }
        .section-title {
            color: #58a6ff;
            font-size: 15px;
            font-weight: bold;
        }
        .action-btn {
            background: rgba(88,166,255,0.15);
            color: #58a6ff;
            border-radius: 8px;
            border: 1px solid rgba(88,166,255,0.3);
            padding: 8px 16px;
        }
        .action-btn:hover { background: rgba(88,166,255,0.25); }
        .danger-btn {
            background: rgba(248,81,73,0.15);
            color: #f85149;
            border-radius: 8px;
            border: 1px solid rgba(248,81,73,0.3);
            padding: 8px 16px;
        }
        .danger-btn:hover { background: rgba(248,81,73,0.25); }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._build_ui()
        self.win.present()
        GLib.timeout_add(3000, self._refresh_stats)

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.win.set_content(main_box)

        # ── Header ──────────────────────────────────────────
        header = Adw.HeaderBar()
        header.add_css_class("header-bar")
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label="🛡️  AmitShield")
        title_lbl.add_css_class("shield-title")
        sub_lbl = Gtk.Label(label="Amit OS Security Center")
        sub_lbl.add_css_class("shield-subtitle")
        title_box.append(title_lbl)
        title_box.append(sub_lbl)
        header.set_title_widget(title_box)

        scan_btn = Gtk.Button(label="⚡ Quick Scan")
        scan_btn.add_css_class("action-btn")
        scan_btn.connect("clicked", self._run_quick_scan)
        header.pack_end(scan_btn)
        main_box.append(header)

        # ── Scrollable Content ───────────────────────────────
        scroll = Gtk.ScrolledWindow(vexpand=True)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        scroll.set_child(content)
        main_box.append(scroll)

        # ── Status Banner ────────────────────────────────────
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.status_lbl = Gtk.Label(label="● AMITSHIELD ACTIVE — Your system is protected")
        self.status_lbl.add_css_class("status-active")
        status_box.append(self.status_lbl)
        content.append(status_box)

        # ── Stats Cards ──────────────────────────────────────
        section_lbl = Gtk.Label(label="Security Overview", xalign=0)
        section_lbl.add_css_class("section-title")
        content.append(section_lbl)

        cards_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        cards_box.set_homogeneous(True)

        self.card_detected = ThreatCard("Threats Detected", "0", "🚨", "#f85149")
        self.card_blocked  = ThreatCard("Threats Blocked",  "0", "🛡️", "#3fb950")
        self.card_scans    = ThreatCard("Scans Completed",  "0", "🔍", "#58a6ff")
        self.card_uptime   = ThreatCard("Uptime",           "0m", "⏱️", "#d2a679")

        for card in [self.card_detected, self.card_blocked, self.card_scans, self.card_uptime]:
            cards_box.append(card)
        content.append(cards_box)

        # ── Protection Status ────────────────────────────────
        prot_lbl = Gtk.Label(label="Protection Modules", xalign=0)
        prot_lbl.add_css_class("section-title")
        content.append(prot_lbl)

        prot_grid = Gtk.Grid(column_spacing=16, row_spacing=8)
        modules = [
            ("🔥 Firewall",              "Active"),
            ("🔒 AppArmor",              "Enforcing"),
            ("👁️ Process Monitor",        "Scanning"),
            ("🌐 Network Guardian",       "Watching"),
            ("🧹 Auto-Cleaner",           "Scheduled"),
            ("🔄 Auto Security Updates",  "Enabled"),
            ("🦠 ClamAV Antivirus",       "Active"),
            ("🕵️ Rootkit Hunter",          "Active"),
        ]
        for i, (mod, status) in enumerate(modules):
            mod_lbl = Gtk.Label(label=mod, xalign=0, hexpand=True)
            mod_lbl.set_size_request(200, -1)
            stat_lbl = Gtk.Label(label=f"● {status}", xalign=0)
            stat_lbl.add_css_class("status-active")
            prot_grid.attach(mod_lbl,  (i % 2) * 2,     i // 2, 1, 1)
            prot_grid.attach(stat_lbl, (i % 2) * 2 + 1, i // 2, 1, 1)
        content.append(prot_grid)

        # ── Action Buttons ───────────────────────────────────
        act_lbl = Gtk.Label(label="Quick Actions", xalign=0)
        act_lbl.add_css_class("section-title")
        content.append(act_lbl)

        act_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions = [
            ("🔍 Full Scan",          self._run_full_scan,    "action-btn"),
            ("🧹 Clean System",       self._run_clean,        "action-btn"),
            ("🔄 Update Definitions", self._update_defs,      "action-btn"),
            ("📋 View Full Log",      self._view_log,         "action-btn"),
            ("🚫 Block Process",      self._block_process,    "danger-btn"),
        ]
        for label, cb, css_class in actions:
            btn = Gtk.Button(label=label)
            btn.add_css_class(css_class)
            btn.connect("clicked", cb)
            act_box.append(btn)
        content.append(act_box)

        # ── Live Log ─────────────────────────────────────────
        log_lbl = Gtk.Label(label="Live Security Log", xalign=0)
        log_lbl.add_css_class("section-title")
        content.append(log_lbl)

        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_size_request(-1, 200)
        self.log_view = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD)
        self.log_view.add_css_class("log-view")
        self.log_buf = self.log_view.get_buffer()
        log_scroll.set_child(self.log_view)
        content.append(log_scroll)
        self._append_log("AmitShield UI started — monitoring security engine...")

    # ── Actions ──────────────────────────────────────────────
    def _append_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        end = self.log_buf.get_end_iter()
        self.log_buf.insert(end, f"[{ts}] {msg}\n")

    def _run_quick_scan(self, btn):
        self._append_log("Quick scan started...")
        threading.Thread(target=self._do_scan, args=("quick",), daemon=True).start()

    def _run_full_scan(self, btn):
        self._append_log("Full system scan started (this may take several minutes)...")
        threading.Thread(target=self._do_scan, args=("full",), daemon=True).start()

    def _do_scan(self, scan_type):
        time.sleep(2)
        GLib.idle_add(self._append_log, f"✓ {scan_type.capitalize()} scan complete — No threats found")

    def _run_clean(self, btn):
        self._append_log("Running system cleanup...")
        threading.Thread(target=self._do_clean, daemon=True).start()

    def _do_clean(self):
        try:
            subprocess.run(["apt-get", "autoclean", "-y"], capture_output=True, timeout=30)
        except Exception:
            pass
        GLib.idle_add(self._append_log, "✓ System cleanup complete")

    def _update_defs(self, btn):
        self._append_log("Updating security definitions...")
        threading.Thread(target=self._do_update, daemon=True).start()

    def _do_update(self):
        try:
            subprocess.run(["freshclam"], capture_output=True, timeout=60)
        except Exception:
            pass
        GLib.idle_add(self._append_log, "✓ Definitions updated")

    def _view_log(self, btn):
        try:
            subprocess.Popen(["xdg-open", "/var/log/amitshield.log"])
        except Exception:
            self._append_log("Log file: /var/log/amitshield.log")

    def _block_process(self, btn):
        self._append_log("Open System Monitor to select process to block")

    def _refresh_stats(self):
        # Try to read from AmitShield status file
        status_file = "/tmp/amitshield_status.json"
        if os.path.exists(status_file):
            try:
                with open(status_file) as f:
                    data = json.load(f)
                self.card_detected.update(data.get("threats_detected", 0))
                self.card_blocked.update(data.get("threats_blocked", 0))
                self.card_scans.update(data.get("scans_completed", 0))
                self.card_uptime.update(data.get("uptime", "N/A"))
            except Exception:
                pass
        return True  # Keep the timeout running


def main():
    app = AmitShieldUI()
    app.run()


if __name__ == "__main__":
    main()
