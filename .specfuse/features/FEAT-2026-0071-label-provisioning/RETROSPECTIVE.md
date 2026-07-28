<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Retrospective — FEAT-2026-0071, label registry + provisioning on init/upgrade

**Correlation ID.** `FEAT-2026-0071/G1-CLOSE`. Single terminal gate; this is the
whole closing ceremony.

**Verdict.** `met_locally`. Every acceptance criterion of T01–T03 is verified by a
test that runs in this session, and every oracle below was re-run fresh here. The
hedge is not about the tests — it is that no work unit and no oracle ever invoked
the real `gh label create` or a successful real `gh label list`, and that close
obligation 3's consumer-visible contract list (headline: `init` and `upgrade` now
touch the network) has not yet been acknowledged by a human. Both are recorded
below with the exact re-run that upgrades the verdict to `met`.

## What was built

Three work units, strictly linear, all `done` at `attempts: 1`.

- **T01 — the registry.** `specfuse/loop/labels.py` ships `LABEL_REGISTRY`, seven
  frozen `LabelSpec` entries (name, colour, description, consumer). The names are
  *imported*, not retyped: `gh_features.FEATURE_LABEL` for `specfuse:feature`,
  `escalation.NEEDS_HUMAN_LABEL` and the five members of
  `escalation.CATEGORY_LABELS` for the rest. The hardcoded literal at
  `specfuse/loop/gh_features.py:28` became the module-level constant
  `FEATURE_LABEL` at line 21, and the `gh issue list` call at line 30 now uses it,
  so the string exists once. `tests/test_label_registry.py` recomputes the
  escalation label set from those modules at test time and asserts the registry
  covers it exactly — the drift guard.
- **T02 — provisioning.** `provision_labels(target, *, runner=None)` in the same
  module, following the injectable-runner seam `gh_backend.GitHubBackend` and
  `escalation.emit_escalation` already use. It lists existing labels first and
  creates only what is missing; it never passes `--force`, so an operator's edited
  colour or description survives every upgrade. It returns a `ProvisionReport`
  (`created` / `already_present` / `failed` / `skipped` / `reason`) on every path
  and raises on none — missing binary, list failure, unparseable output, and a
  per-label create failure that does not abandon the remaining labels.
- **T03 — the wiring.** `scaffold.init()` (line 564) and
  `scaffold.upgrade_specfuse()` (line 515) call
  `_provision_labels_best_effort()`, which wraps `provision_labels` in a bare
  `except Exception` — belt to T02's braces — and reports outcomes to **stderr**,
  never folding label names into the returned path list. The opt-out is
  `_labels_disabled()`: the `no_labels` keyword argument or the
  `SPECFUSE_NO_LABELS` environment variable.

## Oracles re-run fresh in this session

Every command below was executed in this closing session, from the repository
root, with the exit code read directly — no producing WU's self-report was
inherited.

| # | Command | Exit | Observed |
|---|---|---|---|
| 1 | `python3 -m pytest tests/test_label_registry.py -q` | 0 | `6 passed in 0.01s` |
| 2 | `python3 -m pytest tests/test_provision_labels.py -q` | 0 | `14 passed in 0.02s` |
| 3 | `python3 -m pytest tests/test_scaffold_label_provisioning.py -q` | 0 | `9 passed in 0.18s` |
| 4 | `python3 -m pytest tests/test_scaffold_init.py tests/test_scaffold_upgrade.py tests/test_init_integration.py -q` | 0 | `64 passed, 1 skipped in 1.67s` |
| 5 | `python3 -c "from specfuse.loop.labels import LABEL_REGISTRY; from specfuse.loop.gh_features import FEATURE_LABEL"` | 0 | both symbols import |
| 6 | `python3 -c "from specfuse.loop.labels import provision_labels"` | 0 | symbol imports |
| 7 | `grep -c '\-\-force' specfuse/loop/labels.py` | 1 (no match) | prints `0` — T02 criterion 6 satisfied |

Oracle 7's exit code is `1` because `grep -c` exits non-zero when the count is
zero. The criterion asserts on the **printed count**, which is `0`. Recording the
exit code without this note would misread as a failure.

**One unplanned real-binary observation.** `gh` *is* on this machine's PATH, and
`_provision_labels_best_effort` uses the default runner, so oracle 4's 64 tests
each ran a genuine `gh label list` subprocess in a pytest tmpdir. Probed directly,
in an empty temporary directory outside any git repository:

```
$ gh label list --json name,color,description --limit 1000
failed to run git: fatal: not a git repository (or any of the parent directories): .git
exit 1
```

So the *not-a-git-repository* degradation path is verified against the real
binary, not only against a stub — and oracle 4 passing is the evidence that the
degradation is silent enough not to perturb 64 pre-existing assertions. That is
one of six degradation paths; the other five remain stub-only.

### Failure-class breakdown

No failed attempts in this gate. All three producing work units recorded
`outcome: passed` on attempt 1 with `failure_class: null` and
`failure_signature: null` in `events.jsonl`, and `re_arm_count: 0` throughout.
There are no failure classes to break down.

## Cost analysis

Planned figures from `PLAN.md` (`planned_cost_usd: 14.50`) and the per-WU
frontmatter; actuals read from `events.jsonl` `attempt_outcome` payloads.

| WU | Planned | Actual | Delta |
|---|---|---|---|
| T01 — registry | $2.50 | $0.479112 | −$2.02 (−81%) |
| T02 — provision_labels | $4.00 | $1.200377 | −$2.80 (−70%) |
| T03 — scaffold wiring | $3.00 | $0.839388 | −$2.16 (−72%) |
| **T01–T03 subtotal** | **$9.50** | **$2.518877** | **−$6.98 (−73.5%)** |
| G1-CLOSE (this WU) | $5.00 | not yet in `events.jsonl` — this WU is mid-run | — |
| **Feature total** | **$14.50** | **$2.52 + close** | **−$6.98 before the close is priced** |

**The delta, named.** Implementation came in at **26.5% of its planned budget** —
$2.52 against $9.50. Even if this close spends its full $5.00 allocation the
feature lands near $7.52 against $14.50, roughly **48% under plan**. Wall-clock
was 1,142s (19.0 min) across the three producing units.

The estimate was wrong in a specific, repeatable way. All three units ran on
`sonnet` at `medium` effort and passed first try, so the plan was pricing in
retries that never happened, and the per-WU numbers appear to have been sized for
`opus`-tier work. T02 — the largest at $4.00 planned — was fifteen acceptance
criteria over a single function with an injected runner, which is *wide* rather
than *hard*: many cheap stub tests, no design ambiguity to resolve. Criterion
count is not a cost proxy. Gate budget was $19.50 against $2.52 actual
implementation spend, so the gate had ~7.7× headroom it never needed.

## What the loop did NOT verify

Four entries. This exceeds criterion 3's threshold of 2 entries / 30% of the
gate's criteria, so the sizing flag is raised — and its attribution is checked
rather than assumed, under `## What I'd change`.

**1. The real `gh label create` invocation.** T02 criteria 3, 5, 11, and 12 —
that a create call carries the entry's name, colour, and description; that exactly
the missing names are created; that one failure does not abandon the rest; that
the report distinguishes created/present/failed — are verified only through an
injected stub runner. T02 criterion 13 *forbids* invoking the real binary. So the
argument vector `["gh", "label", "create", name, "--color", colour,
"--description", description]` has never been accepted by `gh` itself. A wrong
flag spelling, a colour `gh` rejects, or a description length limit would pass
every test in this feature.
*Where it is actually verified:* the first real `specfuse init` or
`specfuse upgrade` against a GitHub repository missing at least one registry
label. **Post-merge operator step.**
*Upgrade condition:* run `specfuse init` (or `python3 -c "from
specfuse.loop.labels import provision_labels; print(provision_labels('.'))"`)
in a throwaway authenticated GitHub repository with none of the seven labels, and
observe `created` listing all seven and the labels present in `gh label list`.

**2. The successful real `gh label list` path, including its JSON parse.** This
repository already carries all seven labels — they were created by hand before the
feature was drafted. That makes it an oracle for the **idempotent-skip** path and
explicitly **not** for the create-a-missing-label path, as `PLAN.md` records. But
even the skip path was not exercised against real `gh` here: the only real
invocation this session made (see the oracle table) failed at the not-a-git-repo
check, before any JSON was produced. `json.loads(listed.stdout)` and the
`{item["name"] for item in existing}` comprehension have never seen real `gh`
output.
*Where it is actually verified:* the same post-merge run as entry 1, executed a
second time — the second run must report all seven under `already_present` and
`created == []`.
*Upgrade condition:* two consecutive real runs, the second producing zero creates.

**3. The unauthenticated-`gh` degradation path.** T02 criterion 9 is satisfied by
a stub returning a non-zero return code with an auth-flavoured stderr string. The
implementation does not actually distinguish "unauthenticated" from "not a GitHub
remote" from "list failed" — all three collapse into `skipped=True` with `gh`'s
stderr copied into `reason`. That is a defensible design (the report is honest
about what it saw), but the criterion's wording implies a discrimination the code
does not make, and no real unauthenticated `gh` stderr has ever been observed.
*Where it is actually verified:* `GH_TOKEN= gh auth logout` followed by a real
provisioning run inside a git repository with a GitHub remote.
*Upgrade condition:* observe `skipped=True` and a `reason` that names the auth
failure, with exit status still zero from the enclosing `init`/`upgrade`.

**4. The opt-out as a consumer actually reaches it.** T03 criteria 6 and 7 verify
`SPECFUSE_NO_LABELS` and the `no_labels` keyword argument at the `scaffold`
function boundary. Nothing verifies that a user of the **`specfuse` CLI** can opt
out, because the CLI lives in the umbrella repository and no `--no-labels` flag
exists — by design, per `PLAN.md`'s scope boundary. The roadmap's own detail
section said "`--no-labels` opts out", which was never true of what shipped; that
line is corrected in this close (criterion 7).
*Where it is actually verified:* a future umbrella release adding
`specfuse init --no-labels` that sets the same environment variable.
*Upgrade condition:* out of scope for this feature — this entry is a
documentation-accuracy deferral, discharged by the roadmap correction, not a
behavioural one.

## Lessons

Promoted to `.specfuse/LEARNINGS.md` — three entries under
`[FEAT-2026-0071/G1-CLOSE]`, on: a pure-filesystem entry point acquiring its first
subprocess call being a contract change even when the return type is unchanged;
an imported-vocabulary registry guarding names while leaving colours and
descriptions hand-kept; and roadmap prose that describes an interface the scope
boundary later rejected.

## Consumer-visible contract changes

Enumerated per close-discipline §3 across T01–T03. **This list has not yet been
acknowledged by a human** — that acknowledgment is the remaining condition on the
`met_locally` verdict, and the gate's `awaiting_review` checkpoint is where it
happens.

**1. `init` and `upgrade` now touch the network. — HEADLINE, behavioural, not
breaking by contract but breaking by expectation.**
Before this feature, `scaffold.init()` and `scaffold.upgrade_specfuse()` contained
no subprocess, no network, and no `gh` call: they were pure filesystem. That is
why they worked offline, inside CI containers, against non-GitHub remotes, and in
directories that were not git repositories at all. They now shell out to `gh label
list` and, when labels are missing, to `gh label create` — one subprocess plus up
to seven more, each a network round-trip to the GitHub API. Every downstream
consumer of these two commands inherits that. The mitigations are real and tested
(never fatal, exit zero on every degradation, opt-out available), but three things
change for consumers regardless: `init`/`upgrade` are **slower** when `gh` is
present and authenticated; they emit **new stderr output** when labels are created
or fail; and they make **outbound network calls** in environments — locked-down CI
runners, air-gapped builds, security-reviewed pipelines — where the previous
guarantee of "filesystem only" may have been a documented or audited property.
A consumer who needs the old behaviour sets `SPECFUSE_NO_LABELS=1`.

**2. New module: `specfuse.loop.labels`.** Addition. Public names:
`LABEL_REGISTRY`, `LabelSpec`, `ProvisionReport`, `provision_labels`.

**3. New public constant: `specfuse.loop.gh_features.FEATURE_LABEL`.** Addition,
value `"specfuse:feature"`. The literal at the `gh issue list` call site now reads
this constant. No behaviour change — same string, one home.

**4. New keyword argument `no_labels: bool = False`** on `scaffold.init()` and
`scaffold.upgrade_specfuse()`. Addition, defaulted, so positional and existing
keyword callers are unaffected.

**5. New environment variable `SPECFUSE_NO_LABELS`.** Addition. Any truthy value
disables provisioning in both entry points. Previously unread, so no consumer can
be relying on the old meaning.

**6. New stderr output from `init` and `upgrade`.** Addition. Two shapes:
`specfuse: label provisioning — created [...], failed [...]` when anything was
created or failed, and `specfuse: label provisioning raised unexpectedly: <exc>`
on an unexpected exception. Silent when every label was already present. A
consumer parsing these commands' stderr strictly would see new lines; stdout and
the return value are untouched.

**7. Asymmetry between `init()` and `init_specfuse()`.** Provisioning is wired
into `init()` only. A caller of `init_specfuse()` directly gets the pre-0071
pure-filesystem behaviour and **no** label provisioning, and `init_specfuse()`
does not accept `no_labels`. Worth stating because the two names are close enough
to be assumed equivalent.

**Explicitly NOT changed.** The return value of `init()` and
`upgrade_specfuse()` — still a sorted list of `.specfuse/` relpaths written, with
no label names folded in (T03 criterion 8). No file-writing, pruning, or manifest
behaviour changed. No label is renamed; `specfuse:feature` keeps its colon.
`escalation.py` was not modified. Nothing was removed.

## What went well

- **Importing the vocabulary instead of retyping it worked exactly as intended.**
  T01's coverage test recomputes the escalation label set from `escalation.py` and
  `gh_features.py` at test time. Two hand-kept lists of the same seven strings was
  the failure mode the plan named, and the registry structurally cannot have it.
- **The never-raise property was designed rather than patched.** T02 returns a
  report on six degradation paths; T03 adds a bare `except Exception` on top. The
  belt-and-braces looked redundant when planned and is not: it is what makes
  "an upgrade can never fail because a label could not be created" a statement
  about the call site rather than a statement about `provision_labels`'s current
  implementation.
- **The regression criterion earned its place.** T03 criterion 11's run over the
  three pre-existing scaffold suites was the only check that would have caught
  provisioning perturbing 64 unrelated tests — and, unplanned, it is the only real
  `gh` invocation anywhere in the feature.
- **Three WUs, three first-try passes, no re-arms, 26.5% of planned cost.** The
  linear dependency chain (data → function → wiring) meant no unit ever waited on
  an ambiguity another unit owned.

## What I'd change

**The sizing flag fired, and gate count is not what explains it.** Criterion 3's
mechanical rule — more than 2 entries or 30% of criteria under `## What the loop
did NOT verify` flags the feature's single-gate sizing — is tripped: 4 entries
against 9 criteria (44%). Per `[FEAT-2026-0046/G1-CLOSE]` in `LEARNINGS.md`, a
threshold that detects is not evidence about cause, so: **the attribution is
wrong here.** All four deferrals trace to one declared scope boundary — *no work
unit touches a real GitHub repository; every `gh` interaction runs through an
injected runner* — which `PLAN.md` chose deliberately and which a two-gate or
three-gate split would reproduce unchanged. Splitting T01/T02/T03 across more
gates adds review checkpoints; it does not put a real `gh label create` on the
wire. What would actually close entries 1–3 is **a different work unit**: a
live-`gh` integration unit, run against a throwaway repository, explicitly
exempted from T02 criterion 13's stub-only rule and marked as requiring network
plus authentication. That unit belongs in *this* gate, not in a second one.

**The plan's cost model priced retries that a linear chain does not incur.** $9.50
planned against $2.52 actual is not a small miss. The estimate treated criterion
count as a difficulty proxy — T02's fifteen criteria drew the largest budget while
being the widest-but-shallowest unit in the feature. A strictly linear graph with
no cross-unit ambiguity is the cheapest shape there is, and the plan should price
it as such.

**The roadmap promised an interface the scope boundary then rejected.** The detail
section said "`--no-labels` opts out" while `PLAN.md` had already ruled a CLI flag
out of scope in favour of `SPECFUSE_NO_LABELS`. Both documents were written for
this feature, and they disagreed from the start. The roadmap is the surface a
consumer reads; a scope decision that changes the shipped interface has to be
written back to it at decision time, not at close time.

## Follow-ups

- **FU-1 (discharges deferrals 1 and 2).** Run provisioning for real against a
  throwaway authenticated GitHub repository with none of the seven labels present;
  confirm all seven are created, then re-run and confirm zero creates and seven
  `already_present`. Upgrades the verdict to `met`. Post-merge operator step.
- **FU-2 (discharges deferral 3).** Observe a real unauthenticated `gh` run and
  confirm `skipped=True` with an auth-naming `reason` and exit zero from the
  enclosing command. Optionally split `reason` into a typed cause if the collapsed
  string proves insufficient in practice.
- **FU-3 (deferral 4, documentation only).** Discharged in this close by the
  roadmap correction. A `--no-labels` CLI flag remains available to a future
  umbrella release, reading the same `SPECFUSE_NO_LABELS` variable.
- **FU-4 (operator acknowledgment).** The consumer-visible contract-change list
  above, and specifically entry 1 — `init` and `upgrade` now make outbound network
  calls — needs explicit human acknowledgment at the gate's `awaiting_review`
  checkpoint before the verdict moves off `met_locally`.
