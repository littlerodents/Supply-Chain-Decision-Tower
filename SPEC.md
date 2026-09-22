# SPEC · repro-pack

> 由 2026-09-22 grilling 共识卡固化（baseline 2.0）。变更需明说，改这里。

## Problem Statement

报 bug 的传统形态——录屏/截图 + 人写的描述——同时服务两个对象：给人看（他要脑补现场），给流程看（分诊、留档）。在 agent 时代这个形态正在失效：能接入的场景里，对方 agent 直接远程接手，不再需要描述；不能接入的场景里（黑盒 SaaS、瞬态 bug、安全边界、审计要求），仍然只能交证据，但消费证据的不再是人类工程师，而是修复 agent——而一段裸录屏对 agent 是低效的：它得自己重新发现错误文本、定位时间点、推断复现路径。

两类场景之间缺一座桥：**一份 agent 可直接消费的证据包**。

## Solution

`repro-pack` 是一个 Agent Skill：给 agent 一段操作录屏（30–90s），它调用多模态大模型理解录屏，产出一个**复现包**——

- 结构化 bug 卡（JSON：类型/位置/严重度/错误原文/复现步骤骨架）
- 带时间戳的关键帧（圈出出错画面）
- 从画面中抽取的 console/报错文本
- 按 agent 消费格式写好的 GitHub issue

配套一个评测层：同一批录屏任务，对比「拿到包的修复 agent」与「只拿裸录屏的修复 agent」，用实测数据（BENCHMARK.md）证明包的价值——NVIDIA Tier-3 评测哲学往下游再推一层。

无 bug 的录屏是负例：不产包，只回一句「未发现问题」，不触发下游。

## User Stories

1. 作为报障者，我丢一段录屏给 agent，就能拿到一份我不需要自己动笔组织的 bug 证据包，所以我把「报 bug」从写作任务变成拖拽任务。
2. 作为报障者，当我的录屏里没有 bug 时，agent 不会小题大做地编造一个问题单，所以我能信任它的输出。
3. 作为接单的修复 agent，我拿到的 issue 里复现步骤、错误原文、出错时间戳齐全，所以我不需要在别人机器上盲目摸索现场。
4. 作为被黑盒 SaaS bug 困扰的用户，我给不了 SSH 也给不了远程控制，所以我需要把录屏变成对方支持工单能直接消化的结构化证据。
5. 作为开源维护者，我收到的 issue 是机器生成的标准格式，所以我的分诊成本下降。
6. 作为评测者，我用同一批任务对比带/不带 skill 的表现，所以 skill 的价值有实测数字而不是自述。
7. 作为 DGX Spark 的使用者，我把 skill 装进本地 OpenClaw workspace，所以整个链路在我的本地算力上可复现。
8. 作为想换模型的用户，我只改三个环境变量（base_url/model/api_key）就能切换主脑，所以我不被任何厂商绑定。
9. 作为演示评委，我 clone 仓库后用自己的录屏亲手跑通，所以我相信作品是真的能跑。
10. 作为安全审查者，我在仓库里找不到任何密钥，所以这个 skill 可以被放心审计。
11. 作为队友，我在 6:30–9:30 的晚间时段领取独立工单（任务集/runner/README/视频），所以两个人的并行不需要互相等待。
12. 作为赛事读者，我在 README 里读到部署说明、技术栈与评测方法，所以我能对照评分表逐项核验。

## Implementation Decisions

- **主脑**：StepFun 多模态端点（OpenAI 兼容）。`step-3.7-flash` 与 `step-5-preview` 在 D1 用同一段录屏做双模型对照（质量/延迟/成本三维），赢家做主脑，输家做换脑演示素材。Coding Plan 已确认含 step-5-preview。
- **可移植性**：端点三值（base_url / model / api_key）全部走环境变量，代码零改动换脑。
- **运行面**：DGX Spark 上装 OpenClaw，skill 装进 workspace（复用 9/20 训练营配方），`skills list --eligible` 作为安装验证口。本地 Qwen（图片模式）为备脑/换脑素材。
- **出口**：结构化 bug 卡（`bugcard.json`）为必产出物；GitHub Issues 为默认出口（`gh issue create`），issue body 按 agent 消费格式渲染。
- **输出契约**：包目录结构固定（bugcard.json + frames/ + repro.md），负例末行输出 `NO_BUG_FOUND`。
- **skill 结构**：遵循 agentskills.io 渐进披露——frontmatter（name/description/触发词/negative triggers）常驻 ~100 token，正文 <5K token，细节下沉 references/，可执行物在 scripts/。
- **评测三层**：①包质量（gold 字段召回 + 负例零误触 + 成本）为 P0；②修复 agent 带包 vs 裸录屏 A/B 为 P1；③安全接入端点为 P2（只写 Future work，不实现）。

## Testing Decisions

- 只测外部行为：入口脚本对录屏的产出物（目录结构、schema 合法性、负例行为），不测模型内部。
- 最高接缝：`scripts/repro_pack.py` 的 CLI 入口（`--validate` 本地可全测，不依赖 API）。
- 评测用 `evals/evals.json` 任务集（≥8 正例 + ≥2 负例，含 gold answer），runner 一键跑出 JSON 结果，禁止手工挑好结果。
- 阈值写死：负例误触必须为 0；正例 gold 三字段召回 ≥70% 才算 P0 达标。

## Out of Scope

- 飞书/企微等需要个人凭证的出口
- 实时屏幕捕获（只吃已有录屏文件）
- P2 安全接入端点（限时最小权限 SSH/远程通道）
- 前端界面（OpenClaw Web UI 即交互面）
- 五维全量评测、沙箱隔离、双 agent 集群
- 移动端

## Further Notes

- 提交物按赛事规则：公开仓 URL + 500 字以上 README（含部署/技术栈说明、skill markdown 展示）+ B 站演示视频 + 十日谈征文（CSDN/知乎，标注 AI 生成）+ 团队合影 + 表单。
- 冻结点：9/26 晚 v0.1.0；9/29 中午前交表单。
