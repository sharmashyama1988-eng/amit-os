#!/usr/bin/env python3
"""
AmitClock - World Clock & Timer
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import time, threading

CSS = b"""
* { font-family: 'Noto Sans', sans-serif; }
window { background: #0d1117; }
.time-display { color: #58a6ff; font-size: 72px; font-weight: 900; }
.date-display { color: #8b949e; font-size: 18px; margin-bottom: 20px; }
.tab-btn {
    background: transparent;
    color: #8b949e;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 20px;
    font-size: 14px;
}
.tab-btn:hover { color: #e6edf3; }
.tab-btn.active { color: #58a6ff; border-bottom: 2px solid #58a6ff; }
.timer-btn {
    background: #1f6feb;
    color: white;
    border-radius: 50%;
    min-width: 64px;
    min-height: 64px;
    font-size: 20px;
}
.timer-btn:hover { background: #388bfd; }
.stop-btn { background: #f85149; }
.stop-btn:hover { background: #ff7b72; }
"""

class AmitClock(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitClock")
        self.set_default_size(400, 500)
        self.set_resizable(False)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._build()
        GLib.timeout_add(1000, self._update_time)

    def _build(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # ── Tabs ─────────────────────────────────────────────
        tabs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True)
        self.btn_clock = Gtk.Button(label="CLOCK")
        self.btn_timer = Gtk.Button(label="TIMER")
        for b in [self.btn_clock, self.btn_timer]:
            b.get_style_context().add_class("tab-btn")
            tabs.pack_start(b, True, True, 0)
        
        self.btn_clock.get_style_context().add_class("active")
        vbox.pack_start(tabs, False, False, 0)

        self.stack = Gtk.Stack()
        vbox.pack_start(self.stack, True, True, 0)

        # ── Clock Page ───────────────────────────────────────
        clk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        clk_box.set_valign(Gtk.Align.CENTER)
        
        self.lbl_time = Gtk.Label()
        self.lbl_time.get_style_context().add_class("time-display")
        
        self.lbl_date = Gtk.Label()
        self.lbl_date.get_style_context().add_class("date-display")
        
        clk_box.pack_start(self.lbl_time, False, False, 0)
        clk_box.pack_start(self.lbl_date, False, False, 0)
        self.stack.add_named(clk_box, "clock")

        # ── Timer Page ───────────────────────────────────────
        tmr_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        tmr_box.set_valign(Gtk.Align.CENTER)
        
        self.lbl_tmr = Gtk.Label(label="00:00:00")
        self.lbl_tmr.get_style_context().add_class("time-display")
        self.lbl_tmr.set_markup('<span font="48">00:00:00</span>')
        
        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        btns.set_halign(Gtk.Align.CENTER)
        
        self.start_btn = Gtk.Button(label="▶")
        self.start_btn.get_style_context().add_class("timer-btn")
        self.start_btn.connect("clicked", self._on_timer_start)
        
        self.rst_btn = Gtk.Button(label="↺")
        self.rst_btn.get_style_context().add_class("timer-btn")
        self.rst_btn.get_style_context().add_class("stop-btn")
        self.rst_btn.connect("clicked", self._on_timer_reset)
        
        btns.pack_start(self.start_btn, False, False, 0)
        btns.pack_start(self.rst_btn,   False, False, 0)
        
        tmr_box.pack_start(self.lbl_tmr, False, False, 0)
        tmr_box.pack_start(btns,         False, False, 0)
        self.stack.add_named(tmr_box, "timer")

        # Tab events
        self.btn_clock.connect("clicked", lambda _: self._set_page("clock"))
        self.btn_timer.connect("clicked", lambda _: self._set_page("timer"))

        self._update_time()

    def _set_page(self, name):
        self.stack.set_visible_child_name(name)
        self.btn_clock.get_style_context().remove_class("active")
        self.btn_timer.get_style_context().remove_class("active")
        if name == "clock": self.btn_clock.get_style_context().add_class("active")
        else: self.btn_timer.get_style_context().add_class("active")

    def _update_time(self):
        now = time.localtime()
        self.lbl_time.set_label(time.strftime("%H:%M", now))
        self.lbl_date.set_label(time.strftime("%A, %B %d, %Y", now))
        return True

    # Timer logic
    _timer_running = False
    _timer_seconds = 0

    def _on_timer_start(self, btn):
        self._timer_running = not self._timer_running
        btn.set_label("⏸" if self._timer_running else "▶")
        if self._timer_running:
            threading.Thread(target=self._timer_loop, daemon=True).start()

    def _on_timer_reset(self, btn):
        self._timer_running = False
        self._timer_seconds = 0
        self.start_btn.set_label("▶")
        self._update_timer_lbl()

    def _timer_loop(self):
        while self._timer_running:
            time.sleep(1)
            if not self._timer_running: break
            self._timer_seconds += 1
            GLib.idle_add(self._update_timer_lbl)

    def _update_timer_lbl(self):
        h, m = divmod(self._timer_seconds, 3600)
        m, s = divmod(m, 60)
        self.lbl_tmr.set_markup(f'<span font="48">{h:02}:{m:02}:{s:02}</span>')


def main():
    win = AmitClock()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
