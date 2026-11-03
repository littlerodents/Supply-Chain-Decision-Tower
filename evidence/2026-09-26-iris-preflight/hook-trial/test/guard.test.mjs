import test from 'node:test';
import assert from 'node:assert/strict';
import { rewriteSkillRead } from '../guard.mjs';

const wrong = '/home/parker/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md';
const right = '/home/sparker/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md';
const ctx = { sessionId: 'pi-dgx-hooktest-pos1' };
const exists = () => true;

function call(toolName = 'read', path = wrong) {
  return { toolName, params: { path, offset: 2 } };
}

test('rewrites only the exact observed bad read for a test session', () => {
  const event = call();
  assert.deepEqual(rewriteSkillRead(event, ctx, '/home/sparker', exists), {
    params: { path: right, offset: 2 },
  });
  assert.equal(event.params.path, wrong);
});

test('does not touch already correct or adjacent paths', () => {
  assert.equal(rewriteSkillRead(call('read', right), ctx, '/home/sparker', exists), undefined);
  assert.equal(rewriteSkillRead(call('read', wrong.replace('SKILL.md', 'scripts/tools.py')), ctx, '/home/sparker', exists), undefined);
  assert.equal(rewriteSkillRead(call('read', wrong + '/../SKILL.md'), ctx, '/home/sparker', exists), undefined);
});

test('does not touch any other tool or session', () => {
  assert.equal(rewriteSkillRead(call('exec'), ctx, '/home/sparker', exists), undefined);
  assert.equal(rewriteSkillRead(call(), { sessionId: 'pi-dgx-other' }, '/home/sparker', exists), undefined);
  assert.equal(rewriteSkillRead(call(), {}, '/home/sparker', exists), undefined);
});

test('fails closed without target file or HOME', () => {
  assert.equal(rewriteSkillRead(call(), ctx, '', exists), undefined);
  assert.equal(rewriteSkillRead(call(), ctx, '/home/sparker', () => false), undefined);
  assert.equal(rewriteSkillRead({ toolName: 'read', params: null }, ctx, '/home/sparker', exists), undefined);
});

test('exact-match boundary: near misses and other skills stay untouched', () => {
  assert.equal(rewriteSkillRead(call('read', wrong + 'x'), ctx, '/home/sparker', exists), undefined);
  assert.equal(rewriteSkillRead(call('read', wrong.replace('supply-chain-control-tower', 'other-skill')), ctx, '/home/sparker', exists), undefined);
  assert.equal(rewriteSkillRead(call('read', wrong.replace('SKILL.md', 'scripts/tools.py')), ctx, '/home/sparker', exists), undefined);
});

test('session gate is prefix-exact and case-sensitive', () => {
  assert.equal(rewriteSkillRead(call(), undefined, '/home/sparker', exists), undefined);
  assert.equal(rewriteSkillRead(call(), { sessionId: 'PI-DGX-HOOKTEST-pos1' }, '/home/sparker', exists), undefined);
  assert.equal(rewriteSkillRead(call(), { sessionId: 'x-pi-dgx-hooktest-pos1' }, '/home/sparker', exists), undefined);
});

test('rewrites a minimal event carrying no extra params', () => {
  assert.deepEqual(
    rewriteSkillRead({ toolName: 'read', params: { path: wrong } }, ctx, '/home/sparker', exists),
    { params: { path: right } },
  );
});
