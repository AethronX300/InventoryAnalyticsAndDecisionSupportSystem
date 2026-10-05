"""
Meridian · Inventory IQ  —  data layer (SQLite, standard library only).

* Creates `meridian.db` next to this file on first run.
* Seeds a deterministic 210-day dataset (same product catalogue as the original app).
* All money is stored in CENTS (integers); all timestamps are epoch seconds (local time).
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meridian.db")
PERIOD_DAYS = 210
DAY = 86_400

DEFAULT_SETTINGS = {
    "company": "Meridian Provisions",
    "currency": "₹",
    "orderCost": 48,        # per purchase order
    "holdingPct": 0.24,     # annual holding cost, fraction of unit cost
    "overstockDays": 75,    # days of cover above which = overstock
    "deadStockDays": 28,    # days without sales = dead
    "surgePct": 40,         # % uplift vs baseline that flags a surge
}

_lock = threading.RLock()
_cache: dict = {"core": None}


# --------------------------------------------------------------------------- #
# connection + schema
# --------------------------------------------------------------------------- #
def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    return c


SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT NOT NULL UNIQUE, name TEXT NOT NULL, category TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '', cost INTEGER NOT NULL, price INTEGER NOT NULL,
  stock INTEGER NOT NULL DEFAULT 0, reorder_point INTEGER NOT NULL DEFAULT 12,
  reorder_qty INTEGER NOT NULL DEFAULT 24, lead_time_days INTEGER NOT NULL DEFAULT 7
);
CREATE TABLE IF NOT EXISTS sales (
  id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL, qty INTEGER NOT NULL,
  unit_price INTEGER NOT NULL, total INTEGER NOT NULL, customer TEXT NOT NULL,
  channel TEXT NOT NULL DEFAULT 'counter', at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sales_at_idx ON sales(at);
CREATE INDEX IF NOT EXISTS sales_product_idx ON sales(product_id);
CREATE TABLE IF NOT EXISTS stock_movements (
  id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL, type TEXT NOT NULL,
  qty INTEGER NOT NULL, note TEXT NOT NULL DEFAULT '', at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS mov_product_idx ON stock_movements(product_id);
CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


# --------------------------------------------------------------------------- #
# deterministic RNG (mulberry32, same as the original seed script)
# --------------------------------------------------------------------------- #
class Rng:
    def __init__(self, seed: int):
        self.a = seed & 0xFFFFFFFF

    def __call__(self) -> float:
        self.a = (self.a + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((self.a ^ (self.a >> 15)) * (1 | self.a)) & 0xFFFFFFFF
        t = ((t + (((t ^ (t >> 7)) * (61 | t)) & 0xFFFFFFFF)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296


def _poisson(lam: float, r: Rng) -> int:
    if lam <= 0.001:
        return 0
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= r()
        if not (p > L and k < 14):
            break
    return k - 1


# --------------------------------------------------------------------------- #
# product catalogue
# --------------------------------------------------------------------------- #
def _d(sku, name, cat, desc, cost, price, base, trend, wk, target, rp, rq, lead,
       receipts=(), dead=None, spike=None):
    return dict(sku=sku, name=name, cat=cat, desc=desc, cost=cost, price=price, base=base,
                trend=trend, wk=wk, target=target, rp=rp, rq=rq, lead=lead,
                receipts=list(receipts), dead=dead, spike=spike)


DEFS = [
    _d("P-001", "Tea Packet", "Tea", "Classic black tea.", 7200, 12000, 1.6, 0.1, [1.1, .9, .95, 1, 1, 1.1, 1.2], 10, 15, 30, 5, []),
    _d("P-002", "Potato Chips", "Snacks", "Crunchy salted potato chips.", 3000, 5000, 2.5, 0.05, [1.2, .9, .95, 1, 1, 1.1, 1.2], 20, 25, 50, 4, []),
    _d("P-003", "Chocolate Ice Cream", "Ice Cream", "Rich chocolate ice cream.", 13800, 23000, 0.8, -0.1, [1.3, .8, .9, 1, 1, 1.2, 1.3], 10, 8, 16, 3, []),
    _d("P-004", "Bread Loaf", "Bakery", "Freshly baked white bread.", 2700, 4500, 3.0, 0.0, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 10, 10, 20, 1, []),
    _d("P-005", "Orange Juice", "Beverages", "Freshly squeezed orange juice.", 8400, 14000, 1.2, 0.1, [1.1, .9, .95, 1, 1, 1.1, 1.2], 10, 10, 20, 2, []),
    _d("P-006", "Fresh Milk", "Dairy", "Full cream fresh milk.", 3900, 6500, 4.0, 0.0, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 10, 12, 24, 1, []),
    _d("P-007", "Dark Chocolate", "Chocolate", "70% cocoa dark chocolate.", 9000, 15000, 0.5, 0.2, [1.2, .9, .9, 1, 1.05, 1.1, 1.2], 10, 8, 16, 5, []),
    _d("P-008", "Salted Peanuts", "Nuts", "Roasted and salted peanuts.", 4800, 8000, 1.5, -0.05, [1.1, .9, 1, 1, 1, 1.1, 1.2], 20, 20, 40, 7, []),
    _d("P-009", "Apple", "Fruits", "Fresh red apples.", 1200, 2000, 5.0, 0.0, [1.1, .9, 1, 1, 1, 1.1, 1.2], 20, 25, 50, 3, []),
    _d("P-010", "Corn Flakes", "Cereals", "Crunchy breakfast cereal.", 10800, 18000, 0.9, 0.05, [1.2, .9, 1, 1, 1, 1.1, 1.2], 10, 10, 20, 6, []),
]

RETAIL = ["Ava Chen", "Marcus Reid", "Hana Sato", "Ben Okafor", "Elena Petrov", "Jonas Weber", "Priya Nair",
          "Tom Alvarez", "Sofia Rossi", "Daniel Kim", "Marta Silva", "Leo Fontaine", "Noor Haddad", "Felix Braun"]
B2B = ["Driftwood Café", "Atlas Hospitality", "Fern & Fog Bistro", "Harbor Hotel", "Northside Club"]
CATEGORIES = ["Tea", "Snacks", "Ice Cream", "Bakery", "Beverages", "Dairy", "Chocolate", "Nuts", "Fruits", "Cereals"]
SKU_PREFIX = {"Tea": "TEA", "Snacks": "SNA", "Ice Cream": "ICE", "Bakery": "BAK", "Beverages": "BEV", "Dairy": "DAI", "Chocolate": "CHO", "Nuts": "NUT", "Fruits": "FRU", "Cereals": "CER"}


# --------------------------------------------------------------------------- #
# seeding
# --------------------------------------------------------------------------- #
def _seed(c: sqlite3.Connection) -> None:
    r = Rng(20240117)
    now = datetime.now()
    today0 = datetime(now.year, now.month, now.day)
    start0 = today0 - timedelta(days=PERIOD_DAYS - 1)
    hour_cap = min(19, now.hour)

    for d in DEFS:
        c.execute(
            "INSERT INTO products(sku,name,category,description,cost,price,stock,reorder_point,reorder_qty,lead_time_days)"
            " VALUES(?,?,?,?,?,?,0,?,?,?)",
            (d["sku"], d["name"], d["cat"], d["desc"], d["cost"], d["price"], d["rp"], d["rq"], d["lead"]))
    ids = [row["id"] for row in c.execute("SELECT id FROM products ORDER BY id")]

    sales_rows, mov_rows = [], []
    for pi, d in enumerate(DEFS):
        pid, sold = ids[pi], 0
        for off in range(PERIOD_DAYS):
            day = start0 + timedelta(days=off)
            is_today = off == PERIOD_DAYS - 1
            lam = d["base"] * (1 + d["trend"] * (off / (PERIOD_DAYS - 1) - 1))
            lam *= d["wk"][(day.weekday() + 1) % 7]
            if d["dead"] is not None and off >= PERIOD_DAYS + d["dead"]:
                lam *= 0.04
            if d["spike"]:
                spike_from = PERIOD_DAYS + d["spike"][0]
                if off >= spike_from:
                    t = (off - spike_from) / max(1, PERIOD_DAYS - 1 - spike_from)
                    lam *= 1 + (d["spike"][1] - 1) * min(1, 0.35 + 0.65 * t)
            n = _poisson(lam, r)
            if n <= 0:
                continue
            wholesale = r() < 0.14
            qty = 2 + int(r() * 5) if wholesale else n
            price = d["price"]
            if wholesale:
                customer, channel = B2B[int(r() * len(B2B))], "wholesale"
                price = round(d["price"] * 0.88 / 10) * 10
            else:
                channel = "counter" if r() < 0.55 else "online"
                customer = RETAIL[int(r() * len(RETAIL))]
                if channel == "online" and r() < 0.1:
                    price = round(d["price"] * 0.9 / 10) * 10
            hour = 8 + int(r() * 12)
            if is_today and hour > hour_cap:
                continue
            at = day.replace(hour=hour, minute=int(r() * 60), second=int(r() * 60)).timestamp()
            sales_rows.append((pid, qty, price, qty * price, customer, channel, at))
            mov_rows.append((pid, "sale", -qty, f"Sale · {customer}", at))
            sold += qty

        for off, qty in d["receipts"]:       # offsets are days before today
            at = (today0 + timedelta(days=off)).replace(hour=9, minute=15).timestamp()
            mov_rows.append((pid, "receipt", qty, f"Purchase order · inbound {qty} units", at))
        receipts_qty = sum(q for _, q in d["receipts"])
        q0 = max(1, d["target"] + sold - receipts_qty)
        mov_rows.append((pid, "initial", q0, "Opening stock count",
                         (start0 - timedelta(days=4)).replace(hour=8).timestamp()))
        end_delta = d["target"] - (q0 + receipts_qty - sold)
        if end_delta:
            mov_rows.append((pid, "adjustment", end_delta,
                             "Cycle count correction" if end_delta > 0 else "Shrinkage / damaged units write-off",
                             (start0 + timedelta(days=PERIOD_DAYS - 3)).replace(hour=17, minute=30).timestamp()))

    stock = {}
    for m in mov_rows:
        stock[m[0]] = stock.get(m[0], 0) + m[2]
    for pid, st in stock.items():
        c.execute("UPDATE products SET stock=? WHERE id=?", (max(0, st), pid))
    c.executemany("INSERT INTO sales(product_id,qty,unit_price,total,customer,channel,at) VALUES(?,?,?,?,?,?,?)", sales_rows)
    c.executemany("INSERT INTO stock_movements(product_id,type,qty,note,at) VALUES(?,?,?,?,?)", mov_rows)
    c.executemany("INSERT INTO app_settings(key,value) VALUES(?,?)",
                  [(k, json.dumps(v)) for k, v in DEFAULT_SETTINGS.items()])


def ensure_ready() -> None:
    with _lock:
        c = _conn()
        try:
            c.executescript(SCHEMA)
            if c.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
                _seed(c)
            c.commit()
        finally:
            c.close()


def reseed() -> None:
    with _lock:
        c = _conn()
        try:
            for t in ("stock_movements", "sales", "products", "app_settings"):
                c.execute(f"DELETE FROM {t}")
            c.execute("DELETE FROM sqlite_sequence")
            _seed(c)
            # OVERRIDE final stock to exactly match the image
            exact_stocks = {
                "P-001": 35, "P-002": 65, "P-003": 6, "P-004": 20, "P-005": 22,
                "P-006": 30, "P-007": 14, "P-008": 48, "P-009": 75, "P-010": 12
            }
            for sku, stock in exact_stocks.items():
                c.execute("UPDATE products SET stock = ? WHERE sku = ?", (stock, sku))
            c.commit()
        finally:
            c.close()
        _cache["core"] = None


# --------------------------------------------------------------------------- #
# reads
# --------------------------------------------------------------------------- #
def load_core() -> dict:
    """Everything the analytics layer needs, cached until the next write."""
    with _lock:
        if _cache["core"] is not None:
            return _cache["core"]
        c = _conn()
        try:
            products = [
                dict(id=r["id"], sku=r["sku"], name=r["name"], category=r["category"], description=r["description"],
                     cost=r["cost"], price=r["price"], stock=r["stock"], reorderPoint=r["reorder_point"],
                     reorderQty=r["reorder_qty"], leadTimeDays=r["lead_time_days"])
                for r in c.execute("SELECT * FROM products ORDER BY sku")]
            sales = [dict(id=r["id"], productId=r["product_id"], qty=r["qty"], unitPrice=r["unit_price"],
                          total=r["total"], customer=r["customer"], channel=r["channel"], at=r["at"])
                     for r in c.execute("SELECT * FROM sales ORDER BY at")]
            moves = [dict(id=r["id"], productId=r["product_id"], type=r["type"], qty=r["qty"],
                          note=r["note"], at=r["at"])
                     for r in c.execute("SELECT * FROM stock_movements ORDER BY at, id")]
            settings = dict(DEFAULT_SETTINGS)
            for r in c.execute("SELECT key,value FROM app_settings"):
                try:
                    settings[r["key"]] = json.loads(r["value"])
                except ValueError:
                    pass
        finally:
            c.close()
        _cache["core"] = dict(products=products, sales=sales, movements=moves, s=settings)
        return _cache["core"]


# --------------------------------------------------------------------------- #
# writes  (each returns (ok: bool, message: str))
# --------------------------------------------------------------------------- #
def _write(fn):
    with _lock:
        c = _conn()
        try:
            out = fn(c)
            c.commit()
            _cache["core"] = None
            return out
        except Exception as e:  # pragma: no cover
            c.rollback()
            return False, str(e)
        finally:
            c.close()


def record_sale(product_id: int, qty: int, unit_price: int, customer: str, channel: str):
    def go(c):
        p = c.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if not p:
            return False, "Product not found."
        if qty <= 0:
            return False, "Quantity must be a positive number."
        if qty > p["stock"]:
            return False, f"Only {p['stock']} units of {p['sku']} on hand."
        now, who = time.time(), (customer or "").strip() or "Walk-in"
        c.execute("INSERT INTO sales(product_id,qty,unit_price,total,customer,channel,at) VALUES(?,?,?,?,?,?,?)",
                  (product_id, qty, unit_price, qty * unit_price, who, channel, now))
        c.execute("INSERT INTO stock_movements(product_id,type,qty,note,at) VALUES(?,?,?,?,?)",
                  (product_id, "sale", -qty, f"Sale · {who}", now))
        c.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, product_id))
        return True, "ok"
    return _write(go)


def add_product(f: dict):
    def go(c):
        cat = f["category"] if f["category"] in SKU_PREFIX else "Accessories"
        sku = (f.get("sku") or "").strip().upper()
        if not sku:
            n = c.execute("SELECT COUNT(*) FROM products WHERE sku LIKE ?", (SKU_PREFIX[cat] + "-%",)).fetchone()[0]
            sku = f"{SKU_PREFIX[cat]}-{n + 1:03d}"
            while c.execute("SELECT 1 FROM products WHERE sku=?", (sku,)).fetchone():
                n += 1
                sku = f"{SKU_PREFIX[cat]}-{n + 1:03d}"
        if c.execute("SELECT 1 FROM products WHERE sku=?", (sku,)).fetchone():
            return False, f"SKU {sku} already exists."
        cur = c.execute(
            "INSERT INTO products(sku,name,category,description,cost,price,stock,reorder_point,reorder_qty,lead_time_days)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (sku, f["name"].strip(), cat, f.get("description", ""), int(round(f["cost"] * 100)),
             int(round(f["price"] * 100)), f["stock"], f["reorderPoint"], f["reorderQty"], f["leadTimeDays"]))
        if f["stock"] > 0:
            c.execute("INSERT INTO stock_movements(product_id,type,qty,note,at) VALUES(?,?,?,?,?)",
                      (cur.lastrowid, "initial", f["stock"], "Opening stock count", time.time()))
        return True, sku
    return _write(go)


def adjust_stock(product_id: int, delta: int, note: str):
    def go(c):
        p = c.execute("SELECT stock FROM products WHERE id=?", (product_id,)).fetchone()
        if not p or p["stock"] + delta < 0:
            return False, "Adjustment would take stock below zero."
        c.execute("UPDATE products SET stock=stock+? WHERE id=?", (delta, product_id))
        c.execute("INSERT INTO stock_movements(product_id,type,qty,note,at) VALUES(?,?,?,?,?)",
                  (product_id, "adjustment", delta, note or "Manual adjustment", time.time()))
        return True, "ok"
    return _write(go)


def receive_stock(product_id: int, qty: int, note: str):
    def go(c):
        c.execute("UPDATE products SET stock=stock+? WHERE id=?", (qty, product_id))
        c.execute("INSERT INTO stock_movements(product_id,type,qty,note,at) VALUES(?,?,?,?,?)",
                  (product_id, "receipt", qty, note or "Purchase order received", time.time()))
        return True, "ok"
    return _write(go)


def set_reorder_point(product_id: int, rp: int):
    return _write(lambda c: (c.execute("UPDATE products SET reorder_point=? WHERE id=?", (rp, product_id)), (True, "ok"))[1])


def save_settings(values: dict):
    def go(c):
        for k, v in values.items():
            c.execute("INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                      (k, json.dumps(v)))
        return True, "ok"
    return _write(go)


ensure_ready()
