# 演示视频分镜脚本（≤3 分钟 · B 站 · 罗登思照录）

> **STOP：仅作历史分镜草案，暂不可照此录制或发布。** 2026-09-26 真入口正例未产合约 JSON，负例未产 `NO_REORDER:100`；HTTP 200、Skill ready 和本地工具输出均不等于演示过关。先用新鲜 OpenClaw 正负例验收，过后再替换本草案中的镜头与数字；公开发布仍需 owner 授权。
> 录屏工具随意（QuickTime/OBS），浏览器全屏，字幕建议后期加（B 站描述记得**标注 AI 生成**）。

| 时间 | 分镜 | 画面 | 口播/字幕 | 素材 |
|---|---|---|---|---|
| 0:00–0:20 | **开场·痛点** | BENCHMARK.md 首屏 或 纯黑底大字 | 「MIT 报告：企业 AI 项目 95% 没有产生真价值。缺的不是模型，是把模型塞进业务的能力。FDE 岗位一年涨 7 倍，答案已经写在招聘市场上。我们把一个真实 FDE 案例做成了 Agent Skill。」 | README 第一节 |
| 0:20–0:50 | **是什么** | GitHub 仓库页滚动：skills/ 目录 → SKILL.md → tools.py | 「供应链控制塔 skill：一句运营问句，agent 查库存、算缺口、比供应商，产出结构化补货单。架构反转：宿主 agent 当大脑，skill 只给工具+知识+契约，本体零 LLM。顺带修了上游三个真 bug。」 | repo 首页 + `docs/N1-VERDICT.md` |
| 0:50–1:30 | **真实问句（待验收后补拍）** | OpenClaw 新会话现场问 SKU 13001 / San Francisco / 12 周；必须在真实入口产出严格决策 JSON | 只有 `decision=REORDER`、3268 件、Nature Source Coffee、总价 **$119,282** 且有工具证据时，才可剪入；`evidence/d3/agent-out3.json` 总价 $119,006，**禁止作为正确答案备用镜头** | 待新鲜录屏 |
| 1:30–1:55 | **人看的那一面** | 面板 :8501：切 SKU=13001/仓库=SF/周期=12 周 → 红色「短缺 3268」徽章 + 预测曲线 + 库存/供应商表 | 「零 LLM 证据面板——所有数字由 skill 工具层直算，塔台给人看，agent 给人干活，双入口。」 | panel 实录 |
| 1:55–2:25 | **换脑（仅历史素材）** | 贴已留存的 StepFun / 本地 Nemotron 同题输出，明确为历史单题对照 | 「曾在同题上取得两份输出；不代表跨模型稳定性或 OpenClaw 真入口已按契约通过。」 | `evidence/d3/brainswap-*.md`，发布前复核 |
| 2:25–2:45 | **BENCHMARK（按证据更新）** | 展示修订后的 `benchmark/BENCHMARK.md` 与失败轮次 | 「Nemotron 带 Skill 留存三轮 12/12、9/12、11/12；裸组工具权限不同，不能推因果；真入口负例尚未过。」不使用“稳定满分／零误触”字幕 | `benchmark/BENCHMARK.md` |
| 2:45–3:00 | **收尾（待验收）** | 仓库与测试证据（仅 owner 批准公开后展示） | 「FDE 案例转化 × Skill 设计与评测 × DGX Spark 本地算力；已验证与未验证范围见 README。」 | README / ISA |

**B 站发布要素**：标题建议「把真实 FDE 案例装进 Agent Skill：供应链控制塔｜NVIDIA DGX Spark 黑客松」；描述含 repo 链接 + **AI 生成标注**；标签：Agent Skills / DGX Spark / 黑客松 / 供应链。
