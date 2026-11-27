---
class: added
trace: FEAT-LOOP-2026-0252
---
While a feature runs, the driver keeps `<feature>/work/STATUS.json` (never committed) with the unit, attempt, phase, gate, elapsed time and files touched, refreshed during an attempt every `defaults.heartbeat_seconds` in `verification.yml` (default 30)
