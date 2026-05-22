#!/usr/bin/env python3
"""
AmitPaint - Simple Drawing App
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Cairo
import math

CSS = b"""
window { background: #1a1a2e; }
.toolbar { background: #16213e; padding: 6px; border-bottom: 1px solid #0f3460; }
.canvas { background: white; border-radius: 8px; margin: 10px; }
.color-btn { min-width: 32px; min-height: 32px; border-radius: 50%; border: 2px solid #0f3460; }
.tool-btn { background: transparent; color: #60a5fa; border: none; padding: 8px; font-size: 18px; }
.tool-btn:hover { background: #0f3460; border-radius: 8px; }
.tool-btn.active { background: #1f6feb; color: white; border-radius: 8px; }
"""

class AmitPaint(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitPaint")
        self.set_default_size(800, 600)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.brush_size = 4
        self.color = (0, 0, 0)
        self.tool = "brush"
        self.surface = None

        self._build()

    def _build(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        # Toolbar
        tb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        tb.get_style_context().add_class("toolbar")
        
        tools = [("🖌️", "brush"), ("Eraser", "eraser"), ("Line", "line"), ("Rect", "rect"), ("Circle", "circle")]
        self.tool_btns = {}
        for icon, name in tools:
            btn = Gtk.Button(label=icon)
            btn.get_style_context().add_class("tool-btn")
            btn.connect("clicked", self._set_tool, name)
            tb.pack_start(btn, False, False, 0)
            self.tool_btns[name] = btn
        self.tool_btns["brush"].get_style_context().add_class("active")

        # Color palette
        colors = [(0,0,0), (1,1,1), (1,0,0), (0,1,0), (0,0,1), (1,1,0), (1,0,1), (0,1,1)]
        for c in colors:
            btn = Gtk.Button()
            btn.get_style_context().add_class("color-btn")
            rgba = Gdk.RGBA(*c, 1)
            btn.override_background_color(Gtk.StateFlags.NORMAL, rgba)
            btn.connect("clicked", self._set_color, c)
            tb.pack_start(btn, False, False, 0)

        vbox.pack_start(tb, False, False, 0)

        # Drawing Area
        self.da = Gtk.DrawingArea()
        self.da.get_style_context().add_class("canvas")
        self.da.connect("draw", self._on_draw)
        self.da.connect("configure-event", self._on_configure)
        self.da.connect("button-press-event", self._on_button_press)
        self.da.connect("motion-notify-event", self._on_motion)
        self.da.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | 
                          Gdk.EventMask.BUTTON1_MOTION_MASK)
        
        vbox.pack_start(self.da, True, True, 0)

    def _set_tool(self, btn, name):
        for b in self.tool_btns.values(): b.get_style_context().remove_class("active")
        btn.get_style_context().add_class("active")
        self.tool = name

    def _set_color(self, btn, c):
        self.color = c

    def _on_configure(self, widget, event):
        if self.surface: self.surface.finish()
        self.surface = widget.get_window().create_similar_surface(
            Cairo.Content.COLOR, widget.get_allocated_width(), widget.get_allocated_height())
        cr = Cairo.Context(self.surface)
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        return True

    def _on_draw(self, widget, cr):
        cr.set_source_surface(self.surface, 0, 0)
        cr.paint()
        return False

    def _draw_brush(self, x, y):
        cr = Cairo.Context(self.surface)
        cr.set_source_rgb(*self.color if self.tool != "eraser" else (1, 1, 1))
        cr.set_line_width(self.brush_size)
        cr.set_line_cap(Cairo.LineCap.ROUND)
        cr.arc(x, y, self.brush_size/2, 0, 2*math.pi)
        cr.fill()
        self.da.queue_draw()

    def _on_button_press(self, widget, event):
        if event.button == 1:
            self._draw_brush(event.x, event.y)
        return True

    def _on_motion(self, widget, event):
        if event.state & Gdk.ModifierType.BUTTON1_MASK:
            self._draw_brush(event.x, event.y)
        return True

def main():
    win = AmitPaint()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
