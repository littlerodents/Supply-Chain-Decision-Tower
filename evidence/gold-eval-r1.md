# Gold 评测报告（run r1，2026-09-27 06:06:07）

**总分 9/12**

| 任务 | 类型 | 判定 | 依据 | 延迟s | tokens |
|---|---|---|---|---|---|
| pos-dec-001 | decision | ✅ | 八字段与金答案一致 | 16.3 | 223714 |
| pos-dec-002 | decision | ✅ | 八字段与金答案一致 | 20.5 | 259527 |
| pos-dec-003 | decision | ✅ | 八字段与金答案一致 | 20.2 | 259269 |
| pos-dec-004 | decision | ❌ | total_cost: want=46389.9 got=46369.9 | 22.2 | 298201 |
| pos-qry-001 | query | ✅ | 金答案 4 个数字全部命中且零工具失败 | 7.7 | 108498 |
| pos-qry-002 | query | ✅ | 金答案 3 个数字全部命中且零工具失败 | 7.6 | 108553 |
| pos-qry-003 | query | ✅ | 金答案 8 个数字全部命中且零工具失败 | 12.7 | 147123 |
| pos-qry-004 | query | ❌ | 回复缺少金答案数字: ['2'] | 7.3 | 108444 |
| neg-stk-001 | negative | ❌ | 末行应='NO_REORDER:100' 实='`NO_REORDER:100`' | 12.0 | 183533 |
| neg-stk-002 | negative | ✅ | 末行纯文本 NO_REORDER:140，零建议字段 | 16.2 | 146971 |
| neg-stk-003 | negative | ✅ | 末行纯文本 NO_REORDER:50，零建议字段 | 11.7 | 147745 |
| neg-irr-001 | irrelevant | ✅ | 未触发供应链决策输出 | 11.9 | 109955 |

分类：decision 3/4，query 3/4，negative 2/3，irrelevant 1/1
