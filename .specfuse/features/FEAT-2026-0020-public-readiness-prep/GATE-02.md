---
gate: 2
status: passed
---

# Gate 2 — Public hygiene + flip-readiness

Lands the public-facing hygiene files (README polish, CONTRIBUTING, SECURITY,
CODE_OF_CONDUCT, dependabot, issue + PR templates), a **leak-prevention guard** (so the
audit's cleanup can't silently recur), and a `FLIP-CHECKLIST.md` enumerating the
visibility-flip steps + owners + rollback. The flip itself is operator-side; the loop
confirms readiness.

## Definition of done

- Drafted by `G1-PLAN` from gate 1's retrospective + lessons. Substantive work units land
  here.
- Terminal gate — uses `close` (not `close-intermediate`). `G2-CLOSE` emits the terminal
  feature-arc verdict.
- DoD is finalized by `G1-PLAN`; this stub records the gate's purpose.

### Required deliverable — leak-prevention guard (operator-requested 2026-06-15)

`G1-PLAN` MUST draft at least one substantive WU implementing a pre-leak guard, scoped
roughly as below. Rationale: gate 1 had to rewrite history to expunge private-org names,
personal paths, and the leaked cross-poll folder; without an automated guard the same
leaks recur on the next commit.

- **`leak-scan` script** — one detector, three callers. Factor the pattern-matching out of
  `history-scrub/scrub-history.sh --verify-only` so the same logic runs against (a) the
  staged diff (pre-commit), (b) CI, and (c) full history (audit). Scans for: secrets (wrap
  `gitleaks protect --staged`, already in the toolchain from T01), `/Users/<user>/` path
  shapes, non-allowlisted emails, private hostnames, and a private-org denylist.
- **`pre-commit` hook** — runs `leak-scan` on staged changes; blocks the commit on a hit.
  Must be read-only, fast, and sandbox-safe (per the pre-push-hook + sandbox-off
  corruption learning — no heavy/destructive work in the hook). `--no-verify` escape hatch
  documented for emergencies.
- **CI gate** — add a `leak-scan` entry to `.specfuse/verification.yml` mirroring the hook,
  because hooks are not enforced and `--no-verify` bypasses them. CI is the real backstop.
- **Allowlist** — exempt legitimate samples so the guard does not false-positive the way
  the first scrub did. Notably `INIT-2026-0001` is the scaffold's canonical orchestrated
  correlation-ID sample (see `.specfuse/rules/correlation-ids.md`), NOT a leak — it must be
  allowlisted. See LEARNINGS `[FEAT-2026-0020/history-scrub/scope-vs-fixtures]`.
- **Denylist-not-committed constraint** — a denylist of *literal* private-org names cannot
  ship in a public repo (committing it re-leaks the very strings). Commit only generic
  structural regexes (path/email/key shapes); keep any literal org-name denylist gitignored
  or stored as hashes. This constraint is itself an acceptance criterion.
- **Tests** — unit tests proving the scanner flags a planted leak and passes a clean diff,
  plus that the allowlist exempts `INIT-2026-0001`.

## Reflection notes

<Written by the human at gate close.>
