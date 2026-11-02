# supply-chain-control-tower · 把 FDE 行业案例转化为 Agent Skill

> 第三届 NVIDIA DGX Spark 黑客松 · Agent Skills 开发挑战赛 参赛作品
> Evander · abloom25 · alingalingling ｜ 2026-09

## 一、作品说明

**一句话**：把 FDE（前线部署工程师）的供应链控制塔案例转化为可安装的 Agent Skill：提供库存、预测、供应商、运费工具和结构化补货决策规程；库存充足时应明确回答**不需要补货**。截至 2026-09-26，DGX OpenClaw 真入口尚未稳定按契约出单，不能承诺「一装即用」。

**为什么值得做**：MIT NANDA 实验室《The GenAI Divide》——企业 AI 项目 95% 没有产生可入报表的价值；同期 FDE（Forward Deployed Engineer）岗位需求一年涨 7 倍（范冰《前线部署工程师》）。诊断是一致的：模型不稀缺，稀缺的是**把模型塞进真实业务、且能沉淀为可分发资产的能力**。Skill 正是这种能力的载体——这正是本次赛题「Agent Skills 开发挑战赛」的题眼。

**核心亮点**：
1. **工具与规程分离**：上游 `control_center_llm` 依赖 Gemini/LangChain/Streamlit；本项目把业务工具、领域知识和决策规程整理为 Skill，本体不调用 LLM。工具层可确定性测试；宿主 agent 的自动调用、输出契约和跨模型稳定性**不能由这个结构直接证明**。
2. **转化即修复**：移植中实测修复上游三处 bug——`hash()` 跨进程不稳定导致预测/运费不可复现（×2，改 `zlib.crc32`）、solver 的 f-string 双花括号导致 SQL 恒查空、库存恒为 0（改参数化查询）。每处都有回归测试锁死（`tests/test_tools.py`）。
3. **带数学底座的评测层**：12 题任务集（8 正 + 3 负例 + 1 无关），金答案由工具函数**直算**（零人工标注）；负例红线 = 库存充足时必须 `NO_REORDER`，零误触。
4. **有波动的评测记录**：已有裸组 2/12×2、Nemotron +skill 三轮 **12/12、9/12、11/12**；StepFun +skill 留存一轮 10/12，原 12 题满分文件已被未验收审计试验覆盖。裸组与带 Skill 组工具/数据权限不等，不能由此证明因果增益或稳定性；原始证据在被 gitignore 的本地 `evidence/`，见 `benchmark/BENCHMARK.md`。

**技术实现与架构**：skill 提供库存/供应商查询、预测、缺口、运费、知识直读和图表等工具，CSV → 内存 SQLite，使用 pandas/numpy/标准库；SKILL.md 定义触发范围、决策 SOP 和结构化输出契约（含 `tool_trace`）。评测 runner 有迷你 agent 循环，但本地评测**不能替代** OpenClaw 真入口。项目以 SPEC → 工单 → 可证伪验收留痕；初始工具开发未做到测试先行，14 条 ISC 目前 **9 条勾选**，不等于主人入口验收通过（见 `ISA.md`）。

## 二、部署说明（本地算力 × 智能体 × 大模型）

- **平台**：DGX Spark（GB10 Grace Blackwell，119Gi 统一内存，租用 4T 版）。OpenClaw 2026.9.5 部署于其上（官方安装器，Node 26 运行时），skill 装入 workspace（`openclaw skills list` → ✓ ready）。
- **本地算力用途与限制**：OpenClaw Gateway、Ollama 中的 Nemotron-3-Super-120B-A12B、零 LLM 的 Streamlit 证据面板均部署在 DGX Spark。历史对话可作排障素材；2026-09-26 新鲜真入口复跑时，普通问句未产决策 JSON；用 `$supply-chain-control-tower` 显式引用的正例只产正确数字的 Markdown，负例也未产 `NO_REORDER`。`skills list ✓ ready`、HTTP 200 和模型已下载都不是业务验收。
- **模型口径**：未微调，未验证 NVIDIA SDK 接入，也未部署 Iris。已有模型选型、四象限评测及换脑素材；样本与工具权限不等、模型结果有波动，不能称「1+1>2」或稳定性能提升。
- **Agent Skills 设计**：如上「核心亮点 1」，全部设计文件在 `skills/supply-chain-control-tower/`（[SKILL.md](skills/supply-chain-control-tower/SKILL.md) 即赛题要求的 skill markdown）。

## 三、技术栈说明

| 层 | 组件 |
|---|---|
| NVIDIA | DGX Spark（GB10 平台/本地算力）；**NVIDIA 开源模型 Nemotron-3-Super-120B-A12B**（本地推理）；OpenClaw on DGX Spark |
| StepFun 阶跃星辰 | step-3.7-flash（runner 评测与历史素材；当前 DGX OpenClaw Gateway 未配置为此模型）；step-5-preview（历史选型对照） |
| 其他 | Ollama 0.34.4（ARM64 本地推理）、pandas/numpy/sqlite3（skill 工具层）、Streamlit（证据面板）、pytest（回归锁） |

## 四、快速开始

```bash
git clone <本仓库> && cd <仓库>
npx skills add ./skills/supply-chain-control-tower --yes   # 装进你的 agent（Claude Code/Codex/Copilot/OpenCode/Warp/OpenClaw）
python3 skills/supply-chain-control-tower/scripts/tools.py gap --sku 13001 --location "San Francisco" --weeks 12
# → {"current_stock":30, "forecast_demand":3298, "gap_stock_minus_demand":-3268, ...}
python3 -m pytest tests/test_tools.py -q  # 已入仓工具回归；非 OpenClaw 真入口验收
```

## 透明引用与致谢

- 本作品转化自 **ikatsov/tensor-house**（Apache-2.0）之 `supply-chain/control_center_llm` 子项目，原样快照见 `case/`（含 ATTRIBUTION），我们的转化与修复清单见上文与 `docs/N1-VERDICT.md`。感谢原作者的开源工作。
- 叙事素材引自范冰《前线部署工程师》（免费公开）与 MIT NANDA《The GenAI Divide》报告。
- 本 README 与仓内文档由 AI（pi + StepFun/Anthropic 模型）协作生成，按平台规范标注。

## 发布合规自检清单（排雷）

- [ ] 公开前复检工作树和 Git 历史是否含密钥；已在聊天暴露的 SSH 口令须轮换，不得入库
- [x] Apache-2.0 上游署名与修改点声明
- [x] AI 生成内容标注（本 README、B 站视频描述、CSDN/知乎征文发布时同步标注）
- [x] 赛规四节说明齐备（本文件第一~三节 + SKILL.md 链接）
- [ ] 团队合影（提交前完成）
- [ ] B 站演示视频 URL / 征文 URL（提交表单时填入）

## 更多

评测方法与可得数据边界：`benchmark/BENCHMARK.md` ｜ 决策/阻塞台账：`ISA.md` ｜ 真入口失败记录：`evidence/2026-09-26-iris-preflight/PROBE.md`（本地忽略目录）｜ 选题研究：`docs/TOPIC-RESEARCH.md`、`docs/topic-deepdive/`
