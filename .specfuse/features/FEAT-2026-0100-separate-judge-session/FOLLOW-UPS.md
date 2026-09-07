# Follow-ups

Filed by the judge for gate 1. Each entry is the judge's own words.

### Behaviour 1 (judge prompt contains the gate's diff)

The diff fed to the judge is anchored to `GATE-01.md baseline.entry_sha = 7e0252555d94c4ddcc9e701082d4f8375b64cba5`, a commit stamped when T02H shipped hygiene mid-gate — not the gate's actual start. The real gate range is `git merge-base main HEAD` (`b8a02057`) to `HEAD`.

- command: `git diff b8a020575a66b1e2f0d6aa6299ccfa6195aa1c3c..HEAD --stat` → 43 files changed, 4674 insertions(+), 20 deletions(-)
- command: `git diff 7e0252555d94c4ddcc9e701082d4f8375b64cba5..HEAD --stat` (what `resolve_gate_start_sha` actually returns, and what the judge prompt for this close carries) → 13 files changed, 660 insertions(+), 347 deletions(-)
- exit: 0 (both)

The diff a judge sees omits the entire T01–T05 implementation of the separate-judge-session feature — the substance of the gate — and shows only hygiene/close commits. The close's own measurements section names this exact defect and ships it unfixed by design (`entry_sha` present → carried forward, never recomputed). A judge cannot verify "the gate's diff" per the definition of done when the diff it's handed is 14% of the real one.
