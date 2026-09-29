# PR-06 validation record — move maintenance tools and utility into the package

Phase 2. `git mv holdings_maintenance src/pdsfile/holdings_maintenance`;
`git mv utility/show_opus_products.py src/pdsfile/tools/show_opus_products.py`
(empty `utility/` removed); hyphenated modules renamed to importable names
(`re-validate.py` → `re_validate.py`, `shelf-consistency-check.py` →
`shelf_consistency_check.py`, rename-only). Packaging discovery collapsed to
`src`-only.

## Content edits required by the move (itemized)
- 11 `[project.scripts]` targets reprefixed `holdings_maintenance.…` →
  `pdsfile.holdings_maintenance.…`.
- `pdsinfoshelf.py`, `re_validate.py`: dropped the `REPO_ROOT` +
  `sys.path.insert` hack and the now-dead `from pathlib import Path` (its only
  use was the hack); intra-package imports → `from pdsfile.holdings_maintenance.
  pds3 import …`. `sys` kept (still used: `sys.exit`/`sys.argv`).
- `pds4infoshelf.py`: repointed `from holdings_maintenance.pds4 import
  pds4checksums` → `from pdsfile.holdings_maintenance.pds4 import pds4checksums`.
  **Third cross-import site not itemized in the plan** — it had no sys.path hack
  (resolved only because `holdings_maintenance` was a top-level package), so the
  move requires it.
- `show_opus_products.py`: two `from pdsfile.pds{3,4}file.tests.helper import
  PDS{3,4}_HOLDINGS_DIR` imports replaced with direct `os.environ[...]` reads
  (same semantics the helper used); `.preload()` call sites unchanged.

## Deviation from the literal spec (flagged to owner)
Added three empty `__init__.py`: `holdings_maintenance/pds3/`,
`holdings_maintenance/pds4/`, `tools/`. These dirs never had one, and
setuptools' `find_packages` only discovers dirs that contain `__init__.py`, so
without them a built wheel silently omits `pdsfile.holdings_maintenance.pds3`,
`.pds4`, and `pdsfile.tools` — breaking every console-script entry point (all
target `pdsfile.holdings_maintenance.pds{3,4}.*`) and the `show_opus_products`
tool in a real (non-editable) install. The editable install masks this, so the
plan's editable-only PR-06 gate would not have caught it. **Verified by building
a wheel** (`pip wheel . --no-deps`): with the files, the archive contains
`pdsfile/holdings_maintenance/pds3/pdsarchives.py`, `…/pds4/pds4infoshelf.py`,
`pdsfile/tools/show_opus_products.py`, etc. Convention match: the existing
`holdings_maintenance/__init__.py` is already an empty file.

## Ratchet / target bookkeeping
- ruff per-file-ignores keys reprefixed to `src/pdsfile/…` (incl. the two
  renamed modules); no key still starts with `holdings_maintenance/` or
  `utility/`.
- `holdings_maintenance` and `utility` dropped from the ruff targets in
  `gen_ruff_ratchet.py` (`TARGETS = ['src/pdsfile', 'scripts', 'conftest.py']`)
  and `run-all-checks.sh` (`RUFF_TARGETS="src/pdsfile scripts conftest.py"`);
  both now covered by `src/pdsfile`.

## Gates
- `pip install -e .` succeeds; all 11 console scripts resolve and `--help`;
  `python -m pdsfile.tools.show_opus_products --help` works.
- `find_packages('src', include=['pdsfile*'])` includes the three
  previously-missing subpackages.
- `scripts/run-all-checks.sh` green: ruff (ratchet) clean, pyroma **10/10**,
  API-freeze manifest unchanged (tooling is not part of the public API surface).
- Full `--mode ns` suite (`tests/api/` + both `src/pdsfile/pds{3,4}file/tests/`
  + all `rules/*.py`) against the limited testing holdings: **679 passed, 34
  skipped, 0 failed** — unchanged from the pre-move baseline.

## Note (pre-existing, not a finding)
`re_validate.py` runs its main flow at import (no `if __name__ == '__main__'`
guard), printing "Missing volume path" when imported bare. It is a standalone
script, not a console entry point, and nothing imports it — behavior unchanged
by this PR.

## Adversarial review
See `critiques/pr-06/round-1.md`. Zero findings; converged in one round.
