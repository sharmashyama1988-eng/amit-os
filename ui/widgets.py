"""AmitOS Custom GTK3 Widgets"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib


class AmitButton(Gtk.Button):
    """Styled AmitOS button with variants"""
    def __init__(self, label="", variant="primary", icon=None):
        super().__init__(label=label)
        ctx = self.get_style_context()
        ctx.add_class("amit-button")
        if variant == "danger":
            ctx.add_class("danger")
        elif variant == "success":
            ctx.add_class("success")
        if icon:
            self.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
            self.set_always_show_image(True)


class AmitCard(Gtk.Frame):
    """A styled card container"""
    def __init__(self, title=""):
        super().__init__()
        self.set_shadow_type(Gtk.ShadowType.NONE)
        self.get_style_context().add_class("amit-card")
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._box.set_margin_top(12)
        self._box.set_margin_bottom(12)
        self._box.set_margin_start(12)
        self._box.set_margin_end(12)
        if title:
            lbl = Gtk.Label(label=f"<b>{title}</b>")
            lbl.set_use_markup(True)
            lbl.set_halign(Gtk.Align.START)
            self._box.pack_start(lbl, False, False, 0)
        self.add(self._box)

    def add_widget(self, widget):
        self._box.pack_start(widget, False, False, 0)


class AmitLabel(Gtk.Label):
    """AmitOS styled label"""
    def __init__(self, text="", secondary=False, markup=False):
        super().__init__()
        if markup:
            self.set_markup(text)
        else:
            self.set_text(text)
        self.set_halign(Gtk.Align.START)
        if secondary:
            self.get_style_context().add_class("amit-label-secondary")


class AmitHeader(Gtk.Box):
    """Top header bar for AmitOS apps"""
    def __init__(self, title="", subtitle=""):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.get_style_context().add_class("amit-header")
        self.set_margin_bottom(0)

        icon = Gtk.Image.new_from_icon_name("computer", Gtk.IconSize.LARGE_TOOLBAR)
        self.pack_start(icon, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_lbl = Gtk.Label(label=f"<b>{title}</b>")
        title_lbl.set_use_markup(True)
        title_lbl.set_halign(Gtk.Align.START)
        vbox.pack_start(title_lbl, False, False, 0)

        if subtitle:
            sub_lbl = Gtk.Label(label=subtitle)
            sub_lbl.get_style_context().add_class("amit-label-secondary")
            sub_lbl.set_halign(Gtk.Align.START)
            vbox.pack_start(sub_lbl, False, False, 0)

        self.pack_start(vbox, True, True, 0)


class AmitSearchBar(Gtk.SearchEntry):
    """AmitOS search bar"""
    def __init__(self, placeholder="Search..."):
        super().__init__()
        self.set_placeholder_text(placeholder)
        self.get_style_context().add_class("amit-entry")


class AmitSpinner(Gtk.Box):
    """Loading spinner with label"""
    def __init__(self, text="Loading..."):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.set_halign(Gtk.Align.CENTER)
        self._spinner = Gtk.Spinner()
        self.pack_start(self._spinner, False, False, 0)
        self.pack_start(Gtk.Label(label=text), False, False, 0)

    def start(self):
        self._spinner.start()

    def stop(self):
        self._spinner.stop()
