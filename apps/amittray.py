#!/usr/bin/env python3
"""
AmitTray - System Status Tray Applet
Shows WiFi, Bluetooth, Battery, Volume in system tray
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import subprocess, os, re, threading, time

try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
    HAS_INDICATOR = True
except Exception:
    HAS_INDICATOR = False

CSS = b"""
* { font-family: 'Noto Sans', sans-serif; }
.popup-window {
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 14px;
    padding: 0;
}
.section-header {
    background: #111827;
    color: #9ca3af;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 8px 16px;
    border-radius: 14px 14px 0 0;
}
.row-item {
    padding: 10px 16px;
    border-bottom: 1px solid #374151;
    color: #e5e7eb;
    font-size: 13px;
}
.row-item:hover { background: #374151; }
.status-on  { color: #10b981; font-weight: bold; }
.status-off { color: #6b7280; }
.action-btn {
    background: #1d4ed8;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 6px 14px;
    font-size: 12px;
    margin: 4px;
}
.action-btn:hover { background: #2563eb; }
.toggle-on {
    background: #059669;
    color: white;
    border-radius: 12px;
    border: none;
    padding: 4px 12px;
    font-size: 12px;
}
.toggle-off {
    background: #374151;
    color: #9ca3af;
    border-radius: 12px;
    border: none;
    padding: 4px 12px;
    font-size: 12px;
}
"""

def run(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL,
                                       text=True, timeout=3).strip()
    except Exception:
        return ""

def get_wifi_info():
    out = run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"])
    for line in out.split("\n"):
        if line.startswith("yes:"):
            parts = line.split(":")
            ssid   = parts[1] if len(parts) > 1 else "Connected"
            signal = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            bars   = "▂▄▆█"[:max(1, signal // 25)]
            return True, ssid, signal, bars
    return False, "", 0, ""

def get_bt_info():
    out = run(["bluetoothctl", "show"])
    powered = "Powered: yes" in out
    devs = []
    if powered:
        dout = run(["bluetoothctl", "info"])
        if "Connected: yes" in dout:
            name = re.search(r"Name: (.+)", dout)
            devs.append(name.group(1).strip() if name else "Device")
    return powered, devs

def get_battery():
    for path in ["/sys/class/power_supply/BAT0", "/sys/class/power_supply/BAT1"]:
        cap  = f"{path}/capacity"
        stat = f"{path}/status"
        if os.path.exists(cap):
            try:
                pct = int(open(cap).read().strip())
                status = open(stat).read().strip() if os.path.exists(stat) else ""
                icon = ("🔋","🪫")[pct < 20]
                charging = "⚡" if status == "Charging" else ""
                return True, pct, charging, icon
            except Exception: pass
    return False, 0, "", ""

def get_volume():
    out = run(["pactl", "list", "sinks"])
    m = re.search(r"Volume:.*?(\d+)%", out)
    muted = "Mute: yes" in out
    vol = int(m.group(1)) if m else 0
    return vol, muted

def wifi_signal_icon(signal):
    if signal >= 75: return "📶"
    if signal >= 50: return "🛜"
    if signal >= 25: return "📡"
    return "❌"


class AmitTray:
    def __init__(self):
        self._popup = None
        self._wifi_on = True
        self._bt_on   = False

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._build_statusbar()
        GLib.timeout_add(3000, self._update_icon)
        self._update_icon()

    def _build_statusbar(self):
        """Minimal status window if no AppIndicator3 available."""
        self._win = Gtk.Window(
            title="AmitTray",
            decorated=False,
            skip_taskbar_hint=True,
            skip_pager_hint=True,
            type_hint=Gdk.WindowTypeHint.DOCK,
            resizable=False
        )
        self._win.set_keep_above(True)
        self._win.move(Gdk.Screen.get_default().get_width() - 280, 2)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(4)
        box.set_margin_bottom(4)

        self.wifi_lbl = Gtk.Label(label="📶")
        self.bt_lbl   = Gtk.Label(label="🔵")
        self.bat_lbl  = Gtk.Label(label="🔋")
        self.vol_lbl  = Gtk.Label(label="🔊")

        for lbl in [self.wifi_lbl, self.bt_lbl, self.bat_lbl, self.vol_lbl]:
            eb = Gtk.EventBox()
            eb.add(lbl)
            eb.connect("button-press-event", self._on_icon_click)
            box.pack_start(eb, False, False, 0)

        self._win.add(box)
        self._win.show_all()

    def _update_icon(self):
        # WiFi
        connected, ssid, signal, bars = get_wifi_info()
        self.wifi_lbl.set_label(wifi_signal_icon(signal) if connected else "❌")
        self.wifi_lbl.set_tooltip_text(f"WiFi: {ssid} ({signal}%)" if connected else "WiFi: Disconnected")

        # Bluetooth
        bt_on, devs = get_bt_info()
        self.bt_lbl.set_label("🔵" if bt_on else "⚫")
        self.bt_lbl.set_tooltip_text("Bluetooth: " + (devs[0] if devs else ("On" if bt_on else "Off")))

        # Battery
        has_bat, pct, charging, icon = get_battery()
        if has_bat:
            self.bat_lbl.set_label(f"{icon}{pct}%{charging}")
            self.bat_lbl.set_tooltip_text(f"Battery: {pct}% {charging}")
        else:
            self.bat_lbl.set_label("🔌")

        # Volume
        vol, muted = get_volume()
        self.vol_lbl.set_label("🔇" if muted else "🔊")
        self.vol_lbl.set_tooltip_text(f"Volume: {'Muted' if muted else str(vol)+'%'}")

        return True

    def _on_icon_click(self, eb, event):
        if self._popup and self._popup.get_visible():
            self._popup.hide()
            return
        self._show_popup(event)

    def _show_popup(self, event):
        if self._popup:
            self._popup.destroy()

        win = Gtk.Window(decorated=False, resizable=False)
        win.get_style_context().add_class("popup-window")
        win.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        win.set_keep_above(True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        win.add(vbox)

        # ── WiFi Section ────────────────────────────────────
        self._add_section(vbox, "NETWORK")
        connected, ssid, signal, _ = get_wifi_info()
        wrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        wrow.get_style_context().add_class("row-item")
        wlbl = Gtk.Label(
            label=f"  {wifi_signal_icon(signal)}  {ssid if connected else 'Not Connected'}",
            xalign=0, hexpand=True)
        wstatus = Gtk.Label(label="Connected" if connected else "Off")
        wstatus.get_style_context().add_class("status-on" if connected else "status-off")
        wtgl = Gtk.Button(label="On" if connected else "Off")
        wtgl.get_style_context().add_class("toggle-on" if connected else "toggle-off")
        wtgl.connect("clicked", self._toggle_wifi)
        wrow.pack_start(wlbl,    True,  True,  0)
        wrow.pack_start(wstatus, False, False, 0)
        wrow.pack_start(wtgl,    False, False, 0)
        vbox.pack_start(wrow, False, False, 0)

        # WiFi networks button
        wnet_btn = Gtk.Button(label="  Open Network Settings")
        wnet_btn.get_style_context().add_class("row-item")
        wnet_btn.connect("clicked", lambda _: self._open("nm-connection-editor"))
        vbox.pack_start(wnet_btn, False, False, 0)

        # ── Bluetooth Section ────────────────────────────────
        self._add_section(vbox, "BLUETOOTH")
        bt_on, devs = get_bt_info()
        brow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        brow.get_style_context().add_class("row-item")
        blbl = Gtk.Label(
            label=f"  🔵  {devs[0] if devs else 'Bluetooth'}",
            xalign=0, hexpand=True)
        bstatus = Gtk.Label(label="On" if bt_on else "Off")
        bstatus.get_style_context().add_class("status-on" if bt_on else "status-off")
        btgl = Gtk.Button(label="On" if bt_on else "Off")
        btgl.get_style_context().add_class("toggle-on" if bt_on else "toggle-off")
        btgl.connect("clicked", self._toggle_bt)
        brow.pack_start(blbl,    True,  True,  0)
        brow.pack_start(bstatus, False, False, 0)
        brow.pack_start(btgl,    False, False, 0)
        vbox.pack_start(brow, False, False, 0)

        bt_btn = Gtk.Button(label="  Open Bluetooth Manager")
        bt_btn.get_style_context().add_class("row-item")
        bt_btn.connect("clicked", lambda _: self._open("blueman-manager"))
        vbox.pack_start(bt_btn, False, False, 0)

        # ── Volume Section ───────────────────────────────────
        self._add_section(vbox, "VOLUME")
        vol, muted = get_volume()
        vrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        vrow.get_style_context().add_class("row-item")
        vicon = Gtk.Label(label="  🔇" if muted else "  🔊", xalign=0)
        slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        slider.set_value(vol)
        slider.set_hexpand(True)
        slider.connect("value-changed", self._set_volume)
        vrow.pack_start(vicon,  False, False, 0)
        vrow.pack_start(slider, True,  True,  0)
        vbox.pack_start(vrow, False, False, 0)

        # ── Battery Section ──────────────────────────────────
        has_bat, pct, charging, icon = get_battery()
        if has_bat:
            self._add_section(vbox, "BATTERY")
            bat_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            bat_row.get_style_context().add_class("row-item")
            bat_bar = Gtk.ProgressBar()
            bat_bar.set_fraction(pct / 100)
            bat_bar.set_hexpand(True)
            bat_lbl = Gtk.Label(label=f"{pct}% {charging}")
            bat_lbl.get_style_context().add_class("status-on" if pct > 20 else "status-off")
            bat_row.pack_start(Gtk.Label(label=f" {icon} "), False, False, 0)
            bat_row.pack_start(bat_bar, True,  True,  0)
            bat_row.pack_start(bat_lbl, False, False, 4)
            vbox.pack_start(bat_row, False, False, 0)

        # ── Quick actions ────────────────────────────────────
        self._add_section(vbox, "QUICK ACTIONS")
        acts = [
            ("  ⚙️  System Settings",   "systemsettings5"),
            ("  🔒  Lock Screen",         "loginctl lock-session"),
            ("  💤  Suspend",             "systemctl suspend"),
            ("  🔄  Restart",             "systemctl reboot"),
            ("  ⏻  Shutdown",             "systemctl poweroff"),
        ]
        for label, cmd in acts:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("row-item")
            btn.connect("clicked", lambda _, c=cmd: (self._open(c), win.destroy()))
            vbox.pack_start(btn, False, False, 0)

        win.show_all()
        # Position popup above taskbar
        screen_h = Gdk.Screen.get_default().get_height()
        win.move(Gdk.Screen.get_default().get_width() - 300, screen_h - 600)
        win.connect("focus-out-event", lambda w, e: w.destroy())
        self._popup = win

    def _add_section(self, parent, label):
        lbl = Gtk.Label(label=label, xalign=0)
        lbl.get_style_context().add_class("section-header")
        parent.pack_start(lbl, False, False, 0)

    def _toggle_wifi(self, btn):
        try:
            out = run(["nmcli", "radio", "wifi"])
            if "enabled" in out:
                subprocess.Popen(["nmcli", "radio", "wifi", "off"])
            else:
                subprocess.Popen(["nmcli", "radio", "wifi", "on"])
        except Exception:
            pass

    def _toggle_bt(self, btn):
        try:
            out = run(["bluetoothctl", "show"])
            if "Powered: yes" in out:
                subprocess.Popen(["bluetoothctl", "power", "off"])
            else:
                subprocess.Popen(["bluetoothctl", "power", "on"])
        except Exception:
            pass

    def _set_volume(self, slider):
        try:
            vol = int(slider.get_value())
            subprocess.Popen(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{vol}%"])
        except Exception:
            pass

    def _open(self, cmd):
        try:
            subprocess.Popen(cmd.split())
        except Exception:
            pass


def main():
    tray = AmitTray()
    Gtk.main()

if __name__ == "__main__":
    main()
