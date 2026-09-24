# CONTEXT · repro-pack 领域语言（v2 · 控制塔时期）

> 让 agent 和人用同一套词。v1（repro-pack 时期）术语已归档到文末。

| 术语 | 含义 | 排除 |
|---|---|---|
| **架构反转** | 上游让 LLM 在应用内写代码（PAL）；我们让宿主 agent 当 planner/coder/critic，skill 只给工具+知识+契约，**skill 本体零 LLM** | 不是把上游代码包一层 |
| **控制塔 skill** | supply-chain-control-tower：自然语言运营问句 → 工具链查证 → 结构化补货决策 | 不是聊天机器人 |
| **缺口（gap）** | `stock = 库存 - N 周预测需求`；负=短缺需补，正=充足不补 | 不是增长率 |
| **决策 JSON** | 正例输出契约八字段（decision/order_qty/supplier/unit_cost/shipping_cost/total_cost/rationale/tool_trace） | 自由文本散文=违约 |
| **NO_REORDER** | 负例末行契约：`NO_REORDER:<正gap>`，禁止任何补货建议 | 「建议少量备货」也算误触 |
| **金答案直算** | evals 的 gold 由 tools.py 绕过 LLM 直接计算——数学唯一，不许手填 | 人工标注数字 |
| **四象限** | {裸 agent, +skill} × {3.7-flash, 本地 Nemotron} 的 BENCHMARK 矩阵 | 不是排行榜 |
| **修理位（xfail）** | tests/ 里挂 xfail 的已知缺陷测试——修好自动变绿，测试即工单 | 不是失败 |
| **换脑三值** | base_url/model/api_key——切主脑只改三个环境变量（继承 v1） | 不含改代码 |
| **负例零误触** | 负例必须 NO_REORDER，误触一次即 P0 失败（继承 v1） | 不接受「误触率低」 |
| **冻结点** | 9/26 晚 v0.1.0：之后只修不加（继承 v1） | 不是停止工作 |

## 归档（v1 · repro-pack 时期，释文见 git 历史）

复现包 / bug 卡 / bugcard / 接入优先 / 证物层 / PACK 契约 / 双模型对照
