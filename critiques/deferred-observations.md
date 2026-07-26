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

## From PR-03+04
- **`scripts/dump_public_api.py` trips RUF100 (unused `# noqa: BLE001`).** BLE is
  not in the ruff `select` set, so the noqa is unused. The file is frozen
  post-PR-02 (plan §6.4), so it was ratcheted (`["RUF100"]`) rather than edited.
  A later PR could remove the dead noqa (comment-only, freeze-neutral) with owner
  sign-off, then drop the ratchet entry.

## From PR-07
- **`helper.py` double-import (benign, resolved in PR-08).** After the tests
  move to the top-level `tests/` tree, `helper.py` loads under two module names:
  `pds{3,4}file.helper` (test modules' relative `from .helper`, since `tests/`
  has no `__init__.py` so pytest prepend-mode names the package `pds{3,4}file`)
  and `tests.pds{3,4}file.helper` (root conftest). Harmless — read-only env-var
  constants + stateless functions, no name collision with `pdsfile.pds{3,4}file`.
  PR-08 (conftest moves, tests restructured, `testpaths` added) removes the
  divergence; no action needed before then.

## From PR-08 (rounds 1–3)
- **Pre-existing pds4 uranus s-mode blackbox failures (full-holdings golden
  area, owner-deferred).** A full `pytest tests --mode s` (i.e. including
  `tests/pds4file/`) shows 5 failures in
  `tests/pds4file/test_pds4file_blackbox.py` (uranus_occ, a
  `KeyError`→`UnboundLocalError` around `pdsfile.py:4254/4265`). Verified
  **identical on `origin/rewrite`** — pre-existing, not introduced by PR-08 —
  and **not** exercised by the CI s-mode invocation, which is pds3-only
  (`tests/pds3file tests/rules/pds3 --mode s`). Sits in the full-holdings
  golden/shelf-reproducibility area the owner split out of PR-08. Owner:
  the deferred additive-coverage / golden-reproducibility follow-up.
- **`_is_forgiven` ignores a category's `pr` field.**
  `tests/api/test_api_freeze.py::_is_forgiven` never reads `pr`, so §6.1's
  "a category activates only from its named PR" is not enforced in code
  (pre-existing in the PR-02 checker; the file is frozen post-PR-02). The PR-08
  allowlist entry still records `"pr": "PR-08"` for provenance. Owner: a future
  checker-hardening PR with owner sign-off.
- **PR-07's `helper.py` double-import is NOT resolved by PR-08.** The owner's
  split narrowed PR-08 to rule-test extraction only — it did not add
  `testpaths` or restructure `tests/pds{3,4}file/`, which still use `from
  .helper import …`. Re-deferred to whichever PR adds `testpaths` / the
  pds{3,4}file test restructure (the PR-07 note that attributed this to PR-08
  predates the split).

## From PR-06 (CodeRabbit review of #97)
- **17 pre-existing bugs/quality issues in the holdings-maintenance tools** (1
  Critical, 6 Major, 10 Minor) surfaced when PR-06 moved the tools into the
  package. None introduced by the move. Captured in full in
  `critiques/coderabbit-findings.md` — to be addressed in a maintenance-tools
  quality pass (with tests), issue #82, not in a mechanical move PR.

## From PR-09 (owner request, 2026-07-25)
- **Remove the `PDSFILE_TEST_HOLDINGS` selector env var — deferred to PR-11.**
  The owner wants the explicit `PDSFILE_TEST_HOLDINGS=full` selector to go away.
  It can be replaced without an env var, but not by markers alone: markers pick
  *which tests* run (per-item), while *which data tree to preload* is a
  session-level choice whose locations are machine-specific (`PDS3/4_HOLDINGS_DIR`
  for full; `PDSFILE_TEST_DATA_DIR` for the mini checkout) and so cannot become
  markers. Planned end-state, to land with the mini tree in PR-11:
  - Infer the flavor: mini when `PDSFILE_TEST_DATA_DIR` resolves to real trees,
    else full when `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR` are set and valid,
    else skip all gracefully.
  - Add a `--holdings full|mini` pytest CLI option (parallels `--mode`/`--update`)
    as the explicit override for the "both present" case — a flag, not an env var.
  - Then drop `export PDSFILE_TEST_HOLDINGS=full` from
    `scripts/automated_tests/pdsfile_main_test.sh` (full becomes inferred).
  - Keep `full_holdings` as the applicability marker (auto-skip under mini); PR-11
    also tags the actual size/volume-count tests with `@pytest.mark.full_holdings`.
  PR-09 keeps the explicit-`full` selector as originally spec'd until then.

## From PR-13 (maintenance-tool test suite, issue #82)

Five pre-existing defects surfaced while writing the tool tests. **None is fixed
in PR-13** — that PR is behavior-preserving (§6.4) — but each is pinned by a test
that asserts today's behavior and names, in its docstring, the source line and the
PR that owns the fix. Whichever PR changes the behavior will see the pin fail.

1. **`pds4archives` cannot round-trip.** `write_archive()` adds members under
   `arcname=<bundle-set basename>` (`pds4archives.py:238-241`) while
   `read_archive_info()` rebuilds each member path with the prefix that already
   ends at the bundle set (`pds4archives.py:126-135`, via
   `dirpath_and_prefix_for_archive`). Every member comes back doubled
   (`bundles/<bs>/<bs>/…`), so `--validate` fails immediately after a successful
   `--initialize`. The complete holdings set's `archives-bundles/<bs>/` directory
   is empty, i.e. this has never round-tripped in production either.
   Pinned by `test_pds4_archives.test_validate_cannot_round_trip`. **Owner: PR-25.**
2. **`pds4archives` on a bundle raises `RuntimeError: No active exception to
   reraise`** — the "no archive paths resolved" branch is a bare `raise` outside
   any `except` (`pds4archives.py:214-218`). Reached whenever the tool is pointed
   at a bundle in a bundle set whose archives are defined at the set level.
   Pinned by `test_pds4_archives.test_initialize_on_a_bundle_raises`.
   **Owner: PR-25.**
3. **`pds4indexshelf` cannot shelve any PDS4 metadata table that exists today.**
   `generate_indexdict()` builds a `pdstable.PdsTable` from `pdsf.label_abspath`
   (`pds4indexshelf.py:52`), a PDS3 detached-label reader. For
   `uranus_occs_earthbased` the `.csv` has no PDS3 label, so `label_abspath` is
   empty and the read raises `FileNotFoundError`; for
   `cassini_uvis_solarocc_beckerjarmak2023` the `.xml` is misparsed as a PDS3
   label and raises `ValueError: row count mismatch`. Both PDS4 bundle sets that
   exist fail. Pinned by
   `test_pds4_indexshelf.test_initialize_cannot_read_a_pds4_index`.
   **Owner: PR-27.**
4. **`pds4linkshelf --update` raises against any existing shelf.**
   `generate_links()` is handed the *loaded* shelf as `old_links`, whose values are
   the plain tuples that were pickled, and then dereferences `info.linktext` on
   them (`pds4linkshelf.py:395`) — `AttributeError: 'tuple' object has no
   attribute 'linktext'`. The pds3 twin merges the same data correctly, so this is
   pds4-only. Pinned by
   `test_pds4_linkshelf.test_update_is_broken_and_repair_is_the_working_path`.
   **Owner: PR-27.**
5. **`pdschecksums` and `pds4checksums` never propagate errors into the exit
   code.** Both compute a `proceed` flag from `fatal or errors` and then use it
   only to gate the optional `--infoshelf` chain (`pdschecksums.py:905-919`,
   `pds4checksums.py:878-892`); neither ends in `sys.exit(status)` the way the
   other nine tools do. A `--validate` that reports checksum mismatches still
   exits 0. Pinned in both checksum test modules (see
   `support.TOOLS_WITHOUT_EXIT_STATUS`). **Owner: PR-25** — its `run_main()` spec
   says "set exit code from fatal/errors", which will change these two tools'
   exit codes; that is an intended, plan-sanctioned behavior change and the pins
   must be updated with it.

Two further observations, not defects in a single tool:

6. **`shelf_consistency_check` targets a legacy holdings layout.** It walks for
   `shelves/<info|links|index>/…`, but current holdings keep shelves in
   `_infoshelf-volumes/`, `_linkshelf-volumes/` and `_indexshelf-metadata/`, none
   of which contain the substring `shelves`. Run against a modern tree with real,
   valid shelves it reports "Tests performed: 0, Errors found: 0". Its
   `error += 1` / `errors` typo (already on PR-15's list, fixed in PR-28) is only
   reachable through the legacy layout. Both are pinned in
   `test_shelf_consistency_check.py`. **PR-28**, which gives this tool a `main()`,
   is where the layout question has to be answered.
7. **Info-shelf sidecars are local-time dependent.** `pdsinfoshelf` /
   `pds4infoshelf` format modification times with
   `datetime.fromtimestamp(...).strftime(...)`, so the same tree shelved in two
   time zones produces different sidecars. The tests pin `TZ=UTC` in the tool
   subprocess environment to make goldens portable; whether the tools themselves
   should record UTC is a behavior question for the Phase 6 consolidation.
