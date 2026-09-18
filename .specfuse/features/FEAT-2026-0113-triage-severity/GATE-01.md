---
gate: 1
status: open
feature_oracle: "python3 -m unittest tests.test_marker_dual_shape -v"
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:079d7d0f34d28da94dfc12d029c2811895aedaaa:1243e6b0132b414c07fe5cbe686e160a4037550a:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:1e7eddd5a3fb006c5435e947cd08d29e4f2b3d83:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:4acc6dfc5e8cece358c167d876515eba4a39a500:5d728025305dbcbc973444ab63766194217eee09:5f9026863810e1e3137208731988d399091684f0:5ff66b6e4d8a264f23709ea60706111a4c59ed11:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:a2e0ab09b92e5f9fb2297b90c91a8e671835590c:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:caffe2d63ceacde448842a91bc7a12c206a67523:e3b0de29b81a6c8e0abeacb3898519b98014b9ef
  ran_at: 2026-09-18T00:48:19.798038+00:00
  ok: true
  failing: []
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
