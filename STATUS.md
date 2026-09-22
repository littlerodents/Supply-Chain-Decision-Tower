# STATUS · repro-pack（仪表盘）

> 台账主体是 ISA.md（决策/验证都在那）。这里只回答：现在在哪、卡在谁身上。

- **阶段**：D1 spike **完成**——kill-switch #1（视频机制风险）解除，主脑 provisional `step-3.7-flash`
- **进度**：ISC 3/11（ISC-1 正例产包 / ISC-2 validate 契约 / ISC-4 负例零误触）
- **更新**：2026-09-22T19:04Z（iteration 1）

## 卡在 owner 手里的三件事

1. **Spark SSH 访问方式**（阻塞 D3 / ISC-6，不阻塞其他）
2. **`.env` 手写**（闸门拦了 agent 写入，这是设计行为）：在仓库根跑
   `printf 'REPRO_API_KEY=<你的key>\nREPRO_BASE_URL=https://api.stepfun.com/v1\nREPRO_MODEL=step-3.7-flash\n' > .env`
3. **队友档期回执**（18:30–21:30 假设不变则无影响；T2 录屏是他今晚的活）

## 下一步（按序）

1. T2：队友录真实任务集（gold 设计三教训见 `evidence/spike/dual-model.md`：双语关键词 / type 口径写死 / 负例≥2）
2. T5：SKILL.md 触发工程 + `npx skills` 本地安装验证（O 线，无阻塞）
3. D3（等 SSH）：Spark 装 OpenClaw + skill 入 workspace

## 风险雷达

- ~~视频输入机制~~ **已死**（base64 data URI 直接过）
- 真实录屏复跑：ISC-1/4 证据目前基于合成片，T2 到位后追加验证
- key 曾在聊天明文出现——建议赛后在 StepFun 控制台轮换
