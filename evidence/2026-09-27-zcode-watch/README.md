# Zcode / DGX 只读监测与醒后 PDF

> **9/27 16时更新：当前语义结论看[远端恢复与验收报告](../2026-09-27-entry-recovery/REVIEW.md)。** 主人15:25恢复认证，监测15:54已有6次远端成功。下面06时状态是历史；自动PDF的静态风险基于旧共享文件，不能继续当当前远端实现的结论。新报告已纠正“面板未接Agent/三项工具展示问题未修”，并给出部署校验器4项假PASS。自动采样仍只做元数据/固定规则，17:39停止，不因通道恢复扩大权限或续期。

## 授权与 ANCHOR（2026-09-27 06:25 CST）

owner 最新请求：继续观察 Zcode 在 sparker 上的工作、指出不符合要求之处、持续汇总 PDF，醒后整体汇报。继承原停止线 **2026-09-27 17:39 CST**；不自动续期。baseline 2.0、项目冻结与运行态/发布边界不变。

本轮地面事实：旧 `/tmp/pi-zcode-watch-20260926/` 四个文件均 ENOENT，旧 launchctl 标签查询无运行结果，SSH master socket 不存在。中断原因未知；不声称此前一直在观测。新监测是恢复，不是把旧状态冒充当前心跳。

**可观察完成态**：固定白名单共享文件每5分钟采样，记录内容哈希变化/时间；有现成 SSH master 才复用执行固定只读探针，否则显式标 REMOTE_UNOBSERVED；PDF首版可打开且含中文、来源/未知/风险，随后随心跳原子更新；17:39停止采样并封存最后报告。全过程不读凭据/私有对话/终端历史，不跑模型、不执行被监测代码、不改远端。

**必要与充分**：单测/进程存在仅证明监控机制；实际间隔心跳+PDF更新证明已启动。真正“观测DGX发生什么”还须成功的远端探针；没有通道就保持PARTIAL，不借PDF存在宣称远端已观测。变化未带作者签名，不能直接归因给Zcode；自动检查是固定规则，不是持续在线的人工语义审查。

**失败清单**：①无SSH仍宣称看到远端；②口令/原文进入日志；③符号链接越界读取；④睡眠/退出后假连续、到期不停止；⑤PDF中文不可读或损坏；⑥把旧风险自动判成已修/把本助手文档变更归因Zcode。

## 范围

- 原始来源：当前项目固定文档/面板/工具源码的哈希；已存在的StepFun/Nemotron/Qwen评测回执只提取合同检查结果和数值，不复制完整回复。所有新事件仅称“共享文件变化，作者未知”。
- 远端：只复用 `/tmp/dgx-spark-master.sock`；不创建新的认证连接、不使用给过的口令。不读取远端配置/凭据/原始日志。允许探针仅用户/架构、Gateway active/PID、面板HTTP状态、5个Skill文件哈希；它们不等于UI或业务验收。
- PDF：`ZCODE-DGX-REPORT.pdf`；可读源 `ZCODE-DGX-REPORT.md`；事件 `events.jsonl`；状态 `state.json`。全部在本目录（gitignore），不上传/发布/飞书外发。
- 运行：一个可停止的本机用户任务；5分钟间隔，后台优先级低；机器睡眠时不采样，恢复后标记缺口，17:39后不补采。
- 测试边界沿用本请求可观察接口：一次采样→状态/事件/PDF；无通道退化、只读/不泄露、限时停止。不测试或执行Zcode私有代码，不新增模型负载。

## 当前状态（06:43已核）

**RUNNING_LOCAL_ONLY / 总体PARTIAL**：本机后台PID16088，两个实际后台样本06:38:04.633→06:43:17.997相隔313.364秒；PDF已自动更新。9项回归、真实3.09秒到期停止实验、两页PDF中文与渲染图检查通过。详细证据 [VERIFY.md](VERIFY.md)。机械闸门 **valid=true / stage=PARTIAL / exit 1**：远端运行未观测、最终主人入口缺证，不得称整个任务完成。

远端当前未观测，SSH探针次数0；不会把本机机制验收冒充整个请求完成。第二样本的ISA/STATUS变化来自本助手记录监测台账，不是Zcode远端动作。醒后在当前对话按最新PDF整体汇报；系统不能感知主人何时醒来，不自动发外部消息。

## 运行入口与停止

- PDF：[ZCODE-DGX-REPORT.pdf](ZCODE-DGX-REPORT.pdf)；[Markdown](ZCODE-DGX-REPORT.md)；[状态](state.json)；[只含元数据的事件](events.jsonl)。本地文件，不公开上传。
- 自有任务：`com.evander.pi.zcode-report-watch`；安装描述在 `/Users/evander/Library/LaunchAgents/com.evander.pi.zcode-report-watch.plist`。一个低优先级进程，无模型/浏览器常驻或新增依赖。
- 只查它：`launchctl print gui/$(id -u)/com.evander.pi.zcode-report-watch`。
- 若主人要求提前停止，只停止这个任务：`launchctl bootout gui/$(id -u)/com.evander.pi.zcode-report-watch`；不要停Gateway/Ollama或其他服务。
- 17:39按代码硬截止停止采样，不自动续期；是否真实退出仍需到时回读状态。机器睡眠/重启、异常或权限变化可能造成盲区，报告的最后实际采样时间是新鲜度判断依据。
