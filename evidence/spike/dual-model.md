# D1 Spike 结论文档 · 双模型对照（ISC-3 证据底稿）

> 2026-09-22T19:04Z · 合成测试片 clip.mp4（6s，Error 500 出现于 2.0s）· 3 runs/model
> 原始数据：`dual-raw.json` / `dual-run-console.txt` / 探针 `text-*.json` `image-*.json` `video-*.json`

## 机制定案（kill-switch #1 解除）

- StepFun 视频输入：**`video_url` + base64 data URI 直接过**（两模型同形态命中），无需 URL 上传，本地文件直进端点
- base_url：`https://api.stepfun.com/v1`（官方 Quickstart 确认）；model id：`step-3.7-flash` / `step-5-preview`（官方表格：均支持文本/图片/视频）
- 端到端：正例 → `PACK:` + 三件套（bugcard/frames×3/repro.md）；负例 → exit 0 + `NO_BUG_FOUND` + 零产包（`e2e.txt`）

## 三维对照

| 维度 | step-3.7-flash | step-5-preview | 判定 |
|---|---|---|---|
| 质量命中（gold 三字段） | 1/3 × 3 次 | 1/3 × 3 次 | **平**（无区分度，见教训） |
| 中位延迟 | **10.18s** | 15.87s | **3.7 Flash 胜 ~36%** |
| 平均 tokens | **5506** | 5687 | 3.7 Flash 略省 |
| 输出稳定性 | 3 次输出完全一致 | location 措辞 3 种变体 | 3.7 Flash 更稳 |
| 模型状态 | 生产级 | **preview**（平台有「模型下线与迁移」页） | 3.7 Flash 无下线风险 |

## 定案（D2 provisional）

**主脑 = `step-3.7-flash`**（质量平 → 看延迟 → 赢；另加稳定性 tie-breaker：preview 有下线风险）。
**备脑/换脑演示 = `step-5-preview`**（1M 上下文是它的独有卖点，README 换脑一节用）。

## 教训（喂给 T2 的 gold 设计）

1. `location_kw` 必须双语（"save/保存"）——英文关键词对不上中文回答，本轮 location 全落选是 gold 的锅不是模型的
2. `type` 分类学要在 T2 gold 里写死口径（Error 500 → network 还是 runtime-error，两模型一致判 network，建议 gold 跟模型口径走）
3. 质量维度在合成片上无区分度——**ISC-3 的质量结论以 D4 真实任务集为准**，本文件只定机制+主脑 provisional
