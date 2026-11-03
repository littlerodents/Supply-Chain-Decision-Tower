# 2026-09-25 晚：Iris 隔离试验前置核查（PARTIAL）

> 仅记录本轮实际读取和执行；非 DGX 本机运行证据，不新增/关闭 ISC。`evidence/` 被 gitignore，团队读者需另行获取原始材料。

## 可证伪目标

1. DGX 当前资源/连接可查，且 Iris-mini 能隔离运行，不影响已在运行的 120B、OpenClaw、面板。
2. Iris 搜索结果能以来源+证据字段传给控制塔，并由 OpenClaw 在真实入口完成补货问句，满足 `decision=REORDER`、`total_cost=119282`，负例不误补货。
3. 单 agent 与串接版同题、同数据/工具权限的质量和延迟可比较；串接失败即标未证明。

## 本轮执行与结果

- `python3 -m pytest tests/test_tools.py -q` → `7 passed, 3 xfailed in 3.71s`；三个 xfail 为队友 BUG-1/2/3，未占用其修理位。
- `python3 skills/supply-chain-control-tower/scripts/tools.py gap --sku 13001 --location 'San Francisco' --weeks 12` → 现库 30、预测 3298、缺口 -3268。
- 读取 `skills/supply-chain-control-tower/evals/gold.json` 的 `pos-dec-001` → REORDER、3268、Nature Source Coffee、119282.0；`tools.py suppliers` → unit_cost 34.5；`tools.py shipping` → unit_shipping_cost_usd 2.0。
- 读取**历史** OpenClaw 结果 `evidence/d3/agent-out3.json` → decision「需补货」而非契约枚举 `REORDER`，total_cost 119006.0；这不是本轮在 DGX 上的新鲜入口验收。
- 读取 `evidence/evals/results-nemotron-skill*.json` → 三轮 12/12、9/12、11/12；`results-stepfun-skill.json` 目前只有 4 条（此前临时审计试验覆盖），且四条 `verifier_tools` 均为 0。该 4/4 不能替代原 12 题基线或证明双 agent。
- 本机尝试非交互 SSH 连接 `dgx`、`dgx-spark`、`spark`：均无解析；仅观察到不明确归属的 `shadow` 别名，read-only 指纹探针连接超时，**未证明它是 DGX**。未读取凭据文件、未传密钥、未变更远程服务；没有可验证的 DGX 资源快照。
- `ISA.md` v2 的 14 条 ISC 中仅 9 条被 `[x]` 勾选，头部 `11/14` 与清单不一致；是否再关闭 ISC-12/14/15 需按各自判据重新取证，不能靠测试文件存在自动计入。
- `skills/supply-chain-control-tower/SKILL.md` 示例总价写 119284.0，与工具金答案 119282.0 不符；未在本轮修改（入口与回归验证前不要把错例扩散）。

## 尚未验证 / 下一入口

缺少当前 DGX 的**无密钥 SSH 入口或可访问的只读运行端点**，因此磁盘/内存/ARM64 服务兼容、Iris-mini 部署、Serper 搜索、OpenClaw+Iris 串接、负例端到端全为 UNPROVEN。拿到可用入口后先做只读资源快照和隔离容量判断，再决定是否下载/启动 Iris-mini；不停止 120B 或重启现有 Gateway，不公开发布，也不使用此前明文出现的密钥。

赛期旧文档的 9/26 晚冻结与 9/25 会议讨论的 9/27 完整版冲突；本轮未擅自改定排期。
