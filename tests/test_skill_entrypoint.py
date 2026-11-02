"""Control-tower skill examples must work from an OpenClaw agent's workspace."""

import json
import os
from pathlib import Path
import re
import subprocess

SKILL = Path(__file__).resolve().parents[1] / "skills" / "supply-chain-control-tower"


def test_openclaw_tool_example_works_outside_skill_directory(tmp_path):
    """The agent starts in its workspace, not inside the installed skill."""
    installed = tmp_path / ".openclaw" / "workspace" / "skills" / SKILL.name
    installed.parent.mkdir(parents=True)
    installed.symlink_to(SKILL, target_is_directory=True)
    text = (SKILL / "SKILL.md").read_text()
    script = re.search(r"^S=.*$", text, re.MULTILINE).group(0)
    env = dict(os.environ, HOME=str(tmp_path))
    run = subprocess.run(
        ["bash", "-c", f'{script}\npython3 "$S" shipping --source Seattle --destination "San Francisco"'],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["unit_shipping_cost_usd"] == 2.0


def test_skill_decision_example_matches_known_gold():
    """Example in the agent instructions must not teach the wrong total."""
    text = (SKILL / "SKILL.md").read_text()
    example = json.loads(re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL).group(1))
    assert example["decision"] == "REORDER"
    assert example["order_qty"] == 3268
    assert example["total_cost"] == 119282.0
