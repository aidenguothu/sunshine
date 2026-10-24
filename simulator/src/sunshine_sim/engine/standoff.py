"""Geometric screening only; this module does not predict casing deflection."""

from dataclasses import dataclass
from math import isfinite

from sunshine_sim.engine.models import CasingSpec, positive


@dataclass(frozen=True)
class StandoffResult:
    radial_clearance_m: float
    minimum_gap_m: float
    standoff_ratio: float
    standoff_percent: float
    eccentricity_ratio: float
    model_id: str = "circular-prescribed-offset-v0.1"
    validation_status: str = "UNVALIDATED — geometric screening only"


def single_joint_standoff(
    casing: CasingSpec, hole_diameter_m: float, eccentricity_m: float
) -> StandoffResult:
    """Calculate uniform single-joint standoff from a PRESCRIBED center offset.

    c = (hole diameter - casing OD) / 2
    minimum gap = c - e; standoff ratio = (c - e) / c.

    Assumes circular, straight, concentric-axis sections except for a constant
    lateral offset e along the joint. At e=0 standoff is 100%; at e=c it is 0%.
    Rejects interference rather than silently clamping an impossible geometry.

    Does NOT use centralizer force, survey, buoyancy, drag, axial tension, or
    beam sag to predict e. Joint length, grade, mass, and ID are retained as
    future mechanical-solver inputs, but are not used in this geometric model.
    No API/ISO algorithm or standards compliance is asserted.
    """
    positive("hole_diameter_m", hole_diameter_m)
    if hole_diameter_m <= casing.outer_diameter_m:
        raise ValueError("Hole diameter must exceed casing OD")
    if not isfinite(eccentricity_m) or eccentricity_m < 0:
        raise ValueError("Eccentricity must be finite and nonnegative")
    clearance = (hole_diameter_m - casing.outer_diameter_m) / 2
    if eccentricity_m > clearance:
        raise ValueError("Eccentricity exceeds radial clearance: wall interference")
    gap = clearance - eccentricity_m
    ratio = gap / clearance
    return StandoffResult(clearance, gap, ratio, ratio * 100, eccentricity_m / clearance)
