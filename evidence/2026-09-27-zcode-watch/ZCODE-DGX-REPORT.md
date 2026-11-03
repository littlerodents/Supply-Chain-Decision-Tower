# Zcode / DGX 只读观察简报

## 一、先看结论

报告更新时间：11-02 14:45:27 CST

最后实际采样：09-27 17:34:39 CST

监测状态：STOPPED_DEADLINE；停止线：09-27 17:39:00 CST

累计本地采样：133；有效远端探针：21；共享文件变化：9；远端状态变化：9。

远端未观测：本版最后采样没有有效只读探针。已知共享文件不等于DGX实时运行事实。

所有未签名文件变化均为“作者未知”，不能归因Zcode；未订阅私有会话或终端历史。

旧监控目录/任务在09-27 06:23核查时缺失，SSH socket也不存在；中断原因未知，不能声称此前连续在线。

## 二、不符合验收要求的地方（针对产物，不针对人）

### [P0] 远端未观测

没有可复用的已认证SSH通道/有效探针；不能判断Zcode此刻在DGX做了什么，也不能保证服务正常。

### [P0] 本地正例仍缺通过证据

留存本地模型正例未满足合同。StepFun云端成功不能替代本地入口；此为既有样本复核，不是新推理。

### [P1] 面板仍是工具证据面，不是聊天闭环

已知版本图题52周却截取12/26等点；缺库存记录可被当0；Seattle固定参考运费易被误认作实际路线。按FE-01先修，再从浏览器取证。

### [P1] 旧评测判定器不足以证明增益

既有离线反证：错误gap/补货建议可误判PASS；四题审计0工具/0修正。不把不同worker轮次2/4→4/4当协同收益。

### [P1] 闭环证据仍要补齐

固定规则只能核对留存终答；不证明真实工具逐步轨迹、当下UI、稳定性、GPU收益或主人签收。

## 三、本轮发生了什么（观测时间，不是实际变更发生时间）

09-27 06:43:17 CST | ISA.md | 作者未知 | 63ba26f40982 → 4c549ba8144e

09-27 06:43:17 CST | STATUS.md | 作者未知 | 5050b0bc4547 → a99b170ee306

09-27 15:03:52 CST | STATUS.md | 作者未知 | a99b170ee306 → 84af854879cd

09-27 15:08:52 CST | ISA.md | 作者未知 | 4c549ba8144e → 9890c2758e63

09-27 15:43:56 CST | DGX/panel/app.py | 作者未知 | 6f932197d697 → 8e480f310384

09-27 16:04:08 CST | STATUS.md | 作者未知 | 84af854879cd → 0ee6fbe2d566

09-27 16:09:14 CST | ISA.md | 作者未知 | 9890c2758e63 → f42bfab5cccf

09-27 16:29:24 CST | DGX/panel/app.py | 作者未知 | 8e480f310384 → 187d1d4d3b7f

09-27 16:34:25 CST | DGX/data/inventory.csv | 作者未知 | 3da1d077c38a → e63aed1dd691

09-27 16:34:25 CST | DGX/data/suppliers.csv | 作者未知 | 47a10fa7bf26 → d2acaa3e53f8

09-27 16:39:26 CST | DGX/panel/app.py | 作者未知 | 187d1d4d3b7f → c4feead2303e

09-27 16:44:28 CST | DGX/panel/app.py | 作者未知 | c4feead2303e → b2f97807afa9

09-27 16:49:29 CST | DGX/panel/app.py | 作者未知 | b2f97807afa9 → 2bf80c54a9f0

09-27 16:54:30 CST | DGX/panel/app.py | 作者未知 | 2bf80c54a9f0 → d13f8c2d72aa

09-27 17:09:37 CST | DGX/panel/app.py | 作者未知 | d13f8c2d72aa → 4fa8578be381

09-27 17:29:39 CST | ISA.md | 作者未知 | f42bfab5cccf → da8d16172835

09-27 17:29:39 CST | STATUS.md | 作者未知 | 0ee6fbe2d566 → ab0e040a39fb

09-27 17:34:39 CST | ISA.md | 作者未知 | da8d16172835 → 6bfe70015763

采样缺口次数：0；本机睡眠/关机时无法采样，恢复后不补造记录。

## 四、既有工作与证据边界

历史已留证：StepFun显式云端三例；本地Nemotron/Qwen失败轮；前端PRD与完整性SPEC已落盘。下面仅重新核对本机原始回执的格式/核心数字，不执行新模型，不作为本轮动作归因。

step-pos1：TEXT_CHECK_PASS；原回执耗时=12935 ms。

step-pos2：TEXT_CHECK_PASS；原回执耗时=12092 ms。

step-neg1：TEXT_CHECK_PASS；原回执耗时=7744 ms。

nem-pos1：TEXT_CHECK_FAIL；原回执耗时=69152 ms。

nem-pos2：TEXT_CHECK_FAIL；原回执耗时=171124 ms。

nem-neg1：TEXT_CHECK_PASS；原回执耗时=44333 ms。

qwen-pos1：TEXT_CHECK_FAIL；原回执耗时=32657 ms。

qwen-neg1：TEXT_CHECK_FAIL；原回执耗时=98704 ms。

TEXT_CHECK_PASS仅是固定格式/数字筛查，不等于全面语义正确、真实工具轨迹或主人入口通过；负例零误触仍需严格复核全文。

## 五、醒后建议顺序

1. 先看远端观测覆盖：没有通道则远端活动未知，不能据此评价Zcode是否完成了部署。

2. 对照docs/FRONTEND-PRD.md的FE-01~08与docs/REVIEW-COMPLETENESS-SPEC.md的PC-01~06；源码改变后要求新鲜入口证据，不把静态检查当上线。

3. 先守住本地入口与负例；旧StepFun云端成绩仅作对照。模型路线是独立决策，本监控不改默认脑。

4. 文档/视频口径、公开证据包及凭据轮换仍要独立处理；本任务不发布、不替主人签收。

## 六、来源、停止与局限

来源：ISA.md、STATUS.md、前端PRD、完整性SPEC、panel/app.py与tools/run_evals.py哈希；evidence/2026-09-26-iris-preflight/ab-comparison内8份回执。

可复核文件：同目录state.json、events.jsonl（仅元数据与检查结果）、watch.py、test_watch.py；完整回执不复制进PDF。

每5分钟更新一次。报告日期之后的动作不在本版覆盖内；新文件若不在固定白名单不会自动发现。

到17:39停止；运行期间只读，不用口令、不看凭据/配置、不跑模型、不执行被监测代码、不抢Terminal、不改变DGX、不安装依赖。

本机只有一个低优先级监测进程和PDF/JSON文件写入；机器睡眠或进程中断时报告可能变旧。

baseline 2.0及冻结不变。当前总体PARTIAL；此报告不是已完成项目、完整审计或主人签收。
