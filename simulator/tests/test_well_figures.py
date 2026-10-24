import json
from copy import deepcopy
from importlib.resources import files

import pytest

from sunshine_sim.data.catalog import load_catalog
from sunshine_sim.engine.job import simulate_job
from sunshine_sim.ui.well_figures import cross_section, depth_tracks, offset_at

JOB = json.loads(files("sunshine_sim").joinpath("data/examples/demo_job.json").read_text())
PRODUCTS = load_catalog(
    files("sunshine_sim").joinpath("data/examples/demo_catalog.json").read_text()
)


def test_depth_alignment_and_units():
    result = simulate_job(JOB, PRODUCTS)
    fig = depth_tracks(JOB, result, 67.0, 1012.0)
    for axis in ("yaxis", "yaxis2", "yaxis3", "yaxis4"):
        assert list(fig.layout[axis].range) == [1024.0, 1000.0]
    assert fig.layout.xaxis2.title.text == "Diameter (mm)"
    caliper = next(t for t in fig.data if t.name == "Caliper")
    assert max(caliper.x) == pytest.approx(225.0)
    support = next(t for t in fig.data if t.name == "DEMO-B" and t.xaxis == "x4")
    assert support.x[0] == pytest.approx(result["supports"][0]["reaction_n"] / 1000)
    assert sum(t.name == "Sampled standoff" for t in fig.data) == 8
    design = depth_tracks(JOB)
    assert design.layout.xaxis2.title.text == "Diameter (mm)"
    assert not any(t.xaxis in ("x3", "x4") for t in design.data)


def test_cross_section_keeps_true_aspect_and_geometry():
    result = simulate_job(JOB, PRODUCTS)
    ratio = offset_at(result, 1012.0)
    fig = cross_section(JOB, result, 1012.0)
    assert fig.layout.yaxis.scaleanchor == "x"
    hole, casing = fig.data[:2]
    assert max(hole.x) == pytest.approx(107.95)
    gap = fig.data[-1].x[1] - fig.data[-1].x[0]
    assert gap == pytest.approx(ratio * (215.9 - 177.8) / 2)
    assert max(casing.x) < max(hole.x)


def test_invalid_spans_are_not_drawn_as_valid_geometry():
    job = deepcopy(JOB)
    job["placements"] = [dict(md_m=d, product_id="DEMO-A") for d in [1000.0, 1012.0, 1024.0]]
    result = simulate_job(job, PRODUCTS)
    assert result["minimum_standoff_lower_bound"] is None
    assert offset_at(result, 1006.0) is None
    assert cross_section(job, result, 1006.0) is None
    fig = depth_tracks(job, result)
    assert not any((t.name or "").startswith("Section") for t in fig.data)
    assert fig.layout.shapes  # invalid spans/target bands are visible
