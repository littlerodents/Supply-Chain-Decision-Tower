# N1 判决书 · processors 覆盖面实测（2026-09-24）

> 对照 `topic-deepdive/01` 的 P0 风险：「program_aided 的覆盖面 UNPROVEN」。判决基于克隆实测（源码逐文件读过），非推测。

## 判决：GO——覆盖面超出预期一个量级，② 备胎解除待命

## 实测清单

**架构**：完整 program-aided agent 流水线（非散 notebook）
- 5 段循环：`create_standalone_query → create_logic(planner) → create_script(coder) → fix_script(critic) → execute_script(exec 沙箱)`
- 4 份提示词工程文件共 411 行（chat/planner/coder/critic）——SKILL.md references 的直接原料
- Streamlit 应用 84 行把五段渲染成「Chat manager / Software engineer ×2 / Technical lead / Final answer」对话——UI 叙事现成

**7 个文档化工具**（api.py docstring 即 API 文档，SKILL.md 可直接引用）：

| 工具 | 作用 | evals 价值 |
|---|---|---|
| `query_inventory(sql)` | INVENTORY(sku,brand,location,quantity) 内存 SQLite | SQL 正确性可判 |
| `query_suppliers(sql)` | SUPPLIERS(sku,supplier,location,unit_cost) | 同上 |
| `get_forecast(sku,location)` | 52 周需求预测（合成正弦） | 确定性 |
| `stock_demand_difference(sku,location,weeks)` | **库存-需求缺口 = 补货决策原语** | **金答案直接可算** |
| `get_shipping_cost(src,dst)` | 单件运费 | 确定性 |
| `search_documents(q)` | 供应链知识检索（原为 LLM 检索） | 我们改为 agent 直读知识文档（上下文工程，更简） |
| `print_answer/print_table/show_line_chart` | 输出三件套 | 输出契约素材 |

**依赖面（移植后）**：pandas + numpy + sqlite3（stdlib）——LLM 依赖仅 `utilities.get_llm` 一处（langchain_google_genai），整体砍除。

## 架构反转（N2 SPEC 的核心决策）

原项目：Streamlit 应用内跑 PAL 循环（Gemini 写代码→修代码→exec）。
我们的 skill 化：**宿主 agent（OpenClaw@Spark，主脑 3.7-flash，换脑=本地 Nemotron 120B）本身就是 planner/coder/critic**——skill 只提供：工具 API（scripts/）+ 领域知识与决策规程（SKILL.md + references/）+ 输出契约 + evals。
这正是「MCP 管连接、skill 管知识、harness 管调度」的架构叙事（周旭讲义）——转化即升级，不是搬运。

## 移植期顺手抓到的两个 bug（上游问题，我们的修正义务）

1. `forecast.py` 用 `hash(sku)` 做种子——**Python 哈希跨进程随机，预测不可复现** → 移植时换 `zlib.crc32`，gold 答案才稳定
2. `tools/*.py` import `streamlit.logger`——非 UI 文件偷依赖 streamlit → 移植时换标准 logging

## 遗产并入

- 上游原样代码入仓 `case/control_center_llm/`（Apache-2.0，ATTRIBUTION 注明来源与修改点）
- prompt 四件套蒸馏进 `skills/…/references/`（planner 里的决策规程 = skill 的领域知识）
