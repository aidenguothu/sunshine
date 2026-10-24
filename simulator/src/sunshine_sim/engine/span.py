"""Closed-form, simply supported straight beam; NOT a centralizer/contact solver."""

from dataclasses import dataclass
from math import isfinite, pi, radians, sin

from sunshine_sim.engine.models import CasingSpec, positive


@dataclass(frozen=True)
class SpanCase:
    hole_diameter_m: float
    span_length_m: float
    inclination_deg: float
    internal_density_kg_m3: float
    external_density_kg_m3: float

    def __post_init__(self) -> None:
        positive("hole_diameter_m", self.hole_diameter_m)
        positive("span_length_m", self.span_length_m)
        if not isfinite(self.inclination_deg) or not 0 <= self.inclination_deg <= 90:
            raise ValueError(
                "Inclination must be finite and between 0 and 90 degrees from vertical"
            )
        for name in ("internal_density_kg_m3", "external_density_kg_m3"):
            value = getattr(self, name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")


@dataclass(frozen=True)
class SpanResult:
    second_moment_m4: float
    effective_weight_n_m: float
    lateral_load_n_m: float
    end_reaction_n: float
    maximum_free_sag_m: float
    minimum_clearance_margin_m: float
    minimum_standoff_ratio: float | None
    status: str
    positions_m: tuple[float, ...]
    free_deflection_m: tuple[float, ...]
    standoff_ratios: tuple[float, ...] | None
    model_id: str = "ideal-support-straight-beam-v0.2"
    validation_status: str = "UNVALIDATED screening — not an operational recommendation"


def solve_span(casing: CasingSpec, case: SpanCase, samples: int = 101) -> SpanResult:
    """Uniform Euler-Bernoulli beam with ideal centered supports at x=0,L.

    I=pi(OD^4-ID^4)/64; w=g(m+rho_internal*A_internal-rho_external*A_outer).
    q=w*sin(inclination); y(x)=q*x*(L^3-2*L*x^2+x^3)/(24*E*I).
    Exact max sag=5*q*L^4/(384*E*I), independent of plot sampling.

    Static flooded straight segment; uniform fluids/hole; free pin rotation;
    no axial load/end-pressure contribution, curvature, friction, spring compliance,
    coupling effects, or wall contact. Reject net upward loading rather than
    applying an unvalidated uplift convention. Ideal support reactions are NOT
    product starting/running forces or a product suitability assessment.

    If free sag exceeds radial clearance or 1% of span, standoff is withheld.
    The 1% bound is a conservative prototype guard, not a validated validity limit.
    """
    if isinstance(samples, bool) or not isinstance(samples, int) or not 3 <= samples <= 10001:
        raise ValueError("samples must be an integer between 3 and 10001")
    if case.hole_diameter_m <= casing.outer_diameter_m:
        raise ValueError("Hole diameter must exceed casing OD")
    outer_area = pi * casing.outer_diameter_m**2 / 4
    inner_area = pi * casing.inner_diameter_m**2 / 4
    weight = 9.80665 * (
        casing.mass_per_length_kg_m
        + case.internal_density_kg_m3 * inner_area
        - case.external_density_kg_m3 * outer_area
    )
    if weight < 0:
        raise ValueError(
            "Net upward effective weight is outside this prototype's operating envelope"
        )
    moment = pi * (casing.outer_diameter_m**4 - casing.inner_diameter_m**4) / 64
    load = weight * sin(radians(case.inclination_deg))
    length = case.span_length_m
    ei = casing.youngs_modulus_pa * moment
    sag = 5 * load * length**4 / (384 * ei)
    clearance = (case.hole_diameter_m - casing.outer_diameter_m) / 2
    positions = tuple(length * i / (samples - 1) for i in range(samples))
    deflections = tuple(
        load * x * (length**3 - 2 * length * x**2 + x**3) / (24 * ei) for x in positions
    )
    if sag / length > 0.01:
        status = "outside_small_deflection_guard"
    elif sag > clearance:
        status = "wall_contact_requires_contact_solver"
    else:
        status = "within_ideal_support_screen"
    valid = status == "within_ideal_support_screen"
    return SpanResult(
        moment,
        weight,
        load,
        load * length / 2,
        sag,
        clearance - sag,
        (clearance - sag) / clearance if valid else None,
        status,
        positions,
        deflections,
        tuple((clearance - y) / clearance for y in deflections) if valid else None,
    )


@dataclass(frozen=True)
class SpacingScreen:
    candidates: tuple[tuple[float, SpanResult], ...]
    longest_passing_candidate_m: float | None
    target_standoff_ratio: float


def screen_spacings(
    casing: CasingSpec, case: SpanCase, spacings_m: tuple[float, ...], target_ratio: float
) -> SpacingScreen:
    """Screen supplied ideal-support spans; not a full-string placement optimizer.

    None means no supplied candidate passes. The selected length is only the
    longest tested passing candidate, not a continuous optimum or safe spacing.
    """
    from dataclasses import replace

    if not isfinite(target_ratio) or not 0 <= target_ratio <= 1:
        raise ValueError("Target ratio must be finite and between 0 and 1")
    if not spacings_m or len(spacings_m) > 1000:
        raise ValueError("Provide 1 to 1000 spacing candidates")
    results = tuple(
        (length, solve_span(casing, replace(case, span_length_m=length)))
        for length in sorted(set(spacings_m))
    )
    passing = [
        length
        for length, result in results
        if result.minimum_standoff_ratio is not None
        and result.minimum_standoff_ratio >= target_ratio
    ]
    return SpacingScreen(results, max(passing) if passing else None, target_ratio)
