#!/usr/bin/env python3
"""D1 spike 探针：text → image → video，三级梯子。

用法（在仓库根）：
    python3 tools/probe.py text
    python3 tools/probe.py image assets/samples/shot.png
    python3 tools/probe.py video assets/samples/clip.mp4
    python3 tools/probe.py video assets/samples/clip.mp4 --model step-5-preview

判据与记录方式见 tools/spike_plan.md。输出原样落 evidence/spike/。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openai_compat import chat, image_part, text_part, video_part_variants  # noqa: E402

EVID = "evidence/spike"


def _save(tag, content, usage, latency, variant=None):
    os.makedirs(EVID, exist_ok=True)
    name = f"{tag}-{variant or 'base'}.json"
    with open(os.path.join(EVID, name), "w") as f:
        json.dump({"content": content, "usage": usage, "latency_sec": latency}, f, ensure_ascii=False, indent=2)
    print(f"[ok] {name}  latency={latency}s  usage={usage}")


def probe_text(model):
    msg = [{"role": "user", "content": "Reply with exactly: PONG"}]
    content, usage, lat = chat(msg, model=model)
    assert "PONG" in content, f"探针失败：{content!r}"
    _save(f"text-{model.replace('.', '_')}", content, usage, lat)


def probe_image(path, model):
    msg = [{"role": "user", "content": [
        text_part("用一句话描述这张截图里发生了什么。"),
        image_part(path),
    ]}]
    content, usage, lat = chat(msg, model=model)
    _save(f"image-{model.replace('.', '_')}", content, usage, lat)


def probe_video(path, model):
    ok = False
    for variant, part in video_part_variants(path):
        try:
            msg = [{"role": "user", "content": [
                text_part("这段录屏里发生了什么错误？一句话。"),
                part,
            ]}]
            content, usage, lat = chat(msg, model=model)
            print(f"[HIT] variant={variant} latency={lat}s")
            _save(f"video-{model.replace('.', '_')}", content, usage, lat, variant)
            ok = True
            break
        except Exception as e:  # noqa: BLE001
            print(f"[miss] variant={variant}: {str(e)[:120]}")
    if not ok:
        print("[FAIL] 四种视频形态全 4xx/超时 → 按 spike_plan.md 第 4 步走抽帧 fallback")
        raise SystemExit(3)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["text", "image", "video"])
    ap.add_argument("path", nargs="?", help="image/video 的文件路径")
    ap.add_argument("--model", default=os.environ.get("REPRO_MODEL", "step-3.7-flash"))
    a = ap.parse_args()
    if a.stage in ("image", "video") and not a.path:
        raise SystemExit("image/video 阶段需要文件路径")
    {"text": lambda: probe_text(a.model),
     "image": lambda: probe_image(a.path, a.model),
     "video": lambda: probe_video(a.path, a.model)}[a.stage]()
