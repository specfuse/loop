#!/usr/bin/env bash
#
# Copyright 2026 Specfuse contributors
# Licensed under the Apache License, Version 2.0. See LICENSE.
#
# Operator-side Linux race probe — runs the integration test suite N×
# inside a fresh Ubuntu container to catch fs/cleanup races that don't
# fire on the operator's macOS (APFS) but do on Linux CI runners (ext4).
#
# Rationale: this repo's pre-push hook (`/.githooks/pre-push` ->
# `scripts/smoke-test.sh`) runs the same gates CI runs, but on the
# operator's local platform — script-parity, not environment-parity.
# Once-luck plus platform difference means a race that's deterministic
# on Linux can pass macOS hook 100% of the time. This script closes
# that gap before push, for the specific surface this repo's FEAT-2026-0013
# attacked.
#
# Usage:
#   ./scripts/check-linux-race.sh            # default 50 iterations
#   N=10 ./scripts/check-linux-race.sh       # custom iteration count
#
# Output:
#   - On success: a single line like `     50 OK`.
#   - On failure: counts per outcome line + non-zero exit.
#
# Requirements: docker installed and daemon running.

set -u

N="${N:-50}"
IMAGE="${IMAGE:-python:3.12}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker not found. Install Docker or run the audit on a Linux box directly." >&2
    exit 2
fi
if ! docker info >/dev/null 2>&1; then
    echo "docker daemon not running. Start Docker Desktop or systemctl start docker." >&2
    exit 2
fi

echo "==> Linux race probe (N=${N}, image=${IMAGE})"
echo "==> Mounting ${REPO_ROOT} read-write into container's /app"

# --network=none would be cleaner but `pip install -e .[dev]` may need network
# for first-run; subsequent runs reuse cache layers if pinned.
docker run --rm \
    -v "${REPO_ROOT}:/app" \
    -w /app \
    -e PYTHONDONTWRITEBYTECODE=1 \
    "${IMAGE}" \
    bash -c "
        set -e
        python -m pip install --quiet --disable-pip-version-check -e '.[dev]' >/tmp/pip.log 2>&1 || {
            echo 'pip install failed:'
            tail -20 /tmp/pip.log
            exit 1
        }
        echo '==> Running full test suite (discover tests) ${N}× in Linux container'
        echo '    (covers all 5 integration_workspace import sites + every other test)'
        pass=0
        fail=0
        oserrs=0
        for i in \$(seq 1 ${N}); do
            out=\$(python -m unittest discover tests -q 2>&1)
            rc=\$?
            if [ \$rc -eq 0 ]; then
                pass=\$((pass+1))
            else
                fail=\$((fail+1))
            fi
            # Independent race-shape check: count runs whose stderr mentioned
            # OSError + 'Directory not empty' — the actual failure mode
            # FEAT-2026-0013 attacks. Surfaces even if unittest exit was 0
            # (e.g. an ignore_cleanup_errors=True suppression).
            if printf '%s' \"\$out\" | grep -qE 'OSError.*Directory not empty'; then
                oserrs=\$((oserrs+1))
            fi
        done
        echo \"==> Results across ${N} runs:\"
        echo \"    PASS (exit 0):                    \$pass\"
        echo \"    FAIL (exit nonzero):              \$fail\"
        echo \"    Runs that emitted the race OSError: \$oserrs\"
        # Surface exit-0 nonzero only if any failed
        [ \$fail -eq 0 ] || exit 1
    "
rc=$?

if [ $rc -ne 0 ]; then
    echo ""
    echo "==> Probe FAILED (exit $rc). Do NOT push." >&2
    exit $rc
fi

echo ""
echo "==> Probe complete. Read the counts above:"
echo "    - PASS == ${N} AND OSError count == 0  → safe to push."
echo "    - FAIL > 0                              → race still fires; do NOT push."
echo "    - PASS == ${N} but OSError count > 0    → suppression hid the race"
echo "                                              (e.g. ignore_cleanup_errors=True)."
echo "                                              Symptom suppressed but root cause"
echo "                                              still active. Decide accordingly."
