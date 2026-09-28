# SPEC v2 · 供应链控制塔 Agent Skill（FDE 案例转化）

> 2026-09-24 锁定（owner 确认① + R1-R5 修正案生效）。取代 SPEC v1（repro-pack，见 ISA D12）。
> 上游案例：ikatsov/tensor-house · supply-chain/control_center_llm（Apache-2.0，原样快照在 `case/`）。

## Problem Statement

区域零售/小型制造的供应链管理者，日常问的是这类问题：「Portland 的 Italian Roast 还够卖几周？该不该补？找哪个供应商、补多少、总共花多少钱？」答案散在库存表、供应商表、需求预测里。AI 时代这类问句本该一句话得到答案——但 MIT《GenAI Divide》：企业 AI 项目 95% 烧钱无价值，缺的不是模型，是把模型塞进真实业务的**可复用能力包**。范冰《前线部署工程师》开篇的同一判断：FDE 岗位一年涨 7 倍，说明「落地最后一公里」是稀缺能力——而 Skill 正是这一能力可分发、可验证、可安装的形态。

上游案例（FDE 式交付物：program-aided 控制塔）验证了业务形态，但它是一个绑死 Gemini/LangChain/Streamlit 的单体应用。转化命题：把它变成**任何 agent 都能装的技能**。

## Solution

**supply-chain-control-tower skill**——架构反转式转化：

- 原项目：应用内跑 PAL 循环（Gemini 写代码→修→exec）
- 我们：**宿主 agent（OpenClaw@DGX Spark / Claude Code / Codex…）就是 planner/coder/critic**；skill 提供三样东西——**工具 API**（7 个移植函数）、**领域知识与决策规程**（蒸馏自上游 411 行提示词工程）、**输出契约**（结构化补货决策）

装了 skill 的 agent 收到运营问句后：按决策规程调工具链（缺口计算→供应商比价→运费→决策），产出结构化决策 JSON；库存充足时明确 NO_REORDER 并给余量依据。**skill 本体零 LLM 调用**——纯确定性、全可测，智力全部来自宿主 agent 的主脑（3.7-flash；换脑=本地 Nemotron 120B，平台适配承重墙 R1）。

配套 evals 层：{裸 agent, 带 skill} × {3.7-flash, 本地 Nemotron} 四象限任务集实测 → BENCHMARK.md——NVIDIA Tier-3 哲学的社区化实践。

## User Stories

1. 作为供应链经理，我问「Portland 的 Italian Roast 够卖几周」，agent 调 `stock_demand_difference` 给出缺口与周数，所以我不用翻表。
2. 作为供应链经理，我问「该补多少找谁补、总成本多少」，skill 规程引导 agent 走完 缺口→`query_suppliers` 比价（含 `get_shipping_cost`）→结构化建议单，所以我拿到的是决策不是数据。
3. 作为供应链经理，库存充足时我问「要不要补货」，agent 明确说不需要并给余量数字，**绝不编造补货建议**（负例零误触）。
4. 作为评委，我 clone 仓库 `npx skills add` 后用自己的问句在 OpenClaw 里复现，所以我相信它真的能跑。
5. 作为观众，我在演示视频看到同一问句由云端 3.7-flash 与本地 120B 各答一遍、BENCHMARK 四象限对照，所以我看到「换脑三值」与本地算力的价值。
6. 作为评测者，我一键跑 runner，正例命中金答案（工具直算）、负例零误触、延迟成本全统计，所以 skill 的价值有数字。
7. 作为开源社区开发者，我在 README 看到透明的案例引用（Apache-2.0 + 署名）与转化说明，所以我认可这是转化不是搬运。
8. 作为经理，我要图表，agent 用 `show_line_chart` 输出 52 周预测线图。
9. 作为 agent，我写错 SQL 时工具报错信息可读可自纠（上游 critic 环节精神的延续）。
10. 作为演示者，Streamlit 塔台可作人看证据面板（R2：可牺牲项，超 4h 降级）。

## Implementation Decisions

- **架构反转**：无内嵌 LLM（砍 `langchain_google_genai`/LangChain 全链）；skill = 工具+知识+契约；智能在宿主 agent（MCP 管连接、skill 管知识、harness 管调度）
- **7 工具移植**（`scripts/tools/`）：`query_inventory/query_suppliers`（CSV→内存 SQLite，pandas+sqlite3）、`get_forecast`（**hash→zlib.crc32 稳定化**，修复上游不可复现 bug）、`stock_demand_difference`、`get_shipping_cost`、知识检索改为 `references/supply-chain-knowledge.md` 供 agent 直读（替代上游 LLM Searcher）、输出三件套（print_answer/print_table/show_line_chart）
- **SKILL.md 渐进披露**：frontmatter（触发词+负触发+OpenClaw metadata bins）；正文=问句分类+补货决策 SOP；references=api 文档（上游 docstring 直接复用）+知识文档
- **输出契约**：正例=`{"decision","order_qty","supplier","unit_cost","shipping_cost","total_cost","rationale","tool_trace"}`；负例=末行 `NO_REORDER:<余量周数>`
- **主脑**：OpenClaw gateway 配 3.7-flash（OpenAI 兼容 provider，key 运行时注入不落盘）；换脑素材=本地 `nemotron-3-super-120b`（R1 必选、演示最后一幕）
- **evals runner**：headless harness（问句+±SKILL.md 上下文→LLM→判定），四象限一次跑完；OpenClaw 现场演示为人工证据层
- **Streamlit 塔台**（R2）：原样适配优先，超 4 小时降级为 demo 录屏
- **数据**：上游咖啡数据集原样（4 SKU×2 仓+供应商表）；万行级扩容= P1
- **透明引用**（R4）：README 署名上游 + 修改点清单

## Testing Decisions

- 只测外部行为（问句→最终答案），不测 skill 内部实现
- **金答案由工具函数直算**（不经 LLM）——决策数值数学唯一
- 负例判定：充足库存问句 → 必须含 `NO_REORDER` 且不得含补货建议
- 工具选择判定：`tool_trace` 缺正确工具链即错（如补货决策未调 `stock_demand_difference`）
- 阈值：正例命中 ≥70%（3.7-flash 带 skill）才算达标；负例误触 = 0（P0）
- 四象限跑 3 轮取中位，记录质量/延迟/token

## Out of Scope

真实预测模型（保留确定性合成预测）· 多级库存网络 · 真实供应商数据 · cuDF 加速（P1）· Streamlit 重设计 · 移动端 · 多语言 · 安全接入端点（P2 立碑）

## Further Notes

- R1-R5 修正案全文：`docs/topic-deepdive/00-plan-verdict.md`
- 发布排雷清单（R5）：征文/B站视频标注 AI 生成 · Apache-2.0+署名 · key 零提交（已验证）· 合影（owner 决定留痕）· 500 字 README 结构对赛规
- 冻结 9/26 晚 v0.1.0 · 发布 9/28（push 需 owner 点头）· 提交 9/29 12:00 前
