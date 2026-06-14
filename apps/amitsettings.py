#!/usr/bin/env python3
"""
AmitSettings - System Configuration Hub
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import subprocess, os

CSS = b"""
* { font-family: 'Noto Sans', sans-serif; }
window { background: #0d1117; }
.sidebar { background: #161b22; border-right: 1px solid #30363d; min-width: 200px; }
.header { background: #161b22; padding: 20px; border-bottom: 1px solid #30363d; }
.header-title { color: #58a6ff; font-size: 24px; font-weight: bold; }
.nav-btn {
    background: transparent;
    color: #8b949e;
    border: none;
    padding: 12px 20px;
    font-size: 14px;
    text-align: left;
    border-radius: 8px;
    margin: 2px 8px;
}
.nav-btn:hover { background: #21262d; color: #e6edf3; }
.nav-btn.active { background: #1f6feb; color: white; }
.content-area { padding: 30px; }
.setting-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.setting-title { color: #e6edf3; font-size: 16px; font-weight: bold; }
.setting-desc  { color: #8b949e; font-size: 13px; }
.action-btn {
    background: #21262d;
    color: #58a6ff;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
}
.action-btn:hover { background: #30363d; }
.section-label { color: #8b949e; font-size: 11px; font-weight: bold; margin: 20px 0 8px 20px; letter-spacing: 1px; }
"""

class AmitSettings(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitSettings")
        self.set_default_size(900, 600)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._build()

    def _build(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(hbox)

        # ── Sidebar ──────────────────────────────────────────
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.get_style_context().add_class("sidebar")
        
        logo_lbl = Gtk.Label(label="Amit OS")
        logo_lbl.get_style_context().add_class("header-title")
        logo_lbl.set_margin_top(20)
        logo_lbl.set_margin_bottom(20)
        sidebar.pack_start(logo_lbl, False, False, 0)

        sections = [
            ("Personalization", ["Wallpaper", "Themes", "Icons", "Taskbar"]),
            ("System", ["Display", "Sound", "Power", "Storage"]),
            ("Network", ["WiFi", "Bluetooth", "VPN"]),
            ("Security", ["AmitShield", "Firewall", "Users"]),
            ("About", ["System Info", "Updates"])
        ]

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)

        for sec_name, items in sections:
            lbl = Gtk.Label(label=sec_name.upper())
            lbl.get_style_context().add_class("section-label")
            sidebar.pack_start(lbl, False, False, 0)
            
            for item in items:
                btn = Gtk.Button(label=f"  {item}")
                btn.get_style_context().add_class("nav-btn")
                btn.connect("clicked", self._on_nav, item)
                sidebar.pack_start(btn, False, False, 0)
                
                # Create a placeholder page for each
                self.stack.add_named(self._create_page(item), item)

        hbox.pack_start(sidebar, False, False, 0)

        # ── Main Content ─────────────────────────────────────
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hdr.get_style_context().add_class("header")
        self.title_lbl = Gtk.Label(label="Personalization")
        self.title_lbl.get_style_context().add_class("header-title")
        hdr.pack_start(self.title_lbl, False, False, 0)
        main_vbox.pack_start(hdr, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.stack)
        main_vbox.pack_start(scroll, True, True, 0)

        hbox.pack_start(main_vbox, True, True, 0)

    def _create_page(self, name):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.get_style_context().add_class("content-area")
        
        # Add some sample settings based on name
        if name == "Wallpaper":
            self._add_setting(vbox, "Desktop Wallpaper", "Change the background image of your desktop", "systemsettings5 kcm_wallpaper")
            self._add_setting(vbox, "Lock Screen", "Configure the image shown when the system is locked", "systemsettings5 kcm_screenlocker")
        elif name == "WiFi":
            self._add_setting(vbox, "Wireless Networks", "Connect to WiFi and manage saved networks", "nm-connection-editor")
        elif name == "AmitShield":
            self._add_setting(vbox, "Security Engine", "Configure real-time protection and scanning", "python3 /usr/local/bin/amitshield-ui.py")
        elif name == "Display":
            self._add_setting(vbox, "Resolution & Scaling", "Adjust screen size and orientation", "systemsettings5 kcm_kscreen")
        else:
            self._add_setting(vbox, f"Configure {name}", f"Launch the official system module for {name}", f"systemsettings5 kcm_{name.lower()}")

        return vbox

    def _add_setting(self, parent, title, desc, cmd):
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        card.get_style_context().add_class("setting-card")
        
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        t = Gtk.Label(label=title, xalign=0)
        t.get_style_context().add_class("setting-title")
        d = Gtk.Label(label=desc, xalign=0)
        d.get_style_context().add_class("setting-desc")
        info.pack_start(t, False, False, 0)
        info.pack_start(d, False, False, 0)
        
        btn = Gtk.Button(label="Open")
        btn.get_style_context().add_class("action-btn")
        btn.set_valign(Gtk.Align.CENTER)
        def run_cmd(*_):
            try:
                subprocess.Popen(cmd.split())
            except Exception:
                pass
        btn.connect("clicked", run_cmd)
        
        card.pack_start(info, True, True, 0)
        card.pack_start(btn, False, False, 0)
        parent.pack_start(card, False, False, 0)

    def _on_nav(self, btn, item):
        self.title_lbl.set_label(item)
        self.stack.set_visible_child_name(item)


def main():
    win = AmitSettings()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
