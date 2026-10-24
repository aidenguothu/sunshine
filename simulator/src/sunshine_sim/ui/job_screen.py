"""Job-oriented placement editor. All results remain unvalidated screening."""

import json
from dataclasses import asdict
from importlib.resources import files

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from sunshine_sim.data.catalog import load_catalog
from sunshine_sim.engine.job import simulate_job
from sunshine_sim.reporting.csv_export import screening_csv


def regular_layout(job, spacing, product_id):
    start = job["casing_sections"][0]["start_md_m"]
    end = job["casing_sections"][-1]["end_md_m"]
    if not np.isfinite(spacing) or spacing <= 0 or (end - start) / spacing > 1000:
        raise ValueError("Spacing must be positive and generate no more than 1000 supports")
    depths = sorted(
        set(
            [float(v) for v in np.arange(start, end, spacing)]
            + [end]
            + [s["start_md_m"] for s in job["casing_sections"]]
        )
    )
    return [dict(md_m=v, product_id=product_id) for v in depths]


def render_job_screen():
    st.info(
        "Job planner: edit inputs, assign products at measured depths, then run. "
        "Only a straight, constant-inclination/azimuth interval is supported. "
        "Pin-connected spans share support loads; continuous casing moments are not solved."
    )
    demo = files("sunshine_sim").joinpath("data/examples/demo_job.json").read_text()
    catalog_text = st.session_state.get(
        "catalog_json",
        files("sunshine_sim").joinpath("data/examples/demo_catalog.json").read_text(),
    )
    products = load_catalog(catalog_text)
    ids = [p.spec.product_id for p in products]
    if "job_source" not in st.session_state:
        st.session_state.job_source = json.loads(demo)
        st.session_state.job_revision = 0
    upload = st.file_uploader("Import saved job JSON (schema 0.4)", type="json")
    if st.button("Load uploaded job"):
        try:
            if upload is None or upload.size > 1_000_000:
                raise ValueError("Select a JSON job smaller than 1 MB")
            source = json.loads(upload.getvalue())
            if source.get("schema_version") != "0.4":
                raise ValueError("Unsupported schema")
            # Require valid structure and compatible products before replacing the editor state.
            simulate_job(source, products)
            st.session_state.job_source = source
            st.session_state.job_revision += 1
        except (ValueError, AttributeError) as exc:
            st.error(str(exc))
    if st.button("Reset to synthetic demo"):
        st.session_state.job_source = json.loads(demo)
        st.session_state.job_revision += 1
    job = json.loads(json.dumps(st.session_state.job_source))
    rev = st.session_state.job_revision
    st.caption(
        "Demo: 1000–1024 m MD, two casing sections, 60° inclination, synthetic caliper "
        "washouts, bow-spring supports. No wellsite or certified product data."
    )
    with st.expander("1 · Casing string (SI units)", expanded=True):
        flat = [
            dict(start_md_m=s["start_md_m"], end_md_m=s["end_md_m"], **s["casing"])
            for s in job["casing_sections"]
        ]
        rows = st.data_editor(flat, num_rows="dynamic", key=f"casing-{rev}")
        job["casing_sections"] = [
            dict(
                start_md_m=r["start_md_m"],
                end_md_m=r["end_md_m"],
                casing={k: v for k, v in r.items() if k not in ("start_md_m", "end_md_m")},
            )
            for r in rows
        ]
    with st.expander("2 · Survey and caliper (MD in m; diameter in m)"):
        job["survey"] = st.data_editor(job["survey"], num_rows="dynamic", key=f"survey-{rev}")
        job["caliper"] = st.data_editor(job["caliper"], num_rows="dynamic", key=f"caliper-{rev}")
        st.caption(
            "Nonconstant survey angles are rejected. Hole-size changes at support locations "
            "require product curves tested at those exact hole sizes."
        )
        job["internal_density_kg_m3"] = st.number_input(
            "Internal fluid density (kg/m³)", value=job["internal_density_kg_m3"], key=f"ri-{rev}"
        )
        job["external_density_kg_m3"] = st.number_input(
            "External fluid density (kg/m³)", value=job["external_density_kg_m3"], key=f"ro-{rev}"
        )
    st.subheader("3 · Place centralizers")
    st.caption(
        "Edit MD and product per row. Include both end supports and casing-section boundaries. "
        "Create/edit products in Product catalog & comparison first."
    )
    selected = st.selectbox("Product for generated layouts", ids)
    spacing = st.number_input("Generate nominal spacing (m)", value=3.0, min_value=0.1)
    if st.button("Generate placement rows"):
        try:
            job["placements"] = regular_layout(job, spacing, selected)
            st.session_state.job_source = job
            st.session_state.job_revision += 1
            st.rerun()
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            st.error(str(exc))
    job["placements"] = st.data_editor(
        job["placements"],
        num_rows="dynamic",
        column_config={
            "product_id": st.column_config.SelectboxColumn("Product", options=ids, required=True)
        },
        key=f"placements-{rev}",
    )
    target = st.number_input(
        "Illustrative target (%) — engineer-defined", value=67.0, min_value=0.0, max_value=100.0
    )
    st.subheader("4 · Run or compare candidate layouts")
    candidates = st.text_input("Nominal spacing candidates (m)", "3, 6, 12")
    if st.button("Compare regular layouts for all catalog products"):
        try:
            values = [float(v) for v in candidates.split(",")]
            if not 1 <= len(values) <= 20 or len(products) > 20:
                raise ValueError("Compare at most 20 spacings and 20 products")
            comparison = []
            for product in products:
                for value in values:
                    record = dict(
                        product_id=product.spec.product_id,
                        spacing_m=value,
                        data_status=product.data_status,
                        review_status="UNVALIDATED — demonstration only",
                    )
                    try:
                        candidate = dict(
                            job, placements=regular_layout(job, value, product.spec.product_id)
                        )
                        result = simulate_job(candidate, products)
                        bound = result["minimum_standoff_lower_bound"]
                        record.update(
                            support_count=len(candidate["placements"]),
                            lower_bound_percent=None if bound is None else 100 * bound,
                            meets_target=bound is not None and bound >= target / 100,
                            status=result["status"],
                        )
                    except ValueError as exc:
                        record.update(meets_target=False, status=str(exc))
                    comparison.append(record)
            st.session_state.layout_comparison = dict(
                rows=comparison,
                input=job,
                catalog=catalog_text,
                target=target,
                candidates=candidates,
            )
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            st.error(str(exc))
    stored_comparison = st.session_state.get("layout_comparison")
    if stored_comparison:
        comparison = stored_comparison["rows"]
        if (
            stored_comparison["input"] != job
            or stored_comparison["catalog"] != catalog_text
            or stored_comparison["target"] != target
            or stored_comparison["candidates"] != candidates
        ):
            st.warning(
                "Layout comparison inputs changed. Recompare before using these saved results."
            )
        st.dataframe(comparison, hide_index=True)
        passed = [r for r in comparison if r["meets_target"]]
        if passed:
            best = min(passed, key=lambda r: r["support_count"])
            st.success(
                f"Fewest supports among tested passing layouts: {best['support_count']} "
                f"with {best['product_id']} at nominal {best['spacing_m']:g} m. "
                "Screening only; not a global or operational optimum."
            )
        else:
            st.warning("No tested layout meets the target within this model.")
        st.download_button(
            "Download layout comparison CSV",
            screening_csv(comparison),
            "unvalidated-layout-comparison.csv",
            "text/csv",
        )
    if st.button("Run current placement", type="primary"):
        try:
            result = simulate_job(job, products)
            st.session_state.job_run = dict(input=job, result=result)
        except ValueError as exc:
            st.session_state.pop("job_run", None)
            st.error(str(exc))
    saved = st.session_state.get("job_run")
    if saved:
        if saved["input"] != job or saved["result"]["catalog_snapshot"] != [
            asdict(p) for p in products
        ]:
            st.warning(
                "Inputs changed since this result. Run again; "
                "displayed results use the saved inputs."
            )
        result = saved["result"]
        lower = result["minimum_standoff_lower_bound"]
        if lower is None:
            st.error(
                "Interval result withheld: one or more spans are unsupported "
                "or may contact the wall."
            )
        else:
            st.metric("Conservative interval standoff lower bound", f"{100 * lower:.2f}%")
        fig = go.Figure()
        for i in range(len(result["spans"])):
            rows = [r for r in result["profile"] if r["span_index"] == i]
            fig.add_trace(
                go.Scatter(
                    x=[r["md_m"] for r in rows],
                    y=[
                        None if r["standoff_ratio"] is None else 100 * r["standoff_ratio"]
                        for r in rows
                    ],
                    mode="lines",
                    name=f"Span {i + 1}",
                )
            )
        source_job = saved["input"]
        supports = result["supports"]
        diameters = [r["hole_diameter_m"] for r in source_job["caliper"]]
        depths = [r["md_m"] for r in source_job["caliper"]]
        casing_od = source_job["casing_sections"][0]["casing"]["outer_diameter_m"]
        fig.add_trace(
            go.Scatter(
                x=[r["md_m"] for r in supports],
                y=[
                    None
                    if r["offset_m"] is None
                    else 100
                    * (
                        1
                        - r["offset_m"]
                        / ((float(np.interp(r["md_m"], depths, diameters)) - casing_od) / 2)
                    )
                    for r in supports
                ],
                text=[r["product_id"] for r in supports],
                mode="markers",
                name="Centralizer positions",
                marker=dict(symbol="diamond", size=9),
                hovertemplate="MD %{x} m<br>%{text}<extra></extra>",
            )
        )
        fig.add_hline(y=target, line_dash="dash", annotation_text="Current illustrative target")
        fig.update_layout(xaxis_title="Measured depth (m)", yaxis_title="Screened standoff (%)")
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Wellbore caliper profile used in this run"):
            caliper_plot = go.Figure(
                go.Scatter(
                    x=depths,
                    y=[1000 * d for d in diameters],
                    name="Hole diameter",
                    mode="lines+markers",
                )
            )
            caliper_plot.add_hline(y=1000 * casing_od, annotation_text="Casing OD")
            caliper_plot.update_layout(xaxis_title="MD (m)", yaxis_title="Diameter (mm)")
            st.plotly_chart(caliper_plot, use_container_width=True)
        st.dataframe(result["supports"], hide_index=True)
        st.dataframe(result["spans"], hide_index=True)
        st.subheader("Per-joint conservative screening results")
        st.dataframe(result["joints"], hide_index=True)
        st.download_button(
            "Download complete job report JSON",
            json.dumps(saved, indent=2, allow_nan=False),
            "unvalidated-job-report.json",
            "application/json",
        )
        st.download_button(
            "Download support schedule CSV",
            screening_csv(
                [dict(r, review_status=result["review_status"]) for r in result["supports"]]
            ),
            "unvalidated-support-schedule.csv",
            "text/csv",
        )
    st.download_button(
        "Download editable job JSON",
        json.dumps(job, indent=2, allow_nan=False),
        "centralizer-job.json",
        "application/json",
    )
