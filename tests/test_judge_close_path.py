#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""The close path dispatches a judge and honours only a lowered verdict
(FEAT-2026-0100/T02).

Every case here drives the real `loop.run` against a temp git repo with
`dispatch`, `verify`, and `run_judge_session` patched — the same shape
`tests/test_terminal_flips.py` uses. The judge is a session, so the only
honest way to test what it changes is to let the driver run its close path
end to end and read the surfaces afterwards: the close WU's on-disk
`verdict:`, `FOLLOW-UPS.md`, the gate file, the roadmap row, and the `judged`
event.

The one thing the judge must not see is the close's own opinion of its work,
so `test_judge_prompt_excludes_close_prose` asserts on the prompt string the
runner was handed, not on the bundle builder (which `tests/test_judge_module.py`
already covers).
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests._loop_loader import load_loop
from tests._workspace import integration_workspace

loop = load_loop()

_WU_BODY = (
    "\n\n**Context.** test\n\n**Acceptance criteria.** test\n\n"
    "**Do not touch.** test\n\n**Verification.** test\n\n"
    "**Escalation triggers.** test\n"
)

#: The sentence the close writes into its own `## Verdict` section. A judge
#: prompt containing this string is a judge reading the grade it is supposed
#: to be assigning.
_CLOSE_VERDICT_PROSE = "Every criterion of this gate demonstrably holds."

_CRITERION_ID = "T01#1"


def _retrospective_text(verdict: str) -> str:
    """A close's RETROSPECTIVE.md: measurements the judge reads, prose it must not."""
    return (
        "# Retrospective\n\n"
        "Nothing generalizes from this gate.\n\n"
        "## Measurements\n\n"
        "- suite: 12 passed, 0 failed\n"
        "- MEASUREMENT-SENTINEL-9001\n\n"
        "## Cost analysis\n\n"
        "- planned $1.00, actual $0.50\n\n"
        "## Verdict\n\n"
        f"verdict: {verdict} — {_CLOSE_VERDICT_PROSE}\n\n"
        "## Retrospective\n\n"
        "The close's own account of how well it did.\n"
    )


def _judge_output(verdict: str, findings: int = 0) -> str:
    """What a judge session prints: prose, then one fenced `result` block."""
    body = f"verdict: {verdict}\n"
    for i in range(1, findings + 1):
        body += (
            f"\n### criterion {i}\n\n"
            f"JUDGE-FINDING-{i}: the oracle does not pass on this tree.\n\n"
            f"- command: `python3 -m unittest tests.test_x`\n"
            f"- exit: 1\n"
        )
    return f"I re-ran the oracles.\n\n```result\n{body}```\n"


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    out = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def _events(feature_dir: Path, event_type: str) -> list[dict]:
    path = feature_dir / "events.jsonl"
    if not path.exists():
        return []
    out = []
    for raw in path.read_text().splitlines():
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if event.get("event_type") == event_type:
            out.append(event)
    return out


class JudgeClosePathCase(unittest.TestCase):
    """Shared fixture: one feature, one terminal gate, one close WU."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._patches: list[tuple[str, object]] = []
        self.judge_prompts: list[str] = []

    def tearDown(self):
        os.chdir(self._cwd)
        for name, original in self._patches:
            setattr(loop, name, original)

    def _patch(self, name: str, replacement) -> None:
        self._patches.append((name, getattr(loop, name)))
        setattr(loop, name, replacement)

    # -- fixture ---------------------------------------------------------- #

    def _write_feature(
        self,
        root: Path,
        feature_id: str,
        close_verdict: str,
        plan_extra: str = "",
    ) -> Path:
        fdir = root / f".specfuse/features/{feature_id}-test"
        fdir.mkdir(parents=True)
        close_id = f"{feature_id}/G1-CLOSE"

        (fdir / "PLAN.md").write_text(
            f"---\nfeature_id: {feature_id}\ntitle: Test\nslug: test\n"
            f"branch: feat/{feature_id.lower()}-test\n"
            f"roadmap_goal: test\nstatus: active\n{plan_extra}---\n\n# Plan\n\n"
            f"```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
            f"    work_units:\n      - id: {close_id}\n        file: WU-close.md\n"
            f"        depends_on: []\n```\n"
        )
        (fdir / "GATE-01.md").write_text(
            "---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n\n"
            "## Definition of done\n\n"
            "- DEFINITION-OF-DONE-SENTINEL-4242 holds on this tree.\n"
        )
        (fdir / "GATE-01-CRITERIA.md").write_text(
            f"# Criteria\n\n### {_CRITERION_ID}\n\n"
            "- **criterion:** CRITERION-SENTINEL-7777 passes\n"
            "- **oracle:** `python3 -m unittest tests.test_x`\n"
            "- **kind:** `command`\n"
            "- **state:** `unverified`\n"
        )
        (fdir / "WU-close.md").write_text(
            f"---\nid: {close_id}\ntype: close\nmodel: opus\n"
            f"status: pending\nattempts: 0\nverdict: {close_verdict}\n---\n\n"
            f"# Close{_WU_BODY}"
        )

        specfuse = root / ".specfuse"
        (specfuse / "roadmap.md").write_text(
            f"---\nproject: test\n---\n\n# Roadmap\n\n"
            f"| Feature ID | Title | Status | Folder | Detail |\n"
            f"|------------|-------|--------|--------|--------|\n"
            f"| {feature_id} | Test | active | — | — |\n\n"
            f"## {feature_id} — Test\n\nContent.\n"
        )
        (specfuse / "roadmap-archive.md").write_text(
            "---\nproject: test\n---\n\n# Archived\n\n"
            "<!-- Archived sections appended below -->\n"
        )
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m",
                        "scaffold"], check=True)
        return fdir

    def _install_stubs(self, fdir: Path, close_verdict: str, judge_runner) -> None:
        """Patch dispatch / verify / run_judge_session for one close run."""

        def fake_dispatch(wu, failure_note, cost_tracking=True):
            (fdir / "RETROSPECTIVE.md").write_text(
                _retrospective_text(close_verdict))
            if close_verdict == "not_met":
                (fdir / "FOLLOW-UPS.md").write_text(
                    "# Follow-ups\n\n### the close's own follow-up\n\n"
                    "**Evidence.** stub — n/a\n\n**Re-run when.** stub\n")
            return ("", {"input_tokens": 10, "output_tokens": 5,
                         "cost_usd": 0.001})

        self._patch("dispatch", fake_dispatch)
        self._patch("verify", lambda wu, feature_dir, cfg=None: (True, "(stub pass)"))
        self._patch("run_judge_session", judge_runner)

    def _recording_runner(self, output: str):
        def runner(prompt, *, timeout=None):
            self.judge_prompts.append(prompt)
            return output, None
        return runner

    def _run(self) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            loop.run(None, dry_run=False)
        return buf.getvalue()


class TestJudgeLowersVerdict(JudgeClosePathCase):

    def test_judge_lowers_met_to_not_met_and_writes_followups(self):
        """Close says met, judge says not_met with two findings: the judge wins.

        Everything a `not_met` close would have produced must be true
        afterwards — the on-disk verdict, FOLLOW-UPS.md in the judge's words,
        an un-flipped gate and roadmap row — plus a `judged` event carrying
        both verdicts so the disagreement is auditable.
        """
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9801"
            fdir = self._write_feature(root, feature_id, close_verdict="met")
            self._install_stubs(
                fdir, "met",
                self._recording_runner(_judge_output("not_met", findings=2)),
            )

            self._run()

            wu_fm = _read_frontmatter(fdir / "WU-close.md")
            self.assertEqual(
                wu_fm.get("verdict"), "not_met",
                "the judge's lowered verdict must be written to the close WU",
            )

            followups = fdir / "FOLLOW-UPS.md"
            self.assertTrue(followups.exists(),
                            "a lowered verdict must file FOLLOW-UPS.md")
            entries = loop.parse_followup_entries(followups.read_text())
            self.assertEqual(len(entries), 2,
                             f"expected 2 judge findings, got {entries!r}")
            self.assertIn("JUDGE-FINDING-1", followups.read_text())
            self.assertIn("JUDGE-FINDING-2", followups.read_text())

            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review",
                             "a lowered verdict must not flip the gate to passed")
            roadmap = (root / ".specfuse/roadmap.md").read_text()
            self.assertIn(f"| {feature_id} | Test | active |", roadmap,
                          "a lowered verdict must leave the roadmap row active")

            judged = _events(fdir, "judged")
            self.assertEqual(len(judged), 1, "exactly one judged event")
            payload = judged[0]["payload"]
            self.assertEqual(payload.get("close_verdict"), "met")
            self.assertEqual(payload.get("judge_verdict"), "not_met")
            self.assertEqual(payload.get("verdict"), "not_met")
            self.assertTrue(payload.get("lowered"))


class TestJudgeCannotRaise(JudgeClosePathCase):

    def test_judge_cannot_raise_not_met(self):
        """Close says not_met, judge says met: the verdict stays not_met."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9802"
            fdir = self._write_feature(root, feature_id, close_verdict="not_met")
            self._install_stubs(
                fdir, "not_met", self._recording_runner(_judge_output("met")),
            )

            self._run()

            wu_fm = _read_frontmatter(fdir / "WU-close.md")
            self.assertEqual(wu_fm.get("verdict"), "not_met",
                             "a judge may lower a verdict, never raise one")
            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "awaiting_review")

            judged = _events(fdir, "judged")
            self.assertEqual(len(judged), 1)
            payload = judged[0]["payload"]
            self.assertEqual(payload.get("close_verdict"), "not_met")
            self.assertEqual(payload.get("judge_verdict"), "met")
            self.assertEqual(payload.get("verdict"), "not_met")
            self.assertFalse(payload.get("lowered"))
            self.assertTrue(payload.get("disagreed"),
                            "the event must record that the two disagreed")


class TestJudgeAgrees(JudgeClosePathCase):

    def test_judge_agreeing_met_lets_flips_fire(self):
        """Both say met: the terminal flips fire exactly as before the judge."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9803"
            fdir = self._write_feature(root, feature_id, close_verdict="met")
            self._install_stubs(
                fdir, "met", self._recording_runner(_judge_output("met")),
            )

            self._run()

            wu_fm = _read_frontmatter(fdir / "WU-close.md")
            self.assertEqual(wu_fm.get("verdict"), "met")
            plan_fm = _read_frontmatter(fdir / "PLAN.md")
            self.assertEqual(plan_fm.get("status"), "done",
                             "an agreed met verdict must flip PLAN.md to done")
            gate_fm = _read_frontmatter(fdir / "GATE-01.md")
            self.assertEqual(gate_fm.get("status"), "passed",
                             "an agreed met verdict must flip the gate to passed")

            judged = _events(fdir, "judged")
            self.assertEqual(len(judged), 1)
            self.assertEqual(judged[0]["payload"].get("judge_verdict"), "met")
            self.assertFalse(judged[0]["payload"].get("disagreed"))


class TestJudgeUnusable(JudgeClosePathCase):
    """#3620: on a terminal gate, a judge that gives no verdict (timeout,
    cannot run, unreadable output, or a defect in its path) must not let the
    close's own `met` fire the terminal flips. The close's verdict is kept as
    written, the flips are withheld and the run halts for a human."""

    def _assert_flips_withheld(self, fdir: Path, output: str) -> dict:
        wu_fm = _read_frontmatter(fdir / "WU-close.md")
        self.assertEqual(wu_fm.get("verdict"), "met",
                         "an unusable judge must leave the close's verdict alone")
        plan_fm = _read_frontmatter(fdir / "PLAN.md")
        self.assertEqual(plan_fm.get("status"), "active",
                         "an unjudged met must not flip PLAN.md to done")
        gate_fm = _read_frontmatter(fdir / "GATE-01.md")
        self.assertNotEqual(gate_fm.get("status"), "passed",
                            "an unjudged met must not pass the terminal gate")
        judged = _events(fdir, "judged")
        self.assertEqual(len(judged), 1)
        payload = judged[0]["payload"]
        self.assertIsNone(payload.get("judge_verdict"))
        self.assertTrue(payload.get("unjudged"))
        self.assertTrue((payload.get("reason") or "").strip(),
                        "a null judge verdict must carry a reason")
        halts = [e for e in _events(fdir, "human_escalation")
                 if e["payload"].get("reason") == "judge_unavailable_terminal"]
        self.assertEqual(len(halts), 1, output)
        self.assertIn(payload["reason"], halts[0]["payload"].get("judge_reason", ""))
        self.assertIn("judge_unavailable_terminal", output)
        return payload

    def test_judge_timeout_withholds_the_flips(self):
        def timing_out(prompt, *, timeout=None):
            raise subprocess.TimeoutExpired(cmd=["claude"], timeout=timeout or 1)

        with integration_workspace() as root:
            os.chdir(root)
            fdir = self._write_feature(root, "FEAT-2026-9804", close_verdict="met")
            self._install_stubs(fdir, "met", timing_out)
            payload = self._assert_flips_withheld(fdir, self._run())
            self.assertIn("timed out", payload["reason"])

    def test_unreadable_judge_withholds_the_flips(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = self._write_feature(root, "FEAT-2026-9805", close_verdict="met")
            self._install_stubs(
                fdir, "met",
                self._recording_runner("I could not decide. Sorry.\n"))
            self._assert_flips_withheld(fdir, self._run())

    def test_judge_that_cannot_run_withholds_the_flips(self):
        def missing(prompt, *, timeout=None):
            raise FileNotFoundError("claude")

        with integration_workspace() as root:
            os.chdir(root)
            fdir = self._write_feature(root, "FEAT-2026-9806", close_verdict="met")
            self._install_stubs(fdir, "met", missing)
            self._assert_flips_withheld(fdir, self._run())

    def test_judge_path_defect_withholds_the_flips(self):
        def broken(prompt, *, timeout=None):
            raise RuntimeError("judge path defect")

        with integration_workspace() as root:
            os.chdir(root)
            fdir = self._write_feature(root, "FEAT-2026-9807", close_verdict="met")
            self._install_stubs(fdir, "met", broken)
            payload = self._assert_flips_withheld(fdir, self._run())
            self.assertIn("RuntimeError", payload["reason"])

    def test_not_met_close_with_a_timed_out_judge_does_not_halt(self):
        """Nothing to withhold: a not_met close fires no flips anyway."""
        def timing_out(prompt, *, timeout=None):
            raise subprocess.TimeoutExpired(cmd=["claude"], timeout=timeout or 1)

        with integration_workspace() as root:
            os.chdir(root)
            fdir = self._write_feature(root, "FEAT-2026-9808",
                                       close_verdict="not_met")
            self._install_stubs(fdir, "not_met", timing_out)
            self._run()
            self.assertEqual(
                _read_frontmatter(fdir / "WU-close.md").get("verdict"), "not_met")
            self.assertEqual(
                [e for e in _events(fdir, "human_escalation")
                 if e["payload"].get("reason") == "judge_unavailable_terminal"],
                [])


class TestJudgeDisabled(JudgeClosePathCase):

    def test_judge_disabled_skips_dispatch(self):
        """`judge_disabled: true` in PLAN frontmatter is the escape hatch."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9806"
            fdir = self._write_feature(
                root, feature_id, close_verdict="met",
                plan_extra="judge_disabled: true\n",
            )
            called: list[str] = []

            def never_called(prompt, *, timeout=None):
                called.append(prompt)
                return _judge_output("not_met", findings=2), None

            self._install_stubs(fdir, "met", never_called)
            out = self._run()

            self.assertEqual(called, [],
                             "judge_disabled: true must not dispatch a judge")
            self.assertIn("judge_disabled", out,
                          "the skip must print a notice naming the escape hatch")
            wu_fm = _read_frontmatter(fdir / "WU-close.md")
            self.assertEqual(wu_fm.get("verdict"), "met",
                             "a skipped judge leaves the close's verdict standing")


class TestJudgePromptEvidence(JudgeClosePathCase):

    def test_judge_prompt_excludes_close_prose(self):
        """The prompt carries the evidence and not the close's own grade."""
        with integration_workspace() as root:
            os.chdir(root)
            feature_id = "FEAT-2026-9807"
            fdir = self._write_feature(root, feature_id, close_verdict="met")
            self._install_stubs(
                fdir, "met", self._recording_runner(_judge_output("met")),
            )

            self._run()

            self.assertEqual(len(self.judge_prompts), 1,
                             "the judge is dispatched exactly once")
            prompt = self.judge_prompts[0]

            # Evidence the judge must have.
            self.assertIn("DEFINITION-OF-DONE-SENTINEL-4242", prompt)
            self.assertIn(_CRITERION_ID, prompt)
            self.assertIn("CRITERION-SENTINEL-7777", prompt)
            self.assertIn("diff --git", prompt)
            self.assertIn("MEASUREMENT-SENTINEL-9001", prompt)

            # The retrospective is IN the gate's diff — which is what makes
            # the two exclusions below load-bearing rather than vacuous: the
            # close's `## Verdict` prose arrives inside a diff hunk and has to
            # be stripped there, not merely left out of the measurements slice.
            self.assertIn("RETROSPECTIVE.md", prompt)

            # The close's own opinion of its work, which it must not have.
            self.assertNotIn(_CLOSE_VERDICT_PROSE, prompt)
            self.assertNotIn("## Verdict", prompt)


class TestJudgeDispatchArgv(unittest.TestCase):
    """The judge is invoked through the same builder `dispatch` uses."""

    def test_build_judge_cmd_carries_model_effort_and_json(self):
        cmd = loop.build_judge_cmd()
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertIn(loop.JUDGE_MODEL, cmd)
        self.assertIn(loop.JUDGE_EFFORT, cmd)
        self.assertEqual(cmd[-2:], ["--output-format", "json"])
        self.assertNotIn("{model}", " ".join(cmd))
        self.assertNotIn("{effort}", " ".join(cmd))

    def test_timeout_is_thirty_minutes(self):
        # #3620: real judges re-running a gate's oracles took 20-26 minutes.
        self.assertEqual(loop.JUDGE_TIMEOUT_SECONDS, 30 * 60)


class TestJudgeDisabledFlagReading(unittest.TestCase):

    def test_bool_and_string_true_both_disable(self):
        self.assertTrue(loop._judge_disabled({"judge_disabled": True}))
        self.assertTrue(loop._judge_disabled({"judge_disabled": "true"}))
        self.assertTrue(loop._judge_disabled({"judge_disabled": " True "}))

    def test_absent_false_and_other_values_do_not(self):
        self.assertFalse(loop._judge_disabled({}))
        self.assertFalse(loop._judge_disabled({"judge_disabled": False}))
        self.assertFalse(loop._judge_disabled({"judge_disabled": "no"}))


class TestGateStartSha(unittest.TestCase):
    """Where the judge's diff range starts, and what it refuses to guess."""

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_gate_baseline_entry_sha_wins(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = root / ".specfuse/features/FEAT-2026-9810-test"
            fdir.mkdir(parents=True)
            gate = fdir / "GATE-01.md"
            gate.write_text(
                "---\ngate: 1\nstatus: open\nbaseline:\n"
                "  sha: 0123456789abcdef0123456789abcdef01234567\n"
                "  probed_at: 2026-09-05T00:00:00+00:00\n"
                "  entry_sha: 0123456789abcdef0123456789abcdef01234567\n"
                "  failing: []\n---\n\n# Gate 1\n"
            )
            sha, source = loop.resolve_gate_start_sha(gate, fdir)
            self.assertEqual(sha, "0123456789abcdef0123456789abcdef01234567")
            self.assertIn("baseline.entry_sha", source)

    def test_merge_base_fallback_when_no_baseline_block(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = root / ".specfuse/features/FEAT-2026-9811-test"
            fdir.mkdir(parents=True)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9811\ntitle: T\nslug: t\n"
                "branch: feat/t\nroadmap_goal: t\nstatus: active\nbase: main\n"
                "---\n\n# Plan\n"
            )
            gate = fdir / "GATE-01.md"
            gate.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")
            expected = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "main"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()

            sha, source = loop.resolve_gate_start_sha(gate, fdir)
            self.assertEqual(sha, expected)
            self.assertIn("merge-base", source)

    def test_no_baseline_and_no_resolvable_base_returns_a_reason(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = root / ".specfuse/features/FEAT-2026-9812-test"
            fdir.mkdir(parents=True)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9812\ntitle: T\nslug: t\n"
                "branch: feat/t\nroadmap_goal: t\nstatus: active\n"
                "base: no-such-ref\n---\n\n# Plan\n"
            )
            gate = fdir / "GATE-01.md"
            gate.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

            sha, reason = loop.resolve_gate_start_sha(gate, fdir)
            self.assertIsNone(sha)
            self.assertIn("baseline.sha", reason)
            self.assertIn("merge-base", reason)

    def test_judge_diff_base_survives_a_reprobe(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = root / ".specfuse/features/FEAT-2026-9813-test"
            fdir.mkdir(parents=True)
            gate = fdir / "GATE-01.md"
            gate.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

            loop.write_gate_baseline(
                gate, "1111111111111111111111111111111111111aaa",
                "2026-09-05T00:00:00+00:00", [],
            )
            loop.write_gate_baseline(
                gate, "2222222222222222222222222222222222222bbb",
                "2026-09-05T01:00:00+00:00", [],
            )

            sha, source = loop.resolve_gate_start_sha(gate, fdir)
            self.assertEqual(sha, "1111111111111111111111111111111111111aaa")
            self.assertIn("baseline.entry_sha", source)

    def test_entry_sha_is_written_once(self):
        with integration_workspace() as root:
            fdir = root / ".specfuse/features/FEAT-2026-9814-test"
            fdir.mkdir(parents=True)
            gate = fdir / "GATE-01.md"
            gate.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

            loop.write_gate_baseline(
                gate, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1",
                "2026-09-05T00:00:00+00:00", [],
            )
            first = loop.read_gate_baseline(gate)
            loop.write_gate_baseline(
                gate, "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb2",
                "2026-09-05T01:00:00+00:00", [],
            )
            second = loop.read_gate_baseline(gate)

            self.assertEqual(first["entry_sha"], second["entry_sha"])
            self.assertEqual(second["sha"], "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb2")
            self.assertNotEqual(second["sha"], second["entry_sha"])

    def test_legacy_baseline_without_entry_sha_falls_back_to_merge_base(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = root / ".specfuse/features/FEAT-2026-9815-test"
            fdir.mkdir(parents=True)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9815\ntitle: T\nslug: t\n"
                "branch: feat/t\nroadmap_goal: t\nstatus: active\nbase: main\n"
                "---\n\n# Plan\n"
            )
            gate = fdir / "GATE-01.md"
            gate.write_text(
                "---\ngate: 1\nstatus: open\nbaseline:\n"
                "  sha: 0123456789abcdef0123456789abcdef01234567\n"
                "  probed_at: 2026-09-05T00:00:00+00:00\n"
                "  failing: []\n---\n\n# Gate 1\n"
            )
            expected = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "main"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()

            sha, source = loop.resolve_gate_start_sha(gate, fdir)
            self.assertEqual(sha, expected)
            self.assertIn("merge-base", source)

    def test_legacy_gate_reprobe_seeds_entry_sha_from_merge_base(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = root / ".specfuse/features/FEAT-2026-9816-test"
            fdir.mkdir(parents=True)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9816\ntitle: T\nslug: t\n"
                "branch: feat/t\nroadmap_goal: t\nstatus: active\nbase: main\n"
                "---\n\n# Plan\n"
            )
            gate = fdir / "GATE-01.md"
            gate.write_text(
                "---\ngate: 1\nstatus: open\nbaseline:\n"
                "  sha: 0123456789abcdef0123456789abcdef01234567\n"
                "  probed_at: 2026-09-05T00:00:00+00:00\n"
                "  failing: []\n---\n\n# Gate 1\n"
            )
            expected_merge_base = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "main"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()

            loop.write_gate_baseline(
                gate, "2222222222222222222222222222222222222bbb",
                "2026-09-05T02:00:00+00:00", [], fdir,
            )

            baseline = loop.read_gate_baseline(gate)
            self.assertEqual(baseline["entry_sha"], expected_merge_base)
            self.assertNotEqual(
                baseline["entry_sha"], "2222222222222222222222222222222222222bbb",
            )

    def test_fresh_gate_first_probe_seeds_entry_sha_from_probe(self):
        with integration_workspace() as root:
            os.chdir(root)
            fdir = root / ".specfuse/features/FEAT-2026-9817-test"
            fdir.mkdir(parents=True)
            (fdir / "PLAN.md").write_text(
                "---\nfeature_id: FEAT-2026-9817\ntitle: T\nslug: t\n"
                "branch: feat/t\nroadmap_goal: t\nstatus: active\nbase: main\n"
                "---\n\n# Plan\n"
            )
            gate = fdir / "GATE-01.md"
            gate.write_text("---\ngate: 1\nstatus: open\n---\n\n# Gate 1\n")

            loop.write_gate_baseline(
                gate, "3333333333333333333333333333333333333ccc",
                "2026-09-05T03:00:00+00:00", [], fdir,
            )

            baseline = loop.read_gate_baseline(gate)
            self.assertEqual(
                baseline["entry_sha"], "3333333333333333333333333333333333333ccc",
            )


class TestCaptureGateDiff(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def test_stat_survives_in_full_when_the_body_is_capped(self):
        with integration_workspace() as root:
            os.chdir(root)
            start = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            big = root / "big.txt"
            big.write_text("".join(f"line {i} padding padding padding\n"
                                   for i in range(2000)))
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "big"],
                           check=True)

            diff = loop.capture_gate_diff(start)

            stat, _, body = diff.partition("diff --git")
            self.assertIn("big.txt", stat,
                          "the --stat block leads the capture")
            self.assertNotIn("elided", stat,
                             "the --stat block is never truncated")
            self.assertIn("elided", body, "an oversized body is truncated")
            self.assertLessEqual(len(diff), loop.JUDGE_MAX_EVIDENCE_CHARS,
                                 "the whole capture stays inside the bundle's cap")

    def test_capture_never_exceeds_its_cap_at_any_budget(self):
        """The elision marker must not push the capture past `max_chars`.

        PR #3257's CI run: 8,028 chars against the 8,000 cap. Whether the
        overshoot shows depends on where diff-line boundaries fall against
        the budget, which differs between git versions, so sweep budgets
        rather than trust one environment's boundary.
        """
        with integration_workspace() as root:
            os.chdir(root)
            start = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            big = root / "big.txt"
            big.write_text("".join(f"line {i} padding padding padding\n"
                                   for i in range(2000)))
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "big"],
                           check=True)

            stat_len = len(subprocess.run(
                ["git", "-C", str(root), "diff", "--stat", f"{start}..HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip())

            overshoots = []
            for cap in range(stat_len + 60, stat_len + 1200, 7):
                diff = loop.capture_gate_diff(start, max_chars=cap)
                if len(diff) > cap:
                    overshoots.append((cap, len(diff)))
                self.assertIn("elided", diff, f"cap {cap} did not truncate")
            self.assertEqual(overshoots, [],
                             "every capture stays inside the cap it was given")

            # A cap smaller than the stat itself: the stat takes the cap.
            for cap in (stat_len // 2, stat_len - 1, stat_len + 1):
                diff = loop.capture_gate_diff(start, max_chars=cap)
                self.assertLessEqual(len(diff), cap, f"cap {cap} overshot")
                self.assertNotIn("diff --git", diff,
                                 "no body when the stat consumes the cap")


class TestWriteJudgeFollowups(unittest.TestCase):

    def setUp(self):
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)

    def _findings(self, n: int):
        from specfuse.loop.judge import JudgeFinding
        return [
            JudgeFinding(criterion=f"c{i}",
                         text=f"### c{i}\n\nJUDGE-WORDS-{i}\n")
            for i in range(1, n + 1)
        ]

    def test_creates_the_file_with_one_entry_per_finding(self):
        with integration_workspace() as root:
            fdir = root / ".specfuse/features/FEAT-2026-9813-test"
            fdir.mkdir(parents=True)
            path = loop.write_judge_followups(fdir, 1, self._findings(3))
            entries = loop.parse_followup_entries(path.read_text())
            self.assertEqual(len(entries), 3)
            self.assertIn("JUDGE-WORDS-2", path.read_text())

    def test_appends_rather_than_overwriting_the_close_s_own_entries(self):
        with integration_workspace() as root:
            fdir = root / ".specfuse/features/FEAT-2026-9814-test"
            fdir.mkdir(parents=True)
            (fdir / "FOLLOW-UPS.md").write_text(
                "# Follow-ups\n\n### the close's own\n\nCLOSE-WORDS\n")
            path = loop.write_judge_followups(fdir, 1, self._findings(1))
            text = path.read_text()
            self.assertIn("CLOSE-WORDS", text,
                          "a lowered verdict adds reasons, it does not retract")
            self.assertEqual(len(loop.parse_followup_entries(text)), 2)

    def test_a_not_met_with_no_findings_still_leaves_one_entry(self):
        """`not_met` obliges FOLLOW-UPS.md to hold an entry (close-m)."""
        with integration_workspace() as root:
            fdir = root / ".specfuse/features/FEAT-2026-9815-test"
            fdir.mkdir(parents=True)
            path = loop.write_judge_followups(fdir, 1, [])
            entries = loop.parse_followup_entries(path.read_text())
            self.assertEqual(len(entries), 1)
            self.assertIn("without recording a finding", path.read_text())


if __name__ == "__main__":
    unittest.main()
