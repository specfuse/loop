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

- [ ] **D-9** — run the harvester **twice** against a scratch repository with a planted finding. The second invocation must create **no** second issue. Record both invocations and the resulting issue list
- [ ] **D-10** — `specfuse-monitor run` against a real repository and environment files the issues the dry run predicted. Record the dry-run output and the resulting issue list **side by side**
- [ ] **D-11** — install `specfuse/loop/data/workflows/specfuse-monitor.yml` in the scratch repository, trigger it manually, and record the run URL, outcome, and issue list

> The duplicate-filing risk is the one worth watching. `T09` deliberately **replaced**
> `escalation.py`'s `--search` finder with a client-side filter over an explicitly
> `--limit`ed listing, because FEAT-2026-0046's retrospective recorded that GitHub's
> index does not reliably tokenise HTML-comment markers — and a search returning
> nothing silently files a duplicate on every retry. D-9 is the check that the
> replacement actually works against the real index.

### Entry — *(not yet run)*

```
date:
command:
observed output:
resulting issues:
notes:
```

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
