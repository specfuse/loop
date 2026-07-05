<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: never-touch list

Three categories of path are off-limits to every work-unit session, regardless of
unit type. If a unit's acceptance criteria or verification commands appear to
require modifying something in this list, that is an escalation condition, not a
license to proceed — signal blocked per
[`verification-discipline.md`](verification-discipline.md), naming the
boundary. (How "blocked" is signalled is surface-specific — a `status: blocked`
RESULT on the loop, a `blocked_*` transition on the orchestrator.)

## 1. Generated code directories

Any path under a generated directory — `_generated/`, `gen-src/`, or whatever the
repo declares as its generated tree — is off-limits. Generators own those files
end-to-end; an edit there is silently overwritten on the next regeneration and
leaves no trace of why.

- The canonical names are `_generated/` and `gen-src/`, but the repo's own
  declaration (in its README, a `specfuse.yaml`, or equivalent config) is
  authoritative. If your repo's generated directory uses a different name, treat
  that name with identical prohibition.
- The rule applies to every file under the directory, recursively. Creating a new
  file inside a generated directory is still a write to that directory.
- The rule applies regardless of whether the file currently exists.

When a generated file is wrong, the response is to change the spec or the generator
that produced it, not the file itself. If that is outside this unit's boundary,
signal blocked with the spec/generator change named.

## 2. Secrets and credentials

Secrets include, at minimum: API tokens, deploy keys, SSH private keys, OAuth
client secrets, webhook signing secrets, database passwords, `.env` files, cloud
credentials (AWS, GCP, Azure), and any file conventionally holding a credential
(`*.pem`, `*.key`, `id_rsa*`, `credentials.json`, `.npmrc` tokens, `gh auth`
tokens).

You must not:

- Read the contents of a secrets file. If a unit requires one, see
  [`security-boundaries.md`](security-boundaries.md) for the escalation path.
- Write any value that looks like a credential into the RESULT block, the event
  log, a commit, or any artifact you produce — whether the value came from a real
  secret or was invented.
- Echo the contents of environment variables that hold secrets. Reference them by
  name (`$GITHUB_TOKEN`) over reading their values.
- Commit secret files to the repo under any circumstance, including as examples
  or fixtures.

## 3. `.git/` internals

The `.git/` directory is the repository's internal state. On the loop surface the
driver owns all git operations for work units and the session does not run `git`
at all; on the orchestrator surface an agent may use `git`/`gh` within its unit's
scope. Either way, never write under `.git/` directly:

- No edits to `.git/hooks/*` to bypass checks. If a hook is failing, the right
  response is to diagnose the underlying issue.
- No edits to `.git/config` to change remotes, identity, or signing settings.
- No `git` invocation with flags that skip hooks or signing (`--no-verify`,
  `--no-gpg-sign`, `-c commit.gpgsign=false`) — unless the human has explicitly
  asked for that specific action, which the driver passes through.

## A note on `verification.yml`

`.specfuse/verification.yml` is not on this list — a unit may legitimately add a
gate or refine a command — but **weakening or removing a failing gate to make a
unit pass is forbidden**. That is the same class of failure as bypassing
`.git/hooks/`: corroding the trust model the gates exist to uphold. The correct
response to a failing gate is to fix what it is flagging, not to silence it.

## Applying this rule

Before writing to any path, confirm it is not in one of the three categories above.
If you are uncertain whether a path is "generated" or "hand-written," the repo's
declaration is authoritative; if the declaration is missing or ambiguous, treat
the path as generated and signal blocked rather than write. Silence at a
boundary is not permission.
