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
_BRAND_CN = {
    "House Blend": "综合咖啡", "Italian Roast": "意式浓缩", "Colombian Coffee": "哥伦比亚",
    "Breakfast Blend": "早餐淡焙", "Decaf Espresso": "低因浓缩", "French Roast": "法式深焙",
    "Ethiopian Yirgacheffe": "耶加雪菲", "Kenya AA": "肯亚AA", "Guatemala Antigua": "危地马拉安提瓜",
    "Sumatra Mandheling": "苏门答腊曼特宁", "Costa Rica Tarrazu": "哥斯达黎加塔拉珠",
    "Blue Mountain Blend": "蓝山综合", "Mocha Java": "摩卡爪哇", "Espresso Forte": "浓缩特调",
    "Midnight Roast": "午夜深焙", "Morning Fog": "晨雾", "Pacific Bold": "太平洋浓香",
    "Sunrise citrus Roast": "日出果香焙", "Hazelnut Cream": "榛果奶油", "Vanilla Velvet": "香草丝滑",
    "Caramel Crunch": "焦糖脆", "Cinnamon Spice": "肉桂香料", "Peppermint Mocha": "薄荷摩卡",
    "Pumpkin Harvest": "南瓜丰收", "Maple Pecan": "枫糖山核桃", "Coconut Breeze": "椰风轻拂",
    "Alpine Frost": "高山霜冻", "Desert Bloom": "沙漠之花", "Harbor Lights": "港湾灯火",
    "Golden Gate Roast": "金门焙", "Emerald City": "翡翠城", "Cascade Dawn": "瀑布黎明",
    "Redwood Reserve": "红木珍藏", "Sierra High": "山脊高地", "Coastal Mist": "海岸薄雾",
    "Valley Gold": "谷地黄金", "Autumn Ember": "秋日余烬", "Winter Warmth": "冬日暖阳",
    "Spring Bloom": "春日绽放", "Summer Solstice": "夏至", "Autumn Leaves": "秋叶",
    "Winter Spice": "冬香", "Velvet Evening": "丝绒之夜", "Copper Kettle": "铜壶",
    "Silver Skillet": "银锅", "Bronze Brew": "青铜焙", "Ivory Cream": "象牙奶油",
    "Jade Leaf": "翡翠叶", "Amber Glow": "琥珀光", "Onyx Dark": "缟玛瑙深焙",
    "Pearl White": "珍珠白", "Coral Reef": "珊瑚礁", "Sapphire Sky": "蓝宝石天空",
    "Titanium Roast": "钛金属焙",
}
_LOC_CN = {"San Francisco": "旧金山", "Portland": "波特兰", "Seattle": "西雅图",
           "Los Angeles": "洛杉矶", "Chicago": "芝加哥"}


def brand_disp(en) -> str:
    en = str(en)
    cn = _BRAND_CN.get(en)
    return f"{cn}（{en}）" if cn else en


def loc_disp(en) -> str:
    en = str(en)
    cn = _LOC_CN.get(en)
    return f"{cn}（{en}）" if cn else en
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


def render_result(payload: dict):
    r = payload["r"]
    st.markdown(f"<p class='muted'>结果时间 {payload['at']} · 问句：{html.escape(payload['q'][:60])}</p>",
                unsafe_allow_html=True)
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
    elif "库存记录" in r["text"] and "无" in r["text"] and dj is None:
        st.markdown(verdict_card(True, "Agent 如实回答：该 SKU×仓库无库存记录（未作决策）",
                                 "无记录 ≠ 库存充足——正确行为是不出单、也不说充足"), unsafe_allow_html=True)
    else:
        st.markdown(verdict_card(False, "未通过：没有合格的决策单，且末行不是 NO_REORDER 纯文本",
                                 "Agent 回复预览：" + html.escape(r["text"][:150]) +
                                 "…（常见原因：①问句缺周期被反问 ②偶发技能注入抖动——重试一次）"),
                    unsafe_allow_html=True)
    a = payload.get("audit")
    if a:
        st.markdown("**审计智能体（auditor）独立复算判定**")
        st.markdown(f"<div class='ansbox'>{html.escape(a['text'])}</div>", unsafe_allow_html=True)
        st.markdown(f"<p class='muted'>auditor 工具调用 {a['tools'].get('calls')} 次 / "
                    f"败 {a['tools'].get('failures')} · 会话 {a['sid']}</p>", unsafe_allow_html=True)
    elif payload.get("audit_pending"):
        st.info("决策已完成；审计未完成（可能被页面操作中断）——重新提交可补全。")

    if a:
        render_slip(payload)

def render_slip(payload: dict):
    r = payload["r"]
    dj = last_json_block(r["text"])
    a = payload.get("audit")
    # 决策单：核算+审计通过后可下载的正式单据（可签字流转）
    v = verify_decision(dj) if dj and dj.get("decision") == "REORDER" else {"verdict": "N/A", "checks": []}
    audit_m = re.search(r'"audit"\s*:\s*"(PASS|FAIL)"', a["text"]) if a else None
    slip_ok = (v["verdict"] == "PASS") and (audit_m.group(1) == "PASS" if audit_m else False)
    if dj:
        lines = [f"补货决策单 · {payload['at']}",
                 "=" * 36,
                 f"品类：{dj.get('sku')} @ {dj.get('location')} · 周期 {dj.get('weeks')} 周",
                 f"决策：{dj.get('decision')} · 订量 {dj.get('order_qty')}",
                 f"供应商：{dj.get('supplier')}（单价 {dj.get('unit_cost')} + 运费 {dj.get('shipping_cost')}）",
                 f"总成本：{dj.get('total_cost')}",
                 f"理由：{dj.get('rationale')}",
                 "-" * 36,
                 f"独立核算（零 LLM 工具复算）：{v['verdict']}",
                 *[f"  {'✅' if ok else '❌'} {n} {d}" for n, ok, d in v["checks"] if isinstance(n, str)],
                 f"审计智能体判定：{audit_m.group(1) if audit_m else '未完成'}（独立会话复算）",
                 "-" * 36,
                 f"决策会话：{r['sid']} · 模型 {r['provider']}/{r['model']} · {r['tools'].get('calls')} 次工具调用",
                 f"审计会话：{a['sid'] if a else '-'}",
                 "状态：" + ("✅ 双重验证通过，可进入采购审批" if slip_ok else "⚠️ 验证未全部通过，请勿直接执行"),
                 ]
        st.download_button("📄 下载决策单（含核算与审计）" + ("✅" if slip_ok else "⚠️"),
                           "\n".join(lines).encode("utf-8"),
                           file_name=f"决策单-{dj.get('sku')}-{payload['at'].replace(':','')}.txt",
                           key=f"slip-{payload['r']['sid']}-{id(payload)}")
    st.markdown("<p class='muted'>说明：独立核算=面板内确定性工具复算（零 LLM）；审计=第二个真实 LLM 智能体独立调工具复算。</p>",
                unsafe_allow_html=True)


def decide_and_audit(qq: str, with_audit: bool = True) -> dict:
    """决策智能体 → （审计智能体）→ 完整决策包。就地出单/实时页共用。"""
    r = run_agent(qq)
    payload = {"q": qq, "r": r, "at": time.strftime("%T"),
                "audit": None, "audit_pending": bool(with_audit)}
    dj = last_json_block(r["text"])
    if with_audit and dj and dj.get("decision") == "REORDER":
        msg = (f"审计以下补货决策单。原问句：{qq}\n\n待审决策单：\n{json.dumps(dj, ensure_ascii=False)}\n\n"
               f"来源会话：{r['sid']}。按 supply-chain-audit SOP 独立复算并输出审计判定 JSON。")
        payload["audit"] = run_agent(msg, agent="auditor")
        payload["audit_pending"] = False
    return payload


tab_scan, tab_tool, tab_live, tab_up = st.tabs(
    ["📋 每日巡检（产品形态）", "🧮 工具证据（零 LLM）", "🤖 实时 Agent（默认路由）", "📤 上传我的数据"])

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import custom_data as cd  # noqa: E402

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
                "对例外再到「实时 Agent」页开口追问。点一次后等 2-3 秒，不用连点。</p>",
                unsafe_allow_html=True)
    top, btn = st.columns([3, 1])
    if btn.button("🔄 生成巡检报告", type="primary"):
        with st.spinner("扫描中（约 2-3 秒，请勿连点）…"):
            p = subprocess.Popen(
                [__import__("sys").executable, os.path.join(BASE, "scripts", "daily_scan.py")],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                p.wait(timeout=90)
            except subprocess.TimeoutExpired:
                p.kill()
                st.error("扫描超时（90s）——请截图告诉我")
            if p.returncode == 0:
                st.session_state["scan_ok_at"] = time.strftime("%T")
                st.rerun()
            else:
                st.error(f"扫描失败（exit={p.returncode}）：{p.stderr.read()[-300:]}")
    if "scan_ok_at" in st.session_state:
        st.success(f"✅ 报告已生成 {st.session_state['scan_ok_at']}")
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
        st.markdown("##### ⬇️ 报告文件（拿得走的那种）")
        _csv = pd.DataFrame(rep["shortages"]).to_csv(index=False).encode("utf-8-sig")
        _json = json.dumps(rep, ensure_ascii=False, indent=1).encode("utf-8")
        _ts = rep["generated_at"].replace(":", "").replace(" ", "-")
        dd1, dd2 = st.columns(2)
        dd1.download_button("📄 短缺排行 CSV", _csv, file_name=f"巡检短缺排行-{_ts}.csv", mime="text/csv")
        dd2.download_button("📄 完整报告 JSON", _json, file_name=f"巡检报告-{_ts}.json", mime="application/json")
        st.markdown("##### 短缺排行（按建议采购金额排序，⭐=运费翻转：单价最低者并非总单价最低）")
        sdf = pd.DataFrame(rep["shortages"]).rename(columns=SCAN_CN)
        if "品牌" in sdf: sdf["品牌"] = sdf["品牌"].map(brand_disp)
        if "仓库" in sdf: sdf["仓库"] = sdf["仓库"].map(loc_disp)
        if not sdf.empty:
            sdf["翻转"] = sdf["翻转"].map({True: "⭐", False: ""})
            st.dataframe(sdf, width="stretch")
            with st.expander(f"库存充足 {rep['ample_count']} 个（NO_REORDER，不展开建议）"):
                st.dataframe(pd.DataFrame(rep["ample"]).rename(columns=AMPLE_CN), width="stretch")
            st.markdown("##### 🔍 下钻单个品类：缺口 + 供货建议（可调决策周期）")
            opts = {f"{s['sku']} {brand_disp(s['brand'])} @ {loc_disp(s['location'])} · 缺口 {-s['gap']}" + (" · ⭐翻转" if s["flip"] else ""): s
                    for s in rep["shortages"]}
            pick = st.selectbox("选择品类", list(opts), key="drill_pick")
            if pick:
                s = opts[pick]
                dw = st.slider("下钻决策周期（本卡片与问句都按它，最长 1 年）", 1, 52, rep["weeks"], key="drill_w")
                g = tools.stock_demand_difference(int(s["sku"]), s["location"], dw)
                dgap = g["gap_stock_minus_demand"]
                board = supplier_board(int(s["sku"]), s["location"])
                if dgap < 0 and not board.empty:
                    best = board.iloc[0]
                    st.markdown(
                        f"<div class='card'><h4>{html.escape(str(s['sku']))} {html.escape(brand_disp(s['brand']))} @ {html.escape(loc_disp(s['location']))}"
                        + (" <span class='bad'>⭐ 运费翻转</span>" if s["flip"] else "") + "</h4>"
                        f"<div class='bad'>缺 {-dgap} 件（库存 {g['current_stock']} / {dw} 周需求 {g['forecast_demand']}）</div>"
                        f"<div class='muted' style='margin-top:.4rem'>建议：向 <b>{html.escape(str(best['supplier']))}</b>"
                        f"（{html.escape(str(best['location']))}）下单 <b>{-dgap}</b> 件 · "
                        f"单价 ${best['unit_cost']:.2f} + 运费 ${best['shipping_to_dest']:.2f} = "
                        f"<b>${best['total_unit_cost']:.2f}/件</b> · 总成本 "
                        f"<b>${-dgap * best['total_unit_cost']:,.2f}</b></div>"
                        "<div class='muted'>候选比价见下方「工具证据」页同款表格；每一步数字可核验</div></div>",
                        unsafe_allow_html=True)
                elif dgap >= 0:
                    st.markdown(verdict_card(True, "该周期下库存充足",
                                             f"余量 +{dgap} 件 · 无需补货（NO_REORDER:{dgap}）"), unsafe_allow_html=True)
                if st.button("🤖 让 Agent 出正式决策单（就地出单，约 60-120 秒，勿点其它）"):
                    qq = (f"{s['location']} 的 {s['brand']} 未来 {dw} 周库存够不够？"
                          f"要补的话找哪家供应商、总价多少？")
                    ph = st.empty(); ph.info(f"运行中：{qq}")
                    try:
                        payload = decide_and_audit(qq, with_audit=True)
                        st.session_state["last"] = payload
                        ph.empty()
                        st.success(f"✅ 决策完成（{dw} 周问句）——结果与可下载决策单如下；「实时 Agent」页同步留档")
                        render_result(payload)
                        st.session_state["skip_restore_once"] = True  # 本轮已渲染，实时页不再重复
                    except Exception as e:
                        ph.empty()
                        st.error(f"未出决策：{type(e).__name__}: {e}"[:400])


# ---------------------------------------------------------------- 工具证据模式
with tab_tool:
    st.caption(f"数据全貌：48 SKU · 64 条库存记录 · 每仓只经营其服务的品类（该仓无某 SKU 属业务事实，如实报告）")
    view = st.radio("查看方式", ["按 SKU 看（单品类决策）", "按仓库看（该仓全品类清单）"],
                    horizontal=True, label_visibility="collapsed")
    left, right = st.columns([1, 2])
    with left:
        if view.startswith("按仓库"):
            st.markdown("##### 仓库全貌")
            wloc = st.selectbox("仓库", sorted(_inv.location.unique()), format_func=loc_disp)
            weeks = st.slider("决策周期（周，最长 1 年）", 1, 52, 12)
            rows = _inv[_inv.location == wloc].copy()
            gaps = []
            for _, rr in rows.iterrows():
                g = tools.stock_demand_difference(int(rr["sku"]), wloc, weeks)
                gaps.append({"SKU": int(rr["sku"]), "品牌": brand_disp(_products.get(int(rr["sku"]), "?")),
                             "库存": int(rr["quantity"]), f"{weeks}周需求": g["forecast_demand"],
                             "缺口": g["gap_stock_minus_demand"]})
            gdf = pd.DataFrame(gaps)
            n_short = int((gdf["缺口"] < 0).sum())
            st.markdown(f"<div class='card'><h4>{wloc} · {len(gdf)} 个 SKU 有记录"
                        f"<span class='bad'>（{n_short} 短缺）</span> / "
                        f"<span class='good'>{len(gdf)-n_short} 充足</span> · 周期 {weeks} 周</h4></div>",
                        unsafe_allow_html=True)
            st.dataframe(gdf, width="stretch")
            st.markdown("<p class='muted'>上表=该仓真实全部记录；短缺项可切「按 SKU 看」或巡检页下钻</p>",
                        unsafe_allow_html=True)
            sku = None
        else:
            st.markdown("##### 决策视图")
            sku = st.selectbox("SKU", sorted(_products),
                               format_func=lambda s: f"{s} {brand_disp(_products[s])}")
            locs_of_sku = sorted(_inv[_inv.sku == sku].location.unique())
            st.caption(f"该 SKU 在 {len(locs_of_sku)} 个仓有记录：{('、'.join(locs_of_sku))}")
            loc = st.selectbox("仓库（仅列该 SKU 有记录的仓）", locs_of_sku, format_func=loc_disp)
            weeks = st.slider("决策周期（周，最长 1 年）", 1, 52, 12)

        if sku is not None and not has_inventory(sku, loc):
            st.markdown(
                f"<div class='card'><h4><span class='warn'>⚠️ 无库存记录</span></h4>"
                f"<div class='muted'>{loc} 仓无 SKU {sku} 的库存记录（与所选周期无关：任何周期都无此记录）。"
                f"工具对无记录按 0 处理，本面板不把未知库存当作真实零库存给补货结论——请换有效组合。</div></div>",
                unsafe_allow_html=True)
        elif sku is not None:
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
      if sku is not None:
        st.markdown(f"##### 未来 {weeks} 周需求预测 · {sku} @ {loc}")
        fc = tools.get_forecast(str(sku), loc).head(weeks)
        st.line_chart(fc["demand"], height=280)
        st.markdown("<p class='muted'>确定性合成预测（crc32 稳定化，不随仓库变化）——与 skill 工具层同源 · "
                    f"图示 {weeks} 个数据点 = 所选周期</p>", unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 库存全量（只读原始数据）")
        _inv_disp = _inv.copy()
        _inv_disp["brand"] = _inv_disp["brand"].map(brand_disp)
        _inv_disp["location"] = _inv_disp["location"].map(loc_disp)
        st.dataframe(_inv_disp.rename(columns=_INV_CN), width="stretch")
    with c2:
        if sku is not None:
            st.markdown(f"##### 供应商比价 · SKU {sku}（{brand_disp(_products[sku])}）→ {loc_disp(loc)}（按总单价）")
            board = supplier_board(sku, loc)
            st.dataframe(board.rename(columns=_SUP_CN) if not board.empty else "该 SKU 无供应商记录", width="stretch")
        else:
            st.markdown("##### 供应商比价 · 切到「按 SKU 看」后显示")

# ------------------------------------------------------------ 实时 Agent 模式
Q_DEFAULT = "San Francisco 仓库 SKU 13001 未来 12 周够卖吗？需要补货吗？"
with tab_live:
    st.markdown("##### 自然问句 → Agent 决策")
    st.markdown("<p class='muted'>每问独立会话 · 单次提交 · 本地等待 90s 超时不自动重试 · "
                "独立核算=确定性工具复算（零 LLM）</p>", unsafe_allow_html=True)

    # 每次渲染先清残留的"运行中"标志（防止历史中断把按钮永久锁死）
    st.session_state.pop("running", None)
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

    if st.button("▶ 提交（单次，约 40-90 秒，点一次即可）", type="primary"):
        st.session_state["running"] = True
        ph = st.empty()
        ph.info("运行中…（独立会话，40-90 秒；期间点击其它控件会中断界面刷新，但计算不会丢）")
        try:
            payload = decide_and_audit(q, with_audit)
            st.session_state["last"] = payload
            ph.empty()
            render_result(payload)
        except subprocess.TimeoutExpired:
            ph.empty()
            st.error(f"未出决策：本地等待超过 {AGENT_TIMEOUT_S}s（本地等待已中止、不自动重试；网关侧任务状态未知）")
        except Exception as e:
            ph.empty()
            st.error(f"未出决策：{type(e).__name__}: {e}"[:500] + "（不自动重试，可手动重新提交）")
        finally:
            st.session_state["running"] = False
    elif "last" in st.session_state and not st.session_state.pop("skip_restore_once", False):
        st.markdown("##### 上一次结果（自动恢复显示）")
        render_result(st.session_state["last"])

# ---------------------------------------------------------- 上传我的数据

with tab_up:
    st.markdown("##### 上传你的库存表 → AI 读懂列 → 出你自己的补货单")
    st.markdown("<p class='muted'>支持 CSV（utf-8/gbk）与 Excel。AI 只<b>建议</b>列映射，<b>你确认</b>后才生效；"
                "数据只存在本机面板会话，不覆盖内置演示数据集。<b>边界如实告知</b>：Agent 对话深挖仍绑定内置数据集，"
                "上传数据的巡检与建议单由工具直算层产出。</p>", unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    if s1.button("📋 载入紧固件厂样例（无需上传文件）"):
        try:
            st.session_state["up_df"] = cd.parse_upload(
                open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_factory.csv"), "rb").read(),
                "sample_factory.csv")
            st.session_state.pop("mapping_sug", None)
            st.session_state.pop("custom_canon", None)
            st.session_state.pop("custom_report", None)
            st.rerun()
        except Exception as e:
            st.error(f"样例载入失败：{e}")
    up = st.file_uploader("选择文件", type=["csv", "xlsx", "xls"])
    if up is not None:
        try:
            df = cd.parse_upload(up.getvalue(), up.name)
        except Exception as e:
            st.error(f"解析失败：{e}")
            df = None
        if df is not None:
            st.markdown(f"<p class='muted'>已读取 {up.name}：{df.shape[0]} 行 × {df.shape[1]} 列</p>",
                        unsafe_allow_html=True)
            st.dataframe(df.head(5), width="stretch")
            st.session_state["up_df"] = df

    if "up_df" in st.session_state:
        df = st.session_state["up_df"]
        cA, cB = st.columns([1, 1])
        if cA.button("🤖 AI 映射建议（约 20 秒）"):
            ph = st.empty(); ph.info("AI 正在读表头和样例…")
            try:
                r = run_agent(cd.build_mapping_prompt(df))
                sug = cd.parse_mapping_reply(r["text"])
                ph.empty()
                if sug:
                    st.session_state["mapping_sug"] = sug
                    unmapped = sug.get("unmapped_columns") or []
                    st.success(f"AI 映射建议已生成（未识别列：{unmapped if unmapped else '无'}）——请在下方确认或修改")
                else:
                    st.warning("AI 未给出可解析的映射建议——请在下方手动选择列")
            except Exception as e:
                ph.empty()
                st.warning(f"AI 映射失败（{type(e).__name__}）——请手动选择列，不影响使用")

        st.markdown("###### 列映射确认（AI 建议已预选，可修改）")
        sug = st.session_state.get("mapping_sug", {}).get("mapping", {})
        columns = ["（不提供）"] + [str(c) for c in df.columns]

        def sel(field, key):
            want = (sug.get(field) or {}).get("column")
            default = columns.index(str(want)) if want and str(want) in columns else 0
            choice = st.selectbox(f"{cd.MAPPING_FIELDS[field]}", columns, index=default, key=key)
            return None if choice == "（不提供）" else choice

        m1, m2 = st.columns(2)
        with m1:
            colmap = {"sku": sel("sku", "m_sku"), "location": sel("location", "m_loc")}
            colmap["quantity"] = sel("quantity", "m_qty")
            colmap["weekly_demand"] = sel("weekly_demand", "m_dem")
        with m2:
            colmap["product_name"] = sel("product_name", "m_name")
            colmap["supplier"] = sel("supplier", "m_sup")
            colmap["supplier_city"] = sel("supplier_city", "m_city")
            colmap["unit_cost"] = sel("unit_cost", "m_cost")
        default_dem = st.number_input("全局周均需求（未映射需求列时使用，估算值）", 0.0, 1e7, 100.0, 10.0)

        if st.button("✅ 确认映射并校验", type="primary"):
            canon, errors, notes = cd.validate_and_convert(df, colmap, default_dem)
            if errors:
                for e in errors:
                    st.error(f"校验未通过：{e}")
            else:
                st.session_state["custom_canon"] = canon
                for n in notes:
                    st.markdown(f"<p class='muted'>⚠️ {html.escape(n)}</p>", unsafe_allow_html=True)
                st.success(f"✅ 校验通过：{len(canon)} 个 SKU×仓库组合就绪，可在下方巡检")

        if "custom_canon" in st.session_state:
            w = st.slider("巡检周期（周，最长 1 年）", 1, 52, 12, key="up_weeks")
            if st.button("🚀 在我的数据上巡检", type="primary"):
                ph = st.empty(); ph.info("巡检中…（工具直算，秒级）")
                rep = cd.custom_scan(st.session_state["custom_canon"], w, tools.get_shipping_cost)
                st.session_state["custom_report"] = rep
                ph.empty()
                try:
                    os.makedirs(os.path.join(BASE, "panel", "uploads"), exist_ok=True)
                    json.dump(rep, open(os.path.join(BASE, "panel", "uploads", "latest-custom.json"), "w"),
                              ensure_ascii=False, indent=1)
                except Exception:
                    pass
            rep = st.session_state.get("custom_report")
            if rep:
                st.success(f"✅ 你的数据巡检完成 {rep['generated_at']} · {rep['combos']} 组合 · "
                           f"短缺 {rep['shortage_count']} / 充足 {rep['ample_count']} / "
                           f"运费翻转 {rep['flip_count']} · 建议采购总额 ${rep['total_reorder_cost']:,.0f}")
                sdf = pd.DataFrame(rep["shortages"]).rename(columns=SCAN_CN)
                if "品牌" in sdf: sdf["品牌"] = sdf["品牌"].map(brand_disp)
                if "仓库" in sdf: sdf["仓库"] = sdf["仓库"].map(loc_disp)
                if not sdf.empty:
                    if "翻转" in sdf:
                        sdf["翻转"] = sdf["翻转"].map({True: "⭐", False: ""})
                    if "未含运费" not in sdf and "no_shipping" in sdf:
                        sdf["未含运费"] = sdf["no_shipping"].map({True: "⚠️", False: ""})
                    st.dataframe(sdf, width="stretch")
                    with st.expander(f"库存充足 {rep['ample_count']} 个（NO_REORDER）"):
                        st.dataframe(pd.DataFrame(rep["ample"]).rename(columns=AMPLE_CN), width="stretch")
                else:
                    st.info("你的数据上没有短缺组合——全部充足。")
                _c = pd.DataFrame(rep["shortages"]).to_csv(index=False).encode("utf-8-sig")
                st.download_button("📄 下载你的巡检结果 CSV", _c,
                                   file_name=f"我的数据巡检-{rep['generated_at'].replace(':','')}.csv",
                                   mime="text/csv")
        if st.button("🗑 清除上传数据"):
            for k in ("up_df", "mapping_sug", "custom_canon", "custom_report"):
                st.session_state.pop(k, None)
            st.rerun()
