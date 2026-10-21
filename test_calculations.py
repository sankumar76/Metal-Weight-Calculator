"""Quick sanity checks for core/calculations.py (run headless, no GUI needed)."""

from core import calculations as c
from core.materials import SPECIFIC_GRAVITY
from core.sections import BEAM_SECTIONS, EQUAL_ANGLE_SECTIONS


def approx(a, b, tol=0.05):
    return abs(a - b) <= tol * max(abs(b), 1e-9)


def test_round_bar_matches_d2_over_162_rule():
    # Classic steel-industry shortcut: kg/m = d^2 / 162 (d in mm), for SG=7.85
    d = 100.0
    w = c.round_bar_weight(diameter_mm=d, length_mm=1000.0, sg=7.85)
    shortcut = d ** 2 / 162.0
    assert approx(w, shortcut), f"{w} vs {shortcut}"
    print(f"round bar 100mm dia x 1m: {w:.3f} kg  (shortcut d^2/162 = {shortcut:.3f} kg)  OK")


def test_pipe_weight_reduces_to_round_bar_when_inner_is_zero():
    w_pipe = c.pipe_weight(outer_diameter_mm=50, inner_diameter_mm=0, length_mm=1000, sg=7.85)
    w_bar = c.round_bar_weight(diameter_mm=50, length_mm=1000, sg=7.85)
    assert approx(w_pipe, w_bar, tol=1e-9)
    print(f"pipe with 0 inner dia == round bar: {w_pipe:.4f} kg == {w_bar:.4f} kg  OK")


def test_plate_weight_simple_volume():
    # 1m x 1m x 10mm mild steel plate
    w = c.plate_weight(length_mm=1000, width_mm=1000, thickness_mm=10, sg=7.85)
    expected = 1.0 * 1.0 * 0.010 * 7850  # m3 * kg/m3
    assert approx(w, expected)
    print(f"plate 1m x 1m x 10mm steel: {w:.2f} kg  (expected ~{expected:.2f} kg)  OK")


def test_box_section_area_positive_and_sane():
    area = c.box_section_area(outer_length_mm=100, outer_width_mm=50, thickness_mm=5)
    # outer area 5000, inner area 90*40=3600, wall area = 1400
    assert approx(area, 1400.0, tol=1e-9)
    print(f"box section 100x50x5mm wall area: {area} mm^2  OK")


def test_all_materials_produce_positive_weight():
    for name, sg in SPECIFIC_GRAVITY.items():
        w = c.round_bar_weight(diameter_mm=20, length_mm=1000, sg=sg)
        assert w > 0
    print(f"all {len(SPECIFIC_GRAVITY)} materials compute positive weight  OK")


def test_standard_beam_lookup_and_weight():
    h, b, tw, tf = BEAM_SECTIONS["ISMB 200"]
    w_per_m = c.beam_channel_weight(h, b, tw, tf, length_mm=1000, sg=7.85)
    print(f"ISMB 200 approx weight: {w_per_m:.2f} kg/m (published ~25.4 kg/m)")
    assert 15 < w_per_m < 35  # sanity band, approximate formula ignores fillets


def test_standard_angle_lookup_and_weight():
    a, b, t = EQUAL_ANGLE_SECTIONS["ISA 50x50x6"]
    w_per_m = c.angle_weight(a, b, t, length_mm=1000, sg=7.85)
    print(f"ISA 50x50x6 approx weight: {w_per_m:.2f} kg/m (published ~4.5 kg/m)")
    assert 2 < w_per_m < 7


def test_unit_conversions():
    assert approx(c.convert_length(304.8, "mm", "foot"), 1.0)
    assert approx(c.convert_weight(1.0, "kg", "lb"), 2.2046)
    print("unit conversions: 304.8mm -> 1 foot, 1kg -> 2.2046 lb  OK")


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\nAll {len(tests)} checks passed.")
