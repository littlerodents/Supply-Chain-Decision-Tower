# ISC-25 B站录屏脚本（3.5 分钟版 · 与 GitHub main 对齐）

> **2026-09-29 重写**：叙事对齐 GitHub 仓库 main（github.com/littlerodents/repro-pack）——ROP 驱动 + 双智能体 + DGX Spark 本地算力全栈 + MCP + 17/17 测试。旧版"三腿 A/B 选云脑"的结尾卡**作废**，新结尾卡在仓库 `docs/video-materials/ending-card.html`（已内嵌团队合照，双击打开全屏录制即可）。
> 每条 take 必须用**新的 session id**（take1/take2 只是示例，重录就换 take3/take4…）。录制前自检清单在文末。台词可直接念。

## 分镜总表

| # | 时间 | 画面 | 内容 |
|---|---|---|---|
| 1 | 0:00-0:15 | 标题卡 | 项目名 + 一句话 |
| 2 | 0:15-0:50 | 终端 | DGX Spark 本地算力：119GB 统一内存 + 120B 常驻 + CUDA 批量核算 |
| 3 | 0:50-1:55 | 终端 | ROP 正例 live：问句 → 工具 → 八字段决策 + 审计 |
| 4 | 1:55-2:20 | 终端 | 负例 live：NO_REORDER |
| 5 | 2:20-2:50 | 浏览器 | FIELDWORK 前端：双模式 + 核验徽章 |
| 6 | 2:50-3:15 | 终端 | MCP：7 工具一键全通 |
| 7 | 3:15-3:35 | 结尾卡 | 17/17 战绩 + 团队合照 + 仓库链接 |

## 逐镜台词与操作

### 镜 1 · 标题卡（0:00-0:15）

画面：黑底白字标题卡。

> 台词：供应链控制塔——一个会说"不"的补货决策智能体，跑在 DGX Spark 上。一句自然语言问句进来，一份带工具证据的补货决策单出去；库存够的时候，它敢直接说：不用补。

### 镜 2 · 本地算力（0:15-0:50）

画面：终端依次跑（提前开好，字号调大）：

```bash
nvidia-smi
~/ollama/bin/ollama list
```

> 台词：这台是 DGX Spark，GB10 Grace Blackwell，119G 统一内存，CUDA 13。86G 的 Nemotron-120B 整个常驻在统一内存里——数据、工具、模型、面板，**全栈都在这一台机器本地，敏感数据不出机器**。

画面 A（可选 10s，若用架构图页，口径必须是）：

```
左栏（本地 DGX Spark ⭐主力）：Nemotron-120B 推理 + Python 适配器 + 确定性审计 + 7 只读工具 + 数据
中栏：OpenClaw 网关 + Skill SOP
右栏（虚线·备用）：StepFun step-3.7-flash 云端路由（可选）
```
> 注意：架构图只有一颗星——本地 120B。云端画成虚线备用框；不出现任何其他模型。

画面 B（15s）：展示 CUDA 证据（`evidence/` 下 CUDA benchmark 输出或 dmon 截屏）：

> 台词：补货扫描要核算上百万种参数组合，我们自写了 CUDA kernel 在 GB10 上批量算，Nsight Systems 剖析留档——本地算力不是摆设，是真的在干活。

### 镜 3 · ROP 正例 live（0:50-1:55）★核心镜头

画面：终端。逐字敲入（或粘贴）——**走产品 API（本地 120B 全链路：决策 → 适配器签发 → 独立核算 → 审计），此路径已实测 PASS**：

```bash
curl -s http://127.0.0.1:8765/api/runs -X POST -H 'Content-Type: application/json' -d '{
  "request_id":"demo-take1","session_id":"demo-take1","mode":"live",
  "question":"San Francisco 仓库 SKU 13001 未来 12 周够卖吗？需要补货吗？",
  "sku":13001,"location":"San Francisco","weeks":12}'
```

轮询出结果（本地 120B 约 2-7 分钟，可剪辑加速）：

```bash
curl -s "http://127.0.0.1:8765/api/runs/demo-take1?session_id=demo-take1" | python3 -m json.tool
```

> 台词（边等边念）：现在跑的是本地 Nemotron-120B——86GB 的模型整个躺在 DGX Spark 统一内存里，零云端。回答里每个数字都必须有工具证据：没有工具输出，就没有回答。注意架构的关键一层：**模型负责推理和叙述，八字段决策单由 Python 适配器按工具直算签发，审计层独立复算逐字段对账**——模型的嘴可以飘，签出去的合同飘不了。

结果出来后，把 JSON 关键字段指给镜头看：

> 台词：看这个决策——传统缺口分析说要补 3268 件，ROP 优化算法说：只需补 **359.4** 件。再订货点 332.2，等于提前期需求加安全波动；库存 30 已跌破它，rop_gap 302、安全库存 57.4。我们不是暴力补全缺口，而是科学计算最优订量——**减少过度库存 89%**。供应商 Nature Source Coffee，单价 34.5 加运费 2 块，总价 13118.1 美元——全部来自工具直算和适配器签发，verification: PASS。

### 镜 3B · 云端备用 take（可选，剪辑插入 10-15 秒）

```bash
openclaw agent --session-id pi-dgx-demo-take1b \
  --model stepfun/step-3.7-flash \
  --message "San Francisco 仓库 SKU 13001 未来 12 周够卖吗？需要补货吗？" --json
```

> 台词：同一套流水线也有云端备用路由——StepFun step-3.7-flash，13 秒出单，12/12 评测通过。但它是备用的：决策、审计、数据都在本地，这台机器不联网照样签决策单。

### 镜 4 · 负例 live（1:55-2:20）

```bash
curl -s http://127.0.0.1:8765/api/runs -X POST -H 'Content-Type: application/json' -d '{
  "request_id":"demo-take2","session_id":"demo-take2","mode":"tool",
  "question":"Seattle 仓库 SKU 13001 未来 1 周够卖吗？需要补货吗？",
  "sku":13001,"location":"Seattle","weeks":1}' | python3 -m json.tool
```

> 台词：换一个仓库，只看一周。库存 300，需求 200，盈余 100——看决策。

高亮 `NO_REORDER` 与盈余 100：

> 台词：NO_REORDER，盈余 100。它没有"建议适度补货"，没有给供应商，什么建议都没有——库存够就是够。通用大模型总倾向于显得有用，这一行是我们专门设计出来的信任时刻。

### 镜 5 · 前端产品（2:20-2:50）

画面：浏览器 `http://192.168.11.205:5173`（FIELDWORK）。左表单选**工具模式**提交 → 右侧秒出 hero 大数字；再切 **Agent 模式**提交一条正例 → 轮询出决策卡 + 审计核验徽章 ✅。

> 台词：这才是它作为产品的样子。工具模式，秒回，零模型成本；Agent 模式，等一分钟，拿到的是带审计徽章的决策单。Streamlit 面板（:8501）还有每日巡检——64 个 SKU×仓库组合一键扫完、运费翻转陷阱标星——以及上传你自己 CSV 数据的入口，AI 建议列映射、人确认、工具算数。

### 镜 6 · MCP（2:50-3:15）

画面：终端跑：

```bash
python3 ~/mcp_demo.py        # 仓库内副本：evidence/mcp_demo.py
```

> 台词：整个能力通过标准 MCP 协议暴露——库存、缺口、供应商、运费、预测、组合扫描，加上旗舰的 reorder_decision：问句进，决策智能体、核算、审计，出一个可追责的决策包。任何 Agent 客户端接上就能用，不绑定我们的界面。

### 镜 7 · 结尾卡（3:15-3:35）

画面：全屏打开 `docs/video-materials/ending-card.html`（黑底，已内嵌团队合照）。静置 3 秒后开始念：

> 台词：十七项测试全绿——192 组参数扫描、53 组随机参数、5 项端到端、5 项消融。从一句问话，到一份带证据的决策单；不该补的时候，它会说"不"。代码和完整过程已经开源——我们三个人，一台 DGX Spark，一个会说"不"的智能体。

## 录制前自检（5 分钟）

1. `systemctl --user is-active openclaw-gateway` 必须是 `active`。
2. 空跑确认链路通：用 request_id=demo-take0 走镜 3 同款 API live 命令跑一遍正例，确认最终 verification: PASS（约 2-7 分钟；别占用 take1/take2）。
3. 前端 `http://192.168.11.205:5173` 提前打开加载完，两个模式各点一遍；Streamlit:8501 备份机位可开。
4. 结尾卡提前双击打开确认照片加载正常（无外网依赖，照片已内嵌）。
5. 终端字号调大（录屏可读），背景干净，敲命令慢一点。
6. 证据兜底：`~/isc-submission-20260927/素材/pi-dgx-final27-*.json`（3/3 原始输出）和 `nvidia-smi.txt`/`ollama-list.txt` 都在——**若 live 翻车，切录屏展示这三个 JSON 文件并照念台词，照样成立**。

## 上传 B站注意

- 标题建议：`DGX Spark 供应链控制塔：会说"不"的 AI 补货决策智能体`
- 简介贴表单内容包的"短摘要"+ B站链接回填到 ISC-24 表单。
- 全片约 3 分 35 秒；若比赛要求 ≤3 分钟：镜 2 画面 B 压到 8 秒、镜 5 压到 20 秒、镜 6 压到 15 秒、镜 3B 删掉。
