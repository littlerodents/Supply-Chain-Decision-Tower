#!/usr/bin/env python3
"""数据集规模化 v2：6 SKU → 48 SKU（一次性、可复现，random.seed(42)）。

安全约束（保证金答案证据链）：
  - 纯增量：新 SKU 21001..21042 只追加行，不动旧数据；
  - 新 SKU 库存只放 San Francisco / Portland，不放 Seattle（pos-qry-001 的 Seattle
    列举金答案保持不变）；
  - evals.json 不动 —— 评测集仍为 16 任务，新 SKU 不进评测。
运行后必须跑 gold_gen.py + diff 验证旧金答案零变化。

库存策略：先按工具公式算每个 SKU 的 12 周需求（确定性），再按配额设库存——
  1/3 SKU 设为深度短缺（库存≈需求的 0-8%），2/3 设为充足（150-260%）。
供应商策略：60% 单供应商；40% 双/三供应商，其中约半数刻意制造运费翻转
  （单价最低者 + 运费后反超），单价区间 $14-40。
"""
import importlib.util
import json
import os
import random

random.seed(42)
BASE = os.path.expanduser("~/.openclaw/workspace/skills/supply-chain-control-tower")
spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)

BRANDS = [
    "Ethiopian Yirgacheffe", "Kenya AA", "Guatemala Antigua", "Sumatra Mandheling",
    "Costa Rica Tarrazu", "Blue Mountain Blend", "Mocha Java", "Espresso Forte",
    "Midnight Roast", "Morning Fog", "Pacific Bold", "Sunrise citrus Roast",
    "Hazelnut Cream", "Vanilla Velvet", "Caramel Crunch", "Cinnamon Spice",
    "Peppermint Mocha", "Pumpkin Harvest", "Maple Pecan", "Coconut Breeze",
    "Alpine Frost", "Desert Bloom", "Harbor Lights", "Golden Gate Roast",
    "Emerald City", "Cascade Dawn", "Redwood Reserve", "Sierra High",
    "Coastal Mist", "Valley Gold", "Autumn Ember", "Winter Warmth",
    "Spring Bloom", "Summer Solstice", "Autumn Leaves", "Winter Spice",
    "Velvet Evening", "Copper Kettle", "Silver Skillet", "Bronze Brew",
    "Ivory Cream", "Jade Leaf", "Amber Glow", "Onyx Dark", "Pearl White",
    "Coral Reef", "Sapphire Sky", "Titanium Roast",
]  # 48 个名字，取前 42 生成 21001..21042

CITIES = ["San Francisco", "Portland", "Los Angeles", "Chicago"]
PREFIXES = ["Roastery", "Coffee Co.", "Trading", "Beans", "Imports", "Blenders"]


def demand12(sku: int) -> int:
    return int(tools.get_forecast(str(sku), "x").head(12)["demand"].sum())


def make_supplier_name(i: int) -> str:
    return f"{BRANDS[i % len(BRANDS)].split()[0]} {random.choice(PREFIXES)} #{i}"


def main():
    products, inv_rows, sup_rows = [], [], []
    sup_id = 0
    for i, brand in enumerate(BRANDS[:42]):
        sku = 21001 + i
        products.append({"sku": sku, "brand": brand,
                         "name": f"{brand} Coffee",
                         "description": "Portfolio line for control-tower batch scan demo."})
        d12 = demand12(sku)
        # 1/3 短缺（新仓），2/3 充足；仓库只在 SF/Portland（保证金答案不变）
        locs = random.sample(["San Francisco", "Portland"], k=random.choice([1, 1, 2]))
        for loc in locs:
            if i % 3 == 0:
                qty = max(0, int(d12 * random.uniform(0.0, 0.08)))
            else:
                qty = int(d12 * random.uniform(1.5, 2.6))
            inv_rows.append({"sku": sku, "brand": brand, "location": loc, "quantity": qty})
        # 供应商：60% 单，40% 多（多供应商时一半刻意翻转）
        n_sup = 1 if i % 5 in (0, 1, 2) else random.choice([2, 3])
        cities = random.sample(CITIES, k=n_sup)
        force_flip = n_sup > 1 and i % 4 == 3
        base = round(random.uniform(14, 38), 2)
        for j, city in enumerate(cities):
            sup_id += 1
            if n_sup == 1:
                cost = base
            elif force_flip and j == 0:
                cost = round(base - random.uniform(1.0, 3.0), 2)  # 单价最低
            else:
                cost = round(base + random.uniform(0.0, 4.0), 2)
            sup_rows.append({"sku": sku, "supplier": make_supplier_name(sup_id),
                             "location": city, "unit_cost": cost})
    print(f"生成：{len(products)} SKU / {len(inv_rows)} 库存行 / {len(sup_rows)} 供应商行")
    return products, inv_rows, sup_rows


if __name__ == "__main__":
    products, inv_rows, sup_rows = main()

    p = json.load(open(os.path.join(BASE, "data", "products.json")))
    exist = {x["sku"] for x in p["products"]}
    p["products"] += [x for x in products if x["sku"] not in exist]
    json.dump(p, open(os.path.join(BASE, "data", "products.json"), "w"), indent=4, ensure_ascii=False)

    inv_path = os.path.join(BASE, "data", "inventory.csv")
    lines = open(inv_path).read().rstrip("\n").splitlines()
    lines += [f"{r['sku']},{r['brand']},{r['location']},{r['quantity']}" for r in inv_rows
              if f"{r['sku']}," not in "\n".join(l for l in lines if l.startswith(str(r["sku"]) + ","))]
    open(inv_path, "w").write("\n".join(lines) + "\n")

    sup_path = os.path.join(BASE, "data", "suppliers.csv")
    lines = open(sup_path).read().rstrip("\n").splitlines()
    have = {(l.split(",")[0], l.split(",")[1]) for l in lines[1:]}
    add = [f"{r['sku']},{r['supplier']},{r['location']},{r['unit_cost']:.2f}" for r in sup_rows]
    lines += [a for a in add if (a.split(",")[0], a.split(",")[1]) not in have]
    open(sup_path, "w").write("\n".join(lines) + "\n")
    print("data/*.json|csv 已追加（幂等，重复运行不重复插入）")
