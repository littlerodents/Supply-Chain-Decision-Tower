#!/usr/bin/env python3
"""gold 评测 runner（ISC-25 素材）：12 任务全量跑当前默认脑，对照工具直算金答案判分。

不修改 skill/评测资产，只读取。产物：results JSON + markdown 报告。
"""
import json, os, re, subprocess, sys, time

SKILL = os.path.expanduser("~/.openclaw/workspace/skills/supply-chain-control-tower")
OUTDIR = os.path.expanduser("~/isc-submission-20260927/素材")
RUN_TAG = sys.argv[1] if len(sys.argv) > 1 else "r1"
ENV = dict(os.environ, PATH=os.path.expanduser("~/node26/bin") + ":" + os.environ["PATH"])

evals = json.load(open(os.path.join(SKILL, "evals", "evals.json")))
gold = json.load(open(os.path.join(SKILL, "evals", "gold.json")))


def run_task(task):
    sid = f"pi-dgx-eval27-{task['id']}-{RUN_TAG}"
    t0 = time.time()
    r = subprocess.run(
        ["openclaw", "agent", "--session-id", sid, "--message", task["query"], "--json"],
        capture_output=True, text=True, timeout=280, env=ENV)
    latency = round(time.time() - t0, 1)
    try:
        d = json.loads(r.stdout)
        meta = d["result"]["meta"]
        reply = meta.get("finalAssistantVisibleText") or ""
        am = meta["agentMeta"]
        tools = meta.get("toolSummary", {})
        usage = am.get("usage", {}).get("total")
        raw_path = os.path.join(OUTDIR, sid + ".json")
        open(raw_path, "w").write(r.stdout)
    except Exception as e:
        return {"id": task["id"], "kind": task["kind"], "pass": False,
                "reason": f"runner_error:{e}", "latency": latency}
    return {"id": task["id"], "kind": task["kind"], "pass": False, "reason": "",
            "reply": reply, "tools": tools, "latency": latency, "tokens": usage, "sid": sid}


def last_json_block(text):
    blocks = [b for b in text.split("```") if b.strip().startswith("json")]
    if not blocks:
        return None
    try:
        return json.loads(blocks[-1].strip()[4:].strip())
    except Exception:
        return None


def nums_in(text):
    return {float(x) for x in re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))}


def num_hit(want, got_set, tol=0.005):
    return any(abs(want - g) <= tol for g in got_set)


def score(task, res):
    g = gold[task["id"]]
    reply, why = res["reply"], []
    if task["kind"] == "decision":
        dj = last_json_block(reply)
        if not dj:
            return False, "未输出决策 JSON 代码块"
        for f, tol in [("decision", None), ("supplier", None), ("order_qty", 0.01),
                       ("unit_cost", 0.01), ("shipping_cost", 0.01), ("total_cost", 0.01)]:
            want, got = g.get(f), dj.get(f)
            if tol is None:
                ok = want == got
            else:
                ok = got is not None and abs(float(got) - float(want)) <= tol
            if not ok:
                why.append(f"{f}: want={want} got={got}")
        return (not why), ("; ".join(why) or "八字段与金答案一致")
    if task["kind"] == "query":
        gnums = set()
        if g.get("type") == "table":
            for row in g["rows"]:
                gnums |= {float(v) for v in row.values() if isinstance(v, (int, float))}
        elif g.get("type") == "series":
            gnums = {float(v) for v in g["demand"]}
        else:
            gnums = {float(g["value"])}
        reply_nums = nums_in(reply)
        missing = [w for w in gnums if not num_hit(w, reply_nums)]
        if missing:
            return False, f"回复缺少金答案数字: {sorted(missing)[:6]}"
        if res["tools"].get("failures"):
            return False, f"工具失败 {res['tools']['failures']} 次"
        return True, f"金答案 {len(gnums)} 个数字全部命中且零工具失败"
    if task["kind"] == "negative":
        lines = [l.strip() for l in reply.splitlines() if l.strip()]
        want_line = f"NO_REORDER:{g['gap']}"
        if not lines or lines[-1] != want_line:
            return False, f"末行应={want_line!r} 实={lines[-1] if lines else '空'!r}"
        # 判据：零补货建议字段。全空值的 NO_REORDER 元数据块不算建议（v3 修正）。
        dj = last_json_block(reply)
        if dj is not None and (
            dj.get("decision") == "REORDER"
            or (isinstance(dj.get("order_qty"), (int, float)) and dj.get("order_qty", 0) > 0)
            or dj.get("supplier") not in (None, "", 0)
        ):
            return False, f"负例 JSON 含补货建议字段: decision={dj.get('decision')} order_qty={dj.get('order_qty')} supplier={dj.get('supplier')}"
        if re.search(r"order_qty['\"]?\s*[:=]\s*[1-9]", reply):
            return False, "负例正文含非零订量"
        return True, f"末行纯文本 {want_line}，无补货建议字段（元数据块：{'有' if dj else '无'}）"
    if task["kind"] == "irrelevant":
        if "NO_REORDER" in reply or "order_qty" in reply:
            return False, "无关问句触发了补货输出"
        return True, "未触发供应链决策输出"


results = []
for t in evals["tasks"]:
    res = run_task(t)
    ok, reason = score(t, res)
    res["pass"], res["reason"] = ok, reason
    results.append(res)
    print(f"[{res['id']}] {'PASS' if ok else 'FAIL'} · {reason} · {res['latency']}s", flush=True)

n_pass = sum(1 for r in results if r["pass"])
summary = {"run_tag": RUN_TAG, "ts": time.strftime("%F %T"), "pass": n_pass,
           "total": len(results), "tasks": results}
json.dump(summary, open(os.path.join(OUTDIR, f"gold-eval-{RUN_TAG}.json"), "w"),
          ensure_ascii=False, indent=1, default=str)

by = {}
for r in results:
    by.setdefault(r["kind"], [0, 0])[1] += 1
    by[r["kind"]][0] += r["pass"]
head = f"# Gold 评测报告（run {RUN_TAG}，{summary['ts']}）\n\n**总分 {n_pass}/{len(results)}**\n\n"
rows = ["| 任务 | 类型 | 判定 | 依据 | 延迟s | tokens |", "|---|---|---|---|---|---|"]
for r in results:
    rows.append(f"| {r['id']} | {r['kind']} | {'✅' if r['pass'] else '❌'} | {r['reason'][:60]} | {r['latency']} | {r.get('tokens') or '-'} |")
open(os.path.join(OUTDIR, f"gold-eval-{RUN_TAG}.md"), "w").write(
    head + "\n".join(rows) + "\n\n分类：" + "，".join(f"{k} {v[0]}/{v[1]}" for k, v in by.items()) + "\n")
print(f"\n== 总分 {n_pass}/{len(results)} ==")
