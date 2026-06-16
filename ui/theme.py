"""
AmitOS Dark Theme
=================
Centralized theme constants, GTK CSS, and apply_theme() helper.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
BG          = "#141721"   # Primary background
BG_ALT      = "#1C2030"   # Slightly lighter background (cards, sidebars)
BG_SURFACE  = "#232839"   # Surface / elevated elements
FG          = "#DCE1EB"   # Primary foreground / text
FG_MUTED    = "#8892A4"   # Secondary / muted text
ACCENT      = "#0078FF"   # Primary accent (blue)
ACCENT_DARK = "#005FCC"   # Darker accent for hover / pressed states
ACCENT_GLOW = "#0078FF44" # Translucent accent for focus rings
SUCCESS     = "#23D18B"   # Success / green
WARNING     = "#F5A623"   # Warning / orange
ERROR       = "#F44747"   # Error / red
BORDER      = "#2E3650"   # Subtle border colour
SHADOW      = "rgba(0,0,0,0.45)"

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FONT_FAMILY   = "Inter"
FONT_FALLBACK = "Inter, Cantarell, Noto Sans, Sans-Serif"
FONT_SIZE_SM  = 11
FONT_SIZE_MD  = 13
FONT_SIZE_LG  = 15
FONT_SIZE_XL  = 18
FONT_SIZE_H1  = 24

# ---------------------------------------------------------------------------
# Spacing / sizing
# ---------------------------------------------------------------------------
RADIUS_SM  = 4
RADIUS_MD  = 8
RADIUS_LG  = 12
RADIUS_XL  = 16
PADDING_SM = 6
PADDING_MD = 12
PADDING_LG = 20

# ---------------------------------------------------------------------------
# GTK CSS
# ---------------------------------------------------------------------------
GTK_CSS = """
/* == Global reset ================================================= */
* {
    font-family: Inter, Cantarell, Noto Sans, Sans-Serif;
    font-size: 13pt;
    color: #DCE1EB;
    outline: none;
}

/* == Window / background ========================================== */
window,
.amit-window {
    background-color: #141721;
    color: #DCE1EB;
}

/* == AmitButton =================================================== */
.amit-button {
    background: linear-gradient(180deg, #0078FF 0%, #005FCC 100%);
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 6px 20px;
    font-weight: 600;
    font-size: 13pt;
    transition: all 150ms ease;
    box-shadow: 0 2px 8px #0078FF44;
}

.amit-button:hover {
    background: linear-gradient(180deg, #1A8AFF 0%, #0078FF 100%);
    box-shadow: 0 4px 16px #0078FF44;
}

.amit-button:active {
    background: #005FCC;
    box-shadow: none;
}

.amit-button:disabled {
    background: #232839;
    color: #8892A4;
    box-shadow: none;
}

/* Secondary / ghost button */
.amit-button-secondary {
    background: transparent;
    color: #0078FF;
    border: 1px solid #0078FF;
    border-radius: 8px;
    padding: 6px 20px;
    font-weight: 600;
    font-size: 13pt;
    transition: all 150ms ease;
}

.amit-button-secondary:hover {
    background: #0078FF44;
}

.amit-button-secondary:active {
    background: #0078FF;
    color: #FFFFFF;
}

/* Danger button */
.amit-button-danger {
    background: linear-gradient(180deg, #F44747 0%, #CC2222 100%);
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 6px 20px;
    font-weight: 600;
    transition: all 150ms ease;
}

.amit-button-danger:hover {
    background: linear-gradient(180deg, #FF5555 0%, #F44747 100%);
}

/* == AmitLabel ==================================================== */
.amit-label {
    color: #DCE1EB;
    font-size: 13pt;
}

.amit-label-muted {
    color: #8892A4;
    font-size: 11pt;
}

.amit-label-heading {
    color: #DCE1EB;
    font-size: 18pt;
    font-weight: 700;
}

.amit-label-h1 {
    color: #DCE1EB;
    font-size: 24pt;
    font-weight: 800;
}

.amit-label-accent {
    color: #0078FF;
    font-weight: 600;
}

/* == AmitCard ===================================================== */
.amit-card {
    background-color: #1C2030;
    border: 1px solid #2E3650;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}

.amit-card:hover {
    border-color: #0078FF;
    box-shadow: 0 4px 20px rgba(0,120,255,0.15);
}

/* == AmitHeader =================================================== */
.amit-header {
    background: linear-gradient(90deg, #232839 0%, #1C2030 100%);
    border-bottom: 1px solid #2E3650;
    padding: 12px 20px;
    min-height: 52px;
}

.amit-header-title {
    color: #DCE1EB;
    font-size: 15pt;
    font-weight: 700;
}

.amit-header-subtitle {
    color: #8892A4;
    font-size: 11pt;
}

/* == Dialogs ====================================================== */
.amit-dialog {
    background-color: #1C2030;
    border-radius: 16px;
    border: 1px solid #2E3650;
}

.amit-dialog-title {
    font-size: 15pt;
    font-weight: 700;
    color: #DCE1EB;
    padding-bottom: 6px;
}

.amit-dialog-body {
    color: #8892A4;
    font-size: 13pt;
}

.amit-error-icon {
    color: #F44747;
    font-size: 32pt;
    font-weight: 900;
}

/* == Scrollbars =================================================== */
scrollbar {
    background-color: transparent;
    border: none;
}

scrollbar slider {
    background-color: #2E3650;
    border-radius: 4px;
    min-width: 6px;
    min-height: 6px;
}

scrollbar slider:hover {
    background-color: #8892A4;
}

/* == Entry / TextInput ============================================ */
entry {
    background-color: #232839;
    color: #DCE1EB;
    border: 1px solid #2E3650;
    border-radius: 8px;
    padding: 6px 12px;
    caret-color: #0078FF;
}

entry:focus {
    border-color: #0078FF;
    box-shadow: 0 0 0 2px #0078FF44;
}

/* == Separator ==================================================== */
separator {
    background-color: #2E3650;
    min-height: 1px;
    min-width: 1px;
}

/* == Tooltip ====================================================== */
tooltip {
    background-color: #232839;
    color: #DCE1EB;
    border: 1px solid #2E3650;
    border-radius: 4px;
    padding: 6px 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
"""


# ---------------------------------------------------------------------------
# apply_theme()
# ---------------------------------------------------------------------------
def apply_theme(widget=None):
    """
    Load AmitOS CSS into the GTK style system.

    Parameters
    ----------
    widget : Gtk.Widget, optional
        If provided, the CSS provider is added to this widget's style context
        in addition to the global screen provider.

    Returns
    -------
    Gtk.CssProvider
        The loaded provider so callers can hold a reference if needed.

    Usage
    -----
    >>> from ui.theme import apply_theme
    >>> apply_theme()        # global – call once at startup
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(GTK_CSS.encode("utf-8"))

    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )

    if widget is not None:
        widget.get_style_context().add_provider(
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # Prefer a dark GTK theme variant (e.g. Adwaita-dark) if available
    settings = Gtk.Settings.get_default()
    if settings is not None:
        settings.set_property("gtk-application-prefer-dark-theme", True)

    return provider


def hex_to_rgba(hex_color, alpha=1.0):
    """
    Convert a CSS hex colour string to a Gdk.RGBA.

    Parameters
    ----------
    hex_color : str
        Colour in ``#RRGGBB`` or ``#RGB`` format.
    alpha : float
        Opacity in the range [0.0, 1.0].
    """
    rgba = Gdk.RGBA()
    rgba.parse(hex_color)
    rgba.alpha = alpha
    return rgba
