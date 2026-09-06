# Follow-ups

Filed by the judge for gate 1. Each entry is the judge's own words.

### Definition of done — bullet 1, "the gate's diff"

`resolve_gate_start_sha` returns `GATE-01.md`'s `baseline.entry_sha`, which resolves to commit `7e02525` (T02H). `git log --oneline` on this feature shows all five substantive units (T01–T05: commits `21bda9b`, `4d02a37`, `b6f586d`, `303f1d7`, `1dfd1ba`) landed *before* that commit. A real judge dispatch for this close therefore receives a diff spanning only 2 commits, not the gate's actual work.

- command: `git log --oneline 7e0252555d94c4ddcc9e701082d4f8375b64cba5..HEAD -- .specfuse/features/FEAT-2026-0100-separate-judge-session/` (2 commits, vs. 15+ for the whole gate)
- exit: 0 (informational — the count itself is the finding)

### Definition of done — bullet 1, "the close's `## Measurements` section"

Ran the real slicer against the actual current `RETROSPECTIVE.md`. The `## Measurements` section (lines 34–137, 87 non-blank lines) contains a stray `### Failure-class breakdown` heading at line 109. `slice_wu_section` terminates there, forwarding only 62 of 87 non-blank lines to the judge — the failure-class table and the driver-restart paragraph never reach it. The close's own text claims this file's Measurements section "reaches the bundle whole" and lists "all 62 non-blank lines" as if that were the total; it is not — it is the truncated remainder.

- command: `python3 -c "from specfuse.loop._wu_sections import slice_wu_section; ..."` against `.specfuse/features/FEAT-2026-0100-separate-judge-session/RETROSPECTIVE.md`
- exit: 0 (62 non-blank lines captured vs. 87 actually present in the section)
