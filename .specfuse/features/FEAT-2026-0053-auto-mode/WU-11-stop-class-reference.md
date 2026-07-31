---
id: FEAT-2026-0053/T11
type: implementation
status: done
attempts: 2
planned_cost_usd: 3.00
oracle_env: macos_local
provenance: "G2-PLAN's dispatch brief names 'the seven-plus-one stop classes documented as an operator-facing reference' as minimum gate-3 scope: a parked auto feature is diagnosable only if the reader can map a fired class to a fix. Sharpened by RETROSPECTIVE.md gate-2 Findings 2 — an arm_predicate_evaluated event emitted from an escalation flip site carries a gate number that does not mean what a consumer will read it to mean, so the reference has to teach reading the event, not only the classes."
produces:
  - docs/concepts/autonomy-stop-classes.md
  - specfuse/loop/data/docs/concepts/autonomy-stop-classes.md
  - docs/README.md
  - tests/test_scaffold_data_in_sync.py
duration_seconds: 1015.283
cost_usd: 1.761523
input_tokens: 1540
output_tokens: 17269
---

# The eight stop classes, as an operator-facing reference

**Objective.** Ship `docs/concepts/autonomy-stop-classes.md`: one entry per stop
class, each mapping a fired verdict to the operator action that clears it, plus
how to read an `arm_predicate_evaluated` event correctly. Register the new page
in the docs index and in the scaffold drift guard so it ships to downstream
projects.

**Context.** Correlation ID `FEAT-2026-0053/T11`. A parked `auto` feature stops
at `awaiting_review` with its reason in an event and nowhere else. Without this
page the operator's recovery path is reading `specfuse/loop/arm_eval.py`. `T10`
owns the methodology's conceptual §9 and links here; this page owns the
per-class detail and must not restate §9's framing.

**The eight classes, from `specfuse/loop/arm_eval.py`'s `CLASS_NAMES` — read
them from the source, not from this list, before writing.** In order:
`budget_projection`, `judge_editing`, `decision_class_paths`,
`retroactive_edits`, `drift_caps`, `missing_provenance`,
`open_questions_human_only`, `plan_next_lint`. Three are veto channels
(`VETO_CLASSES`: `missing_provenance`, `open_questions_human_only`,
`plan_next_lint`) — the only places model-authored output reaches the verdict,
and they can only subtract. The published constants
(`BUDGET_PROJECTION_MULTIPLIER`, `DRIFT_CAP_RATIO`, `ADDED_GATE_CAP`,
`JUDGE_PATHS`) are hardcoded in v1 and belong in the page as values, with the
note that tuning graduates to `agent-policy.yml`
([FEAT-2026-0044](../../roadmap.md)) tighten-only.

**Three statuses, not two.** Each class returns `fired`, `clean`, or
`not_evaluable`. `not_evaluable` is the fail-closed path — with no
`PLAN.baseline.json` every class returns `not_evaluable: no_baseline` and
`would_arm` is `False`. An operator who reads `not_evaluable` as "nothing wrong
here" will misdiagnose a feature that will never arm. Say so.

**Reading the event is part of the reference, and it has a known trap.**
`RETROSPECTIVE.md`'s gate-2 Findings §2 records that the first live
`arm_predicate_evaluated` event was emitted from an *escalation* flip site
during a pre-flight baseline halt: its payload reads `gate: 2` for a gate that
had dispatched zero work units, with `open_questions_human_only` fired on
`GATE-03-REVIEW.md missing`. The payload does not record which of the three flip
sites emitted it. The page must state plainly what such an event means ("the
predicate was evaluated at a flip involving gate N") and what it does not mean
("gate N closed and would not arm gate N+1"), because a consumer grouping events
by gate will read it the wrong way.

**Shared surfaces with `T12`, declared up front.** Both this WU and `T12` add a
page under `docs/concepts/` and therefore both edit `docs/README.md`'s concepts
index and `tests/test_scaffold_data_in_sync.py`'s `DOCS_TRACKED` set. `T12`
`depends_on` this WU so the two edits are sequential, not concurrent. Add only
your own entry to each; leave room for the other rather than restructuring
either list.

**Acceptance criteria.**

1. `docs/concepts/autonomy-stop-classes.md` exists and is non-empty, with one
   section per class in `CLASS_NAMES` order — eight sections. Verified by
   `python3 -c "from specfuse.loop.arm_eval import CLASS_NAMES; import pathlib; t=pathlib.Path('docs/concepts/autonomy-stop-classes.md').read_text(); missing=[c for c in CLASS_NAMES if c not in t]; print(missing); assert not missing"`
   exiting `0`.
2. Each class section states, in this order: what the class measures, what input
   makes it fire, whether it is a veto channel, and **the concrete operator
   action that clears it**. A section that describes the class without naming a
   clearing action does not satisfy this criterion.
3. The page states the three per-class statuses and explains `not_evaluable` as
   the fail-closed path, naming `no_baseline` as the case an operator will
   actually meet.
4. The page records the v1 constants with their values —
   `BUDGET_PROJECTION_MULTIPLIER`, `DRIFT_CAP_RATIO`, `ADDED_GATE_CAP`, and the
   `JUDGE_PATHS` prefix list — and states they are hardcoded, with the
   `agent-policy.yml` graduation named as the future home.
5. The page contains a section on reading an `arm_predicate_evaluated` event
   that states both what a payload's `gate` field means and what it does not
   mean, per `RETROSPECTIVE.md` gate-2 Findings §2.

6. **Added at arming (open question 2, accepted as a v1 approximation).** The
   `judge_editing` section states that the class fires on any path under the
   `specfuse/loop/` prefix, that every documentation file in this repo is
   mirrored into `specfuse/loop/data/docs/`, and therefore that **under `auto`
   no gate shipping a documentation file can arm** — the prefix test cannot
   distinguish package data from driver source. Name the same v1-approximation
   shape already documented for `pyproject.toml`. This is the case the first
   `auto` feature to write docs will hit, and the operator who meets it must be
   able to find the answer on this page instead of reading `arm_eval.py`. The
   clearing action required by AC#2 for this class is the human arm, not a code
   change; say so explicitly.
7. `docs/README.md`'s "Concepts (under `concepts/`)" list gains an entry for the
   new page.
8. `specfuse/loop/data/docs/concepts/autonomy-stop-classes.md` exists,
   `DOCS_TRACKED` in `tests/test_scaffold_data_in_sync.py` names the new path,
   and `python3 -m unittest tests.test_scaffold_data_in_sync -v` exits `0`.
   Adding the page without registering it in `DOCS_TRACKED` leaves it untracked
   by the drift guard and does not satisfy this criterion.
9. `python3 -m unittest discover -s tests -v` exits `0`.

**Do not touch.** `specfuse/loop/arm_eval.py` and every other `.py` file under
`specfuse/` except the mirrored data copy — this WU documents the predicate and
changes nothing about it. A class whose documented behavior would require a code
change to be true is an escalation, not an edit. `docs/methodology.md` (T10
owns §9). `docs/concepts/adopting-auto-mode.md` (T12 owns it). Pre-existing
entries in the docs index and in the drift guard's `DOCS_TRACKED` set: append
your one entry to each and leave every other line byte-identical — this WU adds
to those two lists and restructures neither. `.specfuse/rules/`. `RETROSPECTIVE.md` and the other feature-folder artifacts.
Generated directories, secrets, `.git/`. The driver owns all git — you edit
files only. See `.specfuse/rules/never-touch.md`.

**Verification.** The `code` set in `.specfuse/verification.yml`. Scoped
iteration run: `python3 -m unittest tests.test_scaffold_data_in_sync -v`, plus
the class-coverage assertion in criterion 1 run exactly as written.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if a
class's clearing action cannot be stated because the class has no operator-side
remedy — that is a design gap this page would otherwise hide, and it belongs in
front of a human. Emit `status: blocked` if `CLASS_NAMES` in the working tree
does not have eight entries: the documented set and the shipped set have then
diverged and the page would be written against the wrong contract.
