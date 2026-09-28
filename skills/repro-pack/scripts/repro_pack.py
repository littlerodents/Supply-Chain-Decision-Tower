#!/usr/bin/env python3
"""repro-pack 主链路：录屏 → 主脑 → 复现包 → GitHub issue。

用法：
    python3 skills/repro-pack/scripts/repro_pack.py <recording> [--out DIR] [--no-issue]
    python3 skills/repro-pack/scripts/repro_pack.py --validate <bugcard.json>

负例契约：无 bug 录屏 → 不产包、不开 issue、stdout 末行 NO_BUG_FOUND。
成功契约：stdout 末行 PACK:<包目录绝对路径>。

analyze 阶段 UNPROVEN：等 D1 spike 定案视频 API 形态后回填（见 tools/spike_plan.md）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "bugcard.schema.json")
MAX_SEC = 120  # 录屏时长上限，ffmpeg 探测

ANALYZE_PROMPT = """你是 bug 证据分析师。观看这段操作录屏，判断是否存在真实 bug（功能错误/崩溃/数据显示错误/交互失效）。
严格返回 JSON（不要 markdown 代码块）：
{"has_bug": bool, "confidence": 0-1, "bug": {"type": "ui-rendering|runtime-error|network|data-display|interaction|crash|other",
 "severity": "blocker|critical|major|minor|trivial", "location": "出错界面/组件，一句话",
 "error_text": "画面中的错误原文，无则空串", "timestamps": [出错秒数，至少一个],
 "repro_steps": ["步骤1", "..."], "affected_area": "可选", "notes": "可选"},
 "source": {"recording": "文件名", "duration_sec": 秒数}}
注意：样式微瑕、个人偏好、录屏者的误操作不算 bug。找不到 bug 就 has_bug=false。"""


def duration_of(path: str) -> float:
    try:
        out = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                              "-of", "csv=p=0", path], capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip())
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"[intake] 无法探测时长（装 ffmpeg 或检查文件）: {e}")


def analyze(path: str, duration: float):
    """调主脑理解录屏。视频形态已由 D1 spike 实测定案：video_url + base64 data URI。

    openai_compat 惰性导入：--validate 等纯本地路径不依赖网络客户端。
    返回 (card, usage, latency_sec)。模型散文输出重试一次，再失败即报错（SKILL.md 禁令）。
    """
    tools_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
    if os.path.isdir(tools_dir):  # 开发态：优先用仓里 tools/ 的上游版；安装态用同目录自包含副本
        sys.path.insert(0, tools_dir)
    from openai_compat import chat, text_part, data_uri  # noqa: E402

    content = [text_part(ANALYZE_PROMPT),
               {"type": "video_url", "video_url": {"url": data_uri(path)}}]
    last_err = None
    for attempt in range(2):
        raw, usage, lat = chat([{"role": "user", "content": content}])
        try:
            m = re.search(r"\{.*\}", raw, re.S)
            if not m:
                raise ValueError("模型未返回 JSON")
            card = json.loads(m.group(0))
            card.setdefault("source", {})
            card["source"].update({"recording": os.path.basename(path),
                                    "duration_sec": duration,
                                    "model": os.environ.get("REPRO_MODEL", "")})
            card.setdefault("schema_version", "1.0")
            return card, usage, lat
        except (ValueError, json.JSONDecodeError) as e:
            last_err = f"attempt{attempt + 1}: {e}; raw前100字: {raw[:100]!r}"
    raise SystemExit(f"[analyze] 模型两次未返回结构化 JSON——禁令：下游是 agent 不是人。最后错误: {last_err}")


def validate(card: dict) -> None:
    """按 references/bugcard.schema.json 手工校验（零依赖）。失败即抛错。"""
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    req = schema["required"]
    missing = [k for k in req if k not in card]
    assert not missing, f"缺必填字段: {missing}"
    assert card["schema_version"] == "1.0", "schema_version 必须是 1.0"
    assert isinstance(card["has_bug"], bool), "has_bug 必须是 bool"
    assert isinstance(card["confidence"], (int, float)) and 0 <= card["confidence"] <= 1
    bug = card.get("bug")
    if not card["has_bug"]:
        return  # 负例：行为闸门在 run()（不产包/NO_BUG_FOUND）；bug 内容不约束（实测模型回全空对象）
    assert isinstance(bug, dict), "has_bug=true 时 bug 必须是对象"
    obj = schema["definitions"]["bugObject"]
    breq = obj["required"]
    missing = [k for k in breq if k not in bug]
    assert not missing, f"bug 缺必填字段: {missing}"
    p = obj["properties"]
    for enum_field in ("type", "severity"):
        assert bug[enum_field] in p[enum_field]["enum"], f"{enum_field} 不在枚举内: {bug[enum_field]}"
    assert isinstance(bug["timestamps"], list) and len(bug["timestamps"]) >= 1 and all(
        isinstance(t, (int, float)) and t >= 0 for t in bug["timestamps"]), "timestamps 非法"
    assert isinstance(bug["repro_steps"], list) and len(bug["repro_steps"]) >= 1 and all(
        isinstance(s, str) for s in bug["repro_steps"]), "repro_steps 非法"
    assert isinstance(bug["error_text"], str) and isinstance(bug["location"], str)


def extract_frames(recording: str, timestamps, out_dir: str) -> list:
    frames = []
    for i, t in enumerate(sorted(set(timestamps))[:5]):
        dst = os.path.join(out_dir, f"frame_{i:02d}_{int(t)}s.png")
        r = subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss", str(max(0, t - 0.5)),
                            "-i", recording, "-frames:v", "1", dst], timeout=60)
        if r.returncode == 0 and os.path.exists(dst):
            frames.append(dst)
    return frames


def render_repro(card: dict) -> str:
    b = card["bug"]
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(b["repro_steps"], 1))
    return f"""# Repro · {b['type']} / {b['severity']}

- 位置：{b['location']}
- 错误原文：`{b['error_text'] or '（画面无文本错误）'}`
- 出错时间戳：{b['timestamps']}

## 复现步骤
{steps}

> 由 repro-pack 从操作录屏自动装配。置信度 {card['confidence']}。
"""


def create_issue(pack_dir: str, card: dict, repo: str = None) -> str:
    body = render_repro(card) + f"\n---\nbugcard: {os.path.join(pack_dir, 'bugcard.json')}\n"
    cmd = ["gh", "issue", "create", "--title",
           f"[repro-pack] {card['bug']['type']}: {card['bug']['location'][:60]}",
           "--body", body]
    if repo:
        cmd += ["--repo", repo]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise SystemExit(f"[issue] gh 失败: {out.stderr[:200]}")
    return out.stdout.strip()


def run(recording: str, out: str, no_issue: bool, repo: str):
    if not os.path.isfile(recording):
        raise SystemExit(f"[intake] 文件不存在: {recording}")
    dur = duration_of(recording)
    if dur > MAX_SEC:
        raise SystemExit(f"[intake] 录屏 {dur:.0f}s 超过 {MAX_SEC}s 上限")
    card, _usage, _lat = analyze(recording, dur)
    validate(card)
    if not card["has_bug"]:
        print("[negative] 录屏未发现 bug——不产包、不开 issue")
        print("NO_BUG_FOUND")
        return 0
    pack = os.path.abspath(out or f"packs/{time.strftime('%Y%m%d-%H%M%S')}-{os.path.splitext(os.path.basename(recording))[0]}")
    os.makedirs(os.path.join(pack, "frames"), exist_ok=True)
    frames = extract_frames(recording, card["bug"]["timestamps"], os.path.join(pack, "frames"))
    with open(os.path.join(pack, "bugcard.json"), "w") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)
    with open(os.path.join(pack, "repro.md"), "w") as f:
        f.write(render_repro(card))
    validate(json.load(open(os.path.join(pack, "bugcard.json"))))  # 落盘后复验
    issue_url = "" if no_issue else create_issue(pack, card, repo)
    if issue_url:
        print(f"[issue] {issue_url}")
    print(f"PACK:{pack}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("recording", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--no-issue", action="store_true")
    ap.add_argument("--repo", help="gh 目标仓（默认当前目录仓）")
    ap.add_argument("--validate", help="只校验一个 bugcard.json，不调模型")
    a = ap.parse_args()
    if a.validate:
        validate(json.load(open(a.validate)))
        print("VALID")
        sys.exit(0)
    if not a.recording:
        ap.error("需要 recording 或 --validate")
    sys.exit(run(a.recording, a.out, a.no_issue, a.repo))
