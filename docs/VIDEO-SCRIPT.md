# 演示视频分镜脚本（≤3 分钟 · B 站 · 罗登思照录）

> 录制前置检查（一条 ssh 或找 O 线代跑）：
> 租机服务三件套必须在线——gateway :3030（200）/ 面板 :8501（200）/ ollama（nemotron 已拉取）。
> 录屏工具随意（QuickTime/OBS），浏览器全屏，字幕建议后期加（B 站描述记得**标注 AI 生成**）。

| 时间 | 分镜 | 画面 | 口播/字幕 | 素材 |
|---|---|---|---|---|
| 0:00–0:20 | **开场·痛点** | BENCHMARK.md 首屏 或 纯黑底大字 | 「MIT 报告：企业 AI 项目 95% 没有产生真价值。缺的不是模型，是把模型塞进业务的能力。FDE 岗位一年涨 7 倍，答案已经写在招聘市场上。我们把一个真实 FDE 案例做成了 Agent Skill。」 | README 第一节 |
| 0:20–0:50 | **是什么** | GitHub 仓库页滚动：skills/ 目录 → SKILL.md → tools.py | 「供应链控制塔 skill：一句运营问句，agent 查库存、算缺口、比供应商，产出结构化补货单。架构反转：宿主 agent 当大脑，skill 只给工具+知识+契约，本体零 LLM。顺带修了上游三个真 bug。」 | repo 首页 + `docs/N1-VERDICT.md` |
| 0:50–1:30 | **装上就跑**（核心演示） | 浏览器开 OpenClaw Web UI（租机 :3030），输入：「San Francisco 的 Colombian Coffee 未来 12 周够卖吗？不够的话补多少、找谁、总成本多少？」等 agent 三轮（发现→取证→出单） | 字幕标注轮次：「①定位 skill ②工具取证 ③决策单」→ 最终 JSON 特写：3268 件 × Nature Source × $119,006 | 实录即可；若 gateway 慢，备用素材 `evidence/d3/agent-out3.json` |
| 1:30–1:55 | **人看的那一面** | 面板 :8501：切 SKU=13001/仓库=SF/周期=12 周 → 红色「短缺 3268」徽章 + 预测曲线 + 库存/供应商表 | 「零 LLM 证据面板——所有数字由 skill 工具层直算，塔台给人看，agent 给人干活，双入口。」 | panel 实录 |
| 1:55–2:25 | **换脑**（平台适配高光） | 左右分屏贴两份输出：step-3.7-flash（19.2s）vs 本地 Nemotron 120B（201.9s） | 「同一问句、同一 skill、两颗脑子——云端 3.7 十九秒，DGX Spark 本地跑 120B 三分钟，答案一样对。换脑只改三个环境变量，能力资产不绑厂商。」 | `evidence/d3/brainswap-*.md` |
| 2:25–2:45 | **BENCHMARK** | BENCHMARK.md 主表特写 | 「四象限实测：裸 prompt 两颗脑子都只有 16.7%，装上 skill 双双 100%；负例零误触——库存够就是不需要补，绝不编建议。全部轮次数据公开，包括波动。」 | `benchmark/BENCHMARK.md` |
| 2:45–3:00 | **收尾** | repo 页 + 团队名 | 「FDE 案例转化 × Skills 设计与评测 × DGX Spark 本地算力。仓库开源，一条命令复现。我们是 XX 队，谢谢。」 | README 快速开始节 |

**B 站发布要素**：标题建议「把真实 FDE 案例装进 Agent Skill：供应链控制塔｜NVIDIA DGX Spark 黑客松」；描述含 repo 链接 + **AI 生成标注**；标签：Agent Skills / DGX Spark / 黑客松 / 供应链。
