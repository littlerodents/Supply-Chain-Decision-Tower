// Isolated tests for the shipped plugin glue. Builds a throwaway sandbox
// with a stubbed "openclaw/plugin-sdk/plugin-entry" module, copies the exact
// shipped index.ts as index.js, and drives the registered handler as a real
// child process with a controlled HOME.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const pluginDir = join(fileURLToPath(new URL('..', import.meta.url)));
const wrong = '/home/parker/.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md';
const rel = '.openclaw/workspace/skills/supply-chain-control-tower/SKILL.md';

const DRIVER = `
const mod = await import("./index.js");
const regs = [];
mod.default.register({ on: (name, handler, opts) => regs.push({ name, handler, opts }) });
const event = JSON.parse(process.argv[2] === "undefined" ? "null" : process.argv[2]);
const ctx = process.argv[3] === "undefined" ? undefined : JSON.parse(process.argv[3]);
let out;
try { out = { reg: { name: regs[0].name, opts: regs[0].opts }, result: regs[0].handler(event, ctx) ?? null }; }
catch (e) { out = { threw: String(e) }; }
console.log(JSON.stringify(out));
`;

function buildSandbox() {
  const sandbox = mkdtempSync(join(tmpdir(), 'pi-guard-'));
  cpSync(join(pluginDir, 'guard.mjs'), join(sandbox, 'guard.mjs'));
  cpSync(join(pluginDir, 'index.ts'), join(sandbox, 'index.js'));
  writeFileSync(join(sandbox, 'driver.mjs'), DRIVER);
  const pkg = join(sandbox, 'node_modules', 'openclaw');
  const sdk = join(pkg, 'plugin-sdk');
  mkdirSync(sdk, { recursive: true });
  writeFileSync(
    join(pkg, 'package.json'),
    '{"name":"openclaw","exports":{"./plugin-sdk/plugin-entry":"./plugin-sdk/plugin-entry.js"}}\n',
  );
  writeFileSync(
    join(sdk, 'plugin-entry.js'),
    'export function definePluginEntry(defn) { return defn; }\n',
  );
  const home = join(sandbox, 'home');
  mkdirSync(join(home, rel, '..'), { recursive: true });
  return { sandbox, home };
}

function runDriver(sandbox, home, event, ctx) {
  const r = spawnSync(
    process.execPath,
    [join(sandbox, 'driver.mjs'), JSON.stringify(event), ctx === undefined ? 'undefined' : JSON.stringify(ctx)],
    { env: { ...process.env, HOME: home }, encoding: 'utf8' },
  );
  assert.equal(r.status, 0, r.stderr);
  return JSON.parse(r.stdout.trim().split('\n').pop());
}

test('shipped guard.mjs matches the unit-tested canonical copy', () => {
  assert.equal(
    readFileSync(join(pluginDir, 'guard.mjs'), 'utf8'),
    readFileSync(join(pluginDir, '..', '..', 'guard.mjs'), 'utf8'),
  );
});

test('registers exactly one before_tool_call handler matching only read', () => {
  const { sandbox, home } = buildSandbox();
  try {
    const out = runDriver(sandbox, home, null, { sessionId: 'pi-dgx-hooktest-x' });
    assert.ok(!out.threw, out.threw);
    assert.equal(out.reg.name, 'before_tool_call');
    assert.deepEqual(out.reg.opts.matcher, ['read']);
  } finally {
    rmSync(sandbox, { recursive: true, force: true });
  }
});

test('handler rewrites the bad read under a prepared HOME and preserves params', () => {
  const { sandbox, home } = buildSandbox();
  try {
    writeFileSync(join(home, rel), '# SOP\n');
    const out = runDriver(sandbox, home, { toolName: 'read', params: { path: wrong, offset: 2 } }, { sessionId: 'pi-dgx-hooktest-pos1' });
    assert.deepEqual(out.result, { params: { path: join(home, rel), offset: 2 } });
  } finally {
    rmSync(sandbox, { recursive: true, force: true });
  }
});

test('handler fails open (undefined, never throws) for every negative shape', () => {
  const { sandbox, home } = buildSandbox();
  try {
    writeFileSync(join(home, rel), '# SOP\n');
    const cases = [
      [null, { sessionId: 'pi-dgx-hooktest-x' }],
      [undefined, { sessionId: 'pi-dgx-hooktest-x' }],
      [{ toolName: 'read', params: null }, { sessionId: 'pi-dgx-hooktest-x' }],
      [{ toolName: 'read', params: { path: wrong } }, undefined],
      [{ toolName: 'read', params: { path: wrong } }, { sessionId: 'pi-dgx-other' }],
      [{ toolName: 'exec', params: { path: wrong } }, { sessionId: 'pi-dgx-hooktest-x' }],
    ];
    for (const [event, ctx] of cases) {
      const out = runDriver(sandbox, home, event, ctx);
      assert.ok(!out.threw, `threw for ${JSON.stringify([event, ctx])}: ${out.threw}`);
      assert.equal(out.result, null, `expected no rewrite for ${JSON.stringify([event, ctx])}`);
    }
  } finally {
    rmSync(sandbox, { recursive: true, force: true });
  }
});

test('no rewrite when the target SKILL.md does not exist under HOME', () => {
  const { sandbox, home } = buildSandbox();
  try {
    const out = runDriver(sandbox, join(sandbox, 'home-missing'), { toolName: 'read', params: { path: wrong } }, { sessionId: 'pi-dgx-hooktest-x' });
    assert.equal(out.result, null);
  } finally {
    rmSync(sandbox, { recursive: true, force: true });
  }
});
