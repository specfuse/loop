---
id: FEAT-2026-0020/T12
type: implementation
status: done
attempts: 1
oracle_env: macos_local
planned_cost_usd: 0.50
duration_seconds: 92.465
cost_usd: 0.165233
input_tokens: 7
output_tokens: 1073
completed_out_of_loop: true
completed_note: "Loop dispatch HOLLOW-PASSED the bundle: shipped SECURITY.md only; CODE_OF_CONDUCT.md was never created despite the WU's own file-presence gate (test -s CODE_OF_CONDUCT.md). Completed out-of-loop 2026-06-16: fetched Contributor Covenant 2.1 from the canonical EthicalSource repo (the text trips the model output content-filter, so it was curl'd + processed in shell, never generated inline), set the enforcement contact to GitHub Security Advisories/private channels (no email), prepended the Apache header. Verified: Covenant identity + v2.1 grep pass; no leaks."

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Add SECURITY.md and CODE_OF_CONDUCT.md (two small standard files, bundled)

**Objective.** Create `SECURITY.md` (vulnerability-disclosure channel + supported-versions
note) and `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1, unmodified) at the repo root.

**Context.** Part of FEAT-2026-0020 gate 2. Both are small, standard, single-file OSS
hygiene artifacts; per `/authoring-work-units` §6 sizing they bundle cleanly into one WU.
Correlation ID `FEAT-2026-0020/T12`. SECURITY.md's disclosure channel is an
**operator-decision** flagged in `GATE-02-REVIEW.md` (GitHub Security Advisories vs a
direct email fallback) — the operator confirms the exact channel text at arming; this WU
implements the confirmed choice. CODE_OF_CONDUCT.md is the Contributor Covenant 2.1
verbatim with only the contact placeholder filled.

Binding rules in `.specfuse/rules/` apply. The disclosure-channel value is a cross-surface
contract (`/authoring-work-units` §8) — use the operator-confirmed channel, do not invent.

Red-test exempt: content WU — no behavioral surface introduced.

**Acceptance criteria.**

1. `SECURITY.md` exists at repo root and names a concrete disclosure channel
   (GitHub Security Advisories link and/or a fallback email) — the value confirmed by the
   operator at arming per `GATE-02-REVIEW.md` Open Verifications, not an invented address.
2. `SECURITY.md` states how reporters should expect to be acknowledged and which
   versions/branches are in scope (a one-line supported-versions statement is sufficient
   for a pre-1.0 project).
3. `CODE_OF_CONDUCT.md` exists at repo root and is the **Contributor Covenant 2.1**, text
   unmodified except the enforcement-contact placeholder, which is set to the same channel
   as SECURITY.md (or the operator-confirmed alternative).
4. No private-org names, personal paths, or internal URLs introduced. The disclosure email
   (if used) is a project/maintainer address, not a personal `/Users`-derived identity that
   gate 1 redacted.

**Do not touch.**

- Any file other than `SECURITY.md` and `CODE_OF_CONDUCT.md`.
- Sibling gate-2 WU outputs (README — T01; CONTRIBUTING — T02; `.github/` templates — T04;
  dependabot — T05; leak-scan guard — T06; FLIP-CHECKLIST — T07).
- `LICENSE` (already correct Apache-2.0 per gate 1 T05).
- Generated directories, secrets, `.git/`. The driver owns all git — edit files only.
- See `.specfuse/rules/never-touch.md`.

**Verification.**

- `code` gates per `.specfuse/verification.yml` — pass unchanged on a content-only edit.
- Existence checks: `test -s SECURITY.md && test -s CODE_OF_CONDUCT.md`.
- Covenant identity: `grep -qi "Contributor Covenant" CODE_OF_CONDUCT.md` and
  `grep -qiE "2\.1" CODE_OF_CONDUCT.md`.
- Oracle environment: `macos_local`.

**Escalation triggers.**

1. If the SECURITY.md disclosure channel is NOT yet confirmed by the operator at dispatch
   time (the `GATE-02-REVIEW.md` Open Verification is still unchecked), emit
   `status: blocked` — do not invent a disclosure address. This is a cross-surface contract
   value per `/authoring-work-units` §8.
2. If filling the Covenant contact would require a personal email that gate 1 redacted,
   emit `status: blocked` and request a project-level address from the operator.
