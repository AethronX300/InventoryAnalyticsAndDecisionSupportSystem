"""
Meridian · Inventory IQ — Dash entry point.

Run with:   python app.py      then open  http://127.0.0.1:8050

This file wires the existing modules together:
    database.py   SQLite data layer         analytics.py  decision engine
    pages.py      page layouts              charts.py     Plotly figures
    ui.py         components                theme.py      CSS
It owns the app shell (sidebar / top bar), URL routing and every interactive callback.
"""
from __future__ import annotations

import json
import time
from urllib.parse import parse_qs, quote

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

import analytics as an
import charts
import database as db
import pages
from theme import CSS, FONTS
from ui import card, icon, section_head, toast

DAY = 86_400

app = Dash(__name__, suppress_callback_exceptions=True, title="Meridian · Inventory IQ", update_title=None)
server = app.server

app.index_string = (
    "<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}"
    f'<link rel="preconnect" href="https://fonts.googleapis.com">'
    f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    f'<link href="{FONTS}" rel="stylesheet"><style>{CSS}</style></head>'
    "<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"
)


# ============================================================================ helpers
def _norm(pathname) -> str:
    p = (pathname or "/").rstrip("/") or "/"
    return p if p in pages.TITLES else "/"


def _qs(search) -> dict:
    return {k: v[0] for k, v in parse_qs((search or "").lstrip("?")).items() if v}


def _int(v):
    try:
        return None if v in (None, "") else int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _num(v):
    try:
        return None if v in (None, "") else float(v)
    except (TypeError, ValueError):
        return None


def _product_by_sku(sku):
    return next((p for p in db.load_core()["products"] if p["sku"] == sku), None)


def _product_by_id(pid):
    return next((p for p in db.load_core()["products"] if p["id"] == pid), None)


_toast_n = 0
_WRAPPERS = (html.Div, html.Section)


def _toast(title, tone="ok", desc=None):
    """Toast node. The wrapper tag alternates so React re-mounts it and the CSS fade animation restarts."""
    global _toast_n
    _toast_n += 1
    return [_WRAPPERS[_toast_n % 2](toast(title, tone, desc))]


def build_page(path: str, qs: dict):
    if path == "/inventory":
        return pages.inventory_page(qs.get("cat", "all"))
    if path == "/sales":
        return pages.sales_page()
    if path == "/checkout":
        return pages.checkout_page()
    if path == "/analytics":
        return pages.analytics_page()
    if path == "/decisions":
        return pages.decisions_page()
    if path == "/history":
        return pages.history_page(qs.get("product", "all"))
    if path == "/settings":
        return pages.settings_page()
    return pages.overview_page()


# ============================================================================= layout
def serve_layout():
    return html.Div([
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="refresh", data=0),         # bumped after every write -> pages re-render
        dcc.Store(id="modal", data=None),        # {"kind": "sale"|"add"|"adjust"|"receipt"|"reseed", "sku": ...}
        dcc.Store(id="drawer-sku", data=None),   # SKU shown in the product drawer
        html.Div(className="atmosphere"),
        html.Div([
            html.Aside([
                dcc.Link([html.Span(icon("leaf", 19), className="brand-mark"),
                          html.Span([html.Span("Meridian", className="brand-name"),
                                     html.Span("Inventory IQ", className="brand-sub")])], href="/", className="brand"),
                html.Nav(id="nav", className="nav"),
                html.Div([html.Span(className="live-dot"),
                          html.Span("Database live", style={"fontSize": 11, "fontWeight": 600, "color": "#9cb3a4"}),
                          html.Span("v0.9", className="num ml-auto", style={"fontSize": 10, "color": "#5f7466"})],
                         className="side-foot"),
            ], className="side glass-nav"),
            html.Div([
                html.Header(id="topbar", className="topbar glass-top"),
                html.Main(html.Div(id="page", className="page"), className="content"),
            ], className="main"),
        ], className="app"),
        html.Div(id="drawer-host"),
        html.Div(id="modal-host"),
        html.Div(id="toasts", className="toasts"),
    ])


app.layout = serve_layout


# ============================================================================ routing
@app.callback(Output("nav", "children"), Output("topbar", "children"), Output("page", "children"),
              Input("url", "pathname"), Input("url", "search"))
def route(pathname, search):
    path = _norm(pathname)
    return pages.sidebar_nav(path), pages.topbar(path), build_page(path, _qs(search))


@app.callback(Output("page", "children", allow_duplicate=True), Input("refresh", "data"),
              State("url", "pathname"), State("url", "search"), prevent_initial_call=True)
def rerender(_, pathname, search):
    """After any write, rebuild the current page so every KPI and chart reflects the new data."""
    return build_page(_norm(pathname), _qs(search))


# ============================================================================ drawer
# NOTE (Dash rule): a callback is skipped only when *all* its inputs are missing from the page; a mix of present and
# absent inputs raises "nonexistent object". So every callback below only mixes ids that always appear together.
@app.callback(Output("drawer-sku", "data"), Input("url", "pathname"), Input("url", "search"))
def drawer_from_url(pathname, search):
    """Deep links such as /inventory?focus=COF-001 open the drawer; any other navigation closes it."""
    return _qs(search).get("focus") if _norm(pathname) == "/inventory" else None


@app.callback(Output("drawer-sku", "data", allow_duplicate=True),
              Input({"type": "inv-row", "sku": ALL}, "n_clicks"), prevent_initial_call=True)
def drawer_from_row(_):
    if not ctx.triggered or not ctx.triggered[0]["value"] or not isinstance(ctx.triggered_id, dict):
        raise PreventUpdate
    return ctx.triggered_id["sku"]


@app.callback(Output("drawer-sku", "data", allow_duplicate=True),
              Input("dr-close", "n_clicks"), Input("dr-backdrop", "n_clicks"), prevent_initial_call=True)
def drawer_close(*_):
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        raise PreventUpdate
    return None


@app.callback(Output("drawer-host", "children"), Input("drawer-sku", "data"), Input("refresh", "data"))
def drawer_host(sku, _):
    return pages.drawer(sku) if sku else None


# ============================================================================= modals
@app.callback(Output("modal-host", "children"), Input("modal", "data"))
def modal_host(m):
    if not m:
        return None
    kind = m.get("kind")
    if kind == "sale":
        return pages.sale_modal()
    if kind == "add":
        return pages.add_modal()
    if kind == "reseed":
        return pages.reseed_modal()
    p = _product_by_sku(m.get("sku"))
    if not p:
        return None
    return pages.adjust_modal(p) if kind == "adjust" else pages.receipt_modal(p) if kind == "receipt" else None


# --- sale modal helpers ------------------------------------------------------------
@app.callback(Output("sale-price", "value"), Input("sale-product", "value"), prevent_initial_call=True)
def sale_price_from_product(pid):
    p = _product_by_id(pid)
    if not p:
        raise PreventUpdate
    return round(p["price"] / 100, 2)


@app.callback(Output("sale-qty", "value"), Input("sale-minus", "n_clicks"), Input("sale-plus", "n_clicks"),
              State("sale-qty", "value"), State("sale-product", "value"), prevent_initial_call=True)
def sale_qty_step(_m, _p, qty, pid):
    trig = ctx.triggered_id
    if trig not in ("sale-minus", "sale-plus"):
        raise PreventUpdate
    p = _product_by_id(pid)
    q = (_int(qty) or 1) + (1 if trig == "sale-plus" else -1)
    top = max(1, p["stock"]) if p else 10 ** 6
    return max(1, min(top, q))


@app.callback(Output("sale-line", "children"), Output("sale-total", "children"), Output("sale-submit", "children"),
              Input("sale-product", "value"), Input("sale-qty", "value"), Input("sale-price", "value"))
def sale_totals(pid, qty, price):
    p = _product_by_id(pid)
    q, pr = _int(qty) or 0, _num(price) or 0.0
    total = f"₹{q * pr:,.2f}"
    line = ""
    if p:
        line = f"{q} × ₹{pr:,.2f} · {p['stock']} in stock"
        if q > p["stock"]:
            line += f" — only {p['stock']} available"
    return line, total, [icon("check", 15), f"Record · {total}"]


@app.callback(Output("adj-preview", "children"), Input("adj-dir", "value"), Input("adj-qty", "value"),
              State("modal", "data"))
def adjust_preview(direction, qty, m):
    p = _product_by_sku((m or {}).get("sku"))
    if not p:
        raise PreventUpdate
    q = _int(qty) or 0
    new = p["stock"] + (q if direction == "add" else -q)
    if new < 0:
        return f"Can't go below zero — only {p['stock']} on hand."
    return f"{p['stock']} → {new} units · updates cover days and alerts"


@app.callback(Output("rcv-preview", "children"), Input("rcv-qty", "value"), State("modal", "data"))
def receipt_preview(qty, m):
    p = _product_by_sku((m or {}).get("sku"))
    if not p:
        raise PreventUpdate
    return f"{p['stock']} → {p['stock'] + (_int(qty) or 0)} units · updates cover days and alerts"


# --- open / close ----------------------------------------------------------------------
def _register_open(btn_id, kind, needs_sku=False):
    states = [State("drawer-sku", "data")] if needs_sku else []

    @app.callback(Output("modal", "data", allow_duplicate=True), Input(btn_id, "n_clicks"), *states,
                  prevent_initial_call=True)
    def _open(n, *st):
        if not n:
            raise PreventUpdate
        if needs_sku:
            if not st[0]:
                raise PreventUpdate
            return {"kind": kind, "sku": st[0]}
        return {"kind": kind}


for _b, _k in (("btn-sale", "sale"), ("btn-sale-page", "sale"), ("btn-add", "add"), ("st-reseed", "reseed")):
    _register_open(_b, _k)
_register_open("dr-receipt", "receipt", needs_sku=True)
_register_open("dr-adjust", "adjust", needs_sku=True)


@app.callback(Output("modal", "data", allow_duplicate=True),
              Input("m-cancel", "n_clicks"), Input("m-close", "n_clicks"), Input("m-backdrop", "n_clicks"),
              prevent_initial_call=True)
def close_modal(*_):
    if not ctx.triggered or not ctx.triggered[0]["value"]:
        raise PreventUpdate
    return None


# --- writes: one callback per form, each only touching ids that live together ----------
def OUTS():
    return [Output("modal", "data", allow_duplicate=True), Output("toasts", "children", allow_duplicate=True),
            Output("refresh", "data", allow_duplicate=True)]


def _res(refresh, modal=no_update, toast_=no_update, bump=False):
    return modal, toast_, ((refresh or 0) + 1 if bump else no_update)


def _fail(title, desc):
    return no_update, _toast(title, "warn", desc), no_update


@app.callback(*OUTS(), Input("sale-submit", "n_clicks"), State("sale-product", "value"), State("sale-qty", "value"),
              State("sale-price", "value"), State("sale-customer", "value"), State("sale-channel", "value"),
              State("refresh", "data"), prevent_initial_call=True)
def sale_submit(n, pid, qty, price, customer, channel, refresh):
    if not n:
        raise PreventUpdate
    qty, price = _int(qty), _num(price)
    if pid is None or not qty or qty < 1:
        return _fail("Check the quantity", "Quantity must be at least 1.")
    if price is None or price <= 0:
        return _fail("Check the price", "Enter a unit price above zero.")
    p = _product_by_id(pid)
    ok, msg = db.record_sale(int(pid), qty, int(round(price * 100)), customer or "", channel or "counter")
    if not ok:
        return _fail("Couldn't record sale", msg)
    return _res(refresh, None, _toast("Sale recorded", "ok", f"{qty} × {p['name'] if p else 'item'} · ₹{qty * price:,.2f} — stock and analytics updated."), True)


@app.callback(*OUTS(), Input("add-submit", "n_clicks"), State("add-name", "value"), State("add-sku", "value"),
              State("add-cat", "value"), State("add-cost", "value"), State("add-price", "value"),
              State("add-stock", "value"), State("add-rp", "value"), State("add-rq", "value"),
              State("add-lead", "value"), State("add-desc", "value"), State("refresh", "data"),
              prevent_initial_call=True)
def add_submit(n, name, sku, cat, cost, price, stock, rp, rq, lead, desc, refresh):
    if not n:
        raise PreventUpdate
    name, cost, price = (name or "").strip(), _num(cost), _num(price)
    if not name:
        return _fail("Name required", "Give the product a name.")
    if cost is None or cost < 0 or price is None or price <= 0:
        return _fail("Check cost and price", "Enter a cost and a selling price above zero.")
    ok, msg = db.add_product(dict(
        name=name, sku=sku or "", category=cat or "Accessories", cost=cost, price=price,
        stock=max(0, _int(stock) or 0), reorderPoint=max(0, _int(rp) or 0), reorderQty=max(0, _int(rq) or 0),
        leadTimeDays=max(0, _int(lead) or 0), description=(desc or "").strip()))
    if not ok:
        return _fail("Couldn't add product", msg)
    return _res(refresh, None, _toast("Product added", "ok", f"{name} · {msg}"), True)


@app.callback(*OUTS(), Input("adj-submit", "n_clicks"), State("adj-dir", "value"), State("adj-qty", "value"),
              State("adj-note", "value"), State("modal", "data"), State("refresh", "data"), prevent_initial_call=True)
def adjust_submit(n, direction, qty, note, modal, refresh):
    if not n:
        raise PreventUpdate
    p = _product_by_sku((modal or {}).get("sku"))
    if not p:
        return _fail("Product not found", "Close this dialog and try again.")
    q = _int(qty)
    if not q or q < 1:
        return _fail("Check the quantity", "Quantity must be at least 1.")
    delta = q if direction == "add" else -q
    ok, msg = db.adjust_stock(p["id"], delta, (note or "").strip())
    if not ok:
        return _fail("Couldn't update stock", msg)
    return _res(refresh, None, _toast("Stock adjusted", "ok", f"{p['name']} · {delta:+d} units"), True)


@app.callback(*OUTS(), Input("rcv-submit", "n_clicks"), State("rcv-qty", "value"), State("rcv-note", "value"),
              State("modal", "data"), State("refresh", "data"), prevent_initial_call=True)
def receipt_submit(n, qty, note, modal, refresh):
    if not n:
        raise PreventUpdate
    p = _product_by_sku((modal or {}).get("sku"))
    if not p:
        return _fail("Product not found", "Close this dialog and try again.")
    q = _int(qty)
    if not q or q < 1:
        return _fail("Check the quantity", "Quantity must be at least 1.")
    ok, msg = db.receive_stock(p["id"], q, (note or "").strip())
    if not ok:
        return _fail("Couldn't update stock", msg)
    return _res(refresh, None, _toast("Receipt logged", "ok", f"{p['name']} · +{q} units"), True)


@app.callback(*OUTS(), Input("reseed-confirm", "n_clicks"), State("refresh", "data"), prevent_initial_call=True)
def reseed_confirm(n, refresh):
    if not n:
        raise PreventUpdate
    db.reseed()
    return _res(refresh, None, _toast("Demo data regenerated", "ok", "Fresh 210-day dataset loaded."), True)


@app.callback(*OUTS(), Input("dr-rp-save", "n_clicks"), State("dr-rp", "value"), State("drawer-sku", "data"),
              State("refresh", "data"), prevent_initial_call=True)
def reorder_point_save(n, rp, sku, refresh):
    if not n:
        raise PreventUpdate
    p, rp = _product_by_sku(sku), _int(rp)
    if not p or rp is None or rp < 0:
        return _fail("Check the reorder point", "Enter a number of 0 or more.")
    db.set_reorder_point(p["id"], rp)
    return _res(refresh, toast_=_toast("Reorder point updated", "ok", f"{p['name']} · reorder at {rp}"), bump=True)


@app.callback(*OUTS(), Input("st-save-company", "n_clicks"), State("st-company", "value"),
              State("st-currency", "value"), State("refresh", "data"), prevent_initial_call=True)
def company_save(n, company, currency, refresh):
    if not n:
        raise PreventUpdate
    company = (company or "").strip() or db.DEFAULT_SETTINGS["company"]
    db.save_settings({"company": company, "currency": (currency or "").strip()[:3] or "₹"})
    return _res(refresh, toast_=_toast("Profile saved", "ok", company), bump=True)


@app.callback(*OUTS(), Input("st-save-policy", "n_clicks"), State("st-order", "value"), State("st-hold", "value"),
              State("st-over", "value"), State("st-dead", "value"), State("st-surge", "value"),
              State("refresh", "data"), prevent_initial_call=True)
def policy_save(n, order, hold, over, dead, surge, refresh):
    if not n:
        raise PreventUpdate
    cur = db.load_core()["s"]
    db.save_settings({
        "orderCost": _int(order) or cur["orderCost"],
        "holdingPct": (_int(hold) or round(cur["holdingPct"] * 100)) / 100,
        "overstockDays": _int(over) or cur["overstockDays"],
        "deadStockDays": _int(dead) or cur["deadStockDays"],
        "surgePct": _int(surge) or cur["surgePct"]})
    return _res(refresh, toast_=_toast("Policy applied", "ok", "Recommendations recalculated."), bump=True)


# ======================================================================= settings sliders
@app.callback(Output("st-l-order", "children"), Output("st-l-hold", "children"), Output("st-l-over", "children"),
              Output("st-l-dead", "children"), Output("st-l-surge", "children"),
              Input("st-order", "value"), Input("st-hold", "value"), Input("st-over", "value"),
              Input("st-dead", "value"), Input("st-surge", "value"))
def slider_labels(order, hold, over, dead, surge):
    return (f"Cost per purchase order — {an.num(_num(order) or 0)} ₹",
            f"Annual holding cost — {_int(hold)}% of unit cost",
            f"Overstock threshold — {_int(over)} days of cover",
            f"Dead stock window — no sales for {_int(dead)} days",
            f"Surge trigger — weekly demand +{_int(surge)}% vs. baseline")


# ============================================================================= overview
@app.callback(
    Output("ov-kpis-wrap", "children"),
    Output("ov-donut-card", "children"),
    Output("ov-top-card", "children"),
    Input("ov-range", "value"),
    prevent_initial_call=True
)
def update_overview_dynamic(rng):
    rng = int(rng or 30)
    o = an.overview(days=rng)
    return pages.ov_kpis_content(o, rng), pages.ov_donut_content(o, rng), pages.ov_top_content(o, rng)
@app.callback(Output("ov-trend", "figure"), Input("ov-metric", "value"), Input("ov-range", "value"))
def ov_trend(metric, rng):
    rng = int(rng or 30)
    return charts.trend_fig(an.build_trend(db.load_core()["sales"], rng), metric or "revenue", brush=rng == 90)


@app.callback(Output("ov-detail", "children"),
              Input("ov-trend", "clickData"), Input("ov-metric", "value"), Input("ov-range", "value"),
              Input({"type": "ov-clear", "i": ALL}, "n_clicks"), State("ov-range", "value"))
def ov_detail(click, _metric, _rng, _clear, rng):
    if ctx.triggered_id != "ov-trend" or not click:
        return pages.detail_hint()
    day = click["points"][0].get("x")
    core = db.load_core()
    pt = next((t for t in an.build_trend(core["sales"], int(rng or 30)) if t["d"] == str(day)[:10]), None)
    if not pt:
        return pages.detail_hint()
    sep = html.Span("·", style={"color": "#5f7466"})
    return html.Div(html.Div([
        html.Span(className="dot"), html.Span(pt["label"], className="num", style={"fontWeight": 600, "color": "#e9f2ea"}),
        html.Span(f"{an.money(pt['revenue'], core['s']['currency'])} revenue"), sep, html.Span(f"{pt['units']} units"),
        sep, html.Span(f"{pt['orders']} orders"),
        html.Button("clear", id={"type": "ov-clear", "i": 0}, n_clicks=0, style={"color": "#5f7466", "marginLeft": 4})],
        className="detail-line"), className="hint-line")


# =========================================================================== inventory
def filter_inventory(items, q, cat, status, sort):
    needle = (q or "").strip().lower()
    rows = [p for p in items
            if (not cat or cat == "all" or p["category"] == cat)
            and (not status or status == "all" or p["stats"]["status"] == status)
            and (not needle or needle in f"{p['sku']} {p['name']}".lower())]
    key = {"price": lambda p: p["price"], "stock": lambda p: p["stock"], "velocity": lambda p: p["stats"]["velocity"],
           "cover": lambda p: 99999 if p["stats"]["coverDays"] is None else p["stats"]["coverDays"],
           "value": lambda p: p["stats"]["value"]}.get(sort["k"], lambda p: p["name"].lower())
    return sorted(rows, key=key, reverse=sort["dir"] == -1)


SORT_KEYS = ["name", "price", "stock", "velocity", "cover", "value"]


@app.callback(Output("inv-sort", "data"), [Input(f"sort-{k}", "n_clicks") for k in SORT_KEYS],
              State("inv-sort", "data"), prevent_initial_call=True)
def inv_sort(*args):
    cur = args[-1]
    for t in ctx.triggered or []:
        if t["value"]:
            k = t["prop_id"].split(".")[0][len("sort-"):]
            return {"k": k, "dir": -cur["dir"] if cur["k"] == k else 1}
    raise PreventUpdate


@app.callback(Output("inv-head", "children"), Input("inv-sort", "data"))
def inv_head(sort):
    return pages.inv_head(sort)


@app.callback(Output("inv-body", "children"), Output("inv-sub", "children"),
              Input("inv-q", "value"), Input("inv-cat", "value"), Input("inv-status", "value"), Input("inv-sort", "data"))
def inv_body(q, cat, status, sort):
    core = db.load_core()
    items = an.enriched(core)
    rows = filter_inventory(items, q, cat, status, sort)
    return pages.inv_rows(rows, core["s"]["currency"]), f"{len(rows)} of {len(items)} SKUs · click a row for detail"


# ============================================================================== sales
def filter_sales(rows, q, channel, rng):
    now, needle = time.time(), (q or "").strip().lower()
    return [r for r in rows
            if (not channel or channel == "all" or r["channel"] == channel)
            and (rng == "all" or (now - r["at"]) / DAY <= float(rng))
            and (not needle or needle in f"{r['sku']} {r['productName']} {r['customer']}".lower())]


@app.callback(Output("sl-body", "children"), Output("sl-sub", "children"), Output("sales-kpis-wrap", "children"),
              Input("sl-q", "value"), Input("sl-ch", "value"), Input("sl-range", "value"))
def sl_body(q, channel, rng):
    d = an.sales_page()
    rng_val = rng or "30"
    rows = filter_sales(d["rows"], q, channel, rng_val)
    sym = d["s"]["currency"]
    
    rng_labels = {"1": "Today", "7": "7 days", "30": "30 days", "all": "All time"}
    label = rng_labels.get(rng_val, rng_val)
    
    kpis = pages.sales_kpis_content(rows, sym, label)
    
    return pages.sales_rows(rows, sym), f"{len(rows)} shown · {an.money(sum(r['total'] for r in rows), sym)} · click a row to inspect", kpis


# ============================================================================= analytics
@app.callback(Output("an-trend", "figure"), Output("an-sub", "children"),
              Input("an-metric", "value"), Input("an-range", "value"))
def an_trend(metric, rng):
    metric, rng = metric or "revenue", int(rng or 30)
    sales = db.load_core()["sales"]
    cur, prev = an.build_trend(sales, rng), an.build_trend(sales, rng, rng)
    tc, tp = sum(p[metric] for p in cur), sum(p[metric] for p in prev)
    delta = an.delta_vs_prior(tc, tp)
    total = tc / 100 if metric == "revenue" else tc
    sub = f"{an.num(total, 0)} {metric} in {rng}d · {'+' if delta >= 0 else ''}{delta * 100:.1f}% vs. the prior {rng} days"
    return charts.trend_fig(cur, metric, prev, brush=rng == 90), sub


# ============================================================================== history
def filter_history(rows, pid, typ, rng, q, current_stock):
    now, needle = time.time(), (q or "").strip().lower()
    out = [r for r in rows
           if (pid is None or r["productId"] == pid)
           and (not typ or typ == "all" or r["type"] == typ)
           and (rng == "all" or (now - r["at"]) / DAY <= float(rng))
           and (not needle or needle in f"{r['note']} {r['productName']} {r['sku']}".lower())]
    # running stock is only exact for the full, unfiltered ledger of a single product
    if pid is not None and current_stock is not None and typ == "all" and rng == "all" and not needle:
        running, with_running = current_stock, []
        for r in out:                       # newest first -> subtract after capturing
            with_running.append(dict(r, running=running))
            running -= r["qty"]
        out = with_running
    return out


@app.callback(Output("hi-chart", "children"), Output("hi-table", "children"), Output("hi-sub", "children"), Output("hi-kpis-wrap", "children"),
              Input("hi-product", "value"), Input("hi-type", "value"), Input("hi-range", "value"), Input("hi-q", "value"))
def hi_body(product, typ, rng, q):
    d = an.history_page()
    sel = next((p for p in d["products"] if p["sku"] == product), None)
    rng_val = rng or "30"
    rows = filter_history(d["rows"], sel["id"] if sel else None, typ or "all", rng_val, q, sel["stock"] if sel else None)
    net = sum(r["qty"] for r in rows)
    chart = None
    if sel:
        series = an.stock_series(d["movements"], sel["id"], sel["stock"], 90)
        chart = card([section_head(f"{sel['name']} · stock level", "90 days · every sale, receipt and adjustment reflected",
                                   html.Button("Show all products →", id="hi-clear", n_clicks=0,
                                               style={"fontSize": 12, "fontWeight": 600, "color": "#8fc49b"})),
                      pages.graph(None, charts.step_fig(series), 190)])
    sub = f"{len(rows)} entries · net {'+' if net >= 0 else ''}{an.num(net)} units in the current view"
    
    rng_labels = {"1": "Today", "7": "7 days", "30": "30 days", "90": "90 days", "all": "All time"}
    label = rng_labels.get(rng_val, rng_val)
    kpis = pages.history_kpis_content(rows, label)
    
    return chart, pages.history_table(rows, sel is not None), sub, kpis


@app.callback(Output("hi-product", "value"), Input("hi-clear", "n_clicks"), prevent_initial_call=True)
def hi_clear(n):
    if not n:
        raise PreventUpdate
    return "all"


# ===================================================================== chart click-through
def _nav(graph_id, builder):
    @app.callback(Output("url", "href", allow_duplicate=True), Input(graph_id, "clickData"), prevent_initial_call=True)
    def _go(data):
        if not data:
            raise PreventUpdate
        return builder(data["points"][0])


_nav("ov-donut", lambda pt: f"/inventory?cat={quote(str(pt['label']))}")
_nav("an-cat", lambda pt: f"/inventory?cat={quote(str(pt['x']))}")
_nav("an-sc", lambda pt: f"/inventory?focus={quote(str(pt['customdata'][0]))}")


# ================================================================================= main
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=8050)