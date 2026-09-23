# STATUS · repro-pack（仪表盘）

> 台账主体是 ISA.md（决策/验证都在那）。这里只回答：现在在哪、卡在谁身上。

- **阶段**：D1 完成（机制+主脑定案）；今日 D2：O 线 T5 skill 触发工程，T 线 T2 任务集
- **进度**：ISC 3/11（1 正例产包 / 2 validate 契约 / 4 负例零误触）
- **仓库**：`github.com/littlerodents/repro-pack`（PRIVATE，已推 main）
- **更新**：2026-09-23（iteration 1）

## 卡在 owner 手里的

1. **Spark SSH 访问方式**（机主 = 第三位队友，私购机器；今晚动员会当面收）
2. **合影人数待确认**：机主是否正式参赛成员（报名表里有没有他）→ 双人还是三人（D10 挂起）
3. **NIM key**（可选，P1 弹药）：build.nvidia.com 登录 → Get API Key，页面已给 owner 打开

## 已办结

- ✅ 动员会材料：`docs/MEETING-20260923.md`（照念版 25 分钟议程 + 会开不成的三条转发文案）

- ✅ 队友 GitHub 权限：abloom25 已加为私仓协作者（write，邀请待他接受）

- ✅ API key 入 .env（owner 授权后写入，gitignore 确认）
- ✅ 主脑定案 3.7-flash（owner 拍板，D4 检验「更强假设」，反转触发器在 ISA D2）
- ✅ 队友档期确认（18:30–21:30 成立）；今晚 owner 带队开会，材料 = `docs/TEAMMATE-BRIEF.md`
- ✅ 账号归属（ISA D9）：GitHub=littlerodents，B 站=队友 33official；合影=双人合影（ISA D10），D6 前拍

## 下一步（按序）

1. 今晚：队友会 → T2 开录（gold 规范在 brief 第五节）
2. O 线今天：T5（SKILL.md 触发工程 + npx skills 本地安装验证，无阻塞）
3. SSH 一到：D3 上 Spark（OpenClaw 配方 = 训练营 notebook 照抄）

## 风险雷达

- 真实录屏复跑：ISC-1/4 证据基于合成片，T2 到位后追加验证
- key 曾在聊天明文——赛后在 StepFun 控制台轮换
