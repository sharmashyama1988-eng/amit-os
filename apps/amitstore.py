#!/usr/bin/env python3
"""
AmitStore - App Store
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import subprocess, threading, shutil

CSS = b"""
* { font-family: 'Noto Sans', sans-serif; }
window { background: #0d1117; }
.sidebar { background: #161b22; border-right: 1px solid #30363d; min-width: 160px; }
.cat-btn {
    background: transparent;
    color: #8b949e;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 14px;
    text-align: left;
}
.cat-btn:hover { background: #21262d; color: #e6edf3; }
.cat-btn.active { background: #1f6feb; color: #ffffff; }
.header { background: #161b22; padding: 14px 20px; border-bottom: 1px solid #30363d; }
.header-title { color: #e6edf3; font-size: 20px; font-weight: bold; }
.search-entry {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
}
.app-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px;
    margin: 6px;
}
.app-card:hover { border-color: #58a6ff; }
.app-name { color: #e6edf3; font-size: 15px; font-weight: bold; }
.app-desc { color: #8b949e; font-size: 12px; }
.app-cat  { color: #58a6ff; font-size: 11px; }
.btn-install {
    background: #1f6feb;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: bold;
}
.btn-install:hover { background: #388bfd; }
.btn-remove {
    background: #21262d;
    color: #f85149;
    border-radius: 8px;
    border: 1px solid #f85149;
    padding: 6px 16px;
    font-size: 13px;
}
.btn-remove:hover { background: #3d1f1f; }
.status-bar { background: #161b22; padding: 6px 16px; border-top: 1px solid #30363d; }
.status-text { color: #8b949e; font-size: 12px; }
"""

APPS = [
    ("firefox",       "Firefox Browser",     "Fast, private web browser",          "Internet",   "firefox"),
    ("libreoffice",   "LibreOffice Suite",   "Complete office suite",               "Office",     "libreoffice"),
    ("gimp",          "GIMP Image Editor",   "Professional photo editing",          "Graphics",   "gimp"),
    ("blender",       "Blender 3D",          "3D creation and animation",           "Graphics",   "blender"),
    ("inkscape",      "Inkscape SVG Editor", "Vector graphics editor",              "Graphics",   "inkscape"),
    ("obs-studio",    "OBS Studio",          "Screen recorder and streaming",       "Media",      "obs-studio"),
    ("audacity",      "Audacity",            "Audio recording and editing",         "Media",      "audacity"),
    ("mpv",           "MPV Player",          "Lightweight media player",            "Media",      "mpv"),
    ("transmission",  "Transmission",        "BitTorrent client",                   "Internet",   "transmission-gtk"),
    ("thunderbird",   "Thunderbird Mail",    "Email client by Mozilla",             "Internet",   "thunderbird"),
    ("code",          "VS Code",             "Code editor by Microsoft",            "Development","code"),
    ("vim",           "Vim Editor",          "Powerful terminal text editor",       "Development","vim"),
    ("git",           "Git",                 "Version control system",              "Development","git"),
    ("python3-pip",   "Python PIP",          "Python package manager",              "Development","pip3"),
    ("nodejs",        "Node.js",             "JavaScript runtime",                  "Development","node"),
    ("docker.io",     "Docker",              "Container platform",                  "Development","docker"),
    ("virtualbox",    "VirtualBox",          "Run virtual machines",                "System",     "virtualbox"),
    ("timeshift",     "Timeshift",           "System backup and restore",           "System",     "timeshift"),
    ("stacer",        "Stacer",              "System optimizer and monitor",        "System",     "stacer"),
    ("gparted",       "GParted",             "Disk partition manager",              "System",     "gparted"),
    ("baobab",        "Disk Analyzer",       "Visualize disk usage",                "System",     "baobab"),
    ("lutris",        "Lutris",              "Game manager for Linux",              "Games",      "lutris"),
    ("steam",         "Steam",               "Gaming platform",                     "Games",      "steam"),
    ("discord",       "Discord",             "Voice and text chat",                 "Internet",   "discord"),
    ("telegram-desktop","Telegram",          "Messaging app",                       "Internet",   "telegram-desktop"),
]

CATS = ["All","Internet","Office","Graphics","Media","Development","System","Games"]


class AmitStore(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitStore")
        self.set_default_size(900, 600)
        self._installed = set()
        self._cat       = "All"
        self._query     = ""

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._check_installed()
        self._build()

    def _check_installed(self):
        for app in APPS:
            pkg = app[0]
            if shutil.which(app[-1]) or shutil.which(pkg):
                self._installed.add(pkg)

    def _build(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        hdr.get_style_context().add_class("header")
        title = Gtk.Label(label="AmitStore")
        title.get_style_context().add_class("header-title")
        self.search = Gtk.Entry(placeholder_text="Search apps...")
        self.search.get_style_context().add_class("search-entry")
        self.search.set_size_request(260, -1)
        self.search.connect("changed", self._on_search)
        hdr.pack_start(title,       False, False, 0)
        hdr.pack_end(self.search,   False, False, 0)
        vbox.pack_start(hdr, False, False, 0)

        # Body
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(body, True, True, 0)

        # Sidebar categories
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sidebar.get_style_context().add_class("sidebar")
        sidebar.set_margin_top(8)
        self.cat_btns = {}
        for cat in CATS:
            btn = Gtk.Button(label=cat)
            btn.get_style_context().add_class("cat-btn")
            if cat == "All":
                btn.get_style_context().add_class("active")
            btn.connect("clicked", self._on_cat, cat)
            self.cat_btns[cat] = btn
            sidebar.pack_start(btn, False, False, 0)
        body.pack_start(sidebar, False, False, 0)

        # App grid
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.flow = Gtk.FlowBox(
            max_children_per_line=3,
            min_children_per_line=1,
            selection_mode=Gtk.SelectionMode.NONE,
            column_spacing=4, row_spacing=4,
            homogeneous=False
        )
        self.flow.set_margin_top(8)
        self.flow.set_margin_start(8)
        self.flow.set_margin_end(8)
        scroll.add(self.flow)
        body.pack_start(scroll, True, True, 0)

        # Status bar
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.status_bar.get_style_context().add_class("status-bar")
        self.status_lbl = Gtk.Label(label="Ready", xalign=0)
        self.status_lbl.get_style_context().add_class("status-text")
        self.status_bar.pack_start(self.status_lbl, True, True, 0)
        vbox.pack_start(self.status_bar, False, False, 0)

        self._render_apps()

    def _make_app_card(self, pkg, name, desc, cat, cmd):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("app-card")
        card.set_size_request(250, -1)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        icon = Gtk.Label(label=self._emoji(cat))
        icon.set_markup(f'<span font="22">{self._emoji(cat)}</span>')

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        nm = Gtk.Label(label=name, xalign=0)
        nm.get_style_context().add_class("app-name")
        nm.set_ellipsize(Pango.EllipsizeMode.END)
        ct = Gtk.Label(label=cat, xalign=0)
        ct.get_style_context().add_class("app-cat")
        info.pack_start(nm, False, False, 0)
        info.pack_start(ct, False, False, 0)
        top.pack_start(icon, False, False, 0)
        top.pack_start(info, True,  True,  0)
        card.pack_start(top, False, False, 0)

        ds = Gtk.Label(label=desc, xalign=0, wrap=True)
        ds.get_style_context().add_class("app-desc")
        card.pack_start(ds, False, False, 0)

        installed = pkg in self._installed
        btn = Gtk.Button(label="Remove" if installed else "Install")
        btn.get_style_context().add_class("btn-remove" if installed else "btn-install")
        btn.connect("clicked", self._on_action, pkg, name, installed, btn)
        card.pack_start(btn, False, False, 0)
        return card

    def _emoji(self, cat):
        return {"Internet":"🌐","Office":"📄","Graphics":"🎨",
                "Media":"🎵","Development":"💻","System":"⚙️",
                "Games":"🎮"}.get(cat, "📦")

    def _render_apps(self):
        for child in self.flow.get_children():
            self.flow.remove(child)
        q = self._query.lower()
        count = 0
        for app in APPS:
            pkg, name, desc, cat, cmd = app
            if self._cat != "All" and cat != self._cat: continue
            if q and q not in name.lower() and q not in desc.lower(): continue
            card = self._make_app_card(*app)
            self.flow.add(card)
            count += 1
        self.flow.show_all()
        self.status_lbl.set_text(f"{count} apps found  |  {len(self._installed)} installed")

    def _on_cat(self, btn, cat):
        for b in self.cat_btns.values():
            b.get_style_context().remove_class("active")
        btn.get_style_context().add_class("active")
        self._cat = cat
        self._render_apps()

    def _on_search(self, entry):
        self._query = entry.get_text()
        self._render_apps()

    def _on_action(self, btn, pkg, name, installed, button):
        if installed:
            self._run_apt("remove", pkg, name, button)
        else:
            self._run_apt("install", pkg, name, button)

    def _run_apt(self, action, pkg, name, btn):
        btn.set_sensitive(False)
        self.status_lbl.set_text(f"{'Installing' if action=='install' else 'Removing'} {name}...")

        def worker():
            try:
                subprocess.run(
                    ["pkexec", "apt-get", action, "-y", pkg],
                    capture_output=True, timeout=300)
                GLib.idle_add(self._post_action, pkg, action, btn)
            except Exception as e:
                GLib.idle_add(self.status_lbl.set_text, f"Error: {e}")
                GLib.idle_add(btn.set_sensitive, True)

        threading.Thread(target=worker, daemon=True).start()

    def _post_action(self, pkg, action, btn):
        if action == "install":
            self._installed.add(pkg)
        else:
            self._installed.discard(pkg)
        btn.set_sensitive(True)
        self.status_lbl.set_text(f"Done! Package {pkg} {action}ed.")
        self._render_apps()


def main():
    win = AmitStore()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
