# PR-09 adversarial review — round 1

Reviewer: fresh, no-context general-purpose Opus subagent. Goal: adversarially
prove PR-09 ("test: holdings-aware conftest, markers, graceful skip") did NOT
meet its stated goal. The reviewer independently ran pytest across every env
combination rather than trusting any claim.

## Verdict: GOAL MET — zero Major, zero Minor findings

The reviewer could not find a real defect. Every resolution branch behaves as
specified; parity is exact; collection never raises with no holdings; explicit
misconfig errors loudly (exit 4); the skip-reason text is exact; the
`full_holdings` marker auto-skips under mini; api-freeze stays hermetic; ruff
passes; no holdings paths are hardcoded.

## Evidence reproduced by the reviewer
- full `--mode ns` (api+pds3+rules/pds3+pds4+rules/pds4) → 679 passed / 34 skipped.
- full `--mode s` (pds3+rules/pds3) → 555 passed / 3 skipped.
- mini (`PDSFILE_TEST_DATA_DIR=/seti/opus/pdsdata`, PDS3/PDS4 unset) → 679/34 (ns),
  555/3 (s).
- unset + nothing → collects, exit 0, all skipped with reason
  `no holdings available (set PDSFILE_TEST_HOLDINGS)`.
- `PDSFILE_TEST_HOLDINGS=bogus` / `Full` (case-sensitive) → `ERROR: ... must be
  'full' or 'mini'`, exit 4. Empty string treated as unset (graceful).
- full with PDS3/PDS4 unset → `ERROR: ... requires ... to be set`, exit 4.
- mini with no data dir → `ERROR: ... requires PDSFILE_TEST_DATA_DIR`, exit 4;
  with a nonexistent dir → `ERROR: ... missing holdings tree(s): ...`, exit 4.
- `full_holdings` probe test (added then deleted, tree left clean): skipped under
  mini with reason `full_holdings: skipped under the mini fixtures`; ran under full.
- api-freeze `--confcutdir=tests/api` → 1 passed under fresh env, full env, and
  even `PDSFILE_TEST_HOLDINGS=bogus` (root conftest not loaded → truly decoupled).
- `ruff check src/pdsfile tests scripts` → clean. Working tree left clean.

## Low-severity, by-design observations (not defects)
- `resolve_holdings()` is a pure function called ~3x/session (conftest +2 helper
  imports); deterministic from stable env, so DRY holds semantically. No caching
  by design (keeps the resolver stateless).
- Helper modules call `resolve_holdings()` at import, which would raise under an
  explicit-broken config — but `pytest_configure` raises `UsageError` first, so
  it is never observed. The "remove import-time KeyError" goal (the no-holdings
  graceful path) is met: import succeeds with placeholder roots.

## Deferred / out-of-scope (later work, not PR-09 findings)
- `run_tests_coverage.sh` references pre-move paths — already broken on `rewrite`,
  untouched here.
- `scripts/run-all-checks.sh` pytest gate is default-disabled and unwired; if
  enabled without a flavor it would all-skip green. Belongs to PR-11/PR-14.
- The unset default intentionally ignores `PDS{3,4}_HOLDINGS_DIR` unless
  `PDSFILE_TEST_HOLDINGS=full`. The only in-repo consumer
  (`scripts/automated_tests/pdsfile_main_test.sh`, run by
  `.github/workflows/run-tests.yml`) was updated to export the full flavor.
