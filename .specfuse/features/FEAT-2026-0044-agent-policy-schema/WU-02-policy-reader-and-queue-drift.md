---
id: FEAT-2026-0044/T02
type: implementation
status: pending
attempts: 0
planned_cost_usd: 3.50
oracle_env: macos_local
produces:
  - .specfuse/agent-policy.yml
  - tests/test_agent_policy_queue.py
produces_driver_helper: load_policy, roadmap_statuses
---

# Add the policy reader and validate queue entries against the roadmap

**Objective.** Add `load_policy(path) -> dict` to
`specfuse/loop/agent_policy.py`, add a public `roadmap_statuses()` to
`specfuse/loop/lint_roadmap.py`, make `validate_agent_policy` check every queue
entry against the roadmap under the WARN/ERROR split below, and bootstrap this
repo's own `.specfuse/agent-policy.yml`.

**Context.** Correlation ID `FEAT-2026-0044/T02`. Depends on
`FEAT-2026-0044/T01`, which fixed the schema and these load-bearing strings —
quoted here verbatim, do not re-derive them from the diff:

- canonical config path: `.specfuse/agent-policy.yml`
- module: `specfuse/loop/agent_policy.py`
- validator: `validate_agent_policy(path: str | Path | None = None) -> list[str]`
- finding severity prefixes: `ERROR: ` and `WARN: ` (trailing space included)

**Reuse the roadmap parser; do not write a second one.**
`specfuse/loop/lint_roadmap.py` already parses the roadmap's status table:
`_parse_table_rows(lines) -> list` (line 276) returns one dict per row with keys
`id`, `status`, `detail`, `line`. It is private. **Add a public wrapper in that
same module** rather than importing the underscore name from another module:

```python
def roadmap_statuses(repo_root=None) -> dict:
    """Map FEAT-ID -> status string, read from .specfuse/roadmap.md."""
```

Every feature row — including `done`, `abandoned`, and `deferred` ones — lives
in `roadmap.md`; `roadmap-archive.md` holds only detail *sections*, never rows.
So this reads one file, and a FEAT-ID absent from it genuinely does not exist.

**The WARN/ERROR split is the point of this WU, and getting it wrong makes the
CI gate unsatisfiable.** This repo's queue names features that will *complete*.
If "queue entry is not `planned`/`active`/`blocked`" were fatal, the gate would
go red the first time any queued feature reached `done` — firing on a correct
tree, with the "fix" being to mutate the operator's priority file to satisfy a
linter. That is the shape `planning-discipline.md` §2 exists to catch, and
`roadmap_link_gate.py` already makes exactly this split for the same reason.

- **`ERROR: `** — the queue names a FEAT-ID with no row in `roadmap.md`.
  Unresolvable; a human must fix it.
- **`WARN: `** — the queue names a feature whose status is `done` or
  `abandoned`. Normal backlog evolution; `/groom-backlog` (T04) proposes
  removal. Prints, does not fail the gate.
- **No finding** — status is `planned`, `active`, `blocked`, or `deferred`.

`deferred` is deliberately not a finding: a parked feature is a legitimate
queue entry the operator may be holding a slot for, and the roadmap's own
status legend calls it resumable.

**The dogfood file.** Write `.specfuse/agent-policy.yml` for this repository
with a queue reflecting the operator's stated sequence as of 2026-08-09:
`FEAT-2026-0048`, then `FEAT-2026-0047`, then `FEAT-2026-0049`. Set
`rules.triage.auto: false` (T03 wires it; `false` preserves today's behavior),
`rules.bugs.automerge: off` (FEAT-2026-0048 owns the enforcement and it is not
built), `rules.features.gate_review: human`, `wip_limit: 1`. Leave
`escalation.webhook` empty — FEAT-2026-0047 has not shipped.

**Downstream-use note (`[FEAT-2026-0010/G1]`).** No WU in this gate
subprocess-invokes `/groom-backlog`. This file is authored directly here,
because the skill's entire contract is that a human accepts its proposal — an
unattended invocation would defeat it.

**Red-test-first.** Criterion 1 names a test that fails on HEAD because
`load_policy` does not exist.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_agent_policy_queue.py::TestQueueAgainstRoadmap::test_absent_feature_id_is_error`
   exists and **fails on HEAD before this WU runs**.
2. `specfuse/loop/agent_policy.py` defines
   `load_policy(path: str | Path | None = None) -> dict`, defaulting to
   `.specfuse/agent-policy.yml`, returning the parsed mapping.
3. `load_policy` raises `FileNotFoundError` when the path is absent — it does
   **not** silently return defaults, because a missing policy file and an empty
   queue are different declared states and a caller must be able to tell them
   apart. A test asserts this.
4. `specfuse/loop/lint_roadmap.py` defines a public
   `roadmap_statuses(repo_root=None) -> dict` mapping FEAT-ID to status string,
   implemented over the existing `_parse_table_rows`. A test asserts it returns
   `done` for `FEAT-2026-0002` and `blocked` for `FEAT-2026-0011` against the
   real roadmap.
5. `validate_agent_policy` emits one `ERROR: ` finding per queue entry that has
   no row in `roadmap.md`, naming the entry.
6. `validate_agent_policy` emits one `WARN: ` finding per queue entry whose
   roadmap status is `done` or `abandoned`, naming the entry and its status.
7. `validate_agent_policy` emits **no** finding for a queue entry whose status
   is `planned`, `active`, `blocked`, or `deferred`. A test covers all four.
8. The queue check is skipped without error when `roadmap.md` is absent — a
   consuming project may have a policy file before a roadmap. A test asserts
   zero findings in that case rather than a traceback.
9. `.specfuse/agent-policy.yml` exists at the repo root's `.specfuse/`, carries
   the queue and dial values named in this WU's Context, and
   `validate_agent_policy()` against it returns **zero `ERROR: ` findings**.
10. `.specfuse/verification.yml`'s `agent-policy-example-lint` gate is updated
    to run the validator against **both** `.specfuse/agent-policy.yml.example`
    and the live `.specfuse/agent-policy.yml`, and the comment T01 added
    (saying the live file does not exist yet) is corrected.
11. `python3 -m unittest tests.test_agent_policy_queue -v` exits zero after this
    WU's edits.
12. `python3 -c "from specfuse.loop.agent_policy import load_policy; from specfuse.loop.lint_roadmap import roadmap_statuses"`
    exits zero.

**Do not touch.** `specfuse/loop/triage.py` — T03 owns it. The
`/groom-backlog` skill directory — T04 owns it. `_parse_table_rows` itself and
the four existing link-graph checks in `lint_roadmap.py` — add the public
wrapper alongside them, do not alter their behavior; `roadmap-link-gate` must
stay green. `.specfuse/roadmap.md`. Generated directories, secrets, `.git/`.
See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`, `roadmap-link-gate`, and
`agent-policy-example-lint`. Plus the scoped red/green run in criteria 1 and 11
and the symbol check in criterion 12.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`_parse_table_rows` does not in fact expose a usable status per row (read it
first — if the shape differs from this WU's Context, that is a spec error worth
reporting rather than working around); or the roadmap contains a FEAT-ID row
whose status string is outside the documented set, which would mean the status
legend and the table have drifted. If `.specfuse/agent-policy.yml` is absent
from the files you edited, emit `status: blocked` — do not claim complete.
