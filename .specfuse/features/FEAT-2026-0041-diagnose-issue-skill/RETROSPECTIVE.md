<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0041, `diagnose-issue` skill

Terminal close for the feature's only gate. Written by
`FEAT-2026-0041/G1-CLOSE`, attempt 1.

**Verdict: `met_locally`.** Every acceptance criterion in gate 1 was verified
in-loop, including the live `gh` round-trip that this project's LEARNINGS said
was impossible. The hedge is narrow and has exactly one entry: the
consumer-visible contract-change list below requires explicit *human*
acknowledgment (`close-discipline.md` §3), and no dispatched session can supply
it. See [Hedged-verdict follow-up record](#hedged-verdict-follow-up-record-close-discipline-2).

## Gate 1

One gate, terminal, four implementation WUs plus this close. Every
implementation WU passed on attempt 1; no WU was re-armed, blocked, or retried.

## What shipped

| WU | Deliverable | Attempts |
|----|-------------|----------|
| T01 | `specfuse/monitor/diagnosis.py` — the `Diagnosis` model, `render`, `parse`, one marker; `redaction._redact_text` promoted to public `redact_text` | 1 |
| T02 | `/diagnose-issue` skill on all three surfaces (canonical plugin, vendored `.specfuse`, `.claude` discovery symlink) | 1 |
| T03 | `specfuse/monitor/diagnose_cli.py` — the headless entry point, rendering through T01 exclusively | 1 |
| T04 | `tests/test_diagnosis_roundtrip_live.py` — the live `gh` create/comment/read-back/parse/close round-trip | 1 |

The shape that matters: **one renderer, one parser, one marker.** The skill and
the headless CLI are both *callers* of `diagnosis.render`; neither holds a
marker string or a section-heading template of its own, and T03's
`test_both_entry_points_render_identical_body` asserts byte-identical bodies
rather than field-by-field equality. That is what makes "identical format from
both entry points" a checked property instead of a promise.

`confidence` is a bounded float in `[0.0, 1.0]`; `fix_scope` is the closed
vocabulary `small | large | external`, validated in `Diagnosis.__post_init__`
and rejected — never defaulted — by `diagnose_cli.parse_analysis`. A defaulted
`fix_scope` would silently route real work past FEAT-2026-0042's gate, which is
the whole reason the field exists.

### Scope actually built, versus the roadmap row as written

The roadmap row bundled three things: diagnosis works, diagnosis runs headless,
and diagnosis runs *automatically*. **The third was cut at draft time** by
operator decision and is recorded in `PLAN.md` §"Scope: diagnosis and both entry
points; not the auto-trigger". This feature shipped the first two. The cut scope
— the per-component `diagnose: auto` dial, harvester auto-trigger on new
fingerprints, one-diagnosis-per-fingerprint dedupe — is now
[FEAT-2026-0074](../../roadmap.md#feat-2026-0074), filed by this close. The
roadmap detail section for FEAT-2026-0041 has been rewritten to describe what
was built rather than what was originally bundled.

### Documentation reconciled by this close

- **`docs/skills.md`** gains a `/diagnose-issue` entry under *Cross-cutting*,
  naming both entry points and stating plainly that nothing fires it
  automatically yet. T02 shipped the skill on its three surfaces but the
  catalog was not part of its produces-list; a skill absent from the catalog is
  a skill consumers do not find. The packaged copy at
  `specfuse/loop/data/docs/skills.md` is synced byte-for-byte, which
  `tests/test_scaffold_data_in_sync.py` asserts.
- **`.specfuse/roadmap.md`** — FEAT-2026-0041's row gains its folder and detail
  links (both were `—`), and its detail section is rewritten: the auto-trigger
  sentence is removed from **Goal**, a **Scope narrowed at draft time** block
  points at FEAT-2026-0074, and a **Shipped** block records what exists,
  including the sentence that diagnosis correctness is unverified. The row's
  `status` column is deliberately left `active` — the driver owns that flip.

## Oracles re-run fresh (close-discipline §1)

Re-run in this close session, exit codes read directly — not inherited from any
producing WU's self-report. The feature's criteria name the `code` gate set.

| Gate | Command | Result |
|------|---------|--------|
| tests | `python3 -m coverage run --source=specfuse -m unittest discover -s tests` | `Ran 2066 tests in 77.929s` — `FAILED (errors=11, skipped=4)` sandboxed; the 11 are sandbox artifacts, see below. Re-run after this close's own edits: `Ran 2066 tests in 75.141s`, same 11, no new failure |
| lint | `ruff check specfuse .specfuse/scripts tests scripts` | `All checks passed!` (exit 0) |
| security | `bandit -r specfuse .specfuse/scripts -ll` | severity `Medium: 0`, `High: 0` (exit 0) |
| coverage | `coverage report --fail-under=90` | `TOTAL 6371 544 91%` (exit 0) |
| leak-scan | `python3 .specfuse/scripts/leak_scan.py --all` | `leak-scan: gitleaks 8.30.1` / `leak-scan: clean` (exit 0) |
| plannext | `python3 .specfuse/scripts/lint_plan.py <feature_dir>` | `OK — ... is structurally valid.` (exit 0) |

Per-module coverage of what this feature added:

```
specfuse/monitor/diagnosis.py      80   7   91%
specfuse/monitor/diagnose_cli.py   48   6   88%
specfuse/monitor/redaction.py      20   0  100%
```

`diagnose_cli.py` at 88% is below the 90% project floor for that one file while
`TOTAL` is 91%; the gate measures the total, so this passed. The uncovered lines
are `main()`'s argv/stdin plumbing and `_read_file`. Named here rather than left
for a future reader to rediscover.

### The 11 errors are sandbox artifacts, and this is the third close to say so

Sandboxed, the suite reports 11 errors in `tests/test_lint_closing.py` and
`tests/test_autosync_no_cwd_leak.py`. Every one is the same shape:

```
subprocess.CalledProcessError: Command '['git', '-C', '/tmp/.../tmpd4mzksav',
'commit', '-q', '-m', 'init']' returned non-zero exit status 128.
```

`git commit` in a throwaway temp repo, denied by the command sandbox. Re-run
unsandboxed in this session:

```
$ python3 -m unittest tests.test_lint_closing tests.test_autosync_no_cwd_leak
Ran 11 tests in 1.417s
OK
```

T01, T02 and T03 each independently diagnosed this same set. Three sessions
spent attention on it. It is promoted to LEARNINGS by this close so a fourth
does not.

`skipped=4` includes `test_diagnosis_roundtrip_live` skipping by name under the
sandbox — which is the designed behaviour, not a gap. It ran for real in T04;
see below.

## T04's live `gh` round-trip — the raw evidence

**The live test executed. It did not skip.** T04 ran unsandboxed (its
`unsandboxed: true` frontmatter carries the rationale, and the driver emitted an
`unsandboxed_dispatch` event at `2026-08-03T20:26:45Z` before the attempt).
Quoted from T04's RESULT block, its own raw dumps between the `PROBE_BEGIN` /
`PROBE_END` markers `[FEAT-2026-0014/T01/preflight-must-dump-raw]` requires.
Only the account name and the already-`gh`-masked token line are elided; every
other line is verbatim.

Auth, unsandboxed:

```
PROBE_BEGIN
github.com
  ✓ Logged in to github.com account <account> (GH_TOKEN)
  - Active account: true
  - Git operations protocol: ssh
  - Token scopes: 'admin:org', 'admin:repo_hook', 'repo', 'workflow', 'write:packages'
  ✓ Logged in to github.com account <account> (keyring)
  - Active account: false
EXIT:0
PROBE_END
```

Live read against a real, pre-existing issue:

```
PROBE_BEGIN
{"body":"Found running the scaffold-upgrade merge gate against the generator
repo (2026-07-30). ...","number":309,"state":"OPEN","title":"upgrade_merge_gate.
collect_reports assumes .specfuse/scripts/lint_plan.py exists in target —
package-era scaffolds don't ship it","url":".../issues/309"}
EXIT:0
PROBE_END
```

Live write, read-back, and parse:

```
create:  PROBE_BEGIN
         .../issues/327
         EXIT:0
         PROBE_END

comment: PROBE_BEGIN
         .../issues/327#issuecomment-5171348579
         EXIT:0
         PROBE_END

view:    PROBE_BEGIN
         <!-- specfuse:diagnosis confidence=0.42 fix_scope=small -->

         **Root cause:**
         scratch WU T04 live round-trip probe

         **Evidence:**
         created by FEAT-2026-0041/T04 to prove render/post/read/parse over gh

         **Candidate fix:**
         none — this is throwaway scratch content

         **Confidence:** 0.42
         **Fix scope:** small
         EXIT:0
         PROBE_END
```

`parse(read_back_body) == Diagnosis(...)` — **equal: True**. The embedded marker
survives GitHub's own body handling; that is the specific risk a stub cannot
cover, and it is now checked rather than assumed.

Cleanup:

```
PROBE_BEGIN
✓ Closed issue #327 ([FEAT-2026-0041/T04] scratch issue — live gh round-trip
probe (safe to delete))
EXIT:0
PROBE_END
```

**Scratch issue: #327. Final state: closed**, in the same run that created it.
T04 searched for residue before creating (`gh issue list --search
"FEAT-2026-0041/T04 in:title" --state open` → `[]`) and again after (`[]`). No
scratch issue is left open by this feature.

The unittest itself also ran live in that unsandboxed session — `Ran 1 test in
4.247s / OK` — versus the sandboxed run's named skip, `setUpClass ... skipped
'gh live round-trip skipped: gh unauthenticated: github.com'` (`Ran 0 tests, OK
(skipped=1)`).

**One evidence gap, named rather than smoothed over.** The quoted `PROBE`
transcript above is T04's hand-driven probe (`confidence=0.42`); the committed
test constructs a different scratch `Diagnosis` (`confidence=0.33`) and creates
its *own* scratch issue, whose number T04's RESULT does not report. Both
executed. The post-run open-issue search returned `[]`, so the test's own
scratch issue was closed by its assertion path or `tearDown` as designed — but
its number is not in the record. Cost of the gap: if it had leaked, we would
know from the `[]` search that it did not, but we could not name it. A future
live-round-trip WU should require the *test* to print its issue number, not only
the probe.

## The LEARNINGS correction

`[FEAT-2026-0014/T01/gh-claudeP-broken]` has been corrected in place in
`.specfuse/LEARNINGS.md`. It attributed the failure to a `gh`-binary ↔ `claude
-p` subprocess interaction and ruled that **no** acceptance criterion may invoke
`gh` from a dispatched agent. The cause is the **command sandbox**.
`--dangerously-skip-permissions` governs permission *prompts*, not the sandbox,
which is exactly why the flag appeared not to help and why the wrong diagnosis
looked confirmed.

That entry was not merely inaccurate; it was expensive. FEAT-2026-0040 stubbed
every `gh` write path on its authority and deferred D-9, D-10 and D-11 to an
`OPERATOR-JOURNAL.md` that was never written, which is why **0040's close is
hedged to this day**. This feature is the counterfactual: same repo, same
driver, same `gh` binary, one unsandboxed WU — and the round-trip verified
in-loop on the first attempt.

The correction records the evidence (T04, above), keeps the confinement
discipline that was right all along (scope the escape to the single WU that
needs it), and does not overreach: `unsandboxed: true` is now a *sufficient*
lever for this surface, which the old entry explicitly denied.

## Consumer-visible contract changes (close-discipline §3) — awaiting operator acknowledgment

Four additions, one promotion. No removals, no renames of anything that existed
before this feature, no behaviour change to any existing surface.

1. **`specfuse.monitor.redaction._redact_text` → `redact_text`** — *promotion,
   module-private to public API*. The only item on this list that touches
   pre-existing code. `redact_artifact` is unchanged and now calls the public
   name. No caller outside the package could have depended on the underscore
   name, so this is additive in practice; it is listed because widening an API
   surface is a decision, not an accident. Rationale (`PLAN.md`): duplicating
   `_SECRET_PATTERNS` into `diagnosis.py` is how two redaction routines drift
   and one stops catching a secret shape.
2. **`specfuse.monitor.diagnosis`** — *new public module*. Exports `Diagnosis`
   (frozen dataclass: `root_cause`, `evidence`, `candidate_fix`, `confidence`,
   `fix_scope`), `render`, `parse`, `DiagnosisParseError`, `FIX_SCOPES`. The
   `<!-- specfuse:diagnosis confidence=... fix_scope=... -->` marker is a wire
   contract: FEAT-2026-0042 will parse it, so its shape is now consumer-visible
   and cannot change silently.
3. **`specfuse.monitor.diagnose_cli`** — *new module*, invoked as
   `python3 -m specfuse.monitor.diagnose_cli`. Exports `parse_analysis`,
   `render_headless`, `main`, `AnalysisParseError`. No console-script entry
   point was added to `pyproject.toml`; the module path is the interface.
4. **`/diagnose-issue`** — *new skill*, shipped on all three surfaces
   (`plugins/specfuse/skills/diagnose-issue/SKILL.md` canonical,
   `.specfuse/skills/diagnose-issue/SKILL.md` vendored, `.claude/skills/
   diagnose-issue` discovery symlink). User-visible command surface.

**Human acknowledgment of this list has not been obtained.** A dispatched close
session cannot obtain it, and `close-discipline.md` §3 requires it explicitly.
That is the sole reason this feature's verdict is `met_locally` rather than
`met`.

## Cost analysis

`events.jsonl` is the authoritative source; every `attempt_outcome` payload
reconciles exactly with the corresponding WU's `cost_usd` frontmatter field, so
there is no gap to report between the two.

| WU | Planned | Actual | Δ | Attempts |
|----|---------|--------|---|----------|
| T01 diagnosis contract | $4.00 | $1.35 | −$2.65 | 1 |
| T02 skill, three surfaces | $3.50 | $2.29 | −$1.21 | 1 |
| T03 headless entry point | $3.00 | $1.24 | −$1.76 | 1 |
| T04 live `gh` round-trip | $3.00 | $1.38 | −$1.62 | 1 |
| **Implementation subtotal** | **$13.50** | **$6.26** | **−$7.24** | 4 |
| G1-CLOSE (this WU) | $5.00 | not yet in `events.jsonl` | — | 1 |
| **Feature total** | **$18.50** | **≥ $6.26** | — | 5 |

The feature total is a **lower bound**: this close's own `attempt_outcome` event
is emitted by the driver *after* this session ends, so its cost cannot be read
from inside it. Everything else is exact.

Against the gate budget of $23.50 (the $18.50 plan plus one $5.00 re-attempt of
the largest WU, the defensive padding the GATE template prescribes while #260 is
open): implementation consumed 27% of the budget. The padding was not drawn on —
no WU needed a second attempt.

Wall-clock: 652.8 + 862.2 + 728.3 + 645.1 = **2888.4 s (48 min)** of dispatched
implementation time, all four WUs on `sonnet` at `effort: medium`.

**Why the estimates ran 54% high.** Every WU was scoped to one artifact with an
explicit produces-list and a pre-written existing-mechanism search, so no session
spent an attempt discovering what already existed. The estimates were priced for
a discovery phase that `PLAN.md` had already done. This is a good failure — but
it is a *systematic* one, worth pricing into the next feature of this shape
rather than treating as a happy surprise.

### Failure-class breakdown

(no non-passing attempts in scope)

Zero non-passing attempts across all five WUs: no `failure_class` or
`failure_signature` is non-null anywhere in this feature's `events.jsonl`.

## What the loop did NOT verify

**Diagnosis correctness — inherent, not deferred.** Every test in this gate
asserts *format, contract, and round-trip fidelity*. Not one asserts that a
diagnosis names the true root cause. A green gate here means the comment is
well-formed, the fields parse, both entry points agree byte-for-byte, and the
marker survives GitHub — it does **not** mean the diagnosis is right.

This is not a gap someone should close later with more tests. It is inherent:
no in-loop oracle can decide whether a root cause is correct, and `PLAN.md` §2
records the criterion "the diagnosis names the true root cause" as
unsatisfiable-by-construction so it was never written. It is stated here so a
reader of the green gate cannot mistake format fidelity for verified diagnosis
quality. The honest way to learn whether the diagnoses are any good is the one
the roadmap already prescribes: run `/diagnose-issue` interactively on real
findings with a human reading the output, before any auto-trigger dial
(FEAT-2026-0074) is turned on for a component.

Distinct from that, and smaller:

- **The unittest's own scratch issue number** is not in the record (see T04's
  evidence section). The `[]` residue search bounds the risk; the number itself
  is unrecoverable.
- **`diagnose_cli.main()`'s argv/stdin plumbing** (6 uncovered lines, 88% file
  coverage) is exercised by no test — the parse and render layers are.

### Deferred-verification list

Every acceptance criterion of gate 1 was verified in-loop. There is exactly one
obligation this session could not discharge, and it is not a criterion of the
gate but of `close-discipline.md`:

| Item | Why not verified in-loop | Where it actually gets checked |
|------|--------------------------|-------------------------------|
| Human acknowledgment of the consumer-visible contract-change list (`close-discipline.md` §3) | A dispatched close session is not a human; the rule requires explicit human acknowledgment by construction | Operator review of this retrospective's contract-change section, then `/accept-hedged-close` — see the follow-up record below |

No predecessor auto-close debt markers exist in this feature: it has one gate,
it never auto-closed, and no `<!-- specfuse:autoclose-debt gate=N -->` marker
appears anywhere in its folder.

## What worked

- **Naming the sandbox as the real cause at plan time, then confining the escape
  to one WU.** The escape's blast radius was a single work unit; every other WU
  was forbidden from touching `gh` and none reached for it. This is the pattern
  to copy: one WU carries the flag, its rationale is in frontmatter, and the
  gate document says out loud that a second WU wanting the flag is an
  escalation, not a copy-paste.
- **Byte-identical assertion between the two entry points.** "Identical format"
  is the kind of claim that decays into "similar enough" the moment it is
  checked field-by-field. `assertEqual` on the rendered strings cannot decay.
- **Promoting the redactor instead of copying it.** `redaction.py` is at 100%
  coverage and there is exactly one place a secret pattern lives.
- **`PLAN.md` doing the existing-mechanism search up front.** Four WUs, four
  first-attempt passes, and the estimates ran high precisely because the
  discovery work was already done.

## What I'd change

- **Require the live test to print its own scratch issue number**, not only the
  hand-driven probe's. T04 satisfied its criterion and still left one
  unidentifiable artifact behind. The criterion should say "the *test* reports
  the number it created."
- **Price WUs whose discovery is already done in the plan lower.** A 54%
  overshoot four times in a row is a pricing model that has not caught up with
  how much `PLAN.md` now front-loads.
- **Stop paying three sessions to re-diagnose the same 11 sandbox errors.** Now
  promoted to LEARNINGS; that should be the end of it.

## Lessons

Promoted to `.specfuse/LEARNINGS.md` by this close:

- `[FEAT-2026-0014/T01/gh-claudeP-broken]` **corrected in place** — the cause is
  the command sandbox, not the `gh` binary; `unsandboxed: true` is a sufficient
  lever for this surface, and a dispatched WU can exercise `gh` when run
  unsandboxed. Cites T04 as evidence.
- `[FEAT-2026-0041/G1-CLOSE/sandbox-git-temp-repo-errors]` — the 11
  `git commit`-exit-128 errors are a sandbox artifact with a known signature;
  re-run those two modules unsandboxed rather than re-diagnosing them.
- `[FEAT-2026-0041/G1-CLOSE/live-roundtrip-must-name-its-artifact]` — a WU that
  creates a remote artifact must have the *automated test* report its
  identifier, not only the hand-driven probe.
- `[FEAT-2026-0041/G1-CLOSE/one-renderer-two-callers]` — when a format must be
  identical across two entry points, give it one renderer, make both entry
  points callers, and assert byte-identical output.

## Issues and follow-ons

- **[FEAT-2026-0074](../../roadmap.md#feat-2026-0074)** — filed by this close
  for the scope cut at draft time: the per-component `diagnose: auto` dial,
  harvester auto-trigger on new fingerprints, and one-diagnosis-per-fingerprint
  dedupe. New ID, `max(scanned) + 1`; no existing ID renumbered or reused. The
  `gh`-backed source (d) of the next-ID scan was skipped — this close ran
  sandboxed, per the gate's rule that only T04 may reach GitHub — so the ID was
  chosen from the roadmap table, `PLAN.md` files, `LEARNINGS.md`, and
  `RETROSPECTIVE.md` files only. `FEAT-2026-0074` appears in none of them. The
  gaps at `0009`, `0065` and `0066` were left alone rather than filled.
- **FEAT-2026-0040's hedged close** is now unblocked in principle: the reason it
  hedged (the `gh` ban) has been refuted. Re-running its D-9/D-10/D-11 as an
  unsandboxed WU is a separate act and is *not* claimed here.

## Hedged-verdict follow-up record (close-discipline §2)

`verdict: met_locally`. One entry.

### D1 — Human acknowledgment of the contract-change list — OPEN

- **The criterion, verbatim:** "The close enumerates every consumer-visible
  addition, removal, or rename the feature makes across ALL its producing WUs —
  API surface, generated models, published schemas, CLI flags, whatever contract
  consumers depend on — and blocks on explicit human acknowledgment of the
  list." (`close-discipline.md` §3)
- **Why it is unverifiable in this environment:** the list is enumerated (four
  additions and one promotion, above). The acknowledgment is not something a
  dispatched agent can produce; the rule names a human as the actor.
- **The exact re-run condition that would upgrade the verdict to `met`:** an
  operator reads the *Consumer-visible contract changes* section above,
  acknowledges the five items — in particular `_redact_text` → `redact_text` and
  the `<!-- specfuse:diagnosis ... -->` marker becoming a wire contract that
  FEAT-2026-0042 will parse — and runs `/accept-hedged-close FEAT-2026-0041`,
  which records the acknowledgment and re-checks the verdict through the
  driver's `--recheck-verdict` primitive so the terminal flips fire through
  their one owner.

Until then the driver correctly leaves gate 1 `awaiting_review`, the roadmap row
`active`, and `PLAN.md` `active`. Nothing about the engineering is
outstanding — the acknowledgment is.

## Hedged verdict accepted

**Accepted verdict:** `met_locally`

**Operator reason (verbatim):** contract changes reviewed and accepted; nothing to rework

**Acknowledgment.** The operator was shown the five consumer-visible contract
changes enumerated above — the `_redact_text` -> `redact_text` promotion, the new
`specfuse.monitor.diagnosis` module and its `<!-- specfuse:diagnosis ... -->`
marker as a wire contract FEAT-2026-0042 will parse, the new
`specfuse.monitor.diagnose_cli` module, and the `/diagnose-issue` skill — and
acknowledged them explicitly. That acknowledgment is the act D1 was withheld for.

**Recorded:** 2026-08-03T21:16:21Z

**Standing follow-ups, carried forward — accepted, NOT discharged.** These remain
exactly as open as they were before this acceptance:

### D1 — Human acknowledgment of the contract-change list — OPEN

- **The criterion, verbatim:** "The close enumerates every consumer-visible
  addition, removal, or rename the feature makes across ALL its producing WUs —
  API surface, generated models, published schemas, CLI flags, whatever contract
  consumers depend on — and blocks on explicit human acknowledgment of the
  list." (`close-discipline.md` §3)
- **Why it is unverifiable in this environment:** the list is enumerated (four
  additions and one promotion, above). The acknowledgment is not something a
  dispatched agent can produce; the rule names a human as the actor.
- **The exact re-run condition that would upgrade the verdict to `met`:** an
  operator reads the *Consumer-visible contract changes* section above,
  acknowledges the five items — in particular `_redact_text` → `redact_text` and
  the `<!-- specfuse:diagnosis ... -->` marker becoming a wire contract that
  FEAT-2026-0042 will parse — and runs `/accept-hedged-close FEAT-2026-0041`,
  which records the acknowledgment and re-checks the verdict through the
  driver's `--recheck-verdict` primitive so the terminal flips fire through
  their one owner.

