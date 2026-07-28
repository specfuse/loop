# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for FEAT-2026-0040/T03: redact_artifact.

Every text field of a `FailureArtifact` must pass through a redaction pass
before the artifact can be serialized, logged, or sent anywhere. See
`specfuse/monitor/redaction.py` for why this is a purpose-built
implementation rather than a reuse of `loop.py`'s `redact_leak_findings`.
"""

from __future__ import annotations

import unittest

from specfuse.monitor.artifact import FailureArtifact
from specfuse.monitor.redaction import redact_artifact

# Positive control: a purpose-built secret, held only as an in-memory string
# literal in this test module. Never written to disk. Its job is to prove the
# redaction pattern *fires* — a redactor tested only against text with no
# secret in it would pass a "no secrets in output" assertion vacuously.
_PLANTED_SECRET = "postgres://svc_user:Sup3rSecret!Pass@db.internal:5432/orders"


class TestRedaction(unittest.TestCase):
    def test_planted_secret_is_redacted_at_the_boundary(self):
        artifact = FailureArtifact(
            component="orders-worker",
            check_type="dlq",
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text=(
                f"connection failed: could not connect to {_PLANTED_SECRET}"
            ),
        )

        redacted = redact_artifact(artifact)

        for field_value in (
            redacted.component,
            redacted.check_type,
            redacted.failure_class,
            redacted.failure_signature,
            redacted.observed_text,
        ):
            self.assertNotIn(_PLANTED_SECRET, field_value)

    def test_positive_control_pattern_fires_on_planted_secret(self):
        # Proves the pattern actually matches this secret shape, rather than
        # a clean assertion above being evidence of a dead regex.
        artifact = FailureArtifact(
            component="c",
            check_type="dlq",
            failure_class="f",
            failure_signature="sig",
            observed_text=_PLANTED_SECRET,
        )

        redacted = redact_artifact(artifact)

        self.assertIn("<redacted:", redacted.observed_text)
        self.assertNotEqual(_PLANTED_SECRET, redacted.observed_text)

    def test_same_secret_redacts_to_same_token_different_to_different(self):
        secret_a = "Bearer abcDEF123456789token"
        secret_b = "Bearer zyxWVU987654321other"

        first = FailureArtifact(
            component="c",
            check_type="dlq",
            failure_class="f",
            failure_signature="sig",
            observed_text=f"{secret_a} seen twice: {secret_a}",
        )
        second = FailureArtifact(
            component="c",
            check_type="dlq",
            failure_class="f",
            failure_signature="sig",
            observed_text=secret_b,
        )

        redacted_first = redact_artifact(first).observed_text
        redacted_second = redact_artifact(second).observed_text

        tokens_in_first = set(
            part for part in redacted_first.split() if part.startswith("<redacted:")
        )
        self.assertEqual(len(tokens_in_first), 1, redacted_first)
        self.assertNotIn(redacted_first.split()[0], redacted_second)

    def test_ordinary_exception_text_passes_through_unchanged(self):
        text = "ValueError: could not parse order id 'ORD-4471' from payload"
        artifact = FailureArtifact(
            component="orders-worker",
            check_type="error-logs",
            failure_class="parse-error",
            failure_signature="orders.parse.value-error",
            observed_text=text,
        )

        redacted = redact_artifact(artifact)

        self.assertEqual(redacted.observed_text, text)

    def test_failure_signature_survives_redaction_unchanged(self):
        # T02's dedupe fingerprints on failure_signature; redacting it would
        # make two occurrences of the same failure hash to different
        # fingerprints. The signature is a stable classification string, not
        # a home for raw secret-bearing text, so it is left untouched.
        artifact = FailureArtifact(
            component="orders-worker",
            check_type="dlq",
            failure_class="dead-letter",
            failure_signature="orders.created.dlq",
            observed_text=_PLANTED_SECRET,
        )

        redacted = redact_artifact(artifact)

        self.assertEqual(redacted.failure_signature, artifact.failure_signature)


if __name__ == "__main__":
    unittest.main()
