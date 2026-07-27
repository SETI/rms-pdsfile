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
   environment. ~~**Owner: PR-14**, which owns CI/coverage correspondence.~~

   **STILL DEFERRED — re-assigned by PR-14 (2026-07-26), with measurements.** The
   fix works, and its cost is prohibitive on the gate that would pay it. Measured
   on the limited holdings copy with

   ```sh
   PDSFILE_TEST_HOLDINGS=full python -m coverage run -m pytest \
       tests/holdings_maintenance/test_pds3_archives.py --mode ns -q -p no:cacheprovider
   ```

   the only variable being whether
   `tests/holdings_maintenance/support.py::run_tool` prefixes each tool
   subprocess with `-m coverage run --parallel-mode --rcfile <repo>/pyproject.toml`
   and sets an absolute `COVERAGE_FILE` in the subprocess environment:

   | tool subprocesses | pytest summary line |
   |---|---|
   | uninstrumented (today) | `8 passed, 5 warnings in 16.06s` |
   | instrumented | `8 passed, 5 warnings in 138.84s` |

   An **8.6x** slowdown, on the arm of the self-hosted suite that runs on every PR
   and nightly across four Python versions. The cost is the line tracer running
   inside each tool, so the `sitecustomize` / `COVERAGE_PROCESS_START` route named
   above measures the same and costs the same. It also requires parallel data
   files plus a `coverage combine` step (guarded, because a holdings root that
   lacks a declared source subset legitimately produces zero child data files) in
   `scripts/automated_tests/pdsfile_main_test.sh` — the data-gate driver.

   Two things make waiting cheap: coverage numbers stay informational until the
   targets are set, and PR-28 converts the `shelf_consistency_check` and
   `show_opus_products` tests to in-process `main()` calls, which are measured
   with no subprocess machinery at all. If it is taken up, `COVERAGE_CORE=sysmon`
   (Python 3.12+) is the lever worth measuring first — and note the coverage
   artifact is uploaded from the 3.13 leg only, so the instrumentation need not be
   paid on every leg. **Owner: PR-37** (Phase 8, "set codecov targets"), which is
   where the number first has to mean something.
9. ~~**`tests/api/test_api_freeze.py` is not marked `holdings_free`.**~~
   **RESOLVED (PR-14).** `tests/api/conftest.py` marks every item collected from
   `tests/api/` `holdings_free`, so the freeze test runs in the hosted
   no-holdings job (`tests/api/test_api_freeze.py` itself is frozen by §6.4 and is
   not edited). The directory-wide form also covers later additions such as
   `tests/api/test_mixin_collisions.py` (PR-17).

   The entry's second half — "and any other genuinely holdings-free test" — was
   surveyed by measurement, not by inspection, and deliberately left unmarked;
   the reasoning and the numbers are in §4 of `critiques/pr-14/validation.md`
   and the residual option is recorded as entry 15 below.

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
    it. ~~**Owner: PR-14**, which owns CI / `run-all-checks.sh` pytest-invocation
    correspondence.~~

    **RESOLVED (PR-14, owner decision 2026-07-26).** `--mode` now carries
    `choices=('s', 'ns')` and `default='ns'`, so a mistyped mode is a usage error
    and a bare `pytest` selects the broader of the two validated modes (`ns` is
    the only mode in which the whole tree passes; the shelves-only pass is
    pds3-only for that reason). The mixed `else` branch is deleted rather than
    left unreachable: `setup` now derives one `shelves_only` boolean and applies
    it to both classes, so a session where `Pds3File` and `Pds4File` disagree can
    no longer be constructed. `scripts/run-all-checks.sh` passes `--mode ns`
    explicitly so its invocation does not depend on the default. Every `--mode`
    invocation in the repo was surveyed; all already passed an explicit `s` or
    `ns`, so no existing invocation changes behavior, and the two full-data
    per-test pass/fail sets are byte-identical to the pre-change runs
    (`critiques/pr-14/validation.md`).
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

    **PR-14 note (2026-07-26).** PR-14 leaves
    `scripts/automated_tests/pdsfile_main_test.sh` untouched, so the two-pass
    split and its `--mode ns`-only tool-test placement are unchanged. It does add
    a third invocation, `scripts/run-all-checks.sh`, which runs the whole
    `tests/` tree — including `tests/holdings_maintenance/` — once, under
    `--mode ns`. That is the same mode the tool tests already ran in, so the
    coupling recorded here is unchanged and PR-28 still owns re-deriving it.

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

### Added by the PR-14 adversarial review (round 1)

15. **~291 data-suite tests pass with no holdings present, and are deliberately
    not marked `holdings_free`.** Measured on PR-14's branch by lifting the
    blanket skip with a throwaway `tryfirst` plugin that marks every collected
    item `holdings_free`, with all four holdings env vars unset:
    **315 passed / 387 failed / 122 skipped** — i.e. 291 beyond the 24 the
    hosted job ran at the time of the measurement. (PR-15 raised that 24 to 59
    by adding 35 genuinely holdings-free tests in `tests/core/`; a re-run of the
    forced-marker experiment would collect those same 35 among its passes, so
    **the surplus stays 291** and the observation is unchanged.) Grouped by test
    *function*: 124 functions have every parametrized case passing, 41 are
    **mixed** (some cases pass, some fail) and 126 fail outright. The four
    modules involved are `tests/pds{3,4}file/test_pds{3,4}file_blackbox.py`,
    `test_pds3file_blackbox_cached.py` and `test_pds3file_whitebox.py`. The
    result is not order-dependent: each module run alone yields the same passing
    set as it does inside the whole-tree run.

    PR-14 did not mark them, for four reasons recorded in §4 of
    `critiques/pr-14/validation.md`: they do not build their own inputs (they
    concatenate the *resolved* holdings root, which with no holdings is PR-09's
    synthetic `/pdsfile-no-holdings/...` placeholder — the test ids contain it,
    so they assert against a root that does not exist); the pass/fail split runs
    through the middle of parametrize tables, not along module, class or function
    lines, so 41 functions cannot be marked at all; nothing pins the
    no-filesystem-access property, so a mark is a CI-only tripwire right before
    Phase 5 rewrites those very code paths; and the plan's own enumeration of the
    subset (§1 G3: "API freeze, tool unit tests, import/collection smoke") does
    not include the data suite.

    Worth revisiting only together with **issue #92** (move inline
    `@parametrize` values into golden files), which is where the tables would be
    split into a data-dependent and a path-only half in the first place. #92 is
    listed in §9 of the plan as future work outside this effort. **Owner: #92 /
    post-merge.**
16. **`run_tests_coverage.sh` at the repo root cannot run.** It invokes
    `pytest pdsfile/pds3file/tests/ pdsfile/pds3file/rules/*.py`, paths that
    stopped existing when PR-05 moved the package under `src/` and PR-07 moved
    the tests to the top-level `tests/` tree. It is one of the `--mode` call
    sites PR-14 surveyed (it passes valid modes, so PR-14's `choices` change does
    not affect it) and was otherwise left alone. Delete it or update it to the
    current layout. **Owner:** whichever PR next touches the root scripts;
    PR-37's finalization sweep at the latest.
17. **`CONTRIBUTING.md` documents `pytest` without holdings or `--mode`.** Its
    testing section shows bare `pytest` / `pytest tests/<file>` with no mention
    of `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR`, `PDSFILE_TEST_HOLDINGS`, or
    `--mode`. Now that the pytest gate is enabled, a contributor following it
    gets an 800-skip run with no explanation of why. **Owner: Phase 7**
    (PR-33 ch. 5 "Test-suite guide", or PR-34 with the README rewrite).
18. **`tests/pds{3,4}file/helper.py` resolve holdings at import time.** Each
    module does `PDS3_HOLDINGS_DIR = resolve_holdings().pds3_root` at import,
    rather than reading the session's `config._pdsfile_holdings`. The two agree
    today because the resolver is a pure function of the environment and nothing
    mutates it mid-session, but they are two independent resolutions of the same
    question. **Owner:** whichever PR restructures `tests/pds{3,4}file/` (the
    same one that owns PR-07's `helper.py` double-import note above).

### Added by the PR-14 adversarial review (round 2)

19. **`[tool.pytest.ini_options]` declares no `testpaths`.** `python_testing.mdc`
    asks for it, and `critiques/deferred-observations.md`'s PR-08 entry already
    notes that "whichever PR adds `testpaths`" also owns PR-07's `helper.py`
    double-import. Harmless today — every invocation names its paths explicitly,
    and `venv/` is in pytest's default `norecursedirs` — so it is a tidiness item,
    not a correctness one. Pre-existing since PR-03. **Owner:** the same PR that
    restructures `tests/pds{3,4}file/` (see the PR-08 entry above).

### Added by the PR-14 adversarial review (round 3)

20. **The hosted no-holdings job has no floor on how many tests actually ran.**
    The plan calls that run "itself the regression test for PR-09's graceful
    skip", and it does catch the primary regression: a collection error exits
    non-zero. But a regression that skipped *everything* — say the
    `tests/api/conftest.py` path predicate quietly stopping matching — exits 0 and
    the job stays green, because "0 passed, N skipped" is a passing pytest run
    (N was 824 when this was written and is 859 after PR-15).
    PR-14 hardened the one known way that could happen (both sides of the path
    comparison are resolved), and each PR's §6.2 record pins the expected
    no-holdings counts, so a drop is visible in review — but nothing fails
    automatically. A cheap tripwire (assert a floor on the passed count, or
    require specific node ids to have run) belongs with whatever PR next touches
    the hosted job. **Owner:** PR-37's finalization sweep, or any earlier PR that
    edits the lint job.
21. **Two §6.4-frozen files cite the archived v1 plan.**
    `scripts/dump_public_api.py` and `tests/api/test_api_freeze.py` both point at
    `plans/2026-07-17-modernization-plan.md`, which moved to `plans/archive/`.
    Both files are under the absolute prohibition on editing, so PR-14 left them
    alone (it did fix the same stale reference in
    `.cursor/rules/pdsfile_overrides.mdc`, which is not frozen). Fixing a comment
    in a frozen file is freeze-neutral but needs owner sign-off, exactly like the
    dead-`noqa` item recorded under "From PR-03+04" above. **Owner:** the same
    owner-blessed touch-up of the frozen files.

### Added by the CodeRabbit review of PR #107 (2026-07-26)

22. **The self-hosted `test` job still runs on default workflow permissions.**
    `zizmor` flags `excessive-permissions` on `.github/workflows/run-tests.yml`:
    neither the workflow nor the `test` job declares a `permissions:` block, so
    both `pull_request` jobs got the repository's default token scope. PR-14
    fixed the half it owns — the new `lint` job declares
    `permissions: contents: read` and its checkout sets
    `persist-credentials: false` — but the PR-14 bullet says to keep the
    self-hosted matrix exactly as it is, so the `test` job was left alone. It
    checks out PR-head code and then runs it, and it additionally needs whatever
    scope `codecov/codecov-action` uses, so the right block is not simply a copy
    of the lint job's. The same applies to `run-tests-and-opus.yml`, which is
    likewise untouched here. **Owner:** a CI-hardening pass, or PR-37's
    finalization sweep.

## From PR-15 (latent core-path bug fixes, Phase 5)

No entry in 1–22 is resolved or invalidated by PR-15. Entries 10 and 11 are
maintenance-tool defects owned by PR-26/PR-28 and were deliberately not touched:
§5 keeps the tool-bug twins in Phase 6, where those files are already being
edited. Two entries cite suite counts that PR-15 moves — entry 15's "24 the
hosted job runs" and entry 20's "824 skipped" — and both are annotated in place;
the observations themselves stand unchanged. The items below were found while
fixing the seven the plan enumerates; §2 permits only the enumerated changes, so
each is recorded rather than fixed.

23. **`DictionaryCache(lifetime=0)` cannot serve `set()` without an explicit
    lifetime.** The constructor documents `lifetime` as "default lifetime in
    seconds; 0 for no expiration", and `set()` documents `lifetime=None` as "use
    the default lifetime". But `set()` tests the default for truthiness
    (`pdscache.py:196`, `if self.lifetime:`), so a default of `0` falls through
    to `self.lifetime_func(value)`, which is `None` when the cache was built
    with a constant — `TypeError: 'NoneType' object is not callable`. Every
    caller in this repo passes a lifetime function or a non-zero constant, so
    nothing hits it today; it is a trap for the next caller who takes the
    docstring at its word. The fix is a `self.lifetime is not None` test, which
    is a behavior change to a public class and therefore outside PR-15's
    enumerated list. Found because a test fixture built its throwaway cache with
    `lifetime=0`. **Owner:** a future pdscache PR, or phase "b".

24. **`DictionaryCache.set_multi`'s `pause` parameter has never suppressed the
    per-key trim, and still does not.** The broken call PR-15 repaired passed
    `pause=True` down to `set()`, plainly intending to defer trimming until the
    batch finished. `set()`
    has no such parameter and never did, so the intent was never expressible;
    PR-15 dropped the keyword, which is the literal fix for "passes an
    unsupported kwarg". The consequence is that `pause` now governs only the
    final explicit `_trim_if_necessary()` call, while each `set()` inside the
    loop still trims if the cache is not paused. Honoring the original intent
    means either bypassing `resume()`'s trim or giving `set()` a real `pause`
    parameter — both are new semantics for a public method, which §6.4 makes an
    owner decision rather than an executor's. No caller exists in this repo.
    **Owner:** a future pdscache PR, with the owner's read on the intended
    semantics.

25. **`MemcachedCache.set_multi` applies one key's lifetime to the whole batch.**
    The lifetime-lookup loop assigns to a single `lifetime` local
    (`pdscache.py:798-800`), so after it runs, `lifetime` holds whichever key
    memcached happened to yield last. The store loop then passes that one value
    to `set_local()` for **every** key, overwriting the correct per-key lifetimes
    the lookup loop had just written into `local_lifetime_by_key`, and applying
    it to keys that were already local as well. PR-15 fixed only the enumerated
    defect on the same lines — iterating the dictionary as pairs — because until
    that was fixed the method raised before reaching the store loop, and because
    correcting the lifetime plumbing is a second, larger behavior change. The
    regression test added for the enumerated fix uses a single key, so it does
    not pin the batch behavior either way. **Owner:** a future pdscache PR.

26. **`_recache()` silently downgrades a permanent cache entry to an expiring
    one.** `preload` stores the top-level category entries with `lifetime=0`, so
    they never expire. Any lazy property that fills in and then calls
    `self._recache()` re-stores the object with `lifetime=None`, which
    `DictionaryCache.set()` resolves through `cache_lifetime_for_class` to a
    finite value — 7 days for a category object. Measured on `rewrite` @
    `807956a`, i.e. *before* PR-15: reading `description` or `iconset_closed` on
    the `volumes` object already flips its cache entry from permanent to
    expiring. PR-15's `html_path` fix adds `html_path` to that set (14 entries in
    a full walk of the limited holdings copy), which is why this is recorded
    here rather than earlier — it is pre-existing behavior of the property
    pattern, not something the fix introduced, and `MemcachedCache` is unaffected
    because its `set()` preserves a previously-defined lifetime. One further
    consequence: a downgraded entry also joins `DictionaryCache.keys`, the
    trimmable set, so a process that ever exceeds `limit + slop` (220,000) could
    evict a category entry — previously impossible for a `lifetime=0` entry.
    Whether a long-running process should be able to expire a category entry at
    all is a cache-design question for issue #77 phase "b". **Owner:** phase "b".

### Added by the PR-15 adversarial review (round 2)

27. **`html_path` raises `IndexError` on an empty merged category.**
    `pdsfile.py`'s `html_path` handles a merged directory (`self.abspath is
    None`) with `self.child(self.childnames[0]).html_path`, which indexes an
    empty list whenever a category is present in the preload but has no
    children. Measured, not hypothesized: **36 of the 1,910 objects** in PR-15's
    bug-1 probe do exactly this against the limited holdings copy — every
    category that copy does not populate (`archives-bundles`, `bundles` for
    Pds3File, `volumes` for Pds4File, the `checksums-archives-*` set, …). The
    behavior is identical before and after PR-15, which is why the probe's
    before/after comparison is unaffected. The code's own comment already calls
    the approach fragile ("Not a great solution but it usually works … This
    issue will probably never come up"), so this is a known-shaky path rather
    than a surprise; what is new is the measurement of how often it fires.
    Fixing it means deciding what a childless merged category's URL *is*, which
    is a behavior decision outside PR-15's enumerated list. **Owner:** phase "b"
    or a future `pdsfile.py` PR.

28. **`iconset_for`'s terminal lookup assumes an `UNKNOWN` icon set exists.**
    `pdsviewable.py`'s `iconset_for` ends with `ICON_SET_BY_TYPE[icon_type,
    is_open]`. PR-15 made the priority comparison key on the requested open
    state, so any icon type that *wins* the comparison necessarily has a set
    under that key and the lookup cannot raise for a winner. The remaining case
    is the starting value: if `load_icons()` was never called, or was called on a
    tree with no `document_generic` icon, `('UNKNOWN', is_open)` is absent and
    the function raises `KeyError` instead of returning anything. That shape is
    pre-existing — it is only reachable at all now that the function no longer
    raises `NameError` first — and turning it into a graceful return is a new
    behavior, not a bug fix. **Owner:** whichever PR next revisits the icon path.

## From PR-16 (extract module-level path helpers, Phase 5)

Both raised by the PR-16 adversarial review. Neither is fixable inside a pure
move PR: the first is process, the second is a pre-existing defect in code that
moved byte-for-byte and is outside PR-15's enumerated bug list.

29. **An extraction sweep must ask which module namespaces the tests *patch*, not
    only which globals the code *reads*.** PR-16's free-variable sweep answered
    "what must move with the code" correctly and completely. It could not have
    caught what the review did: `tests/core/test_pdsfile_path_resolution.py`
    replaced `glob` on `pdsfile.pdsfile`, so after the move the stub sat on a
    namespace `abspath_for_logical_path` no longer resolves through, and the
    test's outcome became a property of the machine rather than of the test. It
    still *passed*, so §6.2's outcome-set diff — which compares pass/fail, not
    what a test actually exercises — is structurally blind to it. The missing
    step is a one-line grep for `monkeypatch.setattr` / `setattr(<module>` over
    `tests/` and `scripts/` naming any module a PR moves code out of. PR-16 fixed
    its own site by patching the function's `__globals__`, which follows the
    function; the general step belongs in every later extraction PR's checklist.
    It matters most for **PR-17**, which moves the `os`-resolving filesystem
    helpers, where a stale `os` patch would be both likelier and harder to spot.
    **Owner:** PR-17 onward (a step in each extraction PR's sweep).

30. **`repair_case` raises `UnboundLocalError` on a single-component path.**
    `_path_utils.py`'s `repair_case` assigns `found` only inside
    `for k in range(1, len(parts))` but reads it unconditionally after the loop,
    so any path that splits into one component skips the assignment:
    `repair_case('/', Pds3File)` raises `UnboundLocalError: cannot access local
    variable 'found'`. `repair_case('/tmp', Pds3File)` is fine, so only the
    filesystem root and an empty-ish path reach it. Pre-existing and moved
    byte-for-byte by PR-16; it is not in PR-15's enumerated bug list, and PR-16
    is a pure move with no licence to change behavior. The fix is a
    `found = True` initialization (a path with nothing to repair *is* found), but
    that is a behavior change on a currently-raising input and needs its own test
    and PR. **Owner:** PR-23, or whichever PR next edits this file.

### Added by the PR-16 adversarial review (round 2)

31. **`src/pdsfile/__init__.py:10`'s `from pdsfile import *` binds nothing.** It
    is a self-import: when it executes, `sys.modules['pdsfile']` is the
    partially-initialized package, whose namespace holds only dunders and
    `__version__`, and a star import with no `__all__` skips every underscore
    name. Reproduced in a throwaway package with the identical shape — the
    statement contributes zero names. It reads as an intended
    `from .pdsfile import *`, which would be a very different thing: it would
    hoist every public name of `pdsfile.pdsfile` (including `repair_case`,
    `abspath_for_logical_path`, `PATH_EXISTS_CACHE_SIZE` …) onto the package,
    which is **not** the surface `tests/api/api_manifest.json` records for
    `pdsfile`. So this cannot simply be "fixed": deleting it and correcting it
    are both public-surface changes, one shrinking and one growing. It is also
    why `F403`/`F841` sit in that file's ratchet entry. Untouched by PR-16.
    **Owner:** PR-24, or whichever PR next revisits `__init__.py` — with an
    explicit decision about which of the two readings is intended.

32. **A commented-out line of dead code rode along with the move.**
    `src/pdsfile/_path_utils.py`, inside `_clean_join`:
    `#     joined = _clean_join(a,b).replace('\\', '/')`. PR-16 moved it
    byte-for-byte, which is correct — editing it would have been a content change
    inside a move PR. PR-22's brief is to "remove commented-out dead code
    (~89 lines) — listed line-by-line in the PR", and its line list was drawn
    against `pdsfile.py`; this line is no longer in that file. Recorded so the
    line list is rebuilt against the post-Phase-5 module set rather than the
    pre-split one. **Owner:** PR-22 (with PR-23 for the extracted modules'
    style).
