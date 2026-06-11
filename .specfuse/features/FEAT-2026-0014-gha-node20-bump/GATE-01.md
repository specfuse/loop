---
gate: 1
status: awaiting_review
---

# Gate 1 — CI workflow on Node 24 generation, no deprecation warnings

## Definition of done

- `.github/workflows/ci.yml` pins `actions/checkout@v6` and
  `actions/setup-python@v6`.
- A CI run on this feature's branch fetched via `gh run view --log` shows
  zero `Node.js 20` / `node20` deprecation lines.
- Both CI jobs (`smoke-test`) end with `conclusion: success`.
- `RETROSPECTIVE.md` exists, durable lessons (if any) are in
  `.specfuse/LEARNINGS.md`, `PLAN.md` and roadmap row reflect `done`.

Single-gate feature: combined `close` ceremony (`G1-CLOSE`) substitutes
for the four-WU closing sequence. No `plan-next` — no successor gate.

## Reflection notes

<Written by the human at review time.>
