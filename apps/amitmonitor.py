#!/usr/bin/env python3
"""
AmitMonitor - System Resource Monitor
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import subprocess, os, time, threading
from collections import deque

CSS = b"""
* { font-family: 'Noto Sans', sans-serif; }
window { background: #0d1117; }
.header { background: #161b22; padding: 12px 20px; border-bottom: 1px solid #30363d; }
.header-title { color: #58a6ff; font-size: 20px; font-weight: bold; }
.card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px;
    margin: 6px;
}
.card-title { color: #8b949e; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
.card-value { color: #e6edf3; font-size: 28px; font-weight: bold; }
.card-sub { color: #8b949e; font-size: 12px; }
.bar-bg { background: #21262d; border-radius: 4px; }
.bar-cpu { background: linear-gradient(90deg,#3b82f6,#60a5fa); border-radius: 4px; }
.bar-mem { background: linear-gradient(90deg,#10b981,#34d399); border-radius: 4px; }
.bar-disk { background: linear-gradient(90deg,#f59e0b,#fbbf24); border-radius: 4px; }
.proc-list { background: #161b22; color: #e6edf3; font-size: 13px; }
.proc-header { background: #21262d; color: #8b949e; font-size: 12px; font-weight: bold; padding: 8px; }
.section-title { color: #e6edf3; font-size: 14px; font-weight: bold; margin: 8px 6px 4px 6px; }
"""

def read_file(path):
    try:
        with open(path) as f: return f.read().strip()
    except: return ""

def get_cpu_percent():
    def read_stat():
        stat_content = read_file("/proc/stat")
        if not stat_content:
            return 0, 0
        lines = stat_content.split("\n")
        if not lines:
            return 0, 0
        line = lines[0].split()
        if len(line) < 5:
            return 0, 0
        try:
            vals = list(map(int, line[1:]))
            idle  = vals[3]
            total = sum(vals)
            return idle, total
        except Exception:
            return 0, 0
    res1 = read_stat()
    if res1 == (0, 0):
        return 0.0
    i1, t1 = res1
    time.sleep(0.3)
    res2 = read_stat()
    if res2 == (0, 0):
        return 0.0
    i2, t2 = res2
    dt = t2 - t1
    return round(100.0 * (1 - (i2 - i1) / dt), 1) if dt else 0.0

def get_mem():
    data = {}
    meminfo = read_file("/proc/meminfo")
    if not meminfo:
        return 0, 0
    for line in meminfo.split("\n"):
        parts = line.split()
        if len(parts) >= 2:
            try:
                data[parts[0].rstrip(":")] = int(parts[1])
            except ValueError:
                pass
    total = data.get("MemTotal", 0)
    avail = data.get("MemAvailable", total)
    used  = total - avail
    return used // 1024, total // 1024  # MB

def get_disk():
    try:
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize // (1024**3)
        free  = st.f_bfree  * st.f_frsize // (1024**3)
        used  = total - free
        pct   = round(100 * used / total, 1) if total else 0
        return used, total, pct
    except: return 0, 0, 0

def get_processes():
    procs = []
    if not os.path.exists("/proc"):
        return []
    try:
        pids = os.listdir("/proc")
    except Exception:
        return []
    for pid in pids:
        if not pid.isdigit(): continue
        try:
            stat_content = read_file(f"/proc/{pid}/stat")
            if not stat_content: continue
            stat  = stat_content.split()
            if len(stat) < 3: continue
            name  = stat[1].strip("()")
            state = stat[2]
            statm_content = read_file(f"/proc/{pid}/statm")
            if not statm_content: continue
            statm = statm_content.split()
            if len(statm) < 2: continue
            rss   = int(statm[1]) * 4  # KB
            cmd   = read_file(f"/proc/{pid}/comm")
            procs.append((int(pid), cmd or name, state, rss // 1024))
        except: pass
    return sorted(procs, key=lambda x: x[3], reverse=True)[:30]

def get_net():
    try:
        lines = read_file("/proc/net/dev").split("\n")
        rx = tx = 0
        for line in lines[2:]:
            parts = line.split()
            if not parts or parts[0].startswith("lo"): continue
            rx += int(parts[1])
            tx += int(parts[9])
        return rx, tx
    except: return 0, 0


class AmitMonitor(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitMonitor")
        self.set_default_size(860, 580)
        self._cpu_hist = deque([0]*60, maxlen=60)
        self._prev_net = get_net()
        self._prev_time = time.time()

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._build()
        GLib.timeout_add(1500, self._refresh)
        self._refresh()

    def _build(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hdr.get_style_context().add_class("header")
        title = Gtk.Label(label="AmitMonitor")
        title.get_style_context().add_class("header-title")
        self.uptime_lbl = Gtk.Label(label="", xalign=1)
        self.uptime_lbl.get_style_context().add_class("card-sub")
        hdr.pack_start(title, False, False, 0)
        hdr.pack_end(self.uptime_lbl, False, False, 0)
        vbox.pack_start(hdr, False, False, 0)

        # Top cards
        cards = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(cards, False, False, 8)

        self.cpu_val   = self._make_card(cards, "CPU",    "0%",   "#3b82f6", "cpu")
        self.mem_val   = self._make_card(cards, "MEMORY", "0 MB", "#10b981", "mem")
        self.disk_val  = self._make_card(cards, "DISK",   "0 GB", "#f59e0b", "disk")
        self.net_val   = self._make_card(cards, "NETWORK","0 KB/s","#8b5cf6","")

        # Process list
        sec = Gtk.Label(label="Running Processes", xalign=0)
        sec.get_style_context().add_class("section-title")
        vbox.pack_start(sec, False, False, 0)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        self.store = Gtk.ListStore(int, str, str, str)
        tree = Gtk.TreeView(model=self.store)
        tree.get_style_context().add_class("proc-list")

        for i, col in enumerate(["PID","Name","State","Memory"]):
            r = Gtk.CellRendererText()
            c = Gtk.TreeViewColumn(col, r, text=i)
            c.set_min_width(100)
            tree.append_column(c)

        scroll.add(tree)
        vbox.pack_start(scroll, True, True, 8)

    def _make_card(self, parent, title, value, color, kind):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("card")
        card.set_hexpand(True)

        t = Gtk.Label(label=title, xalign=0)
        t.get_style_context().add_class("card-title")

        v = Gtk.Label(label=value, xalign=0)
        v.get_style_context().add_class("card-value")

        bar_bg = Gtk.Box()
        bar_bg.get_style_context().add_class("bar-bg")
        bar_bg.set_size_request(-1, 6)

        bar_fill = Gtk.Box()
        bar_fill.get_style_context().add_class(f"bar-{kind}" if kind else "bar-cpu")
        bar_fill.set_size_request(0, 6)
        bar_bg.pack_start(bar_fill, False, False, 0)

        card.pack_start(t,      False, False, 0)
        card.pack_start(v,      False, False, 0)
        if kind:
            card.pack_start(bar_bg, False, False, 0)
        parent.pack_start(card, True, True, 0)
        return v, bar_fill if kind else None

    def _set_bar(self, bar_fill, pct, width=200):
        if bar_fill:
            w = max(2, int(width * pct / 100))
            bar_fill.set_size_request(w, 6)

    def _refresh(self):
        # CPU
        def do_cpu():
            cpu = get_cpu_percent()
            GLib.idle_add(self._update_cpu, cpu)
        threading.Thread(target=do_cpu, daemon=True).start()

        # Memory
        used_mb, total_mb = get_mem()
        pct_mem = round(100 * used_mb / total_mb, 1) if total_mb else 0
        self.mem_val[0].set_label(f"{used_mb} / {total_mb} MB")
        self._set_bar(self.mem_val[1], pct_mem)

        # Disk
        du, dt, dpct = get_disk()
        self.disk_val[0].set_label(f"{du} / {dt} GB")
        self._set_bar(self.disk_val[1], dpct)

        # Network
        rx, tx = get_net()
        now = time.time()
        dt2 = now - self._prev_time
        if dt2 > 0:
            speed = (rx - self._prev_net[0] + tx - self._prev_net[1]) / dt2 / 1024
            self.net_val[0].set_label(f"{speed:.1f} KB/s")
        self._prev_net  = (rx, tx)
        self._prev_time = now

        # Uptime
        uptime_data = read_file("/proc/uptime").split()
        if uptime_data:
            try:
                up = int(float(uptime_data[0]))
                h, m = divmod(up // 60, 60)
                self.uptime_lbl.set_label(f"Uptime: {h}h {m}m")
            except:
                self.uptime_lbl.set_label("Uptime: N/A")
        else:
            self.uptime_lbl.set_label("Uptime: N/A")

        # Processes
        procs = get_processes()
        self.store.clear()
        for pid, name, state, mem_mb in procs:
            self.store.append([pid, name[:30], state, f"{mem_mb} MB"])

        return True

    def _update_cpu(self, cpu):
        self.cpu_val[0].set_label(f"{cpu}%")
        self._set_bar(self.cpu_val[1], cpu)


def main():
    win = AmitMonitor()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
