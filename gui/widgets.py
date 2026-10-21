"""Reusable UI building blocks used across pages."""

import os
import sys
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import ttk

from PIL import ImageTk

from .theme import COLORS, FONT, FONT_SEMI, px, scale

# Diagram rendering runs off the UI thread so typing never stutters.
_RENDERER = ThreadPoolExecutor(max_workers=1)


def resource_path(*parts) -> str:
    """Path to a bundled resource, both from source and inside a PyInstaller exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *parts)


def bind_tree(widget, sequence, func):
    """Bind *func* on a widget and all of its descendants."""
    widget.bind(sequence, func, add="+")
    for child in widget.winfo_children():
        bind_tree(child, sequence, func)


class Card(tk.Frame):
    """White panel with a hairline border."""

    def __init__(self, parent, padding=20, **kwargs):
        super().__init__(
            parent, bg=COLORS["card"], highlightthickness=1,
            highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
            padx=px(padding), pady=px(padding), **kwargs,
        )


def page_header(parent, title: str, subtitle: str = "", eyebrow: str = "") -> ttk.Frame:
    header = ttk.Frame(parent, style="App.TFrame")
    if eyebrow:
        ttk.Label(header, text=eyebrow.upper(), style="Eyebrow.TLabel").pack(anchor="w")
    ttk.Label(header, text=title, style="Title.TLabel").pack(anchor="w")
    if subtitle:
        ttk.Label(header, text=subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(px(2), 0))
    return header


def divider(parent) -> tk.Frame:
    return tk.Frame(parent, bg=COLORS["border"], height=1)


def card_heading(parent, title: str, subtitle: str = "") -> tk.Frame:
    frame = tk.Frame(parent, bg=COLORS["card"])
    ttk.Label(frame, text=title, style="CardTitle.TLabel").pack(side="left")
    if subtitle:
        ttk.Label(frame, text=subtitle, style="CardSub.TLabel").pack(side="right")
    return frame


class LabeledEntry(tk.Frame):
    """Field label (with an optional symbol badge) above an input group
    that has an optional unit suffix."""

    def __init__(self, parent, label: str, unit: str = "", default: str = "",
                 symbol: str = "", width: int = 10):
        super().__init__(parent, bg=COLORS["card"])
        top = tk.Frame(self, bg=COLORS["card"])
        top.pack(fill="x")
        ttk.Label(top, text=label, style="Field.TLabel").pack(side="left")
        if symbol:
            tk.Label(top, text=symbol, bg=COLORS["accent_soft"], fg=COLORS["accent"],
                     font=(FONT_SEMI, 8), padx=px(6), pady=0).pack(side="right")

        self.box = tk.Frame(self, bg=COLORS["border_strong"], padx=1, pady=1)
        self.box.pack(fill="x", pady=(px(5), 0))
        self.var = tk.StringVar(value=default)
        self.inner = tk.Frame(self.box, bg=COLORS["card"], padx=px(10))
        self.inner.pack(side="left", fill="both", expand=True)
        self.entry = tk.Entry(
            self.inner, textvariable=self.var, width=width, relief="flat", bd=0,
            font=(FONT, 11), bg=COLORS["card"], fg=COLORS["text"],
            insertbackground=COLORS["text"], highlightthickness=0,
            readonlybackground=COLORS["disabled_bg"], disabledbackground=COLORS["disabled_bg"],
            selectbackground=COLORS["accent_soft"], selectforeground=COLORS["text"],
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=px(6))
        self.unit_label = None
        if unit:
            self.unit_label = tk.Label(self.box, text=unit, bg=COLORS["card_alt"],
                                       fg=COLORS["text_muted"], font=(FONT, 9), padx=px(10))
            self.unit_label.pack(side="right", fill="y")
        self.entry.bind("<FocusIn>", lambda e: self.box.configure(bg=COLORS["accent"]))
        self.entry.bind("<FocusOut>", lambda e: self.box.configure(bg=COLORS["border_strong"]))
        self._enabled = True

    def get_float(self, field_name: str = "value") -> float:
        raw = self.var.get().strip().replace(",", "")
        if not raw:
            raise ValueError(f"Please enter a value for {field_name}.")
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"'{raw}' is not a valid number for {field_name}.")

    def peek(self):
        """The current numeric value, or None if blank/invalid."""
        try:
            return float(self.var.get().strip().replace(",", ""))
        except ValueError:
            return None

    def set(self, value) -> None:
        self.var.set("" if value is None else ("%g" % value if isinstance(value, float) else str(value)))

    def set_enabled(self, enabled: bool) -> None:
        """Editable, or read-only (still selectable) when values come from a table."""
        self._enabled = enabled
        self.entry.configure(state="normal" if enabled else "readonly", fg=COLORS["text"])
        self.inner.configure(bg=COLORS["card"] if enabled else COLORS["disabled_bg"])
        if self.unit_label is not None:
            self.unit_label.configure(bg=COLORS["card_alt"] if enabled else COLORS["disabled_bg"])


class LabeledCombo(tk.Frame):
    def __init__(self, parent, label: str, values, variable, width=22, symbol=""):
        super().__init__(parent, bg=COLORS["card"])
        top = tk.Frame(self, bg=COLORS["card"])
        top.pack(fill="x")
        ttk.Label(top, text=label, style="Field.TLabel").pack(side="left")
        if symbol:
            tk.Label(top, text=symbol, bg=COLORS["accent_soft"], fg=COLORS["accent"],
                     font=(FONT_SEMI, 8), padx=px(6)).pack(side="right")
        self.combo = ttk.Combobox(self, textvariable=variable, values=list(values),
                                  state="readonly", width=width, font=(FONT, 10))
        self.combo.pack(fill="x", pady=(px(5), 0))


class MaterialPicker(tk.Frame):
    """Material dropdown plus an editable specific-gravity field, side by side."""

    def __init__(self, parent, materials: dict, default_material: str):
        super().__init__(parent, bg=COLORS["card"])
        self.materials = materials
        self.combo_var = tk.StringVar(value=default_material)
        combo = LabeledCombo(self, "Material", materials.keys(), self.combo_var)
        combo.grid(row=0, column=0, sticky="ew", padx=(0, px(8)))
        combo.combo.bind("<<ComboboxSelected>>", self._on_material_change)
        self.sg = LabeledEntry(self, "Specific Gravity", "g/cm³", str(materials[default_material]), symbol="SG")
        self.sg.grid(row=0, column=1, sticky="ew", padx=(px(8), 0))
        self.sg_var = self.sg.var
        self.columnconfigure(0, weight=1, uniform="m")
        self.columnconfigure(1, weight=1, uniform="m")

    def _on_material_change(self, _event=None):
        material = self.combo_var.get()
        if material in self.materials:
            self.sg_var.set(str(self.materials[material]))

    def reset(self, default_material: str):
        self.combo_var.set(default_material)
        self._on_material_change()

    def get_sg(self) -> float:
        raw = self.sg_var.get().strip()
        if not raw:
            raise ValueError("Please choose a material or enter a specific gravity.")
        try:
            sg = float(raw)
        except ValueError:
            raise ValueError(f"'{raw}' is not a valid specific gravity value.")
        if sg <= 0:
            raise ValueError("Specific gravity must be greater than zero.")
        return sg


class Segmented(tk.Frame):
    """A compact segmented toggle bound to a StringVar."""

    def __init__(self, parent, options, variable: tk.StringVar, command=None):
        super().__init__(parent, bg=COLORS["border_strong"], padx=1, pady=1)
        self.var = variable
        self.command = command
        self.buttons = {}
        for i, (value, text) in enumerate(options):
            b = tk.Label(self, text=text, font=(FONT_SEMI, 9), padx=px(14), pady=px(6),
                         cursor="hand2")
            b.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 1, 0))
            b.bind("<Button-1>", lambda e, v=value: self.select(v))
            b.bind("<Enter>", lambda e, v=value: self._hover(v, True))
            b.bind("<Leave>", lambda e, v=value: self._hover(v, False))
            self.buttons[value] = b
            self.columnconfigure(i, weight=1)
        self.refresh()

    def select(self, value):
        if self.var.get() != value:
            self.var.set(value)
            self.refresh()
            if self.command:
                self.command()

    def _hover(self, value, inside):
        if value != self.var.get():
            self.buttons[value].configure(bg=COLORS["card_alt"] if inside else COLORS["card"])

    def refresh(self):
        for value, b in self.buttons.items():
            on = value == self.var.get()
            b.configure(bg=COLORS["accent"] if on else COLORS["card"],
                        fg="white" if on else COLORS["text_muted"])


class ResultPanel(tk.Frame):
    """Dark summary panel: headline weight plus a row of secondary figures."""

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["result_bg"], padx=px(22), pady=px(16))
        c = COLORS
        tk.Label(self, text="ESTIMATED WEIGHT", bg=c["result_bg"], fg=c["result_muted"],
                 font=(FONT_SEMI, 9)).pack(anchor="w")
        row = tk.Frame(self, bg=c["result_bg"])
        row.pack(anchor="w", pady=(px(2), px(10)))
        self.weight = tk.Label(row, text="—", bg=c["result_bg"], fg=c["result_text"],
                               font=(FONT_SEMI, 26))
        self.weight.pack(side="left")
        self.unit = tk.Label(row, text="kg", bg=c["result_bg"], fg=c["amber"], font=(FONT_SEMI, 13))
        self.unit.pack(side="left", padx=(px(6), 0), pady=(px(12), 0))

        tk.Frame(self, bg=c["result_divider"], height=1).pack(fill="x")

        self.stats = tk.Frame(self, bg=c["result_bg"])
        self.stats.pack(fill="x", pady=(px(10), 0))
        self.stat_labels = []
        for i in range(3):
            cell = tk.Frame(self.stats, bg=c["result_bg"])
            cell.grid(row=0, column=i, sticky="w")
            self.stats.columnconfigure(i, weight=1, uniform="s")
            name = tk.Label(cell, text="", bg=c["result_bg"], fg=c["result_muted"], font=(FONT, 8))
            name.pack(anchor="w")
            value = tk.Label(cell, text="—", bg=c["result_bg"], fg=c["result_text"], font=(FONT_SEMI, 10))
            value.pack(anchor="w")
            self.stat_labels.append((name, value))

        self.message = tk.Label(self, text="", bg=c["result_bg"], fg=c["result_muted"],
                                font=(FONT, 9), anchor="w", justify="left")
        self.message.pack(fill="x", pady=(px(10), 0))

    def show(self, weight_kg: float, stats):
        self.weight.configure(text=f"{weight_kg:,.3f}")
        for (name, value), (n, v) in zip(self.stat_labels, stats):
            name.configure(text=n)
            value.configure(text=v)
        self.message.configure(text="✓  Calculated from the dimensions entered.", fg=COLORS["result_muted"])

    def clear(self, stat_names, message="Enter all dimensions to see the weight."):
        self.weight.configure(text="—")
        for (name, value), n in zip(self.stat_labels, stat_names):
            name.configure(text=n)
            value.configure(text="—")
        self.message.configure(text=message, fg=COLORS["result_muted"])

    def show_error(self, message: str):
        self.weight.configure(text="—")
        for _, value in self.stat_labels:
            value.configure(text="—")
        self.message.configure(text="⚠  " + message, fg="#FCA5A5")


class AsyncImage(tk.Label):
    """A label whose image is produced by *render(**kwargs)* on a worker thread.
    Only the most recent request is displayed; results are cached."""

    def __init__(self, parent, render, width, height, bg, **render_kwargs):
        # Blank placeholder keeps the layout stable until the first render lands.
        self._placeholder = tk.PhotoImage(width=px(width), height=px(height))
        super().__init__(parent, bg=bg, bd=0, image=self._placeholder)
        self._render = render
        self._kwargs = dict(render_kwargs, width=width, height=height, scale=scale())
        self._seq = 0
        self._job = None
        self._photo = None
        self._cache = {}

    def request(self, delay_ms=0, **kwargs):
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(delay_ms, lambda: self._start(kwargs))

    def _start(self, kwargs):
        self._job = None
        self._seq += 1
        seq = self._seq
        key = repr(sorted(kwargs.items()))
        if key in self._cache:
            self._show(self._cache[key])
            return
        future = _RENDERER.submit(self._render, **dict(self._kwargs, **kwargs))
        self._poll(future, seq, key)

    def _poll(self, future, seq, key):
        if not future.done():
            self.after(25, lambda: self._poll(future, seq, key))
            return
        try:
            image = future.result()
        except Exception:
            return
        if len(self._cache) > 64:
            self._cache.clear()
        self._cache[key] = image
        if seq == self._seq:
            self._show(image)

    def _show(self, image):
        self._photo = ImageTk.PhotoImage(image)
        self.configure(image=self._photo)


class NavItem(tk.Frame):
    """Sidebar navigation row with an accent indicator when active."""

    def __init__(self, parent, text, icon, icon_active, command):
        c = COLORS
        super().__init__(parent, bg=c["sidebar"], cursor="hand2")
        self.icon, self.icon_active = icon, icon_active
        self.active = False
        self.indicator = tk.Frame(self, bg=c["sidebar"], width=px(3))
        self.indicator.pack(side="left", fill="y")
        self.icon_label = tk.Label(self, image=icon, bg=c["sidebar"], bd=0)
        self.icon_label.pack(side="left", padx=(px(14), px(10)), pady=px(7))
        self.text = tk.Label(self, text=text, bg=c["sidebar"], fg=c["sidebar_text"],
                             font=(FONT, 10), anchor="w")
        self.text.pack(side="left", fill="x", expand=True)
        bind_tree(self, "<Button-1>", lambda e: command())
        bind_tree(self, "<Enter>", lambda e: self._paint(hover=True))
        bind_tree(self, "<Leave>", lambda e: self._paint(hover=False))

    def set_active(self, active: bool):
        self.active = active
        self._paint()

    def _paint(self, hover=False):
        c = COLORS
        bg = c["sidebar_active"] if self.active else (c["sidebar_hover"] if hover else c["sidebar"])
        for w in (self, self.icon_label, self.text):
            w.configure(bg=bg)
        self.indicator.configure(bg=c["amber"] if self.active else bg)
        self.icon_label.configure(image=self.icon_active if (self.active or hover) else self.icon)
        self.text.configure(fg=c["sidebar_text_active"] if (self.active or hover) else c["sidebar_text"],
                            font=(FONT_SEMI if self.active else FONT, 10))
