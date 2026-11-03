#!/usr/bin/env python3
"""供应链控制塔 · 证据面板 + 实时 Agent 最小闭环（ISC-22 / FE P0-A + P0-B 最小版）

两个模式（Tab）：
  🧮 工具证据 —— 零 LLM，全部经 skill 工具层直算（人看证据层）
  🤖 实时 Agent —— 浏览器问句 → openclaw agent（默认路由）→ 原答与独立核算同屏；
     可选串审计智能体（--agent auditor，第二个真实 LLM 智能体，非核算器）

运行：streamlit run panel/app.py --server.headless true --server.port 8501
改动纪律：只改本文件（前端层）；后端 SKILL/数据/网关配置已冻结（2026-09-27）。
安全：模型输出一律 html.escape 后再渲染（FE-08，按不可信文本处理）。
"""
import html
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
AGENT_TIMEOUT_S = 90  # 实测决策任务 18-39s，留余量

st.set_page_config(page_title="供应链控制塔", page_icon="🚦", layout="wide")

st.markdown("""
<style>
  .block-container {padding-top: 1.4rem; max-width: 1280px;}
  h1 {font-size: 1.7rem; margin-bottom: .1rem;}
  .stTabs [data-baseweb="tab-list"] {gap: .8rem; border-bottom: 2px solid #e8eaf0;}
  .stTabs [data-baseweb="tab"] {font-weight: 600; font-size: 1.02rem; padding: .45rem .2rem;}
  .card {background:#f7f8fc; border:1px solid #e3e6ef; border-radius:12px; padding:1rem 1.2rem; margin:.35rem 0;}
  .card h4 {margin:0 0 .3rem; font-size:1.02rem;}
  .big {font-size:1.9rem; font-weight:700; line-height:1.15;}
  .muted {color:#6b7280; font-size:.85rem;}
  .good {color:#0a7d33;} .bad {color:#c0392b;} .warn{color:#b7791f;}
  div[data-testid="stMetric"] {background:#f7f8fc; border:1px solid #e3e6ef; border-radius:12px; padding:.7rem .9rem;}
  div[data-testid="stMetricLabel"] {font-size:.85rem;}
  .ansbox {background:#101426; color:#e8ecf6; border-radius:12px; padding:1rem 1.2rem;
           font-size:.86rem; line-height:1.55; white-space:pre-wrap; font-family:ui-monospace,Menlo,Consolas,monospace;}
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1>🚦 供应链控制塔 <span class='muted' style='font-size:.95rem;font-weight:400'>"
    "补货决策 · 工具直算 + 双智能体审计</span></h1>", unsafe_allow_html=True)
st.markdown(
    f"<p class='muted'>数据读取 {time.strftime('%F %T')} · 8 条库存 / 9 条供应商 / 6 SKU · "
    "本地样本·非实时库存·合成预测 · 决策脑 StepFun step-3.7-flash（默认路由）</p>",
    unsafe_allow_html=True)

_spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tools)

_products = {p["sku"]: p["brand"] for p in json.load(open(os.path.join(DATA, "products.json")))["products"]}
_BRAND_CN = {11001: "综合咖啡", 12001: "意式浓缩", 13001: "哥伦比亚", 14001: "早餐淡焙",
             15001: "低因浓缩", 16001: "法式深焙"}
_inv = pd.read_csv(os.path.join(DATA, "inventory.csv"))
_sup = pd.read_csv(os.path.join(DATA, "suppliers.csv"))

_INV_CN = {"sku": "SKU 编号", "brand": "品牌", "location": "仓库", "quantity": "库存（件）"}
_SUP_CN = {"sku": "SKU 编号", "supplier": "供应商", "location": "发货地", "unit_cost": "单价 $",
           "shipping_to_dest": "至目标仓运费 $", "total_unit_cost": "总单价 $"}


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


def verdict_card(ok: bool, title: str, detail: str = "") -> str:
    cls, icon = ("good", "✅") if ok else ("bad", "❌")
    d = f"<div class='muted'>{detail}</div>" if detail else ""
    return f"<div class='card'><h4><span class='{cls}'>{icon} {html.escape(title)}</span></h4>{d}</div>"


tab_scan, tab_tool, tab_live = st.tabs(
    ["📋 每日巡检（产品形态）", "🧮 工具证据（零 LLM）", "🤖 实时 Agent（默认路由）"])

REPORT = os.path.join(BASE, "panel", "reports", "latest.json")
SCAN_CN = {"sku": "SKU", "brand": "品牌", "location": "仓库", "stock": "库存",
           "demand": f"需求", "gap": "缺口", "order_qty": "建议订量", "supplier": "推荐供应商",
           "supplier_city": "发货地", "unit_cost": "单价 $", "shipping": "运费 $",
           "total_unit": "总单价 $", "total_cost": "总成本 $", "flip": "翻转"}
AMPLE_CN = {"sku": "SKU", "brand": "品牌", "location": "仓库", "stock": "库存",
            "demand": "需求", "gap": "盈余"}


def load_report():
    if os.path.exists(REPORT):
        try:
            return json.load(open(REPORT))
        except Exception:
            return None
    return None


with tab_scan:
    st.markdown("##### 每日补货巡检 · 全组合一键扫描")
    st.markdown("<p class='muted'>工具直算（零 LLM、秒级、确定性）——控制塔的「早班巡检」；"
                "对例外再到「实时 Agent」页开口追问</p>", unsafe_allow_html=True)
    top, btn = st.columns([3, 1])
    if btn.button("🔄 生成巡检报告", type="primary"):
        with st.spinner("扫描中…"):
            subprocess.run([__import__("sys").executable,
                            os.path.join(BASE, "scripts", "daily_scan.py")],
                           capture_output=True, text=True, timeout=120)
    rep = load_report()
    if not rep:
        st.info("尚无报告——点右上「生成巡检报告」开始第一次全量巡检。")
    else:
        st.markdown(f"<p class='muted'>报告时间 {rep['generated_at']} · 周期 {rep['weeks']} 周 · "
                    f"{rep['combos']} 个 SKU×仓库组合</p>", unsafe_allow_html=True)
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("短缺需补货", f"{rep['shortage_count']} 个")
        k2.metric("库存充足", f"{rep['ample_count']} 个")
        k3.metric("运费翻转陷阱", f"{rep['flip_count']} 个")
        k4.metric("建议采购总额", f"${rep['total_reorder_cost']:,.0f}")
        k5.metric("无供应商组合", f"{rep['no_supplier_count']} 个")
        st.markdown("##### 短缺排行（按建议采购金额排序，⭐=运费翻转：单价最低者并非总单价最低）")
        sdf = pd.DataFrame(rep["shortages"]).rename(columns=SCAN_CN)
        if not sdf.empty:
            sdf["翻转"] = sdf["翻转"].map({True: "⭐", False: ""})
            st.dataframe(sdf, width="stretch")
            with st.expander(f"库存充足 {rep['ample_count']} 个（NO_REORDER，不展开建议）"):
                st.dataframe(pd.DataFrame(rep["ample"]).rename(columns=AMPLE_CN), width="stretch")
            st.markdown("##### 深挖例外 → 交给 Agent")
            opts = {f"{s['sku']} {s['brand']} @ {s['location']} · 缺口 {-s['gap']} · ⭐翻转" if s["flip"]
                    else f"{s['sku']} {s['brand']} @ {s['location']} · 缺口 {-s['gap']}": s
                    for s in rep["shortages"]}
            pick = st.selectbox("选择要追问的短缺组合", list(opts))
            if st.button("📝 填入问句（然后切到「实时 Agent」提交）") and pick:
                s = opts[pick]
                st.session_state["q"] = (f"{s['location']} 的 {s['brand']} 未来 {rep['weeks']} 周库存够不够？"
                                         f"要补的话找哪家供应商、总价多少？")
                st.success("已填入 ✅ 请切到「🤖 实时 Agent」页点提交（可勾审计智能体）")


# ---------------------------------------------------------------- 工具证据模式
with tab_tool:
    left, right = st.columns([1, 2])
    with left:
        st.markdown("##### 决策视图")
        sku = st.selectbox("SKU", sorted(_products),
                           format_func=lambda s: f"{s} {_BRAND_CN.get(s, '')}（{_products[s]}）")
        loc = st.selectbox("仓库", sorted(_inv.location.unique()))
        weeks = st.slider("决策周期（周）", 1, 26, 12)

        if not has_inventory(sku, loc):
            st.markdown(
                f"<div class='card'><h4><span class='warn'>⚠️ 无库存记录</span></h4>"
                f"<div class='muted'>{loc} 仓无 SKU {sku} 的库存记录。工具对无记录按 0 处理，"
                f"本面板不把未知库存当作真实零库存给补货结论。</div></div>", unsafe_allow_html=True)
        else:
            g = tools.stock_demand_difference(sku, loc, weeks)
            gap = g["gap_stock_minus_demand"]
            if gap < 0:
                board = supplier_board(sku, loc)
                best = board.iloc[0]
                flip = board.sort_values("unit_cost").iloc[0]["supplier"] != best["supplier"]
                st.markdown(
                    f"<div class='card'><h4><span class='bad'>🔻 短缺 {-gap} 件 · 建议补货 {-gap} 件</span></h4>"
                    f"<div class='big'>${-gap * best['total_unit_cost']:,.2f}</div>"
                    f"<div class='muted'>推荐 {html.escape(str(best['supplier']))}（{html.escape(str(best['location']))}）· "
                    f"${best['unit_cost']:.2f} + 运费 ${best['shipping_to_dest']:.2f} = "
                    f"<b>${best['total_unit_cost']:.2f}/件</b></div>"
                    + ("<div class='muted' style='margin-top:.4rem'>⭐ <b>运费翻转</b>：单价最低者并非总单价最低——必须含运费比价</div>" if flip else "")
                    + "</div>", unsafe_allow_html=True)
            else:
                st.markdown(verdict_card(True, "库存充足 · 无需补货",
                                         f"余量 +{gap} 件 · 负例口径 NO_REORDER:{gap} · 不给任何补货建议"),
                            unsafe_allow_html=True)
            m1, m2 = st.columns(2)
            m1.metric("当前库存", f"{g['current_stock']} 件")
            m2.metric(f"未来 {weeks} 周需求", f"{g['forecast_demand']} 件")

    with right:
        st.markdown(f"##### 未来 {weeks} 周需求预测 · {sku} @ {loc}")
        fc = tools.get_forecast(str(sku), loc).head(weeks)
        st.line_chart(fc["demand"], height=280)
        st.markdown("<p class='muted'>确定性合成预测（crc32 稳定化，不随仓库变化）——与 skill 工具层同源 · "
                    f"图示 {weeks} 个数据点 = 所选周期</p>", unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 库存全量（只读原始数据）")
        st.dataframe(_inv.rename(columns=_INV_CN), width="stretch")
    with c2:
        st.markdown(f"##### 供应商比价 · SKU {sku}（{_BRAND_CN.get(sku, '')}）→ {loc}（按总单价）")
        board = supplier_board(sku, loc)
        st.dataframe(board.rename(columns=_SUP_CN) if not board.empty else "该 SKU 无供应商记录", width="stretch")

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
        ("订量=短缺量", f(dj.get("order_qty")) == -gap, f"模型答 {dj.get('order_qty')} / 工具算 {-gap}"),
        ("供应商=总单价最低", dj.get("supplier") == best["supplier"],
         f"模型答 {dj.get('supplier')} / 工具算 {best['supplier']}"),
        ("单价一致", abs(f(dj.get("unit_cost")) - best["unit_cost"]) <= 0.01, ""),
        ("运费一致", abs(f(dj.get("shipping_cost")) - best["shipping_to_dest"]) <= 0.01, ""),
    ]
    want_total = round(f(dj.get("order_qty")) * (f(dj.get("unit_cost")) + f(dj.get("shipping_cost"))), 2)
    checks.append(("总价=订量×总单价(±0.01)", abs(f(dj.get("total_cost")) - want_total) <= 0.01,
                   f"模型答 {dj.get('total_cost')} / 实算 {want_total}"))
    return {"verdict": "PASS" if all(c[1] for c in checks) else "FAIL", "checks": checks}


def run_agent(question: str, agent: str = None) -> dict:
    """调 openclaw CLI。关键：显式补 PATH——面板服务进程的环境里没有 ~/node26/bin，
    openclaw 的 `#!/usr/bin/env node` 找不到 node（曾致 JSONDecodeError）。"""
    sid = f"pi-dgx-panel-{uuid.uuid4().hex[:8]}"
    cmd = [OPENCLAW, "agent"] + (["--agent", agent] if agent else []) + \
        ["--session-id", sid, "--message", question, "--json"]
    env = dict(os.environ)
    env["PATH"] = os.path.expanduser("~/node26/bin") + ":" + env.get("PATH", "/usr/bin:/bin")
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=AGENT_TIMEOUT_S, env=env)
    out = (p.stdout or "").strip()
    if not out:
        raise RuntimeError(f"openclaw 无输出（exit={p.returncode}）：{(p.stderr or '').strip()[-300:]}")
    try:
        d = json.loads(out)
    except json.JSONDecodeError:
        s, e = out.find("{"), out.rfind("}")
        if s == -1 or e <= s:
            raise RuntimeError(f"openclaw 输出无法解析（exit={p.returncode}）：{out[:300]}")
        d = json.loads(out[s:e + 1])
    meta = d["result"]["meta"]
    am = meta["agentMeta"]
    return {"sid": sid, "text": meta.get("finalAssistantVisibleText") or "",
            "provider": am.get("provider"), "model": am.get("model"),
            "duration_ms": am.get("durationMs"), "tools": meta.get("toolSummary", {})}


Q_DEFAULT = "San Francisco 仓库 SKU 13001 未来 12 周够卖吗？需要补货吗？"
with tab_live:
    st.markdown("##### 自然问句 → Agent 决策")
    st.markdown("<p class='muted'>每问独立会话 · 单次提交 · 本地等待 90s 超时不自动重试 · "
                "独立核算=确定性工具复算（零 LLM）</p>", unsafe_allow_html=True)

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
            k1, k2, k3 = st.columns(3)
            k1.metric("耗时", f"{r['duration_ms']/1000:.1f}s" if r.get("duration_ms") else "未知")
            k2.metric("模型", f"{r['model']}")
            k3.metric("工具调用", f"{r['tools'].get('calls', '-')} 次 / 败 {r['tools'].get('failures', '-')}")
            st.markdown(f"<p class='muted'>会话 {r['sid']} · {r['provider']}/{r['model']}</p>",
                        unsafe_allow_html=True)
            st.markdown("**Agent 原答（逐字，已转义）**")
            st.markdown(f"<div class='ansbox'>{html.escape(r['text'])}</div>", unsafe_allow_html=True)
            dj = last_json_block(r["text"])
            lines = [l.strip() for l in r["text"].splitlines() if l.strip()]
            if dj and dj.get("decision") == "REORDER":
                v = verify_decision(dj)
                rows = "".join(
                    f"<div>{('✅' if ok else '❌')} {html.escape(name)} "
                    f"<span class='muted'>{html.escape(detail)}</span></div>"
                    for name, ok, detail in v["checks"])
                ok_cn = "通过" if v["verdict"] == "PASS" else "未通过"
                st.markdown(verdict_card(v["verdict"] == "PASS", f"独立核算：{ok_cn}", rows),
                            unsafe_allow_html=True)
            elif lines and re.fullmatch(r"NO_REORDER:\d+", lines[-1]):
                surplus = re.fullmatch(r"NO_REORDER:(\d+)", lines[-1]).group(1)
                st.markdown(verdict_card(True, f"负例合规：无需补货 · 盈余 {surplus} 件",
                                         f"模型末行为纯文本 {lines[-1]}（协议原样保留）· 零补货建议"),
                            unsafe_allow_html=True)
            else:
                st.markdown(verdict_card(False, "未通过：没有合格的决策单，末行也不是 NO_REORDER 纯文本"),
                            unsafe_allow_html=True)
            if with_audit and dj and dj.get("decision") == "REORDER":
                st.markdown("**审计智能体（auditor）独立复算判定**")
                msg = (f"审计以下补货决策单。原问句：{q}\n\n待审决策单：\n{json.dumps(dj, ensure_ascii=False)}\n\n"
                       f"来源会话：{r['sid']}。按 supply-chain-audit SOP 独立复算并输出审计判定 JSON。")
                a = run_agent(msg, agent="auditor")
                st.markdown(f"<div class='ansbox'>{html.escape(a['text'])}</div>", unsafe_allow_html=True)
                st.markdown(f"<p class='muted'>auditor 工具调用 {a['tools'].get('calls')} 次 / "
                            f"败 {a['tools'].get('failures')} · 会话 {a['sid']}</p>", unsafe_allow_html=True)
        except subprocess.TimeoutExpired:
            ph.empty()
            st.error(f"未出决策：本地等待超过 {AGENT_TIMEOUT_S}s（本地等待已中止、不自动重试；网关侧任务状态未知）")
        except Exception as e:
            ph.empty()
            st.error(f"未出决策：{type(e).__name__}: {e}"[:500] + "（不自动重试，可手动重新提交）")
        finally:
            st.session_state["running"] = False
