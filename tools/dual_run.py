#!/usr/bin/env python3
"""D1 双模型对照驱动：同一段录屏，两模型各 N 次，三维（质量/延迟/成本）记录。

用法：
    python3 tools/dual_run.py assets/samples/clip.mp4 --runs 3
    python3 tools/dual_run.py <recording> --runs 3 --gold '{"type":"runtime-error","timestamp":2.0}'
"""
import argparse
import importlib.util
import json
import os
import statistics
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "rp", os.path.join(BASE, "..", "skills", "repro-pack", "scripts", "repro_pack.py"))
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

MODELS = ["step-3.7-flash", "step-5-preview"]


def quality(card, gold):
    """gold 三字段对照：type / location 关键词 / timestamp±3s。返回命中数。"""
    if not gold or not card.get("has_bug"):
        return None
    hits = 0
    b = card["bug"]
    if gold.get("type") and b["type"] == gold["type"]:
        hits += 1
    if gold.get("timestamp") and any(abs(t - gold["timestamp"]) <= 3 for t in b["timestamps"]):
        hits += 1
    if gold.get("location_kw") and gold["location_kw"].lower() in b["location"].lower():
        hits += 1
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recording")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--gold", help="JSON: type/timestamp/location_kw")
    a = ap.parse_args()
    gold = json.loads(a.gold) if a.gold else None
    dur = rp.duration_of(a.recording)
    results = {}
    for model in MODELS:
        os.environ["REPRO_MODEL"] = model
        rows = []
        for i in range(a.runs):
            card, usage, lat = rp.analyze(a.recording, dur)
            rp.validate(card)
            q = quality(card, gold)
            rows.append({"run": i + 1, "latency": lat,
                         "total_tokens": usage.get("total_tokens"),
                         "quality_hits": q, "has_bug": card["has_bug"],
                         "type": card["bug"]["type"], "severity": card["bug"]["severity"],
                         "timestamps": card["bug"]["timestamps"],
                         "location": card["bug"]["location"][:60]})
            print(f"[{model}] run{i+1}: lat={lat}s tok={usage.get('total_tokens')} "
                  f"hits={q}/{3 if gold else '-'} has_bug={card['has_bug']}")
        results[model] = rows
    os.makedirs("evidence/spike", exist_ok=True)
    with open("evidence/spike/dual-raw.json", "w") as f:
        json.dump({"recording": a.recording, "gold": gold, "runs": results}, f, ensure_ascii=False, indent=2)
    print("\n=== 摘要（中位延迟 / 平均 tokens / 质量命中）===")
    for model, rows in results.items():
        lats = statistics.median(r["latency"] for r in rows)
        toks = statistics.mean(r["total_tokens"] for r in rows)
        hits = [r["quality_hits"] for r in rows if r["quality_hits"] is not None]
        print(f"{model:20s} lat={lats}s tok={toks:.0f} hits={hits}")


if __name__ == "__main__":
    main()
