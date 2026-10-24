import json
from dataclasses import replace
from importlib.resources import files

import pytest

from sunshine_sim.data.catalog import dump_catalog, load_catalog
from sunshine_sim.engine.models import CasingSpec, ForceDeflectionPoint
from sunshine_sim.engine.product import solve_product_span
from sunshine_sim.engine.span import SpanCase

DEMO = files("sunshine_sim").joinpath("data/examples/demo_catalog.json").read_text()
PRODUCTS = load_catalog(DEMO)
CASING = CasingSpec(0.1778, 0.1571, 200 / 9.80665, "TEST")
CASE = SpanCase(0.2159, 2, 90, 0, 0)


def test_inverse_curve_and_superposition():
    # q=200 N/m and L=2 m: each isolated support carries exactly 200 N.
    # DEMO-A is 150000 N/m, so each end settles by 200/150000 m.
    r = solve_product_span(CASING, CASE, PRODUCTS[0])
    assert r.support_offset_m == pytest.approx(200 / 150000)
    assert r.ideal_beam.end_reaction_n == pytest.approx(200)
    expected = 1 - (200 / 150000 + r.ideal_beam.maximum_free_sag_m) / 0.01905
    assert r.minimum_standoff_ratio == pytest.approx(expected)
    assert r.standoff_ratios[0] == pytest.approx(1 - 200 / 150000 / 0.01905)
    assert r.standoff_ratios[50] == pytest.approx(expected)
    stronger = solve_product_span(CASING, CASE, PRODUCTS[1])
    assert stronger.support_offset_m == pytest.approx(r.support_offset_m / 2)
    assert stronger.minimum_standoff_ratio > r.minimum_standoff_ratio
    assert stronger.minimum_standoff_ratio <= stronger.ideal_beam.minimum_standoff_ratio


def test_nonlinear_piecewise_inverse_and_exact_endpoint():
    points = (
        ForceDeflectionPoint(0, 0),
        ForceDeflectionPoint(0.005, 100),
        ForceDeflectionPoint(0.015, 500),
    )
    p = replace(PRODUCTS[0], spec=replace(PRODUCTS[0].spec, restoring_curve=points))
    r = solve_product_span(CASING, CASE, p)
    assert r.support_offset_m == pytest.approx(0.0075)
    r = solve_product_span(replace(CASING, mass_per_length_kg_m=500 / 9.80665), CASE, p)
    assert r.support_offset_m == pytest.approx(0.015)


def test_no_extrapolation_and_wall_contact():
    r = solve_product_span(replace(CASING, mass_per_length_kg_m=10000), CASE, PRODUCTS[0])
    assert r.status == "required_force_outside_measured_curve"
    assert r.minimum_standoff_ratio is None
    # Very soft support curves can reach wall contact even if the ideal beam passes.
    points = (ForceDeflectionPoint(0, 0), ForceDeflectionPoint(0.01905, 200))
    p = replace(PRODUCTS[0], spec=replace(PRODUCTS[0].spec, restoring_curve=points))
    r = solve_product_span(CASING, CASE, p)
    assert r.ideal_beam.minimum_standoff_ratio > 0
    assert r.status == "predicted_wall_contact"
    assert r.standoff_ratios is None


def test_vertical_supports_remain_centered():
    r = solve_product_span(CASING, replace(CASE, inclination_deg=0), PRODUCTS[0])
    assert r.support_offset_m == 0
    assert r.minimum_standoff_ratio == 1


def test_no_hole_or_casing_rescaling():
    with pytest.raises(ValueError, match="test hole"):
        solve_product_span(CASING, replace(CASE, hole_diameter_m=0.22), PRODUCTS[0])
    with pytest.raises(ValueError, match="casing OD"):
        solve_product_span(replace(CASING, outer_diameter_m=0.18), CASE, PRODUCTS[0])


def test_catalog_roundtrip_and_metadata_do_not_change_physics():
    assert load_catalog(dump_catalog(PRODUCTS)) == PRODUCTS
    p = replace(
        PRODUCTS[0],
        spec=replace(
            PRODUCTS[0].spec,
            starting_force_n=9999,
            running_force_n=8888,
            free_outer_diameter_m=0.24,
        ),
    )
    a = solve_product_span(CASING, CASE, p)
    b = solve_product_span(CASING, CASE, PRODUCTS[0])
    assert a.minimum_standoff_ratio == b.minimum_standoff_ratio


@pytest.mark.parametrize(
    "change",
    [
        {"curve_basis": "individual_bow_compression"},
        {"data_status": "certified"},
        {"test_conditions": ""},
    ],
)
def test_invalid_curve_provenance(change):
    with pytest.raises(ValueError):
        replace(PRODUCTS[0], **change)


def test_reject_non_monotonic_or_unsupported_curves():
    for points in [
        (ForceDeflectionPoint(0, 1), ForceDeflectionPoint(0.01, 200)),
        (
            ForceDeflectionPoint(0, 0),
            ForceDeflectionPoint(0.005, 100),
            ForceDeflectionPoint(0.01, 50),
        ),
        (ForceDeflectionPoint(0, 0), ForceDeflectionPoint(0.02, 500)),
    ]:
        with pytest.raises(ValueError):
            replace(PRODUCTS[0], spec=replace(PRODUCTS[0].spec, restoring_curve=points))
    with pytest.raises(ValueError):
        replace(PRODUCTS[0], spec=replace(PRODUCTS[0].spec, kind="rigid"))


@pytest.mark.parametrize(
    "text", ["{}", "[]", "{", '{"schema_version":"bad"}', '{"schema_version":"0.3","products":[]}']
)
def test_malformed_catalog(text):
    with pytest.raises(ValueError):
        load_catalog(text)


def test_duplicate_catalog_ids():
    data = json.loads(DEMO)
    data["products"][1] = data["products"][0]
    with pytest.raises(ValueError, match="unique"):
        load_catalog(json.dumps(data))


def test_csv_export_retains_flags_and_neutralizes_formulas():
    import csv
    import io

    from sunshine_sim.reporting.csv_export import screening_csv

    text = screening_csv(
        [{"Product": "=HYPERLINK(bad)", "Standoff": None, "Status": "UNVALIDATED"}]
    )
    row = list(csv.DictReader(io.StringIO(text)))[0]
    assert row["Product"].startswith("'=")
    assert row["Standoff"] == ""
    assert row["Status"] == "UNVALIDATED"
