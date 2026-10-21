"""
Specific gravity (density in g/cm3) reference data.

Values reproduced from the original "Weight Calculator" (Lalta Prasad, v3.0)
Specific Gravity reference screen. These figures apply to the general-purpose
shape calculators (round bar, pipe, box section, plate) where the user may
pick any material.
"""

SPECIFIC_GRAVITY = {
    "Mild Steel (general)": 7.85,
    "Steel - C15": 7.85,
    "Steel - C35": 7.84,
    "Steel - C60": 7.83,
    "Cast Iron": 7.20,
    "Copper": 8.96,
    "Bronze": 8.73,
    "Brass": 8.45,
    "Aluminium": 2.70,
    "Lead": 11.34,
}

DEFAULT_MATERIAL = "Mild Steel (general)"

# Facts shown on the original "Units Conversion" reference screen.
UNIT_FACTS = [
    "1 cu.m = 1000 litres = 220 gallons.",
    "2.2046 Pounds = 1 Kg.",
    "304.8 mm = 1 foot.",
]
