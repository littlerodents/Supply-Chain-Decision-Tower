# Gold 评测报告（run r3，2026-09-27 06:22:59）

**总分 9/12**

| 任务 | 类型 | 判定 | 依据 | 延迟s | tokens |
|---|---|---|---|---|---|
| pos-dec-001 | decision | ✅ | 八字段与金答案一致 | 10.5 | 152685 |
| pos-dec-002 | decision | ✅ | 八字段与金答案一致 | 4.8 | 38150 |
| pos-dec-003 | decision | ❌ | 未输出决策 JSON 代码块 | 22.2 | 336812 |
| pos-dec-004 | decision | ✅ | 八字段与金答案一致 | 18.3 | 259507 |
| pos-qry-001 | query | ✅ | 金答案 4 个数字全部命中且零工具失败 | 7.2 | 108644 |
| pos-qry-002 | query | ✅ | 金答案 3 个数字全部命中且零工具失败 | 8.1 | 108812 |
| pos-qry-003 | query | ✅ | 金答案 8 个数字全部命中且零工具失败 | 9.9 | 146503 |
| pos-qry-004 | query | ✅ | 金答案 1 个数字全部命中且零工具失败 | 7.0 | 108685 |
| neg-stk-001 | negative | ❌ | 负例输出了补货建议字段 | 13.5 | 183918 |
| neg-stk-002 | negative | ✅ | 末行纯文本 NO_REORDER:140，零建议字段 | 9.2 | 146386 |
| neg-stk-003 | negative | ❌ | 末行应='NO_REORDER:50' 实='```' | 10.6 | 146520 |
| neg-irr-001 | irrelevant | ✅ | 未触发供应链决策输出 | 5.8 | 71189 |

分类：decision 3/4，query 4/4，negative 1/3，irrelevant 1/1
