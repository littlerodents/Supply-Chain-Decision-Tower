# supply-chain-control-tower · 把 FDE 行业案例转化为 Agent Skill

> 第三届 NVIDIA DGX Spark 黑客松 · Agent Skills 开发挑战赛 参赛作品
> Evander · abloom25 · alingalingling ｜ 2026-09

## 一、作品说明

**一句话**：把一个真实的 FDE（前线部署工程师）行业落地案例——供应链控制塔——转化为**任何 agent 一装即用的技能包**：运营者一句自然语言（「San Francisco 的 Colombian 未来 12 周够卖吗？不够补多少、找谁、总成本多少？」），agent 查库存、算缺口、比供应商、算运费，产出结构化补货决策单；库存充足时明确回答**不需要补货**，绝不编造建议。

**为什么值得做**：MIT NANDA 实验室《The GenAI Divide》——企业 AI 项目 95% 没有产生可入报表的价值；同期 FDE（Forward Deployed Engineer）岗位需求一年涨 7 倍（范冰《前线部署工程师》）。诊断是一致的：模型不稀缺，稀缺的是**把模型塞进真实业务、且能沉淀为可分发资产的能力**。Skill 正是这种能力的载体——这正是本次赛题「Agent Skills 开发挑战赛」的题眼。

**核心亮点**：
1. **架构反转式转化**（不是搬运）：上游案例 `control_center_llm` 是一个绑死 Gemini/LangChain/Streamlit 的单体应用；我们把其中的「LLM 写代码再执行」反转为**宿主 agent 本身担任 planner/coder/critic，skill 只提供工具 API + 领域知识 + 输出契约，本体零 LLM 调用**——纯确定性、全可测、模型无关（换脑三值即可切换主脑）。
2. **转化即修复**：移植中实测修复上游三处 bug——`hash()` 跨进程不稳定导致预测/运费不可复现（×2，改 `zlib.crc32`）、solver 的 f-string 双花括号导致 SQL 恒查空、库存恒为 0（改参数化查询）。每处都有回归测试锁死（`tests/test_tools.py`）。
3. **带数学底座的评测层**：12 题任务集（8 正 + 3 负例 + 1 无关），金答案由工具函数**直算**（零人工标注）；负例红线 = 库存充足时必须 `NO_REORDER`，零误触。
4. **四象限 BENCHMARK**（NVIDIA Tier-3 评测哲学的社区化实践）：{裸 prompt, +skill} × {StepFun 3.7-flash, 本地 Nemotron 120B} 实测——**裸 2/12（16.7%）×2 vs 带 skill 12/12（100%）×2**：两颗架构迥异的脑子以同样姿势翻车、又双双满贯——skill 才是能力的载体，主脑只是引擎。负例零误触全线通过，全部轮次数据公开（含波动，见 `benchmark/BENCHMARK.md`）。

**技术实现与架构**：skill 含 7 个工具（库存/供应商 SQL 查询、52 周需求预测、库存-需求缺口、运费、知识直读、图表输出），CSV → 内存 SQLite，pandas + numpy + 标准库，无重依赖；SKILL.md 按渐进披露设计（frontmatter 触发词 + 负触发 + OpenClaw 元数据，正文为问句分类与补货决策 SOP，细节下沉 `references/`）；输出契约为八字段决策 JSON（含 `tool_trace` 工具链留痕）。评测 runner 实现迷你 agent 循环（模型输出 bash → 白名单执行 → 结果回传 → ≤8 轮），一条命令复现全部象限。工程过程遵循 SDD：SPEC → 工单 → 可证伪验收（14 条 ISC，10 条已关，每条附真实运行证据，见 `ISA.md`）。

## 二、部署说明（本地算力 × 智能体 × 大模型）

- **平台**：DGX Spark（GB10 Grace Blackwell，119Gi 统一内存，租用 4T 版）。OpenClaw 2026.9.5 部署于其上（官方安装器，Node 26 运行时），skill 装入 workspace（`openclaw skills list` → ✓ ready）。
- **本地算力的三个用途**：① OpenClaw gateway 与 agent 运行时跑在 Spark；② **NVIDIA 开源模型 Nemotron-3-Super-120B-A12B（MoE，87GB）本地部署**（Ollama），既作 gateway 主脑（真问句三轮演示：发现 skill → 工具取证 → 八字段决策 JSON），又作评测象限（全程 33 次工具链调用零失败）；③ 零 LLM 证据面板（Streamlit :8501）——库存/缺口/预测全部由 skill 工具层直算，塔台的「人看证据层」。
- **大模型优化口径（诚实声明）**：不做微调。优化 = ①选型对比（3.7-flash vs step-5-preview vs 本地 120B，同任务实测定主备）②评测驱动（四象限 + 方差公开，发现「触发≠遵守」问题并以 SKILL.md 硬规则修复：无规则版 10-11/12 → 硬规则版 12/12）③换脑三值（base_url/model/api_key）实现能力资产与厂商解耦。
- **Agent Skills 设计**：如上「核心亮点 1」，全部设计文件在 `skills/supply-chain-control-tower/`（[SKILL.md](skills/supply-chain-control-tower/SKILL.md) 即赛题要求的 skill markdown）。

## 三、技术栈说明

| 层 | 组件 |
|---|---|
| NVIDIA | DGX Spark（GB10 平台/本地算力）；**NVIDIA 开源模型 Nemotron-3-Super-120B-A12B**（本地推理）；OpenClaw on DGX Spark |
| StepFun 阶跃星辰 | **step-3.7-flash（主脑）**；step-5-preview（选型对照，Coding Plan 额度） |
| 其他 | Ollama 0.34.4（ARM64 本地推理）、pandas/numpy/sqlite3（skill 工具层）、Streamlit（证据面板）、pytest（回归锁） |

## 四、快速开始

```bash
git clone <本仓库> && cd <仓库>
npx skills add ./skills/supply-chain-control-tower --yes   # 装进你的 agent（Claude Code/Codex/Copilot/OpenCode/Warp/OpenClaw）
python3 skills/supply-chain-control-tower/scripts/tools.py gap --sku 13001 --location "San Francisco" --weeks 12
# → {"current_stock":30, "forecast_demand":3298, "gap_stock_minus_demand":-3268, ...}
python3 tools/run_evals.py --brain stepfun --context skill  # 一键复现评测象限（需 REPRO_API_KEY 等三值环境变量）
```

## 透明引用与致谢

- 本作品转化自 **ikatsov/tensor-house**（Apache-2.0）之 `supply-chain/control_center_llm` 子项目，原样快照见 `case/`（含 ATTRIBUTION），我们的转化与修复清单见上文与 `docs/N1-VERDICT.md`。感谢原作者的开源工作。
- 叙事素材引自范冰《前线部署工程师》（免费公开）与 MIT NANDA《The GenAI Divide》报告。
- 本 README 与仓内文档由 AI（pi + StepFun/Anthropic 模型）协作生成，按平台规范标注。

## 发布合规自检清单（排雷）

- [x] 仓库零密钥（`grep` 终检通过；凭据仅存本地环境变量，不提交）
- [x] Apache-2.0 上游署名与修改点声明
- [x] AI 生成内容标注（本 README、B 站视频描述、CSDN/知乎征文发布时同步标注）
- [x] 赛规四节说明齐备（本文件第一~三节 + SKILL.md 链接）
- [ ] 团队合影（提交前完成）
- [ ] B 站演示视频 URL / 征文 URL（提交表单时填入）

## 更多

评测方法与全部数据：`benchmark/BENCHMARK.md` ｜ 决策过程与验收台账：`ISA.md` ｜ 部署实录：`evidence/d3/OPENCLAW-DEMO.md`（本地证据目录）｜ 选题研究：`docs/TOPIC-RESEARCH.md`、`docs/topic-deepdive/`
