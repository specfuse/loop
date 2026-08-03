---
id: FEAT-2026-0063/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - docs/concepts/autonomy-stop-classes.md
  - specfuse/loop/data/docs/concepts/autonomy-stop-classes.md
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T16:10:44.674582+00:00
duration_seconds: 673.854
cost_usd: 0.828136
input_tokens: 48
output_tokens: 6594
---

# The unverified list, dated and readable, where an operator already looks

**Objective.** Add an "Observed on real input" section to
`docs/concepts/autonomy-stop-classes.md` carrying the per-class branch-observation
table, its measurement date, and the command that regenerates it — and write the same
bytes to the mirrored copy under `specfuse/loop/data/`.

**Context.** Correlation ID `FEAT-2026-0063/T03`. Read `PLAN.md` first. The doc
already documents all eight classes and, since FEAT-2026-0061, their `not_evaluable`
triggers; this WU adds what has actually been *seen*, which the page currently
implies is unknown by not mentioning it.

**Why hand-written prose and not a generated file.** A generated artefact nobody
reads is the failure FEAT-2026-0064's row describes — material that exists and is
discarded because it never reaches a page a human opens. The operator-facing page is
where an operator already goes when a class fires; the table belongs there, with the
regenerate command beside it so the reader can tell how stale it is.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `planning-discipline.md`.

## The trap, stated so it is not rediscovered

`docs/concepts/autonomy-stop-classes.md` is **mirrored** into
`specfuse/loop/data/docs/concepts/autonomy-stop-classes.md`, and
`tests/test_scaffold_data_in_sync.py::TestScaffoldDataInSync::test_package_docs_match_canonical`
byte-matches the two. Editing only the canonical copy fails the `tests` gate on a
diff this WU did not know it owed — and the failure surfaces as an unrelated-looking
sync error, not as "you forgot the mirror." Both paths are in `produces` for that
reason. Whether the mirror is written by hand or by `scripts/sync-scaffold.sh` is the
implementer's call; the acceptance is that the two match.

**Acceptance criteria.**

1. The section states, per class, which verdict branches have been observed on real
   input and which have not, using the sweep's own output rather than a
   hand-transcribed copy of `PLAN.md`'s table. Run T01's sweep and use what it prints.
2. The section carries an explicit measurement date and the exact command to
   regenerate it, so a reader can tell whether the figures are current.
3. The section names the never-fired classes explicitly as **unverified**, and states
   plainly that a class reporting `clean` on every real input to date is not the same
   as a class known to work. It must not read as reassurance.
4. The section states that the sample is small and grows by one per baselined
   feature — so a reader understands the list shrinks over time without anyone
   working on it.
5. It does **not** claim the five never-fired classes are broken. Never having fired
   is consistent with never having met an input that should trip them; the honest
   statement is that the branch is unexercised, not that it is defective.
6. `docs/concepts/autonomy-stop-classes.md` and
   `specfuse/loop/data/docs/concepts/autonomy-stop-classes.md` are byte-identical.
   Assert with `diff` and quote the (empty) output in the result.
7. `tests/test_scaffold_data_in_sync.py` passes — the specific guard this WU is most
   likely to trip. Run it by name and quote the result.
8. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/loop/arm_sweep.py` and its report contract — T01 owns it.
`.specfuse/verification.yml` — T02 owns it. `specfuse/loop/arm_eval.py`. The existing
class-by-class reference sections of the doc: this WU **adds** a section and does not
rewrite FEAT-2026-0061's `not_evaluable` trigger documentation.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. The load-bearing one is
`tests/test_scaffold_data_in_sync.py` (criterion 7) — run it by name and quote the
result, because it is the guard this WU is most likely to trip and its failure reads
as an unrelated sync error rather than a missing mirror.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: the
sweep's output and `PLAN.md`'s recorded table disagree in a way that cannot be
explained by corpus growth (a *different* set of classes never-firing, rather than
the same set on a larger sample); or the mirrored copy cannot be brought byte-identical
without touching files outside this WU's `produces` list. A straightforward count
drift between drafting and execution is **not** a block — that is expected, is why
the figures carry a date, and criterion 1 already says to use what the sweep prints.
Report the new numbers and continue.
