#!/usr/bin/env bash
# 双智能体补货决策流水线：决策智能体出单 → 审计智能体独立复算对账
# 用法：two-agent-pipeline.sh "<问句>" [tag]   （tag 默认 take$$，每次运行自动唯一）
set -euo pipefail
export PATH=$HOME/node26/bin:$PATH

Q="${1:?用法: $0 \"<问句>\" [tag]}"
TAG="${2:-run$$}"
OUT="$HOME/isc-submission-20260927/素材"
DEC_SID="pi-dgx-2ag-${TAG}-dec"
AUD_SID="pi-dgx-2ag-${TAG}-aud"

echo "== 第一环：决策智能体（main / supply-chain-control-tower）=="
openclaw agent --session-id "$DEC_SID" --message "$Q" --json > "$OUT/$DEC_SID.json"
python3 - "$OUT/$DEC_SID.json" "$DEC_SID" <<'PYEOF' > /tmp/2ag-decision-extract.txt
import json,sys
d=json.load(open(sys.argv[1]))
meta=d['result']['meta']
print(meta.get('finalAssistantVisibleText'))
print("\n[[DEC_JSON]]")
text=meta.get('finalAssistantVisibleText') or ''
blocks=[b for b in text.split('```') if b.strip().startswith('json')]
print(blocks[-1].strip()[4:].strip() if blocks else '{}')
PYEOF
cat /tmp/2ag-decision-extract.txt

DEC_JSON=$(sed -n '/\[\[DEC_JSON\]\]/,$p' /tmp/2ag-decision-extract.txt | tail -n +2)
echo
echo "== 第二环：审计智能体（auditor / supply-chain-audit）=="
MSG="审计以下补货决策单。原问句：$Q

待审决策单：
$DEC_JSON

来源会话：$DEC_SID。按 supply-chain-audit SOP 独立复算并输出审计判定 JSON。"
openclaw agent --agent auditor --session-id "$AUD_SID" --message "$MSG" --json > "$OUT/$AUD_SID.json"
python3 - "$OUT/$AUD_SID.json" <<'PYEOF'
import json,sys
d=json.load(open(sys.argv[1]))
meta=d['result']['meta']; am=meta['agentMeta']
print(meta.get('finalAssistantVisibleText'))
lines=[l.strip() for l in (meta.get('finalAssistantVisibleText') or '').splitlines() if l.strip()]
print("\n== 摘要 ==")
print('agent:', am['provider']+'/'+am['model'], '| tools:', json.dumps(meta.get('toolSummary'),ensure_ascii=False))
import re
m=re.search(r'"audit"\s*:\s*"(PASS|FAIL)"', meta.get('finalAssistantVisibleText') or '')
print('最终判定:', m.group(1) if m else '未解析到 audit 字段')
PYEOF
