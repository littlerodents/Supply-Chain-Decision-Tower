#!/usr/bin/env python3
"""OpenAI 兼容端点极简客户端（仅 stdlib，零依赖）。

三值约定（AGENTS.md 硬规矩）：REPRO_BASE_URL / REPRO_MODEL / REPRO_API_KEY。
视频输入的确切 API 形态 UNPROVEN——由 tools/probe.py 在 D1 spike 实测后定案。
"""
import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request


def _endpoint(base_url: str) -> str:
    base = (base_url or "").rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def chat(messages, model=None, base_url=None, api_key=None,
         timeout=180, max_retries=2, temperature=0.2):
    """POST /chat/completions，返回 (content_str, usage_dict, latency_sec)。"""
    base_url = base_url or os.environ.get("REPRO_BASE_URL", "")
    api_key = api_key or os.environ.get("REPRO_API_KEY", "")
    model = model or os.environ.get("REPRO_MODEL", "step-3.7-flash")
    if not base_url or not api_key:
        raise SystemExit("[env] REPRO_BASE_URL / REPRO_API_KEY 未设置——先完成 tools/spike_plan.md 第 0 步")
    payload = {"model": model, "messages": messages, "temperature": temperature}
    req = urllib.request.Request(
        _endpoint(base_url),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST")
    last_err = None
    for attempt in range(max_retries + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return content, usage, round(time.time() - t0, 2)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            last_err = f"HTTP {e.code}: {body}"
            if e.code in (401, 403, 404):  # 重试无意义
                break
        except Exception as e:  # noqa: BLE001
            last_err = repr(e)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"chat 调用失败（model={model}）: {last_err}")


def data_uri(path: str) -> str:
    """本地文件 → base64 data URI（image/jpeg 等按扩展名判定）。"""
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def text_part(text: str) -> dict:
    return {"type": "text", "text": text}


def image_part(path: str) -> dict:
    return {"type": "image_url",
            "image_url": {"url": data_uri(path)}}


def video_part_variants(path: str):
    """视频输入的候选 API 形态（spike 逐个试，命中哪个记进 dual-model.md）。

    UNPROVEN：D1 spike 前不知道 StepFun 收哪种；全部 4xx 就走抽帧 fallback。
    """
    uri = data_uri(path)
    return [
        ("video_url_data_uri", {"type": "video_url", "video_url": {"url": uri}}),
        ("video_data_uri", {"type": "video", "video": uri}),
        ("input_video", {"type": "input_video", "input_video": uri}),
        ("file_part", {"type": "file", "file": {"file_data": uri}}),
    ]
