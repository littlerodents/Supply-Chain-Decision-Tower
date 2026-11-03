# 2026-09-26 下午 · OpenClaw 显式技能引用诊断（失败，止损）

> 仅用 owner 已登录的 Terminal SSH 通道；没有新建密码连接、改 Gateway 配置或重启服务。直接 Gateway 输出保存在远端私有 `/tmp/pi-dgx-explicit-skill.json`、`/tmp/pi-dgx-neg-skill.json`，并非已公开证据；本记录为代理读取的机器证据，非主人签收。

## 控制变量

- `openclaw config get agents.defaults.workspace` → `/home/sparker/.openclaw/workspace`；Gateway 进程属于 `sparker`，`/home/parker` 不存在。
- `openclaw skills info supply-chain-control-tower --json` → `eligible=true`、`modelVisible=true`、`userInvocable=true`、`filePath` 等于正确的 `/home/sparker/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md`。
- 旧会话的 `systemPromptReport` 有该 Skill 的摘要条目，但不保证模型已读取完整正文；脱敏轨迹显示模型此前曾把 Skill 名称当工具、读取 `/home/parker`。
- 当前安装版 OpenClaw `docs/tools/skills.md` 的「Reference a skill in a prompt」节（262–281 行）明确支持在 CLI/Gateway 的消息里用 `$skill-name` 显式引用，并要求模型先读对应 `SKILL.md`。本轮仅改变用户问句是否显式引用；不把它当自动触发或正式产品契约。

## 新鲜结果

- 正例新会话 `pi-dgx-20260926-explicit-skill`：同一 SKU 13001 / San Francisco / 12 周问句前加 `$supply-chain-control-tower`。CLI `status=ok`，159192ms、10 次工具调用、2 次失败。输出 Markdown 含 **3268 件、Nature Source Coffee、34.5+2.0、总价 119282**；但没有 `decision`/`total_cost` 等合约 JSON 字段，**严格正例 FAIL**。内建脱敏轨迹显示至少有 read/exec 工具返回，不能据此宣称终答符合契约。
- 负例**独立新会话** `pi-dgx-20260926-neg-skill`：`$supply-chain-control-tower Seattle 仓库 SKU 13001 未来 1 周够卖吗？需要补货吗？`。CLI `status=ok`，151142ms、26 次工具调用、19 次失败；终答只说要检查 workspace，**没有 `NO_REORDER`**。同机直接运行 `tools.py gap --sku 13001 --location Seattle --weeks 1` → 当前库存 300、预测 200、缺口 **+100**，故期望 `NO_REORDER:100`。负例入口 **FAIL**，不能称零误触。
- 干预只改善了单次正例的自然语言数字，没有让正例 JSON 与负例门同时通过；不能作为「一装即用」的兜底。未改变远端 Skill（上轮临时文档试验已回滚）、未发布、未运行 Iris。

## 止损和下一判据

停止对本地 120B 的提示词反复试错。只有**两个独立自然问句正例**输出工具证据充分、精确的决策 JSON（本题总价 119282），且负例新会话以 `NO_REORDER:100` 结束并无补货建议，才可关闭入口验收；退出码 0、Skill ready、正确数字的 Markdown 都不够。当前先把 README / BENCHMARK / 视频脚本降格到证据允许的口径，旧 StepFun 12 题文件被覆盖、Nemotron 三轮 12/9/11 与权限不等对照都要显式标注。
