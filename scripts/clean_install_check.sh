#!/usr/bin/env bash
#
# Clean-install gate (PR-08, permanent).
#
# Builds a throwaway virtualenv, installs the project with NO optional extras
# (`pip install .`, not `-e ".[dev]"`), and imports the entire public pdsfile
# module surface via scripts/check_runtime_imports.py. This is the only check
# that catches a runtime-dependency leak: every other run has the dev extra
# (pytest etc.) present, so it cannot detect a runtime module still importing a
# dev-only package. A non-editable install from a temp build dir also verifies
# the wheel actually ships every subpackage.
#
# Exit 0 = clean import with runtime deps only; non-zero = leak or build failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TMP_VENV="$(mktemp -d)"
cleanup() { rm -rf "$TMP_VENV"; }
trap cleanup EXIT

PYTHON="${PYTHON:-python3}"

echo "Clean-install gate: creating throwaway venv at $TMP_VENV"
"$PYTHON" -m venv "$TMP_VENV"
# shellcheck source=/dev/null
source "$TMP_VENV/bin/activate"

python -m pip install --quiet --upgrade pip
# Install the project with runtime deps only (no extras). Build isolation on so
# this does not see the caller's environment.
echo "Clean-install gate: pip install . (runtime deps only)"
python -m pip install --quiet "$PROJECT_ROOT"

# Import from a directory OUTSIDE the source tree so `import pdsfile` resolves to
# the installed package, never the src/ checkout.
echo "Clean-install gate: importing full module surface"
( cd "$TMP_VENV" && python "$PROJECT_ROOT/scripts/check_runtime_imports.py" )

echo "Clean-install gate: PASSED"
