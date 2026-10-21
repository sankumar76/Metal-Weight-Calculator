"""
Weight calculation formulas.

All formulas follow the same underlying rule the original "Weight
Calculator" tool uses (and the same rule structural engineers use
generally):

    weight_kg = cross_section_area_mm2 * length_mm * specific_gravity_g_cm3 * 1e-6

This is exactly equivalent to:  weight(g) = volume(mm3) * density(g/cm3) / 1000
since 1 cm3 = 1000 mm3.

Sanity check against the well-known steel bar shortcut "d^2 / 162 = kg/m":
  round_bar_weight(d=100, length=1000, sg=7.85) == 61.65 kg  (100^2/162 = 61.7)
"""

import math


def round_bar_area(diameter_mm: float) -> float:
    """Cross-section area of a solid round bar (mm^2)."""
    return math.pi / 4.0 * diameter_mm ** 2


def round_bar_weight(diameter_mm: float, length_mm: float, sg: float) -> float:
    area = round_bar_area(diameter_mm)
    return area * length_mm * sg * 1e-6


def pipe_area(outer_diameter_mm: float, inner_diameter_mm: float) -> float:
    """Cross-section area of a hollow shaft / pipe (mm^2)."""
    return math.pi / 4.0 * (outer_diameter_mm ** 2 - inner_diameter_mm ** 2)


def pipe_weight(outer_diameter_mm: float, inner_diameter_mm: float,
                 length_mm: float, sg: float) -> float:
    area = pipe_area(outer_diameter_mm, inner_diameter_mm)
    return area * length_mm * sg * 1e-6


def box_section_area(outer_length_mm: float, outer_width_mm: float,
                      thickness_mm: float) -> float:
    """Cross-section area of a rectangular hollow (box) section (mm^2)."""
    inner_length = outer_length_mm - 2 * thickness_mm
    inner_width = outer_width_mm - 2 * thickness_mm
    inner_length = max(inner_length, 0.0)
    inner_width = max(inner_width, 0.0)
    return (outer_length_mm * outer_width_mm) - (inner_length * inner_width)


def box_section_weight(outer_length_mm: float, outer_width_mm: float,
                        thickness_mm: float, total_length_mm: float,
                        sg: float) -> float:
    area = box_section_area(outer_length_mm, outer_width_mm, thickness_mm)
    return area * total_length_mm * sg * 1e-6


def plate_weight(length_mm: float, width_mm: float, thickness_mm: float,
                  sg: float) -> float:
    volume_mm3 = length_mm * width_mm * thickness_mm
    return volume_mm3 * sg * 1e-6


def beam_channel_area(height_mm: float, width_mm: float,
                       web_thickness_mm: float, flange_thickness_mm: float) -> float:
    """
    Approximate cross-section area of an I-beam / channel section (mm^2),
    ignoring root fillet radii (the standard simplified approach used by
    this class of calculator):

        Area = 2 * (flange width * flange thickness) + (web height * web thickness)
    """
    web_height = height_mm - 2 * flange_thickness_mm
    web_height = max(web_height, 0.0)
    return 2 * (width_mm * flange_thickness_mm) + (web_height * web_thickness_mm)


def beam_channel_weight(height_mm: float, width_mm: float,
                         web_thickness_mm: float, flange_thickness_mm: float,
                         length_mm: float, sg: float) -> float:
    area = beam_channel_area(height_mm, width_mm, web_thickness_mm, flange_thickness_mm)
    return area * length_mm * sg * 1e-6


def angle_area(leg_a_mm: float, leg_b_mm: float, thickness_mm: float) -> float:
    """
    Approximate cross-section area of an angle section (mm^2), ignoring
    root fillet radius:

        Area = thickness * (leg_a + leg_b - thickness)
    """
    return thickness_mm * (leg_a_mm + leg_b_mm - thickness_mm)


def angle_weight(leg_a_mm: float, leg_b_mm: float, thickness_mm: float,
                  length_mm: float, sg: float) -> float:
    area = angle_area(leg_a_mm, leg_b_mm, thickness_mm)
    return area * length_mm * sg * 1e-6


def tee_area(height_mm: float, width_mm: float, web_thickness_mm: float,
             flange_thickness_mm: float) -> float:
    """
    Approximate cross-section area of a tee section (mm^2), ignoring root
    fillet radius:

        Area = (flange width * flange thickness) + (web height * web thickness)
    """
    web_height = height_mm - flange_thickness_mm
    web_height = max(web_height, 0.0)
    return (width_mm * flange_thickness_mm) + (web_height * web_thickness_mm)


def tee_weight(height_mm: float, width_mm: float, web_thickness_mm: float,
               flange_thickness_mm: float, length_mm: float, sg: float) -> float:
    area = tee_area(height_mm, width_mm, web_thickness_mm, flange_thickness_mm)
    return area * length_mm * sg * 1e-6


# ---------------------------------------------------------------------------
# Simple unit conversion helpers (Length + Weight), matching the original
# app's "Unit Converter" utility.
# ---------------------------------------------------------------------------

LENGTH_UNITS_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "inch": 25.4,
    "foot": 304.8,
}

WEIGHT_UNITS_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
    "tonne": 1000.0,
    "lb": 1.0 / 2.2046,
}


def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    mm = value * LENGTH_UNITS_TO_MM[from_unit]
    return mm / LENGTH_UNITS_TO_MM[to_unit]


def convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    kg = value * WEIGHT_UNITS_TO_KG[from_unit]
    return kg / WEIGHT_UNITS_TO_KG[to_unit]
