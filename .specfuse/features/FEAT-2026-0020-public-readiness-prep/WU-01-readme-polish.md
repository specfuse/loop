---
id: FEAT-2026-0020/T10
type: implementation
status: pending
attempts: 0
oracle_env: macos_local
planned_cost_usd: 0.60
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Polish README.md for a public first-read — 60-second pitch + quickstart

**Objective.** Add a tight "what is this / why care" pitch near the top of `README.md`
and a copy-pasteable **Quickstart** section, so a stranger landing on the public repo can
understand the loop and run the bundled example in under a minute.

**Context.** Part of FEAT-2026-0020 gate 2 (public hygiene + flip). The repo flips from
private to public ahead of FEAT-2026-0019's first PyPi tag; `README.md` is the public
front door. It already carries a strong "Why it exists" / "How it works" narrative
(see the file); this WU adds the missing fast-orientation surfaces, not a rewrite. The
correlation ID is `FEAT-2026-0020/T10`. Grounding: existing `README.md`,
`docs/methodology.md`, `scripts/smoke-test.sh`, `.specfuse/scripts/loop.py --dry-run`.

Binding rules in `.specfuse/rules/` (`result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`) apply; PLAN.md "Notes" applies.

Red-test exempt: content/docs WU — no behavioral surface introduced; existence checks
below are the verification.

**Acceptance criteria.**

1. `README.md` contains a one-or-two-sentence **pitch** in the first 15 lines that states
   what the loop is and who it is for, readable without scrolling.
2. `README.md` contains a `## Quickstart` section with a fenced, copy-pasteable command
   block that takes a reader from clone to a successful `loop.py --dry-run` (or the
   bundled-example walk) — every command runnable as written, no placeholder secrets.
3. The Quickstart names the actual entrypoints that exist in the repo
   (`.specfuse/scripts/loop.py`, `scripts/smoke-test.sh`) — verified against the tree,
   not invented.
4. No private-org names, `/Users/<name>/` paths, personal emails, or internal URLs are
   introduced (gate-1 audit classes must stay clean).
5. The three-project suite framing and existing methodology links are preserved (no
   regression of current content).

**Do not touch.**

- Any file other than `README.md`.
- Sibling gate-2 WU outputs: `CONTRIBUTING.md` (T02), `SECURITY.md` / `CODE_OF_CONDUCT.md`
  (T03), `.github/` templates (T04), `dependabot.yml` (T05), the leak-scan guard (T06),
  `FLIP-CHECKLIST.md` (T07).
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- `code` gates per `.specfuse/verification.yml` (tests, lint, security, coverage) — pass
  unchanged on a docs-only edit.
- Existence checks: `grep -q "^## Quickstart" README.md`.
- Scope-clean check (feature footprint only): the quickstart commands resolve to real
  files — `test -f .specfuse/scripts/loop.py && test -f scripts/smoke-test.sh`.
- Oracle environment: `macos_local`.

**Escalation triggers.**

1. If the bundled example or `loop.py --dry-run` does not actually run cleanly from a
   fresh clone, do NOT document a command that fails — emit `status: blocked` naming the
   broken entrypoint (a quickstart that lies is worse than none).
2. If polishing the README surfaces a residual gate-1 leak (private-org name, personal
   path) already in the file, do NOT silently fix it here — emit `status: blocked` and
   flag for a hygiene WU, per `RETROSPECTIVE.md` open-action discipline.
