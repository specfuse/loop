---
feature_id: FEAT-2026-0246
title: judge_editing covers the terminal gate
slug: judge-editing-terminal-gate
branch: feat/FEAT-2026-0246-judge-editing-terminal-gate
roadmap_goal: A terminal gate whose own substantive units produce a judge-surface path does not close unattended at any autonomy level; it stops for human review before the close, with an event naming each unit and path
autonomy_default: auto
status: done
planned_cost_usd: 17.00
---

# Plan: judge_editing covers the terminal gate

The `judge_editing` arm stop class (`arm_eval.py`) is what keeps a feature from
changing the machinery that grades it, and it reads only the drafted units of a
*successor* gate. A terminal gate has no successor, so what its own units change is
never checked, and a single-gate feature is never checked at all. FEAT-2026-0224/T01
edited `arm_eval.py` and closed with no human checkpoint (#3542).

Drafting found the gap is wider than the roadmap entry states. `fire_terminal_flips`
(`loop.py`) is gated only on the close's verdict and never reads `autonomy_default`;
`docs/methodology.md` §9 confirms that `review` and `supervised` differ from `auto`
only at the successor-gate arm. So the `review` recommendation #3544 shipped adds no
checkpoint on a terminal gate: FEAT-2026-0224 would have closed identically under it.

This feature adds a pure terminal-gate check in `arm_eval.py`, wires it in front of
both terminal close paths (auto-close and dispatched), lets an operator clear it with
an acknowledgement written into the close unit, and corrects the #3544 wording.

## Decisions (interview, 2026-10-28)

Items marked *operator* were answered explicitly; items marked *recommendation* were
taken as proposed under the operator's "go with your recommendations" and confirmed
when the skeleton was accepted.

1. **The stop applies at every autonomy level** (*operator*). The roadmap entry said
   "under `auto`"; the code shows autonomy does not gate terminal flips, so an
   `auto`-only stop would leave `review` closing unattended while the docs recommend
   it as the safeguard. The #3544 wording is corrected in T04.
2. **The stop sits before the terminal close starts** (*operator*), ahead of both
   `maybe_auto_close_terminal` and the dispatched close. The human reviews the judge
   edit before any judge grades the feature, no close spend is wasted on a rejected
   edit, and clearing reuses the ordinary pending-unit re-dispatch path. Stopping
   before `fire_terminal_flips` instead was rejected: the verdict would come from a
   judge that may be running the edited code, and a `done` close has no re-dispatch
   path to resume on.
3. **No pre-acknowledgement in `PLAN.md`** (*recommendation*). `arm_eval.py`'s
   organizing principle is that model-authored signals may only veto and only
   human-authored facts may approve. `PLAN.md` is written by `/draft-feature` and
   `plan-next`, both models, so a pre-approval there would be a model approving its
   own judge edit. Acknowledgement happens at the halt.
4. **Clearing** (*recommendation*). The operator writes
   `judge_edit_acknowledged: {paths: [...], reason: "<operator's own words>"}` into
   the close unit's frontmatter and runs `/unblock-wu` to flip it back to `pending`.
   The re-check is clean only when the acknowledged paths cover every current hit; it
   emits an acknowledgement event carrying the reason. A judge path added after the
   acknowledgement re-fires. Precedent: the operator-authored `re_arm_override` field
   (`rearm_reproduction_gate`, `loop.py`).
5. **Same `JUDGE_PATHS` as the arm class, universal entries included**
   (*recommendation*). This **corrects the roadmap entry's claim** that projects
   without the driver source are unaffected: `_UNIVERSAL_JUDGE_PATHS`
   (`.specfuse/verification.yml`, `.specfuse/hooks/`, `.specfuse/rules/`,
   `.github/workflows/`, `pyproject.toml`) match in every repository, so a consumer
   feature whose terminal gate edits its CI workflow or `pyproject.toml` halts once.
   Those are that project's judge surfaces; a second, narrower list would drift from
   the arm class's. The whole-file `pyproject.toml` match (a dependency bump fires it)
   is the arm class's existing v1 approximation, inherited and stated as a known limit.
6. **Scope of the check** (*recommendation*): the terminal gate's own units whose type
   is not in `gate_eval.NON_SUBSTANTIVE_TYPES` and whose status is `done`, by their
   declared `produces:` and `produces_driver_helper`. Earlier gates were armed by a
   human or by the arm predicate, which already checks them. Declared paths keep the
   check pure and file-based, like every other arm class.
7. **One gate** (*recommendation*). Four substantive units, under the 12-unit
   threshold in `docs/methodology.md` §6.
8. **This feature runs `auto` as a recursive dogfood** (*recommendation*). It edits
   `arm_eval.py` and `loop.py`, both judge modules. After T01 the driver's existing
   `driver_restart_required` halt makes later units run the new build, so the new
   stop is expected to fire on this feature's own close. `G1-CLOSE` criterion 1
   requires that it fired and was acknowledged, and records `not_met` otherwise —
   which withholds the terminal flips, so a stop that failed to fire still cannot
   close this feature unattended.
9. **`methodology.md`'s "`review` and `supervised` are the same behavior" line stays**
   (*recommendation*). It is accurate; only the advice that leaned on it is wrong.

## Known limits

- **Declared, not actual, paths.** A unit that edits a judge surface it did not
  declare in `produces:` is not caught. Checking the gate's real diff is out of scope.
- **`pyproject.toml` is matched whole-file** (decision 5), as in the arm class.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:**
  `grep -n "judge_editing\|JUDGE_PATHS\|produces_driver_helper" specfuse/loop/*.py`,
  `grep -n "autonomy_default" specfuse/loop/*.py`,
  `grep -n "_override_active =\|re_arm_override\|def resolve_auto_close_override" specfuse/loop/loop.py`.
- **Verdict:** `found the successor-gate check and the operator-override field pattern, extending; no terminal-gate judge-path check exists`
- **If reusing:** `arm_eval._matches_judge_path` and `JUDGE_PATHS` (the one definition
  of a judge surface; `bug_lane.py` already imports it); `gate_eval.NON_SUBSTANTIVE_TYPES`
  for which units count; `escalate_unit` (`loop.py:4394`) for the six-part brief; the
  `re_arm_override` frontmatter field as the shape of an operator-authored clearing
  fact; `/unblock-wu` for the `blocked_human` → `pending` flip. `fire_terminal_flips`
  and `maybe_auto_close_terminal` are not modified, only preceded.
  `resolve_auto_close_override` is not reused: `auto_close_disabled` forces a full
  close, it does not stop one.

## Escalation-predicate satisfiability (§2)

The new stop fires when a done substantive unit of the terminal gate declares a
`JUDGE_PATHS` path. **What does it report on an input already in its intended final
state?** For a feature with no such unit: clean, and the close proceeds exactly as on
HEAD (Definition of done 2, oracle class `CleanFeatureClosesUnchanged`). For a feature
with such units and an acknowledgement covering every hit: clean, with an
acknowledgement event (Definition of done 3). The predicate is satisfiable by a human
action the driver can read from a file.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0246/T01
        file: WU-01-terminal-check-walking-skeleton.md
        depends_on: []
      - id: FEAT-2026-0246/T02
        file: WU-02-acknowledgement.md
        depends_on: [FEAT-2026-0246/T01]
      - id: FEAT-2026-0246/T03
        file: WU-03-every-path-and-brief.md
        depends_on: [FEAT-2026-0246/T01]
      - id: FEAT-2026-0246/T04
        file: WU-04-docs.md
        depends_on: [FEAT-2026-0246/T02]
      - id: FEAT-2026-0246/T05
        file: WU-05-patch-restore-order.md
        depends_on: [FEAT-2026-0246/T03]
      - id: FEAT-2026-0246/T06
        file: WU-06-brief-names-ack-keys.md
        depends_on: [FEAT-2026-0246/T03]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-2026-0246/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0246/T01, FEAT-2026-0246/T02, FEAT-2026-0246/T03, FEAT-2026-0246/T04, FEAT-2026-0246/T05, FEAT-2026-0246/T06]
```

## Scope boundary

**In:** a pure terminal-gate judge-path check in `arm_eval.py`; its wiring ahead of
both terminal close paths in `loop.py`; the `judge_edit_acknowledged` close-unit field,
its re-check and its lint; the new event types in `driver-event.schema.json`; the
six-part brief; the `draft-feature`, `methodology.md` and `autonomy-stop-classes.md`
wording, in every copy.

**Out:**
- Assertion-semantics checks on existing tests — the class stays a path-surface check.
- Checking the gate's actual diff rather than declared `produces:` (known limit).
- The bug lane's own judge-path guardrail, which already covers PRs.
- A pre-acknowledgement field in `PLAN.md` (decision 3).
- Making `review` or `supervised` behave differently from `auto` in general.
- Narrowing the `pyproject.toml` whole-file match.

## Post-merge checklist

- **One consumer-repo halt.** After a loop release containing this feature, run one
  feature in a consumer repository whose terminal gate edits `.github/workflows/` or
  `.specfuse/verification.yml`; confirm the halt names the unit and path, and that
  writing `judge_edit_acknowledged` plus `/unblock-wu` lets the close run.
