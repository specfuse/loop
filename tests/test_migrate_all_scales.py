#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
"""`ids migrate --all` cost tracks the lines that name an ID, not lines x IDs (#3559)."""

import time
import unittest
from unittest import mock

from specfuse.loop import ids

N_IDS = 200
RENAMES = [(f"FEAT-2026-{n:04d}", f"FEAT-ACME-2026-{n:04d}") for n in range(1, N_IDS + 1)]
FOLDERS = [f"FEAT-2026-{n:04d}-slug-{n}" for n in range(1, 101)]


def _plan():
    return ids.AllPlan(RENAMES, [], [], {}, {}, [], [])


def _source(n_lines):
    body = [f"value_{i} = compute({i})  # no feature mentioned here\n" for i in range(n_lines)]
    body[10] = "see FEAT-2026-0007 and features/FEAT-2026-0042-slug-42/PLAN.md\n"
    body[20] = "anchor [x](#feat-2026-0150)\n"
    return "".join(body)


class RewriteSkipsLinesWithoutAnId(unittest.TestCase):
    def test_per_id_work_runs_only_on_lines_naming_that_id(self):
        calls = []
        real = ids._rewrite_line

        def counting(line, old, *a, **kw):
            calls.append(old)
            return real(line, old, *a, **kw)

        with mock.patch.object(ids, "_rewrite_line", counting):
            out = ids._rewrite_file("src/mod.py", _source(1000), RENAMES, True, _plan(), FOLDERS)

        self.assertEqual(sorted(calls), ["FEAT-2026-0007", "FEAT-2026-0042", "FEAT-2026-0150"])
        self.assertIn("see FEAT-ACME-2026-0007 and features/FEAT-ACME-2026-0042-slug-42/", out)
        self.assertIn("[x](#feat-acme-2026-0150)", out)

    def test_large_file_with_many_ids_rewrites_quickly(self):
        text = _source(20_000)
        start = time.perf_counter()
        out = ids._rewrite_file("src/mod.py", text, RENAMES, True, _plan(), FOLDERS)
        elapsed = time.perf_counter() - start
        self.assertIn("FEAT-ACME-2026-0007", out)
        # Before #3559: ~20k lines x 200 IDs x (100 folder checks + 2 regexes), minutes.
        self.assertLess(elapsed, 5.0, f"rewrite took {elapsed:.1f}s")


if __name__ == "__main__":
    unittest.main()
