"""Installed net-lateral support curves, not individual bow compression curves."""

from dataclasses import dataclass
from math import isclose

from sunshine_sim.engine.models import CasingSpec, CentralizerSpec
from sunshine_sim.engine.span import SpanCase, SpanResult, solve_span

CURVE_BASIS = "net_lateral_force_vs_casing_offset_in_test_hole"


@dataclass(frozen=True)
class ProductInput:
    spec: CentralizerSpec
    curve_basis: str
    data_status: str
    test_conditions: str

    def __post_init__(self) -> None:
        if self.curve_basis != CURVE_BASIS:
            raise ValueError(
                "Only installed net lateral force versus casing offset curves are supported"
            )
        if self.data_status not in {"synthetic_demo", "user_supplied_unverified"}:
            raise ValueError("Data status must be synthetic_demo or user_supplied_unverified")
        if not self.test_conditions.strip():
            raise ValueError("Test conditions are required")
        if self.spec.kind != "bow_spring":
            raise ValueError("Only bow-spring curves are supported in this prototype")
        points = self.spec.restoring_curve
        if points[0].compression_m != 0 or points[0].restoring_force_n != 0:
            raise ValueError("Curve must start at zero offset and zero net lateral force")
        if any(b.restoring_force_n <= a.restoring_force_n for a, b in zip(points, points[1:])):
            raise ValueError(
                "Net lateral force must be strictly increasing; no hysteresis branch mixing"
            )
        clearance = (self.spec.test_hole_diameter_m - self.spec.compatible_casing_od_m) / 2
        if points[-1].compression_m > clearance and not isclose(
            points[-1].compression_m, clearance, abs_tol=1e-12, rel_tol=0
        ):
            raise ValueError("Curve offsets cannot exceed test-hole radial clearance")


@dataclass(frozen=True)
class ProductResult:
    product_id: str
    data_status: str
    ideal_beam: SpanResult
    support_offset_m: float | None
    minimum_standoff_ratio: float | None
    standoff_ratios: tuple[float, ...] | None
    status: str
    model_id: str = "isolated-span-installed-support-v0.3"
    validation_status: str = "UNVALIDATED — no operational placement or sales performance claim"


def solve_product_span(casing: CasingSpec, case: SpanCase, product: ProductInput) -> ProductResult:
    """Isolated simply supported span with identical settling supports.

    Per-support load is qL/2, not qL for a shared interior support. Invert the
    measured installed net lateral curve with linear interpolation. Both ends
    settle by the same offset e; span offset is e + free beam sag. No extrapolation,
    product/test-hole rescaling, axial forces, adjacent spans, or nonlinear contact.
    CentralizerSpec.compression_m is interpreted here as casing-center offset,
    NOT individual bow compression. Free OD and run-in forces are metadata only.
    """
    spec = product.spec
    if not isclose(casing.outer_diameter_m, spec.compatible_casing_od_m, abs_tol=1e-9, rel_tol=0):
        raise ValueError("Product casing OD does not match this casing; rescaling is unsupported")
    if not isclose(case.hole_diameter_m, spec.test_hole_diameter_m, abs_tol=1e-9, rel_tol=0):
        raise ValueError("Hole diameter differs from curve test hole; obtain matching test data")
    beam = solve_span(casing, case)
    force = beam.end_reaction_n
    points = spec.restoring_curve
    # Snap only floating-point endpoint noise, never extrapolate a meaningful load.
    if isclose(force, points[-1].restoring_force_n, abs_tol=1e-9, rel_tol=0):
        force = points[-1].restoring_force_n
    if force > points[-1].restoring_force_n:
        return ProductResult(
            spec.product_id,
            product.data_status,
            beam,
            None,
            None,
            None,
            "required_force_outside_measured_curve",
        )
    offset = 0.0
    if force > 0:
        for a, b in zip(points, points[1:]):
            if a.restoring_force_n <= force <= b.restoring_force_n:
                t = (force - a.restoring_force_n) / (b.restoring_force_n - a.restoring_force_n)
                offset = a.compression_m + t * (b.compression_m - a.compression_m)
                break
    clearance = (case.hole_diameter_m - casing.outer_diameter_m) / 2
    maximum = offset + beam.maximum_free_sag_m
    status = beam.status
    if status == "within_ideal_support_screen":
        status = "predicted_wall_contact" if maximum > clearance else "within_product_screen"
    valid = status == "within_product_screen"
    return ProductResult(
        spec.product_id,
        product.data_status,
        beam,
        offset,
        (clearance - maximum) / clearance if valid else None,
        tuple((clearance - offset - y) / clearance for y in beam.free_deflection_m)
        if valid
        else None,
        status,
    )
