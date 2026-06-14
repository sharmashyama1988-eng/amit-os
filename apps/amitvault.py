#!/usr/bin/env python3
"""
AmitVault - Private File Locker
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import os, subprocess, hashlib

CSS = b"""
window { background: #0d1117; }
.vault-header { background: #161b22; padding: 20px; border-bottom: 2px solid #30363d; }
.vault-title { color: #58a6ff; font-size: 24px; font-weight: bold; }
.lock-icon { font-size: 64px; margin: 40px; color: #8b949e; }
.pin-entry { background: #21262d; color: white; font-size: 32px; border: 1px solid #30363d; border-radius: 12px; padding: 10px; }
.btn-unlock { background: #1f6feb; color: white; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 16px; }
.btn-unlock:hover { background: #388bfd; }
"""

VAULT_DIR = os.path.expanduser("~/.amitvault")
os.makedirs(VAULT_DIR, exist_ok=True)

class AmitVault(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitVault")
        self.set_default_size(400, 500)
        self.set_position(Gtk.WindowPosition.CENTER)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._is_locked = True
        self._build_lock_screen()

    def _build_lock_screen(self):
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.add(self.vbox)

        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hdr.get_style_context().add_class("vault-header")
        t = Gtk.Label(label="AmitVault")
        t.get_style_context().add_class("vault-title")
        hdr.pack_start(t, True, True, 0)
        self.vbox.pack_start(hdr, False, False, 0)

        icon = Gtk.Label(label="🔒")
        icon.get_style_context().add_class("lock-icon")
        self.vbox.pack_start(icon, False, False, 0)

        self.pin = Gtk.Entry()
        self.pin.set_visibility(False)
        self.pin.set_placeholder_text("Enter Vault PIN")
        self.pin.set_halign(Gtk.Align.CENTER)
        self.pin.get_style_context().add_class("pin-entry")
        self.pin.set_width_chars(6)
        self.pin.connect("activate", self._on_unlock)
        self.vbox.pack_start(self.pin, False, False, 0)

        btn = Gtk.Button(label="Unlock Vault")
        btn.get_style_context().add_class("btn-unlock")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._on_unlock)
        self.vbox.pack_start(btn, False, False, 0)

    def _on_unlock(self, btn):
        pin = self.pin.get_text()
        # Default pin is 1234 for demo, in real OS this would be set by user
        if pin == "1234":
            self._show_files()
        else:
            self.pin.set_text("")
            self.pin.set_placeholder_text("Wrong PIN!")

    def _show_files(self):
        # Remove lock screen UI
        for child in self.vbox.get_children():
            self.vbox.remove(child)
        
        lbl = Gtk.Label(label="Vault Unlocked ✅")
        lbl.get_style_context().add_class("vault-title")
        lbl.set_margin_top(20)
        self.vbox.pack_start(lbl, False, False, 0)

        # Open vault directory in File Manager
        try:
            subprocess.Popen(["dolphin", VAULT_DIR])
        except Exception:
            pass
        
        btn = Gtk.Button(label="Lock Vault Now")
        btn.get_style_context().add_class("btn-unlock")
        btn.set_margin_top(40)
        btn.connect("clicked", lambda _: Gtk.main_quit())
        self.vbox.pack_start(btn, False, False, 0)
        
        self.vbox.show_all()

def main():
    win = AmitVault()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
