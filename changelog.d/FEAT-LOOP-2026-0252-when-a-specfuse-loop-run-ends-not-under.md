---
class: added
trace: FEAT-LOOP-2026-0252
---
When a `specfuse-loop` run ends (not under `--dry-run`), it sends one notification to the configured escalation webhook and to the new `escalation.notify_command` in `agent-policy.yml`, with the stop reason in the message and in `SPECFUSE_STOP_REASON`. The command runs without a shell, with a 30 s timeout, and its failure does not change the exit code
