#!/usr/bin/env python3
"""
AmitCapture - Snipping Tool
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import os, subprocess, time

CSS = b"""
window { background: rgba(0, 0, 0, 0.4); }
.toolbar { background: #161b22; padding: 10px; border-radius: 12px; margin: 10px; }
.btn-snip { background: #1f6feb; color: white; border-radius: 8px; padding: 8px 16px; font-weight: bold; }
.btn-snip:hover { background: #388bfd; }
.selection-box { border: 2px solid #58a6ff; background: rgba(88, 166, 255, 0.2); }
"""

class AmitCapture(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitCapture")
        self.set_keep_above(True)
        self.set_resizable(False)
        self.set_decorated(False)
        
        # Transparent background for selection
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        self.start_x = self.start_y = 0
        self.cur_x = self.cur_y = 0
        self.is_selecting = False

        self._build()

    def _build(self):
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.vbox)

        self.toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.toolbar.get_style_context().add_class("toolbar")
        self.toolbar.set_halign(Gtk.Align.CENTER)

        btn = Gtk.Button(label="📸 New Snip")
        btn.get_style_context().add_class("btn-snip")
        btn.connect("clicked", self._start_snip)
        self.toolbar.pack_start(btn, False, False, 0)
        
        self.vbox.pack_start(self.toolbar, False, False, 0)
        
        # Overlay for selection
        self.da = Gtk.DrawingArea()
        self.da.connect("draw", self._on_draw)
        self.vbox.pack_start(self.da, True, True, 0)

        self.connect("button-press-event", self._on_press)
        self.connect("button-release-event", self._on_release)
        self.connect("motion-notify-event", self._on_motion)
        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | 
                          Gdk.EventMask.BUTTON_RELEASE_MASK |
                          Gdk.EventMask.POINTER_MOTION_MASK)

    def _start_snip(self, btn):
        self.toolbar.hide()
        self.fullscreen()
        self.is_selecting = False
        self.da.show()

    def _on_press(self, w, e):
        self.start_x, self.start_y = e.x, e.y
        self.is_selecting = True
        return True

    def _on_motion(self, w, e):
        if self.is_selecting:
            self.cur_x, self.cur_y = e.x, e.y
            self.da.queue_draw()
        return True

    def _on_release(self, w, e):
        self.is_selecting = False
        self.cur_x, self.cur_y = e.x, e.y
        self.unfullscreen()
        self._take_screenshot()
        return True

    def _on_draw(self, w, cr):
        if self.is_selecting:
            x = min(self.start_x, self.cur_x)
            y = min(self.start_y, self.cur_y)
            w = abs(self.start_x - self.cur_x)
            h = abs(self.start_y - self.cur_y)
            
            cr.set_source_rgba(0.2, 0.6, 1.0, 0.3)
            cr.rectangle(x, y, w, h)
            cr.fill()
            cr.set_source_rgb(0.3, 0.7, 1.0)
            cr.set_line_width(2)
            cr.rectangle(x, y, w, h)
            cr.stroke()
        return False

    def _take_screenshot(self):
        x = int(min(self.start_x, self.cur_x))
        y = int(min(self.start_y, self.cur_y))
        w = int(abs(self.start_x - self.cur_x))
        h = int(abs(self.start_y - self.cur_y))
        
        if w < 5 or h < 5: 
            self.toolbar.show()
            return

        filename = f"amit_snip_{int(time.time())}.png"
        path = os.path.expanduser(f"~/Pictures/{filename}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Use gnome-screenshot or import (ImageMagick) or spectacle
        # Amit OS uses Spectacle by default, but for custom snip we use 'import'
        try:
            subprocess.Popen(["import", "-window", "root", "-crop", f"{w}x{h}+{x}+{y}", path])
        except Exception:
            pass
        
        # Show notification
        try:
            subprocess.Popen(["notify-send", "AmitCapture", f"Screenshot saved to Pictures/{filename}"])
        except Exception:
            pass
        self.toolbar.show()

def main():
    win = AmitCapture()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
