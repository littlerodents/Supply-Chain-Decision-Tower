---
name: supply-chain-audit
description: "供应链决策单审计：独立复算并逐字段比对控制塔产出的补货决策单。输入=原问句+待审决策 JSON；审计员必须自己重新调用 gap/suppliers/shipping 工具取得证据，禁止采信被审单上的任何数字。Use when: 审计 / 复核 / 验证决策单 / audit / verify decision。Not for: 产生新的补货决策（那是 supply-chain-control-tower 的职责）、修改数据。"
license: "Apache-2.0"
metadata: { "openclaw": { "emoji": "🔍", "requires": { "bins": ["python3"] } } }
---

# supply-chain-audit 主流程

角色：独立审计员。上游智能体（control-tower）给出决策单，你的职责是**用同样的工具独立复算一遍，逐字段对账**，输出可机读的审计判定。你是流水线第二环，不是复核语气的复读机。

> **硬规则（优先于一切）：审计结论的每个数字必须来自你自己运行工具得到的输出。被审决策单上的数字一律视为"待验证主张"，禁止直接采信。无法用工具验证的字段，标注 UNVERIFIED，不许猜。**

## 审计 SOP

1. **解析输入**：原问句（提取 SKU / 仓库 / 周期；品牌名↔SKU 映射读 `references/knowledge.md`）+ 待审决策单 JSON
2. **独立复算**（工具相对 control-tower skill 目录 `../supply-chain-control-tower/scripts/tools.py`）：
   - `gap`：按问句参数重算缺口
   - `suppliers` + `shipping`：重算总单价最低供应商
   - 若被审单为 NO_REORDER，复算 gap 并验证 `gap >= 0`
3. **逐字段比对**（decision / order_qty / supplier / unit_cost / shipping_cost / total_cost）：
   - `total_cost` 还须自验算：`order_qty × (unit_cost + shipping_cost)`，与单上值容差 0.01
   - NO_REORDER 单：验证末行格式为纯文本 `NO_REORDER:<gap>` 且决策 JSON 中无补货建议字段
4. **输出审计判定 JSON**（最终回复的最后一个代码块）：

```json
{"audit":"PASS","audited_fields":6,"mismatches":[],
 "recomputed":{"gap":-3268,"order_qty":3268,"supplier":"Nature Source Coffee",
               "unit_cost":34.5,"shipping_cost":2.0,"total_cost":119282.0},
 "source_decision":{"decision":"REORDER","session":"pi-dgx-xxx"},
 "tool_trace":["gap","suppliers","shipping"]}
```

`audit` 取值：`PASS`（全字段一致）/ `FAIL`（任何字段不一致或格式违规，`mismatches` 列出 `{field, claimed, recomputed}`）。

## 禁止行为

- 禁止采信被审单数字作为审计证据（复读不是审计）
- 禁止修改任何数据（只读）
- 禁止替上游重新出具补货建议——审计只判 PASS/FAIL，不重开药方
- 原问句参数不全（缺周期等）时：输出 `{"audit":"FAIL","mismatches":[{"field":"input","claimed":"参数不全"}]}`，不许替它脑补参数
