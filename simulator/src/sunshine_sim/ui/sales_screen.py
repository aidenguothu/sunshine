"""Additive R1 sales flow; previous simulation screens are preserved."""

import json
import math
from copy import deepcopy
from dataclasses import asdict
from importlib.resources import files
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from sunshine_sim.advisor.catalog import DEMO, dump_skus, import_sku_csv, load_skus
from sunshine_sim.advisor.engineering import FACTORS, hole_csv, survey_csv
from sunshine_sim.advisor.proposal import proposal_html, rfq_text
from sunshine_sim.advisor.service import assess_selection, compatibility, validate_job
from sunshine_sim.advisor.storage import bundle, save_local, unbundle
from sunshine_sim.reporting.csv_export import screening_csv

STORE = Path(__file__).resolve().parents[3] / ".local/advisor"


def resource(name):
    return files("sunshine_sim").joinpath(f"data/examples/{name}").read_text()


def render_sales_screen():
    st.subheader("Sunshine Centralizer Placement Advisor · 扶正器选型助手")
    st.caption(
        "Release 1 · product selection → joint placement → preliminary proposal. "
        "Runs locally without external services. No field-performance or "
        "standards-compliance claim."
    )
    if "sales_job" not in st.session_state:
        st.session_state.sales_job = json.loads(resource("sales_job.json"))
        st.session_state.sales_catalog = resource("sales_catalog.json")
        st.session_state.sales_revision = 0
    products = load_skus(st.session_state.sales_catalog)
    job = deepcopy(st.session_state.sales_job)
    rev = st.session_state.sales_revision
    selected_product = next((p for p in products if p.sku == job.get("selected_sku")), None)
    if job.get("data_origin") == "synthetic demo" or (selected_product and selected_product.demo):
        st.warning(DEMO)
    with st.expander("Open / save a job · 项目存档"):
        upload = st.file_uploader(
            "Open advisor snapshot JSON (job + SKU catalog)", type="json", key="sales-open"
        )
        if st.button("Load advisor snapshot"):
            try:
                if upload is None:
                    raise ValueError("Choose a saved advisor snapshot")
                loaded, skus = unbundle(upload.getvalue().decode())
                st.session_state.sales_job = loaded
                st.session_state.sales_catalog = dump_skus(skus)
                st.session_state.sales_revision += 1
                st.rerun()
            except (ValueError, UnicodeError) as exc:
                st.error(str(exc))
        slots = sorted(p.stem for p in STORE.glob("*.json")) if STORE.exists() else []
        selected_slot = st.selectbox("Saved workspace jobs", slots or ["No saved jobs"])
        if st.button("Open workspace job", disabled=not slots):
            try:
                loaded, skus = unbundle((STORE / f"{selected_slot}.json").read_text())
                st.session_state.sales_job = loaded
                st.session_state.sales_catalog = dump_skus(skus)
                st.session_state.sales_revision += 1
                st.rerun()
            except (ValueError, OSError) as exc:
                st.error(str(exc))
        st.caption(
            "Workspace saves persist across browser reloads. This is shared, single-workspace "
            "storage, not authenticated client storage. Download files for private portability."
        )
    units = st.radio("Input units / 单位", ["Metric", "Field"], horizontal=True, key="sales-units")
    # Preserve SI draft, but discard numeric widget caches when switching displayed units.
    if st.session_state.get("sales-last-units") != units:
        for k in list(st.session_state):
            if k.startswith(("a-input-", "sales-table-base-")):
                del st.session_state[k]
        st.session_state["sales-last-units"] = units
    depth_unit, diam_unit, mass_unit, density_unit = (
        ("m", "mm", "kg/m", "kg/m3") if units == "Metric" else ("ft", "in", "ppf", "ppg")
    )
    prefix = f"a-input-{rev}-{units}-"

    def entry(label, field, unit, optional=False):
        v = job.get(field)
        shown = 0.0 if v is None else v / FACTORS[unit]
        value = st.number_input(
            f"{label} ({unit})", value=float(shown), format="%.6f", key=prefix + field
        )
        job[field] = None if optional and value == 0 else value * FACTORS[unit]

    def convert(value, unit):
        return None if value is None else value * FACTORS[unit]

    def editor(data, *, key, **kwargs):
        # Stable source rows avoid re-applying added/deleted-row patches on every rerun.
        base_key = "sales-table-base-" + key
        if base_key not in st.session_state:
            st.session_state[base_key] = deepcopy(data)
        return st.data_editor(deepcopy(st.session_state[base_key]), key=key, **kwargs)

    tabs = st.tabs(
        [
            "1 · Well / 项目",
            "2 · Geometry & survey / 井身",
            "3 · Sunshine SKU / 产品",
            "4 · Joint placement / 布置",
            "5 · Results & proposal / 方案",
        ]
    )
    with tabs[0]:
        for label, key in [
            ("Job name", "job_name"),
            ("Customer (optional)", "customer"),
            ("Well name", "well_name"),
            ("Region", "region"),
            ("Revision", "revision"),
        ]:
            job[key] = st.text_input(label, value=job.get(key, ""), key=f"sales-{rev}-{key}")
        job["data_origin"] = st.selectbox(
            "Input origin / 数据来源",
            ["synthetic demo", "customer supplied", "user assumption"],
            index=["synthetic demo", "customer supplied", "user assumption"].index(
                job["data_origin"]
            ),
            key=f"origin-{rev}",
        )
        st.caption(
            "Changing the origin does not approve data or remove synthetic product warnings."
        )
        cols = st.columns(2)
        with cols[0]:
            entry("Interval top MD", "top_md_m", depth_unit)
        with cols[1]:
            entry("Interval bottom MD", "bottom_md_m", depth_unit)
    with tabs[1]:
        a, b = st.columns(2)
        with a:
            entry("Casing OD", "casing_od_m", diam_unit)
            entry("Casing ID (0 = unknown)", "casing_id_m", diam_unit, True)
            entry("Verified linear mass (0 = unknown)", "mass_kg_m", mass_unit, True)
        with b:
            entry("Fluid density", "fluid_density_kg_m3", density_unit)
            entry(
                "Previous casing / minimum passage ID (0 = unknown)",
                "previous_casing_id_m",
                diam_unit,
                True,
            )
            st.caption(
                "ID or verified mass is required. R1 does not calculate beam loads; the existing "
                "experimental models remain separate. Modulus is retained in saved inputs."
            )
        st.write(
            "Hole/caliper intervals — exact boundaries; no interpolation across a diameter step"
        )
        displayed = [
            dict(
                top_md_m=h["top_md_m"] / FACTORS[depth_unit],
                bottom_md_m=h["bottom_md_m"] / FACTORS[depth_unit],
                hole_id_m=h["hole_id_m"] / FACTORS[diam_unit],
                restriction_id_m=None
                if h.get("restriction_id_m") is None
                else h["restriction_id_m"] / FACTORS[diam_unit],
                source=h["source"],
            )
            for h in job["holes"]
        ]
        rows = editor(
            displayed,
            num_rows="dynamic",
            key=prefix + "holes",
            column_config={
                k: st.column_config.NumberColumn(label)
                for k, label in [
                    ("top_md_m", f"Top MD ({depth_unit})"),
                    ("bottom_md_m", f"Bottom MD ({depth_unit})"),
                    ("hole_id_m", f"Hole ID ({diam_unit})"),
                    ("restriction_id_m", f"Restriction ID ({diam_unit})"),
                ]
            },
        )
        job["holes"] = [
            dict(
                top_md_m=convert(r["top_md_m"], depth_unit),
                bottom_md_m=convert(r["bottom_md_m"], depth_unit),
                hole_id_m=convert(r["hole_id_m"], diam_unit),
                restriction_id_m=convert(r.get("restriction_id_m"), diam_unit),
                source=r.get("source", ""),
            )
            for r in rows
        ]
        with st.expander("Import hole / restriction intervals CSV"):
            hole_upload = st.file_uploader(
                "TopMD, BottomMD, HoleID, RestrictionID, Source", type="csv"
            )
            hole_depth_unit = st.selectbox("Hole CSV depth unit", ["m", "ft"])
            hole_diameter_unit = st.selectbox("Hole CSV diameter unit", ["mm", "in", "m"])
            if st.button("Import hole intervals"):
                try:
                    if hole_upload is None:
                        raise ValueError("Choose a hole CSV")
                    candidate = deepcopy(job)
                    candidate["holes"] = hole_csv(
                        hole_upload.getvalue().decode(), hole_depth_unit, hole_diameter_unit
                    )
                    validate_job(candidate)
                    st.session_state.sales_job = candidate
                    st.session_state.sales_revision += 1
                    st.rerun()
                except (ValueError, UnicodeError) as exc:
                    st.error(str(exc))
        survey_upload = st.file_uploader(
            "Survey CSV: MD, Inclination, Azimuth (degrees)", type="csv", key="advisor-survey"
        )
        survey_units = st.selectbox("Survey CSV depth unit (explicit)", ["m", "ft"])
        if st.button("Import survey CSV"):
            try:
                if survey_upload is None:
                    raise ValueError("Choose a survey CSV")
                job["survey"] = survey_csv(survey_upload.getvalue().decode(), survey_units)
                st.session_state.sales_job = job
                st.session_state.sales_revision += 1
                st.rerun()
            except (ValueError, UnicodeError) as exc:
                st.error(str(exc))
        st.caption(
            "Survey table is always stored/displayed in SI (m and degrees); import accepts m/ft. "
            "No survey extrapolation is used. Curvature is charted, not mechanically modeled."
        )
        job["survey"] = editor(job["survey"], num_rows="dynamic", key=f"sales-survey-{rev}")
        job["dls_warning_deg_30m"] = st.number_input(
            "DLS review threshold (°/30m; user criterion, not ISO)",
            value=float(job["dls_warning_deg_30m"]),
            min_value=0.0,
            key=f"dls-{rev}",
        )
    with tabs[2]:
        st.caption(
            "No real manufacturer-approved Sunshine SKU was supplied. Bundled "
            "products are fictional. "
            "Sales approval flags in imported files are company assertions, "
            "not authenticated certification."
        )
        catalog_upload = st.file_uploader(
            "Admin import: sales-1 JSON or supplied product CSV template",
            type=["json", "csv"],
            key="sales-catalog-upload",
        )
        if st.button("Load sales catalog"):
            try:
                if catalog_upload is None:
                    raise ValueError("Choose a catalog")
                text = catalog_upload.getvalue().decode()
                new = (
                    import_sku_csv(text)
                    if catalog_upload.name.lower().endswith(".csv")
                    else load_skus(text)
                )
                st.session_state.sales_catalog = dump_skus(new)
                st.session_state.sales_job = job
                st.session_state.sales_job["selected_sku"] = new[0].sku
                st.session_state.sales_revision += 1
                st.rerun()
            except (ValueError, UnicodeError) as exc:
                st.error(str(exc))
        ids = [p.sku for p in products]
        selected = st.selectbox(
            "Select SKU / 选择型号",
            ids,
            index=ids.index(job["selected_sku"]) if job["selected_sku"] in ids else 0,
            key=f"sales-sku-{rev}",
        )
        job["selected_sku"] = selected
        sku = next(p for p in products if p.sku == selected)
        if sku.demo:
            st.warning(DEMO)
        try:
            validate_job(job)
            fits = [
                dict(
                    SKU=p.sku,
                    Family=p.family,
                    Status=compatibility(job, p)["status"],
                    Notes="; ".join(
                        compatibility(job, p)["blocking"] + compatibility(job, p)["review"]
                    ),
                )
                for p in products
            ]
            st.dataframe(fits, hide_index=True)
        except (ValueError, KeyError, TypeError) as exc:
            st.error(str(exc))
        st.json(asdict(sku), expanded=False)
        st.caption(
            "Starting, running and restoring force are separate properties. "
            "A single restoring-force rating never creates a spring curve or standoff prediction."
        )
        st.download_button(
            "Download sales catalog JSON",
            dump_skus(products),
            "sunshine-sales-catalog.json",
            "application/json",
        )
    placement_input_error = False
    with tabs[3]:
        st.info(
            "Fixed patterns use actual joint numbers, not an estimated spacing distance. "
            "No target-standoff optimization is enabled in Release 1."
        )
        entry("Tally start MD", "joint_start_md_m", depth_unit)
        tally_rows = [
            dict(joint_no=i + 1, length=length / FACTORS[depth_unit])
            for i, length in enumerate(job["joint_lengths_m"])
        ]
        edited = editor(
            tally_rows,
            num_rows="dynamic",
            disabled=["joint_no"],
            key=prefix + "tally",
            column_config={
                "length": st.column_config.NumberColumn(f"Actual length ({depth_unit})")
            },
        )
        job["joint_lengths_m"] = [convert(r["length"], depth_unit) for r in edited]
        entry(
            "User-selected mounting offset (verify installation drawing)",
            "joint_offset_m",
            depth_unit,
        )
        entry("Beginning placement-window offset", "start_offset_m", depth_unit)
        entry("End placement-window offset", "end_offset_m", depth_unit)
        entry("Connection clearance", "connection_clearance_m", depth_unit)
        pattern = st.selectbox(
            "Pattern / 布置方式",
            ["Every joint", "Every 2 joints", "Every 3 joints", "Custom joint list"],
            index=3 if job["custom_joints"] is not None else job["pattern_every"] - 1,
            key=f"pattern-{rev}",
        )
        custom_text = st.text_input(
            "Custom joint numbers (comma-separated)",
            ",".join(map(str, job["custom_joints"] or [])),
            key=f"custom-{rev}",
        )
        try:
            job["custom_joints"] = (
                [int(v.strip()) for v in custom_text.split(",") if v.strip()]
                if pattern == "Custom joint list"
                else None
            )
            if pattern != "Custom joint list":
                job["pattern_every"] = ["Every joint", "Every 2 joints", "Every 3 joints"].index(
                    pattern
                ) + 1
        except ValueError:
            placement_input_error = True
            st.error("Custom joints must be integer numbers")
        st.caption(
            "Force include/exclude zones use SI measured depth (m), half-open [top,bottom). "
            "Include forces a unit at each legal joint position in that zone. "
            "Conflicting zones are rejected."
        )
        job["zones"] = editor(
            job["zones"] or [dict(kind="exclude", top_md_m=0.0, bottom_md_m=0.0)],
            num_rows="dynamic",
            key=f"zones-{rev}",
            column_config={
                "kind": st.column_config.SelectboxColumn(options=["include", "exclude"])
            },
        )
        job["zones"] = [
            z for z in job["zones"] if not (z.get("top_md_m") == 0 and z.get("bottom_md_m") == 0)
        ]
        st.caption(
            "Assign SKU by interval or selected joint; joint override takes precedence. "
            "SI MD intervals must not overlap. Products still undergo full passage checks."
        )
        job["sku_zones"] = editor(
            job.get("sku_zones") or [dict(top_md_m=0.0, bottom_md_m=0.0, sku=sku.sku)],
            num_rows="dynamic",
            key=f"sku-zones-{rev}",
            column_config={
                "sku": st.column_config.SelectboxColumn(options=[p.sku for p in products])
            },
        )
        job["sku_zones"] = [
            r
            for r in job["sku_zones"]
            if not (r.get("top_md_m") == 0 and r.get("bottom_md_m") == 0)
        ]
        job["sku_overrides"] = editor(
            job.get("sku_overrides") or [dict(joint_no=0, sku=sku.sku)],
            num_rows="dynamic",
            key=f"sku-overrides-{rev}",
            column_config={
                "sku": st.column_config.SelectboxColumn(options=[p.sku for p in products])
            },
        )
        job["sku_overrides"] = [r for r in job["sku_overrides"] if r.get("joint_no") != 0]
        job["target_ratio"] = (
            st.number_input(
                "Customer target (%) — context only; no meets-target claim",
                value=float(job["target_ratio"] * 100),
                min_value=0.0,
                max_value=100.0,
                key=f"target-{rev}",
            )
            / 100
        )
    st.session_state.sales_job = deepcopy(job)
    with tabs[4]:
        if placement_input_error:
            st.error("Correct custom joint numbers before generating results.")
        else:
            _results(job, sku, products, depth_unit)


def _results(job, sku, products, depth_unit):
    try:
        result = assess_selection(job, products)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        st.error(f"Cannot prepare a proposal: {exc}")
        return
    if result["validity"] == "SYNTHETIC_DEMO":
        st.warning(DEMO)
    fit = result["compatibility"]
    for reason in fit["blocking"]:
        st.error(reason)
    cards = st.columns(3)
    cards[0].metric("Centralizers / 扶正器", len(result["placement"]))
    cards[1].metric("Stop collars / 止动环", sum(p["stop_collar_qty"] for p in result["placement"]))
    cards[2].metric("Dimension status", fit["status"])
    st.caption(f"{result['methodology']} · {result['validity']}")
    _charts(job, result, depth_unit)
    st.write(
        "At centralizer: rigid wall-contact geometric estimate only. Between centralizers: "
        "not calculated. Bow standoff not calculable from available test data / load model in R1."
    )
    st.dataframe(result["placement"], hide_index=True)
    st.subheader("Bill of materials / 物料清单")
    st.dataframe(result["bom"], hide_index=True)
    for reason in result["reasons"]:
        st.caption("• " + reason)
    scenarios = []
    for k in (1, 2, 3):
        try:
            r = assess_selection(
                dict(job, pattern_every=k, custom_joints=None, sku_overrides=[]), products
            )
            scenarios.append(
                dict(
                    pattern=f"Every {k} joint(s)",
                    units=len(r["placement"]),
                    status=r["validity"],
                    standoff="Not optimized; no between-support prediction",
                )
            )
        except ValueError as exc:
            scenarios.append(dict(pattern=f"Every {k} joint(s)", status=str(exc)))
    st.dataframe(scenarios, hide_index=True)
    st.download_button(
        "Download installation CSV",
        screening_csv(
            [
                dict(p, validity=result["validity"], warning=result["banner"])
                for p in result["placement"]
            ]
        ),
        "sunshine-installation.csv",
        "text/csv",
    )
    st.download_button(
        "Download BOM CSV",
        screening_csv(
            [dict(b, validity=result["validity"], warning=result["banner"]) for b in result["bom"]]
        ),
        "sunshine-bom.csv",
        "text/csv",
    )
    from datetime import datetime, timezone

    st.download_button(
        "Download assessment JSON (inputs + results)",
        json.dumps(
            dict(created_at_utc=datetime.now(timezone.utc).isoformat(), job=job, result=result),
            indent=2,
            allow_nan=False,
        ),
        "sunshine-assessment.json",
        "application/json",
    )
    text = bundle(job, products)
    st.download_button(
        "Download complete advisor snapshot JSON",
        text,
        "sunshine-advisor-job.json",
        "application/json",
    )
    slot = st.text_input("Workspace save name (letters/numbers/hyphen/underscore)", "sales-demo")
    overwrite = st.checkbox("Replace this named workspace snapshot if it already exists")
    if st.button("Save job in workspace"):
        try:
            if (STORE / f"{slot}.json").exists() and not overwrite:
                raise ValueError("Choose a new name or explicitly allow replacement")
            save_local(STORE, slot, text)
            st.success("Saved. Reopen from Open / save a job after reload.")
        except (ValueError, OSError) as exc:
            st.error(str(exc))
    st.subheader("Customer proposal & Request Quote / 客户方案与询价")
    st.caption(
        "Contact information is optional and only included with your consent. "
        "No email is sent, and there is no external CRM or SaaS dependency."
    )
    with st.expander("Optional RFQ contact / delivery preferences"):
        contact = {
            name: st.text_input(name, key=f"rfq-{name}")
            for name in [
                "Contact name",
                "Company",
                "Country",
                "Email",
                "Incoterms",
                "Requested delivery date",
                "Notes",
            ]
        }
    consent = st.checkbox("Include these contact details in downloaded proposal/RFQ")
    account = st.text_input("Sunshine account manager contact (company-supplied)", "")
    included = contact if consent else {}
    if fit["blocking"]:
        st.error(
            "Customer proposal/RFQ is blocked by incompatible dimensions. "
            "Correct geometry or choose another SKU."
        )
    else:
        html = proposal_html(job, result, included, account)
        st.download_button(
            "Download proposal — open HTML, then Print / Save PDF",
            html,
            "sunshine-preliminary-proposal.html",
            "text/html",
        )
        rfq = rfq_text(job, result, included)
        st.download_button("Download non-binding RFQ text", rfq, "sunshine-rfq.txt", "text/plain")
        st.text_area("Copy RFQ text (nothing is sent automatically)", rfq, height=180)
    st.caption(result["disclaimer"])


def _charts(job, result, depth_unit):
    factor = FACTORS[depth_unit]
    fig = make_subplots(
        rows=1,
        cols=3,
        shared_yaxes=True,
        subplot_titles=["Inclination + placements", "Dogleg severity", "At-support geometry"],
    )
    survey = result["survey"]
    fig.add_trace(
        go.Scatter(
            x=[r["inclination_deg"] for r in survey],
            y=[r["md_m"] / factor for r in survey],
            name="Inclination (°)",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[r["dls_deg_30m"] for r in survey],
            y=[r["md_m"] / factor for r in survey],
            name="DLS (°/30m)",
        ),
        row=1,
        col=2,
    )
    plan = result["placement"]
    # Placement tick rail is not an extrapolated survey inclination.
    fig.add_trace(
        go.Scatter(
            x=[0] * len(plan),
            y=[p["md_m"] / factor for p in plan],
            mode="markers",
            marker=dict(symbol="line-ew", size=13, color="#07858a"),
            name="Placement MD",
            text=[f"Joint {p['joint_no']} · {p['sku']}" for p in plan],
            hovertemplate="%{text}<br>MD %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    numeric = [p for p in plan if p["at_support_geometric_sor"] is not None]
    if numeric:
        fig.add_trace(
            go.Scatter(
                x=[p["at_support_geometric_sor"] * 100 for p in numeric],
                y=[p["md_m"] / factor for p in numeric],
                mode="markers",
                name="Rigid geometric support SOR",
            ),
            row=1,
            col=3,
        )
    else:
        fig.add_annotation(
            text="No numeric standoff<br>available",
            xref="x3 domain",
            yref="y3 domain",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
    fig.update_yaxes(range=[job["bottom_md_m"] / factor, job["top_md_m"] / factor])
    fig.update_yaxes(title_text=f"Measured depth ({depth_unit})", row=1, col=1)
    fig.update_xaxes(title_text="Inclination (°)", row=1, col=1)
    fig.update_xaxes(title_text="°/30m", row=1, col=2)
    fig.update_xaxes(title_text="SOR (%)", range=[0, 100], row=1, col=3)
    fig.update_layout(
        height=530, template="plotly_white", margin=dict(t=70), legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig, use_container_width=True)
    if numeric:
        md = st.selectbox("Geometric section at placement MD (m)", [p["md_m"] for p in numeric])
        from sunshine_sim.advisor.service import hole_at

        hole = hole_at(job, md)["hole_id_m"] * 1000
        casing = job["casing_od_m"] * 1000
        rigid = (
            next(
                p
                for p in result.get("product_snapshots", [result["product_snapshot"]])
                if p["sku"] == next(r for r in numeric if r["md_m"] == md)["sku"]
            )["rigid_od_m"]
            * 1000
        )
        offset = (hole - rigid) / 2
        theta = [i * 2 * math.pi / 180 for i in range(181)]
        section = go.Figure()
        for name, r, center, color in [
            ("Hole", hole / 2, 0, "#bca67d"),
            ("Rigid OD", rigid / 2, offset, "#07858a"),
            ("Casing OD", casing / 2, offset, "#547186"),
        ]:
            section.add_trace(
                go.Scatter(
                    x=[center + r * math.cos(t) for t in theta],
                    y=[r * math.sin(t) for t in theta],
                    mode="lines",
                    name=name,
                    line_color=color,
                )
            )
        section.update_layout(
            height=350,
            title="Rigid wall-contact illustration — not a force prediction",
            template="plotly_white",
        )
        section.update_yaxes(scaleanchor="x", scaleratio=1, title="mm")
        section.update_xaxes(title="mm")
        st.plotly_chart(section, use_container_width=True)
