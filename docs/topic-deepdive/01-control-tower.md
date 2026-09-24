# 候选档案 ① · 供应链控制塔 skill（源：tensor-house/control_center_llm）

> 2026-09-24 · grilling 结案版。证据均可核查（gh api 实测 / 仓内实测）。

## 选择理由（证据）

| 理由 | 证据 | 来源 |
|---|---|---|
| 数据自带，3 天不死在数据上 | `data/` 含 inventory.csv、products.json、suppliers.csv、suppliers.json（<1MB 全在仓） | gh api 目录实测 |
| UI 现成，演示分白送 | `.streamlit/` 目录 + notebook 内 streamlit 引用 | 同上 |
| License 可商用转化 | **Apache-2.0** | gh api license 实测 |
| FDE 原汁原味 | LangChain 处理器 + 控制塔形态 = FDE 式交付物，非散装 notebook | notebook 分析（langchain 引用 ×1） |
| 换脑叙事独一份 | 原项目挂 **Gemini-pro on Vertex**（config.json 实测）→ 换 3.7-flash（主脑定案：head-to-head 5.0/5 实测）→ 备脑 nemotron-3-super-120b **已在租机本地**（87GB，加载 73s 实测） | config.json + TOPIC-RESEARCH |
| 平台适配 15% 有落点 | OpenClaw 已装机租机（2026.9.5 实测）；LLM+编排跑在 Spark=「Agent Skills × 大模型 × 本地算力」 | D3 实录 |
| 不撞车 | NVIDIA catalog 41 产品线无 inventory control tower（cuOpt 是求解器、VSS 是视频）；FDEOps 是方法论 skill | 刘春晖讲义 catalog 快照 |

## 自我 grilling

### R1 · 评委与工期视角

❓ **Q1：「你们只是搬运 tensor-house，原创性在哪？」**
➡️ 转化物不是复制。原项目 = notebook + 本地 StreamLit demo + Vertex/Gemini 函数调用；交付物 = **Agent Skill**：SKILL.md 渐进披露 + 触发工程 + processors 重写为 skill scripts + **原项目完全没有的 evals/BENCHMARK 层**。评分原文技术深度 25% 的措辞就是「**Skills 设计与融合**」——skill 化工程正是踩分点，不是搬运。

❓ **Q2：「数据 <1MB 还谈 cuDF/GPU，自欺欺人？」**
➡️ 半接受，已降级处理。主叙事不押 cuDF，押「LLM+编排跑 OpenClaw@Spark + 本地 120B 备脑」；cuDF 仅作可选加分（inventory 天然可扩到万行级合成数据），README 不夸大数据。平台适配 15% 的落点是三融合，不是算力炫耀。

❓ **Q3：「Streamlit 是给人的，skill 是给 agent 的，到底交付哪个？」**
➡️ 双层并存：skill 为主（agent 在 OpenClaw 对话里调，输出结构化决策建议——输出契约方法论复用），Streamlit 塔台为「证据面板」（评委肉眼看到库存/供应商状态）。人机双入口，演示视频 30s UI + 60s 对话。

❓ **Q4：「控制塔痛点真实吗？」**
➡️ 中等偏上：控制塔是供应链 SaaS 标准产品形态（SAP IBP/Kinaxis 的企业版）；tensor-house 作者（前 Amazon 供应链工程师）选此域 = 行业共识。诚实边界：演示定位「区域零售/小型制造」轻量场景，不冒充企业级。

❓ **Q5：「3 天够吗？LangChain+Vertex 链路重写是坑吗？」**
➡️ 见 R2-Q7——LangChain 整个砍掉。

### R2 · 衍生攻击

❓ **Q7：「3.7-flash 的工具调用格式兼容 LangChain 的 Gemini 链吗？」**
➡️ **砍 LangChain**——skill 化后不需要它：agent（OpenClaw/pi）自带编排，processors 变成 skill scripts（纯 python 函数 + 结构化 IO），LLM 只做「自然语言→参数」和「结果→建议解释」。更贴「MCP 管连接、skill 管知识、harness 管调度」的架构叙事（周旭讲义原话）。依赖面缩小 = 工期风险下降。

❓ **Q8：「控制塔的决策建议质量怎么客观 evals？」**
➡️ 三层：① 确定性层——补货量/服务水平由 gold 脚本算出（数学唯一），LLM 数值对答案；② **负例层——库存充足时问要不要补货，正确答案=不补（零误触红线直接复用）**；③ 对照层——裸 agent vs 带 skill 的决策准确率/幻觉率。有数学底座的 evals，比标注争议型任务更硬。

❓ **Q9：「无公网 IP，评委怎么看 UI？」**
➡️ 赛规指定形态就是 B 站视频（录屏对拍）；需要在线 demo 时走 ssh 隧道临时开。四候选同担此约束，非 ① 独有。

## 残留风险（明示，非沉默假设）

1. 原项目 `processors/program_aided` 的真实覆盖面 **UNPROVEN**（克隆实测前按最小可行设计，SPEC 里写死验证步骤）
2. 比赛期间其他队同思路的风险不可排除（护城河=evals 深度+换脑叙事）
3. 业务逻辑深度受原项目上限约束（接受——评分要的是落地形态，不是 ERP）

## 结案声明

所有攻击均有证据回答或明示残留，无未答之问。**推荐位次：1**。
评分覆盖：实用 25 ✓ · 技术深度 25（Skills 设计原话）✓ · 平台适配 15（本地算力+120B 备脑）✓ · 演示 10（UI 现成）✓。
