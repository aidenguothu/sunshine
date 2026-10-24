"""Catalog editing, equal-condition product comparison and spacing screening."""

import csv
import io
import json
from dataclasses import asdict, replace
from importlib.resources import files

import plotly.graph_objects as go
import streamlit as st

from sunshine_sim.data.catalog import dump_catalog, load_catalog
from sunshine_sim.engine.models import CasingSpec, CentralizerSpec, ForceDeflectionPoint
from sunshine_sim.engine.product import ProductInput, solve_product_span
from sunshine_sim.engine.span import SpanCase
from sunshine_sim.reporting.csv_export import screening_csv


def render_product_screen() -> None:
    st.warning(
        "Demo/comparative screening only. Isolated span, two identical bow-spring supports; "
        "each supports qL/2. Shared supports in a repeated string carry different loads. "
        "No full-string schedule, contact solution, run-in feasibility or API/ISO approval."
    )
    st.caption(
        "Required curve: NET lateral restoring force versus CASING CENTER OFFSET in the stated "
        "test hole. Individual bow-compression curves and single catalog force ratings cannot "
        "be substituted. Free OD, starting force and running force are recorded, not solved."
    )
    if "catalog_json" not in st.session_state:
        st.session_state.catalog_json = (
            files("sunshine_sim").joinpath("data/examples/demo_catalog.json").read_text()
        )
    with st.expander("Import / export product catalog"):
        upload = st.file_uploader("Import catalog JSON (schema 0.3)", type="json")
        if st.button("Load uploaded catalog"):
            try:
                if upload is None:
                    raise ValueError("Choose a catalog file first")
                imported = load_catalog(upload.getvalue().decode("utf-8"))
                # Imported status is never treated as verified/certified.
                imported = tuple(
                    replace(p, data_status="user_supplied_unverified") for p in imported
                )
                st.session_state.catalog_json = dump_catalog(imported)
                st.success("Loaded unverified user data; engineering review is still required.")
            except (ValueError, UnicodeError) as exc:
                st.error(str(exc))
        st.download_button(
            "Download current catalog",
            st.session_state.catalog_json,
            "centralizer-catalog.json",
            "application/json",
        )
    products = load_catalog(st.session_state.catalog_json)
    chosen = st.selectbox(
        "Catalog product to inspect or edit", [p.spec.product_id for p in products]
    )
    product = next(p for p in products if p.spec.product_id == chosen)
    st.caption(f"Data status: {product.data_status} · {product.spec.test_reference}")
    with st.expander("Enter / edit centralizer specifications"):
        with st.form("product_editor"):
            product_id = st.text_input(
                "Product ID (new ID adds a product)", product.spec.product_id
            )
            casing_od = st.number_input(
                "Compatible casing OD (mm)", value=product.spec.compatible_casing_od_m * 1000
            )
            free_od = st.number_input(
                "Free centralizer OD (mm)", value=product.spec.free_outer_diameter_m * 1000
            )
            test_hole = st.number_input(
                "Curve test-hole diameter (mm)", value=product.spec.test_hole_diameter_m * 1000
            )
            starting = st.number_input(
                "Starting force (N) — metadata only", value=product.spec.starting_force_n
            )
            running = st.number_input(
                "Running force (N) — metadata only", value=product.spec.running_force_n
            )
            reference = st.text_input(
                "Test certificate / revision reference", product.spec.test_reference
            )
            conditions = st.text_input(
                "Test conditions / loading branch / orientation", product.test_conditions
            )
            curve = st.text_area(
                "Curve rows: casing offset (mm), net lateral force (N)",
                "\n".join(
                    f"{p.compression_m * 1000:g},{p.restoring_force_n:g}"
                    for p in product.spec.restoring_curve
                ),
            )
            submitted = st.form_submit_button("Save product to this session")
        if submitted:
            try:
                rows = list(csv.reader(io.StringIO(curve)))
                if not 2 <= len(rows) <= 1000 or any(len(row) != 2 for row in rows):
                    raise ValueError("Provide 2 to 1000 rows, each containing offset_mm, force_N")
                points = tuple(ForceDeflectionPoint(float(r[0]) / 1000, float(r[1])) for r in rows)
                spec = CentralizerSpec(
                    product_id.strip(),
                    "bow_spring",
                    casing_od / 1000,
                    free_od / 1000,
                    test_hole / 1000,
                    starting,
                    running,
                    points,
                    reference,
                )
                updated = ProductInput(
                    spec, product.curve_basis, "user_supplied_unverified", conditions
                )
                entries = tuple(p for p in products if p.spec.product_id != updated.spec.product_id)
                entries += (updated,)
                if len(entries) > 100:
                    raise ValueError("Catalog limit: 100 products")
                st.session_state.catalog_json = dump_catalog(entries)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with st.expander("View catalog force–offset curves"):
        curve_plot = go.Figure()
        for p in products:
            curve_plot.add_trace(
                go.Scatter(
                    x=[point.compression_m * 1000 for point in p.spec.restoring_curve],
                    y=[point.restoring_force_n for point in p.spec.restoring_curve],
                    name=f"{p.spec.product_id} ({p.data_status})",
                    mode="lines+markers",
                )
            )
        curve_plot.update_layout(
            xaxis_title="Casing center offset in test hole (mm)",
            yaxis_title="Net lateral restoring force (N)",
        )
        st.plotly_chart(curve_plot, use_container_width=True)
    st.caption(
        "Edits last only in this session. Download the catalog to retain them. Bow-spring only."
    )
    left, right = st.columns([1, 2])
    with left:
        selected = st.multiselect(
            "Compare products",
            [p.spec.product_id for p in products],
            default=[p.spec.product_id for p in products][:2],
        )
        hole = st.number_input("Hole diameter (mm)", value=215.9)
        od = st.number_input("Casing OD (mm)", value=177.8)
        inside = st.number_input("Casing ID (mm)", value=157.1)
        mass = st.number_input("Casing mass (kg/m)", value=43.2)
        inclination = st.number_input("Inclination from vertical (degrees)", value=60.0)
        rho_i = st.number_input("Internal fluid density (kg/m³)", value=1200.0)
        rho_o = st.number_input("External fluid density (kg/m³)", value=1200.0)
        span = st.number_input("Comparison span (m)", value=4.0)
        target = st.number_input(
            "Illustrative target standoff (%)", min_value=0.0, max_value=100.0, value=67.0
        )
        candidates_text = st.text_input("Candidate isolated spans (m)", "2, 3, 4, 5, 6, 9, 12")
        st.caption(
            "67% is an editable demonstration target, not a universal job acceptance criterion."
        )
    with right:
        try:
            casing = CasingSpec(od / 1000, inside / 1000, mass, "USER-SPECIFIED")
            case = SpanCase(hole / 1000, span, inclination, rho_i, rho_o)
            tokens = candidates_text.split(",")
            if not 1 <= len(tokens) <= 100:
                raise ValueError("Provide 1 to 100 candidate spans")
            lengths = sorted(set(float(v.strip()) for v in tokens))
            if not selected:
                raise ValueError("Select at least one product")
            fig = go.Figure()
            results, table, summary = [], [], []
            for p in products:
                if p.spec.product_id not in selected:
                    continue
                result = solve_product_span(casing, case, p)
                if result.standoff_ratios is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=result.ideal_beam.positions_m,
                            y=[100 * r for r in result.standoff_ratios],
                            name=p.spec.product_id,
                        )
                    )
                else:
                    st.warning(f"{p.spec.product_id}: {result.status} — standoff withheld")
                passes = []
                candidates = []
                for length in lengths:
                    r = solve_product_span(casing, replace(case, span_length_m=length), p)
                    ratio = r.minimum_standoff_ratio
                    passed = ratio is not None and ratio >= target / 100
                    if passed:
                        passes.append(length)
                    table.append(
                        {
                            "Product": p.spec.product_id,
                            "Data": p.data_status,
                            "Span (m)": length,
                            "Min standoff (%)": None if ratio is None else 100 * ratio,
                            "Passes illustrative target": passed,
                            "Status": r.status,
                        }
                    )
                    candidates.append({"span_m": length, "result": asdict(r)})
                summary.append(
                    {
                        "Product": p.spec.product_id,
                        "Longest tested passing isolated span (m)": max(passes) if passes else None,
                    }
                )
                results.append(
                    {"product": asdict(p), "comparison": asdict(result), "candidates": candidates}
                )
        except ValueError as exc:
            st.error(str(exc))
            return
        fig.add_hline(y=target, line_dash="dash", annotation_text="Illustrative target")
        fig.update_layout(xaxis_title="Distance from first support (m)", yaxis_title="Standoff (%)")
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Equal-condition product comparison")
        st.dataframe(summary, hide_index=True)
        st.dataframe(table, hide_index=True)
        csv_rows = [
            dict(
                row,
                Review="UNVALIDATED — demonstration only",
                **{
                    "Hole diameter (mm)": hole,
                    "Casing OD (mm)": od,
                    "Inclination (deg)": inclination,
                    "Target (%)": target,
                },
            )
            for row in table
        ]
        st.download_button(
            "Download spacing comparison (CSV)",
            screening_csv(csv_rows),
            "unvalidated-spacing-comparison.csv",
            "text/csv",
        )
        st.caption(
            "Blank results mean unsupported or infeasible, not zero standoff. "
            "Do not reuse isolated-span lengths as a repeated-string schedule."
        )
        report = {
            "schema_version": "0.3",
            "status": "UNVALIDATED — demonstration only",
            "casing": asdict(casing),
            "case": asdict(case),
            "target_ratio": target / 100,
            "products": results,
            "assumptions": "Isolated static straight span; identical "
            "supports qL/2; installed net lateral curve; piecewise-linear interpolation; "
            "no extrapolation, curvature, axial load, contact or run-in solution.",
        }
        st.download_button(
            "Download product comparison report (JSON)",
            json.dumps(report, indent=2, allow_nan=False),
            "unvalidated-product-comparison.json",
            "application/json",
        )
