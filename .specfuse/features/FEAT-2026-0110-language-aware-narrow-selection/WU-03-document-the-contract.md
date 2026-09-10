---
id: FEAT-2026-0110/T03
type: implementation
status: draft
attempts: 0
planned_cost_usd: 2.50
produces:
  - .specfuse/verification.yml.example
  - specfuse/loop/loop.py
  - specfuse/loop/data/verification.yml.example
---

# Say `narrow_selection` on every surface that currently says "Python"

**Objective.** Update the surfaces that describe narrowing in Python-and-`tests/`
terms, so a consumer can discover the new keys without reading `loop.py`.

**Context.** FEAT-2026-0110/T03, issue #3281. T01 and T02 built the mechanism;
this unit makes it findable. Three surfaces state the old shape:

- `.specfuse/verification.yml.example` — the file a consumer copies. It
  documents `narrow_command` and `{selected_test_modules}` as "the dispatched
  unit's own declared test paths ... under `tests/`, as dotted module names."
- The dispatched-session prompt text in `specfuse/loop/loop.py` (around
  `loop.py:3402`) tells every session "your `produces:` names no `tests/` path,
  run the full `tests` gate" — advice that is wrong in a Maven repo.
- `.specfuse/rules/verification-discipline.md` describes the narrow tier.
  **Check before editing:** that file is vendored from the methodology core and
  is listed in `sync-scaffold.sh`'s `CORE_FILES`. If the wording needs to
  change, it is a core edit, not a loop edit — escalate rather than editing the
  vendored copy (#3285/#3287 exist because that boundary was crossed).

`scripts/sync-scaffold.sh` copies `.specfuse/` to `specfuse/loop/data/`; run it
rather than hand-editing the packaged copy, and it now refuses if the core
checkout is dirty or unpushed — that refusal is about `CORE_FILES`, not about
this unit's files.

**Acceptance criteria.**

1. `.specfuse/verification.yml.example` documents all four keys with their
   defaults and carries the Maven example from #3281 as a comment;
   `grep -c "narrow_selection" .specfuse/verification.yml.example` returns at
   least 1.
2. The dispatched-session prompt text no longer asserts `tests/` as the only
   test root: `grep -n "tests/ path" specfuse/loop/loop.py` returns no line that
   states it as a universal rule, and the replacement names the gate's
   configured roots instead.
3. `.specfuse/verification.yml.example` and
   `specfuse/loop/data/verification.yml.example` are byte-identical after
   running `bash scripts/sync-scaffold.sh`:
   `diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example`
   exits 0.
4. Red-test exempt: documentation and prompt prose introduce no behaviour, and
   criteria 1–3 are greps and a `diff` rather than assertions about runtime.
   The existing suite must stay green:
   `python3 -m unittest tests.test_scaffold_data_in_sync -v` exits 0.

**Do not touch.** `.specfuse/rules/verification-discipline.md` — vendored from
the methodology core; escalate instead (see Context).
`.specfuse/verification.yml` (the live gate set, as distinct from the
`.example`); the sibling WU files `WU-01-narrow-selection-config.md` and
`WU-02-formats-and-refusal.md`; plus `.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set minus every gate declaring `tier: broad`.
Then `bash scripts/sync-scaffold.sh` and the `diff` in criterion 3, and
`python3 -m unittest tests.test_scaffold_data_in_sync -v`. The broad tier is the
driver's — never run in-session.

**Escalation triggers.** Stop with `status: blocked` if the narrow-tier wording
that needs changing turns out to live in `verification-discipline.md` (a
core-owned file — the canonical edit belongs upstream in
`specfuse/specfuse`, and vendoring a local edit is what #3285 fixed); or if
`sync-scaffold.sh` refuses because the core checkout is dirty or carries
unpushed commits, which is a environment condition an operator must clear.
