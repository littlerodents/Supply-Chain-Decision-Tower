---
task: "repro-pack 赛题交付"
slug: 20260922-dgx-hackathon-repro-pack
phase: in-progress
progress: 7/14
started: 2026-09-22T15:30:00Z
updated: 2026-09-24T15:30:00Z
iteration: 2
---

# ISA · repro-pack（第三届 NVIDIA DGX Spark 黑客松预赛）

> ⚠️ **REOPENED 2026-09-23 深夜**：owner 会后拍板选题改道（详见 D12）。未关闭 ISC 冻结待重锚；已关闭 ISC-1/2/4/5 的验证证据保留（过程资产 + 征文素材）。基建（OpenClaw/ffmpeg/租机/工程流/主脑选型）全继承。


## Problem

预赛 9/29 截止，需要一个 7 天内做得完、可证伪、能演示的 Agent Skill 作品。报 bug 的传统形态（人写描述）正被 agent 时代改写：接入优先，但给不了接入的场景里，消费证据的已从人类变成修复 agent——中间缺一座桥。

## Vision

评委 clone 仓库、改三个环境变量，就能用自己的录屏跑出一份修复 agent 可直接开工的复现包；仓库里躺着带负例的 evals 和 A/B 实测的 BENCHMARK.md。当有人对一段录屏说「这事儿现在是一个 agent 帮另一个 agent 接单了」——这活儿成立。

## Out of Scope

- 个人凭证类出口（飞书/企微）
- 实时屏幕捕获
- P2 安全接入端点（仅 README Future work）
- 前端界面；五维全量评测；沙箱；移动端

## Language

见 `CONTEXT.md`（与本文同步维护）。

## Constraints

- 时间：9/23–9/29，O 3–4h/天，T 18:30–21:30（待确认）；冻结 9/26 晚
- 硬件：远程 DGX Spark（SSH 访问方式待 owner 提供）
- 模型：StepFun Coding Plan（含 step-5-preview；3.7 Flash 待确认），OpenAI 兼容端点
- 赛规：公开仓 + ≥500 字 README（部署/技术栈说明）+ B 站视频 + 征文 URL + 合影 + 表单；群内禁泄 API 账号

## Goal

9/29 中午前，预赛表单全字段提交完成（控制塔 skill + 四象限 BENCHMARK + 演示材料），每项提交物有本仓可复核证据。

## Not yet specified

- StepFun 视频输入的确切 API 形态（D1 spike 探明；fallback：抽帧进图片模式）
- 队友档期确认结果
- 公开仓挂谁的 GitHub 账号（发布日 owner 拍板）
- 正例召回阈值在真实任务集上的可达性（D4 校准）


> **v2 重锚（2026-09-24）**：旧 F1-F4（repro-pack）随 D12 改道归档——已关闭的 ISC-1/2/4/5 证据保留在 Verification 作历史与征文素材；未关闭旧 ISC 作废。以下为控制塔 skill 的当前验收集（ISC-12 起）。
## Test Strategy

| isc | type | check | threshold | tool | anchors_to | severity |
|---|---|---|---|---|---|---|
| ISC-12 | bash | 7 工具移植冒烟+crc32 跨进程稳定 | 两次进程同 SKU 同预测 | python | literal | blocker |
| ISC-13 | bash | npx skills 可装+SKILL.md 合规 | skills list 可见 | bash | literal | blocker |
| ISC-14 | bash | 正例输出契约 JSON 八字段齐 | 字段全存在 | runner | literal | blocker |
| ISC-15 | bash | 负例 NO_REORDER 零误触 | 误触=0 | runner | literal | blocker |
| ISC-16 | bash | 任务集 ≥8 正 ≥3 负，金答案工具直算 | 数量达标+金答案落盘 | python | literal | blocker |
| ISC-17 | bash | 四象限 runner 一键跑完 | 输出 JSON 结果 | bash | literal | blocker |
| ISC-18 | eval | 正例命中/负例误触 | 命中≥70% 误触=0 | runner | derived | blocker |
| ISC-19 | bash | BENCHMARK.md 四象限有数 | 2×2 非空 | bash | derived | blocker |
| ISC-20 | manual | OpenClaw@Spark eligible+真问句演示 | 输出+日期证据 | ssh | derived | blocker |
| ISC-21 | bash | 换脑素材：同问句双脑输出存证 | 两份输出落盘 | bash | literal | blocker |
| ISC-22 | manual | 塔台跑通 或 R2 降级记录 | 二选一 | manual | literal | normal |
| ISC-23 | bash | README≥500字+透明引用+排雷清单 | 字数/引用/清单齐 | bash | literal | blocker |
| ISC-24 | manual | 表单全字段提交 | 9/29 12:00 前回执 | manual | literal | blocker |
| ISC-25 | manual | B站视频+征文 URL 就绪 | 两 URL 可访 | manual | literal | blocker |

## Features（v2 · 控制塔 skill）

### F1' · skill 本体（转化）
Why: 一切叙事的实体。
- [ ] ISC-12: 7 工具移植完毕，crc32 稳定化冒烟通过（同 SKU 跨进程预测一致）
- [x] ISC-13: SKILL.md 渐进披露合规 + npx skills add 安装可见
- [ ] ISC-14: 正例问句产出八字段决策 JSON（含 tool_trace）
- [ ] ISC-15: 负例问句 NO_REORDER+余量，零误触

### F2' · evals 层
Why: 技术深度 25% 的踩分点；Tier-3 哲学的社区化实践。
- [x] ISC-16: 任务集 ≥8 正 + ≥3 负，金答案由工具直算落盘
- [x] ISC-17: 四象限 runner（{bare,+skill}×{3.7,nemotron}）一键跑完
- [x] ISC-18: 3.7+skill 正例命中 ≥70%，负例误触=0
- [x] ISC-19: BENCHMARK.md 四象限实测数据齐

### F3' · 部署与演示
Why: 平台适配 15%（R1 承重墙）+ 演示 10%。
- [ ] ISC-20: OpenClaw@Spark skills list eligible + 真实问句演示证据
- [ ] ISC-21: 换脑素材：同一问句 3.7-flash 与本地 120B 各一次输出存证
- [ ] ISC-22: Streamlit 塔台跑通 或 R2 降级触发记录（二选一关闭）

### F4' · 赛事交付（继承）
- [ ] ISC-23: README ≥500 字（部署/技术栈/转化说明/透明引用/排雷清单）
- [ ] ISC-24: 表单全字段 9/29 12:00 前提交
- [ ] ISC-25: B 站视频 + 征文 URL 就绪

## Anti-claims

- A1: 仓库任何提交不含密钥、内网地址、owner 私人凭证（验证：历史 grep）
- A2: 负例永不产包/开 issue（验证：ISC-4/ISC-8）
- A3: 不实现 P2 安全接入端点（验证：无相关代码；README Future work 节存在）
- A4: 不提交需要 owner 个人凭证才能跑的出口（验证：出口仅 gh + 本地文件）

## Decisions

- **D1 选题**：repro-pack（①′重框架）。背景：原①「录屏→人读报告」被 owner 证伪——AI 时代报障从「描述」转向「接入」，但接入是特权不是默认；黑盒 SaaS/瞬态 bug/安全边界/审计四个场景仍需证据，且消费者已变成修复 agent。决定：产出物从「人读报告」改为「agent 可消费复现包」。否决的替代：screen2bug 原框架（前提失效）、作业拍照②（evals 客观化难、教育红线）、mini-SkillEvaluator 单做（演示弱）、TAO 串联④（撞车）。影响：SPEC/CONTEXT/演示脚本全以此为轴。
- **D2 主脑**：StepFun 双模型 D1 对照定主备（step-5-preview 已确认在 Coding Plan 额度内）。**D1 实测定案（provisional）：主脑 = step-3.7-flash**（中位延迟 10.18s vs 15.87s，成本略省，输出更稳，非 preview 无下线风险）；备脑/换脑演示 = step-5-preview。质量维度在合成片上无区分度，D4 真实任务集复确认。机制定案：视频走 video_url + base64 data URI，本地文件直进端点，无需上传。证据：evidence/spike/dual-model.md。**Owner 拍板（2026-09-22T19:4xZ）：选 A——主脑 3.7-flash 定案，D4 升级为「更强假设」检验实验；反转触发器写死：真实任务集上 5-preview 质量命中差 >2 倍，或 3.7 出现任一负例误触 → 主脑换 5-preview（.env 一行改）。**
- **D9 账号与发布归属（2026-09-23 owner 拍板）**：GitHub 私有仓 + 公开仓均挂 owner 账号（littlerodents/repro-pack，私有仓已建已推）；B 站演示视频传队友账号（33official）；公开 push 仍需 owner 点头（D6）；给队友开私有仓权限（待他 GitHub 用户名）。
- **D10 合影口径（2026-09-23，09-23 下午更新挂起）**：赛规原文「团队资料：提交团队合影」。原口径：双人（Evander + abloom25）。**新事实：DGX Spark 为第三位队友私购**——若机主为正式参赛成员，合影改为三人，分工表加机主行（算力线）。当晚动员会收口：机主是否在报名表内。
- **D3 运行面**：DGX Spark + OpenClaw（赛规「本地算力部署」为必答题）；Hermes 仅在 `npx skills` 原生支持时进 README，不投入开发。
- **D4 出口**：bugcard.json 必产出 + GitHub Issues 默认出口。
- **D5 工程流**：遵循 mattpocock/skills；仓库用本地 markdown tracker（`.scratch/BOARD.md`），因公开 remote 尚未创建且赛期仅 7 天；spec 置于仓库根 `SPEC.md`（偏离 to-spec 的 .scratch 惯例，为评委可见性）。
- **D6 档位**：P0（F1–F4 全部 ISC）/ P1（一键 runner、seeded-bug 修复 A/B、NIM 第二脑、Hermes）/ P2（安全接入端点，立碑不建）。
- **D7 排期**：baseline 2.0（D1 spike → D2 四件套 → D3 上 Spark → D4 冻结 → D5 材料 → D6 发布 → D7 提交），变更需 owner 明说。
- **D8 台账**：本项目满足 ISA 条件（交付物≥3、跨会话、第三方复核），用 ISA.md 替代 STATUS+DECISIONS 两件套；STATUS.md 仅作仪表盘。

- **D11 演示面与模型叙事口径（2026-09-23 owner 问询后维持）**：主面 = OpenClaw（配方已验证 + 评委同款栈）；Hermes 仅作可移植性证据位（npx 五客户端实装在手，能一行装才进 README）。叙事分工：skill 主脑 = StepFun 3.7 Flash（赞助商轴，核心功能所在）；本地算力轴 = gateway 本地 Qwen（闭源 API 无本地权重，本地叙事只能开源模型扛；72B 可选档入 SPARK-DEPLOY 剧本——仅 README/征文素材，主演示用 35B-A3B 快档，dense 大模型在 GB10 生成速度慢一个量级）。评分同时点名「开源模型+StepFun」，双覆盖。

- **D12 选题重开（2026-09-23 深夜，owner 会后拍板）**：方向改为「参考 GitHub 上已有 FDE 行业案例 → 把其工作/内容转化为 Agent Skill」，锚「项目落地实用性」等核心评分轴。repro-pack skill 本体搁置（其基建、evals 方法论、负例零误触思想、双模型主脑定案全继承）。grilling 重开，SPEC.md 待重写；期限不重排（9/26 冻结 / 9/28 完成 / 9/29 提交）。T 线默认 abloom25 有时间（owner 指示，后续按事实调整）。合影按 owner 决定走合成路线（诚信风险已警示两次，留痕即止）。

## Verification

（ISC 关闭后回填，只记真实跑过的命令与结果）

D1 夜班全套（2026-09-22T19:04Z，均真跑）：
- ISC-1: `python3 repro_pack.py assets/samples/clip.mp4 --out packs/d1-pos --no-issue` → exit 0，末行 `PACK:.../packs/d1-pos`，包内 bugcard.json + frames/(3 帧) + repro.md（evidence/spike/e2e.txt）
- ISC-2: `repro_pack.py --validate packs/d1-pos/bugcard.json` → `VALID`；红队坏卡×2 仍以「缺必填字段/枚举越界」被拒
- ISC-4: `repro_pack.py assets/samples/neg-001.mp4 --out packs/d1-neg --no-issue` → exit 0，末行 `NO_BUG_FOUND`，`packs/d1-neg` 不存在
- 机制: 探针梯子 text(1.16s)/image(2.88s)/video(5.0s) 全过；双模型 3+3 轮真实输出 → dual-raw.json
- gh 出口（2026-09-23）: `run.sh assets/samples/clip.mp4 --out packs/d2-issue-test`（无 --no-issue）→ issue https://github.com/littlerodents/repro-pack/issues/1 真实创建（标题 agent 消费格式），已关闭留证；输出契约全环节闭环

D2（2026-09-23，均真跑）：
- ISC-5: `npx skills@latest add ./skills/repro-pack --yes` → 安装至 `.agents/skills/repro-pack`（universal: Codex/Copilot/OpenCode/Warp 等；symlink: Claude Code），`npx skills list` 显示 repro-pack（evidence/d2/skill-standalone.txt + 安装器输出）
- 红队（安装器自己抓的）：SKILL.md description 含裸冒号→YAML 解析失败，加双引号后过——D3 当天必踩的雷提前爆了
- 自包含验证：skill 整目录拷至陌生路径 `/tmp/dgx/standalone` → `run.sh --validate` VALID；正例 `PACK:/tmp/dgx/pack-e2e2`；负例 `NO_BUG_FOUND`（不依赖仓内 tools/）

- **D13 SDD 对齐补课（2026-09-24 深夜）**：owner 要求对照 mattpocock 流程盘点并留队友修理余量。诚实结论：to-spec/to-tickets 已合规，**TDD 红绿循环未按规范先行**（工具层是测试后补）。补偿决策：①tests/test_tools.py 建立（7 回归锁含上游 bug 修复回归）②三个已知缺陷以 xfail 挂为「修理位」+ BOARD Bug 队列（BUG-1/2/3，判据=测试变绿）——测试即工单，队友零上下文接手 ③code-review 定档 9/26 冻结前必跑（两轴）④CONTEXT.md 升 v2。判断留痕理由：TDD 偏差是真实发生的过程事实，记录比粉饰有价值（征文素材）。

## Verification（v2）

N3（2026-09-24 晚，均真跑）：
- ISC-12: `tools.py gap --sku 13001 --location "San Francisco" --weeks 12` 两个独立进程 diff 一致（DETERMINISM PASS）；shipping 双进程一致；7 工具全冒烟（gap/inventory/suppliers/forecast/shipping/chart/kb）；**修复上游三 bug**：hash 不稳定×2（crc32）、solver f-string 致库存恒 0（参数化查询）；domain 发现：第 1 周需求恒 200 → 负例=短周期问句（evidence/n3-smoke.txt）
- ISC-13: `npx skills add ./skills/supply-chain-control-tower --yes` → Done；`npx skills list` 可见（evidence/n3-smoke.txt）
- 测试基线（D13）: `python3 -m pytest tests/test_tools.py` → **7 passed, 3 xfailed**（修理位 BUG-1/2/3 挂牌，基线锁）
- code-review（D13-③，偏差关闭）: 两轴执行——Standards 抓出 cmd_inventory/suppliers 重复(已提取 _sql_query)、kb 文件句柄、测试计数脏表达式(已修)；Spec 轴 8 项全对齐(7 工具/契约/任务集/负例)，已知缺口=BUG-2 与 api.md 声明一致（队友位）
- ISC-16: `gold_gen.py` → 12 条金答案直算落盘（pos-dec-002 正确选低价供应商，比价逻辑验证）
- ISC-18: `run_evals.py` 实测——**stepfun/skill 12/12（100%）**，负例 3/3 零误触，无关问句零工具；**stepfun/bare 2/12（16.7%）**——带/无 skill 差距 83pp，Tier-3 叙事实证（evidence/evals/results-*.json）
- nemotron 双象限：租机本地后台执行中（隧道大载荷断连的规避；此腿零凭证暴露）
- 四象限收割（2026-09-25）：bare 2/12 ×2，skill 12/12 ×2（nemotron 延迟中位 97s vs 3.7 6.6s）；负例零误触全线；**触发≠遵守的修复**：无硬规则版 3.7+skill 波动 10-11/12（裸答模式）→ SKILL.md 硬规则版 12/12；BENCHMARK.md 成文（evidence/evals/summary.json + results-*.json）；nemotron 硬规则版确认轮后台中（eval2.flag）

## Remaining Work

- ISC-3 质量维度：待 T2 真实任务集在 D4 定案（合成片上两模型 1/3 平，无区分度；教训：gold 关键词要双语、type 口径要写死）
- ISC-1/4 目前证据基于合成片，T2 真实录屏到位后复跑确认（不重开 ISC，追加验证）
- SSH 未到手（阻塞 ISC-6/D3）；剧本已备：docs/SPARK-DEPLOY.md（官方安装器路线，无需训练营 bundle）
- OpenClaw gateway 走本地 Qwen，skill 走 StepFun——两叙事都占，key 注入方式待机器属性（私有/共享）定
- 队友 GitHub 用户名（开私有仓权限）
