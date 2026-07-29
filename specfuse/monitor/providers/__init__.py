# Copyright 2026 Specfuse Contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Provider-specific adapters for the failure-artifact harvester.

Every module under this package may import the neutral core
(``specfuse.monitor.artifact``, ``.adapters``, ``.fingerprint``,
``.redaction``). Nothing outside this package may import from it — the
core stays provider-agnostic (FEAT-2026-0040/T01 criterion 3).
"""
