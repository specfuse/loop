---
id: FEAT-2026-0072/T02
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
produces:
  - scripts/sync-scaffold.sh
  - tests/sync_scaffold_symlinks.bats
  - .specfuse/verification.yml
model: sonnet
effort: medium
gate_set: code
driver_version: 0.5.0
started_at: 2026-07-28T15:20:47.378888+00:00
duration_seconds: 233.983
cost_usd: 0.623554
input_tokens: 1681
output_tokens: 9754
---

# Make sync-scaffold.sh create the discovery links it currently only documents

**Objective.** Teach `scripts/sync-scaffold.sh` to create any missing
`.claude/skills/` forward symlink, so the contract it documents is the contract it
enforces.

**Context.** Correlation ID `FEAT-2026-0072/T02`. Depends on `T01`, whose guard
defines the invariant this script must satisfy.

The script already references the symlinks twice — lines 24 and 96 — and both are
**comments describing a contract it does not enforce**:

> `#      loop operates on .specfuse/skills/ (via .claude/skills forward symlinks);`

That gap is #284: the links were created once by hand in June and nothing has made
one since, so every skill added in seven weeks was invisible to discovery.

**Create only what is missing, and only forward links.** An existing entry is left
exactly as found — never replaced, never re-pointed. Entries resolving outside
`.specfuse/skills/` (the seven `.agents/skills/` operator-tooling links) are not
this script's business and must not be touched or removed.

**Operator-script rules apply (`/authoring-work-units` §11).** This is a committed
executable humans run, so its acceptance carries `shellcheck` clean, `bash -n`
parses, and a bats happy-path test with external commands stubbed. Both tools are
available locally. `shellcheck` is **not** in `verification.yml`'s gate set, so
name it as a unit-specific check in Verification rather than assuming the gates
cover it.

**Register the new bats suite.** `tests/test_bats_suites_gated.py` (#257) fails
when a `tests/*.bats` file is run by no gate. Adding
`tests/sync_scaffold_symlinks.bats` without a matching `verification.yml` entry
will fail the `tests` gate. That is the precedent guard doing its job on this
feature's own work — add the gate entry in the same WU.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/sync_scaffold_symlinks.bats` exists and its first test **fails on HEAD
   before this WU runs** (the file does not yet exist, which counts as red).
2. Running `scripts/sync-scaffold.sh` in a fixture tree where a skill directory
   exists under `.specfuse/skills/` with no `.claude/skills/` entry creates a
   symlink for it whose resolved target is that directory.
3. Running it where the entry already exists leaves that entry byte-identical —
   same link target, not recreated.
4. An entry in `.claude/skills/` whose target resolves **outside**
   `.specfuse/skills/` is neither modified nor removed.
5. The script is idempotent: a second consecutive run creates nothing and exits
   zero.
6. `shellcheck scripts/sync-scaffold.sh` exits zero.
7. `bash -n scripts/sync-scaffold.sh` exits zero.
8. `.specfuse/verification.yml` gains an entry running
   `bats tests/sync_scaffold_symlinks.bats`, with a comment naming what it guards.
9. `python3 -m pytest tests/test_bats_suites_gated.py -q` exits zero — the new
   suite is registered, and the #257 guard confirms it.
10. `python3 -m pytest tests/test_skill_discovery_links.py -q` exits zero — T01's
    invariant still holds after the script change.
11. `bats tests/sync_scaffold_symlinks.bats` exits zero.
12. `bats tests/sync_scaffold.bats` exits zero — the pre-existing suite for this
    script is unbroken.

**Do not touch.** `tests/test_skill_discovery_links.py` — T01 owns it; this WU
satisfies it. `tests/test_bats_suites_gated.py`. The vendoring logic in
`sync-scaffold.sh` beyond adding the symlink step — this WU adds a capability and
changes nothing about which files are vendored. Real entries under
`.claude/skills/` — the bats tests operate on fixture trees under a temp dir, not
on the live one. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set: `tests`, `lint`, `security`, `coverage`
(≥90%), `leak-scan`. Plus §11's operator-script checks in criteria 6 and 7
(`shellcheck` is not a declared gate — run it explicitly), the bats runs in
criteria 11 and 12, and the two Python guards in criteria 9 and 10.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
`shellcheck` reports a finding that cannot be fixed without restructuring logic
this WU does not own — report it rather than adding a blanket `# shellcheck
disable`; the bats fixture cannot create a temp tree because `mktemp -d` is denied
in the execution environment; or adding the symlink step breaks
`tests/sync_scaffold.bats`. If `scripts/sync-scaffold.sh` is absent from the files
you edited, emit `status: blocked` — do not claim complete.
