---
gate: 1
status: passed
feature_oracle: "python3 -m unittest tests.test_diagnosis_severity_end_to_end -v -b"
cost_budget_usd: 24.00
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:1fea2572bb182d4233b903d016587fe6aeb4b58a:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:56bb22809af19d9fe40ed1755749bbb055c02a2a:5a5f687302f4c04388f1fb3c9b331b789186aef8:5ff66b6e4d8a264f23709ea60706111a4c59ed11:727e67bb41107456bc0a367716633c5f25f0c483:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:8736c3a345751965905e412e4db9d75caec53f07:97bcab1bc7244262cec901f46035f51dfdd07278:9e4fee0a2e47852f661fa0cd40425fba7deb93bd:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-10-17T19:14:33.198871+00:00
  ok: true
  failing: []
---

# Gate 1 — a diagnosed finding carries a severity that orders autofix

## Definition of done

**Stated as an outcome.** Driven through the findings-diagnose and findings-autofix
providers with a stub `gh` and a stub headless session:

1. A headless analysis result carrying `"severity": "high"` posts a diagnosis whose
   marker carries `severity=high`, and the finding issue gets exactly one
   `severity:high` label; a later diagnosis with `"severity": "low"` leaves exactly
   one severity label, `severity:low`.
2. A diagnosis marker without a severity (every diagnosis posted before this
   feature) parses with severity absent, and an unknown severity value reads as
   absent; neither raises, and neither writes a label.
3. With three eligible diagnosed findings of severities `low`, `critical` and none,
   the findings-autofix provider advertises them `critical`, `low`, none — and its
   eligibility decisions are unchanged.
4. A finding issue carrying a `severity:` label and no triage marker is not
   advertised by the bug lane.
5. The headless prompt and `/diagnose-issue` ask for severity against one rubric
   defined once in code.

The `feature_oracle` proves 1–4 end to end. It is red on the current tree (the
module does not exist); `FEAT-2026-0205/T01` is the walking skeleton that creates it
first and turns clauses 1 and 2 green, with clauses 3 and 4 as `unittest.skip`
naming their owners (T03, T04). A skip surviving to the close is a hollow oracle.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Fail closed.** T01's parser pairs "an old marker still parses" with "an unknown
  value reads as absent and never raises", as a lookup, not a caller's try/except.
- **Eligibility untouched.** T03 changes order only; a drafted change to
  `autofix.decide` is out of scope.
- **Lesson `[FEAT-2026-0204/G1-CLOSE]` (live render).** The close runs one opt-in
  live headless diagnosis or records in Deferred verification why not.

## Reflection notes

<Written by the human at review time.>
