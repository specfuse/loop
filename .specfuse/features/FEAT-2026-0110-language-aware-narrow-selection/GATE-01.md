---
gate: 1
status: passed
feature_oracle: "python3 -m unittest tests.test_language_aware_narrow_selection -v"
broad_run:
  tree: 06e0c26931e87f6cdaad1fae464cf4e2fc857483:1a491e59f645ae69f7a291810e4df3ccf0cde2ec:27968248a450a842ccd187b7dce0fb0ded934866:2891080d52e158d5ad72b08822c9becd9d909eb1:3e1ed273ab9179bbc8a1519961dcece15f51277e:5ff66b6e4d8a264f23709ea60706111a4c59ed11:6cb941893be702d489774709423122f148c85211:706675bf82a610e5a4fe6021214483f397139732:834d9d9c16094a386cd9b5a6f9ced9a3a9b4e7fb:97bcab1bc7244262cec901f46035f51dfdd07278:a0ac7a4e56881082fa9373fe5b68d3901463c958:bbd1aea514612d76722a18c7aece7c767cf1a076:c23b62e87f1ae3890c6f9e3d8c7ca7ec9225ed81:c63b7c407a689c32ecafdfb843f171e836e5c489:caffe2d63ceacde448842a91bc7a12c206a67523:dc734df9a53b15728edf9acb076b52d2bd5c6680:e3b0de29b81a6c8e0abeacb3898519b98014b9ef:f96c4e965f231f26dff4e4ded388639f5e348b50
  ran_at: 2026-09-10T00:47:07.337943+00:00
  ok: true
  failing: []
---

# Gate 1 — a non-Python project narrows its per-attempt tests gate

## Definition of done

A work unit whose `produces:` names tests outside `tests/`, in a project whose
`tests` gate declares `narrow_selection`, resolves to a narrow command its own
runner accepts — instead of falling back to the full suite because the selector
only understands dotted Python module names under `tests/`.

The `feature_oracle` above is that claim, executable. It is **red on the tree
this gate starts from** (the module does not exist), and T01 — the walking
skeleton — is what makes it green. It asserts the Maven shape end to end:
a unit declaring `produces:` under `src/test/java/`, a gate declaring
`format: class_name` and `separator: ","`, resolving through
`resolve_narrow_command` to `./mvnw test -Dtest=FooTest,BarTest`.

Also required for the gate to close:

- Every implementation work unit in this gate is `done`.
- A retrospective exists (feature-local `RETROSPECTIVE.md`).
- Generalizable lessons are promoted to `.specfuse/LEARNINGS.md`.
- Documentation reflects what was actually built.
- Per-criterion state and the narrow/broad oracle contract: `close-discipline.md` §5.

This is the feature's terminal gate, so its closing sequence is a single `close`
unit and the terminal verdict is written by a fresh judge session, not by the
close itself.

## The absent-key default is load-bearing

Every key this gate adds is optional, and the defaults reproduce the current
behaviour byte-for-byte:

| key | default | today's behaviour it reproduces |
| --- | --- | --- |
| `test_roots` | `["tests/"]` | `select_narrow_test_modules`' `p.startswith("tests/")` |
| `format` | `python_module` | `_test_module_name`'s dotted conversion |
| `item_template` | `"{module}"` | each module substituted verbatim |
| `separator` | `" "` | `" ".join(modules)` in `resolve_narrow_command` |

A `verification.yml` declaring no `narrow_selection` anywhere must behave
exactly as it does today. That is what keeps this repo's own `tests` gate
untouched, and it is what keeps every WU in this gate holding a working exit
oracle — see PLAN.md's framing on `[FEAT-2026-0019/G1]`.

## Arming discipline (see `.specfuse/rules/planning-discipline.md`)

- **Runtime probe for a default/severity flip (§4).** No WU in this gate flips
  an existing default or severity: every key is new and optional, and the
  defaults are chosen to reproduce current behaviour. T02 introduces one new
  refusal on an unknown `format` value — PLAN.md's satisfiability section
  records that it reports zero on every gate in the current corpus.
- **Flag-scope table (§3).** No WU introduces or flips a behaviour flag.
  `CHANGED_FILE_SELECTION_ENABLED` is explicitly out of scope and is not
  touched.

## Reflection notes

<Written by the human at review time.>
