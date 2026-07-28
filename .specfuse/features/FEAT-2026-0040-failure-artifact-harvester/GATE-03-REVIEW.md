# Gate-3 review — drafted by `FEAT-2026-0040/G2-PLAN`

The operator's pre-arm document for gate 3 of `FEAT-2026-0040-failure-artifact-harvester`,
the **terminal** gate. Flip each gate-3 WU `status: draft` → `pending` only after
running the §4 substitute probe and working the **Open questions** in §6.

> **Filename note.** This file is `GATE-03-REVIEW.md`, not `GATE-02-REVIEW.md`. The
> driver's `assert_gate_review_exists` computes the expected filename from the
> **next** gate — the one this document arms — so a gate-2 `plan-next` writes
> `GATE-03-REVIEW.md`. `close-discipline.md` §4 records this as the single most
> expensive guard in the system: $53.11 of measured waste across 15 refusals,
> because the intuitive name is wrong.

---

## 1. What gate 2 shipped, and what gate 3 is authored against

Four substantive WUs, all `done`, **all on their first attempt**, no escalations and
no blocked reports. **$13.33 actual against $16.50 as drafted (−19%)**.

| WU | shipped | planned → actual |
|---|---|---|
| `T04` | The `dialect` contract — `CRON_DIALECTS`, four ERROR-severity validator rules, both example copies migrated, `derive-monitoring` emitting the field, a walk-discovered tree-wide sweep | $4.50 → **$6.25** |
| `T05` | `ServiceBusDlqAdapter` over a constructor-injected `ServiceBusDlqTransport`; one redacted artifact per dead-lettered message carrying `subscription` + `function` | $4.00 → **$1.53** |
| `T06` | `ErrorLogsAdapter`, `Http5xxAdapter`, `InvariantAdapter`, each resolving through `resolve_telemetry(component, environment)` | $4.00 → **$1.18** |
| `T07` | `specfuse/monitor/schedule.py` (`most_recent_firing`) plus `HeartbeatAdapter` — a stdlib-only cron evaluator over both arities that **refuses** on arity disagreement | $4.00 → **$4.37** |

**The shape gate 3 is authored against**, read from the shipped source rather than
assumed:

```python
# specfuse/monitor/adapters.py       (gate 1, done)
class TelemetryAdapter(Protocol):
    def fetch_failures(self) -> Iterable[FailureArtifact]: ...
class BrokerAdapter(Protocol):
    def fetch_failures(self) -> Iterable[FailureArtifact]: ...
def resolve_telemetry(component: str, environment: Mapping[str, object]) -> object: ...

# specfuse/monitor/artifact.py       (gate 1, done)
_TARGET_COORDINATE_FIELDS = {
    "dlq": ("subscription", "function"),
    "heartbeat": ("name",),
    "queue-stalled": ("subscription", "function"),   # <- already mapped, no adapter yet
}
```

Three consequences for gate 3's drafting, each checked rather than assumed:

- **`queue-stalled` is already in `_TARGET_COORDINATE_FIELDS`.** Gate 1 mapped the
  check type to `subscription` + `function` before any adapter existed, so `T08`
  needs **no change to `artifact.py`** — it builds through the existing
  `from_target`. The escalation trigger "`FailureArtifact` cannot carry what a stall
  finding needs" is therefore unlikely to fire, and if it does, that is a real
  finding about gate 1's model.
- **`fetch_failures()` takes no arguments**, so every adapter is configured at
  construction. `T10`'s CLI is therefore an *assembler*: it constructs adapters from
  config and calls one no-argument method. That is what keeps the dispatch registry
  small enough to be worth having.
- **`resolve_telemetry` exists and every gate-2 adapter already calls it with the
  component.** `T10` is the first caller that *chooses* the component, which is why
  its criterion 6 is a grep against reaching into `environment["telemetry"]`
  directly — the one shortcut that would quietly undo the #262 seam.

**What gate 2 deliberately did not prove.** Nothing has ever run end to end. Six
adapter classes exist and no code path constructs more than one of them at a time.
Gate 3 is where the parts meet, and where an enumeration bug becomes visible for the
first time.

---

## 2. What changed from `PLAN.md`'s gate-3 sketch, and why

`PLAN.md`'s scope boundary named three gate-3 elements: the issue lifecycle with
fingerprint dedupe, the `specfuse-monitor run` CLI, and the local plus GitHub Actions
runner surfaces. All three are drafted; none is deferred. One WU exists that the
sketch did not name, and it is not a surprise.

| sketch element | drafted as | change from the sketch |
|---|---|---|
| issue lifecycle with fingerprint dedupe | `T09` | Unchanged in scope. Sharpened in the one place the sketch left open: **which** part of `escalation.py` is reused. The runner seam, `_extract_issue_number`, the marker convention, and find-then-create are reused; `_find_existing_issue`'s `--search` strategy is **replaced**, per 0046's own retrospective. Two hardenings added that the same failure mode implies — an explicit `--limit` that is never read as "not found", and the fingerprint in the title as an optimization that correctness never rests on. |
| `specfuse-monitor run` CLI | `T10` | Unchanged in scope. Carries the gate's one **flag-scope table** (§3 below), because `--dry-run`'s headline claim needs crossing against the paths it gates. |
| local + GitHub Actions runner surfaces | `T11` | Unchanged in scope. Sharpened: the workflow ships as a **template under `specfuse/loop/data/`** and is explicitly *not* installed into this repo's `.github/workflows/`, which would schedule a monitoring run against a config that will never exist. |
| — | **`T08` — the `queue-stalled` adapter** | **Not an oversight.** `GATE-02-REVIEW.md` §2 named the gap before gate 2 was armed, §6.1 answer 3 records the operator placing it here so gate 2 stayed the adapter-*shape* gate, and gate 2's `RETROSPECTIVE.md` carries it as follow-up **FU-B**. It extends `T05`'s `BrokerAdapter` — queue depth and age-of-oldest are broker coordinates, not telemetry — and it is also, deliberately, **the one gate-3 unit whose evidence is complete in-loop**. |

**Ordering.** `T08` and `T09` are independent and both depend on nothing: the adapter
and the issue sink touch disjoint surfaces. `T10` depends on both — the CLI should
be able to enumerate all six check types rather than five, and it terminates in the
issue lifecycle. `T11` depends on `T10`, because a runner surface for a cycle that
does not exist is a template for nothing.

---

## 3. Existing-mechanism search (`planning-discipline.md` §1) — two verdicts

**Issue lifecycle — `found, reusing (with one deliberate exception)`.**

- **Command:** `grep -n "^def \|marker" specfuse/loop/escalation.py`
- **Surfaced:** `_correlation_marker` (line 47), `_default_runner` (145),
  `_find_existing_issue` (150), `_extract_issue_number` (178), `emit_escalation` (185)
  with idempotent find-then-create.
- **Read, not just grepped** — `emit_escalation`'s own docstring: *"Idempotent:
  searches for an open issue carrying the `needs-human` label and this correlation
  ID's marker before creating… Mirrors the find-then-create seam used by
  `GitHubBackend.on_feature_complete` in `gh_backend.py`."*
- **Verdict: reuse the seam, replace the finder.** `T09` reuses the injected-runner
  callable, `_extract_issue_number`, the HTML-comment marker convention, the
  `marker in body` re-check, and the find-then-create ordering. It does **not** reuse
  the `--search`-the-marker query, because FEAT-2026-0046's retrospective records it
  as unsafe for exactly this consumer:

  > *"`_find_existing_issue` passes an HTML comment to GitHub's `--search`, and
  > GitHub's issue search index does not reliably tokenise HTML comment content. …
  > a search that returns **nothing** does not [degrade safely] — it silently files a
  > duplicate on every retry, which is the one property this WU called load-bearing."*

  For an escalation firing a handful of times, a duplicate is noise. For a harvester
  whose entire value is dedupe across thousands of occurrences, an intermittently-blind
  finder makes the feature worthless with every gate green. **The retrospective names
  the fix in the same paragraph** — *"drop `--search` and filter `gh issue list
  --label needs-human --json number,body` client-side, which the existing body
  re-check already makes correct"* — and `T09` implements it. `escalation.py` itself
  is unmodified (`T09` criterion 12), so this is not a cross-feature contract change.

**Runner surface — `no existing mechanism, building new`.**

- **Commands:** `ls .github/workflows` → `ci.yml`, `leak-scan-content.yml`,
  `release.yml`. `grep -rn "workflows" --include='*.sh' --include='*.py' scripts/
  specfuse/loop/*.py` → **no match**. `find specfuse/loop/data -maxdepth 2 -type d`
  → `rules-local`, `docs`, `schemas`, `rules`, `templates` — **no `workflows/`**.
- **Verdict:** all three existing workflows are this repository's own gates; none is
  a consumer template and the scaffold ships no workflow to target projects today.
  So the shipping mechanism is new, and its first question — where the template lands
  and who copies it — is `T11`'s to decide rather than to inherit. That is also why
  `T11`'s escalation triggers name the packaging gates: a new directory under
  `data/` may need a `pyproject.toml` package-data change, and that is a distribution
  decision worth a human's eye.

**CLI entry point — `found, extending`.** `grep -n -A6 "\[project.scripts\]"
pyproject.toml` → four entry points (`specfuse-loop`, `specfuse-lint`,
`specfuse-monitor-lint`, `specfuse-stats`). `specfuse-monitor` is **not** among them
and does not collide with `specfuse-monitor-lint`. `T10` adds a fifth in the same
block, with `dependencies = []` unchanged — the package's zero-runtime-dependency
property is asserted through the CLI by `T10` criterion 2.

---

## 4. Arming discipline — §2, §3, §4 each answered

`planning-discipline.md` is binding at plan-next and arm time. All three checks are
addressed below; **none is silently omitted**, and the two that do not apply say why.

### 4.1 §2 — escalation-predicate satisfiability: **not applicable, with the reason**

> *What does this rule report on a spec/input already in its intended final state?*

Gate 3 introduces **no severity flip, no `WARNING`→`ERROR` change, and no blocking
check over existing repository state.** Every assertion it makes is over modules the
gate itself writes (`issues.py`, `cli.py`, `T08`'s adapter), a new entry point, and a
new template — so on a correct tree each reports **zero** by construction, because
the tree does not contain them until this gate writes them. `T11` criterion 10 is the
only assertion over *existing* state and it asserts the status quo (this repo's three
workflows, unchanged).

**The one place a flip was tempting, and was deliberately refused.** `T08` needs to
know what `stall_after: 15m` means. The obvious move is to bound the grammar in
`lint_monitoring.py` — which would be a severity flip, would make §4's runtime probe
mandatory on a gate that otherwise needs none, and would be a **breaking schema
change to a second field one release after `dialect`**. `T08` instead settles the
grammar *in the adapter*, refusing unparseable values rather than coercing them, and
the lint-time tightening is carried as a named follow-up (§7). Recorded here so the
absence of a probe is a decision, not a gap.

### 4.2 §3 — flag-scope table: **applicable, and `T10` carries it**

Gate 3 introduces exactly one behaviour flag: **`--dry-run`**, whose headline claim
is *"a dry run touches nothing outside this process."* That is precisely the class of
claim §3 exists for — it stays true until someone adds a convenience, and here the
defect would be a monitoring tool filing issues during a rehearsal. `WU-10`'s table
crosses the claim against all eight code paths. Two rows are worth the operator's eye
at arming:

- **`fetch_failures()` is NOT gated.** Deliberate: all environment access in this
  feature is read-only, and a dry run that does not read has nothing to print. Stated
  in the table so `--dry-run` is never mistaken for `--offline`. **If you disagree,
  say so now** — see Open question 2.
- **Every `gh` invocation IS gated**, and `T10` criterion 8 asserts an *empty*
  recorded call set, not merely a short one. That criterion is the table's oracle.

`--component` and `--env` are **selectors, not behaviour flags**: they narrow which
components and environment are enumerated and change no code path's behaviour on
those selected. `T11`'s `runner` dial is a **routing decision**, not a code-path gate.
Both recorded as assessed rather than omitted.

### 4.3 §4 — runtime probe: **not applicable, with the reason — plus one substitute worth running**

§4 binds a gate whose WUs flip a **default value** or a **severity**, and forbids
arming such a gate on "mechanical, nothing design-open." Gate 3 flips neither. It
adds modules, an entry point, and a template; it changes no existing rule's outcome
on any existing input; and §4.1 records why the one candidate flip was kept out.
`[FEAT-2026-0049/F4]` is why this reason is written out rather than left implicit —
that gate was armed on an unexamined "nothing design-open" and spun three times
(~$14) on a defect one local run would have exposed.

**The substitute probe, and it is one command.** Every "produces no in-loop
evidence" designation in `T09`, `T10`, and `T11` rests on a single inherited claim:
`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]`'s finding that `gh` returns auth errors
inside `claude -p`. That claim is from another feature, in another session, on
another day. **Before arming, confirm it still holds here:**

```
claude -p 'run: gh auth status; echo "exit=$?"'
```

- **If `gh` fails as recorded** — the expected outcome — the three WUs' stubbed-runner
  scoping and their D-9/D-10/D-11 deferrals are correctly drawn, and this document's
  hedged-verdict expectation stands.
- **If `gh` in fact works** — three WUs are scoped more pessimistically than they need
  to be, and the honest response is to re-arm them with real acceptance criteria
  instead of deferred ones, not to run them as drafted and report a hedge that was
  avoidable. That would be a materially better gate.

**Paste the observed output here before arming:**

```
<not yet run>
```

### 4.4 §5 — planning-WU cost floors: applied

Gate 3's only ceremony unit is `G3-CLOSE` at **$5.00**, exactly §5's `close` floor.
No `plan-next` unit exists in gate 3 — it is the terminal gate, so there is no next
gate to draft. The floors were not raised to absorb a retry; §5 is explicit that a
closing-WU retry is a defect to diagnose, and that the padding belongs in the gate
budget instead (§5's corollary, applied in §5.2 below).

---

## 5. Cost

### 5.1 Per-WU estimates for gate 3

| WU | type | planned | reasoning |
|---|---|---|---|
| `T08` | implementation | **$4.00** | New-module adapter work of the same shape `T05` cost $1.53 and `T06` cost $1.18. Priced at gate 2's adapter figure rather than at their actuals, per §5.3. The threshold-grammar decision and the skip-with-recorded-reason surface are the parts that are not mechanical. |
| `T09` | implementation | **$5.00** | The largest substantive unit. A new module, reuse across a package boundary, a finder that must be built *against* the shipped one, four negative observations, and the paging question. The one unit where getting it subtly wrong is invisible until production. |
| `T10` | implementation | **$5.00** | Config load, enumeration on the 0069 axis, a provider registry, the seam, watermark fallback in three failure modes, the run summary, and the flag-scope table's oracle. It is also the first unit that composes six adapters, so it is where a gate-1/gate-2 mismatch surfaces. |
| `T11` | implementation | **$4.00** | A template plus a dial plus docs. Structurally simple, but it introduces a new `data/` subdirectory and may touch packaging — which is exactly the kind of surprise that makes a "simple" unit spin. |
| `G3-CLOSE` | close | **$5.00** | `planning-discipline.md` §5 floor. Load-bearing (`auto_close_disabled: true`): three gates of oracles to re-run, a contract enumeration to have acknowledged, a deferred list of eleven items, and the `gate 1` literal. |
| | | **$23.00** | |

`GATE-03.md` carries `cost_budget_usd: 28.00` — the $23.00 sum plus one re-attempt of
the largest WU ($5.00), per §5's corollary. That padding is defensive, not a
prediction that a retry is normal.

### 5.2 `PLAN.md` re-baseline and the delta

| | |
|---|---|
| previous `planned_cost_usd` | **$52.00** — gate 1's five units ($20.00) plus gate 2's six ($27.00) plus gate 3's close placeholder ($5.00) |
| gate 3's four substantive units | **+$18.00** (`T08` $4.00, `T09` $5.00, `T10` $5.00, `T11` $4.00) |
| **new `planned_cost_usd`** | **$70.00** |
| **delta** | **+$18.00 (+34.6%)** |

`G3-CLOSE`'s $5.00 was already inside the $52.00 figure and is **not** double-counted.
Unlike the previous re-baseline's +108%, this one is the last: every gate is now
drafted, so the figure does not rise again. **Feature-to-date actual spend is $22.67**
against the $70.00 drafted plan.

### 5.3 The calibration signal, and what was done with it

Gate 2's implementation units came in **$13.33 against $16.50 (−19%)**, and the
underrun is not evenly spread: `T05` −62%, `T06` −70%, `T07` +9%, `T04` **+39%**.

`GATE-02-REVIEW.md` §5.3 refused to scale gate 2 down on gate 1's 72% underrun, on
the grounds that gate 1's units were unusually clean — new modules, no tree to
migrate, no severity flip — while `T04` was none of those things. **That call is now
measured, and it was right in the specific way it predicted:** the three new-module
adapter units landed near gate 1's shape, and the single over-run was exactly the
migration-and-severity-flip unit. Had the gate been priced at gate 1's actuals,
`T04` would have been budgeted near $1.25, cost $6.25, and halted the run on the
first unit of the gate.

Applied to gate 3: **`T08` is priced at $4.00, gate 2's adapter figure, not at
`T05`/`T06`'s $1.18–$1.53 actuals.** Two observations of cheap adapter work are not a
distribution — `planning-discipline.md` §5's own provenance records two earlier
revisions of that rule each generalising a floor from a single feature, and both were
wrong. And `T09` and `T10` are structurally *unlike* the cheap units: they cross a
package boundary, compose six existing modules, and build against a known-defective
predecessor. They are priced above the adapters for that reason, not by reflex.
See **Open question 1** — trimming is the operator's call, not this document's.

---

## 6. Open questions for the operator — work these before arming

1. **Trim `T08` to the adapter actuals?** `T05` and `T06` cost $1.18–$1.53 against
   $4.00 each, and `T08` is the same shape: a new adapter class, a stub transport, a
   handful of negative observations. Pricing it at $2.00 would be defensible. Against
   trimming: `[FEAT-2026-0069/G2-CLOSE]`'s lesson is that pricing a gate at its
   optimistic figure is how a budget halt lands mid-gate, and `T08` carries one thing
   the earlier adapters did not — the threshold-grammar decision, which is a design
   call inside an implementation unit. **Recommendation: leave it at $4.00.** The
   budget is a halt threshold, not a spend target, and under-running costs nothing.

2. **Is `--dry-run` allowed to hit the network?** `WU-10`'s flag-scope table says
   **yes**: a dry run performs the read-only `fetch_failures()` calls and gates only
   the writes (watermark, `gh`). The argument for it is that a dry run whose whole
   purpose is "show me what you would file" cannot show anything without reading, and
   every read in this feature is read-only by scope. The argument against is that
   some operators read `--dry-run` as `--offline` and will run it expecting zero
   external calls — against a production telemetry backend with real quota.
   **Recommendation: keep the current split, and make `T11`'s docs state it in one
   sentence.** If you prefer a separate `--offline`, say so now: adding a second flag
   after the first ships means two flags to explain forever.

3. **Does `stall_after` become required and bounded at lint time, and if so, when?**
   `T08` settles the grammar in the adapter and refuses unparseable values; the
   validator stays permissive, so a typo'd `stall_after` is a **runtime refusal, not
   a lint error**. That is a real gap, and closing it inside gate 3 would mean a
   severity flip, a §4 probe, and a second breaking schema change one release after
   `dialect`. **Recommendation: leave it out of gate 3** and carry it as the follow-up
   in §7 — but decide *now* whether that follow-up gets a home, because a gap named in
   a retrospective and given no owner is a gap that stays open.

4. **A `queue-stalled` target with no `stall_after` — skip, or fail?** The schema
   makes the coordinate optional, so such a config is *valid*. `T08` criterion 8
   skips the target and records the reason, and `T10` criterion 10 surfaces the skip
   in the run summary. The alternative is to raise, which makes a schema-valid config
   crash the harvester. **Recommendation: the drafted skip-and-report.** The failure
   mode it must avoid — a target silently monitored by nobody — is handled by the run
   summary, not by silence. Confirm you agree that the summary is a sufficient
   surface; if not, this becomes question 3 with a deadline.

5. **Is the operator run against the downstream .NET backend still planned, and does
   it now also cover a scratch GitHub repository?** `GATE-02-REVIEW.md` §6.1 answer 4
   recorded the Azure-side run as planned, which is what keeps `met` reachable for
   D-1 … D-8. Gate 3 adds **three GitHub-side deferrals** (D-9, D-10, D-11) whose
   proxy is an operator-journal artifact, and they need a *different* oracle: a
   scratch repository, not the .NET backend. If only the Azure run is planned, the
   terminal verdict is `met_locally` regardless of how gate 3 goes, and that should be
   expected now rather than discovered at `G3-CLOSE`.

6. **Where does the operator journal live?** D-9, D-10, and D-11 each name "an
   operator-journal artifact in the feature folder" as their verification proxy, and
   `G3-CLOSE` cites it. No such file exists yet and no convention in this repo names
   one. **Recommendation: `OPERATOR-JOURNAL.md` in this feature folder**, appended by
   the operator, one dated entry per run with the command, the observed output, and
   the resulting issue list. Decide the name before arming: a proxy nobody can find is
   the same as no proxy.

---

### 6.1 Operator decisions — recorded at arming

<Filled in by the human at review time. Record the answer to each question above,
and to the §4.3 probe, before flipping any gate-3 WU to `pending`.>

---

## 7. What gate 3 will **not** verify — known now, and the close must say so

`verification.yml` records that this repo "is a CLI tool with no deployable
components and will never carry a real monitoring.yml", and
`[FEAT-2026-0020/G1-CLOSE-INTERMEDIATE]` records that `gh` returns auth errors inside
`claude -p`. Together those bound gate 3's evidence completely:

| # | deferred criterion | why the loop cannot verify it | verification proxy |
|---|---|---|---|
| D-9 | `T09` — a second harvest of one fingerprint against a **real repository** creates no second issue | The stub returns whatever the test hands it. This is the exact shape 0046's own deferred item 2 took, and the property `T09` exists to fix | Operator runs the harvester twice against a scratch repository with a planted finding; both invocations and the resulting issue list recorded in the operator journal |
| D-10 | `T10` — `specfuse-monitor run` against a real repository and environment files the issues the dry run predicted | The write path terminates in `T09`'s `gh` surface; the dry-run path is in-loop and the write path is not | Same operator run, with the dry-run output and the resulting issue list recorded side by side |
| D-11 | `T11` — the shipped workflow, installed in a consumer repository, completes a scheduled run and files findings | A scheduled GitHub Actions workflow cannot be executed from a work-unit session at all. The template is asserted structurally only | Operator installs the template in a scratch repository, triggers it manually, records the run URL, outcome, and issue list |

**D-1 … D-8 from gate 2 carry forward unchanged** — every adapter is stub-verified,
no live Service Bus namespace or App Insights workspace has been reached, and no DST
transition has been observed in production. `RETROSPECTIVE.md` enumerates them.

**`T08` is the counterweight, and it matters that it exists.** It touches no `gh`
surface and needs no live environment: every one of its thirteen criteria is decidable
in-loop by a test, a grep, or an import. `T10`'s dry-run path and enumeration are
likewise real in-loop evidence. So gate 3 is **not** a gate that produces nothing —
the escalation `G2-PLAN` was told to report if it could not draft one is not
triggered. What gate 3 cannot do is prove that the GitHub surface underneath its
lifecycle behaves as the stubs say.

### Follow-ups this gate creates or carries

- **FU-D (new) — `stall_after` is unbounded at lint time.** `T08` settles the grammar
  in the adapter and refuses unparseable values; `lint_monitoring.py` still accepts
  anything. A typo'd threshold is a runtime refusal, not a lint error. Deliberately
  out of gate 3 (§4.1). Needs a home — see Open question 3.
- **FU-A (carried) — the fixture-signing contamination.**
  `tests/test_autosync_no_cwd_leak.py`'s `_make_repo` should set `commit.gpgsign=false`
  on its throwaway repos. Observed at gate 2's arming and again at its close. A
  one-line fixture change for a hygiene WU or a bug branch; no gate-3 WU owns the file.
- **FU-B (discharged) — `queue-stalled` has no adapter.** `T08` is the discharge.
  Listed here so the trail from `GATE-02-REVIEW.md` §2 → §6.1 answer 3 → `RETROSPECTIVE.md`
  FU-B → `T08` is unbroken.
- **FU-C (carried) — `azure_service_bus.py` at 81% line coverage**, concentrated in
  `build_azure_transport`, which cannot be exercised without the SDK on the path.
  `T08` extends that same module, so the figure will move; named so a future coverage
  tightening does not read it as neglect.

`G3-CLOSE` criteria 3, 7, 8, and 13 require each of the above in the terminal
retrospective. A close that reports "the issue lifecycle is verified" on stub
evidence is the failure this section exists to prevent.
