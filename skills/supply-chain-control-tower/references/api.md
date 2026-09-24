# 工具 API 语义（scripts/tools.py）

> 全部 bash 调用、JSON 输出到 stdout、stderr 走日志。数据层：CSV → 内存 SQLite，纯只读、纯确定性。

## gap —— 库存-需求缺口（补货决策原语）

```bash
python3 scripts/tools.py gap --sku 13001 --location "San Francisco" --weeks 12
```

返回：`current_stock`、`forecast_demand`（N 周合计）、`gap_stock_minus_demand`。
**判读：gap < 0 = 短缺需补（订量 = -gap）；gap ≥ 0 = 充足不补。**

## inventory / suppliers —— SQL 查询

```bash
python3 scripts/tools.py inventory --sql "SELECT * FROM inventory WHERE sku=12001"
python3 scripts/tools.py suppliers --sql "SELECT * FROM suppliers WHERE sku=12001 ORDER BY unit_cost"
```

表结构：
- `inventory(sku INT, brand TEXT, location TEXT, quantity INT)`
- `suppliers(sku INT, supplier TEXT, location TEXT, unit_cost REAL)` —— `location` 是**供应商发货地**（运费计算的 source）

SQL 错误会抛 pandas 异常——读报错信息修正 SQL 再试（自纠预期）。

## forecast —— 52 周需求预测

```bash
python3 scripts/tools.py forecast --sku 11001 --location "San Francisco" --weeks 8
```

返回逐周 `demand`（int）。确定性：跨进程一致；location 不影响结果（如实说明，勿编造差异）。

## shipping —— 单件运费

```bash
python3 scripts/tools.py shipping --source Seattle --destination "San Francisco"
```

返回 `unit_shipping_cost_usd`（float）。source = 供应商发货地，destination = 目标仓库。

## chart —— 预测线图

```bash
python3 scripts/tools.py chart --sku 13001 --location "San Francisco" --weeks 26 --out /tmp/fc.png
```

matplotlib 缺失时自动降级输出 CSV（返回 `chart_fallback_csv` 字段）。

## kb —— 拓扑全量

```bash
python3 scripts/tools.py kb
```

产品/库存/供应商全量 JSON——回答宽泛问题（「有哪些产品」）时一次拿全。
