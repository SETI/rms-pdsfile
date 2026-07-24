#!/usr/bin/env python3
"""Generate the `[tool.ruff.lint.per-file-ignores]` ratchet from the current tree.

Runs `ruff check` over the lint targets, groups the reported violations by
(file, rule code), and prints one TOML `per-file-ignores` entry per file listing
exactly its current codes. Committing that block makes `ruff check` pass now; the
ratchet may only SHRINK in later PRs (never grow, never be replaced by inline
`noqa`). Re-run this to regenerate after a shrink and confirm the diff only
removes codes. This script only prints the block; it does not edit pyproject.toml.
"""

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Lint targets at this phase: pdsfile moved to src/ in PR-05; holdings_maintenance
# and utility move under the package in PR-06. Keep in sync with the ruff targets
# in scripts/run-all-checks.sh; re-point both in each Phase-2 move PR.
TARGETS = ['src/pdsfile', 'holdings_maintenance', 'utility', 'scripts', 'conftest.py']

_REPO_ROOT = Path(__file__).resolve().parents[1]


def main():
    proc = subprocess.run(
        ['ruff', 'check', '--output-format', 'json', '--no-fix', *TARGETS],
        cwd=_REPO_ROOT, capture_output=True, text=True)
    # ruff exits 1 when violations exist (expected); only a hard failure has no
    # JSON on stdout.
    if not proc.stdout.strip():
        sys.stderr.write(proc.stderr)
        raise SystemExit(f'ruff produced no JSON (exit {proc.returncode})')
    violations = json.loads(proc.stdout)

    by_file = defaultdict(set)
    for v in violations:
        code = v.get('code')
        if not code:  # syntax errors etc. have no code; cannot be ignored per-file
            continue
        rel = Path(v['filename']).resolve().relative_to(_REPO_ROOT).as_posix()
        by_file[rel].add(code)

    lines = []
    for path in sorted(by_file):
        codes = ', '.join(f'"{c}"' for c in sorted(by_file[path]))
        lines.append(f'"{path}" = [{codes}]')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
