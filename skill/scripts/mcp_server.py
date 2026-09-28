#!/usr/bin/env python3
"""供应链控制塔 · MCP 服务器（Model Context Protocol，stdio，零依赖手写实现）。

把控制塔工具层与双智能体决策流水线暴露为标准 MCP 接口，任意外部 Agent
（Claude/其它 MCP 客户端/OpenClaw 等）可挂载调用：

  gap(sku, location, weeks)          库存-需求缺口（决策原语）
  inventory(location)                库存查询
  suppliers(sku)                     供应商比价（含至指定仓运费需另调 shipping）
  shipping(source, destination)      单件运费
  forecast(sku, weeks)               需求预测
  scan_portfolio(weeks)              全组合巡检（产品形态，工具直算零 LLM）
  reorder_decision(question)         旗舰工具：问句 → 决策智能体 → 确定性核算
                                     → 审计智能体 → 返回可追责决策包

用法（MCP 客户端配置示例）：
  {"mcpServers": {"supply-chain-tower": {
      "command": "python3",
      "args": ["/home/sparker/.openclaw/workspace/skills/supply-chain-control-tower/scripts/mcp_server.py"]}}}

协议：JSON-RPC 2.0，stdio 按行分帧；initialize/tools list/tools call/ping。
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import uuid

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENCLAW = os.path.expanduser("~/node26/bin/openclaw")
AGENT_TIMEOUT = 120

_spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tools)

_spec2 = importlib.util.spec_from_file_location("scan", os.path.join(BASE, "scripts", "daily_scan.py"))
scan = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(scan)


def _board(sku: int):
    import pandas as pd
    sup = pd.read_csv(os.path.join(BASE, "data", "suppliers.csv"))
    rows = sup[sup.sku == int(sku)].copy()
    if rows.empty:
        return rows, None
    return rows, None


def _best_supplier(sku: int, dest: str):
    import pandas as pd
    sup = pd.read_csv(os.path.join(BASE, "data", "suppliers.csv"))
    rows = sup[sup.sku == int(sku)].copy()
    if rows.empty:
        return None
    rows["ship"] = [tools.get_shipping_cost(c, dest) for c in rows["location"]]
    rows["total"] = rows["unit_cost"] + rows["ship"]
    return rows.sort_values("total").iloc[0].to_dict()


def _run_agent(question: str, agent: str = None) -> dict:
    sid = f"pi-dgx-mcp-{uuid.uuid4().hex[:8]}"
    cmd = [OPENCLAW, "agent"] + (["--agent", agent] if agent else []) + \
        ["--session-id", sid, "--message", question, "--json"]
    env = dict(os.environ, PATH=os.path.expanduser("~/node26/bin") + ":" + os.environ.get("PATH", ""))
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=AGENT_TIMEOUT, env=env)
    out = (p.stdout or "").strip()
    if not out:
        raise RuntimeError(f"openclaw 无输出（exit={p.returncode}）：{(p.stderr or '')[-200:]}")
    d = json.loads(out[out.find("{"):out.rfind("}") + 1]) if not out.startswith("{") else json.loads(out)
    meta = d["result"]["meta"]
    return {"sid": sid, "text": meta.get("finalAssistantVisibleText") or "",
            "provider": meta["agentMeta"].get("provider"), "model": meta["agentMeta"].get("model"),
            "duration_ms": meta["agentMeta"].get("durationMs"),
            "tools": meta.get("toolSummary", {})}


def _last_json(text: str):
    blocks = [b for b in text.split("```") if b.strip().startswith("json")]
    for b in reversed(blocks):
        try:
            return json.loads(b.strip()[4:].strip())
        except Exception:
            continue
    return None


def _verify(dj: dict) -> dict:
    """确定性核算（零 LLM），与面板同判据。"""
    try:
        sku, loc, weeks = int(dj.get("sku")), dj.get("location"), int(dj.get("weeks"))
    except (TypeError, ValueError):
        return {"verdict": "FAIL", "checks": ["sku/location/weeks 不完整"]}
    g = tools.stock_demand_difference(sku, loc, weeks)
    rop_gap = g.get("rop_gap")
    ss = g.get("safety_stock", 0) or 0
    want_qty = round(rop_gap + ss, 1) if (rop_gap is not None and rop_gap > 0) else 0
    best = _best_supplier(sku, loc)
    checks = []
    if best is None:
        return {"verdict": "FAIL", "checks": [f"SKU {sku} 无供应商"]}
    f = lambda x: float(x) if x is not None else 0.0  # noqa: E731
    checks.append(f"订量(ROP): {dj.get('order_qty')} vs 工具 {want_qty} -> "
                  f"{'OK' if f(dj.get('order_qty')) == want_qty else 'MISMATCH'}")
    checks.append(f"供应商: {dj.get('supplier')} vs 工具 {best['supplier']} -> "
                  f"{'OK' if dj.get('supplier') == best['supplier'] else 'MISMATCH'}")
    want = round(f(dj.get("order_qty")) * (f(dj.get("unit_cost")) + f(dj.get("shipping_cost"))), 2)
    checks.append(f"总价: {dj.get('total_cost')} vs 实算 {want} -> "
                  f"{'OK' if abs(f(dj.get('total_cost')) - want) <= 0.01 else 'MISMATCH'}")
    ok = all("MISMATCH" not in c for c in checks)
    return {"verdict": "PASS" if ok else "FAIL", "checks": checks}


def tool_reorder_decision(question: str) -> dict:
    """问句 → 决策智能体 → 确定性核算 → 审计智能体 → 决策包。"""
    r = _run_agent(question)
    dj = _last_json(r["text"])
    package = {"question": question, "decision_agent": {
        "session": r["sid"], "model": f"{r['provider']}/{r['model']}",
        "duration_ms": r["duration_ms"], "tool_summary": r["tools"],
        "final_text": r["text"], "decision_json": dj}}
    if dj and dj.get("decision") == "REORDER":
        v = _verify(dj)
        package["independent_verification"] = v  # 零 LLM 工具复算
        a = _run_agent(
            f"审计以下补货决策单。原问句：{question}\n\n待审决策单：\n{json.dumps(dj, ensure_ascii=False)}\n\n"
            f"来源会话：{r['sid']}。按 supply-chain-audit SOP 独立复算并输出审计判定 JSON。",
            agent="auditor")
        m = re.search(r'"audit"\s*:\s*"(PASS|FAIL)"', a["text"])
        package["audit_agent"] = {"session": a["sid"], "model": f"{a['provider']}/{a['model']}",
                                  "tool_summary": a["tools"], "final_text": a["text"],
                                  "verdict": m.group(1) if m else "UNPARSED"}
        if package["audit_agent"]["verdict"] == "UNPARSED":
            # 确定性审计兜底：审计智能体输出不可解析时，以零 LLM 复算为准
            package["audit_agent"]["verdict"] = v["verdict"]
            package["audit_agent"]["fallback"] = "审计智能体输出未解析，按确定性核算判定（零 LLM 对账）"
        package["overall"] = "PASS" if (v["verdict"] == "PASS" and package["audit_agent"]["verdict"] == "PASS") else "FAIL"
    elif dj is None and re.search(r"^NO_REORDER:\d+$", r["text"].strip().splitlines()[-1]):
        package["independent_verification"] = {"verdict": "PASS", "checks": ["负例末行合规（纯文本 NO_REORDER）"]}
        package["overall"] = "PASS"
    elif dj is None and "库存记录" in r["text"] and "无" in r["text"]:
        package["independent_verification"] = {"verdict": "PASS", "checks": ["无库存记录，Agent 如实拒答（未编数未出单）"]}
        package["overall"] = "NO_RECORD_TRUTHFUL"
    else:
        package["overall"] = "FAIL"
    return package


TOOLS = [
    {"name": "gap", "description": "ROP 驱动决策：返回 rop_gap(正=低于ROP需补货)、reorder_point、safety_stock",
     "inputSchema": {"type": "object", "properties": {
         "sku": {"type": "integer"}, "location": {"type": "string"}, "weeks": {"type": "integer"}},
         "required": ["sku", "location", "weeks"]}},
    {"name": "inventory", "description": "库存查询（可按仓库过滤）",
     "inputSchema": {"type": "object", "properties": {"location": {"type": "string"}}}},
    {"name": "suppliers", "description": "SKU 的全部候选供应商（含单价与发货地）",
     "inputSchema": {"type": "object", "properties": {"sku": {"type": "integer"}}, "required": ["sku"]}},
    {"name": "shipping", "description": "两城市间单件运费",
     "inputSchema": {"type": "object", "properties": {
         "source": {"type": "string"}, "destination": {"type": "string"}},
         "required": ["source", "destination"]}},
    {"name": "forecast", "description": "未来 N 周需求预测（确定性合成）",
     "inputSchema": {"type": "object", "properties": {
         "sku": {"type": "integer"}, "weeks": {"type": "integer"}}, "required": ["sku"]}},
    {"name": "scan_portfolio", "description": "全组合巡检（产品形态）：短缺排行/运费翻转/建议采购总额，工具直算零 LLM",
     "inputSchema": {"type": "object", "properties": {"weeks": {"type": "integer", "default": 12}}}},
    {"name": "reorder_decision", "description":
        "旗舰：自然语言问句 → 决策智能体(八字段决策单) → 确定性核算(零LLM) → 审计智能体独立复算 → 可追责决策包。"
        "约 60-120 秒。",
     "inputSchema": {"type": "object", "properties": {"question": {"type": "string"}},
                     "required": ["question"]}},
]


def call_tool(name: str, args: dict):
    if name == "gap":
        return tools.stock_demand_difference(args["sku"], args["location"], args["weeks"])
    if name == "inventory":
        import pandas as pd
        df = pd.read_csv(os.path.join(BASE, "data", "inventory.csv"))
        if args.get("location"):
            df = df[df.location == args["location"]]
        return json.loads(df.to_json(orient="records", force_ascii=False))
    if name == "suppliers":
        import pandas as pd
        df = pd.read_csv(os.path.join(BASE, "data", "suppliers.csv"))
        return json.loads(df[df.sku == int(args["sku"])].to_json(orient="records", force_ascii=False))
    if name == "shipping":
        return {"source": args["source"], "destination": args["destination"],
                "unit_shipping_cost": tools.get_shipping_cost(args["source"], args["destination"])}
    if name == "forecast":
        df = tools.get_forecast(str(args["sku"]), "").head(int(args.get("weeks", 12)))
        return json.loads(df.reset_index().to_json(orient="records", force_ascii=False, date_format="iso"))
    if name == "scan_portfolio":
        return scan.scan(int(args.get("weeks", 12)))
    if name == "reorder_decision":
        return tool_reorder_decision(args["question"])
    raise ValueError(f"unknown tool: {name}")


def handle(req: dict) -> dict | None:
    m, rid = req.get("method"), req.get("id")
    if m == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": req.get("params", {}).get("protocolVersion", "2025-03-26"),
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "supply-chain-control-tower", "version": "1.0.0"}}}
    if m == "notifications/initialized":
        return None
    if m == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if m == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if m == "tools/call":
        try:
            result = call_tool(req["params"]["name"], req["params"].get("arguments", {}))
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "isError": True,
                "content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}]}}
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {m}"}}
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            resp = handle(json.loads(line))
        except Exception as e:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False, default=str) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
