"""Simulation results workspace with synchronized depth tracks and section inspection."""

import streamlit as st

from sunshine_sim.ui.well_figures import cross_section, depth_tracks, hole_at, offset_at, section_at


def render_result_view(saved, target):
    job, result = saved["input"], saved["result"]
    lower = result["minimum_standoff_lower_bound"]
    stats = st.columns(4)
    stats[0].metric(
        "Conservative interval standoff lower bound",
        "Withheld" if lower is None else f"{100 * lower:.2f}%",
    )
    stats[1].metric("Centralizers", len(result["supports"]))
    stats[2].metric("Screened spans", len(result["spans"]))
    invalid = sum(s["standoff_lower_bound"] is None for s in result["spans"])
    stats[3].metric("Unsupported / possible-contact spans", invalid)
    if lower is None:
        st.error("Interval result withheld. Red bands mark spans requiring a more complete solver.")
    elif lower < target / 100:
        st.warning("The conservative interval bound is below the current illustrative target.")
    else:
        st.info(
            "Conservative interval bound meets the current illustrative target "
            "within this screening model."
        )
    start, end = job["casing_sections"][0]["start_md_m"], job["casing_sections"][-1]["end_md_m"]
    md = st.number_input(
        "Inspect measured depth (m)",
        min_value=float(start),
        max_value=float(end),
        value=float((start + end) / 2),
        step=0.25,
    )
    st.caption(
        "Depth increases downward. Tracks share measured depth, not TVD. The schematic is a "
        "local transverse view with independent horizontal/depth scales, not a well trajectory. "
        "Diamonds and stylized bows mark placements; glyph length is exaggerated, "
        "not device geometry. "
        "Solid line = sampled profile; dotted line = conservative span bound; "
        "amber line = target; red background = below target or unsupported span."
    )
    tracks, section, tables = st.tabs(
        ["Depth-aligned overview", "Cross-section inspector", "Engineering tables"]
    )
    with tracks:
        overview = depth_tracks(job, result, target, md)
        st.plotly_chart(overview, use_container_width=True)
        html = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>Sunshine screening diagram</title>"
            "</head><body><h2>Sunshine · UNVALIDATED demonstration</h2>"
            "<p>Depth-aligned local schematic, not a trajectory or operational design. "
            "Bows are schematic symbols. Dotted lines are conservative bounds. "
            "Red bands denote below-target regions or unsupported spans.</p>"
            + overview.to_html(full_html=False, include_plotlyjs=True)
            + "</body></html>"
        )
        st.download_button(
            "Download interactive diagram (HTML)",
            html,
            "sunshine-unvalidated-diagram.html",
            "text/html",
        )
    with section:
        left, right = st.columns([1.3, 1])
        fig = cross_section(job, result, md)
        if fig is None:
            st.warning("Cross-section withheld: selected depth lies in an unsupported span.")
        else:
            with left:
                st.plotly_chart(fig, use_container_width=True)
            with right:
                ratio = offset_at(result, md)
                hole = hole_at(job, md) * 1000
                casing = section_at(job, md)["casing"]
                st.metric("Interpolated local standoff", f"{100 * ratio:.2f}%")
                st.metric("Hole diameter", f"{hole:.2f} mm")
                st.metric(
                    "Casing OD / ID",
                    f"{1000 * casing['outer_diameter_m']:.2f} / "
                    f"{1000 * casing['inner_diameter_m']:.2f} mm",
                )
                st.metric(
                    "Local low-side gap",
                    f"{ratio * (hole - 1000 * casing['outer_diameter_m']) / 2:.2f} mm",
                )
                st.caption(
                    "Interpolated from the plotted profile, not a new equilibrium solution. "
                    "The interval lower bound is conservative and need not occur at this depth."
                )
    with tables:
        st.subheader("Placement schedule and support reactions")
        st.dataframe(result["supports"], hide_index=True)
        st.subheader("Span bounds and validity")
        st.dataframe(result["spans"], hide_index=True)
        st.subheader("Per-joint conservative screening results")
        st.dataframe(result["joints"], hide_index=True)
