#!/usr/bin/env python3
"""每日补货巡检（控制塔的产品形态）：全 SKU × 有库存仓库 一键批量扫描。

纯工具直算（零 LLM、毫秒级、确定性）——这是控制塔的「早班巡检」；
Agent 只在管理者对某个例外开口追问时出场（见面板「实时 Agent」页）。

用法：python3 scripts/daily_scan.py [--weeks 12]
产物：panel/reports/latest.json + scan-<时间戳>.json
"""
import argparse
import importlib.util
import json
import os
import time

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tools)

_inv = pd.read_csv(os.path.join(BASE, "data", "inventory.csv"))
_sup = pd.read_csv(os.path.join(BASE, "data", "suppliers.csv"))
_products = {p["sku"]: p["brand"] for p in json.load(open(os.path.join(BASE, "data", "products.json")))["products"]}


def board(sku: int, dest: str) -> pd.DataFrame:
    rows = _sup[_sup.sku == sku].copy()
    if rows.empty:
        return rows
    rows["ship"] = [tools.get_shipping_cost(c, dest) for c in rows["location"]]
    rows["total"] = (rows["unit_cost"] + rows["ship"]).round(2)
    return rows.sort_values("total")


def scan(weeks: int = 12) -> dict:
    shortages, ample, no_record_sup = [], [], 0
    for _, r in _inv.iterrows():
        sku, loc = int(r["sku"]), r["location"]
        b = board(sku, loc)
        if b.empty:
            no_record_sup += 1
            continue
        g = tools.stock_demand_difference(sku, loc, weeks)
        gap = g["gap_stock_minus_demand"]
        if gap < 0:
            best = b.iloc[0]
            flip = bool(b.sort_values("unit_cost").iloc[0]["supplier"] != best["supplier"])
            shortages.append({
                "sku": sku, "brand": _products.get(sku, "?"), "location": loc,
                "stock": int(g["current_stock"]), "demand": int(g["forecast_demand"]),
                "gap": int(gap), "order_qty": int(-gap),
                "supplier": best["supplier"], "supplier_city": best["location"],
                "unit_cost": float(best["unit_cost"]), "shipping": float(best["ship"]),
                "total_unit": float(best["total"]), "total_cost": round(int(-gap) * float(best["total"]), 2),
                "flip": flip,
            })
        else:
            ample.append({"sku": sku, "brand": _products.get(sku, "?"), "location": loc,
                          "gap": int(gap), "stock": int(g["current_stock"]),
                          "demand": int(g["forecast_demand"])})
    shortages.sort(key=lambda x: -x["total_cost"])
    return {"generated_at": time.strftime("%F %T"), "weeks": weeks,
            "combos": len(_inv), "shortage_count": len(shortages), "ample_count": len(ample),
            "flip_count": sum(1 for s in shortages if s["flip"]),
            "no_supplier_count": no_record_sup,
            "total_reorder_cost": round(sum(s["total_cost"] for s in shortages), 2),
            "shortages": shortages, "ample": ample}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=int, default=12)
    a = ap.parse_args()
    rep = scan(a.weeks)
    outdir = os.path.join(BASE, "panel", "reports")
    os.makedirs(outdir, exist_ok=True)
    json.dump(rep, open(os.path.join(outdir, "latest.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(rep, open(os.path.join(outdir, f"scan-{time.strftime('%Y%m%d-%H%M%S')}.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in
                      ("generated_at", "weeks", "combos", "shortage_count", "ample_count",
                       "flip_count", "total_reorder_cost")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
