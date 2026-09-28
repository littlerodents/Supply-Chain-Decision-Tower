# 供应链控制塔：会说"不"的补货决策智能体

一句自然语言问句 → 双智能体流水线（决策+审计）→ 带工具证据的八字段补货决策单；库存充足时输出 `NO_REORDER:<盈余>`、绝不给建议。运行于 NVIDIA DGX Spark，主力 = 本地 Nemotron-120B + Python 适配器 + 确定性审计（17/17 全绿），云端 StepFun 仅备用；数据/工具/面板/模型全在本地。

## 架构

```
自然语言问句
   │
   ▼
OpenClaw 网关（DGX Spark，systemd 常驻）
   │
   ├─ 决策智能体 main ── skill: supply-chain-control-tower（SOP+红线）
   │        │ 调用 7 只读工具（gap/inventory/suppliers/forecast/shipping/chart/kb）
   │        ▼
   │   八字段决策 JSON（含 tool_trace）
   │        │  作为契约交给下游
   ▼        ▼
审计智能体 auditor ── skill: supply-chain-audit（禁止采信被审单数字）
   │        独立重调工具复算 → 逐字段对账 + 总价自验算
   ▼
PASS / FAIL 判定 JSON（mismatches 精确到字段）

本地轴：SQLite/CSV 数据 · Streamlit 面板 :8501（工具证据 + 实时 Agent 最小闭环） · ollama（120B 86GB / 30B MoE 18GB）
云脑：StepFun step-3.7-flash（默认路由，评测门控选出：3/3 vs 本地 1/3、0/2）
算法插槽：scripts/algorithms.py（安全库存/ROP/EOQ/报童，教科书用例测试通过）

面板四模式（panel/app.py，内置 48 SKU / 64 组合 / 75 供应商行 + 用户上传数据）：
  📋 每日巡检 —— 产品形态：一键全组合扫描（工具直算，秒级零 LLM），短缺排行/运费翻转标记/
     建议采购总额，例外一键填入问句转 Agent 追问；报告留档 panel/reports/
  🧮 工具证据 —— 零 LLM 直算；动态 SKU、无记录防护、图题=点数、供应商含运费比价（运费翻转标注）
  🤖 实时 Agent —— 问句 → openclaw agent（默认路由）→ 原答/确定性独立核算/审计智能体判定同屏；
     独立会话、单次提交、90s 超时不自动重试（Streamlit AppTest 端到端验证 PASS）
```

## 快速开始（DGX Spark 上）

```bash
# 每日巡检（产品形态）：全 SKU×仓库 一键扫描，秒级出短缺排行与决策单草稿
python3 skills/supply-chain-control-tower/scripts/daily_scan.py

# 双智能体流水线（每 take 自动唯一会话）
~/isc-submission-20260927/bin/two-agent-pipeline.sh "San Francisco 仓库 SKU 13001 未来 12 周够卖吗？需要补货吗？" demo

# 12 任务 gold 评测（工具直算金答案，机器判分）
python3 ~/isc-submission-20260927/bin/run_gold_eval.py r1

# 经典算法插槽
python3 scripts/algorithms.py from-forecast --sku 13001 --location "San Francisco" --weeks 12

# 面板
python3 panel/app.py   # → http://<DGX-IP>:8501
```

## 评测结果（2026-09-27）

- 演示路径严格判据：3/3（正例八字段 3268/Nature Source Coffee/34.5+2.0/119282.0 + 工具证据；负例末行纯文本 NO_REORDER:100）
- 12 任务×5 轮：9→10→9→11→**12/12**。四种失败模式（心算总价/周期歧义/负例围栏/省略 JSON 块+追问）逐一经"失败样本→SOP 收紧→复测"闭环修复，全系列 60 份原始 JSON 留档
- 数据集扩展（6 SKU×3 仓，纯增量、旧决策金答案 diff 验证零变化）：16 任务含**运费翻转对抗案例**（单价最低≠总单价最低），单轮 **16/16**
- 审计智能体实证：正确单六字段全对账 PASS；错误单（总价差 21.0）被 FAIL 精确拦截

## 文档与证据

- `答辩文档.md`（评分标准逐条论证）
- `ISC-24-表单内容包.md` / `ISC-25-征文初稿.md` / `ISC-25-B站录屏脚本.md` / `提交检查单.md`
- `素材/`（全部原始 JSON 与平台证据）

## 许可与致谢

Apache-2.0。数据与求解器衍生自 ikatsov/tensor-house `control_center_llm`（移植中修复上游 3 处 bug：跨进程 hash 不稳定、solver f-string 致库存恒 0、Streamlit 隐式依赖）。
  📤 上传我的数据 —— CSV(utf-8/gbk)/Excel 上传 → AI 列映射建议 → 人工确认 → 确定性校验
     （长表多供应商/缺列诚实降级）→ 在用户自己的数据上全量巡检出补货单（custom_data.py 纯逻辑单测覆盖）

## MCP 服务器（Agent 原生接口，任意外部 Agent 可挂载）

```json
{"mcpServers": {"supply-chain-tower": {
  "command": "python3",
  "args": ["~/.openclaw/workspace/skills/supply-chain-control-tower/scripts/mcp_server.py"]}}}
```

7 个工具：`gap` / `inventory` / `suppliers` / `shipping` / `forecast` / `scan_portfolio`（全组合巡检）/
`reorder_decision`（旗舰：问句 → 决策智能体 → 零 LLM 确定性核算 → 审计智能体 → 可追责决策包，实测 overall PASS）。
协议：MCP over stdio（JSON-RPC 2.0，零依赖手写实现，scripts/mcp_server.py，客户端实测通过）。
