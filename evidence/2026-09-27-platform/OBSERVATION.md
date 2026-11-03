# DGX Spark 平台适配 · 只读证据核查（2026-09-27 00:32 CST）

## 目标与判据

目标是为评审的「DGX Spark 平台适配 15%」建立可复核证据；不能用硬件型号、`skills list ready` 或 StepFun 云端成功推断本地 GPU 推理优势。必要证据：机器身份与 NVIDIA 驱动；本地开源模型在同机真实跑；**若要主张 GPU 加速/大模型装载优势，还需推理窗口内的 GPU/统一内存遥测、模型后端归属与可复现任务输出**。

## 本轮实际只读观察

在 owner 已登录且空闲的 DGX Terminal 执行 `uname -m`、`nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,power.draw --format=csv,noheader,nounits`，真实回显：

```
aarch64
NVIDIA GB10, 580.173.02, [N/A], [N/A], 0, 3.97
NVIDIA_RC=0
```

这是**空闲时快照**：GPU utilization=0，`nvidia-smi` 对此机内存字段返回 N/A；不能读成「推理没用 GPU」，更不能读成「已证明 120B GPU 加速」。`ollama ps` 在本轮快照中没有驻留模型行；未启动新的推理、服务或配置更改。

现存 `evidence/2026-09-26-iris-preflight/ab-comparison/` 六份 DGX Gateway 同题 A/B 原始 JSON：StepFun 3/3、Ollama Nemotron 本地 1/3（两个正例失败、一个负例成功；Nemotron 69.2s / 171.1s / 44.3s）。它证实**在 DGX 上有实际本地模型回合与云模型回合**，不含同回合 GPU 占用、显存/统一内存、tokens/s 或实际 offload 的独立遥测；三题样本也不足以估计稳定性能。Streamlit :8501 HTTP 200 是独立只读业务面板，不是 NVIDIA GPU 优势证据。

## 待证与停止线

- **UNPROVEN**：120B 运行时具体 GPU offload、统一内存占用、吞吐/能效；是否使用 NVIDIA SDK/NIM/TensorRT-LLM（项目当前无已核证部署），默认聊天模型仍为 Ollama 且正例未通过。StepFun 在 DGX Gateway 调用成功属于平台集成，不等于 StepFun 在 DGX 本地算。
- 下一最小反证：在不改配置、不重启、不抢现有会话的隔离时段，用**单次固定输入**同步采 `nvidia-smi` / 可用硬件遥测与 Ollama 后端执行回执，记录峰值/基线/进程归属/输出和服务健康。若无法保证低影响或无独占时段，**不发这次推理**，维持平台优势“部分有证、加速未证”。不做提示词试错、Iris 安装或新 agent 串接。
- 该目录在 gitignore 的 `evidence/` 下；将来给评委前须脱敏拣选证据，经 owner 审核发布，不能假定私仓读者已拥有它。
