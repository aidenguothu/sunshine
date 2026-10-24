import json
from copy import deepcopy
from dataclasses import replace
from importlib.resources import files

import pytest

from sunshine_sim.advisor.catalog import DEMO, SalesSKU, dump_skus, load_skus
from sunshine_sim.advisor.engineering import (
    beam_sag,
    curve_sor,
    hole_csv,
    midspan_sor,
    rigid_sor,
    survey_csv,
    to_si,
)
from sunshine_sim.advisor.placement import placements
from sunshine_sim.advisor.proposal import proposal_html, rfq_text
from sunshine_sim.advisor.service import assess, compatibility, hole_at, validate_job
from sunshine_sim.advisor.storage import bundle, save_local, unbundle

BASE = files("sunshine_sim").joinpath("data/examples")
SKUS = load_skus(BASE.joinpath("sales_catalog.json").read_text())
JOB = json.loads(BASE.joinpath("sales_job.json").read_text())
RIGID, BOW = SKUS


def test_reference_geometry_sag_and_units():
    assert rigid_sor(0.2159, 0.1778, 0.205) == pytest.approx(0.7139107611548556)
    assert beam_sag(100, 10, 1e6) == pytest.approx(0.0130208333333)
    assert beam_sag(100, 20, 1e6) == pytest.approx(16 * beam_sag(100, 10, 1e6))
    assert beam_sag(0, 10, 1e6) == 0
    assert midspan_sor(1, 1, 0.01, 0.02) == 0.5
    assert midspan_sor(1, 1, 0.03, 0.02) == 0
    assert midspan_sor(None, 1, 0.01, 0.02) is None
    assert to_si(1, "in") == 0.0254
    assert to_si(1, "ft") == 0.3048
    assert to_si(1, "lbf") == 4.4482216152605
    assert to_si(10, "ppg") == pytest.approx(1198.264273)
    with pytest.raises(ValueError):
        to_si(1, "kgf")
    for dr in (0.17, 0.23):
        with pytest.raises(ValueError):
            rigid_sor(0.2159, 0.1778, dr)
    with pytest.raises(ValueError):
        rigid_sor(0.1778, 0.1778, 0.1778)


def test_measured_curve_no_fabrication():
    curve = [dict(load_n=0, sor=1), dict(load_n=1000, sor=0.7), dict(load_n=2000, sor=0.3)]
    assert curve_sor(curve, 500) == 0.85
    assert curve_sor(curve, 1500) == 0.5
    assert curve_sor(curve, 3000) is None
    assert curve_sor(curve[:1], 0) is None
    for bad in (
        [curve[0], curve[0]],
        [dict(load_n=0, sor=1.5), curve[1]],
        [dict(load_n=0, sor=0.3), dict(load_n=2, sor=0.7)],
    ):
        with pytest.raises(ValueError):
            curve_sor(bad, 1)


def test_survey_dls_wrap_and_field_equivalence():
    rows = survey_csv("MD,Inclination,Azimuth\n0,0,0\n300,90,0", "m")
    assert rows[1]["dls_deg_30m"] == pytest.approx(9)
    vertical = survey_csv("MD,Inclination,Azimuth\n0,0,0\n300,0,359", "m")
    assert vertical[1]["dls_deg_30m"] == 0
    wrap = survey_csv("MD,Inclination,Azimuth\n0,90,359\n30,90,1", "m")
    assert wrap[1]["dls_deg_30m"] == pytest.approx(2)
    field = survey_csv("MD,Inclination,Azimuth\n0,0,0\n984.251968503937,90,0", "ft")
    assert field[1]["md_m"] == pytest.approx(rows[1]["md_m"])
    assert field[1]["dls_deg_30m"] == pytest.approx(9)
    assert survey_csv("MD,Inclination,Azimuth\n0,180,360\n30,180,0", "m")[0]["azimuth_deg"] == 0


@pytest.mark.parametrize(
    "text,unit",
    [
        ("", "m"),
        ("MD,Inclination\n0,0", "m"),
        ("MD,Inclination,Azimuth\n0,0,0", "m"),
        ("MD,Inclination,Azimuth\n0,0,0\n0,0,0", "m"),
        ("MD,Inclination,Azimuth\n0,0,0\n30,190,0", "m"),
        ("MD,Inclination,Azimuth\n0,0,0\n30,0,inf", "m"),
        ("MD_m,Inclination,Azimuth\n0,0,0\n30,0,0", "ft"),
        ("MD,Inclination,Azimuth\n0,0,0\n30,0,0", "unknown"),
    ],
)
def test_invalid_survey(text, unit):
    with pytest.raises(ValueError):
        survey_csv(text, unit)


def test_hole_import_and_boundary_change():
    text = (
        "TopMD,BottomMD,HoleID,RestrictionID,Source\n"
        "900,1200,215.9,210,caliper\n1200,1500,250,210,caliper"
    )
    holes = hole_csv(text, "m", "mm")
    job = dict(JOB, holes=holes)
    assert hole_at(job, 1199)["hole_id_m"] == pytest.approx(0.2159)
    assert hole_at(job, 1200)["hole_id_m"] == 0.25
    assert hole_at(job, 1500)["hole_id_m"] == 0.25
    validate_job(job)
    with pytest.raises(ValueError):
        hole_csv("", "m", "mm")


def test_rigid_and_bow_restrictions():
    assert assess(JOB, RIGID)["placement"][0]["at_support_geometric_sor"] == pytest.approx(
        0.713910761
    )
    narrow = dict(JOB, previous_casing_id_m=0.2)
    assert compatibility(narrow, RIGID)["status"] == "Not suitable"
    assert (
        compatibility(JOB, BOW)["status"] == "Verify"
    )  # Free OD .222 > passage .21, compressed .188 passes.
    assert not compatibility(JOB, BOW)["blocking"]
    badbow = replace(BOW, compressed_od_m=0.211)
    assert compatibility(JOB, badbow)["blocking"]
    result = assess(JOB, BOW)
    assert all(p["at_support_geometric_sor"] is None for p in result["placement"])
    assert all(p["between_support_sor"] is None for p in result["placement"])
    assert not result["optimization_enabled"]
    with pytest.raises(ValueError):
        replace(RIGID, demo=False)
    with pytest.raises(ValueError):
        replace(RIGID, approved_for_customers=True)


def test_actual_joint_patterns_and_collars():
    job = deepcopy(JOB)
    job.update(top_md_m=900.0, bottom_md_m=1020.0, joint_lengths_m=[10, 14] * 5)
    counts = []
    for k in (1, 2, 3):
        job["pattern_every"] = k
        p = placements(job, BOW)
        counts.append(len(p))
        assert [r["joint_no"] for r in p] == list(range(1, 11, k))
    assert counts == [10, 5, 4]
    assert (
        placements(dict(job, pattern_every=2), BOW)[1]["md_m"] == 930
    )  # Joint 3 starts at 924, not 920.
    for n in (0, 1, 2):
        sku = replace(BOW, collars_per_unit=n)
        r = assess(JOB, sku)
        assert sum(p["stop_collar_qty"] for p in r["placement"]) == len(r["placement"]) * n


def test_custom_offsets_inclusions_exclusions_and_body_checks():
    job = deepcopy(JOB)
    job.update(
        custom_joints=[1, 2, 3],
        zones=[
            dict(kind="exclude", top_md_m=900.0, bottom_md_m=912.0),
            dict(kind="include", top_md_m=948.0, bottom_md_m=960.0),
        ],
    )
    assert [p["joint_no"] for p in placements(job, RIGID)] == [2, 3, 5]
    with pytest.raises(ValueError):
        placements(dict(job, custom_joints=[2, 2]), RIGID)
    with pytest.raises(ValueError):
        placements(dict(job, custom_joints=[999]), RIGID)
    with pytest.raises(ValueError):
        placements(
            dict(
                job,
                zones=[
                    dict(kind="include", top_md_m=900.0, bottom_md_m=920.0),
                    dict(kind="exclude", top_md_m=910.0, bottom_md_m=930.0),
                ],
            ),
            RIGID,
        )
    with pytest.raises(ValueError, match="connection"):
        placements(dict(JOB, joint_offset_m=0.1), replace(RIGID, length_m=0.5))
    out = placements(dict(JOB, start_offset_m=18.0, end_offset_m=18.0), RIGID)
    assert out[0]["md_m"] >= 918 and out[-1]["md_m"] <= 1482
    assert len({p["md_m"] for p in out}) == len(out)


def test_save_load_catalog_and_proposal_safety(tmp_path):
    text = bundle(JOB, SKUS)
    loaded, products = unbundle(text)
    assert loaded == JOB and products == SKUS
    save_local(tmp_path, "well-rev1", text)
    assert unbundle((tmp_path / "well-rev1.json").read_text())[0] == JOB
    with pytest.raises(ValueError):
        save_local(tmp_path, "../escape", text)
    result = assess(JOB, RIGID)
    html = proposal_html(
        dict(JOB, customer="<script>alert(1)</script>"),
        result,
        {},
        "Company contact required",
        "2026-10-24T00:00:00Z",
    )
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert html.count('<section class="page">') == 3
    assert DEMO in html
    assert "window.print()" in html and "Request Quote" in html
    assert "No cement isolation or run-to-bottom performance is guaranteed" in html
    assert "2026-10-24T00:00:00Z" in html
    assert "price" in html and "Not supplied" in html
    bowhtml = proposal_html(JOB, assess(JOB, BOW), {}, "")
    assert "geometric wall-contact SOR:" not in bowhtml
    assert (
        "width:" not in bowhtml.split("</style>")[1]
    )  # No fabricated numeric bow standoff graphic.
    assert "NON-BINDING" in rfq_text(JOB, result, {"Email": "user@example.test"})


def test_full_approved_schema_and_price_are_supplied_not_invented():
    sku = SalesSKU(
        "TEST-APPROVAL-FIXTURE",
        "Sunshine Petroleum",
        "rigid",
        0.1778,
        0.2159,
        0.2159,
        rigid_od_m=0.205,
        minimum_bore_m=0.18,
        length_m=0.3,
        collars_per_unit=0,
        collar_rule_reference="TEST ONLY installation fixture",
        demo=False,
        approved_for_customers=True,
        datasheet_reference="TEST ONLY fixture",
        revision="test",
    )
    result = assess(dict(JOB, data_origin="customer supplied"), sku)
    assert result["bom"][0]["unit_price"] is None
    assert result["compatibility"]["status"] == "Suitable"
    assert load_skus(dump_skus([sku]))[0] == sku
    with pytest.raises(ValueError):
        replace(sku, unit_price=12)
    priced = replace(sku, unit_price=12, currency="USD", price_reference="TEST ONLY company quote")
    assert assess(JOB, priced)["bom"][0]["total"] == 25 * 12


@pytest.mark.parametrize(
    "field,value",
    [
        ("casing_od_m", 0.3),
        ("casing_id_m", 0.19),
        ("fluid_density_kg_m3", -1),
        ("target_ratio", float("nan")),
        ("casing_od_m", None),
        ("mass_kg_m", float("inf")),
    ],
)
def test_invalid_job_numbers(field, value):
    with pytest.raises(ValueError):
        validate_job(dict(JOB, **{field: value}))


def test_incomplete_survey_marks_review_without_extrapolation():
    job = dict(
        JOB,
        survey=[
            dict(md_m=1000.0, inclination_deg=0.0, azimuth_deg=0.0),
            dict(md_m=1100.0, inclination_deg=0.0, azimuth_deg=0.0),
        ],
    )
    result = assess(job, RIGID)
    assert any("no extrapolation" in r for r in result["reasons"])


def test_mixed_product_intervals_overrides_bom_and_unknown_standoff():
    from sunshine_sim.advisor.service import assess_selection

    job = dict(
        JOB,
        sku_zones=[dict(top_md_m=1200.0, bottom_md_m=1500.0, sku=BOW.sku)],
        sku_overrides=[dict(joint_no=1, sku=BOW.sku)],
    )
    result = assess_selection(job, SKUS)
    assert len(result["placement"]) == 25
    assert result["placement"][0]["sku"] == BOW.sku
    assert result["placement"][0]["at_support_geometric_sor"] is None
    rigid = [p for p in result["placement"] if p["sku"] == RIGID.sku]
    assert all(p["at_support_geometric_sor"] is not None for p in rigid)
    assert len(result["product_snapshots"]) == 2
    assert sum(b["quantity"] for b in result["bom"] if b["description"] == "Centralizer") == 25
    assert next(
        b["quantity"] for b in result["bom"] if b["description"] == "Stop collar / retainer"
    ) == 2 * (25 - len(rigid))
    html = proposal_html(job, result, {}, "")
    assert RIGID.sku in html and BOW.sku in html and DEMO in html
    with pytest.raises(ValueError):
        assess_selection(dict(job, sku_overrides=[dict(joint_no=2, sku=BOW.sku)]), SKUS)


def test_dynamic_tally_rows_do_not_duplicate_on_rerun():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(
        str(__import__("pathlib").Path(__file__).parents[1] / "src/sunshine_sim/ui/app.py"),
        default_timeout=20,
    ).run()
    app.radio[0].set_value("Sunshine sales advisor / 选型助手").run()
    key = "a-input-0-Metric-tally"
    app.session_state[key] = {
        "edited_rows": {},
        "added_rows": [{"length": 12.0}],
        "deleted_rows": [],
    }
    app.run()
    assert len(app.session_state["sales_job"]["joint_lengths_m"]) == 51
    app.run()
    assert len(app.session_state["sales_job"]["joint_lengths_m"]) == 51
