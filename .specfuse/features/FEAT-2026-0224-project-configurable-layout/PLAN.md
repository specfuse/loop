---
feature_id: FEAT-2026-0224
title: Project-configurable layout (decisions)
slug: project-configurable-layout
branch: feat/FEAT-2026-0224-project-configurable-layout
roadmap_goal: A project can declare where and how it records decisions in an optional `.specfuse/layout.yml`, and every loop surface that builds or checks a decision link follows it, with behaviour byte-identical when the file is absent
autonomy_default: auto
status: active
planned_cost_usd: 24.00
---

# Plan: Project-configurable layout (decisions)

Specfuse hardcodes where it reads and writes. In `loop` the whole problem is
decisions: `block-feature` and five other skills tell a project that a blocker is
"an ADR", build `docs/adr/…` links for it, and `lint_roadmap` checks every
Blocked-by link with `(doc.path.parent / href).exists()`, so a fragment link such as
`decisions.md#D-0007` fails as a missing file. A project that edits those files
locally loses the edit on the next `specfuse upgrade` or plugin update.

This feature adds an optional `.specfuse/layout.yml` with only a `decisions:` block,
a resolver module (`specfuse.loop.layout`) that owns the defaults, path validation
and the one link render-and-check function, and makes `lint_roadmap`,
`block-feature`, the roadmap template and the blocker wording in five skills and two
docs follow it. With no file, or with the block omitted, behaviour is today's —
proven by goldens on the deterministic surfaces, recorded before any consumer
changes.

## Decisions (interview, 2026-10-27)

Items marked *operator* were answered explicitly; items marked *recommendation*
were taken as proposed and confirmed by the operator.

1. **One gate** (*operator*). The roadmap entry sketched two gates (foundation,
   then decision-style support). This feature has 7 substantive units, under the
   12-unit threshold in `docs/methodology.md` §6, and the roadmap entry already pins
   every gate-2 surface, so a `close-intermediate` + `plan-next` would discover
   nothing. Same correction FEAT-2026-0204 made.
2. **The umbrella `specfuse layout get` entry is a post-merge follow-up**
   (*operator*). It lives in the sibling `specfuse/specfuse` repo
   (`DELEGATED_COMMANDS` in `specfuse/cli.py`), which the driver cannot dispatch to
   (`[FEAT-2026-0028/G2]`), and its target `specfuse.loop.layout:main` exists for
   installed users only after a loop release. In this feature the interface is
   `python3 -m specfuse.loop.layout`, and every criterion invokes it from source
   (`[FEAT-2026-0056/G1-CLOSE-INTERMEDIATE]`). The close names the umbrella entry under
   "what the loop did NOT verify".
3. **Autonomy `auto`** (*operator*, over a recommendation of `review`). T01 registers
   `layout.py` in `arm_eval.py`'s non-judge module registry (enforced by
   `tests/test_judge_path_registry.py`), and `arm_eval.py` is itself a judge module,
   so the `judge_editing` stop class is **expected to fire** and veto the auto arm.
   That halt is anticipated, not a defect; the operator reviews the registry entry
   when it fires.
4. **Location containment only when `decisions:` is declared** (*recommendation*).
   With no layout the default location (`docs/adr`) is not enforced, so an existing
   project's Blocked-by link outside `docs/adr` stays green (Definition of done 1).
5. **Fragment stripping applies always** (*recommendation*). Today `x.md#frag` is a
   false "does not resolve" error even with no layout; after T05 the file is checked
   and then the anchor. This is a findings change for existing projects (a false
   error becomes a correct check), recorded in `CHANGELOG.md`; the T04 golden
   fixtures carry no fragment links, so the goldens still prove "no layout =
   today".
6. **What counts as an anchor** (*recommendation*): an explicit `<a id="…">` or
   `<a name="…">`, or the GitHub heading slug of a heading, matched exactly. An
   entries heading `## D-0007 — title` slugs to `d-0007--title`, so a link to
   `#D-0007` needs an explicit anchor.
7. **Per-style defaults** (*recommendation*, fixed so goldens are deterministic):
   `style: adr`, `location: docs/adr`, `link: "{path}"` (the repo-relative path the
   operator supplies, today's `block-feature` behaviour); an `entries` style with no
   `location` defaults to `docs/decisions` and with no `link` to
   `{location}/decisions.md#{id}`. Placeholders: `{location}`, `{path}`, `{id}`,
   `{domain}`; any other placeholder is a validation error.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:**
  `grep -rnE "is_relative_to|isabs|is_absolute\(\)" specfuse/loop/*.py`,
  `grep -rn "layout" specfuse/loop/*.py`,
  `grep -n "_LINK_RE|_REF_RE|exists()" specfuse/loop/lint_roadmap.py`, and the
  replaced-wording grep `grep -rnE "ADR" docs plugins specfuse/loop/data README.md`
  (excluding `docs/adr/` and CHANGELOG), per `[FEAT-2026-0110/G1]`.
- **Verdict:** `no existing layout config or repo-path validator, building new; found the Blocked-by link check, extending`
- **If reusing:** `specfuse/loop/lint_roadmap.py:397` — the Blocked-by file check
  (`target = (doc.path.parent / href).resolve()`), which T05 extends with fragment
  stripping, anchor and location checks; `_find_anchors` (line 145) only recognises
  `feat-NNNN-NNNN` anchors, so T05 adds a general anchor reader rather than widening
  it. The only path-containment helper is `loop._is_relative_to` (`loop.py:10580`),
  private to the driver; `layout.py` must not import `loop.py`, so it carries its own.
  `decisions_format.py` parses a feature's `DECISIONS.md`, a different artifact from a
  project's decision records; not reused.
- **Wording surfaces** the grep found: the roadmap template (both copies),
  `block-feature`, `attention`, `gate-status`, `groom-backlog`, `pick-feature`,
  `roadmap-add` (both copies each), and `docs/methodology.md:29`, `docs/skills.md:52`,
  which the roadmap entry did not list.

## Escalation-predicate satisfiability (§2)

`lint_roadmap` gains new ERROR findings (missing anchor; target outside
`decisions.location`) and `layout.validate()` new ERRORs (invalid path forms, unknown
style or placeholder). **What does each report on an input already in its intended
final state?** Zero: a roadmap with no layout file reports exactly HEAD's findings
(T04 goldens, decisions 4 and 5), and this repo's own roadmap (no `layout.yml`)
stays green under `roadmap-link-gate`. The `paths:` finding is WARN, which that gate
deliberately does not fail.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0224/T01
        file: WU-01-layout-walking-skeleton.md
        depends_on: []
      - id: FEAT-2026-0224/T02
        file: WU-02-layout-validation.md
        depends_on: [FEAT-2026-0224/T01]
      - id: FEAT-2026-0224/T03
        file: WU-03-link-function.md
        depends_on: [FEAT-2026-0224/T01]
      - id: FEAT-2026-0224/T04
        file: WU-04-no-layout-goldens.md
        depends_on: [FEAT-2026-0224/T01, FEAT-2026-0224/T03]
      - id: FEAT-2026-0224/T05
        file: WU-05-lint-roadmap-decision-links.md
        depends_on: [FEAT-2026-0224/T02, FEAT-2026-0224/T03, FEAT-2026-0224/T04]
      - id: FEAT-2026-0224/T06
        file: WU-06-block-feature-uses-link.md
        depends_on: [FEAT-2026-0224/T03]
      - id: FEAT-2026-0224/T07
        file: WU-07-template-and-blocker-wording.md
        depends_on: [FEAT-2026-0224/T03, FEAT-2026-0224/T04]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-2026-0224/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0224/T01, FEAT-2026-0224/T02, FEAT-2026-0224/T03, FEAT-2026-0224/T04, FEAT-2026-0224/T05, FEAT-2026-0224/T06, FEAT-2026-0224/T07]
```

## Scope boundary

**In:** `.specfuse/layout.yml` with a `decisions:` block (`style: adr | entries`,
`location`, `link`); `specfuse.loop.layout` (load, defaults, path validation,
`get` / `check` / `link` subcommands, the link render-and-check function);
`lint_roadmap` fragment, anchor and location checks plus layout findings;
`block-feature`; the roadmap template rendered through the layout at seed time; the
blocker wording in five skills and two docs; every change in all copies
(`plugins/specfuse/skills/` and `.specfuse/skills/`;
`specfuse/loop/data/roadmap.template.md` and `.specfuse/roadmap.template.md`).

**Out:**
- **`paths:` keys** and their authoring consumers, and a reusable literal-path audit
  — the authoring follow-up, which must call the resolver without making
  `specfuse-authoring` depend on `loop` by accident. A `paths:` block is a WARN here.
- **The umbrella `specfuse layout get` entry** (decision 2) — post-merge.
- **Generator scenario-test assertions on `x-async.emit`** (clabonte/generator#2971).
- **The `block-feature` vs lint tension** on a not-yet-written ADR file (the skill
  says do not require it to exist; the lint errors on a missing file). Unchanged.
- Reading decision approval state from a decision record.

## Post-merge checklist

- **Umbrella delegated command.** After a loop release containing
  `specfuse.loop.layout`, open a PR in `specfuse/specfuse` adding
  `"layout": ("specfuse.loop.layout:main", "specfuse-layout", "resolve the project's layout.yml")`
  to `DELEGATED_COMMANDS` in `specfuse/cli.py`, raise the umbrella's loop floor to
  that release, publish, and confirm `specfuse layout get decisions.style` prints
  `adr` in a project with no `layout.yml`.
- **One entries-style project.** In a consumer repo that records decisions as
  entries, add a `layout.yml`, run `/block-feature` on one feature, and confirm the
  rendered link passes `roadmap-link-gate`.
