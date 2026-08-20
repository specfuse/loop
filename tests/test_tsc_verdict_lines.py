#!/usr/bin/env python3
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`select_gate_report_lines` must recognise tsc/vue-tsc verdicts (#2390).

`tsc --noEmit` (and `vue-tsc --noEmit`) emit no pass/fail summary in either
direction under a plain non-TTY invocation: a clean run is silent (exit 0,
just the npm banner) and a failing run prints one `file(line,col): error
TS####: message` line per diagnostic with no trailing count. Without a
pattern for that line shape, `select_gate_report_lines` pins nothing on a
typecheck failure, falls back to a positional tail, and appends its
`NO VERDICT FOUND` banner — degrading a 15-diagnostic compile break to
`failure_class: other` with no compiler output reaching the retry.

Same shape as #723 (ruff) and #1413 (Maven surefire), for the TypeScript
compiler.
"""

from __future__ import annotations

import unittest

from tests._loop_loader import load_loop

load_loop()

from specfuse.loop.loop import (  # noqa: E402  (after sys.path setup above)
    _NO_VERDICT_NOTE,
    select_gate_report_lines,
)


class TestTscVerdictsAreRecognised(unittest.TestCase):
    def test_tsc_diagnostic_line_is_pinned_as_a_verdict(self):
        out = (
            "> acme-admin-app@0.0.0 typecheck\n"
            "> vue-tsc --noEmit\n"
            "\n"
            "packages/acme-core/src/data/api/user-api-client.ts"
            "(275,42): error TS6133: 'file' is declared but its value is "
            "never read.\n"
        )

        lines = select_gate_report_lines(out, window=15)

        self.assertTrue(
            any("error TS6133" in ln for ln in lines),
            f"TS diagnostic missing from selection: {lines}")
        self.assertNotIn(_NO_VERDICT_NOTE, lines)

    def test_the_verdict_survives_a_flood_that_pushes_it_out_of_the_window(self):
        # Mirrors the ruff/surefire regression guard: a diagnostic list long
        # enough to push the first error out of a 15-line tail must still be
        # pinned rather than silently dropped.
        head = (
            "packages/core/src/data/api/notification-job-api-client.ts"
            "(12,32): error TS6138: Property 'axios' is declared but its "
            "value is never read."
        )
        noise = "\n".join(f"src/mod_{i}.ts:{i}:1: some other note" for i in range(400))
        out = f"{head}\n{noise}\n"

        lines = select_gate_report_lines(out, window=15)

        self.assertEqual(lines[0], head)
        self.assertNotIn(_NO_VERDICT_NOTE, lines)

    def test_a_genuinely_verdictless_output_still_gets_the_banner(self):
        lines = select_gate_report_lines("some unrelated chatter\nand more\n", 15)

        self.assertIn(_NO_VERDICT_NOTE, lines)


if __name__ == "__main__":
    unittest.main()
