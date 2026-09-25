#!/usr/bin/env python3
"""换脑演示素材采集（ISC-21）：同一问句，双脑各跑一遍，全量对话存证。

用法：
  python3 tools/demo_capture.py --brain stepfun          # 输出 evidence/d3/brainswap-stepfun.md
  python3 tools/demo_capture.py --brain nemotron          # 需在 Spark 上跑
"""
import argparse
import importlib.util
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(BASE, "skills", "supply-chain-control-tower")
TOOLS = os.path.join(SKILL, "scripts", "tools.py")
sys.path.insert(0, os.path.join(BASE, "tools"))
sys.path.insert(0, os.path.join(BASE, "skills", "supply-chain-control-tower", "evals"))
from run_evals import BRAINS, MAX_ROUNDS, run_agent  # noqa: E402

QUESTION = ("San Francisco 的 Colombian Coffee 未来 12 周够卖吗？"
            "不够的话补多少、找哪个供应商、总成本多少？请给出完整建议单。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", choices=list(BRAINS), required=True)
    ap.add_argument("--question", default=QUESTION)
    a = ap.parse_args()
    brain = BRAINS[a.brain]
    final, rounds, calls, lat, tok = run_agent(a.question, brain, use_skill=True)
    os.makedirs(os.path.join(BASE, "evidence", "d3"), exist_ok=True)
    out = os.path.join(BASE, "evidence", "d3", f"brainswap-{a.brain}.md")
    with open(out, "w") as f:
        f.write(f"# 换脑素材 · {a.brain}\n\n> 问句：{a.question}\n"
                f"> 轮数 {rounds} · 工具调用 {calls} · 延迟 {lat}s · tokens {tok}\n\n"
                f"## 最终回答\n\n{final}\n")
    print(f"[{a.brain}] rounds={rounds} tools={calls} lat={lat}s → {out}")
    print("终答前 200 字：", final[:200].replace(chr(10), " "))


if __name__ == "__main__":
    main()
