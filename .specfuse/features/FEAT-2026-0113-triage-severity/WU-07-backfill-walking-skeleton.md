---
id: FEAT-2026-0113/T07
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.00
produces:
  - specfuse/agent/severity_backfill.py
  - pyproject.toml
  - tests/test_severity_backfill_end_to_end.py
---

# T07 — the backfill mode exists end to end, for one issue

**Objective.** A standalone `specfuse-backfill-severity` console script that
re-reads one already-marked, severity-less issue, amends its marker and projects
the label — and that the conductor binary cannot reach at all.

**Context.** `FEAT-2026-0113/T07`, gate 3. **This unit is the gate's tracer
bullet** (`/authoring-work-units` §14): it is the only unit in gate 3 permitted
to stub, and what it may stub is named below. It exists because `GATE-03.md`'s
`feature_oracle` is appended to **every** attempt's gate list, so a gate whose
oracle module lands last fails every earlier unit on `ModuleNotFoundError` —
that is what cost gate 2 four attempts (`RETROSPECTIVE.md`, gate 2; the
`FEAT-2026-0113/T02H` insertion).

Stubbable here, and only here: selection breadth (T08 owns the predicate — this
unit may take a single issue number), the marker amendment (T08 owns
`amend_marker_severity`; this unit carries a local `_amend_marker` that T09
deletes when it switches the call site over), and classification (T10 owns the
session — this unit may inject a fixed severity). **Not** stubbable: the write
order. `PLAN.md`'s **Record precedence** is binding — the marker's `severity=`
field is authoritative, the `severity:<value>` label is a projection, and the
marker is written first.

**The mode is a separate entry point, decided at the gate-3 arm checkpoint
(Q1).** It was drafted as a `--backfill-severity` flag on `specfuse-agent`,
which was cheaper and shared the conductor's repo detection and branch restore —
but it put a bulk issue-mutating maintenance mode behind the same binary an
unattended run uses, one argv typo away from the wrong thing. It is now its own
console script, `specfuse-backfill-severity`, registered in `pyproject.toml`'s
`[project.scripts]` beside the five that already exist.

The separation is structural rather than conventional: `specfuse/agent/run.py`
is **not edited at all** by this gate, so there is no branch in the conductor's
`main()` that could reach the backfill, and no flag on it to mistype. Criterion 2
proves the absence rather than asserting it.

**Note for the arming reviewer:** editing `pyproject.toml` fires the arm
predicate's `decision_class_paths` stop class, which is clean today. That is the
console-script registration and nothing else — no dependency is added, removed or
re-pinned.

**Acceptance criteria.**

1. `tests/test_severity_backfill_end_to_end.py::SeverityBackfill::test_marked_issue_without_severity_is_amended_then_labelled`
   fails on HEAD before this unit runs (an absent module is red) and passes
   after: with an injected runner whose issue listing returns one open issue
   whose body carries `<!-- specfuse:triage category=bug confidence=high -->`
   and whose labels carry `triage:bug`, the mode run with `--apply` issues
   `gh issue edit <n> --repo <r> --body` carrying a marker with `severity=`
   **before** `gh issue edit <n> --repo <r> --add-label severity:<value>`,
   asserted on the order of the recorded calls and not on their presence.
2. `test_the_conductor_cannot_reach_the_backfill`: `grep -c severity_backfill
   specfuse/agent/run.py` reports `0`, and `git diff main -- specfuse/agent/run.py`
   is empty at this unit's tree — the conductor is not edited, so no flag, branch
   or import in it can reach the backfill. Asserted as absence, not as behaviour
   under a patch.
2b. `pyproject.toml` registers exactly one new console script,
   `specfuse-backfill-severity = specfuse.agent.severity_backfill:main`, and the
   `[project.dependencies]` list is byte-identical to `main`'s — asserted by
   diffing that table, so a console-script edit cannot smuggle a dependency
   change past the reviewer.
3. `GATE-03.md`'s `feature_oracle` command exits 0 at this unit's tree — the
   walking-skeleton property, stated as a check rather than as a promise.
4. `python3 -c "from specfuse.agent.severity_backfill import backfill_severity"`
   exits 0, and the one stub this unit is permitted to leave is named
   `_amend_marker` so T09's switch-over has a single symbol to delete (§9).

**Do not touch.** `specfuse/agent/run.py` — **the whole file**, which is the
Q1 decision made structural: the conductor gains no flag, no branch and no
import, and criterion 2 measures that as an empty diff. `specfuse/loop/triage.py`
(T08). `specfuse/loop/labels.py` and `specfuse/agent/triage_invoke.py` (gate 2's,
read through their published names only). `specfuse/agent/providers/triage.py` —
the normal triage path is gate 2's and no gate-3 unit edits it. In
`pyproject.toml`, everything except the one `[project.scripts]` line: no
dependency added, removed or re-pinned, no version bump.
`.specfuse/agent-policy.yml` and `rules.bugs.min_severity`.

**Verification.** The narrow tier for `implementation` — the `code` gates in
`.specfuse/verification.yml` minus those declaring `tier: broad`, with `tests`
narrowed to this unit's `produces:` modules. Plus, in this unit's session:
`python3 -m unittest tests.test_agent_provider_triage tests.test_triage_severity_end_to_end -b`
(gate 2's behaviour, unedited), and criterion 4's import check.

**Escalation triggers.** If standing the mode up appears to require **any** edit
to `specfuse/agent/run.py` — a shared helper moved, an import added, a flag
threaded — stop and escalate rather than making it. Whatever is needed should be
imported from a module both entry points read, or duplicated in the backfill; the
conductor staying untouched is the boundary this gate's risk acceptance rests on,
and it was chosen deliberately over the cheaper shared-binary option. If the marker cannot be amended
without appending a second marker to the body, stop and escalate rather than
appending: an issue carrying two markers is read by whichever one
`_MARKER_RE.search` finds first, and every later gate-3 unit is scoped to
amendment, not to repair.
