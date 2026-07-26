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

Eight pre-existing defects surfaced: entries 1-5 while writing the tool tests,
entries 10-11 during the adversarial review rounds, and entry 14 from the CI
failure of PR #105. (Entries 12-13 are process observations from the coordinator
review, not tool defects.) **None is fixed in PR-13** —
that PR is behavior-preserving (§6.4) — but each is pinned by a test that asserts
today's behavior and points at its numbered entry below, where the defect, its
location and the owning PR are written up. Whichever PR changes the behavior will
see the pin fail.

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

### Added by the PR-13 adversarial review (round 1)

8. **The tool tests contribute no measured coverage.** The suite driver runs
   `python -m coverage run -m pytest`, but every maintenance tool runs in a child
   process with no `COVERAGE_PROCESS_START`, so `coverage report` sees nothing
   from the 100+ new tests. Subprocess invocation is load-bearing and cannot be
   given up (see §2.2 of `plans/2026-07-25-pr-13-subplan.md`), so the fix is a
   `COVERAGE_PROCESS_START` / `sitecustomize` hook in the tests' subprocess
   environment. **Owner: PR-14**, which owns CI/coverage correspondence.
9. **`tests/api/test_api_freeze.py` is not marked `holdings_free`.** PR-14's spec
   says the hosted no-holdings job must run the API-freeze test as part of its
   pytest subset, but the collect-and-skip rule will still skip it there. PR-13
   only owed the `crlf` tests. **Owner: PR-14** — mark the API-freeze test (and
   any other genuinely holdings-free test) when that job is built.

### Added by the PR-13 adversarial review (round 2)

10. **`pdsinfoshelf`'s validate comparison is defective in three ways** (pds3
    only; `pds4infoshelf` gets all three right, which is why the two test modules
    expect opposite outcomes):
    - `checksum1 != checksum1` compares a value to itself, so a content change is
      never reported. Pinned by
      `test_pds3_infoshelf.test_known_undetected_corruption[label_byte0_same_size]`.
    - `abs(modtime1 != modtime2) > 1` takes `abs()` of a bool, which is 0 or 1 and
      never `> 1`, so modification-time drift is never reported. Pinned by
      `test_pds3_infoshelf.test_known_undetected_corruption[label_mtime_plus_100]`.
    - The child-count message formats `(count1, count1)`, so it prints the
      on-disk count twice instead of on-disk versus shelved. Pinned by
      `test_pds3_infoshelf.test_update_picks_up_a_new_file`.
    **Owner: PR-26.** The parent plan's PR-26 list already names the first two;
    the message defect is not on it and should be folded in when the pair moves
    onto the shared core. All three pins must be inverted at that point.
11. **`crlf.test_crlf` raises `ZeroDivisionError` on a zero-byte file.** The
    non-ASCII fraction divides by the decoded length without guarding an empty
    file, so `crlf --repair` over a tree containing one dies instead of reporting
    it. Pinned by
    `test_crlf.TestArgumentValidation.test_an_empty_file_raises_zerodivisionerror`.
    **Owner: PR-28**, which gives `crlf` a `main()`; deciding what an empty file
    should classify as ('OK'? 'BINARY'?) is part of that work.

### Added by the PR-13 coordinator review

12. **`--mode` has no default, and its fallback is an asymmetric combination the
    suite never validates.** `pytest_addoption` declares `--mode` with no
    `default=` (`tests/conftest.py:22`), so omitting it leaves
    `config.option.mode` as `None` and the `setup` fixture takes its `else`
    branch (`tests/conftest.py:73-75`), setting `Pds3File.use_shelves_only(True)`
    and `Pds4File.use_shelves_only(False)`. That mixed state is neither `s` (both
    True) nor `ns` (both False), and it carries `# pragma: no cover` — neither CI
    nor `scripts/automated_tests/pdsfile_main_test.sh` ever reaches it, because
    both invocations pass `--mode` explicitly. The same branch is also the
    **silent fallback for any unrecognized value**: `--mode NS`, `--mode n` or a
    typo selects the mixed mode instead of erroring. Pre-existing and unchanged by
    the rewrite — the identical block is on `main` at `conftest.py:36`, and PR-09
    moved the surrounding code without touching it; PR-13 does not touch it
    either. Not currently reachable in a harmful way: the hosted no-holdings job
    omits `--mode`, but with no holdings the fixture returns before the branch.
    It becomes live the moment a `--mode`-less invocation gains holdings. Fix
    direction (not decided here): give the option `choices=('s', 'ns')` plus an
    explicit `default`, so a typo fails loudly and the default is a mode the suite
    actually exercises — or document what the mixed combination is for and cover
    it. **Owner: PR-14**, which owns CI / `run-all-checks.sh` pytest-invocation
    correspondence.
13. **The maintenance-tool tests run in the `--mode ns` invocation only.**
    `scripts/automated_tests/pdsfile_main_test.sh` adds
    `tests/holdings_maintenance/` to the not-shelves-only pass and deliberately
    omits it from the shelves-only pass (recorded as deviation 2 in
    `plans/2026-07-25-addendum-holdings-free-marker.md`, owner-accepted
    2026-07-26). The justification is that `--mode` flips `use_shelves_only`
    inside the pytest process while every tool runs in its own subprocess that
    inherits none of it, so the two passes would execute byte-identical work.
    **That justification is load-bearing on subprocess invocation and expires
    where invocation changes.** PR-28's spec switches the
    `shelf_consistency_check` and `show_opus_products` tests to call `main()`
    in-process; those tests then run inside the pytest process and *do* observe
    `use_shelves_only`, at which point the mode question is live for them and the
    single-pass decision must be re-derived rather than inherited. **Owner:
    PR-28** (re-derive for the two tools it converts), with **PR-14** noting the
    same coupling if it changes how the suite is invoked. Entry 12 above is the
    related question of what mode a `--mode`-less run selects at all.

### Added by the CI failure of PR #105 (2026-07-26)

14. **`pdsdependency` emits its "Steps required" plan in filesystem-enumeration
    order.** Each dependency rule does `abspaths = glob.glob(pattern)` with no
    sort and then iterates it, so the steps a single rule contributes come out in
    whatever order the directory happens to enumerate. `glob` does not sort, and
    ext4 returns entries in a per-filesystem hash order, so the *same* tree yields
    a different plan order on a different machine — which is exactly how this
    surfaced: the tool tests passed against both holdings roots on the development
    machine and failed on the CI runner, with the two cumulative-table steps
    swapped and nothing else changed.

    Not a correctness defect — the *set* of steps is identical and the plan works
    in any order within a rule — but it makes the output unstable for anyone
    diffing two runs, and it is the kind of thing a shared tool core should fix
    once. **Owner: Phase 6** (`pdsdependency` stays standalone in PR-25, so
    whichever PR touches it next): sort the glob results.

    **PR-13 did not change the tool.** It stopped depending on the unspecified
    order instead: the step-list golden is compared as a sorted multiset
    (`support.check_golden(..., unordered=True)`), which still pins the exact set
    and text of every step, while the twelve steps whose position the tool *does*
    determine — those from rules whose glob matched a single path — are pinned in
    exact order, so a rule reordering its messages still fails the test. When the
    tool starts sorting, the test keeps passing and the golden stays valid.
