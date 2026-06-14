---
id: FEAT-2026-0018/T01
type: implementation
effort: high
status: done
attempts: 2
planned_cost_usd: 1.80
generated_surfaces: []
produces_driver_helper:
  - AutoCloseDecision
  - evaluate_auto_close
  - _read_plan_metrics
  - _read_wu_metrics
  - _read_events
  - _apply_predicate
duration_seconds: 1340.116
cost_usd: 2.85459
input_tokens: 56
output_tokens: 72423
---

# Standalone `gate_eval.py` module — predicate + decision dataclass

**Objective.** Land a pure, side-effect-free Python module at
`.specfuse/scripts/gate_eval.py` that, given a feature directory and
a gate id, returns a deterministic `AutoCloseDecision` against the
v1 predicate. No imports from `loop.py`. No git commands. No state
mutation. Driver wiring is T04's job; tests are T02's job; CLI is
T03's job. This WU ships only the module.

**Context.** This is `FEAT-2026-0018/T01`. Foundation of the
deterministic gate-close predicate. The predicate's v1 constants
and exact algorithm are specified in `PLAN.md` § "Predicate v1" —
read that section before authoring.

Inputs the module must parse:
- **`PLAN.md`** — feature frontmatter (`planned_cost_usd`,
  `auto_close_disabled`), task graph (gate → work_units → ids).
  Use the same minimal YAML the rest of the loop uses
  (`.specfuse/scripts/_miniyaml.py`).
- **WU frontmatter** for each WU in the target gate
  (`planned_cost_usd`, `cost_usd`, `attempts`, `type`,
  `auto_close` if present, FEAT-2026-0016 cumulative fields if
  present — graceful degrade when absent).
- **GATE-NN.md frontmatter** (`status`, `cost_budget_usd`).
- **`events.jsonl`** at `.specfuse/events.jsonl` — filter to this
  gate's WUs; look for `human_escalation` / `blocked_human` /
  `replan` events, plus `attempt_outcome` (final per WU).

Reference binding rules: `.specfuse/rules/never-touch.md` (no
driver edits — that's T04), `.specfuse/rules/correlation-ids.md`
(parsing WU IDs).

Why pure module separate from `loop.py`: predicate evolution is
the highest-tuning surface this feature creates. Unit-testable in
isolation, backtestable retroactively (T03), reusable by future
tooling without dragging in driver dependencies.

**Acceptance criteria.**

1. **File created:** `.specfuse/scripts/gate_eval.py` exists. No
   import of `loop` or anything from `.specfuse/scripts/loop.py`.
   No `subprocess` calls. No file writes. Pure read + compute.
   Verify: `python3 -c "import ast; tree = ast.parse(open('.specfuse/scripts/gate_eval.py').read()); imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]; assert not any('loop' in (getattr(n, 'module', '') or '') + ' '.join(a.name for a in n.names) for n in imports), 'loop import found'"`.

2. **`AutoCloseDecision` dataclass** at module top-level (uses
   `dataclasses.dataclass(frozen=True)`):
   ```python
   @dataclass(frozen=True)
   class AutoCloseDecision:
       auto: bool                     # True iff predicate fires
       reasons: list[str]             # one entry per failing criterion (empty if auto)
       metrics: dict                  # raw numbers for human inspection
       gate_id: int
       feature_id: str
       predicate_version: str         # "v1" — bumped when constants change
   ```
   `metrics` SHOULD include at minimum: `per_wu_cost`, `per_wu_planned`,
   `gate_total_cost`, `gate_budget`, `plan_next_cost`, `plan_next_planned`,
   `blocked_human_events`, `replan_events`, `final_outcomes`.

3. **Hardcoded predicate constants** at module top (named, not
   inlined):
   ```python
   PREDICATE_VERSION = "v1"
   PER_WU_COST_RATIO_CEILING = 1.5
   PER_WU_HARD_OVERRUN_RATIO = 2.0
   PLAN_NEXT_COST_RATIO_CEILING = 1.5
   ```

4. **`evaluate_auto_close(feature_dir: Path, gate_id: int) -> AutoCloseDecision`**
   top-level function. Algorithm (in order; collect all failure
   reasons rather than short-circuiting — operator sees every
   trip):
   - Load PLAN.md frontmatter + task graph. If
     `auto_close_disabled: true` in frontmatter, return
     `AutoCloseDecision(auto=False, reasons=["auto_close_disabled_per_plan"], ...)`.
     This is honored even before reading WU evidence — it's the
     operator's manual override.
   - Resolve gate's WU list from the task graph. For each WU,
     parse its file's frontmatter.
   - Load `events.jsonl`; filter to events whose payload
     references one of this gate's WU ids.
   - Apply each predicate criterion (PLAN.md § "Predicate v1");
     each failed criterion appends a reason string to `reasons`.
     Reason strings should be machine-parseable + human-readable,
     e.g. `"blocked_human_in_chain: T02 escalated 2026-06-12"`,
     `"per_wu_cost_overrun: T03 actual=$1.85 planned=$0.80 ratio=2.31x"`,
     `"plan_next_overrun: G1-PLAN actual=$5.76 planned=$1.50 ratio=3.84x"`.
   - If `reasons` is empty → `auto=True`. Otherwise `auto=False`.

5. **Helper functions** (top-level, prefixed `_`, individually
   testable):
   - `_read_plan_metrics(feature_dir: Path) -> dict` — returns
     frontmatter + parsed task-graph gates.
   - `_read_wu_metrics(wu_path: Path) -> dict` — returns WU
     frontmatter as dict, with defaults for missing fields
     (cost_usd defaults to 0.0, attempts defaults to 0, etc.).
   - `_read_events(events_path: Path, wu_ids: list[str]) -> list[dict]`
     — returns events filtered to this gate's WUs. If the file
     doesn't exist, returns `[]` (graceful degrade).
   - `_apply_predicate(plan_metrics, wu_metrics_list, events,
     gate_budget) -> tuple[list[str], dict]` — returns
     `(reasons, metrics_dict)`. This is the pure-function core
     of the predicate; T02 tests target this directly.

6. **Graceful degrade** behavior, explicit:
   - Missing `planned_cost_usd` on a WU: skip checks 3/4/5 for
     that WU. Add `"planned_cost_missing: <wu_id>"` to a separate
     `warnings` list inside `metrics["warnings"]`. Does NOT
     disable auto on its own (warning, not failure).
   - Missing `cost_budget_usd` on the gate: skip check 6.
   - Missing `events.jsonl`: treat as empty. Predicate evaluates
     against frontmatter only. Add
     `"events_jsonl_missing"` to `metrics["warnings"]`.
   - Missing WU file referenced in PLAN.md graph: this IS a
     failure — `reasons.append("wu_file_missing: <wu_id>")` and
     auto=False. The graph said this WU exists; predicate refuses
     to evaluate against partial data.

7. **No closing-WU types in cost checks.** When iterating WUs for
   checks 3/4 (per-WU cost ratios), SKIP WUs whose `type` is
   `close` / `close-intermediate`. Rationale: this predicate is
   asked AT close time; the closing WU is either skipped (auto
   path) or about to dispatch (non-auto path). Its `cost_usd` is
   either 0 (skipped) or unknown (pre-dispatch). Plan-next IS
   in scope for check 5 separately because plan-next dispatches
   even on auto-intermediate close (option A).

8. **Symbol-existence check** before declaring complete (per
   authoring-work-units §9). Run from repo root; every command
   must exit 0:

   ```bash
   # a. Module file exists with expected symbols
   test "$(grep -cE '^(class AutoCloseDecision|def evaluate_auto_close|def _read_plan_metrics|def _read_wu_metrics|def _read_events|def _apply_predicate|PREDICATE_VERSION|PER_WU_COST_RATIO_CEILING|PER_WU_HARD_OVERRUN_RATIO|PLAN_NEXT_COST_RATIO_CEILING)' .specfuse/scripts/gate_eval.py)" = "10"

   # b. Module imports cleanly with no side effects
   (cd .specfuse/scripts && python3 -c "from gate_eval import AutoCloseDecision, evaluate_auto_close, _read_plan_metrics, _read_wu_metrics, _read_events, _apply_predicate, PREDICATE_VERSION, PER_WU_COST_RATIO_CEILING, PER_WU_HARD_OVERRUN_RATIO, PLAN_NEXT_COST_RATIO_CEILING; assert PREDICATE_VERSION == 'v1'")

   # c. Module does NOT import from loop
   ! grep -E '^(from loop|import loop)' .specfuse/scripts/gate_eval.py

   # d. AutoCloseDecision is frozen + has all expected fields
   (cd .specfuse/scripts && python3 -c "from gate_eval import AutoCloseDecision; import dataclasses; assert dataclasses.is_dataclass(AutoCloseDecision); fields = {f.name for f in dataclasses.fields(AutoCloseDecision)}; assert fields == {'auto','reasons','metrics','gate_id','feature_id','predicate_version'}, fields")

   # e. Smoke-eval against this feature's own gate 1 (will return
   # auto=False because draft WUs have no cost_usd yet) — proves
   # the module runs end-to-end without raising.
   python3 -c "import sys; sys.path.insert(0, '.specfuse/scripts'); from pathlib import Path; from gate_eval import evaluate_auto_close; d = evaluate_auto_close(Path('.specfuse/features/FEAT-2026-0018-auto-close-predicate'), 1); print(d.auto, d.reasons[:3])"

   # f. Working-tree diff touches the module file (prior-hollow-pass guard)
   git diff --name-only HEAD | grep -qx '.specfuse/scripts/gate_eval.py'
   ```

   If (a) returns anything other than `10`, OR (b)/(d)/(e) raises,
   OR (c) matches anything, OR (f) is empty: emit `status: blocked`
   with the failing command + observed output. Do NOT flip this
   WU's frontmatter `status` field as a substitute for shipping
   the code.

**Do not touch.** Exactly 1 file changes:
- `.specfuse/scripts/gate_eval.py` (new file).

No edits to: `.specfuse/scripts/loop.py` (T04 owns), `lint_plan.py`,
`.specfuse/templates/`, skills, other features, secrets, `.git/`,
`_generated/`. The driver owns all git; edit files only. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`
(tests, lint, security, coverage) must pass. Plus AC8's symbol-
existence + import checks. Note: T01 ships the module but no tests
yet — coverage cannot enforce ≥ 90% on `gate_eval.py` until T02
lands. The `code` gate's existing coverage policy applies to other
files unchanged.

**Escalation triggers.**

1. **Completeness.** AC8 command (a) returns anything other than
   `10` → emit `status: blocked`. The module is incomplete. Do
   NOT flip this WU's frontmatter `status` field as a substitute
   for shipping the code; that is the documented hollow-pass shape
   (see FEAT-2026-0007/T04, FEAT-2026-0008/T01, FEAT-2026-0017/T01
   priors).
2. **Loop-import bleed.** If `gate_eval.py` ends up importing
   anything from `loop.py` (a `WorkUnit` dataclass, a parsing
   helper, anything), emit `status: blocked` with the offending
   import line. The architectural contract is that `loop.py`
   imports `gate_eval` (T04's job), never the reverse. Pure
   module is the unit-testability + reusability lever.
3. **YAML-parsing dependency.** This repo uses
   `.specfuse/scripts/_miniyaml.py`, a deliberate minimal-YAML
   parser. Do NOT add `pyyaml` or `ruamel.yaml`. Re-use
   `_miniyaml` (it's importable as a sibling module from
   `.specfuse/scripts/`). If `_miniyaml` lacks a feature you
   need (it parses flat frontmatter + simple lists/maps), emit
   `status: blocked` with the specific shape that fails — do NOT
   reach for a heavier parser unilaterally.
4. **Algorithm ambiguity.** The PLAN.md "Predicate v1" section
   names seven checks. If implementation of any check requires
   reading evidence the section does not name (e.g., a field
   not in WU frontmatter, an event type not in events.jsonl),
   emit `status: blocked` naming the missing input. Do not
   invent a degraded behavior unilaterally; the operator
   refines the spec.
