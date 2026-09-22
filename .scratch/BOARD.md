# BOARD · repro-pack 工单板

> 一行一票。负责人 O=Evander，T=队友。状态：todo/doing/done/blocked。

| # | 负责人 | 状态 | 依赖 | 票面与验收 |
|---|---|---|---|---|
| T1 | O | **done** | key | Spike 完成：梯子全绿（视频=video_url+base64 data URI）；主脑 provisional step-3.7-flash；质量维度挂 D4；结论文档 evidence/spike/dual-model.md |
| T2 | T | todo | — | **任务集**：录 8–12 段 30–90s 正例 + 2–3 段负例；每段写 gold answer（bug 类型/位置/严重度）；落 `assets/samples/` + `evals/evals.json` |
| T3 | O | **doing** | T1 | 主链路：合成片 E2E 已通（ISC-1/2 已关）；待 T2 真实录屏复跑后关闭 |
| T4 | O | todo | T3 | **包装配+出口**：frames 抽取、repro.md 渲染、gh issue、输出契约（`PACK:` 末行；负例 `NO_BUG_FOUND`）（ISC-4） |
| T5 | O | todo | T3 | **SKILL.md 触发工程**：frontmatter 触发词+负触发、正文<5K token、references 下沉；`npx skills` 本地安装验证（ISC-5） |
| T6 | T | todo | T2,T4 | **evals runner**：一键跑全量任务集，输出字段召回/误触/成本 JSON（ISC-7/8） |
| T7 | O | todo | T4,T5,SSH | **上 Spark**：OpenClaw 安装、skill 入 workspace、`skills list --eligible` 截图证据（ISC-6） |
| T8 | O | todo(P1) | T7 | **换脑素材**：本地 Qwen 图片模式跑通同链路；NIM 第二脑对照（buffer 才吃） |
| T9 | T | todo | T6,冻结 | **BENCHMARK.md**：A/B 全量实测两栏数据（ISC-9）；冻结 9/26 晚后跑 |
| T10 | T | todo | T9 | **README**：≥500 字、部署说明、技术栈说明、skill 结构、评测方法（ISC-10 前半） |
| T11 | T | todo | T7,T9 | **演示视频**：≤3min，脚本：痛点(接入优先)→装skill→跑→换脑→BENCHMARK；传 B 站 |
| T12 | T | todo | — | **十日谈征文**：CSDN/知乎，开发历程随手记，9/28 发，标注 AI 生成 |

里程碑：9/26 晚冻结 v0.1.0 → 9/28 发布（push 公开需 owner 点头+合影）→ 9/29 12:00 前表单提交（ISC-11）。
