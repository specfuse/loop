---
id: FEAT-2026-0003/T02
type: implementation
model: claude-sonnet-4-6
status: pending
attempts: 0
---

# GitHub feature discovery — list specfuse:feature issues as loop-feature candidates

**Objective.** Add `.specfuse/scripts/gh_features.py`: a discovery script that
lists a target repo's open `specfuse:feature` GitHub issues and maps each to a
loop-feature candidate, with an injectable command runner so it is fully
unit-tested without a live `gh` call.

**Context.** This is `FEAT-2026-0003/T02`, gate 1 of the GitHub feature-pick
build. Step 1 of the capability ("Discover") in
[`docs/handoff-github-feature-pick.md`](../../../docs/handoff-github-feature-pick.md)
§3: query a target repo's open issues labelled `specfuse:feature`; each is a
feature. The contract from §2:

- Issue **title**: `[<id>] <summary>` where `<id>` is `INIT-YYYY-NNNN/FNN`
  (orchestrated) or `FEAT-YYYY-NNNN` (component-local).
- Issue **labels**: `specfuse:feature` (the query), `initiative:INIT-YYYY-NNNN`
  (present only on orchestrated features; absent ⇒ component-local),
  `type:<task-type>`, and an `autonomy:<level>` label when present.

`gh` is the host's authenticated tool — using it is authorized
(`security-boundaries.md` "authenticated tooling"); never read or echo the
value of `GH_TOKEN` or any credential, reference it by name only. Follow the
loop's existing testability pattern: an injectable callable (cf. `loop.py`'s
`dispatch_fn` / `verify_fn` stubs) so tests pass canned JSON instead of spawning
`gh`. Reference the binding rules under `.specfuse/rules/`; honor
`result-contract.md`, `never-touch.md`, `security-boundaries.md`.

**Acceptance criteria.**
1. `gh_features.py` defines `list_features(repo, runner=<default>)` returning a
   list of candidate objects. The default `runner` shells `gh issue list --repo
   <repo> --label specfuse:feature --state open --json
   number,title,labels,url,body` using `subprocess` with an **argument list (no
   `shell=True`)** and returns the parsed JSON; `runner` is injectable for tests.
2. Each issue maps to a candidate carrying: `feature_id` parsed from the title's
   leading `[…]` tag (admits both `INIT-YYYY-NNNN/FNN` and `FEAT-YYYY-NNNN`),
   `title` (the summary after the tag), `initiative` (the value after
   `initiative:` on a matching label, else `None`), `task_type` (the value after
   `type:`, else `None`), `autonomy` (the value after `autonomy:`, else the
   default `review`), `url`, and `number`.
3. An issue whose title has no parseable `[<id>]` tag is skipped with a warning
   to stderr — discovery is read-only and resilient, never crashes on one bad
   issue.
4. A CLI entrypoint (`python3 .specfuse/scripts/gh_features.py <repo>`) prints
   one line per candidate: feature_id, task_type, autonomy, url.
5. `tests/test_gh_features.py` drives `list_features` with a stub runner
   returning canned JSON covering: an orchestrated issue (INIT title +
   `initiative:`/`type:`/`autonomy:` labels), a component-local issue (FEAT
   title, no `initiative:`, no `autonomy:` → defaults), and an untagged title
   (skipped). It asserts the parsed fields and makes **no live `gh` call**.

**Do not touch.** `loop.py`, `lint_plan.py`, `_miniyaml.py`, any feature folder
under `.specfuse/features/`, generated directories, secrets (`.env`, `*.pem`,
`*.key`, credential files — and never read `GH_TOKEN`'s value), `.git/`. The
driver owns all git — edit files only. This WU produces exactly two new files:
`.specfuse/scripts/gh_features.py` and `tests/test_gh_features.py`.

**Verification.** The `code` gates in `.specfuse/verification.yml`: the full
test suite (`python3 -m unittest discover -s tests -v`), `ruff` lint, `bandit`
security scan (must stay clean — the argument-list `subprocess` call must not
trip a medium+ finding), and coverage ≥ the floor (the new script must be
exercised by the new tests so TOTAL coverage does not drop below the gate).

**Escalation triggers.** If the title/label contract in the handoff is
insufficient to determine `feature_id` or `autonomy` unambiguously, stop and
emit `status: blocked` naming the gap rather than inventing a label scheme. If
writing the default runner requires a `gh` flag the host `gh` does not support,
note it — but since tests stub the runner, the unit work should not depend on a
live `gh`; only block if the default runner cannot be written at all.
</content>
