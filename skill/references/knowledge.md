# 供应链知识（产品/仓库/供应商拓扑）

> agent 回答品牌名相关问句前先读本表；一切以 `kb` 工具实时输出为准（本表是它的静态镜像）。

## 产品（SKU ↔ 品牌）

| SKU | 品牌 | 品名 |
|---|---|---|
| 11001 | House Blend | Medium Roast Ground Coffee |
| 12001 | Italian Roast | Espresso Italiano |
| 13001 | Colombian Coffee | Colombian Fresh Roasted |
| 14001 | Breakfast Blend | Light Roast Ground Coffee |
| 15001 | Decaf Espresso | Swiss Water Decaf Espresso |
| 16001 | French Roast | Dark Roast Whole Bean Coffee |

## 仓库与当前库存（inventory.csv）

| SKU | 仓库 | 库存 |
|---|---|---|
| 11001 | San Francisco | 250 |
| 12001 | Portland | 340 |
| 12001 | Seattle | 100 |
| 13001 | Seattle | 300 |
| 13001 | San Francisco | 30 |
| 14001 | San Francisco | 40 |
| 15001 | Seattle | 260 |
| 16001 | Portland | 85 |

注意：**11001 无 Portland 库存行；12001 无 San Francisco 行；13001 无 Portland 行**——问「某仓某品」先查 `inventory`，查空就明说「该仓无此品库存记录」，不许编数字。

## 供应商格局（suppliers.csv）

| SKU | 供应商 | 发货地 | 单价 |
|---|---|---|---|
| 11001 | Coffee Wholesale USA | San Francisco | 21.90 |
| 12001 | Coffee Wholesale USA | Seattle | 23.90 |
| 12001 | Nature Source Coffee | Seattle | 31.90 |
| 13001 | Nature Source Coffee | Seattle | 34.50 |
| 14001 | Budget Beans Co. | Los Angeles | 15.50 |
| 14001 | Golden Gate Roasters | San Francisco | 19.90 |
| 16001 | Pacific Roast Trading | Seattle | 24.50 |
| 16001 | Rose City Coffee | Portland | 25.90 |
| 16001 | Cascade Coffee Co. | Chicago | 24.90 |

决策要点：12001 有**双供应商可比价**（同在 Seattle，运费同，单价差 8.0）；11001/13001 为单一供应商。

**运费翻转案例（重要）**：14001 与 16001 的单价最低者都不是总单价最低者——Budget Beans 15.50+运费7=22.50 败给 Golden Gate 19.90+运费2=21.90；Pacific 24.50+1=25.50 败给 Cascade 24.90+0=24.90。**只按 unit_cost 排序会选错供应商，必须比 unit_cost+运费。**

## 预测特性（合成预测，确定性）

- 第 1 周需求恒为 200（公式 sin(0)=0）；随周次按正弦波动，52 周窗口
- 同 SKU 跨进程结果一致（crc32 稳定化）；**location 不影响预测**（上游公式如此，如实说明）
- 推论：短周期（1–2 周）问句在库存 ≥200 时天然是「不补」负例；长周期（≥8 周）几乎必然短缺
