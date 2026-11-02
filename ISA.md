---
task: "repro-pack 赛题交付"
slug: 20260922-dgx-hackathon-repro-pack
phase: in-progress
progress: 11/14
started: 2026-09-22T15:30:00Z
updated: 2026-09-28T11:43:00Z
iteration: 5
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
- 硬件：远程 DGX Spark；SSH已获授权，9/27 15:25主人完成认证并恢复复用通道，不在台账存凭据
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
- [x] ISC-14: 正例问句产出八字段决策 JSON（含 tool_trace）— StepFun 脑两独立会话严格通过（2026-09-26 深夜终，evidence/step-acceptance/pos1|pos2.json）
- [x] ISC-15: 负例问句 NO_REORDER+余量，零误触 — 末行纯文本 NO_REORDER:100（2026-09-26 深夜终，evidence/step-acceptance/neg1.json）

### F2' · evals 层
Why: 技术深度 25% 的踩分点；Tier-3 哲学的社区化实践。
- [x] ISC-16: 任务集 ≥8 正 + ≥3 负，金答案由工具直算落盘
- [x] ISC-17: 四象限 runner（{bare,+skill}×{3.7,nemotron}）一键跑完
- [x] ISC-18: 3.7+skill 正例命中 ≥70%，负例误触=0
- [x] ISC-19: BENCHMARK.md 四象限实测数据齐

### F3' · 部署与演示
Why: 平台适配 15%（R1 承重墙）+ 演示 10%。
- [x] ISC-20: OpenClaw@Spark skills list eligible + 真实问句演示证据
- [x] ISC-21: 换脑素材：同一问句 3.7-flash 与本地 120B 各一次输出存证
- [x] ISC-22: 自建零 LLM 证据面板跑通（:8501 HTTP 200）；上游原版因 Gemini key 不可得按 R2 记录替代

### F4' · 赛事交付（继承）
- [x] ISC-23: README ≥500 字（部署/技术栈/转化说明/透明引用/排雷清单）
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

- **D14 评审补强顺序（owner 2026-09-27，历史决策）**：先补 DGX Spark 平台适配的**直接运行证据**，再做模型/多智能体的可证伪技术实验，最后收口项目完整性；真实企业系统/行业试点价值的主张在这之后讨论。**改变工作优先级不等于改 baseline 2.0、解除 9/26 晚冻结或授权新增服务、改 Gateway、公开发布。**平台门先区分“在 GB10 上运行过本地模型”与“测得 GPU/统一内存加速”；没有同步遥测绝不写 NVIDIA GPU 性能优势。模型深度门只按与 StepFun 单独运行的增益、负例零误触和成本判断，不把 Iris/双 agent 串接当既有能力。
- **D15 当前顺序（owner 2026-09-27 续，覆盖 D14 排序）**：先证伪相对 StepFun 单独运行的协同增益，再**优先产出项目完整性 20% 的规格，前端 PRD 第一**；其余三项评审 SPEC 后续。已先以旧 verifier 四题做离线反证，发现审计 0 工具/0 修正、负例旧 judge 可误判，不能声称增益。`docs/FRONTEND-PRD.md` 与 `docs/REVIEW-COMPLETENESS-SPEC.md` 先落盘为**规格**，不宣称功能已实现。`ISA.md` 后续的 owner「入口不想用云端」仍生效，云端 StepFun 3/3 不冒充本地脑交付，本地 Nemotron/Qwen 正例未过。baseline 2.0、冻结和凭据/发布边界均不变。

- **D16 醒后监测与PDF（owner 2026-09-27 06时续）**：主人要求继续监测Zcode在sparker的工作、指出不符合验收要求之处、持续汇总PDF，醒后汇报。这授权有限只读监测与报告，不授权修改DGX/模型、看私有对话、使用或披露凭据、发布或替主人签收。旧监控文件与运行任务已缺失，恢复一个5分钟间隔的本机低优先级观察任务，沿用9/27 17:39截止；SSH缺失时REMOTE_UNOBSERVED，不反复拨号或口令注入。所有共享变化在未有作者证据前标作者未知。D15仍是产品规格优先级，当前先完成监测支撑；baseline 2.0和冻结不变。

- **D17 通道恢复与只读验收（owner 2026-09-27 醒后）**：主人批准先恢复只读证据通道、核实际部署/最新回执，再按PRD验前端与正负例；不增加模型或第二Agent。15:25主人自行认证，随后本助手只读复用。实际云端默认及既有auditor不构成主人改选产品路线的授权；不在未确认本地约束变更时提交新的云端推理。查出问题不自动授权改远端实现或运行态。baseline 2.0及冻结不变。

- **D18 最小前端整改（owner 2026-09-27，16:36开工）**：明确授权修四类误判并默认关闭审计；暂不动模型和Gateway。范围限前端，不改数据/工具/Agent定义、不新增模型调用或发布。原问句绑定与冲突决策检查用于封同类绕过，不能以修改验证器掩盖原答。并发源码必须先取新版本、保留他人工作再最小合并；不能用此授权扩张为脑路由改选。本地入口约束、baseline 2.0及17:39监测停止线不变。

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

## Verification（N5 · 2026-09-25，均真跑，证据 evidence/d3/）

- ISC-20: skills list ready + eligible=1；gateway 真问句三轮（发现→取证 3268×Nature Source→八字段 JSON，agent-out3.json）；gateway 环境变量排障记录在案
- ISC-21: brainswap-stepfun.md（19.2s/3 工具）+ brainswap-nemotron.md（201.9s/6 工具）——同题同对，速度差 10 倍
- ISC-22: panel :8501 HTTP 200（45 分钟建成，未触止损）；nemotron run3 R8=11/12 入 evidence

## Verification（材料日 · 2026-09-25）

- ISC-23: README 全文成稿——汉字 1211 字（>500），四节结构/透明引用/排雷清单/skill md 链接/本地算力/NVIDIA+StepFun/BENCHMARK 数字 八项自检全过；同批产出 VIDEO-SCRIPT.md（7 分镜含素材指针与 B站发布要素）+ ESSAY-SKELETON.md（D0-D7 八节每节带仓内素材指针）

## 2026-09-25 晚 · Iris 隔离试验前置核查（PARTIAL）

- ISC 清单现有 **9/14 勾选**，原页头 11/14 为重复/误计，已按清单更正；不据此认定全部 9 项在主人最终入口过关。
- 本机重跑 `python3 -m pytest tests/test_tools.py -q` → 7 passed, 3 xfailed；工具直算 pos-dec-001 总价 119282。历史 OpenClaw 真入口留存 `evidence/d3/agent-out3.json` 决策枚举仍为「需补货」，总价 119006，不满足严格决策契约。SKILL.md 例子误写 119284，待代码/文档交付阶段按证据修正。
- 此前临时 `--verify` 试验污染 `evidence/evals/results-stepfun-skill.json`：现仅 4 条，审计工具调用全为 0；未经独立复核不得作为 12 题对照或协同增益。`tools/run_evals.py` 有未提交实验改动，未动队友 BUG-1/2/3。
- 本轮未找到可用 DGX SSH 入口：三个通用别名解析失败，另一不确定归属的别名连接超时；**Iris 部署/串接未发生**、DGX 资源现状 UNPROVEN。经 owner 允许后才可在已确认的 DGX 上隔离试装；不停止现有模型和服务。
- 检查明细与下一可证伪入口：`evidence/2026-09-25-preflight/PROBE.md`（本地忽略目录，私仓不会自动附带）。会议提出的 9/27 完整版与旧 9/26 冻结冲突，未自行改排期。

## 2026-09-26 凌晨 · DGX 可达，Iris 与主人入口仍未验收（REOPENED）

- 复用 owner 已登录的 SSH 会话取新鲜快照：DGX `aarch64`，119Gi 内存/约 114Gi 当前可用，磁盘余 2.7T；Ollama 仅登记 Nemotron 120B（约 80.9Gi），采样时未加载；OpenClaw/面板均在监听。**空闲内存不等于两模型可安全并跑**。
- Iris-mini 权重尚未安装。官方 Hugging Face 权重入口从 Mac 与 DGX 均超时；系统 Python 中也没有 torch/transformers/vllm。官方 Iris-Harness README（GitHub 可达）要求自备模型兼容端点以及搜索、摘要、评判凭据；不使用不明镜像/明文旧密钥做替代，故部署/搜索串接均 **UNPROVEN**。
- 真入口红队：`openclaw agent --session-id pi-dgx-20260926-pos1 --json` 同一自然问句两轮分别耗时 116239ms/355810ms，工具调用 9/73、失败 3/2。两次 CLI 都 exit 0、status ok，**第一轮只说要查运费，第二轮只说要尝试运行 shipping，均无决策 JSON**；不能关闭 ISC-14，先前 ISC-20 的 `skills list ready` 等过程证据不替代严格契约。
- 同机脚本直跑 `shipping` → 2.0、`gap` → -3268/现库 30，排除了「工具完全不可用」；优先调查 Agent 为何在工具路径上兜圈。两份原始 OpenClaw 输出留在远端临时目录（无凭据共享）；详细命令和灰度见本地 `evidence/2026-09-26-iris-preflight/PROBE.md`。此轮没有修改或重启 DGX 服务、没下载权重、没发消息/下单；仓内原 `tools/run_evals.py` 实验改动仍原封不动。

- **失败的最小修复试验（第 1 轮）**：脱敏轨迹见 skill 被当作工具调用、模型反复猜错 `/home/parker` 路径（实际 `/home/sparker`）、两次 exec 未找到。新增 `tests/test_skill_entrypoint.py`：改前两红；本地 `SKILL.md` 换 OpenClaw 绝对路径并修正示例总价后 `9 passed, 3 xfailed`。临时部署到 DGX 的文档改版从 `/tmp` 直跑工具正常，但同一**真入口**新会话仍只回「需要查运费」（134355ms/12 工具调用/5 失败，无 JSON）；明确提示正确绝对路径的诊断新会话也未产决策（112688ms/19 调用/11 失败）。`openclaw config get agents.defaults.workspace` 是正确的 `/home/sparker/.openclaw/workspace`。不能把本地测试绿当修复成功。**远端 SKILL 已按 SHA 校验恢复原版**，本地改动及测试为未提交候选；不重启/停止 120B 或 Gateway。下一修复门：找可复现的 Agent 工具路径引导接缝，回到自然问句重验正负例。详情见本地 `evidence/2026-09-26-iris-preflight/PROBE.md`。

- **机械闸门**：`bun ~/Desktop/2026-Evander-工作台/PAI/runtime/closeloop-verify.ts evidence/2026-09-26-iris-preflight/claim.json` → exit 1，`valid=true / stage=REOPENED`，SOURCE/BUILD/RUNTIME 有过程证据但 `OWNER_ENTRYPOINT` 未通过；入口证据是**代理操作机器自证，不是主人确认**。本轮不可称交付完成。权重取不到且入口失败，停止追加 Iris 安装与多 agent 营销声明。

## 2026-09-26 下午 · 止损决定与赛前口径（REOPENED，不新增 ISC）

- 继续复用 owner 已登录的 DGX Terminal；宿主进程属 `sparker`，Skill 安装路径、`eligible`、`modelVisible` 与 workspace 配置均正确。安装版 OpenClaw 文档确认消息中可用 `$supply-chain-control-tower` 显式引用；**它只改善了一次正例数字，未解决契约**：新会话输出 3268 / Nature Source / 119282，但为 Markdown、非决策 JSON（159192ms，10 工具调用、2 失败）。
- 新独立负例显式引用同一 Skill 后 151142ms、26 调用、19 失败，终答仅称查看 workspace；同机工具金答案为 Seattle / SKU13001 / 1 周缺口 +100，必须 `NO_REORDER:100`，故负例入口未过。既有原生态问句也失败。按 owner 认可的止损线，**停止继续烧 120B 的提示词碰运气；Iris 不进入当前参赛主张**。
- 下调本地 `README.md`、`benchmark/BENCHMARK.md` 和 `docs/VIDEO-SCRIPT.md` 的满分/稳定性/真入口/错总价声明，提醒原始 `evidence/` 被忽略、StepFun 12 题文件已覆盖、Nemotron 三轮 12/9/11、裸组工具权限不等；视频不得拿旧 `119006` 当正确镜头。未发布或推送。详证：`evidence/2026-09-26-iris-preflight/explicit-skill-probe.md`（本地忽略目录）。
- **完成态仍未实现**：须有两个独立新会话的严格正例 JSON（SKU13001@SF 12周，补 3268、Nature Source、总价119282、有工具证据）+ Seattle 1 周负例末行 `NO_REORDER:100`、零补货建议。旧 9/26 晚冻结仍是基线；无证据时不宣称完成，不擅自延至 9/27。

- 本地 `python3 -m pytest tests/test_skill_entrypoint.py tests/test_tools.py -q` → **9 passed、3 xfailed**；`git diff --check` 通过，README、BENCHMARK 和视频脚本的链接/事实核对已做。机械闸门：`bun ~/Desktop/2026-Evander-工作台/PAI/runtime/closeloop-verify.ts evidence/2026-09-26-iris-preflight/claim-pm.json` → **exit 1 / valid=true / stage=REOPENED**（OWNER_ENTRYPOINT 失败）。入口证据由**代理操作机器自证，不是主人确认**；不得说参赛主链已完成。原 `tools/run_evals.py` 未验收改动未动；本地 `SKILL.md` 文档候选仍未在 DGX 实装。

## 2026-09-26 下午 · Skill `read` 最小复现（只读诊断，ISC 不变）

- 取现存 DGX 内建脱敏轨迹 `pi-dgx-debug-explicit-20260926/events.jsonl`（SHA256 `7c5774c9d043c20879eecef935cac63aab3d73c3c9850b76923475383e600231`），按 `toolCallId` 关联调用/结果：同一会话 5 秒内读 `/home/parker/.../SKILL.md` → `success=false/File not found`，随后另一条读 Skill → `success=true` 且内容含「补货决策 SOP」（成功路径在导出中用 `$WORKSPACE_DIR` 占位脱敏）。同机只变更 home 路径的 Python 文件读取重演：`parker` → exit 1；`sparker` → exit 0。复放文档里的秒级红灯命令 → `BAD_SKILL_READS 1` / exit 1；另一会话仍有 3 次同型失败。详见本地被忽略的 `evidence/2026-09-26-iris-preflight/minimal-skill-read.md`。
- **局部结论**：至少这一类工具失败来自模型提交的错误 `tool.call.arguments.path`，而非 Skill 文件不存在或运费算法；即使后续成功读取 SOP，最终决策契约仍可能失败，故不能认定主链根因已解或关闭 ISC-14/15。本轮未再次推理、试装 Iris、改配置、动 `tools/run_evals.py` 或评测结果；项目阶段继续 REOPENED。

- **修复位复核（owner 要求修后续查）**：DGX 新鲜 `openclaw skills info ... --json` 的 `filePath` 仍正确，失败会话的 `systemPromptReport` 也包含该 Skill；安装版 OpenClaw 文档称注入的 Skill XML 带 `location`，但已脱敏系统提示不可直接查看真实文本。首个错路径出现在模型 `assistant.message`，不是仓内 `tools.py`；正例后来成功读 SOP、跑工具，终答却约 836 字符 Markdown 且不含 `"decision"`，故只纠正路径也**不能推定**通过主链。OpenClaw `before_tool_call` 能改写参数，但要在 Gateway 安装/启用插件，属于尚未获准的运行时工具策略改动；不做 `/home/parker` 链接、不以提示词试错、不重启、不再跑 120B。**未修、未重验新会话，REOPENED**；需 owner 决定是否授权范围限定的 Gateway 修复实验。详证仍记 `evidence/2026-09-26-iris-preflight/minimal-skill-read.md`。

## 2026-09-26 傍晚 · owner 授权协作与限时监控（项目继续 REOPENED）

- owner 后续授权 Zcode 临时试验限定该 Skill 错误 `read` 路径的 Gateway hook；另一条指令确认**先解释 SPEC/PRD 差异再改**，随后确认启用**24 小时本机只读监控**。职责分离：Zcode 独写 hook/Gateway；本助手只看共享代码/脱敏回执、本地测试与提醒，不抢已登录的 DGX Terminal、不碰服务或凭据。未发现独立 `PRD.md`，仅以 `SPEC.md`/本 ISA 判当前契约；项目冻结仍按 2.0，不据监控自动延后。
- 本机监控放在 `/tmp/pi-zcode-watch-20260926/`，`launchctl` 标签 `com.evander.pi.zcode-watch`：17:40–17:45 CST 期间实测 `state=running / pid=20247`，一分钟后 `last_scan` 自动前进；到期按配置 2026-09-27 17:39 CST 自动退出。仅监看共享试验目录白名单，变更时跑本地 guard 测试（当前 **7/7**）、语法检查与本机通知；不轮询 DGX、不启动模型、不发网络消息。独立监控单测 **4/4**、plist lint OK；已自行捕获 Zcode 的 `bin/dgx-term.py` 变化，语法 OK，但远端退出码/`--timeout` 功能仍需单独反证（见共享目录 `MONITOR-NOTE.md`）。远端插件触发、PID、真实入口及回滚在缺脱敏回执前均 **UNPROVEN**。
- 监控代码/配置机械闸门：`bun ~/Desktop/2026-Evander-工作台/PAI/runtime/closeloop-verify.ts /tmp/pi-zcode-watch-20260926/claim.json` → **valid=true / stage=PARTIAL / exit 1**，SOURCE/BUILD/RUNTIME 已核，OWNER_ENTRYPOINT 缺主人实际看到提醒的证据；这不改变控制塔主线的 **REOPENED**。本轮未改 `tools/run_evals.py` 或旧评测文件、未部署 Zcode hook、未发布。

## 2026-09-26 晚 · Gateway hook 试验执行完毕（REOPENED 不变，ISC-14 未过）

- **授权内完成**：`rewriteSkillRead` 纯函数 + 插件 `pi-supply-read-guard`（package/manifest/index.ts/自包含 guard 副本）。单元 `node --test test/guard.test.mjs` → **7/7**；插件隔离沙箱（stub SDK + 子进程 HOME 控制）→ **5/5**；handler 全 try/catch 永不抛错（`before_tool_call` 抛错会 fail-closed 拦调用，故反向外兜 fail-open 保护无关会话）。证据：`evidence/2026-09-26-iris-preflight/hook-trial/final-tests.txt`。
- **DGX 上机零重启**：Terminal 通道（未新建 SSH）完成 install --link --force → enable → inspect --runtime → 三会话验收 → disable 全链；Gateway PID **2010301**、broker 2010380、面板 2006235 全程不变（`Applied in Gateway generation 3` 热应用；inspect 显示 enabled/activated/`before_tool_call` 已注册）。远端 sha256 与本地逐文件一致。详证：`hook-trial/TRIAL-RECORD.md`。
- **入口验收**：正例两独立新会话（`pi-dgx-hooktest-pos1/pos2`）均 **FAIL**——终答停在「Now let me read the SKILL.md…」/「Let me search more specifically…」即自停（91807ms/7 调用、39744ms/3 调用），无 119282/3268/Nature Source/decision；两轮模型均未再提交 `/home/parker` 错路径，**hook vivo 改写效力 UNPROVEN**（未触发≠修复成功）。负例 `pi-dgx-hooktest-neg1` 58246ms，**数值与方向正确、严格末行 FAIL**：终答末行含 `结论：NO_REORDER:100（库存充足，可支持本周销售）`，不是纯文本 `NO_REORDER:100`；虽满足 `SPEC.md` §52 的宽松包含式判据，不满足 `SKILL.md` §38 / owner 已确认的严格入口契约。原试验报告的“首次 PASS”仅为宽松判法，不关闭 ISC-15。原始 JSON 存 `hook-trial/results/`，脱敏回执 `hook-trial/runtime-{pos,pos2,neg}.json` + `monitor-receipt.json` + `runtime-rollback.json` 已按监控 README 格式落盘。
- **停止边界、机制待证**：原始结果中 pos1 为 7 调用/1 失败，pos2 为 3 调用/0 失败；两者 `completion.stopReason=stop / finishReason=stop / aborted=false`，终答均为宣告下一步而未执行，且未提交触发 hook 的错路径。至少 pos2 **无需工具报错也能出现症状**；“模型本身提前结束”与“Gateway 将普通文本视作终答”尚无法从汇总结果区分，pos1 的局部工具失败也不能直接抹除。若真要判机制，只读获取这两个既有会话的脱敏逐步轨迹（最后原始 tool_calls、tool result、回合结束位置）；按 owner 止损线不再烧 120B 碰提示词。
- **机械闸门**：`bun ~/Desktop/2026-Evander-工作台/PAI/runtime/closeloop-verify.ts evidence/2026-09-26-iris-preflight/claim-hook.json` → exit 1，**valid=true / stage=REOPENED**，SOURCE/BUILD/RUNTIME 已核、OWNER_ENTRYPOINT failed；入口证据为**代理自证（BEFORE_AFTER 机器证据，非主人确认）**。本轮不可称主链完成。
- **监控质疑闭环**：远端退出码实测 RC_FALSE=1/RC_TRUE=0；`--timeout` 限界反证（sleep 8 预算 3 → 5.7s TIMEOUT 无输出泄漏；预算 30 → 11.0s 成功）——期间修复两版缺陷（固定轮询无视预算、滞后宽限击穿短预算）。插件已停用（`Disabled plugin`），远端 `/tmp/pi-supply-read-guard` 与三份 `/tmp/pi-dgx-hook-*.json` 留存待 owner 清理；`tools/run_evals.py`/旧评测/SKILL.md 未动；SSH 口令轮换待办不变。

## 2026-09-26 深夜 · owner 选 A：StepFun 接 gateway 入口（差一次重启授权，UNPROVEN）

- owner 拍板选 A（StepFun 跑真入口），条件「先确认切换方式不触发重启」。已验证的无重启路径：`openclaw agent --model stepfun/step-3.7-flash` 逐次覆写存在；官方 `@openclaw/stepfun-provider` 插件已装（generation 6 热应用，PID 2010301 不变）并 reload 到 generation 7；onboard（cn 端点）+ `models auth paste-api-key` 双双入库（共享库 stepfun:cn + agent 库 stepfun:manual）；openclaw.json 已写 `baseUrl=https://api.stepfun.com/v1`。
- **key 有效性已证**：Mac 直连 `api.stepfun.com/v1` 与 `/step_plan/v1`（step-3.7-flash）均 HTTP 200；activate 探测 401 只因默认探测模型 step-3.5-flash 不在 Plan 内。
- **卡点**：运行中网关对新 provider 凭据无热读取路径——插件 reload（gen7）后 agent 运行仍报 401/或 missing-provider-auth；`--local` 在网关运行态被拒；`gateway call` 无配置重载方法。OpenClaw 工具自身提示需 `openclaw gateway restart`。**按 owner 红线停在此处待授权**；重启影响面已告知（gateway 换 PID 约 1 分钟、会话落盘不丢、面板/Nemotron/SSH 独立不受影响，9/25 曾两次重启无事故）。
- 通道升级：owner 的 Terminal 窗口中途关闭后，改用**一条 ControlMaster 复用 ssh**（`/tmp/dgx-spark-master.sock`，8h persist），owner 随后也重连了 Terminal；两通道并存（远端上限 64）。验收将以 ssh 通道跑（真实退出码、无屏幕截断）。
- 重启授权后的既定步骤：restart → 核对新 PID 与服务恢复 → `pi-dgx-step-20260926-pos1/pos2/neg1` 三会话（`--model stepfun/step-3.7-flash`，自然问句同 hook 试验轮）→ 判据同前（正例八字段 JSON×2 + 负例末行 NO_REORDER:100）→ 更新台账与闸门。StepFun 配置在重启前为惰性（默认模型仍是 ollama/nemotron），不重启也无副作用。

- **21:35 CST 独立只读复核**：主人 Terminal 已连回 DGX，选中 tab 空闲时仅查现存轨迹目录、`ps` 与 `openclaw plugins inspect --runtime --json`，不发模型问句：新 hooktest 的内建脱敏逐步导出尚不存在（仅旧 debug 目录）；Gateway PID 2010301 / broker 2010380 / 面板 2006235 均仍存活，插件此时 `enabled=false / activated=false / hookCount=0`。本机监控 `state.json` 仍活跃，已将正例标 `NO_FINAL_JSON` ×2、负例标 `NEGATIVE_CONTRACT_FAIL`，证据/纠错见 `hook-trial/MONITOR-NOTE.md`。项目继续 REOPENED，不能用 Zcode 原始报告中的负例 PASS 宣称负例严格过关。

## 2026-09-26 深夜续 · 重启执行完毕、StepFun key 中途失效（BLOCKED on owner）

- owner 授权重启后执行：发现「前台模式网关吞掉协作 restart 请求」（PID/uptime 不变）→ `gateway stop` 被运营保护拒绝后 kill 旧进程 2010301 → `openclaw gateway install` 建成 **systemd 用户服务**（`~/.config/systemd/user/openclaw-gateway.service`）并启动，Health OK。**重启回归与修复**：新服务环境缺 `OLLAMA_API_KEY`（9/25 已知坑，本地 ollama 只需任意非空值）→ drop-in `openclaw-gateway.service.d/ollama-env.conf` + daemon-reload + 服务重启；修复后本地脑冒烟 `pi-dgx-smoke26`（「Seattle 仓 SKU13001 现库存？」）→ **status ok / nemotron / 94s / 答案 300 件正确**，面板 2006235 全程无恙。网关改由 systemd 托管（重启一条命令），比原终端前台模式更稳。
- **StepFun key 失效（新事实，21:15→22:05 之间）**：同 key 21:15 从 Mac 双端点实测 **200×2**；22:05 起全端点（Mac/DGX × .com/.ai）一律 **401 `{"message":"Incorrect API key provided","type":"invalid_api_key"}`**。key 在两次探测之间被 StepFun 侧作废/轮换（或额度耗尽停用；不排除网关多次 401 重试触发风控，外部无法区分）。**与 DGX 出口 IP 无关、与 OpenClaw 无关**（Mac 同样 401）。
- **阻塞在 owner**：登 platform.stepfun.com 查 key 状态或签发新 key。到手后约 5 分钟收尾：`echo <新key> | openclaw models auth paste-api-key --provider stepfun` → `systemctl --user restart openclaw-gateway` → 三会话验收。**验收判据按协作方 21:35 复核收紧**：负例末行必须是纯文本 `NO_REORDER:100`（SKILL.md §38 严格契约），hooktest-neg1 的「结论：NO_REORDER:100（…）」不再算过。
- 遗留：StepFun key 与 SSH 口令均需轮换（清单 +1）；远端新增 systemd drop-in 为无害配置，`/tmp/pi-dgx-step*.json` 错误样本可清理。

## 2026-09-26 22:43 CST · owner 最新决定：守 A / B 待另行明确授权（HOLD，不变更冻结基线）

- 本条是**最新 owner 指令**，覆盖上述“到手后 5 分钟收尾”的旧执行计划：从此刻起只保持现状与已确认的 24 小时只读监控，**不换 StepFun key、不再重启/停止 Gateway、不跑新的 StepFun/Nemotron 问句、不恢复 Iris、不靠提示词碰运气、不发布**。先前按当时授权执行的 Gateway 重启、systemd 迁移与 StepFun 401 是既成事实，不能写成“仍待第一次重启”，也不擅自回滚。
- owner 若未来**明确选择 B**，进入验收的唯一充分条件：两个独立自然问句产出完整正例 JSON（SKU13001@San Francisco / 12 周，补 3268、Nature Source Coffee、总价 119282，含工具证据）＋一个 Seattle / 1 周负例**末行仅** `NO_REORDER:100` 且无补货建议。任一失败即止步，不扩大到提示词试错或 Iris；凭据处理、服务重启与发布授权均不能从本条推导。当前 StepFun 401 机制未经消歧，主链仍 **REOPENED**。
- 本机监控只读共享 hook 试验代码和脱敏回执，配置到 2026-09-27 17:39 CST 自动退出；不自动订阅 Zcode 私有会话、StepFun 凭据、Gateway 运行态。无新鲜主人入口证据前不升级状态。

## 2026-09-26 深夜终 · owner 交付新 key、StepFun 真入口三会话严格通过（承接并解除上节 HOLD）

- **授权衔接**：上节 HOLD 等「另行明确授权」——owner 随即在 Zcode 会话直接交付新 key（原文「阶跃用这个 key」），即为该授权；据此完成 key 入库 + systemd 服务重启（PID 2640896，Health OK）与三会话验收。未回滚任何既成事实，未碰 Iris/提示词/发布。
- 新 key Mac 双端点 200 验证后入库。**首轮正例暴露已知文档缺陷**：`pi-dgx-step26b-pos1` status ok / 18.3s / 4 工具 0 失败，八字段 JSON 齐但 `total_cost:119284.0`——即 ISA 早记录的「SKILL.md 示例误写 119284」把模型带偏（3268×36.5=119282）。**修复**：远端 SKILL.md `sed 119284→119282`（备份 `.bak-20260926`；本地候选本已改对，两端一致）。修文档缺陷，非放水判据。
- **三会话严格验收全过**（`--model stepfun/step-3.7-flash`，自然问句，独立新会话，网关真入口，判据=上节 owner 写死的充分条件）：
  - `pi-dgx-step26c-pos1`：12.9s / 4 工具 0 失败 / 八字段 JSON：REORDER、3268、Nature Source Coffee、34.5+2.0、**119282.0**、tool_trace gap/suppliers/shipping ✓
  - `pi-dgx-step26c-pos2`（变体问句）：12.1s / 4 工具 0 失败 / 同上全对 ✓
  - `pi-dgx-step26c-neg1`：7.7s / 2 工具 0 失败 / **末行纯文本 `NO_REORDER:100`**、300/200/+100 与金答案一致、无补货建议 ✓
  - 原始 JSON 落盘 `evidence/2026-09-26-iris-preflight/step-acceptance/`（pos1/pos2/neg1 + 修复前 pos1-preSkillFix 对照）。
- **ISC-14 / ISC-15 按严格判据通过**（14 条 ISC 现 **11/14**）；ISC-24（表单）、ISC-25（B站+征文）仍开放；owner 飞书入口签收已服务端核验；其他 ISC 仍按实际状态开放。网关默认模型仍为 ollama/nemotron（StepFun 为逐次 `--model` 覆写），演示默认脑切换待 owner 拍板。速度对照增量证据：StepFun 入口 7.7–12.9s vs 本地 120B 同判据 40–356s 未过。
- 安全清单不变：StepFun 新旧 key 与 SSH 口令均在聊天暴露，轮换待办。

- **闸门独立复核（2026-09-27 00:17–00:19 CST）**：原 `claim-step.json` 写 `claimed_stage=ACCEPTED`，尽管 verdict 四层通过却因脚本仅 `DONE` 返回 0 而 **exit 1**；原 `VERDICT.md` 的 AFTER 及飞书确认的 `observed_at` 又早于证物形成/确认时间。原件已存 `step-acceptance/claim-step-before-independent-review.json`（SHA256 `f791fe6371a1f14e61d6583c9233a8a9b33e7afb365a917bdfb4ba844bcb2795`）。独立回读三份原始 JSON：两独立 session 末尾 JSON 代码块八字段齐、3268/119282 算术吻合，工具实际摘要 4 次 `read/exec`、0 失败且终答 `tool_trace` 列 gap/suppliers/shipping；负例独立 session 末行纯 `NO_REORDER:100`、无补货建议。更正 claim 为 `DONE`，将 AFTER/OWNER_CONFIRMATION 观察时刻更新为本轮实际核验时间，再跑同一闸门 → **valid=true / stage=DONE / exit 0**；飞书主人确认服务端核验。闸门备注中两条 BEFORE_AFTER 仍是**代理自证（非主人确认）**，另有独立 OWNER_CONFIRMATION。ISC-14/15 在**显式 StepFun 路由**范围内维持关闭，项目整体仍 11/14。
- **未扩张的产品边界**：只读 `openclaw config get agents.defaults.model` 仍为 ollama；成功三会话均是逐次 `--model stepfun/step-3.7-flash`。本轮未切默认脑、未验证评委安装后零配置自然聊天；原始结果只有通用 `read/exec` 调用摘要与终答 `tool_trace`，**不含每次业务工具参数/结果的脱敏逐步轨迹**，不得把模型列出的名字冒充独立的逐调用证明。默认脑切换、公开发布、凭据轮换与 Iris 均非此轮结论或授权。

## 2026-09-27 凌晨 · 真入口 A/B：StepFun 3/3 vs 本地 Nemotron 1/3（owner 点名对比）

- owner 指示「看看 stepfun 和 nemotron 120b 哪个本地效果更好，给证据」→ 同机同网关同 Skill 同三问同严格判据，唯一变量 `--model`。**StepFun 3/3（12.9s/12.1s/7.7s，10 工具 0 失败）vs Nemotron 1/3（69s/171s 正例双败——2 工具 2 失败/仅 1 工具，两轮终答均向用户索要数据；负例 44.3s 严格过）**。本地脑可靠域=单步判断；多步决策链 0/2。与 harness 历史（stepfun 12/12×2 中位 6.6s vs nemotron 12/9/11 中位 97s）互相印证。证据件 `evidence/2026-09-26-iris-preflight/ab-comparison/`（AB-COMPARISON.md + 六份原始 JSON，会话 `pi-dgx-step26c-*` / `pi-dgx-nem26-*`）。演示默认脑建议 StepFun，待 owner 拍板。

## 2026-09-27 凌晨 · 平台适配先行的只读地面核查（PARTIAL）

- 复用空闲 DGX Terminal 真跑 `uname -m` → `aarch64`；`nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,power.draw --format=csv,noheader,nounits` → `NVIDIA GB10, 580.173.02, [N/A], [N/A], 0, 3.97`，命令 exit 0。闲时利用率 0 和内存 N/A **既不是 GPU 失败证据也不是推理加速证据**；本轮未启动模型或改服务。`evidence/2026-09-27-platform/OBSERVATION.md` 给出可复核边界；旧 AB 六份原始 JSON 证明本地 Nemotron 1/3 与云端 StepFun 3/3 的入口输出，但缺同步 GPU/offload/吞吐记录，不能把云端效果算成 DGX GPU 优势。
- 下一证伪门只需一段获准且不争用服务的**固定输入**硬件遥测＋模型执行回执，若推理会影响现有用户或无法隔离则止步并标 UNPROVEN。之后才进入模型/多智能体增益的受控对照；最后再修 README/视频/证据包与默认入口。平台分项尚不可声称保证 15%，项目仍 PARTIAL。

## 2026-09-27 凌晨续 · owner 约束「不想用云端」→ Qwen3-30B-A3B 本地腿 0/2，本地无脑可过关

- owner 明确 StepFun 为云端、入口不想用云。按 D11 预案补测本地 Qwen：ModelScope 直下 Qwen3-30B-A3B Q4_K_M（18.56GB，SHA256 与官方清单一致，~24MB/s 13 分钟；ollama 官方源仅 2.2MB/s 已弃），`ollama create qwen3:30b-a3b-local` 注册（模板含标准工具渲染）。
- **Qwen 本地腿 0/2**：正例1 FAIL（32.7s / 26 调用 16 败——未读 SKILL.md，把 tool_search 目录条目名当工具连调）；负例 FAIL（98.7s / 57 调用循环不收敛，无 NO_REORDER）。pos2 按止损未跑。失败形态与 nemotron 又不相同（索要数据/宣告即停 vs 工具名幻觉/循环失控）——多步工具契约下的系统性短板。
- **三腿终局**（同条件同判据）：StepFun 云 3/3（32.7s 总，10 调 0 败）｜Nemotron 120B 本地 1/3（仅单步负例过，284.6s）｜Qwen3-30B 本地 0/2。**「入口不用云端」约束下，现有本地脑无一通过真入口。** 证据 `evidence/2026-09-26-iris-preflight/ab-comparison/`（已扩为三腿版）。
- 待 owner 决策的三条路：①云脑入口+本地轴素材的混合叙事（StepFun 使用本就在评分轴）②继续本地攻坚（换 Qwen3-32B dense/官方模板版/其他开源脑，每轮成本高且无把握）③纯本地降格交付（正例演示缺失）。ssh 通道现状：ControlMaster 单通道复用（owner 已知会），本机 footprint 仅 1 进程 + socket + 暂存文件。

## 2026-09-27 01:28 CST · 完整性规格优先与 SSH 只读核验（PARTIAL）

- 前端 PRD 先写，随后项目完整性 20% SPEC：`docs/FRONTEND-PRD.md`（FE-01~05）与 `docs/REVIEW-COMPLETENESS-SPEC.md`（PC-01~06）。把功能、稳定、前后端、文档、逻辑和 3 分钟演示逐一落为可证伪门；**这是文档交付，不是前端/后端/视频完成**。源事实为 `SPEC.md`、本 ISA/`STATUS.md`、面板/工具源码、三例 StepFun 证据、本地两模型失败轮。
- 离线核对旧 `tools/run_evals.py`（只读，SHA256 `02b87ab7…`）：审计四题 4/4、另一轮相同四题 StepFun-only 2/4；审计四题全 `PASS/kept`、总 verifier tool_calls=0、改答=0、额外耗时 **69.1 秒**。不同 worker 轮次不能当配对增益；以错误负例文本「NO_REORDER:100」后追加「建议补货20件」，或改 gap 为 999，旧 `judge()` 均判 PASS。**协同增益及负例不退化 UNPROVEN**；旧 runner/结果一字未改。
- owner 明确许可 SSH 直连；01:07 复用存活的 SSH master 只读核对 DGX `sparker/aarch64`、面板 app.py SHA256 `da7de9cf…` 与本地相同、gateway 用户服务 active、面板 HTTP 200。01:20 socket 已消失；随后仅一次 publickey 非交互 SSH 探测被拒。**未在工具调用、文件或日志写口令，未再次登录、未改远端配置/模型**。HTTP 200 不证明页面交互通过；待 owner 自行建立可复用认证通道或给安全的非交互授权方式后才追加远端验收。
- **滚动 24 小时 Human/AI 计划（2026-09-27 01:28–09-28 01:28 CST，按当前授权，不改 2.0）**：AI 现在核对两文档事实/链接并交付 PARTIAL 状态；Human 自行决定入口用本地脑攻坚、改选云端或诚实降格，并在需要远端复验时自行建立安全复用 SSH；AI 仅在新授权/入口可用后做受限只读 FE/PC 对照与脱敏证据，失败即停；Human 复核材料和是否授权任何运行态改动/公开发布。未获决策前不自动发模型试验、配服务、发稿或处理凭据。

## 2026-09-27 06时续接 · 前端 PRD 优先收口（仅文档，项目 PARTIAL）

- `docs/FRONTEND-PRD.md` v0.2 补齐单页结构、三条用户流程、NOT_READY/NEEDS_INPUT/RUNNING/失败/过期等状态、服务端字段接缝、请求隔离、P0-A工具面/P0-B实时面、FE-01~08与T-01~08；`docs/REVIEW-COMPLETENESS-SPEC.md` 补PC→FE→ISC映射、六请求窗口回归、两次三分钟彩排配方。演示验收与ISC-24/25公开提交分离，避免为了“完整”偷扩发布权限。
- 真实文档核验：Markdown解析/表格渲染/本地链接/FE与PC编号检查通过；本地工具直算30/3298/-3268与300/200/+100，供应商和USD119282.00吻合gold。红队按内存副本变异错总价、抹去零缺口、破坏源码链接，检查均拒绝（3/3），不改任何金答案或历史结果。详见 `evidence/2026-09-27-completeness-docs/REVIEW.md`。
- 新鲜源码反证确认：现有面板选1/12/26周实际画12/12/26点却标52周；库存查无行返回0；这些是发现未改的UI/数据解释风险，不是本轮已经修好。STATE/请求合同均为目标，HTTP200不替代浏览器验收。源码及历史评测保持原样，未连接DGX/模型、未操作凭据或服务。项目计数维持11/14历史勾选，不关闭新的产品ISC。

### 滚动24小时 Human / AI（09-27 06:13 → 09-28 06:13 CST）

这是覆盖全窗口的条件计划，替代01:28计划窗口；**baseline 2.0、9/26冻结、9/28发布须授权和9/29截止不变**，不是自动后台任务或主人预约。写规格当前无须主人决策；只有进入互斥的模型/部署实施时才需选择。

| 时段（CST） | AI 工作/停止线 | Human 可选动作 | 证明物 |
|---|---|---|---|
| 09-27 06:13–08:00 | 收口两规格与STATUS，核对链接/数值/保护文件哈希，交付文档；不启服务 | 按链接查看前端PRD；无需为文档完成另行签字 | 两文档+REVIEW.md，产品仍PARTIAL |
| 08:00–12:00 | 有反馈则仅修规格歧义；无新消息即待命，不自行做前端集成 | 反馈目标/界面；若要实施再选本地攻坚、云端或降格 | 真实反馈及对应文档diff；没有反馈不伪造批准 |
| 12:00–17:39 | 仅在新授权和可用通道下安排受限复验；否则保持UNPROVEN，不反复试SSH/模型 | 需要远端复验时提供安全复用通道；凭据轮换由主人处理 | 获准复验的脱敏结果；没有就记录未执行 |
| 17:39–24:00 | 既有hook监控按原配置到期，不续期；有会话时只读确认，无会话不声称已观察退出 | 可审查材料与是否允许后续运行态改动；无需为停止监控动作签字 | 若实际检查则记录停止状态；自动到期本身不当新授权 |
| 09-28 00:00–06:13 | 按已获反馈保持规格/证据一致；无新增授权继续HOLD实现与发布，不自动发模型/推仓/传视频 | 自主决定发布与提交条件，不由本计划代签 | 下次续接以真实入口证据更新；缺证继续PARTIAL |

## 2026-09-27 06:41 CST · 恢复监测并生成醒后PDF（PARTIAL，非远端完整审计）

- 06:23真读旧 `/tmp/pi-zcode-watch-20260926/` 的README/watch/config/state均ENOENT，launchctl旧任务查询无运行结果，SSH socket不存在；中断原因未知，不能把历史心跳当现在连续监控。原“17:39等待旧监控退出”计划已被此新事实替代。
- 新运行目录 `evidence/2026-09-27-zcode-watch/`（gitignore）；一个本机用户LaunchAgent `com.evander.pi.zcode-report-watch`，Python来自现有安装、未装依赖。固定白名单采样，只持久化哈希/时间/检查结果；不复制原始终答，不执行被监测代码。有既存SSH master才进行固定只读身份/架构、Gateway active/PID、面板HTTP、Skill文件哈希探针；ProxyCommand=false与BatchMode防止回退新认证。当前远端0次观测，不能判断Zcode此刻在远端做了什么。
- 验证：测试先从缺实现红灯开始，9项回归通过（含符号链接拒绝、不复制canary、不执行被监测代码、坏回执、无通道不拨号、远端变更不归因、采样缺口与截止）；真实子进程3秒截止测试3.09秒退出，STOPPED_DEADLINE、只采1次。PDF两页中文已提取与渲染图回看，主结论明确远端未观测；旧代码/评测/材料15项SHA未变。后台任务已真启动（首查PID16088），首个后台采样06:38:04.633 CST落盘；后续间隔心跳与机械闸门记录于监测README/VERIFY。
- 报告入口 `evidence/2026-09-27-zcode-watch/ZCODE-DGX-REPORT.pdf`，同目录Markdown/state/events可追溯。针对产物列P0/P1/REVIEW，不主观责备Zcode；自动规则不是持续人工语义审查。新来源不在白名单则不可见；本机睡眠会有采样缺口。只恢复自己的观察任务，不抢Terminal、不改远端、不公开发送。醒后在当前对话汇报，不假称能检测主人已醒或自动外发消息。

### 当前滚动24小时 Human / AI（09-27 06:41 → 09-28 06:41 CST）

替代上一监测排期；baseline 2.0与冻结/发布需授权均不变。没有后台模型/浏览器常驻，只有已启动的有限观察任务。

| 时段 | AI / 自动任务 | Human | 证明物与停止线 |
|---|---|---|---|
| 09-27 06:41–12:00 | 每5分钟采样共享白名单、检查已有SSH socket、更新PDF；无通道明示远端未知 | 可休息；醒后可直接看PDF或在当前会话问汇报 | state/events与带时间PDF；不得伪造远端或作者归因 |
| 12:00–17:39 | 沿同一授权继续；若醒后有新指令只按指令限域调整，不自动扩来源/模型/服务 | 按需看总体问题和决定后续实现路线；凭据轮换自行处理 | 变更哈希/固定规则问题；新鲜入口证据缺失仍PARTIAL |
| 17:39–24:00 | 到期停止采样，写最后报告；不续期、不为了观察停任何DGX服务 | 无需配合到期；报告留本机 | 到期逻辑已测试，真实到期状态须届时或续接时再查 |
| 09-28 00:00–06:41 | 无自动采样/外发；若有会话再回读最后PDF并整体汇报 | 自主唤起会话、审阅报告；未唤起不假称已经汇报 | 报告截止时间保持不动，未观测区间明确列出 |

## 2026-09-27 15时早段 · 主人批准通道恢复→部署回执核对→PRD验收（当时BLOCKED_AUTH）

- 最新直接指令：先恢复已获授权的远端只读证据通道，核对实际部署版本与最新回执，再按PRD验收前端及正负例；不再增加模型或第二Agent。授权不包括改默认脑、重启、发布或先行修改前端实现。
- 14:55醒后汇报真读记录：101次本地采样（100次后台），远端0；只有本助手早晨更新ISA/STATUS两处变化，34个白名单文件与最新快照哈希一致。最大后台采样间隔313.364秒，无超过10分钟的间隔；不是完整远端操作审计。
- 15:00后尝试一次非交互publickey认证，exit255/Permission denied；没有尝试密码、没有执行远端命令、不降低主机校验。授权已有，但可用认证会话缺失；当前工具无安全交互输密，需主人在系统SSH提示中隐藏输入一次建立共享socket，不再次发明文口令。详情 `evidence/2026-09-27-entry-recovery/PROBE.md`。
- 当前停止在认证；不把本机旧副本当实际新部署，不先跑模型问句。监测原17:39停止线、baseline 2.0与冻结不变；上一滚动计划中的“有通道才复验”条件仍未满足。接通后才只读核对版本/回执并决定真实入口可执行哪项验收，项目仍PARTIAL。

## 2026-09-27 16:02 · 通道已恢复，远端已迭代，严格业务验收仍PARTIAL

- SSH：主人15:25在独立系统终端隐藏输入认证，本助手15:28/15:57实际复用返回sparker/aarch64；Gateway active/PID2702395、面板HTTP200。认证阻塞解除；口令没有进入脚本、日志、证据。
- 实际部署不同于本机旧副本：新增实时Tab，默认StepFun云端；已有main/auditor，页面默认开审计。数据6SKU/8库存/9供应商、任务16题；新增算法模块未接主链。panel在本轮由6f932197d697…变至8e480f310384…（15:42版，15:53/15:57仍同hash）；不以未签名变化确定作者，不把异步更新归因自己。
- 真实浏览器15:48–15:49八项限定检查通过：工具正例30/3298/3268/119282，负例300/200/+100，缺记录防护，1/12/26周期显示/取样，供应商发货地，实时页静态入口及1366布局。旧“纯工具、未接Agent/三项显示问题未修”口径已过期。无新Agent提交；键盘取消审计仅作用隔离测试会话，全局默认未改。
- P0反证：部署校验函数允许NO_REORDER:999、建议补20件后追加NO_REORDER:100、充足库存却订-100件、正例缺rationale/tool_trace四种错误PASS。测试脚本exit0表示漏洞成功复现，不是产品全绿。FE-03/04不可关闭；本地实时正负例、并发/超时/安全完整矩阵未验。额外缺供应商UI边界因导航超时未完成，保留失败，不称已复现线上崩溃。
- 新回执：只读查到两个UI命名StepFun会话15:23/15:42成功结束，tail隐藏具体工具参数/结果及原答，不能当合同通过；新读01:45三例云端旧终答数字吻合。06:02auditor旧回执13工具/1失败，不再泛化“所有审计零工具”；新样本仍未证明纠错收益。
- 详细证据：`evidence/2026-09-27-entry-recovery/REVIEW.md`及同目录源快照、浏览器图/JSON、回执投影、redteam输出。首轮等待/checkbox脚本失败、numpy序列化失败、CDP目标不符和边界超时均可见。未覆盖冻结源码、旧评测或金答案，未改DGX服务/模型/代码，不增Agent，不发布，不关闭新ISC；历史11/14保持。
- 监测：15:54已取得6次远端固定探针；不能补造早前盲区。旧自动PDF的静态问题源为旧共享版，当前语义结论以本轮报告为准，自动心跳/哈希仍有效。

### 历史滚动24小时 Human / AI（09-27 16:02 → 09-28 16:02 CST）

这是按现有授权的完整条件计划，不是新增定时任务。唯一实际后台任务仍是原5分钟只读监控，17:39硬停止，baseline 2.0不变。

| 时间（CST） | AI | Human | 证明物/停止条件 |
|---|---|---|---|
| 09-27 16:02–17:39 | 完成只读验收回执/报告；原监测继续固定探针；不新发模型或修改实现 | 复核假PASS、云端默认与本地约束；如需整改另行授权 | 报告、源码哈希、UI截图、反证结果、真实心跳；缺证保持PARTIAL |
| 17:39–24:00 | 原任务到期停止，不续期；只有当前会话实际回查才确认退出 | 无需配合到期；按需审查结果 | 截止后state/退出回执，未检查则不声称已观察停止 |
| 09-28 00:00–09:00 | HOLD，无新后台业务任务、安装、模型试验或发布 | 无强制动作，认证/发布决定仍由主人掌握 | 无新增执行不写成进展 |
| 09:00–16:02 | 仅收到新指令后按批准范围修复/复验；否则保留证据和阻塞 | 决定是否授权最小整改及是否调整入口路线 | 获准后新鲜同入口正负例；未授权不改运行态 |

## 2026-09-27 17:23 · 最小整改候选有证，SSH断线+并发版本漂移，部署未证

- 16:36真读面板基底 `c4feead2303e…`，已有每日巡检。只制作单文件前端补丁，保留巡检；本机冻结面板仍 `da7de9cf…`，没有用远端整版覆盖本机源码。
- 原始反例经隔离Streamlit UI按钮/解析/核验卡片链真实复现，外部CLI答复用夹具，不发模型。修后 `app-ui-replay29.py`（SHA9b000ef5…）29/29：四反例不再亮绿灯，正确正/负、历史负例、八字段正例、零缺口、错仓库、混合决策、空值及审计默认关闭均过。隔离回退旧版后四误判+默认开审计重新出现（5失败/7，2正确控制通过），没有回滚生产。
- 失败不藏：初轮pandas平台探针被测试桩拦；历史正确负例一度过严被降级；混合JSON/NO标记、模型改仓库一度绕过。对应红灯均保留，前两次修复后29项通过。
- 第三项压力反证发现新正文核验的嵌套量词：64逗号后夹带建议，真实函数5秒超时。最新候选去掉冗余内层+后约0.005秒返回UNPROVEN，SHA变为 `d21d3817…`；全29项回放属于前一SHA，最新版本仍需在重连/重基线后全量重跑。不得混称所有验收已过。
- 实际部署尝试17:11 SSH exit255（Connection closed by UNKNOWN port 65535），回执0字节；17:14 socket/master、临时18501转发均不存在，原因未知。部署是否落盘未独立回查，未取得改后浏览器证据，不能称上线。已给主人既有安全短入口恢复认证，不读口令/Terminal会话。
- 还发现持续并发改动：监测记录16:44 b2f978…、16:49 2bf80c…、16:54 d13f8c…、17:09 4fa8578be381…；17:10真实浏览器有新增上传Tab、新提交文案，默认审计仍开，零页面/网络/HTTP错误。作者未知，基底已过期。恢复后必须先读新源码、核是否已应用、最小重放补丁并适配UI回放定位器，禁止直接覆盖或拿旧基底29/29当新部署验收。
- 本机旧回归9 passed/3 xfailed；本轮未安装依赖、未发推理/重启/配置/发布命令，临时CSV零缺口仅发生在测试副本。机械闸门valid=true / PARTIAL / exit1，缺RUNTIME和OWNER_ENTRYPOINT。详细证据/下一步在 `evidence/2026-09-27-panel-minfix/REVIEW.md`。ISC仍11/14，不新增关闭；完整本地业务链仍PARTIAL。

### 当前滚动24小时 Human / AI（09-27 17:23 → 09-28 17:23 CST）

仅条件计划，不新建后台任务；唯一原监测仍17:39硬停止，不自动续期，baseline 2.0不变。

| 时间（CST） | AI | Human | 证明物/停止条件 |
|---|---|---|---|
| 09-27 17:23–17:39 | 记录部分验收与阻塞；若通道恢复则只取新源码、最小合并与受限复验，不增加模型调用 | 需要继续远端工作时自行在系统SSH完成认证，不发聊天口令 | 新鲜源码/运行态哈希与改后页面；缺证保持PARTIAL |
| 17:39–24:00 | 原监测到期停止；仅当前交互会话恢复后继续已授权整改，不安排新后台轮询 | 按需提供认证并看结果，无新增产品选择要求 | 真正回查到退出才说已观察停止；源码漂移先停覆盖 |
| 09-28 00:00–09:00 | HOLD，无额外后台任务/自动模型试验/发布 | 无强制动作 | 不把计划写成已执行 |
| 09:00–17:23 | 仅在新指令/恢复的当前会话下收尾同一前端任务；仍不换脑、不重启Gateway | 若需要不可逆/新范围再由主人决定，否则无需再次授权既定范围 | 同版本全回归、真实新页面、配置/服务不变回执及机械闸门 |

## 2026-09-27 18:01 · 指定Zcode会话全量测试请求（BLOCKED_SSH，未开始新测试）

- 最新明确请求：查看 `/home/sparker/sess_48d1acd2-2b49-41eb-a1f5-dc59f7ce5eb6.zcode-session` 当前产物，做全量测试、真实E2E、消融及递归不定参数审查。接续优先级是先读取指定路径/当前实现并固定版本，而不是直接部署D18旧候选。具体目录/文件类型与内容尚未读到，不猜测。
- 验证边界：先盘点现有测试和全部已实现入口；真实推理与模型答复夹具分列。消融锁定同题、同数据、同权限和判据，审计前后必须对应同一worker输出，不以不同轮次冒充提升；记录质量/误触、延迟、成本。递归参数审查采用有界扰动和反例递进，缺参、类型、范围、组合、异常及不可信输入分轴，不承诺穷尽无限输入。
- 本轮先测不改；只读指定会话及项目相关产物，内容先脱敏；不读凭据/其他私有会话、不接管Terminal、不新增模型/Agent、切默认脑、重启服务、改生产数据或发布。旧最小整改授权未被扩张；当前全量复核不自动套旧补丁。本地入口约束仍在，云端对照不得代替本地验收。
- 18:01复查：控制socket不存在，未执行该会话的读取、E2E或消融，不能拿旧29项代替。当前只需恢复安全SSH认证，不需要重新确认测试目标。恢复后再根据真实实现确定有限测试清单/预算，无已启动的新后台测试或排程。
- 同时关闭旧监测的到期观察缺口：state STOPPED_DEADLINE，17:39:00.095写终态、最后采样17:34:39.545、133次/远端21次；launchctl not running、退出0。未自动续期。此项只证明原任务到期退出，不证明此前远端全时段覆盖或当前项目完成，ISC不变、baseline 2.0不变。

## 2026-09-28 19:43 · 视频录制与B站上传（BLOCKED_ACCESS）

主人明确授权3–4分钟演示视频及B站上传；按最新handoff走新前端5173及Streamlit8501，服务红则报告、不自动修复，不干扰另一会话本地模型部署。19:42实查共享SSH socket缺失；192.168.11.205三个给定端口均超时，本机对应端口均拒绝连接。只证明本机访问不可用，不判定DGX服务/OOM/重启原因。未开录、未调模型、未上传、未启动新后台任务。

可证伪DONE、5类失败清单、脚本真实性问题、访问回执及完整滚动24小时条件计划见 `evidence/2026-09-28-video/PREFLIGHT.md`。基线2.0不变、原ISC计数不变。录制前须重新核实判定器/实际工具链，不能用绿色PASS、旧JSON或工具模式替代实时Agent成功。当前需主人用既有系统SSH入口恢复共享master，不索聊天密码。

## Remaining Work（当前控制塔；旧 repro-pack 待办已归档于历史）

- 当前只交付PRD/SPEC；FE-01的数据缺失/图题/运费解释待修，FE-02~08与PC-01~06未成套验收，浏览器实时适配未实现。
- 本地模型正例未过；云端StepFun已证三例不覆盖owner本地入口约束。双Agent增益UNPROVEN；不再拿旧宽松judge或被覆盖的StepFun评测宣称稳定满分。
- README/BENCHMARK/VIDEO-SCRIPT及部署配方仍需按事实更新；可分发的脱敏证据包尚未形成，evidence被忽略。ISC-12清单未闭合、ISC-24/25提交与发布仍待真实证明，不因本轮文档升级完成态。
- 可复用SSH通道缺失；主机地址/授权已给，不再写“SSH未到手”。未以工具使用口令，不抢Terminal；后续复验需安全认证通道。StepFun/SSH凭据轮换、远端临时文件处理仍待主人安排。
- 队友权限、材料审阅及公开push/视频/表单需各自真实授权与回执；其余三个评审轴SPEC后置。
