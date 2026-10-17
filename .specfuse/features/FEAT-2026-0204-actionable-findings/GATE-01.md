---
gate: 1
status: awaiting_review
feature_oracle: "python3 -m unittest tests.test_monitor_finding_lifecycle_end_to_end tests.test_monitor_finding_context_end_to_end -v -b"
cost_budget_usd: 36.00
broad_run:
  tree: 014779809262a45fe65968ee7f836779c2801631:06e0c26931e87f6cdaad1fae464cf4e2fc857483:07ca9c541fb97154fd97d8e23d7f69cd87918215:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4444b5ce09c73cf0225108da03b75a9bff889310:4acc6dfc5e8cece358c167d876515eba4a39a500:55b11c7ec71942c69f5e48ed7d35c15ab8b6dddc:5ff66b6e4d8a264f23709ea60706111a4c59ed11:727e67bb41107456bc0a367716633c5f25f0c483:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:ba1ab2fe62a90d25fafb5cf043ce40c5f6c32dbe:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-10-17T16:33:37.580635+00:00
  ok: false
  failing:
    - gate: tests
      failure_class: tests
      failure_signature: "(failures=1,"
    - gate: coverage
      failure_class: other
      failure_signature: "no_gate_marker"
---

# Gate 1 — findings that are never refiled, never false, and carry what a diagnosis needs

## Definition of done

**Stated as an outcome.** Driven through `run_cycle(dry_run=False)` with stub
transports and a stub `gh`:

1. A fingerprint whose issue is **closed** within the lookup window is **reopened**
   with exactly one comment carrying the new occurrence count and first/last seen in
   UTC, and no `gh issue create` is issued for it. A fingerprint whose issue is open
   still takes today's update path, and a new fingerprint still files one issue.
2. Nothing in the monitor closes an issue.
3. A **closed `dlq`** issue whose recorded message ids cover every message in the
   queue stays closed with no `gh` write; a new message id reopens it with a comment
   naming that message.
4. A `heartbeat` target whose expected firing precedes the component's earliest
   observed heartbeat produces **no** `silent-schedule` finding; a target that has
   emitted before and then missed a firing still does.
5. A finding-meta marker the reader cannot fully understand reads as **absent** and
   never raises out of a cycle.
6. Every finding's title is readable without the fingerprint, it carries
   `component:<name>` and `check:<type>` labels, and its body says when and where it
   was seen this run (count, first, last in UTC, instances) — with no fingerprint
   changed by any of it.
7. For each of `error-logs`, `http-5xx`, `dlq`, `heartbeat` and `queue-stalled`, a
   finding built from fixture rows carries the sections `PLAN.md`'s "Diagnostic
   context" names for that check; each check still issues exactly one query, every
   query passes the workspace schema check, and every section is redacted before
   egress.

The `feature_oracle` proves 1, 3, 4, 6 and 7 end to end. It is red on the current tree (the
module does not exist) and `FEAT-2026-0204/T01` is the walking skeleton that turns it
green for clause 1 — the only unit in this gate permitted to stub
(`/authoring-work-units` §14). T01 creates both oracle modules **first**; every class
it cannot yet satisfy starts as `unittest.skip` with a reason **naming the unit that
owns it** (T03–T08), and each owning unit removes its skip. A skip that survives to the close is a hollow oracle, and the close checks for
it by name.

Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Scope boundary lifted on purpose (PLAN.md decision 1).** `issues.py`'s docstring
  says the module never reopens. T01 changes that sentence to "never closes" in the
  same diff as the reopen call. A drafted change that reopens without rewriting the
  docstring, or that adds any `gh issue close`, is wrong rather than a variant.
- **Fail closed (§ lesson `[FEAT-2026-0113/G1-CLOSE-INTERMEDIATE]`).** `_parse_meta`
  is called on every listed finding. T02's criteria pair every "still parses" with
  "an unreadable value reads as absent and never raises", spelled as a lookup that
  cannot raise rather than a `try/except` around the caller.
- **Count callers from the tree, not the plan.** Before T02 dispatches, list every
  caller of `_parse_meta`, `find_finding_issue` and `_list_findings`
  (`grep -rn` over `specfuse/`); the plan names `record_finding` and
  `annotate_if_quiet`, and `autofix_state` and `triage` read finding issues too.
- **One query per check (PLAN.md decision 7).** T04's earliest heartbeat and every
  T05–T08 correlation are aggregates or joins inside the check's one query, never a
  second query built from a returned value (`security-boundaries.md`). The Reproduce
  KQL in a finding is text for a human, never executed.
- **Fingerprint independence.** No context field may enter `fingerprint_artifact`; a
  unit that changes a fingerprint re-files every existing finding as new.

## Reflection notes

<Written by the human at review time.>
