"""Visual theme: colour palette, fonts, DPI scaling and ttk styling."""

import tkinter as tk
from tkinter import ttk

COLORS = {
    # Surfaces
    "bg": "#F1F5F9",
    "card": "#FFFFFF",
    "card_alt": "#F8FAFC",
    "border": "#E2E8F0",
    "border_strong": "#CBD5E1",
    # Sidebar
    "sidebar": "#0B1A30",
    "sidebar_hover": "#132744",
    "sidebar_active": "#1A3358",
    "sidebar_text": "#93A4BD",
    "sidebar_text_active": "#FFFFFF",
    "sidebar_heading": "#5C6F8C",
    # Brand
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "accent_soft": "#E8EFFE",
    "amber": "#F59E0B",
    "amber_dark": "#B45309",
    "amber_soft": "#FEF3E2",
    # Text
    "text": "#0F172A",
    "text_muted": "#64748B",
    "text_subtle": "#94A3B8",
    # Result panel
    "result_bg": "#0E2342",
    "result_text": "#FFFFFF",
    "result_muted": "#9FB3CF",
    "result_divider": "#24406A",
    # States
    "error": "#DC2626",
    "error_soft": "#FDECEC",
    "disabled_bg": "#F1F5F9",
}

FONT = "Segoe UI"
FONT_SEMI = "Segoe UI Semibold"

_scale = 1.0


def set_scale(value: float) -> None:
    global _scale
    _scale = max(1.0, value)


def scale() -> float:
    return _scale


def px(n: float) -> int:
    """Convert a design size in logical pixels to device pixels."""
    return int(round(n * _scale))


def hex_to_rgb(color: str):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def apply_theme(root: tk.Tk) -> None:
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    c = COLORS
    style.configure(".", font=(FONT, 10), background=c["bg"], foreground=c["text"])

    for name, bg in (("App", c["bg"]), ("Card", c["card"]), ("Sidebar", c["sidebar"]),
                     ("Result", c["result_bg"])):
        style.configure(f"{name}.TFrame", background=bg)

    labels = {
        "Eyebrow": (c["bg"], c["accent"], (FONT_SEMI, 9)),
        "Title": (c["bg"], c["text"], (FONT_SEMI, 20)),
        "Subtitle": (c["bg"], c["text_muted"], (FONT, 10)),
        "Section": (c["bg"], c["text_muted"], (FONT_SEMI, 9)),
        "CardTitle": (c["card"], c["text"], (FONT_SEMI, 12)),
        "CardSub": (c["card"], c["text_muted"], (FONT, 9)),
        "Field": (c["card"], c["text"], (FONT_SEMI, 9)),
        "Body": (c["card"], c["text"], (FONT, 10)),
        "Muted": (c["card"], c["text_muted"], (FONT, 9)),
        "Value": (c["card"], c["accent_hover"], (FONT_SEMI, 18)),
        "Error": (c["card"], c["error"], (FONT, 9)),
    }
    for name, (bg, fg, font) in labels.items():
        style.configure(f"{name}.TLabel", background=bg, foreground=fg, font=font)

    flat = dict(borderwidth=0, focusthickness=0, relief="flat")
    style.configure("Accent.TButton", background=c["accent"], foreground="white",
                    font=(FONT_SEMI, 10), padding=(px(20), px(9)),
                    bordercolor=c["accent"], lightcolor=c["accent"], darkcolor=c["accent"], **flat)
    style.map("Accent.TButton",
              background=[("pressed", c["accent_hover"]), ("active", c["accent_hover"])],
              bordercolor=[("active", c["accent_hover"])],
              lightcolor=[("active", c["accent_hover"])],
              darkcolor=[("active", c["accent_hover"])])

    style.configure("Ghost.TButton", background=c["card"], foreground=c["text"],
                    font=(FONT_SEMI, 10), padding=(px(16), px(8)), borderwidth=1,
                    bordercolor=c["border_strong"], lightcolor=c["card"], darkcolor=c["card"],
                    focusthickness=0, relief="solid")
    style.map("Ghost.TButton",
              background=[("pressed", c["bg"]), ("active", c["card_alt"])],
              bordercolor=[("active", c["text_subtle"])])

    style.configure("TCombobox", padding=(px(8), px(6)), arrowsize=px(14),
                    fieldbackground=c["card"], background=c["card"], foreground=c["text"],
                    bordercolor=c["border_strong"], lightcolor=c["card"], darkcolor=c["card"],
                    arrowcolor=c["text_muted"], selectbackground=c["card"],
                    selectforeground=c["text"])
    style.map("TCombobox",
              fieldbackground=[("disabled", c["disabled_bg"]), ("readonly", c["card"])],
              foreground=[("disabled", c["text_subtle"])],
              bordercolor=[("focus", c["accent"]), ("hover", c["text_subtle"])],
              lightcolor=[("focus", c["accent"])],
              background=[("disabled", c["disabled_bg"])],
              arrowcolor=[("disabled", c["text_subtle"]), ("hover", c["accent"])],
              selectbackground=[("focus", c["card"])],
              selectforeground=[("focus", c["text"])])
    root.option_add("*TCombobox*Listbox.font", (FONT, 10))
    root.option_add("*TCombobox*Listbox.background", c["card"])
    root.option_add("*TCombobox*Listbox.foreground", c["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", "white")
    root.option_add("*TCombobox*Listbox.borderWidth", 0)

    style.configure("Treeview", background=c["card"], fieldbackground=c["card"],
                    foreground=c["text"], rowheight=px(34), borderwidth=0, font=(FONT, 10))
    style.map("Treeview", background=[("selected", c["accent_soft"])],
              foreground=[("selected", c["text"])])
    style.configure("Treeview.Heading", background=c["card_alt"], foreground=c["text_muted"],
                    font=(FONT_SEMI, 9), relief="flat", borderwidth=0, padding=(px(10), px(8)))
    style.map("Treeview.Heading", background=[("active", c["bg"])])
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    style.configure("TSeparator", background=c["border"])
