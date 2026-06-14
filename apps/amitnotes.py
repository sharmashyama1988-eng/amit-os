#!/usr/bin/env python3
"""
AmitNotes - Quick Notes App
Amit OS v1.0
"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import json, os, time
from datetime import datetime

NOTES_FILE = os.path.expanduser("~/.local/share/amitos/notes.json")
os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)

CSS = b"""
* { font-family: 'Noto Sans', sans-serif; }
window { background: #111827; }
.sidebar { background: #1f2937; border-right: 1px solid #374151; }
.note-row {
    padding: 12px 16px;
    border-bottom: 1px solid #374151;
    color: #e5e7eb;
}
.note-row:hover { background: #374151; }
.note-row.selected { background: #1d4ed8; }
.note-title { font-weight: bold; font-size: 14px; color: #f9fafb; }
.note-preview { font-size: 12px; color: #9ca3af; }
.note-date { font-size: 10px; color: #6b7280; }
.editor {
    background: #111827;
    color: #e5e7eb;
    font-size: 15px;
    font-family: 'Noto Sans', sans-serif;
    padding: 20px;
    border: none;
}
.toolbar { background: #1f2937; padding: 6px 12px; }
.btn-action {
    background: #1d4ed8;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 6px 14px;
    font-size: 13px;
}
.btn-action:hover { background: #2563eb; }
.btn-del {
    background: #7f1d1d;
    color: #fca5a5;
    border-radius: 8px;
    border: none;
    padding: 6px 14px;
    font-size: 13px;
}
.btn-del:hover { background: #991b1b; }
.search-entry {
    background: #374151;
    color: #e5e7eb;
    border: 1px solid #4b5563;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    margin: 8px;
}
.empty-state { color: #4b5563; font-size: 16px; }
"""

class Note:
    def __init__(self, nid=None, title="", body="", ts=None):
        self.id    = nid or str(int(time.time() * 1000))
        self.title = title
        self.body  = body
        self.ts    = ts or time.time()

    def to_dict(self):
        return {"id": self.id, "title": self.title, "body": self.body, "ts": self.ts}

    @staticmethod
    def from_dict(d):
        return Note(d["id"], d["title"], d["body"], d["ts"])


class AmitNotes(Gtk.Window):
    def __init__(self):
        super().__init__(title="AmitNotes")
        self.set_default_size(780, 520)
        self.notes   = []
        self.current = None
        self._dirty  = False
        self._block_select = False

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._load_notes()
        self._build()
        self._refresh_list()
        GLib.timeout_add(5000, self._autosave)

    # ── Persistence ──────────────────────────────────────────
    def _load_notes(self):
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE) as f:
                    self.notes = [Note.from_dict(d) for d in json.load(f)]
            except Exception:
                self.notes = []

    def _save_notes(self):
        with open(NOTES_FILE, "w") as f:
            json.dump([n.to_dict() for n in self.notes], f, indent=2)

    def _autosave(self):
        if self._dirty:
            self._save_current()
        return True

    # ── Build UI ─────────────────────────────────────────────
    def _build(self):
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(paned)

        # ── Left sidebar ─────────────────────────────────────
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.get_style_context().add_class("sidebar")
        sidebar.set_size_request(220, -1)

        # Toolbar
        tb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tb.get_style_context().add_class("toolbar")
        new_btn = Gtk.Button(label="+ New")
        new_btn.get_style_context().add_class("btn-action")
        new_btn.connect("clicked", self._new_note)
        tb.pack_start(new_btn, True, True, 0)
        sidebar.pack_start(tb, False, False, 0)

        # Search
        self.search = Gtk.Entry(placeholder_text="Search notes...")
        self.search.get_style_context().add_class("search-entry")
        self.search.connect("changed", self._on_search)
        sidebar.pack_start(self.search, False, False, 0)

        # List
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect("row-selected", self._on_select)
        scroll.add(self.list_box)
        sidebar.pack_start(scroll, True, True, 0)
        paned.pack1(sidebar, False, False)

        # ── Right editor ─────────────────────────────────────
        editor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Editor toolbar
        etb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        etb.get_style_context().add_class("toolbar")
        self.title_entry = Gtk.Entry(placeholder_text="Note title...")
        self.title_entry.set_hexpand(True)
        self.title_entry.connect("changed", self._mark_dirty)
        etb.pack_start(self.title_entry, True, True, 0)

        save_btn = Gtk.Button(label="Save")
        save_btn.get_style_context().add_class("btn-action")
        save_btn.connect("clicked", lambda _: self._save_current())
        etb.pack_start(save_btn, False, False, 0)

        del_btn = Gtk.Button(label="Delete")
        del_btn.get_style_context().add_class("btn-del")
        del_btn.connect("clicked", self._delete_note)
        etb.pack_start(del_btn, False, False, 0)
        editor_box.pack_start(etb, False, False, 0)

        # Text editor
        scroll2 = Gtk.ScrolledWindow()
        self.textview = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD)
        self.textview.get_style_context().add_class("editor")
        self.textview.get_buffer().connect("changed", self._mark_dirty)
        scroll2.add(self.textview)
        editor_box.pack_start(scroll2, True, True, 0)
        paned.pack2(editor_box, True, False)

    # ── List management ──────────────────────────────────────
    def _make_row(self, note):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.get_style_context().add_class("note-row")
        box.set_margin_top(2); box.set_margin_bottom(2)

        title = Gtk.Label(label=note.title or "Untitled", xalign=0)
        title.get_style_context().add_class("note-title")
        title.set_ellipsize(Pango.EllipsizeMode.END)

        preview = note.body.replace("\n", " ")[:60]
        prev_lbl = Gtk.Label(label=preview, xalign=0)
        prev_lbl.get_style_context().add_class("note-preview")
        prev_lbl.set_ellipsize(Pango.EllipsizeMode.END)

        dt = datetime.fromtimestamp(note.ts).strftime("%b %d, %H:%M")
        date_lbl = Gtk.Label(label=dt, xalign=0)
        date_lbl.get_style_context().add_class("note-date")

        box.pack_start(title,    False, False, 0)
        box.pack_start(prev_lbl, False, False, 0)
        box.pack_start(date_lbl, False, False, 0)
        row = Gtk.ListBoxRow()
        row.add(box)
        row._note_id = note.id
        return row

    def _refresh_list(self, query=""):
        for child in self.list_box.get_children():
            self.list_box.remove(child)
        q = query.lower()
        for note in sorted(self.notes, key=lambda n: n.ts, reverse=True):
            if q and q not in note.title.lower() and q not in note.body.lower():
                continue
            self.list_box.add(self._make_row(note))
        self.list_box.show_all()

    def _on_search(self, entry):
        self._refresh_list(entry.get_text())

    def _on_select(self, lb, row):
        if self._block_select or not row: return
        self._save_current()
        note = next((n for n in self.notes if n.id == row._note_id), None)
        if not note: return
        self.current = note
        self._block_select = True
        self.title_entry.set_text(note.title)
        buf = self.textview.get_buffer()
        buf.set_text(note.body)
        self._block_select = False
        self._dirty = False

    def _mark_dirty(self, *_):
        self._dirty = True

    # ── Actions ──────────────────────────────────────────────
    def _new_note(self, *_):
        self._save_current()
        note = Note(title="New Note", body="")
        self.notes.append(note)
        self.current = note
        self._save_notes()
        self._block_select = True
        self._refresh_list()
        # Re-select the new note row in list_box
        for child in self.list_box.get_children():
            if getattr(child, "_note_id", None) == note.id:
                self.list_box.select_row(child)
                break
        self.title_entry.set_text("New Note")
        self.textview.get_buffer().set_text("")
        self._block_select = False
        self.title_entry.grab_focus()

    def _save_current(self, *_):
        if not self.current: return
        self.current.title = self.title_entry.get_text() or "Untitled"
        buf = self.textview.get_buffer()
        self.current.body  = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        self.current.ts    = time.time()
        self._save_notes()
        self._dirty = False
        self._block_select = True
        self._refresh_list(self.search.get_text())
        # Re-select the current note
        for child in self.list_box.get_children():
            if getattr(child, "_note_id", None) == self.current.id:
                self.list_box.select_row(child)
                break
        self._block_select = False

    def _delete_note(self, *_):
        if not self.current: return
        self.notes = [n for n in self.notes if n.id != self.current.id]
        self.current = None
        self._save_notes()
        self._refresh_list()
        self.title_entry.set_text("")
        self.textview.get_buffer().set_text("")


def main():
    win = AmitNotes()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
