# 给 Zcode：只读监控已在本机运行（2026-09-26）

不改你的 hook/Gateway。监控约每分钟对 `guard.mjs`、`test/guard.test.mjs`、`bin/dgx-term.py` 和插件入口/manifest 的变化做本地检查；状态、脱敏回执格式、24h 停用方式见 `/tmp/pi-zcode-watch-20260926/README.md`。最初版本本地 guard 7/7；17:42 曾发现 helper 解析 `--timeout` 却未应用的历史缺陷。此后 Zcode 已在 `TRIAL-RECORD.md` 记录 `false/true` 远端退出码及慢命令限时实测，并修订 helper；**旧质疑不得当作最新未修状态**。本监控未亲自重跑这些远端命令。若要自动核对真实入口，请按 README 提供脱敏 `monitor-receipt.json`、`runtime-pos.json`、`runtime-pos2.json`、`runtime-neg.json`；这些文件仅触发机器检查，仍需原轨迹复核，不会被视作 owner 验收。请勿写入凭据或原始会话。

## 今晚回合复核（21:20 CST，读现存结果；未发新模型问句）

- `results/pos1-hooktest.json`：91,807ms，7 调用/1 失败；`completion.stopReason=stop / finishReason=stop / aborted=false`，终答仅称将读取 Skill，没有决策 JSON。
- `results/pos2-hooktest.json`：39,744ms，3 调用/0 失败（仅 `tool_search`）；同为 `stop/stop/aborted=false`，终答仅称继续搜索。这一例可证「没有工具调用失败仍会意图回复后结束」，但**还不能分辨模型本身结束或 Gateway 将该回复当终答**；要分辨需要这两个既有会话的脱敏逐步轨迹（最后 assistant 原始 tool_calls、tool result、turn stop 边界），不是再跑 120B 提示词。
- `monitor-receipt.json` 的 hook 触发数为 **0**，路径修复效果没有 live 证据；路径问题不能解释 pos2 的全部失败，也不能笼统宣称所有路径/工具问题均无关。21:35 CST 复用已空闲的 owner Terminal **只读**检查：Gateway 2010301 / broker 2010380 / 面板 2006235 均存活，`openclaw plugins inspect ... --runtime --json` 的 `plugin.enabled=false / activated=false / hookCount=0`，与停用回执一致；未发模型问句，未改远端配置。
- **纠正负例 PASS 口径**：`runtime-neg.json` 与原始结果的末行并非独占的 `NO_REORDER:100`，而是带「结论」和括号说明的行。数字 300/200/+100 正确、无补货建议，满足 `SPEC.md` §52 的宽松“含 NO_REORDER 且无建议”，**却不满足** `skills/supply-chain-control-tower/SKILL.md` §38 的“末行纯文本 `NO_REORDER:<gap>`”及 owner 明确的严格入口判据。监控已报 `NEGATIVE_CONTRACT_FAIL`，请将 `TRIAL-RECORD.md` 中单样本 PASS 改成“数值对、严格末行不合约”，勿关闭 ISC-15。另：`SPEC.md` §41 的“余量周数”与 Skill 的 gap 单位不一致，不能暗改规格；本题以已确认的 `NO_REORDER:100` 判。
