# BOARD · repro-pack 工单板（v2 · 新题工单 · 2026-09-24 重排）

> 旧 repro-pack 工单已随 D12 改道归档（其 skill/脚本保留在仓，作为过程资产与征文素材）。
> 负责人：O=Evander，T=abloom25，机主=alingalingling。状态：todo/doing/done/blocked。

## 主线（锁题①后立即生效）

| # | 负责人 | 状态 | 依赖 | 票面与验收 |
|---|---|---|---|---|
| N1 | O | **done** | 锁题 | ✓ 判决 GO（docs/N1-VERDICT.md）：PAL 五段+7 工具+411 行提示词，依赖面 pandas/numpy/sqlite3；②备胎解除 |
| N2 | O | **done** | N1 | ✓ SPEC v2 锁定（架构反转）+ ISA 重锚（ISC-12~25，0/14） |
| N3 | O | todo | N2 | **skill 主链**：processors→skill scripts、SKILL.md（渐进披露+触发词+负触发）、输出契约（PACK 式复用）、3.7-flash 主脑接入 |
| N4 | T | todo | N3 | **evals + runner**：gold 数学底座（补货量/服务水平唯一解）、负例集、裸 agent vs 带 skill A/B |
| N5 | O | todo | N3 | **Spark 部署**：skill 入 OpenClaw workspace（eligible 验证）、Streamlit 塔台跑通、换脑演示素材（3.7-flash↔本地 120B） |
| N6 | T | todo | N4 | **BENCHMARK.md + README**（≥500字、部署/技术栈说明、skill 结构展示） |
| N7 | 罗登思 | todo | N5,N6 | **B 站演示视频**（≤3min：MIT 95% 开场→装 skill→问一句出决策→塔台 UI→换脑→BENCHMARK；传 33official） |
| N8 | T | todo | — | **十日谈征文**（CSDN/知乎，开发历程随手记，9/28 发，标注 AI 生成） |

## 里程碑：9/26 晚冻结 v0.1.0 → 9/28 发布（公开 push 需 O 点头 + 合影）→ 9/29 12:00 前表单提交。

## P1 池（buffer 才吃）：① 一键重跑 runner → ② cuDF 数据层加速（万行级扩容后）→ ③ NIM 第二脑（key 服务组修复后）→ ④ Hermes 可移植性演示

## 已归档（repro-pack 旧线）：T1-T12 见 git 历史；其战果（4/11 ISC、负例契约、gh 出口、双模型对比）全部继承到新线
