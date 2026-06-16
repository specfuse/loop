---
feature_id: FEAT-2026-0024
title: Hashed denylist + issue/PR-body leak guard
slug: hashed-denylist-leak-guard
branch: feat/FEAT-2026-0024-hashed-denylist-leak-guard
roadmap_goal: CI catches re-introduction of private org-names (not just gitleaks secrets) in both tracked files and GitHub issue/PR bodies, without committing the literal private strings to the public repo.
autonomy_default: review
status: done
planned_cost_usd: 16.00
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->


# Plan: Hashed denylist + issue/PR-body leak guard

Closes the two leak-guard surface gaps surfaced by FEAT-2026-0020's review
(GitHub issues #45 and #46), both rooted in LEARNINGS
`[FEAT-2026-0020/G2/leak-guard-surface-asymmetry]`:

- **#45 — CI has no org-name coverage.** `leak_scan.py`'s denylist
  (`leak_denylist.txt`) is **gitignored** — committing the literal private
  strings to a public repo would re-leak them. So in CI the denylist is absent
  and `leak-scan --all` enforces **gitleaks secrets only**; org-name
  re-introduction is not caught. A `acme-widget-iac` reference reached a PR
  body during FEAT-2026-0020 (caught manually, not by CI).
- **#46 — issue/PR bodies are an unscanned public surface.** The pre-commit
  hook scans git commits only. GitHub issue/PR titles, bodies, and comments are
  a separate public surface the hook cannot see — and is exactly where the
  FEAT-2026-0020 leaks landed (12 issue/PR bodies redacted; a leak reached PR
  #43's body, caught only by a manual pre-flip sweep).

#46 builds on #45: the Action that scans issue/PR bodies runs the same scanner
and the same committed hashed denylist that gate 1 produces. So the two issues
ship as one coupled feature, gate 1 → gate 2.

This file owns the **shape** of the feature: the gate order, which work units
belong to each gate, and the dependency edges between them. It does **not** own
status — each WU file owns its own status, and each GATE file owns its gate's
status. Detail only as far as gate 1; `plan-next` drafts gate 2 from the
retrospective + lessons.

## The hashing design (gate 1 crux)

The plaintext denylist matches by **substring** (`entry.lower() in
line.lower()`), so `acme-widget-iac` matches when embedded in any longer
string. Hashing cannot substring-match a hash, so the scanner must extract
candidate substrings, hash each, and compare to a committed hash set. Three
options were weighed (architect-hat call, operator-confirmed):

- **Rejected — single-token / atom n-grams.** Splitting lines into
  `[a-z0-9]+` atoms and hashing atom n-grams misses **mid-atom substrings**:
  the denylist entry `acmewidget` would not match inside the atom
  `acmewidgetapp`. A leak guard that silently false-negatives is the worst
  failure mode.
- **Chosen — char-sliding-window at a committed length-set.** The generator
  normalizes each literal (lowercase, strip all non-`[a-z0-9]`), records the
  **set of distinct normalized lengths** and a committed salt in the
  `.hashes` file header, and writes one salted SHA-256 per normalized literal.
  At scan time the scanner normalizes each line the same way and, for each
  committed length L, slides an L-char window, hashing each window and
  comparing to the set. This preserves full substring fidelity (a 10-char
  window over `acmewidgetapp` yields `acmewidget`) and leaks only a handful
  of small integers (the distinct lengths), never content.
- **Honesty caveat (documented, not a defect).** Low-entropy org names + a
  committed public salt = **obfuscation, not secrecy**. The salt stops trivial
  rainbow-table lookup; it does not hide the names from an attacker who already
  has the repo. The guard's purpose is to catch **accidental re-introduction**,
  not to withstand a targeted brute force. This is stated in the generated
  `.hashes` header and the close-WU docs.

## Scope OUT

- **Expunging GitHub edit history.** GitHub retains body edit history; the
  gate-2 Action stops *new* leaks on open/edit but cannot remove
  already-published revisions — that stays a delete+recreate / GitHub-Support
  operation. Documented as a limitation, not built.
- **Replacing the plaintext denylist.** The gitignored `leak_denylist.txt`
  stays as the local-convenience source of truth; the hashed file is generated
  from it and is the CI/Action source of truth. No removal of the plaintext
  path.
- **Hashing the pre-commit (`--staged`) surface.** Pre-commit runs locally
  where the plaintext denylist is present, so `scan_text`/`scan_staged` keep
  using it. The hashed denylist is wired into the CI surface (`scan_repo` /
  `--all`) and the gate-2 Action — the surfaces where the plaintext file is
  absent. (T02 MAY also load the hashed file as a supplement in `scan_text`,
  but that is not required.)
- **Local Action emulation (`act`/Docker).** Gate 2's live trigger is
  operator-verified post-merge (see gate-2 oracle below); in-loop coverage is
  unit tests over the scan-runner against fixture issue/PR JSON.
- **Cost levers / broadening the verification contract.** This is leak-guard
  surface coverage, not cost control or a `verification.yml` redesign.

## Gate-2 oracle (operator-confirmed)

#46's headline acceptance — "the Action flags a planted string in an issue/PR
body on open/edit" — can only run in a real GitHub Actions environment. In-loop
coverage is unit tests over the scan-runner script fed fixture issue/PR JSON
(planted hit + clean). The live `issues` + `pull_request`-triggered run is
operator-verified post-merge and recorded in the close WU's `## What the loop
did NOT verify`. This is the FEAT-2026-0020
`[FEAT-2026-0020/G2/out-of-loop-completion]` precedent.

## Task graph

```yaml
gates:
  - gate: 1
    file: GATE-01.md
    work_units:
      - id: FEAT-2026-0024/T01
        file: WU-01-hashed-denylist-core.md
        depends_on: []
      - id: FEAT-2026-0024/T02
        file: WU-02-ci-wiring-and-generator.md
        depends_on: [FEAT-2026-0024/T01]
      # --- closing sequence: 2-WU intermediate (non-terminal gate) ---
      - id: FEAT-2026-0024/G1-CLOSE-INTERMEDIATE
        file: WU-90-gate-1-close-intermediate.md
        depends_on: [FEAT-2026-0024/T01, FEAT-2026-0024/T02]
      - id: FEAT-2026-0024/G1-PLAN
        file: WU-91-gate-1-plan-next.md
        depends_on: [FEAT-2026-0024/G1-CLOSE-INTERMEDIATE]
  - gate: 2
    file: GATE-02.md
    work_units:
      # Substantive WUs drafted by G1-PLAN (issue #46, the issue/PR-body Action).
      # T03 (runner) depends on nothing — gate 1 is the barrier and the committed
      # hashed denylist already exists; T04 (workflow + docs) wires T03. Docs are
      # bundled into T04 (a standalone `docs`-type WU mid-gate would collide with
      # the closing-sequence detector in lint_plan.py).
      - id: FEAT-2026-0024/T03
        file: WU-03-content-scan-runner.md
        depends_on: []
      - id: FEAT-2026-0024/T04
        file: WU-04-action-workflow-and-docs.md
        depends_on: [FEAT-2026-0024/T03]
      # --- closing sequence: 1-WU close (terminal gate) ---
      - id: FEAT-2026-0024/G2-CLOSE
        file: WU-90-gate-2-close.md
        depends_on: [FEAT-2026-0024/T03, FEAT-2026-0024/T04]
```

## Notes

- **Two gates, both independently shippable.** Gate 1 (#45) is a complete,
  useful improvement on its own — CI gains org-name coverage. Gate 2 (#46)
  consumes gate 1's committed hashed denylist + scanner. `autonomy: review`
  halts at the gate boundary so the hashing core is eyeballed before the Action
  builds on it (security tooling + a surface that posts to a public GitHub).
- **Both gate-1 WUs are `model: opus`, `effort: high`.** Same rationale as
  FEAT-2026-0022's Notes: the changes sit in the leak-guard correctness path,
  and a false-negative regression silently re-opens the leak surface this
  feature exists to close. Each is red-test-first (`/authoring-work-units` §12).
- **`planned_cost_usd: 16.00` is the full feature total** (gate-1 T01 $2.50 +
  T02 $2.50 + G1-CLOSE-INTERMEDIATE $2.00 + G1-PLAN $2.00; gate-2 T03 $2.50 +
  T04 $2.00 + G2-CLOSE $2.50). Reconciled up from the $11.50 draft estimate once
  `plan-next` drafted gate 2's substantive WUs (T03, T04), per the lint Σ-check.
- **Dependencies live here, not in WU frontmatter.** WU file numbers track the
  correlation sub-ID; closing units use the reserved 90+ range.
