# troubleshooting.md

| 症状 | 原因 | 处置 |
|---|---|---|
| `REPRO_* 未设置` | 三值没进环境 | 只走环境变量，见 SKILL.md 前置；不入库 |
| HTTP 401/403 | key 无效 / plan 额度不含该模型 | 换 `REPRO_MODEL`（plan 含 step-5-preview）或查额度 |
| 视频形态全 4xx/超时 | 平台不支持该上传形态 | 走抽帧模式：`ffmpeg -i in.mp4 -vf "fps=0.5" f_%02d.png` 后用图片模式；spike 判据见 tools/spike_plan.md |
| `模型未返回 JSON` | 主脑输出散文 | 脚本自带一次重试；仍失败即报错（禁令：下游是 agent 不是人） |
| `gh` 失败 | 未登录 / 仓库无权限 | `gh auth status`；或 `--no-issue` 只产包 |
| 录屏 >120s | intake 上限 | 剪到 ≤90s（任务集口径） |

红线：负例误触（无 bug 却产包/开 issue）不是故障排除项，是 P0 失败——回 ISA ISC-8。
