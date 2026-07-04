---
feature_id: FEAT-2026-0030
title: Driver-side sanitization of agent-authored text before events.jsonl staging
slug: events-jsonl-sanitize
branch: feat/FEAT-2026-0030-events-jsonl-sanitize
roadmap_goal: A single driver-side sanitization pass over agent-authored strings before they are written to events.jsonl — redact absolute home-directory paths (macOS /Users/<x>/ and Linux /home/<x>/) so a benign path quoted into a blocked reason no longer trips the pre-commit leak-scan and halts the gate, while preserving the audit signal.
autonomy_default: auto
status: active
planned_cost_usd: 2.50
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Driver-side sanitization of agent-authored text before events.jsonl staging

The loop driver writes agent-authored free-text (blocked reasons, failure notes)
into `events.jsonl`, then stages and commits that audit trail. When the text
contains an absolute home-directory path the agent mentioned while explaining where
it searched, the repo's structural pre-commit leak-scan flags it (`user-path`) and
rejects the bookkeeping commit — halting the gate mid-run and forcing a manual
redact-and-commit recovery. This bit the FEAT-2026-0029 run repeatedly (driver
0.3.6): the agent's `agent_blocked_reason` quoted a local checkout path.

This is the same self-poison family as the closed #76 (which redacted the leak
hook's **own FINDINGS text** via `redact_leak_findings`, loop.py:1281) and #73 (the
general form). But the fix for #76 only covers text shaped like a leak-scan FINDINGS
label; a **raw home path inside an ordinary note field** never routes through it.
This feature closes that gap with one general chokepoint.

**Decisions (set at draft time):**
- **Chokepoint = `flush_events` (loop.py:473).** Every events.jsonl write passes
  through it; sanitizing there covers all sources (blocked reasons, failure
  excerpts, notes, captured FINDINGS) in one place.
- **Redact home paths only** — `/Users/<x>/…` (macOS) and `/home/<x>/…` (Linux),
  the class that actually halted us. Matches `leak_scan.py`'s `user-path` rule, so
  this repo's staged events.jsonl passes `--staged`. Emails / private-hosts are OUT.
- **Self-contained — no import of `.specfuse/scripts/leak_scan.py`.** The driver
  (`loop.py`) ships in the pip package; `leak_scan.py` is repo-internal and is NOT
  copied into target projects (issue #55, LEARNINGS `leak_guard_specfuse_internal`).
  The redaction regex lives in the driver.
- **Out of scope:** retiring `leak_scan.py`'s per-token allowlist band-aids (a
  separate, riskier change touching every commit's scan — follow-up); unifying with
  the existing `redact_leak_findings` #76 helper (the two stay complementary — the
  new pass handles raw home paths, the #76 helper handles FINDINGS-label text);
  emails / private-hosts.

This file owns the **shape**. Single gate → single terminal `close` (≤ 4 substantive
WUs, per `docs/methodology.md` §6 ceremony proportionality). Autonomy `auto`: the
gate auto-closes if it stays on-plan, else the `gate_eval` predicate disables
auto-close and dispatches the close as a reflective session.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0030/T01
        file: WU-01-redact-home-paths.md
        depends_on: []
      - id: FEAT-2026-0030/G1-CLOSE
        file: WU-90-gate-1-close.md
        depends_on:
          - FEAT-2026-0030/T01
```

## Notes

- Dependencies live here, not in WU frontmatter — scheduling is the driver's job.
- The fix is driver-local and fully in-loop-verifiable (unlike FEAT-2026-0029's
  cross-repo git choreography): the redaction, its unit tests, and the
  `leak_scan --staged` dogfood proof all run inside the loop sandbox.
