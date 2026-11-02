#!/usr/bin/env python3
"""四象限评测 runner（ISC-17）：{bare, +skill} × {step-3.7-flash, nemotron-local}。

agent 模拟协议：模型可在回复中输出 ```bash 代码块调用工具（仅允许本 skill 的 tools.py），
harness 白名单执行并把 stdout 回传，最多 MAX_ROUNDS 轮，终答按 gold.json 判定。

用法：
  python3 tools/run_evals.py --brain stepfun --context skill
  python3 tools/run_evals.py --brain stepfun --context bare --tasks pos-dec-001
  python3 tools/run_evals.py --brain nemotron --context skill   # 需在 Spark 上或开隧道
产物：evidence/evals/results-<brain>-<context>.json + 终端摘要
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(BASE, "skills", "supply-chain-control-tower")
TOOLS = os.path.join(SKILL, "scripts", "tools.py")

sys.path.insert(0, os.path.join(BASE, "tools"))
from openai_compat import chat  # noqa: E402

BRAINS = {
    "stepfun": (os.environ.get("REPRO_BASE_URL", "https://api.stepfun.com/v1"),
                "step-3.7-flash", os.environ.get("REPRO_API_KEY", "")),
    "nemotron": ("http://127.0.0.1:11434/v1", "nemotron-3-super:120b-a12b", "ollama"),
}
MAX_ROUNDS = 8
DANGEROUS = ("rm ", "sudo", "curl", "wget", ">>", "&&", "||", ";", "|", "`", "$(")

BARE_SYS = "你是供应链运营助手。用中文直接回答用户问题。"

SKILL_SYS = f"""你已安装 supply-chain-control-tower skill。请严格按以下技能文档工作：

{open(os.path.join(SKILL, 'SKILL.md')).read()}

工具 API 语义：
{open(os.path.join(SKILL, 'references', 'api.md')).read()}

供应链知识：
{open(os.path.join(SKILL, 'references', 'knowledge.md')).read()}

工具脚本绝对路径：{TOOLS}
调用方式：在回复中输出 ```bash 代码块（仅此脚本，例如 ```bash
python3 {TOOLS} gap --sku 13001 --location "San Francisco" --weeks 12
``` ），系统会执行并把 JSON 输出回传给你。拿到全部所需数据后，按输出契约给出最终回答（正例=决策 JSON 代码块，负例=末行 NO_REORDER:<余量>）。"""


def extract_bash(text: str) -> list:
    blocks = re.findall(r"```bash\s*(.*?)```", text, re.DOTALL)
    cmds = []
    for b in blocks:
        for line in b.strip().splitlines():
            line = line.strip()
            if "tools.py" in line and line.startswith("python3") \
                    and not any(d in line for d in DANGEROUS):
                cmds.append(line)
    return cmds


def extract_json(text: str):
    m = re.findall(r"\{[^{}]*\}", text, re.DOTALL)
    for s in reversed(m):
        try:
            return json.loads(s)
        except Exception:  # noqa: BLE001
            continue
    return None


def run_agent(question: str, brain: tuple, use_skill: bool):
    """迷你 agent 循环：返回 (final_text, rounds, tool_calls, latency, tokens)。"""
    sysmsg = SKILL_SYS if use_skill else BARE_SYS
    msgs = [{"role": "user", "content": f"{sysmsg}\n\n---\n\n用户问题：{question}"}]
    t0, tokens, rounds, calls = time.time(), 0, 0, 0
    final = ""
    for _ in range(MAX_ROUNDS):
        rounds += 1
        out, usage, _ = chat(msgs, model=brain[1], base_url=brain[0], api_key=brain[2], timeout=300)
        tokens += usage.get("total_tokens") or 0
        final = out
        cmds = extract_bash(out)
        if not cmds:
            break
        feedback = []
        for c in cmds[:4]:
            calls += 1
            r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=90)
            feedback.append(f"$ {c}\n{r.stdout.strip()[:3000]}" + (f"\n[stderr] {r.stderr.strip()[-300:]}" if r.returncode else ""))
        msgs.append({"role": "assistant", "content": out})
        msgs.append({"role": "user", "content": "工具输出：\n" + "\n\n".join(feedback) +
                     "\n\n继续。拿到足够数据后请给最终回答（不再输出 bash）。"})
    return final, rounds, calls, round(time.time() - t0, 1), tokens


AUDIT_SYS = """你是供应链决策审计 agent（另一独立智能体，与作答者无通信）。
用户会给你：原问题 + 作答者的最终回答。你的职责：独立使用工具（bash 调用 tools.py，与作答者相同协议）复核关键数字（缺口/库存/预测/单价/运费/总量），然后只输出一行判定：
- 数字全部正确 → `VERDICT: PASS`
- 有错 → `VERDICT: FAIL` + 一个修正后的八字段决策 JSON 代码块（或 NO_REORDER:<gap>）
不要寒暄，不要重复作答者的推理。"""


def run_verifier(question: str, worker_final: str, brain: tuple):
    """双 agent 审计：verifier 独立复核 worker 终答。返回 (final_text, tool_calls, latency)。"""
    msgs = [{"role": "user", "content":
             f"{AUDIT_SYS}\n\n---\n\n原问题：{question}\n\n作答者最终回答：\n{worker_final[:3000]}\n\n请独立复核。"}]
    t0, calls = time.time(), 0
    final = worker_final
    for _ in range(4):
        out, _u, _l = chat(msgs, model=brain[1], base_url=brain[0], api_key=brain[2], timeout=300)
        final = out
        cmds = extract_bash(out)
        if not cmds:
            break
        feedback = []
        for c in cmds[:4]:
            calls += 1
            r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=90)
            feedback.append(f"$ {c}\n{r.stdout.strip()[:2000]}")
        msgs.append({"role": "assistant", "content": out})
        msgs.append({"role": "user", "content": "工具输出：\n" + "\n\n".join(feedback) + "\n\n给出最终判定（PASS 或 FAIL+修正JSON）。"})
    return final, calls, round(time.time() - t0, 1)


def apply_verdict(worker_final: str, verdict_text: str) -> str:
    """FAIL 且审计给出修正 JSON/NO_REORDER 时采纳修正，否则维持原答。"""
    if "VERDICT: FAIL" in verdict_text:
        if "NO_REORDER" in verdict_text:
            return verdict_text[verdict_text.find("NO_REORDER"):]
        m = re.findall(r"\{[^{}]*\"decision\"[^{}]*\}", verdict_text, re.DOTALL)
        for s in reversed(m):
            try:
                json.loads(s)
                return s
            except Exception:  # noqa: BLE001
                continue
    return worker_final


def judge(task, gold, final_text, tool_calls) -> dict:
    k, tid = task["kind"], task["id"]
    res = {"task": tid, "pass": False}
    g = gold
    if k in ("decision", "negative"):
        has_no = "NO_REORDER" in final_text
        j = extract_json(final_text)
        dec = (j or {}).get("decision")
        if g["decision"] == "NO_REORDER":
            res["pass"] = has_no and dec != "REORDER" and "order_qty" not in final_text
            res["expect"] = "NO_REORDER+" + str(g["gap"])
        else:
            ok = (dec == "REORDER" and j.get("order_qty") == g["order_qty"]
                  and j.get("supplier") == g["supplier"]
                  and j.get("total_cost") is not None
                  and abs(j["total_cost"] - g["total_cost"]) <= max(1.0, g["total_cost"] * 0.01))
            res["pass"] = bool(ok)
            res["expect"] = f"REORDER {g['order_qty']}×{g['supplier']} ≈{g['total_cost']}"
    elif k == "query":
        def _nums(s):
            return {round(float(x), 2) for x in re.findall(r"\d+\.?\d*", s)}
        gnums = _nums(json.dumps(g, ensure_ascii=False))
        tnums = _nums(final_text)
        res["pass"] = len(gnums) > 0 and gnums.issubset(tnums)
        res["expect"] = "数字集一致：" + ",".join(str(x) for x in sorted(gnums)[:6])
    elif k == "irrelevant":
        res["pass"] = tool_calls == 0
        res["expect"] = "零工具调用"
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", choices=list(BRAINS), required=True)
    ap.add_argument("--context", choices=["bare", "skill"], required=True)
    ap.add_argument("--tasks", help="逗号分隔 id，缺省全量")
    ap.add_argument("--verify", choices=list(BRAINS), help="审计 agent 所用主脑（双 agent 协同）")
    a = ap.parse_args()
    tasks = json.load(open(os.path.join(SKILL, "evals", "evals.json")))["tasks"]
    gold = json.load(open(os.path.join(SKILL, "evals", "gold.json")))
    if a.tasks:
        keep = set(a.tasks.split(","))
        tasks = [t for t in tasks if t["id"] in keep]
    brain = BRAINS[a.brain]
    results = []
    for t in tasks:
        final, rounds, calls, lat, tok = run_agent(t["query"], brain, a.context == "skill")
        v_info = {}
        if a.verify and t["kind"] in ("decision", "negative"):
            v_text, v_calls, v_lat = run_verifier(t["query"], final, BRAINS[a.verify])
            corrected = apply_verdict(final, v_text)
            v_info = {"verifier": a.verify, "verdict": ("FAIL-corrected" if corrected != final else "PASS/kept"),
                      "verifier_tools": v_calls, "verifier_latency_s": v_lat}
            final = corrected
        r = judge(t, gold[t["id"]], final, calls)
        r.update({"rounds": rounds, "tool_calls": calls, "latency_s": lat, "tokens": tok, **v_info})
        results.append(r)
        print(f"[{a.brain}/{a.context}] {t['id']:14s} {'✓' if r['pass'] else '✗'} "
              f"rounds={rounds} tools={calls} lat={lat}s | 期望 {r.get('expect','')[:50]}")
    npass = sum(1 for r in results if r["pass"])
    print(f"\n=== {a.brain}/{a.context}: {npass}/{len(results)} pass ===")
    os.makedirs(os.path.join(BASE, "evidence", "evals"), exist_ok=True)
    out = os.path.join(BASE, "evidence", "evals", f"results-{a.brain}-{a.context}.json")
    json.dump(results, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"→ {out}")


if __name__ == "__main__":
    main()
