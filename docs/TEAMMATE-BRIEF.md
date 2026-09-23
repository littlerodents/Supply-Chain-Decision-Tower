# TEAMMATE-BRIEF · 给队友的完整上下文（5 分钟读完）

> 你拿到的是 repro-pack 项目的全量背景 + 你今晚开工的 T2 任务规格。
> 读完有疑问，今晚开会对齐；不想读字，先跳到「你的任务」。

## 一、我们在做什么（为什么值得做）

报 bug 的传统形态——录屏/截图 + 人写描述——正在被 agent 时代改写：**能接入的场景，对方 agent 直接远程接手，描述已死**。但接入是特权不是默认——黑盒 SaaS、瞬态 bug、安全边界、审计要求——这些场景里录屏仍是唯一目击证据，而消费证据的已从人类工程师变成了**修复 agent**。

**repro-pack 就是这座桥**：一段操作录屏进 → 产出一个修复 agent 可直接开工的「复现包」（结构化 bug 卡 + 带时间戳关键帧 + 画面错误原文 + 复现步骤）→ 开成 GitHub issue。无 bug 的负例只回一句 `NO_BUG_FOUND`，绝不产包。

## 二、赛事硬约束（为什么是 7 天冲刺）

- **9/29 中午前交预赛表单**：公开仓 URL + B 站演示视频 URL + ≥500 字 README（含部署/技术栈说明）+ 十日谈征文 URL（CSDN/知乎，标注 AI 生成）+ 团队合影
- 评分权重：创新实用 25% · 技术深度 25%（原话点名「Skills 设计与融合」）· 完整性 20% · 平台适配 15%（点名 StepFun 模型使用 + 本地算力 DGX Spark）· 演示 10% · 征文 5%
- 里程碑：**9/26 晚冻结 v0.1.0** → 9/28 发布 → 9/29 提交

## 三、技术全景（30 秒版）

```
录屏(≤90s) → step-3.7-flash(主脑,视频原生) → 复现包(bugcard.json + frames/ + repro.md) → gh issue
                                              ↘ 负例 → NO_BUG_FOUND,零产包(P0 硬指标)
评测层: evals.json 任务集(你的T2) → runner A/B → BENCHMARK.md
运行面: DGX Spark + OpenClaw(本地算力叙事); 备脑/换脑演示 = step-5-preview(1M 上下文)
```

主脑定案依据（D1 实测 3+3 轮）：3.7-flash 中位 10.18s vs 5-preview 15.87s，输出零漂移，生产级 vs preview。详见 `evidence/spike/dual-model.md`（本文件也是你 T2 的 gold 设计规范）。

## 四、分工（O=Evander，T=你）

| 线 | 任务 |
|---|---|
| O | 主链路 skill、Spark 部署、换脑、发包 |
| **T（你）** | **T2 任务集录屏+gold** → T6 evals runner → T9 BENCHMARK → T10 README → T11 演示视频（B 站传你的 33official）→ T12 征文主笔 |

节奏：每晚 18:30–21:30；你的工单互不阻塞，T2 最优先。

## 五、你的任务 · T2 任务集（今晚可开工，不需要 API key）

**录屏要求**：30–90 秒（硬上限 120s，超了主链路直接拒收）、mp4/mov/webm、命名 `pos-001.mp4`…/`neg-001.mp4`…

**正例 8–12 段**，覆盖型谱（每型 1–2 段，型名就是 bug 卡的 `type` 枚举，gold 用同一套词）：

| type | 画面长什么样 |
|---|---|
| ui-rendering | 布局塌陷/错位/样式炸了 |
| runtime-error | 报错弹窗、console 红字 |
| network | 请求失败、加载超时、断网页面 |
| data-display | 数字/列表/图表显示不对 |
| interaction | 点击无响应、按钮卡死 |
| crash | 白屏、整页崩掉 |

可以「自导自演」造 bug（断网、改 DOM、贴假弹窗），但操作要像真实使用；**红线：不含真实工作/内部系统录屏，不含个人信息**。

**负例 2–3 段**：完全正常的操作。加分项：录一段「像 bug 但不是」的（比如正常 loading 转圈）——负例零误触是全项目 P0 硬指标，越刁钻越值钱。

**每段配一条 gold**（照抄这个模板填，双语关键词是铁律——模型可能中文答）：

```json
{"id": "pos-001", "kind": "positive", "recording": "assets/samples/pos-001.mp4",
 "scenario": "一句话场景",
 "gold": {"type": "runtime-error", "severity": "major",
          "location_kw": ["保存", "save", "设置"], "timestamp": 12.5}}
```

- `type`：用上面型谱的词，写死口径，别自造词
- `severity`：blocker/critical/major/minor/trivial 五档
- `timestamp`：bug 出现的大致秒数（±3s 容差）
- 负例：`{"kind": "negative", "gold": {"expected": "NO_BUG_FOUND"}}`

**交付**：仓库 clone 后直接把录屏放 `assets/samples/`、gold 追加进 `skills/repro-pack/evals/evals.json`，推分支；或先传文件给 O 入库，都行。

## 六、仓库与协作

- 仓库：`https://github.com/littlerodents/repro-pack`（私有，找 Evander 开权限）
- 先读：`SPEC.md`（共识）→ `CONTEXT.md`（黑话表）→ `AGENTS.md`（仓规矩：密钥零提交、负例零误触）
- 你 T2 不需要 API key；到 T6 runner 阶段需要时 Evander 配 `.env`（已在 gitignore）

有任何和这份简报冲突的信息，以简报 + 仓库 `ISA.md` 为准；都不清楚就问，7 天冲刺别猜。
