---
name: supply-chain-control-tower
description: "供应链控制塔：用自然语言运营问句驱动库存-供应商-补货决策——查库存、算库存-需求缺口、供应商比价（含运费）、产出结构化补货建议单，或给出明确的无需补货结论。Use when: 补货决策 / 库存够不够 / 该订多少 / 找哪个供应商 / 缺货风险 / 未来几周的需求 / supply chain / reorder / stock level / inventory. Not for: 与供应链无关的问句、要求修改库存数据（本 skill 只读）、真实运输下单执行、多级库存网络优化。"
license: "Apache-2.0 (derived from ikatsov/tensor-house control_center_llm, Apache-2.0)"
metadata: { "openclaw": { "emoji": "🚦", "requires": { "bins": ["python3"] } } }
---

# supply-chain-control-tower 主流程

目标：运营者一句话 → 工具链查证 → 结构化决策（或明确的「不需要」）。**只读不写；参数不全先问；负例绝不产建议。**

> **硬规则（优先于一切）：凡回答中出现库存/需求/补货量/价格/运费数字，必须先有对应工具输出作证据——禁止凭记忆或估算作答。没有工具输出，就没有回答。**

> **输出格式契约（判据按此机器判定）：正例回复以恰好一个 ```json 代码块结尾，其后不得再有任何正文、追问或选项列表（"还需要我…吗/你要我做哪个"之类禁止）；即使本轮工具已算出全部数字、即使认为结论"已给出"，也必须在回复末尾完整重写决策 JSON 代码块，不得以"见上文"为由省略；负例回复的最后一行是裸文本 `NO_REORDER:<盈余>`——禁止用反引号或代码围栏包裹，禁止附加任何 JSON 块/代码块。**
>
> **OUTPUT CONTRACT (English, equally binding — reply in the user's language, but ALWAYS end with the machine-readable block):** For a replenishment decision, the reply MUST end with exactly one ```json fenced block containing the complete decision JSON with keys: decision, sku, location, weeks, order_qty, supplier, unit_cost, shipping_cost, total_cost, rationale, tool_trace. Never end with a question, an offer ("shall I...?"), or any text after the block — even if all numbers were already stated in prose above, restate them in the JSON block. For a no-replenishment case, the last line must be bare text `NO_REORDER:<surplus>` with no fences and no JSON block.

## 问句分类（第一步）

1. **状态查询**（库存多少/有哪些供应商/需求曲线）→ 直接调对应工具，用表格/数字回答，结束
2. **补货决策**（该不该补/补多少/找谁/总成本）→ 走下方决策 SOP
3. **无关问句** → 不触发本 skill（见 frontmatter 负触发）

## 补货决策 SOP

1. **补齐参数**：SKU（品牌名↔SKU 映射先读 `references/knowledge.md`）、仓库、决策周期（周）。**周期缺失必须先问，不许默认猜测**；「本周/这一周/未来一周」即 1 周，属周期明确，无需追问
2. `gap` 工具先看 `record_exists`：**为 false 时直接回复「该仓无此品库存记录，未作决策」——禁止把缺记录当零库存算缺口、禁止出决策单、也禁止输出 NO_REORDER（无记录 ≠ 库存充足），这是第一红线**
3. `gap` 判定（有记录时）——注意 ROP 驱动模式：
   - 工具返回 `rop_gap`（ROP−库存，正=低于再订货点）和 `safety_stock`（安全库存）
   - **rop_gap > 0 → 需补货**，建议订量 = rop_gap + safety_stock（不是裸缺口！）
   - **rop_gap <= 0 → 不补**（库存高于再订货点，预防性不行动）
   - 推理时用"库存已跌破再订货点 ROP=xxx"的语言，不说"缺口 xxx 件"
   - `gap >= 0`（旧逻辑，仅供参考）→ 不补，末行输出 `NO_REORDER:<gap>`（如 +140），**禁止给出任何补货建议、订量或供应商**
3. `gap < 0` → 短缺量 = `-gap`：
   - `suppliers` 工具查该 SKU 的供应商，按 `unit_cost` 排序
   - 对每个候选调 `shipping`（供应商所在城市 → 目标仓库），比较 `unit_cost + unit_shipping_cost` 总单价
   - 推荐总单价最低者；建议订量 = 短缺量
   - **总成本必须用 python3 实算**（如 `python3 -c "print(1941*(21.9+2.0))"`，四舍五入到分），**禁止心算乘法**——LLM 长乘法不可靠
4. 输出**决策 JSON**（最终回复的最后一个代码块）：

```json
{"decision":"REORDER","sku":13001,"location":"San Francisco","weeks":12,
 "order_qty":3268,"supplier":"Nature Source Coffee","unit_cost":34.5,
 "shipping_cost":2.0,"total_cost":119282.0,
 "rationale":"未来12周预测需求3298，现库30，缺3268；唯一供应商 Seattle，单价34.5+运费2.0",
 "tool_trace":["gap","suppliers","shipping"]}
```

负例末行（裸文本，无围栏无反引号，其后无任何内容）：`NO_REORDER:140`

## 工具（bash 调用，全部 JSON 输出；脚本相对本 skill 目录）

```bash
S=scripts/tools.py
python3 $S gap --sku 13001 --location "San Francisco" --weeks 12   # 缺口（决策原语）
python3 $S inventory --sql "SELECT * FROM inventory WHERE location='Seattle'"
python3 $S suppliers --sql "SELECT * FROM suppliers WHERE sku=12001 ORDER BY unit_cost"
python3 $S forecast --sku 11001 --location "San Francisco" --weeks 8
python3 $S shipping --source Seattle --destination "San Francisco"
python3 $S chart --sku 13001 --location "San Francisco" --weeks 26 --out /tmp/f.png
python3 $S kb   # 产品/仓库/供应商拓扑全量
```

完整 API 语义：`references/api.md`；业务映射（品牌名→SKU、仓库、供应商格局）：`references/knowledge.md`。

## 禁止行为

- 不写入/修改任何数据（只读）
- 不编造供应商、价格、库存数字——一切数字必须来自工具输出
- 周期（weeks）不明时先问，不许猜
- **负例（gap≥0）绝不产补货建议**——宁可只回一句 NO_REORDER
- 不推断库存商品之外的任何业务判断（如停售、调价）

## 上游与修复

转化自 `case/control_center_llm`（Apache-2.0）。移植中修复上游三处 bug：hash 跨进程不稳定（预测/运费）、solver f-string 致库存恒 0、streamlit 隐式依赖。详见 `scripts/tools.py` 头注。
