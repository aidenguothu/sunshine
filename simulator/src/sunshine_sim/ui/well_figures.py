"""Depth-aligned diagrams. Display adapters only; no engineering solve here."""

from math import cos, pi, sin

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PALETTE = ["#007f86", "#d97b27", "#7d5db0", "#3574bc", "#ba4874"]


def product_colors(job):
    return {
        name: PALETTE[i % len(PALETTE)]
        for i, name in enumerate(sorted({r["product_id"] for r in job["placements"]}))
    }


def section_at(job, md):
    return next(s for s in job["casing_sections"] if s["start_md_m"] <= md <= s["end_md_m"])


def hole_at(job, md):
    return float(
        np.interp(
            md, [r["md_m"] for r in job["caliper"]], [r["hole_diameter_m"] for r in job["caliper"]]
        )
    )


def offset_at(result, md):
    """Return plotted profile interpolation only inside a supported span."""
    for i, span in enumerate(result["spans"]):
        if span["start_md_m"] <= md <= span["end_md_m"]:
            if span["standoff_lower_bound"] is None:
                return None
            rows = [r for r in result["profile"] if r["span_index"] == i]
            ratios = [r["standoff_ratio"] for r in rows]
            if not rows or any(r is None for r in ratios):
                return None
            return float(np.interp(md, [r["md_m"] for r in rows], ratios))
    return None


def depth_tracks(job, result=None, target=67.0, selected_md=None):
    """Local transverse schematic against MD, NOT a trajectory or TVD plot."""
    count = 4 if result else 2
    fig = make_subplots(
        rows=1,
        cols=count,
        shared_yaxes=True,
        horizontal_spacing=0.065,
        column_widths=[0.32, 0.18, 0.32, 0.18] if result else [0.62, 0.38],
        subplot_titles=["Well schematic", "Hole / casing", "Standoff", "Support load"][:count],
    )
    start = job["casing_sections"][0]["start_md_m"]
    end = job["casing_sections"][-1]["end_md_m"]
    depths = sorted(
        set(
            [r["md_m"] for r in job["caliper"] if start <= r["md_m"] <= end]
            + [start, end]
            + list(np.linspace(start, end, 101))
        )
    )
    radii = [hole_at(job, d) * 500 for d in depths]
    fig.add_trace(
        go.Scatter(
            x=[-r for r in radii] + radii[::-1],
            y=depths + depths[::-1],
            fill="toself",
            fillcolor="#f0e8d9",
            line_color="#b7a78d",
            name="Open hole",
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )
    for i, s in enumerate(job["casing_sections"]):
        local = [d for d in depths if s["start_md_m"] <= d <= s["end_md_m"]]
        if not local or local[0] != s["start_md_m"]:
            local.insert(0, s["start_md_m"])
        if local[-1] != s["end_md_m"]:
            local.append(s["end_md_m"])
        od = s["casing"]["outer_diameter_m"] * 1000
        # Design outlines stay centered. Result view leaves unsupported spans blank.
        shifts = []
        for d in local:
            ratio = offset_at(result, d) if result else 1.0
            shifts.append(
                None if ratio is None else (1 - ratio) * (hole_at(job, d) * 1000 - od) / 2
            )
        for radius, fill, name in [
            (od / 2, "#68879d", "Casing OD"),
            (s["casing"]["inner_diameter_m"] * 500, "#eef5f7", "Casing bore"),
        ]:
            # Separate polygons for valid spans prevents interpolation through invalid sections.
            run = []

            def add_run(points):
                if len(points) < 2:
                    return
                x = [v - radius for _, v in points] + [v + radius for _, v in points[::-1]]
                y = [d for d, _ in points] + [d for d, _ in points[::-1]]
                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=y,
                        fill="toself",
                        fillcolor=fill,
                        line=dict(color="#547186", width=1),
                        showlegend=False,
                        name=f"Section {i + 1} · {name}",
                        hovertemplate=(
                            f"Section {i + 1}<br>{name}<br>MD %{{y:.2f}} m<extra></extra>"
                        ),
                    ),
                    row=1,
                    col=1,
                )

            for d, shift in zip(local, shifts):
                if shift is None:
                    add_run(run)
                    run = []
                else:
                    run.append((d, shift))
            add_run(run)
        fig.add_trace(
            go.Scatter(
                x=[od, od],
                y=[s["start_md_m"], s["end_md_m"]],
                mode="lines",
                line=dict(color="#547186", width=3),
                name=f"Casing OD · section {i + 1}",
                showlegend=False,
                hovertemplate="OD %{x:.1f} mm<br>MD %{y:.2f} m<extra></extra>",
            ),
            row=1,
            col=2,
        )
    fig.add_trace(
        go.Scatter(
            x=[2 * r for r in radii],
            y=depths,
            name="Caliper",
            line=dict(color="#a28a60", width=2),
            hovertemplate="Hole %{x:.1f} mm<br>MD %{y:.2f} m<extra></extra>",
        ),
        row=1,
        col=2,
    )
    colors = product_colors(job)
    for product, color in colors.items():
        placements = [p for p in job["placements"] if p["product_id"] == product]
        fig.add_trace(
            go.Scatter(
                x=[0] * len(placements),
                y=[p["md_m"] for p in placements],
                mode="markers",
                marker=dict(
                    color=color, size=11, symbol="diamond", line=dict(color="white", width=1)
                ),
                name=product,
                hovertemplate=f"{product}<br>MD %{{y:.2f}} m<extra></extra>",
            ),
            row=1,
            col=1,
        )
    glyph_height = (end - start) * 0.008
    for product, color in colors.items():
        xs, ys = [], []
        for placement in job["placements"]:
            if placement["product_id"] != product:
                continue
            md = placement["md_m"]
            casing_radius = section_at(job, md)["casing"]["outer_diameter_m"] * 500
            hole_radius = hole_at(job, md) * 500
            ratio = offset_at(result, md) if result else 1.0
            if ratio is None:
                continue
            center = (1 - ratio) * (hole_radius - casing_radius)
            for side in [-1, 1]:
                xs.extend(
                    [
                        center + side * casing_radius,
                        side * hole_radius,
                        center + side * casing_radius,
                        None,
                    ]
                )
                ys.extend([md - glyph_height, md, md + glyph_height, None])
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                line=dict(color=color, width=2),
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=1,
        )
    if result:
        for i, span in enumerate(result["spans"]):
            rows = [r for r in result["profile"] if r["span_index"] == i]
            fig.add_trace(
                go.Scatter(
                    x=[
                        None if r["standoff_ratio"] is None else 100 * r["standoff_ratio"]
                        for r in rows
                    ],
                    y=[r["md_m"] for r in rows],
                    mode="lines",
                    line=dict(color="#007f86", width=2.5),
                    name="Sampled standoff",
                    showlegend=i == 0,
                    hovertemplate="Standoff %{x:.2f}%<br>MD %{y:.2f} m<extra></extra>",
                ),
                row=1,
                col=3,
            )
            bound = span["standoff_lower_bound"]
            if bound is not None:
                fig.add_trace(
                    go.Scatter(
                        x=[100 * bound] * 2,
                        y=[span["start_md_m"], span["end_md_m"]],
                        mode="lines",
                        line=dict(color="#597d92", dash="dot", width=1),
                        name="Conservative span bound",
                        showlegend=i == 0,
                        hovertemplate="Span bound %{x:.2f}%<extra></extra>",
                    ),
                    row=1,
                    col=3,
                )
            else:
                fig.add_hrect(
                    y0=span["start_md_m"],
                    y1=span["end_md_m"],
                    fillcolor="#c94d47",
                    opacity=0.12,
                    line_width=0,
                    row=1,
                    col=3,
                )
        for product, color in colors.items():
            supports = [r for r in result["supports"] if r["product_id"] == product]
            fig.add_trace(
                go.Scatter(
                    x=[r["reaction_n"] / 1000 for r in supports],
                    y=[r["md_m"] for r in supports],
                    mode="markers",
                    marker=dict(color=color, size=9),
                    name=product,
                    showlegend=False,
                    hovertemplate=(
                        f"{product}<br>Load %{{x:.3f}} kN<br>MD %{{y:.2f}} m<extra></extra>"
                    ),
                ),
                row=1,
                col=4,
            )
    if result:
        fig.add_vrect(
            x0=0, x1=target, fillcolor="#c94d47", opacity=0.055, line_width=0, row=1, col=3
        )
        fig.add_vline(x=target, line=dict(color="#c0802f", dash="dash"), row=1, col=3)
    if selected_md is not None:
        for col in range(1, count + 1):
            fig.add_hline(
                y=selected_md, line=dict(color="#536c80", dash="dot", width=1), row=1, col=col
            )
    for col, title in enumerate(
        ["Local offset (mm)", "Diameter (mm)", "Standoff (%)", "Reaction (kN)"][:count], 1
    ):
        fig.update_xaxes(
            title_text=title, side="top", row=1, col=col, showgrid=True, gridcolor="#e8eef1"
        )
        fig.update_yaxes(range=[end, start], row=1, col=col, showgrid=True, gridcolor="#edf1f3")
    fig.update_xaxes(range=[-max(radii) * 1.15, max(radii) * 1.15], row=1, col=1)
    if result:
        fig.update_xaxes(range=[0, 100], row=1, col=3)
        fig.update_xaxes(rangemode="tozero", row=1, col=4)
    fig.update_yaxes(title_text="Measured depth (m)", row=1, col=1)
    fig.update_layout(
        height=690,
        template="plotly_white",
        margin=dict(l=60, r=20, t=100, b=75),
        legend=dict(orientation="h", y=-0.08),
        hovermode="closest",
        font=dict(family="Arial, sans-serif", color="#243d50"),
        paper_bgcolor="white",
    )
    for annotation in fig.layout.annotations:
        annotation.y = 1.14
        annotation.font = dict(size=14, color="#243d50")
    return fig


def cross_section(job, result, md):
    casing = section_at(job, md)["casing"]
    hole = hole_at(job, md) * 1000
    ratio = offset_at(result, md)
    if ratio is None:
        return None
    offset = (1 - ratio) * (hole - casing["outer_diameter_m"] * 1000) / 2
    theta = np.linspace(0, 2 * pi, 181)
    fig = go.Figure()
    for name, r, center, color, fill in [
        ("Hole", hole / 2, 0, "#b7a78d", "#f0e8d9"),
        ("Casing OD", casing["outer_diameter_m"] * 500, offset, "#547186", "#68879d"),
        ("Casing bore", casing["inner_diameter_m"] * 500, offset, "#547186", "#eef5f7"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=[center + r * cos(t) for t in theta],
                y=[r * sin(t) for t in theta],
                mode="lines",
                fill="toself",
                fillcolor=fill,
                line_color=color,
                name=name,
            )
        )
    gap = (hole - casing["outer_diameter_m"] * 1000) / 2 - offset
    left = offset + casing["outer_diameter_m"] * 500
    fig.add_trace(
        go.Scatter(
            x=[left, hole / 2],
            y=[0, 0],
            mode="lines+markers",
            line=dict(color="#d97b27", width=4),
            name=f"Low-side gap {gap:.2f} mm",
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=35, b=25),
        title=f"Cross-section · MD {md:.2f} m",
        legend=dict(orientation="h", y=-0.15),
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1, title_text="mm")
    fig.update_xaxes(title_text="Local low-side direction → (mm)", constrain="domain")
    return fig
