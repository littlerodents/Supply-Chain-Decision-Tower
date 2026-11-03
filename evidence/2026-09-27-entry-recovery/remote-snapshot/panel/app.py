#!/usr/bin/env python3
"""供应链控制塔 · 证据面板 + 实时 Agent 最小闭环（ISC-22 / FE P0-A + P0-B 最小版）

两个模式（Tab）：
  🧮 工具证据 —— 零 LLM，全部经 skill 工具层直算（人看证据层）
  🤖 实时 Agent —— 浏览器问句 → openclaw agent（默认路由）→ 原答与独立核算同屏；
     可选串审计智能体（--agent auditor，第二个真实 LLM 智能体，非核算器）

运行：streamlit run panel/app.py --server.headless true --server.port 8501
改动纪律：只改本文件（前端层）；后端 SKILL/数据/网关配置已冻结（2026-09-27）。
"""
import importlib.util
import json
import os
import re
import subprocess
import time
import uuid

import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # skill 根
DATA = os.path.join(BASE, "data")
OPENCLAW = os.path.expanduser("~/node26/bin/openclaw")
AGENT_TIMEOUT_S = 90  # 实测决策任务 18-39s，留余量（PRD v0.2 拟 60s 偏紧）

st.set_page_config(page_title="供应链控制塔", page_icon="🚦", layout="wide")
st.title("🚦 供应链控制塔 · 控制面板")
st.caption("工具层直算零 LLM · 决策脑 StepFun step-3.7-flash（默认路由）· 本地样本 · 非实时库存 · 合成预测")

_spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tools)

_products = {p["sku"]: p["brand"] for p in json.load(open(os.path.join(DATA, "products.json")))["products"]}
_inv = pd.read_csv(os.path.join(DATA, "inventory.csv"))
_sup = pd.read_csv(os.path.join(DATA, "suppliers.csv"))
st.caption(f"数据读取时间 {time.strftime('%F %T')} · {_inv.shape[0]} 条库存行 / {_sup.shape[0]} 条供应商行 / {len(_products)} SKU")


def has_inventory(sku: int, loc: str) -> bool:
    return bool(((_inv.sku == sku) & (_inv.location == loc)).any())


def supplier_board(sku: int, dest: str) -> pd.DataFrame:
    """该 SKU 全部候选供应商：真实发货地 + 至目标仓运费 + 总单价（含运费翻转）。"""
    rows = _sup[_sup.sku == sku].copy()
    if rows.empty:
        return rows
    rows["shipping_to_dest"] = [tools.get_shipping_cost(c, dest) for c in rows["location"]]
    rows["total_unit_cost"] = (rows["unit_cost"] + rows["shipping_to_dest"]).round(2)
    return rows.sort_values("total_unit_cost")


tab_tool, tab_live = st.tabs(["🧮 工具证据（零 LLM）", "🤖 实时 Agent（默认路由）"])

# ---------------------------------------------------------------- 工具证据模式
with tab_tool:
    left, right = st.columns([1, 2])
    with left:
        st.subheader("决策视图")
        sku = st.selectbox("SKU", sorted(_products), format_func=lambda s: f"{s} {_products[s]}")
        loc = st.selectbox("仓库", sorted(_inv.location.unique()))
        weeks = st.slider("决策周期（周）", 1, 26, 12)

        if not has_inventory(sku, loc):
            st.warning(f"⚠️ {loc} 仓无 SKU {sku} 的库存记录——工具对无记录按 0 处理，"
                       "本面板不把未知库存当作真实零库存给补货结论。请换有效组合。")
        else:
            g = tools.stock_demand_difference(sku, loc, weeks)
            gap = g["gap_stock_minus_demand"]
            if gap < 0:
                st.error(f"短缺 {-gap} 件 → 需补货（建议订量 {-gap}）")
                board = supplier_board(sku, loc)
                if not board.empty:
                    best = board.iloc[0]
                    flip = board.sort_values("unit_cost").iloc[0]["supplier"] != best["supplier"]
                    st.markdown(
                        f"**推荐（总单价最低）**：{best['supplier']}（{best['location']}）"
                        f"· 单价 ${best['unit_cost']:.2f} + 运费 ${best['shipping_to_dest']:.2f}"
                        f" = **${best['total_unit_cost']:.2f}/件** · 总成本 {-gap * best['total_unit_cost']:,.2f} USD"
                        + ("\n\n⭐ **运费翻转**：单价最低者并非总单价最低——必须含运费比价。" if flip else ""))
            elif gap == 0:
                st.success("恰好充足 · 余量 0 件 → 无需补货（NO_REORDER:0）")
            else:
                st.success(f"充足 · 余量 +{gap} 件 → 无需补货（NO_REORDER:{gap}）")
            st.metric("当前库存", f"{g['current_stock']} 件")
            st.metric(f"未来 {weeks} 周预测需求", f"{g['forecast_demand']} 件")

    with right:
        st.subheader(f"未来 {weeks} 周需求预测 · {sku} @ {loc}（{weeks} 个数据点）")
        fc = tools.get_forecast(str(sku), loc).head(weeks)
        st.line_chart(fc["demand"], height=260)
        st.caption("确定性合成预测（crc32 稳定化，不随仓库变化）——与 skill 工具层同源，跨进程一致")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("库存全量（只读原始数据）")
        st.dataframe(_inv, width="stretch")
    with c2:
        st.subheader(f"供应商比价 · SKU {sku} → {loc}（按总单价排序）")
        board = supplier_board(sku, loc)
        st.dataframe(board if not board.empty else "该 SKU 无供应商记录", width="stretch")

# ------------------------------------------------------------ 实时 Agent 模式
def last_json_block(text: str):
    blocks = [b for b in text.split("```") if b.strip().startswith("json")]
    if not blocks:
        return None
    try:
        return json.loads(blocks[-1].strip()[4:].strip())
    except Exception:
        return None


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def verify_decision(dj: dict) -> dict:
    """确定性独立核算（零 LLM）：决策单字段 vs 工具直算。"""
    if not isinstance(dj, dict) or dj.get("decision") != "REORDER":
        return {"verdict": "FAIL", "checks": [("决策类型", False, "非 REORDER 决策单")]}
    try:
        sku, loc, weeks = int(dj.get("sku")), dj.get("location"), int(dj.get("weeks"))
    except (TypeError, ValueError):
        return {"verdict": "FAIL", "checks": [("输入参数", False, "sku/location/weeks 不完整")]}
    if not has_inventory(sku, loc):
        return {"verdict": "FAIL", "checks": [("库存记录", False, f"{loc} 无 SKU {sku} 库存记录")]}
    g = tools.stock_demand_difference(sku, loc, weeks)
    gap = g["gap_stock_minus_demand"]
    board = supplier_board(sku, loc)
    if board.empty:
        return {"verdict": "FAIL", "checks": [("供应商", False, f"SKU {sku} 无供应商记录")]}
    best = board.iloc[0]
    checks = [
        ("订量=短缺量", f(dj.get("order_qty")) == -gap, f"claimed {dj.get('order_qty')} / 工具 {-gap}"),
        ("供应商=总单价最低", dj.get("supplier") == best["supplier"],
         f"claimed {dj.get('supplier')} / 工具 {best['supplier']}"),
        ("单价一致", abs(f(dj.get("unit_cost")) - best["unit_cost"]) <= 0.01, ""),
        ("运费一致", abs(f(dj.get("shipping_cost")) - best["shipping_to_dest"]) <= 0.01, ""),
    ]
    want_total = round(f(dj.get("order_qty")) * (f(dj.get("unit_cost")) + f(dj.get("shipping_cost"))), 2)
    checks.append(("总价=订量×总单价(±0.01)", abs(f(dj.get("total_cost")) - want_total) <= 0.01,
                   f"claimed {dj.get('total_cost')} / 实算 {want_total}"))
    return {"verdict": "PASS" if all(c[1] for c in checks) else "FAIL", "checks": checks}


def run_agent(question: str, agent: str = None) -> dict:
    sid = f"pi-dgx-panel-{uuid.uuid4().hex[:8]}"
    cmd = [OPENCLAW, "agent"] + (["--agent", agent] if agent else []) + \
        ["--session-id", sid, "--message", question, "--json"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=AGENT_TIMEOUT_S)
    d = json.loads(p.stdout)
    meta = d["result"]["meta"]
    am = meta["agentMeta"]
    return {"sid": sid, "text": meta.get("finalAssistantVisibleText") or "",
            "provider": am.get("provider"), "model": am.get("model"),
            "duration_ms": am.get("durationMs"), "tools": meta.get("toolSummary", {})}


Q_DEFAULT = "San Francisco 仓库 SKU 13001 未来 12 周够卖吗？需要补货吗？"
with tab_live:
    st.subheader("自然问句 → Agent 决策（同屏：原答 + 独立核算）")
    st.caption(f"每问独立会话 · 单次提交 · 本地等待 {AGENT_TIMEOUT_S}s 超时不自动重试 · 独立核算为确定性工具复算（零 LLM）")

    if "q" not in st.session_state:
        st.session_state["q"] = Q_DEFAULT
    b1, b2, b3 = st.columns(3)
    if b1.button("填入：正例 T-01"):
        st.session_state["q"] = Q_DEFAULT
    if b2.button("填入：负例 T-02"):
        st.session_state["q"] = "Seattle 仓库 SKU 13001 未来 1 周够卖吗？需要补货吗？"
    if b3.button("填入：运费翻转陷阱"):
        st.session_state["q"] = "San Francisco 的 Breakfast Blend 未来 12 周库存够不够？要补的话找哪家供应商、总价多少？"
    q = st.text_area("问句", key="q", height=90)
    with_audit = st.checkbox("串审计智能体（第二个真实 LLM 智能体独立复算）", value=True)

    if st.button("▶ 提交（单次）", type="primary", disabled=bool(st.session_state.get("running"))):
        st.session_state["running"] = True
        ph = st.empty()
        ph.info("运行中…（独立会话，请勿重复提交）")
        try:
            r = run_agent(q)
            ph.empty()
            with st.container():
                l, rr = st.columns([2, 1])
                with l:
                    st.markdown("**Agent 原答（逐字）**")
                    st.text(r["text"])
                with rr:
                    st.metric("耗时", f"{r['duration_ms']/1000:.1f}s" if r.get("duration_ms") else "未知")
                    st.caption(f"{r['provider']}/{r['model']}")
                    st.caption(f"会话 {r['sid']}")
                    st.caption(f"工具调用 {r['tools'].get('calls')} 次 / 失败 {r['tools'].get('failures')} 次")
                dj = last_json_block(r["text"])
                lines = [l.strip() for l in r["text"].splitlines() if l.strip()]
                if dj and dj.get("decision") == "REORDER":
                    v = verify_decision(dj)
                    (st.success if v["verdict"] == "PASS" else st.error)(f"独立核算：{v['verdict']}")
                    for name, ok, detail in v["checks"]:
                        st.markdown(f"{'✅' if ok else '❌'} {name} {detail}")
                elif lines and re.fullmatch(r"NO_REORDER:\d+", lines[-1]):
                    st.success(f"负例合规：末行纯文本 {lines[-1]}（零补货建议字段）")
                else:
                    st.error("未通过：无合规决策 JSON，且末行非 NO_REORDER 纯文本")
                if with_audit and dj and dj.get("decision") == "REORDER":
                    st.markdown("**审计智能体（auditor）独立复算判定**")
                    msg = (f"审计以下补货决策单。原问句：{q}\n\n待审决策单：\n{json.dumps(dj, ensure_ascii=False)}\n\n"
                           f"来源会话：{r['sid']}。按 supply-chain-audit SOP 独立复算并输出审计判定 JSON。")
                    a = run_agent(msg, agent="auditor")
                    st.text(a["text"])
                    st.caption(f"auditor 工具调用 {a['tools'].get('calls')} 次 / 失败 {a['tools'].get('failures')} 次 · 会话 {a['sid']}")
        except subprocess.TimeoutExpired:
            ph.empty()
            st.error(f"未出决策：本地等待超过 {AGENT_TIMEOUT_S}s（本地等待已中止、不自动重试；网关侧任务状态未知）")
        except Exception as e:
            ph.empty()
            st.error(f"未出决策：{type(e).__name__}（不自动重试，可手动重新提交）")
        finally:
            st.session_state["running"] = False
