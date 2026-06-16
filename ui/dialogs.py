"""AmitOS Dialog Classes"""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class AmitDialog(Gtk.Dialog):
    """Base AmitOS dialog"""
    def __init__(self, parent, title, width=400, height=200):
        super().__init__(title=title, transient_for=parent, modal=True)
        self.set_default_size(width, height)
        self.set_border_width(16)


class AmitErrorDialog(AmitDialog):
    """Error dialog with icon"""
    def __init__(self, parent, message, title="Error"):
        super().__init__(parent, title)
        box = self.get_content_area()
        hbox = Gtk.Box(spacing=12)
        icon = Gtk.Image.new_from_icon_name("dialog-error", Gtk.IconSize.DIALOG)
        hbox.pack_start(icon, False, False, 0)
        lbl = Gtk.Label(label=message)
        lbl.set_line_wrap(True)
        hbox.pack_start(lbl, True, True, 0)
        box.pack_start(hbox, True, True, 0)
        self.add_button("OK", Gtk.ResponseType.OK)
        self.show_all()


class AmitConfirmDialog(AmitDialog):
    """Confirmation dialog"""
    def __init__(self, parent, message, title="Confirm"):
        super().__init__(parent, title)
        box = self.get_content_area()
        hbox = Gtk.Box(spacing=12)
        icon = Gtk.Image.new_from_icon_name("dialog-question", Gtk.IconSize.DIALOG)
        hbox.pack_start(icon, False, False, 0)
        lbl = Gtk.Label(label=message)
        lbl.set_line_wrap(True)
        hbox.pack_start(lbl, True, True, 0)
        box.pack_start(hbox, True, True, 0)
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("OK", Gtk.ResponseType.OK)
        self.show_all()

    def confirmed(self):
        return self.run() == Gtk.ResponseType.OK


class AmitAboutDialog(Gtk.AboutDialog):
    """AmitOS About dialog"""
    def __init__(self, parent, app_name="AmitOS App", version="1.0"):
        super().__init__(transient_for=parent, modal=True)
        self.set_program_name(app_name)
        self.set_version(version)
        self.set_copyright("© 2026 Amit OS")
        self.set_comments("Part of the Amit OS ecosystem")
        self.set_license_type(Gtk.License.MIT_X11)
        self.set_website("https://github.com/sharmashyama1988-eng/amit-os")
        self.set_logo_icon_name("computer")
