# SPARK-DEPLOY · D3 部署剧本（SSH 一到就照跑）

> 目标：1 小时内从「裸 Spark」到「OpenClaw 里 repro-pack ready + 冒烟通过」。
> 配方来源：官方安装器 + 训练营 workshop notebook（真实命令提取），非凭记忆。

## 前置确认（进群问 / 连上先跑）

```bash
uname -m          # 期待 aarch64
df -h /           # 磁盘余量
free -h; nvidia-smi 2>/dev/null || echo '无 nvidia-smi（GB10 可能用别的工具）'
command -v python3 ffmpeg node; node -v 2>/dev/null   # Node 24.16+/26 供 OpenClaw
```

- [ ] 机器可用时段 / 是否独占
- [ ] 能否装东西（curl 管道安装 / npm -g）
- [ ] 机器是私有还是共享（决定 key 注入方式，见第 5 步）

## 第 1 步 · 装 OpenClaw（官方安装器，ARM64 Linux 支持）

```bash
curl -fsSL https://openclaw.ai/install.sh | bash     # 或 npm install -g openclaw@latest --allow-scripts=openclaw
openclaw --version
```

## 第 2 步 · onboard + gateway 配置（训练营 cell 27 的真实命令）

```bash
openclaw onboard --non-interactive --accept-risk --mode local --skip-health
openclaw config set gateway.mode local
openclaw config set gateway.port 3030
openclaw config set gateway.bind lan
openclaw config set agents.defaults.thinkingDefault off
```

**Gateway 主脑 = 本地 Qwen（推荐）**：`openclaw config set agents.defaults.model.primary 'ollama/qwen3.6:35b'`
——本地算力叙事 + 不需要在 Spark 放 StepFun key 给 gateway。若机器有 Ollama+Qwen 直接可用；没有就先 `ollama pull qwen3.6:35b`（37.5GB，耗时看带宽，可后台跑）。
**skill 的主脑与 gateway 无关**：repro_pack.py 自己拿 `REPRO_*` 三值调 StepFun。

## 第 3 步 · 装入 skill（训练营 cell 37 配方）

```bash
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME}"   # workshop 用 $OPENCLAW_HOME/.openclaw/…
SKILL_DST="$OPENCLAW_HOME/.openclaw/workspace/skills/repro-pack"
mkdir -p "$SKILL_DST"
# 从本仓（scp / git clone 私有仓）把 skills/repro-pack/ 整目录复制过去：
rsync -a skills/repro-pack/ "$SKILL_DST/"
openclaw gateway restart 2>/dev/null || openclaw gateway start
openclaw skills list            # ⭐ 期待 repro-pack 状态 ready —— 这就是 ISC-6 的证据帧
```

## 第 4 步 · key 注入（二选一，机器属性决定）

- **私有机**：`printf 'REPRO_API_KEY=…\nREPRO_BASE_URL=https://api.stepfun.com/v1\n' > "$SKILL_DST/scripts/.env"`（不入 git）
- **共享机**：不落盘，演示前 `export REPRO_API_KEY=…` 注入 gateway 进程环境，散场 `unset`

## 第 5 步 · 冒烟（按序，前两步不花钱）

```bash
bash "$SKILL_DST/scripts/run.sh" --validate <任一 bugcard.json>   # 零成本：链路/依赖 OK
bash "$SKILL_DST/scripts/run.sh" <一段 30s 小录屏> --out /tmp/smoke --no-issue  # 花一次 token
# 期待末行：PACK:/tmp/smoke/...
```

全过 → 截图/终端输出存 `evidence/d3/`，ISC-6 关闭。任何一步卡住：`skills list` 的警告多半是 `requires.bins`（python3/bash/ffmpeg 缺谁装谁）。

## 已知未知（连上后再钉）

- OpenClaw 配 OpenAI 兼容 provider 的确切语法（本剧本不需要它，gateway 走本地 Qwen；仅当 Qwen 拉模型太慢才回来查 docs.openclaw.ai）
- GB10 上 GPU 状态工具名（nvidia-smi 或 dmesg）
