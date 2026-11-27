---
class: added
trace: FEAT-LOOP-2026-0252
---
The driver prints one plain line per phase change (agent session started and finished, each gate started and finished with result and duration) and appends `agent_session_started`, `agent_session_finished`, `gate_started` and `gate_finished` to `events.jsonl` as they happen. `events.jsonl` line order is no longer guaranteed to be timestamp order, because a unit's buffered events are still written later
