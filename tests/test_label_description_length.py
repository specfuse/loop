#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Every registered label description fits what GitHub will accept.

`gh label create` rejects a description over **100 characters** with
`HTTP 422: Validation Failed — description is too long (maximum is 100
characters)`. `provision_labels` reports the failure and carries on, which is
the right behaviour for one repository being briefly unreachable and the wrong
outcome entirely for a spec that can never be created anywhere.

Measured on a consumer repository at upgrade time:

    label provisioning — created [], failed ['bug-lane:ci-pending',
    'bug-lane:test-not-red-on-base', 'bug-lane:red-on-base-unverified']

`bug-lane:ci-pending` is 101 characters and had been failing in every
repository since it shipped. Nothing noticed, because the consequence only
appears later and elsewhere: a declining bug-lane path calls `gh pr edit
--add-label` against a label that was never created, which is #1420 exactly —
the failure `tests/test_bug_lane_labels_registered.py` was written for, arriving
through the one door that test does not watch.

That test asserts every declining reason HAS a spec. This one asserts the spec
is one GitHub will actually accept. A registry entry that cannot be created is
indistinguishable, at the moment it matters, from no entry at all.
"""

from __future__ import annotations

import unittest

from specfuse.loop.labels import LABEL_REGISTRY

#: GitHub's documented maximum for a label description.
GITHUB_LABEL_DESCRIPTION_MAX = 100


class LabelDescriptionsFitGitHubsLimit(unittest.TestCase):

    def test_no_description_exceeds_the_limit(self):
        too_long = [
            f"{spec.name}: {len(spec.description)} chars"
            for spec in LABEL_REGISTRY
            if len(spec.description) > GITHUB_LABEL_DESCRIPTION_MAX
        ]

        self.assertEqual(
            too_long, [],
            f"`gh label create` rejects a description over "
            f"{GITHUB_LABEL_DESCRIPTION_MAX} characters with HTTP 422, so "
            f"these labels cannot be created in ANY repository — and a "
            f"declining path that tries to apply one fails the way #1420 did. "
            f"Over the limit:\n  " + "\n  ".join(too_long),
        )

    def test_the_registry_is_not_empty(self):
        # Guards the assertion above against passing vacuously if the registry
        # were ever emptied or failed to import.
        self.assertGreater(len(LABEL_REGISTRY), 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
