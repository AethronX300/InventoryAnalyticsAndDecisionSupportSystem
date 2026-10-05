"""Meridian · Inventory IQ — Plotly figures styled to match the original Recharts look."""
from __future__ import annotations

import plotly.graph_objects as go

from analytics import cat_color

FONT = "Manrope, system-ui, sans-serif"
INK, DIM, GRID = "#e9f2ea", "#7d9485", "rgba(255,255,255,.06)"
METRIC_COLOR = {"revenue": "#8fc49b", "units": "#7fb0c9", "orders": "#d9a45b"}
METRIC_LABEL = {"revenue": "Revenue", "units": "Units", "orders": "Orders"}


def _rgba(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def base_layout(**kw) -> dict:
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=DIM, size=11),
        margin=dict(l=46, r=10, t=8, b=30),
        showlegend=False, autosize=True,
        hoverlabel=dict(bgcolor="rgba(9,16,12,.96)", bordercolor="rgba(255,255,255,.14)",
                        font=dict(family=FONT, color=INK, size=12)),
    )
    layout.update(kw)
    return layout


def _axis(**kw) -> dict:
    ax = dict(showgrid=True, gridcolor=GRID, zeroline=False, showline=False, ticks="", tickfont=dict(size=10.5, color="#67806f"),
              fixedrange=False)
    ax.update(kw)
    return ax


def _pick(p: dict, metric: str) -> float:
    return p["revenue"] / 100 if metric == "revenue" else p[metric]


# ---------------------------------------------------------------------------- trend
def trend_fig(cur: list, metric: str, prev: list | None = None, brush: bool = False) -> go.Figure:
    color = METRIC_COLOR[metric]
    x = [p["d"] for p in cur]
    y = [_pick(p, metric) for p in cur]
    money = metric == "revenue"
    yfmt = "₹%{y:,.0f}" if money else "%{y:,.0f}"
    fig = go.Figure()
    if prev:
        fig.add_trace(go.Scatter(
            x=x, y=[_pick(p, metric) for p in prev] + [None] * max(0, len(x) - len(prev)), name="Previous period", mode="lines",
            line=dict(color="#5f7a6b", width=1.6, dash="dash", shape="spline", smoothing=1.2),
            hovertemplate=f"Previous  <b>{yfmt}</b><extra></extra>"))
    mode = "lines+markers" if len(x) <= 1 else "lines"
    fig.add_trace(go.Scatter(
        x=x, y=y, name=METRIC_LABEL[metric], mode=mode,
        line=dict(color=color, width=2.6, shape="spline", smoothing=1.2),
        marker=dict(size=8, color=color),
        fill="tozeroy", fillcolor=_rgba(color, .1),
        fillgradient=dict(type="vertical", colorscale=[[0, _rgba(color, 0)], [1, _rgba(color, .34)]]),
        hovertemplate=f"{METRIC_LABEL[metric]}  <b>{yfmt}</b><extra></extra>"))
    fig.update_layout(**base_layout(
        hovermode="x unified",
        xaxis=_axis(showgrid=False, tickformat="%-m/%-d", hoverformat="%a, %b %-d", nticks=10, tickangle=0,
                    showspikes=True, spikemode="across", spikethickness=1, spikedash="dot", spikecolor="rgba(255,255,255,.22)",
                    rangeslider=dict(visible=brush, thickness=0.1, bgcolor="rgba(255,255,255,.03)",
                                     bordercolor="rgba(255,255,255,.08)", borderwidth=1)),
        yaxis=_axis(tickformat="₹.2~s" if money else ".0f", rangemode="tozero", nticks=5),
    ))
    return fig


# ------------------------------------------------------------------------ sparkline
def sparkline(values: list, color: str = "#7fb48d", money: bool = False) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=list(range(len(values))), y=values, mode="lines", line=dict(color=color, width=1.7, shape="spline", smoothing=1),
        fill="tozeroy", fillcolor=_rgba(color, .1),
        fillgradient=dict(type="vertical", colorscale=[[0, _rgba(color, 0)], [1, _rgba(color, .3)]]),
        hovertemplate=("₹%{y:,.0f}" if money else "%{y:,.0f}") + "<extra></extra>"))
    fig.update_layout(**base_layout(margin=dict(l=0, r=0, t=4, b=2), hovermode="x",
                                    xaxis=dict(visible=False, fixedrange=True),
                                    yaxis=dict(visible=False, fixedrange=True, rangemode="tozero")))
    return fig


# --------------------------------------------------------------------------- donut
def donut_fig(categories: list) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=[c["name"] for c in categories], values=[c["revenue"] / 100 for c in categories], sort=False, hole=.74,
        direction="clockwise", textinfo="none", pull=[.015] * len(categories),
        marker=dict(colors=[c["color"] for c in categories], line=dict(color="#0c140f", width=3)),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} · %{percent}<extra></extra>"))
    fig.update_layout(**base_layout(margin=dict(l=10, r=10, t=10, b=10)))
    return fig


# ----------------------------------------------------------------- category perf
def catperf_fig(categories: list) -> go.Figure:
    names = [c["name"] for c in categories]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=names, y=[c["revenue"] / 100 for c in categories], name="Revenue", width=.28,
        marker=dict(color=[_rgba(c["color"], .78) for c in categories], line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Revenue ₹%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=names, y=[c["margin"] * 100 for c in categories], name="Gross margin", yaxis="y2", mode="lines+markers",
        line=dict(color="#d9a45b", width=2, shape="spline", smoothing=1),
        marker=dict(size=7, color="#d9a45b", line=dict(color="#0c140f", width=2)),
        hovertemplate="Gross margin <b>%{y:.1f}%</b><extra></extra>"))
    fig.update_layout(**base_layout(
        margin=dict(l=48, r=44, t=8, b=30), hovermode="x unified", bargap=.5,
        xaxis=_axis(showgrid=False, tickfont=dict(size=11, color=DIM)),
        yaxis=_axis(tickformat="₹.2~s", rangemode="tozero", nticks=5),
        yaxis2=dict(overlaying="y", side="right", range=[0, 100], ticksuffix="%", showgrid=False, zeroline=False,
                    tickfont=dict(size=10.5, color="#67806f"), nticks=5)))
    return fig


# --------------------------------------------------------------------- scatter
def scatter_fig(velocity: list) -> go.Figure:
    fig = go.Figure()
    top = max((v["revenue"] for v in velocity), default=1) or 1
    cats = []
    for v in velocity:
        if v["category"] not in cats:
            cats.append(v["category"])
    for cat in cats:
        pts = [v for v in velocity if v["category"] == cat]
        fig.add_trace(go.Scatter(
            x=[p["velocity"] for p in pts], y=[p["margin"] for p in pts], mode="markers", name=cat,
            customdata=[[p["sku"], p["name"], p["revenue"] / 100] for p in pts],
            marker=dict(size=[max(p["revenue"], 1) for p in pts], sizemode="area", sizeref=2 * top / (30 ** 2), sizemin=7,
                        color=_rgba(cat_color(cat), .78), line=dict(width=1, color=_rgba(cat_color(cat), .95))),
            hovertemplate="<b>%{customdata[1]}</b><br>%{customdata[0]} · " + cat +
                          "<br>Velocity %{x:.2f} u/d<br>Margin %{y:.0f}%<br>30d revenue ₹%{customdata[2]:,.0f}<extra></extra>"))
    fig.update_layout(**base_layout(
        margin=dict(l=44, r=14, t=8, b=40), hovermode="closest",
        xaxis=_axis(title=dict(text="units / day", font=dict(size=10.5, color="#67806f")), rangemode="tozero"),
        yaxis=_axis(ticksuffix="%", range=[0, 80], nticks=5)))
    return fig


# ------------------------------------------------------------------------- step
def step_fig(series: list, reorder_point: int | None = None) -> go.Figure:
    x = [p["d"] for p in series]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=[p["stock"] for p in series], mode="lines", line=dict(color="#8fc49b", width=2.2, shape="hv"),
        fill="tozeroy", fillcolor=_rgba("#8fc49b", .1),
        fillgradient=dict(type="vertical", colorscale=[[0, _rgba("#8fc49b", 0)], [1, _rgba("#8fc49b", .32)]]),
        hovertemplate="Stock <b>%{y:,.0f}</b> units<extra></extra>"))
    if reorder_point is not None:
        fig.add_trace(go.Scatter(x=[x[0], x[-1]], y=[reorder_point] * 2, mode="lines", hovertemplate="Reorder point <b>%{y}</b><extra></extra>",
                                 line=dict(color="#d9a45b", width=1.4, dash="dash")))
    fig.update_layout(**base_layout(
        margin=dict(l=36, r=8, t=8, b=28), hovermode="x unified",
        xaxis=_axis(showgrid=False, tickformat="%-m/%-d", hoverformat="%a, %b %-d", nticks=7,
                    showspikes=True, spikemode="across", spikethickness=1, spikedash="dot", spikecolor="rgba(255,255,255,.22)"),
        yaxis=_axis(rangemode="tozero", nticks=4)))
    return fig
