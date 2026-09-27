#!/usr/bin/env python3
"""供应链控制塔 · 前端对接 HTTP API（新前端 A 线的契约实现）。

零依赖（stdlib），端口 8765。所有能力来自既有冻结后端：tools.py 直算、
daily_scan 巡检、custom_data 上传映射、openclaw 双智能体决策流水线。
红线：只读业务数据、无凭据下发、固定白名单端点、错误一律 JSON。

启动：nohup python3 api_server.py >~/api.log 2>&1 &
访问：本机 http://127.0.0.1:8765/api/health ；外部经 SSH 隧道
      ssh -p <SSH端口> -N -L 8765:127.0.0.1:8765 sparker@<你的DGX-SSH地址>
"""
import base64
import importlib.util
import json
import os
import re
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.expanduser("~/.openclaw/workspace/skills/supply-chain-control-tower")
OPENCLAW = os.path.expanduser("~/node26/bin/openclaw")
AGENT_TIMEOUT = 150

_spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(tools)
_spec2 = importlib.util.spec_from_file_location("scan", os.path.join(BASE, "scripts", "daily_scan.py"))
scan = importlib.util.module_from_spec(_spec2); _spec2.loader.exec_module(scan)
sys_path_hack = __import__("sys").path
sys_path_hack.insert(0, os.path.join(BASE, "panel"))
import custom_data as cd  # noqa: E402

import pandas as pd  # noqa: E402

_products = {p["sku"]: p["brand"] for p in json.load(open(os.path.join(BASE, "data", "products.json")))["products"]}
_inv = pd.read_csv(os.path.join(BASE, "data", "inventory.csv"))
_sup = pd.read_csv(os.path.join(BASE, "data", "suppliers.csv"))
BRAND_CN = cd  # 占位避免误用
_CN = {"House Blend": "综合咖啡", "Italian Roast": "意式浓缩", "Colombian Coffee": "哥伦比亚"}


def bdisp(en):
    return f"{_CN.get(str(en))}（{en}）" if _CN.get(str(en)) else str(en)


JOBS = {}  # job_id -> {"status":..., "result":..., "error":...}


def run_agent(question: str, agent=None) -> dict:
    sid = f"pi-dgx-api-{uuid.uuid4().hex[:8]}"
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
            "duration_ms": meta["agentMeta"].get("durationMs"), "tools": meta.get("toolSummary", {})}


def last_json(text):
    for b in [b for b in text.split("```") if b.strip().startswith("json")][::-1]:
        try:
            return json.loads(b.strip()[4:].strip())
        except Exception:
            pass
    return None


def supplier_board(sku, dest):
    rows = _sup[_sup.sku == int(sku)].copy()
    if rows.empty:
        return []
    rows["ship"] = [tools.get_shipping_cost(c, dest) for c in rows["location"]]
    rows["total"] = (rows["unit_cost"] + rows["ship"]).round(2)
    rows = rows.sort_values("total")
    return [dict(supplier=r["supplier"], location=r["location"], unit_cost=float(r["unit_cost"]),
                 shipping=float(r["ship"]), total_unit=float(r["total"])) for _, r in rows.iterrows()]


def decide_and_audit(question, with_audit=True):
    r = run_agent(question)
    pkg = {"question": question, "decision_agent": {
        "session": r["sid"], "model": f"{r['provider']}/{r['model']}", "duration_ms": r["duration_ms"],
        "tool_summary": r["tools"], "final_text": r["text"], "decision_json": last_json(r["text"])}}
    dj = pkg["decision_agent"]["decision_json"]
    if dj and dj.get("decision") == "REORDER":
        g = tools.stock_demand_difference(int(dj.get("sku") or 0), dj.get("location") or "", int(dj.get("weeks") or 0))
        board = supplier_board(dj.get("sku"), dj.get("location"))
        best = board[0] if board else None
        f = lambda x: float(x) if x is not None else 0.0  # noqa: E731
        checks = []
        ok = best is not None and g.get("record_exists")
        if ok:
            c1 = f(dj.get("order_qty")) == -g["gap_stock_minus_demand"]
            c2 = dj.get("supplier") == best["supplier"]
            want = round(f(dj.get("order_qty")) * (f(dj.get("unit_cost")) + f(dj.get("shipping_cost"))), 2)
            c3 = abs(f(dj.get("total_cost")) - want) <= 0.01
            checks = [f"订量 {dj.get('order_qty')}/{-g['gap_stock_minus_demand']}:" + ("OK" if c1 else "MISMATCH"),
                      f"供应商 {dj.get('supplier')}/{best['supplier']}:" + ("OK" if c2 else "MISMATCH"),
                      f"总价 {dj.get('total_cost')}/{want}:" + ("OK" if c3 else "MISMATCH")]
            ok = c1 and c2 and c3
        pkg["independent_verification"] = {"verdict": "PASS" if ok else "FAIL", "checks": checks}
        if with_audit:
            a = run_agent(
                f"审计以下补货决策单。原问句：{question}\n\n待审决策单：\n{json.dumps(dj, ensure_ascii=False)}\n\n"
                f"来源会话：{r['sid']}。按 supply-chain-audit SOP 独立复算并输出审计判定 JSON。",
                agent="auditor")
            m = re.search(r'"audit"\s*:\s*"(PASS|FAIL)"', a["text"])
            pkg["audit_agent"] = {"session": a["sid"], "model": f"{a['provider']}/{a['model']}",
                                  "tool_summary": a["tools"], "final_text": a["text"],
                                  "verdict": m.group(1) if m else "UNPARSED"}
            pkg["overall"] = "PASS" if (ok and pkg["audit_agent"]["verdict"] == "PASS") else "FAIL"
        else:
            pkg["overall"] = "PASS" if ok else "FAIL"
        pkg["slip_text"] = slip(pkg)
    elif dj is None and re.search(r"^NO_REORDER:\d+$", (r["text"].strip().splitlines() or [""])[-1]):
        pkg["independent_verification"] = {"verdict": "PASS", "checks": ["负例末行合规"]}
        pkg["overall"] = "PASS"
    elif dj is None and "库存记录" in r["text"] and "无" in r["text"]:
        pkg["independent_verification"] = {"verdict": "PASS", "checks": ["无库存记录，如实拒答"]}
        pkg["overall"] = "NO_RECORD_TRUTHFUL"
    else:
        pkg["overall"] = "FAIL"
    return pkg


def slip(pkg):
    dj = pkg["decision_agent"]["decision_json"]
    v = pkg.get("independent_verification", {})
    a = pkg.get("audit_agent", {})
    lines = ["补货决策单 · " + time.strftime("%F %T"), "=" * 36,
             f"品类：{dj.get('sku')} @ {dj.get('location')} · 周期 {dj.get('weeks')} 周",
             f"决策：{dj.get('decision')} · 订量 {dj.get('order_qty')}",
             f"供应商：{dj.get('supplier')}（单价 {dj.get('unit_cost')} + 运费 {dj.get('shipping_cost')}）",
             f"总成本：{dj.get('total_cost')}", f"理由：{dj.get('rationale')}", "-" * 36,
             f"独立核算（零 LLM 工具复算）：{v.get('verdict')}",
             *[f"  · {c}" for c in v.get("checks", [])],
             f"审计智能体判定：{a.get('verdict', '未串审计')}（独立会话复算）", "-" * 36,
             f"决策会话：{pkg['decision_agent']['session']}",
             f"审计会话：{a.get('session', '-')}",
             "状态：" + ("✅ 双重验证通过，可进入采购审批"
                        if pkg.get("overall") == "PASS" else "⚠️ 验证未全部通过，请勿直接执行")]
    return "\n".join(lines)


def job_worker(job_id, question, with_audit):
    try:
        JOBS[job_id] = {"status": "RUNNING", "started_at": time.strftime("%T")}
        JOBS[job_id] = {"status": "SUCCEEDED", "result": decide_and_audit(question, with_audit),
                        "finished_at": time.strftime("%T")}
    except Exception as e:
        JOBS[job_id] = {"status": "FAILED", "error": f"{type(e).__name__}: {e}"[:400]}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg):
        self._send(code, {"error": {"type": "ApiError", "message": msg}})

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p = u.path
        try:
            if p == "/api/health":
                return self._send(200, {"ok": True, "service": "supply-chain-tower-api", "port": 8765,
                                        "model": "stepfun/step-3.7-flash（默认路由）",
                                        "data": {"skus": len(_products), "inventory_rows": len(_inv),
                                                 "supplier_rows": len(_sup)}})
            if p == "/api/products":
                return self._send(200, [
                    {"sku": s, "brand": b, "display": f"{s} {bdisp(b)}",
                     "locations": sorted(_inv[_inv.sku == s].location.unique())} for s, b in sorted(_products.items())])
            if p == "/api/inventory":
                return self._send(200, [
                    {"sku": int(r["sku"]), "brand": r["brand"], "display": bdisp(r["brand"]),
                     "location": r["location"], "quantity": int(r["quantity"])}
                    for _, r in _inv.iterrows()])
            if p == "/api/gap":
                for k in ("sku", "location", "weeks"):
                    if k not in q:
                        return self._err(400, f"缺少参数 {k}")
                g = tools.stock_demand_difference(int(q["sku"]), q["location"], int(q["weeks"]))
                return self._send(200, g)
            if p == "/api/suppliers":
                if "sku" not in q:
                    return self._err(400, "缺少参数 sku")
                board = supplier_board(q["sku"], q.get("location", ""))
                return self._send(200, {"board": board,
                                        "flip": bool(board and sorted(board, key=lambda x: x["unit_cost"])[0]["supplier"] != board[0]["supplier"])})
            if p == "/api/scan":
                return self._send(200, scan.scan(int(q.get("weeks", 12))))
            if p == "/api/scan/latest":
                lp = os.path.join(BASE, "panel", "reports", "latest.json")
                if not os.path.exists(lp):
                    return self._err(404, "尚无报告，请先 GET /api/scan")
                return self._send(200, json.load(open(lp)))
            m = re.match(r"^/api/decision/([a-f0-9]+)$", p)
            if m:
                job = JOBS.get(m.group(1))
                if not job:
                    return self._err(404, "任务不存在")
                return self._send(200, job)
            return self._err(404, f"未知端点 {p}")
        except Exception as e:
            return self._err(500, f"{type(e).__name__}: {e}")

    def do_POST(self):
        p = self.path
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            if p == "/api/decision":
                question = (body.get("question") or "").strip()
                if not question:
                    return self._err(400, "缺少 question")
                jid = uuid.uuid4().hex[:10]
                threading.Thread(target=job_worker, args=(jid, question, body.get("with_audit", True)),
                                 daemon=True).start()
                return self._send(202, {"job_id": jid, "status": "RUNNING",
                                        "poll": f"/api/decision/{jid}", "expected_seconds": "60-120"})
            if p == "/api/upload/preview":
                raw = base64.b64decode(body.get("file_b64", ""))
                df = cd.parse_upload(raw, body.get("filename", "x.csv"))
                return self._send(200, {"rows": int(df.shape[0]), "columns": [str(c) for c in df.columns],
                                        "sample": df.head(3).to_dict(orient="records"),
                                        "mapping_fields": cd.MAPPING_FIELDS})
            if p == "/api/upload/scan":
                raw = base64.b64decode(body.get("file_b64", ""))
                df = cd.parse_upload(raw, body.get("filename", "x.csv"))
                canon, errors, notes = cd.validate_and_convert(
                    df, body.get("mapping", {}), float(body.get("default_weekly_demand", 100)))
                if errors:
                    return self._send(422, {"error": {"type": "ValidationError", "messages": errors}})
                rep = cd.custom_scan(canon, int(body.get("weeks", 12)), tools.get_shipping_cost)
                return self._send(200, {"notes": notes, "report": rep})
            return self._err(404, f"未知端点 {p}")
        except Exception as e:
            return self._err(500, f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", 8765), H)
    print("API on :8765", flush=True)
    srv.serve_forever()
