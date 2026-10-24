from dataclasses import replace
from math import pi

import pytest

from sunshine_sim.engine.models import CasingSpec
from sunshine_sim.engine.span import SpanCase, screen_spacings, solve_span

CASING = CasingSpec(0.1778, 0.1571, 43.2, "N80")
CASE = SpanCase(0.2159, 6, 90, 1200, 1200)


def test_independent_horizontal_benchmark():
    # Independent arithmetic: equal-density buoyancy displaces steel section.
    steel_area = pi / 4 * (0.1778**2 - 0.1571**2)
    w = (43.2 - 1200 * steel_area) * 9.80665
    inertia = pi / 64 * (0.1778**4 - 0.1571**4)
    expected_sag = 5 * w * 6**4 / (384 * 207e9 * inertia)
    r = solve_span(CASING, CASE)
    assert r.maximum_free_sag_m == pytest.approx(expected_sag)
    assert r.end_reaction_n * 2 == pytest.approx(w * 6)
    assert r.minimum_standoff_ratio == pytest.approx(1 - expected_sag / 0.01905)
    assert r.free_deflection_m[0] == pytest.approx(0)
    assert r.free_deflection_m[-1] == pytest.approx(0)
    assert r.free_deflection_m[50] == pytest.approx(expected_sag)
    assert r.free_deflection_m == pytest.approx(tuple(reversed(r.free_deflection_m)))


def test_vertical_and_inclined_load():
    r = solve_span(CASING, replace(CASE, inclination_deg=0))
    assert r.minimum_standoff_ratio == 1
    r30 = solve_span(CASING, replace(CASE, inclination_deg=30))
    assert r30.maximum_free_sag_m == pytest.approx(solve_span(CASING, CASE).maximum_free_sag_m / 2)


def test_scaling_and_sampling_independence():
    r = solve_span(CASING, CASE, samples=4)  # no midpoint sample
    half = solve_span(CASING, replace(CASE, span_length_m=3))
    assert r.maximum_free_sag_m == pytest.approx(16 * half.maximum_free_sag_m)
    assert r.minimum_standoff_ratio == solve_span(CASING, CASE, samples=101).minimum_standoff_ratio
    stiff = solve_span(replace(CASING, youngs_modulus_pa=414e9), CASE)
    assert stiff.maximum_free_sag_m == pytest.approx(r.maximum_free_sag_m / 2)


def test_contact_is_not_clipped_or_presented_as_valid_standoff():
    r = solve_span(CASING, replace(CASE, span_length_m=12))
    assert r.status == "wall_contact_requires_contact_solver"
    assert r.minimum_standoff_ratio is None
    assert r.standoff_ratios is None
    assert r.minimum_clearance_margin_m < 0


def test_large_deflection_guard():
    r = solve_span(CASING, replace(CASE, span_length_m=100))
    assert r.status == "outside_small_deflection_guard"
    assert r.minimum_standoff_ratio is None


def test_candidate_selection_and_infeasibility():
    target = 0.8  # test target only; not a regulatory criterion
    result = screen_spacings(CASING, CASE, (12, 3, 6), target)
    expected = [
        length
        for length, r in result.candidates
        if r.minimum_standoff_ratio is not None and r.minimum_standoff_ratio >= target
    ]
    assert result.longest_passing_candidate_m == max(expected)
    assert screen_spacings(CASING, CASE, (12,), target).longest_passing_candidate_m is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("span_length_m", 0),
        ("inclination_deg", 91),
        ("inclination_deg", float("nan")),
        ("external_density_kg_m3", -1),
        ("internal_density_kg_m3", float("inf")),
    ],
)
def test_invalid_case(field, value):
    with pytest.raises(ValueError):
        replace(CASE, **{field: value})


def test_invalid_solver_inputs():
    for samples in (2, 10002, True, 5.5):
        with pytest.raises(ValueError):
            solve_span(CASING, CASE, samples)
    with pytest.raises(ValueError, match="upward"):
        solve_span(CASING, replace(CASE, external_density_kg_m3=10000))
    with pytest.raises(ValueError, match="Hole"):
        solve_span(CASING, replace(CASE, hole_diameter_m=0.1))
    for target in (-0.1, 1.1, float("nan")):
        with pytest.raises(ValueError):
            screen_spacings(CASING, CASE, (3,), target)
    with pytest.raises(ValueError):
        screen_spacings(CASING, CASE, (), 0.8)
