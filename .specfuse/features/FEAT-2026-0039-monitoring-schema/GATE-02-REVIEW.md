# Gate 2 review — the derive-monitoring skill (drafted, unarmed)

Written by `FEAT-2026-0039/G1-PLAN`. Five substantive WUs drafted at
`status: draft`; nothing is armed. The human reviews this document, accepts /
revises / rejects each WU, and arms at the gate boundary (`/arm-gate`).

This review is deliberately weighted toward doubt. The decisions are in §1, the
verification story per WU in §2, and the things gate 2 **will not** prove in §3.
§3 is the part worth reading twice.

---

## 0. Escalation checks cleared before drafting

`WU-91`'s escalation triggers named two conditions that would have made drafting
worthless. Both were checked against the shipped code, not against `PLAN.md`'s
description of it.

**Schema drift — cleared.** `PLAN.md`'s gate-2 sketch assumes gate 1 shipped a
schema with typed provider bindings, per-component dials, and a neutral check-type
set. `specfuse/loop/lint_monitoring.py` ships exactly that:
`RUNNER_VALUES = {local, gh-actions, in-cluster}`,
`DIAGNOSE_VALUES = {manual, auto}`, `AUTOFIX_VALUES = {off, on}`,
`CHECK_TYPES = {dlq, error-logs, http-5xx, heartbeat, invariant}`,
`HARVEST_MODE_VALUES = {peek, quarantine}`,
`REQUIRED_COMPONENT_FIELDS = (name, type, runner, diagnose, autofix, checks)`,
`REQUIRED_PROVIDER_BINDINGS = (telemetry, broker)`. The sketch and the shipped
enums agree field for field. No drift; drafting proceeded.

Two shipped details the sketch did not state, now carried into the WUs because
each is an attempt-burner:

- `validate_monitoring` takes a **path**, not a string. T08's extractor must write
  each block to a `tempfile` before validating. Named in T08's body.
- `autofix` must be **quoted** in emitted YAML — `_miniyaml` does not accept the
  bare `off`/`on` spellings, and `AUTOFIX_VALUES` holds the strings. Named in T05
  (AC10) and T07.
- Component `type` is **not** enum-constrained by the validator — only its presence
  is checked. So discovery is free to propose `http-service` / `queue-consumer`
  style strings without a schema change, which is what T05 does.

**Discovery factorability — cleared.** The second trigger was "block if discovery
cannot be factored into a deterministic, testable reference implementation at all."
It can, and the split is clean: `discover_components` (tree + injected pattern
table → neutral records), `suggest_checks` (record → conservative check list), and
`audit_diagnosability` (tree → WARN findings) are all pure functions of their
inputs. What genuinely needs model judgment is confined to the *interview* — naming
components the operator would recognise, and the `invariant` queries, which T05
explicitly forbids the algorithm from inventing. That is the honest boundary, and
§3(c) says what it costs.

---

## 1. Decisions and rationale

### 1.1 Five WUs, not four — the bootstrap artifacts split out

`WU-91` left this call to this WU. **Split**, as T06, for three reasons:

1. **Different surface, different failure modes.** T07 touches
   `plugins/specfuse/skills/` + the vendoring path + `docs/skills.md`. T06 touches
   `specfuse/loop/data/`, `sync-scaffold.sh`'s `FILES`, three Python test manifests,
   a bats fixture, and `gitignore.snippet` — scaffold plumbing, with an
   enumerated-list failure mode T07 does not share. Merged, one WU carries two
   unrelated ways to go red and its `produces:` list stops being diagnosable.
2. **Ordering forces it.** T07's skill text points at
   `monitoring.overrides.yml.example` by name. If the artifact does not exist when
   the skill is written, T07 authors a consumer for something that exists nowhere —
   the `[FEAT-2026-0029/G1-CLOSE]` failure `PLAN.md` already paid for once and
   explicitly cites when moving the GitHub Actions workflow out of scope. T06 before
   T07 makes the reference real.
3. **T08 needs both done.** The drift test's declared surface list spans T06's and
   T07's outputs. With both as separate `done` WUs, T08's `depends_on` is honest;
   merged, T08 would depend on a WU that is half its own oracle.

Cost of the split: one more dispatch (~$2.00), one more squash. Accepted.

### 1.2 T04 → T06 dependency is about shared lists, not logic

T04 and T06 have no logical dependency. They are chained anyway because both edit
the *same five hand-maintained enumeration lists* (`sync-scaffold.sh` `FILES`,
`test_scaffold_data_in_sync.py` `TRACKED`, `test_scaffold_resources.py`,
`test_init_integration.py`, `sync_scaffold.bats` `setup()`). Serialising them keeps
each squash's diff attributable to one WU. T05 stays unchained — it touches only a
new test module.

### 1.3 The six-surface (and seven-surface) seeding enumeration

Both T04 and T06 add a file to the packaged seed. Adding one is **not** a
one-file edit; six independent hand-maintained lists enumerate the seed set, and
missing any one turns a currently-green suite red:

| Surface | What breaks if missed |
|---|---|
| `specfuse/loop/data/<path>` | `test_package_data_matches_canonical` — "package copy missing" |
| `scripts/sync-scaffold.sh` `FILES=()` | seed never syncs; `test_no_orphan_files_in_package_data` if hand-copied |
| `tests/test_scaffold_data_in_sync.py` `TRACKED` | `test_no_orphan_files_in_package_data` — orphan |
| `tests/test_scaffold_resources.py` | expected-relpath mismatch |
| `tests/test_init_integration.py` (two lists) | expected-set mismatch + `test_rules_byte_faithful` |
| `tests/sync_scaffold.bats` `setup()` | `sync_file()` returns 1 on missing source under `set -euo pipefail`; `[ "$status" -eq 0 ]` fails |

T06 adds a seventh: `gitignore.snippet` in **both** copies, since the snippet is
itself a tracked seed file. Enumerated in each WU's body so no attempt is spent
rediscovering it. This is `planning-discipline.md` §1 applied to a plumbing surface
rather than a validation rule — the lists were read, not assumed.

Also read and recorded: `sync-scaffold.sh` does **not** sync `docs/`. T07 edits
`docs/skills.md` and must hand-copy to `specfuse/loop/data/docs/skills.md`, because
`test_package_docs_match_canonical` asserts byte equality and no script maintains
it. `CORE_FILES` is the core-vendored subset (`correlation-ids`, `never-touch`,
`security-boundaries`, `verification-discipline`); `design-for-diagnosis.md` is
loop-authored like `planning-discipline.md`, so it goes in `FILES` only.

### 1.4 The rule is seeded and NOT `@`-imported — made executable, not asserted

`PLAN.md` decided the posture. T04 turns it into a test: `_RULES_BLOCK` must not
contain `design-for-diagnosis`. Without that assertion the decision survives only as
prose, and the next well-meaning session that "completes" the import list reverses
it silently. Confirmed against source: `_RULES_BLOCK`
(`specfuse/loop/scaffold.py:184`) imports five rules and omits
`planning-discipline.md` and `close-discipline.md` — the precedent is real, not
inferred.

### 1.5 The diagnosability audit is WARN, never ERROR

Honored in T05 (AC6) and T07 (AC6). The reason is already recorded in `PLAN.md`'s
**escalation-predicate satisfiability** section: a populated codebase predating the
design-for-diagnosis rule violates it everywhere by construction, so an ERROR
predicate reports non-zero on input already in its intended final state — the
`planning-discipline.md` §2 unsatisfiability test, failed. LEARNINGS records the
general form (`[FEAT-2026-0015/G2-CLOSE]`). No re-derivation needed; the drafted WUs
cite it and both carry an assertion that no ERROR path exists.

T05's AC6 asserts on **the set of severities the function can emit**, not merely on
one fixture's output. A fixture-only assertion would pass while an `ERROR` branch sat
unreached — the same shape as a rule read as `ERROR` in source but gated off at
runtime (`verification-discipline.md` §3).

### 1.6 The `.claude/skills/` symlink is operator work

T07 carries it as a pre-dispatch prerequisite with the exact `ln -s` command, and
its escalation triggers say explicitly **do not block on the symlink's absence**.
`.claude/skills` sits under the sandbox's `denyWithinAllow` — a deny nested inside
an allow scope, which survives `unsandboxed: true` (`[FEAT-2026-0016/G3-CLOSE]`).
No AC depends on it. A WU drafted without this split burns an attempt.

The operator step, for the arming human's checklist:

```
ln -s ../../.specfuse/skills/derive-monitoring .claude/skills/derive-monitoring
```

### 1.7 No production module for discovery — the reference implementation lives in the test

T05 produces only `tests/test_derive_monitoring_discovery.py`, following
`test_roadmap_add_skill.py` / `test_roadmap_archive_skill.py`, which hold their
skills' algorithms inline. Alternative considered and rejected: a module under
`specfuse/loop/`. Rejected because the driver never calls it — the *skill* is the
consumer, and the skill is prose read by a model. A module nothing imports is dead
weight that the ≥90% coverage floor then obliges someone to test for its own sake.
The reference implementation's job is to pin the algorithm the skill describes; a
test module does that and the established pattern already says so.

Consequence, stated plainly: nothing mechanically forces the skill's prose and the
reference implementation to stay in agreement. T07 AC5 requires `SKILL.md` to cite
the reference implementation's path, which makes divergence *visible* to a reader.
It does not make it *detectable*. See §3(d).

### 1.8 The fragment-marker convention for T08

`validate_monitoring` requires top-level `environments:` and `components:`, so a
snippet-shaped example fails it. Options weighed:

- *Validate only blocks that look complete* (heuristic) — a bad dial inside a
  snippet then never gets checked, and the skip is invisible.
- *Forbid snippets entirely* — makes the skill's prose worse to read.
- **Chosen: explicit `# lint-monitoring: fragment` first line, with the marker count
  asserted against a declared expected number.** A fragment is a visible, counted
  decision; the escape hatch cannot quietly become the norm.

T08 also carries two anti-vacuity assertions (AC2 negative observation, AC3
expected block count), because a glob that silently matches nothing passes
"every block validates" perfectly.

### 1.9 `monitoring.overrides.yml` uses gate 1's schema, unchanged

One schema, one validator. A second overrides-specific schema would need a second
validator, a second gate, and a second drift surface, for a file whose merge
semantics this feature does not implement anyway. T06 requires the example to pass
`validate_monitoring` clean (AC1) and requires each artifact's header to state that
merge and execution semantics land in FEAT-2026-0040 (AC7).

### 1.10 The filename has no `.local.` segment

`PLAN.md` recorded this; T06 makes it a test (AC4). `leak_scan.py:43` classifies
`<word>.local` as a private-host finding, the pre-commit hook runs the structural
scan on the staged diff, and the driver squashes **without** `--no-verify` — so a
`monitoring<dot>local<dot>yml` token would be rejected three times and the WU would
block on `spinning_detected`. Verified against the shipped regex, not from memory.

This bit while drafting: the first version of T06 and of this review spelled the
rejected filename literally, which would have made *these two files* trip the hook
on the driver's squash of this very WU and block `G1-PLAN` on
`spinning_detected` — the trap describing itself. Both now use `<dot>` placeholders,
and T06 carries an explicit instruction not to write the matching token into any file
it produces, comments and fixtures included.

### 1.11 Cost — gate 2 lands at exactly the sketched $16.00

T04 $2.00 · T05 $3.00 · T06 $2.00 · T07 $2.50 · T08 $1.50 = **$11.00** substantive,
plus G2-CLOSE $5.00 (the `planning-discipline.md` §5 floor) = **$16.00**, against
`GATE-02.md`'s `cost_budget_usd: 20.0`. Feature total is now $18.00 (gate 1) +
$16.00 = **$34.00**, matching `PLAN.md`'s feature-level figure exactly. The
structural cost-delta WARN `PLAN.md` predicted is now gone —
`lint_plan.py .specfuse/features/FEAT-2026-0039-monitoring-schema` exits 0 with no
WARN lines.

**Doubt about these numbers.** T05 at $3.00 is the one most likely to overrun: eight
tests, two fixture trees, a source-scanning boundary test, and a ≥90% coverage floor
over a reference implementation written from scratch. T07 at $2.50 assumes SKILL.md
comes in near `derive-verification`'s size (17KB) with its structure to copy — if the
authoring session instead re-derives the method, it doubles. Neither is under-drafted
on purpose; both are named here so an overrun reads as a calibration data point in
G2-CLOSE's cost analysis rather than as a surprise.

### 1.12 What this WU deliberately did NOT edit

- **`GATE-02.md`.** Its definition of done says the WU list "is filled in then," but
  `WU-91`'s permitted-edit set is "gate-2 WU files, `GATE-02-REVIEW.md`, and
  `PLAN.md`'s gate-2 graph and `G2-CLOSE`'s `depends_on`" — `GATE-02.md` is not on
  it, and gate files are driver/human territory. The WU list lives in `PLAN.md`'s
  graph, which is authoritative (`docs/methodology.md` §2, one fact one home).
  **For the arming human:** if you want the five WU ids mirrored into `GATE-02.md`'s
  bullet, that is a one-line edit at arm time.
- **`WU-92`'s acceptance criteria.** It already carries `## Cost analysis` (AC2) and
  `## What the loop did NOT verify` (AC3, with the exact re-run condition), so
  criterion 7 was already met and no edit was warranted. But see §4 — there is one
  thing it is missing.
- **`PLAN.md`'s cost/WARN notes.** Now historical rather than wrong; left as written
  to keep this WU's diff to the graph.

---

## 2. Verification story per drafted WU

Every WU carries a red-test-first AC naming a specific test that fails on HEAD. No
§12 exemption was needed — including T07, whose skill is prose: its registration,
frontmatter, internal consistency, and example validity are all mechanically
checkable even though its interview quality is not.

| WU | Red test (fails on HEAD) | What green actually proves | Negative observation |
|---|---|---|---|
| T04 | `test_design_for_diagnosis_rule.py::test_rule_is_seeded` | The rule file exists, seeds into a scaffolded tree byte-faithfully, and is absent from `_RULES_BLOCK` | AC7 denylist scan — the rule names no vendor/framework token |
| T05 | `test_derive_monitoring_discovery.py::test_discovered_config_passes_lint_monitoring` | Discovery output, rendered as YAML, validates clean against gate 1's validator — gate 2's definition of done in one assertion | AC7 audit fires on an undiagnosable tree and is silent on a diagnosable one; AC6 asserts the emittable severity set |
| T06 | `test_monitoring_bootstrap_artifacts.py::test_overrides_example_validates_clean` | Both artifacts exist, validate, seed without rename, and the live overrides file is gitignored | AC5 rejects an inline-literal credential built in the test |
| T07 | `test_derive_monitoring_skill_registration.py::test_skill_present_in_both_trees` | The skill exists in both trees byte-identically, is discoverable, cites T04/T05, states WARN-not-ERROR, and names the symlink as operator work | AC8 rejects an inline-literal credential string |
| T08 | `test_monitoring_fenced_blocks.py::test_every_yaml_block_validates_clean` | No prose example in the skill or bootstrap artifacts can drift from the schema | AC2 a deliberately broken block is caught; AC3/AC4 bound the vacuous-pass and skip-count holes |

The chain that matters: **T05's AC1 and T08's AC1 together are gate 2's real
oracle.** T05 proves the algorithm's output is schema-valid; T08 proves the prose
examples an operator will actually copy are schema-valid. Everything else is
presence and consistency checking.

---

## 3. Open risks — what gate 2 will not prove

### (a) The fixture is stylized. Here is exactly what it does and does not prove.

T05's fixture is a `{relpath: content}` mapping built in a `tempfile` directory —
two `acme-*` components, one HTTP-serving, one message-consuming, with evidence
files written to satisfy an evidence-pattern table the test also declares.

**What passing it proves.** That the discovery algorithm is deterministic; that its
output, rendered as YAML, satisfies `validate_monitoring`; that the audit fires on
absent diagnosability properties and stays silent when they are present; that the
neutral-record shape survives a second, differently-named stack. These are real
properties and they are the ones the schema contract actually needs.

**What passing it does not prove, at all.** That the evidence patterns match how a
real backend is laid out. The fixture's tree was written by the same session that
wrote the patterns that match it — it is a closed loop, and a closed loop always
closes. Every quantity that matters in the field is unmeasured: whether a real repo
yields the *right number* of components (a service mesh or a monorepo may yield
dozens of false components, or one), whether the suggested checks are the ones an
operator would have chosen, whether the audit's findings are actionable rather than
noise, and whether the component names discovery invents are names the operator
recognises. A fixture cannot be wrong about a repo it was written from.

The honest characterisation: T05's tests are a **regression guard on an algorithm's
shape**, not evidence that the algorithm works. The first real backend is the first
measurement, and it happens post-merge (§3(c)).

### (b) Stack-specific detection leaking into the provider-agnostic core

**The boundary.** Gate 1 already holds its half: `lint_monitoring.py` treats
`provider` as an opaque string and interprets nothing — no vendor concept appears in
the validator. Gate 2's half is the discovery core: **evidence patterns are an
injected input, never baked in.** `discover_components(tree, patterns)` consumes the
table; the table is per-stack data. Adding a stack is a new table, not a patch to
the core. This is the same boundary FEAT-2026-0040's adapter interface depends on —
if the core absorbs stack knowledge here, 0040 inherits a core it must special-case.

**How the drafted tests hold it — two independent mechanisms, because one is not
enough.**

1. *Behavioural* (T05 AC4): `test_neutral_records_survive_a_second_stack` runs
   discovery over a second fixture tree in a differently named stack with a second
   pattern table, and asserts the emitted records are structurally identical — same
   types, same dials, same suggested check types — differing only in names and
   evidence paths. A core that has absorbed stack knowledge produces different
   structure and this test goes red.
2. *Structural* (T05 AC5 + T04 AC7): `test_core_names_no_stack_tokens` scans the
   reference implementation's own source against an inline denylist of framework /
   logging-library / cloud-vendor tokens; T04 runs the same scan over the rule text.
   This catches leakage that happens to be behaviourally invisible on two fixtures.

**Where these mechanisms are weak, stated rather than glossed.** The behavioural
test compares two fixtures *the same session authored*. If that session holds a
mistaken model of both stacks in the same direction, both fixtures encode the same
mistake and the test agrees with itself. The structural test is only as good as the
denylist, which is a hand-written list of tokens the author thought to include —
"provider-agnostic" is a negative property, and no finite denylist proves a
negative. T05's AC5 also flags a specific vacuous-pass hazard: the scan must cover
the *core functions* and not the fixture section, or the pattern tables' own stack
tokens would be scanned as if they were core, and the mechanism the WU uses to
achieve that has to be stated in a comment. Together these two tests make leakage
*hard* and *visible*. They do not make it impossible. The real test is 0040 writing
its first adapter against this core.

### (c) The skill's interview quality has no in-loop oracle. None.

This is the largest gap in gate 2 and it is structural, not an oversight.

`derive-monitoring` is an interactive skill. Its value is the interview: which
questions it asks, which it correctly declines to ask because the repo already
answered them, whether it batches them tolerably, whether it invents a component the
operator does not recognise, whether the reconciliation report is honest about what
came from evidence versus from an answer. **Nothing in gate 2 tests any of that.**

Why it cannot be tested in-loop, concretely: a dispatched `claude -p` session has no
human channel — the skill's own documented behaviour is that piping a prompt
consumes stdin and silently degrades to `[gap]` mode — and the skill's target is a
*different repository*, which a dispatched WU has neither access to nor commit
rights in. Both halves of the requirement are missing, so no amount of test-writing
closes it.

What gate 2 verifies instead, and it is worth being precise that this is a much
weaker claim: that `SKILL.md` **exists**, is discoverable, is registered, states its
hard rules, cites the artifacts its method depends on, and that its examples
validate. That is a claim about the *document*. Whether the document produces a good
interview is unmeasured.

Two consequences, both drafted:

- T07 carries an explicit "no in-loop oracle for interview quality" paragraph
  instructing the session **not** to manufacture a test that appears to cover it. A
  fabricated interview test would be worse than the gap — it would hide it.
- `WU-92` AC3 already requires `## What the loop did NOT verify` to name the live run
  against a real multi-component backend as post-merge operator work, with the exact
  re-run condition that upgrades it: *an operator runs the skill against a real
  project and its drafted `monitoring.yml` passes `lint_monitoring` clean.* That
  condition is the right one and it is necessary — but note it is also **not
  sufficient** for interview quality: a clean-validating draft proves the output is
  schema-valid, not that the interview asked the right questions. The operator
  judging the draft's *content* is the only oracle that exists, and it is a human
  one.

`GATE-02.md`'s definition of done says "an operator can run `/derive-monitoring`
… and get a drafted `monitoring.yml` that passes gate 1's validator." Gate 2 will
close having proven the second clause on a fixture and the first clause not at all.
The verdict must say so; `met_locally` is the honest ceiling, and
`close-discipline.md` §2 makes the follow-up record mandatory on that verdict.

### (d) Prose–implementation divergence has no guard

§1.7's cost. T07 AC5 makes `SKILL.md` cite the reference implementation's path, so a
reader can check agreement. Nothing detects the case where T05's algorithm is later
changed and the skill's prose description of it is not — the skill is read by a
model, and a model will follow the prose. Residual, accepted, named here so it is not
discovered as a surprise in 0040.

### (e) `docs/concepts/monitoring-schema.md`'s example is not covered by the drift test

Gate 1 shipped a schema-reference doc with an `## Example` section. `GATE-02.md`
scopes the drift test to "the skill and the bootstrap artifacts," so that example
sits outside T08's declared surface list — a monitoring example in the repo that no
gate validates. T08 AC6 forces the choice into the open: either extend the surface
list to include it (preferred, if its example is a complete config) or record the
exclusion with a reason. Not silently left out.

### (f) The bootstrap artifacts have no live consumer until FEAT-2026-0040

Worth stating because it is adjacent to a failure `PLAN.md` already paid for. The
GitHub Actions workflow was moved to 0040 because its *body invokes*
`specfuse-monitor run`, a binary that does not exist — broken on day one
(`[FEAT-2026-0029/G1-CLOSE]`). T06's artifacts are different in kind: each is a data
file, valid and validatable standing alone, whose consumer arrives later. T06 makes
that distinction binding — no runner script, no `Makefile` target, no invocation of
a nonexistent binary, and a header line in each artifact naming 0040 as the owner of
merge and execution semantics. **This is a line, and lines can be argued with.** If
the arming human reads it as the same failure wearing a different hat, the right
response is to defer T06 to 0040 alongside the workflow and drop T07's references to
it — a coherent alternative, not a defect to patch.

---

## 4. For the arming human — one gap in `WU-92` worth closing

Gate 1 **auto-closed** (`RETROSPECTIVE.md`, `predicate=v1`, `$5.93`). Its own
`## What the loop did NOT verify (gate 1)` section says the full close-intermediate
ceremony did not run, so gate 1's per-criterion deferred-verification list was
**never enumerated**, and it states that gate 2's close must reconcile it before the
terminal verdict.

`WU-92`'s current acceptance criteria do not mention that reconciliation. AC3 covers
this feature's *known* deferred entry (the live run); nothing obliges the close to go
back and enumerate what gate 1's auto-close skipped. Since `WU-91`'s permitted-edit
set does not include `WU-92`'s body, this is flagged rather than fixed.

**Suggested AC to add to `WU-92` at arm time:** *"Reconcile gate 1's un-enumerated
deferred-verification list. Gate 1 auto-closed, so its per-criterion deferred list
was never produced; walk T01–T03's acceptance criteria and either confirm each was
verified in-loop or add it to `## What the loop did NOT verify` with its re-run
condition."*

Two lower-priority items, both one-liners: mirror the five WU ids into
`GATE-02.md`'s definition-of-done bullet (§1.12), and create the
`.claude/skills/derive-monitoring` symlink before any interactive use of the skill
(§1.6).

---

## 5. Arming checklist

- [ ] `.claude/skills/derive-monitoring` symlink created (operator, pre-dispatch — §1.6)
- [ ] §4's gate-1 reconciliation AC added to `WU-92`, or consciously declined
- [ ] T04–T08 flipped `draft` → `pending`; gate 1 marked `passed`
- [ ] §3(a) accepted: the fixture is a shape guard, not field evidence
- [ ] §3(c) accepted: interview quality is unverified in-loop and `met_locally` is the honest ceiling for gate 2
- [ ] §3(f) accepted: T06's artifacts ship now rather than deferring to FEAT-2026-0040
- [ ] T05's and T07's cost estimates accepted as the likeliest overruns (§1.11)
