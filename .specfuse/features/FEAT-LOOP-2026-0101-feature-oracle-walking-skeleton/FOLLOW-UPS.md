# Follow-ups

Filed by the judge for gate 1. Each entry is the judge's own words.

### Declared-but-unrunnable oracle is a CONFIGURATION ERROR

Definition of done requires a declared `feature_oracle` that is "empty, or a command that cannot be resolved" to be a CONFIGURATION ERROR before any unit dispatches. Code (`loop.py` `verify()`/`read_gate_feature_oracle`) only checks empty/whitespace/non-string — a syntactically present but unresolvable command (nonexistent binary) is dispatched through `_run_gate_set` like any other gate and reported as an ordinary FAIL, not a CONFIGURATION ERROR.

- command: constructed a temp feature with `GATE-01.md` frontmatter `feature_oracle: "totally-nonexistent-command-zzz"`, called `specfuse.loop.loop.verify(wu, feature_dir, cfg, gate_file=gate)` directly (Python one-liner, in-session)
- exit: `verify()` returned `ok=False` with report `### feature_oracle: FAIL ... /bin/sh: totally-nonexistent-command-zzz: command not found` — not the CONFIGURATION ERROR message shape used for the empty-string case
