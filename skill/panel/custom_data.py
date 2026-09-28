#!/usr/bin/env python3
"""用户上传数据的解析 / AI 映射 / 校验 / 巡检（纯逻辑，可单测；UI 在 app.py）。

设计原则：
  - AI 只提议映射，人工确认后才生效（映射错了决策全错）；
  - 缺列诚实降级：无供应商列→只出缺口订量；无发货地→比价不含运费并标注；
    无需求列→用用户手填的全局周均需求，明确标注为估算；
  - 与内置演示数据完全隔离：本模块不读写 skill/data，只消费传入的 DataFrame；
    预测/运费用 tools 的纯函数（get_forecast 只依赖 SKU、get_shipping_cost 只依赖城市名）。
"""
import io
import json

import pandas as pd

# 目标字段：canonical 名 → 中文说明（必填/可选）
MAPPING_FIELDS = {
    "sku": "SKU/料号/品号（必填，唯一编号）",
    "product_name": "品名（可选）",
    "location": "仓库/地点（必填）",
    "quantity": "当前库存数量（必填，数值）",
    "weekly_demand": "周需求/预测（可选，数值；没有则手填全局估算）",
    "supplier": "供应商名称（可选；提供后出比价推荐）",
    "supplier_city": "供应商发货地/城市（可选；提供后含运费比价）",
    "unit_cost": "采购单价（可选，数值）",
}


def parse_upload(raw: bytes, filename: str) -> pd.DataFrame:
    """CSV（utf-8→gbk 容错）或 Excel → DataFrame。"""
    name = filename.lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(raw), engine="openpyxl")
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别编码（尝试 utf-8/gbk 均失败）")


def build_mapping_prompt(df: pd.DataFrame) -> str:
    """把表头+3 行样例发给 agent，请求映射建议 JSON。"""
    sample = df.head(3).to_csv(index=False)
    fields = json.dumps(MAPPING_FIELDS, ensure_ascii=False, indent=1)
    return f"""你是数据集成工程师。用户上传了一张库存表，列名如下（含 3 行样例）：

{sample}

请把各列映射到目标字段。目标字段说明：
{fields}

只输出一个 json 代码块，格式：
```json
{{"mapping": {{"sku": {{"column": "原列名或null", "confidence": 0.9}}, ...}},
 "unmapped_columns": ["无法归类的原列名"],
 "notes": "一句话说明 ambiguous 的判断"}}
```
注意：weekly_demand 接受"周需求/周预测/月销量(注明 monthly)"等，宁可低置信也不要乱配；
找不到合适列就填 null。"""


def parse_mapping_reply(text: str) -> dict | None:
    """从 agent 回复提取映射建议；失败返回 None（UI 退回纯手动）。"""
    blocks = [b for b in text.split("```") if b.strip().startswith("json")]
    for b in reversed(blocks):
        try:
            d = json.loads(b.strip()[4:].strip())
            if "mapping" in d:
                return d
        except Exception:
            continue
    return None


def validate_and_convert(df: pd.DataFrame, column_of: dict, default_weekly_demand: float):
    """人工确认后的转换+校验。返回 (canon_df, errors, notes)。"""
    errors, notes = [], []

    def col(field):
        return column_of.get(field) or None

    for must in ("sku", "location", "quantity"):
        if not col(must):
            errors.append(f"必填字段未映射：{MAPPING_FIELDS[must]}")
    if errors:
        return None, errors, notes
    canon = pd.DataFrame({
        "sku": df[col("sku")].astype(str).str.strip(),
        "product_name": df[col("product_name")].astype(str) if col("product_name") else "",
        "location": df[col("location")].astype(str).str.strip(),
        "quantity": pd.to_numeric(df[col("quantity")], errors="coerce"),
    })
    if canon["quantity"].isna().any():
        errors.append(f"库存列存在非数值行：{int(canon['quantity'].isna().sum())} 行")
        return None, errors, notes
    if col("weekly_demand"):
        canon["weekly_demand"] = pd.to_numeric(df[col("weekly_demand")], errors="coerce")
        n_bad = int(canon["weekly_demand"].isna().sum())
        if n_bad:
            notes.append(f"需求列 {n_bad} 行非数值，按全局估算 {default_weekly_demand} 补")
            canon["weekly_demand"] = canon["weekly_demand"].fillna(default_weekly_demand)
    else:
        canon["weekly_demand"] = float(default_weekly_demand)
        notes.append(f"未映射需求列：全部按手填估算 周均 {default_weekly_demand}（非真实预测）")
    canon["supplier"] = df[col("supplier")].astype(str) if col("supplier") else ""
    canon["supplier_city"] = df[col("supplier_city")].astype(str) if col("supplier_city") else ""
    if col("unit_cost"):
        canon["unit_cost"] = pd.to_numeric(df[col("unit_cost")], errors="coerce")
    else:
        canon["unit_cost"] = float("nan")
    dup = canon.duplicated(subset=["sku", "location"]).sum()
    if dup:
        q_conflict = canon[canon.duplicated(subset=["sku", "location"], keep=False)] \
            .groupby(["sku", "location"])["quantity"].nunique().gt(1).sum()
        notes.append(f"{dup} 行 SKU×仓库重复（长表多供应商属正常）——缺口按该组合首行的库存计算，"
                     f"供应商比价用该 SKU 全部行；库存值冲突的组合数：{int(q_conflict)}")
    if not col("supplier"):
        notes.append("未映射供应商列：巡检只出缺口与建议订量，不出'找谁买'")
    elif not col("supplier_city"):
        notes.append("未映射供应商发货地：比价不含运费（标注'未含运费'）")
    return canon.reset_index(drop=True), errors, notes


def custom_scan(canon: pd.DataFrame, weeks: int, ship_fn, forecast_fn=None) -> dict:
    """在用户数据上跑巡检，报告结构与 daily_scan 一致（便于复用渲染）。"""
    sup_rows = canon[(canon["supplier"] != "") & canon["supplier"].notna() & (canon["unit_cost"] > 0)] \
        if "supplier" in canon else pd.DataFrame()
    Z, LEAD, CV = 1.645, 1.0, 0.20  # 95% SL；自有数据无需求历史：σ 按 CV=0.2 估算、提前期按 1 周
    shortages, ample = [], []
    uniq = canon.drop_duplicates(subset=["sku", "location"], keep="first")
    for _, r in uniq.iterrows():
        mu = float(r["weekly_demand"])
        demand = mu * weeks
        ss = Z * (CV * mu) * (LEAD ** 0.5)
        rop = mu * LEAD + ss
        rop_gap = rop - float(r["quantity"])
        gap = float(r["quantity"]) - demand
        base = {"sku": r["sku"], "brand": r["product_name"] or r["sku"], "location": r["location"],
                "stock": int(r["quantity"]), "demand": int(round(demand)), "gap": int(round(gap)),
                "rop_gap": int(round(rop_gap)), "safety_stock": round(ss, 1)}
        if rop_gap > 0:  # ROP 驱动：库存已跌破再订货点 = 需补货
            entry = dict(base, order_qty=int(round(rop_gap + ss)))
            cands = sup_rows[(sup_rows["sku"] == r["sku"])].drop_duplicates(
                subset=["supplier"], keep="first") if not sup_rows.empty else pd.DataFrame()
            if not cands.empty:
                has_city = (cands["supplier_city"] != "").all()
                cands = cands.copy()
                cands["ship"] = [float(ship_fn(c, r["location"])) for c in cands["supplier_city"]] \
                    if has_city else 0.0
                cands["total_unit"] = cands["unit_cost"] + cands["ship"]
                cands = cands.sort_values("total_unit")
                best = cands.iloc[0]
                flip = bool(has_city and cands.sort_values("unit_cost").iloc[0]["supplier"] != best["supplier"])
                entry.update({
                    "supplier": best["supplier"], "supplier_city": best["supplier_city"],
                    "unit_cost": float(best["unit_cost"]),
                    "shipping": float(best["ship"]) if has_city else 0.0,
                    "total_unit": float(best["total_unit"]),
                    "total_cost": round(entry["order_qty"] * float(best["total_unit"]), 2),
                    "flip": flip, "no_shipping": not has_city,
                })
            else:
                entry.update({"supplier": "", "supplier_city": "", "unit_cost": 0.0, "shipping": 0.0,
                              "total_unit": 0.0, "total_cost": 0.0, "flip": False, "no_shipping": False})
            shortages.append(entry)
        else:
            ample.append(base)
    shortages.sort(key=lambda x: -x["total_cost"])
    return {"generated_at": __import__("time").strftime("%F %T"), "weeks": weeks,
            "combos": len(uniq), "shortage_count": len(shortages), "ample_count": len(ample),
            "flip_count": sum(1 for s in shortages if s.get("flip")),
            "no_supplier_count": sum(1 for s in shortages if not s.get("supplier")),
            "total_reorder_cost": round(sum(s["total_cost"] for s in shortages), 2),
            "shortages": shortages, "ample": ample}
