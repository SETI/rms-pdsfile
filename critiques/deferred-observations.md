# Deferred observations

Non-blocking items surfaced by per-PR adversarial reviews, recorded for the
phase/PR that owns them.

## From PR-02 (round 1)
- **Freeze is defeatable by editing the manifest/dumper/test.** Inherent to this
  contract style; prohibited by plan §6.4 and documented in both docstrings and
  the allowlist `_comment`. Process control, not a technical gap. Owner: process.
- **`test_api_freeze.py` collection needs holdings env vars** until the root
  `conftest.py` becomes skip-aware. Owner: **PR-09** (already documented in the
  test docstring).
- **`_is_forgiven` lacks `KeyError`/`re.error` guards** for a malformed future
  allowlist entry. Harmless while seeded empty and fail-safe (raises rather than
  mis-forgives). Owner: whichever PR first adds allowlist entries (PR-07/PR-08)
  may add validation.

## From PR-02 (round 2)
- **Module-level public function signatures are frozen by name+kind only.** The
  dumper records signatures for class members but not module-level functions
  (per the PR-02 algorithm, step 3 vs step 4). `cache_lifetime_for_class`
  (public, re-exported into `pdsfile` and `pdsfile.pds3file` from
  `preload_and_cache.py`) could have its signature changed without the freeze
  noticing — a gap vs ground rule 1's "identical signatures." Owner decision:
  leave as spec'd, or extend the dumper to sign module-level functions (small
  additive change; a plan-algorithm deviation needing an addendum per §6.4).
  **RESOLVED (owner, 2026-07-23): leave as spec'd — won't fix.**
  `cache_lifetime_for_class` has no external callers; its only references are
  internal to `PdsFile`. There is therefore no external signature to protect, so
  the freeze's class-member-only signature coverage is sufficient. No dumper
  change; no plan addendum needed.
