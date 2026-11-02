# BENCHMARK · supply-chain-control-tower（阶段性测量，非验收报告）

> 2026-09-26 核对。12 题任务集：8 条正例、3 条负例、1 条无关；金答案由工具直算。下表是**本地评测 runner** 的留存文件统计，不是 DGX OpenClaw 真入口的通过率。`evidence/` 被 gitignore，私仓读者目前无法仅凭仓库复核原始 JSON。`tools/run_evals.py` 有未验收的 `--verify` 实验改动，重跑前须隔离输出，不能覆盖旧证据。

| 模型与条件 | 现存原始文件 | 留存结果 | 解释边界 |
|---|---|---|---|
| StepFun / 裸 | `results-stepfun-bare.json` | 2/12 | 裸组没有与 +skill 组等同的数据/工具权限，不能直接计算 Skill 因果增益 |
| StepFun / +skill | `results-stepfun-skill-run2.json` | 10/12 | 曾记录 12/12，但同名原始文件现被审计试验覆盖成 4/4（审计工具调用 0 次），**不能作为完整 12 题复核证据** |
| Nemotron / 裸 | `results-nemotron-bare.json` | 2/12 | 同上，不能直接归因 |
| Nemotron / +skill | `results-nemotron-skill.json`、`-run2.json`、`-run3.json` | **12/12、9/12、11/12** | 轮次上限/提示词版本不完全相同；单次 12/12 不能称稳定满分 |

以上文件均在本地 `evidence/evals/`。StepFun 当前 `results-stepfun-skill.json` 仅 **4 条**，不是原来的 12 题结果；历史 `summary.json` 对 StepFun/+skill 目前也仅记 `n=1`。不得拿被覆盖的文件名或 4/4 冒烟恢复已失去的基线。

## 真入口：2026-09-26 DGX OpenClaw（阻塞）

在真实 Gateway 用 SKU 13001 / San Francisco / 12 周自然问句，多个新会话 `status=ok` 却只说要查运费、**没有决策 JSON**；按绝对路径试探与临时 Skill 文档修正都未解决，远端文档已回滚。OpenClaw 的 Skill 列表虽为 `✓ ready`，不能替代入口验收。

OpenClaw 官方支持 `$技能名` 显式引用；一次正例因此输出了正确的数量 **3268**、供应商 Nature Source Coffee、总价 **119282**，但只是 Markdown，**未满足决策 JSON 契约**。另一独立负例（SKU 13001 / Seattle / 1 周）工具直算缺口 **+100**，Gateway 在 26 次工具调用后仍没有给出 `NO_REORDER:100`。因此不能写「负例零误触已在真入口验证」。详见 `evidence/2026-09-26-iris-preflight/PROBE.md` 与 Gateway 留存轨迹；入口证据为代理操作机器自证，非主人签收。

## 目前可以／不可以得出的结论

- **已证实**：工具层对指定样本可直算金答案；DGX 上 OpenClaw 能识别安装的 Skill；本地 runner 在若干条件下有上述命中数。
- **未证明**：宿主 OpenClaw 自然问句能稳定按契约出单；两种模型等权限对照下的 Skill 因果增益；跨模型稳定性、有效的多 agent 审计、Iris 串接收益。
- **下一验收**：先在两个独立新会话得到严格正例 JSON（`decision=REORDER`、3268、Nature Source Coffee、119282，含工具证据），并在负例新会话末行输出 `NO_REORDER:100`、零补货建议；再用相同数据/工具权限和锁定提示词版本重复评测，单列失败轮与延迟。未过则保留阻塞状态，不拍成成功演示。
