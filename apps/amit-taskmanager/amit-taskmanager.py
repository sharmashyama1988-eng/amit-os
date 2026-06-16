#!/usr/bin/env python3
import gi
import psutil
import os
import signal
from gi.repository import Gtk, GLib, Gdk

gi.require_version('Gtk', '3.0')

class ProcessManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitOS Task Manager")
        self.set_default_size(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)

        notebook = Gtk.Notebook()
        self.add(notebook)

        # Dashboard Tab
        dash_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        dash_vbox.set_border_width(20)
        self.cpu_label = Gtk.Label(label="CPU Usage: 0%")
        self.mem_label = Gtk.Label(label="Memory Usage: 0%")
        self.cpu_label.set_halign(Gtk.Align.START)
        self.mem_label.set_halign(Gtk.Align.START)
        
        # Style labels
        self.cpu_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0.47, 1, 1))
        
        dash_vbox.pack_start(self.cpu_label, False, False, 0)
        dash_vbox.pack_start(self.mem_label, False, False, 0)
        notebook.append_page(dash_vbox, Gtk.Label(label="Dashboard"))

        # Processes Tab
        proc_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        proc_vbox.set_border_width(10)
        
        # Search Box
        search_box = Gtk.SearchEntry()
        search_box.connect("search-changed", self.on_search_changed)
        proc_vbox.pack_start(search_box, False, False, 0)
        
        # TreeView
        self.store = Gtk.ListStore(int, str, str, str) # PID, Name, CPU, RAM
        self.filter = self.store.filter_new()
        self.filter.set_visible_func(self.filter_tree)
        self.tree = Gtk.TreeView(model=self.filter)
        
        for i, col_title in enumerate(["PID", "Process Name", "CPU %", "RAM %"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col_title, renderer, text=i)
            self.tree.append_column(column)
            
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.tree)
        proc_vbox.pack_start(scroll, True, True, 0)
        
        # Kill Button
        kill_btn = Gtk.Button(label="End Process")
        kill_btn.connect("clicked", self.on_kill_clicked)
        proc_vbox.pack_start(kill_btn, False, False, 0)
        
        notebook.append_page(proc_vbox, Gtk.Label(label="Processes"))

        self.search_query = ""
        self.update_stats()
        GLib.timeout_add_seconds(2, self.update_stats)

    def filter_tree(self, model, iter, data):
        if not self.search_query:
            return True
        name = model[iter][1].lower()
        return self.search_query in name

    def on_search_changed(self, entry):
        self.search_query = entry.get_text().lower()
        self.filter.refilter()

    def update_stats(self):
        # Update Dash
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        self.cpu_label.set_markup(f"<span size='20000' weight='bold'>CPU Usage:</span> <span size='20000'>{cpu}%</span>")
        self.mem_label.set_markup(f"<span size='20000' weight='bold'>Memory:</span> <span size='20000'>{mem}%</span>")

        # Update Process List
        self.store.clear()
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                self.store.append([
                    p.info['pid'], 
                    p.info['name'], 
                    f"{p.info['cpu_percent']:.1f}", 
                    f"{p.info['memory_percent']:.1f}"
                ])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return True

    def on_kill_clicked(self, button):
        selection = self.tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            pid = model[treeiter][0]
            try:
                os.kill(pid, signal.SIGKILL)
                self.update_stats()
            except ProcessLookupError:
                pass

if __name__ == "__main__":
    win = ProcessManager()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
