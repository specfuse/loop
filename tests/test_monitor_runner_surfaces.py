# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the local and GitHub Actions runner surfaces
(FEAT-2026-0040/T11) — the `runner` dial's routing/reporting behaviour in
`specfuse.monitor.cli`, and the shipped GitHub Actions template."""

from __future__ import annotations

import io
import re
import tempfile
import unittest
from pathlib import Path

import specfuse.monitor.cli as cli
from specfuse.loop import _miniyaml
from specfuse.loop.lint_monitoring import RUNNER_VALUES

REPO_ROOT = Path(__file__).parent.parent
WORKFLOW_PATH = REPO_ROOT / "specfuse" / "loop" / "data" / "workflows" / "specfuse-monitor.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


_ENVIRONMENT = {
    "telemetry": {"provider": "acme-telemetry", "credentials": {"api_key": "ACME_API_KEY"}},
    "broker": {"provider": "acme-broker", "credentials": {"connection_string": "ACME_CONN"}},
}


def _stub_resolver(module, check_type, binding):
    raise AssertionError("no adapter should be dispatched — all fixtures use targetless heartbeat")


def _component(name, runner):
    return {
        "name": name,
        "type": "http-service",
        "runner": runner,
        "diagnose": "manual",
        "autofix": "off",
        "checks": [],
    }


def _config(components):
    return {"environments": {"production": _ENVIRONMENT}, "components": components}


class _CliTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.watermark_dir = Path(self._tmpdir.name)


# ---------------------------------------------------------------------------
# criteria 1, 2, 3 — the dial routes; skipped components are reported
# ---------------------------------------------------------------------------


class TestRunnerDial(_CliTestCase):
    def test_components_for_another_runner_are_skipped_and_reported(self):
        config = _config([
            _component("local-worker", "local"),
            _component("actions-worker", "gh-actions"),
        ])
        out = io.StringIO()
        code = cli.run_cycle(
            config,
            dry_run=True,
            transport_resolver=_stub_resolver,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        output = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("local-worker", output)
        self.assertIn("actions-worker", output)
        self.assertIn("skipped", output)
        skip_line = next(line for line in output.splitlines() if "actions-worker" in line and "skipped" in line)
        self.assertIn("gh-actions", skip_line)
        # the handled component's line must not carry a "skipped" marker
        handled_lines = [line for line in output.splitlines() if "local-worker" in line]
        self.assertTrue(handled_lines)
        self.assertTrue(all("skipped" not in line for line in handled_lines))

    def test_gh_actions_run_selects_only_the_gh_actions_component(self):
        config = _config([
            _component("local-worker", "local"),
            _component("actions-worker", "gh-actions"),
        ])
        out = io.StringIO()
        cli.run_cycle(
            config,
            runner="gh-actions",
            dry_run=True,
            transport_resolver=_stub_resolver,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        output = out.getvalue()
        skip_line = next(line for line in output.splitlines() if "local-worker" in line and "skipped" in line)
        self.assertIn("local", skip_line)
        handled_lines = [line for line in output.splitlines() if "actions-worker" in line]
        self.assertTrue(all("skipped" not in line for line in handled_lines))

    def test_in_cluster_component_is_reported_unhandled_by_design_not_dropped_or_errored(self):
        config = _config([_component("edge-worker", "in-cluster")])
        out = io.StringIO()
        code = cli.run_cycle(
            config,
            dry_run=True,
            transport_resolver=_stub_resolver,
            watermark_dir=self.watermark_dir,
            out=out,
        )
        output = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("edge-worker", output)
        self.assertIn("in-cluster", output)
        self.assertIn("FEAT-2026-0043", output)
        self.assertIn("unhandled by design", output)

    def test_unknown_runner_value_is_a_clear_error_not_a_skip(self):
        config = _config([_component("mystery-worker", "cloud-magic")])
        with self.assertRaises(cli.MonitorCliError) as ctx:
            cli.run_cycle(
                config,
                dry_run=True,
                transport_resolver=_stub_resolver,
                watermark_dir=self.watermark_dir,
                out=io.StringIO(),
            )
        message = str(ctx.exception)
        self.assertIn("mystery-worker", message)
        self.assertIn("cloud-magic", message)
        for value in sorted(RUNNER_VALUES):
            self.assertIn(value, message)

    def test_cli_runner_flag_defaults_to_local(self):
        parser = cli.build_parser()
        args = parser.parse_args(["run"])
        self.assertEqual(args.runner, "local")

    def test_cli_runner_flag_rejects_unsupported_choice(self):
        parser = cli.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["run", "--runner", "cloud-magic"])


# ---------------------------------------------------------------------------
# criteria 5-10 — the shipped GitHub Actions template
# ---------------------------------------------------------------------------


class TestGitHubActionsTemplate(unittest.TestCase):
    def setUp(self):
        self.raw = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.data = _miniyaml.parse(self.raw)

    def test_file_exists_and_parses_as_a_mapping_with_on_and_jobs(self):
        self.assertIsInstance(self.data, dict)
        self.assertIn("on", self.data)
        self.assertIn("jobs", self.data)

    def test_declares_schedule_cron_and_manual_dispatch(self):
        on = self.data["on"]
        schedule = on.get("schedule")
        self.assertIsInstance(schedule, list)
        self.assertTrue(schedule)
        self.assertTrue(all("cron" in entry and entry["cron"] for entry in schedule))
        self.assertIn("workflow_dispatch", on)

    def test_a_step_invokes_the_real_entry_point(self):
        """The template runs `specfuse monitor run`, and that subcommand has a
        real backing module.

        The umbrella dispatches `specfuse monitor` into the module this
        package's `specfuse-monitor` console script names, so the entry-point
        declaration is still what makes the subcommand resolvable — renaming
        the module or its `main()` without telling the umbrella turns the
        subcommand into a run-time ImportError.
        """
        pyproject = PYPROJECT_PATH.read_text(encoding="utf-8")
        match = re.search(r'^specfuse-monitor\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
        self.assertIsNotNone(match, "pyproject.toml must declare the specfuse-monitor entry point")

        steps = self.data["jobs"]["monitor"]["steps"]
        run_commands = [step["run"] for step in steps if "run" in step]
        self.assertTrue(
            any(cmd.startswith("specfuse monitor run") for cmd in run_commands),
            f"no step invokes 'specfuse monitor run'; got {run_commands}",
        )
        self.assertFalse(
            any(cmd.startswith("specfuse-monitor") for cmd in run_commands),
            f"template still uses the deprecated flat command; got {run_commands}",
        )

    def test_permissions_are_exactly_least_privilege(self):
        permissions = self.data.get("permissions")
        self.assertIsInstance(permissions, dict)
        self.assertEqual(set(permissions.keys()), {"issues", "contents"})
        self.assertEqual(permissions["issues"], "write")
        self.assertEqual(permissions["contents"], "read")

    def test_no_literal_secret_every_credential_value_is_a_reference(self):
        env_blocks = []
        for step in self.data["jobs"]["monitor"]["steps"]:
            env = step.get("env")
            if env:
                env_blocks.append(env)
        self.assertTrue(env_blocks, "expected at least one step with an env: block")
        for env in env_blocks:
            for key, value in env.items():
                self.assertTrue(
                    re.match(r"^\$\{\{\s*(secrets|vars)\.[A-Za-z0-9_]+\s*\}\}$", value),
                    f"env {key!r} is not a secrets/vars reference: {value!r}",
                )
        # negative observation: no inline literal-secret shape (long opaque
        # token) sits on a non-comment line outside a ${{ }} reference.
        for lineno, line in enumerate(self.raw.splitlines(), start=1):
            code = line.split("#", 1)[0]
            for token in re.findall(r"[A-Za-z0-9/+_-]{24,}", code):
                self.assertIn(
                    "${{", code,
                    f"line {lineno}: long literal token {token!r} outside a ${{{{ }}}} reference",
                )

    def test_not_installed_in_this_repository_own_workflows(self):
        own_workflows = sorted(p.name for p in (REPO_ROOT / ".github" / "workflows").glob("*.yml"))
        self.assertEqual(own_workflows, ["ci.yml", "leak-scan-content.yml", "release.yml"])
        self.assertFalse((REPO_ROOT / ".github" / "workflows" / "specfuse-monitor.yml").exists())


# ---------------------------------------------------------------------------
# criterion 11 — docs
# ---------------------------------------------------------------------------


class TestRunnerSurfacesDocs(unittest.TestCase):
    def test_doc_exists_and_covers_both_surfaces_and_the_deferred_dial(self):
        doc_path = REPO_ROOT / "docs" / "concepts" / "monitoring-runners.md"
        self.assertTrue(doc_path.is_file())
        text = doc_path.read_text(encoding="utf-8")
        self.assertIn("local", text)
        self.assertIn("gh-actions", text)
        self.assertIn("in-cluster", text)
        self.assertIn("FEAT-2026-0043", text)
        self.assertIn("--dry-run", text)


if __name__ == "__main__":
    unittest.main()
