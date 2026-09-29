# PR-07 validation record — move tests to top-level tests/ tree

Phase 2, last mechanical move. `git mv` the test suite out of the package:
`src/pdsfile/pds3file/tests` → `tests/pds3file`, `pds4file/tests` →
`tests/pds4file`, and the `test_results/` goldens →
`tests/golden/full/pds{3,4}/`. 73 test/golden files, all pure renames.

## Content edits required by the move (itemized)
- Root `conftest.py`: helper imports `pdsfile.pds{3,4}file.tests.helper` →
  `tests.pds{3,4}file.helper`. Root conftest is NOT moved (PR-08). `tests`
  resolves as a PEP 420 namespace package (no `tests/__init__.py`;
  `tests/pds{3,4}file/__init__.py` kept, so the two `helper` modules stay
  distinct) with the repo root on `sys.path` at collection time.
- `pytest_support.py` (pds3, pds4; still under `rules/`): `TEST_RESULTS_DIR`
  repointed from `<package>/test_results/` to `<repo-root>/tests/golden/full/
  pds{3,4}/` (package dir is three levels below repo root under `src/`); trailing
  `/` preserved (used as `TEST_RESULTS_DIR + expected`).
- `pyproject.toml`: `[tool.pytest.ini_options] pythonpath = ["src"]`. No
  `testpaths` yet (rule-module tests stay under `src/` until PR-08).
- `scripts/automated_tests/pdsfile_main_test.sh`: pytest test paths →
  `tests/pds{3,4}file/`; rule-module globs stay under `src/`.
- ruff ratchet: moved test files' per-file-ignores keys reprefixed to
  `tests/pds{3,4}file/…`; `tests` added to the ruff targets in
  `gen_ruff_ratchet.py` and `run-all-checks.sh` so the moved files stay linted
  (`tests/` is clean under the reprefixed ratchet).

## API manifest: unchanged
The tests subpackages were already excluded from the public-API dump, so their
removal from the package is a no-op for the freeze. The plan's pre-approved
forgiveness category #1 turned out precautionary — zero manifest diff.

## Gates
- Collection: 713 collected, conftest's `tests.pds3file.helper` import resolves.
- Full `--mode ns` (`tests/api` + `tests/pds{3,4}file` + all `rules/*.py`):
  **679 passed, 34 skipped, 0 failed** — golden-path repoint exercised by the
  `opus_products`/`associated_abspaths` rule tests.
- `--mode s`: **555 passed, 3 skipped, 0 failed**.
- `scripts/run-all-checks.sh` green: ruff (ratchet) clean and byte-identical on
  regen, pyroma **10/10**, API-freeze unchanged.
- Wheel: ships NO test/golden files (they left the package); rules +
  `pytest_support` retained.

## Note (latent smell, benign — resolved in PR-08)
`helper.py` now loads under two module names: `pds{3,4}file.helper` (test
modules' relative `from .helper`, because `tests/` has no `__init__.py` so
pytest prepend-mode names the package `pds{3,4}file`) and `tests.pds{3,4}file.
helper` (root conftest). Harmless — `helper.py` only reads env vars into
module-level constants (same value both times) and defines stateless functions;
no module-level mutable state, and the top-level `pds{3,4}file` names don't
collide with the real `pdsfile.pds{3,4}file`. PR-08 (conftest moves, tests
restructured) removes the divergence. Logged in
`critiques/deferred-observations.md`.

## Adversarial review
See `critiques/pr-07/round-1.md`. Zero findings; converged in one round.
