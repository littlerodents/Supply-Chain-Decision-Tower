#!/usr/bin/env python3
"""供应链控制塔 · 前端对接 HTTP API（双契约：fieldwork-frontend /runs + 旧端点）。

零依赖（stdlib），端口 8765。能力来自冻结后端：tools 直算、daily_scan、custom_data、
openclaw 双智能体流水线。红线：只读、无凭据下发、白名单端点、错误统一 JSON。

fieldwork 契约（见前端 API.md / src/lib/types.ts）：
  GET /api/catalog                     目录（inventory/suppliers/products/source/live）
  POST /api/runs                       创建运行（mode=tool 秒级直算 / live 双智能体）
  GET  /api/runs/{id}?session_id=      轮询（幂等/会话归属/409/422 语义，错误 {"detail"}）
旧端点（Streamlit B 线 / 调试）：/api/health /api/products /api/inventory /api/gap
  /api/suppliers /api/scan /api/scan/latest /api/decision(旧异步) /api/upload/*

启动：nohup python3 api_server.py >/home/sparker/api.log 2>&1 &
"""
import base64
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.expanduser("~/.openclaw/workspace/skills/supply-chain-control-tower")
OPENCLAW = os.path.expanduser("~/node26/bin/openclaw")
AGENT_TIMEOUT = 150
CST = timezone(timedelta(hours=8))


def _now_iso():
    return datetime.now(CST).isoformat(timespec="seconds")


_spec = importlib.util.spec_from_file_location("tools", os.path.join(BASE, "scripts", "tools.py"))
tools = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(tools)
_spec2 = importlib.util.spec_from_file_location("scan", os.path.join(BASE, "scripts", "daily_scan.py"))
scan = importlib.util.module_from_spec(_spec2); _spec2.loader.exec_module(scan)
__import__("sys").path.insert(0, os.path.join(BASE, "panel"))
import custom_data as cd  # noqa: E402

import pandas as pd  # noqa: E402

_products_full = json.load(open(os.path.join(BASE, "data", "products.json")))["products"]
_products = {p["sku"]: p["brand"] for p in _products_full}
_pnames = {p["sku"]: p.get("name", "") for p in _products_full}
_inv = pd.read_csv(os.path.join(BASE, "data", "inventory.csv"))
_sup = pd.read_csv(os.path.join(BASE, "data", "suppliers.csv"))
_SOURCE_VERSION = hashlib.md5(("".join(sorted(_inv.to_csv(index=False))) +
                               "".join(sorted(_sup.to_csv(index=False)))).encode()).hexdigest()[:10]

JOBS = {}   # 旧 /api/decision 任务
RUNS = {}   # fieldwork /api/runs：request_id -> {"session_id","fingerprint","run",...}


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


def source_info():
    return {"version": _SOURCE_VERSION, "read_at": _now_iso(),
            "label": "本地样本 · 非实时库存 · 合成预测（DGX Spark）"}


def build_result(sku, location, weeks, decision_src="tool", dj=None, final_text=None,
                 verify_status="NOT_APPLICABLE", differences=None, events=None):
    g = tools.stock_demand_difference(int(sku), location, int(weeks))
    gap = g["gap_stock_minus_demand"]  # 旧 gap（参考）
    rop_gap = g.get("rop_gap", -gap)   # ROP gap（决策驱动）
    fc = tools.get_forecast(str(sku), location).head(int(weeks))
    cum, fpts = 0, []
    for dtx, r in fc.iterrows():
        cum += int(r["demand"])
        fpts.append({"date": dtx.isoformat() if hasattr(dtx, "isoformat") else str(dtx),
                     "demand": int(r["demand"]), "cumulative": cum})
    board = supplier_board(sku, location)
    qty = max(0, rop_gap + g.get('safety_stock', 0))  # ROP缺口+安全库存
    candidates = [{"supplier": b["supplier"], "source": b["location"], "unit_cost": b["unit_cost"],
                   "shipping_cost": b["shipping"], "landed_unit_cost": b["total_unit"],
                   "total_cost": round(qty * b["total_unit"], 2)} for b in board]
    if decision_src == "live" and dj and dj.get("decision") == "REORDER":
        decision = {"decision": "REORDER", "order_qty": dj.get("order_qty"),
                    "supplier": dj.get("supplier"), "unit_cost": dj.get("unit_cost"),
                    "shipping_cost": dj.get("shipping_cost"), "total_cost": dj.get("total_cost"),
                    "rationale": dj.get("rationale", ""), "tool_trace": dj.get("tool_trace", [])}
    elif rop_gap > 0 and board and decision_src == "tool":
        b = board[0]
        decision = {"decision": "REORDER", "order_qty": qty, "supplier": b["supplier"],
                    "unit_cost": b["unit_cost"], "shipping_cost": b["shipping"],
                    "total_cost": round(qty * b["total_unit"], 2),
                    "rationale": f"库存 {g['current_stock']}，{weeks} 周预测需求 {g['forecast_demand']}，缺口 {qty}；"
                                 f"总单价最低 {b['supplier']}（{b['unit_cost']}+{b['shipping']}）",
                    "tool_trace": ["gap", "suppliers", "shipping"]}
    elif decision_src == "live":
        decision = {"decision": "QUERY"}
    else:
        decision = {"decision": "NO_REORDER", "surplus": gap}
    return {"kind": "decision",
            "facts": {"sku": int(sku), "location": location, "weeks": int(weeks),
                      "current_stock": g["current_stock"], "forecast_demand": g["forecast_demand"],
                      "gap_stock_minus_demand": gap,
                      "rop_gap": rop_gap, "reorder_point": g.get("reorder_point"),
                      "safety_stock": g.get("safety_stock"),
                      "decision_mode": g.get("decision_mode", "gap")},
            "forecast": fpts, "candidates": candidates, "decision": decision,
            "source": source_info(), "final_text": final_text,
            "verification": {"status": verify_status, "differences": differences or []},
            "inventory": [{"sku": int(r["sku"]), "brand": r["brand"], "location": r["location"],
                           "quantity": int(r["quantity"])} for _, r in _inv.iterrows()],
            "suppliers": [{"sku": int(r["sku"]), "supplier": r["supplier"], "location": r["location"],
                           "unit_cost": float(r["unit_cost"])} for _, r in _sup.iterrows()],
            "_events": events or []}


def calc_events(sku, location, weeks):
    g = tools.stock_demand_difference(int(sku), location, int(weeks))
    board = supplier_board(sku, location)
    return [
        {"call_id": uuid.uuid4().hex[:8], "name": "gap", "origin": "calculator",
         "arguments": {"sku": int(sku), "location": location, "weeks": int(weeks)},
         "result": {"gap": g["gap_stock_minus_demand"], "stock": g["current_stock"],
                    "demand": g["forecast_demand"]}, "status": "SUCCEEDED", "at": _now_iso()},
        {"call_id": uuid.uuid4().hex[:8], "name": "suppliers", "origin": "calculator",
         "arguments": {"sku": int(sku)},
         "result": {"candidates": board}, "status": "SUCCEEDED", "at": _now_iso()},
    ]


def live_worker(entry, question, sku, location, weeks):
    rec = entry["run"]
    t0 = time.time()
    try:
        r = run_agent(question)
        entry["agent"] = r
        rec["model"] = f"{r['provider']}/{r['model']}"
        rec["model_location"] = "configured"
        text = r["text"]
        dj = last_json(text)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        ev = [{"call_id": r["sid"], "name": "agent_decision", "origin": "agent",
               "arguments": {"question": question[:120]},
               "result": {"tool_summary": r["tools"], "decision_json": dj},
               "status": "SUCCEEDED", "at": _now_iso()}]
        if dj and dj.get("decision") == "REORDER":
            # 独立核算（零 LLM）
            g = tools.stock_demand_difference(int(dj.get("sku") or sku), dj.get("location") or location,
                                              int(dj.get("weeks") or weeks))
            board = supplier_board(dj.get("sku") or sku, dj.get("location") or location)
            f = lambda x: float(x) if x is not None else 0.0  # noqa: E731
            diffs = []
            if not g.get("record_exists"):
                diffs.append("该 SKU×仓库无库存记录")
            elif board:
                best = board[0]
                if f(dj.get("order_qty")) != -g["gap_stock_minus_demand"]:
                    diffs.append(f"订量：模型 {dj.get('order_qty')} / 工具 {-g['gap_stock_minus_demand']}")
                if dj.get("supplier") != best["supplier"]:
                    diffs.append(f"供应商：模型 {dj.get('supplier')} / 工具 {best['supplier']}")
                want = round(f(dj.get("order_qty")) * (f(dj.get("unit_cost")) + f(dj.get("shipping_cost"))), 2)
                if abs(f(dj.get("total_cost")) - want) > 0.01:
                    diffs.append(f"总价：模型 {dj.get('total_cost')} / 实算 {want}")
            # 审计智能体
            a = run_agent(
                f"审计以下补货决策单。原问句：{question}\n\n待审决策单：\n{json.dumps(dj, ensure_ascii=False)}\n\n"
                f"来源会话：{r['sid']}。按 supply-chain-audit SOP 独立复算并输出审计判定 JSON。",
                agent="auditor")
            m = re.search(r'"audit"\s*:\s*"(PASS|FAIL)"', a["text"])
            ev.append({"call_id": a["sid"], "name": "audit_agent", "origin": "agent",
                       "arguments": {"source_decision": r["sid"]},
                       "result": {"verdict": m.group(1) if m else "UNPARSED", "final_text": a["text"][:2000]},
                       "status": "SUCCEEDED", "at": _now_iso()})
            calc_ok = g.get("record_exists") and board and not diffs
            audit_ok = (m.group(1) == "PASS") if m else False
            status = "PASS" if (calc_ok and audit_ok) else ("UNPROVEN" if not m else "FAIL")
            if not calc_ok and m:
                status = "FAIL"
            res = build_result(dj.get("sku") or sku, dj.get("location") or location,
                               int(dj.get("weeks") or weeks), decision_src="live", dj=dj,
                               final_text=text, verify_status=status,
                               differences=diffs + ([f"审计判定：{m.group(1)}"] if m else ["审计未完成"]),
                               events=ev)
        elif lines and re.fullmatch(r"NO_REORDER:\d+", lines[-1]):
            res = build_result(sku, location, weeks, decision_src="tool", final_text=text,
                               verify_status="PASS", differences=["负例末行合规（纯文本 NO_REORDER）"],
                               events=ev)
        elif "库存记录" in text and "无" in text:
            res = build_result(sku, location, weeks, decision_src="live", dj=None, final_text=text,
                               verify_status="PASS", differences=["Agent 如实回复无库存记录（未编数）"],
                               events=ev)
        else:
            res = build_result(sku, location, weeks, decision_src="live", dj=None, final_text=text,
                               verify_status="UNPROVEN", differences=["模型未输出合格决策单"], events=ev)
        rec["result"] = res
        rec["events"] = res.pop("_events", ev)
        rec["status"] = "SUCCEEDED"
        rec["stage"] = "done"
    except subprocess.TimeoutExpired:
        rec["status"] = "TIMED_OUT"; rec["error"] = f"推理超过 {AGENT_TIMEOUT}s"
    except Exception as e:
        rec["status"] = "FAILED"; rec["error"] = f"{type(e).__name__}: {e}"[:300]
    finally:
        rec["duration_ms"] = int((time.time() - t0) * 1000)


class ApiError(Exception):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail


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

    def _detail(self, code, msg):
        self._send(code, {"detail": msg})

    def _err(self, code, msg):
        self._send(code, {"error": {"type": "ApiError", "message": msg}})

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    # ------------------------------------------------------------- GET
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
            if p == "/api/catalog":
                return self._send(200, {
                    "inventory": [{"sku": int(r["sku"]), "brand": r["brand"], "location": r["location"],
                                   "quantity": int(r["quantity"])} for _, r in _inv.iterrows()],
                    "suppliers": [{"sku": int(r["sku"]), "supplier": r["supplier"], "location": r["location"],
                                   "unit_cost": float(r["unit_cost"])} for _, r in _sup.iterrows()],
                    "products": [{"sku": int(s), "brand": b, "name": _pnames.get(s, "")}
                                 for s, b in sorted(_products.items())],
                    "source": source_info(),
                    "live": {"ready": True, "model": "step-3.7-flash", "location": "configured",
                             "reason": None}})
            m = re.match(r"^/api/runs/([A-Za-z0-9-]+)$", p)
            if m:
                rid = m.group(1)
                entry = RUNS.get(rid)
                if not entry:
                    return self._detail(404, "请求不存在")
                if entry["session_id"] != q.get("session_id"):
                    return self._detail(404, "请求不属于当前会话")
                return self._send(200, entry["run"])
            if p == "/api/products":
                return self._send(200, [{"sku": s, "brand": b, "display": f"{s} {b}",
                                         "locations": sorted(_inv[_inv.sku == s].location.unique())}
                                        for s, b in sorted(_products.items())])
            if p == "/api/inventory":
                return self._send(200, [{"sku": int(r["sku"]), "brand": r["brand"], "display": r["brand"],
                                         "location": r["location"], "quantity": int(r["quantity"])}
                                        for _, r in _inv.iterrows()])
            if p == "/api/gap":
                for k in ("sku", "location", "weeks"):
                    if k not in q:
                        return self._err(400, f"缺少参数 {k}")
                return self._send(200, tools.stock_demand_difference(int(q["sku"]), q["location"], int(q["weeks"])))
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
            mo = re.match(r"^/api/decision/([a-f0-9]+)$", p)
            if mo:
                job = JOBS.get(mo.group(1))
                if not job:
                    return self._err(404, "任务不存在")
                return self._send(200, job)
            return self._err(404, f"未知端点 {p}")
        except ApiError as e:
            return self._detail(e.code, e.detail)
        except Exception as e:
            return self._err(500, f"{type(e).__name__}: {e}")

    # ------------------------------------------------------------- POST
    def do_POST(self):
        p = self.path
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            if p == "/api/runs":
                return self.handle_run(body)
            if p == "/api/decision":
                question = (body.get("question") or "").strip()
                if not question:
                    return self._err(400, "缺少 question")
                jid = uuid.uuid4().hex[:10]
                threading.Thread(target=self._legacy_decision_job, args=(jid, question, body.get("with_audit", True)),
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
        except ApiError as e:
            return self._detail(e.code, e.detail)
        except Exception as e:
            return self._err(500, f"{type(e).__name__}: {e}")

    def handle_run(self, b):
        rid, sid = b.get("request_id", ""), b.get("session_id", "")
        mode = b.get("mode")
        if mode not in ("tool", "live"):
            return self._detail(422, "mode 必须为 tool 或 live")
        question = (b.get("question") or "").strip()
        if mode == "live" and not question:
            return self._detail(422, "live 模式必须提供 question")
        try:
            sku, weeks = int(b.get("sku")), int(b.get("weeks"))
            location = str(b.get("location"))
        except (TypeError, ValueError):
            return self._detail(422, "sku/weeks 必须为整数")
        if not (1 <= weeks <= 52):
            return self._detail(422, "weeks 需在 1-52")
        if sku not in _products:
            return self._detail(422, f"未知 SKU {sku}")
        if not bool(((_inv.sku == sku) & (_inv.location == location)).any()):
            return self._detail(422, f"{location} 仓无 SKU {sku} 库存记录（请从目录选择有效组合）")
        fingerprint = json.dumps([mode, question, sku, location, weeks], ensure_ascii=False)
        if rid in RUNS:
            e = RUNS[rid]
            if e["session_id"] != sid or e["fingerprint"] != fingerprint:
                return self._detail(409, "request_id 已被其它会话或不同输入使用")
            return self._send(202, e["run"])
        for e in RUNS.values():
            if e["session_id"] == sid and e["run"]["status"] in ("RUNNING",):
                return self._detail(409, "当前会话已有执行中的分析，请等待其完成")
        run = {"request_id": rid, "session_id": sid, "mode": mode, "status": "RUNNING",
               "input": {"question": question, "sku": sku, "location": location, "weeks": weeks},
               "model": None, "model_location": None, "started_at": _now_iso(),
               "duration_ms": None, "stage": "accepted", "error": None,
               "backend_unknown": False, "result": None, "events": []}
        RUNS[rid] = {"session_id": sid, "fingerprint": fingerprint, "run": run}
        if mode == "tool":
            try:
                res = build_result(sku, location, weeks, decision_src="tool",
                                   verify_status="NOT_APPLICABLE",
                                   differences=["工具直算模式：结果即工具输出，无模型参与"],
                                   events=calc_events(sku, location, weeks))
                run["result"] = res
                run["events"] = res.pop("_events")
                run["status"] = "SUCCEEDED"
                run["stage"] = "done"
                run["duration_ms"] = 0
            except Exception as e:
                run["status"] = "FAILED"
                run["error"] = f"{type(e).__name__}: {e}"[:300]
        else:
            run["stage"] = "agent_running"
            threading.Thread(target=live_worker, args=(RUNS[rid], question, sku, location, weeks),
                             daemon=True).start()
        return self._send(202, run)

    @staticmethod
    def _legacy_decision_job(jid, question, with_audit):
        try:
            JOBS[jid] = {"status": "RUNNING", "started_at": _now_iso()}
            r = run_agent(question)
            pkg = {"question": question, "decision_agent": {
                "session": r["sid"], "model": f"{r['provider']}/{r['model']}",
                "duration_ms": r["duration_ms"], "tool_summary": r["tools"],
                "final_text": r["text"], "decision_json": last_json(r["text"])}}
            JOBS[jid] = {"status": "SUCCEEDED", "result": pkg, "finished_at": _now_iso()}
        except Exception as e:
            JOBS[jid] = {"status": "FAILED", "error": f"{type(e).__name__}: {e}"[:400]}


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", 8765), H)
    print("API on :8765（含 /api/catalog + /api/runs 契约）", flush=True)
    srv.serve_forever()
