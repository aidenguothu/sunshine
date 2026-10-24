"""Jointed pin-span interval screen, not a continuous casing/contact solver."""

from dataclasses import asdict
from math import isclose, isfinite

import numpy as np
from numpy.polynomial import Polynomial

from sunshine_sim.engine.models import CasingSpec
from sunshine_sim.engine.product import ProductInput
from sunshine_sim.engine.span import SpanCase, solve_span


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError("Job numbers must be finite numeric values")
    return float(value)


def simulate_job(job: dict, products: tuple[ProductInput, ...]) -> dict:
    """Solve independent pin spans sharing lateral support reactions.

    Uniform local load in each span; all survey inclinations and azimuths must
    be constant (curvature unsupported). Every casing-section boundary requires
    a support. OD must be unchanged across sections. Supports can settle by
    different amounts; free beam shape plus linear end settlement is used.
    Maximum offset is found analytically; minimum clearance gives a conservative
    standoff lower bound even for variable piecewise-linear caliper.
    """
    try:
        return _simulate(job, products)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError(f"Invalid job structure: {exc}") from exc


def _simulate(job, products):
    sections, survey, caliper, placements = (
        job["casing_sections"],
        job["survey"],
        job["caliper"],
        job["placements"],
    )
    for rows in (sections, survey, caliper, placements):
        if not isinstance(rows, list) or not 1 <= len(rows) <= 2000:
            raise ValueError("Each job table must contain 1 to 2000 rows")
    if len(survey) < 2 or len(caliper) < 2 or len(placements) < 2:
        raise ValueError("Survey, caliper and placements each need at least two rows")
    start = finite(sections[0]["start_md_m"])
    end = finite(sections[-1]["end_md_m"])
    if start < 0 or end <= start:
        raise ValueError("Invalid interval depths")
    casings = []
    previous = start
    for s in sections:
        a, b = finite(s["start_md_m"]), finite(s["end_md_m"])
        if a != previous or b <= a:
            raise ValueError("Casing sections must be ordered, contiguous and nonoverlapping")
        casings.append(CasingSpec(**s["casing"]))
        previous = b
    if any(c.outer_diameter_m != casings[0].outer_diameter_m for c in casings):
        raise ValueError("Changing casing OD at a support is not yet supported")
    for table in (survey, caliper, placements):
        depths = [finite(row["md_m"]) for row in table]
        if any(b <= a for a, b in zip(depths, depths[1:])):
            raise ValueError("Table depths must be strictly increasing, with no duplicates")
    if survey[0]["md_m"] > start or survey[-1]["md_m"] < end:
        raise ValueError("Survey must cover the entire casing interval")
    if caliper[0]["md_m"] > start or caliper[-1]["md_m"] < end:
        raise ValueError("Caliper must cover the entire casing interval")
    inclination = finite(survey[0]["inclination_deg"])
    azimuth = finite(survey[0]["azimuth_deg"])
    if not 0 <= inclination <= 90 or not 0 <= azimuth < 360:
        raise ValueError("Survey angles out of range")
    if any(
        not isclose(finite(r["inclination_deg"]), inclination, abs_tol=1e-9)
        or not isclose(finite(r["azimuth_deg"]), azimuth, abs_tol=1e-9)
        for r in survey
    ):
        raise ValueError("Curved survey unsupported: use a constant-inclination/azimuth interval")
    cds = [finite(r["hole_diameter_m"]) for r in caliper]
    if min(cds) <= casings[0].outer_diameter_m:
        raise ValueError("Every caliper diameter must exceed casing OD")
    md = [p["md_m"] for p in placements]
    if md[0] != start or md[-1] != end:
        raise ValueError("Place end supports exactly at both interval boundaries")
    if any(s["start_md_m"] not in md for s in sections):
        raise ValueError("Every casing section boundary requires a support")
    catalog = {p.spec.product_id: p for p in products}
    if len(catalog) != len(products):
        raise ValueError("Catalog IDs must be unique")

    def hole_at(depth):
        return float(np.interp(depth, [r["md_m"] for r in caliper], cds))

    beams, section_ids = [], []
    for a, b in zip(md, md[1:]):
        idx = next(i for i, s in enumerate(sections) if s["start_md_m"] <= a < s["end_md_m"])
        case = SpanCase(
            hole_at(a),
            b - a,
            inclination,
            finite(job["internal_density_kg_m3"]),
            finite(job["external_density_kg_m3"]),
        )
        beams.append(solve_span(casings[idx], case))
        section_ids.append(idx)
    forces = [0.0] * len(md)
    for i, beam in enumerate(beams):
        forces[i] += beam.end_reaction_n
        forces[i + 1] += beam.end_reaction_n
    support_rows, offsets = [], []
    for i, placement in enumerate(placements):
        pid = placement["product_id"]
        if pid not in catalog:
            raise ValueError(f"Unknown product: {pid}")
        p = catalog[pid]
        if not isclose(
            p.spec.compatible_casing_od_m, casings[0].outer_diameter_m, abs_tol=1e-9, rel_tol=0
        ):
            raise ValueError(f"{pid}: incompatible casing OD at MD {md[i]}")
        if not isclose(p.spec.test_hole_diameter_m, hole_at(md[i]), abs_tol=1e-9, rel_tol=0):
            raise ValueError(f"{pid}: test-hole mismatch at MD {md[i]}; no curve rescaling allowed")
        curve = p.spec.restoring_curve
        limit = curve[-1].restoring_force_n
        offset = (
            None
            if forces[i] > limit + 1e-9
            else float(
                np.interp(
                    min(forces[i], limit),
                    [v.restoring_force_n for v in curve],
                    [v.compression_m for v in curve],
                )
            )
        )
        offsets.append(offset)
        support_rows.append(
            dict(
                md_m=md[i],
                product_id=pid,
                data_status=p.data_status,
                reaction_n=forces[i],
                offset_m=offset,
                status="curve_load_exceeded" if offset is None else "within_curve",
            )
        )
    spans, profile = [], []
    for i, beam in enumerate(beams):
        a, b = md[i : i + 2]
        length = b - a
        status, lower, lower_depth = "within_jointed_span_screen", None, None
        if offsets[i] is None or offsets[i + 1] is None:
            status = "support_curve_load_exceeded"
        elif beam.maximum_free_sag_m / length > 0.01:
            status = "outside_small_deflection_guard"
        else:
            # Work in normalized t=x/L to avoid poorly scaled polynomial roots.
            scale = (
                beam.lateral_load_n_m
                * length**4
                / (24 * casings[section_ids[i]].youngs_modulus_pa * beam.second_moment_m4)
            )
            poly = Polynomial(
                [offsets[i], offsets[i + 1] - offsets[i] + scale, 0, -2 * scale, scale]
            )
            roots = [
                float(r.real) for r in poly.deriv().roots() if abs(r.imag) < 1e-9 and 0 < r.real < 1
            ]
            probes = [0.0, 1.0, *roots]
            max_t = max(probes, key=poly)
            max_offset = float(poly(max_t))
            caliper_depths = [r["md_m"] for r in caliper if a < r["md_m"] < b]
            clearance = min(
                (hole_at(d) - casings[section_ids[i]].outer_diameter_m) / 2
                for d in [a, b, *caliper_depths]
            )
            if max_offset > clearance:
                status = "possible_contact_bound_requires_contact_solver"
            else:
                lower = 1 - max_offset / clearance
                lower_depth = a + max_t * length  # maximum offset, not actual minimum-ratio depth
            depths = sorted(
                set(
                    [a + length * j / 100 for j in range(101)]
                    + caliper_depths
                    + [a + max_t * length]
                )
            )
            for depth in depths:
                gap = (hole_at(depth) - casings[section_ids[i]].outer_diameter_m) / 2
                ratio = (gap - float(poly((depth - a) / length))) / gap
                profile.append(
                    dict(
                        md_m=depth,
                        standoff_ratio=ratio if lower is not None else None,
                        hole_diameter_m=hole_at(depth),
                        span_index=i,
                    )
                )
        spans.append(
            dict(
                start_md_m=a,
                end_md_m=b,
                casing_section=section_ids[i],
                standoff_lower_bound=lower,
                maximum_offset_md_m=lower_depth,
                status=status,
            )
        )
    joints = []
    for section, casing in zip(sections, casings):
        joint_start = section["start_md_m"]
        count = (section["end_md_m"] - joint_start) / casing.joint_length_m
        if count > 5000:
            raise ValueError("Limit exceeded: 5000 joints per casing section")
        while joint_start < section["end_md_m"]:
            joint_end = min(joint_start + casing.joint_length_m, section["end_md_m"])
            overlaps = [
                s for s in spans if s["start_md_m"] < joint_end and s["end_md_m"] > joint_start
            ]
            bounds = [s["standoff_lower_bound"] for s in overlaps]
            joints.append(
                dict(
                    start_md_m=joint_start,
                    end_md_m=joint_end,
                    standoff_lower_bound=min(bounds)
                    if all(v is not None for v in bounds)
                    else None,
                    status="UNVALIDATED conservative span-envelope bound",
                )
            )
            joint_start = joint_end
    complete = all(s["standoff_lower_bound"] is not None for s in spans)
    return dict(
        model_id="jointed-pin-span-v0.4",
        review_status="UNVALIDATED — demonstration only",
        status="screen_complete" if complete else "unsupported_or_possible_contact",
        minimum_standoff_lower_bound=min(s["standoff_lower_bound"] for s in spans)
        if complete
        else None,
        joints=joints,
        supports=support_rows,
        spans=spans,
        profile=profile,
        assumptions="Independent pin spans (rotation discontinuities); shared force load; "
        "no continuous-string moments, axial force, curvature, friction or contact; "
        "piecewise-linear caliper; conservative standoff bound, not exact minimum.",
        catalog_snapshot=[asdict(p) for p in products],
    )
