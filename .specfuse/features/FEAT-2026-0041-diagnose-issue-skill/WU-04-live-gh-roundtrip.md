---
id: FEAT-2026-0041/T04
type: implementation
status: done
attempts: 1
planned_cost_usd: 3.00
unsandboxed: true
unsandboxed_rationale: "gh fails inside the command sandbox (invalid-token error plus a TLS certificate failure, both reproduced 2026-08-03). This unit verifies the diagnosis comment's real GitHub round-trip, which FEAT-2026-0040 could only stub — its D-9/D-10/D-11 were deferred to an operator journal never written, leaving its close hedged. The escape is confined to this single work unit; every other unit in the gate is stub-verified and forbidden from calling gh."
produces:
  - tests/test_diagnosis_roundtrip_live.py
oracle_env: macos_local
model: sonnet
effort: medium
gate_set: code
driver_version: 0.8.0
started_at: 2026-08-03T20:26:45.484881+00:00
duration_seconds: 728.332
cost_usd: 1.382084
input_tokens: 1746
output_tokens: 13476
---

# The live round-trip: read a real issue, post to a disposable one

**Objective.** Prove the diagnosis comment survives a real GitHub round-trip — rendered
by T01, posted via `gh`, read back, and parsed to an equal `Diagnosis` — using a live
read against an existing issue and a live write against a scratch issue this work unit
creates and closes itself.

**Context.** Correlation ID `FEAT-2026-0041/T04`. Read `PLAN.md` first, especially the
section on why the `gh` constraint no longer holds. This work unit is the one carrying
`unsandboxed: true`; the rationale is in its frontmatter and the driver refuses the
flag without one.

**Why this work unit exists.** FEAT-2026-0040 stubbed every `gh` write path because
`LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken]` ruled that no acceptance criterion
may invoke `gh` from a dispatched agent. That entry attributes the failure to the wrong
layer — the cause is the command **sandbox**, not a `gh`/subprocess interaction, and
`--dangerously-skip-permissions` never helped because it governs permission prompts
rather than the sandbox. Run unsandboxed, `gh auth status` and `gh issue view` both
exit 0 against the real API. This unit converts 0040's entire deferred category into
in-loop evidence.

**Run the `gh` commands unsandboxed.** If a `gh` call returns
`The token in GH_TOKEN is invalid` or `tls: failed to verify certificate`, you are
sandboxed — that is the artifact described above, **not** a broken feature and not a
reason to weaken an acceptance criterion. Re-run the command unsandboxed.

**Do not trust your own summary of a command's result.** Per
`LEARNINGS [FEAT-2026-0014/T01/preflight-must-dump-raw]`, dump raw stdout and stderr
between unforgeable markers and quote them in the result. A classification of an
external tool's behaviour is not evidence when the raw output exists.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`, `operator-escalation.md`.

## Blast radius, deliberately bounded

The **read** half touches an existing issue read-only. The **write** half touches only
a scratch issue this unit creates, comments on, verifies, and closes. Nothing is
written to any issue a human is using.

The scratch issue's title and body must carry an identifying marker naming this
correlation ID, so a stray one left by a killed attempt is unambiguously identifiable
as test residue rather than a real finding. Close it in the same run that creates it.

**Acceptance criteria.**

1. `tests/test_diagnosis_roundtrip_live.py` exists and carries the live round-trip as a
   test that **skips explicitly** when `gh` is unavailable or unauthenticated — named
   skip, not silent pass. A test that vacuously passes without reaching GitHub is the
   failure mode this WU exists to remove.
2. **Live read, raw evidence.** Run `gh auth status` and a `gh issue view` against an
   existing issue in this repository. Dump raw stdout+stderr between `PROBE_BEGIN` /
   `PROBE_END` markers and quote both in the result, with exit codes. `gh auth status`
   must show `Logged in to github.com`; the view must return real issue JSON.
3. **Live write round-trip.** Create a scratch issue whose title and body name
   `FEAT-2026-0041/T04`; render a `Diagnosis` through T01; post it as a comment via
   `gh issue comment`; read the comment back via `gh`; parse it with T01's parser; and
   assert the parsed `Diagnosis` equals the one rendered. Quote the raw output of each
   `gh` call.
4. **Cleanup.** Close the scratch issue in the same run and quote the raw output of the
   close. Report its issue number in the result whether or not the close succeeded, so
   a human can find it.
5. A test asserts the marker survives GitHub's own body handling — the comment read
   back through `gh` still parses, so no round-trip through the API mangles the
   embedded marker. This is the specific risk a stub cannot cover.
6. **Report the residue honestly.** If any scratch issue from a prior attempt of this
   WU is still open, name it in the result rather than silently closing it — a killed
   attempt leaving residue is information about attempt behaviour, not litter to hide.
7. The `code` gate set passes: `tests`, `lint`, `security`, `coverage` (≥90%),
   `leak-scan`.

**Do not touch.** `specfuse/monitor/diagnosis.py` — T01 owns it; this unit is a
consumer proving the contract holds live, not a place to fix it. Any issue in this
repository other than the scratch issue this unit creates — no comments, no edits, no
closes on real work. `plugins/specfuse/skills/` and the headless entry point.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`, `lint`,
`security`, `coverage` (≥90%), `leak-scan`. Beyond the gates, criteria 2–4 are the
oracle: raw `gh` output quoted in the result, with exit codes. A green test suite with
a skipped live test is **not** this WU passing — criterion 1's skip exists for other
environments, and this run must actually reach GitHub.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if: `gh`
fails unsandboxed with a real authentication or permission error (as opposed to the
sandbox artifact, which you must retry unsandboxed before concluding anything); the
account lacks permission to create or close an issue in this repository; the marker
does not survive the API round-trip, which is a genuine T01 contract defect and must be
reported rather than worked around by loosening the parser; or a prior attempt's
scratch issue cannot be closed. Do **not** weaken any acceptance criterion to make this
unit green — its entire value is being the one place the `gh` surface is not a stub,
and a stubbed T04 is worth less than no T04, because it would read as live evidence.
