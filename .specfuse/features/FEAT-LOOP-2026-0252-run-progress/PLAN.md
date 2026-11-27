---
feature_id: FEAT-LOOP-2026-0252
title: Show a running unit's progress, and notify when the driver stops
slug: run-progress
branch: feat/FEAT-LOOP-2026-0252-run-progress
roadmap_goal: While `specfuse-loop` runs, an operator can see which unit, attempt, phase and verification gate is running and for how long, from the driver's terminal or a second one, and is notified once when the run stops.
autonomy_default: auto
status: done
planned_cost_usd: 14.50
---

# Plan: Show a running unit's progress, and notify when the driver stops

Between an attempt's start line and its outcome the driver prints nothing, and `events.jsonl`
gets `task_started` and then nothing until `attempt_outcome`: the agent session is one
blocking `claude -p --output-format json` call, a unit's events are buffered (`wu_events`,
`flush_events`) and `gate_result` events are written after the whole gate set. An operator
report measured a median attempt of 237 s and a maximum of 2265 s over 184 attempts, and 26
runs that ended in `human_escalation` with nothing telling the operator.

This feature writes phase events as they happen, keeps a live status file with a heartbeat,
adds a `--watch` reader, and sends one notification when the run stops.

## Decisions (2026-11-26)

The operator chose each of 1–6 from presented options and said "take your recommendations
for the rest" for 7 and 8.

1. **All three asks in one feature:** phase events, a live view, a stop notification. They
   share the same driver call sites, and the notification reuses `notify.py`.
2. **Phase changes in `events.jsonl`; heartbeats in a status file.** `agent_session_started`,
   `agent_session_finished`, `gate_started` and `gate_finished` are appended to `events.jsonl`
   when they happen (about 2 + 2×gates lines per attempt; `reset_preserving_events` already
   keeps lines written mid-attempt). The heartbeat overwrites
   `<feature>/work/STATUS.json`, which is under the gitignored `work/` and never committed.
3. **The agent session is not changed.** The heartbeat comes from a driver thread (elapsed
   time, files touched via `_paths_differing_from`). `dispatch()`, its `--output-format json`
   parse and the cost fields three guards depend on stay as they are.
4. **Both a plain driver line per phase change and a `--watch` reader.** The driver prints one
   plain line per phase change (no `\r`, no ANSI); `specfuse-loop --watch` keeps a status line
   current from another terminal.
5. **Stop notification through both channels.** Once per stop, when `run()` returns: the
   existing webhook (`agent-policy.yml` `escalation.webhook_env` / `provider`) when configured,
   and a new `escalation.notify_command` run as an argument list when configured.
6. **Autonomy `auto`.** A fresh judge writes the terminal verdict from evidence only.
   `loop.py` and `arm_eval.py` are judge surfaces, so the terminal judge-editing stop fires
   before the close: acknowledge it with your own reason and `/unblock-wu`.
7. **Heartbeat interval** *(recommendation applied):* 30 s, from `defaults.heartbeat_seconds`
   in `verification.yml`, read the way `fail_fast_deliverables` is.
8. **One gate** *(recommendation applied):* four substantive units and a terminal `close`
   (`docs/methodology.md` §6).

**Out of scope:** streaming the agent session's output (`stream-json`, tool-call counts); a
`specfuse watch` alias in the umbrella CLI (another repository); a notification per event;
re-pinging; any change to `dispatch()` or to the `attempt_outcome` payload.

## Existing-mechanism search (mandatory — see `.specfuse/rules/planning-discipline.md` §1)

- **Grep command run:** `grep -n "notify\|post_notification\|heartbeat\|gate_result\|flush_events\|output-format" specfuse/loop/loop.py`;
  `ls specfuse/loop/` (found `heartbeat.py`, `notify.py`, `notify_escalation.py`,
  `notify_sla.py`); `grep -n "^escalation:" -A8 .specfuse/agent-policy.yml.example`.
- **Verdict:** reuse and extend. `notify.post_notification` (webhook, redaction, quiet hours)
  is reused for the stop notification; `escalation` in `agent-policy.yml` gains one key.
  `heartbeat.py` measures run-level silence from `events.jsonl` and is unrelated to a
  heartbeat inside an attempt; it is not changed. `gate_result` (FEAT-LOOP-2026-0250) is
  written after the gate set and stays; `gate_started` / `gate_finished` are the live
  counterpart. No live progress surface or watch command exists.
- **If reusing:** the stop reason is derived from the events this run wrote, not from state
  held in the process (LEARNINGS `[FEAT-LOOP-2026-0075/G2-CLOSE/...]`: rehydrate from the
  durable log).

## Escalation-predicate satisfiability (mandatory for any severity flip — §2)

n/a — no check changes severity.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-LOOP-2026-0252/T01
        file: WU-01-phase-events-and-status.md
        depends_on: []
      - id: FEAT-LOOP-2026-0252/T02
        file: WU-02-heartbeat.md
        depends_on: [FEAT-LOOP-2026-0252/T01]
      - id: FEAT-LOOP-2026-0252/T03
        file: WU-03-watch.md
        depends_on: [FEAT-LOOP-2026-0252/T01]
      - id: FEAT-LOOP-2026-0252/T04
        file: WU-04-stop-notification-and-docs.md
        depends_on: [FEAT-LOOP-2026-0252/T02, FEAT-LOOP-2026-0252/T03]
      # --- closing sequence: single terminal close (single-gate feature) ---
      - id: FEAT-LOOP-2026-0252/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on: [FEAT-LOOP-2026-0252/T01, FEAT-LOOP-2026-0252/T02, FEAT-LOOP-2026-0252/T03, FEAT-LOOP-2026-0252/T04]
```

## Post-merge checklist

- Run a real feature whose units take several minutes; confirm `specfuse-loop --watch` in a
  second terminal shows the phase and gate changing and `files_touched` growing.
- Configure `escalation.notify_command` with a desktop notifier (for example
  `terminal-notifier -message`) and confirm exactly one notification arrives when the run halts
  and when it completes.
- With a chat webhook configured, confirm the stop message arrives once.

## Notes

- LEARNINGS `[FEAT-LOOP-2026-0251/T04]`: a unit that adds driver output runs every test module
  that matches driver output text, not only its own.
- LEARNINGS `[FEAT-LOOP-2026-0250/T04]`: a unit that edits `docs/*.md` refreshes its packaged
  copy under `specfuse/loop/data/docs/` in the same unit (`scripts/sync-scaffold.sh`).
- LEARNINGS `[FEAT-LOOP-2026-0250/T01]`: a test that validates events through `validate_event`
  pins the packaged schemas and clears the validator caches.
- `produces:` lists only `.py` files under `tests/` (#3539).
- FEAT-LOOP-2026-0251 took seven closes because the definition of done left room for
  interpretation. `GATE-01.md` states each clause as a checkable fact; a unit that finds a
  clause ambiguous blocks and names it rather than choosing a reading.
- **First-close follow-up (2026-11-26, #3626).** The stop reason was taken from the bytes of
  `events.jsonl` past an offset recorded when `run()` started, before the run checks out the
  feature branch. A checkout to a branch with a different log made an older run's escalation
  count as this run's, or skipped this run's own lines. `notify_stop` now reads the events
  stamped at or after the run's start time, so the branch the log came from no longer matters.
  Tested in `TestStopNotification` with a real checkout both ways (an older escalation only on
  the feature branch; a starting log longer than the feature branch's).
