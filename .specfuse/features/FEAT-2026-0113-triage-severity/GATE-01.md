---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_marker_dual_shape -v"
---

# Gate 1 — the triage marker reads both shapes, and nothing writes severity yet

## Definition of done

A triage marker carrying a `severity=` field parses, **and** every marker shape
already written in the wild parses exactly as it does today, with no write path
changed anywhere. This gate proves backward compatibility before anything depends
on it.

The risk this gate exists to retire: `_MARKER_RE` is positionally anchored —

```python
r"<!-- specfuse:triage category=(?P<category>\S+) confidence=(?P<confidence>\S+) -->"
```

— so `\S+` cannot span the space before an appended field and the literal ` -->`
cannot match. Adding `severity=` makes the regex **fail to match entirely**: every
new marker would scan as untriaged and be re-triaged on every run, and the triage
label would be reapplied forever. That is the orphaning the published-marker
contract explicitly warns about ("treat the format as frozen; a future change needs
a reader that accepts both shapes, not an edit"). Landing the reader alone, with
nothing writing the new shape, is what makes the rest of the feature safe to build.

Standard gate obligations (retrospective, lessons, docs, next-gate drafting,
per-criterion state and the narrow/broad oracle contract) are as
`close-discipline.md` §5 defines them; they are not restated here.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

Gate 2 drafts the write path. Before arming it, note that `PLAN.md`'s **Record
precedence** section already fixes marker-before-label and the label as a projection
— a drafted unit that reorders those is wrong, not a variation.
