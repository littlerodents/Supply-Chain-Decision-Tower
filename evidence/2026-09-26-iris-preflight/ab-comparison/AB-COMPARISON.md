# A/B 对照 · StepFun 3.7-flash vs 本地 Nemotron-3-Super-120B（2026-09-27 00:0x CST）

> 同机同网关（DGX spark-5c72，systemd openclaw-gateway）、同 Skill（SKILL.md 已修 119282）、同三问自然问句、同严格判据（正例=八字段决策 JSON 含 3268/Nature Source Coffee/119282 + 工具证据；负例=末行纯文本 `NO_REORDER:100` 零补货建议）。唯一变量=脑子（`--model` 逐次指定）。会话 id：StepFun 腿 `pi-dgx-step26c-*`，Nemotron 腿 `pi-dgx-nem26-*`。原始 JSON 同目录。

## 结果矩阵

| 问句 | StepFun 3.7-flash | Nemotron 120B（本地 ollama） |
|---|---|---|
| 正例1「SF SKU13001 12周够卖吗」 | ✅ **PASS** 12.9s / 4 工具 0 失败 / 八字段 JSON：3268、Nature Source Coffee、34.5+2.0、**119282.0**、tool_trace gap·suppliers·shipping | ❌ **FAIL** 69.2s / 2 工具 **2 失败** / 无任何关键数字；终答反问用户「你有数据文件吗」 |
| 正例2「帮我决策补多少」 | ✅ **PASS** 12.1s / 4 工具 0 失败 / 同上全对 | ❌ **FAIL** 171.1s / 1 工具 0 失败 / 无数字；终答「请把相关数据点发我」 |
| 负例「Seattle 1周够卖吗」 | ✅ **PASS** 7.7s / 2 工具 0 失败 / 末行纯文本 `NO_REORDER:100`、300/200/+100 对 | ✅ **PASS** 44.3s / 3 工具 0 失败 / 末行纯文本 `NO_REORDER:100`、300/200 对 |
| **严格通过率** | **3/3（100%）** | **1/3（33%）** |
| 总耗时 / 总工具失败 | 32.7s / 0 | 284.6s / 2 |

## 关键观察

1. **正例（多步决策链）是分水岭**：StepFun 三步工具链（gap→suppliers→shipping）一次成型并按契约吐 JSON；Nemotron 两轮正例都没能完成工具链——本轮的失败形态是「向用户索要数据」（pos1 还伴随 2 次工具执行失败），与早前 hooktest 轮的「宣告动作即自停」同属链路中断，形态不稳定。
2. **负例（单步判断）本地脑可过**：Nemotron 负例 44 秒严格通过（末行恰好纯文本）。本地脑不是全坏，是**步骤越多越不可靠**——单步 1/1，两步以上 0/2。
3. **速度差 4–14 倍**：同判据下 StepFun 7.7–12.9s vs Nemotron 44–171s。
4. **与 harness 历史一致**：仓内评测（ISA N4/收割记录）stepfun+skill 两轮 12/12 稳定、中位 6.6s；nemotron+skill 三轮 12/9/11 不稳、中位 97s。入口 A/B 与 harness 两个层面互相印证。

## 结论

**在「真入口 + 严格契约」口径下，StepFun 3.7-flash 显著优于本地 Nemotron-120B：正例 2/2 vs 0/2，全判据 3/3 vs 1/3，速度 32.7s vs 284.6s，工具纪律 0 失败 vs 2 失败。** 本地 Nemotron 的可靠域目前只有单步负例判断。演示默认脑建议 StepFun（本地脑保留作换脑 A/B 素材与离线兜底叙事）。

## 证据件

- StepFun 腿原始 JSON：`step-pos1.json` / `step-pos2.json` / `step-neg1.json`（= step-acceptance/ 同源副本）
- Nemotron 腿原始 JSON：`nem-pos1.json` / `nem-pos2.json` / `nem-neg1.json`
- 判据来源：ISA「2026-09-26 22:43」节 owner 写死的充分条件 + SKILL.md §38
- 环境基线：Gateway systemd PID 2640896 起步；每腿会话 id 独立；远端 /tmp/pi-dgx-{step26c,nem26}-*.json 留存


---

# 追加 · Qwen3-30B-A3B 本地腿（2026-09-27 01:0x CST）

> owner 约束「不想用云端」后补测的第二个本地脑：ModelScope 直下 Qwen3-30B-A3B Q4_K_M GGUF（18.56GB，SHA256 与官方清单一致 `0d003f66…`，均速 ~24MB/s/13min），`ollama create qwen3:30b-a3b-local` 注册。嵌入模板含标准工具渲染（<tools> XML + <tool_call>），非模板缺失。

| 问句 | 结果 | 形态 |
|---|---|---|
| 正例1 | ❌ FAIL 32.7s / 26 调用 **16 失败** / 无数字 | 未读 SKILL.md，掉进 tool_search 目录，把目录条目名（canvas/notion/tmux 等）当工具连调 16 败；终答「无可用工具，请提供数据」 |
| 负例 | ❌ FAIL 98.7s / **57 调用** 2 失败 / 无 NO_REORDER | 换了形态：用了 read/exec/process 但工具循环不收敛，终答停在「我再找找别的 skill」 |

（pos2 未跑：pos1 失败签名已明确，按止损纪律不再烧轮次。）

## 三腿终局（同机同网关同 Skill 同问句同严格判据）

| 脑 | 部署 | 严格通过 | 正例多步链 | 总耗时 | 工具纪律 |
|---|---|---|---|---|---|
| StepFun 3.7-flash | **云端 API** | **3/3** | 2/2 一次成型 | 32.7s | 10 调 0 败 |
| Nemotron-3-Super-120B | 本地 ollama | 1/3 | 0/2（向用户索要数据） | 284.6s | 6 调 2 败 |
| Qwen3-30B-A3B Q4 | 本地 ollama（导入 GGUF） | 0/2 | 0/1（工具名幻觉） | 131.4s | 83 调 18 败 |

**结论：在「入口不用云端」约束下，现有两颗本地脑都无法通过真入口验收。** 本地失败形态还各不相同且不稳定（索要数据 / 宣告即停 / 工具名幻觉 / 循环不收敛）——这是 120B/30B 级模型在 32k 上下文 + 多步工具契约下的系统性短板，不是单次运气。原始 JSON：qwen-pos1.json / qwen-neg1.json。
