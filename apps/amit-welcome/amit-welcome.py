#!/usr/bin/env python3
import gi
import os
import subprocess

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class WelcomeWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Welcome to Amit OS 1.0")
        self.set_default_size(600, 400)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(20)
        self.add(vbox)
        
        # Header Label
        header_label = Gtk.Label()
        header_label.set_markup("<span size='xx-large' weight='bold'>Welcome to Amit OS 1.0</span>")
        vbox.pack_start(header_label, False, False, 10)
        
        # Subheader
        subheader = Gtk.Label(label="Your secure, fast, and customizable operating system.")
        vbox.pack_start(subheader, False, False, 5)
        
        # Notebook for tabs
        notebook = Gtk.Notebook()
        vbox.pack_start(notebook, True, True, 0)
        
        # Tab 1: Getting Started
        tab1_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        tab1_vbox.set_border_width(15)
        
        lbl1 = Gtk.Label(label="Get to know Amit OS and its features. \nUse the tools below to start your journey.")
        lbl1.set_justify(Gtk.Justification.CENTER)
        tab1_vbox.pack_start(lbl1, False, False, 0)
        
        btn_update = Gtk.Button(label="Update System")
        btn_update.connect("clicked", self.on_update_clicked)
        tab1_vbox.pack_start(btn_update, False, False, 0)
        
        notebook.append_page(tab1_vbox, Gtk.Label(label="Getting Started"))
        
        # Tab 2: AmitShield Security
        tab2_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        tab2_vbox.set_border_width(15)
        
        lbl2 = Gtk.Label(label="AmitShield Security keeps your system safe from threats.\nBuilt-in firewall, antivirus, and privacy controls.")
        lbl2.set_justify(Gtk.Justification.CENTER)
        tab2_vbox.pack_start(lbl2, False, False, 0)
        
        notebook.append_page(tab2_vbox, Gtk.Label(label="AmitShield Security"))
        
        # Tab 3: Customization
        tab3_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        tab3_vbox.set_border_width(15)
        
        lbl3 = Gtk.Label(label="Make Amit OS your own.\nCustomize themes, icons, and behavior in the Control Panel.")
        lbl3.set_justify(Gtk.Justification.CENTER)
        tab3_vbox.pack_start(lbl3, False, False, 0)
        
        btn_control = Gtk.Button(label="Open Control Panel")
        btn_control.connect("clicked", self.on_control_panel_clicked)
        tab3_vbox.pack_start(btn_control, False, False, 0)
        
        notebook.append_page(tab3_vbox, Gtk.Label(label="Customization"))
        
    def on_update_clicked(self, widget):
        try:
            subprocess.Popen(["amitos-update"])
        except Exception as e:
            print(f"Error running amitos-update: {e}")
            
    def on_control_panel_clicked(self, widget):
        try:
            subprocess.Popen(["amitcontrol"])
        except Exception as e:
            print(f"Error running amitcontrol: {e}")

if __name__ == '__main__':
    app = WelcomeWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
