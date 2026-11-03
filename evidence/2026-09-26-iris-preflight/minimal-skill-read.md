# 最小可复现故障：Skill 读取请求中的错误 home 路径

> 2026-09-26 下午，只读分析现存脱敏轨迹；**不是**对最终补货决策故障的完整根因证明。原始脱敏导出仍在 DGX 用户目录，未复制会话全文或凭据。`evidence/` 被 gitignore，私仓不会自动附带本文件。

## 来源与对照

- DGX 导出：`~/.openclaw/trajectory-exports/pi-dgx-debug-explicit-20260926/events.jsonl`，SHA256 `7c5774c9d043c20879eecef935cac63aab3d73c3c9850b76923475383e600231`。按 `toolCallId` 关联 `tool.call` 与 `tool.result`，去重后只看同一会话中的 **2 次 Skill `read`**，相隔约 5 秒。
- `2026-09-26T07:03:22.474Z`：`read('/home/parker/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md')` → `success=false`，`File not found`。
- `2026-09-26T07:03:27.773Z`：导出中成功调用的路径被脱敏成 `$WORKSPACE_DIR/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md` → `success=true`，返回内容含「补货决策 SOP」。**`$WORKSPACE_DIR` 是脱敏占位符，不当作可直接执行的真实路径。**
- 导出共 72 个事件；错误路径在可见事件中最早出现于 `assistant.message`（同为 `07:03:22.474Z`），随后进入 `tool.call` / `tool.result`。导出里没有更早的这个字串，但不能据此排除未导出的隐藏上下文或证明模型为何生成它。
- 同机、同一脚本只替换 home 路径重演：读取 `/home/parker/.../SKILL.md` → **exit 1**；读取 `/home/sparker/.../SKILL.md` → **exit 0、`SOP_READ_OK`**。DGX 的 `openclaw config get agents.defaults.workspace` 与 `skills info ... filePath` 均指向 `/home/sparker/...`；实际 `/home/parker` 不存在。另一独立会话的脱敏轨迹还有 3 次指向 `/home/parker` 的失败 `read`。

## 秒级红灯（在已有 DGX 会话中执行；不调用模型、不改文件）

```bash
python3 - <<'PY'
import json, pathlib, sys
p = pathlib.Path.home() / '.openclaw/trajectory-exports/pi-dgx-debug-explicit-20260926/events.jsonl'
events = [json.loads(line) for line in p.open()]
calls = {e['data'].get('toolCallId'): e['data'].get('arguments', {}).get('path', '')
         for e in events if e.get('type') == 'tool.call' and e['data'].get('name') == 'read'
         and isinstance(e['data'].get('arguments'), dict)}
results = {e['data'].get('toolCallId'): e['data'] for e in events
           if e.get('type') == 'tool.result' and e['data'].get('name') == 'read'}
wrong = '/home/parker/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md'
bad = [key for key, path in calls.items() if path == wrong and key in results
       and results[key].get('success') is False
       and 'File not found' in str(results[key].get('result', {}).get('details', {}).get('error', ''))]
print('BAD_SKILL_READS', len(bad))
sys.exit(1 if bad else 0)
PY
# 本轮真跑：BAD_SKILL_READS 1；exit 1。换成以后新导出的同格式轨迹，若不再发错路径则应 exit 0。
```

**证伪边界**：已排除「Skill 文件根本不存在」和「正确路径在本机不可读」；模型发出的 `tool.call.arguments.path` 确实是错误路径，不能把它归因为 `scripts/tools.py` 运费算法。但成功读过 SOP 的会话最终仍未满足 JSON 契约，故**纠正路径至多解决这一类失败，不能据此声称主链修好**。修复必须在全新 OpenClaw 会话重跑正例 JSON 和负例 `NO_REORDER:100`；本轮未做任何修复或模型复跑。

## 修复可行性复核（2026-09-26 下午，只读）

- `openclaw skills info supply-chain-control-tower --json` 再次返回正确的 `/home/sparker/.../SKILL.md`，`eligible/modelVisible/userInvocable=true`；失败会话的 `systemPromptReport.skills.entries` 也含该 Skill。安装版 `docs/tools/skills.md:773–779` 说明 Skill XML 注入包含 `location`。脱敏 `system-prompt.txt` 本身只有占位内容，**不能据此断言实际 prompt 的具体路径文字**；四份注入工作区文件中均无 `/home/parker` 或 `/home/sparker` 字串。
- 失败路径最先出现在可见 `assistant.message`，同一会话在正确读到 SOP 后仍走了后续工具、最终输出约 836 字符的 Markdown，**没有 `"decision"` 字段**；独立负例终答约 73 字符，没有 `NO_REORDER:100`。因此文档正文、仓内 `tools.py` 或一次路径纠偏都不是已证实的完整修复位；本地改过 `SKILL.md` 正文但新入口仍失败的历史结果也一致。
- 安装版 `docs/plugins/hooks/reference.md:148` 和 `docs/plugins/hooks/tool-policy.md:66–72` 描述 `before_tool_call` 可重写 `read` 参数；这属于 **Gateway 全局插件/工具策略变更**，未授权时不安装、不启用、不热重载。`/home/parker` 建目录/链接亦不做。当前只验证了可复放的局部故障；没有可在本 Skill 文件里修好「读取前」错误的确定性修复证据，主链仍是 REOPENED。

