# PROJECT-BRIEF · repro-pack 团队对齐文档（v2，2026-09-24）

> 给三位队友的 10 分钟对齐材料。读这一份 = 知道我们在做什么、为什么、谁干什么、还剩几天。
> 深入阅读地图在文末。

## 一、我们在做什么（一句话）

把 GitHub 上真实的 **FDE（前线部署工程师）行业落地案例**转化成 **Agent Skill**——推荐题：**供应链控制塔 skill**（源：`tensor-house/supply-chain/control_center_llm`，Apache-2.0）。

**叙事主线**（也是 README 开场白）：MIT 报告——企业 AI 项目 95% 烧钱无价值；FDE 岗位一年涨 7 倍（范冰《前线部署工程师》开篇）。缺的不是模型，是把模型塞进真实业务的能力包——**Skill 就是这个能力包的形态**。

## 二、为什么是①（团队今晚确认的事）

- **证据链**：数据自带（inventory/products/suppliers 实测在仓）· Streamlit UI 现成（演示分白送）· License Apache-2.0 可合规转化 · 原项目挂 Gemini-pro（我们换 3.7-flash = 换脑叙事独一份）· NVIDIA catalog 无同类 skill（不撞车）
- **评分锚定**（官方权重）：实用性 25 ✓（真实运营形态）· 技术深度 25 ✓（原话就是「Skills 设计与融合」，skill 化工程+evals 层踩分）· 平台适配 15 ✓（OpenClaw 已装上 DGX Spark + 本地 120B 备脑已上线）· 演示 10 ✓（UI 现成）
- **唯一未验证项**：原项目 `processors/` 的真实覆盖面——**锁定①后我第一件事就是克隆实测**，翻车则 ②（需求预测→补货）按接棒条件顶上（条件写在 `docs/topic-deepdive/02`）
- 四候选完整攻击与回答：`docs/topic-deepdive/01-04`（位次 ①>②>③>④）

## 三、已经建成的资产（不用重做，全部实测过）

| 资产 | 状态 |
|---|---|
| 租机 DGX Spark（GB10/119Gi/CUDA13/Docker/sudo） | OpenClaw 2026.9.5 + ffmpeg + Node26 已装机 |
| 本地大模型 | **nemotron-3-super-120b（87GB）已上线租机**，加载 73 秒——平台适配的实物证据 |
| 主脑定案 | **step-3.7-flash**（与 Nemotron head-to-head：质量 5.0/5 vs 3.7/5，更快更稳） |
| 工程流 | mattpocock skills + closeloop 台账（ISA 11 条验收纪律）+ 私仓（三人已授权） |
| 评测方法论 | evals+负例零误触+BENCHMARK——在 repro-pack 上全链验证过 |

## 四、时间线（期限不重排，baseline 2.0）

| 日 | 事 |
|---|---|
| **9/24 晚** | 团队对齐锁题① → 我克隆实测 processors → SPEC v2 + 工单落地 |
| **9/25–9/26** | 建造：skill 主链（processors→scripts、SKILL.md、输出契约、负例）→ evals → 上 Spark 部署 + Streamlit 塔台 |
| **9/26 晚** | **冻结 v0.1.0**（只修不加） |
| 9/27 | README/演示视频/BENCHMARK 收尾 |
| 9/28 | 发布（公开仓 push 需 Evander 点头 · 视频传 B 站 33official · 征文发 CSDN/知乎标注 AI 生成） |
| **9/29 12:00 前** | 表单提交（仓 URL + B站 URL + 征文 URL + 合影 + 500 字 README） |

## 五、分工（默认版，对齐会上可调）

- **Evander（O）**：主链 skill 化 + SPEC/台账 + Spark 部署 + 换脑演示素材
- **abloom25（T）**：evals runner + BENCHMARK 数据 + README 主体（500 字要求）+ 十日谈征文初稿
- **罗登思**：B 站演示视频（脚本我用 ① 的素材现成配好）
- **机主（alingalingling）**：算力线已交付大半（租机/权限），剩余为演示时段配合；想接活任挑 P1

## 六、两条红线（不商量）

1. **负例零误触**：库存充足问「要不要补货」，正确答案=不补——任何误触即 P0 失败
2. **密钥零提交**：key 不进 git、不进群（赛规原文）

## 阅读地图（按序，全在私仓 littlerodents/repro-pack）

1. 本文档 → 2. `docs/topic-deepdive/01-control-tower.md`（①的完整攻击与证据）→ 3. `docs/TOPIC-RESEARCH.md`（搜索过程+模型对比数据）→ 4. `ISA.md`（全部决策留痕，含 repro-pack 为什么改道的 D12）→ 5. `CONTEXT.md`（黑话表）
