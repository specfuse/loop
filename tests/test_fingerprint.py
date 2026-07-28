# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0040/T02: fingerprint_artifact.

Binding constraint (inherited from FEAT-2026-0069): a finding derived from a
target must fingerprint on that target's coordinates, not only the component
name — else 20 DLQ targets on one component collapse into one issue.
"""

from __future__ import annotations

import subprocess
import sys
import unittest

from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.fingerprint import fingerprint_artifact


class TestFingerprint(unittest.TestCase):
    def test_dlq_fingerprint_incorporates_subscription_and_function(self):
        base = FailureArtifact(
            component="orders-worker",
            check_type="dlq",
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text="message moved to dead-letter queue",
            target_coordinates={
                "subscription": "orders-created-sub",
                "function": "process-order",
            },
        )
        other_subscription = FailureArtifact(
            component="orders-worker",
            check_type="dlq",
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text="message moved to dead-letter queue",
            target_coordinates={
                "subscription": "orders-shipped-sub",
                "function": "process-order",
            },
        )
        other_function = FailureArtifact(
            component="orders-worker",
            check_type="dlq",
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text="message moved to dead-letter queue",
            target_coordinates={
                "subscription": "orders-created-sub",
                "function": "process-refund",
            },
        )
        base_fp = fingerprint_artifact(base)
        self.assertNotEqual(base_fp, fingerprint_artifact(other_subscription))
        self.assertNotEqual(base_fp, fingerprint_artifact(other_function))

    def test_heartbeat_fingerprint_incorporates_name(self):
        first = FailureArtifact(
            component="orders-worker",
            check_type="heartbeat",
            failure_class="missed-heartbeat",
            failure_signature="missed-heartbeat",
            observed_text="no heartbeat observed in window",
            target_coordinates={"name": "orders-worker-heartbeat"},
        )
        second = FailureArtifact(
            component="orders-worker",
            check_type="heartbeat",
            failure_class="missed-heartbeat",
            failure_signature="missed-heartbeat",
            observed_text="no heartbeat observed in window",
            target_coordinates={"name": "refunds-worker-heartbeat"},
        )
        self.assertNotEqual(fingerprint_artifact(first), fingerprint_artifact(second))

    def test_distinct_targets_produce_distinct_fingerprints(self):
        dlq_targets = [
            {"subscription": f"orders-sub-{i}", "function": "process-order"}
            for i in range(20)
        ]
        artifacts = [
            FailureArtifact(
                component="orders-worker",
                check_type="dlq",
                failure_class="dead-letter",
                failure_signature="orders.created.dlq",
                observed_text="message moved to dead-letter queue",
                target_coordinates=target,
            )
            for target in dlq_targets
        ]
        fingerprints = {fingerprint_artifact(a) for a in artifacts}
        self.assertEqual(len(fingerprints), len(artifacts))

    def test_invariant_fingerprint_ignores_absent_target_coordinates(self):
        first = FailureArtifact(
            component="orders-worker",
            check_type="invariant",
            failure_class="invariant-violation",
            failure_signature="orders.pending-count",
            observed_text="pending count exceeded threshold",
        )
        second = FailureArtifact(
            component="orders-worker",
            check_type="invariant",
            failure_class="invariant-violation",
            failure_signature="orders.pending-count",
            observed_text="pending count exceeded threshold (retry)",
        )
        self.assertIsNone(first.target_coordinates)
        self.assertIsNone(second.target_coordinates)
        self.assertEqual(fingerprint_artifact(first), fingerprint_artifact(second))

    def test_invariant_fingerprint_distinguishes_different_fingerprint_by(self):
        pending_count = FailureArtifact(
            component="orders-worker",
            check_type="invariant",
            failure_class="invariant-violation",
            failure_signature="orders.pending-count",
            observed_text="pending count exceeded threshold",
        )
        stock_level = FailureArtifact(
            component="orders-worker",
            check_type="invariant",
            failure_class="invariant-violation",
            failure_signature="orders.stock-level",
            observed_text="stock level exceeded threshold",
        )
        self.assertNotEqual(
            fingerprint_artifact(pending_count), fingerprint_artifact(stock_level)
        )

    def test_identical_artifacts_produce_the_same_fingerprint(self):
        def build():
            return FailureArtifact(
                component="orders-worker",
                check_type="dlq",
                failure_class="dead-letter",
                failure_signature="orders.created.dlq",
                observed_text="message moved to dead-letter queue",
                target_coordinates={
                    "subscription": "orders-created-sub",
                    "function": "process-order",
                },
            )

        self.assertEqual(fingerprint_artifact(build()), fingerprint_artifact(build()))

    def test_fingerprint_insensitive_to_coordinate_ordering(self):
        forward = FailureArtifact(
            component="orders-worker",
            check_type="dlq",
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text="message moved to dead-letter queue",
            target_coordinates={
                "subscription": "orders-created-sub",
                "function": "process-order",
            },
        )
        reversed_order = FailureArtifact(
            component="orders-worker",
            check_type="dlq",
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text="message moved to dead-letter queue",
            target_coordinates={
                "function": "process-order",
                "subscription": "orders-created-sub",
            },
        )
        self.assertEqual(
            fingerprint_artifact(forward), fingerprint_artifact(reversed_order)
        )

    def test_fingerprint_stable_across_separate_processes(self):
        script = (
            "from specfuse.monitor.artifact import FailureArtifact\n"
            "from specfuse.monitor.fingerprint import fingerprint_artifact\n"
            "artifact = FailureArtifact(\n"
            "    component='orders-worker',\n"
            "    check_type='dlq',\n"
            "    failure_class='dead-letter',\n"
            "    failure_signature='orders.created.dlq',\n"
            "    observed_text='message moved to dead-letter queue',\n"
            "    target_coordinates={'subscription': 'orders-created-sub', 'function': 'process-order'},\n"
            ")\n"
            "print(fingerprint_artifact(artifact))\n"
        )
        first = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, check=True
        )
        second = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, check=True
        )
        self.assertEqual(first.stdout, second.stdout)
        self.assertTrue(first.stdout.strip())


if __name__ == "__main__":
    unittest.main()
