# spike_plan.md · D1 双模型对照运行手册

> 目标：一天内回答三个问题——①StepFun 视频输入能不能直接吃录屏；②3.7 Flash 和 step-5-preview 谁当主脑；③fallback 要不要启用。

## 第 0 步 · 读一手文档（GROUND，不许跳）

带 key 登录后读官方文档，确认 base_url、模型 id、视频输入的确切参数形态与大小限制：
- `https://platform.stepfun.com/docs/zh/guides/models/step-5-preview`
- `https://platform.stepfun.com/docs/zh/guides/models/step-3-7-flash`（或站内搜索 3.7 Flash）
- Quickstart：`https://platform.stepfun.com/docs/zh/quickstart/overview`

若文档给了明确视频参数形态 → 改 `tools/openai_compat.py:video_part_variants()`，把命中的形态放第一位。

## 第 1-3 步 · 探针梯子（各模型各跑一遍）

```bash
export REPRO_BASE_URL=<文档给的端点> REPRO_API_KEY=<key>
python3 tools/probe.py text
python3 tools/probe.py image assets/samples/shot.png
python3 tools/probe.py video assets/samples/clip.mp4                      # 默认 3.7 Flash
python3 tools/probe.py video assets/samples/clip.mp4 --model step-5-preview
```

判据：text 必须回 PONG；image 必须出非空描述；video 四种形态命中任意一种即 PASS。

## 第 4 步 · fallback（video 全挂才走）

`ffmpeg -i clip.mp4 -vf "fps=0.5,scale=1280:-1" frames_%02d.png` → 用 image 模式拼时间戳序列。
抽帧质量评估：拿同一段录屏，问模型能否定位错误帧；误差 >5s 或完全答非 → kill-switch 触发，回 ISA 更新 D2，向 owner 报告换脑/换题选项。

## 第 5 步 · 双模型对照（ISC-3）

同一段 30s 含 bug 录屏，两个模型各跑 3 次，记录到 `evidence/spike/dual-model.md`：

| 维度 | 记录什么 | 怎么测 |
|---|---|---|
| 质量 | bug 类型/位置/时间戳是否命中 gold（T2 的第一段录屏当 gold） | 对照 gold 逐字段打勾 |
| 延迟 | 3 次中位延迟（s） | probe 输出的 latency |
| 成本 | 3 次平均 usage tokens | probe 输出的 usage |

**定案规则**：质量打平看延迟，延迟打平看成本；任何一维差 >2 倍即出局。结论 + 原始输出一起进 `evidence/spike/dual-model.md`，并回填 ISA D2。

## 红线

- key 只进环境变量， spike 产物（evidence/ 已 ignore）里不得出现
- 3 次失败仍无结论 → 记录现状，升级 owner，不许默默换题
