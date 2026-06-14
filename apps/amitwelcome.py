#!/usr/bin/env python3
"""
AmitWelcome - Welcome & Onboarding Screen
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import subprocess, os

CSS = b"""
* { font-family: 'Noto Sans', sans-serif; }
window {
    background: linear-gradient(135deg, #0d1117 0%, #1a1a2e 100%);
}
.os-logo  { color: #58a6ff; font-size: 64px; font-weight: 900; }
.os-tag   { color: #8b949e; font-size: 16px; letter-spacing: 3px; }
.section-title { color: #e6edf3; font-size: 18px; font-weight: bold; margin-top: 16px; }
.feat-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 20px;
    margin: 6px;
}
.feat-icon  { font-size: 32px; }
.feat-title { color: #e6edf3; font-size: 14px; font-weight: bold; margin-top: 4px; }
.feat-desc  { color: #8b949e; font-size: 12px; }
.btn-primary {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 12px 32px;
    font-size: 15px;
    font-weight: bold;
}
.btn-primary:hover { background: #388bfd; }
.btn-secondary {
    background: transparent;
    color: #58a6ff;
    border-radius: 10px;
    border: 1px solid #30363d;
    padding: 12px 24px;
    font-size: 14px;
}
.btn-secondary:hover { background: rgba(88,166,255,0.1); }
.step-num {
    background: #1f6feb;
    color: white;
    border-radius: 50%;
    font-size: 14px;
    font-weight: bold;
    min-width: 28px;
    min-height: 28px;
}
.step-text { color: #8b949e; font-size: 13px; }
.version-tag { color: #30363d; font-size: 11px; }
"""

FEATURES = [
    ("🛡️", "AmitShield",        "Built-in security engine\nprotects in real time"),
    ("⚡", "Blazing Fast",      "Optimized kernel & desktop\nfor maximum speed"),
    ("🎨", "Beautiful UI",      "Dark theme with KDE Plasma\nWindows-like experience"),
    ("📦", "15+ Apps Ready",    "Calculator, Browser, Notes\nMedia, Office & more"),
    ("🔒", "Secure by Default", "Firewall, AppArmor, Fail2Ban\nall pre-configured"),
    ("🔄", "Auto Updates",      "Security patches applied\nautomatically"),
]

PERSONAS = [
    ("🎮", "Gamer",      "Steam, Lutris, Discord, GPU Drivers", "steam lutris discord-canary"),
    ("💻", "Developer",  "VS Code, Git, Docker, Node.js, Vim",   "code git docker.io nodejs vim"),
    ("🎨", "Creative",   "GIMP, Blender, OBS, Inkscape",        "gimp blender obs-studio inkscape"),
    ("📚", "Student",    "LibreOffice, Zoom, PDF, AmitNotes",   "libreoffice zoom-client okular"),
    ("🛡️", "Privacy",    "Tor, VPN, AmitShield Max",            "torbrowser-launcher openvpn"),
]

QUICK_STARTS = [
    ("1", "Open AmitBrowser",   "chromium --no-sandbox"),
    ("2", "Open AmitFiles",     "dolphin"),
    ("3", "Open AmitShield",    "python3 /usr/local/bin/amitshield-ui.py"),
    ("4", "Open AmitStore",     "python3 /usr/local/bin/amitstore.py"),
]

class AmitWelcome(Gtk.Window):
    def __init__(self):
        super().__init__(title="Welcome to Amit OS")
        self.set_default_size(800, 560)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._page = 0
        self._build()

    def _build(self):
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self._stack.set_transition_duration(300)
        self.add(self._stack)

        self._stack.add_named(self._page_welcome(),    "welcome")
        self._stack.add_named(self._page_persona(),    "persona")
        self._stack.add_named(self._page_features(),   "features")
        self._stack.add_named(self._page_quickstart(), "quickstart")

    # ── Pages ─────────────────────────────────────────────────
    def _page_persona(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24); box.set_margin_start(32); box.set_margin_end(32)

        title = Gtk.Label(label="Choose Your Persona")
        title.get_style_context().add_class("section-title")
        box.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Amit OS will automatically install the best tools for your needs.\nNo bloatware, only what you choose.")
        desc.get_style_context().add_class("step-text")
        box.pack_start(desc, False, False, 0)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)
        self.persona_btns = []
        for i, (icon, name, d, pkgs) in enumerate(PERSONAS):
            btn = Gtk.ToggleButton()
            btn.get_style_context().add_class("feat-card")
            
            b_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            ic = Gtk.Label(label=icon); ic.get_style_context().add_class("feat-icon")
            nm = Gtk.Label(label=name); nm.get_style_context().add_class("feat-title")
            ds = Gtk.Label(label=d, wrap=True); ds.get_style_context().add_class("feat-desc")
            
            b_box.pack_start(ic, False, False, 0)
            b_box.pack_start(nm, False, False, 0)
            b_box.pack_start(ds, False, False, 0)
            btn.add(b_box)
            btn._pkgs = pkgs
            btn._name = name
            grid.attach(btn, i % 3, i // 3, 1, 1)
            self.persona_btns.append(btn)

        box.pack_start(grid, True, True, 0)

        self.apply_btn = Gtk.Button(label="Apply Persona & Continue →")
        self.apply_btn.get_style_context().add_class("btn-primary")
        self.apply_btn.connect("clicked", self._apply_persona)
        box.pack_start(self.apply_btn, False, False, 12)
        
        return box

    def _apply_persona(self, btn):
        selected = [b for b in self.persona_btns if b.get_active()]
        if not selected:
            self._next()
            return
        
        all_pkgs = " ".join([b._pkgs for b in selected])
        self.apply_btn.set_sensitive(False)
        self.apply_btn.set_label("Setting up your Amit OS... Please wait.")
        
        def worker():
            # In a real ISO, this would run pkexec apt install
            # subprocess.run(["pkexec", "apt-get", "install", "-y", all_pkgs])
            GLib.idle_add(self._next)
            
        threading.Thread(target=worker, daemon=True).start()

    def _page_welcome(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(40)
        box.set_margin_bottom(40)

        logo = Gtk.Label(label="Amit OS")
        logo.get_style_context().add_class("os-logo")

        tag = Gtk.Label(label="FAST  •  SECURE  •  BEAUTIFUL")
        tag.get_style_context().add_class("os-tag")

        ver = Gtk.Label(label="Version 1.0 — Based on Debian 12 Bookworm")
        ver.get_style_context().add_class("version-tag")

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_size_request(300, 1)

        desc = Gtk.Label(
            label="Welcome! Amit OS gives you the power of Linux\n"
                  "with the comfort of a modern Windows-like experience.\n"
                  "AmitShield is already protecting your system.",
            justify=Gtk.Justification.CENTER
        )
        desc.get_style_context().add_class("step-text")

        btn = Gtk.Button(label="Get Started  →")
        btn.get_style_context().add_class("btn-primary")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._next)

        box.pack_start(logo, False, False, 0)
        box.pack_start(tag,  False, False, 0)
        box.pack_start(ver,  False, False, 0)
        box.pack_start(sep,  False, False, 8)
        box.pack_start(desc, False, False, 0)
        box.pack_start(btn,  False, False, 16)
        return box

    def _page_features(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24)
        box.set_margin_start(32)
        box.set_margin_end(32)
        box.set_margin_bottom(16)

        title = Gtk.Label(label="What's included in Amit OS")
        title.get_style_context().add_class("section-title")
        box.pack_start(title, False, False, 0)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)
        for i, (icon, name, desc) in enumerate(FEATURES):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.get_style_context().add_class("feat-card")

            ic = Gtk.Label(label=icon)
            ic.get_style_context().add_class("feat-icon")
            ic.set_xalign(0)

            nm = Gtk.Label(label=name, xalign=0)
            nm.get_style_context().add_class("feat-title")

            ds = Gtk.Label(label=desc, xalign=0, wrap=True)
            ds.get_style_context().add_class("feat-desc")

            card.pack_start(ic, False, False, 0)
            card.pack_start(nm, False, False, 0)
            card.pack_start(ds, False, False, 0)
            grid.attach(card, i % 3, i // 3, 1, 1)

        box.pack_start(grid, True, True, 0)

        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btns.set_halign(Gtk.Align.CENTER)

        back = Gtk.Button(label="← Back")
        back.get_style_context().add_class("btn-secondary")
        back.connect("clicked", self._prev)

        nxt = Gtk.Button(label="Quick Start  →")
        nxt.get_style_context().add_class("btn-primary")
        nxt.connect("clicked", self._next)

        btns.pack_start(back, False, False, 0)
        btns.pack_start(nxt,  False, False, 0)
        box.pack_start(btns, False, False, 8)
        return box

    def _page_quickstart(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(32)
        box.set_margin_start(80)
        box.set_margin_end(80)
        box.set_margin_bottom(24)

        title = Gtk.Label(label="Launch your first app")
        title.get_style_context().add_class("section-title")
        box.pack_start(title, False, False, 0)

        for num, label, cmd in QUICK_STARTS:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            row.set_margin_top(4)

            num_lbl = Gtk.Label(label=num)
            num_lbl.get_style_context().add_class("step-num")
            num_lbl.set_size_request(28, 28)

            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("btn-secondary")
            btn.set_hexpand(True)
            btn.connect("clicked", self._launch, cmd)

            row.pack_start(num_lbl, False, False, 0)
            row.pack_start(btn,     True,  True,  0)
            box.pack_start(row, False, False, 0)

        done_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        done_box.set_halign(Gtk.Align.CENTER)
        done_box.set_margin_top(16)

        back = Gtk.Button(label="← Back")
        back.get_style_context().add_class("btn-secondary")
        back.connect("clicked", self._prev)

        done = Gtk.Button(label="Start Using Amit OS!")
        done.get_style_context().add_class("btn-primary")
        done.connect("clicked", Gtk.main_quit)

        chk = Gtk.CheckButton(label="Don't show on startup")
        chk.get_style_context().add_class("step-text")

        done_box.pack_start(back, False, False, 0)
        done_box.pack_start(done, False, False, 0)
        box.pack_start(done_box, False, False, 0)
        box.pack_start(chk,      False, False, 0)
        return box

    def _next(self, *_):
        pages = ["welcome","persona","features","quickstart"]
        self._page = min(self._page + 1, len(pages) - 1)
        self._stack.set_visible_child_name(pages[self._page])

    def _prev(self, *_):
        pages = ["welcome","persona","features","quickstart"]
        self._page = max(self._page - 1, 0)
        self._stack.set_visible_child_name(pages[self._page])

    def _launch(self, btn, cmd):
        try:
            subprocess.Popen(cmd.split())
        except Exception:
            pass


def main():
    win = AmitWelcome()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
