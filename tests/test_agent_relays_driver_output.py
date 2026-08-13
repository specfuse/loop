# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A `specfuse run` invocation's output reaches the operator while it runs.

`agent/run.py:_default_runner` calls `subprocess.run(capture_output=True)`, so
the driver's per-work-unit lines were captured and discarded -- `classify_halt`
reads `returncode` and, on `HALT_DRIVER_ERROR` only, a 20-line stderr tail. An
operator watching a `specfuse-agent` run saw one line when an item started and
the next when it ended. Observed 2026-08-12: one feature item ran 3h40m while
its close work unit spun three times on a single guard, and the only way to see
that in flight was `ps` plus reading work-unit frontmatter by hand.

These tests pin the three properties that fix rests on: the output is relayed
line by line rather than at the end, `classify_halt` still receives what it
needs, and a provider that was given its own runner keeps using it.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specfuse.agent import driver_invoke
from specfuse.agent.driver_invoke import driver_log_path, teeing_runner
from specfuse.agent.providers.feature import FeatureProvider
from specfuse.agent.state import AgentSnapshot


def _echo_argv(lines, exit_code=0):
    """A child process that prints `lines` to stdout and exits `exit_code`."""
    script = "; ".join(
        ["import sys"]
        + [f"print({line!r}); sys.stdout.flush()" for line in lines]
        + [f"sys.exit({exit_code})"]
    )
    return [sys.executable, "-c", script]


def _write_feature(root: Path, feature_id: str) -> Path:
    feature_dir = root / f"{feature_id}-slug"
    feature_dir.mkdir(parents=True)
    (feature_dir / "PLAN.md").write_text(
        f"---\nfeature_id: {feature_id}\nstatus: active\n---\n\n"
        "## Task graph\n\n```yaml\ngates:\n  - gate: 1\n    file: GATE-01.md\n"
        "    work_units: []\n```\n"
    )
    (feature_dir / "GATE-01.md").write_text("---\ngate: 1\nstatus: open\n---\n")
    return feature_dir


class TestTeeingRunner(unittest.TestCase):
    def test_relays_each_line_as_it_arrives(self):
        seen = []
        runner = teeing_runner(None, reporter=seen.append)

        runner(_echo_argv(["dispatching T01", "dispatching T02"]), check=False)

        joined = "\n".join(seen)
        self.assertIn("dispatching T01", joined)
        self.assertIn("dispatching T02", joined)

    def test_writes_the_same_lines_to_the_log_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "work" / "driver-20260812T210000.log"
            runner = teeing_runner(log_path)

            runner(_echo_argv(["dispatching T01"]), check=False)

            self.assertTrue(log_path.is_file())
            self.assertIn("dispatching T01", log_path.read_text())

    def test_result_keeps_the_shape_classify_halt_reads(self):
        runner = teeing_runner(None)

        result = runner(_echo_argv(["boom"], exit_code=1), check=False)

        self.assertIsInstance(result, subprocess.CompletedProcess)
        self.assertEqual(result.returncode, 1)
        # stderr is merged into stdout, and classify_halt's driver-error branch
        # tails stderr -- so the merged text must be reachable from both.
        self.assertIn("boom", result.stdout)
        self.assertIn("boom", result.stderr)

    def test_unopenable_log_path_does_not_fail_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            # A path whose parent is a regular file cannot be mkdir'd.
            blocker = Path(tmp) / "blocker"
            blocker.write_text("not a directory")
            seen = []
            runner = teeing_runner(blocker / "work" / "d.log", reporter=seen.append)

            result = runner(_echo_argv(["still ran"]), check=False)

            self.assertEqual(result.returncode, 0)
            self.assertIn("still ran", result.stdout)
            self.assertTrue(any("log unavailable" in line for line in seen))


class TestDriverLogPath(unittest.TestCase):
    def test_lands_inside_the_feature_s_gitignored_work_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_feature(root, "FEAT-2026-0099")

            path = driver_log_path(root, "FEAT-2026-0099", stamp="20260812T210000")

            self.assertIsNotNone(path)
            self.assertEqual(path.parent.name, "work")
            self.assertEqual(path.name, "driver-20260812T210000.log")

    def test_returns_none_when_the_feature_directory_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(
                driver_log_path(Path(tmp), "FEAT-2026-0099", stamp="s")
            )


class TestFeatureProviderStreamingIsOptIn(unittest.TestCase):
    """The regression guard: an injected runner must keep being used.

    Every test in `test_agent_provider_feature.py` injects a recording runner
    whose `on_call` side effect is what drives its assertions. A provider that
    quietly built its own runner would make those stop firing.
    """

    def _snapshot(self, queue):
        return AgentSnapshot(
            queue=queue,
            triage_auto=False,
            bug_automerge=False,
            bug_lane_limits={},
            issues=(),
            issues_error=None,
            prs=(),
            prs_error=None,
            features=(),
        )

    def test_injected_runner_is_used_when_streaming_is_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_feature(root, "FEAT-A")
            calls = []

            def _runner(argv, check=False):
                calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            provider = FeatureProvider(repo="o/r", runner=_runner, features_root=root)
            items = provider.advertise(self._snapshot(("FEAT-A",)))
            provider.execute(items[0])

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0], driver_invoke.build_invocation("FEAT-A"))

    def test_streaming_provider_does_not_call_the_injected_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_feature(root, "FEAT-A")
            calls = []

            def _runner(argv, check=False):  # pragma: no cover - must not run
                calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            reported = []
            provider = FeatureProvider(
                repo="o/r",
                runner=_runner,
                features_root=root,
                stream_driver_output=True,
                reporter=reported.append,
            )
            items = provider.advertise(self._snapshot(("FEAT-A",)))
            # `specfuse` is not on PATH in the test environment; the point here
            # is only that the injected runner was bypassed for a teeing one.
            try:
                provider.execute(items[0])
            except (FileNotFoundError, OSError):
                pass

            self.assertEqual(calls, [])
            self.assertTrue(
                any("driver output" in line for line in reported),
                f"expected the log path to be reported, got {reported}",
            )


if __name__ == "__main__":
    unittest.main()
