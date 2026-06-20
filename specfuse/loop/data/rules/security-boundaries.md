<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Rule: security boundaries

Every session operates inside a privilege model that is narrower than "do whatever
the shell will let you do." This rule describes the generic posture every session
takes on every work unit. It complements [`never-touch.md`](never-touch.md), which
lists the specific path categories that are off-limits.

## Secrets

Secrets include API tokens, deploy keys, SSH private keys, OAuth client secrets,
webhook signing secrets, database passwords, `.env` files, cloud credentials, and
anything conventionally treated as a credential (see the enumeration in
[`never-touch.md`](never-touch.md) §2). The posture is strict:

- **Never read.** Do not open a secrets file to inspect its contents, not even
  "just to see the format." If a unit's verification needs one, stop and
  escalate (see below).
- **Never log.** Do not echo a secret value, include it in the RESULT block's
  evidence, paste it into a commit message, or write it into an event log entry.
  This applies whether the value came from a real secret or was constructed.
- **Never commit.** Secrets files are excluded from commits categorically. A
  `.env` in your working directory is a mistake; remove it before the driver
  commits, not after. If you discover a secret already committed, emit
  `status: blocked` immediately — do not attempt history rewriting.
- **Reference by name, not by value.** When a command needs a secret, pass it via
  an environment variable reference (`$GITHUB_TOKEN`) rather than substituting
  the value into the command line. Do not expand secret variables into log output;
  prefer tool invocations that read the variable themselves.
- **Do not exfiltrate.** Do not send secrets — or anything that might be a secret
  — to external services (web renderers, pastebins, diagnostic endpoints) even
  when debugging. External services cache and index input; a "deleted" paste is
  not deleted.

Treat suspected-secret values with the same care as confirmed-secret values. A
40-character hex string is a credential until proven otherwise.

## When a work unit appears to require privileged access

A unit whose acceptance criteria or verification commands appear to require
reading a secret, editing generated code directly, or any other privileged action
is almost always a unit-definition problem, not a license to break the rule.

1. **Stop.** Do not attempt the privileged action. Do not attempt to work around
   the requirement (for example, by running a command that reads the secret
   implicitly).
2. **Re-read the unit.** Verify you have understood the step correctly. Often the
   unit describes how the *human* will verify, with the session doing an
   upstream-only step.
3. **If the requirement is genuine, escalate via the RESULT block.** Emit
   `status: blocked` with a precise `blocked_reason` naming the privilege
   required (e.g., "verification command requires reading
   `config/db-prod.env`"). The driver halts the gate and the human decides
   whether to adjust the unit, run the step out-of-band, or provide a scoped
   credential.
4. **Do not report the unit complete.** A verification that could not be run is
   not a verification; a unit whose verification cannot be run is not done (see
   [`result-contract.md`](result-contract.md)).

The common mistake here is to "helpfully" substitute a weaker check for a
privileged one — "I couldn't run the secret-requiring command, so I inspected the
diff visually and it looks right." That is a verification-bypass, not a
verification, and it produces a RESULT block the driver cannot trust.

## Authenticated tooling

Some tools the session legitimately uses — `gh` for GitHub, `git` over SSH, package
registries — rely on credentials configured on the host. Interaction with those
tools is authorized without qualification: the credentials are the host's, not
yours, and you are not expected to inspect or transmit them. The prohibition is on
*reading the credentials themselves* and on *using them for anything outside the
unit's scope* — not on using a credentialed tool to do the work the unit names.

If an authenticated tool returns an error that implies a credential problem
(expired token, permission denied, 401/403), stop and emit `status: blocked`. Do
not attempt to re-authenticate, reconfigure the credential, or swap accounts.

## Log hygiene

Every line you emit may end up in the RESULT block, the event log, a commit
message, or a human's review screen. Treat them as public:

- Redact suspected secrets from any command output you reproduce as evidence. If
  you cannot redact cleanly, do not reproduce the output — reference it
  abstractly or by path.
- Do not paste stack traces that include environment variables or config-file
  contents without inspecting them first.
- Commit messages are part of the eventual public history. Write them
  accordingly: no customer names, no internal-only references, no leaked URLs.

## Scope creep

A unit that grants a specific privilege grants that specific privilege, not the
surrounding category. The authorization is for the scope named, not for adjacent
scopes that are similar. If a unit authorizes a write to file `A` and an
adjacent change to file `B` looks obvious and useful, `B` is a separate unit.
Scope creep is how small privilege grants turn into broad ones, and it is the
class of failure this rule exists to prevent.
