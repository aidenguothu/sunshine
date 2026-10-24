"""Immutable inputs in SI units. No UI, filesystem, or database dependencies."""

from dataclasses import dataclass
from math import isfinite


def positive(name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")


@dataclass(frozen=True)
class CasingSpec:
    outer_diameter_m: float
    inner_diameter_m: float
    mass_per_length_kg_m: float
    grade: str
    joint_length_m: float = 12.0
    youngs_modulus_pa: float = 207e9

    def __post_init__(self) -> None:
        for name in (
            "outer_diameter_m",
            "inner_diameter_m",
            "mass_per_length_kg_m",
            "joint_length_m",
            "youngs_modulus_pa",
        ):
            positive(name, getattr(self, name))
        if self.inner_diameter_m >= self.outer_diameter_m:
            raise ValueError("Casing ID must be less than OD")
        if not self.grade.strip():
            raise ValueError("Casing grade is required")


@dataclass(frozen=True)
class ForceDeflectionPoint:
    compression_m: float
    restoring_force_n: float

    def __post_init__(self) -> None:
        for name in ("compression_m", "restoring_force_n"):
            value = getattr(self, name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")


@dataclass(frozen=True)
class CentralizerSpec:
    product_id: str
    kind: str
    compatible_casing_od_m: float
    free_outer_diameter_m: float
    test_hole_diameter_m: float
    starting_force_n: float
    running_force_n: float
    restoring_curve: tuple[ForceDeflectionPoint, ...]
    test_reference: str

    def __post_init__(self) -> None:
        if not self.product_id.strip() or not self.test_reference.strip():
            raise ValueError("Product ID and test reference are required")
        if self.kind not in {"bow_spring", "rigid", "semi_rigid"}:
            raise ValueError("Unsupported centralizer kind")
        for name in (
            "compatible_casing_od_m",
            "free_outer_diameter_m",
            "test_hole_diameter_m",
        ):
            positive(name, getattr(self, name))
        if (
            min(self.free_outer_diameter_m, self.test_hole_diameter_m)
            <= self.compatible_casing_od_m
        ):
            raise ValueError("Centralizer and test hole OD must exceed compatible casing OD")
        for name in ("starting_force_n", "running_force_n"):
            value = getattr(self, name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if len(self.restoring_curve) < 2:
            raise ValueError("At least two measured force-deflection points are required")
        if any(
            b.compression_m <= a.compression_m
            for a, b in zip(self.restoring_curve, self.restoring_curve[1:])
        ):
            raise ValueError("Compression points must be strictly increasing")
