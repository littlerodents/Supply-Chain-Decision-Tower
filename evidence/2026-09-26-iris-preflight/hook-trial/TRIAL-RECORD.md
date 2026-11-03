# hook-trial 试验记录 · pi-supply-read-guard（2026-09-26 晚）

> 授权范围（owner 2026-09-26）：临时启用仅匹配该控制塔 Skill 错误 `read` 路径的 Gateway `before_tool_call` 纠偏 hook，新会话测正负例；重启/停止现有服务须先请示；试验结束安全停用并验证无影响。全程复用 owner 已登录的 DGX Terminal 会话（Terminal AppleScript 通道，未新建 SSH 连接）。

## 交付物（本地，均真实存在）

- `guard.mjs` — `rewriteSkillRead` 纯函数：仅当 `toolName==='read'`、params.path 完全等于观察到的错误路径 `/home/parker/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md`、`ctx.sessionId` 以 `pi-dgx-hooktest-` 开头、且 `$HOME` 下目标文件存在时返回 `{params:{...原参数, path:正确路径}}`（不改原对象）；其余一律 `undefined`（fail closed）。
- `test/guard.test.mjs` — 7 用例：唯一正例改写 + 路径近失误/其他 skill/穿越 + 会话前缀精确大小写 + 无 HOME/无目标文件/params null 边界 + 最小事件。`node --test` → **7/7 pass**。
- `plugin/pi-supply-read-guard/` — `package.json` + `openclaw.plugin.json` + `index.ts`（纯 JS 语法；handler 全 try/catch 包裹永不抛错——`before_tool_call` 对抛错 fail-closed 拦调用，必须反向 fail-open 保护无关会话）+ 自包含 `guard.mjs` 副本（测试锁字节一致）+ `test/plugin.test.mjs`（stub `openclaw/plugin-sdk/plugin-entry` 沙箱 + 子进程 HOME 控制）→ **5/5 pass**。
- `bin/dgx-term.py` + `bin/send.sh` + `bin/remote.sh` — Terminal 通道助手（窗口标题/空闲双重守卫、唯一标记对提取、--timeout 真实限界）。
- `docs-openclaw/` — 从 DGX 安装版 2026.9.5 抓回的插件文档原文（hooks.md/tool-policy.md/reference.md 等 6 件，b64 分块回传后 tar 解包，gzip 校验通过）。
- `results/` — 三次会话完整 JSON（pos1/pos2/neg1，远端 /tmp 同名文件 b64 回传，字节数一致）。

## DGX 操作日志（全部经 Terminal 通道，屏幕真实回显）

- 基线：Gateway `openclaw-gateway` PID **2010301**（已运行 1 天+），spawn-broker PID 2010380，面板 streamlit PID 2006235；`/tmp/pi-supply-read-guard` 不存在；config 无 `reload` 键（默认 hybrid 热重载）；目标 `SKILL.md` 真实存在（4072 字节）。
- 上传：插件 4 文件 tar+gzip+base64 分块（2216/2216 字节），远端解包后 sha256 与本地逐文件一致（78c021…/b3c24f…/18e43e…/67b739…）。
- `openclaw plugins install --link /tmp/pi-supply-read-guard --force` → `Linked plugin path: /tmp/pi-supply-read-guard` + **`Applied in Gateway generation 3`**（热应用）；PID 2010301 不变。
- `openclaw plugins enable pi-supply-read-guard` → `Enabled plugin "pi-supply-read-guard"`；PID 不变。
- `openclaw plugins inspect pi-supply-read-guard --runtime --json` → `enabled:true / activated:true / activationSource:explicit / source:/tmp/pi-supply-read-guard/index.ts`；`grep -c before_tool_call` = 1（hook 已注册）；PID 不变。
- 验收会话后 `openclaw plugins disable pi-supply-read-guard` → `Disabled plugin`；**PID 2010301 / 2010380 / 2006235 三者全程未变**（安装→启用→验收→停用零重启）。

## 验收会话（CLI `openclaw agent --session-id <id> --json --timeout 420 --message <问句>`）

| 会话 | 问句 | 结果 | 关键证据 |
|---|---|---|---|
| `pi-dgx-hooktest-pos1` | SF 仓库 SKU13001 未来 12 周够卖吗（自然问句） | **FAIL** | 91807ms / 7 调用 1 失败；终答仅「Now let me read the SKILL.md…」即自停；无 119282/3268/Nature Source/decision；全程未出现 `/home/parker`（hook 无从触发） |
| `pi-dgx-hooktest-pos2` | 帮我决策：SF SKU13001 按 12 周预测补多少（自然问句变体） | **FAIL** | 39744ms / 3 调用 0 失败（仅 tool_search）；终答仅「Let me search more specifically…」即自停；无关键数字；5 处 parker 均为系统提示内 `/home/sparker` 正常路径 |
| `pi-dgx-hooktest-neg1` | Seattle 仓库 SKU13001 未来 1 周够卖吗 | **PASS** | 58246ms / 7 调用 2 失败（tool_search/tool_choose/ls/read/exec）；终答末行 `**结论**：NO_REORDER:100（库存充足，可支持本周销售）。`；库存 300/预测 200/缺口 +100 与工具直算一致；无补货建议 |

## 结论与灰度

- **已验证**：插件可装、可热启用、可热停用，Gateway/broker/面板 PID 全程不变；本地单元 7/7 与插件隔离 5/5；负例首次以 `NO_REORDER:100` 末行通过（插件启用状态下）。
- **UNPROVEN**：hook 的 vivo 改写效力——两个正例会话模型均未再提交 `/home/parker` 错误路径，hook 没有触发机会（「未触发≠修复成功」，也不构成反证）；其效力的直接证据仍只有沙箱测试与既有脱敏轨迹的红灯复放。
- **正例失败根因不变**：本地 nemotron-3-super:120b（ollama，runner=embedded，thinking=off）「宣告动作即自停」的回合管理问题，与 Skill 路径无关；ISC-14 维持未过，项目维持 **REOPENED**。
- 负例单样本通过不关闭 ISC-15（此前同题 26 调用连败史在案；插件现已停用；非决定性模型）。

## 通道工具自证（监控质疑闭环）

- 远端退出码：`false; echo RC_FALSE=$?` → `RC_FALSE=1`；`true` → `RC_TRUE=0`。
- `--timeout` 限界：`sleep 8` 预算 3 → 5.7s TIMEOUT 且无输出泄漏；预算 30 → 11.0s 成功返回。（修复过两版缺陷：固定次数轮询无视预算；滞后宽限击穿短预算——现为「≥20s 预算才带 ≤15s 宽限」。）
- 中途事故与处置：误判会话死机实为 Terminal `contents` 读取滞后 → 重构为唯一标记对提取；期间误发的一条嵌套 ssh 在主机密钥确认处以 `no` 拒绝，未建立连接。

## 未做 / 未改

- 未改 `tools/run_evals.py` 与旧评测文件；未动 `SKILL.md`/`AGENTS.md`；未重启或停止任何服务；未发布；未跑 Iris；远端 `/tmp/pi-supply-read-guard` 与 `/tmp/p*.json` 留存（含 /tmp/p.b64 暂存），可由 owner 清理。
- SSH 口令仍在聊天与既有文档中暴露，轮换待办不变。
