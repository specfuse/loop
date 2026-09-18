---
gate: 3
status: open
feature_oracle: "python3 -m unittest tests.test_severity_backfill_end_to_end -v -b"
baseline:
  sha: 2ad6947f2f37e4817881cfad478733154fa4d245
  probed_at: 2026-09-18T11:13:46.301258+00:00
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1243e6b0132b414c07fe5cbe686e160a4037550a:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:1e7eddd5a3fb006c5435e947cd08d29e4f2b3d83:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:68aa52d59df9de92481bf5033d40ba0435e4000f:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:93ee36315be5a8a103cff62f2d5f68e591030cf5:97bcab1bc7244262cec901f46035f51dfdd07278:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d07e72b6db906e22e1c0961f3f89c84f5c1f32a6:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:e72cd2d47186e8a0ff1f9158e04f1749f9f874e5
  entry_sha: 2ad6947f2f37e4817881cfad478733154fa4d245
  source: attributed:FEAT-2026-0113/T09
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: "test_the_declared_console_scripts_match_the_wired_set"
    - gate: coverage
      failure_class: other
      failure_signature: "no_gate_marker"
---

# Gate 3 — backfill for issues already marked

## Definition of done

Drafted by gate 2's `plan-next`. The milestone: issues already carrying a triage
marker with no severity field can be re-read and labelled under an explicit mode,
never as part of a normal run.

Without this gate the feature classifies new issues and leaves the 31 measured
stranded issues exactly as they are — the marker is their idempotency key and it is
already written, so nothing else will ever revisit them.

The `feature_oracle` above drives the backfill mode end to end over an injected
runner: an open issue whose body carries a two-field triage marker and whose
labels are complete — the shape `list_untriaged` excludes and nothing revisits —
is re-read under `specfuse-backfill-severity --apply`, its marker amended with
`severity=` and the `severity:<value>` label projected after it; and the same
repository under a conductor run with no flag is left untouched, asserted by
argv. Both halves are in one module because the milestone is the pair: a backfill
that runs, and a normal run that does not.

`FEAT-2026-0113/T07` is the walking skeleton that turns it green and is the only
unit in this gate permitted to stub (`/authoring-work-units` §14). The oracle is
appended to every attempt's gate list, so a gate whose oracle module lands last
fails every earlier unit on `ModuleNotFoundError` — gate 2 paid four attempts for
that ordering and `GATE-03-REVIEW.md` records the correction.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Before flipping this gate's drafted work units to `pending`:

- **Runtime probe (§4).** Any unit here that flips a default or a severity is armed
  only after the change is applied locally and the unit's full tests gate is run —
  the whole oracle, not a subset — with the failure list pasted into this gate's
  `GATE-NN-REVIEW.md`. "Mechanical, nothing design-open" is not a basis to skip it.
- **Flag scope (§3).** Any unit introducing a flag or a policy key carries its
  flag-scope table.
- **Record precedence.** `PLAN.md` fixes marker-authoritative, label-as-projection,
  marker-written-first. A drafted unit that reorders those is wrong, not a variant.
- **Existing-mechanism search (§1).** `labels.py:267` already lists labels with
  their descriptions. A drafted unit that issues its own `gh label list` has not
  done the search.

## Arm-checkpoint decision (2026-09-18, operator-directed)

**Q1 — the backfill is its own console script, not a flag on `specfuse-agent`.**
It was drafted as `--backfill-severity` on the conductor binary: cheaper, and it
shared repo detection and branch restore. The operator chose the separate entry
point, because a bulk issue-mutating maintenance mode behind the same binary an
unattended run uses is one argv typo from the wrong thing.

Made structural rather than conventional: `specfuse/agent/run.py` is not edited
by this gate at all, and T07 criterion 2 measures that as an empty diff rather
than asserting it under a patch. `pyproject.toml` gains exactly one
`[project.scripts]` line and no dependency change.

**Q2 — dry run stays the default; `--apply` is required to write.** Backfill
only; the normal triage path is unchanged and gains no flag. A rare maintenance
action earns a second deliberate command.

**Q4 — the rubric stays vocabulary-only in this gate.** A repository whose
severity labels fall outside `SEVERITY_VALUES` gets a thin rubric — measured:
`clabonte/generator` yields a single entry — and T10 criterion 3 reports why
rather than pretending otherwise. The fix is two separate changes, deliberately
outside this feature: a shipped default alias table (#3355) so those words read
without every operator writing the same map, and an opt-in mode that harmonises
a repository's own labels onto the standard vocabulary (#3356), which dissolves
the mismatch instead of translating around it forever. A harmonised repository
needs neither aliases nor #3353's write-side projection.

**Consequence to hold in view at close:** backfill ships before it can unstrand
the 31 measured issues in the repository that motivated the feature. That is
accepted, not overlooked — #3356 is what unstrands them, and it reuses this
gate's selection and write machinery.
