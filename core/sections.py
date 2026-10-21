"""
Standard Indian Standard (IS) rolled structural steel section dimensions.

Source: published IS 808 (beams & channels), IS 1852 (angles) and IS 1173
(tee bars) dimension tables, as commonly reproduced in structural steel
handbooks. These are STEEL-ONLY rolled sections (no aluminium/brass/bronze
equivalents exist in these standards).

Each entry gives the nominal cross-section dimensions in millimetres:
  Beams / Channels : (H, B, tw, tf)   = depth, flange width, web thickness, flange thickness
  Tee bars         : (H, B, tw, tf)   = depth, flange width, web thickness, flange thickness
  Angles           : (A, B, t)        = leg 1, leg 2, thickness  (A == B for equal angles)

This is a curated set of the most commonly used sizes in each series, not an
exhaustive reproduction of every listed designation. For a size not listed
here, use the "Custom / General Section" mode of the matching calculator,
which uses the identical formula and lets you type the dimensions directly
(from a mill certificate, drawing, or the IS handbook).
"""

# ---------------------------------------------------------------------------
# Beams: (H, B, tw, tf) in mm
# ---------------------------------------------------------------------------
BEAM_SECTIONS = {
    # Indian Standard Junior Beams
    "ISJB 150": (150, 80, 4.6, 6.8),
    "ISJB 175": (175, 90, 4.8, 7.0),
    "ISJB 200": (200, 100, 5.0, 7.2),
    "ISJB 225": (225, 110, 5.2, 7.4),
    # Indian Standard Light Weight Beams
    "ISLB 75": (75, 75, 4.0, 6.0),
    "ISLB 100": (100, 75, 4.0, 6.5),
    "ISLB 125": (125, 75, 4.4, 6.6),
    "ISLB 150": (150, 80, 4.6, 6.8),
    "ISLB 175": (175, 90, 4.8, 7.0),
    "ISLB 200": (200, 100, 5.0, 7.2),
    "ISLB 225": (225, 110, 5.2, 7.4),
    "ISLB 250": (250, 125, 5.5, 7.6),
    "ISLB 300": (300, 150, 6.7, 9.4),
    "ISLB 350": (350, 165, 7.4, 10.0),
    "ISLB 400": (400, 165, 8.0, 12.5),
    "ISLB 450": (450, 170, 8.6, 13.4),
    "ISLB 500": (500, 180, 9.2, 14.1),
    "ISLB 550": (550, 190, 9.9, 14.7),
    "ISLB 600": (600, 210, 10.5, 15.6),
    # Indian Standard Medium Weight Beams
    "ISMB 100": (100, 75, 4.0, 6.5),
    "ISMB 125": (125, 75, 4.4, 6.7),
    "ISMB 150": (150, 80, 4.8, 7.6),
    "ISMB 175": (175, 85, 5.2, 8.5),
    "ISMB 200": (200, 100, 5.7, 10.8),
    "ISMB 225": (225, 110, 6.5, 11.8),
    "ISMB 250": (250, 125, 6.9, 12.5),
    "ISMB 300": (300, 140, 7.7, 13.1),
    "ISMB 350": (350, 140, 8.1, 14.2),
    "ISMB 400": (400, 140, 8.9, 16.0),
    "ISMB 450": (450, 150, 9.4, 17.4),
    "ISMB 500": (500, 180, 10.2, 17.2),
    "ISMB 550": (550, 190, 11.2, 19.3),
    "ISMB 600": (600, 210, 12.0, 20.3),
    # Indian Standard Wide Flange Beams
    "ISWB 150": (150, 100, 5.4, 7.6),
    "ISWB 175": (175, 125, 5.8, 8.1),
    "ISWB 200": (200, 140, 5.7, 9.3),
    "ISWB 225": (225, 150, 6.5, 9.9),
    "ISWB 250": (250, 150, 6.9, 11.4),
    "ISWB 300": (300, 150, 7.7, 12.4),
    "ISWB 350": (350, 170, 8.1, 13.2),
    "ISWB 400": (400, 180, 8.6, 14.4),
    "ISWB 450": (450, 200, 9.4, 15.4),
    "ISWB 500": (500, 200, 10.2, 17.2),
    "ISWB 550": (550, 210, 11.1, 18.8),
    "ISWB 600": (600, 220, 12.0, 20.3),
    # Indian Standard Column Sections (H-Beams)
    "ISHB 150": (150, 150, 5.4, 9.0),
    "ISHB 175": (175, 175, 5.8, 9.5),
    "ISHB 200": (200, 200, 6.1, 9.0),
    "ISHB 225": (225, 225, 6.5, 9.5),
    "ISHB 250": (250, 250, 6.9, 9.7),
    "ISHB 300": (300, 250, 7.6, 10.6),
    "ISHB 350": (350, 250, 8.3, 11.6),
    "ISHB 400": (400, 250, 9.1, 12.7),
    "ISHB 450": (450, 250, 9.8, 13.7),
    # Provisional Sizes
    "100(P)": (100, 50, 4.0, 5.6),
    "125(P)": (125, 70, 4.1, 5.9),
    "150(P)": (150, 80, 4.5, 6.5),
    "175(P)": (175, 90, 4.6, 6.9),
    "200(P)": (200, 100, 5.2, 7.6),
    "300(P)": (300, 125, 6.0, 8.9),
}

# ---------------------------------------------------------------------------
# Channels: (H, B, tw, tf) in mm
# ---------------------------------------------------------------------------
CHANNEL_SECTIONS = {
    # Indian Standard Junior Channels
    "ISJC 100": (100, 50, 4.2, 6.2),
    "ISJC 125": (125, 65, 4.4, 6.4),
    "ISJC 150": (150, 75, 4.6, 6.6),
    "ISJC 175": (175, 75, 4.8, 6.8),
    "ISJC 200": (200, 75, 5.0, 7.0),
    # Indian Standard Light Channels
    "ISLC 100": (100, 50, 4.0, 5.5),
    "ISLC 125": (125, 65, 4.2, 5.8),
    "ISLC 150": (150, 75, 4.4, 6.0),
    "ISLC 175": (175, 75, 4.8, 6.5),
    "ISLC 200": (200, 75, 5.0, 7.0),
    # Indian Standard Medium Weight Channels
    "ISMC 75": (75, 40, 4.4, 7.3),
    "ISMC 100": (100, 50, 4.7, 7.5),
    "ISMC 125": (125, 65, 5.0, 8.1),
    "ISMC 150": (150, 75, 5.4, 9.0),
    "ISMC 175": (175, 75, 6.0, 9.5),
    "ISMC 200": (200, 75, 6.2, 11.4),
    "ISMC 225": (225, 80, 6.4, 12.4),
    "ISMC 250": (250, 82, 7.2, 14.1),
    "ISMC 300": (300, 90, 7.8, 13.6),
    "ISMC 350": (350, 100, 8.1, 13.5),
    "ISMC 400": (400, 100, 8.6, 15.3),
    # Indian Standard Channel Sections for General Use
    "ISCG 250": (250, 75, 6.5, 12.0),
    "ISCG 300": (300, 90, 7.5, 13.0),
}

# ---------------------------------------------------------------------------
# Equal angles: (A, A, t) in mm  -- leg x leg x thickness
# ---------------------------------------------------------------------------
EQUAL_ANGLE_SECTIONS = {
    "ISA 20x20x3": (20, 20, 3),
    "ISA 25x25x3": (25, 25, 3),
    "ISA 25x25x5": (25, 25, 5),
    "ISA 30x30x3": (30, 30, 3),
    "ISA 30x30x5": (30, 30, 5),
    "ISA 35x35x4": (35, 35, 4),
    "ISA 40x40x4": (40, 40, 4),
    "ISA 40x40x5": (40, 40, 5),
    "ISA 45x45x5": (45, 45, 5),
    "ISA 45x45x6": (45, 45, 6),
    "ISA 50x50x5": (50, 50, 5),
    "ISA 50x50x6": (50, 50, 6),
    "ISA 55x55x6": (55, 55, 6),
    "ISA 60x60x6": (60, 60, 6),
    "ISA 65x65x6": (65, 65, 6),
    "ISA 65x65x8": (65, 65, 8),
    "ISA 70x70x6": (70, 70, 6),
    "ISA 75x75x6": (75, 75, 6),
    "ISA 75x75x8": (75, 75, 8),
    "ISA 80x80x6": (80, 80, 6),
    "ISA 80x80x8": (80, 80, 8),
    "ISA 90x90x6": (90, 90, 6),
    "ISA 90x90x8": (90, 90, 8),
    "ISA 100x100x8": (100, 100, 8),
    "ISA 100x100x10": (100, 100, 10),
    "ISA 110x110x10": (110, 110, 10),
    "ISA 130x130x10": (130, 130, 10),
    "ISA 150x150x10": (150, 150, 10),
    "ISA 150x150x12": (150, 150, 12),
    "ISA 200x200x12": (200, 200, 12),
    "ISA 200x200x16": (200, 200, 16),
}

# ---------------------------------------------------------------------------
# Unequal angles: (A, B, t) in mm
# ---------------------------------------------------------------------------
UNEQUAL_ANGLE_SECTIONS = {
    "ISA 30x20x3": (30, 20, 3),
    "ISA 30x20x4": (30, 20, 4),
    "ISA 40x25x4": (40, 25, 4),
    "ISA 40x25x5": (40, 25, 5),
    "ISA 45x30x5": (45, 30, 5),
    "ISA 50x30x5": (50, 30, 5),
    "ISA 50x30x6": (50, 30, 6),
    "ISA 60x40x5": (60, 40, 5),
    "ISA 60x40x6": (60, 40, 6),
    "ISA 65x45x5": (65, 45, 5),
    "ISA 65x45x6": (65, 45, 6),
    "ISA 75x50x6": (75, 50, 6),
    "ISA 75x50x8": (75, 50, 8),
    "ISA 80x50x6": (80, 50, 6),
    "ISA 90x60x6": (90, 60, 6),
    "ISA 90x60x8": (90, 60, 8),
    "ISA 100x65x7": (100, 65, 7),
    "ISA 100x65x8": (100, 65, 8),
    "ISA 100x75x8": (100, 75, 8),
    "ISA 125x75x8": (125, 75, 8),
    "ISA 125x75x10": (125, 75, 10),
    "ISA 125x95x8": (125, 95, 8),
    "ISA 150x75x8": (150, 75, 8),
    "ISA 150x115x8": (150, 115, 8),
    "ISA 150x115x10": (150, 115, 10),
    "ISA 200x100x10": (200, 100, 10),
    "ISA 200x150x10": (200, 150, 10),
    "ISA 200x150x12": (200, 150, 12),
}

# ---------------------------------------------------------------------------
# Tee bars: (H, B, tw, tf) in mm
# ---------------------------------------------------------------------------
TEE_SECTIONS = {
    # Indian Standard Normal Tee Bars (ISNT)
    "ISNT 40": (40, 40, 4.0, 4.0),
    "ISNT 50": (50, 50, 4.5, 4.5),
    "ISNT 60": (60, 60, 5.0, 5.0),
    "ISNT 75": (75, 75, 5.5, 5.5),
    "ISNT 100": (100, 100, 6.0, 6.0),
    # Indian Standard Deep Legged Tee Bars (ISDT)
    "ISDT 75": (75, 50, 5.0, 6.0),
    "ISDT 100": (100, 60, 6.0, 7.0),
    "ISDT 125": (125, 65, 6.5, 8.0),
    # Indian Standard Slit Light Weight Tee Bars (ISLT)
    "ISLT 75": (75, 75, 4.0, 6.5),
    "ISLT 100": (100, 75, 4.0, 6.5),
    "ISLT 125": (125, 75, 4.4, 6.7),
    # Indian Standard Slit Medium Weight Tee Bars (ISMT)
    "ISMT 100": (100, 75, 4.8, 7.6),
    "ISMT 125": (125, 75, 5.2, 8.5),
    "ISMT 150": (150, 100, 5.7, 10.8),
}
