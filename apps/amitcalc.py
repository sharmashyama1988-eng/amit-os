#!/usr/bin/env python3
"""
AmitCalc - Scientific Calculator
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango
import math

CSS = b"""
* { font-family: 'Noto Sans', sans-serif; }
window { background: #1a1a2e; }
.display-box {
    background: #0f0f1a;
    border-radius: 12px;
    margin: 12px;
    padding: 16px;
}
.display-expr {
    color: #666;
    font-size: 14px;
}
.display-main {
    color: #ffffff;
    font-size: 36px;
    font-weight: bold;
}
.btn-num {
    background: #16213e;
    color: #ffffff;
    border-radius: 10px;
    border: none;
    font-size: 18px;
    font-weight: 500;
    padding: 8px;
    margin: 3px;
}
.btn-num:hover { background: #1e2d50; }
.btn-op {
    background: #0f3460;
    color: #60a5fa;
    border-radius: 10px;
    border: none;
    font-size: 18px;
    font-weight: bold;
    padding: 8px;
    margin: 3px;
}
.btn-op:hover { background: #1a4a8a; }
.btn-eq {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: #ffffff;
    border-radius: 10px;
    border: none;
    font-size: 20px;
    font-weight: bold;
    padding: 8px;
    margin: 3px;
}
.btn-eq:hover { background: #2563eb; }
.btn-clear {
    background: #7f1d1d;
    color: #fca5a5;
    border-radius: 10px;
    border: none;
    font-size: 16px;
    font-weight: bold;
    padding: 8px;
    margin: 3px;
}
.btn-clear:hover { background: #991b1b; }
.btn-sci {
    background: #1e1b4b;
    color: #a5b4fc;
    border-radius: 10px;
    border: none;
    font-size: 13px;
    padding: 6px;
    margin: 3px;
}
.btn-sci:hover { background: #2e2b5e; }
"""

class AmitCalc(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitCalc")
        self.set_default_size(340, 520)
        self.set_resizable(False)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.expr   = ""
        self.result = "0"
        self.new_num = True

        self._build()
        self.connect("key-press-event", self._on_key)

    def _build(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # Display
        disp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        disp.get_style_context().add_class("display-box")
        self.expr_lbl   = Gtk.Label(label="", xalign=1)
        self.expr_lbl.get_style_context().add_class("display-expr")
        self.result_lbl = Gtk.Label(label="0", xalign=1)
        self.result_lbl.get_style_context().add_class("display-main")
        self.result_lbl.set_ellipsize(Pango.EllipsizeMode.START)
        disp.pack_start(self.expr_lbl,   False, False, 0)
        disp.pack_start(self.result_lbl, False, False, 0)
        vbox.pack_start(disp, False, False, 0)

        # Scientific row
        sci_grid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        sci_grid.set_margin_start(8); sci_grid.set_margin_end(8)
        sci_btns = [
            ("sin",  "math.sin("),("cos",  "math.cos("),
            ("tan",  "math.tan("),("log",  "math.log10("),
            ("ln",   "math.log("), ("√",   "math.sqrt("),
            ("π",    str(math.pi)),("e",   str(math.e)),
            ("x²",  "**2"),       ("1/x", "1/("),
        ]
        for i, (lbl, val) in enumerate(sci_btns):
            b = Gtk.Button(label=lbl)
            b.get_style_context().add_class("btn-sci")
            b.connect("clicked", self._sci, val)
            sci_grid.attach(b, i % 5, i // 5, 1, 1)
        vbox.pack_start(sci_grid, False, False, 4)

        # Main buttons
        grid = Gtk.Grid(row_homogeneous=True, column_homogeneous=True)
        grid.set_margin_start(8); grid.set_margin_end(8); grid.set_margin_bottom(8)

        layout = [
            [("C","clear"),("±","negate"),("%","pct"),("÷","op/")],
            [("7","7"),    ("8","8"),     ("9","9"),   ("×","op*")],
            [("4","4"),    ("5","5"),     ("6","6"),   ("−","op-")],
            [("1","1"),    ("2","2"),     ("3","3"),   ("+","op+")],
            [("(","("),    ("0","0"),     (")",")")],
            [(".","."),    ("=","eq"),    ("⌫","del")],
        ]
        eq_styles = {"=":"btn-eq","C":"btn-clear","÷":"btn-op",
                     "×":"btn-op","−":"btn-op","+":"btn-op"}

        for r, row in enumerate(layout):
            for c, (lbl, val) in enumerate(row):
                btn = Gtk.Button(label=lbl)
                cls = eq_styles.get(lbl, "btn-num")
                btn.get_style_context().add_class(cls)
                btn.connect("clicked", self._press, val)
                grid.attach(btn, c, r, 1, 1)

        vbox.pack_start(grid, True, True, 0)

    def _press(self, btn, val):
        if val == "eq":
            self._calculate()
        elif val == "clear":
            self.expr = ""; self.result = "0"; self.new_num = True
        elif val == "del":
            self.expr = self.expr[:-1] if self.expr else ""
            self.result = self.expr or "0"
        elif val == "negate":
            try:
                v = float(self.result)
                self.result = str(-v)
                self.expr   = self.result
            except: pass
        elif val == "pct":
            try:
                self.result = str(float(self.result) / 100)
                self.expr   = self.result
            except: pass
        elif val.startswith("op"):
            op = val[2:]
            self.expr += op
            self.result = self.expr
        else:
            if self.new_num and val not in "()":
                self.new_num = False
            self.expr += val
            self.result = self.expr
        self._update()

    def _sci(self, btn, val):
        self.expr += val
        self.result = self.expr
        self._update()

    def _calculate(self):
        try:
            safe = self.expr.replace("^","**")
            r = eval(safe, {"__builtins__":{},"math":math})
            self.expr_lbl.set_text(self.expr + " =")
            if isinstance(r, (int, float)):
                if isinstance(r, float):
                    self.result = f"{r:.10f}".rstrip('0').rstrip('.')
                    if self.result == "":
                        self.result = "0"
                else:
                    self.result = str(r)
            else:
                self.result = str(r)
            self.expr    = self.result
            self.new_num = True
        except Exception:
            self.result = "Error"
        self._update()

    def _update(self):
        self.result_lbl.set_text(self.result or "0")
        if not self.expr_lbl.get_text().endswith("="):
            self.expr_lbl.set_text(self.expr)

    def _on_key(self, w, e):
        key = Gdk.keyval_name(e.keyval)
        if key in "0123456789.":    self._press(None, key)
        elif key == "Return":        self._press(None, "eq")
        elif key == "BackSpace":     self._press(None, "del")
        elif key == "Escape":        self._press(None, "clear")
        elif key == "plus":          self._press(None, "op+")
        elif key == "minus":         self._press(None, "op-")
        elif key == "asterisk":      self._press(None, "op*")
        elif key == "slash":         self._press(None, "op/")

def main():
    win = AmitCalc()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
