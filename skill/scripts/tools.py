#!/usr/bin/env python3
"""supply-chain-control-tower · 工具层 CLI（上游移植 + 三处修复）

用法（agent 直接 bash 调用，全部输出 JSON 到 stdout）：
  tools.py inventory --sql "SELECT * FROM INVENTORY WHERE location='Seattle'"
  tools.py suppliers --sql "SELECT * FROM SUPPLIERS WHERE sku=12001"
  tools.py forecast --sku 11001 --location "San Francisco" [--weeks 12]
  tools.py gap --sku 13001 --location "San Francisco" --weeks 12
  tools.py shipping --source Seattle --destination "San Francisco"
  tools.py chart --sku 13001 --location "San Francisco" --weeks 26 --out /tmp/f.png
  tools.py kb

对上游 case/control_center_llm 的三处修复：
  1. forecast/shipping 用 hash() —— 跨进程不稳定，预测/运费不可复现 → 改 zlib.crc32
  2. solver.py f-string 双花括号 bug —— SQL 永远查空、库存恒为 0 → 修复为参数化查询
  3. tools 依赖 streamlit（logger / st.line_chart）→ 标准库 logging / matplotlib（缺失时优雅降级为 CSV）
"""
import argparse
import datetime
import json
import logging
import os
import sqlite3
import sys
import zlib

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stderr)
log = logging.getLogger("tools")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # skill 根
DATA = os.path.join(BASE, "data")


def _db() -> sqlite3.Connection:
    """CSV → 内存 SQLite（每次调用重建，数据量小，纯确定性）。"""
    con = sqlite3.connect(":memory:")
    for name in ("inventory", "suppliers"):
        df = pd.read_csv(os.path.join(DATA, f"{name}.csv"))
        df.to_sql(name, con, if_exists="replace", index=False)
    return con


def _sql_query(args, table: str):
    con = _db()
    try:
        df = pd.read_sql(args.sql, con)
    finally:
        con.close()
    print(df.to_json(orient="records", force_ascii=False))


def cmd_inventory(args):
    _sql_query(args, "inventory")


def cmd_suppliers(args):
    _sql_query(args, "suppliers")


def _crc(s: str) -> int:
    return zlib.crc32(str(s).encode("utf-8"))


def get_forecast(sku: str, location: str) -> pd.DataFrame:
    """52 周需求预测（上游公式，种子换 crc32 —— 修复 #1）。

    注意：location 不参与上游公式，保留参数形状以兼容 API。
    """
    max_units = 200
    horizon = 52
    today = datetime.date.today()
    next_monday = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=7)
    x = [next_monday + datetime.timedelta(weeks=i) for i in range(horizon)]
    seed = _crc(sku) % max_units
    y = (np.sin(np.linspace(0, 10, horizon)) * seed + max_units).astype(int)
    df = pd.DataFrame({"date": x, "demand": y})
    return df.set_index("date")


def cmd_forecast(args):
    df = get_forecast(args.sku, args.location)
    if args.weeks:
        df = df.head(args.weeks)
    print(df.reset_index().to_json(orient="records", force_ascii=False, date_format="iso"))


def stock_demand_difference(sku: int, location: str, weeks: int):
    """库存-需求缺口（修复 #2：上游 SQL 永远查空 → 库存恒 0）。返回 dict。

    record_exists=False 表示该 SKU×仓库无库存记录：此时 gap 无意义，
    上游（skill SOP/面板/MCP）必须如实告知无记录，禁止当作零库存出决策。
    """
    con = _db()
    row = pd.read_sql(
        "SELECT quantity FROM inventory WHERE sku=? AND location=?",
        con, params=(int(sku), location))
    exists = not row.empty
    stock = int(row["quantity"].iloc[0]) if exists else 0
    demand = int(get_forecast(str(sku), location).head(weeks)["demand"].sum())
    gap = stock - demand
    return {"sku": int(sku), "location": location, "weeks": weeks,
            "record_exists": exists,
            "current_stock": stock, "forecast_demand": demand, "gap_stock_minus_demand": gap,
            "note": ("该仓无此品库存记录——gap 无意义，如实回复无记录，禁止出决策单或 NO_REORDER"
                     if not exists else "gap<0=短缺需补货；gap>=0=充足无需补货")}


def cmd_gap(args):
    print(json.dumps(stock_demand_difference(args.sku, args.location, args.weeks),
                     ensure_ascii=False, indent=2))


def get_shipping_cost(source: str, destination: str) -> float:
    """单件运费（上游公式，种子换 crc32 —— 修复 #1）。"""
    return float((_crc(source) + _crc(destination)) % 10)


def cmd_shipping(args):
    print(json.dumps({"source": args.source, "destination": args.destination,
                      "unit_shipping_cost_usd": get_shipping_cost(args.source, args.destination)},
                     ensure_ascii=False, indent=2))


def cmd_chart(args):
    df = get_forecast(str(args.sku), args.location).head(args.weeks or 52).reset_index()
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(df["date"], df["demand"], marker="o", markersize=3)
        ax.set_title(f"Demand forecast · sku {args.sku} @ {args.location} ({args.weeks or 52}w)")
        ax.set_ylabel("units/week")
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(args.out, dpi=120)
        print(json.dumps({"chart": os.path.abspath(args.out)}, ensure_ascii=False))
    except ImportError:
        out_csv = args.out + ".csv"
        df.to_csv(out_csv, index=False)
        print(json.dumps({"chart_fallback_csv": os.path.abspath(out_csv),
                          "reason": "matplotlib 未安装"}, ensure_ascii=False))


def cmd_kb(args):
    """供应链知识直读（替代上游 LLM Searcher —— 上下文工程）。"""
    with open(os.path.join(DATA, "products.json")) as f:
        products = json.load(f)["products"]
    suppliers = pd.read_csv(os.path.join(DATA, "suppliers.csv")).to_dict(orient="records")
    inventory = pd.read_csv(os.path.join(DATA, "inventory.csv")).to_dict(orient="records")
    print(json.dumps({"products": products, "locations_inventory": inventory,
                      "supplier_options": suppliers}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inventory"); p.add_argument("--sql", required=True); p.set_defaults(fn=cmd_inventory)
    p = sub.add_parser("suppliers"); p.add_argument("--sql", required=True); p.set_defaults(fn=cmd_suppliers)
    p = sub.add_parser("forecast"); p.add_argument("--sku", required=True); p.add_argument("--location", required=True); p.add_argument("--weeks", type=int); p.set_defaults(fn=cmd_forecast)
    p = sub.add_parser("gap"); p.add_argument("--sku", required=True, type=int); p.add_argument("--location", required=True); p.add_argument("--weeks", required=True, type=int); p.set_defaults(fn=cmd_gap)
    p = sub.add_parser("shipping"); p.add_argument("--source", required=True); p.add_argument("--destination", required=True); p.set_defaults(fn=cmd_shipping)
    p = sub.add_parser("chart"); p.add_argument("--sku", required=True); p.add_argument("--location", required=True); p.add_argument("--weeks", type=int); p.add_argument("--out", default="/tmp/forecast.png"); p.set_defaults(fn=cmd_chart)
    p = sub.add_parser("kb"); p.set_defaults(fn=cmd_kb)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
