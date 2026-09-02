# Project notes — specfuse/loop

This is the source repo for the Specfuse Loop scaffold. Skills under
`.claude/skills/` are symlinks into `.specfuse/skills/` so Claude Code's
discovery picks them up.

## Specfuse binding rules (read before any work-unit dispatch)
@.specfuse/rules/result-contract.md
@.specfuse/rules/never-touch.md
@.specfuse/rules/security-boundaries.md
<!-- What a dispatched session is held to, and nothing else: at most 2,500 words
     of binding rules per dispatch (FEAT-2026-0084/T01). Every other rule still
     ships in .specfuse/rules/ and is linked from the three above — the
     ID-minting and gate-planning references belong to the sessions that do that
     work, and the two human-facing rules govern what a skill says to a person,
     which is not what an implementing session does. Project-authored rules live
     in .specfuse/rules-local/ (never touched by `specfuse upgrade`); add one
     @.specfuse/rules-local/<rule>.md line per rule below. -->
