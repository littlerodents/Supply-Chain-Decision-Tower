# REBUILD.md：换一台 DGX Spark 怎么复原这套系统

> 2026-09-29 租赁机到期前留档。按此文档可在新机器上复原全部能力。

## 仓库结构 ↔ 运行时位置

| 仓库路径 | 运行时位置（DGX Spark） |
|---|---|
| `skill/` | `~/.openclaw/workspace/skills/supply-chain-control-tower/` |
| `skill-audit/` | `~/.openclaw/workspace/skills/supply-chain-audit/` |
| `skill/data/` | 同名数据文件（CSV/JSON，含 SQLite 若有） |
| `evidence/` | 评测与测试证据（只读存档，无需部署） |

## 复原步骤

1. **Node + OpenClaw**：装 Node 26 到 `~/node26`，OpenClaw CLI 在 `~/node26/bin/openclaw`。非交互 ssh 必须 `export PATH=$HOME/node26/bin:$PATH`（面板里跑 agent 子进程也是同一坑，`panel/app.py` 的 `run_agent()` 已内置 PATH 注入）。
2. **网关**：systemd 用户服务 `openclaw-gateway.service`（端口 3030）。drop-in 需设 `OLLAMA_API_KEY=任意值`（本地 ollama 必需但校验为空）。单元文件在本机 `~/.config/systemd/user/`，也在私有档案 tar 里。
3. **模型**（ollama 在 `~/ollama/bin`）：
   - `nemotron-3-super:120b-a12b`（86GB）——本地推理主力。ollama 官方源仅 2.2MB/s，**走 ModelScope（实测 24MB/s）**拉 GGUF 再 `ollama create` 导入。
   - **推荐建 t0 变体**（temperature=0 烤入，实测工具调用更稳）：`ollama show nemotron-3-super:120b-a12b --modelfile > /tmp/n.modelfile`，把 `PARAMETER temperature 1` 改 0，`ollama create nemotron-3-super:120b-a12b-t0 -f /tmp/n.modelfile`（复用权重 blob，分钟级）。网关默认指到 t0。
   - 云端可选路由：StepFun step-3.7-flash（key 走 `openclaw models auth`，**旧 key 已在聊天暴露，必须轮换后重新入库**）。
   - 默认路由切换：`openclaw config set agents.defaults.model.primary <模型>`（热加载，无需重启网关；设 ollama 模型需 `OLLAMA_API_KEY=任意值` 环境变量）。
4. **技能**：按上表把 `skill/` 与 `skill-audit/` 拷进 workspace/skills/。**SKILL.md 是冻结协议，改动必须有变更流程**（本项目发生过队友覆盖 SKILL.md 导致全部 live 会话 UNPROVEN 的事故，见 docs/journey/02-failures.md）。
5. **服务栈**（同一台机器）：
   - API：`skill/panel/api_server.py`，端口 8765（前端 :5173 的 `/api` 代理指向它）
   - 面板：`skill/panel/app.py`，`python3 -m streamlit run app.py --server.port 8501`
   - 前端：fieldwork-frontend（GitHub: abloom25/fieldwork-frontend），vite dev :5173
6. **验证**：`python3 skill/evals/test_suite.py`（17 项全绿）+ `python3 evidence/mcp_demo.py`（7 工具全通）。

## 已知坑（都是本项目踩过的）

- **120B 裸 CLI 的 SOP 遵守不稳**（反问澄清/订量口径漂移到裸缺口）——产品路径因此走 API live 模式：**适配器按工具直算签发八字段契约（ROP 口径），模型未出单时兜底签发；审计智能体输出不可解析时按零 LLM 确定性对账判定**。这套兜底 9/29 实测 PASS（REORDER 359.4 / Nature Source / 13118.1）。单环推理 2-7 分钟，AGENT_TIMEOUT 需 ≥600s。
- SKILL.md 示例必须锚定 ROP 口径（359.4/13118.1）；曾因新旧两套订量指令并存导致模型口径漂移。
- Streamlit 页面在 agent 响应期间点击会取消渲染——app.py 已用 session_state 恢复机制修复，别回退。
- gap 语义：`rop_gap`（ROP−库存）与遗留字段 `gap_stock_minus_demand`（库存−需求）符号相反，API 两个字段都返回，别混用。
- NVFP4/148B 在 aarch64 上 vLLM 起不来（Triton GCC 编译失败），要本地大模型走 ollama GGUF 路线；TensorRT-LLM 是部署后课题。
- 杀进程别用 `pkill -f`（命令串自匹配会自杀），用 PID 文件。

## 不随机器保留的东西

- 模型权重（86GB/101GB）——可重新拉取，不值得传输。
- `/tmp` 下会话 JSON——关键证据已入 `evidence/`。
- StepFun key——反正要轮换。
