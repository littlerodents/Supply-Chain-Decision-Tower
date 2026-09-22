# STATUS · repro-pack（仪表盘）

> 台账主体是 ISA.md（决策/验证都在那）。这里只回答：现在在哪、卡在谁身上。

- **阶段**：D0 已完成（仓库+台账落地）→ D1 待启动
- **日期**：2026-09-22 深夜（iteration 1）

## 卡在 owner 手里的三个输入

1. **Spark SSH 访问方式**（阻塞 ISC-6，不阻塞 D1 spike）
2. **StepFun API key**（阻塞 spike 与 ISC-1/3；plan 已领、step-5-preview 已确认在额度）
3. **队友档期确认**（18:30–21:30 假设不变则无影响）

## 下一步（按序）

1. owner 给 key → 跑 `tools/spike_plan.md` 的探针梯子（text→image→video）→ 双模型对照 → `evidence/spike/dual-model.md` 定主备脑
2. 同步开 `.scratch/BOARD.md` 上的 T2（任务集录屏，队友线）
3. spike 过 → T3 主链路动工；不过 → 走 fallback（抽帧进图片模式）并回 ISA 记 D 节

## 风险雷达

- StepFun 视频输入 API 形态未实测（全项目最大技术风险，D1 见真章）
- 队友档期未确认（若砍半，P1 全弃保 P0）
