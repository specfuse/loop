---
feature_id: FEAT-2026-0110
title: Language-aware narrow test selection
slug: language-aware-narrow-selection
branch: feat/FEAT-2026-0110-language-aware-narrow-selection
roadmap_goal: A project whose tests are not Python under tests/ can narrow its per-attempt tests gate, instead of silently paying the full suite on every attempt.
autonomy_default: review
status: active
planned_cost_usd: 15.00
---

# Plan: Language-aware narrow test selection

FEAT-2026-0109 gate 2 made the per-attempt `tests` gate run a unit-scoped
command through `narrow_command` and `{selected_test_modules}`. Both halves of
the selection it substitutes are Python-and-`tests/`-shaped:
`select_narrow_test_modules` keeps only `produces:` entries starting with
`tests/`, and `_test_module_name` converts them to dotted unittest module names.

A Maven or Gradle project keeps tests under `src/test/java/...`; a JS project
under `__tests__/` or `*.test.ts`. None of those start with `tests/`, so the
selection is always empty, the fail-safe fallback runs the gate's full
`command`, and gate 2 delivers nothing there. Measured in one Maven consumer:
driver-side verification is 8 to 11 minutes per attempt — a third to a half of
each attempt — across roughly 47 full-suite runs per feature (#3281, from the
2026-09-09 review of that consumer's `events.jsonl`).

This feature makes the selector configurable through `verification.yml` while
keeping the fail-safe: an empty or unresolvable selection still falls back to
the gate's full `command`, never to an empty run.

**Why four keys and not the issue's one.** #3281 proposed `test_roots` and
`format`. That covers Maven (`-Dtest=A,B`) only if the joined list can use a
comma, and it cannot express Gradle at all — Gradle wants a *repeated flag*
(`--tests A --tests B`), which no join character produces. So the render is
split in two: `item_template` renders each selected test, `separator` joins
them. Today's behaviour is the default of both, so nothing moves for a project
that declares neither.

**Why this repo's `verification.yml` is not edited.**
`[FEAT-2026-0019/G1]` records that a feature which migrates the verification
harness the driver itself runs cannot be decomposed into separately-gated WUs:
each WU's exit oracle is the very surface being migrated, so no WU can pass
alone. The named trigger is "if a WU edits `verification.yml`, the test loader,
or how the driver's own code is imported." This feature avoids that entirely —
the defaults (`test_roots: ["tests/"]`, `format: python_module`,
`item_template: "{module}"`, `separator: " "`) reproduce the current behaviour
byte-for-byte, so this repo's `tests` gate needs no declaration and every WU
keeps a working oracle.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n '"tier"\|get("tier")\|tier ==' specfuse/loop/loop.py`
  and `grep -n "def .*validate.*gate\|ALLOWED_GATE_KEYS\|unknown key" specfuse/loop/loop.py`
- **Verdict:** found `resolve_gate_tiers`, reusing its *shape*; no generic
  gate-key validator exists, so T02 builds the refusal new.
- **Detail.** `resolve_gate_tiers` is the precedent for reading an optional
  per-gate key with an absent-key default that preserves prior behaviour — its
  docstring states the rule this feature copies: "An entry declaring no `tier`
  key runs in BOTH tiers — the absent-key default that keeps a
  `verification.yml` with no tier declarations anywhere byte-identical to
  today." The second grep returned nothing: there is no shared validator for
  unknown or malformed gate keys, so T02's `CONFIGURATION ERROR` follows the
  existing per-site convention (`loop.py:173`, `loop.py:462`, and the
  `feature_oracle` refusal) rather than extending a mechanism that does not
  exist.

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

- **What does the rule report on an input already in its intended final state?**
  Zero. T02's only refusal fires on an *unknown* `format` value. A
  `verification.yml` that declares no `narrow_selection` at all, or declares one
  with a known format, reports nothing — verified by the whole existing gate
  corpus, none of which declares the key. This feature raises no existing check
  to `ERROR` and asserts no "zero issues" close predicate.

## Task graph

```yaml
# Single gate, single terminal close: 3 substantive WUs is under the ceremony
# proportionality threshold (docs/methodology.md §6), so no close-intermediate
# and no plan-next.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0110/T01
        file: WU-01-narrow-selection-config.md
        depends_on: []
      - id: FEAT-2026-0110/T02
        file: WU-02-formats-and-refusal.md
        depends_on: [FEAT-2026-0110/T01]
      - id: FEAT-2026-0110/T03
        file: WU-03-document-the-contract.md
        depends_on: [FEAT-2026-0110/T02]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0110/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-2026-0110/T01, FEAT-2026-0110/T02, FEAT-2026-0110/T03]
```

## Scope boundary — explicitly OUT

- **The changed-file half stays disabled and `tests/`-shaped.**
  `select_tests_for_changed_files` ships behind
  `CHANGED_FILE_SELECTION_ENABLED = False`, and nothing writes
  `.specfuse-changed-file-test-map.json` yet, so code keyed on the new
  `test_roots` there could not be exercised end to end — its acceptance
  criteria would land in the close's "what the loop did NOT verify" list rather
  than being proven. **The contract for whoever enables it:** the map must key
  on the same `test_roots` this feature adds, or a non-Python project will
  narrow on its declared half and silently fall back on its changed-file half.
- **This repo's `.specfuse/verification.yml` is not edited** — see the framing
  above.
- **No consumer repository is edited.** The Maven example in #3281 is a fixture
  in this repo's tests, not a change to the consumer that reported it.
- **No new measurement of the consumer's wall clock.** The 8–11 min/attempt
  figure is #3281's, already measured; re-measuring it needs that consumer's
  repo and is a post-merge observation, not an in-loop acceptance criterion.

## Post-merge checklist

Observable only outside this repository, so filed as a post-merge observation
rather than an acceptance criterion (`close-discipline.md` §2). Gate 1 verified
that the resolved command *strings* are correct; it could not verify that the
runners accept them or that narrowing recovers the wall clock #3281 measured,
because neither is measurable here.

- [ ] In the Maven consumer that reported #3281, declare `narrow_selection` on
      its `tests` gate (`test_roots: ["src/test/java/"]`, `format: class_name`,
      `separator: ","`) and confirm `./mvnw test -Dtest=...` is accepted by the
      runner and selects the expected classes.
- [ ] Over one feature's worth of attempts in that consumer, compare per-attempt
      driver-side verification wall clock against the 8–11 minutes recorded in
      #3281's 2026-09-09 review of its `events.jsonl`, and record the delta on
      that issue. A narrowed attempt that still falls back to the full command is
      the failure mode to watch for — it means the declared `test_roots` do not
      match where that project's `produces:` entries actually point.
- [ ] Confirm the Gradle (`item_template: "--tests {module}"`) and JS
      (`format: path`) shapes against a real `./gradlew` and `jest` invocation in
      any consumer that adopts them. This repository has no JVM or Node toolchain
      and asserted string equality only.

## Notes

- Dependencies live here, not in WU frontmatter.
- T01 is the walking skeleton: it wires the thinnest end-to-end path and turns
  the gate's `feature_oracle` green. Stubs are permitted in T01 and nowhere
  else in this gate.
