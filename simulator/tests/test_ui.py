from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "src/sunshine_sim/ui/app.py"


def test_geometry_and_beam_modes():
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.metric[0].value == "73.75%"
    app.radio[0].set_value("Ideal-support beam & spacing").run()
    assert not app.exception
    assert not app.error
    assert app.dataframe
    assert app.success
    # Increase span to force contact; no physical standoff should be presented.
    app.number_input[5].set_value(12.0).run()
    assert not app.exception
    assert "wall_contact" in app.error[0].value
    assert all(metric.label != "Minimum ideal-support standoff" for metric in app.metric)
    app.text_input[0].set_value("3, broken").run()
    assert app.error
    assert not app.exception


def test_product_comparison_and_editor():
    app = AppTest.from_file(str(APP)).run()
    app.radio[0].set_value("Product catalog & comparison").run()
    assert not app.exception
    assert not app.error
    assert len(app.dataframe) == 2
    # Synthetic stronger support must display greater standoff at identical span.
    rows = app.dataframe[1].value
    at_four = rows[rows["Span (m)"] == 4]
    assert at_four.iloc[1]["Min standoff (%)"] > at_four.iloc[0]["Min standoff (%)"]
    # Save an edited ID; the new product must be present and marked unverified.
    editor_id = next(w for w in app.text_input if w.label.startswith("Product ID"))
    editor_id.set_value("USER-TEST")
    next(b for b in app.button if b.label == "Save product to this session").click().run()
    assert not app.exception
    assert "USER-TEST" in app.selectbox[0].options
    assert "user_supplied_unverified" in app.session_state["catalog_json"]
    next(w for w in app.number_input if w.label == "Hole diameter (mm)").set_value(220).run()
    assert app.error
    assert not app.exception


def test_job_planner_run_and_candidate_comparison():
    app = AppTest.from_file(str(APP)).run()
    app.radio[0].set_value("Job placement planner").run()
    assert not app.exception
    next(b for b in app.button if b.label == "Run current placement").click().run()
    assert not app.exception
    assert not app.error
    assert app.metric[0].label == "Conservative interval standoff lower bound"
    assert len(next(d.value for d in app.dataframe if "reaction_n" in d.value.columns)) == 9
    next(
        b for b in app.button if b.label == "Compare regular layouts for all catalog products"
    ).click().run()
    assert not app.exception
    assert app.success

    # Results survive reruns, and input changes mark saved comparisons stale.
    app.run()
    assert app.success
    next(w for w in app.number_input if w.label.startswith("Illustrative target (%)")).set_value(
        80
    ).run()
    assert any("Recompare" in w.value for w in app.warning)


def test_sales_advisor_patterns_units_and_unknown_bow():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.radio[0].set_value("Sunshine sales advisor / 选型助手").run()
    assert not app.exception and not app.error
    assert app.metric[0].value == "25"
    next(s for s in app.selectbox if s.label == "Pattern / 布置方式").set_value("Every joint").run()
    assert app.metric[0].value == "50"
    next(r for r in app.radio if r.label == "Input units / 单位").set_value("Field").run()
    assert not app.exception and not app.error
    assert app.metric[0].value == "50"
    next(r for r in app.radio if r.label == "Input units / 单位").set_value("Metric").run()
    assert not app.exception and not app.error
    next(s for s in app.selectbox if s.label == "Select SKU / 选择型号").set_value(
        "DEMO-BOW-7x8.5"
    ).run()
    assert not app.exception and not app.error
    assert app.metric[1].value == "100"
    frame = next(d.value for d in app.dataframe if "at_support_geometric_sor" in d.value.columns)
    assert frame["at_support_geometric_sor"].isna().all()
    next(s for s in app.selectbox if s.label == "Pattern / 布置方式").set_value(
        "Custom joint list"
    ).run()
    next(
        w for w in app.text_input if w.label == "Custom joint numbers (comma-separated)"
    ).set_value("bad").run()
    assert app.error
    assert not app.exception


def test_sales_mixed_catalog_plan_ui():
    import json
    from copy import deepcopy
    from importlib.resources import files

    job = json.loads(files("sunshine_sim").joinpath("data/examples/sales_job.json").read_text())
    job["sku_zones"] = [dict(top_md_m=1200.0, bottom_md_m=1500.0, sku="DEMO-BOW-7x8.5")]
    job["sku_overrides"] = [dict(joint_no=1, sku="DEMO-BOW-7x8.5")]
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    app.session_state["sales_job"] = deepcopy(job)
    app.session_state["sales_catalog"] = (
        files("sunshine_sim").joinpath("data/examples/sales_catalog.json").read_text()
    )
    app.session_state["sales_revision"] = 0
    app.radio[0].set_value("Sunshine sales advisor / 选型助手").run()
    assert not app.exception and not app.error
    assert app.metric[0].value == "25"
    assert app.metric[1].value == "26"
