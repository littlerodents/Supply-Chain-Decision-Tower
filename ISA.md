---
task: "repro-pack 赛题交付"
slug: 20260922-dgx-hackathon-repro-pack
phase: in-progress
progress: 3/11
started: 2026-09-22T15:30:00Z
updated: 2026-09-22T19:04:48Z
iteration: 1
---

# ISA · repro-pack（第三届 NVIDIA DGX Spark 黑客松预赛）

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

9/29 中午前，预赛表单全字段提交完成，且每一项提交物都有本仓可复核的证据。

## Not yet specified

- StepFun 视频输入的确切 API 形态（D1 spike 探明；fallback：抽帧进图片模式）
- 队友档期确认结果
- 公开仓挂谁的 GitHub 账号（发布日 owner 拍板）
- 正例召回阈值在真实任务集上的可达性（D4 校准）

## Test Strategy

| isc | type | check | threshold | tool | anchors_to | severity |
|---|---|---|---|---|---|---|
| ISC-1 | bash | 样例录屏跑入口脚本，产出包目录 | exit 0 且三件套齐 | bash | derived | blocker |
| ISC-2 | bash | bugcard 过 schema 校验 | --validate exit 0 | bash | literal | blocker |
| ISC-3 | bash | 双模型对照报告存在且同输入 | 两模型各≥1条真实输出 | bash+eval | derived | blocker |
| ISC-4 | bash | 负例不产包 | 末行 NO_BUG_FOUND 且无 issue | bash | literal | blocker |
| ISC-5 | bash | npx skills 本地安装成功 | skills list 可见 repro-pack | bash | literal | blocker |
| ISC-6 | manual | Spark 上 OpenClaw eligible | 截图/日志日期+证据 | ssh | derived | blocker |
| ISC-7 | bash | evals.json 规模 | ≥8 正 ≥2 负 | python | literal | blocker |
| ISC-8 | eval | 字段召回/误触 | 召回≥70%，误触=0 | runner | derived | blocker |
| ISC-9 | bash | BENCHMARK.md 含 A/B 两栏实测 | 两栏非空有数 | bash | derived | blocker |
| ISC-10 | bash | README≥500字+无密钥扫描 | 字数≥500；grep sk-型命中=0 | bash | literal | blocker |
| ISC-11 | manual | 表单全字段提交 | 提交回执/截图日期 | manual | literal | blocker |

## Features

### F1 · 复现包主链路
Why: 没有「录屏进、包出」，一切叙事归零。

- [x] ISC-1: 对 `assets/samples/` 任意 ≤90s 正例录屏，`scripts/repro_pack.py` 退出码 0，产出含 `bugcard.json`、`frames/`、`repro.md` 的包目录
- [x] ISC-2: `repro_pack.py --validate <bugcard.json>` 对所有产出包 exit 0（按 `references/bugcard.schema.json`）
- [ ] ISC-3: `evidence/spike/dual-model.md` 含 3.7 Flash 与 step-5-preview 对同一录屏的真实输出对照（质量/延迟/成本三维），主备脑由此定案
- [x] ISC-4: 对每段负例录屏：不产包、不开 issue、stdout 末行 `NO_BUG_FOUND`（当前证据：合成负例 neg-001.mp4；T2 真实负例入 evals 后复跑）

### F2 · Skill 化与部署
Why: 交付单元是 skill，不是脚本；本地算力是赛题必答题。

- [ ] ISC-5: 通过 `npx skills add`（本地路径或仓库）安装后，agent 的 skills list 可见 `repro-pack` 且触发描述完整
- [ ] ISC-6: DGX Spark 上 OpenClaw `skills list --eligible` 显示 repro-pack ready（证据：终端输出+日期）

### F3 · 评测层
Why: 25% 技术深度分靠它；「带/不带」的实测是评委叙事核心。

- [ ] ISC-7: `evals/evals.json` ≥8 正例 + ≥2 负例，每例含 gold 字段与录屏文件引用
- [ ] ISC-8: runner 一键跑全量：正例 gold 三字段召回 ≥70%，负例误触 = 0（结果 JSON 落盘）
- [ ] ISC-9: `benchmark/BENCHMARK.md` 含「带包 vs 裸录屏（P1，若 buffer 不足则降级为带 skill vs 不带 skill 的 agent 表现对比）」两栏实测数据

### F4 · 赛事交付物
Why: 表单不交，前面全白干。

- [ ] ISC-10: README ≥500 字，含部署说明、技术栈说明、skill 结构说明；`grep -rE '(sk-|api[_-]?key.*=)'` 类密钥扫描 0 命中
- [ ] ISC-11: 表单全字段提交（仓库 URL / B 站 URL / 征文 URL / 合影），9/29 12:00 前完成

## Anti-claims

- A1: 仓库任何提交不含密钥、内网地址、owner 私人凭证（验证：历史 grep）
- A2: 负例永不产包/开 issue（验证：ISC-4/ISC-8）
- A3: 不实现 P2 安全接入端点（验证：无相关代码；README Future work 节存在）
- A4: 不提交需要 owner 个人凭证才能跑的出口（验证：出口仅 gh + 本地文件）

## Decisions

- **D1 选题**：repro-pack（①′重框架）。背景：原①「录屏→人读报告」被 owner 证伪——AI 时代报障从「描述」转向「接入」，但接入是特权不是默认；黑盒 SaaS/瞬态 bug/安全边界/审计四个场景仍需证据，且消费者已变成修复 agent。决定：产出物从「人读报告」改为「agent 可消费复现包」。否决的替代：screen2bug 原框架（前提失效）、作业拍照②（evals 客观化难、教育红线）、mini-SkillEvaluator 单做（演示弱）、TAO 串联④（撞车）。影响：SPEC/CONTEXT/演示脚本全以此为轴。
- **D2 主脑**：StepFun 双模型 D1 对照定主备（step-5-preview 已确认在 Coding Plan 额度内）。**D1 实测定案（provisional）：主脑 = step-3.7-flash**（中位延迟 10.18s vs 15.87s，成本略省，输出更稳，非 preview 无下线风险）；备脑/换脑演示 = step-5-preview。质量维度在合成片上无区分度，D4 真实任务集复确认。机制定案：视频走 video_url + base64 data URI，本地文件直进端点，无需上传。证据：evidence/spike/dual-model.md。
- **D3 运行面**：DGX Spark + OpenClaw（赛规「本地算力部署」为必答题）；Hermes 仅在 `npx skills` 原生支持时进 README，不投入开发。
- **D4 出口**：bugcard.json 必产出 + GitHub Issues 默认出口。
- **D5 工程流**：遵循 mattpocock/skills；仓库用本地 markdown tracker（`.scratch/BOARD.md`），因公开 remote 尚未创建且赛期仅 7 天；spec 置于仓库根 `SPEC.md`（偏离 to-spec 的 .scratch 惯例，为评委可见性）。
- **D6 档位**：P0（F1–F4 全部 ISC）/ P1（一键 runner、seeded-bug 修复 A/B、NIM 第二脑、Hermes）/ P2（安全接入端点，立碑不建）。
- **D7 排期**：baseline 2.0（D1 spike → D2 四件套 → D3 上 Spark → D4 冻结 → D5 材料 → D6 发布 → D7 提交），变更需 owner 明说。
- **D8 台账**：本项目满足 ISA 条件（交付物≥3、跨会话、第三方复核），用 ISA.md 替代 STATUS+DECISIONS 两件套；STATUS.md 仅作仪表盘。

## Verification

（ISC 关闭后回填，只记真实跑过的命令与结果）

D1 夜班全套（2026-09-22T19:04Z，均真跑）：
- ISC-1: `python3 repro_pack.py assets/samples/clip.mp4 --out packs/d1-pos --no-issue` → exit 0，末行 `PACK:.../packs/d1-pos`，包内 bugcard.json + frames/(3 帧) + repro.md（evidence/spike/e2e.txt）
- ISC-2: `repro_pack.py --validate packs/d1-pos/bugcard.json` → `VALID`；红队坏卡×2 仍以「缺必填字段/枚举越界」被拒
- ISC-4: `repro_pack.py assets/samples/neg-001.mp4 --out packs/d1-neg --no-issue` → exit 0，末行 `NO_BUG_FOUND`，`packs/d1-neg` 不存在
- 机制: 探针梯子 text(1.16s)/image(2.88s)/video(5.0s) 全过；双模型 3+3 轮真实输出 → dual-raw.json

## Remaining Work

- ISC-3 质量维度：待 T2 真实任务集在 D4 定案（合成片上两模型 1/3 平，无区分度；教训：gold 关键词要双语、type 口径要写死）
- ISC-1/4 目前证据基于合成片，T2 真实录屏到位后复跑确认（不重开 ISC，追加验证）
- SSH 未到手（阻塞 ISC-6/D3）；.env 由 owner 手写（闸门拦截了 agent 写入，设计行为）
- 队友档期未回执
