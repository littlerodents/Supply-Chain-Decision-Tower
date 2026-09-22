# issue-template.md · agent 消费格式

issue body 的渲染形状（`repro_pack.py:render_repro` 是代码级真源，本文件是文档真源，两者必须同步改）：

```markdown
# Repro · <type> / <severity>

- 位置：<location>
- 错误原文：`<error_text>`
- 出错时间戳：<timestamps>

## 复现步骤
1. <step>
2. <step>

> 由 repro-pack 从操作录屏自动装配。置信度 <confidence>。
---
bugcard: <包目录>/bugcard.json
```

要求：标题 `[repro-pack] <type>: <location 前 60 字>`；不携带录屏中出现的个人数据。
