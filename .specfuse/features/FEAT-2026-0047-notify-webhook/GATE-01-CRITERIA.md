### T01#1

- **criterion:** `tests/test_notify.py::TestPostNotification::test_no_webhook_configured_is_noop`
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) — proves the named test exists and is green; the `fails on HEAD` half is historical and is recorded as D4 in RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#2

- **criterion:** `specfuse/loop/notify.py` defines
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) (TestPostNotification::test_no_webhook_configured_is_noop) + python3 -c inspect.signature over the shipped symbol (RETROSPECTIVE.md § 'Signature and identity checks', exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#3

- **criterion:** `resolve_webhook_url(policy_path=None) -> str | None` reads the env-var
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) (TestResolveWebhookUrl: missing policy file / empty key / absent env var / set env var — all four cases) + this close's security re-test (RETROSPECTIVE.md § 'Security claim 2 re-tested', exit 0) check 2g
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#4

- **criterion:** **The resolved URL never leaves the process except as the POST target.** A
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) (test_url_never_leaves_process_on_poster_exception) + this close's security re-test (RETROSPECTIVE.md § 'Security claim 2 re-tested', exit 0) checks 2b/2c/2c'/2d/2e — a unique sentinel token in the resolved URL was absent from the return value, the captured root-logger output, and the built payload, while the same URL DID reach the injected poster (so the absence is non-vacuous)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#5

- **criterion:** Three pure adapter functions exist, one per provider, each mapping a neutral
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) (TestPayloadAdapters: discord/slack/teams envelope shapes + test_unknown_provider_yields_no_payload_and_no_post)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#6

- **criterion:** `redact_text` from `specfuse.monitor.redaction` is applied to every
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) (test_redaction_applied_before_entering_payload)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#7

- **criterion:** **Never fatal:** a poster that raises, times out, or returns a non-2xx
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) (test_poster_raising_is_never_fatal, test_poster_timeout_is_never_fatal, test_poster_non_2xx_status_is_never_fatal) + this close's security re-test (RETROSPECTIVE.md § 'Security claim 2 re-tested', exit 0) checks 2a/2f
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#8

- **criterion:** Quiet hours suppress the post and nothing else: with `quiet_hours` covering
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) (test_quiet_hours_suppress_post_and_nothing_else, test_outside_quiet_hours_posts_normally)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#9

- **criterion:** `escalation.webhook` is **renamed** to `escalation.webhook_env` in
- **oracle:** python3 -m unittest tests.test_agent_policy_schema -v (Ran 29 tests, OK, exit 0) (test_old_webhook_key_is_error) + this close's security re-test (RETROSPECTIVE.md § 'Security claim 1 re-tested', exit 0) check 1a — a purpose-built policy carrying `escalation.webhook` returned exactly ["ERROR: unknown 'escalation.webhook' key", "ERROR: missing 'escalation.webhook_env' key"] (negative observation: the rule fires on bad input)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#10

- **criterion:** `validate_agent_policy` emits an `ERROR: ` finding when `webhook_env`'s
- **oracle:** python3 -m unittest tests.test_agent_policy_schema -v (Ran 29 tests, OK, exit 0) (test_webhook_env_url_shaped_is_error, test_webhook_env_name_shaped_is_valid, test_webhook_env_empty_is_valid) + this close's security re-test (RETROSPECTIVE.md § 'Security claim 1 re-tested', exit 0) checks 1b/1c — a literal https:// URL is an ERROR: finding, while `SPECFUSE_NOTIFY_WEBHOOK` and `""` both yield zero findings
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#11

- **criterion:** `escalation.provider` is validated against the four permitted values; an
- **oracle:** python3 -m unittest tests.test_agent_policy_schema -v (Ran 29 tests, OK, exit 0) (test_provider_enum_rejects_bad_value, test_provider_absent_is_valid)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#12

- **criterion:** `.specfuse/agent-policy.yml.example` and this repo's live
- **oracle:** python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml (exit 0) + the same over .specfuse/agent-policy.yml.example (exit 0) — the `agent-policy-example-lint` gate (exit 0) + this close's security re-test (RETROSPECTIVE.md § 'Security claim 3 re-tested', exit 0) checks 3a/3b/3c/3d — the live policy's `escalation.webhook_env` is `""`, it carries no `webhook` key at all, and it validates with zero findings
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#13

- **criterion:** `python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml`
- **oracle:** python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml (exit 0) + the same over .specfuse/agent-policy.yml.example (exit 0) — the `agent-policy-example-lint` gate (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#14

- **criterion:** No test performs a real HTTP request — every poster is injected. A test
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0) (test_no_network_call_under_default_no_op_path)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#15

- **criterion:** `python3 -m unittest tests.test_notify -v` exits zero after this WU's edits.
- **oracle:** python3 -m unittest tests.test_notify -v (Ran 18 tests, OK, exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T01#16

- **criterion:** `python3 -c "from specfuse.loop.notify import post_notification, resolve_webhook_url"`
- **oracle:** python3 -c "from specfuse.loop.notify import post_notification, resolve_webhook_url" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#1

- **criterion:** `tests/test_notify_escalation.py::TestNotifyNewEscalation::test_posts_one_liner_and_link`
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0) — proves the named test exists and is green; the `fails on HEAD` half is historical and is recorded as D4 in RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#2

- **criterion:** `specfuse/loop/notify_escalation.py` defines
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0) + python3 -c inspect.signature over the shipped symbol (RETROSPECTIVE.md § 'Signature and identity checks', exit 0) — shipped signature is (correlation_id: str, *, repo: str, issue_number: str, category: str, summary: str, policy_path: Optional[str] = None, poster: Optional[Callable] = None) -> bool
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#3

- **criterion:** The rendered message contains the issue link, the category, and a summary
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0) (test_posts_one_liner_and_link, test_message_has_no_extra_newline) + this close's composite oracle (RETROSPECTIVE.md § 'The composite oracle', exit 0) check 5a' — the single rendered message was '[needs-human:blocked-wu] <summary> — https://github.com/<owner>/<repo>/issues/42'
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#4

- **criterion:** `NEEDS_HUMAN_LABEL` and `CATEGORY_LABELS` are **imported** from
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0) (test_imports_are_same_objects_as_escalation_module) + python3 -c inspect.signature over the shipped symbol (RETROSPECTIVE.md § 'Signature and identity checks', exit 0) — `notify_escalation.NEEDS_HUMAN_LABEL is escalation.NEEDS_HUMAN_LABEL` and the same for CATEGORY_LABELS, asserted by object identity
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#5

- **criterion:** An unknown category is rejected before posting, matching
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0) (test_unknown_category_rejected_before_posting) + this close's security re-test (RETROSPECTIVE.md § 'Security claim 2 re-tested', exit 0) checks 2h/2h' — an unknown category raised ValueError with zero poster calls recorded
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#6

- **criterion:** `specfuse/loop/escalation.py` is **unmodified** by this WU — `git diff
- **oracle:** python3 -m unittest discover -s tests -p "test_escalation*.py" -v (Ran 16 tests, OK, exit 0) settles the second half — escalation.py's own tests pass untouched. The `git diff --stat` half was NOT run: a work-unit session runs no git (result-contract.md rule 1). See RETROSPECTIVE.md entry D3 for the re-run condition
- **kind:** `narrow`
- **state:** `unverified`
- **attempt:** `1`

### T02#7

- **criterion:** With no webhook configured, `notify_new_escalation` returns `False`, makes no
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0) (test_no_webhook_configured_returns_false_and_no_call) + this close's composite oracle (RETROSPECTIVE.md § 'The composite oracle', exit 0) check 5d
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#8

- **criterion:** A poster that raises causes `notify_new_escalation` to return `False` without
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0) (test_poster_raising_returns_false_not_raise) + this close's security re-test (RETROSPECTIVE.md § 'Security claim 2 re-tested', exit 0) check 2f
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#9

- **criterion:** Every payload passes through T01's redaction path — a test with a redactable
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0) (test_redaction_applied_to_summary)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#10

- **criterion:** `python3 -m unittest tests.test_notify_escalation -v` exits zero after this
- **oracle:** python3 -m unittest tests.test_notify_escalation -v (Ran 7 tests, OK, exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T02#11

- **criterion:** `python3 -c "from specfuse.loop.notify_escalation import notify_new_escalation"`
- **oracle:** python3 -c "from specfuse.loop.notify_escalation import notify_new_escalation" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#1

- **criterion:** `tests/test_notify_sla.py::TestSlaSweep::test_repings_once_then_parks`
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) — proves the named test exists and is green; the `fails on HEAD` half is historical and is recorded as D4 in RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#2

- **criterion:** `specfuse/loop/notify_sla.py` defines
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) + python3 -c inspect.signature over the shipped symbol (RETROSPECTIVE.md § 'Signature and identity checks', exit 0) — shipped signature is (runner: Callable, repo: str, *, now: datetime, policy_path: Optional[str] = None, poster: Optional[Callable] = None) -> list
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#3

- **criterion:** `PARKED_LABEL = "escalation-parked"` is a module-level constant, and
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_needs_human_label_imported_not_retyped) + python3 -c inspect.signature over the shipped symbol (RETROSPECTIVE.md § 'Signature and identity checks', exit 0) — notify_sla.PARKED_LABEL == 'escalation-parked' and `notify_sla.NEEDS_HUMAN_LABEL is escalation.NEEDS_HUMAN_LABEL`
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#4

- **criterion:** An issue younger than `escalation.sla_hours` is untouched: no post, no
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_issue_younger_than_sla_is_untouched, test_boundary_at_exactly_the_window_is_untouched, test_boundary_just_past_the_window_acts)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#5

- **criterion:** An issue past the window with **no** re-ping marker is re-pinged once: one
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_no_marker_repings_exactly_once) + this close's composite oracle (RETROSPECTIVE.md § 'The composite oracle', exit 0) checks 5b/5b'/5b''
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#6

- **criterion:** An issue past the window that **already** carries the marker is parked: the
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_already_marked_parks_with_no_second_post) + this close's composite oracle (RETROSPECTIVE.md § 'The composite oracle', exit 0) checks 5c/5c'
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#7

- **criterion:** The re-ping count is re-derived from issue comments on every call, with no
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_two_successive_sweeps_are_stable) + this close's composite oracle (RETROSPECTIVE.md § 'The composite oracle', exit 0) check 5c'''' — a third sweep still parked and still posted nothing
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#8

- **criterion:** A parked issue stays **open** — a test asserts no close command reaches the
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_parked_issue_never_closed) + this close's composite oracle (RETROSPECTIVE.md § 'The composite oracle', exit 0) check 5c''' — no argv reaching the fake runner contained 'close' on any path
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#9

- **criterion:** A malformed or unparseable marker is ignored rather than fatal, and does not
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_malformed_marker_ignored_not_fatal)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#10

- **criterion:** With no webhook configured, the sweep still parks correctly and makes no
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_no_webhook_configured_still_parks_no_poster_call) + this close's composite oracle (RETROSPECTIVE.md § 'The composite oracle', exit 0) check 5d'
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#11

- **criterion:** Every GitHub access goes through the injected `runner`; a test exercises
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0) (test_all_paths_use_injected_runner_no_network)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#12

- **criterion:** `python3 -m unittest tests.test_notify_sla -v` exits zero after this WU's
- **oracle:** python3 -m unittest tests.test_notify_sla -v (Ran 17 tests, OK, exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T03#13

- **criterion:** `python3 -c "from specfuse.loop.notify_sla import sla_sweep, PARKED_LABEL"`
- **oracle:** python3 -c "from specfuse.loop.notify_sla import sla_sweep, PARKED_LABEL" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#1

- **criterion:** `tests/test_heartbeat.py::TestSilenceCheck::test_stale_when_no_events_within_window`
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0) — proves the named test exists and is green; the `fails on HEAD` half is historical and is recorded as D4 in RETROSPECTIVE.md
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#2

- **criterion:** `specfuse/loop/heartbeat.py` defines
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0) (test_no_events_returns_none, test_newest_across_multiple_features) + python3 -c inspect.signature over the shipped symbol (RETROSPECTIVE.md § 'Signature and identity checks', exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#3

- **criterion:** `silence_check(*, now, repo_root=None, policy_path=None) -> dict` returns a
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0) + this close's verdict-shape probe (exit 0) — the returned dict carries stale, no_events, last_run_at, hours_since, silence_hours
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#4

- **criterion:** A repo with a recent event is **not** stale; one whose newest event predates
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0) (test_not_stale_with_recent_event, test_boundary_exactly_at_window_is_not_stale, test_stale_when_no_events_within_window)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#5

- **criterion:** **No events at all is reported distinctly**, not as stale-with-`hours_since:
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0) (test_no_events_at_all_is_a_distinct_verdict) + this close's verdict-shape probe — a repo with no events returns {stale: False, no_events: True, last_run_at: None, hours_since: None}, distinct from both stale and healthy
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#6

- **criterion:** A malformed or unparseable line in `events.jsonl` is skipped, not fatal, and
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0) (test_malformed_line_is_skipped, test_malformed_line_among_valid_does_not_look_silent)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#7

- **criterion:** `escalation.silence_hours` is added to the schema, defaults to `24`, and is
- **oracle:** python3 -m unittest tests.test_agent_policy_schema -v (Ran 29 tests, OK, exit 0) (silence_hours int > 0 validation) + python3 .specfuse/scripts/lint_agent_policy.py .specfuse/agent-policy.yml (exit 0) + the same over .specfuse/agent-policy.yml.example (exit 0) — the `agent-policy-example-lint` gate (exit 0) — the live policy carries silence_hours: 24 and validates clean
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#8

- **criterion:** `silence_check` performs **no** post itself — posting is the caller's choice.
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0) (test_no_poster_call_from_within_silence_check)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#9

- **criterion:** `plugins/specfuse/skills/attention/SKILL.md` gains a section instructing the
- **oracle:** grep -qF 'specfuse.loop.heartbeat.silence_check' over plugins/specfuse/skills/attention/SKILL.md (exit 0) and over .specfuse/skills/attention/SKILL.md (exit 0) — the skill section SHIPPED. The criterion's second half did NOT: `grep -rl 'heartbeat.silence_check' tests/` returns nothing (exit 1), so no test asserts the literal. See RETROSPECTIVE.md entry D2
- **kind:** `narrow`
- **state:** `fail`
- **attempt:** `1`

### T04#10

- **criterion:** `scripts/sync-scaffold.sh` has been run and
- **oracle:** python3 -m unittest tests.test_skills_vendored_in_sync -v (Ran 4 tests, OK, exit 0) + python3 -m unittest tests.test_attention_skill_structure tests.test_attention_nonwriting_guard -v (Ran 5 tests, OK, exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#11

- **criterion:** Reading `events.jsonl` is read-only: a test asserts no file under
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0) (test_does_not_write_any_events_file)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#12

- **criterion:** `python3 -m unittest tests.test_heartbeat -v` exits zero after this WU's
- **oracle:** python3 -m unittest tests.test_heartbeat -v (Ran 10 tests, OK, exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`

### T04#13

- **criterion:** `python3 -c "from specfuse.loop.heartbeat import last_run_at, silence_check"`
- **oracle:** python3 -c "from specfuse.loop.heartbeat import last_run_at, silence_check" (exit 0)
- **kind:** `narrow`
- **state:** `pass`
- **attempt:** `1`
