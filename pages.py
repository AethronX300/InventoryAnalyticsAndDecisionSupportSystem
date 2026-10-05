"""Meridian · Inventory IQ — page layouts (Overview, Inventory, Sales, Analytics, Decisions, History, Settings)."""
from __future__ import annotations

from datetime import datetime

from dash import dcc, html

import analytics as an
import charts
import database as db
from analytics import fmt_dt, money, money_compact, num
from ui import (btn, card, chips, count_int, count_money, cx, delay, delta_node, dropdown, empty_state, eyebrow, field,
                icon, kpi_card, link_btn, modal, pill, progress, ring, search_box, section_head, segmented, stat_card,
                status_pill)

GRAPH_CFG = {"displayModeBar": False, "responsive": True}
REC_ICON = {"stockout": "alert", "reorder": "truck", "surge": "pulse", "overstock": "box", "dead": "tag", "watch": "info"}
SEV_TONE = {"critical": "crit", "warning": "warn", "opportunity": "info", "info": "info"}
CLS_COLOR = {"A": "#8fc49b", "B": "#d9a45b", "C": "#7fb0c9"}
TOP_SHADES = ["#8fc49b", "#74b490", "#63a682", "#539873", "#448a63"]
NAV = [("/", "Overview", "grid"), ("/inventory", "Inventory", "box"), ("/sales", "Sales", "receipt"),
       ("/analytics", "Analytics", "chart"), ("/decisions", "Decisions", "compass"),
       ("/history", "Stock History", "clock"), ("/settings", "Settings", "sliders")]
TITLES = {"/": ("Overview", "Business position at a glance"), "/inventory": ("Inventory", "Products, stock levels and health"),
          "/sales": ("Sales", "Transactions and point of sale"), "/checkout": ("Checkout", "Point of Sale Terminal"),
          "/analytics": ("Analytics", "Demand, performance and patterns"),
          "/decisions": ("Decisions", "Data-driven recommendations"), "/history": ("Stock History", "Every movement, auditable"),
          "/settings": ("Settings", "Preferences, policy and data")}


def graph(id, fig, h, cls="", **kw):
    if id is not None:          # newer Dash rejects id=None
        kw["id"] = id
    return dcc.Graph(figure=fig, className=cls, style={"height": f"{h}px", "width": "100%"}, config=GRAPH_CFG, **kw)


def hbars(rows, d0=0):
    """Clickable horizontal bar list. rows: (href, name, value, share 0-1, color, tooltip)."""
    out = []
    for i, (href, name, share, color, tip) in enumerate(rows):
        out.append(dcc.Link([
            html.Span(name, className="nm", style={"width": 150, "textAlign": "right", "flex": "none"}),
            html.Div(html.Div(html.Div(className="fill grow-w", style={"--w": f"{max(2, share * 100):.1f}%", "background": color, **delay(d0 + i * 70)}),
                              className="bar thick"), className="grow tip", **{"data-tip": tip}),
        ], href=href, className="hrow", style={"padding": "7px 4px"}))
    return html.Div(out, className="stack6")


# ============================================================================ sidebar / header
def sidebar_nav(pathname: str):
    return [dcc.Link([icon(i, 16), label], href=p, className=cx("nav-item", "active" if p == pathname else ""))
            for p, label, i in NAV]


def topbar(pathname: str):
    t, s = TITLES.get(pathname, TITLES["/"])
    d = datetime.now()
    return [html.Div([html.H1(t), html.P(s)]),
            html.Div([html.Span(f"{d.strftime('%b')} {d.day}, {d.year}", className="num", style={"fontSize": 11.5, "color": "#7d9485"}),
                      btn("Record sale", id="btn-sale", variant="primary", ic="plus")], className="row-flex gap12 ml-auto")]


# ================================================================================== overview
def ov_kpis_content(o, days):
    s, sym = o["s"], o["s"]["currency"]
    def spark(vals, color, money=False):
        return graph(None, charts.sparkline(vals, color, money), 40, "kpi-spark wipe-x")

    day_lbl = "Today" if days == 1 else f"{days} days"
    
    return [
        kpi_card(f"Revenue · {day_lbl}", count_money(o["rev"], sym), "pulse", delta_node(o["revDelta"]),
                 spark(o["revSpark"], "#7fb48d", True), href="/analytics", d=0),
        kpi_card(f"Units sold · {day_lbl}", count_int(o["u"]), "tag", delta_node(o["unitsDelta"]),
                 spark(o["unitsSpark"], "#7fb0c9"), sub=f"{num(o['u'] / days, 1)} units per day", d=60),
        kpi_card("Inventory value", count_money(o["invValue"], sym), "layers", sub=f"{s['company']} · at cost",
                 href="/inventory", d=120),
        kpi_card("Products at risk", count_int(o["riskCount"]), "alert",
                 sub=f"{money(o['riskValue'], sym)} of stock value · critical or out", href="/decisions", d=180),
    ]

def ov_donut_content(o, days):
    s, sym = o["s"], o["s"]["currency"]
    tcats = sum(c["revenue"] for c in o["categories"]) or 1
    day_lbl = "Today" if days == 1 else f"Last {days} days"
    tot_lbl = "Today" if days == 1 else f"{days}d"
    return [
        section_head("Revenue by category", f"{day_lbl} · click to explore"),
        html.Div([graph("ov-donut", charts.donut_fig(o["categories"]), 250, "spin-in dg"),
                  html.Div([eyebrow(f"Total {tot_lbl}"), html.Span(money_compact(tcats, sym), className="num big")], className="donut-center")],
                 className="donut-wrap"),
        html.Div([dcc.Link([html.Span(className="sw", style={"background": c["color"]}), html.Span(c["name"], className="nm"),
                            html.Span(money(c["revenue"], sym), className="num ml-auto", style={"color": "#c5d6c9"}),
                            html.Span(f"{c['revenue'] / tcats * 100:.0f}%", className="num t-r", style={"color": "#67806f", "width": 40})],
                           href=f"/inventory?cat={c['name']}", className="legend-row") for c in o["categories"][:4]], className="legend"),
    ]

def ov_top_content(o, days):
    s, sym = o["s"], o["s"]["currency"]
    mx = max((t["revenue"] for t in o["top"]), default=1) or 1
    day_lbl = "Today" if days == 1 else f"{days}-day"
    return [
        section_head("Top products", f"By {day_lbl} revenue · click to open in inventory"),
        hbars([(f"/inventory?focus={t['sku']}", t["name"] if len(t["name"]) < 27 else t["name"][:25] + "…", t["revenue"] / mx,
                TOP_SHADES[i], f"{t['name']} · {money(t['revenue'], sym)}") for i, t in enumerate(o["top"])])
    ]

def overview_page():
    days = 30
    o = an.overview(days=days)
    
    kpis = html.Div(ov_kpis_content(o, days), id="ov-kpis-wrap", className="grid kpis")

    trend = card([
        section_head("Sales trend", "Click a point to inspect the day", html.Div([
            segmented("ov-metric", [("revenue", "Revenue"), ("units", "Units"), ("orders", "Orders")], "revenue"),
            segmented("ov-range", [(1, "Today"), (14, "14d"), (30, "30d"), (90, "90d")], 30)], className="row-flex gap8")),
        graph("ov-trend", charts.trend_fig(o["trend"][30], "revenue"), 272, "wipe-x"),
        html.Div(id="ov-detail", children=detail_hint()),
    ], cls="card xl8", d=120)

    donut = card(ov_donut_content(o, days), id="ov-donut-card", cls="card xl4", d=180)
    top = card(ov_top_content(o, days), id="ov-top-card", cls="card lg5", d=240)

    health = card([
        section_head("Inventory health", "Weighted by stock value"),
        html.Div([ring(o["health"]["score"], "Health"),
                  html.Div([html.Div([
                      html.Div([html.Span(sg["label"], className=f"t-{sg['tone']}", style={"fontWeight": 600}),
                                html.Span(f"{sg['count']} SKU", className="num", style={"color": "#7d9485"})],
                               className="row-flex", style={"justifyContent": "space-between", "fontSize": 11, "marginBottom": 4}),
                      progress(max(.03, sg["share"]), sg["tone"], 300 + i * 90)]) for i, sg in enumerate(o["health"]["segments"][:5])],
                           className="stack", style={"flex": 1, "minWidth": 0})], className="row-flex gap12", style={"gap": 16}),
        dcc.Link("Open inventory →", href="/inventory", className="link-moss t-c", style={"display": "block", "marginTop": 16}),
    ], cls="card lg4", d=300)

    alerts = card([section_head("Needs attention", "Live alerts"),
                   html.Div([dcc.Link([html.Div([pill("opp" if a["severity"] == "opportunity" else a["severity"], SEV_TONE[a["severity"]], dot=True),
                                                 html.Span(a["sku"], className="num ml-auto", style={"fontSize": 10, "color": "#67806f"})],
                                                className="row-flex gap8"),
                                       html.P(a["headline"], className="clamp2")],
                                      href=f"/inventory?focus={a['sku']}", className="alert-card glass-inset") for a in o["alerts"][:4]],
                            className="stack")], cls="card lg3", d=360)

    recs = card([section_head("Decision engine", "Highest-priority recommendations right now",
                              dcc.Link("View all decisions →", href="/decisions", className="link-moss")),
                 html.Div([dcc.Link([html.Div([html.Span(icon(REC_ICON.get(r["type"], "info"), 14), className=f"ric {SEV_TONE[r['severity']]}"),
                                               html.Span(r["sku"], className="num", style={"fontSize": 11, "fontWeight": 700, "color": "#7d9485"}),
                                               html.Span(icon("external", 12), className="ext")], className="row-flex gap8", style={"marginBottom": 8}),
                                     html.P(r["headline"], className="hd clamp2"), html.P(r["action"], className="ac")],
                                    href=f"/inventory?focus={r['sku']}", className="rec glass-inset lift rise", style=delay(480 + i * 70))
                           for i, r in enumerate(o["recs"][:4])], className="grid cols-rec")], cls="card", d=420)

    return [kpis, html.Div([trend, donut], className="grid g12"), html.Div([top, health, alerts], className="grid g12"), recs]


def detail_hint():
    return html.Div(html.Span("Hover for values · drag the brush on 90d to zoom · figures refresh after every sale"), className="hint-line")


# ================================================================================== inventory
INV_COLS = "minmax(190px,2.4fr) 80px minmax(140px,1.4fr) 112px 92px 84px 84px"
STATUS_FILTERS = [("all", "All"), ("healthy", "Healthy"), ("low", "Low"), ("critical", "Critical"), ("out", "Out"),
                  ("overstock", "Overstock"), ("dead", "Dead")]


def inventory_page(cat="all"):
    d = an.inventory()
    t, sym = d["totals"], d["s"]["currency"]
    cats = sorted({i["category"] for i in d["items"]})
    return [
        html.Div([stat_card("SKUs tracked", num(t["skus"]), "box", 0), stat_card("Units on hand", num(t["units"]), "layers", 60),
                  stat_card("Stock value (cost)", money(t["value"], sym), "scale", 120),
                  stat_card("Below reorder point", num(t["below"]), "alert", 180)], className="grid kpis"),
        card([
            section_head("Product inventory", html.Span(id="inv-sub"), btn("Add product", id="btn-add", variant="primary", size="sm", ic="plus")),
            html.Div([search_box("inv-q", "Search name or SKU…", 240),
                      dropdown("inv-cat", [{"label": "All categories", "value": "all"}] + [{"label": c, "value": c} for c in cats], cat, 160),
                      chips("inv-status", STATUS_FILTERS, "all")], className="row-flex wrap gap12", style={"marginBottom": 14, "gap": 10}),
            html.Div([html.Div(id="inv-head"), html.Div(id="inv-body")], className="tscroll"),
            dcc.Store(id="inv-sort", data={"k": "name", "dir": 1}),
        ], cls="card", d=160),
    ]


def inv_head(sort: dict):
    def th(k, label, right=False):
        arrow = icon("arrowUp" if sort["dir"] == 1 else "arrowDown", 10) if sort["k"] == k else None
        return html.Div(html.Button([label, arrow], id=f"sort-{k}", n_clicks=0), className="t-r" if right else "")
    return html.Div([th("name", "Product"), th("price", "Price", True), th("stock", "Stock"), html.Div("Status"),
                     th("velocity", "Velocity", True), th("cover", "Cover", True), th("value", "Value", True)],
                    className="trow thead", style={"--cols": INV_COLS})


def inv_rows(items, sym):
    if not items:
        return empty_state("search", "No products match", "Try a different search term, category or status filter.")
    rows = []
    for p in items:
        st = p["stats"]
        ratio = min(1, p["stock"] / max(1, p["reorderPoint"] * 2.2))
        tone = "crit" if st["status"] in ("out", "critical") else "ok" if st["status"] == "healthy" else "warn"
        cover = "—" if st["coverDays"] is None else "400+" if st["coverDays"] > 400 else str(round(st["coverDays"]))
        rows.append(html.Div([
            html.Div([html.P(p["name"], className="tname"), html.P(f"{p['sku']} · {p['category']}", className="tsub num")]),
            html.Div(money(p["price"], sym), className="tc num t-r"),
            html.Div([html.Div([html.Span(p["stock"], className="n num"), html.Div(progress(ratio, tone), style={"flex": 1})], className="stock-cell"),
                      html.P(f"reorder at {p['reorderPoint']}", className="u", style={"marginTop": 4})]),
            html.Div(status_pill(st["status"])),
            html.Div([f"{st['velocity']:.1f} ", html.Span("u/d", className="u")], className="tc num t-r"),
            html.Div([cover + " ", html.Span("d", className="u")], className="tc num t-r"),
            html.Div(money(st["value"], sym), className="tc num t-r"),
        ], id={"type": "inv-row", "sku": p["sku"]}, n_clicks=0, className="trow link", style={"--cols": INV_COLS}))
    return rows


# ---------------------------------------------------------------------------- drawer
MOVE_META = {"sale": ("Sale", "info"), "receipt": ("Receipt", "ok"), "adjustment": ("Adjustment", "warn"), "initial": ("Opening", "neutral")}


def drawer(sku: str):
    d = an.product_detail(sku)
    if not d:
        return None
    p, st, sym, rec = d["item"], d["item"]["stats"], d["s"]["currency"], d["rec"]
    last = ""
    if st["daysSinceSale"]:
        last = "last sale yesterday" if st["daysSinceSale"] == 1 else f"last sale {st['daysSinceSale']}d ago"
    stats = [("Price", money(p["price"], sym)), ("Cost", money(p["cost"], sym)), ("Margin", f"{round(st['marginPct'] * 100)}%"),
             ("Velocity", f"{st['velocity']:.1f} u/d"), ("Cover", "—" if st["coverDays"] is None else f"{round(st['coverDays'])} d"),
             ("Stock value", money(st["value"], sym))]
    moves = []
    for m in d["moves"]:
        lbl, tone = MOVE_META.get(m["type"], MOVE_META["adjustment"])
        moves.append(html.Div([pill(lbl, tone), html.Span(f"{m['qty']:+d}", className=cx("num", "t-ok" if m["qty"] >= 0 else "t-crit"), style={"fontWeight": 700, "fontSize": 12.5}),
                               html.Span(m["note"], className="ellipsis", style={"fontSize": 11.5, "color": "#9cb3a4"}),
                               html.Span(an.fmt_day(m["at"]), className="num ml-auto",
                                         style={"fontSize": 10.5, "color": "#67806f", "whiteSpace": "nowrap"})], className="move glass-inset"))
    return html.Div([
        html.Div(id="dr-backdrop", n_clicks=0, className="backdrop", style={"background": "rgba(4,9,6,.55)"}),
        html.Div([
            html.Div([html.Div([html.Div([pill(p["sku"]), pill(p["category"])], className="row-flex gap8"),
                                html.H2(p["name"], className="disp ellipsis", style={"fontSize": 16, "fontWeight": 700, "color": "#f0f7f2", "marginTop": 6})],
                               style={"minWidth": 0}),
                      html.Button(icon("x", 16), id="dr-close", n_clicks=0, className="icon-btn ml-auto")], className="drawer-head"),
            html.Div([
                html.Div([status_pill(st["status"]), html.Span(last, style={"fontSize": 11, "color": "#7d9485"})], className="row-flex gap8"),
                html.P(p["description"], style={"fontSize": 12, "color": "#9cb3a4", "lineHeight": 1.6, "marginTop": -6}) if p["description"] else None,
                html.Div([html.Div([icon("sparkle", 14), html.Span("Recommendation", className="eyebrow", style={"color": "#e4bd83"})], className="row-flex gap8 t-warn"),
                          html.P(rec["headline"], style={"fontSize": 12.5, "color": "#e9f2ea", "marginTop": 6, "lineHeight": 1.4})], className="rec-box") if rec else None,
                html.Div([html.Div([eyebrow(k), html.P(v, className="num v")], className="mini glass-inset") for k, v in stats], className="grid cols-3"),
                html.Div([eyebrow("Reorder point"),
                          dcc.Input(id="dr-rp", type="number", min=0, value=p["reorderPoint"], className="inp num", style={"width": 84}, debounce=False),
                          btn("Save", id="dr-rp-save", size="sm"),
                          html.Span(f"lead {p['leadTimeDays']}d · case {p['reorderQty']}", className="ml-auto", style={"fontSize": 11, "color": "#67806f"})],
                         className="row-flex gap12 glass-inset", style={"borderRadius": 8, "padding": 12}),
                html.Div([section_head("Stock · 60 days", "Step history incl. sales, receipts, adjustments"),
                          graph("dr-chart", charts.step_fig(d["series"], p["reorderPoint"]), 190, "wipe-x")]),
                html.Div([section_head("Recent movements"), html.Div(moves or html.P("No movements recorded yet.", className="sub"), className="stack6")]),
                html.Div([btn("Log receipt", id="dr-receipt", ic="truck", cls="flex1"), btn("Adjust stock", id="dr-adjust", ic="sliders", cls="flex1")],
                         className="row-flex gap8", style={"paddingBottom": 8}),
            ], className="drawer-body"),
        ], className="drawer glass-pop"),
    ], className="overlay")


# ===================================================================================== sales
SALES_COLS = "112px minmax(170px,2fr) 50px 76px 84px minmax(110px,1fr) 92px 22px"
CH_TONE = {"counter": "neutral", "online": "info", "wholesale": "ok"}


def sales_kpis_content(rows, sym, label):
    rev = sum(r["total"] for r in rows)
    units = sum(r["qty"] for r in rows)
    orders = len(rows)
    aov = (rev / units / 100) if units else 0
    return [
        kpi_card(f"Revenue · {label}", count_money(rev, sym), "pulse", d=0),
        kpi_card(f"Units · {label}", count_int(units), "chart", d=60),
        kpi_card(f"Orders · {label}", count_int(orders), "receipt", d=120),
        kpi_card(f"Avg unit price · {label}", html.Span([sym, html.Span(className="count", style={"--to": int(aov)}), f".{int(round(aov % 1 * 100)):02d}"], className="num"), "tag", d=180),
    ]

def sales_page():
    return [html.Div(id="sales-kpis-wrap", className="grid kpis"), card([
        section_head("Transactions", html.Span(id="sl-sub"), btn("Record sale", id="btn-sale-page", variant="primary", size="sm", ic="plus")),
        html.Div([search_box("sl-q", "Search product, SKU or customer…", 270),
                  dropdown("sl-ch", [{"label": "All channels", "value": "all"}] + [{"label": c.title(), "value": c} for c in ("counter", "online", "wholesale")], "all", 150),
                  segmented("sl-range", [("1", "Today"), ("7", "7 days"), ("30", "30 days"), ("all", "All time")], "30")],
                 className="row-flex wrap", style={"gap": 10, "marginBottom": 14}),
        html.Div([html.Div([html.Div(x, className="t-r" if x in ("Qty", "Unit", "Total") else "") for x in
                            ("When", "Product", "Qty", "Unit", "Total", "Customer", "Channel", "")],
                           className="trow thead", style={"--cols": SALES_COLS}), html.Div(id="sl-body")], className="tscroll"),
    ], cls="card", d=160)]


def sales_rows(rows, sym):
    if not rows:
        return empty_state("receipt", "No transactions match", "Adjust the filters, or record a new sale.")
    out = []
    for r in rows[:300]:
        out.append(html.Details([
            html.Summary([
                html.Div(fmt_dt(r["at"]), className="num", style={"fontSize": 12, "color": "#9cb3a4", "whiteSpace": "nowrap"}),
                html.Div([html.P(r["productName"], className="tname"), html.P(f"{r['sku']} · {r['category']}", className="tsub num")]),
                html.Div(r["qty"], className="tc num t-r"), html.Div(money(r["unitPrice"], sym, 2), className="tc num t-r"),
                html.Div(money(r["total"], sym, 2), className="tc num t-r", style={"fontWeight": 600, "color": "#e9f2ea"}),
                html.Div(r["customer"], className="tc ellipsis", style={"fontSize": 12}),
                html.Div(pill(r["channel"], CH_TONE.get(r["channel"], "neutral"))),
                html.Span(icon("chevronRight", 13), className="chev"),
            ], className="trow link", style={"--cols": SALES_COLS}),
            html.Div([html.Span(["Unit margin", html.B(f"{r['marginPct'] * 100:.0f}%", className="num")], className="k"),
                      html.Span(["Gross profit", html.B(money(r["total"] * r["marginPct"], sym, 2), className="num")], className="k"),
                      html.Span(["Ref", html.B(f"S-{r['id']:05d}", className="num", style={"color": "#c5d6c9"})], className="k"),
                      link_btn("Open product", f"/inventory?focus={r['sku']}", "soft", "sm", "box", "ml-auto")], className="more glass-inset"),
        ], className="sale"))
    return out


# ===================================================================================== checkout
def checkout_page():
    return [card([
        section_head("Checkout Terminal", "Ring up a customer"),
        html.Div([
            html.Div(icon("shopping-cart", 32), className="eb glass-inset", style={"margin": "0 auto 16px"}),
            html.H4("Point of Sale"),
            html.P("Record a transaction, deduct stock, and register revenue."),
            html.Div(btn("Open Sale Terminal", id="btn-sale-page", variant="primary", size="lg", ic="plus"), style={"marginTop": 24})
        ], className="empty", style={"padding": "60px 20px", "textAlign": "center"})
    ], cls="card", d=0)]


# ================================================================================== analytics
def analytics_page():
    d = an.analytics_page()
    s, sym = d["s"], d["s"]["currency"]
    cur = d["ranges"][30]
    abc = d["abc"]
    mxv = max((v["velocity"] for v in d["velocity"]), default=0.001) or 0.001
    fast = d["velocity"][:6]
    slow = [v for v in d["velocity"] if v["velocity"] < 0.12][-6:][::-1]
    maxw = max((w["orders"] for w in d["weekday"]), default=1) or 1

    trend = card([
        section_head("Trend vs. previous period", html.Span(id="an-sub"), html.Div([
            segmented("an-metric", [("revenue", "Revenue"), ("units", "Units"), ("orders", "Orders")], "revenue"),
            segmented("an-range", [(1, "Today"), (14, "14d"), (30, "30d"), (60, "60d"), (90, "90d")], 30)], className="row-flex gap8")),
        graph("an-trend", charts.trend_fig(cur["cur"], "revenue", cur["prev"]), 286, "wipe-x"),
        html.Div([html.Span([html.Span(className="line-sw"), "current period"]), html.Span([html.Span(className="line-sw dash"), "previous period"]),
                  html.Span("drag the brush to zoom · hover for exact values", className="ml-auto", style={"color": "#5f7466"})], className="legend-inline"),
    ], d=0)

    cls_boxes = []
    for c in "ABC":
        rows = [r for r in abc if r["cls"] == c]
        share = sum(r["share"] for r in rows)
        cls_boxes.append(html.Div([html.Div([html.Span(className="dotc", style={"background": CLS_COLOR[c]}),
                                             html.Span(f"Class {c}", style={"fontSize": 11, "fontWeight": 700, "color": "#c5d6c9"}),
                                             html.Span(f"{len(rows)} SKUs", className="num ml-auto", style={"fontSize": 11, "color": "#7d9485"})], className="row-flex gap8"),
                                   html.P([html.Span(className="count", style={"--to": round(share * 100)}), "% ",
                                           html.Span("of revenue", style={"fontSize": 10, "color": "#67806f", "fontWeight": 400})], className="num v")], className="cls-box glass-inset"))
    abc_card = card([
        section_head("ABC analysis", "30-day revenue concentration · 80 / 15 / 5 rule"),
        html.Div(cls_boxes, className="row-flex", style={"gap": 8, "marginBottom": 12}),
        html.Div([dcc.Link([pill(r["cls"], {"A": "ok", "B": "warn", "C": "info"}[r["cls"]], cls="w24"), html.Span(r["name"], className="nm"),
                            html.Div(html.Div(html.Div(className="fill grow-w", style={"--w": f"{min(100, r['share'] * 220):.1f}%", "background": CLS_COLOR[r["cls"]], "opacity": .85, **delay(i * 60)}), className="bar"), className="grow"),
                            html.Span(f"{r['share'] * 100:.1f}%", className="num t-r val-s", style={"width": 52}),
                            html.Span(money(r["revenue"], sym), className="num t-r", style={"fontSize": 11, "color": "#c5d6c9", "width": 64})],
                           href=f"/inventory?focus={r['sku']}", className="hrow") for i, r in enumerate(abc[:7])], className="stack6"),
    ], cls="card xl5", d=90)

    def mover_col(title, ic, items, grad, valcls, digits):
        rows = [dcc.Link([html.Span(v["name"], className="nm", style={"width": 150, "flex": "none"}),
                          html.Div(html.Div(html.Div(className=f"fill grow-w {grad}", style={"--w": f"{max(4, v['velocity'] / mxv * 100):.1f}%", **delay(i * 70)}), className="bar thick"), className="grow"),
                          html.Span(f"{v['velocity']:.{digits}f} u/d", className=cx("num t-r", valcls), style={"fontSize": 11.5, "fontWeight": 600, "width": 62})],
                         href=f"/inventory?focus={v['sku']}", className="hrow") for i, v in enumerate(items)]
        return html.Div([html.P([icon(ic, 11), " ", title], className="eyebrow", style={"marginBottom": 8}),
                         html.Div(rows) if rows else html.P("Nothing dangerously slow right now.", className="sub")])

    movers = card([section_head("Movers", "Trailing 28-day velocity · fast vs. slow"),
                   html.Div([mover_col("Fast movers", "arrowUp", fast, "grad-ok", "t-ok", 1),
                             mover_col("Slow movers", "arrowDown", slow, "grad-warn", "t-warn", 2)], className="grid cols-2", style={"gap": 24})],
                  cls="card xl7", d=150)

    cat = card([section_head("Category performance", "30-day revenue with gross margin · click a bar"),
                graph("an-cat", charts.catperf_fig(d["categories"]), 270, "wipe-y")], cls="card xl6", d=210)
    scat = card([section_head("Velocity vs. margin", f"90-day totals · {money(d['rev90'], sym)} revenue · {money(d['gp90'], sym)} gross profit · bubble = 30d revenue"),
                 graph("an-sc", charts.scatter_fig(d["velocity"]), 270, "wipe-x")], cls="card xl6", d=270)

    week = card([section_head("Weekly rhythm", "Orders by weekday · trailing 28 days"),
                 html.Div([html.Div([html.Span(w["orders"], className=cx("n num", "peak" if w["orders"] == maxw else "")),
                                     html.Div(className=cx("wbar grow-h tip", "peak" if w["orders"] == maxw else ""),
                                              style={"--h": f"{max(3, w['orders'] / maxw * 100):.1f}%", **delay(i * 60)},
                                              **{"data-tip": f"{w['name']}: {w['orders']} orders · {money(w['revenue'], sym)}"}),
                                     html.Span(w["name"], className="d")], className="wcol") for i, w in enumerate(d["weekday"])], className="week")],
                cls="card lg5", d=330)
    top8 = abc[:8]
    mx = max((r["revenue"] for r in top8), default=1) or 1
    leaders = card([section_head("Revenue leaders", "Top 8 products by 30-day revenue · click to inspect"),
                    hbars([(f"/inventory?focus={r['sku']}", r["name"] if len(r["name"]) < 29 else r["name"][:27] + "…", r["revenue"] / mx,
                            CLS_COLOR[r["cls"]], f"{r['name']} · {money(r['revenue'], sym)} · class {r['cls']}") for r in top8])],
                   cls="card lg7", d=390)
    return [trend, html.Div([abc_card, movers], className="grid g12"), html.Div([cat, scat], className="grid g12"), html.Div([week, leaders], className="grid g12")]


# ================================================================================== decisions
def decisions_page():
    d = an.decisions_page()
    sym = d["s"]["currency"]
    groups = [("critical", "Act now", "Revenue is actively at risk"), ("warning", "Monitor & prepare", "Policy thresholds breached or capital idle"),
              ("opportunity", "Opportunities", "Demand signals worth riding")]
    out = [card([html.Div([ring(d["health"]["score"], "Inventory health"),
                           html.Div([html.Div([pill(f"{d['counts']['critical']} critical", "crit", dot=True), pill(f"{d['counts']['warning']} warnings", "warn"),
                                               pill(f"{d['counts']['opportunity']} opportunities", "info")], className="row-flex gap8"),
                                     html.P("Generated from live data: 14-day exponential-smoothing demand forecasts, reorder-point and lead-time checks, EOQ order sizing, "
                                            "days-of-cover policy and dead-stock detection. Every figure links to the product behind it.",
                                            style={"fontSize": 12, "color": "#9cb3a4", "lineHeight": 1.6, "maxWidth": 520})], className="stack", style={"gap": 12})],
                          className="row-flex", style={"gap": 20})], cls="card")]
    for gi, (key, title, sub) in enumerate(groups):
        recs = [r for r in d["recs"] if r["severity"] == key or (key == "opportunity" and r["severity"] == "info")]
        body = (card(empty_state("check", "Nothing here", "No items in this bucket right now — the engine re-evaluates after every change."), cls="card")
                if not recs else
                html.Div([card([
                    html.Div([html.Span(icon(REC_ICON.get(r["type"], "info"), 15), className=cx("ico-box glass-inset", f"t-{SEV_TONE[r['severity']]}")),
                              html.Div([html.P(r["name"], className="ellipsis", style={"fontSize": 13, "fontWeight": 700, "color": "#e9f2ea"}),
                                        html.P(f"{r['sku']} · {r['category']} · priority {round(r['score'])}", className="num", style={"fontSize": 10.5, "color": "#67806f", "marginTop": 2})], style={"minWidth": 0}),
                              pill(r["severity"], SEV_TONE[r["severity"]], dot=r["severity"] == "critical", cls="ml-auto")], className="row-flex gap12", style={"marginBottom": 10}),
                    html.P(r["headline"], style={"fontSize": 12.5, "fontWeight": 600, "color": "#dceade", "lineHeight": 1.35}),
                    html.Ul([html.Li(x) for x in r["reasons"]]),
                    html.Div([html.Span(["" + m["label"], html.B(m["value"], className="num")], className="metric glass-inset") for m in r["metrics"]],
                             className="row-flex wrap", style={"gap": 6, "marginTop": 12}),
                    html.Div([link_btn("Open product", f"/inventory?focus={r['sku']}", "soft", "sm", "box"),
                              link_btn("History", f"/history?product={r['sku']}", "ghost", "sm", "clock"),
                              html.Span(r["action"], className="ml-auto", style={"fontSize": 11, "fontWeight": 600, "color": "#7d9485"})], className="dec-foot"),
                ], cls=f"dec {r['severity']}", d=gi * 80 + i * 60) for i, r in enumerate(recs)],
                         className="grid cols-1-2" if gi == 0 else "grid cols-1-2 cols-1-3"))
        out.append(html.Div([section_head(title, sub, html.Span(f"{len(recs)} items", className="num", style={"fontSize": 12, "color": "#7d9485"})), body]))
    rows = []
    for i, f in enumerate(d["forecast"]):
        tone = "crit" if f["daysLeft"] < 7 else "warn" if f["daysLeft"] < 14 else "ok"
        label = "no demand" if f["daysLeft"] > 400 else "< 1 day" if f["daysLeft"] < 1 else f"~{round(f['daysLeft'])} days"
        rows.append(dcc.Link([html.Span(f["name"], className="nm", style={"width": 220, "flex": "none"}),
                              html.Span(f["sku"], className="num", style={"fontSize": 11, "color": "#67806f", "width": 64}),
                              html.Div(html.Div(html.Div(className=f"fill grow-w {tone}", style={"--w": f"{max(3, min(100, f['daysLeft'] / 60 * 100)):.1f}%", **delay(340 + i * 60)}), className="bar thick"), className="grow"),
                              html.Span(label, className=f"num t-r t-{tone}", style={"fontSize": 12, "fontWeight": 700, "width": 96})],
                             href=f"/inventory?focus={f['sku']}", className="hrow"))
    out.append(card([section_head("Depleting soonest", "Projected days of stock at the trailing 14-day demand rate",
                                  html.Span("exponential smoothing · alpha 0.35", style={"fontSize": 10.5, "color": "#67806f"})),
                     html.Div(rows, className="stack6")], cls="card", d=300))
    return out


# =================================================================================== history
HIST_COLS = "130px minmax(170px,2fr) 100px 70px minmax(150px,2fr)"
HIST_COLS_P = HIST_COLS + " 90px"
TYPE_LABEL = {"sale": ("Sale", "info"), "receipt": ("Receipt", "ok"), "adjustment": ("Adjustment", "warn"), "initial": ("Opening", "neutral")}


def history_kpis_content(rows, label):
    receipts = sum(1 for m in rows if m["type"] == "receipt")
    received = sum(m["qty"] for m in rows if m["type"] == "receipt")
    adjustments = sum(1 for m in rows if m["type"] == "adjustment")
    sold = sum(-m["qty"] for m in rows if m["type"] == "sale")
    return [
        stat_card(f"Receipts · {label}", num(receipts), "truck", 0),
        stat_card(f"Units received · {label}", num(received), "arrowUp", 60),
        stat_card(f"Adjustments · {label}", num(adjustments), "sliders", 120),
        stat_card(f"Units sold · {label}", num(sold), "tag", 180)
    ]

def history_page(product="all"):
    d = an.history_page()
    opts = [{"label": "All products", "value": "all"}] + [{"label": f"{p['name']} · {p['sku']}", "value": p["sku"]} for p in d["products"]]
    return [
        html.Div(id="hi-kpis-wrap", className="grid kpis"),
        html.Div(id="hi-chart"),
        card([section_head("Movement ledger", html.Span(id="hi-sub")),
              html.Div([dropdown("hi-product", opts, product, 270, searchable=True),
                        dropdown("hi-type", [{"label": "All types", "value": "all"}, {"label": "Sales", "value": "sale"}, {"label": "Receipts", "value": "receipt"},
                                             {"label": "Adjustments", "value": "adjustment"}, {"label": "Opening counts", "value": "initial"}], "all", 170),
                        segmented("hi-range", [("1", "Today"), ("7", "7d"), ("30", "30d"), ("90", "90d"), ("all", "All time")], "30"),
                        search_box("hi-q", "Search note or product…", 230)], className="row-flex wrap", style={"gap": 10, "marginBottom": 14}),
              html.Div(id="hi-table", className="tscroll")], cls="card", d=140),
    ]


def history_table(rows, with_stock):
    if not rows:
        return empty_state("clock", "No movements match", "Widen the date range or clear the filters.")
    cols = HIST_COLS_P if with_stock else HIST_COLS
    head = html.Div([html.Div("When"), html.Div("Product"), html.Div("Type"), html.Div("Qty", className="t-r"), html.Div("Note")] +
                    ([html.Div("Stock after", className="t-r")] if with_stock else []), className="trow thead", style={"--cols": cols})
    out = [head]
    for r in rows[:400]:
        lbl, tone = TYPE_LABEL.get(r["type"], (r["type"], "neutral"))
        cells = [html.Div(fmt_dt(r["at"]), className="num", style={"fontSize": 12, "color": "#9cb3a4", "whiteSpace": "nowrap"}),
                 html.Div([html.P(r["productName"], className="tname", style={"fontSize": 12.5}), html.P(r["sku"], className="tsub num")]),
                 html.Div(pill(lbl, tone)),
                 html.Div(f"{r['qty']:+d}", className=cx("num t-r", "t-ok" if r["qty"] >= 0 else "t-crit"), style={"fontWeight": 700, "fontSize": 13}),
                 html.Div(r["note"], className="ellipsis", style={"fontSize": 11.5, "color": "#9cb3a4"})]
        if with_stock:
            cells.append(html.Div(r["running"] if "running" in r else html.Span("filtered", style={"color": "#5f7466"}), className="num t-r tc", style={"fontWeight": 600}))
        out.append(html.Div(cells, className="trow", style={"--cols": cols}))
    return out


# ==================================================================================== settings
def settings_page():
    d = an.settings_page()
    s, c = d["s"], d["counts"]

    def slider(label_id, text, id, lo, hi, step, val):
        return html.Div([html.P(text, id=label_id, style={"fontSize": 11.5, "fontWeight": 600, "color": "#9cb3a4", "marginBottom": 8}),
                         dcc.Input(id=id, type="range", min=lo, max=hi, step=step, value=val, debounce=False)])

    return [html.Div([
        card([section_head("Company profile", "Shown in headers and reports"),
              html.Div([field("Company name", dcc.Input(id="st-company", value=s["company"], className="inp", debounce=False), cls="span2"),
                        field("Currency", dcc.Input(id="st-currency", value=s["currency"], maxLength=3, className="inp", debounce=False), "Symbol used across the app")], className="grid cols-3"),
              html.Div(btn("Save profile", id="st-save-company", variant="primary", ic="check"), style={"marginTop": 16, "display": "flex", "justifyContent": "flex-end"})],
             cls="card-lg lg6", d=0),
        card([section_head("Analysis policy", "Drives EOQ sizing, overstock and dead-stock detection, surge flags"),
              html.Div([slider("st-l-order", f"Cost per purchase order — {s['orderCost']} ₹", "st-order", 10, 300, 1, s["orderCost"]),
                        slider("st-l-hold", f"Annual holding cost — {round(s['holdingPct'] * 100)}% of unit cost", "st-hold", 5, 60, 1, round(s["holdingPct"] * 100)),
                        slider("st-l-over", f"Overstock threshold — {s['overstockDays']} days of cover", "st-over", 30, 180, 5, s["overstockDays"]),
                        slider("st-l-dead", f"Dead stock window — no sales for {s['deadStockDays']} days", "st-dead", 10, 90, 1, s["deadStockDays"]),
                        slider("st-l-surge", f"Surge trigger — weekly demand +{s['surgePct']}% vs. baseline", "st-surge", 15, 120, 5, s["surgePct"])], className="stack16"),
              html.Div(btn("Apply policy", id="st-save-policy", variant="primary", ic="check"), style={"marginTop": 16, "display": "flex", "justifyContent": "flex-end"})],
             cls="card-lg lg6", d=80),
        card([section_head("Data", "Local SQLite · seeded with a deterministic 210-day demo dataset"),
              html.Div([html.Div([eyebrow(l), html.P(v, className="num", style={"fontSize": 18, "fontWeight": 600, "color": "#e9f2ea", "marginTop": 4})], className="glass-inset", style={"borderRadius": 8, "padding": 12})
                        for l, v in (("Products", num(c["products"])), ("Sales", num(c["sales"])), ("Movements", num(c["movements"])), ("History depth", f"{c['oldest']}d"))], className="grid cols-4", style={"marginBottom": 16}),
              html.Div([html.Div([html.Span(icon("refresh", 16), className="ric crit", style={"width": 36, "height": 36}),
                                  html.Div([html.P("Regenerate demo data", style={"fontSize": 13, "fontWeight": 600, "color": "#e9f2ea"}),
                                            html.P("Replaces all products, sales and movements with a fresh dataset.", style={"fontSize": 11, "color": "#9cb3a4"})])], className="row-flex gap12"),
                        btn("Reseed", id="st-reseed", variant="danger")], className="row-flex glass-inset", style={"justifyContent": "space-between", "borderRadius": 8, "padding": 14})],
             cls="card-lg lg7", d=160),
        card([section_head("About this build"),
              html.Div([html.P([icon("layers", 14), "Meridian · Inventory Intelligence — Python edition v0.9"]),
                        html.P([icon("database", 14), "SQLite · transactional stock movements"]),
                        html.P([icon("sparkle", 14), "Decision engine: exponential smoothing, EOQ, ABC, days-of-cover, surge detection"]),
                        html.P([icon("eye", 14), "Every chart is computed live from stored data and updates after each action"])], className="about")],
             cls="card-lg lg5", d=240),
    ], className="grid g12")]


# ===================================================================================== modals
def _num(id, value, **kw):
    return dcc.Input(id=id, type="number", value=value, className="inp num", debounce=False, **kw)


def _footer(submit):
    return [btn("Cancel", id="m-cancel", variant="ghost"), submit]


def sale_modal():
    core = db.load_core()
    prods = sorted(core["products"], key=lambda p: (p["category"], p["name"]))
    first = prods[0]
    opts = [{"label": f"{p['category']} · {p['name']} — {p['stock']} in stock", "value": p["id"]} for p in prods]
    body = html.Div([
        field("Product", dropdown("sale-product", opts, first["id"], searchable=True), cls="span2"),
        field("Quantity", html.Div([html.Button(icon("minus", 14), id="sale-minus", n_clicks=0, className="step-btn glass-inset"),
                                    _num("sale-qty", 1, min=1, step=1, style={"textAlign": "center"}),
                                    html.Button(icon("plus", 14), id="sale-plus", n_clicks=0, className="step-btn glass-inset")], className="row-flex", style={"gap": 8})),
        html.Div(field("Unit price (₹)", _num("sale-price", round(first["price"] / 100, 2), min=0, step=0.01, disabled=True, style={"opacity": 0.8, "cursor": "not-allowed"})), id="sale-price-wrap"),
        field("Customer", dcc.Input(id="sale-customer", placeholder="Walk-in", className="inp", debounce=False)),
        field("Channel", segmented("sale-channel", [("counter", "Counter"), ("online", "Online"), ("wholesale", "Wholesale")], "counter")),
        html.Div([html.Span(id="sale-line", style={"fontSize": 12, "color": "#9cb3a4"}),
                  html.Span(id="sale-total", className="num", style={"fontSize": 19, "fontWeight": 600, "color": "#a9d6b0"})],
                 className="glass row-flex span2", style={"padding": 14, "justifyContent": "space-between"}),
    ], className="grid cols-2")
    return modal("Record a sale", body, _footer(btn("Record", id="sale-submit", variant="primary", ic="check")),
                 "Stock, revenue and analytics update instantly", "receipt")


def add_modal():
    body = html.Div([
        field("Name", dcc.Input(id="add-name", className="inp", placeholder="e.g. Sumatra Mandheling · 250g", debounce=False), cls="span2"),
        field("SKU", dcc.Input(id="add-sku", className="inp", placeholder="COF-021", debounce=False), "Leave blank to auto-assign"),
        field("Category", dropdown("add-cat", [{"label": c, "value": c} for c in db.CATEGORIES], "Coffee")),
        field("Cost (₹)", _num("add-cost", None, min=0, step=0.01, placeholder="8.50")),
        field("Price (₹)", _num("add-price", None, min=0, step=0.01, placeholder="19.00")),
        field("Opening stock", _num("add-stock", None, min=0, placeholder="0")),
        field("Reorder point", _num("add-rp", 12, min=0)),
        field("Case size", _num("add-rq", 24, min=0)),
        field("Lead time (days)", _num("add-lead", 7, min=0)),
        field("Description", dcc.Input(id="add-desc", className="inp", placeholder="Short tasting / product notes", debounce=False), cls="span2"),
    ], className="grid cols-2")
    return modal("Add product", body, _footer(btn("Add product", id="add-submit", variant="primary", ic="check")), ic="plus")


def adjust_modal(p):
    body = html.Div([segmented("adj-dir", [("remove", "Remove stock"), ("add", "Add stock")], "remove"),
                     field("Quantity", _num("adj-qty", 5, min=1, step=1)),
                     field("Reason", dcc.Input(id="adj-note", value="Cycle count correction", className="inp", debounce=False)),
                     html.P(id="adj-preview", style={"fontSize": 11.5, "color": "#7d9485"})], className="stack", style={"gap": 14})
    return modal("Adjust stock", body, _footer(btn("Apply", id="adj-submit", variant="primary")), p["name"], "sliders")


def receipt_modal(p):
    body = html.Div([field("Quantity", _num("rcv-qty", p["reorderQty"] or 24, min=1, step=1), f"Suggested case size: {p['reorderQty']}"),
                     field("Reference", dcc.Input(id="rcv-note", value="Purchase order received", className="inp", debounce=False)),
                     html.P(id="rcv-preview", style={"fontSize": 11.5, "color": "#7d9485"})], className="stack", style={"gap": 14})
    return modal("Log receipt", body, _footer(btn("Receive", id="rcv-submit", variant="primary")), p["name"], "truck")


def reseed_modal():
    body = html.P("This wipes all current products, sales and stock movements, then writes a fresh deterministic 210-day dataset. "
                  "Any products you added or sales you recorded will be removed.", style={"fontSize": 13, "color": "#c5d6c9", "lineHeight": 1.6})
    return modal("Regenerate demo data?", body, _footer(btn("Yes, reseed everything", id="reseed-confirm", variant="danger", ic="refresh")), ic="refresh")