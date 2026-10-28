#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""block-feature renders decision links through `layout link`, never by hand."""

import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "specfuse" / "skills" / "block-feature" / "SKILL.md"
PREFIX = "python3 -m specfuse.loop.layout link"

ENTRIES_LAYOUT = """decisions:
  style: entries
  location: docs/decisions
  link: "{location}/{domain}.yaml#{id}"
"""

ADR_TARGET = "docs/adr/0007-event-schema-versioning.md"
ADR_LABEL = "ADR-0007: event-schema versioning"
FILL = {
    "<path>": ADR_TARGET,
    "<id>": "D-0007",
    "<label>": ADR_LABEL,
    "<domain>": "billing",
}


def _commands():
    text = SKILL.read_text(encoding="utf-8")
    cmds = []
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.S):
        for line in block.splitlines():
            if line.strip().startswith(PREFIX):
                cmds.append(line.strip())
    return cmds


def _run(repo, cmd):
    for key, val in FILL.items():
        cmd = cmd.replace(f'"{key}"', shlex.quote(val)).replace(key, shlex.quote(val))
    argv = shlex.split(cmd)
    argv[0] = sys.executable
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(argv, cwd=repo, capture_output=True, text=True, env=env, check=False)


class BlockFeatureLayout(unittest.TestCase):
    def test_skill_states_layout_link_command(self):
        self.assertTrue(_commands(), "no `python3 -m specfuse.loop.layout link` command in skill")

    def test_skill_reads_decisions_style(self):
        self.assertIn("layout get decisions.style", SKILL.read_text(encoding="utf-8"))

    def test_commands_run_in_no_layout_repo(self):
        text = SKILL.read_text(encoding="utf-8")
        m = re.search(r"\[ADR-0007[^\]]*\]\(\.\./docs/adr/[^)]*\)", text)
        self.assertIsNotNone(m, "skill lacks its rendered ADR example")
        with tempfile.TemporaryDirectory() as d:
            adr_outputs = []
            for cmd in _commands():
                res = _run(d, cmd)
                self.assertEqual(res.returncode, 0, f"{cmd}: {res.stderr}")
                if "<path>" in cmd:
                    adr_outputs.append(res.stdout.strip())
            self.assertTrue(adr_outputs)
            for out in adr_outputs:
                self.assertEqual(out, m.group(0))

    def test_commands_run_in_entries_repo(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".specfuse").mkdir()
            (Path(d) / ".specfuse" / "layout.yml").write_text(ENTRIES_LAYOUT)
            for cmd in _commands():
                if "<domain>" not in cmd:
                    continue  # template needs {domain}; only the --domain command applies
                res = _run(d, cmd)
                self.assertEqual(res.returncode, 0, f"{cmd}: {res.stderr}")

    def test_no_hand_built_adr_path(self):
        for line in SKILL.read_text(encoding="utf-8").splitlines():
            if "../docs/adr" in line:
                self.assertIn("[ADR-0007", line)


if __name__ == "__main__":
    unittest.main()
