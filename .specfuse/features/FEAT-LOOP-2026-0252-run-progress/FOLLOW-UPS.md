# Follow-ups — FEAT-LOOP-2026-0252

First close of gate 1. One entry is open.

### Definition of done clause 6 (stop reason when the event log changes during `run()`)

**Criterion, verbatim:** "**Stop notification.** Each return from `run()` (and each exception
out of it) sends exactly one notification. Its `stop_reason` is `halted` when this run wrote
a `human_escalation`, else `awaiting_review` when it wrote `gate_reached` and the gate is
`awaiting_review`, else `complete` when `PLAN.md` is `done`, else `error` when `run()`
raised, else `stopped`. The message goes to `notify.post_notification` when a webhook is
configured, and to `escalation.notify_command` when set: run as an argument list
(`shlex.split`, never a shell) with `SPECFUSE_STOP_REASON`, `SPECFUSE_FEATURE`,
`SPECFUSE_WORK_UNIT` and `SPECFUSE_MESSAGE` in its environment and a 30 s timeout. A command
that fails, hangs or does not exist is logged and does not change `run()`'s exit code. With
neither configured, or under `--dry-run`, nothing is sent or run. The `agent-policy.yml`
validator accepts a string `escalation.notify_command` and reports an ERROR for any other
type."

**What fails:** the `stop_reason` rule only. `remember_run` stores the size of
`events.jsonl` before `ensure_feature_branch` can check out the feature branch.
`notify_stop` reads from that offset in the file that is there afterwards. Lines from
earlier runs can then count as this run's, or this run's lines can be skipped. The
`WU` named in the message comes from the same lines.

**Evidence.** Both probes drive `loop.main()` through `_Notified` from
`tests/test_run_progress.py` and wrap `ensure_feature_branch` to rewrite the log as a
checkout would. The checkout is simulated.

- command: `PYTHONPATH=. python3 <scratchpad>/probe_offset.py`
- exit: 0
- output: `control (log unchanged by checkout): rc=0 posts=1 commands=1
  reason=awaiting_review`, then `checkout brings an earlier run's escalation: rc=0 posts=1
  commands=1 reason=halted`
- command: `PYTHONPATH=. python3 <scratchpad>/probe_converse.py`
- exit: 0
- output: `control: rc=1 commands=1 reason=halted unit='FEAT-LOOP-2026-9999/T01'`, then
  `checkout shortens the log: rc=1 commands=1 reason=stopped unit=''`

The scratch scripts do not outlive the session. To rebuild the first one: wrap
`loop.ensure_feature_branch`, call the real function, append one `human_escalation` line to
`<feature>/events.jsonl`, run `_Notified()` and read `SPECFUSE_STOP_REASON`.

**Re-run condition.** A test through `loop.main()`, in which the run starts on a branch
other than the feature branch and the two branches hold different `events.jsonl` files (a
real checkout), passes both ways: (a) an older `human_escalation` only on the feature branch,
and a run that reaches the gate, reports `awaiting_review`; (b) a starting log longer than
the feature branch's, and a run that halts, reports `halted` and names the halted unit. The
existing `TestStopNotification` tests stay green.

**Possible fix, not tried.** Take the offset after the branch has been entered, keeping an
early one for returns that happen before that. Check the `--prepare` and `--prepare-only`
paths, which also switch branches, and the `driver_build_pinned` line written before the
switch.
