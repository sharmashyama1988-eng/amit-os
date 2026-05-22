#!/usr/bin/env python3
"""
AmitSearch - Global Search Bar (Spotlight Style)
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import os, subprocess

CSS = b"""
window {
    background: rgba(13, 17, 23, 0.95);
    border: 2px solid #30363d;
    border-radius: 16px;
}
.search-entry {
    background: transparent;
    color: #e6edf3;
    font-size: 24px;
    border: none;
    padding: 20px;
    caret-color: #58a6ff;
}
.result-item {
    padding: 12px 20px;
    border-bottom: 1px solid #21262d;
    color: #8b949e;
}
.result-item:hover { background: #1f6feb; color: white; }
.result-title { font-size: 16px; font-weight: bold; }
.result-path { font-size: 11px; opacity: 0.7; }
.shortcut-tag { background: #30363d; border-radius: 4px; padding: 2px 6px; font-size: 10px; }
"""

class AmitSearch(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitSearch")
        self.set_default_size(600, -1)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_keep_above(True)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._build()

    def _build(self):
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.vbox)

        # Search Entry
        self.entry = Gtk.Entry()
        self.entry.get_style_context().add_class("search-entry")
        self.entry.set_placeholder_text("Search files, apps, or commands...")
        self.entry.connect("changed", self._on_search)
        self.entry.connect("activate", self._on_activate)
        self.vbox.pack_start(self.entry, False, False, 0)

        # Results List
        self.results_box = Gtk.ListBox()
        self.results_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.vbox.pack_start(self.results_box, True, True, 0)

        self.connect("key-press-event", self._on_key)

    def _on_search(self, entry):
        q = entry.get_text().lower()
        for child in self.results_box.get_children():
            self.results_box.remove(child)
        
        if len(q) < 2: return

        # Search Desktop entries (.desktop files)
        apps = []
        app_dirs = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
        for d in app_dirs:
            if not os.path.exists(d): continue
            for f in os.listdir(d):
                if f.endswith(".desktop"):
                    with open(os.path.join(d, f)) as df:
                        content = df.read()
                        if q in content.lower():
                            name = next((line[5:] for line in content.split("\n") if line.startswith("Name=")), f)
                            exec_cmd = next((line[5:] for line in content.split("\n") if line.startswith("Exec=")), "")
                            apps.append((name, exec_cmd, "App"))
        
        for name, cmd, kind in apps[:8]:
            self._add_result(name, cmd, kind)
        
        self.results_box.show_all()

    def _add_result(self, title, path, kind):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.get_style_context().add_class("result-item")
        
        t = Gtk.Label(label=title, xalign=0)
        t.get_style_context().add_class("result-title")
        
        p = Gtk.Label(label=f"{kind} • {path[:60]}", xalign=0)
        p.get_style_context().add_class("result-path")
        
        box.pack_start(t, False, False, 0)
        box.pack_start(p, False, False, 0)
        row.add(box)
        row._cmd = path
        self.results_box.add(row)

    def _on_activate(self, entry):
        row = self.results_box.get_selected_row()
        if not row:
            row = self.results_box.get_row_at_index(0)
        
        if row:
            cmd = row._cmd.split("%")[0].strip() # Clean KDE/Gnome placeholders
            subprocess.Popen(cmd.split())
            Gtk.main_quit()

    def _on_key(self, w, e):
        key = Gdk.keyval_name(e.keyval)
        if key == "Escape":
            Gtk.main_quit()

def main():
    win = AmitSearch()
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
