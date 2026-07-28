# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Single registry of every GitHub label this package reads.

Each entry names the label, its provisioning colour/description, and the
consumer that reads it. Names are imported from the modules that own the
vocabulary (``escalation.py``, ``gh_features.py``) rather than retyped here,
so the registry cannot drift from what those consumers actually query.
"""

from __future__ import annotations

from dataclasses import dataclass

from specfuse.loop import escalation, gh_features


@dataclass(frozen=True)
class LabelSpec:
    name: str
    colour: str
    description: str
    consumer: str


LABEL_REGISTRY: tuple[LabelSpec, ...] = (
    LabelSpec(
        name=gh_features.FEATURE_LABEL,
        colour="1d76db",
        description="A roadmap-candidate feature request specfuse discovery reads",
        consumer="gh_features.py",
    ),
    LabelSpec(
        name=escalation.NEEDS_HUMAN_LABEL,
        colour="d93f0b",
        description="The loop stopped and needs a human decision",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="gate-review",
        colour="fbca04",
        description="A gate is at awaiting_review and needs review-and-arm",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="blocked-wu",
        colour="e99695",
        description="A work unit stopped and needs an operator decision",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="triage-question",
        colour="c5def5",
        description="An inbound issue needs categorising before it can be routed",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="drafting-needed",
        colour="bfd4f2",
        description="A queued feature has no folder yet and needs /draft-feature",
        consumer="escalation.py",
    ),
    LabelSpec(
        name="merge-approval",
        colour="0e8a16",
        description="A pull request is green and waiting on a merge decision",
        consumer="escalation.py",
    ),
)
