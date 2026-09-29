#!/usr/bin/env python3
"""金答案生成器（ISC-16 判据）：绕过 LLM，用 tools 直接算每个任务的标准答案。

运行：python3 skill/evals/gold_gen.py
产物：同目录 gold.json（任务 id → 金答案）。金答案直算，零手填。
"""
import importlib.util
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # skill 根
_spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tools)

import pandas as pd  # noqa: E402


def best_supplier(sku: int, dest: str) -> dict:
    """总单价（unit_cost + 运费）最低的供应商。"""
    sup = pd.read_csv(os.path.join(BASE, "data", "suppliers.csv"))
    rows = sup[sup.sku == int(sku)]
    best, best_unit = None, float("inf")
    for _, r in rows.iterrows():
        ship = tools.get_shipping_cost(r["location"], dest)
        unit = float(r["unit_cost"]) + ship
        if unit < best_unit:
            best_unit = unit
            best = {"supplier": r["supplier"], "supplier_location": r["location"],
                    "unit_cost": float(r["unit_cost"]), "shipping_cost": float(ship)}
    return best


def main():
    tasks = json.load(open(os.path.join(BASE, "evals", "evals.json")))["tasks"]
    gold = {}
    for t in tasks:
        p, k = t["params"], t["kind"]
        if k == "decision":
            g = tools.stock_demand_difference(p["sku"], p["location"], p["weeks"])
            rop_gap = g.get("rop_gap", -g["gap_stock_minus_demand"])
            if rop_gap > 0:  # ROP 驱动：低于 ROP 需补货
                b = best_supplier(p["sku"], p["location"])
                qty = int(rop_gap + g.get("safety_stock", 0))  # ROP 缺口+安全库存
                gold[t["id"]] = {
                    "decision": "REORDER", "order_qty": qty, "supplier": b["supplier"],
                    "unit_cost": b["unit_cost"], "shipping_cost": b["shipping_cost"],
                    "total_cost": round(qty * (b["unit_cost"] + b["shipping_cost"]), 2),
                    "gap": g["gap_stock_minus_demand"],
                    "rop_gap": rop_gap, "reorder_point": g.get("reorder_point"),
                    "safety_stock": g.get("safety_stock")}
            else:
                gold[t["id"]] = {"decision": "NO_REORDER", "gap": g["gap_stock_minus_demand"],
                                 "rop_gap": rop_gap}
        elif k == "negative":
            g = tools.stock_demand_difference(p["sku"], p["location"], p["weeks"])
            gold[t["id"]] = {"decision": "NO_REORDER", "gap": g["gap_stock_minus_demand"],
                             "rop_gap": g.get("rop_gap")}
        elif k == "query":
            if "sql" in p:
                con = tools._db()
                df = pd.read_sql(p["sql"], con)
                con.close()
                gold[t["id"]] = {"type": "table", "rows": df.to_dict(orient="records")}
            elif p.get("tool") == "forecast":
                df = tools.get_forecast(str(p["sku"]), p["location"]).head(p["weeks"])
                gold[t["id"]] = {"type": "series", "demand": [int(x) for x in df["demand"]]}
            elif p.get("tool") == "shipping":
                gold[t["id"]] = {"type": "scalar",
                                 "value": tools.get_shipping_cost(p["source"], p["destination"])}
        elif k == "irrelevant":
            gold[t["id"]] = {"no_tool": True}
    out = os.path.join(BASE, "evals", "gold.json")
    json.dump(gold, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"gold.json 生成完毕：{len(gold)} 条 → {out}")
    for tid, g in list(gold.items())[:4]:
        print(f"  {tid}: {json.dumps(g, ensure_ascii=False)[:110]}")


if __name__ == "__main__":
    main()
