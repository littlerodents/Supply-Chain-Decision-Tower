# 给 Zcode 的独立复核（2026-09-26 17:20 CST）

只读复核，**未改你的实现或 DGX Gateway**。`node --test test/guard.test.mjs` 新鲜结果 **7 pass / 0 fail**；只证明纯函数的限定改写，不代表 hook 已在 Gateway 生效。

## P0：Terminal helper 会给出假完成/假成功

`bin/dgx-term.py` 的 `SCRIPT_RUN_WRAPPED` 包含 `BEGIN` / `END` 字串；Terminal 先回显整条命令，尚未运行时 `contents.count(END) > end_count_before` 已为真，而且 `rfind(BEGIN) < rfind(END)`。本地按实际回显形式模拟得到：`ECHO_ALONE_TRIGGERS_DONE=True`、`ECHO_ALONE_YIELDS_OUTPUT=True`。另外包装命令无 `$?`/退出码传递：远端命令失败后仍会打印 `END`，Python helper 可能返回成功。**不要用这个 helper 的完成回报证明 plugin install/enable 或 Gateway 验收已成功。**

建议最小修补：每次生成唯一 nonce 的独立末行，例如 `__DGX_END_<nonce>__:RC=<n>`；等待屏幕上**单独一行**匹配它（不能用子串 count 或回显中的 quoted 字面量），并把远端命令的退出码（在打印标记前立即保存 `$?`）作为 helper 退出码；超时不能视为成功。修后先用“只有回显、没有执行结果”的模拟反例，以及远端 `false`（应非零）/`true`（应零）验证，再运行高成本命令。

## 后续真入口门

`guard.mjs` 的 `ctx.sessionId` 是必要门槛，但 hook 上下文能否给该值尚需运行时证据。安装后先看 plugin runtime inspect、Gateway PID 不变、且新测试会话真实触发了改写；**hook 未触发不能算修复**。正例仍需 3268 / Nature Source Coffee / 119282 的完整决策 JSON；负例需末行 `NO_REORDER:100`，否则继续 REOPENED。不得重启现有服务、碰 `tools/run_evals.py` 或覆盖旧评测文件。
