#!/usr/bin/env python3
"""custom_data 纯逻辑单测（跑法：python3 panel/test_custom_data.py && echo ALL-GREEN）。"""
import io
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import custom_data as cd  # noqa: E402


def t_parse():
    csv = "料号,品名,仓库,库存,周需求\nA1,螺栓,上海仓,10,50\nA2,螺母,苏州仓,900,20\n"
    df = cd.parse_upload(csv.encode("utf-8"), "inv.csv")
    assert list(df.columns)[:4] == ["料号", "品名", "仓库", "库存"]
    df_gbk = cd.parse_upload(csv.encode("gbk"), "inv.csv")
    assert df_gbk.shape == (2, 5)
    print("parse_upload OK（utf-8/gbk）")


def t_mapping_reply():
    ok = '建议如下：\n```json\n{"mapping": {"sku": {"column": "料号", "confidence": 0.95}}, "unmapped_columns": []}\n```\n完毕'
    assert cd.parse_mapping_reply(ok)["mapping"]["sku"]["column"] == "料号"
    assert cd.parse_mapping_reply("抱歉我不认识这表") is None
    assert "料号" in cd.build_mapping_prompt(pd.DataFrame({"料号": ["A1"], "库存": [3]}))
    print("mapping 提示词/回复解析 OK")


def t_validate():
    df = pd.DataFrame({
        "料号": ["A1", "A1", "A2"], "品名": ["螺栓", "螺栓", "螺母"],
        "仓": ["上海", "上海", "苏州"], "库存": [10, 10, 900],
        "供": ["甲", "乙", ""], "城": ["上海", "苏州", ""], "价": [8.0, 7.0, None],
    })
    col = {"sku": "料号", "product_name": "品名", "location": "仓", "quantity": "库存",
           "weekly_demand": None, "supplier": "供", "supplier_city": "城", "unit_cost": "价"}
    canon, errs, notes = cd.validate_and_convert(df, col, default_weekly_demand=50)
    assert not errs and len(canon) == 3  # 全行保留（长表多供应商不丢比价信息）
    assert any("长表多供应商" in n for n in notes)  # 重复组合给说明
    assert any("手填估算" in n for n in notes)
    assert canon.iloc[0]["weekly_demand"] == 50.0
    # 必填缺失
    _, errs2, _ = cd.validate_and_convert(df, {k: v for k, v in col.items() if k != "location"}, 50)
    assert any("location" in e or "仓库/地点" in e for e in errs2)
    print("validate_and_convert OK（去重/估算/必填校验）")


def t_scan():
    canon = pd.DataFrame({
        "sku": ["A1", "A1", "A2", "A3"],
        "product_name": ["螺栓", "螺栓", "螺母", "垫片"],
        "location": ["上海", "苏州", "苏州", "苏州"],  # A1 在两仓
        "quantity": [10, 500, 900, 5],
        "weekly_demand": [50.0, 50.0, 20.0, 30.0],
        "supplier": ["甲", "甲", "乙", ""],
        "supplier_city": ["上海", "上海", "苏州", ""],
        "unit_cost": [8.0, 8.0, 7.0, float("nan")],
    })
    ship = lambda s, d: 5.0 if s == "上海" else 1.0  # noqa: E731
    rep = cd.custom_scan(canon, weeks=12, ship_fn=ship)
    s = {(x["sku"], x["location"]): x for x in rep["shortages"]}
    a = {(x["sku"], x["location"]): x for x in rep["ample"]}
    assert ("A2", "苏州") in a and ("A1", "上海") in s  # 900 vs 240 充足；10 vs 600 短缺
    x = s[("A1", "上海")]
    assert x["order_qty"] == 590 and x["supplier"] == "甲" and x["shipping"] == 5.0
    assert abs(x["total_cost"] - 590 * 13.0) < 0.01  # 8+5
    assert ("A3", "苏州") in s and s[("A3", "苏州")]["supplier"] == ""  # 无供应商→只出缺口
    assert rep["no_supplier_count"] == 1 and rep["ample_count"] == 1
    # 翻转：同 SKU 两个供应商，单价低者运费高
    canon2 = canon.copy()
    canon2.loc[len(canon2)] = ["A4", "圈", "上海", 1, 40, "远供", "上海", 6.0]
    canon2.loc[len(canon2)] = ["A4", "圈", "上海", 1, 40, "近供", "苏州", 7.5]
    canon2 = canon2[~((canon2.sku == "A1"))]
    rep2 = cd.custom_scan(canon2, weeks=12, ship_fn=ship)
    x4 = [z for z in rep2["shortages"] if z["sku"] == "A4"][0]
    # 远供 6+5=11 vs 近供 7.5+1=8.5 → 近供胜，翻转
    assert x4["supplier"] == "近供" and x4["flip"] is True
    print("custom_scan OK（缺口/比价/翻转/无供应商降级）")


if __name__ == "__main__":
    t_parse(); t_mapping_reply(); t_validate(); t_scan()
    print("ALL-GREEN")
