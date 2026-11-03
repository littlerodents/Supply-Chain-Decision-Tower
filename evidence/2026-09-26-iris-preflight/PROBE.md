# 2026-09-26 · DGX 主机与 Iris 前置试验（PARTIAL）

> 本轮经 owner 已登录的 macOS Terminal SSH 会话操作，同一条通道复用；未在命令/文件中写 SSH 口令。租机管理员提示 SSH 通道上限 64，勿动固件。`evidence/` 被 gitignore，此记录不会自动出现在私仓。

## ANCHOR / 失败门

DONE：①隔离条件满足；②在 DGX 上能运行 Iris-mini 搜索模型并留下搜索出处→控制塔工具输入→决策的真实轨迹；③同题、同权限单 agent 与串接版能对照成本、正确性、延迟；④真实 OpenClaw 入口决策严格满足金答案、负例不误补。未跑到最终入口不算 DONE。

失败门：远程不可达/身份不明；权重或依赖取不到；与现有 120B 并跑 OOM；搜索缺凭据或证据不入决策；OpenClaw 自身在真实入口不会产出完整决策。

## 新鲜直接观察

- 复用主人已登录的 Terminal（`spark-5c72`），`uname -m` → `aarch64`；`free -h` → 119Gi 总内存、约 114Gi 可用（测时）；`df -h / /home` → 2.9T 总量、2.7T 可用。`nvidia-smi` 仅给 NVIDIA GB10，集成内存栏 N/A。
- 端口：Ollama 11434（loopback）、OpenClaw 3030、Streamlit 8501 在监听；OpenClaw CLI 已安装、控制塔 SKILL.md 已在 workspace。Ollama `/api/ps` → 当前加载模型 `[]`；`/api/tags` → `nemotron-3-super:120b-a12b`（磁盘大小约 80.9Gi）。**这是空闲时资源快照，不能推出 Iris 与 Nemotron 可同时加载**。
- 受检的 `~/Iris`、`~/iris`、标准 Hugging Face Iris-mini 模型缓存路径均不存在；系统 `python3` 未找到 `torch` / `transformers` / `vllm` / `huggingface_hub`；并非穷尽所有虚拟环境。
- 官方权重 URL（Hugging Face `AllSpark-Research/Iris-mini` 的 config.json）：Mac 及 DGX 均连接超时（HTTP 000）；GitHub 官方 `Iris-Harness/README.md` 在 DGX 可达（HTTP 200）。官方 README 说明 Harness 不启动模型，须自备 OpenAI-compatible 服务、`SERPER_API_KEY`、网页摘要模型及 judge；论文成绩来自单 agent ReAct 搜索，不是本项目双 agent 性能证明。未改网络配置、未绕官方来源下载权重、未配置任何搜索或评判凭据。
- 用 OpenClaw Gateway 同一新会话 `pi-dgx-20260926-pos1` 问 `San Francisco 仓库 SKU 13001 未来 12 周够卖吗...`（不带输出枚举答案、不投递消息、不真实下单）：第一次 `--json` 退出 0，`status=ok`，用时 **116239ms**，`toolSummary.calls=9`、失败 3；**最终仅说需要检查运费**，未交付决策 JSON。追问「继续完成上一问」后第二次退出 0，`status=ok`，用时 **355810ms**，`toolSummary.calls=73`、失败 2；**最终仅说准备直接调用 shipping 命令**，仍没有决策 JSON。两轮总共 82 次工具调用、约 472 秒，未通过 ISC-14/主人入口；CLI exit 0 / status ok 不代表业务成功。服务器原始响应在用户目录 `/tmp/pi-dgx-pos1.json`、`/tmp/pi-dgx-pos1-turn2.json`（仅本机临时证据，未外传）。
- 红队证伪：**不是工具本身不能算**。在同一 DGX 直接执行 `python3 ~/.openclaw/workspace/skills/supply-chain-control-tower/scripts/tools.py shipping --source Seattle --destination 'San Francisco'` → 运费 2.0；`gap --sku 13001 --location 'San Francisco' --weeks 12` → 缺口 -3268、库存 30。对照本地 `gold.json` 的 119282：模型/Agent 的入口执行与输出仍需修复，不能用工具层绿灯代替。

## 主链最小修复试验（未通过主人入口，已回滚远端）

- 用 OpenClaw 内建 `sessions export-trajectory` **仅导出本轮会话的脱敏轨迹**（远端 `~/.openclaw/trajectory-exports/pi-dgx-debug-20260926/`、`pi-dgx-debug-pos2-20260926/`、`pi-dgx-debug-path-20260926/`，未公开）。第一次两轮可见 skill 被误当 callable tool、误找 `/home/parker`（实际系统为 `/home/sparker`）、exec 命令未找到；非 shipping 算法坏掉。
- 本地新增 `tests/test_skill_entrypoint.py`：从非 skill 工作目录运行 SKILL 中的 OpenClaw 工具示例，并核对示例金答案。改前 `2 failed`：相对路径找不到 `scripts/tools.py`、示例总价 119284≠119282；本地 `SKILL.md` 改为 OpenClaw 绝对脚本路径并修正示例后，连同既有回归 `9 passed, 3 xfailed`。
- 远端 SKILL.md 改前 SHA256 `ed2e5b...` 与本地原稿一致；临时原子部署修订版 SHA256 `a6b4d1...` 并在远端从 `/tmp` 直跑 shipping=2.0、`openclaw skills list --eligible` 仍 `✓ ready`。**主人入口同问句新会话** `pi-dgx-20260926-pos2`：CLI `status=ok`，134355ms，12 次工具调用、5 次失败，最终仍只说“需要查运费”，没有决策 JSON；因此最小文档修复**不解决**主问题。
- 脱敏轨迹中该新会话的失败为 `tool_describe` 将 skill 当工具、`read/ls` 反复访问不存在的 `/home/parker/...`；就算在诊断问句中明确告诉模型正确路径，另一新会话（112688ms、19 次工具调用、11 次失败）仍请求 `/home/parker/...`，只说要查看 workspace。`openclaw config get agents.defaults.workspace` 实测为 `/home/sparker/.openclaw/workspace`。这证明宿主路径已正确配置、模型/工具使用仍跑偏；**不能断言只改 SKILL 文本已修复**。
- 远端用原件备份按 SHA 前置校验原子恢复 SKILL.md，SHA 回到 `ed2e5b...`；Gateway/120B/面板未重启，本轮未发布。**本地** `SKILL.md` 与新增测试仍为未提交候选，只有内部绿灯，不可宣传为已交付主入口；既有 `tools/run_evals.py` 的实验改动未触碰。

## 后续门槛（未执行）

1. 先控制塔入口修复：调查为何 Agent 反复找 shipping 路径却未完成，确保正例严格 JSON、总价直算、负例 NO_REORDER。新鲜再跑主人入口才可说修复成功。
2. Iris 仅在权重官方来源可达、ARM64/GB10 serving 方案可实装、具有独立搜索/摘要/评判凭据且不挤占 120B 时，再在独立路径和端口试装；不可把下载依赖、HTTP 存活或 mock 搜索叫作协同。
3. 对照实验须等数据/工具权限，并报告失败轮、负例、token/延迟；单轮改善不宣称稳定的“1+1>2”。旧 9/26 冻结与会议 9/27 完整版仍冲突，未擅自改时间基线。
