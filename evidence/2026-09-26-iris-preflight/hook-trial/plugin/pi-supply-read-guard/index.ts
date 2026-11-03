// Trial-only OpenClaw plugin: rewrites the one observed bad SKILL.md read
// path (model-generated /home/parker) for supply-chain-control-tower, and
// only for pi-dgx-hooktest-* sessions. Deliberately plain JavaScript in a
// .ts file so the exact shipped source can be exercised by node --test via
// a byte-identical .js copy. The handler never throws: before_tool_call
// fails closed (blocks the call) on thrown errors, so any unexpected
// failure must fail open (return undefined) to leave other sessions alone.
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { rewriteSkillRead } from "./guard.mjs";

export default definePluginEntry({
  id: "pi-supply-read-guard",
  name: "PI supply-chain skill read guard",
  description:
    "Trial hook: rewrite the one observed bad SKILL.md read path, pi-dgx-hooktest-* sessions only.",
  register(api) {
    api.on(
      "before_tool_call",
      (event, ctx) => {
        try {
          return rewriteSkillRead(event, ctx, homedir(), (p) => existsSync(p));
        } catch {
          return undefined;
        }
      },
      { matcher: ["read"], priority: 50 },
    );
  },
});
