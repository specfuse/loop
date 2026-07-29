# Operator journal — FEAT-2026-0040

Verification proxy for the deferrals this feature could not settle in-loop. Named in
`GATE-03-REVIEW.md` §6.1 answer 6 and cited by **D-9**, **D-10** and **D-11**; the
terminal close recorded that it did not exist, which is why those three are open.

**This file is written by the operator, not by an agent.** Each entry records what a
human ran and observed. An agent may create this scaffold and may read the file to
report on it; it must not fill in an entry it did not witness. A journal an agent
wrote is not evidence — it is the agent citing itself, which is the failure
`.specfuse/rules/operator-escalation.md` names as writing the human's own
justification for them.

## How an entry discharges a deferral

Append one dated entry per run. Record the **command as invoked**, the **observed
output**, and the **resulting issue list** — the three things the deferral's upgrade
condition names. Then flip the checkbox and note the date.

When every box for a deferral is ticked, the verdict can be re-evaluated:

```
/accept-hedged-close FEAT-2026-0040     # records the acceptance
python3 .specfuse/scripts/loop.py --recheck-verdict FEAT-2026-0040
```

`--recheck-verdict` re-reads the close WU's verdict from disk and fires the terminal
flips through their single owner. Editing `PLAN.md`, `GATE-03.md`, or the roadmap row
by hand is the divergence that cost issue #49 — don't.

---

## How to run these — read before starting

### What the shipped code actually allows, and one constraint nobody wrote down

`specfuse-monitor run` resolves a provider by importing
`specfuse.monitor.providers.<provider_with_underscores>` — **only from inside that
package.** There is no plugin path, no entry-point discovery, no environment override.
The two resolvable providers are `azure_app_insights` and `azure_service_bus`.

**Consequence: a scratch repository cannot produce a finding on its own.** Run 2 was
described at arming as an independent oracle — "a scratch repository, not the .NET
backend" — and for D-11 that holds. For D-9 and D-10 it does not: the CLI has no way
to manufacture a finding without a live Azure environment behind it. That was not
visible at drafting time and is worth knowing before you book time for this.

There is a seam. `run_cycle()` accepts `transport_resolver=` and `gh_runner=`
separately, so a fake transport can plant a finding while the **real** `gh` files the
issue. `main()` does not expose it, so this needs ~15 lines of Python rather than a
flag. Both paths are given below; each says what it proves and what it does not.

### Prerequisites, both runs

```bash
pipx install specfuse            # or: pip install specfuse-loop
specfuse-monitor --help          # confirms the entry point resolves
gh auth status                   # must succeed — the harvester shells out to gh
```

The scratch repository needs the seven labels this project's registry declares.
`specfuse init <target>` provisions them, best-effort; confirm with `gh label list`.

Config lives at **`.specfuse/monitoring.yml`** in the repository you run from.
Watermarks land in `.specfuse/monitor-watermarks/`. The repository findings are filed
against is resolved from `git config --get remote.origin.url` — so **run from inside
the scratch clone**, not from this repo.

---

### Path A — the full oracle (Azure + scratch repo together)

Discharges **D-1 … D-11**. This is the only path that exercises the real thing end to
end, and the two runs stop being independent: the GitHub side needs a real finding,
and only Azure can produce one.

1. **Point a scratch repository's config at the real Azure environment.** Copy
   `.specfuse/monitoring.yml.example` into the scratch clone as
   `.specfuse/monitoring.yml` and replace the `acme-*` placeholders with the real
   coordinates. Validate before running anything:

   ```bash
   specfuse-monitor-lint .specfuse/monitoring.yml
   ```

2. **Export the credentials the config names.** Every `credentials:` value is an
   *environment variable name*, read via `os.environ.get`. A missing one yields an
   empty binding, not an error.

3. **Dry run first — it reads, and it does not write.**

   ```bash
   specfuse-monitor run --dry-run
   ```

   `--dry-run` is not `--offline`: it performs the read-only telemetry and broker
   calls and gates only the writes. Against a production backend that is real quota.
   Record the output — D-10 wants the dry-run listing and the resulting issue list
   **side by side**.

4. **Real run.**

   ```bash
   specfuse-monitor run
   gh issue list --label specfuse-monitor
   ```

5. **Run it again, unchanged.** This is D-9, and it is the single most important
   observation in this document:

   ```bash
   specfuse-monitor run
   gh issue list --label specfuse-monitor      # the count must NOT have grown
   ```

   A duplicate here means the client-side fingerprint filter that `T09` substituted
   for `escalation.py`'s `--search` does not hold against the real index — the exact
   defect it was written to avoid.

6. **Check the per-target split.** With two or more `dlq` targets on one component,
   confirm findings from different targets produced **different issues**. That is
   FEAT-2026-0069's binding constraint, and the thing this whole feature exists to
   get right.

7. **D-11 — the workflow.** Copy
   `specfuse/loop/data/workflows/specfuse-monitor.yml` into the scratch repo's
   `.github/workflows/`, add the secrets it references, trigger it via
   `workflow_dispatch`, and record the run URL and resulting issues.

8. **D-8 needs patience.** DST cannot be forced. Leave a heartbeat check running
   across a real transition and check the computed instant afterwards.

### Path B — GitHub side only, no Azure

Discharges **D-9** and **partially D-10**. Use when Azure is not available, or to
de-risk the GitHub half before booking the full run.

A fake transport plants the finding; the real `gh` files it. Run this from inside the
scratch clone:

The script is committed alongside this journal as **`plant-finding.py`**. It uses a
fake transport for the finding and leaves `gh_runner` at its default — the real `gh` —
which is the whole point. It refuses to run until you type the repository name back,
because it files real issues.

```bash
cd /path/to/scratch-clone
python3 plant-finding.py     # first run  — expect 2 issues created
python3 plant-finding.py     # second run — expect 0 created, 2 found
```

It plants findings on **two** `dlq` subscriptions rather than one, so the same run
also proves FEAT-2026-0069's binding constraint: two targets on one component must
produce **two** issues, not one collapsed bucket. Point the subscription names in
`fake_resolver` at whatever your `monitoring.yml` declares.

Run it **twice** and confirm the issue count does not grow.

**What Path B proves:** the fingerprint-keyed find-or-create works against the real
GitHub index — which is D-9 in full, and the highest-risk item.

**What it does not prove:** that `specfuse-monitor run` itself files what its dry run
predicted, because the CLI was not the entry point. D-10 stays partially open, and
the journal entry should say so rather than tick it.

---

## Run 1 — Azure: the downstream .NET backend

**Discharges D-1 … D-8.** Every adapter in gates 2 and 3 ran against a stub; no live
Service Bus namespace or App Insights workspace was ever reached.

- [ ] **D-1** — `fetch_failures()` returns one artifact per dead-lettered message, against the real peek API (paging, throttling, dead-letter metadata field names)
- [ ] **D-2** — the adapter issues no settlement call when a real peek iterator is exhausted or a lock lapses
- [ ] **D-3** — signature normalization collapses repeat occurrences of a *real* dead-lettered message or exception row
- [ ] **D-4** — a real KQL result set carries the columns the error-logs, http-5xx and invariant queries name
- [ ] **D-5** — ⚠️ *silent failure mode.* A real workspace returns a column matching the operator-authored `invariant.fingerprint_by`. A missing column still produces artifacts that fingerprint — **wrongly**. Check the column exists, not merely that findings appeared
- [ ] **D-6** — no query is built from observed data, against the real client
- [ ] **D-7** — ⚠️ *false-positive direction.* Real heartbeat telemetry is complete and timely enough that a silent schedule is distinguishable from a query gap
- [ ] **D-8** — the deployed schedule agrees with the computed instant **across a real DST boundary**. This one cannot be rushed; it needs a transition to actually occur

### Entry — *(not yet run)*

```
date:
command:
observed output:
resulting issues:
notes:
```

---

## Run 2 — a scratch GitHub repository

**Discharges D-9, D-10, D-11.** A *different* oracle from run 1: these are GitHub-side,
and the .NET backend cannot settle them. `gh` is unusable from a work-unit session —
`gh auth status` reports both the `GH_TOKEN` and keyring tokens invalid — so every
`gh` argument list the loop recorded went nowhere.

- [x] **D-9** — run the harvester **twice** against a scratch repository with a planted finding. The second invocation must create **no** second issue. Record both invocations and the resulting issue list
- [ ] **D-10** — `specfuse-monitor run` against a real repository and environment files the issues the dry run predicted. Record the dry-run output and the resulting issue list **side by side**
- [ ] **D-11** — install `specfuse/loop/data/workflows/specfuse-monitor.yml` in the scratch repository, trigger it manually, and record the run URL, outcome, and issue list

> The duplicate-filing risk is the one worth watching. `T09` deliberately **replaced**
> `escalation.py`'s `--search` finder with a client-side filter over an explicitly
> `--limit`ed listing, because FEAT-2026-0046's retrospective recorded that GitHub's
> index does not reliably tokenise HTML-comment markers — and a search returning
> nothing silently files a duplicate on every retry. D-9 is the check that the
> replacement actually works against the real index.

### Entry — 2026-07-29 · Path B · **agent-executed, awaiting operator countersign**

**Attribution, stated plainly.** This entry was produced by an agent running in the
operator's own session — where `gh` works, unlike a work-unit session — at the
operator's explicit request. The commands and outputs below were executed and
observed, not reconstructed. It is **not** an operator-witnessed entry, and the
checkboxes above are deliberately left unticked until the operator reviews it. See
the header: an agent may create this scaffold and read the file; the decision that
evidence is sufficient belongs to a human.

**Repository:** `clabonte/specfuse-monitor-scratch` (private, created for this).
**Config:** one component, **two** `dlq` targets (`orders-sub`/`ProcessOrder`,
`inventory-sub`/`ReserveStock`) — two rather than one so the same run tests
FEAT-2026-0069's per-target split alongside the dedupe.

**A blocking defect was hit first, and required a manual workaround.**

```
$ python plant-finding.py
CalledProcessError: ['gh','issue','create',...,'--label','monitoring-finding'] → exit 1
$ gh issue create ... --label monitoring-finding
could not add label: 'monitoring-finding' not found
```

`issues.py`'s `FINDING_LABEL = "monitoring-finding"` is absent from
`LABEL_REGISTRY`, so `provision_labels()` created seven labels and not the eighth the
harvester needs. **Zero issues filed.** Filed as
[#300](https://github.com/specfuse/loop/issues/300). Worked around by creating the
label by hand — which is why D-9 below is reported as *conditionally* observed.

**Run 1** — after the workaround:

```
scratch/scratch-worker: 2 finding(s) — created 2, updated 0, throttled 0
total: 2 finding(s) across 1 component(s)

#1 [monitor:cf9d2e6800ce] scratch-worker: MaxDeliveryCountExceeded
#2 [monitor:deb48dbe5fe4] scratch-worker: MaxDeliveryCountExceeded
```

**Run 2** — identical invocation, nothing changed:

```
scratch/scratch-worker: 2 finding(s) — created 0, updated 0, throttled 2
total: 2 finding(s) across 1 component(s)

#1, #2 — issue count unchanged
```

**What this establishes.**

- **D-9 — observed, conditional on #300.** `created 0` on the second run: the
  fingerprint-keyed find-or-create holds **against the real GitHub index**. This is
  the item that mattered — FEAT-2026-0046 recorded that GitHub does not reliably
  tokenise HTML-comment markers, so a `--search`-based finder silently duplicates on
  every retry, and `T09` replaced it with a client-side filter for that reason. The
  replacement works. The condition: this run needed a hand-created label, so the path
  is not yet reproducible from a clean install.
- **Two targets, two distinct fingerprints** (`cf9d2e6800ce` ≠ `deb48dbe5fe4`), two
  separate issues. FEAT-2026-0069's binding constraint — the reason this feature
  exists — observed against real GitHub for the first time.
- **D-10 — remains partially open, as predicted.** `specfuse-monitor run --dry-run`
  against this config failed with
  `missing required argument(s) ['fully_qualified_namespace', 'topic_name']`: the dry
  run *reads*, so it needs a real Azure transport. The CLI was not the entry point
  here — `plant-finding.py` was — exactly the limit the runbook records. **Do not tick
  D-10.**
- **D-11 — untouched.** The workflow was not installed or triggered.

### Countersigned — 2026-07-29T17:42:05Z

**The operator countersigned this entry and accepted D-9 as discharged**, instructing
the agent to record that decision. The judgment is the operator's; this paragraph is
the record of it, not a substitute for it.

**The open question that made this conditional is now closed.** D-9 was reported as
*conditionally* observed because the run needed a hand-created label to work around
[#300](https://github.com/specfuse/loop/issues/300). That is fixed and merged
(`b67b7ce`, PR #301): `monitoring-finding` is now in `LABEL_REGISTRY`, sourced from
the module that owns it, with a guard that walks the package and asserts every label
constant is declared.

**Re-verified after the fix, on a second fresh repository**
(`clabonte/specfuse-label-probe`), with **no manual step**:

```
ProvisionReport(created=['specfuse:feature', 'needs-human', 'gate-review',
                         'blocked-wu', 'triage-question', 'drafting-needed',
                         'merge-approval', 'monitoring-finding'], failed=[])

scratch/scratch-worker: 2 finding(s) — created 2, updated 0, throttled 0
  #1 [monitor:cf9d2e6800ce]   #2 [monitor:deb48dbe5fe4]
```

So the dedupe result stands on a run that is now reproducible from a clean install,
which is a stronger claim than the entry originally made. **D-9 is ticked.**

**D-10 and D-11 remain unticked and are not countersigned.** D-10's CLI path still
fails without a real Azure transport — `missing required argument(s)
['fully_qualified_namespace', 'topic_name']` — and D-11's workflow has never been
installed or triggered. Both need run 1 or a separate Actions run. Ticking them on
this evidence would be exactly the overreach this journal's header warns about.

**Evidence retained.** `clabonte/specfuse-monitor-scratch` (the original run, which
found #300) and `clabonte/specfuse-label-probe` (the post-fix re-verification) are
both private and kept, because this entry cites their issue numbers. Delete them only
after this record is no longer load-bearing.

---

## Not deferrals — recorded here so they are not mistaken for one

- **FU-C** — `specfuse/monitor/providers/azure_service_bus.py` sits at 79% line
  coverage; the uncovered lines are the lazy SDK transport factories, unexercisable
  without the SDK on the path. Run 1 is the first time a real transport is
  constructed, so it is worth re-measuring afterwards.
- **FU-A** ([#296](https://github.com/specfuse/loop/issues/296)) and **FU-D**
  ([#295](https://github.com/specfuse/loop/issues/295)) are filed and owned
  elsewhere. Nothing in this journal discharges them.
- **FU-E** was the close's main stated reason for `partially_met` and is **fixed** in
  `1341fe9` — the cron sweep flagged `T11`'s GitHub Actions workflow, whose
  `on.schedule.cron` is POSIX 5-field and has no dialect to declare. HEAD is green.
  It is not a deferral and needs nothing here.
