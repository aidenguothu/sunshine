"""Run: streamlit run src/sunshine_sim/ui/app.py"""

import json
from dataclasses import asdict
from math import cos, pi, sin

import plotly.graph_objects as go
import streamlit as st

from sunshine_sim.engine.models import CasingSpec
from sunshine_sim.engine.standoff import single_joint_standoff
from sunshine_sim.ui.span_screen import render_span_screen

st.set_page_config(page_title="Sunshine | Standoff prototype", layout="wide")
st.title("Sunshine · Casing standoff prototype")
st.warning(
    "UNVALIDATED engineering screening. Not for operational placement or compliance decisions."
)
mode = st.radio("Calculation mode", ["Prescribed-offset geometry", "Ideal-support beam & spacing"])
if mode == "Ideal-support beam & spacing":
    render_span_screen()
    st.stop()
st.caption(
    "Prescribe eccentricity to explore geometry. This does not predict centralizer performance."
)
left, right = st.columns([1, 2])
with left:
    hole = st.number_input("Hole diameter (mm)", min_value=1.0, value=215.9)
    od = st.number_input("Casing OD (mm)", min_value=1.0, value=177.8)
    inside = st.number_input("Casing ID (mm)", min_value=0.1, value=157.1)
    eccentricity = st.number_input("Prescribed center offset (mm)", min_value=0.0, value=5.0)
    st.caption("Example casing: 43.2 kg/m, N80, 12 m joint. These do not affect this model.")
try:
    casing = CasingSpec(od / 1000, inside / 1000, 43.2, "N80")
    result = single_joint_standoff(casing, hole / 1000, eccentricity / 1000)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
with right:
    st.metric("Uniform joint standoff", f"{result.standoff_percent:.2f}%")
    st.metric("Minimum annular gap", f"{result.minimum_gap_m * 1000:.2f} mm")
    fig = go.Figure()
    theta = [i * 2 * pi / 200 for i in range(201)]
    for label, radius, offset, color in [
        ("Hole", hole / 2, 0, "#9c7b53"),
        ("Casing OD", od / 2, eccentricity, "#3b745f"),
        ("Casing ID", inside / 2, eccentricity, "#8cb6a5"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=[offset + radius * cos(t) for t in theta],
                y=[radius * sin(t) for t in theta],
                name=label,
                mode="lines",
                line_color=color,
            )
        )
    fig.update_layout(xaxis_title="mm", yaxis_title="mm", yaxis_scaleanchor="x")
    st.plotly_chart(fig, use_container_width=True)
st.download_button(
    "Download screening result (JSON)",
    json.dumps(
        {
            "casing": asdict(casing),
            "hole_diameter_m": hole / 1000,
            "prescribed_eccentricity_m": eccentricity / 1000,
            "result": asdict(result),
        },
        indent=2,
    ),
    file_name="unvalidated-standoff.json",
    mime="application/json",
)
