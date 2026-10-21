import sys
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from . import app_info
from .diagrams import render_icon
from .theme import COLORS, FONT, FONT_SEMI, apply_theme, hex_to_rgb, px, scale, set_scale
from .widgets import NavItem, resource_path
from .pages import (
    AboutPage,
    AnglePage,
    BeamPage,
    BoxSectionPage,
    ChannelPage,
    HomePage,
    PipePage,
    PlatePage,
    RoundBarPage,
    SpecificGravityPage,
    TeePage,
    UnitConverterPage,
)

NAV_GROUPS = [
    (None, [("home", "Home")]),
    ("CALCULATORS", [
        ("round_bar", "Solid Shaft"),
        ("pipe", "Hollow Shaft / Pipe"),
        ("box", "Box Section"),
        ("plate", "Plate"),
        ("beam", "Beam Section"),
        ("channel", "Channel Section"),
        ("angle", "Angle Section"),
        ("tee", "Tee Section"),
    ]),
    ("REFERENCE", [
        ("sg_ref", "Specific Gravity"),
        ("units", "Unit Converter"),
    ]),
]

PAGE_CLASSES = {
    "home": HomePage,
    "round_bar": RoundBarPage,
    "pipe": PipePage,
    "box": BoxSectionPage,
    "plate": PlatePage,
    "beam": BeamPage,
    "channel": ChannelPage,
    "angle": AnglePage,
    "tee": TeePage,
    "sg_ref": SpecificGravityPage,
    "units": UnitConverterPage,
    "about": AboutPage,
}


def _enable_dpi_awareness():
    """Render crisply on high-DPI Windows displays instead of being bitmap-stretched."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _work_area(root):
    """Screen area excluding the taskbar: (x, y, width, height)."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            rect = wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):  # SPI_GETWORKAREA
                return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
        except Exception:
            pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight() - 60


class WeightCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        set_scale(self.winfo_fpixels("1i") / 96.0)
        self.title(f"{app_info.APP_NAME} — {app_info.COMPANY}")
        self._set_window_icon()

        wx, wy, ww, wh = _work_area(self)
        title_bar = px(32)
        w, h = min(px(1200), ww - px(24)), min(px(780), wh - title_bar - px(16))
        self.geometry(f"{w}x{h}+{wx + max((ww - w) // 2, 0)}+{wy + max((wh - h - title_bar) // 2, 0)}")
        self.minsize(min(px(1060), w), min(px(660), h))
        apply_theme(self)

        outer = ttk.Frame(self, style="App.TFrame")
        outer.pack(fill="both", expand=True)
        self._build_sidebar(outer)

        self.container = ttk.Frame(outer, style="App.TFrame")
        self.container.pack(side="left", fill="both", expand=True)
        self.pages = {}
        for key, cls in PAGE_CLASSES.items():
            page = cls(self.container, self)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.pages[key] = page
        self.show_page("home")

    def _set_window_icon(self):
        try:
            if sys.platform == "win32":
                self.iconbitmap(default=resource_path("assets", "icon.ico"))
            else:
                self._icon_photo = tk.PhotoImage(file=resource_path("assets", "icon.png"))
                self.iconphoto(True, self._icon_photo)
        except tk.TclError:
            pass

    def _build_sidebar(self, outer):
        c = COLORS
        sidebar = tk.Frame(outer, bg=c["sidebar"], width=px(244))
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=c["sidebar"], padx=px(18), pady=px(20))
        brand.pack(fill="x")
        logo = Image.open(resource_path("assets", "icon.png")).resize((px(40), px(40)), Image.LANCZOS)
        self._logo = ImageTk.PhotoImage(logo)
        tk.Label(brand, image=self._logo, bg=c["sidebar"]).pack(side="left")
        names = tk.Frame(brand, bg=c["sidebar"])
        names.pack(side="left", padx=(px(12), 0))
        tk.Label(names, text=app_info.APP_NAME, bg=c["sidebar"], fg="white",
                 font=(FONT_SEMI, 12)).pack(anchor="w")
        tk.Label(names, text=app_info.COMPANY, bg=c["sidebar"], fg=c["sidebar_text"],
                 font=(FONT, 8)).pack(anchor="w")
        tk.Frame(sidebar, bg=c["sidebar_hover"], height=1).pack(fill="x", padx=px(16))

        self._icons = []
        self.nav = {}
        normal = hex_to_rgb(c["sidebar_text"])
        active = hex_to_rgb(c["amber"])

        def add_item(parent, key, label):
            icon_kind = key if key != "home" else "home"
            ic = ImageTk.PhotoImage(render_icon(icon_kind, 18, normal, scale=scale()))
            ia = ImageTk.PhotoImage(render_icon(icon_kind, 18, active, scale=scale()))
            self._icons += [ic, ia]
            item = NavItem(parent, label, ic, ia, lambda k=key: self.show_page(k))
            item.pack(fill="x")
            self.nav[key] = item

        nav = tk.Frame(sidebar, bg=c["sidebar"])
        nav.pack(fill="x", pady=(px(10), 0))
        for heading, items in NAV_GROUPS:
            if heading:
                tk.Label(nav, text=heading, bg=c["sidebar"], fg=c["sidebar_heading"],
                         font=(FONT_SEMI, 8), anchor="w").pack(fill="x", padx=px(20), pady=(px(12), px(4)))
            for key, label in items:
                add_item(nav, key, label)

        footer = tk.Frame(sidebar, bg=c["sidebar"])
        footer.pack(side="bottom", fill="x", pady=(0, px(14)))
        add_item(footer, "about", "About")
        tk.Label(footer, text=f"v{app_info.VERSION}  ·  © {app_info.COPYRIGHT_YEAR} {app_info.COMPANY}",
                 bg=c["sidebar"], fg=c["sidebar_heading"], font=(FONT, 8), anchor="w").pack(
            fill="x", padx=px(20), pady=(px(8), 0))

    def show_page(self, key: str):
        page = self.pages.get(key)
        if page is None:
            return
        page.tkraise()
        for k, item in self.nav.items():
            item.set_active(k == key)


def main():
    _enable_dpi_awareness()
    app = WeightCalculatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
