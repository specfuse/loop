### T01#1

- **criterion:** `tests/test_language_aware_narrow_selection.py` exists and fails on HEAD
- **oracle:** `python3 -m unittest tests.test_language_aware_narrow_selection -v`  # module present, 5 tests, OK, exit 0
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#2

- **criterion:** That module asserts the Maven shape end to end: a `WorkUnit` whose
- **oracle:** `python3 -m unittest tests.test_language_aware_narrow_selection.LanguageAwareNarrowSelectionTests.test_maven_shape_resolves_through_narrow_command -v`  # OK, exit 0; resolved './mvnw test -Dtest=FooTest,BarTest'
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#3

- **criterion:** A gate declaring **no** `narrow_selection` resolves byte-identically to
- **oracle:** `python3 -m unittest tests.test_language_aware_narrow_selection.LanguageAwareNarrowSelectionTests.test_no_narrow_selection_key_is_byte_identical_to_today -v` (OK, exit 0, resolved 'python3 -m unittest tests.test_declared') AND `python3 -m unittest tests.test_tiered_verification_e2e -v` (5 tests, OK, exit 0, unsandboxed) with no edit to that file
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#4

- **criterion:** `grep -n "narrow_selection" specfuse/loop/loop.py` shows the key read via
- **oracle:** `grep -n "narrow_selection" specfuse/loop/loop.py`  # 11 hits, exit 0; line 4608 is `cfg = (gate or {}).get("narrow_selection") or {}` and DEFAULT_NARROW_SELECTION_CONFIG (loop.py:4575) carries all four documented defaults. `grep -c "narrow_selection" .specfuse/verification.yml`  # printed 0, exit 1 (no match — the asserted state)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#1

- **criterion:** A new test in `tests/test_language_aware_narrow_selection.py` asserting the
- **oracle:** `python3 -m unittest tests.test_language_aware_narrow_selection.LanguageAwareNarrowSelectionTests.test_gradle_shape_uses_item_template_for_repeated_flag -v`  # OK, exit 0; resolved './gradlew test --tests FooTest --tests BarTest'
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#2

- **criterion:** `format: path` renders each selected `produces:` entry verbatim, asserted by
- **oracle:** `python3 -m unittest tests.test_language_aware_narrow_selection.LanguageAwareNarrowSelectionTests.test_path_format_renders_entries_verbatim -v`  # OK, exit 0; resolved 'jest __tests__/foo.test.js __tests__/bar.test.js'
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#3

- **criterion:** An unknown `format` value raises a `CONFIGURATION ERROR` whose message names
- **oracle:** `python3 -m unittest tests.test_language_aware_narrow_selection.LanguageAwareNarrowSelectionTests.test_unknown_format_is_a_configuration_error_naming_the_gate -v`  # OK, exit 0; loop.verify() returned ok=False with "CONFIGURATION ERROR: gate 'tests' declares `narrow_selection.format: 'typo_format'` ... in .specfuse/verification.yml" — no fallback to the gate's full command
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#4

- **criterion:** `python3 -m unittest tests.test_language_aware_narrow_selection -v` exits 0,
- **oracle:** `python3 -m unittest tests.test_language_aware_narrow_selection -v` (5 tests, OK, exit 0) AND `python3 -m unittest tests.test_tiered_verification_e2e -v` (5 tests, OK, exit 0, unsandboxed)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#1

- **criterion:** `.specfuse/verification.yml.example` documents all four keys with their
- **oracle:** `grep -c "narrow_selection" .specfuse/verification.yml.example`  # printed 3, exit 0 (>= 1)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#2

- **criterion:** The dispatched-session prompt text no longer asserts `tests/` as the only
- **oracle:** `grep -n "tests/ path" specfuse/loop/loop.py`  # no output, exit 1; the replacement at loop.py:3406-3407 reads "names none of that gate's configured test roots (`narrow_selection.test_roots`, default `tests/`)"
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#3

- **criterion:** `.specfuse/verification.yml.example` and
- **oracle:** `diff .specfuse/verification.yml.example specfuse/loop/data/verification.yml.example`  # no output, exit 0
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#4

- **criterion:** Red-test exempt: documentation and prompt prose introduce no behaviour, and
- **oracle:** `python3 -m unittest tests.test_scaffold_data_in_sync -v`  # 4 tests, OK, exit 0
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
