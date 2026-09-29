# 供应链控制塔：会说"不"的补货决策智能体

一句自然语言问句 → 双智能体流水线（决策+审计）→ 带工具证据的补货决策单；库存充足时输出 `NO_REORDER:<盈余>`、绝不给建议。

**运行于 NVIDIA DGX Spark（GB10 · CUDA 13.0 · 119GB 统一内存），ROP 驱动的预防性补货决策，全程可本地运行。**

## 核心特性

### 🔬 ROP 驱动决策（从"救火"到"预防性补货"）
- **再订货点**：ROP = μ_weekly × L + z_α × σ_weekly × √L（95% 服务水平）
- **安全库存**：由需求波动 σ × 服务水平系数 z × 提前期 √L 科学计算
- **智能订量**：只补到 ROP + 安全水位，不暴力补全缺口（减少过度库存 89%）
- 示例：库存 30 件，12 周需求 3298 → 传统方法订 3268 件，ROP 方法订 **359 件**

### 🤖 双智能体架构
- **决策智能体**：调工具（gap/suppliers/shipping）推理 → 适配器组装八字段决策 JSON
- **审计智能体**：独立调工具复算 → Python 确定性逐字段对比 → PASS/FAIL
- **负例纪律**：库存充足时只说 NO_REORDER，绝不给补货建议

### 🏠 DGX Spark 本地算力全栈
| 层 | 跑什么 | 用的什么 |
|---|---|---|
| GPU 推理 | Nemotron-120B（86GB MoE） | GB10 GPU + 119GB 统一内存 |
| CUDA 计算 | 自写 kernel，100 万组合批量核算 | CUDA 13.0 + Nsight Systems 剖析 |
| 确定性审计 | Python 逐字段对比 | ARM CPU（与 GPU 共享统一内存） |
| 产品层 | 前端 + API + MCP + 面板 | 同一台机器 |

### 🔌 Agent 原生接口（MCP）
7 个工具通过标准 MCP 协议（stdio JSON-RPC）暴露：
- `gap`（ROP 决策）/ `inventory` / `suppliers` / `shipping` / `forecast` / `scan_portfolio`
- `reorder_decision`（旗舰：问句→决策智能体→核算→审计→可追责决策包）

### 📊 上传自有数据
CSV（utf-8/gbk）/ Excel 上传 → AI 列映射建议 → 人工确认 → 在用户自己的数据上跑巡检

## 架构

```
自然语言问句
   │
   ▼
OpenClaw 网关（DGX Spark，systemd 常驻）
   │
   ├─ 决策智能体 ── skill: supply-chain-control-tower（SOP+红线）
   │     │ 调用只读工具（gap/suppliers/shipping）
   │     ▼
   │   ROP 驱动决策 → Python 适配器 → 八字段决策 JSON
   │        │
   │        ▼ 作为契约交给下游
   ▼        ▼
审计智能体 ── skill: supply-chain-audit（禁止采信被审单数字）
   │        独立重调工具复算 → Python 确定性逐字段对比
   ▼
PASS / FAIL 判定 + 可下载决策单

本地轴：数据/工具/面板/120B 模型 → DGX Spark 统一内存
云脑（备用）：StepFun step-3.7-flash（可选路由，12/12 评测）
```

## 测试结果

| 测试类型 | 数量 | 结果 |
|---|---|---|
| 全参数扫描（SKU×仓×周期） | 192 | ✅ 192/192 |
| 边界值（最短/最长/无记录/不存在） | 4 | ✅ 4/4 |
| 运费翻转（对抗案例） | 2 | ✅ 2/2 |
| 审计拦截（注入错误） | 3 | ✅ 3/3 |
| 随机参数 | 53 | ✅ 53/53 |
| E2E 端到端 | 5 | ✅ 5/5 |
| 消融测试 | 5 | ✅ 5/5 |
| **总计** | **17 项** | **17/17 全绿** |

## 快速开始（DGX Spark 上）

```bash
# 依赖（工具层/巡检/面板）：numpy、pandas、streamlit
python3 -m pip install -r requirements.txt

# 每日巡检（ROP 驱动）：全 SKU×仓库 一键扫描
python3 skill/scripts/daily_scan.py

# MCP 演示（7 工具一键全通）
python3 evidence/mcp_demo.py

# 经典算法（安全库存/ROP/EOQ/报童）
python3 skill/scripts/algorithms.py from-forecast --sku 13001 --location "San Francisco" --weeks 12

# 面板
cd skill/panel && python3 -m streamlit run app.py --server.port 8501
```

> 以上命令在仓库内可直接运行（需 numpy/pandas，面板另需 streamlit）。实时 Agent / API 服务 / 评测套件需按 [REBUILD.md](REBUILD.md) 部署到运行时路径（默认 `~/.openclaw/workspace/skills/supply-chain-control-tower`，可用 `SCT_BASE` 覆盖）。

## 文档

| 文档 | 说明 |
|---|---|
| [答辩文档](docs/答辩文档.md) | 评分标准逐条论证（含 Baseline 对比） |
| [过程记录](docs/journey/) | 完整时间线 + 8 个踩坑实录 + 8 条反思教训 |
| [本地模型攻坚终报](docs/本地模型攻坚终报.md) | Nemotron 五轮调优全负 + 148B 部署尝试 |
| [前端对接规格书](docs/03-新前端对接规格书.md) | HTTP API 契约（/api/catalog + /api/runs） |
| [ISC-24 表单内容包](docs/ISC-24-表单内容包.md) | 提交材料 |
| [参赛征文](docs/征文-供应链控制塔.md) | 叙述文稿 |
| [ISC-25 B站录屏脚本](docs/ISC-25-B站录屏脚本.md) | 演示分镜 |
| [复原手册](REBUILD.md) | 换一台 DGX Spark 怎么把系统原样跑起来 |

> 审计智能体的 Skill 在 [`skill-audit/`](skill-audit/SKILL.md)（与 `skill/` 的决策 Skill 构成双智能体）。

## 过程记录（诚实展示）

我们不是一次做对的。[docs/journey/](docs/journey/) 记录了完整过程：

- [时间线](docs/journey/01-timeline.md)：7 个阶段，从环境验证到 ROP 升级
- [踩坑实录](docs/journey/02-failures.md)：8 个真实的失败案例（SKILL.md 被覆盖、148B 部署失败、Streamlit 取消 bug 等）
- [反思](docs/journey/03-reflections.md)：如果重来一次，8 条可传承的工程教训

> 失败不是浪费，是付费的学习。这份记录就是收据。

**原始提交链**：从 D0 脚手架起的每一次提交（SPEC/ISA/STATUS、spike 探针、七轮评测证据）完整保留在本仓库的 [`process` 分支](https://github.com/littlerodents/repro-pack/tree/process)；`main` 为整理后的交付版。

## 团队

![团队合照](docs/images/team.jpg)

三个人，一台 DGX Spark，一个会说"不"的智能体。

## 许可与致谢

Apache-2.0。数据与求解器衍生自 ikatsov/tensor-house `control_center_llm`（移植中修复上游 3 处 bug）。
