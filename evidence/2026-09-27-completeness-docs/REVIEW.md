# 前端 PRD / 完整性 SPEC · 文档验收

## ANCHOR（2026-09-27 06:03 CST）

本轮交付：`docs/FRONTEND-PRD.md` 优先，其次 `docs/REVIEW-COMPLETENESS-SPEC.md`，同步 ISA/STATUS。只读来源及文档变更；不安装依赖、启动本机服务、操作 Terminal、连接模型、改 DGX 配置或发布。

文档 DONE 判据：全文可读；页面结构、用户流程、状态、数据单位、边界和验收样例明确；完整性原文六要求映射到 PC-01~06；引用文件真实存在；样例数字与工具/金答案相符；STATUS 当前排序与 D15 一致。验收只代表文档内容核对，不代表 owner 批准了产品取舍或产品已上线。

失败清单：
1. 把 StepFun 云端历史成功偷换为本地入口成功。
2. 图表标题/单位/零缺口或无记录语义与代码、数据矛盾。
3. 页面只有愿景，没有输入冲突、请求状态和错误/回放行为。
4. 路径断链或 PRD 与 PC/ISA 互相矛盾。
5. 改写现有工具、旧评测、冻结 SPEC 或无关用户改动。

必要：文档静态检查通过。充分（限文档）：明确上述可实施与可证伪合同并把文件入口交给主人。产品 DONE 仍须真正浏览器及模型入口证据；此次无动态 UI 验收，也无新的主人签收。

## GROUND

06:03–06:08 回读项目 AGENTS/CONTEXT/SPEC/ISA/STATUS、两份草稿、panel/app.py、tools.py、SKILL.md、CSV、gold.json、README、AB 报告与 Qwen 原始终答。本轮 SSH master socket 不在；没有新建连接或使用口令。

红队发现：
- 面板标题写「52 周」，实际 `head(weeks if weeks >= 8 else 12)` 只画 8–26 或 12 点，PRD 初稿也误把 52 周写成现有 UI。
- `gap >= 0` 包含 0；初稿写「正gap」会漏掉恰好充足，需明确 `NO_REORDER:0`。
- 缺库存行被工具当作 0；SKU13001/Portland 在 CSV 无行，UI 不能将其冒充盘点为 0 的事实。
- 初稿引用 `scripts/tools.py`、`ab-comparison/` 等省略了根目录，不适合作为可点击证据入口。
- `STATUS.md` 仍用 D14 的平台先行排序，未反映 D15 前端 PRD 优先及本地入口未过。

## VERIFY（2026-09-27 06时本轮真实执行）

命令均在仓库根以 `PYTHONDONTWRITEBYTECODE=1 python3 -B -` 执行一次性只读断言；Markdown使用本机已有 `markdown_it.MarkdownIt('commonmark').enable('table')` 内存渲染，无安装/服务器。另跑 `git diff --check` → exit 0；新文档不在git diff中，另逐行检查末尾空白/代码围栏/文件末尾换行。

| 文档判据 | 真跑结果 |
|---|---|
| 文本/表格可加载，链接可解析 | 前端PRD和完整性SPEC均成功渲染；本地链接 **14/14、13/13** 存在；STATUS新增3/3链接存在。不是浏览器视觉验收 |
| 需求覆盖 | FE-01~08、T-01~08、PC-01~06存在；状态/请求id/本地约束/零缺口条款齐，六项评审文字有对应内容 |
| 工具事实与金答案 | import实际tools.py，直接调用gap与shipping并读取CSV/gold：正例30/3298/-3268、负例300/200/+100；Decimal核算3268×(34.50+2.0)=**119282.00**，供应商Nature Source Coffee，全部断言通过 |
| 已知风险不是凭空编造 | SKU13001/Portland库存无行，工具仍返回current_stock=0；SKU11001供应商发货地SF；按现有图截取逻辑，所选1/12/26周对应12/12/26点 |
| 文档红队实验 | 仅改内存副本：把正例总价119282.00改119284.00、抹去NO_REORDER:0、破坏tools.py链接；三种变异均被对应检查拒绝 **3/3**。只证明文档检查能抓这些错，不证明产品实现已处理它们 |
| 状态一致 | ISA真实复选框 **11/14**，frontmatter一致；STATUS含D15、FE-01~08、PC-01~06，项目仍PARTIAL；未关闭新产品ISC |
| 旧证物/代码保护 | 与改文档前采样比较，工具/面板/冻结SPEC/现有材料/8份评测JSON **15/15 SHA256不变** |
| 历史入口分界 | 回读8份已存在原始JSON：正例按八字段/decision/3268/供应商/119282核对，负例核对末行与无order_qty；StepFun3/3、Nemotron1/3、Qwen0/2，与PRD吻合。此处是历史文本复核，不是新模型试验，也不是负例全文语义安全的独立证明 |
| 凭据与副作用 | 仅针对四份本轮文档检查常见key/私钥/密码文本模式，0命中；未做全仓密钥安全声明。未连接DGX/模型、未使用口令、未启服务、未发布 |

### 验证后的文档指纹

- `docs/FRONTEND-PRD.md`：`df5a51e1dee3295a6fece6bd9925317abbd61665ef57108ae3f022f7674f25e0`
- `docs/REVIEW-COMPLETENESS-SPEC.md`：`9acd468f8ed6286679d4ef4e3dade0544bab05d09c3b7ec251cb2fd630c4f1c6`
- `STATUS.md`：`5050b0bc4547b93dd5ac0bc7567bebe9690e1ab0ad00e828232b8dd1d1b9c3a0`
- `ISA.md`：`63ba26f40982d2a308e847d14df425107edf79617a9bd9a8f39904636981459a`

### 保护文件指纹（前后相同）

| 仓库相对路径 | SHA256 |
|---|---|
| tools/run_evals.py | 02b87ab711548f60ec6faa6874cdd28622e3962e4908d2bb757c1a592986a1d3 |
| skills/supply-chain-control-tower/panel/app.py | da7de9cf3f443aabb37ac76d8e2a3518f821d74ba354a84c41f61e6c2e41236c |
| skills/supply-chain-control-tower/scripts/tools.py | edb9285af5f7e1c5db68f899b8786bbcd487b0b2a289dce9e6a34ca534ad296d |
| SPEC.md | 2826e32c6abb974543a7ee4be48a7bef6ab6ccfe96ddd762edbf19e38b10900e |
| README.md | 83120744ad8e5ed63b1daaa96fc6a00d6c349758b2bee02f0e3f006f37c82ea8 |
| benchmark/BENCHMARK.md | a04cf76de9d6225b78a5b1521025bc3ae2d05c0af67083a08dc6046fb9cbc853 |
| docs/VIDEO-SCRIPT.md | eabfd071e90559bdd8edce90b164c9a65163a80de407ba4d9f25730fd8840858 |
| evidence/evals/results-nemotron-bare.json | f5c741f0564fe35f557e02f0b082a322aad7f8c18863df91516b10722b5448c6 |
| evidence/evals/results-nemotron-skill-run2.json | 6d8b7775e045105df2bb78b51e809b9dd76df29ce1ee394bddd3b992c7c9313a |
| evidence/evals/results-nemotron-skill-run3.json | 8487db66d7b11403289b16a0cd29bdac9593af020a21f011851b6f1d4cd1fcdb |
| evidence/evals/results-nemotron-skill.json | 53c4bed26de51fe0708fb2aa3d7ab5557debcf37b4f432194c63cbf5bfff9192 |
| evidence/evals/results-stepfun-bare.json | 676494de9f18288c8796fbef14b87166c4428db3fd0e7c07b6d2d048de3fc338 |
| evidence/evals/results-stepfun-skill-run2.json | 5dc4e2cf5c799576da805b74500761baa13a0171994afa5c8367f9e01250f0f0 |
| evidence/evals/results-stepfun-skill.json | 1f18b7e4cbc859042b093bbd27335eecf5d4f9a85cf7377dd703b102cfc74d84 |
| evidence/evals/summary.json | ec29236b2cf9cdc8da028006a203ade7396fe47d76ba9215c64ee9ac76595f8f |

## 灰度结论

五条文档失败清单已逐项核对，文档可交付审阅；**不是产品DONE，也不是新的owner签收**。前端集成、真实浏览器、当下DGX运行、本地模型正例、长期稳定性和公开复现包均未验/未完成。无代码或配置交付物，本轮未重跑代码交付机械闸门，未借旧StepFun闸门升级产品状态。两份规格与ISA/STATUS为本轮唯一项目文档变更，另留此本地忽略证据；现有未提交工作不回滚、不提交。
