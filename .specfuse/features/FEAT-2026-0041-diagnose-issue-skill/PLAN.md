---
feature_id: FEAT-2026-0041
title: diagnose-issue skill — root-cause diagnosis of harvester findings
slug: diagnose-issue-skill
branch: feat/FEAT-2026-0041-diagnose-issue-skill
roadmap_goal: A /diagnose-issue NN skill that reads a harvester finding, reads the component source, and posts a structured diagnosis comment — root cause, evidence trail, candidate fix, plus machine-readable confidence and fix_scope fields — in an identical format from both the interactive and headless entry points.
autonomy_default: review
status: active
planned_cost_usd: 18.50
---

# Plan: `diagnose-issue` skill — root-cause diagnosis of harvester findings

FEAT-2026-0040 shipped a harvester that files findings. Nothing root-causes them.
The unique value of a repo-resident agent is joining a failure artifact with the
source code that produced it — naming *why* a dead-lettered message failed, not
merely that it did. That is the thing external monitoring cannot do, and it is the
next rung of the autonomy ladder: findings arrive pre-diagnosed.

## Scope: diagnosis and both entry points; not the auto-trigger

The roadmap row bundles three things — diagnosis works, diagnosis runs headless, and
diagnosis runs *automatically* (harvester auto-trigger on new fingerprints, a
per-component `diagnose: auto` dial, one diagnosis per fingerprint rather than per
occurrence). **The third is out of this feature**, by an operator decision recorded at
draft time.

The seam is natural: the dial is a *scheduling* concern, not a *diagnosis* concern.
[FEAT-2026-0042](../../roadmap.md#feat-2026-0042), the autofix consumer, needs only
the **output contract** — the `confidence` and `fix_scope` fields — and does not care
how the diagnosis came to be written. Building the auto-trigger first would automate
a diagnosis quality nobody has read yet. A follow-on roadmap row is filed at close.

## The `gh` constraint, and why it no longer holds

`LEARNINGS [FEAT-2026-0014/T01/gh-claudeP-broken]` records that `gh` fails inside a
dispatched `claude -p` session even with `--dangerously-skip-permissions`, and rules
that **no acceptance criterion may invoke `gh` from a dispatched agent**. On that
basis FEAT-2026-0040 stubbed every `gh` write path and deferred D-9, D-10 and D-11 to
operator runs recorded in an `OPERATOR-JOURNAL.md` that was never written — which is
why its close is hedged to this day.

**That entry attributes the failure to the wrong layer.** Probed 2026-08-03 with the
raw-output discipline `[FEAT-2026-0014/T01/preflight-must-dump-raw]` requires:

```
sandboxed:    gh auth status  -> "The token in GH_TOKEN is invalid."          (the 0014 symptom)
              gh issue view   -> tls: failed to verify certificate x509 -26276 (the 0040 symptom)
unsandboxed:  both exit 0, real issue JSON returned
```

The cause is the **command sandbox**, not a `gh`-binary/subprocess interaction.
`--dangerously-skip-permissions` governs permission prompts, not the sandbox, which is
why the flag never helped and why the original diagnosis looked confirmed. A dispatched
work unit *can* exercise `gh` — it must run those commands unsandboxed.

T04 uses this. It is the difference between shipping this feature with its integration
surface verified and repeating 0040's deferred list. The LEARNINGS entry is wrong and
should be corrected; that is a separate act from this feature and is named in the
close's follow-ups rather than done silently here.

## Existing-mechanism search (`.specfuse/rules/planning-discipline.md` §1)

```
Command: grep -rlnE "def render_|def parse_|diagnosis|Diagnosis" specfuse/monitor/
         grep -nE "_MARKER_TEMPLATE|_parse_meta|def _marker" specfuse/monitor/issues.py
         grep -nE "issue comment|def comment|add_comment" specfuse/monitor/issues.py

Verdict: NO diagnosis model, renderer, or parser exists. The only `diagnosis`-adjacent
         hit is an unrelated identifier in providers/azure_service_bus.py.

Reuse:   issues.py already owns the embedded-marker pattern this feature copies —
         `_MARKER_TEMPLATE = "<!-- specfuse:finding fingerprint={fingerprint} -->"`,
         `_marker()`, `_parse_meta()`, with the documented rule that "the marker in
         the body, re-checked client-side, is the sole authority." T01 follows that
         shape rather than inventing a second convention, so FEAT-2026-0042 inherits
         a parser instead of a habit.

         redaction.py owns `_redact_text(text)` and `_SECRET_PATTERNS` (connection
         strings, AWS key IDs, bearer tokens, credential-shaped assignments), with
         digest-keyed replacement so repeats of one secret redact identically. This
         feature must route diagnosis prose through it rather than re-implement it.

Gap:     there is no comment-posting helper — `gh issue comment` is called inline at
         issues.py:273 for the quiet-annotation path only. T01 does not add one; the
         skill posts. See the boundary note below.
```

## Escalation-predicate satisfiability (`.specfuse/rules/planning-discipline.md` §2)

Two criteria classes on this feature could be authored unsatisfiably.

**Diagnosis correctness.** No test can assert that a root cause is *right*. Every
acceptance criterion here is about **format, contract, and round-trip fidelity**; not
one claims the diagnosis is correct. A criterion of the form "the diagnosis names the
true root cause" would be unsatisfiable in-loop and must not be written. This is stated
so the gap is deliberate rather than discovered, and `GATE-01.md` records that passing
format tests must not be read as verified diagnosis quality.

**The live `gh` round-trip.** Satisfiable, but only unsandboxed and only in T04, which
carries `unsandboxed: true` with its rationale. Every other work unit is stub-verified
and must not reach for `gh` — a WU without the flag that writes a `gh` acceptance
criterion produces exactly the sandboxed failure above and will read as a broken
feature rather than a sandbox artifact.

## Runtime probe for a default/severity flip (§4)

Not applicable. No default value, threshold, or severity is flipped. This feature adds
a module, a skill, and a headless entry point; it changes no existing behaviour.

## Flag-scope table (§3)

Not applicable. No behaviour flag is introduced. `unsandboxed: true` on T04 is an
existing driver frontmatter field, not a new flag.

## Scope boundary — explicitly OUT

- **Auto-trigger, the `diagnose: auto` dial, harvester wiring, per-fingerprint dedupe.**
  Operator decision at draft time; a follow-on roadmap row is filed at close.
- **FEAT-2026-0042's gate consumption.** This feature ships the contract; 0042 consumes
  it. No `confidence` threshold or `fix_scope` routing logic is written here.
- **Diagnosis correctness.** Inherent, per §2 above.
- **A general comment-posting helper in `issues.py`.** The skill posts; adding a helper
  whose only consumer is a skill repeats the `[FEAT-2026-0029/G1-CLOSE]` failure of
  shipping a surface with no live caller.

## Two traps that will otherwise be rediscovered mid-attempt

**Skills have three surfaces.** The canonical source is
`plugins/specfuse/skills/<name>/SKILL.md`; it is synced into `.specfuse/skills/<name>/`;
and `.claude/skills/<name>` is a discovery symlink. Writing only one leaves the skill
invisible to Claude Code — the exact failure FEAT-2026-0072 fixed after four skills sat
undiscoverable for seven weeks. T02 writes all three and asserts all three.

**`_redact_text` is module-private.** T01 needs it for diagnosis prose. Promoting it to
a public name is a deliberate API widening; duplicating the patterns is how two
redaction routines drift and one stops catching a secret shape. T01 promotes rather
than copies, and the rename is a consumer-visible contract change the close enumerates.

## Gates

```yaml
# Single terminal gate: 4 substantive WUs, at the ceremony proportionality
# threshold of 4 (docs/methodology.md §6), so one gate with a single terminal close.
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0041/T01
        file: WU-01-diagnosis-contract.md
        depends_on: []
      - id: FEAT-2026-0041/T02
        file: WU-02-diagnose-issue-skill.md
        depends_on: [FEAT-2026-0041/T01]
      - id: FEAT-2026-0041/T03
        file: WU-03-headless-entry-point.md
        depends_on: [FEAT-2026-0041/T01, FEAT-2026-0041/T02]
      - id: FEAT-2026-0041/T04
        file: WU-04-live-gh-roundtrip.md
        depends_on: [FEAT-2026-0041/T01]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0041/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0041/T01
          - FEAT-2026-0041/T02
          - FEAT-2026-0041/T03
          - FEAT-2026-0041/T04
```
