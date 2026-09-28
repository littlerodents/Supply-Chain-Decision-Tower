# AGENTS.md · repro-pack

> ⚠️ 历史工作区约定（旧 repro-pack 方向，已被 D12 改道废弃；现行约定见 [REBUILD.md](REBUILD.md)）。文内 REPRO_\* 环境变量等属旧架构残留记录。

在本仓库工作的 agent 先读 `CONTEXT.md`（领域语言）与 `SPEC.md`（共识），台账与证据规矩见 `ISA.md`。

## Agent skills

### Issue tracker

本地 markdown：工单在 `.scratch/BOARD.md` 一张板管理（赛期 7 天，无 GitHub remote 期间）。详见 `docs/agents/issue-tracker.md`。

### Triage labels

默认五角色标签。详见 `docs/agents/triage-labels.md`。

### Domain docs

single-context：`CONTEXT.md` 在仓库根，ADR 在 `docs/adr/`。详见 `docs/agents/domain.md`。

## 硬规矩（本仓特有）

1. **三值走环境变量**：`REPRO_BASE_URL` / `REPRO_MODEL` / `REPRO_API_KEY`，任何代码/文档不得硬编码端点或密钥。
2. **密钥零提交**：`.env*` 已被 ignore；提交前跑 `grep -rnE "sk-[A-Za-z0-9]" --exclude-dir=.git .` 必须 0 命中。
3. **负例零误触**：无 bug 录屏永不产包、永不开 issue，这是 ISC-4/ISC-8 的 blocker。
4. **证据落盘**：一切验证产出到 `evidence/<日期或里程碑>/`（已 ignore，本地保留），ISC 关闭时把命令与结果回填 ISA.md。
5. **冻结纪律**：9/26 晚 v0.1.0 后只修 bug；改动先查 ISA Decisions 是否冲突。
