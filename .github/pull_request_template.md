## Summary

<!-- One or two sentences: what does this PR do and why? -->

## Linked issue

Closes #<!-- issue number -->

## Type of change

- [ ] Bug fix (1-bug-1-branch-1-PR: test reproduces the bug first, then fix)
- [ ] Feature / substantive change (went through `.specfuse/features/` gate cycle)
- [ ] Config / docs / cosmetic (no behavioural surface changed)

## Pre-PR checklist

> Mirror of CONTRIBUTING.md "Before opening a PR".

- [ ] Branch from `main` with a descriptive name (`fix/…`, `feat/…`)
- [ ] Issue referenced above (`closes #N` or `re: #N`)
- [ ] One change per PR — unrelated changes split into separate PRs
- [ ] `python3 .specfuse/scripts/lint_plan.py .specfuse/features/<feature>` passes (if a feature folder was touched)
- [ ] `python3 .specfuse/scripts/loop.py --dry-run` walks the gate in dependency order
- [ ] `./scripts/smoke-test.sh` exits `0`

## Notes for reviewer

<!-- Anything non-obvious about the implementation, trade-offs made, or areas to focus on. -->
