"""Meridian · Inventory IQ — reusable UI components (the Python twin of the original ui.tsx)."""
from __future__ import annotations

from dash import dcc, html

from analytics import money

# ---------------------------------------------------------------------------- basics


def cx(*parts) -> str:
    return " ".join(p for p in parts if p)


def icon(name: str, size: int = 16, cls: str = "", **kw):
    return html.Span(className=cx("ico", f"i-{name}", cls), style={"width": size, "height": size}, **kw)


def delay(ms: int) -> dict:
    return {"--d": f"{ms}ms"}


def card(children, cls: str = "", d: int = 0, hover: bool = False, **kw):
    style = {**delay(d), **kw.pop("style", {})}
    return html.Div(children, className=cx("glass rise", "card-hover" if hover else "", cls), style=style, **kw)


def section_head(title, sub=None, right=None):
    return html.Div([html.Div([html.H3(title), html.P(sub) if sub is not None else None]), right], className="shead")


def eyebrow(text, cls=""):
    return html.Span(text, className=cx("eyebrow", cls))


def empty_state(ic, title, desc):
    return html.Div([html.Div(icon(ic, 20), className="eb glass-inset"), html.H4(title), html.P(desc)], className="empty")


# ----------------------------------------------------------------------------- pills

STATUS_META = {"out": ("Out of stock", "crit"), "critical": ("Critical", "crit"), "low": ("Low", "warn"),
               "overstock": ("Overstock", "warn"), "dead": ("Dead stock", "warn"), "healthy": ("Healthy", "ok")}


def pill(text, tone="neutral", dot=False, cls=""):
    return html.Span([html.Span(className="dot") if dot else None, text], className=cx("pill", tone, cls))


def status_pill(status):
    label, tone = STATUS_META.get(status, STATUS_META["healthy"])
    return pill(label, tone, dot=status in ("out", "critical"))


# ---------------------------------------------------------------------------- buttons


def btn(label=None, id=None, variant="soft", size="md", ic=None, cls="", **kw):
    kids = [icon(ic, 13 if size == "sm" else 15) if ic else None, label]
    props = dict(className=cx("btn", f"btn-{variant}", "sm" if size == "sm" else "", cls), n_clicks=0, **kw)
    if id is not None:
        props["id"] = id
    return html.Button(kids, **props)


def link_btn(label, href, variant="soft", size="sm", ic=None, cls=""):
    return dcc.Link([icon(ic, 13) if ic else None, label], href=href,
                    className=cx("btn", f"btn-{variant}", "sm" if size == "sm" else "", cls))


# ----------------------------------------------------------------- animated numbers


def count_int(n: int, cls: str = ""):
    """Integer that counts up from 0 using a CSS-registered custom property (no JS)."""
    return html.Span(className=cx("count num", cls), style={"--to": int(n)})


def count_money(cents: float, sym: str = "₹", digits: int = 0):
    dollars = int(round(cents / 100))
    if dollars >= 1000:
        return html.Span([sym, html.Span(className="count", style={"--to": dollars // 1000}), f",{dollars % 1000:03d}"],
                         className="num")
    return html.Span([sym, html.Span(className="count", style={"--to": dollars})], className="num")


def delta_node(frac: float, good_down: bool = False):
    up = frac >= 0
    good = (not up) if good_down else up
    zero = abs(frac) < 0.0005
    sign = "+" if up else "−"
    return html.Span([icon("arrowUp" if up else "arrowDown", 11) if not zero else None, f"{sign}{abs(frac * 100):.1f}%"],
                     className=cx("delta num", "flat" if zero else "good" if good else "bad"))


# --------------------------------------------------------------------------- cards


def kpi_card(label, value_node, ic=None, delta=None, spark=None, sub=None, href=None, d=0):
    body = [
        html.Div([eyebrow(label), icon(ic, 15) if ic else None], className="kpi-top"),
        html.Div([
            html.Div([html.Div([html.Span(value_node, className="kpi-val"), delta], className="baseline"),
                      html.P(sub, className="kpi-sub") if sub is not None else None]),
            spark,
        ], className="kpi-body"),
    ]
    cls = "glass rise kpi card-hover" if href else "glass rise kpi"
    if href:
        return dcc.Link(body, href=href, className=cls, style=delay(d))
    return html.Div(body, className=cls, style=delay(d))


def stat_card(label, value, ic, d=0):
    return card([html.Span(icon(ic, 17), className="stat-ico glass-inset"),
                 html.Div([eyebrow(label), html.P(value, className="num v")])], cls="stat", d=d)


def ring(score: int, caption: str = "", size: int = 128):
    tone = "ok" if score >= 78 else "warn" if score >= 58 else "crit"
    return html.Div([
        html.Div(className=cx("ring", tone), style={"--score": score, "--size": f"{size}px"}),
        html.Div([count_int(score, "big"), html.Span(caption, className="cap")], className="ring-center"),
    ], className="ring-wrap", style={"--size": f"{size}px"})


def progress(value: float, tone: str = "ok", delay_ms: int = 0, thick: bool = False):
    pct = max(0, min(100, value * 100))
    return html.Div(html.Div(className=cx("fill grow-w", tone), style={"--w": f"{pct:.1f}%", **delay(delay_ms)}),
                    className=cx("bar", "thick" if thick else ""))


def field(label, child, hint=None, cls=""):
    return html.Div([eyebrow(label), child, html.Span(hint, className="hint") if hint else None], className=cx("field", cls))


def search_box(id, placeholder="Search…", width=None):
    return html.Div([icon("search", 14),
                     dcc.Input(id=id, type="text", placeholder=placeholder, debounce=False, className="inp", autoComplete="off")],
                    className="search", style={"width": width} if width else None)


def segmented(id, options, value, cls=""):
    return dcc.RadioItems(id=id, options=[{"label": l, "value": v} for v, l in options], value=value,
                          className=cx("seg", cls), inline=True)


def chips(id, options, value):
    return dcc.RadioItems(id=id, options=[{"label": l, "value": v} for v, l in options], value=value,
                          className="chips", inline=True)


def dropdown(id, options, value, width=None, **kw):
    return dcc.Dropdown(id=id, options=options, value=value, clearable=False, searchable=kw.pop("searchable", False),
                        className="dd", style={"width": width} if width else None, **kw)


# ---------------------------------------------------------------------- overlays


def modal(title, body, footer, sub=None, ic=None, width=560, backdrop_id="m-backdrop", close_id="m-close"):
    head = html.Div([
        html.Span(icon(ic, 16), className="modal-ico") if ic else None,
        html.Div([html.H2(title), html.P(sub, className="sub") if sub is not None else None]),
        html.Button(icon("x", 15), id=close_id, n_clicks=0, className="icon-btn ml-auto", title="Close"),
    ], className="modal-head")
    return html.Div([
        html.Div(id=backdrop_id, n_clicks=0, className="backdrop"),
        html.Div([head, html.Div(body, className="modal-body"), html.Div(footer, className="modal-foot")],
                 className="modal glass-pop", style={"maxWidth": width}),
    ], className="overlay center")


def toast(title, tone="ok", desc=None):
    ic = {"ok": "check", "warn": "alert", "crit": "alert", "info": "info"}[tone]
    color = {"ok": "t-ok", "warn": "t-warn", "crit": "t-crit", "info": "t-info"}[tone]
    return html.Div([html.Span(icon(ic, 16), className=color, style={"marginTop": 2}),
                     html.Div([html.B(title), html.Span(desc, className="d") if desc else None])],
                    className=cx("toast glass-chip", tone))


def fmt_money(cents, sym="₹", digits=0):
    return money(cents, sym, digits)
