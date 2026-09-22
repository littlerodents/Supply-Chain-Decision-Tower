# repro-pack

> 把「报 bug」从人类描述升级为 agent 接单：录屏进，**复现包**出，修复 agent 直接消费。
>
> 第三届 NVIDIA DGX Spark 黑客松 · Agent Skills 开发挑战赛 参赛作品（预赛）。

## 为什么（AI 时代报 bug 的方式变了）

能接入的场景，对方 agent 直接远程接手，描述已死；给不了接入的场景（黑盒 SaaS、瞬态 bug、安全边界、审计），录屏仍是唯一目击证据——但消费它的已从人类工程师变成修复 agent。**repro-pack 就是这座桥**：把一段操作录屏装配成 agent 可直接开工的复现包。

> 🚧 D5（9/27）前填充以下各节至 500 字以上（赛规要求）。

## 是什么

（复现包四件套：bugcard.json / frames/ / repro.md / GitHub issue，含负例契约）

## 部署说明（赛规必填）

- 本地算力：DGX Spark 上的 OpenClaw workspace 安装本 skill（`npx skills add` / 训练营配方），`openclaw skills list --eligible` 验证
- 主脑：StepFun 多模态端点（三值环境变量：`REPRO_BASE_URL` / `REPRO_MODEL` / `REPRO_API_KEY`），step-3.7-flash 与 step-5-preview 双模型对照见 `benchmark/BENCHMARK.md`
- 大模型优化与 Agent Skills 设计思路：（D5 填）

## 技术栈说明（赛规必填）

- NVIDIA：DGX Spark（GB10，本地算力运行面）、OpenClaw
- StepFun 阶跃星辰：step-3.7-flash / step-5-preview（Coding Plan）
- 开源模型备脑：Qwen（图片模式，换脑演示）

## 评测

`evals/evals.json`（≥8 正例 + ≥2 负例）+ A/B 实测数据见 `benchmark/BENCHMARK.md`（负例零误触是 P0 硬指标）。

## 安装与使用

```bash
npx skills add <本仓库> --skill repro-pack --yes
python3 skills/repro-pack/scripts/repro_pack.py <你的录屏.mp4>
# 负例 → 末行 NO_BUG_FOUND；正例 → 末行 PACK:<包目录>（或加 --no-issue 只产包）
```

## Roadmap（Future work，立碑不建）

P2：限时最小权限的 agent 安全接入端点（录屏证物 → 接入交接的下一步）。

## 团队

Evander（O）· 队友（T）。开发历程见十日谈征文（链接 D6 更新）。
