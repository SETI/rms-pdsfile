# PR-02 validation record — public-API freeze manifest and checker

## Gates active in Phase 0 for this PR
- API-freeze manifest test (introduced by this PR)
- No ruff gate yet (Phase 1), no format gate (Phase 5), no hermetic CI (Phase 4).

## Results
- `pytest tests/api/test_api_freeze.py` under the full harness with real-holdings
  preload (`PDS3_HOLDINGS_DIR=/data/pdsdata/holdings`,
  `PDS4_HOLDINGS_DIR=/data/pdsdata/pds4-holdings`): **1 passed** (339s; the time
  is the pre-PR-09 conftest preload, not the test).
- Fresh no-holdings process (`python scripts/dump_public_api.py`): manifest is
  **byte-reproducible** across runs and byte-identical to the committed
  `tests/api/api_manifest.json`.
- Checker logic verified directly: detects removed member, changed signature,
  and changed kind; exact-record and category-predicate forgiveness both work.
- Manifest shape: 43 modules, 39 classes (PdsFile 217 public members; all pds3
  and pds4 rule subclasses and their inherited surface captured).

## Design note (in-process vs subprocess; excluded-module references)
The freeze is the *import-time* public surface. Generating the manifest
in-process would record names bound by the test harness:
- the root conftest's `from pdsfile.pds3file.tests.helper import ...` binds a
  `tests` attribute on `pdsfile.pds3file` / `pdsfile.pds4file`;
- the rules' `from .pytest_support import *` transitively binds `pytest_support`
  (on each rules package) and `pdsfile_test_helper` (on `pdsfile`).
Left unhandled, the freeze would pass hermetically (no preload/conftest) but
fail on the self-hosted holdings gate, and would freeze test-infra names the
plan wants invisible (`pdsfile_test_helper`, `pytest_support`). Two mechanisms
fix this: (1) `test_api_freeze.py` regenerates via a fresh child subprocess;
(2) `dump_public_api.py` skips module-attribute references to the excluded
modules. `preload()` itself was confirmed to inject **zero** public surface
changes (measured pre/post preload: 0 diffs).

## Adversarial review
See `critiques/pr-02/round-*.md`.
