<!-- Per-criterion close state for gate 1 (close-discipline.md §5).
     Written by FEAT-2026-0113/G1-CLOSE-INTERMEDIATE, attempt 1. Every entry's
     oracle re-ran fresh in that session against the working tree; no green is
     inherited from a producing WU's self-report.

     Oracle key (each spelled in full at least once below):
       O1  python3 -m unittest tests.test_marker_dual_shape -v -b   (gate feature_oracle)
       O2  historical replay: `git show <sha>:specfuse/loop/triage.py` loaded as a
           module, parse_marker called on the shape under test
       O3  repo-wide marker sweep: every `<!-- specfuse:triage ... -->` literal in
           `git ls-files`, compared old anchored regex vs current parse_marker
       O4  python3 -m unittest tests.test_triage tests.test_triage_apply
           tests.test_triage_skill_contract tests.test_triage_skips_agent_escalations
           tests.test_agent_provider_triage tests.test_agent_policy_triage_dial
           tests.test_agent_invoke_usage tests.test_caller_check_ratchet
           tests.test_bug_lane_run -b
       O5  git --no-pager diff main -- specfuse/   (structural: what the gate changed)
     Every oracle above has a knowable scope (named test nodeids, a named module
     list, a countable grep over a fixed file set, a bounded diff), so every entry
     is `kind: narrow`. The full suite, coverage and the `tier: broad` gates are
     the driver's once-per-gate broad run, not a criterion oracle here. -->

### T01#1

- **criterion:** `tests/test_marker_dual_shape.py::DualShapeMarker::test_a_three_field_marker_parses` fails on HEAD before this unit runs, because the anchored regex returns no match for a marker carrying `severity=`.
- **oracle:** O2 — `git show 81e10f9^:specfuse/loop/triage.py` loaded as a module; `parse_marker("<!-- specfuse:triage category=bug confidence=high severity=critical -->")` returned `None`. O1's `test_a_three_field_marker_parses` asserts the `('bug','high')` the pre-T01 reader could not produce.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01#2

- **criterion:** The marker reader parses the fields inside `<!-- specfuse:triage … -->` as `key=value` pairs rather than a fixed sequence, so field order and field count do not decide whether a marker is seen at all.
- **oracle:** O5 — the diff shows `_MARKER_RE` reduced to a shell (`<!-- specfuse:triage (?P<fields>.*?) -->`) plus a separate `_MARKER_FIELD_RE = (\S+)=(\S+)` applied with `findall`. O1's `test_a_three_field_marker_parses` and `MarkerCorpus::test_three_field_shape_round_trips_through_the_two_field_contract` exercise the count-independence behaviourally.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01#3

- **criterion:** That same test passes after this unit.
- **oracle:** O1 — `test_a_three_field_marker_parses (tests.test_marker_dual_shape.DualShapeMarker) ... ok`; `Ran 11 tests`, `OK`, exit 0.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01#4

- **criterion:** `parse_marker(body)` still returns a `(category, confidence)` 2-tuple for a two-field marker and `None` for a body carrying no marker — byte-identical behaviour, asserted against the existing `tests/test_triage*.py` cases, which are not edited by this unit.
- **oracle:** O3 (all 6 old-parseable literals in the repo return the identical tuple under the current reader; 0 divergences over 15 distinct literals) + O4 (`Ran 90 tests`, `OK`, exit 0, `tests/test_triage*.py` unmodified in O5's diff).
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01#5

- **criterion:** `parse_marker_fields(body)` returns a `dict` of every field present, or `None` for a body carrying no marker. A two-field marker yields exactly `{"category": …, "confidence": …}` — no `severity` key invented with a default.
- **oracle:** O1 (`DualShapeMarker::test_two_field_marker_still_parses`, `test_no_marker_returns_none`) plus a direct in-session call: `parse_marker_fields(render_marker("bug","high"))` returned exactly `{'category': 'bug', 'confidence': 'high'}`; the three-field form returned `{'category': 'bug', 'confidence': 'high', 'severity': 'critical'}`.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01#6

- **criterion:** `render_marker(category, confidence)` emits the two-field form byte-identically to today, asserted by string equality against a literal, not field-wise.
- **oracle:** O1 (`DualShapeMarker::test_render_marker_still_two_field`) plus in-session string equality: `render_marker("bug","high") == "<!-- specfuse:triage category=bug confidence=high -->"` is `True`. O5 shows `_MARKER_TEMPLATE` and `render_marker` untouched by the gate's diff.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01#7

- **criterion:** No caller of `parse_marker` is edited, and no write path changes.
- **oracle:** O5 — `git --no-pager diff --stat main -- specfuse/` reports exactly one file, `specfuse/loop/triage.py`, 23 insertions / 6 deletions, and the hunks are confined to `_MARKER_RE`, the new `parse_marker_fields`, and `parse_marker`'s body. `apply_triage` and every other write path are absent from the diff. O4's 90 tests cover the live callers in `agent/state.py`, `agent/triage_invoke.py`, `bug_lane_run.py` and `bug_lane_state.py` and pass unmodified.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01H#1

- **criterion:** `tests/test_marker_dual_shape.py::FailsClosed::test_a_marker_missing_a_required_field_reads_as_absent` fails on HEAD before this unit runs, raising `KeyError` rather than returning `None`.
- **oracle:** O2 at T01's tree — `git show 81e10f9:specfuse/loop/triage.py`, `parse_marker("<!-- specfuse:triage category=bug -->")` → `RAISED KeyError: 'confidence'`; the `confidence=` empty form raised identically. The pre-T01 tree returned `None` for both.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01H#2

- **criterion:** `parse_marker(body)` returns `None` — never raises — when the marker is present but carries no `category`, no `confidence`, or an empty value for either. Written as a lookup that cannot raise, not a `try/except KeyError` around the existing indexing.
- **oracle:** O2 at T01H's tree (`git show 79be9a3:specfuse/loop/triage.py`) — all three malformed shapes returned `None`, none raised. O5's diff shows the implementation is `fields.get(...)` plus a falsiness guard, with no `try`/`except` anywhere in `parse_marker`.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01H#3

- **criterion:** That same test passes after this unit, and it covers all four shapes: missing `confidence`, missing `category`, `confidence=` empty, `category=` empty.
- **oracle:** O1 — `test_a_marker_missing_a_required_field_reads_as_absent (tests.test_marker_dual_shape.FailsClosed) ... ok`. The four shapes are present as literals in that case's body and all four appear in O3's repo sweep, each reading `new=None`.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01H#4

- **criterion:** `parse_marker_fields` is **unchanged** and still reports exactly the fields present — it is the raw reader, and a caller wanting to know that a field is missing needs it to keep saying so.
- **oracle:** O5 — the diff between T01 and HEAD touches only `parse_marker`'s body; `parse_marker_fields` is byte-identical across `git show 81e10f9:` and `git show 79be9a3:`. In-session call on `<!-- specfuse:triage category=bug -->` still yields `{'category': 'bug'}`, i.e. it still reports the absence.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01H#5

- **criterion:** Every existing assertion in `tests/test_marker_dual_shape.py` and `tests/test_triage*.py` passes unmodified. A test edited to accommodate this change is a signal the change is wrong.
- **oracle:** O1 (`Ran 11 tests`, `OK`) + O4 (`Ran 90 tests`, `OK`, exit 0). O5's diff over `tests/` between T01 and T01H is additive only: one new `FailsClosed` case class, no edited assertion.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T01H#6

- **criterion:** The literal at `tests/test_agent_invoke_usage.py:83` is left alone — it is a fixture for a different subject, and this unit fixes the reader rather than the corpus.
- **oracle:** O3 — the sweep still finds `<!-- specfuse:triage category=bug -->` in `tests/test_agent_invoke_usage.py`, unchanged, and it reads `old=None new=None`. `tests/test_agent_invoke_usage.py` does not appear in O5's diff, and its tests pass inside O4's 90.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_marker_dual_shape.py::MarkerCorpus::test_every_shipped_marker_shape_parses` fails on HEAD before this unit runs.
- **oracle:** O2-style historical read — `git show 79be9a3:tests/test_marker_dual_shape.py` carries no `MarkerCorpus` class and no corpus helpers, so the nodeid did not resolve on the pre-T02 tree. It resolves and passes now under O1.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T02#2

- **criterion:** The corpus is assembled from the repository's own marker literals rather than hand-typed: `render_marker`'s output across the full cross-product of `CATEGORIES` × `CONFIDENCES`, plus the literal marker strings already present in `tests/` and in `CHANGELOG.md`'s published-contract entries. Each parses to the category and confidence it names.
- **oracle:** O1 (`MarkerCorpus::test_every_shipped_marker_shape_parses ... ok`) — its `_shipped_markers_from_tests` walks `ast.Constant` values across `tests/*.py` and `_shipped_markers_from_changelog` reads the template out of `CHANGELOG.md`, so nothing is hand-typed. Independently corroborated by O3, which sweeps every tracked file in the repository (not only `tests/`) and finds 15 distinct literals, all accounted for.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T02#3

- **criterion:** A marker embedded in a realistic issue body — surrounded by prose, preceded and followed by blank lines, and with other HTML comments nearby — parses, and a second unrelated HTML comment is never mistaken for a marker.
- **oracle:** O1 — `MarkerCorpus::test_marker_in_a_realistic_issue_body_parses ... ok` and `MarkerCorpus::test_an_unrelated_html_comment_alone_is_never_a_marker ... ok`.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T02#4

- **criterion:** Round trip: for every `(category, confidence)` pair, `parse_marker(render_marker(c, f)) == (c, f)`.
- **oracle:** O1 (`RoundTrip::test_render_then_parse_is_identity_for_every_pair ... ok`) plus an in-session cross-product run over `CATEGORIES` × `CONFIDENCES` = 5 × 2 = 10 markers: 0 mismatches under the current reader **and** 0 under the old anchored regex, i.e. the identity is unchanged, not merely present.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T02#5

- **criterion:** A malformed marker (missing a field, an empty value, an unterminated comment) returns `None` rather than a partial tuple or a raised exception — a marker the reader cannot fully understand must read as absent, which is the fail-closed direction.
- **oracle:** O1 — `FailsClosed::test_a_marker_missing_a_required_field_reads_as_absent ... ok` and `FailsClosed::test_an_unterminated_comment_reads_as_absent ... ok`. O3 confirms on real literals: all five malformed shapes tracked in the repository read `new=None`, none raised during the sweep.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`

### T02#6

- **criterion:** The three-field forward-compatible shape parses through `parse_marker_fields` and still yields a correct 2-tuple through `parse_marker`'s two-field contract. (The WU body spells this `parse_matcher`; that is a typo for `parse_marker`, the only reader with a two-field contract.)
- **oracle:** O1 (`MarkerCorpus::test_three_field_shape_round_trips_through_the_two_field_contract ... ok`) plus the in-session call: `parse_marker_fields` on the three-field marker returned `{'category': 'bug', 'confidence': 'high', 'severity': 'critical'}` and `parse_marker` returned `('bug', 'high')`.
- **kind:** `narrow`
- **state:** `pass`
- **proved_at_sha:** `026cf994f70d98f2675f3b2bc31c049d8956ad01`
- **attempt:** `1`
