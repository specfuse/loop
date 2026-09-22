# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The severity write path projects the repository's own word (#3353).

`severity_aliases` (#3349) let an operator say `severity:major` means `high`.
`read_severity_label` honours that map, so the `min_severity` floor reads an
aliased label correctly. The classifier that FEAT-2026-0113 added does not: it
answers in the published vocabulary, and the write path projected that answer
straight to `severity:<value>`.

So a repository declaring aliases got both spellings in circulation -- the
floor reading `severity:major`, the backfill writing `severity:high` beside it
-- with nothing reporting the asymmetry.

The fix keeps the classifier answering in the vocabulary (the marker's
`severity=` field stays comparable across repositories) and projects the
repository's own label on write, but only onto a label the repository actually
defines. That bound is what keeps a shipped default alias -- `blocker`,
`urgent`, `trivial` -- from inventing a label nobody created.

No test invokes the real gh binary: every test injects a stub runner.
"""

from __future__ import annotations

import unittest

from specfuse.agent.severity_backfill import apply_severity_backfill
from specfuse.loop.labels import severity_label_projection


class _Result:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _IssueRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, args, cwd=None, check=False):
        self.calls.append(args)
        return _Result(returncode=0)

    def added_labels(self):
        return [
            args[args.index("--add-label") + 1]
            for args in self.calls
            if "--add-label" in args
        ]


class SeverityLabelProjection(unittest.TestCase):

    def test_aliased_label_the_repo_defines_is_projected(self):
        projection = severity_label_projection(
            ["severity:major", "severity:minor"]
        )

        self.assertEqual(projection.get("high"), "severity:major")
        self.assertEqual(projection.get("low"), "severity:minor")

    def test_in_vocabulary_label_is_never_projected_away(self):
        # The repository defines both spellings. The vocabulary one wins, the
        # same precedence read_severity_rubric applies when building the rubric.
        projection = severity_label_projection(
            ["severity:major", "severity:high"]
        )

        self.assertNotIn("high", projection)

    def test_default_alias_the_repo_does_not_define_is_not_projected(self):
        # `blocker -> critical` ships in DEFAULT_SEVERITY_ALIASES. A repository
        # that never created `severity:blocker` must not have one written at it.
        projection = severity_label_projection(["severity:critical"])

        self.assertEqual(projection, {})

    def test_two_aliases_onto_one_value_resolve_deterministically(self):
        names = ["severity:urgent", "severity:blocker"]

        first = severity_label_projection(names)
        second = severity_label_projection(list(reversed(names)))

        self.assertEqual(first, second)
        self.assertEqual(first["critical"], "severity:blocker")

    def test_no_severity_labels_projects_nothing(self):
        self.assertEqual(severity_label_projection(["bug", "enhancement"]), {})


class BackfillWritesTheProjectedLabel(unittest.TestCase):

    DECISION = [{"number": 7, "body": "<!-- specfuse:triage kind=bug -->",
                 "severity": "high"}]

    def test_projection_is_written_instead_of_the_vocabulary_label(self):
        runner = _IssueRunner()

        rows = apply_severity_backfill(
            runner, "acme/widget", list(self.DECISION),
            label_projection={"high": "severity:major"},
        )

        self.assertEqual(runner.added_labels(), ["severity:major"])
        self.assertTrue(rows[0]["label_written"])

    def test_marker_still_records_the_vocabulary_value(self):
        # The projection is a label-only concern: the marker stays comparable
        # across repositories, which is why the classifier was left answering
        # in the vocabulary in the first place.
        runner = _IssueRunner()

        apply_severity_backfill(
            runner, "acme/widget", list(self.DECISION),
            label_projection={"high": "severity:major"},
        )

        bodies = [
            args[args.index("--body") + 1]
            for args in runner.calls if "--body" in args
        ]
        self.assertEqual(len(bodies), 1)
        self.assertIn("severity=high", bodies[0])
        self.assertNotIn("severity=major", bodies[0])

    def test_absent_projection_keeps_the_vocabulary_label(self):
        runner = _IssueRunner()

        apply_severity_backfill(runner, "acme/widget", list(self.DECISION))

        self.assertEqual(runner.added_labels(), ["severity:high"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
