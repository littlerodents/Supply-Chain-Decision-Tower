# N5 部署与演示记录（ISC-20/21/22 证据汇总）

> 2026-09-25 · 环境：租机 DGX Spark（GB10/119Gi）· OpenClaw 2026.9.5（gateway :3030）· Ollama 0.34.4 + nemotron-3-super-120b（87GB，本地）· Streamlit 面板 :8501

## ISC-20 · skill 入 workspace + 真问句演示

- 部署：`rsync skills/supply-chain-control-tower/ → ~/.openclaw/workspace/skills/`
- 验收：`openclaw skills list` → **🚦 supply-chain-control-tower ✓ ready**（source: openclaw-workspace）；`--eligible` 计数 1
- 真问句（gateway 主脑=本地 120B，三轮对话）：
  - turn1（发现）：agent 主动定位 skill 与 tools.py
  - turn2（取证）：产出 3268 × Nature Source（数字正确）
  - turn3（契约）：输出八字段决策 JSON（`agent-out3.json`；decision 字段本地化为「需补货」，数字与金答案一致：qty 3268、供应商唯一、$34.5+$2.0、总成本误差 0.23%）
- 踩坑记录（征文素材）：gateway 进程环境缺 `OLLAMA_API_KEY`（.bashrc 在启动后写入）+ 进程名实为 `openclaw-gateway`（连字符），两次重启排障后 `env-has-key:1` 生效

## ISC-21 · 换脑素材（同一问句双脑存证）

| 脑 | 轮数 | 工具调用 | 延迟 | 结果 |
|---|---|---|---|---|
| step-3.7-flash（StepFun 云端） | 4 | 3 | 19.2s | 金答案精确 |
| nemotron-3-super-120b（GB10 本地） | 3 | 6 | 201.9s | 金答案精确 |

全文：`brainswap-stepfun.md` / `brainswap-nemotron.md`——同一问句、同一 skill、两颗脑子、同一个正确答案，只有速度差。

## ISC-22 · 塔台（自建证据面板，跑通）

- `panel/app.py`（Streamlit，零 LLM——库存/供应商/缺口/预测全经 skill 工具层直算）
- 验收：租机 `:8501 → HTTP 200`（headless 常驻）
- R2 说明：上游原版塔台依赖 Gemini/Vertex key（config.json 实测），不可得 → 按修正案 R2 以自建证据面板替代（原版快照保留在 `case/`），**未触发 4 小时止损线**（面板 ~45 分钟建成）

## BENCHMARK 补充

- nemotron/skill run3（R8 轮上限）：**11/12**（挂题 neg-stk-003；三轮全景 12→9→11，区间 75–100%，详见 BENCHMARK.md 版本注记）
