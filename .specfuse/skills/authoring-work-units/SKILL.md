---
name: authoring-work-units
description: How to write a single Specfuse work unit that won't block spuriously or pass hollowly. Reference for humans authoring WUs in the loop, and for reviewing PM-agent drafts in the orchestrator. Lean; eight evidence-backed rules, one per spot a real run has tripped on.
---

# Authoring a work unit

This skill teaches how to fill the five-section WU contract
(`.specfuse/templates/WU.template.md`, methodology §4) well — section by
section, plus one cross-cutting sizing rule.

**The bar.** Every rule below names a concrete failure mode it prevents. If
a rule can't name the failure, it's filler and was cut. `"Write clear
acceptance criteria"` is filler; `"Scope acceptance-criteria checks to the
feature's own footprint — repo-wide greps trip on pre-existing unrelated
state"` is the right shape. Apply the same bar when adding rules.

This is shared methodology craft — works for the loop (single-repo) and the
orchestrator (multi-repo). The loop is the near-term author, like the
architecture addendum; orchestrator-side adoption is the fold-in.

---

## 1. Context — write for a cold session

The body below the frontmatter is **all a fresh, memoryless session gets**.

- Name the correlation ID (`FEAT-YYYY-NNNN/TNN`) and the grounding files
  (specs, docs, target paths) the session needs to orient.
- **Reference** binding rules under `.specfuse/rules/` — never restate.
  Restated rules drift from source.
- Enough to orient, not a wall. If you're summarizing the feature spec,
  the WU is misscoped — link it instead.

> *Prevents:* a fresh session thrashing for lack of grounding, or acting
> on a restated rule that has since changed at source.

## 2. Acceptance criteria — scope to the feature's own footprint

Criteria that grep or scan the **whole repo** trip on pre-existing,
unrelated state and cause a correct-but-unwanted block. Bound every check
to the feature's own footprint: its slug, the paths it creates or edits,
the symbols it introduces, the files in `generated_surfaces` /
`files_changed`.

- Phrase each criterion as an **objective statement a reviewer can judge
  and a gate can mechanically check** — not an intention. (`"GET /health
  returns 200 with JSON {status, version}"` ✓ — `"endpoint is
  well-tested"` ✗.)
- Avoid compound criteria (`"X and also Y"`). Split so a single failure
  attributes to a single line.
- A criterion that needs inspecting unrelated parts of the repo is the
  wrong shape; narrow the scope, or move the check to a repo-wide
  hygiene WU / the `code` gate set.

> *Prevents:* a throwaway "grep returns zero hits" criterion blocking on a
> stale roadmap pointer the WU never touched (real failure logged in
> `.specfuse/LEARNINGS.md` under `[meta/first-live-use]`); also prevents
> reviewers waving through subjective criteria that hide unmet
> requirements.

## 3. Do not touch — name real paths, AND name what the WU produces

Generic `"don't touch other files"` is one an agent will cross. List the
actual boundaries this WU might brush against:

- The **generated directories** in this repo (`_generated/`, `gen-src/`,
  or whatever your repo declares).
- The **specific sibling-WU files** in this gate, by path, if the gate's
  graph is already laid out and the WU's work is adjacent to theirs.
- **Secrets** files (`.env`, `*.pem`, `*.key`, `credentials.json`) and
  `.git/` internals.
- **The driver owns all git.** The session edits files only — never runs
  `git`. State this even when it feels redundant; without it, an agent
  helpfully runs `git add` and corrupts the driver's bookkeeping.

**Companion rule — name what the WU is expected to produce.** The
boundaries above are one half; the other half is naming the files this WU
should *author*. The Acceptance criteria section (§2) should list the
specific paths the WU is responsible for (e.g. `.github/workflows/cd.yml`
and the CI section of `CLAUDE.md`). A reviewer should be able to point at
every changed file in the squash commit and find it in either the WU's
produces-list or the gate's verification output. Without an explicit
produces-list, an agent can "helpfully" do work that belongs to a later
WU in the same gate (observed: a T01 that wrote CLAUDE.md doc updates
that were T92's job), and the verification gates don't object.

> *Prevents:* an agent reaching into a generated directory because "don't
> touch other files" didn't sound like *this*; side commits the driver's
> squash can't reconcile; and silent over-reach where a WU does adjacent
> work that should have belonged to a sibling WU.

## 4. Verification — name the gates the driver will actually run

The WU's Verification section names gates, but the driver (or branch
protection) runs whatever is in `verification.yml`'s relevant set. If they
disagree, the WU's stated verification is fiction.

- For `implementation` WUs, name the `code` set as declared in this
  repo's `verification.yml`. Don't list a gate the file doesn't have, and
  don't omit one it does.
- For fast-iteration or probe work, prefer a **scoped** gate command
  (`pytest tests/test_health.py`, `mvn test -Dtest=HealthTest`) over a
  full-suite one. A minutes-long full run on every attempt makes the
  three-attempt budget effectively one attempt.
- Some runners fail silently on a missing-but-named test (no tests found
  ≠ all passed). Name a real test, and confirm the runner exits non-zero
  when nothing matches.

> *Prevents:* a WU that "passes" the agent's check but fails the driver's
> re-run; and a WU burning each of three attempts on a full suite the
> iteration didn't need.

## 5. Escalation triggers — distinguish "my check tripped" from "the bad thing happened"

Triggers should fire on the **real hazard**, not on any flagging condition.
The best observed agent behaviour, when a criterion tripped ambiguously,
emitted `status: blocked` *and* explained the trip might be a false alarm
on pre-existing state, recommending human review — rather than pushing
through or silently passing.

- Name triggers as conditions, not actions: `"if no router module exists,
  block — that's a different unit of work"`, not `"create the router."`
- When you're unsure whether a tripped criterion is the real failure or
  pre-existing unrelated state, the right move is a reasoned
  `status: blocked` with the evidence. **Blocked is a respectable
  outcome** (see [`../../rules/result-contract.md`](../../rules/result-contract.md));
  a guessed pass is worse than an honest block.
- A trigger that only ever fires on the agent's own bug is not a trigger;
  it's a code-quality concern. Triggers exist for spec/scope ambiguities
  the agent shouldn't resolve unilaterally.

> *Prevents:* the agent forcing a doubtful pass that costs the gate's
> trust budget; also prevents triggers that fire constantly and become
> noise the next reader ignores.

---

## 6. Sizing — one WU = one focused session's work

A WU is crafted to land in a single fresh-session pass. The Ralph property
(fresh context per attempt) only buys leverage when the unit is
small-enough to fit.

- If a WU needs multiple rounds of **unrelated** work, it's two WUs.
  ("Add the endpoint AND refactor the router module" is two.)
- If a WU's acceptance criteria number in the double digits, suspect
  bundling — most well-sized WUs have 2–5 criteria.
- Sizing interacts with gate-cutting (how to slice a feature into the
  right number of gates with the right WUs each). **That's a separate
  skill** and is deferred until multi-gate runs surface decomposition
  evidence; this skill stays at the per-WU level.

> *Prevents:* a WU that exhausts the three-attempt budget on the first
> sub-problem and never reaches the second; also prevents the driver
> producing one squashed commit that mixes two unrelated changes.

---

## 7. Hygiene work units — when a blocked WU points outside its scope

A substantive WU sometimes discovers that its verification can't pass
because of a pre-existing bug in a path its **Do not touch** rule
forbids (a shared module, a dependency version, a config file owned
elsewhere). Observed: a `terraform validate` gate failing on an
`automatic_upgrade_channel`-vs-`automatic_channel_upgrade` mismatch in a
shared module that the WU was correctly forbidden from editing.

The right move is to insert a **hygiene WU** earlier in the gate (or as
a precursor gate) scoped to that fix alone:

- **ID convention.** The hygiene WU's ID is the target substantive
  WU's ordinal followed by `H` — e.g. `FEAT-YYYY-NNNN/T02H` is "the
  hygiene WU for T02." Multiple hygiene WUs for the same target use
  `T02H1`, `T02H2`. See
  [`../../rules/correlation-ids.md`](../../rules/correlation-ids.md)
  for the canonical pattern; the linter (`lint_plan.py`) enforces it.
- **One narrow acceptance criterion** — e.g. `"modules/aks/cluster.tf
  uses the azurerm-3.x attribute name automatic_channel_upgrade"`. The
  hygiene WU's "produces" list names only the broken file.
- **Pass on its own verification** before the blocked WU runs again.
  The blocked WU then re-runs unmodified; its scope and "Do not touch"
  bounds are intact.
- **PLAN.md wiring.** Insert the hygiene WU's row into the gate's
  `work_units` graph BEFORE the target substantive WU. Update the
  target's `depends_on` to include the hygiene WU's ID. Flip the
  target's `status` from `blocked_human` back to `pending` so the
  loop will re-dispatch it after the hygiene WU passes.
- **Evidence requirement.** The hygiene WU's **Context** section
  must quote the blocked WU's `human_escalation` event from
  `events.jsonl` verbatim — the timestamp, the reason, and the
  agent's blocked_reason text. That's the trace from "this fix
  exists because of that block." Without it, a hygiene WU looks
  indistinguishable from speculative pre-emptive work.
- **Never the wrong responses:** do NOT loosen the blocked WU's "Do
  not touch" to permit the cross-cutting fix (muddies its boundary);
  do NOT fix it manually out-of-loop and pretend the gate ran clean
  (silent drift between the methodology's recorded history and git).

The hygiene WU is methodology-honest: every state change goes through
the loop, every commit traces to a WU, every fix has its own evidence
trail. The cost is one more WU; the benefit is the gate cycle stays
trustworthy.

> *Prevents:* the temptation to either widen the blocked WU's scope
> (eroding the per-WU contract) or silently fix out-of-band (eroding
> the audit trail). Both undermine the same invariant — that every
> committed state change traces to a WU that was dispatched, verified,
> and committed by the loop.

---

## 8. Cross-surface contract values — verify against the source, never invent

When an acceptance criterion names a value that lives in **another system** —
a GitHub label name, an API field name, an event-schema key, a shared protocol
constant, a branch/trailer format — that value must be **verified against the
authoritative source before the gate is armed**, not invented from the feature's
own internal conventions. An invented value is a silent correctness risk: it
looks right to the author, satisfies the WU's own AC, passes offline tests, and
fails only at live/integration time.

- For every AC that references an external system's vocabulary, write a **pre-arm
  check line** into the WU spec: `verify <value> against <authoritative source>
  before locking this AC`. The gate review document lists these open
  verifications; the gate is not armed until each is checked.
- This blind spot is **systematic in `plan-next` drafts**, not random — a planner
  drafting a downstream gate will confidently invent plausible, internally
  consistent cross-repo values it cannot see. So every `plan-next` gate review
  should carry a **"Cross-repo contracts" table**: each invented value alongside
  its authoritative source and a checked/unchecked status.

> *Prevents:* the failure observed in `[FEAT-2026-0003/G3-LESSONS]` — a draft
> invented the report-back labels `loop:in-progress`/`loop:complete`; the correct
> values were the orchestrator's canonical `state:in-progress`/`state:done`
> (`naming-convention.md §5.1` + `labels.md`). Caught at gate-3 arming by reading
> the source; had it shipped, every adopted feature would have reported state on
> a label namespace the orchestrator's poller never queries.

---

## 9. Verification — add symbol-existence checks when the WU requires new functions

The `code` gate (`python3 -m unittest discover`) passes when no new tests are
registered and existing tests make no assertion about absent symbols. An agent
can claim `complete` without having written any production code; the driver
commits only the WU-status flip; gate verification passes on the unchanged
codebase. Observed in `FEAT-2026-0007/T04`: all required functions absent from
`loop.py`; gate passed; gap invisible until integration time.

- For every WU that requires a new importable function, constant, or class, add an
  **explicit existence check** to the WU's own Verification section — not just "run
  the code gate." Canonical form: `python3 -c "from module import symbol_name"`.
  Use `grep -c "^def symbol_name" target.py` when import would trigger side-effects.
- Add a **completeness escalation trigger** alongside any correctness trigger:
  `"If [required_function / required_file] is absent from the files you edited,
  emit status: blocked — do not claim complete."` This fires before the RESULT
  block is written, not after the driver re-runs gates and finds nothing.

> *Prevents:* a WU that passes all code gates on the unchanged codebase because
> the required test file was never written and the required functions were never
> defined — the exact failure mode in `FEAT-2026-0007/T04` (retry escalation
> ladder declared complete with zero production code committed).

## 10. Helper-duplication pre-flight — enumerate symbols before declaring scope

When a WU's spec names a helper symbol that exists in the codebase
(a fixture, a context manager, a top-level function in `tests/` or
elsewhere), do **NOT** assume it appears only once. Enumerate before
authoring the WU's "Do not touch" / Acceptance criteria sections:

```bash
grep -rn "def <symbol>" tests/                       # for test helpers
grep -rn "def <symbol>\|class <symbol>" src/         # for code symbols
```

If the enumeration returns more than one hit, EVERY hit is in scope
for the WU OR every hit must be named in "Do not touch" with the
explicit reason "out of scope — handled in <other WU / future
feature>". Silently fixing one of N duplicates ships an incomplete
fix; the others slip and surface later (typically in CI on the
deferred surface).

The rule applies symmetrically when the WU CREATES a new symbol
intended to replace duplicates: enumerate the current call sites and
list them as `## Files modified to switch to the new helper`. If the
WU author cannot enumerate exhaustively, the WU is under-specified
and should not be dispatched.

> *Prevents:* the FEAT-2026-0013 ship-fail-fail-fail-fail cycle. v1
> attacked ONE `integration_workspace()` fixture; CI re-failed on a
> different test file's OWN copy. v2 attacked the same one + added
> belt-and-suspenders; CI re-failed on a copy in yet another file.
> v3 finally centralized after enumerating all 5 sites. Cumulative
> cost of the missed enumeration: ~$10 (v1+v2 dispatches + re-arm
> overhead). The pre-flight grep is free.

---

## 11. Operator scripts are software, not docs — require shellcheck + bats

When a WU emits an **executable artifact intended for human operators**
(a committed `.sh` script, an installer helper, a runbook whose body is
a sequence of shell commands an operator copy-pastes), the loop's
default `code` gate set typically does NOT exercise it — there is no
unit test, no syntax check, and nothing that catches the kinds of
quirks shell scripts ship with on a fresh workstation. The WU passes
on "the file exists with these sections" and the operator discovers
the bugs against real systems post-merge.

For every WU that ships an executable operator script, its Acceptance
criteria must include all three of the following — phrased as
gate-mechanically-checkable lines (§2):

1. **`shellcheck <script>` produces zero warnings**, or every disable
   directive (`# shellcheck disable=SCxxxx`) carries an inline
   justification comment naming the reason.
2. **`bash -n <script>` parses clean** — catches typos and unterminated
   constructs the shellcheck pass would skip on a parse failure.
3. **At least one bats-core test against the happy path**, with all
   external commands (`az`, `kubectl`, `curl`, `gh`, `terraform`, etc.)
   replaced by PATH-shimmed stubs. The bats test is the contract: the
   stubs assert the script's call shape, the test verifies the script's
   exit code + observable output on the success path. A test on the
   happy path alone is enough to catch lifecycle bugs (trap-revoke
   ordering, set -e silent-abort, premature exits); error-branch
   coverage is bonus, not required by this rule.

Add a corresponding entry to the WU's **Verification** section naming
the gate command — for most repos this is a `code` gate entry like
`bash -n scripts/<name>.sh && shellcheck scripts/<name>.sh && bats
tests/<name>.bats`. If your `verification.yml` does not yet declare
a gate that runs bats, the WU's Hygiene precursor (§7) is to add one.

**Skip the rule when** the WU body is a pure file artifact with no
executable shipped — a markdown-only runbook that documents commands
without committing a script, a Terraform module, a Helm chart, a
config file. The rule fires on the presence of a committed
executable, not on the WU's docs-vs-implementation type.

> *Prevents:* the failure observed in `example-iac` Argo CD
> session 2026-06-14 — FEAT-2026-0028/T02 shipped two ~500-LoC
> operator scripts (`bootstrap-argocd-entra-app.sh`,
> `bootstrap-argocd-cluster.sh`) treated as docs artifacts. Post-merge
> the operator hit 10 patches over ~3.5hr fixing portability
> (`${VAR,,}` doesn't work on stock macOS bash 3.2), lifecycle
> (trap-revoke fired before the revoke was needed; KV read aborted
> silently under `set -e`), and surface (`az ad sp create` raced with
> re-runs; `az ad sp show` would have caught it). `shellcheck` flags
> the portability issue at static analysis; one bats happy-path test
> with `az` stubbed catches the create-race + lifecycle bugs at WU
> time. Cost: ~15min of test setup per script in WU acceptance vs
> ~3.5hr of post-merge patching across 10 PRs.

---

## Haiku — when (and when not)

`model: haiku` is opt-in only — never a default in `MODEL_BY_TYPE`. Use it
when cost matters more than depth **and** the task fits the narrow profile below.

**Recommended for:**
- `docs` WUs that reconcile a small, bounded set of changes (≤ 2 files,
  no cross-WU reasoning, purely mechanical reformatting or appending).
- `lessons` WUs that append ≤ 5 self-contained entries from the retrospective
  (pattern-matched synthesis; no forward-design reasoning).

**Discouraged for:**
- `implementation` — multi-file edits require cross-file reasoning that
  regresses on Haiku (observed: symbols introduced in file A not referenced
  correctly in file B without a full-context pass).
- `plan-next`, `close`, and `close-intermediate` — forward design, cross-WU
  coordination, terminal feature-arc verdicts, and the folded retro+lessons+docs
  synthesis in `close-intermediate` require the full reasoning budget; Haiku
  consistently misses implicit constraints.
- `retrospective` for a gate with > 3 substantive WUs — synthesising cost
  tables, failure traces, and lessons-to-graduate across many WUs requires
  deep context.

**Rationale.** Gate-1 closing WUs on this feature ran at ~$0.20 / 90 s on
Sonnet at `low` effort (see `RETROSPECTIVE.md` cost table). Haiku 4.5 would
compress these further — appropriate only when the task is purely additive
and volume is small. Multi-file forward design or cross-WU reasoning regresses:
Haiku's smaller context window and weaker planning capability produce
incomplete or inconsistent artifacts at gate scale.

**Override mechanic.** Set `model: haiku` explicitly in the WU's frontmatter
to opt in. There is no way to make Haiku the default for a type; the override
is always per-WU and always deliberate. See `.specfuse/templates/WU.template.md`
frontmatter notes for the full `model:` and `effort:` field contract, including
the type-keyed defaults in `MODEL_BY_TYPE` and `EFFORT_BY_TYPE`.

---

## This skill distills `.specfuse/LEARNINGS.md`

When a gate's `lessons` work unit surfaces a new authoring rule — one that
would change how a future WU is written or executed — it graduates here
once it's reusable and durable. The pipeline is **runs → retrospective →
lessons → LEARNINGS.md → this skill**. If a rule lives only in LEARNINGS
and would clearly change WU authoring, it's a candidate for promotion on
the next edit.

## Version

**v0.9.** Added §11 (Operator scripts are software, not docs — require
shellcheck + `bash -n` + bats happy-path in Acceptance for any WU that
ships an executable operator artifact) — graduated from the
`example-iac` Argo-CD-on-AKS session of 2026-06-14, where two
~500-LoC bootstrap scripts shipped as docs artifacts cost ~3.5hr of
post-merge patching across 10 PRs to fix portability, lifecycle, and
surface bugs that static + bats checks would catch at WU time.

**v0.8.** Added §10 (Helper-duplication pre-flight: enumerate symbols
before declaring scope) — graduated from `[FEAT-2026-0013/G1+G2]` after
the ship-fail-ship-fail-ship-fail cycle that burned ~$10 on missed
duplicates of `integration_workspace()` across 5 test files.

**v0.7.** Added cross-reference in the Haiku section to `WU.template.md`
frontmatter notes for the full `model:` / `effort:` field contract and
type-keyed defaults. v0.6 added the `## Haiku — when (and when not)`
section — graduated from `[FEAT-2026-0007/T06]` after the
defaults-by-WU-type policy established that Haiku is opt-in only and
recommended solely for small `docs`/`lessons` WUs. v0.5 added
§9 (explicit symbol-existence checks and completeness escalation triggers
in the Verification section when a WU requires new importable functions
or constants) — graduated from `[FEAT-2026-0007/G1-LESSONS]` after the
retry escalation ladder (T04) was declared complete with zero production
code committed and the `code` gate passed on the unchanged codebase.
v0.4 added §8 (verify cross-surface contract values against the
authoritative source rather than inventing them; carry a "Cross-repo
contracts" table in every plan-next gate review) — graduated from
`[FEAT-2026-0003/G3-LESSONS]`. v0.2 added the produces-list companion
in §3 and the hygiene-WU pattern in §7. v0.3 tightened §7 with the
canonical `T<NN>H` ID convention, the explicit PLAN.md wiring step, and
the evidence-from-events-log requirement. Expected to keep growing —
each multi-gate or multi-feature run that surfaces a rule that would
change how a future WU is written or executed graduates here from
LEARNINGS.md.
