declared produces path(s) not in this WU's squash diff: .specfuse/skills/authoring-work-units/SKILL.md

Two escape hatches: `produces_unchanged:` — the deliverable already holds at HEAD; `produces_amended:` — the plan named a path this solution did not need.

Each listed path is a deliverable this WU declared in `produces:` but did not change. Either make the declared change this attempt, or — if the deliverable already holds at HEAD — say so in the RESULT block under `produces_unchanged:` with the command and output that show it (result-contract.md, closing obligation 1). Do not declare done while a deliverable is untouched and unjustified.

```result
produces_unchanged:
  - path: .specfuse/skills/authoring-work-units/SKILL.md
    justification: <the command you ran and its output showing the deliverable already holds>
produces_amended:
  - path: .specfuse/skills/authoring-work-units/SKILL.md
    reason: <why this WU no longer needs this produces: path>
```

A bookkeeping guard refused this attempt's pass. The previous attempt's edits are STILL PRESENT in the working tree, and verification already PASSED on them — re-authoring them is the one thing not to do. Apply only the mechanical fix below, then re-emit the RESULT block in full. Make the declared `produces:` change this attempt, or justify it as already satisfied under `produces_unchanged:` in the RESULT block, before declaring done.

Retained diff (your tree is still here):

```diff
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/GATE-01.md b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/GATE-01.md
index 2af381e..f089c0c 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/GATE-01.md
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/GATE-01.md
@@ -3,6 +3,13 @@ gate: 1
 status: open
 feature_oracle: "python3 -m unittest tests.test_fix_unit_insertion_e2e -v -b"
 cost_budget_usd: 40.00
+baseline:
+  sha: 932e8687fdb8488be4274b4c0b994277386b55b1
+  probed_at: 2026-09-26T16:53:07.231764+00:00
+  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:19e6172a5f8ed4e64796dcbec75a5c167dfaa326:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:5ff66b6e4d8a264f23709ea60706111a4c59ed11:7236c0b74a800bb48cc28ab6dc46543c53a4dc90:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:9d592b0fb98f8caf8cbe2b603e967434ec0199bf:9f955f7d0d0875a1252a7fedb2e56a6960f4abda:a122d1db4fd063b79f10e884eb141d8209a59054:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d664745f3d8e8d366a9f5029d78452efa5fda16f:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
+  entry_sha: 932e8687fdb8488be4274b4c0b994277386b55b1
+  source: attributed:FEAT-2026-0115/T04
+  failing: []
 ---
 
 # Gate 1 — a block that names its fix unit continues the gate
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/PROGRESS.md b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/PROGRESS.md
index 5443a82..6b57015 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/PROGRESS.md
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/PROGRESS.md
@@ -2,3 +2,4 @@
 - **FEAT-2026-0115/T02**: attempt 2 outcome=spinning_signature_repeat
 - **FEAT-2026-0115/T03**: attempt 1 outcome=passed
 - **FEAT-2026-0115/T02**: attempt 1 outcome=passed
+- **FEAT-2026-0115/T04**: attempt 3 outcome=passed
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-04-document-the-contract.md b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-04-document-the-contract.md
index 157b11a..307c31f 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-04-document-the-contract.md
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-04-document-the-contract.md
@@ -1,8 +1,8 @@
 ---
 id: FEAT-2026-0115/T04
 type: implementation
-status: pending
-attempts: 0
+status: done
+attempts: 3
 planned_cost_usd: 3.00
 produces:
   - .specfuse/rules/result-contract.md
@@ -12,6 +12,10 @@ produces:
   - specfuse/loop/data/docs/methodology.md
   - .specfuse/verification.yml.example
   - specfuse/loop/data/verification.yml.example
+duration_seconds: 1163.681
+cost_usd: 2.776901
+input_tokens: 240
+output_tokens: 34698
 ---
 
 # Document `blocked_next:` where the sessions and the authors read
diff --git a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
index bc8ed95..df82c82 100644
--- a/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
+++ b/.specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/events.jsonl
@@ -13,3 +13,10 @@
 {"timestamp": "2026-09-26T16:33:29.997845+00:00", "correlation_id": "FEAT-2026-0115/T03", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 225.451, "cost_usd": 1.3358510000000003, "input_tokens": 96, "output_tokens": 23777, "cache_read_input_tokens": 3862865, "cache_creation_input_tokens": 81329, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-03-auto-close-and-brief.md", "specfuse/loop/gate_eval.py", "specfuse/loop/loop.py", "tests/test_fix_unit_insertion_bookkeeping.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
 {"timestamp": "2026-09-26T16:33:29.997999+00:00", "correlation_id": "FEAT-2026-0115/T03", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 225.451, "cost_usd": 1.3358510000000003, "input_tokens": 96, "output_tokens": 23777, "cache_read_input_tokens": 3862865, "cache_creation_input_tokens": 81329}], "type": "implementation", "re_arm_count": 0, "cost_usd": 1.335851, "cumulative_cost_usd": 1.335851, "attempts_lifetime": 1, "planned_cost_usd": 3.0}}
 {"timestamp": "2026-09-26T16:35:05.871522+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_build_pinned", "source": "driver", "source_version": "0.25.0", "payload": {"tree": "cda5ba7aadd38d0fa6d7dc7a9c6273975bc961dd", "path": "/private/var/folders/zc/rgq11x850d78dx_kf1fd4vx80000gn/T/specfuse-pins/cda5ba7aadd38d0fa6d7dc7a9c6273975bc961dd/specfuse/loop"}}
+{"timestamp": "2026-09-26T16:35:06.003036+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "task_started", "source": "driver", "source_version": "0.25.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 1}}
+{"timestamp": "2026-09-26T16:35:06.003040+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "re_arm_dispatched", "source": "driver", "source_version": "0.25.0", "payload": {"re_arm_count": 1, "reason": "Both sessions reported status: blocked with a real reason (the unit forbade the edits its own design needed); the driver read the block-scalar RESULT as complete (#3436) and escalated as a spin. Unit re-scoped to write-then-evaluate; override because the escalated signature is the parse defect, not the unit."}}
+{"timestamp": "2026-09-26T16:46:31.815626+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "passed", "duration_seconds": 685.709, "cost_usd": 3.124198799999999, "input_tokens": 156, "output_tokens": 58420, "cache_read_input_tokens": 9614814, "cache_creation_input_tokens": 154181, "model": "sonnet", "effort": "medium", "failure_class": null, "failure_signature": null, "failure_excerpt": null, "files_touched": [".specfuse/features/FEAT-2026-0115-blocked-with-a-fix-unit-continues/WU-02-stop-classes-and-caps.md", "specfuse/loop/loop.py", "tests/test_fix_unit_insertion_e2e.py", "tests/test_fix_unit_insertion_refused.py"], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
+{"timestamp": "2026-09-26T16:46:31.815869+00:00", "correlation_id": "FEAT-2026-0115/T02", "event_type": "task_completed", "source": "driver", "source_version": "0.25.0", "payload": {"attempts": 1, "attempts_usage": [{"attempt": 1, "duration_seconds": 685.709, "cost_usd": 3.124198799999999, "input_tokens": 156, "output_tokens": 58420, "cache_read_input_tokens": 9614814, "cache_creation_input_tokens": 154181}], "type": "implementation", "re_arm_count": 1, "cost_usd": 3.124199, "cumulative_cost_usd": 3.124199, "attempts_lifetime": 3, "planned_cost_usd": 5.0}}
+{"timestamp": "2026-09-26T16:46:31.822496+00:00", "correlation_id": "FEAT-2026-0115", "event_type": "driver_staleness_detected", "source": "driver", "source_version": "0.25.0", "payload": {"gate": 1, "wu_id": "FEAT-2026-0115/T02", "driver_paths": ["specfuse/loop/loop.py"], "halted": false, "reason": "driver_restart_required", "pinned_tree": "cda5ba7aadd38d0fa6d7dc7a9c6273975bc961dd", "next_pin_tree": "e00d97b42e626f00a759afaf791e209a592ead49"}}
+{"timestamp": "2026-09-26T16:46:31.895685+00:00", "correlation_id": "FEAT-2026-0115/T04", "event_type": "task_started", "source": "driver", "source_version": "0.25.0", "payload": {"type": "implementation", "model": "sonnet", "re_arm_count": 0}}
+{"timestamp": "2026-09-26T16:53:07.119738+00:00", "correlation_id": "FEAT-2026-0115/T04", "event_type": "attempt_outcome", "source": "driver", "source_version": "0.25.0", "payload": {"attempt": 1, "outcome": "failed", "duration_seconds": 395.144, "cost_usd": 0.8116977999999999, "input_tokens": 66, "output_tokens": 10723, "cache_read_input_tokens": 2360199, "cache_creation_input_tokens": 58074, "model": "sonnet", "effort": "medium", "failure_class": "tests", "failure_signature": "test_distilled_file_is_under_its_own_sub_budget", "failure_excerpt": "### tests: FAIL\n#207: surefire failures name Class.method, not 'FAIL: test_*' \u2014 ... ok\nFAIL: test_distilled_file_is_under_its_own_sub_budget (test_binding_block_allocation.BindingBlockAllocationTests.test_distilled_file_is_under_its_own_sub_budg\n...\nve.md link graph \u2014 0 error(s), 1 warning(s)\nNO VERDICT FOUND: the gate command produced no recognisable pass/fail summary anywhere in its output \u2014 the lines above are the tail only, and may be unrelated to the failure. Run the command directly.", "files_touched": [], "agent_status": "complete", "agent_blocked_reason": null, "re_arm_count": 0}}
diff --git a/.specfuse/rules/result-contract.md b/.specfuse/rules/result-contract.md
index 5425926..220ed3e 100644
--- a/.specfuse/rules/result-contract.md
+++ b/.specfuse/rules/result-contract.md
@@ -5,23 +5,23 @@ Licensed under the Apache License, Version 2.0. See LICENSE.
 
 # Rule: the RESULT block contract
 
-A dispatched work-unit session ends with a single fenced `result` block as the
-very last thing in its output. The driver reads it; a dispatched session that
-emits none is treated as a failed attempt. The RESULT is **advisory** — the
-driver re-runs verification itself, and that is what decides done.
+A dispatched work-unit session ends with one fenced `result` block as the last
+thing in its output; the driver reads it, and a session emitting none is a
+failed attempt. The RESULT is **advisory** — the driver re-runs verification
+itself, and that decides done.
 
 ## Who reads it — emit it only when something does
 
-This block is a **machine interface**, not a report. Emit it when a program is
-on the other end: a work-unit session the driver dispatched (always), or a
-skill invoked **non-interactively** from a calling program that parses the
-outcome (`fix-bug` under `autofix_invoke` is the live example).
+This block is a **machine interface**, not a report. Emit it only when a
+program is on the other end: a dispatched work-unit session (always), or a
+skill invoked **non-interactively** from a calling program parsing the
+outcome (`fix-bug` under `autofix_invoke`).
 
-Do **not** emit it on an interactive run — a human who typed `/pick-feature`
-has no parser, and the block lands as a slab to scroll past, the verbosity
-[`human-output.md`](human-output.md) exists to prevent. Report to them per
-that rule instead. When in doubt: a slash command typed by a person is
-interactive; a `claude -p` dispatch is not.
+Do **not** emit it on an interactive run — a human typing `/pick-feature` has
+no parser, and the block becomes a slab to scroll past, the verbosity
+[`human-output.md`](human-output.md) prevents. Report per that rule instead.
+Rule of thumb: a person-typed slash command is interactive; a `claude -p`
+dispatch is not.
 
 ## The cycle: state intent, act, verify, report
 
@@ -34,16 +34,16 @@ cycle; this file is normative on how the loop surface reports step 4.
 2. **Act.** Stay inside that scope. "While I was here I also fixed X" is drift;
    the work unit's **Do not touch** section is binding.
 3. **Verify.** Re-read what you produced — Write/Edit reports the action taken,
-   not the property you wanted — and run the work unit's own verification
-   commands, in declared order, with full output. On the loop that set is the
+   not the property you wanted — and run the unit's own verification commands,
+   in declared order, with full output. On the loop that set is the
    **per-attempt (narrow) tier**: the unit type's gates minus any declaring
    `tier: broad`, with `tests` through its `narrow_command` over the unit's
    `produces:` test modules. The full suite, coverage and every `tier: broad`
-   gate are the driver's, once per gate — running them in-session buys nothing
-   the driver does not re-run. "I assume the tests still pass" is not
-   verification. A behavioural claim needs a run, not a source reading; a
-   rule-or-severity claim needs a **negative observation** — the rule seen
-   rejecting a purpose-built bad input.
+   gate are the driver's, once per gate — running them in-session buys
+   nothing. "I assume the tests still pass" is not verification. A
+   behavioural claim needs a run, not a source reading; a rule-or-severity
+   claim needs a **negative observation** — the rule seen rejecting a
+   purpose-built bad input.
 4. **Report.** Report only what verification confirmed.
 
 A failing check leaves you in one of three situations: correctable locally
@@ -67,6 +67,10 @@ acceptance_criteria:
     met: true | false
     evidence: <how you know — a test name, a behavior, a line reference>
 blocked_reason: <present only when status is blocked>
+blocked_next:                      # optional — a drafted fix unit
+  kind: fix_unit
+  file: <path to the drafted WU>
+  id: <the drafted WU's id>
 produces_unchanged:                # optional — obligation 1 below
   - path: <a produces: entry, verbatim>
     justification: <the command you ran and its output showing the deliverable already holds>
@@ -78,38 +82,41 @@ produces_amended:                 # optional — obligation 1 below
 
 `summary` is backward-looking by this contract's own definition — one sentence
 on what changed. `forward_note` is the other half: what surprised you, or what
-the next unit should know, that `summary` does not capture. It is optional and
-never required by any guard. Omit it and nothing changes: the driver's
-`PROGRESS.md` entry is exactly what it would have written without this field
+the next unit should know, that `summary` misses. Optional, never required by
+any guard — omit it and the driver's `PROGRESS.md` entry is unchanged
 (FEAT-2026-0106/T02).
 
 ## Rules
 
-1. **No git.** You edit files only. The driver stages, squashes, and commits one
-   trailer-carrying commit per work unit.
-2. **Verify before you report.** Do not report success you have not checked.
-3. **Blocked is a valid, respectable outcome.** A precise `blocked_reason` after
-   one honest attempt is cheaper than three attempts chasing a `complete` that
+1. **No git.** Edit files only. The driver stages, squashes, and commits one
+   trailer-carrying commit per unit.
+2. **Verify before reporting.** Do not report success you have not checked.
+3. **Blocked is a valid, respectable outcome.** A precise `blocked_reason`
+   after one honest attempt beats three attempts chasing a `complete`
    verification keeps rejecting.
-4. **Stop at a boundary rather than working around it.** Generated directories,
-   secrets, and `.git/` internals are off-limits
+4. **Stop at a boundary rather than working around it.** Generated
+   directories, secrets, and `.git/` internals are off-limits
    ([`never-touch.md`](never-touch.md),
-   [`security-boundaries.md`](security-boundaries.md)); weakening a failing gate
-   to make a unit pass is the same class of failure. Silence at a boundary is
-   not permission.
-5. **No secret-looking values in evidence.** The block is read by the driver and
-   may be archived.
-6. **Never mint or rewrite a correlation ID to make something fit.** A
-   well-formed ID that disagrees across surfaces is `blocked`, not a rename
+   [`security-boundaries.md`](security-boundaries.md)); weakening a failing
+   gate to pass is the same failure class. Silence at a boundary is not
+   permission.
+5. **No secret-looking values in evidence.** The driver reads and may archive
+   this block.
+6. **Never mint or rewrite a correlation ID to make it fit.** A well-formed
+   ID disagreeing across surfaces is `blocked`, not a rename
    ([`correlation-ids.md`](correlation-ids.md)).
 7. **A "pre-existing" failure claim cites the commit it was measured on.**
-   Calling a failure pre-existing is a claim about a *different* commit —
-   typically the merge-base — and nothing observed on your own branch
-   establishes it. Name the command and commit, give the numbers from both
-   sides, and emit `status: blocked` rather than asserting an unmeasured
-   baseline: a mass of errors sharing one signature (network refused,
-   unresolvable build dependencies) reports where the suite ran, not the
-   repository (#2075).
+   Calling a failure pre-existing is a claim about a *different* commit,
+   typically the merge-base, that nothing on your own branch establishes.
+   Name the command and commit, give the numbers from both sides, and emit
+   `status: blocked` rather than asserting an unmeasured baseline: a mass of
+   errors sharing one signature (network refused, unresolvable build
+   dependencies) reports where the suite ran, not the repository (#2075).
+8. **A block may name its own fix.** `blocked_next:` points at a drafted work
+   unit — `provenance: agent`, `status: draft`, the five WU sections filled —
+   the driver inserts ahead of this one and re-arms it, when the feature runs
+   `auto` and the draft passes the arm checks; no `blocked_next` escalates
+   unchanged.
 
 ## Closing obligations for implementation WUs (FEAT-2026-0049)
 
@@ -119,19 +126,18 @@ never required by any guard. Omit it and nothing changes: the driver's
    `produces_amended:` (the plan named a path the solution didn't need — drop
    only, never add) — spelled as `produces:` spells it, plus the proving
    command and output. The driver reads that list: a justified entry passes
-   and is recorded on the attempt as `produces_justified`; an unjustified one,
-   or a blank justification, is refused (#198, #3268, outcome
-   `produces_not_in_diff`). Silence on an
-   unchanged deliverable is not a valid close.
+   and is recorded as `produces_justified`; an unjustified one, or a blank
+   justification, is refused (#198, #3268, outcome `produces_not_in_diff`).
+   Silence on an unchanged deliverable is not valid.
 2. **A plan-level contradiction is `blocked`, not `complete`.** Put the
-   finding in `blocked_reason`; never write it into a gate document and close
+   finding in `blocked_reason`; never bury it in a gate document and close
    `complete`.
 3. **Every `evidence:` cites an executed command** and its observed exit
-   code/output. Reading source, grepping a string, or citing another WU's
-   RESULT is not verification.
-4. **Analysis without edits is not a silent attempt.** Say so and end
-   `blocked` rather than spending the attempt on prose.
-
-The driver's whole cycle — re-verify, commit, advance the dependency frontier,
-dispatch the next unit — runs on this block being an honest claim about what
-happened. State intent. Act. Verify. Report. Every time.
+   code/output. Reading source or citing another WU's RESULT is not
+   verification.
+4. **Analysis without edits is not a silent attempt.** Say so; end `blocked`
+   rather than spend the attempt on prose.
+
+The driver's whole cycle — re-verify, commit, advance the dependency
+frontier, dispatch next — runs on this block being an honest claim. State
+intent. Act. Verify. Report. Every time.
diff --git a/.specfuse/verification.yml.example b/.specfuse/verification.yml.example
index dd0ec10..347e43c 100644
--- a/.specfuse/verification.yml.example
+++ b/.specfuse/verification.yml.example
@@ -136,12 +136,20 @@
 #                               # ignored and the path is judged as an
 #                               # unjustified unchanged deliver
… (diff truncated)

```
