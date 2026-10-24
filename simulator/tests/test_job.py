import json
from copy import deepcopy
from importlib.resources import files

import pytest

from sunshine_sim.data.catalog import load_catalog
from sunshine_sim.engine.job import simulate_job
from sunshine_sim.ui.job_screen import regular_layout

PRODUCTS = load_catalog(
    files("sunshine_sim").joinpath("data/examples/demo_catalog.json").read_text()
)
DEMO = json.loads(files("sunshine_sim").joinpath("data/examples/demo_job.json").read_text())


def test_demo_bound_profile_and_equilibrium():
    r = simulate_job(DEMO, PRODUCTS)
    assert r["status"] == "screen_complete"
    assert len(r["spans"]) == 8
    assert 0 < r["minimum_standoff_lower_bound"] < 1
    for s in r["spans"]:
        points = [p for p in r["profile"] if s["start_md_m"] <= p["md_m"] <= s["end_md_m"]]
        assert min(p["standoff_ratio"] for p in points) >= s["standoff_lower_bound"] - 1e-12
    # Total support load equals integrated transverse weight for both casing sections.
    from sunshine_sim.engine.models import CasingSpec
    from sunshine_sim.engine.span import SpanCase, solve_span

    total = 0
    for s in DEMO["casing_sections"]:
        beam = solve_span(CasingSpec(**s["casing"]), SpanCase(0.2159, 3, 60, 1200, 1200))
        total += beam.lateral_load_n_m * (s["end_md_m"] - s["start_md_m"])
    assert sum(s["reaction_n"] for s in r["supports"]) == pytest.approx(total)
    # Interior supports share two span loads; first section has uniform spans.
    assert r["supports"][1]["reaction_n"] == pytest.approx(2 * r["supports"][0]["reaction_n"])
    json.dumps(r, allow_nan=False)


def test_mixed_products_affect_adjacent_spans():
    job = deepcopy(DEMO)
    r = simulate_job(job, PRODUCTS)
    job["placements"][1]["product_id"] = "DEMO-A"
    mixed = simulate_job(job, PRODUCTS)
    assert mixed["supports"][1]["offset_m"] > r["supports"][1]["offset_m"]
    assert mixed["spans"][0]["standoff_lower_bound"] < r["spans"][0]["standoff_lower_bound"]
    assert mixed["spans"][3] == r["spans"][3]


def test_layouts_and_no_false_success():
    job = deepcopy(DEMO)
    job["placements"] = regular_layout(job, 12, "DEMO-A")
    r = simulate_job(job, PRODUCTS)
    assert r["minimum_standoff_lower_bound"] is None
    assert r["status"] != "screen_complete"
    assert any(s["standoff_lower_bound"] is None for s in r["spans"])
    with pytest.raises(ValueError, match="test-hole"):
        job["placements"] = regular_layout(job, 4, "DEMO-B")
        simulate_job(job, PRODUCTS)


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda j: j["survey"][1].update(inclination_deg=61), "Curved"),
        (lambda j: j["survey"][1].update(azimuth_deg=10), "Curved"),
        (lambda j: j["placements"][1].update(md_m=1000), "strictly"),
        (lambda j: j["placements"][0].update(md_m=999), "boundaries"),
        (lambda j: j["placements"][1].update(product_id="UNKNOWN"), "Unknown"),
        (lambda j: j["caliper"][0].update(md_m=1001), "cover"),
        (lambda j: j["caliper"][1].update(hole_diameter_m=0.1), "diameter"),
        (lambda j: j["casing_sections"][1].update(start_md_m=1013), "contiguous"),
        (lambda j: j["placements"].pop(4), "boundary"),
        (lambda j: j["caliper"][1].update(hole_diameter_m=float("nan")), "finite"),
    ],
)
def test_job_rejects_invalid_inputs(mutation, match):
    j = deepcopy(DEMO)
    mutation(j)
    with pytest.raises(ValueError, match=match):
        simulate_job(j, PRODUCTS)


def test_per_joint_envelopes_and_unsupported_structure():
    result = simulate_job(DEMO, PRODUCTS)
    assert len(result["joints"]) == 2
    assert result["joints"][0]["standoff_lower_bound"] == min(
        s["standoff_lower_bound"] for s in result["spans"] if s["end_md_m"] <= 1012
    )
    for invalid in ({}, dict(DEMO, placements=[]), dict(DEMO, survey=[{}])):
        with pytest.raises(ValueError):
            simulate_job(invalid, PRODUCTS)
