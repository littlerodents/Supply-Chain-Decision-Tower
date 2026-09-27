# Gold 评测报告（run r2，2026-09-27 06:09:01）

**总分 10/12**

| 任务 | 类型 | 判定 | 依据 | 延迟s | tokens |
|---|---|---|---|---|---|
| pos-dec-001 | decision | ✅ | 八字段与金答案一致 | 18.1 | 224230 |
| pos-dec-002 | decision | ✅ | 八字段与金答案一致 | 12.4 | 183899 |
| pos-dec-003 | decision | ✅ | 八字段与金答案一致 | 19.3 | 225526 |
| pos-dec-004 | decision | ❌ | total_cost: want=46389.9 got=46368.9 | 14.7 | 221017 |
| pos-qry-001 | query | ✅ | 金答案 4 个数字全部命中且零工具失败 | 7.5 | 108506 |
| pos-qry-002 | query | ✅ | 金答案 3 个数字全部命中且零工具失败 | 8.0 | 108588 |
| pos-qry-003 | query | ✅ | 金答案 8 个数字全部命中且零工具失败 | 9.9 | 146334 |
| pos-qry-004 | query | ✅ | 金答案 1 个数字全部命中且零工具失败 | 7.8 | 109879 |
| neg-stk-001 | negative | ❌ | 末行应='NO_REORDER:100' 实='你希望按未来几周做补货决策？这是计算缺口必须的参数。' | 6.8 | 108998 |
| neg-stk-002 | negative | ✅ | 末行纯文本 NO_REORDER:140，零建议字段 | 14.2 | 183932 |
| neg-stk-003 | negative | ✅ | 末行纯文本 NO_REORDER:50，零建议字段 | 9.1 | 147279 |
| neg-irr-001 | irrelevant | ✅ | 未触发供应链决策输出 | 6.8 | 106571 |

分类：decision 3/4，query 4/4，negative 2/3，irrelevant 1/1
