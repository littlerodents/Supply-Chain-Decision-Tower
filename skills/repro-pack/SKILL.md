---
name: repro-pack
description: "把一段操作录屏（30–90s）装配成 agent 可直接消费的「复现包」：结构化 bug 卡 + 带时间戳关键帧 + 画面错误原文 + 复现步骤，并按 agent 消费格式开 GitHub issue。Use when: 录屏报 bug / 从屏幕录像提取错误 / 给修复 agent 交接现场 / bug 证据包 / repro pack / screenshot video to issue. Not for: 无 bug 录屏的内容摘要、实时屏幕捕获、人工润色的报告、需要远程接入对方的场景（本 skill 不做 SSH/远程控制）。"
license: Apache-2.0
metadata: { "openclaw": { "emoji": "📦", "requires": { "bins": ["python3", "bash", "ffmpeg"] } } }
---

# repro-pack 主流程

目标：录屏进 → 复现包出 → 修复 agent 接单。负例（无 bug）只回一句，不产任何包。

## 前置

- 三值环境变量（换脑只改这三个）：`REPRO_BASE_URL`、`REPRO_MODEL`（默认 `step-3.7-flash`）、`REPRO_API_KEY`
- `ffmpeg`（必需）；`gh`（开 issue 时需要，`--no-issue` 时可缺）
- 录屏文件 ≤120s、mp4/mov/webm

## Run

**标准调用**（agent 从对话里拿到录屏路径后执行）：

```bash
"<skill_dir>/scripts/run.sh" "<录屏绝对路径>" --out <输出目录> [--no-issue]
```

- 用户在 OpenClaw 对话里发的录屏会落在 inbound，把那个**绝对路径**传进来，不要自己猜路径
- 只想本地校验产出物：`run.sh --validate <bugcard.json>`

## 步骤（脚本内部）

1. **intake**：文件存在、时长 ≤120s，否则报错退出
2. **analyze**：调主脑（OpenAI 兼容端点，视频走 video_url+base64）。模型必须返回结构化 JSON——散文输出视为失败，重试一次后报错
3. **负例分支**：`has_bug=false` → 不产包、不开 issue、stdout 末行 `NO_BUG_FOUND`（纯文本）
4. **assemble**：`bugcard.json`（过 schema 校验）+ `frames/`（带时间戳关键帧）+ `repro.md`
5. **出口**：`gh issue create`（body 按 agent 消费格式）；`--no-issue` 跳过

## 输出契约

- 成功：stdout 末行必须是未格式化纯文本 `PACK:<包目录绝对路径>`——生成了包不等于用户看到了包，输出通道是契约的一部分
- 负例：末行 `NO_BUG_FOUND`

## 禁止行为

- 不推断录屏人物的任何身份信息
- 不在包/issue 里携带录屏中出现的个人数据（邮箱、头像、账单），发现即脱敏
- 不修改任何官方 skill 文件；环境差异一律走本 skill 的适配层

## references/

- `bugcard.schema.json`：bug 卡 JSON Schema（`--validate` 的判据）
- `issue-template.md`：issue body 模板
- `troubleshooting.md`：常见故障（401/超时/视频形态拒绝 → 抽帧模式）
