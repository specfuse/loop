---
name: triage-issues
description: "Categorize inbound GitHub issues (bug/feature/duplicate/question/wontfix), propose a route for each, and record the decision through specfuse.loop.triage's marker-first write path. Judgment only — classifies free text and proposes; the operator confirms before anything is written. Never acts on the route it names."
---

<!--
Copyright 2026 Specfuse Contributors
Licensed under the Apache License, Version 2.0. See LICENSE.
-->

# Triage inbound issues (interactive)

This skill answers "what is this issue, and where should it go?" for open
issues `specfuse.loop.triage.list_untriaged` finds with no triage marker. It
reads each issue, proposes a category and a route, and — on the operator's
explicit accept — records the decision through `apply_triage`.

The module (`specfuse/loop/triage.py`) owns the mechanism: the closed
category vocabulary, the category-to-route map, the marker's render/parse
pair, and the untriaged scan. This skill owns the judgment: reading an
issue's free text and proposing which of the five categories it is. See
`PLAN.md`'s "the seam" section — this skill does not re-implement the
vocabulary, the routes, the marker format, or the scan.

## Categories and routes

Quoting the contract `specfuse/loop/triage.py` defines, not authoring one:

| category | route |
| --- | --- |
| bug | fix-bug |
| feature | roadmap-add |
| duplicate | link-and-close |
| question | needs-human |
| wontfix | close |

`duplicate` has no detection mechanism. The module gives it a marker and a
route and nothing else — no similarity search, no automatic linking. This
skill proposes `duplicate` only from reading the issue itself (e.g. it
references or quotes another issue by number); the operator confirms it, the
same as every other category.

## Hard rules

- **Propose and confirm, per issue.** For each issue: a proposed category, its
  route (from the table above), a one-paragraph rationale, and a confidence
  (`high` or `low`, per `CONFIDENCES`). The operator accepts, changes, or
  skips each. Nothing is written before an explicit accept for that issue.
- **Skip the already-structured.** `list_untriaged` flags a row
  `already_structured` when it carries a harvester finding marker
  (`specfuse/monitor/issues.py`'s marker). Propose that issue's category from
  its structure (it is a `monitoring-finding`, so `bug`) rather than
  re-categorising it from prose.
- **Never act on a route.** This skill categorises, routes, and records. It
  does not invoke `/fix-bug`, does not write a roadmap row, and does not
  close an issue. It names the route and stops.
- **Record only through `apply_triage`.** All writes go through
  `specfuse.loop.triage.apply_triage`, marker first, label best-effort. This
  skill does not hand-compose the marker string or call `gh issue edit`
  itself.
- **`auto` stays off unless the operator asks for it.** `apply_triage`'s
  `auto` parameter defaults to `False`. Only pass `auto=True` when the
  operator explicitly asks for the auto dial; even then, `apply_triage`
  itself downgrades any non-`high`-confidence decision to `question` before
  writing — this skill does not need to re-implement that downgrade.

## When to invoke

- User runs `/triage-issues` to sweep open issues with no triage marker.
- User asks to "triage", "categorize", or "sort" inbound issues.
- User pastes an issue and asks what category/route it should get.

Do NOT invoke for: acting on an already-named route (that is `/fix-bug`'s,
`/roadmap-add`'s, or the operator's job); re-triaging an issue that already
carries a marker (v1 is: marked means done, per `PLAN.md`'s scope boundary);
deterministic duplicate detection (does not exist — see above).

## Method

### 1. Scan for untriaged issues

Call `specfuse.loop.triage.list_untriaged(runner, repo)`. Each returned row
carries `number`, `title`, `body`, `labels`, and `already_structured`.

### 2. Propose per issue

For each row, in order:

- If `already_structured` is `True`, propose `bug` (the harvester only
  creates `monitoring-finding` issues) with a rationale naming the finding
  marker as the source, and skip free-text classification entirely.
- Otherwise, read the issue's title and body and propose one of the five
  categories from the table above, its route, a one-paragraph rationale, and
  a confidence.
- Present the proposal to the operator and wait for accept / change / skip.
  A "change" replaces the proposed category (and its route, read from the
  table, not re-typed) before recording. A "skip" leaves the issue untouched
  — no marker, no label, retried on the next scan.

### 3. Record accepted decisions

Batch the accepted decisions (or record them one at a time — either is
correct) and call `specfuse.loop.triage.apply_triage(runner, repo, decisions,
auto=...)`. Report each row's `marker_written` / `label_written` outcome; a
failed label write is cosmetic (per `PLAN.md`'s "registered is not
provisioned" note) and does not mean the issue is still untriaged.

### 4. RESULT

Per [`../../rules/result-contract.md`](../../rules/result-contract.md).
`status: complete` means: the scan ran, every returned issue was presented
for accept/change/skip, and every accepted decision was recorded through
`apply_triage`. `status: blocked` is reserved for the escalation triggers
below.

## What this skill does NOT do

- **Does not act on a route.** No invoking `/fix-bug`, no writing a roadmap
  row, no closing an issue — categorise, route, record, stop.
- **Does not detect duplicates.** `duplicate` is judgment-only; there is no
  similarity search or automatic linking anywhere in this skill or in
  `triage.py`.
- **Does not re-implement the mechanism.** The vocabulary, the routes, the
  marker format, and the scan all live in `specfuse/loop/triage.py`; this
  skill calls them, never restates them as independent logic.
- **Does not write anything before an explicit per-issue accept.** No batch
  auto-apply of proposals the operator has not seen.
- **Does not re-triage a marked issue.** A marker present means done, per
  `PLAN.md`'s scope boundary — whether stale triage should ever be revisited
  is deliberately left open.

## Escalation framing (binding — `.specfuse/rules/operator-escalation.md`)

Whenever this skill halts for a human decision — `gh` is unreachable, an
issue's text is too ambiguous to propose any category with a `high`
confidence, or a proposed category does not fit the five available — present
it in the six parts that rule requires, in plain English, **before** any
correlation ID or field name: what has been done so far; what the issue is
about; what decision is needed and why; why it did not resolve automatically;
the options with their pros and cons; and a recommendation.

Never author the operator's own justification. Where a field records *why a
human decided something* (a category, a route), that text comes from them,
not from this skill.

## Version

**v0.1.** First cut: scan via `list_untriaged`, propose per issue, record
accepted decisions via `apply_triage`. `FEAT-2026-0045/T03`, the judgment
half of the mechanism T01 and T02 shipped.

The drift test (`tests/test_triage_skill_contract.py`) asserts this file's
documented categories and routes match `specfuse/loop/triage.py`'s constants
exactly. That is worth having — prose and constants are two statements of one
contract, and prose drifts — but it is **not** proof that an agent following
this prose triages an unseen issue correctly. No test in this repository
composes this skill with the module end-to-end; that composition is untested
by design, per `[FEAT-2026-0069/G2-CLOSE]`.
