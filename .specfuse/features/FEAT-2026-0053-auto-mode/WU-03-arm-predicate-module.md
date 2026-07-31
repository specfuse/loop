---
id: FEAT-2026-0053/T03
type: implementation
status: done
attempts: 1
planned_cost_usd: 4.50
produces:
  - specfuse/loop/arm_eval.py
  - tests/test_arm_eval.py
produces_driver_helper:
  - evaluate_arm_predicate
model: sonnet
effort: medium
gate_set: code
driver_version: 0.7.1
started_at: 2026-07-30T19:25:55.451558+00:00
duration_seconds: 696.771
cost_usd: 2.0213
input_tokens: 52
output_tokens: 39702
---

# The arm predicate — seven stop classes, hardcoded constants, pure evaluation

**Objective.** Ship `arm_eval.py`: a pure, side-effect-free predicate that
evaluates whether a just-closed gate's drafted successor may be armed, returning
a structured per-class verdict.

**Context.** Correlation ID `FEAT-2026-0053/T03`. Mirror the shape of
`gate_eval.py`'s `evaluate_auto_close` — pure evaluation over files, a
structured decision object, a formatter for the event trail, no side effects.
Separate module deliberately: arming and closing are different decisions with
different inputs; do not fold this into `gate_eval.py`.

**The organizing principle (PLAN.md):** model-authored signals may only veto;
only mechanical facts and human-authored constants may approve. Classes 6 and 7
below are veto channels — they can force `would_arm: False`, never `True`.

**Hardcoded constants (operator decision — no config surface in this feature):**
`BUDGET_PROJECTION_MULTIPLIER = 2.0`, `DRIFT_CAP_RATIO = 0.5`,
`ADDED_GATE_CAP = 1`, `JUDGE_PATHS` (verification.yml, `.specfuse/hooks/`,
`.specfuse/rules/`, `.github/workflows/`, `specfuse/loop/`, the coverage/lint
config sections of `pyproject.toml`), `DEPENDENCY_MANIFESTS` (the dependency
sections of `pyproject.toml`, `requirements*.txt`, `package.json`).

**The seven classes.** Inputs: the parsed PLAN, `load_baseline(feature_dir)`
(T01), the feature dir (WU frontmatter, `events.jsonl`), the drafted next-gate
WU files, and the review file.

1. **Budget projection** — lifetime spend across all WU statuses (the #221
   lesson: blocked burn counts) plus planned cost of not-yet-done WUs exceeds
   `BUDGET_PROJECTION_MULTIPLIER ×` the baseline's planned total.
2. **Judge-editing** — any drafted WU whose `produces:` paths or declared
   `produces_driver_helper` surface intersect `JUDGE_PATHS`.
3. **Decision-class paths** — any drafted WU whose `produces:` intersect
   `DEPENDENCY_MANIFESTS`.
4. **Retroactive edits** — a baseline WU belonging to a passed gate whose
   goal line or type differs from the baseline, or which has left the graph.
5. **Drift caps** — WUs present in the plan but not in the baseline: count or
   planned-dollar sum above `DRIFT_CAP_RATIO ×` the baseline figures, or the
   count of gates not in the baseline exceeding `ADDED_GATE_CAP`.
6. **Missing provenance** — any *added* WU (not in baseline) lacking a
   `provenance:` field. Veto channel.
7. **Open questions / human-only** — review-file `open_questions` missing OR
   non-empty, or any drafted WU carrying `human_only: true`. Veto channel;
   missing field fails closed.

**Honest v1 limit (state it in the module docstring):** a draft that weakens an
*existing* test's assertions is undetectable here. Judge-editing catches paths,
not semantics.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_arm_eval.py::TestArmPredicate::test_clean_on_plan_feature_would_arm`
   exists and **fails on HEAD before this WU runs** (file does not yet exist —
   red).
2. `evaluate_arm_predicate(feature_dir, just_closed_gate)` returns a structured
   decision carrying an overall `would_arm` bool plus a per-class result
   (fired / clean / not-evaluable, with a human-readable reason) for all seven
   classes, and a `_format_decision`-style serializer for the event payload.
3. Every class has at least one firing test and one staying-quiet test —
   fourteen or more focused cases over fixture feature dirs.
4. `baseline is None` short-circuits to `would_arm: False` with reason
   `no_baseline` — features predating T01 never auto-arm.
5. `tests/test_arm_eval.py::TestArmPredicate::test_clean_on_plan_feature_would_arm`
   **passes after this WU's edits**.

**Do not touch.** `specfuse/loop/loop.py` — wiring is T04's job; this module
must not import from `loop.py` (the dependency points the other way).
`specfuse/loop/gate_eval.py` (mirror its shape; never modify it).
`specfuse/loop/plan_baseline.py` beyond importing it. Generated directories,
secrets, `.git/`. The driver owns all git — edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`, plus symbol
existence: `python3 -c "from specfuse.loop.arm_eval import evaluate_arm_predicate"`.
Scoped iteration run: `python3 -m unittest tests.test_arm_eval -v`.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
any class cannot be evaluated from PLAN + baseline + frontmatter + events alone
and would need a git diff of body prose — name the class and stop; do not
approximate silently. If `evaluate_arm_predicate` is absent from the files you
edited, do not claim complete.
