# AmitOS UI Framework
from .theme import apply_theme, COLORS, GTK_CSS
from .widgets import AmitButton, AmitCard, AmitLabel, AmitHeader
from .dialogs import AmitDialog, AmitErrorDialog, AmitConfirmDialog

__all__ = [
    "apply_theme", "COLORS", "GTK_CSS",
    "AmitButton", "AmitCard", "AmitLabel", "AmitHeader",
    "AmitDialog", "AmitErrorDialog", "AmitConfirmDialog",
]
