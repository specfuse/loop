---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_run_progress -v -b"
cost_budget_usd: 18.00
broad_run:
  tree: 07bbf72d1e7af3c1a03af605f40e5563dc3a18db:0ec7c6da6e74f0b56753f09657b654a6d289b91b:12064a6191eeb830a9826d911a8543fbaba3da75:21853f95bd08cd0c5cd8f5fe0caad3f248ba8e72:27968248a450a842ccd187b7dce0fb0ded934866:287efde8f90320baffac08f5f3287b9456a65cb9:2e29b2f7e073a0cbe290f01d3b397e1cdd10c81c:3e6b8329522b39869d0b9caf5e22bf61f1a87ec0:42796ea0e0a6c03811b0e4bc9dbd3b5ee62dd2e4:4acc6dfc5e8cece358c167d876515eba4a39a500:6f70c7c8afa618acb6b7b66ad5b035d661250dc6:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:d74b7d113b844e84f0009098f576fd28477f072d:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:f1126d17cf8e5a0a44edefbee7cb726fab9cf3a2:fa2f4f88657587b6e3b560977858810846b1d366
  ran_at: 2026-11-27T03:34:05.038818+00:00
  ok: true
  failing: []
---

# Gate 1 — a running unit's progress is visible, and the operator is notified once when the run stops

## Definition of done

**Stated as an outcome.** In temporary feature folders, with a stubbed agent session and stub
gate commands, driven through `loop.run()`:

1. **Phase events, written as they happen.** Each attempt appends `agent_session_started` and
   `agent_session_finished` to `events.jsonl`, and each verification gate it runs appends
   `gate_started` then `gate_finished` (payload: `attempt`, `gate`, and on `gate_finished` also
   `ok` and `duration_seconds`). All four validate against the packaged
   `driver-event.schema.json`. They are on disk while the attempt runs: the stubbed session
   reads `events.jsonl` and finds its own `agent_session_started`, and a stub gate command finds
   its own `gate_started`.
2. **Status file.** While a unit runs, `<feature>/work/STATUS.json` holds `feature`, `wu_id`,
   `attempt`, `max_attempts`, `phase` (one of `agent`, `gate`, `between`, `stopped`), `gate`
   (the running gate's name, else null), `started_at`, `updated_at`, `elapsed_seconds` and
   `files_touched`. After `run()` returns, `phase` is `stopped` and `stop_reason` is set (see
   clause 6). `git ls-files` never lists the file.
3. **Heartbeat.** With `defaults.heartbeat_seconds: 1`, a stubbed session that runs for 3 s and
   writes one file sees `updated_at` advance at least twice during `phase: agent`, and
   `files_touched` lists that file. After `run()` returns, also when it raises, no heartbeat
   thread is alive. A missing, non-integer or non-positive `heartbeat_seconds` means 30.
4. **Plain driver lines.** The driver prints one line per phase change (session started and
   finished, each gate started and finished with its result and duration). Driver output
   contains no `\r` and no ANSI escape sequence.
5. **Watcher.** `specfuse-loop --watch [--feature F]` reads the status file and prints a line
   naming the unit, attempt, phase, elapsed time and current gate. When stdout is not a
   terminal it prints a line only when one of those changes. It prints `no update for Ns` when
   `updated_at` is older than three heartbeat intervals. It exits 0 once `phase` is `stopped`,
   and exits 1 with a message naming the expected path when no status file exists.
6. **Stop notification.** Each return from `run()` (and each exception out of it) sends exactly
   one notification. Its `stop_reason` is `halted` when this run wrote a `human_escalation`,
   else `awaiting_review` when it wrote `gate_reached` and the gate is `awaiting_review`, else
   `complete` when `PLAN.md` is `done`, else `error` when `run()` raised, else `stopped`. The
   message goes to `notify.post_notification` when a webhook is configured, and to
   `escalation.notify_command` when set: run as an argument list (`shlex.split`, never a shell)
   with `SPECFUSE_STOP_REASON`, `SPECFUSE_FEATURE`, `SPECFUSE_WORK_UNIT` and `SPECFUSE_MESSAGE`
   in its environment and a 30 s timeout. A command that fails, hangs or does not exist is
   logged and does not change `run()`'s exit code. With neither configured, or under
   `--dry-run`, nothing is sent or run. The `agent-policy.yml` validator accepts a string
   `escalation.notify_command` and reports an ERROR for any other type.
7. **Nothing else changes.** `dispatch()` and the `attempt_outcome` payload are unchanged.
   Every existing test passes unchanged, apart from edits forced by the new driver lines being
   picked up by a text-matching assertion; no such edit removes or weakens an assertion, and
   each is named in the close.

The `feature_oracle` proves 1–6. It is red on the current tree; `FEAT-LOOP-2026-0252/T01` is the
walking skeleton that creates `tests/test_run_progress.py` and turns clauses 1, 2 and 4 green,
with the other classes `unittest.skip` naming their owner (T02–T04). A skip surviving to the
close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Live, not after the fact.** "Written as it happens" is asserted by the stub reading the
  file during the attempt, never by comparing timestamps afterwards.
- **Counted, not inferred.** "Exactly one notification" is asserted by a call counter on the
  poster and on a stub command, never by reading logs.
- **Positive controls.** Clause 6 pairs each configured channel with an unconfigured run;
  clause 5 pairs a fresh status file with a stale one.
- **No reading chosen silently.** A unit that finds a clause above ambiguous blocks and names
  the clause; it does not pick an interpretation.
- **Expected self-halt.** `loop.py` and `arm_eval.py` are judge surfaces; acknowledge the stop
  with your own reason and `/unblock-wu`.

## Reflection notes

<Written by the human at review time.>
