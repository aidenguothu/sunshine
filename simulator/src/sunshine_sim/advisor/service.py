"""Pure Release 1 dimensional assessment, placement and commercial quantities."""

from dataclasses import asdict

from sunshine_sim.advisor.catalog import DEMO
from sunshine_sim.advisor.engineering import number, rigid_sor, validate_survey
from sunshine_sim.advisor.placement import placements

MODEL = "sunshine-sales-r1.0"
DISCLAIMER = (
    "This preliminary centralizer placement assessment is based on supplied well data and a "
    "simplified screening model. It is intended for product selection and quotation support, "
    "not as a substitute for detailed well-engineering, casing-running or cementing design. "
    "Final centralizer type, spacing, stop-collar selection and placement must be verified by "
    "the responsible qualified engineer against actual well conditions, current standards, "
    "and manufacturer test data. No cement isolation or run-to-bottom performance is guaranteed."
)


def validate_job(job):
    top, bottom = number(job["top_md_m"], "Top MD", 0), number(job["bottom_md_m"], "Bottom MD", 0)
    if top >= bottom:
        raise ValueError("Bottom MD must exceed top MD")
    od = number(job["casing_od_m"], "Casing OD")
    inside = job.get("casing_id_m")
    if od <= 0 or (inside is not None and not 0 < number(inside) < od):
        raise ValueError("Casing OD must be positive and ID must be between zero and OD")
    if inside is None and job.get("mass_kg_m") is None:
        raise ValueError("Supply casing ID or verified linear mass")
    if job.get("mass_kg_m") is not None and number(job["mass_kg_m"]) <= 0:
        raise ValueError("Linear mass must be positive")
    if job.get("modulus_pa") is not None and number(job["modulus_pa"]) <= 0:
        raise ValueError("Young modulus must be positive when supplied")
    number(job["fluid_density_kg_m3"], "Fluid density", 0)
    target = number(job["target_ratio"], "Customer target")
    if not 0 <= target <= 1:
        raise ValueError("Target must be 0–100%")
    holes = job["holes"]
    if not 1 <= len(holes) <= 10000:
        raise ValueError("Supply hole intervals")
    last = top
    for h in holes:
        a, b = number(h["top_md_m"]), number(h["bottom_md_m"])
        if a != last or b <= a:
            raise ValueError(
                "Hole intervals must be ordered, contiguous and cover the analysis interval"
            )
        if number(h["hole_id_m"]) <= od:
            raise ValueError("Hole ID must exceed casing OD in every interval")
        restriction = h.get("restriction_id_m")
        if restriction is not None and number(restriction) <= od:
            raise ValueError("Restriction ID must exceed casing OD")
        if not h.get("source"):
            raise ValueError("Label hole origin: caliper, nominal, customer supplied or synthetic")
        last = b
    if last != bottom:
        raise ValueError("Hole intervals must cover the analysis interval exactly")
    if job.get("previous_casing_id_m") is not None and number(job["previous_casing_id_m"]) <= od:
        raise ValueError("Previous casing / passage ID must exceed casing OD")
    number(job.get("dls_warning_deg_30m", 3), "DLS warning threshold", 0)
    return validate_survey(job["survey"])


def hole_at(job, md):
    for i, h in enumerate(job["holes"]):
        if h["top_md_m"] <= md < h["bottom_md_m"] or (
            i == len(job["holes"]) - 1 and md == h["bottom_md_m"]
        ):
            return h
    raise ValueError("Placement is outside the hole profile")


def compatibility(job, sku):
    """Checks entire run path supplied, not just the final installation location."""
    blocks, reviews = [], []
    if not sku.demo and "sunshine" not in sku.manufacturer.lower():
        blocks.append("Sales advisor requires an authorized Sunshine manufacturer SKU")
    if abs(job["casing_od_m"] - sku.casing_od_m) > 1e-8:
        blocks.append("SKU casing OD does not match the selected casing")
    if sku.minimum_bore_m is None:
        reviews.append("Product internal bore/fit drawing not supplied")
    elif sku.minimum_bore_m <= job["casing_od_m"]:
        blocks.append("Product bore does not clear casing OD")
    holes = job["holes"]
    passage = [h["hole_id_m"] for h in holes]
    passage += [h["restriction_id_m"] for h in holes if h.get("restriction_id_m") is not None]
    if job.get("previous_casing_id_m") is not None:
        passage.append(job["previous_casing_id_m"])
    minimum = min(passage)
    if any(not sku.hole_min_m - 1e-9 <= h["hole_id_m"] <= sku.hole_max_m + 1e-9 for h in holes):
        reviews.append("Some hole diameters are outside the supplied product application range")
    if sku.family == "rigid":
        if sku.rigid_od_m > minimum:
            blocks.append("Rigid OD exceeds minimum hole/restriction passage")
    else:
        if sku.compressed_od_m is None:
            reviews.append("Compressed OD / restriction running data required")
        elif sku.compressed_od_m > minimum:
            blocks.append("Compressed product OD exceeds minimum passage")
        reviews.append(
            "Bow/semi-rigid running conditions require engineering review; "
            "free OD alone is not a pass/fail test"
        )
    if sku.length_m is None:
        reviews.append("Product body length missing; coupling/body clearances cannot be verified")
    if not sku.collar_rule_reference:
        reviews.append(
            "Stop-collar installation rule reference required (including "
            "zero-collar configurations)"
        )
    if sku.collars_per_unit and not sku.collar_sku:
        reviews.append("Stop-collar part number not supplied; obtain approved retainer SKU")
    if not sku.approved_for_customers:
        reviews.append("Manufacturer approval metadata not supplied; selection is unverified")
    return dict(
        status="Not suitable" if blocks else ("Verify" if reviews else "Suitable"),
        blocking=blocks,
        review=reviews,
        minimum_passage_m=minimum,
    )


def assess(job, sku):
    survey = validate_job(job)
    fit = compatibility(job, sku)
    plan = placements(job, sku)
    reasons = list(fit["review"])
    if survey[0]["md_m"] > job["top_md_m"] or survey[-1]["md_m"] < job["bottom_md_m"]:
        reasons.append(
            "Survey does not cover analysis interval: no extrapolation; obtain missing stations"
        )
    max_dls = max(r["dls_deg_30m"] for r in survey)
    if max_dls > job.get("dls_warning_deg_30m", 3):
        reasons.append("Customer DLS warning threshold exceeded; curvature/tension not modeled")
    reasons.append(
        "Between-centralizer standoff not calculated: sag, curvature and "
        "axial load are not modeled in R1"
    )
    if sku.family == "rigid" and not fit["blocking"]:
        for p in plan:
            h = hole_at(job, p["md_m"])
            # Dimension-only wall-contact support estimate; no load equilibrium assertion.
            p["at_support_geometric_sor"] = rigid_sor(
                h["hole_id_m"], job["casing_od_m"], sku.rigid_od_m
            )
            p["between_support_sor"] = None
    else:
        for p in plan:
            p["at_support_geometric_sor"] = None
            p["between_support_sor"] = None
        reasons.append(
            "Standoff not calculable from available test data / load model; "
            "one restoring-force rating is not a curve"
        )
    synthetic = sku.demo or job.get("data_origin") == "synthetic demo"
    needs_review = (
        fit["blocking"]
        or fit["review"]
        or survey[0]["md_m"] > job["top_md_m"]
        or survey[-1]["md_m"] < job["bottom_md_m"]
        or max_dls > job.get("dls_warning_deg_30m", 3)
    )
    quality = (
        "SYNTHETIC_DEMO"
        if synthetic
        else ("REVIEW_REQUIRED" if needs_review else "DIMENSIONAL_ONLY")
    )
    count = len(plan)
    bom = [
        dict(
            sku=sku.sku,
            description="Centralizer",
            quantity=count,
            unit_price=sku.unit_price,
            currency=sku.currency,
            price_reference=sku.price_reference,
            total=None if sku.unit_price is None else count * sku.unit_price,
        )
    ]
    if sku.collars_per_unit:
        bom.append(
            dict(
                sku=sku.collar_sku or "PART NUMBER REQUIRED",
                description="Stop collar / retainer",
                quantity=count * sku.collars_per_unit,
                unit_price=None,
                currency="",
                price_reference="",
                total=None,
            )
        )
    return dict(
        model_version=MODEL,
        validity=quality,
        methodology="Dimensional selection + joint pattern; rigid wall-contact geometry only",
        banner=DEMO if synthetic else "PRELIMINARY — ENGINEERING REVIEW REQUIRED",
        compatibility=fit,
        placement=plan,
        bom=bom,
        survey=survey,
        maximum_dls_deg_30m=max_dls,
        reasons=reasons,
        product_snapshot=asdict(sku),
        between_support_status="Not calculated",
        optimization_enabled=False,
        disclaimer=DISCLAIMER,
    )


def assess_selection(job, products):
    """Apply per-interval/per-joint SKU choices without modifying legacy solvers."""
    from dataclasses import replace

    catalog = {p.sku: p for p in products}
    if job["selected_sku"] not in catalog:
        raise ValueError("Selected SKU is absent from the sales catalog")
    primary = catalog[job["selected_sku"]]
    zones = job.get("sku_zones", [])
    for z in zones:
        a, b = number(z["top_md_m"]), number(z["bottom_md_m"])
        if not job["top_md_m"] <= a < b <= job["bottom_md_m"] or z["sku"] not in catalog:
            raise ValueError("Invalid SKU-assignment interval or unknown product")
    for i, a in enumerate(zones):
        for b in zones[i + 1 :]:
            if max(a["top_md_m"], b["top_md_m"]) < min(a["bottom_md_m"], b["bottom_md_m"]):
                raise ValueError("SKU-assignment intervals must not overlap")
    overrides = job.get("sku_overrides", [])
    if len({p["joint_no"] for p in overrides}) != len(overrides):
        raise ValueError("Duplicate per-joint SKU override")
    planned = placements(job, replace(primary, length_m=None))
    legal = {p["joint_no"] for p in planned}
    for p in overrides:
        if p["joint_no"] not in legal or p["sku"] not in catalog:
            raise ValueError("SKU override must reference a selected legal joint and known SKU")
    assignments = {}
    for p in planned:
        choice = primary.sku
        for z in zones:
            if z["top_md_m"] <= p["md_m"] < z["bottom_md_m"]:
                choice = z["sku"]
        for o in overrides:
            if o["joint_no"] == p["joint_no"]:
                choice = o["sku"]
        assignments.setdefault(choice, []).append(p["joint_no"])
    parts = []
    for sku, joints in assignments.items():
        # Includes/excludes were already applied when selecting legal positions.
        group = dict(job, custom_joints=joints, zones=[])
        parts.append(assess(group, catalog[sku]))
    result = parts[0].copy()
    result["placement"] = sorted(
        [p for r in parts for p in r["placement"]], key=lambda p: p["md_m"]
    )
    result["bom"] = [b for r in parts for b in r["bom"]]
    result["product_snapshot"] = asdict(catalog[next(iter(assignments))])
    result["product_snapshots"] = [asdict(catalog[k]) for k in assignments]
    result["compatibility"] = dict(
        status="Not suitable"
        if any(r["compatibility"]["blocking"] for r in parts)
        else ("Verify" if any(r["compatibility"]["review"] for r in parts) else "Suitable"),
        blocking=[
            f"{r['product_snapshot']['sku']}: {v}"
            for r in parts
            for v in r["compatibility"]["blocking"]
        ],
        review=[
            f"{r['product_snapshot']['sku']}: {v}"
            for r in parts
            for v in r["compatibility"]["review"]
        ],
        minimum_passage_m=min(r["compatibility"]["minimum_passage_m"] for r in parts),
    )
    result["reasons"] = list(dict.fromkeys(v for r in parts for v in r["reasons"]))
    if any(r["validity"] == "SYNTHETIC_DEMO" for r in parts):
        result["validity"] = "SYNTHETIC_DEMO"
        result["banner"] = DEMO
    elif any(r["validity"] == "REVIEW_REQUIRED" for r in parts):
        result["validity"] = "REVIEW_REQUIRED"
    for a, b in zip(result["placement"], result["placement"][1:]):
        la, lb = catalog[a["sku"]].length_m, catalog[b["sku"]].length_m
        if la is not None and lb is not None and a["md_m"] + la / 2 > b["md_m"] - lb / 2:
            raise ValueError("Adjacent mixed-SKU centralizer bodies overlap")
    # Merge identical retainer part numbers while preserving unknown pricing.
    merged = {}
    for row in result["bom"]:
        key = (row["sku"], row["description"])
        if key not in merged:
            merged[key] = row.copy()
        else:
            merged[key]["quantity"] += row["quantity"]
            if row["total"] is not None:
                merged[key]["total"] += row["total"]
    result["bom"] = list(merged.values())
    return result
