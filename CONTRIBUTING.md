# Contributing to Specfuse Loop

Specfuse Loop is part of the Specfuse methodology suite, alongside
`specfuse/codegen` and `specfuse/orchestrator`. Each project is independently
adoptable; contributions should keep the loop usable on its own, with no hard
dependency on the other two.

## Ground rules

- **Open-source hygiene from every commit.** No consumer-product names, no
  private-organization names, no internal URLs, no fixtures containing
  sensitive data. Write every commit message and code comment as if a stranger
  will read it. Apache 2.0 license headers belong on source files from the
  first commit.
- **Boring beats clever.** Git, Markdown, a polling/driver loop, plain files.
  Every piece should be individually replaceable. Nothing load-bearing that
  needn't be.
- **The contract is shared; the implementation is local.** The gate-cycle
  methodology, the work-unit contract, the correlation-ID scheme, and the
  verification discipline are shared vocabulary with `specfuse/orchestrator`.
  Changes to those contracts are coordinated, not unilateral — see
  `docs/methodology.md`.

## First-time setup (install the leak-prevention guard)

Run once per fresh clone to install the pre-commit leak-scan hook and seed the
gitignored org-name denylist:

```bash
bash scripts/setup.sh
```

This sets `core.hooksPath` to `.specfuse/hooks` (so the `pre-commit` hook runs
the leak scanner on every commit) and creates `.specfuse/scripts/leak_denylist.txt`
— a **gitignored** file where you list any private org / repo / hostname strings
this clone must never commit. The hook blocks commits that introduce secrets,
`/Users/<user>/` paths, emails, private hostnames, or a denylisted string.
Emergency bypass: `git commit --no-verify` (CI still enforces the secrets gate).

> The denylist is gitignored on purpose — committing the literal private strings
> to a public repo would re-leak them. Each clone keeps its own.

## Running tests and gates locally

Install dev dependencies once:

```bash
python3 -m pip install -e '.[dev]'
```

Run everything CI runs — scaffold integrity check plus all `code` gates — with
one command:

```bash
./scripts/smoke-test.sh
```

Or run individual gates from `.specfuse/verification.yml` directly:

```bash
# Unit tests
python3 -m unittest discover -s tests -v

# Lint
ruff check .specfuse/scripts tests scripts

# Security scan (medium+ severity)
bandit -r .specfuse/scripts -ll

# Coverage (must stay ≥ 90 %)
coverage run --source=.specfuse/scripts -m unittest discover -s tests \
  && coverage report --fail-under=90
```

`scripts/smoke-test.sh`, `.specfuse/verification.yml`, and
`.github/workflows/ci.yml` all declare the same commands. If you change one,
change all three — drift breaks the verification-as-oracle property.

## Before opening a PR

- **Branch from `main`.** Name your branch something descriptive
  (`fix/lint-discovery`, `feat/gate-timeout`).
- **Reference an issue.** Mention the issue number in the PR description
  (`closes #N` or `re: #N`). For design-touching changes, open the issue first
  and discuss before coding.
- **Scope one change per PR.** A PR that changes the loop driver *and* the
  methodology contract is two PRs. Mixing unrelated changes makes review and
  revert harder.
- Run `python3 .specfuse/scripts/lint_plan.py .specfuse/features/<feature>` on
  any feature folder you touched.
- Run `python3 .specfuse/scripts/loop.py --dry-run` against the bundled example
  and confirm it still walks the gate in dependency order.
- Run `./scripts/smoke-test.sh` and confirm it exits `0` before pushing.

## How this repo develops itself

Specfuse Loop is developed using its own methodology — every non-trivial change
goes through the gate-cycle process it ships.

**Substantive changes (new features, API changes, methodology updates)** are
planned as a Specfuse feature: a folder under `.specfuse/features/` with a
`PLAN.md` that defines gates and work units. The driver runs each work unit, the
gates verify it, and a human reviews and arms each gate boundary before the next
one opens. If you want to propose a significant change, open an issue first — the
maintainers will determine whether it needs a full feature folder or can be a
simple bug-fix PR.

**Bug fixes** follow the 1-bug-1-branch-1-PR rule: one branch, one PR, no
feature folder. Write a test that reproduces the bug first, then fix it. Keep
the scope tight — refactoring unrelated code in the same PR is out of scope.

This self-dogfooding means `.specfuse/features/` is also the audit trail for how
the repo itself has evolved. See `docs/methodology.md` for the full gate-cycle
contract.

## Reporting

Use the issue tracker for bugs and design discussion. For anything touching the
shared contracts, say so explicitly in the issue title so it can be coordinated
with the other Specfuse projects.
