"""Actual-joint placement patterns, not distance-based or standoff optimization."""

from sunshine_sim.advisor.engineering import number


def joint_tally(start, lengths):
    start = number(start, "Joint start MD", 0)
    if not 1 <= len(lengths) <= 10000:
        raise ValueError("Provide 1–10000 actual joint lengths")
    result = []
    for i, length in enumerate(lengths, 1):
        if number(length, "Joint length") <= 0:
            raise ValueError("Joint lengths must be positive")
        result.append(dict(joint_no=i, start_md_m=start, end_md_m=start + length))
        start += length
    return result


def placements(job, sku):
    tally = joint_tally(job["joint_start_md_m"], job["joint_lengths_m"])
    top, bottom = number(job["top_md_m"]), number(job["bottom_md_m"])
    if not 0 <= top < bottom or tally[0]["start_md_m"] > top or tally[-1]["end_md_m"] < bottom:
        raise ValueError("Actual joint tally must cover the positive analysis interval")
    k = job["pattern_every"]
    if type(k) is not int or k not in (1, 2, 3):
        raise ValueError("Pattern must be every 1, 2 or 3 joints")
    offset = number(job["joint_offset_m"], "Within-joint offset", 0)
    startoff = number(job.get("start_offset_m", 0), "Beginning offset", 0)
    endoff = number(job.get("end_offset_m", 0), "End offset", 0)
    if top + startoff > bottom - endoff:
        raise ValueError("Beginning/end offsets leave no placement window")
    zones = job.get("zones", [])
    for z in zones:
        a, b = number(z["top_md_m"]), number(z["bottom_md_m"])
        if a >= b or a < top or b > bottom or z["kind"] not in ("include", "exclude"):
            raise ValueError("Invalid inclusion/exclusion zone")
    for a in zones:
        for b in zones:
            if a["kind"] != b["kind"] and max(a["top_md_m"], b["top_md_m"]) < min(
                a["bottom_md_m"], b["bottom_md_m"]
            ):
                raise ValueError("Conflicting include/exclude zones")
    custom = job.get("custom_joints")
    legal_ids = {j["joint_no"] for j in tally}
    if custom is not None and (
        any(type(v) is not int or v not in legal_ids for v in custom)
        or len(custom) != len(set(custom))
    ):
        raise ValueError("Custom joint numbers must be unique and exist in the tally")
    # Anchor k-pattern to first candidate joint inside the placement interval.
    legal = [
        j
        for j in tally
        if top + startoff <= j["start_md_m"] + offset <= bottom - endoff
        and j["start_md_m"] + offset < j["end_md_m"]
    ]
    if not legal:
        raise ValueError("No legal joints for the selected offset/window")
    first = legal[0]["joint_no"]
    result = []
    for j in legal:
        md = j["start_md_m"] + offset
        selected = (
            j["joint_no"] in custom if custom is not None else (j["joint_no"] - first) % k == 0
        )
        included = any(
            z["kind"] == "include" and z["top_md_m"] <= md < z["bottom_md_m"] for z in zones
        )
        excluded = any(
            z["kind"] == "exclude" and z["top_md_m"] <= md < z["bottom_md_m"] for z in zones
        )
        if (selected or included) and not excluded:
            if sku.length_m is not None:
                clearance = number(job.get("connection_clearance_m", 0), "Connection clearance", 0)
                if (
                    md - sku.length_m / 2 < j["start_md_m"] + clearance
                    or md + sku.length_m / 2 > j["end_md_m"] - clearance
                ):
                    raise ValueError(
                        f"Centralizer crosses connection/clearance at joint {j['joint_no']}"
                    )
                if md - sku.length_m / 2 < top or md + sku.length_m / 2 > bottom:
                    raise ValueError("Centralizer body crosses analysis interval")
                for z in zones:
                    if z["kind"] == "exclude" and max(md - sku.length_m / 2, z["top_md_m"]) < min(
                        md + sku.length_m / 2, z["bottom_md_m"]
                    ):
                        raise ValueError(
                            f"Centralizer body overlaps exclusion at joint {j['joint_no']}"
                        )
            result.append(
                dict(
                    joint_no=j["joint_no"],
                    md_m=md,
                    sku=sku.sku,
                    stop_collar_qty=sku.collars_per_unit,
                    instruction=f"Joint {j['joint_no']}: mount at {offset:g} m from joint start; "
                    "verify connection/collar clearances against installation drawing.",
                )
            )
    if not result:
        raise ValueError("No centralizers remain after placement constraints")
    if sku.length_m:
        if any(b["md_m"] - a["md_m"] < sku.length_m for a, b in zip(result, result[1:])):
            raise ValueError("Centralizer bodies overlap")
    return result
