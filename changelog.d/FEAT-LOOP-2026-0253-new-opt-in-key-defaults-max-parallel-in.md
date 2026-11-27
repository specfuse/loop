---
class: added
trace: FEAT-LOOP-2026-0253
---
New opt-in key `defaults.max_parallel` in verification.yml (integer >= 1, default 1): above 1, gates of one set whose `needs:` are met run concurrently and results keep the order of the set; any other value is a CONFIGURATION ERROR.
