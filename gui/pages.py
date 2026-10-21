"""One page per calculator / reference tool."""

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from core import calculations as calc
from core.materials import SPECIFIC_GRAVITY, DEFAULT_MATERIAL, UNIT_FACTS
from core.sections import (
    BEAM_SECTIONS,
    CHANNEL_SECTIONS,
    EQUAL_ANGLE_SECTIONS,
    UNEQUAL_ANGLE_SECTIONS,
    TEE_SECTIONS,
)
from . import app_info
from .diagrams import render_reference_art, render_section
from .theme import COLORS, FONT, FONT_SEMI, hex_to_rgb, px, scale
from .widgets import (
    AsyncImage,
    Card,
    LabeledCombo,
    LabeledEntry,
    MaterialPicker,
    ResultPanel,
    Segmented,
    bind_tree,
    card_heading,
    divider,
    page_header,
    resource_path,
)

CARD_RGB = hex_to_rgb(COLORS["card"])
DIAGRAM_SIZE = (380, 234)
PAGE_PAD = (28, 22)
LB_PER_KG = 2.2046


def _page_padding():
    return (px(PAGE_PAD[0]), px(PAGE_PAD[1]))


def _require_positive(**values):
    for name, v in values.items():
        if v <= 0:
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be greater than zero.")


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------
SHAPE_TILES = [
    ("round_bar", "Solid Shaft", "Round bar · diameter × length"),
    ("pipe", "Hollow Shaft / Pipe", "Outer & inner diameter"),
    ("box", "Box Section", "Rectangular hollow section"),
    ("plate", "Plate", "Length × width × thickness"),
    ("beam", "Beam Section", "IS beams or custom I-section"),
    ("channel", "Channel Section", "IS channels or custom"),
    ("angle", "Angle Section", "Equal & unequal angles"),
    ("tee", "Tee Section", "IS tee bars or custom"),
]


class _Tile(tk.Frame):
    """Clickable card with hover highlight."""

    def __init__(self, parent, command, **kwargs):
        super().__init__(parent, bg=COLORS["card"], highlightthickness=1,
                         highlightbackground=COLORS["border"], cursor="hand2", **kwargs)
        self.command = command

    def finish(self):
        bind_tree(self, "<Button-1>", lambda e: self.command())
        bind_tree(self, "<Enter>", lambda e: self.configure(highlightbackground=COLORS["accent"]))
        bind_tree(self, "<Leave>", lambda e: self.configure(highlightbackground=COLORS["border"]))


class HomePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="App.TFrame", padding=_page_padding())
        page_header(
            self, app_info.APP_NAME,
            "Theoretical weight of metal shapes and Indian Standard structural steel sections.",
            eyebrow=app_info.COMPANY,
        ).pack(fill="x", pady=(0, px(18)))

        ttk.Label(self, text="SHAPES & SECTIONS", style="Section.TLabel").pack(anchor="w", pady=(0, px(8)))
        grid = ttk.Frame(self, style="App.TFrame")
        grid.pack(fill="x")
        cols = 4
        self.thumbs = []
        for i, (key, title, desc) in enumerate(SHAPE_TILES):
            r, c = divmod(i, cols)
            tile = _Tile(grid, lambda k=key: controller.show_page(k))
            tile.grid(row=r, column=c, padx=(0 if c == 0 else px(7), 0 if c == cols - 1 else px(7)),
                      pady=(0, px(14)), sticky="nsew")
            thumb = AsyncImage(tile, lambda **kw: render_section(detailed=False, bg=CARD_RGB, **kw),
                               176, 104, COLORS["card"], kind=key)
            thumb.pack(pady=(px(10), 0))
            thumb.request()
            self.thumbs.append(thumb)
            body = tk.Frame(tile, bg=COLORS["card"], padx=px(14), pady=px(10))
            body.pack(fill="x")
            ttk.Label(body, text=title, style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(body, text=desc, style="Muted.TLabel").pack(anchor="w", pady=(px(1), 0))
            tile.finish()
        for c in range(cols):
            grid.columnconfigure(c, weight=1, uniform="tile")

        ttk.Label(self, text="REFERENCE & INFO", style="Section.TLabel").pack(anchor="w", pady=(px(4), px(8)))
        ref = ttk.Frame(self, style="App.TFrame")
        ref.pack(fill="x")
        refs = [
            ("sg_ref", "Specific Gravity", "Material density reference table"),
            ("units", "Unit Converter", "Length & weight conversions"),
            ("about", "About", f"Version {app_info.VERSION} · author & credits"),
        ]
        self._ref_images = []
        for i, (key, title, desc) in enumerate(refs):
            tile = _Tile(ref, lambda k=key: controller.show_page(k), padx=px(14), pady=px(12))
            tile.grid(row=0, column=i, padx=(0 if i == 0 else px(7), 0 if i == 2 else px(7)), sticky="nsew")
            if key == "about":
                img = Image.open(resource_path("assets", "icon.png")).resize((px(46), px(46)), Image.LANCZOS)
            else:
                img = render_reference_art(key, 46, scale=scale())
            photo = ImageTk.PhotoImage(img)
            self._ref_images.append(photo)
            tk.Label(tile, image=photo, bg=COLORS["card"]).pack(side="left")
            text = tk.Frame(tile, bg=COLORS["card"])
            text.pack(side="left", padx=(px(12), 0))
            ttk.Label(text, text=title, style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(text, text=desc, style="Muted.TLabel").pack(anchor="w")
            tk.Label(tile, text="→", bg=COLORS["card"], fg=COLORS["text_subtle"],
                     font=(FONT_SEMI, 13)).pack(side="right")
            tile.finish()
            ref.columnconfigure(i, weight=1, uniform="ref")


# ---------------------------------------------------------------------------
# Calculator pages: inputs on the left, live diagram + results on the right
# ---------------------------------------------------------------------------
class CalculatorPage(ttk.Frame):
    title = "Shape"
    subtitle = ""
    kind = ""
    fields = []  # (symbol, label) -- symbols double as diagram dimension keys
    length_label = "Length"
    stat_names = ("Cross-section area", "Weight per metre", "Weight in pounds")
    formula = ()

    def __init__(self, parent, controller):
        super().__init__(parent, style="App.TFrame", padding=_page_padding())
        self.controller = controller
        page_header(self, self.title, self.subtitle, eyebrow="Calculator").pack(fill="x", pady=(0, px(16)))

        body = ttk.Frame(self, style="App.TFrame")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)

        self.inputs = Card(body, padding=22)
        self.inputs.grid(row=0, column=0, sticky="new", padx=(0, px(18)))

        right = ttk.Frame(body, style="App.TFrame")
        right.grid(row=0, column=1, sticky="n")
        diagram_card = Card(right, padding=16)
        diagram_card.pack(fill="x")
        card_heading(diagram_card, "Shape Diagram", "dimensions in mm").pack(fill="x", pady=(0, px(6)))
        self.diagram = AsyncImage(
            diagram_card, lambda **kw: render_section(self.kind, bg=CARD_RGB, detailed=True, **kw),
            DIAGRAM_SIZE[0], DIAGRAM_SIZE[1], COLORS["card"],
        )
        self.diagram.pack()
        self.result = ResultPanel(right)
        self.result.pack(fill="x", pady=(px(14), 0))
        self.right = right

        card_heading(self.inputs, "Dimensions", "all values in millimetres").pack(fill="x", pady=(0, px(14)))
        self.build_selector(self.inputs)

        grid = tk.Frame(self.inputs, bg=COLORS["card"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="f")
        grid.columnconfigure(1, weight=1, uniform="f")
        self.f = {}
        specs = list(self.fields) + [("L", self.length_label)]
        for i, (sym, label) in enumerate(specs):
            r, c = divmod(i, 2)
            w = LabeledEntry(grid, label, "mm", symbol=sym)
            w.grid(row=r, column=c, sticky="ew", padx=(0 if c == 0 else px(8), px(8) if c == 0 else 0),
                   pady=(0, px(14)))
            self.f[sym] = w
        self.f["L"].set("1000")

        divider(self.inputs).pack(fill="x", pady=(px(2), px(14)))
        self.material = MaterialPicker(self.inputs, SPECIFIC_GRAVITY, DEFAULT_MATERIAL)
        self.material.pack(fill="x", pady=(0, px(18)))

        buttons = tk.Frame(self.inputs, bg=COLORS["card"])
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Calculate Weight", style="Accent.TButton",
                   command=self.on_calculate).pack(side="left")
        ttk.Button(buttons, text="Reset", style="Ghost.TButton",
                   command=self.on_reset).pack(side="left", padx=(px(10), 0))
        ttk.Label(buttons, text="Results update as you type", style="Muted.TLabel").pack(side="right")

        self.formula_strip = None
        if self.formula:
            strip = tk.Frame(self.right, bg=COLORS["accent_soft"], padx=px(16), pady=px(10))
            tk.Label(strip, text="FORMULA", bg=COLORS["accent_soft"], fg=COLORS["accent"],
                     font=(FONT_SEMI, 8)).pack(anchor="w")
            for line in self.formula:
                tk.Label(strip, text=line, bg=COLORS["accent_soft"], fg=COLORS["text"],
                         font=(FONT, 10)).pack(anchor="w")
            self.formula_strip = strip
            self._show_formula(True)
            self.bind("<Configure>", lambda e: self.after_idle(self._fit_formula), add="+")

        for w in self.f.values():
            w.var.trace_add("write", self._changed)
        self.material.sg_var.trace_add("write", self._changed)
        self._live_job = None
        self.after_init()
        self.refresh_live()

    # -- hooks for subclasses ----------------------------------------------
    def build_selector(self, parent):
        pass

    def after_init(self):
        pass

    def compute(self):
        """Return (weight_kg, [(stat name, formatted value), ...])."""
        raise NotImplementedError

    def on_reset(self):
        for sym, w in self.f.items():
            w.set("1000" if sym == "L" else "")
        self.material.reset(DEFAULT_MATERIAL)

    # -- shared behaviour --------------------------------------------------
    def _show_formula(self, show):
        if show:
            self.formula_strip.pack(fill="x", pady=(px(14), 0))
        else:
            self.formula_strip.pack_forget()

    def _fit_formula(self, _event=None):
        """Hide the formula strip on short windows so the buttons stay visible."""
        strip = self.formula_strip
        shown = strip.winfo_manager() == "pack"
        need = self.winfo_reqheight()
        have = self.winfo_height()
        if shown and need > have:
            self._show_formula(False)
        elif not shown:
            # The strip only adds height if it makes the right column the taller one.
            right = self.right.winfo_reqheight()
            extra = max(0, right + strip.winfo_reqheight() + px(14) - max(right, self.inputs.winfo_reqheight()))
            if need + extra <= have:
                self._show_formula(True)

    def section_stats(self, area_mm2, weight_kg, sg):
        return [
            ("Cross-section area", f"{area_mm2:,.2f} mm²"),
            ("Weight per metre", f"{area_mm2 * sg / 1000:,.3f} kg/m"),
            ("Weight in pounds", f"{weight_kg * LB_PER_KG:,.2f} lb"),
        ]

    def _changed(self, *_):
        if self._live_job is not None:
            self.after_cancel(self._live_job)
        self._live_job = self.after(40, self.refresh_live)

    def refresh_live(self):
        self._live_job = None
        values = {sym: w.peek() for sym, w in self.f.items() if sym != "L"}
        self.diagram.request(delay_ms=90, values=values, length=self.f["L"].peek())
        if any(not w.var.get().strip() for w in self.f.values()) or not self.material.sg_var.get().strip():
            self.result.clear(self.stat_names)
            return
        self.on_calculate()

    def on_calculate(self):
        try:
            weight, stats = self.compute()
            self.result.show(weight, stats)
        except ValueError as exc:
            self.result.show_error(str(exc))
        except ZeroDivisionError:
            self.result.show_error("Please check the values entered.")


class RoundBarPage(CalculatorPage):
    title = "Solid Shaft / Round Bar"
    subtitle = "Weight of a solid round bar from its diameter and length."
    kind = "round_bar"
    fields = [("D", "Diameter")]
    formula = ("Area = π/4 × D²", "Weight (kg) = Area × L × SG × 10⁻⁶")

    def compute(self):
        d = self.f["D"].get_float("diameter")
        l = self.f["L"].get_float("length")
        sg = self.material.get_sg()
        _require_positive(diameter=d, length=l)
        area = calc.round_bar_area(d)
        weight = calc.round_bar_weight(d, l, sg)
        return weight, self.section_stats(area, weight, sg)


class PipePage(CalculatorPage):
    title = "Hollow Shaft / Pipe"
    subtitle = "Weight of a hollow shaft, tube or pipe from its outer and inner diameters."
    kind = "pipe"
    fields = [("OD", "External Diameter"), ("ID", "Internal Diameter")]
    formula = ("Area = π/4 × (OD² − ID²)", "Weight (kg) = Area × L × SG × 10⁻⁶")

    def compute(self):
        od = self.f["OD"].get_float("external diameter")
        idm = self.f["ID"].get_float("internal diameter")
        l = self.f["L"].get_float("length")
        sg = self.material.get_sg()
        _require_positive(external_diameter=od, length=l)
        if idm < 0 or idm >= od:
            raise ValueError("Internal diameter must be smaller than the external diameter.")
        area = calc.pipe_area(od, idm)
        weight = calc.pipe_weight(od, idm, l, sg)
        return weight, self.section_stats(area, weight, sg)


class BoxSectionPage(CalculatorPage):
    title = "Box Section"
    subtitle = "Rectangular or square hollow section (RHS / SHS)."
    kind = "box"
    fields = [("A", "Section Length"), ("B", "Section Width"), ("t", "Wall Thickness")]
    length_label = "Total Length"
    formula = ("Area = A × B − (A − 2t) × (B − 2t)", "Weight (kg) = Area × L × SG × 10⁻⁶")

    def compute(self):
        a = self.f["A"].get_float("section length")
        b = self.f["B"].get_float("section width")
        t = self.f["t"].get_float("thickness")
        l = self.f["L"].get_float("total length")
        sg = self.material.get_sg()
        _require_positive(section_length=a, section_width=b, thickness=t, total_length=l)
        if 2 * t >= min(a, b):
            raise ValueError("Wall thickness is too large for the section size.")
        area = calc.box_section_area(a, b, t)
        weight = calc.box_section_weight(a, b, t, l, sg)
        return weight, self.section_stats(area, weight, sg)


class PlatePage(CalculatorPage):
    title = "Plate"
    subtitle = "Flat plate or sheet from its length, width and thickness."
    kind = "plate"
    fields = [("W", "Width"), ("T", "Thickness")]
    stat_names = ("Plate area", "Weight per m²", "Weight in pounds")
    formula = ("Weight (kg) = L × W × T × SG × 10⁻⁶",)

    def compute(self):
        w = self.f["W"].get_float("width")
        t = self.f["T"].get_float("thickness")
        l = self.f["L"].get_float("length")
        sg = self.material.get_sg()
        _require_positive(width=w, thickness=t, length=l)
        weight = calc.plate_weight(l, w, t, sg)
        return weight, [
            ("Plate area", f"{l * w / 1e6:,.4f} m²"),
            ("Weight per m²", f"{t * sg:,.3f} kg/m²"),
            ("Weight in pounds", f"{weight * LB_PER_KG:,.2f} lb"),
        ]


class StructuralSectionPage(CalculatorPage):
    """Pick a Standard IS designation (auto-fills dimensions) or enter a
    custom section -- same formula either way."""

    section_table = {}
    designation_label = "Designation"

    def build_selector(self, parent):
        self.mode = tk.StringVar(value="standard")
        row = tk.Frame(parent, bg=COLORS["card"])
        row.pack(fill="x", pady=(0, px(14)))
        self.mode_toggle = Segmented(row, [("standard", "Standard IS Section"), ("custom", "Custom Section")],
                                     self.mode, self.refresh_mode)
        self.mode_toggle.pack(side="left")
        self.build_extra_toggle(row)

        self.designation_var = tk.StringVar()
        self.designation = LabeledCombo(parent, self.designation_label, [], self.designation_var)
        self.designation.pack(fill="x", pady=(0, px(14)))
        self.designation.combo.bind("<<ComboboxSelected>>", lambda e: self.load_designation())

    def build_extra_toggle(self, row):
        pass

    def current_table(self):
        return self.section_table

    def after_init(self):
        self.reload_designations()
        self.refresh_mode()

    def reload_designations(self):
        names = list(self.current_table().keys())
        self.designation.combo.configure(values=names)
        if names:
            self.designation.combo.current(0)

    def refresh_mode(self):
        standard = self.mode.get() == "standard"
        self.designation.combo.configure(state="readonly" if standard else "disabled")
        for sym, w in self.f.items():
            if sym != "L":
                w.set_enabled(not standard)
        if standard:
            self.load_designation()

    def load_designation(self):
        dims = self.current_table().get(self.designation_var.get())
        if dims:
            for (sym, _), value in zip(self.fields, dims):
                self.f[sym].set(value)

    def on_reset(self):
        self.f["L"].set("1000")
        self.material.reset(DEFAULT_MATERIAL)
        self.mode.set("standard")
        self.mode_toggle.refresh()
        self.reload_designations()
        self.refresh_mode()

    def i_section_values(self):
        h = self.f["H"].get_float("section height")
        b = self.f["B"].get_float("flange width")
        tw = self.f["tw"].get_float("web thickness")
        tf = self.f["tf"].get_float("flange thickness")
        l = self.f["L"].get_float("length")
        sg = self.material.get_sg()
        _require_positive(section_height=h, flange_width=b, web_thickness=tw,
                          flange_thickness=tf, length=l)
        if tw >= b:
            raise ValueError("Web thickness must be smaller than the flange width.")
        return h, b, tw, tf, l, sg


class BeamPage(StructuralSectionPage):
    title = "Beam Section"
    subtitle = "IS beams (ISJB / ISLB / ISMB / ISWB / ISHB / Provisional) or a custom I-section."
    kind = "beam"
    fields = [("H", "Section Height"), ("B", "Flange Width"),
              ("tw", "Web Thickness"), ("tf", "Flange Thickness")]
    section_table = BEAM_SECTIONS
    formula = ("Area = 2 × B × tf + (H − 2tf) × tw", "Weight (kg) = Area × L × SG × 10⁻⁶")

    def compute(self):
        h, b, tw, tf, l, sg = self.i_section_values()
        if 2 * tf >= h:
            raise ValueError("Two flange thicknesses must be less than the section height.")
        area = calc.beam_channel_area(h, b, tw, tf)
        weight = calc.beam_channel_weight(h, b, tw, tf, l, sg)
        return weight, self.section_stats(area, weight, sg)


class ChannelPage(BeamPage):
    title = "Channel Section"
    subtitle = "IS channels (ISJC / ISLC / ISMC / ISCG) or a custom channel."
    kind = "channel"
    section_table = CHANNEL_SECTIONS


class AnglePage(StructuralSectionPage):
    title = "Angle Section"
    subtitle = "IS equal and unequal angles, or a custom angle."
    kind = "angle"
    fields = [("A", "Leg A"), ("B", "Leg B"), ("t", "Thickness")]
    formula = ("Area = t × (A + B − t)", "Weight (kg) = Area × L × SG × 10⁻⁶")

    def build_extra_toggle(self, row):
        self.angle_type = tk.StringVar(value="equal")
        self.type_toggle = Segmented(row, [("equal", "Equal"), ("unequal", "Unequal")],
                                     self.angle_type, self.on_type_change)
        self.type_toggle.pack(side="right")

    def current_table(self):
        return EQUAL_ANGLE_SECTIONS if self.angle_type.get() == "equal" else UNEQUAL_ANGLE_SECTIONS

    def on_type_change(self):
        self.reload_designations()
        if self.mode.get() == "standard":
            self.load_designation()

    def on_reset(self):
        self.angle_type.set("equal")
        self.type_toggle.refresh()
        super().on_reset()

    def compute(self):
        a = self.f["A"].get_float("leg A")
        b = self.f["B"].get_float("leg B")
        t = self.f["t"].get_float("thickness")
        l = self.f["L"].get_float("length")
        sg = self.material.get_sg()
        _require_positive(leg_a=a, leg_b=b, thickness=t, length=l)
        if t >= min(a, b):
            raise ValueError("Thickness must be smaller than both legs.")
        area = calc.angle_area(a, b, t)
        weight = calc.angle_weight(a, b, t, l, sg)
        return weight, self.section_stats(area, weight, sg)


class TeePage(StructuralSectionPage):
    title = "Tee Section"
    subtitle = "IS tee bars (ISNT / ISDT / ISLT / ISMT) or a custom tee."
    kind = "tee"
    fields = [("H", "Section Height"), ("B", "Flange Width"),
              ("tw", "Web Thickness"), ("tf", "Flange Thickness")]
    section_table = TEE_SECTIONS
    formula = ("Area = B × tf + (H − tf) × tw", "Weight (kg) = Area × L × SG × 10⁻⁶")

    def compute(self):
        h, b, tw, tf, l, sg = self.i_section_values()
        if tf >= h:
            raise ValueError("Flange thickness must be less than the section height.")
        area = calc.tee_area(h, b, tw, tf)
        weight = calc.tee_weight(h, b, tw, tf, l, sg)
        return weight, self.section_stats(area, weight, sg)


# ---------------------------------------------------------------------------
# Reference pages
# ---------------------------------------------------------------------------
class SpecificGravityPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="App.TFrame", padding=_page_padding())
        page_header(self, "Specific Gravity", "Reference densities used by the material picker.",
                    eyebrow="Reference").pack(fill="x", pady=(0, px(16)))

        body = ttk.Frame(self, style="App.TFrame")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        table_card = Card(body, padding=0)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, px(18)))
        cols = ("material", "sg", "density")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=len(SPECIFIC_GRAVITY))
        for col, text, width, anchor in (("material", "MATERIAL", 220, "w"),
                                         ("sg", "SPECIFIC GRAVITY", 140, "e"),
                                         ("density", "DENSITY (kg/m³)", 140, "e")):
            tree.heading(col, text=text, anchor=anchor)
            tree.column(col, width=px(width), anchor=anchor, stretch=True)
        tree.tag_configure("odd", background=COLORS["card_alt"])
        for i, (name, sg) in enumerate(SPECIFIC_GRAVITY.items()):
            tree.insert("", "end", values=(f"   {name}", f"{sg:.2f}   ", f"{sg * 1000:,.0f}   "),
                        tags=("odd",) if i % 2 else ())
        tree.pack(fill="both", expand=True, padx=1, pady=1)

        info = Card(body, padding=22)
        info.grid(row=0, column=1, sticky="nsew")
        ttk.Label(info, text="How weight is calculated", style="CardTitle.TLabel").pack(anchor="w")
        formula = tk.Frame(info, bg=COLORS["accent_soft"], padx=px(14), pady=px(12))
        formula.pack(fill="x", pady=(px(12), px(14)))
        tk.Label(formula, text="Weight (kg) =", bg=COLORS["accent_soft"], fg=COLORS["accent_hover"],
                 font=(FONT_SEMI, 10)).pack(anchor="w")
        tk.Label(formula, text="Area (mm²) × Length (mm) × SG × 10⁻⁶", bg=COLORS["accent_soft"],
                 fg=COLORS["text"], font=(FONT_SEMI, 11)).pack(anchor="w")
        notes = [
            "Specific gravity is the density in g/cm³ — for example steel is 7.85.",
            "You can type any specific gravity on a calculator page to use a material not listed here.",
            "Results are theoretical weights from nominal dimensions; actual weights vary with mill tolerances and root radii.",
        ]
        for note in notes:
            row = tk.Frame(info, bg=COLORS["card"])
            row.pack(fill="x", pady=(0, px(8)))
            tk.Label(row, text="•", bg=COLORS["card"], fg=COLORS["amber"], font=(FONT_SEMI, 11)).pack(side="left", anchor="n")
            ttk.Label(row, text=note, style="Body.TLabel", wraplength=px(270), justify="left").pack(
                side="left", padx=(px(8), 0))


class _ConverterCard(Card):
    def __init__(self, parent, title, units, convert, from_unit, to_unit):
        super().__init__(parent, padding=22)
        self.convert = convert
        ttk.Label(self, text=title, style="CardTitle.TLabel").pack(anchor="w", pady=(0, px(12)))
        self.value = LabeledEntry(self, "Value", default="1")
        self.value.pack(fill="x", pady=(0, px(12)))

        row = tk.Frame(self, bg=COLORS["card"])
        row.pack(fill="x")
        row.columnconfigure(0, weight=1)
        row.columnconfigure(2, weight=1)
        self.from_var = tk.StringVar(value=from_unit)
        self.to_var = tk.StringVar(value=to_unit)
        fc = LabeledCombo(row, "From", units, self.from_var, width=10)
        fc.grid(row=0, column=0, sticky="ew")
        ttk.Button(row, text="⇄", style="Ghost.TButton", width=3, command=self.swap).grid(
            row=0, column=1, sticky="s", padx=px(10))
        tc = LabeledCombo(row, "To", units, self.to_var, width=10)
        tc.grid(row=0, column=2, sticky="ew")

        out = tk.Frame(self, bg=COLORS["card_alt"], padx=px(16), pady=px(12),
                       highlightthickness=1, highlightbackground=COLORS["border"])
        out.pack(fill="x", pady=(px(16), 0))
        tk.Label(out, text="RESULT", bg=COLORS["card_alt"], fg=COLORS["text_muted"],
                 font=(FONT_SEMI, 8)).pack(anchor="w")
        self.result = tk.Label(out, text="", bg=COLORS["card_alt"], fg=COLORS["accent_hover"],
                               font=(FONT_SEMI, 16), anchor="w")
        self.result.pack(fill="x")

        for var in (self.value.var, self.from_var, self.to_var):
            var.trace_add("write", lambda *_: self.update_result())
        self.update_result()

    def swap(self):
        a, b = self.from_var.get(), self.to_var.get()
        self.from_var.set(b)
        self.to_var.set(a)

    def update_result(self):
        try:
            v = self.value.get_float("value")
            result = self.convert(v, self.from_var.get(), self.to_var.get())
            self.result.configure(text=f"{v:g} {self.from_var.get()} = {result:,.6g} {self.to_var.get()}",
                                  fg=COLORS["accent_hover"])
        except (ValueError, KeyError) as exc:
            self.result.configure(text=str(exc), fg=COLORS["error"])


class UnitConverterPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="App.TFrame", padding=_page_padding())
        page_header(self, "Unit Converter", "Length and weight conversions — results update as you type.",
                    eyebrow="Reference").pack(fill="x", pady=(0, px(16)))

        body = ttk.Frame(self, style="App.TFrame")
        body.pack(fill="x")
        body.columnconfigure(0, weight=1, uniform="c")
        body.columnconfigure(1, weight=1, uniform="c")
        _ConverterCard(body, "Length", calc.LENGTH_UNITS_TO_MM.keys(), calc.convert_length,
                       "m", "mm").grid(row=0, column=0, sticky="nsew", padx=(0, px(9)))
        _ConverterCard(body, "Weight", calc.WEIGHT_UNITS_TO_KG.keys(), calc.convert_weight,
                       "kg", "lb").grid(row=0, column=1, sticky="nsew", padx=(px(9), 0))

        facts = Card(self, padding=22)
        facts.pack(fill="x", pady=(px(18), 0))
        ttk.Label(facts, text="Handy reference", style="CardTitle.TLabel").pack(anchor="w", pady=(0, px(10)))
        row = tk.Frame(facts, bg=COLORS["card"])
        row.pack(fill="x")
        for i, fact in enumerate(UNIT_FACTS):
            chip = tk.Frame(row, bg=COLORS["amber_soft"], padx=px(14), pady=px(10))
            chip.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else px(10), 0))
            row.columnconfigure(i, weight=1, uniform="f")
            tk.Label(chip, text=fact, bg=COLORS["amber_soft"], fg=COLORS["amber_dark"],
                     font=(FONT_SEMI, 10)).pack(anchor="w")


class AboutPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="App.TFrame", padding=_page_padding())
        page_header(self, "About", eyebrow=app_info.APP_NAME).pack(fill="x", pady=(0, px(16)))

        card = Card(self, padding=30)
        card.pack(fill="x")

        top = tk.Frame(card, bg=COLORS["card"])
        top.pack(fill="x")
        logo = Image.open(resource_path("assets", "icon.png")).resize((px(96), px(96)), Image.LANCZOS)
        self._logo = ImageTk.PhotoImage(logo)
        tk.Label(top, image=self._logo, bg=COLORS["card"]).pack(side="left")
        title = tk.Frame(top, bg=COLORS["card"])
        title.pack(side="left", padx=(px(20), 0))
        tk.Label(title, text=app_info.APP_NAME, bg=COLORS["card"], fg=COLORS["text"],
                 font=(FONT_SEMI, 22)).pack(anchor="w")
        badge = tk.Label(title, text=f"Version {app_info.VERSION}", bg=COLORS["accent_soft"],
                         fg=COLORS["accent"], font=(FONT_SEMI, 9), padx=px(10), pady=px(3))
        badge.pack(anchor="w", pady=(px(4), 0))
        ttk.Label(card, text=(
            "Calculates the theoretical weight of solid and hollow shafts, box sections, plates and "
            "Indian Standard structural steel sections — beams, channels, angles and tees — for any "
            "material, from its dimensions and specific gravity."),
            style="Body.TLabel", wraplength=px(640), justify="left").pack(anchor="w", pady=(px(20), px(18)))

        divider(card).pack(fill="x", pady=(0, px(14)))
        info = tk.Frame(card, bg=COLORS["card"])
        info.pack(fill="x")
        rows = [
            ("Version", app_info.VERSION),
            ("Author", app_info.AUTHOR),
            ("Company", app_info.COMPANY),
            ("Copyright", app_info.COPYRIGHT),
        ]
        for r, (k, v) in enumerate(rows):
            tk.Label(info, text=k, bg=COLORS["card"], fg=COLORS["text_muted"], font=(FONT, 10),
                     anchor="w").grid(row=r, column=0, sticky="w", pady=px(5))
            tk.Label(info, text=v, bg=COLORS["card"], fg=COLORS["text"], font=(FONT_SEMI, 10),
                     anchor="w").grid(row=r, column=1, sticky="w", padx=(px(40), 0), pady=px(5))

        note = tk.Frame(self, bg=COLORS["amber_soft"], padx=px(18), pady=px(12))
        note.pack(fill="x", pady=(px(16), 0))
        tk.Label(note, text=(
            "Weights shown are theoretical values based on nominal dimensions. Actual weights may vary "
            "with manufacturing tolerances, root radii and material grade."),
            bg=COLORS["amber_soft"], fg=COLORS["amber_dark"], font=(FONT, 9),
            wraplength=px(760), justify="left").pack(anchor="w")
