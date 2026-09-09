---
gate: 3
status: open
feature_oracle: "python3 -m unittest tests.test_installed_copy_driver_e2e -q"
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:24569137b900ffe7745932a6208d35bbef1b2042:27968248a450a842ccd187b7dce0fb0ded934866:354329a74a735e3e0e9b4e2e22c2f64736a49f7c:3e1ed273ab9179bbc8a1519961dcece15f51277e:4fe99caff104dedcd9f52f2b84d9cdd440ebc1b9:5ff66b6e4d8a264f23709ea60706111a4c59ed11:831280d4f4defc99cf113cf1968b467da7b51390:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:863d8cb380c6778e41ebdf2c44ce04ef3367e8b4:97bcab1bc7244262cec901f46035f51dfdd07278:9a17cae3ef5843d005f5ee768f8ecce4027c0238:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:efde0847dce23ff89ddf38ac07d88f490cad8d66
  ran_at: 2026-09-09T13:35:58.186243+00:00
  ok: false
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: "test_skip_uses_recorded_failing_set"
    - gate: coverage
      failure_class: other
      failure_signature: "no_gate_marker"
---

# Gate 3 — the driver runs from a pinned build, and says which one

Gates 1 and 2 changed **what the driver runs**. Gate 3 changes **what the
driver *is*** while it runs: the process executes a build materialized outside
the working tree and recorded by tree hash, so a work unit editing
`specfuse/loop/*.py` no longer makes the running process stale relative to the
tree it is about to verify — and therefore no longer halts the run for a human
to restart it.

**This gate is deliberately alone.** `[FEAT-2026-0019/G1]` records that a
feature migrating the harness the driver itself runs cannot be decomposed into
separately-gated work units: each unit's exit oracle is the very surface being
migrated, so no unit can pass alone and the driver thrashes. The last attempt
cost $5.63 and 49 minutes before abandonment. Gate 3 therefore carries exactly
one substantive unit, T08, and its closing unit.

## What this is worth, measured on this repository

Counted in the `G2-PLAN` session that drafted this gate, over every
`.specfuse/features/*/events.jsonl` in this repo, on `driver_staleness_detected`
events carrying `halted: true`:

| Measure | Value |
|---|---|
| Halted restarts, repo-wide | **49** |
| Features that paid at least one | **14 of 71** |
| Worst features | FEAT-2026-0100 (7), **FEAT-2026-0109 (7)** |
| This feature's restarts | 3 in gate 1, 4 in gate 2 |
| Median dead time between the halt and the next event, repo-wide | **541s (9.0 min)** |
| Mean / p90 dead time | 3440s / 8518s |
| Total dead time across all 49 | **46.8 hours** |
| This feature's own dead time across its 7 restarts | **558s (9.3 min)** |
| Agent dollars burned by a halt | **$0.00** — no dispatch is spent |

**Read those two dead-time rows against each other before reading gate 3 as a
speed feature.** With an operator watching, a restart costs 23–238s: this
feature paid 9.3 minutes total for seven restarts, against the 194.4s gate 2
spent on a single broad run. The repo-wide median is 9 minutes and the mean is
57, because the distribution's tail is halts that landed when nobody was at the
keyboard. **The tax gate 3 removes is not wall clock — it is the loop's
inability to run unattended.** Gates 1 and 2 bought seconds; gate 3 buys the
property that a self-hosting feature can be left alone. State it that way or the
gate will read as a disappointment.

## Definition of done

- **The driver executes a pinned build, and records which one.** At startup, in
  a checkout carrying its own `specfuse/loop/` source, the driver materializes
  that package into a content-addressed build **outside the working tree**,
  keyed on `HEAD^{tree}` (T02's `_current_tree_hash`), and executes from it.
  The build's identity — the tree hash and the path — is recorded on the run
  where an operator reading an escalation can find it.
- **A unit editing `specfuse/loop/*.py` does not halt the run.** No
  `driver_staleness_detected` with `halted: true`, and no
  `EXIT_DRIVER_RESTART_REQUIRED`, when the run is pinned. The edit is still
  **recorded** — non-halting — naming the build it will take effect in. The
  halt is retired for the pinned case only; an unpinned run keeps today's
  behaviour byte-identically.
- **The pin is transparent to the operator's command.** `specfuse run --feature
  X` and `python3 -m specfuse.loop.loop --feature X` both still work and both
  reach the pinned execution; no new command is required to get it, and
  `resume_command_for` returns a command that reproduces the same pinned
  execution rather than one that silently escapes it.
- **#1040's guarantee survives the migration.** `build_provenance` today has two
  states — in-tree, and out-of-tree-therefore-suspect — and its warning calls an
  out-of-tree run "confidently wrong". A pinned run *is* out of tree and is not
  wrong, so the module gains a third state: **pinned at a recorded tree**. Only
  an **unidentified** out-of-tree build keeps the "confidently wrong" warning.
  A pinned run whose working tree has since moved reports both hashes and says
  which one it executed; it does not call itself an error, and it does not go
  quiet.
- **The cost is stated at the moment it is incurred.** A driver change landed by
  a unit takes effect at the **next run**, not at this gate's close. The driver
  says so, in words, at the point where it declines to halt — an operator must
  never have to infer from silence which build verified their gate.
- **A project that never installed the driver is unaffected.** No
  `specfuse/loop/` in the working tree means no pin, no re-exec, no new event,
  no changed behaviour — the same silence-by-construction posture
  `build_provenance` already takes for downstream projects.
- Per-criterion state and the narrow/broad oracle contract:
  `close-discipline.md` §5.

## This gate's oracle

```
python3 -m unittest tests.test_installed_copy_driver_e2e -q
```

Red on HEAD by construction — the module does not exist. T08 is the tracer
bullet that makes it green, and the only unit in this gate permitted to leave
stubs behind it.

**Binding on how the oracle is built: it must be out of process.** The oracle
drives a real driver **subprocess**, launched from a materialized pin, over a
temporary scaffold repository, with a stub `claude` executable on `PATH`
(`CLAUDE_CMD` at `specfuse/loop/loop.py:288` resolves `argv[0]` through `PATH`,
so this needs no new dispatch seam). It asserts **only** on that subprocess's
exit code and the `events.jsonl` it writes. It must **not** import
`specfuse.loop.loop` into the test process and assert on the result — an
in-process assertion measures the working tree, which is precisely the copy this
gate migrates away from, and a gate whose oracle measures that copy proves
nothing.

**How this advances gate 2's oracle.** Gate 1's oracle
(`tests.test_lazy_baseline_e2e`) and gate 2's
(`tests.test_tiered_verification_e2e`) both drive `loop.run()` **in process**,
with dispatch monkeypatched. That is what lets them assert richly on *what the
driver ran* — which gates, in which tier, in what order — and it is exactly what
makes them blind to *which build ran it*: the answer is fixed to the test
process's own imports before the first assertion executes. An in-process oracle
cannot observe its own provenance.

Gate 3's property **is** that provenance, so its oracle is the first in this
feature that cannot be in-process. Three claims it must carry, none of which
gate 2's oracle can phrase:

1. **Identity of the executing build.** The run records the build it executed,
   and that build is the pin rather than the working tree.
2. **Absence of the halt across a real driver edit.** A unit whose squash
   actually touches `specfuse/loop/loop.py` is followed by the next unit's
   dispatch **in the same process**, with no `halted: true` staleness event and
   no exit `3`. Gate 2's oracle monkeypatches dispatch and never squashes a
   driver edit, so it never reaches the halt seam at all.
3. **A moving working tree does not move what the run executes.** Mutate
   `specfuse/loop/loop.py` in the workspace mid-run; the pinned process's
   behaviour is unchanged, and it says which tree it is running against. This
   negative is what makes "pinned" mean something, and it is unstatable in an
   oracle whose subject and whose runner are the same import.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe (§4).** Done at draft time and recorded in
  `GATE-03-REVIEW.md` § "Runtime probe": a pinned copy of `specfuse/` was
  materialized and the driver's `main()` executed from it against this
  repository. It ran; `SPECFUSE_DIR` is `Path(".specfuse")` — cwd-relative, not
  `__file__`-relative — so the pin needs no path rewriting. `build_provenance`
  fired its "confidently wrong" warning on that run, which is the definition-of-
  done bullet above, observed rather than predicted.
- **Flag scope (§3).** T08 introduces no behaviour flag. It changes a default
  the driver applies to itself on every run in a driver source checkout, which
  is the §4 surface above, and its flag-scope table is the pinned/unpinned
  matrix in T08's body.
- **Predicate satisfiability (§2).** This gate raises no check to `ERROR` and
  flips no `WARNING` to blocking. It *narrows* an existing halt rather than
  widening one, so the adjacent risk is under-halting — bounded by the third
  definition-of-done bullet, which keeps the unpinned path byte-identical.
- **Review-summary obligation.** Gate 3 is terminal: there is no gate 4 to draft
  and no further oracle to advance. `G3-CLOSE` is a terminal `close` and carries
  the `close-discipline.md` §3 enumeration across all three gates.

## Reflection notes

<Written by the human at review time. Whether the pin ever made a close verify
against a build the gate had already moved past, how many restarts gate 3 itself
paid before the pin landed, and whether an unattended run actually completed.>
