---
id: FEAT-2026-0061/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 2.50
produces:
  - docs/concepts/autonomy-stop-classes.md
  - specfuse/loop/data/docs/concepts/autonomy-stop-classes.md
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-07-31T14:10:09.427955+00:00
duration_seconds: 205.677
cost_usd: 0.444499
input_tokens: 22
output_tokens: 3913
---

# Document what `decision_class_paths` can and cannot see

**Objective.** Rewrite §3 of `docs/concepts/autonomy-stop-classes.md` so it names
the class's coverage list, its `not_evaluable` triggers, and its limits — and sync
the `specfuse/loop/data/docs/` mirror so the shipped package data matches.

**Context.** Correlation ID `FEAT-2026-0061/T02`. Depends on T01: the coverage list
in this document must be **read off the shipped code**, not written in parallel with
it. If they disagree, the code is right and this document is the defect.

§3 today (`docs/concepts/autonomy-stop-classes.md:75`) says the class measures
whether a WU touches *"`pyproject.toml`, `package.json`, or a `requirements*.txt`
file"* and stops there. It documents the class without naming what it cannot see,
which is precisely the gap that let a Maven repository look covered.

The neighbouring §2 is the model to follow. It carries an **"Added-at-arming v1
approximation"** block that states a limit plainly, explains the consequence
(*"under `auto`, no gate that ships a documentation file can arm"*), and names the
clearing action. §3 needs the same honesty about its own edges.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**The mirror is not optional.** Every doc in this repository is mirrored into
`specfuse/loop/data/docs/` by the scaffold sync, and
`tests/test_scaffold_data_in_sync.py` fails when the two drift. Editing the source
doc without syncing the mirror turns the `tests` gate red. This is why the WU is
`type: implementation` and runs the `code` gate set rather than `type: docs`, which
would route to the `doc` set and skip the guard.

**Acceptance criteria.**

1. §3 of `docs/concepts/autonomy-stop-classes.md` names the **full covered list** as
   shipped by T01 — every exact-match manifest and every pattern — under
   **Measures:**.
2. The list in the document matches the table in `specfuse/loop/arm_eval.py` exactly.
   Verify by reading the shipped constant, not this WU's or T01's prose; name the
   command used to check in the result.
3. §3 documents the two `not_evaluable` triggers — the named-uncovered list and the
   glob/directory `produces:` entry — including what the operator should do when
   each fires.
4. §3 documents the **precedence** rule: a covered hit fires even when an
   undecidable path is present in the same WU.
5. §3 states the class's limit plainly, in the shape §2's "v1 approximation" block
   uses: coverage is a fixed list in the driver, so an ecosystem absent from it is
   invisible unless it appears in the named-uncovered list, and extending coverage
   is a driver release rather than project configuration.
6. The named-uncovered list is reproduced with each entry's reason, matching T01's
   shipped rationale. If T01 emptied the list, §3 says so explicitly and documents
   the glob trigger as the sole `not_evaluable` path — do not describe a list that
   does not exist.
7. The existing **Fires when:**, **Veto channel:**, and **Clearing action:**
   subsections are preserved in shape and updated in content where the widened
   surface changes them.
8. `specfuse/loop/data/docs/concepts/autonomy-stop-classes.md` is byte-identical to
   the source doc.
9. `python3 -m unittest tests.test_scaffold_data_in_sync -v` exits zero.
10. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
    `leak-scan`.
11. `leak-scan` clean — this WU writes prose, and
    `.specfuse/rules/` treats prose surfaces as in scope. Use no real
    organisation names, absolute home paths, or private repository paths in
    examples.

**Do not touch.** `specfuse/loop/arm_eval.py` — T01 owns it; if the code is wrong,
report it rather than patching it from a documentation WU. §§1–2 and 4–8 of
`autonomy-stop-classes.md`, except where criterion 7 requires it. `docs/methodology.md`
§412's class list — the names are unchanged by this feature. `scripts/sync-scaffold.sh`.
Generated directories, secrets, `.git/`. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. The real verification surface is
criterion 9's sync guard plus criterion 2's read-off-the-code check.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
shipped table in `arm_eval.py` cannot be read unambiguously into a documented list,
which would mean T01's criterion 3 ("stated in one place") was not actually met —
report the mismatch, do not paper over it in prose; or the mirror sync cannot be
performed without invoking a script this WU is told not to touch. If
`docs/concepts/autonomy-stop-classes.md` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
