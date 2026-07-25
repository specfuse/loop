---
feature_id: FEAT-2026-0039
title: Monitoring schema + derive-monitoring skill
slug: monitoring-schema
branch: feat/FEAT-2026-0039-monitoring-schema
roadmap_goal: Ship a declarative `.specfuse/monitoring.yml` schema with a committed structural validator, a seeded design-for-diagnosis rule, and the `derive-monitoring` skill that drafts a project's monitoring config from repo evidence — so the harvester CLI (FEAT-2026-0040) is built against a contract that is already machine-checkable rather than one that is only described in prose.
autonomy_default: review
status: active
planned_cost_usd: 34.00
---

# Plan: Monitoring schema + derive-monitoring skill

`verification.yml` declares how a project proves a change is correct **before** it
merges. Nothing in the scaffold declares how a project notices that a deployed
component is misbehaving **after** it ships. This feature adds that second
declarative surface — `monitoring.yml` — plus the skill that drafts one from repo
evidence, and the rule that says what a component must do to be diagnosable in the
first place.

The ordering matters. FEAT-2026-0040 builds the harvester CLI that reads this
schema; FEAT-2026-0041/0042 build diagnosis and autofix on top of that. All three
are currently `blocked` on this feature. The roadmap's justification for landing
the schema first is that it "keeps the harvester purely additive" — a promise that
is only checkable if the schema has a validator, which is why this feature ships
one rather than a prose specification alone.

## Scope boundary

**IN.** The `monitoring.yml` schema and its structural validator
(`specfuse/loop/lint_monitoring.py` + `.specfuse/scripts/` shim), the shipped
`.specfuse/monitoring.yml.example` and its reference doc, scaffold seeding and gate
wiring, the design-for-diagnosis rule, the `derive-monitoring` skill with its
discovery reference implementation and fixture, and the local bootstrap artifacts
the skill drafts (a gitignored local-overrides example and a read-only secrets
checklist).

**OUT — owned by FEAT-2026-0040.** The harvester CLI itself, the telemetry and
broker provider adapters, fingerprinting, redaction of harvested artifact text,
and GitHub issue lifecycle. This feature defines the neutral vocabulary those
adapters normalize into; it implements none of them.

**OUT — moved to FEAT-2026-0040, narrowing the roadmap's stated scope.** The
GitHub Actions runner workflow. The roadmap listed it under this feature's
deliverable (c), but that workflow's body invokes `specfuse-monitor run`, a CLI
that does not exist until 0040. Shipping a workflow template whose entry point is
a nonexistent binary is the `[FEAT-2026-0029/G1-CLOSE]` failure verbatim — a WU
authoring a consumer for an artifact that exists nowhere, which cost a dispatch to
rediscover. The workflow lands in 0040 where its binary is real. This feature
still ships the local-runner bootstrap artifacts, so the "interview ends, first
`--dry-run` is minutes away" property survives for local runs.

**OUT — post-merge operator work, by construction.** The live run of
`derive-monitoring` against a real multi-component backend. The skill is
interactive and its target is a different repository: a dispatched WU has neither
the human channel the interview needs nor commit access to the target. Gate 2's
close declares this explicitly under `## What the loop did NOT verify`; the in-loop
substitute is a repo-tree fixture (see the verification note below).

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

```
grep -rniE "monitor" specfuse .specfuse/scripts docs -l   -> 0 hits
grep -rniE "adapter|provider" specfuse -l                 -> 0 hits
ls .specfuse/schemas/                                     -> event.schema.json, events/
```

**Verdict: no existing mechanism, building new.** Nothing in the driver or the
scaffold declares, validates, or reads post-deploy monitoring configuration. The
nearest relatives were read and classified:

- **Reused, not rebuilt:** `specfuse/loop/_miniyaml.py` — the repo's in-house YAML
  parser for the documented subset. The package has zero runtime dependencies
  (`pyproject.toml`), so `monitoring.yml` is parsed by `_miniyaml`, never PyYAML.
- **Pattern borrowed:** `specfuse/loop/lint_plan.py` already validates the
  scaffold's structural files and already reads `verification.yml`
  (`lint_plan.py:176`). `lint_monitoring.py` is its sibling, not an extension of
  it — the two validate unrelated artifacts and coupling them would drag PLAN
  linting into monitoring's failure modes.
- **Pattern borrowed:** `tests/test_roadmap_add_skill.py` and
  `tests/test_roadmap_archive_skill.py` are this repo's established shape for
  testing an interactive skill — a reference implementation of the skill's
  deterministic algorithm, unit-tested. Gate 2's discovery WU follows it.
- **Seeding precedent:** `scaffold.py`'s `_SEED_RENAME` maps
  `verification.yml.example -> verification.yml` because gates are mandatory.
  Monitoring is opt-in, so `monitoring.yml.example` seeds **without** a rename;
  adding a rename entry would auto-create a live monitoring config in every
  scaffolded project, including the ones that deploy nothing.

## Escalation-predicate satisfiability (mandatory — §2)

This feature adds a new blocking `code` gate, so the question applies: **what does
the validator report on a tree already in its intended final state?**

**Zero — and the reason needs stating, because the obvious wiring gets it wrong.**
This repository is a CLI tool. It has no deployable components and will never carry
a live `monitoring.yml`. So the gate cannot be "validate this repo's
`monitoring.yml`": that gate would either fail permanently on an absent file, or
pass vacuously forever and provide no signal.

The gate therefore validates **`.specfuse/monitoring.yml.example`** — the artifact
this feature actually ships. A correct example reports zero findings, and the gate
has real signal: the example cannot silently drift from the validator. Two
consequences are binding on T01 and T03:

1. **An absent `monitoring.yml` is not an error.** `validate_monitoring` on a
   missing file returns an empty finding list, and the CLI exits 0. Monitoring is
   opt-in; a project that has not configured it is in a correct final state.
2. **Target projects get the gate commented out** in `verification.yml.example`,
   pointing at their own `monitoring.yml`. An uncommented gate would fail every
   freshly-scaffolded project on day one.

A related severity question belongs to gate 2 and is recorded here so `plan-next`
does not have to rediscover it: the skill's **diagnosability audit produces gap
findings, and those are WARN, never ERROR**. A populated codebase that predates the
design-for-diagnosis rule will violate it everywhere by construction — an ERROR
there is unsatisfiable on real input, and LEARNINGS already records the general
form (`[FEAT-2026-0015/G2-CLOSE]`: lint surfaces introduced into a populated
codebase default to WARN).

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0039/T01
        file: WU-01-monitoring-schema-validator.md
        depends_on: []
      - id: FEAT-2026-0039/T02
        file: WU-02-monitoring-example-and-schema-doc.md
        depends_on: [FEAT-2026-0039/T01]
      - id: FEAT-2026-0039/T03
        file: WU-03-shim-seed-and-gate-wiring.md
        depends_on: [FEAT-2026-0039/T02]
      # --- non-terminal gate: close-intermediate then plan-next ---
      - id: FEAT-2026-0039/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on: [FEAT-2026-0039/T01, FEAT-2026-0039/T02, FEAT-2026-0039/T03]
      - id: FEAT-2026-0039/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0039/G1-CLOSE-INTERMEDIATE]

  - gate: 2
    file: GATE-02.md
    work_units:
      # Substantive WUs are drafted by G1-PLAN and inserted BEFORE this close.
      - id: FEAT-2026-0039/G2-CLOSE
        file: WU-92-gate-2-close.md
        depends_on: []
```

## Gate 2 sketch (for `plan-next`, not binding)

Gate 1's `plan-next` refines this against what gate 1 actually shipped. Definition
of done: an operator can run `/derive-monitoring` and get a drafted
`monitoring.yml` that passes gate 1's validator.

- The design-for-diagnosis rule → `.specfuse/rules/design-for-diagnosis.md`,
  **seeded into scaffolded projects but NOT `@`-imported into `CLAUDE.md`**. It
  governs how the target application's code is written (correlation IDs, structured
  logging, per-component role names, DLQ error-context capture), not how a work
  unit executes — so it is reference-only, the same posture as
  `planning-discipline.md` and `close-discipline.md`, which sit in
  `.specfuse/rules/` unimported. Importing it would tax every session in every
  downstream project for a rule most sessions never consult.
- Component-discovery reference implementation + repo-tree fixture + tests, per the
  `test_roadmap_add_skill.py` pattern. The fixture asserts the **neutral** contract
  — evidence patterns produce neutral component records — with one stack's patterns
  as input. Nothing stack-specific may leak into the core; that is the same
  boundary the provider adapters enforce in 0040.
- The `derive-monitoring` skill: canonical copy in `plugins/specfuse/skills/`,
  synced to `.specfuse/skills/`. **The `.claude/skills/` discovery symlink is an
  operator prerequisite, not agent work** — Claude Code's sandbox lists
  `.claude/skills` under `denyWithinAllow`, a deny rule inside an allow scope that
  survives `unsandboxed: true` (`[FEAT-2026-0016/G3-CLOSE]`). A WU that tries will
  burn an attempt rediscovering it.
- A fenced-block drift test: every `yaml` block in the skill and in the bootstrap
  artifacts is extracted and run through `lint_monitoring`, so no example anywhere
  can drift from the schema.

## Notes

- **Multi-gate (7 substantive WUs > 4)** — full ceremony per
  `docs/methodology.md §6`. Gate 1 is non-terminal (`close-intermediate` +
  `plan-next`); gate 2 pre-declares its terminal `close` so the linter reads the
  last gate as non-empty and gate 1 as non-terminal.
- **Secrets are structural here, not incidental.** Monitoring config names
  telemetry workspaces, broker namespaces, and the credentials to read them. The
  schema admits credentials **by environment-variable name only** — an inline
  connection string or instrumentation key is a validator finding, not a style
  preference. Every example uses placeholder organization and host names;
  `.specfuse/rules/security-boundaries.md` and the `leak-scan` gate both bite on
  this surface.
- **Provider-agnostic by construction.** Check types (`dlq`, `error-logs`,
  `http-5xx`, `heartbeat`, `invariant`) are neutral concepts and environments carry
  typed provider bindings. The validator must be expressible without importing a
  single vendor-specific concept — T01 escalates rather than special-casing one, because
  that boundary is what makes 0040's adapter interface possible.
- **Cost note.** `planned_cost_usd` totals $34: gate 1 at $18 (T01 $3.00, T02
  $2.50, T03 $2.50, two planning WUs at the $5.00 floor from
  `planning-discipline.md` §5), gate 2 sketched at ~$16.
- **The local-overrides file is NOT named with a `.local.` segment.** The roadmap's
  detail section proposed one, but this repo's `leak-scan` pre-commit hook classifies
  any `<word>.local` token as a private-host finding and rejects the commit — it fired
  on this PLAN's first commit attempt. `leak_scan.py --all` (the CI oracle) passes the
  same token, so this is the documented stricter-hook asymmetry, not a real leak. The
  durable fix is the filename, because the driver commits every WU squash **without**
  `--no-verify`: any gate-2 WU whose diff contains the token would be rejected three
  times and block on `spinning_detected`. Gate 2 picks a name with no `.local.`
  segment (`monitoring.overrides.yml` unless it finds a better one) and records the
  choice.
- **Expected lint WARN until gate 1 closes.** `lint_plan.py` compares this
  feature-level $34 against the sum of *existing* WU `planned_cost_usd` values
  ($23) and warns at a 32% delta. That gap is structural, not an estimating error:
  gate 2's substantive WUs do not exist yet — `G1-PLAN` drafts them, and the sum
  converges once it does. The feature-level figure is deliberately left honest
  rather than trimmed to silence the warning, because the terminal close reconciles
  actual spend against it and an understated plan would make gate 2's real cost read
  as an overrun.
