"""UI adapter for the ideal-support beam screening model."""

import json
from dataclasses import asdict

import plotly.graph_objects as go
import streamlit as st

from sunshine_sim.engine.models import CasingSpec
from sunshine_sim.engine.span import SpanCase, screen_spacings, solve_span


def render_span_screen() -> None:
    st.info(
        "Ideal, perfectly centered, simply supported ends; straight uniform casing; "
        "static lateral buoyant weight only. No real centralizer stiffness, axial load, "
        "curvature or contact solution. Results are NOT product-qualified spacing recommendations."
    )
    left, right = st.columns([1, 2])
    with left:
        hole = st.number_input("Hole diameter (mm)", min_value=1.0, value=215.9)
        od = st.number_input("Casing OD (mm)", min_value=1.0, value=177.8)
        inside = st.number_input("Casing ID (mm)", min_value=0.1, value=157.1)
        mass = st.number_input("Casing mass (kg/m)", min_value=0.1, value=43.2)
        modulus = st.number_input("Young's modulus (GPa)", min_value=1.0, value=207.0)
        length = st.number_input("Support spacing (m)", min_value=0.1, value=6.0)
        inclination = st.number_input(
            "Inclination from vertical (degrees)", min_value=0.0, max_value=90.0, value=60.0
        )
        rho_i = st.number_input("Internal fluid density (kg/m³)", min_value=0.0, value=1200.0)
        rho_o = st.number_input("External fluid density (kg/m³)", min_value=0.0, value=1200.0)
        target = st.number_input(
            "Illustrative target standoff (%) — set by your engineer",
            min_value=0.0,
            max_value=100.0,
            value=80.0,
        )
        candidates = st.text_input("Candidate spacings (m, comma-separated)", "3, 4, 5, 6, 9, 12")
    try:
        casing = CasingSpec(od / 1000, inside / 1000, mass, "USER-SPECIFIED", 12, modulus * 1e9)
        case = SpanCase(hole / 1000, length, inclination, rho_i, rho_o)
        result = solve_span(casing, case)
        if len(candidates.split(",")) > 1000:
            raise ValueError("Provide no more than 1000 candidates")
        spacings = tuple(float(v.strip()) for v in candidates.split(","))
        screen = screen_spacings(casing, case, spacings, target / 100)
    except ValueError as exc:
        st.error(str(exc))
        return
    with right:
        if result.minimum_standoff_ratio is None:
            st.error(
                f"{result.status}: predicted free sag is outside the model's permitted geometry "
                "or deflection range. Physical standoff is withheld; "
                "a more complete solver is needed."
            )
        else:
            st.metric(
                "Minimum ideal-support standoff", f"{100 * result.minimum_standoff_ratio:.2f}%"
            )
            st.caption(
                f"Analytic minimum occurs at midspan: {length / 2:.2f} m from the first support."
            )
        st.metric("Predicted maximum free sag", f"{1000 * result.maximum_free_sag_m:.2f} mm")
        st.caption(
            f"Lateral load: {result.lateral_load_n_m:.2f} N/m · "
            f"Ideal reaction per support: {result.end_reaction_n:.2f} N"
        )
        if result.standoff_ratios is not None:
            fig = go.Figure(
                go.Scatter(
                    x=result.positions_m,
                    y=[100 * v for v in result.standoff_ratios],
                    name="Ideal-support standoff",
                    mode="lines",
                )
            )
            fig.add_hline(y=target, line_dash="dash", annotation_text="Illustrative target")
            fig.update_layout(
                xaxis_title="Distance from first support (m)", yaxis_title="Standoff (%)"
            )
            st.plotly_chart(fig, use_container_width=True)
        st.subheader("Candidate spacing screen")
        st.caption(
            "Only the supplied candidates are tested. "
            "No joint locations or string schedule are optimized."
        )
        rows = []
        for spacing, candidate in screen.candidates:
            ratio = candidate.minimum_standoff_ratio
            rows.append(
                {
                    "Spacing (m)": spacing,
                    "Minimum standoff (%)": None if ratio is None else 100 * ratio,
                    "Meets illustrative target": ratio is not None and ratio >= target / 100,
                    "Model status": candidate.status,
                }
            )
        st.dataframe(rows, hide_index=True)
        best = screen.longest_passing_candidate_m
        if best is None:
            st.warning("No supplied candidate meets the target within this ideal-support screen.")
        else:
            st.success(
                f"Longest tested passing ideal-support span: {best:g} m "
                "(not an operational recommendation)."
            )
    st.download_button(
        "Download beam screening report (JSON)",
        json.dumps(
            {
                "schema_version": "0.2",
                "casing": asdict(casing),
                "case": asdict(case),
                "result": asdict(result),
                "spacing_screen": asdict(screen),
                "assumptions": "Ideal centered pins; uniform static load; straight beam; "
                "no axial force, curvature, spring compliance, friction or contact solution; "
                "no operational or standards compliance approval.",
            },
            indent=2,
            allow_nan=False,
        ),
        file_name="unvalidated-beam-screen.json",
        mime="application/json",
    )
