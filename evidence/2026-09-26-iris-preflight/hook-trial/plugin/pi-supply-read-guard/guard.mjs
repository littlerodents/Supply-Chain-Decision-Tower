// Rewrites the single observed bad read path (model-generated /home/parker)
// for the supply-chain-control-tower skill to the current user's real file.
// Exact-match only; any mismatch or missing prerequisite returns undefined
// (fail closed) and the original event is never mutated.
const BAD_PATH = '/home/parker/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md';
const SKILL_RELPATH = '.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md';
const SESSION_PREFIX = 'pi-dgx-hooktest-';

export { BAD_PATH, SKILL_RELPATH, SESSION_PREFIX };

export function rewriteSkillRead(event, ctx, home, exists) {
  if (!event || event.toolName !== 'read') return undefined;
  const params = event.params;
  if (!params || params.path !== BAD_PATH) return undefined;
  const sessionId = ctx && ctx.sessionId;
  if (typeof sessionId !== 'string' || !sessionId.startsWith(SESSION_PREFIX)) return undefined;
  if (typeof home !== 'string' || home === '') return undefined;
  const target = `${home}/${SKILL_RELPATH}`;
  if (typeof exists !== 'function' || !exists(target)) return undefined;
  return { params: { ...params, path: target } };
}
