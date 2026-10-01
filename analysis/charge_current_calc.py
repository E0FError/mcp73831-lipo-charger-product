#!/usr/bin/env python3
"""
charge_current_calc.py
======================
Reproduces the charge-current programming analysis for the
**DTU LiPo Charger v1.0** (MCP73831-2ACI single-cell Li-Ion/LiPo charger).

The MCP73831 sets the fast-charge current with a resistor on the PROG pin:

    I_REG [mA] = 1000 V / R_PROG [kOhm]        (Microchip DS20001984)

The product exposes five E-series presets through a 6-position DIP switch,
plus a sixth position that connects a user-solderable PTH resistor.

The script prints the preset table and writes a figure to
``images/charge-current-vs-rprog.svg``.  Standard library only.
"""

from __future__ import annotations

import json
import os

# --------------------------------------------------------------------------
# Design inputs
# --------------------------------------------------------------------------
# E-series resistors fitted on the board (DIP positions 1-5).
PRESETS = [
    ("1", 10.0e3, 100),   # exact target
    ("2", 5.1e3, 200),
    ("3", 3.3e3, 300),
    ("4", 2.4e3, 400),
    ("5", 2.0e3, 500),
]

# The current is defined by I_REG = 1000 / R_PROG[kOhm].
K = 1000.0  # [V]  (1 V / 1 kOhm = 1 mA)


def ireg_ma(r_ohm: float) -> float:
    """Fast-charge current in mA for a PROG resistor in ohms."""
    return K / (r_ohm / 1e3)


def rprog_kohm(i_ma: float) -> float:
    """Ideal PROG resistor in kOhm for a target current in mA."""
    return K / i_ma


def preset_table() -> list[dict]:
    rows = []
    for pos, r, target in PRESETS:
        actual = ireg_ma(r)
        rows.append({
            "position": pos,
            "r_ohm": r,
            "r_label": f"{r/1e3:g} k\u03a9",
            "target_mA": target,
            "actual_mA": actual,
            "error_percent": (actual - target) / target * 100,
        })
    return rows


def custom_table() -> list[dict]:
    """Ideal and nearest E24 resistor for a few custom currents."""
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
           3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    rows = []
    for target in (50, 150, 250, 350, 450):
        ideal = rprog_kohm(target)
        candidates = []
        for mult in (1, 10, 100, 1000):
            candidates += [v * mult for v in e24]
        nearest = min(candidates, key=lambda v: abs(v - ideal))
        rows.append({
            "target_mA": target,
            "ideal_kohm": ideal,
            "e24_kohm": nearest,
            "actual_mA": ireg_ma(nearest * 1e3),
        })
    return rows


# --------------------------------------------------------------------------
# Minimal dependency-free SVG plotting (same helper as the buck-converter repo)
# --------------------------------------------------------------------------


class SvgPlot:
    def __init__(self, width, height, pad):
        self.w, self.h, self.pad = width, height, pad
        self.parts = []

    def set_range(self, x0, x1, y0, y1):
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1

    @property
    def pw(self): return self.w - self.pad["l"] - self.pad["r"]

    @property
    def ph(self): return self.h - self.pad["t"] - self.pad["b"]

    def sx(self, x): return self.pad["l"] + (x - self.x0) / (self.x1 - self.x0) * self.pw

    def sy(self, y): return self.pad["t"] + (self.y1 - y) / (self.y1 - self.y0) * self.ph

    def add(self, s): self.parts.append(s)

    def rect(self, x, y, w, h, fill, opacity=1.0):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'fill="{fill}" opacity="{opacity}"/>')

    def line(self, x1, y1, x2, y2, stroke, width=1.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{width}"{d}/>')

    def text(self, x, y, s, size=14, anchor="start", fill="#1a1a1a",
             weight="normal", rotate=None):
        t = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate else ""
        lines = s.split("\n")
        spans = f'<tspan x="{x:.1f}">{lines[0]}</tspan>'
        for extra in lines[1:]:
            spans += f'<tspan x="{x:.1f}" dy="{size + 3}">{extra}</tspan>'
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica,Arial,sans-serif" '
                 f'font-size="{size}" text-anchor="{anchor}" fill="{fill}" '
                 f'font-weight="{weight}"{t}>{spans}</text>')

    def polyline(self, pts, stroke, width=2.5, fill="none"):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{width}"/>')

    def marker(self, x, y, color, r=6):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" '
                 f'stroke="white" stroke-width="1.6"/>')

    def save(self, path):
        body = "\n".join(self.parts)
        open(path, "w").write(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
            f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">\n{body}\n</svg>\n')


BLUE = "#1f5fbf"
ACCENT = "#c0392b"
GREEN = "#2e8b57"


def plot_curve(out: str) -> None:
    p = SvgPlot(1280, 720, {"l": 100, "r": 90, "t": 110, "b": 90})
    p.set_range(1.0, 11.0, 0, 600)
    p.rect(0, 0, p.w, p.h, "#ffffff")
    p.text(p.w / 2, 44, "MCP73831 charge current vs. PROG resistor",
           size=23, anchor="middle", weight="bold")
    p.text(p.w / 2, 70, "I_REG = 1000 V / R_PROG   (R in k\u03a9, I in mA)",
           size=14, anchor="middle", fill="#555555")
    for xv in [2, 3, 4, 5, 6, 7, 8, 9, 10]:
        px = p.sx(xv)
        p.line(px, p.pad["t"], px, p.h - p.pad["b"], "#e8e8e8", 1)
        p.text(px, p.h - p.pad["b"] + 24, str(xv), size=13, anchor="middle")
    for yv in range(0, 601, 100):
        py = p.sy(yv)
        p.line(p.pad["l"], py, p.w - p.pad["r"], py, "#e8e8e8", 1)
        p.text(p.pad["l"] - 12, py + 5, str(yv), size=13, anchor="end")
    p.line(p.pad["l"], p.pad["t"], p.pad["l"], p.h - p.pad["b"], "#555555", 1.6)
    p.line(p.pad["l"], p.h - p.pad["b"], p.w - p.pad["r"], p.h - p.pad["b"],
           "#555555", 1.6)
    p.text(p.w / 2, p.h - 14, "Programming resistor  R_PROG  [k\u03a9]", size=15,
           anchor="middle", weight="bold")
    p.text(20, p.h / 2, "Charge current  I_REG  [mA]", size=15, anchor="middle",
           weight="bold", rotate=-90)

    # curve over the useful 1-11 kOhm span
    curve = [(p.sx(r / 10), p.sy(ireg_ma(r * 100)))
             for r in range(10, 111)]
    p.polyline(curve, BLUE, 3)

    # preset markers with labels
    for pos, r, target in PRESETS:
        px, py = p.sx(r / 1e3), p.sy(ireg_ma(r))
        p.marker(px, py, ACCENT, 6)
        p.text(px + 10, py - 8, f"DIP {pos}\n{ireg_ma(r):.0f} mA",
               size=12, fill="#333333")

    p.text(p.sx(2.15), p.sy(88),
           "DIP 6  \u2192  PTH resistor\n"
           "(user-soldered)\nR_PROG[k\u03a9] = 1000 / I_REG[mA]",
           size=14, fill=GREEN, weight="bold")
    p.save(out)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    img = os.path.join(root, "images")
    os.makedirs(img, exist_ok=True)

    rows = preset_table()
    print("=" * 62)
    print(" DTU LiPo Charger v1.0 - charge-current presets")
    print("=" * 62)
    print(f" {'DIP':4}{'R_PROG':>11}{'target':>10}{'actual':>10}{'error':>10}")
    print("-" * 62)
    for r in rows:
        print(f" {r['position']:4}{r['r_label']:>11}{r['target_mA']:>8} mA"
              f"{r['actual_mA']:>8.1f} mA{r['error_percent']:>+8.1f} %")
    print("-" * 62)
    print(" R9 (DIP 6): user-solderable PTH resistor, same formula")
    print("\n Custom examples:")
    print(f" {'target':>8}{'ideal kOhm':>13}{'E24 kOhm':>11}{'actual':>10}")
    for r in custom_table():
        print(f" {r['target_mA']:>6} mA{r['ideal_kohm']:>11.1f} k\u03a9"
              f"{r['e24_kohm']:>9} k\u03a9{r['actual_mA']:>7.1f} mA")
    print("=" * 62)

    data = {"presets": rows, "custom": custom_table(),
            "formula": "I_REG[mA] = 1000 / R_PROG[kOhm]"}
    with open(os.path.join(here, "design_summary.json"), "w") as fh:
        json.dump(data, fh, indent=2)

    plot_curve(os.path.join(img, "charge-current-vs-rprog.svg"))
    print(f"\nWrote figure to {img}")


if __name__ == "__main__":
    main()
