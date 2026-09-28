#!/usr/bin/env python3
"""模型对比 · FDE 结构化任务（ Nemotron 本地 vs 3.7 Flash 云端 ）。

用法（本地跑，Nemotron 走 SSH 隧道 → 租机 ollama 的 OpenAI 兼容端点）：
    # 先开隧道（复用 ControlMaster）:
    # sshpass -e ssh -p 39954 $CM -N -L 11434:127.0.0.1:11434 sparker@spark.zhujihezi.com &
    python3 tools/compare_fde.py --runs 3
    # 单测一端:
    python3 tools/compare_fde.py --runs 3 --only nemotron-local
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openai_compat import chat  # noqa: E402

PROMPT = (
    "你是前线部署工程师（FDE）。客户说：「我们有300家门店的销售数据在Excel里，"
    "每周人工汇总报表要2天，经常出错。」只输出严格JSON："
    '{"problem":一句话,"data_assets":[...],"proposed_solution":一句话,"risks":[...],"expected_value":一句话}'
)

CANDIDATES = {
    "step-3.7-flash": ("https://api.stepfun.com/v1", "step-3.7-flash",
                       os.environ.get("REPRO_API_KEY", "")),
    "nemotron-local": ("http://127.0.0.1:11434/v1", "nemotron-3-super:120b-a12b", "ollama"),
}


def judge(text: str) -> dict:
    """质量五维打分（0/1）：JSON 一次成型 / 五字段齐全 / 方案具体性 / 风险≥2条 / 价值可量化。"""
    s = text.strip()
    score = {"json_valid": 0, "fields_complete": 0, "solution_specific": 0, "risks_gte2": 0, "value_quantified": 0}
    try:
        obj = json.loads(s[s.find("{"):s.rfind("}") + 1])
        score["json_valid"] = 1
        need = ["problem", "data_assets", "proposed_solution", "risks", "expected_value"]
        if all(k in obj for k in need):
            score["fields_complete"] = 1
            score["risks_gte2"] = 1 if len(obj.get("risks", [])) >= 2 else 0
            sol = obj.get("proposed_solution", "")
            score["solution_specific"] = 1 if len(sol) >= 15 and any(w in sol for w in ["自动", "平台", "流程", "系统", "agent", "AI"]) else 0
            val = obj.get("expected_value", "")
            score["value_quantified"] = 1 if any(c.isdigit() for c in val) else 0
    except Exception:  # noqa: BLE001
        pass
    return score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", choices=list(CANDIDATES))
    a = ap.parse_args()
    names = [a.only] if a.only else list(CANDIDATES)
    for name in names:
        base, model, key = CANDIDATES[name]
        hits_total = 0
        for i in range(a.runs):
            t0 = time.time()
            out, usage, lat = chat([{"role": "user", "content": PROMPT}],
                                   model=model, base_url=base, api_key=key, temperature=0.2)
            sc = judge(out)
            hits = sum(sc.values())
            hits_total += hits
            print(f"[{name}] run{i+1}: lat={lat}s tok={usage.get('total_tokens')} 质量{hits}/5 {list(sc)}")
        print(f"[{name}] === 平均质量 {hits_total/a.runs:.1f}/5（{a.runs} runs）===")


if __name__ == "__main__":
    main()
