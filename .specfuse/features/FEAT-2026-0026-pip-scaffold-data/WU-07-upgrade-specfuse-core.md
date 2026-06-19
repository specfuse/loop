---
id: FEAT-2026-0026/T07
type: implementation
effort: high
status: draft
planned_cost_usd: 2.50
produces:
  - specfuse/loop/scaffold.py
  - tests/test_scaffold_upgrade.py
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# `specfuse upgrade` core — overlay versioned files onto an existing `.specfuse/`

**Objective.** Add `specfuse.loop.scaffold.upgrade_specfuse(target)` — the in-process core
that **overlays** the packaged versioned seed (`templates/`, `rules/`,
`verification.yml.example`, `VERSION`) onto an existing `.specfuse/`, **preserves**
user-authored files, **prunes** versioned files the current seed no longer ships, refreshes
the `.claude` wiring, stamps `VERSION`, and is **version-gated / never-downgrade**. This is
the upgrade counterpart of T04's `init_specfuse`; the umbrella `specfuse upgrade` CLI calls
it (the CLI itself is cross-repo — see GATE-03-REVIEW.md).

**Context.** This is `FEAT-2026-0026/T07`, gate 3 (terminal), depends on T04
(`init_specfuse`, `wire_claude`, `init`) + T02's resource API (`iter_scaffold_files`,
`read_scaffold`, `scaffold_version`). Parity target is `init.sh --upgrade` mode
(`init.sh:86-108` VERSIONED vs USER_AUTHORED split; `init.sh:448-475` overlay loop +
seed-if-missing). Two deliberate **divergences from init.sh** (resolved at draft — see the
review's contracts table, but treat as given here):

- The pip seed ships a **smaller versioned footprint** than init.sh. T01 packaged only
  `templates/`, `rules/`, `verification.yml.example`, `roadmap.template.md`,
  `LEARNINGS.template.md`, `VERSION`, `gitignore.snippet` — **no** `skills/`, `scripts/`,
  or `docs/` (the Claude Code plugin replaces skills; pip replaces vendored scripts). So
  this WU overlays only what the seed ships; it does **not** vendor `scripts/`/`skills/`.
- **Never-downgrade is new** — `init.sh` has no version gate. This WU adds one: refuse if
  the installed seed (`scaffold_version()`) is **older** than the target's
  `.specfuse/VERSION` (semver compare; both are `MAJOR.MINOR.PATCH`, e.g. `0.2.0`).

`wire_claude` is merge-safe and idempotent (T05) — reuse it to refresh `.claude`; do not
reimplement wiring. Pure stdlib, no `Path(__file__)` (resolve source bytes via T02's API
only). Ground in `.specfuse/rules/result-contract.md` and `.specfuse/rules/never-touch.md`.

**Red-test (§12):** `tests/test_scaffold_upgrade.py::test_upgrade_refuses_downgrade` fails
on HEAD (function absent) and passes after this WU; paired with
`test_upgrade_overlays_versioned_preserves_user`.

**Acceptance criteria.**

1. **Red test first.** `tests/test_scaffold_upgrade.py::test_upgrade_refuses_downgrade`
   exists and **fails on HEAD** before this WU's edits (import error / missing symbol).
2. `specfuse/loop/scaffold.py` gains
   `upgrade_specfuse(target: str | Path, *, ci_check: str | None = None) -> list[str]`
   that, against a target dir whose `.specfuse/` **already exists**:
   - overlays the versioned seed (`templates/`, `rules/`, `verification.yml.example`) from
     T02's resource API, overwriting those files in place,
   - stamps `.specfuse/VERSION` to `scaffold_version()`,
   - seeds any **missing** user-authored file from its template (`LEARNINGS.md`,
     `roadmap.md`, `verification.yml`, an empty `features/`) — mirrors `init.sh:467-475`,
   - refreshes the `.claude` wiring by calling `wire_claude(target)` (merge-safe),
   - returns the sorted list of relpaths written.
3. **Preserve user-authored.** Existing `LEARNINGS.md`, `verification.yml`, `roadmap.md`,
   and the `features/` tree are **never overwritten or deleted** — proven by a test that
   writes sentinel content into each before upgrade and asserts it is byte-unchanged after.
4. **Prune removed-versioned.** A versioned file present in the target but **not** in the
   current packaged seed's versioned footprint (`templates/`, `rules/`) is removed by the
   upgrade — proven by planting a stray `.specfuse/rules/obsolete.md` and asserting it is
   gone after. The prune is **scoped to the versioned footprint only**; it must not touch
   user-authored paths or any `.specfuse/scripts/` or `.specfuse/skills/` directory (the
   init.sh-legacy migration prune is out of scope — see escalation).
5. **Never-downgrade.** If the target's `.specfuse/VERSION` is **newer** than
   `scaffold_version()`, `upgrade_specfuse` raises a distinct, catchable error
   (e.g. `ScaffoldDowngradeError`) naming both versions; nothing is written. Equal or older
   target VERSION proceeds. Proven by a test that stamps a future VERSION and asserts the
   refusal + no-write.
6. **Byte-faithful overlay + no `__file__`.** Each overlaid versioned file byte-matches its
   `read_scaffold(relpath)` content (diffed against the resource API, not disk); a test or
   grep confirms no new `Path(__file__)`-relative reads in `scaffold.py`.
7. The red test (AC1) and `test_upgrade_overlays_versioned_preserves_user` pass after the
   edits; `code` gates stay green (coverage ≥ 90 on `specfuse/`).

**Do not touch.** This repo's own `.specfuse/` (tests write to `tmp_path`, never the repo
root); `specfuse/loop/data/` content (T01 owns it); the driver modules; T04's
`init_specfuse` / T05's `wire_claude` contracts beyond calling them; `init.sh` (T08 owns
the shim); secrets; `.git/`. The driver owns all git — edit files only. Do **not** add a
`specfuse` console script here (the umbrella CLI is cross-repo; see GATE-03-REVIEW.md).

**Verification.** `code` gates (tests incl. the new file, coverage ≥ 90, ruff, bandit); the
red→green proof (AC1, AC7); the preserve-user-authored test (AC3); the prune test (AC4); the
never-downgrade refusal + no-write test (AC5); the byte-faithful diff against `read_scaffold`
(AC6). Symbol-existence (§9): `python3 -c "from specfuse.loop.scaffold import upgrade_specfuse, ScaffoldDowngradeError"`.
See `.specfuse/skills/verification/SKILL.md`.

**Escalation triggers.** **(a)** If `.specfuse/VERSION` is malformed or absent in the
target (not a clean `MAJOR.MINOR.PATCH`), the never-downgrade compare is undefined — emit
`status: blocked` naming the unparseable value rather than guessing a compare order or
silently overwriting. **(b)** The **init.sh-legacy migration prune** — whether
`upgrade_specfuse` should delete a target's vendored `.specfuse/scripts/` and
`.specfuse/skills/` symlinks left by a pre-pip `init.sh` — is a **migration-semantics
decision the loop must not make unilaterally**. Keep AC4's prune scoped to the versioned
footprint only and flag the legacy-prune question for the close; do **not** rm those
directories in this WU. **(c)** If `roadmap.template.md` / `LEARNINGS.template.md` are
absent from the packaged seed, emit `status: blocked` naming the missing seed file rather
than inventing seed content.
