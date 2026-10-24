import math

import pytest

from sunshine_sim.engine.models import CasingSpec, CentralizerSpec, ForceDeflectionPoint
from sunshine_sim.engine.standoff import single_joint_standoff


@pytest.fixture
def casing():
    return CasingSpec(0.1778, 0.1571, 43.2, "N80", 12.0)


@pytest.mark.parametrize("fraction,expected", [(0, 100), (0.25, 75), (0.5, 50), (1, 0)])
def test_geometric_limits(casing, fraction, expected):
    clearance = (0.2159 - casing.outer_diameter_m) / 2
    result = single_joint_standoff(casing, 0.2159, fraction * clearance)
    assert result.standoff_percent == pytest.approx(expected)
    assert result.minimum_gap_m == pytest.approx(clearance * (1 - fraction))
    assert result.standoff_ratio + result.eccentricity_ratio == pytest.approx(1)


def test_hand_calculated_example(casing):
    # 8.5 in hole, 7 in casing, prescribed offset 5 mm.
    result = single_joint_standoff(casing, 0.2159, 0.005)
    assert result.radial_clearance_m == pytest.approx(0.01905)
    assert result.minimum_gap_m == pytest.approx(0.01405)
    assert result.standoff_percent == pytest.approx(73.75328084)


@pytest.mark.parametrize("offset", [-0.001, 0.02, math.nan, math.inf])
def test_reject_bad_offset(casing, offset):
    with pytest.raises(ValueError):
        single_joint_standoff(casing, 0.2159, offset)


@pytest.mark.parametrize("hole", [0.1778, 0.15, 0, math.nan, math.inf])
def test_reject_bad_hole(casing, hole):
    with pytest.raises(ValueError):
        single_joint_standoff(casing, hole, 0)


def test_monotonic_standoff(casing):
    values = [single_joint_standoff(casing, 0.2159, e).standoff_ratio for e in [0, 0.005, 0.01]]
    assert values[0] > values[1] > values[2]


def test_invalid_casing():
    with pytest.raises(ValueError):
        CasingSpec(0.1778, 0.18, 43.2, "N80")


def test_centralizer_curve_validation():
    with pytest.raises(ValueError, match="strictly increasing"):
        CentralizerSpec(
            "DEMO",
            "bow_spring",
            0.1778,
            0.23,
            0.2159,
            100,
            80,
            (ForceDeflectionPoint(0.01, 200), ForceDeflectionPoint(0.005, 100)),
            "SYNTHETIC — not a Sunshine product",
        )
