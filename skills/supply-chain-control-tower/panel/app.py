#!/usr/bin/env python3
"""供应链控制塔 · 证据面板（ISC-22）

Streamlit 只读面板：库存/供应商/缺口/预测全部经 skill 工具层直算，零 LLM——
塔台的「人看证据层」，agent 问答走 OpenClaw（「agent 干活层」），人机双入口。

运行：streamlit run panel/app.py --server.headless true --server.port 8501
"""
import importlib.util
import os

import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # skill 根
DATA = os.path.join(BASE, "data")

st.set_page_config(page_title="供应链控制塔", page_icon="🚦", layout="wide")
st.title("🚦 供应链控制塔 · 证据面板")
st.caption("数据经 supply-chain-control-tower skill 工具层直算（零 LLM）· 转化自 ikatsov/tensor-house（Apache-2.0）")

_spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tools)

left, right = st.columns([1, 2])
with left:
    st.subheader("决策视图")
    sku = st.selectbox("SKU", [11001, 12001, 13001],
                       format_func=lambda s: {11001: "11001 House Blend", 12001: "12001 Italian Roast",
                                              13001: "13001 Colombian"}[s])
    loc = st.selectbox("仓库", ["San Francisco", "Portland", "Seattle"])
    weeks = st.slider("决策周期（周）", 1, 26, 12)

    g = tools.stock_demand_difference(sku, loc, weeks)
    if g["gap_stock_minus_demand"] < 0:
        st.error(f"短缺 {-g['gap_stock_minus_demand']} 件 → 需补货")
        ship = tools.get_shipping_cost("Seattle", loc)
        st.info(f"参考：Seattle 发货至 {loc} 单件运费 ${ship:.2f}")
    else:
        st.success(f"充足 · 余量 +{g['gap_stock_minus_demand']} 件 → 无需补货")
    st.metric("当前库存", f"{g['current_stock']} 件")
    st.metric(f"未来 {weeks} 周预测需求", f"{g['forecast_demand']} 件")

with right:
    st.subheader(f"52 周需求预测 · {sku} @ {loc}")
    fc = tools.get_forecast(str(sku), loc).head(weeks if weeks >= 8 else 12)
    st.line_chart(fc["demand"], height=260)
    st.caption("确定性合成预测（crc32 稳定化）——与 skill 工具层同源，跨进程一致")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader("库存全量")
    st.dataframe(pd.read_csv(os.path.join(DATA, "inventory.csv")), use_container_width=True)
with c2:
    st.subheader("供应商格局")
    st.dataframe(pd.read_csv(os.path.join(DATA, "suppliers.csv")), use_container_width=True)
