# 监测与PDF · 验证回执（2026-09-27 06:43 CST）

## 已验证

- 代码/测试：`PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/2026-09-27-zcode-watch/test_watch.py` → **9 tests OK**，原输出 `test-output.txt`。真实红灯包括缺实现、远端变更计数缺失、深嵌套JSON导致RecursionError；修后全部通过。
- 红队：符号链接源被拒、不复制canary、变更代码不执行、无socket不调用SSH、失败master不发探针、远端响应按字段白名单去掉额外内容、变化不归因Zcode。远端成功样本是模拟系统边界的测试，**不是DGX现场成功**。
- 到期真实进程实验：临时夹具、3秒截止、实际命令退出0，耗时**3.09秒**；状态STOPPED_DEADLINE、active=false、只采1次、远端0次。生产截止设为2026-09-27 17:39 CST，真正截止尚未到，不声称已观察其退出。
- Plist：`plutil -lint /Users/evander/Library/LaunchAgents/com.evander.pi.zcode-report-watch.plist` → OK；该自有任务bootstrap后 `state=running / PID16088 / runs=1 / never exited`。不动任何DGX服务。
- 心跳：一次性首版06:36:26.916；后台首样06:38:04.633；后台次样06:43:17.997。两个**实际后台**采样相隔**313.364秒**（约5分钟，另含渲染开销），samples=3（含首版），remote_samples=0。PDF自动更新为155025 bytes，SHA256 `0b3ed11aa4136920b067884882d9ef22930f36b2890f0c8e314be41e52b325c7`；这是06:43版本，随后正常更新会改变哈希。
- PDF：reportlab使用系统STHeiti嵌入子集字体；pypdf读取两页及中文关键词通过；pdftoppm转PNG后回看两页，标题、风险、来源、未知范围可读。预览在 `preview-page1.png` / `preview-page2.png`（早期版本预览，不冒充最终截止版）。属于代理机器检查，不是主人醒后签收。
- 项目保护：工具/面板/冻结SPEC/旧材料与8份评测JSON共**15/15 SHA256不变**（对照前一文档回执的保护表）。只新增监测代码/测试/证据、一个用户LaunchAgent并更新ISA/STATUS。

## 当前未满足的部分

- **远端未观测**：SSH socket不在，探针返回REMOTE_UNOBSERVED/NO_REUSABLE_CHANNEL；0次远端SSH命令，未用口令。没有独立的Zcode私有会话观察通道。本机共享产物不能替代“在sparker云端做了什么”的直接证据。
- 第二后台样本发现ISA/STATUS两处变化；这是本助手本轮更新监测台账产生，不是Zcode新增远端动作。程序统一标“作者未知”，不会自动归因。
- 新文件若不在固定白名单则不可见；不扫描所有/tmp、用户目录、凭据或历史。自动检查为固定规则，不是全天候人工代码审查。代码/报告不会自动判所有缺陷已修、不会替代FE/PC主人入口验收。
- 本机睡眠/关机会停止采样；超过10分钟的间隔计入gap_count；报告始终注明最后实际采样时间。无保活阻止休眠、不自动续期、不唤醒主人或外发PDF。

## 完成态

**本机监测与PDF更新已验证启动；总体PARTIAL**，因缺远端观测及醒后整体汇报。机械闸门复跑 `bun .../closeloop-verify.ts claim.json` → **valid=true / stage=PARTIAL / exit 1**；SOURCE/BUILD通过，整体RUNTIME未满足，OWNER_ENTRYPOINT缺证。实际输出 `gate-output.json`。不把PDF存在或进程运行等同完整主人结果，也不为交付而缩成INTERNAL。

**第1轮claim修复**：最初把“本机心跳通过”与“整体远端运行未满足”同时写在同一RUNTIME:OUTCOME层，闸门拒绝为contradictory evidence（valid=false）。已保留 `claim-before-scope-repair.json` 与 `gate-before-scope-repair.json`，把整体运行层明确记为未满足；本机心跳仍保留在events和本回执，不删除失败证据、不把局部成功替代完整目标。修正后得到上述有效PARTIAL判定。
