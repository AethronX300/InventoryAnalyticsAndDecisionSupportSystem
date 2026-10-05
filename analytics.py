"""
Meridian · Inventory IQ  —  analytics + decision engine.

Direct port of the original lib/analytics.ts:
exponential-smoothing demand forecast, reorder-point / lead-time checks, EOQ order sizing,
days-of-cover policy, dead-stock detection, surge detection, ABC analysis, health score.
"""
from __future__ import annotations

import math
import time
from datetime import datetime, timedelta

import database as db

DAY = 86_400

CAT_COLORS = {
    "Beverages": "#7fb0c9", "Tea": "#d9a45b", "Chocolate": "#cf8470",
    "Bakery": "#b5c98f", "Dairy": "#8fc49b", "Cereals": "#a594c9",
    "Snacks": "#e2c073", "Nuts": "#c4a39b", "Fruits": "#f28d8d", "Ice Cream": "#8fb7d3"
}
FALLBACK_COLOR = "#8fa89b"

def cat_color(cat: str) -> str:
    return CAT_COLORS.get(cat, FALLBACK_COLOR)


def day_key(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def clamp(v, lo, hi):
    return min(hi, max(lo, v))


# ------------------------------------------------------------------ formatting
def money(cents: float, sym: str = "₹", digits: int = 0) -> str:
    return f"{sym}{cents / 100:,.{digits}f}"


def money_compact(cents: float, sym: str = "₹") -> str:
    v = cents / 100
    if abs(v) >= 1_000_000:
        return f"{sym}{v / 1_000_000:.2f}M"
    if abs(v) >= 10_000:
        return f"{sym}{v / 1000:.1f}k"
    if abs(v) >= 1_000:
        return f"{sym}{v / 1000:.2f}k"
    return money(cents, sym)


def num(n: float, digits: int = 1) -> str:
    s = f"{n:,.{digits}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def fmt_dt(ts: float) -> str:
    d = datetime.fromtimestamp(ts)
    return f"{d.strftime('%b')} {d.day} · {(d.hour + 11) % 12 + 1}:{d.minute:02d} {'PM' if d.hour >= 12 else 'AM'}"


def fmt_day(ts: float) -> str:
    d = datetime.fromtimestamp(ts)
    return f"{d.strftime('%b')} {d.day}"


def delta_vs_prior(cur: float, prior: float) -> float:
    if prior <= 0:
        return 1.0 if cur > 0 else 0.0
    return (cur - prior) / prior


# ------------------------------------------------------------------- core data
def by_product(sales: list) -> dict:
    out: dict = {}
    for s in sales:
        out.setdefault(s["productId"], []).append(s)
    return out


def compute_stats(products: list, sales: list, s: dict) -> dict:
    now = time.time()
    grouped = by_product(sales)
    stats = {}
    for p in products:
        u28 = u7 = u30 = rev30 = 0
        last = None
        for row in grouped.get(p["id"], []):
            t = row["at"]
            if last is None or t > last:
                last = t
            dd = (now - t) / DAY
            if dd > 30:
                continue
            if dd <= 7:
                u7 += row["qty"]
            if dd <= 28:
                u28 += row["qty"]
            u30 += row["qty"]
            rev30 += row["total"]
        velocity = u28 / 28
        cover = p["stock"] / velocity if velocity > 0.004 else None
        since = None if last is None else int((now - last) // DAY)
        if p["stock"] == 0:
            status = "out"
        elif p["stock"] <= p["reorderPoint"] * 0.5:
            status = "critical"
        elif p["stock"] <= p["reorderPoint"]:
            status = "low"
        elif cover is not None and cover > s["overstockDays"]:
            status = "overstock"
        elif since is not None and since > s["deadStockDays"]:
            status = "dead"
        else:
            status = "healthy"
        stats[p["id"]] = dict(
            velocity=velocity, velocity7=u7 / 7, coverDays=cover, status=status,
            value=p["stock"] * p["cost"], revenue30=rev30, units30=u30,
            marginPct=(p["price"] - p["cost"]) / p["price"] if p["price"] > 0 else 0, daysSinceSale=since)
    return stats


def enriched(core: dict) -> list:
    stats = compute_stats(core["products"], core["sales"], core["s"])
    return [dict(p, stats=stats[p["id"]]) for p in core["products"]]


# ----------------------------------------------------------------------- trend
def build_trend(sales: list, days: int, offset: int = 0) -> list:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    out, idx = [], {}
    for i in range(days + offset - 1, offset - 1, -1):
        d = today - timedelta(days=i)
        pt = dict(label=f"{d.month}/{d.day}", d=d.strftime("%Y-%m-%d"), revenue=0, units=0, orders=0)
        out.append(pt)
        idx[pt["d"]] = pt
    for row in sales:
        pt = idx.get(day_key(row["at"]))
        if pt:
            pt["revenue"] += row["total"]
            pt["units"] += row["qty"]
            pt["orders"] += 1
    return out


# -------------------------------------------------------------- forecasting
def daily_demand(sales_by_pid: dict, pid: int, days: int = 14) -> float:
    now = time.time()
    daily: dict = {}
    for row in sales_by_pid.get(pid, []):
        if (now - row["at"]) / DAY > days:
            continue
        k = day_key(row["at"])
        daily[k] = daily.get(k, 0) + row["qty"]
    alpha, level, seen = 0.35, 0.0, 0
    for i in range(days - 1, -1, -1):
        v = daily.get(day_key(now - i * DAY), 0)
        level = v if seen == 0 else alpha * v + (1 - alpha) * level
        seen += 1
    return level


def eoq(annual_units: float, order_cost: float, unit_cost_cents: float, holding_pct: float):
    h = holding_pct * unit_cost_cents
    if annual_units <= 0 or h <= 0 or order_cost <= 0:
        return None
    return math.sqrt(2 * annual_units * order_cost / h)


# ---------------------------------------------------------------------- health
_FACTOR = {"out": .9, "critical": .62, "low": .38, "dead": .34, "overstock": .26, "healthy": 0}
_LABEL = {"out": "Out of stock", "critical": "Critical", "low": "Below reorder point",
          "overstock": "Overstocked", "dead": "Dead stock", "healthy": "Healthy"}
_TONE = {"out": "crit", "critical": "crit", "low": "warn", "overstock": "warn", "dead": "warn", "healthy": "ok"}


def compute_health(products: list, stats: dict) -> dict:
    total = sum(p["stock"] * p["cost"] for p in products) or 1
    penalty, seg = 0.0, {}
    for p in products:
        st = stats[p["id"]]["status"]
        w = p["stock"] * p["cost"] / total
        penalty += w * _FACTOR.get(st, 0) * 100
        e = seg.setdefault(st, dict(count=0, share=0.0))
        e["count"] += 1
        e["share"] += w
    score = round(clamp(100 - penalty, 4, 100))
    segments = [dict(label=_LABEL[k], count=seg[k]["count"], share=seg[k]["share"], tone=_TONE[k])
                for k in ("out", "critical", "low", "overstock", "dead", "healthy") if k in seg]
    return dict(score=score, tone="ok" if score >= 78 else "warn" if score >= 58 else "crit", segments=segments)


# ------------------------------------------------------------ recommendations
def _cover_label(days):
    if days is None:
        return "no demand"
    return "400+ days" if days > 400 else f"{round(days)} days"


def build_recommendations(core: dict, stats: dict) -> list:
    products, sales, s = core["products"], core["sales"], core["s"]
    sym = s["currency"]
    grouped = by_product(sales)
    now = time.time()
    recs = []

    def mk(p, rid, typ, sev, score, headline, reasons, metrics, action):
        recs.append(dict(id=rid, type=typ, severity=sev, productId=p["id"], sku=p["sku"], name=p["name"],
                         category=p["category"], score=score, headline=headline, reasons=reasons,
                         metrics=[dict(label=a, value=b) for a, b in metrics], action=action))

    for p in products:
        st = stats[p["id"]]
        d14 = daily_demand(grouped, p["id"], 14)
        days_left = p["stock"] / d14 if d14 > 0.01 else None
        e = eoq(st["velocity"] * 365, s["orderCost"], p["cost"], s["holdingPct"])
        suggested = max(p["reorderQty"], round(e / 4) * 4) if e else p["reorderQty"]
        value_txt = f"{sym}{round(p['stock'] * p['cost'] / 100):,}"
        base = [("Velocity", f"{st['velocity']:.1f} u/d"), ("Cover", _cover_label(st["coverDays"])),
                ("Lead time", f"{p['leadTimeDays']} days"), ("Stock value", value_txt)]
        tied = f"{sym}{round(p['stock'] * p['cost'] / 100)}"

        if p["stock"] == 0:
            live = st["daysSinceSale"] is not None and st["daysSinceSale"] <= s["deadStockDays"]
            lost = round(st["velocity7"] * p["price"] / 100)
            mk(p, f"out-{p['id']}", "stockout", "critical", 96, "Out of stock — no sellable units left",
               [f"Sold {st['units30']} units in the last 30 days — demand is live while the shelf is empty." if live
                else f"Last sale {st['daysSinceSale'] if st['daysSinceSale'] is not None else '—'} days ago; demand may have dropped.",
                f"Every day out of stock forfeits roughly {sym}{lost} of expected revenue."],
               base[:2] + [("Lost est./day", f"{sym}{lost}")],
               "Restock immediately" if live or st["daysSinceSale"] is None else "Review restock vs. delisting")
            continue

        if days_left is not None and days_left < p["leadTimeDays"]:
            gap = max(0, p["leadTimeDays"] - days_left)
            mk(p, f"stockout-{p['id']}", "stockout", "critical", 90 + min(8, p["leadTimeDays"] - days_left),
               f"Stock depletes in ~{max(1, round(days_left))} days — before replenishment lands",
               [f"Trailing 14-day demand ≈ {d14:.1f} units/day vs. {p['stock']} units on hand.",
                f"Lead time is {p['leadTimeDays']} days, so the reorder window has already passed by ~{round(gap)} days.",
                f"Expected stockout gap: ~{round(gap * d14)} units of demand."],
               base + [("Suggested order", f"{suggested} units")], "Raise purchase order now")
            continue

        if p["stock"] <= p["reorderPoint"]:
            pct = round(p["stock"] / max(1, p["reorderPoint"]) * 100)
            m = base + [("Suggested order", f"{suggested} units")]
            if e:
                m.append(("EOQ", f"{round(e)} units"))
            mk(p, f"reorder-{p['id']}", "reorder", "warning", 62 + (1 - p["stock"] / max(1, p["reorderPoint"])) * 18,
               "Below reorder point",
               [f"Stock {p['stock']} ≤ reorder point {p['reorderPoint']} ({pct}% of trigger).",
                f"At {st['velocity']:.1f} units/day, cover is {_cover_label(st['coverDays'])}.",
                f"EOQ for current demand ≈ {round(e)} units; rounded to {suggested} (case-pack 4)." if e
                else "Suggested order uses standard case size."], m, "Prepare purchase order")
            continue

        def within(days):
            return sum(x["qty"] for x in grouped.get(p["id"], []) if (now - x["at"]) / DAY <= days)
        u7 = within(7)
        baseline = (within(63) - u7) / 56
        if u7 >= 4 and baseline >= 0.15 and u7 / 7 >= baseline * (1 + s["surgePct"] / 100):
            lift = (u7 / 7 / baseline - 1) * 100
            mk(p, f"surge-{p['id']}", "surge", "opportunity", 48 + min(20, lift / 6),
               f"Demand up +{round(lift)}% vs. trailing baseline",
               [f"Last 7 days: {u7} units vs. {baseline:.1f}/day over the prior 8 weeks.",
                f"Cover at current pace: {_cover_label(st['coverDays'])}.",
                "A surge like this usually rewards early, slightly larger orders — cheaper than emergency air freight."],
               [("7-day units", str(u7)), ("Baseline u/d", f"{baseline:.1f}"), ("Cover", _cover_label(st["coverDays"]))],
               "Consider expediting stock")
            continue

        if st["coverDays"] is not None and st["coverDays"] > s["overstockDays"]:
            mk(p, f"over-{p['id']}", "overstock", "warning", 34 + min(14, st["coverDays"] / 60),
               f"Slow-moving — {round(st['coverDays'])} days of cover on hand",
               [f"Policy threshold is {s['overstockDays']} days; this SKU sits at {round(st['coverDays'])}.",
                f"{tied} of working capital is tied up here.",
                "Consider a bundle, a temporary promotion, or pausing the next order."],
               [("Units on hand", str(p["stock"])), ("Capital tied", tied), ("Velocity", f"{st['velocity']:.1f} u/d")],
               "Promote or hold next order")
            continue

        if st["daysSinceSale"] is not None and st["daysSinceSale"] > s["deadStockDays"]:
            mk(p, f"dead-{p['id']}", "dead", "warning", 40 + min(16, st["daysSinceSale"] / 6),
               f"Dead stock — no sales in {st['daysSinceSale']} days",
               [f"{p['stock']} units on hand with zero movement past the {s['deadStockDays']}-day policy window.",
                f"{tied} of capital at risk of obsolescence.",
                "Options: clearance price, bundle with a fast mover, or vendor return if the contract allows."],
               [("Days idle", str(st["daysSinceSale"])), ("Capital tied", tied), ("Units", str(p["stock"]))],
               "Plan clearance or return")
    return sorted(recs, key=lambda r: -r["score"])


# ------------------------------------------------------------------------ ABC
def compute_abc(products: list, stats: dict) -> list:
    rows = sorted(((p, stats[p["id"]]["revenue30"]) for p in products if stats[p["id"]]["revenue30"] > 0),
                  key=lambda x: -x[1])
    total = sum(r for _, r in rows) or 1
    cum, out = 0.0, []
    for p, rev in rows:
        share = rev / total
        cum += share
        out.append(dict(sku=p["sku"], name=p["name"], category=p["category"], revenue=rev, share=share, cum=cum,
                        cls="A" if cum <= 0.8 else "B" if cum <= 0.95 else "C"))
    return out


# --------------------------------------------------------------- stock series
def stock_series(movements: list, pid: int, current_stock: int, days: int) -> list:
    now = time.time()
    rows = [m for m in movements if m["productId"] == pid and m["at"] <= now]
    rows.sort(key=lambda m: m["at"])
    times = [m["at"] for m in rows]
    suffix = [0] * (len(rows) + 1)
    for i in range(len(rows) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + rows[i]["qty"]
    out = []
    for i in range(days - 1, -1, -1):
        d = datetime.fromtimestamp(now - i * DAY).replace(hour=23, minute=59, second=59)
        t = d.timestamp()
        lo, hi = 0, len(times)
        while lo < hi:
            mid = (lo + hi) // 2
            if times[mid] > t:
                hi = mid
            else:
                lo = mid + 1
        out.append(dict(d=d.strftime("%Y-%m-%d"), label=f"{d.month}/{d.day}", stock=max(0, current_stock - suffix[lo])))
    return out


# --------------------------------------------------------------- misc helpers
def category_breakdown(products: list, sales: list) -> list:
    pmap = {p["id"]: p for p in products}
    cats: dict = {}
    for p in products:
        cats.setdefault(p["category"], dict(revenue=0, units=0, cost=0, skus=0))["skus"] += 1
    now = time.time()
    for r in sales:
        if (now - r["at"]) / DAY > 30:
            continue
        p = pmap.get(r["productId"])
        if p:
            c = cats[p["category"]]
            c["revenue"] += r["total"]
            c["units"] += r["qty"]
            c["cost"] += p["cost"] * r["qty"]
    out = [dict(name=n, revenue=c["revenue"], units=c["units"], skus=c["skus"], color=cat_color(n),
                margin=(c["revenue"] - c["cost"]) / c["revenue"] if c["revenue"] > 0 else 0)
           for n, c in cats.items()]
    return sorted(out, key=lambda x: -x["revenue"])


def weekday_pattern(sales: list, days: int = 28) -> list:
    b = [dict(orders=0, revenue=0, units=0) for _ in range(7)]
    now = time.time()
    for r in sales:
        if (now - r["at"]) / DAY > days:
            continue
        i = (datetime.fromtimestamp(r["at"]).weekday() + 1) % 7
        b[i]["orders"] += 1
        b[i]["revenue"] += r["total"]
        b[i]["units"] += r["qty"]
    names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    return [dict(name=names[i], **b[i]) for i in range(7)]


def top_products(products: list, stats: dict, n: int) -> list:
    rows = sorted(products, key=lambda p: -stats[p["id"]]["revenue30"])[:n]
    return [dict(id=p["id"], sku=p["sku"], name=p["name"], category=p["category"], revenue=stats[p["id"]]["revenue30"])
            for p in rows]


# =========================================================== page-level bundles
def overview(days: int = 30) -> dict:
    core = db.load_core()
    products, sales, s = core["products"], core["sales"], core["s"]
    stats = compute_stats(products, sales, s)
    now = time.time()
    rev = revp = u = up = 0
    for r in sales:
        dd = (now - r["at"]) / DAY
        if dd <= days:
            rev += r["total"]
            u += r["qty"]
        elif dd <= days * 2:
            revp += r["total"]
            up += r["qty"]
    t_days = build_trend(sales, days)
    risk = [p for p in products if stats[p["id"]]["status"] in ("critical", "out")]
    recs = build_recommendations(core, stats)
    
    # Filter category breakdown for the selected period
    cat_rev = {p["category"]: 0 for p in products}
    for r in sales:
        if (now - r["at"]) / DAY <= days:
            cat_rev[next(p["category"] for p in products if p["id"] == r["productId"])] += r["total"]
            
    # Normalize categories
    t_cat = sum(cat_rev.values()) or 1
    categories = [{"name": c, "revenue": v, "margin": 0.4, "color": cat_color(c)} 
                 for c, v in sorted(cat_rev.items(), key=lambda x: x[1], reverse=True) if v > 0]
                 
    return dict(
        s=s, rev=rev, revDelta=delta_vs_prior(rev, revp), revSpark=[t["revenue"] / 100 for t in t_days],
        u=u, unitsDelta=delta_vs_prior(u, up), unitsSpark=[t["units"] for t in t_days],
        invValue=sum(p["stock"] * p["cost"] for p in products),
        riskCount=len(risk), riskValue=sum(p["stock"] * p["cost"] for p in risk),
        trend={d: build_trend(sales, d) for d in (1, 14, 30, 90)},
        categories=categories, top=top_products(products, stats, 5),
        health=compute_health(products, stats), alerts=recs[:5], recs=recs[:4],
        days=days)


def inventory() -> dict:
    core = db.load_core()
    items = enriched(core)
    stats = {i["id"]: i["stats"] for i in items}
    recs = {r["sku"]: r for r in build_recommendations(core, stats)}
    return dict(s=core["s"], items=items, recs=recs,
                totals=dict(skus=len(items), units=sum(i["stock"] for i in items),
                            value=sum(i["stats"]["value"] for i in items),
                            below=sum(1 for i in items if i["stats"]["status"] in ("low", "critical", "out"))))


def product_detail(sku: str):
    core = db.load_core()
    items = enriched(core)
    item = next((i for i in items if i["sku"] == sku), None)
    if not item:
        return None
    stats = {i["id"]: i["stats"] for i in items}
    rec = next((r for r in build_recommendations(core, stats) if r["sku"] == sku), None)
    moves = [m for m in core["movements"] if m["productId"] == item["id"]]
    return dict(s=core["s"], item=item, rec=rec, moves=list(reversed(moves))[:8],
                series=stock_series(core["movements"], item["id"], item["stock"], 60))


def sales_page() -> dict:
    core = db.load_core()
    products, s = core["products"], core["s"]
    pmap = {p["id"]: p for p in products}
    now = time.time()
    midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    today = week = rev30 = u30 = orders = 0
    for r in core["sales"]:
        dd = (now - r["at"]) / DAY
        if r["at"] >= midnight:
            today += r["total"]
        if dd <= 7:
            week += r["total"]
        if dd <= 30:
            rev30 += r["total"]
            u30 += r["qty"]
            orders += 1
    rows = []
    for r in reversed(core["sales"][-600:]):
        p = pmap.get(r["productId"], {})
        rows.append(dict(r, productName=p.get("name", "—"), sku=p.get("sku", "—"), category=p.get("category", "—"),
                         marginPct=(r["unitPrice"] - p["cost"]) / r["unitPrice"] if p and r["unitPrice"] else 0))
    return dict(s=s, rows=rows, today=today, week=week, orders=orders, aov=rev30 / u30 if u30 else 0)


def analytics_page() -> dict:
    core = db.load_core()
    products, sales, s = core["products"], core["sales"], core["s"]
    stats = compute_stats(products, sales, s)
    abc = compute_abc(products, stats)
    pmap = {p["id"]: p for p in products}
    now = time.time()
    rev90 = gp90 = 0
    for r in sales:
        if (now - r["at"]) / DAY > 90:
            continue
        p = pmap.get(r["productId"])
        if p:
            rev90 += r["total"]
            gp90 += (r["unitPrice"] - p["cost"]) * r["qty"]
    velocity = sorted(({"sku": p["sku"], "name": p["name"], "category": p["category"],
                        "velocity": stats[p["id"]]["velocity"], "revenue": stats[p["id"]]["revenue30"],
                        "margin": stats[p["id"]]["marginPct"] * 100} for p in products), key=lambda v: -v["velocity"])
    return dict(s=s, abc=abc, velocity=velocity, categories=category_breakdown(products, sales),
                weekday=weekday_pattern(sales, 28), rev90=rev90, gp90=gp90,
                ranges={d: dict(cur=build_trend(sales, d), prev=build_trend(sales, d, d)) for d in (14, 30, 60, 90)})


def decisions_page() -> dict:
    core = db.load_core()
    products, sales, s = core["products"], core["sales"], core["s"]
    stats = compute_stats(products, sales, s)
    recs = build_recommendations(core, stats)
    grouped = by_product(sales)
    fc = []
    for p in products:
        d14 = daily_demand(grouped, p["id"], 14)
        fc.append(dict(sku=p["sku"], name=p["name"], stock=p["stock"], daysLeft=p["stock"] / d14 if d14 > 0.01 else 9999))
    fc.sort(key=lambda f: f["daysLeft"])
    return dict(s=s, recs=recs, health=compute_health(products, stats), forecast=fc[:8],
                counts={k: sum(1 for r in recs if r["severity"] == k) for k in ("critical", "warning", "opportunity")})


def history_page() -> dict:
    core = db.load_core()
    pmap = {p["id"]: p for p in core["products"]}
    now = time.time()
    summ = dict(receipts=0, adjustments=0, sold=0, received=0)
    for m in core["movements"]:
        if (now - m["at"]) / DAY > 30:
            continue
        if m["type"] == "receipt":
            summ["receipts"] += 1
            summ["received"] += m["qty"]
        elif m["type"] == "adjustment":
            summ["adjustments"] += 1
        elif m["type"] == "sale":
            summ["sold"] += -m["qty"]
    rows = [dict(m, productName=pmap.get(m["productId"], {}).get("name", "—"), sku=pmap.get(m["productId"], {}).get("sku", "—"))
            for m in reversed(core["movements"])]
    return dict(s=core["s"], rows=rows, products=core["products"], summary=summ, movements=core["movements"])


def settings_page() -> dict:
    core = db.load_core()
    oldest = int((time.time() - core["sales"][0]["at"]) // DAY) if core["sales"] else 0
    return dict(s=core["s"], counts=dict(products=len(core["products"]), sales=len(core["sales"]),
                                         movements=len(core["movements"]), oldest=oldest))
