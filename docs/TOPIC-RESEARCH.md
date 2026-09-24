# TOPIC-RESEARCH · FDE 案例→Skill 选题研究（DFS+BFS 双路）

> 2026-09-24 · Round 1 搜索成果。标注口径 = 官方评分：实用性/落地25 · 技术深度25 · 完整性20 · 平台适配15 · 演示10 · 征文5

## DFS · 范冰《前线部署工程师》第 8 章（owner 指定源）

案例为**公司叙事，不可直接跑**——用途是方法论骨架 + 真痛点证据，不是 skill 原料：

- **8.1 Palantir**：二十年「笨办法」炼护城河（战场/飓风/油田 + 方法论还原）
- **8.2 OpenAI**：约翰迪尔农田、BBVA 十二万人（「部署即战略」）
- **8.3 四种变奏**：Anthropic 可审计 / Sierra·Decagon 交付即产品 / Harvey 高壁垒 / Databricks·Snowflake 嵌入式
- **8.4 中国案例**：火山引擎、华为、180 天创业实战全复盘
- **开篇即最佳 README 引言素材**：MIT《GenAI Divide》——企业 AI 项目 95% 无财务价值 + FDE 岗位年涨 7 倍 =「真痛点」一句话成立

## BFS · 可跑案例池（skill 的真正原料）

| 候选 | 是什么 | 可跑性 | 评分锚定初判 |
|---|---|---|---|
| **`ikatsov/tensor-house`** | 企业 AI notebook：**营销/定价/供应链/制造**四个行业域 | ⭐高（notebook 即跑） | **实用性25 强**——真行业落地+可演示；深度25 取决于选哪个域 |
| `muratcankoylan/AI-Investigator` | 企业调研→报告生成系统 | 中高 | 实用性中；演示形态好（输入→报告） |
| `NirDiamant/GenAI_Agents` | 50+ agent 技法实现库 | 高 | 技法原料库，适合抽 1 个行业技法包装 |
| `patchy631/ai-engineering-hub` | agents/RAG/LLM 实战教程仓 | 高 | 同上，量大需筛 |
| `databricks/databricks-agent-skills` / `google/agents-cli` | **「案例→skill」包装先例** | — | 格式合规路径参考（不抄内容） |
| `suboss87/FDEOps`（★903） | FDE 工程实践已打包成 agent skills | — | **撞车警示**：做「FDE 方法论 skill」会撞它；做具体行业案例（A 层）不撞 |

## 形态裁决（owner 已定 A 层）

- **A 工作流程层 = 主**：案例里「FDE 替行业干的活」→ agent 按步骤执行的 skill
- B 交付物层：并进 A 的输出契约（终点即交付物），不单列
- C 方法论层：**砍**——FDEOps 已占位（★903 撞车）+ 书全文免费公开（转述=二道贩子）+ 3 天窗口一道菜都紧

## 模型对比（进行中）

| | step-3.7-flash | nemotron-3-super-120b-a12b |
|---|---|---|
| 结构化 FDE 任务（需求→JSON） | **JSON 一次成型**，5.1–5.8s，内容合格 ×2 runs | NIM API **403**（key 缺服务组） |
| 定位 | 现任主脑，基线已立 | MoE 120B 总参/12B 激活——会上指定对比对象 |
| 本地可行性 | —（闭源 API） | Ollama Q4 ≈60–70GB，租机 119Gi **放得下**（若 API 对比赢→演示本地部署=平台适配 15% 满配） |

**对比结果（2026-09-24 实测，租机本地 head-to-head，同一 FDE 结构化任务 ×3 runs）**：

| | step-3.7-flash（云端） | nemotron-3-super-120b-a12b（**GB10 本地**） |
|---|---|---|
| 质量（五维判分） | **5.0/5 × 3**（满贯零漂移） | 4/5 · 3/5 · 4/5（均值 3.7） |
| 延迟 | 4.8–12.1s（中位 ~6.4s） | 30.6–33.3s（含 thinking 生成） |
| 结论 | **主脑留任**（更强+更稳，owner 判据） | 备脑/本地叙事（见下） |

**本地部署遗产**：nemotron 87GB 已在租机 Ollama 上线（加载 1m13s，serve 正常）——「DGX Spark 本地跑 NVIDIA 开源 120B」= 平台适配 15% 的实物证据 + BENCHMARK 真实 A/B 数据源。NGC key 重生成不再紧急（API 路线已被本地路线替代）。
注：任务为结构化 JSON 输出；nemotron 开 thinking 模式（深度换速度），README 记录时注明口径。

## 待 owner 裁决

1. NGC key 重生成（2 分钟）
2. 池子挑选：建议我 DFS 下钻 `tensor-house`（四个行业域 notebook 清单 → 给你 3 个具体案例供三选一），或你直接点名
