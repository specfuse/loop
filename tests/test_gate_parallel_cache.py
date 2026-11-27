"""Parallel gates and the gate result cache (FEAT-LOOP-2026-0253).

The gate's feature oracle. Stub gates are Python commands that append their
start and end time to a log outside the feature folder and sleep, so
concurrency is read from recorded intervals, never from total wall time.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from specfuse.loop import loop

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


@unittest.skip("FEAT-LOOP-2026-0253/T02")
class TestParallelSafety(unittest.TestCase):
    def test_pending(self):
        self.fail("not implemented")


@unittest.skip("FEAT-LOOP-2026-0253/T03")
class TestCacheHit(unittest.TestCase):
    def test_pending(self):
        self.fail("not implemented")


@unittest.skip("FEAT-LOOP-2026-0253/T03")
class TestCacheMiss(unittest.TestCase):
    def test_pending(self):
        self.fail("not implemented")


@unittest.skip("FEAT-LOOP-2026-0253/T03")
class TestNeverForAVerdict(unittest.TestCase):
    def test_pending(self):
        self.fail("not implemented")


@unittest.skip("FEAT-LOOP-2026-0253/T04")
class TestConfigurationErrors(unittest.TestCase):
    def test_pending(self):
        self.fail("not implemented")


if __name__ == "__main__":
    unittest.main()
