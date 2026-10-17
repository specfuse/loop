# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""FEAT-2026-0204 gate 1 oracle: per-check diagnostic context (PLAN.md
"Diagnostic context"). Each class is skipped with its owning unit; the owner
removes the skip and makes it pass."""

from __future__ import annotations

import unittest


@unittest.skip("owned by FEAT-2026-0204/T05")
class EveryFinding(unittest.TestCase):
    SECTIONS = ("First seen", "Last seen", "Instances", "Reproduction")

    def test_sections_present(self):
        self.fail("T05")


@unittest.skip("owned by FEAT-2026-0204/T05")
class ErrorLogsContext(unittest.TestCase):
    SECTIONS = ("Top frame", "Request", "Logger", "Client abort", "Sample OperationIds")

    def test_sections_present(self):
        self.fail("T05")


@unittest.skip("owned by FEAT-2026-0204/T06")
class Http5xxContext(unittest.TestCase):
    SECTIONS = ("Correlated exception", "Failing dependency", "Duration", "Sample OperationIds")

    def test_sections_present(self):
        self.fail("T06")


@unittest.skip("owned by FEAT-2026-0204/T07")
class DlqContext(unittest.TestCase):
    SECTIONS = ("Message id", "Sequence number", "Dead-letter reason", "Body shape", "Peek command")

    def test_sections_present(self):
        self.fail("T07")


@unittest.skip("owned by FEAT-2026-0204/T08")
class HeartbeatContext(unittest.TestCase):
    SECTIONS = ("Schedule", "Last execution", "Earliest heartbeat", "Telemetry in silent gap")

    def test_sections_present(self):
        self.fail("T08")


@unittest.skip("owned by FEAT-2026-0204/T08")
class QueueStalledContext(unittest.TestCase):
    SECTIONS = ("Oldest active message age", "Last completed message", "Depth")

    def test_sections_present(self):
        self.fail("T08")


if __name__ == "__main__":
    unittest.main()
