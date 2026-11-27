"""Parallel gates and the gate result cache (FEAT-LOOP-2026-0253).

The gate's feature oracle. Stub gates are Python commands that append their
start and end time to a log outside the feature folder and sleep, so
concurrency is read from recorded intervals, never from total wall time.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from specfuse.loop import loop, progress

_STUB = """\
import sys, time
name, log, seconds, code = sys.argv[1:5]
def record(kind):
    with open(log, "a") as fh:
        fh.write("%s %s %r\\n" % (name, kind, time.time()))
record("start")
time.sleep(float(seconds))
record("end")
print("output of " + name)
sys.exit(int(code))
"""

# Records its process group, then hangs with a child in that group.
_HANG_STUB = """\
import os, subprocess, sys, time
open(sys.argv[1], "w").write(str(os.getpgrp()))
subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"])
time.sleep(5)
"""

# Reads the status file until it names both gates, then saves what it read.
_STATUS_STUB = """\
import json, sys, time
status_path, seen_path = sys.argv[1:3]
deadline = time.time() + 10
status = {}
while time.time() < deadline:
    try:
        with open(status_path) as fh:
            status = json.load(fh)
    except (OSError, ValueError):
        pass
    if {"reader", "other"} <= set(status.get("gates_running", [])):
        break
    time.sleep(0.02)
with open(seen_path, "w") as fh:
    json.dump(status, fh)
"""

_SLEEP = 0.6


class _StubGates(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.stub = self.tmp / "stub.py"
        self.stub.write_text(_STUB)
        self.log = self.tmp / "intervals.log"
        # Absent on purpose: no gate log is persisted, so reports hold no path.
        self.feature_dir = self.tmp / "no-feature"

    def gate(self, name, seconds=0.0, code=0, needs=None):
        command = shlex.join([
            Path(sys.executable).as_posix(), self.stub.as_posix(), name,
            self.log.as_posix(), str(seconds), str(code)])
        gate = {"name": name, "command": command}
        if needs:
            gate["needs"] = needs
        return gate

    def records(self):
        """(name, kind, time) tuples in time order."""
        if not self.log.exists():
            return []
        rows = [line.split() for line in self.log.read_text().splitlines()]
        return sorted(
            ((n, k, float(t)) for n, k, t in rows), key=lambda r: r[2])

    def interval(self, name):
        times = {k: t for n, k, t in self.records() if n == name}
        return times["start"], times["end"]

    def started(self):
        return [n for n, kind, _ in self.records() if kind == "start"]

    def overlap(self, a, b):
        (a0, a1), (b0, b1) = self.interval(a), self.interval(b)
        return a0 < b1 and b0 < a1

    def peak_running(self):
        running = peak = 0
        for _, kind, _ in self.records():
            running += 1 if kind == "start" else -1
            peak = max(peak, running)
        return peak


class TestDefaultUnchanged(_StubGates):
    def mixed_set(self):
        return [
            self.gate("good", seconds=0.2),
            self.gate("bad", seconds=0.2, code=1),
            self.gate("dependent", needs=["bad"]),
            self.gate("last", seconds=0.2),
        ]

    def expected(self, gates):
        """What the one-gate-at-a-time loop returned for `mixed_set`."""
        command = {g["name"]: g["command"] for g in gates}

        def ran(name, verdict):
            tail = loop.select_gate_report_lines(
                f"output of {name}\n", window=15,
                returncode=0 if verdict == "PASS" else 1)
            return (name, verdict == "PASS", False,
                    f"### {name}: {verdict}\n```\n$ {command[name]}\n"
                    + "\n".join(tail) + "\n```")

        return [
            ran("good", "PASS"),
            ran("bad", "FAIL"),
            ("dependent", False, True,
             "### dependent: SKIP — dependency 'bad' failed"),
            ran("last", "PASS"),
        ]

    @staticmethod
    def comparable(results):
        return [(r["name"], r["ok"], r.get("skipped", False),
                 re.sub(r"\d+\.\d+s", "", r["report"])) for r in results]

    def test_results_match_the_sequential_loop(self):
        gates = self.mixed_set()
        results = loop._run_gate_set(gates, self.feature_dir)
        self.assertEqual(self.comparable(results), self.expected(gates))

    def test_each_gate_starts_after_the_previous_one_ended_in_order(self):
        gates = loop.order_gate_set(self.mixed_set())
        loop._run_gate_set(gates, self.feature_dir)
        self.assertEqual(
            [(n, k) for n, k, _ in self.records()],
            [(n, k) for n in ("good", "bad", "last") for k in ("start", "end")])

    def test_returncodes_are_captured_for_gates_that_ran(self):
        captured = {}
        loop._run_gate_set(
            self.mixed_set(), self.feature_dir, _capture_returncodes=captured)
        self.assertEqual(captured, {"good": 0, "bad": 1, "last": 0})

    def test_max_parallel_defaults_to_one(self):
        for cfg in ({}, None, {"defaults": None}, {"defaults": {}}):
            self.assertEqual(loop.resolve_max_parallel(cfg), 1, cfg)
        for bad in (0, -2, "4", 2.0, True, None, [2]):
            cfg = {"defaults": {"max_parallel": bad}}
            self.assertEqual(loop.resolve_max_parallel(cfg), 1, bad)
        self.assertEqual(
            loop.resolve_max_parallel({"defaults": {"max_parallel": 4}}), 4)


class TestParallel(_StubGates):
    def pair(self):
        return [self.gate("a", seconds=_SLEEP), self.gate("b", seconds=_SLEEP)]

    def test_two_independent_gates_overlap_at_two(self):
        loop._run_gate_set(self.pair(), self.feature_dir, max_parallel=2)
        self.assertTrue(self.overlap("a", "b"), self.records())

    def test_two_independent_gates_do_not_overlap_at_one(self):
        loop._run_gate_set(self.pair(), self.feature_dir, max_parallel=1)
        self.assertFalse(self.overlap("a", "b"), self.records())

    def test_no_more_than_max_parallel_run_at_once(self):
        gates = [self.gate(n, seconds=_SLEEP) for n in ("a", "b", "c")]
        loop._run_gate_set(gates, self.feature_dir, max_parallel=2)
        self.assertEqual(self.peak_running(), 2, self.records())

    def test_a_gate_starts_after_the_gate_it_needs_ends(self):
        gates = [self.gate("a", seconds=_SLEEP),
                 self.gate("b", needs=["a"]),
                 self.gate("c", seconds=_SLEEP)]
        results = loop._run_gate_set(gates, self.feature_dir, max_parallel=3)
        self.assertTrue(all(r["ok"] for r in results), results)
        self.assertGreaterEqual(self.interval("b")[0], self.interval("a")[1])
        self.assertTrue(self.overlap("a", "c"), self.records())

    def test_a_failed_dependency_skips_its_dependents_unrun(self):
        gates = [self.gate("a", seconds=0.2, code=1),
                 self.gate("b", needs=["a"]),
                 self.gate("c", needs=["b"])]
        results = loop._run_gate_set(gates, self.feature_dir, max_parallel=3)
        self.assertEqual(
            [r.get("skipped", False) for r in results], [False, True, True])
        self.assertIn("SKIP — dependency 'b' failed", results[2]["report"])
        self.assertEqual(self.started(), ["a"])

    def test_every_gate_set_caller_applies_the_configured_limit(self):
        for caller in ("verify", "broad", "baseline"):
            with self.subTest(caller=caller):
                self.log.unlink(missing_ok=True)
                cfg = {"defaults": {"max_parallel": 2}, "code": self.pair()}
                if caller == "verify":
                    wu = loop.WorkUnit(
                        wu_id="FEAT-2026-9001/T01", type="implementation",
                        model="m", status="pending", attempts=0, title="t", body="",
                        depends_on=[], file=self.tmp / "WU.md")
                    loop.verify(wu, self.feature_dir, cfg=cfg)
                elif caller == "broad":
                    loop.run_gate_broad_set(self.feature_dir, cfg=cfg)
                else:
                    loop.probe_baseline(self.feature_dir, cfg=cfg)
                self.assertTrue(self.overlap("a", "b"), self.records())


class TestResultOrder(_StubGates):
    def test_a_later_gate_finishing_first_keeps_declared_order(self):
        gates = [self.gate("tests", seconds=_SLEEP * 2, code=1),
                 self.gate("lint", code=1),
                 self.gate("other")]
        results = loop._run_gate_set(gates, self.feature_dir, max_parallel=3)

        # Positive control: finishing order really is not declared order.
        self.assertLess(self.interval("lint")[1], self.interval("tests")[1])
        self.assertEqual(
            [r["name"] for r in results], ["tests", "lint", "other"])
        report = "\n\n".join(r["report"] for r in results)
        self.assertEqual(
            re.findall(r"^### ([\w-]+):", report, re.MULTILINE),
            ["tests", "lint", "other"])
        self.assertEqual(
            loop.parse_gate_failure_signature(report)[0], "tests")

    def test_gate_result_events_are_in_declared_order(self):
        cfg = {"defaults": {"max_parallel": 2},
               "code": [self.gate("slow", seconds=_SLEEP), self.gate("fast")]}
        loop.run_gate_broad_set(self.feature_dir, cfg=cfg)
        self.assertLess(self.interval("fast")[1], self.interval("slow")[1])
        events = loop.build_phase_gate_events("broad", "FEAT-2026-9001")
        self.assertEqual(
            [json.loads(json.dumps(e))["payload"]["gate"] for e in events],
            ["slow", "fast"])


class TestParallelSafety(_StubGates):
    def report_progress(self):
        """Run progress reporting into a real feature folder."""
        self.feature_dir = self.tmp / "feature"
        self.feature_dir.mkdir()
        self.events_path = self.feature_dir / "events.jsonl"
        quiet = contextlib.redirect_stdout(io.StringIO())
        quiet.__enter__()
        self.addCleanup(quiet.__exit__, None, None, None)
        progress.begin_run(
            "FEAT-2026-9001", self.feature_dir, self.events_path,
            build_event=loop.build_event, flush_events=loop.flush_events)
        self.addCleanup(progress.end_run)

    def status(self):
        return json.loads(progress.status_path(self.feature_dir).read_text())

    def script(self, name, source, *args):
        path = self.tmp / f"{name}.py"
        path.write_text(source)
        return {"name": name, "command": shlex.join(
            [Path(sys.executable).as_posix(), path.as_posix(),
             *(Path(a).as_posix() for a in args)])}

    @unittest.skipIf(sys.platform == "win32", "POSIX process groups")
    def test_a_timeout_kills_its_group_while_the_others_pass(self):
        pgid_file = self.tmp / "pgid"
        gates = [self.script("hang", _HANG_STUB, pgid_file),
                 self.gate("a", seconds=0.2), self.gate("b", seconds=0.2)]
        with mock.patch.object(loop, "GATE_TIMEOUT_SECONDS", 1):
            results = loop._run_gate_set(
                gates, self.feature_dir, max_parallel=3)
        self.assertEqual([r["ok"] for r in results], [False, True, True],
                         results)
        self.assertIn("GATE TIMEOUT: exceeded 1s and was killed",
                      results[0]["report"])
        pgid = int(pgid_file.read_text())
        deadline = time.monotonic() + 2
        # The orphaned child stays in the group until it is reaped.
        with self.assertRaises(ProcessLookupError):
            while time.monotonic() < deadline:
                os.killpg(pgid, 0)
                time.sleep(0.02)

    def test_each_parallel_gate_writes_each_event_once_on_whole_lines(self):
        self.report_progress()
        names = ["a", "b", "c", "d"]

        def torn_flush(path, events):
            """Write each line in two halves, so unserialised writers mix."""
            for event in events:
                line = json.dumps(event) + "\n"
                for part in (line[:20], line[20:]):
                    with path.open("a") as fh:
                        fh.write(part)
                    time.sleep(0.01)

        progress._run.flush_events = torn_flush
        loop._run_gate_set(
            [self.gate(n, seconds=0.2) for n in names], self.feature_dir,
            max_parallel=4)
        events = [json.loads(line)
                  for line in self.events_path.read_text().splitlines()]
        for event_type in ("gate_started", "gate_finished"):
            self.assertEqual(
                sorted(e["payload"]["gate"] for e in events
                       if e["event_type"] == event_type), names, event_type)
        self.assertEqual(len(events), 2 * len(names))
        self.assertEqual(self.status()["gates_running"], [])

    def test_the_status_file_names_every_running_gate(self):
        self.report_progress()
        seen = self.tmp / "seen.json"
        gates = [
            self.script("reader", _STATUS_STUB,
                        progress.status_path(self.feature_dir), seen),
            self.gate("other", seconds=2),
        ]
        loop._run_gate_set(gates, self.feature_dir, max_parallel=2)
        status = json.loads(seen.read_text())
        self.assertEqual(status["phase"], "gate")
        self.assertEqual(sorted(status["gates_running"]), ["other", "reader"])
        self.assertEqual(status["gate"], status["gates_running"][-1])
        after = self.status()
        self.assertEqual(
            (after["phase"], after["gate"], after["gates_running"]),
            ("between", None, []))

    def test_gate_stays_the_latest_started_gate_still_running(self):
        self.report_progress()
        self.assertEqual(self.status_after(progress.gate_started, "a"),
                         ("gate", "a", ["a"]))
        self.assertEqual(self.status_after(progress.gate_started, "b"),
                         ("gate", "b", ["a", "b"]))
        self.assertEqual(
            self.status_after(progress.gate_finished, "b", True, 0.1),
            ("gate", "a", ["a"]))
        self.assertEqual(
            self.status_after(progress.gate_finished, "a", True, 0.1),
            ("between", None, []))

    def status_after(self, call, *args):
        call(*args)
        status = self.status()
        return status["phase"], status["gate"], status["gates_running"]


class _CachedGates(unittest.TestCase):
    """A scratch repository as the working directory. Each run of a gate's
    command appends its name to a counter file outside it."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.counter = root / "counter.log"
        self.stub = root / "count.py"
        self.stub.write_text(
            "import sys\n"
            "open(sys.argv[2], 'a').write(sys.argv[1] + '\\n')\n"
            "sys.exit(int(sys.argv[3]))\n")
        repo = root / "repo"
        self.feature_dir = repo / "feature"
        self.feature_dir.mkdir(parents=True)
        (repo / "src").mkdir()
        (repo / ".gitignore").write_text("work/\n*.ignored\n")
        self.source = repo / "src" / "a.txt"
        self.source.write_text("one\n")
        subprocess.run(
            ["git", "init", "-q", str(repo)], check=True, capture_output=True)
        previous = os.getcwd()
        os.chdir(repo)
        self.addCleanup(os.chdir, previous)

    def command(self, name, code=0):
        return shlex.join([
            Path(sys.executable).as_posix(), self.stub.as_posix(), name,
            self.counter.as_posix(), str(code)])

    def gate(self, name="unit", code=0, inputs=("src/*",), **extra):
        gate = {"name": name, "command": self.command(name, code), **extra}
        if inputs:
            gate["inputs"] = list(inputs)
        return gate

    def count(self, name="unit"):
        if not self.counter.exists():
            return 0
        return self.counter.read_text().split().count(name)

    def verify(self, *gates, gate_file=None):
        wu = loop.WorkUnit(
            wu_id="FEAT-2026-9001/T01", type="implementation", model="m",
            status="pending", attempts=0, title="t", body="", depends_on=[],
            file=self.feature_dir / "WU.md")
        ok, report = loop.verify(
            wu, self.feature_dir, cfg={"code": list(gates)},
            gate_file=gate_file)
        return wu, ok, report


class TestCacheHit(_CachedGates):
    def test_an_unchanged_tree_reuses_the_pass(self):
        self.verify(self.gate())
        wu, ok, report = self.verify(self.gate())
        self.assertEqual(self.count(), 1)
        self.assertTrue(ok, report)
        self.assertIn("### unit: PASS (cached)", report)
        [event] = loop.build_attempt_gate_events(wu, 2)
        payload = event["payload"]
        self.assertIs(payload["cached"], True)
        self.assertEqual(payload["duration_seconds"], 0)
        self.assertIs(payload["ok"], True)

    def test_an_ignored_file_does_not_change_the_key(self):
        self.verify(self.gate())
        Path("src/scratch.ignored").write_text("x")
        self.verify(self.gate())
        self.assertEqual(self.count(), 1)

    def test_a_gate_run_fresh_carries_no_cached_field(self):
        wu, _, _ = self.verify(self.gate())
        [event] = loop.build_attempt_gate_events(wu, 1)
        self.assertNotIn("cached", event["payload"])

    def test_a_hit_readies_its_dependents_under_parallel_gates(self):
        gates = [self.gate("dependent", inputs=None, needs=["unit"]),
                 self.gate()]
        cache_path = self.feature_dir / "work" / "gate-cache.json"
        for _ in range(2):
            results = loop._run_gate_set(
                gates, self.feature_dir, max_parallel=2,
                cache_path=cache_path)
        self.assertEqual([r["ok"] for r in results], [True, True], results)
        self.assertEqual((self.count(), self.count("dependent")), (1, 2))


class TestCacheMiss(_CachedGates):
    def assert_reruns_after(self, change, gate=None):
        self.verify(self.gate())
        change()
        self.verify(gate or self.gate())
        self.assertEqual(self.count(), 2)

    def test_editing_a_matching_file(self):
        self.assert_reruns_after(lambda: self.source.write_text("two\n"))

    def test_adding_a_matching_file(self):
        self.assert_reruns_after(lambda: Path("src/b.txt").write_text("new"))

    def test_deleting_a_matching_file(self):
        Path("src/b.txt").write_text("kept")
        self.assert_reruns_after(self.source.unlink)

    @unittest.skipIf(sys.platform == "win32", "POSIX file modes")
    def test_chmod_on_a_matching_file(self):
        self.assert_reruns_after(lambda: self.source.chmod(0o755))

    def test_changing_the_command(self):
        changed = self.gate()
        changed["command"] += " extra"
        self.assert_reruns_after(lambda: None, changed)

    def test_a_failure_is_not_stored(self):
        for _ in range(2):
            _, ok, _ = self.verify(self.gate(code=1))
            self.assertFalse(ok)
        self.assertEqual(self.count(), 2)

    def test_a_gate_without_inputs(self):
        for _ in range(2):
            self.verify(self.gate(inputs=None))
        self.assertEqual(self.count(), 2)
        self.assertIsNone(loop.gate_cache_key(self.gate(inputs=None)))


class TestNeverForAVerdict(_CachedGates):
    def store_pass(self, gate):
        """Store a PASS of *gate*, shown to be served to `verify()`."""
        self.verify(gate)
        _, _, report = self.verify(gate)
        self.assertIn("PASS (cached)", report)
        self.assertEqual(self.count(gate["name"]), 1)

    def test_the_broad_run(self):
        self.store_pass(self.gate())
        ok, failing = loop.run_gate_broad_set(
            self.feature_dir, cfg={"code": [self.gate()]})
        self.assertTrue(ok, failing)
        self.assertEqual(self.count(), 2)

    def test_the_baseline_probe(self):
        self.store_pass(self.gate())
        self.assertEqual(loop.probe_baseline(
            self.feature_dir, cfg={"code": [self.gate()]}), [])
        self.assertEqual(self.count(), 2)

    def test_the_feature_oracle(self):
        command = self.command("feature_oracle")
        gate_file = self.feature_dir / "GATE-01.md"
        gate_file.write_text(
            f"---\nfeature_oracle: {json.dumps(command)}\n---\n")
        # Store a PASS under the oracle's name and command.
        cache_path = self.feature_dir / "work" / "gate-cache.json"
        seeded = {"name": "feature_oracle", "command": command,
                  "inputs": ["src/*"]}
        loop._run_gate_set([seeded], self.feature_dir, cache_path=cache_path)
        _, ok, report = self.verify(
            self.gate("other", inputs=None), gate_file=gate_file)
        self.assertTrue(ok, report)
        self.assertEqual(self.count("feature_oracle"), 2)

    def test_a_gate_another_gate_needs(self):
        self.store_pass(self.gate())
        for tier in ("narrow", "broad"):
            with self.subTest(dependent_tier=tier):
                before = self.count()
                _, _, report = self.verify(
                    self.gate(),
                    self.gate("dependent", inputs=None, needs=["unit"],
                              tier=tier))
                self.assertEqual(self.count(), before + 1)
                self.assertNotIn("PASS (cached)", report)


class TestConfigurationErrors(_CachedGates):
    def assert_refused(self, cfg, key):
        wu = loop.WorkUnit(
            wu_id="FEAT-2026-9001/T01", type="implementation", model="m",
            status="pending", attempts=0, title="t", body="", depends_on=[],
            file=self.feature_dir / "WU.md")
        ok, report = loop.verify(wu, self.feature_dir, cfg=cfg)
        self.assertFalse(ok)
        self.assertIn("CONFIGURATION ERROR", report)
        self.assertIn(key, report)
        self.assertEqual(self.count(), 0)

    def test_bad_max_parallel(self):
        for bad in (0, -1, "2", 1.5):
            with self.subTest(max_parallel=bad):
                self.assert_refused(
                    {"defaults": {"max_parallel": bad},
                     "code": [self.gate()]},
                    "max_parallel")

    def test_bad_inputs(self):
        for bad in ("src/", [], [""], [3]):
            with self.subTest(inputs=bad):
                gate = self.gate(inputs=None)
                gate["inputs"] = bad
                self.assert_refused({"code": [gate]}, "inputs")


if __name__ == "__main__":
    unittest.main()
