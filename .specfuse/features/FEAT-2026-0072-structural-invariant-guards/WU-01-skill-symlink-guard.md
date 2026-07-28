---
id: FEAT-2026-0072/T01
type: implementation
status: pending
attempts: 0
planned_cost_usd: 2.50
produces:
  - tests/test_skill_discovery_links.py
---

# Assert every skill has a discovery link — forward complete, reverse filtered

**Objective.** Ship `tests/test_skill_discovery_links.py`: every directory under
`.specfuse/skills/` has a `.claude/skills/` entry symlinking to it, and no link
pointing *into* `.specfuse/skills/` dangles.

**Context.** Correlation ID `FEAT-2026-0072/T01`. This is the guard; T02 makes
`sync-scaffold.sh` satisfy it automatically.

`CLAUDE.md` states the contract — *"Skills under `.claude/skills/` are symlinks
into `.specfuse/skills/` so Claude Code's discovery picks them up."* Nothing
enforced it, and four skills sat invisible for seven weeks (#284). The links
themselves were restored in PR #285, so this WU adds the assertion, not the data.

**Copy the shape of `tests/test_bats_suites_gated.py`.** That guard (#257) is the
working precedent for this exact problem: diff a declared set against an actual
set, assert both directions, and carry an explicit opt-out whose entries require a
written reason. Read it before writing. **Do not import from it** — two checks over
unrelated surfaces sharing a helper couples them for no gain.

**The asymmetry is the whole point, and getting it wrong is the obvious mistake.**
Seven entries in `.claude/skills/` point at `../../.agents/skills/` — local
operator tooling, untracked, nothing to do with specfuse:

```
cavecrew, caveman, caveman-commit, caveman-compress,
caveman-help, caveman-review, caveman-stats
```

A symmetric `set(.specfuse/skills/*) == set(.claude/skills/*)` assertion reports
non-zero on a correct tree, which makes it unsatisfiable under
`planning-discipline.md` §2. So:

- **Forward, complete:** every directory in `.specfuse/skills/` must have a
  `.claude/skills/` entry that is a symlink resolving to that directory.
- **Reverse, filtered:** only entries whose link target resolves inside
  `.specfuse/skills/` are checked for a live target. Everything else is ignored,
  and the test must say why in a comment.

Binding rules apply by reference: `result-contract.md`, `never-touch.md`,
`security-boundaries.md`, `correlation-ids.md`.

**Acceptance criteria.**

1. `tests/test_skill_discovery_links.py::TestSkillDiscoveryLinks::test_every_skill_has_a_discovery_link`
   exists and **fails on HEAD before this WU runs** (the test file does not yet
   exist, which counts as red).
2. A test asserts every directory in `.specfuse/skills/` has a corresponding entry
   in `.claude/skills/`, and names the offenders when it fails.
3. A test asserts each such entry is a **symlink** (not a copied directory) whose
   resolved target is the matching `.specfuse/skills/` directory.
4. A test asserts that entries in `.claude/skills/` whose target resolves inside
   `.specfuse/skills/` all resolve to something that exists — no dangling links.
5. Entries in `.claude/skills/` whose target resolves **outside**
   `.specfuse/skills/` are ignored by every assertion, and a comment in the test
   states that they are operator tooling and why a symmetric check would be wrong.
6. The whole suite passes against the tree as it stands — PR #285 restored the
   four missing links, so this check reports zero on a correct tree today.
7. An `_INTENTIONALLY_UNLINKED` mapping exists for deliberate exclusions, is
   **empty** as of this WU, and a test asserts every entry in it carries a
   non-empty reason string.
8. A test asserts no entry in `_INTENTIONALLY_UNLINKED` names a skill absent from
   `.specfuse/skills/` — a stale opt-out is its own drift.
9. `python3 -m pytest tests/test_skill_discovery_links.py -q` exits zero after
   this WU's edits (the same file named in criterion 1).

**Do not touch.** `tests/test_bats_suites_gated.py` — read it for shape, do not
edit or import it. Anything under `.claude/skills/` or `.specfuse/skills/` — this
WU asserts on that tree and must not modify it; if the assertion fails, report it
rather than creating a link to make your own test pass. `scripts/sync-scaffold.sh`
— T02 owns it. Generated directories, secrets, `.git/`. See
`.specfuse/rules/never-touch.md`.

**Verification.** The `code` gate set in `.specfuse/verification.yml`: `tests`,
`lint`, `security`, `coverage` (≥90%), `leak-scan`. Plus the scoped red/green run
in criteria 1 and 9.

**Escalation triggers.** Emit `status: blocked` rather than pushing through if:
the forward assertion fails on the current tree, meaning a skill link is missing
that PR #285 was supposed to have restored — report which, do not create it; or
distinguishing "resolves inside `.specfuse/skills/`" from "resolves elsewhere"
cannot be done reliably for a relative symlink. If
`tests/test_skill_discovery_links.py` is absent from the files you edited, emit
`status: blocked` — do not claim complete.
