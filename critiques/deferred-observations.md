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
21. **CLOSED — owner decision, 2026-08-04: leave them.** Asked directly, in the
    context of a sweep that removed every other plan and critique citation from
    `src/` and `tests/`, the owner ruled that `tests/api/test_api_freeze.py`'s
    docstring stays as it is. The two frozen files keep their references to the
    archived v1 plan; no owner-blessed touch-up is wanted. They are now the only
    plan citations left in any `.py` file in the repository, which is the
    intended end state, not an oversight. The original entry follows.

    **Two §6.4-frozen files cite the archived v1 plan.**
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

Six entries, all raised by the PR-16 adversarial review; 29 and 30 in round 1,
31 and 32 in round 2, 33 and 34 in round 4. None is fixable inside a pure move
PR: 29 is process, 30 is a pre-existing defect in code that moved byte-for-byte
and is outside PR-15's enumerated bug list, 31 would change the public surface in
whichever direction it were resolved, 32 belongs to the PR that owns dead-code
removal, and 33 and 34 are pre-existing conditions of files PR-16 does not
touch.

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

    **Extended by the PR-16 round-3 review:** the same asymmetry exists one level
    down, for module-level *data* rather than modules. `FILE_BYTE_UNITS` is
    re-exported by `pdsfile.pdsfile` but read by `formatted_file_size` through
    `_path_utils`'s globals, so mutating the list in place still works while
    *rebinding* `pdsfile.pdsfile.FILE_BYTE_UNITS` is now silently inert. Measured:
    no consumer anywhere does either, so nothing is broken today. PR-17 moves
    `PATH_EXISTS_CACHE_SIZE` and hits the same shape, so the sweep step should
    cover rebinding of re-exported data, not only of modules.
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

    **RESOLVED by the owner, 2026-08-04: the intent was to export the `PdsFile`
    class only.** Implemented in PR-24 as
    `from pdsfile.pdsfile import PdsFile as PdsFile`. Three things make this a
    strictly neutral change rather than the surface change the entry feared:

    - **The manifest does not move.** `PdsFile` already reached the package
      namespace indirectly, via `from .pds3file import *` / `from .pds4file
      import *`, and `pdsfile.PdsFile is pdsfile.pdsfile.PdsFile` was already
      true. A fresh `dump_public_api.py` before and after is byte-identical at
      733,876 bytes. The import makes explicit a name that was already exported
      by accident of star-import ordering.
    - **The redundant alias is load-bearing.** Written as a plain
      `from ... import PdsFile` the name is unreferenced below and raises
      `F401`, which would have traded one code for another rather than dropping
      one. The `X as X` form is the same explicit-re-export marker
      `preload_and_cache.py` uses.
    - **The absolute form keeps the import order.** Written relatively,
      `.pdsfile` sorts after `.pds3file`/`.pds4file` and isort raises `I001`;
      obeying it would move the core import below the two star imports and
      change which module initializes first.

    `F403` drops from 3 occurrences to 2 — the two remaining are the genuine
    star imports, which stay.

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

    **RESOLVED by PR-22**, which removed the line and rebuilt the inventory
    against `pdsfile.py` plus all ten modules this phase created. The real
    inventory is **eight** lines, not ~89; the same eight are present on
    `rewrite`, so PR-15 through PR-21 neither added nor removed one. Listed
    line by line in `critiques/phase5-validation.md` §7 of the PR-22 section.

### Added by the PR-16 adversarial review (round 4)

33. **`scripts/gen_ruff_ratchet.py` cannot be exercised against the current
    tree.** Its docstring workflow is "re-run this after a shrink and confirm the
    diff only removes codes", but it runs `ruff check` with the project config,
    whose committed `per-file-ignores` already suppress every violation, so it
    emits an empty block. Reproducing a ratchet regeneration therefore requires
    clearing the table first, which the script does not do and does not document.
    Pre-existing and not touched by PR-16; noted because the ratchet is a
    standing §2 gate and PR-23/PR-24 both lean on exactly that workflow when they
    shrink the entries to their enumerated freeze-locked sets. **Owner:** PR-23.

34. **Six pre-existing tracked files carry multi-component fragments of the real
    holdings roots.** §3.4 requires that no absolute holdings path appear in
    committed code, tests, docs, CI or `critiques/` records. Measured by scanning
    every tracked file for any run of two or more consecutive components of
    either root: `tests/pds3file/test_pds3file_whitebox.py`,
    `plans/archive/2026-07-17-modernization-plan.md`,
    `critiques/2026-07-21-unified-mini-holdings-analysis.md`,
    `critiques/pr-02/validation.md`, `critiques/pr-14/round-1.md` and
    `critiques/pr-14/validation.md`. No complete root appears in any of them; the
    longest run is 29 characters, in the archived v1 plan. PR-16 does not touch
    any of these files and cleaning them is outside a pure move PR's goal, so
    they are recorded rather than fixed — but one of them is a **test module**,
    which is the one category where a fragment could also become a portability
    problem rather than only a disclosure one. The scan is a few lines and would
    make a reasonable addition to `run-all-checks.sh` if the owner wants the rule
    enforced rather than observed. **Owner:** owner decision, then PR-24 (records
    and the archived plan) and PR-36 (the test module, via the critique pass).

## From PR-17 (extract the shelf and local-filesystem subsystems, Phase 5)

One entry, raised by the PR-17 adversarial review in round 1. It is not fixable
inside PR-17: it asks for a change to the parent plan's own text, which is the
owner's to make.

35. **The plan's Phase-5 preamble illustrates a base order that the mixin
    convention PR-17 established now rejects.** The preamble writes the technique
    as `class PdsFile(_ShelfMixin, _OpusMixin, …)`. PR-17 fixed the ordering rule
    as **alphabetical by mixin class name, with `object` last** — recorded in
    `plans/2026-07-27-pr-17-subplan.md` §4 and `critiques/phase5-validation.md`'s
    PR-17 §6, and asserted by
    `tests/api/test_mixin_collisions.py::test_the_mixin_bases_are_listed_alphabetically`.
    `_OpusMixin` sorts before `_ShelfMixin`, so the preamble's illustration is in
    the opposite order, and an executor of PR-18–PR-22 who reads only the plan
    will write a class statement the test rejects. The illustration is plainly
    illustrative — it lists two mixins that never arrive in the same PR and ends
    in an ellipsis — so nothing is wrong today; the risk is a wasted round later.

    **This is an owner decision, and it has exactly two one-line forms.** Either
    (a) the alphabetical rule stands: reorder the preamble's illustration and add
    "listed alphabetically" to it, and the test stays as it is; or (b) the rule is
    not wanted: delete
    `test_the_mixin_bases_are_listed_alphabetically` from
    `tests/api/test_mixin_collisions.py` and the class statement keeps whatever
    order each PR appends. PR-17 chose (a) because a class statement cannot be
    written without *some* order, the plan settles none, and an unenforced
    convention is what produces the wasted round; the choice is behaviorally inert
    either way — the mixins are disjoint and no name is shadowed, both asserted by
    the same test file. The decision, with both forms spelled out, is written up
    as a §6.4 addendum:
    `plans/2026-07-27-addendum-phase5-mixin-base-order.md`, which PR-17 cannot
    merge without. **Owner:** owner, before PR-17 merges and PR-18 appends the
    next mixin.

### Added by the PR-17 adversarial review (round 2)

Three entries, all pre-existing conditions of code PR-17 moved byte-for-byte.
A pure move has no licence to change any of them.

36. **`os_path_exists`'s `lru_cache` survives a `SHELVES_ONLY` toggle.** The
    decorator on `_local_fs.py`'s `os_path_exists` keys the cache on
    `(cls, abspath, force_case_sensitive)` only, while `PdsFile.use_shelves_only`
    mutates `SHELVES_ONLY` on the subclasses. An entry computed in one mode is
    returned in the other, and nothing clears the cache on the toggle. The
    suite's two passes each set the mode once at session start, so it does not
    bite there; a long-running consumer that toggles would see it. Pre-existing
    and bit-identical across the move — the decorator line is one of the
    byte-for-byte segments. **Owner:** phase "b" of issue #77, or whichever PR
    next changes cache behavior.

37. **`_get_shelf` discards the exception it is reporting.** `_shelves.py`'s
    `_get_shelf` binds `except Exception as e` and raises
    `IOError('Unable to open pickle file: %s' % shelf_path)` without `from e`, so
    the underlying `UnpicklingError`/`EOFError` is lost and `e` is unused. This
    is the F841 and one of the B904s that `_shelves.py`'s ratchet entry now
    carries, inherited from `pdsfile.py`'s. **Owner:** PR-23, which owns the core
    modules' ruff cleanup.

38. **The two shelf-tree fallbacks are written asymmetrically.** In
    `_local_fs.py`, `os_path_exists`'s "maybe it's in the infoshelf tree" block
    probes with `cls.os_path_exists(...)` — the cached, shelf-aware method —
    while the parallel block in `os_path_isdir` probes with bare
    `os.path.exists(...)`. Both paths are reached only under `SHELVES_ONLY`. The
    difference is at least a missed cache and possibly a behavior difference on a
    path the shelves know about but the file system does not; deciding which is
    correct requires a behavior change, which a move PR may not make. Recorded as
    an observation, not a diagnosis. **Owner:** phase "b" of issue #77.

### Added by the PR-17 adversarial review (round 3)

39. **The `__dict__` and `__weakref__` descriptors have moved off `PdsFile` onto
    its first mixin base.** Measured: on the parent both are in
    `vars(PdsFile)`; on this branch both are in `vars(_LocalFsMixin)` and
    `vars(_ShelfMixin)` and neither is in `vars(PdsFile)`. That is ordinary
    CPython behavior — the descriptors are created for the first class in a
    hierarchy whose instances need them — and nothing observable changes:
    `dir(PdsFile)`, the API manifest, instance `__dict__`, weak references and
    pickling were each checked and are identical. The consequence worth recording
    is that as Phase 5 adds mixins, the descriptors keep migrating to whichever
    base sorts first, so any introspection of the form `'__dict__' in
    vars(PdsFile)` is unstable across the phase's PRs. Nothing in `src/`,
    `tests/`, `scripts/` or either consumer does that today.
    `tests/api/test_mixin_collisions.py` excludes both names from what counts as
    "defined by a mixin", which is why its collision check does not fire on them.
    **Owner:** phase "b" of issue #77.

40. **`test_no_mixin_module_imports_pdsfile_at_module_level` reads literal import
    statements only.** It parses `ast.Import` / `ast.ImportFrom`, so all six
    spellings of a module-level back-import are covered (two of which raise on
    their own anyway), but a dynamic
    `importlib.import_module('pdsfile.pdsfile')` at module level would pass. No
    mixin module has a dynamic import today and none is expected to; tightening
    the check is worth doing only if one grows one. **Owner:** whichever Phase-5
    PR first adds a dynamic import to a mixin module, if any does.

41. **`shelf_lookup`'s sidecar shortcut is dark in the reference holdings root.**
    An info shelf is a `<bundlename>_info.pickle` plus a readable
    `<bundlename>_info.py` sidecar, and `shelf_lookup` reads the sidecar's second
    line for a bundle rather than unpickling the shelf. The limited testing copy
    the goldens are tuned to carries the `.pickle` half only, so that branch is
    never executed by either local pass and only the complete-set nightly reaches
    it. PR-17 compensates for the parse itself with
    `tests/core/test_shelf_sidecar_record.py` (holdings-free) plus a direct run
    against the complete set, but the branch in `shelf_lookup` that *chooses* the
    shortcut remains uncovered locally. Fixing it means either a test that builds
    a whole shelf pair under `tmp_path` or a change to which root CI uses.
    **Owner:** PR-37 (Phase 8), where CI root selection and coverage targets are
    settled.

### Added by the PR-17 adversarial review (round 5) — and by its removal

42. **A mixin module must not import `pdsfile.pdsfile` at import time, and nothing
    checks it.** The Phase-5 preamble pins this ("a mixin module must **not** do a
    module-level `from pdsfile.pdsfile import PdsFile` … any extracted method that
    needs a *class object* uses a **function-local deferred import**"), and PR-17
    is where the rule first has modules to apply to. PR-17 shipped **no** check for
    it: one was written and then removed. That history is the entry's substance,
    so it is recorded plainly rather than summarised away.

    The check was a **voluntary addition** — the plan asks
    `tests/api/test_mixin_collisions.py` for a set-intersection collision check,
    and nothing more. It entered as a *Deferred* item in the PR-17 review's round
    1, which this executor chose to take up rather than defer. It then produced a
    **Major in round 4** (it missed every absolute `from pdsfile.pdsfile import X`,
    a regression introduced while closing a relative-import hole — a silent
    coverage *trade*) and, after that was fixed, another **Major in round 5** (it
    missed an import in a `class` body, plus the `else` branch of
    `if TYPE_CHECKING:` and `match`/`case`). Round 5 measured 56 of 252
    spelling × nesting cells missing. Rounds 4 and 5 were the only rounds of five
    to return a Major, and both were this check. **Removing it is what makes
    §6.6's four-round cap actionable**: the cap exists to surface a mis-scope, and
    the mis-scope was a guard the plan never asked for consuming two rounds.

    **Design note for whoever takes this up — do not patch the AST walk a third
    time.** Both Majors have the same root cause: the AST approach is a *syntactic
    approximation of a runtime fact*, so its case matrix only ever grows. It has
    so far had to learn about relative vs absolute spellings, aliased forms,
    `from . import pdsfile` vs `from .pdsfile import X`, imports nested in
    module-level `try`/`if`/`with`, class bodies (which **do** execute at import
    time), the `else` branch of `if TYPE_CHECKING:`, and `match`/`case` — with
    `__import__`, `importlib.import_module` and star-imports still ahead of it.
    **The robust implementation is behavioral, not syntactic:** import each mixin
    module in a **fresh interpreter, before `pdsfile.pdsfile` is imported**, and
    assert `pdsfile.pdsfile` did not land in `sys.modules`. That cannot be fooled
    by nesting or by spelling, it tests the property the preamble actually cares
    about rather than a proxy for it, and it is shorter than the AST version.

    Note what still catches the loudest cases in the meantime: the two spellings
    that import `PdsFile` *itself* (`from pdsfile.pdsfile import PdsFile` and
    `from .pdsfile import PdsFile`) raise `ImportError … circular import` and fail
    the whole suite at collection, so an executor who writes the obvious wrong
    thing finds out immediately. Only an import of some *other* already-bound name
    out of the core module is silent.

    **Owner: PR-22.** It is the last Phase-5 PR, so the behavioral check would run
    over the **complete** mixin set at the moment that set is finished, which is
    when it means the most; PR-22 already owns "add a module docstring mapping the
    decomposition", and a coherence check on that decomposition belongs with the PR
    that declares it complete; and adding a shared check mid-phase is precisely
    what went wrong here — PR-18–PR-21 would inherit and trust an implementation
    they never reviewed.

    **RESOLVED by PR-22** — `tests/api/test_mixin_import_isolation.py`, 10 ids,
    holdings-free, behavioral exactly as the design note requires. One obstacle
    the note does not anticipate had to be solved and is recorded so nobody
    re-derives it: `src/pdsfile/__init__.py` does `from .pds3file import *`, so
    importing *any* `pdsfile.*` submodule executes the package `__init__` and
    pulls `pdsfile.pdsfile` into `sys.modules` — the naive probe is red for all
    ten private modules, always. The check installs a stub `pdsfile` package (a
    real `ModuleSpec` with `submodule_search_locations`, no `__init__` executed)
    so relative and in-package absolute imports still resolve while the package
    `__init__`'s star-imports do not. One subprocess per module, subjects
    discovered from `PdsFile.__bases__`. Seen red twice, both with the *silent*
    spelling this entry names: a head-placed `from pdsfile.pdsfile import
    repair_case` in `_associations.py` (caught by the subprocess exit code) and a
    tail-placed one in `_properties.py` that raises nothing anywhere and is caught
    **only** by the `sys.modules` assertion. `critiques/phase5-validation.md`
    §16 of the PR-22 section has both.

## From PR-18 (extract the checksum, archive and log path builders, Phase 5)

Three entries, all raised by the executor's own measurements rather than by a
review round. None is fixable inside PR-18: the first two ask for changes to test
files PR-18 does not touch, and the third is a note that PR-23 must carry.

43. **The tool tests exercise the log-path builders but do not pin their value,
    and coverage cannot see them at all.** The parent plan describes PR-18's
    deduplication as "behavior-identical, golden-tested via the tool tests from
    PR-13". Measured three ways
    (`critiques/phase5-validation.md`, PR-18 §8): a per-test-context coverage run
    attributes **no** `tests/holdings_maintenance/` context to any line of
    `_derived_paths.py`, because PR-13's harness runs each tool as a subprocess
    (`tests/holdings_maintenance/support.py:297`) that in-process coverage does
    not follow; the tools nevertheless do call `log_path_for_volume` /
    `log_path_for_volset` / `log_path_for_index` unconditionally in `main()`'s
    loop, which the log files left in each test tree prove; but **no test in
    `tests/holdings_maintenance/` asserts anything about a log filename**, so with
    `_log_path_for` deliberately emitting `.LOGWRONG` and a wrong target segment,
    four tool-test modules still report 31 passed, exactly as unmutated.

    The real regression net is `tests/pds3file/test_pds3file_blackbox.py`'s 41
    log-path ids, and PR-18 shows by mutation that it is a live one. Two things
    are worth carrying forward anyway. **(a)** A tool test could cheaply assert
    the *shape* of the log file it produces — the tools already write it into a
    temporary tree the test owns, so the assertion is a `glob` and a regex, and it
    would make the tools' own use of the log-path builders a value net rather than
    a liveness net. **(b)** More generally, **any future claim of the form "the
    tool tests cover X" cannot be checked with in-process coverage**; it needs
    either `COVERAGE_PROCESS_START` plumbed into `ToolTree.env` or an assertion on
    an artifact. PR-18 chose the artifact, once; a standing answer belongs with the
    tests. **Owner: Phase 6**, which is where those tool files are being edited.

44. **The log-path golden tests stop matching in the year 2100.**
    `tests/pds3file/test_pds3file_blackbox.py`'s 41 log-path cases match the
    embedded time tag with the literal regex `20..-..-..T..-..-..`, so they assert
    the format and the position of the tag rather than its value — which is what
    lets them run without pinning the clock, and PR-18's §9 controls show they are
    sensitive to everything around it. The leading `20` is the only part that is
    not a wildcard, and it is a date assumption in a test rather than in the code:
    `LOGFILE_TIME_FMT` is `'%Y-%m-%dT%H-%M-%S'` and has no such limit. Replacing
    `20..` with `\d{4}` costs nothing and is behavior-neutral, but it is an edit to
    a test file PR-18 does not otherwise touch, and PR-18's gate is an identical
    pass/fail set. **Owner: PR-24**, which already edits the test tree's style.

45. **`A002`'s permanent freeze-locked home is now `_derived_paths.py`, not
    `pdsfile.py`.** The plan's PR-23 section enumerates the freeze-locked
    per-file-ignores core keeps forever and names `A002` as
    "`log_path_for_*(…, dir='')` in `pdsfile.py`, called by keyword `dir='…'` from
    the tools — frozen param name". PR-18 moves those three methods, so all three
    `A002` occurrences move with them: `pdsfile.py`'s entry drops the code and
    `src/pdsfile/_derived_paths.py = ["A002"]` gains it
    (`critiques/phase5-validation.md`, PR-18 §7). Nothing is wrong today — the
    ratchet is a strict split and the union is unchanged — but PR-23 must
    enumerate `A002` against the new file, and an executor working from the plan's
    text alone would look for it in the wrong place and could conclude the
    suppression had been dropped. The same will be true of any other freeze-locked
    code the remaining Phase-5 PRs relocate. **Owner: PR-23.**

### Added by the PR-18 adversarial review (round 1)

46. **The one piece of code PR-18 changes has no holdings-free coverage at all.**
    The hosted lint/no-holdings job runs 80 of the 880 ids and none of them
    reaches `_log_path_for`; the whole regression net for the deduplication is
    `tests/pds3file/test_pds3file_blackbox.py`'s 41 log-path ids, which need
    `PDS3_HOLDINGS_DIR`. So a machine without holdings — which is every stock
    GitHub runner, and every contributor the plan's risk table is about — cannot
    catch a regression in this code, and the gate that runs there would stay green
    through one.

    This is a property of the tests rather than of PR-18: `log_path_for_*` is pure
    string assembly over `self.disk_`, `self.category_`, `self.bundleset_`,
    `self.bundlename`, `self.logical_path` and `cls.LOG_ROOT_`, so it is one of
    the easiest things in the package to test without a holdings tree — an
    instance built by hand with those six attributes set exercises every branch,
    including both `place` values and the `is_index` guard. PR-18 may not add it:
    its gate is an identical pass/fail set, and a new test id is movement.

    **Owner: Phase 6**, alongside entry 43, which concerns the same surface from
    the other direction — the tool tests run this code but assert nothing about
    its output. A single holdings-free test module for the log-path builders would
    close both.

### Added by the PR-18 adversarial review (round 3)

47. **`log_path_for_index`'s docstring first line describes a bundle.**
    `src/pdsfile/_derived_paths.py` opens it with "Return a complete log file path
    for this bundle."; it returns an *index* log path, as its own second line and
    its `is_index` guard both say. The sibling `log_path_for_bundleset` says
    "for this bundle set", so the line is a copy that was never updated. PR-18
    moved the definition byte-for-byte and deliberately did not touch it: a commit
    that edited the text would break the byte-for-byte claim that makes the move
    checkable, and the wording is not a behavior. **Owner: Phase 7** (PR-29–PR-34),
    where `doc_python.mdc` comes into force and the docstrings are revised anyway.

    The PR-18 round-4 review found a second docstring in the same module with the
    same defect, and it belongs to this entry rather than to a new one:
    `dirpath_and_prefix_for_archive` says "Return the absolute path to the
    directory associated with this archive path." and returns the 2-tuple
    `(dirpath, parent)`. Its sibling `dirpath_and_prefix_for_checksum` gets this
    right — "Return tuple (…)". Also moved verbatim, also correctly untouched
    here. The Phase-7 docstring pass should treat `_derived_paths.py` as a file
    with more than one of these, not as a single fix.

### Added by the PR-18 adversarial review (round 4)

48. **The mixin shadowing check looks at `PdsFile` only, not at `Pds3File` /
    `Pds4File`.** `tests/api/test_mixin_collisions.py:89`
    (`test_no_mixin_is_shadowed_by_pdsfile_itself`) intersects each mixin's names
    with `_defined_names(PdsFile)` and stops there. But the subclasses are exactly
    where `PdsFile`'s method surface is extended — `src/pdsfile/pds3file/__init__.py`
    defines `log_path_for_volume` and `log_path_for_volset` as aliases — and they
    are what the maintenance tools instantiate. A name added to a subclass that a
    mixin also defines would silently make the mixin's copy unreachable on the
    class callers actually use: the failure the test exists to catch, one level
    down, where the test cannot see it.

    Measured at PR-18's head: the intersection is **empty** for both subclasses
    against all three mixins, so nothing is broken today and no PR is blocked. The
    test file is PR-17's and is outside PR-18's diff, and PR-18's gate is an
    identical pass/fail set, so strengthening the check would be a new assertion
    in a test PR-18 does not otherwise touch. **Owner: PR-19**, or whichever
    Phase-5 PR next edits the mixin harness — the extension is one more
    intersection per subclass in the same test.

## From PR-19 (extract the OPUS and index-row support, Phase 5)

**Entry 48 is resolved by this PR** — `tests/api/test_mixin_collisions.py` now
carries `test_no_mixin_is_shadowed_by_a_pdsfile_subclass`, parametrized over
`Pds3File` and `Pds4File`, and the intersection is measured empty for both
against all five mixins (`critiques/phase5-validation.md`, PR-19 §11).

49. **The `cls.__bases__[0].__name__ == 'Pds4File'` string sniff is fragile, and
    the plan asks for it to be recorded rather than fixed.**
    `src/pdsfile/_index_rows.py`, inside
    `data_abspath_associated_with_index_row`'s nested `get_keys`, chooses between
    the PDS3 and PDS4 column-name tables by comparing the *name* of a class's
    first direct base against a string literal. It is fragile in three separate
    ways: it breaks for any class whose `__bases__[0]` is not exactly
    `Pds3File`/`Pds4File` (a deeper subclass, or a class that lists a mixin
    first); it silently takes the PDS3 branch for `Pds4File` itself, whose
    `__bases__[0]` is `PdsFile`; and it is invisible to every static tool,
    because the class is named only in a string.

    The plan's PR-19 section is explicit that it must **not** be changed here:
    "an inherited boolean would not be behavior-identical (it would differ for
    `Pds4File` itself and for deeper subclasses), so replacing it here would
    violate the freeze's spirit — record the string-sniff fragility as a
    phase-'b' item instead and move on." PR-19 moved it byte-for-byte and
    verified the premise the plan rests on: `__bases__[0].__name__` is identical
    for all 34 classes in the hierarchy before and after the move, and the
    sniff's verdict is `True` for exactly the same six pds4 rule classes on both
    sides (`critiques/phase5-validation.md`, PR-19 §7).

    The phase-"b" fix is an inherited class attribute (e.g. a private
    `_IS_PDS4` set on `Pds3File`/`Pds4File`) read as `cls._IS_PDS4`, which is
    correct for every class in the hierarchy rather than only for the direct rule
    subclasses. It is an observable behavior change for `Pds4File` itself and for
    any deeper subclass, which is exactly why it is not a phase-"a" change.
    **Owner: phase "b" of issue #77.**

50. **`data_pdsfile_for_index_row` has no in-process test coverage at all, and
    rms-viewmaster calls it three times.** A per-test-context coverage run over
    `tests/pds3file/`, `tests/pds4file/`, `tests/rules/`, `tests/core/` and
    `tests/holdings_maintenance/` attributes **50** distinct test contexts to the
    two modules PR-19 creates and **zero** of them to
    `data_pdsfile_for_index_row` (`critiques/phase5-validation.md`, PR-19 §9).
    Independently: mutating it to always return `None` leaves the suite at 721
    passed, exactly as unmutated (§10). Unlike PR-18's entry 43, this is not the
    subprocess blindness — nothing calls it in-process either.

    It is not dead code. `viewmaster/viewmaster.py:873`, `:1449` and `:1580` call
    it on every index-row page. So the one method in this extraction with no test
    is also one of the two that a live consumer depends on. The method is four
    lines over `data_abspath_associated_with_index_row` (which *is* covered) plus
    `from_abspath`, so a test costs almost nothing.

    PR-19 may not add it: its gate is an identical pass/fail set apart from the
    two ids entry 48 required, and a further new test id is movement.
    **Owner: Phase 6**, alongside entries 43 and 46, which are the same shape.

51. **Four parts of the moved OPUS and index-row code are not pinned by the
    golden tests — measured by mutation, not guessed.** PR-19 ran nine mutations
    that turn tests red and, deliberately, recorded the ones that do not
    (`critiques/phase5-validation.md`, PR-19 §10). Each is 721 passed / 34
    skipped, identical to unmutated, in a full-tree copy that asserted it had
    imported the mutation:

    a. **The `__bases__` sniff's PDS4 branch.** Forced *on*, one test fails;
       forced *off*, nothing does. So the PDS3 side is pinned and the PDS4 side
       is not, on the limited testing copy the goldens are tuned to.
    b. **`opus_products`' cross-PDS sibling discovery.** Replacing
       `PdsFile.__subclasses__()` with `[]` — which drops every cross-PDS3/PDS4
       product — changes no outcome. (The *import* that feeds it is pinned:
       deleting the deferred import gives 39 failures. It is the value that is
       not.) `tests/rules/pds3/test_coiss_xxxx.py:54` skips the golden cases that
       would cover this when the pds4 reproj bundles are absent, which is the
       likely cause.
    c. **`opus_products`' version ordering.** `new_sublists.sort(...,
       reverse=True)` → ascending changes no outcome, so no golden case has two
       versions of one product.
    d. **`data_pdsfile_for_index_row`** — entry 50, listed here for completeness.

    Round 2 of the PR-19 review demonstrated that **(a) is cheap to close**: a
    synthetic index-row object with `row_dicts` holding a PDS4-style column name
    exercises the branch with no shelf and no PDS4 bundle present, so the test
    needs neither the complete holdings set nor the reproj bundles that (b)
    waits on. Round 2 ran that probe against the parent tip and against PR-19's
    head and got byte-identical answers, which is also an independent check of
    the move.

    None is a defect in PR-19: all four are properties of the test suite and all
    four are equally true on the parent branch. They are the honest answer to
    "which parts of this extraction would a regression escape", and (b) is the
    one worth acting on first, because cross-PDS product assembly is what OPUS
    imports. **Owner: Phase 6** for (a), (c) and (d); (b) additionally depends on
    whether the complete holdings set makes those golden cases runnable, so it
    belongs with whoever next revisits the pds3/pds4 cross-product goldens.

52. **18 of the 34 rule modules define a module-level `opus_products` table, one
    namespace away from the mixin method of the same name.**
    `src/pdsfile/pds3file/rules/COISS_xxxx.py:263` and the equivalent line in 17
    other rule modules define `opus_products = translator.TranslatorByRegex([…])`
    at module level, which the rule *class* then consumes as
    `OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS` (`:737`).
    Because the table is a module global and the class attribute is spelled in
    upper case, it never shadows `_OpusMixin.opus_products` — verified: **zero**
    rule modules have an indented `opus_products =`, and the mixin/subclass
    intersection is empty across the whole 33-class hierarchy
    (`critiques/phase5-validation.md`, PR-19 §11).

    Nothing is broken. But the two names differ only in where they are bound, the
    method is now defined in a different file from the class that inherits it,
    and PR-24 already has to do delicate `F811` work in `COVIMS_0xxx.py` for the
    same table-versus-method confusion one level down. A one-line comment at the
    top of the rules' `OPUS_PRODUCTS` blocks, or a rename of the module-level
    table, would remove the trap. **Owner: PR-24**, which is editing these files
    anyway.

### Added by the PR-19 adversarial review (round 1)

53. **The new subclass shadowing check names its subjects instead of discovering
    them.** `tests/api/test_mixin_collisions.py`'s
    `test_no_mixin_is_shadowed_by_a_pdsfile_subclass` is parametrized over the
    literal list `[Pds3File, Pds4File]`, so a *third* direct subclass of
    `PdsFile` would silently go unchecked — the same narrowness entry 48
    described, one step out. Everything else in that module discovers its
    subjects from `PdsFile.__bases__`, which is why every extraction PR inherits
    the checks for free.

    PR-19 chose the literal list deliberately and the choice is defensible today:
    the two subclasses have to be **imported** for `PdsFile.__subclasses__()` to
    see them at all, so a discovery-based version would need the same two imports
    and could then pass vacuously if an import were dropped — which is exactly
    what the test's `assert subclass in PdsFile.__subclasses__()` line exists to
    prevent. The robust form is to import the two packages for their side effect,
    parametrize over `PdsFile.__subclasses__()`, and keep a separate assertion
    that the discovered set is non-empty and contains both. That is a strictly
    better test and it is a change to a test file, not to `src/`, so it costs
    nothing behaviorally — but it would add or rename ids, and PR-19's gate is an
    identical pass/fail set apart from the two ids entry 48 required.

    Round 3 of the PR-19 review added a second half to this entry. The check is
    **strict**: it forbids any name a mixin and a subclass both define, and a
    future PR that moved into a mixin one of the names `Pds3File`/`Pds4File`
    already override would trip it *legitimately*, because that name was shadowed
    before the move too. That cannot happen in the rest of Phase 5 — measured, the
    34 (`Pds3File`) and 35 (`Pds4File`) such names are class attributes and
    translator tables, which the Phase-5 mechanics keep on `PdsFile`, plus
    `__init__`, `__repr__` and the four
    `use_shelves_only`/`require_shelves`/`set_logger`/`set_easylogger`
    classmethods, all of which are on PR-22's explicit stay-list — and the
    measurement is recorded in the test's own comment. But whoever generalizes the
    check should express the invariant rather than the intersection: what is
    actually wrong is a mixin name that is unreachable on the class callers use
    *and* was reachable before.
    **Owner: PR-20**, or whichever Phase-5 PR next edits the mixin harness.

    **PR-20 was directed not to take this up** and did not: the Phase-5
    coordinator ruled that entries 53 and 54 stay open and that PR-20 build no
    new check, which is the scope rule written after PR-17 spent two review
    rounds on a voluntarily adopted Deferred item. PR-20 touches no test file at
    all. It did re-measure the intersection this entry is about, with its two new
    mixins included: empty for `Pds3File`, for `Pds4File` and for all 33 classes
    in the hierarchy. **Owner: unchanged — the next Phase-5 PR that edits the
    mixin harness.**

### Added by the PR-19 adversarial review (round 2)

54. **The mixins' "state contract" docstrings are hand-written, drift, and are
    mechanically derivable.** Each Phase-5 mixin opens with a paragraph naming
    the PdsFile attributes, properties and sibling-mixin methods its bodies
    reach. That paragraph is the only place a reader can learn what a mixin
    depends on, and it is the only part of a mixin module that is *not* checked
    by anything: PR-19's rounds 1 and 2 each found the `_IndexRowsMixin` version
    wrong or incomplete — round 1 that three names it called lazy properties are
    plain instance attributes, round 2 that it omitted two properties, one class
    attribute and one write. Both were fixed by deriving the list from the AST
    instead of writing it; the derivation is about twenty lines.

    `tests/api/test_mixin_collisions.py` cannot catch this: it checks what a
    mixin *defines*, never what it *reads*. A read-side check — walk each mixin
    module's AST for `self.X` / `cls.X`, and assert every name resolves on
    `PdsFile` or on a sibling mixin — would catch both the drifting docstring and
    a genuinely stranded attribute, which is the failure mode the whole "class
    attributes stay on `PdsFile`" rule exists to prevent and which nothing
    currently verifies.

    PR-19 did not build it: the mixin harness is a test file it touches only for
    entry 48, and a new check is a new test id, which its gate forbids beyond the
    two entry 48 required. Building a check the plan did not ask for is also the
    failure mode PR-17 paid two rounds for. **Owner: PR-22**, which adds the last
    and largest mixin (`_PropertiesMixin`) and is where a stranded attribute is
    most likely.

    **Round 3 of the same review found a third instance**, which is the argument
    for treating this as due rather than optional: `_OpusMixin`'s list omitted
    `version_rank`, read as `li[0].version_rank`, because the AST walk that
    produced the list followed `self.X` and `cls.X` but not an attribute on a
    *subscript*. A derivation that runs in a test would have to walk every
    `Attribute` node and resolve the root of its value expression, and would have
    to scope the claim to PdsFile-side names so `str`, `list` and translator
    methods do not swamp it. PR-19's scratch harness now does both and verifies
    both docstrings complete in both directions.

    Round 4 added the last piece such a check will need: it must exclude the
    names the mixin **itself** defines. `_IndexRowsMixin`'s methods call each
    other -- `child_of_index` calls `find_selected_row_key` and `get_indexshelf`,
    `data_abspath_associated_with_index_row` calls `child_of_index`,
    `data_pdsfile_for_index_row` calls it in turn -- so a naive walk reports four
    `self.X` reads that are not external dependencies at all. PR-19's docstrings
    exclude them, which is why they list no method the mixin defines; an
    automated version has to do the same or it will emit four false positives on
    this module alone.

    Round 2 also noted that `_version` appears in `dir(pdsfile)` on this branch
    and not in the manifest. It is a gitignored `setuptools-scm` build artifact
    present in the working tree, identical on the parent branch, and not an
    effect of any Phase-5 PR. Recorded here so a later round does not re-derive
    it; no owner, no action.

### Added by the PR-20 executor's own measurements (2026-07-27)

55. **Four methods PR-20 moved have zero in-process test coverage, and
    rms-viewmaster calls two of them.** A `dynamic_context = test_function`
    coverage run over `tests/pds3file/`, `tests/pds4file/`, `tests/rules/`,
    `tests/core/` and `tests/holdings_maintenance/` attributes 224 distinct test
    functions to `src/pdsfile/_sorting.py` and `src/pdsfile/_associations.py`,
    and **zero** to `sort_sibnames`, `sort_siblings`, `associated_logical_paths`
    and `associated_pdsfiles`. A grep of `tests/` confirms it independently: none
    of the four has a single call site there. Mutating each of them — reversing
    the list `sort_sibnames` hands to `sort_basenames`, truncating what
    `sort_siblings` sorts, truncating either association method's answer — leaves
    the suite at 721 passed.

    Unlike PR-19's entry 50, this is not a "nothing calls it anywhere" finding:
    rms-viewmaster calls `associated_pdsfiles` at seven sites
    (`viewmaster.py:844,1039,1047,1258,1433,1444,1547`) and `sort_siblings` at
    one (`viewmaster.py:1407`), and `sort_siblings` is the only caller of
    `sort_sibnames`. `associated_logical_paths` has no consumer call site in
    either repo but is a frozen public method. So four live pieces of the public
    surface are pinned by nothing but the API manifest, which records a signature
    and not a behavior.

    PR-20 did not fix it: its gate is an identical pass/fail set and any new test
    is a new id. The natural owner is whoever next adds tests to
    `tests/pds3file/` — the four are cheap to cover, since `sort_siblings` and
    `associated_pdsfiles` are thin wrappers over `sort_sibnames` and
    `associated_abspaths`, both of which are heavily golden-tested.
    **Owner: unassigned (a future test PR, not Phase 5).**

56. **Several transformation tests assert a subset, never a length, so a
    truncated answer is invisible to them.** PR-20's negative controls turned up
    seven mutations of *covered* code that changed no outcome. The dominant shape
    is `test_abspaths_for_pdsfiles`, `test_pdsfiles_for_logicals` and their
    whitebox twins, which do

    ```python
    res = pds3file.Pds3File.abspaths_for_pdsfiles(pdsfiles=pdsfiles, must_exist=True)
    for path in res:
        assert path in expected
    ```

    — every returned value must be expected, but nothing asserts that everything
    expected was returned, so replacing the body's return with `[...][:1]` still
    passes. Adding `assert len(res) == len(expected)`, or comparing sorted lists,
    would close it and is a one-line change per test.

    The other five green controls are branch reachability or a caller that never
    looks at a length, rather than assertion strength in the method's own test, and are recorded here so a later round does not re-derive them:
    `split_basename`'s three-group `BUNDLENAME_PLUS_REGEX` return needs a bundle
    name whose split rule leaves it unchanged and no golden case supplies one;
    `sort_basenames`' `labels_after=True` sort key is never exercised;
    `viewable_childnames_by_anchor` and `pdsfiles_for_basenames` are reached only
    through `viewset_lookup`, which never checks a length; and
    `associated_parallel`'s `# This should never happen` return is, as its comment
    says, not reached.

    PR-20 may not act on any of it — its gate is the pass/fail set — and
    strengthening an assertion in a test the PR does not otherwise touch is the
    volunteered-scope failure mode the common brief §5.1 forbids.
    **Owner: unassigned (a future test PR, not Phase 5).**

### Added by the PR-20 adversarial review (round 2)

57. **WITHDRAWN — owner decision, 2026-07-27: absolute holdings paths in plan and
    critique files are not confidential.** The owner's ruling, verbatim: "I don't
    care about absolute paths in plan or critique files. They aren't
    confidential." So **this entry needs no action**: no scrub of
    `plans/archive/2026-07-17-modernization-plan.md` is required, and a reviewer
    should not re-raise it. The measurement below stands as an accurate record of
    what was found and why it looked like a problem at the time; it is simply no
    longer one.

    What the ruling does **not** change: code, tests and CI still resolve holdings
    roots through `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` rather than hardcoding
    them. That requirement stands on portability grounds — a hardcoded root breaks
    on any other machine — and is independent of confidentiality. Nothing under
    `src/`, `tests/` or `.github/` may carry a literal holdings path.

    *The original entry, as written by PR-20, follows.*

    **An archived plan carries a home-rooted holdings path, which §3.4 says no
    checked-in file should.** `plans/archive/2026-07-17-modernization-plan.md`
    contains **two distinct `~`-rooted path tokens, three occurrences in all**,
    naming a machine-local holdings tree. §3.4 is categorical: "No absolute
    holdings path may be hardcoded in committed code, tests, docs, or CI" and
    "The limited copy's location is machine-local and confidential (appears in no
    checked-in file)."

    Measurements that bound it, all made without reproducing the strings:

    - **Both tokens are the immediate parent directory of both current roots.**
      Neither is byte-equal to `PDS3_HOLDINGS_DIR` or to `PDS4_HOLDINGS_DIR`, but
      `os.path.dirname()` of each of those roots **equals** the committed token,
      and each root is the token plus **one** further component. So appending the
      obvious component to what is committed yields the location §3.4 calls
      confidential — for both roots. **This is a disclosure, not stale history.**
      (PR-20's first draft of this entry said "neither token is the current
      root … a stale-history hygiene item rather than a live leak", which was
      true only under literal string equality and would have steered the owner
      wrong. Round 3 of PR-20's review caught it; the correction is the
      measurement above.)
    - Every *other* holdings path in that file is under `/data/pdsdata`, which
      §3.4 names in the open as the complete set and which is not confidential.
    - **It is entirely pre-existing.** The same three occurrences are present at
      `bf42ae7` (PR-20's parent) and on `origin/rewrite`; the file does not exist
      on `origin/main`. No Phase-5 PR introduced it.
    - **No tracked file contains either current root verbatim** — a sweep of every
      file `git ls-files` reports returns zero hits — so this archived plan is the
      only exposure, and it is one component short of exact.

    PR-20 left it alone because it is outside PR-20's diff and pre-existing, and
    because rewriting an archived plan to scrub a path is a change the owner
    should authorize rather than one an extraction PR makes in passing — but it
    should be treated as an actual confidentiality fix rather than filed as
    hygiene. The fix is a one-line substitution to the env-var placeholder in each
    of the three spots.

    **Resolution: the owner ruled on 2026-07-27 that these paths are not
    confidential, so no edit is made and the entry is closed.** It was surfaced by
    PR-20 as an item needing a decision, and the decision is recorded above.

## From PR-21 (extract the preload machinery, Phase 5)

### Added by the PR-21 executor's own measurements (2026-07-27)

58. **`pylibmc` is reachable as `pdsfile.pdsfile.pylibmc` today and as
    `pdsfile._preload.pylibmc` after PR-21 — and on any machine where it is
    reachable at all, the API-freeze gate is already red.** PR-21 moved the
    `try: import pylibmc / HAS_PYLIBMC = True / except ImportError` block out of
    `pdsfile.py` and into `_preload.py`, because `preload` is its only consumer.
    `HAS_PYLIBMC` is a frozen member of `pdsfile.pdsfile`, so it is re-exported in
    the redundant-alias form; `pylibmc` is a *conditionally bound module import*,
    and re-exporting it would need a new `if HAS_PYLIBMC:` statement in
    `pdsfile.py` — new logic rather than a move.

    Measured rather than argued:

    - `pylibmc` is not installed in this environment, so `pdsfile.pdsfile.pylibmc`
      does not exist here on either side of the change.
    - With a stub `pylibmc.py` on `PYTHONPATH`, `HAS_PYLIBMC` becomes `True`,
      `'pylibmc' in vars(pdsfile.pdsfile)` becomes `True`, and
      `scripts/dump_public_api.py` records `"pylibmc": "module"` under
      `pdsfile.pdsfile`. Diffing that dump against the committed
      `tests/api/api_manifest.json` reports **two extra names, both spelled
      `pylibmc`: one under `pdsfile.pdsfile` and one under `pdsfile.pdscache`.**
    - **Only the first is PR-21's, and it is the smaller half.**
      `src/pdsfile/pdscache.py:7` has its own optional `import pylibmc` behind a
      `try`, and `pdsfile.pdscache` is also one of the dumper's seven fixed
      modules (`scripts/dump_public_api.py:37`). Phase 5 does not touch it, and
      re-running the same stub against PR-21's HEAD leaves the diff at **one**
      extra name, under `pdsfile.pdscache`.

    So `pylibmc` is not part of the frozen contract; a machine that has it already
    fails the freeze gate before Phase 5 touches anything, and **still fails it
    after PR-21**, via `pdscache`. Nothing in `src/`, `tests/`, `scripts/`,
    rms-opus or rms-viewmaster refers to `pdsfile.pdsfile.pylibmc`. What the owner
    may want to decide separately: the manifest is environment-dependent for
    optional dependencies — a property of the dumper's `vars(module)` walk rather
    than of any PR — and it means the freeze gate cannot be run on a
    memcached-capable deployment host, whatever Phase 5 does. Any fix has to cover
    `pdscache` as well as `pdsfile.pdsfile`, and editing the dumper or the
    manifest is a §6.4 prohibition for the executor, so this is an owner decision.

    **A third reviewer suggested annotating the exception in the code**, at
    `src/pdsfile/pdsfile.py`'s re-export block, whose comment says the private
    names there "are carried so that no name reachable as `pdsfile.pdsfile.<name>`
    is lost". PR-21 declined, for two reasons worth recording so the next reader
    does not re-derive them. The clause is a *purpose* statement scoped to the
    four private names the sentence introduces (`_GLOB_CACHE_SIZE`,
    `_clean_abspath`, `_clean_glob`, `_needs_glob`), not a global invariant over
    the module — none of the four is `pylibmc`. And the sentence is inherited
    wording, written by PR-16 and extended by PR-17, PR-20 and PR-21 only by
    adding names to its lists, so rewording its claim is a change to another PR's
    prose. If the owner wants the exception visible in the source rather than
    here, that is a one-line edit for whichever PR next touches that block.
    **Owner: unassigned (a freeze/manifest question, not Phase 5).**

59. **Five measured coverage gaps in the preload machinery, none of which PR-21
    may close.** From a `dynamic_context = test_function` coverage run and 19
    mutation controls over the moved code:

    - **`cache_lifetime` is never executed.** Only its `def` line is covered. It
      is passed as `lifetime=cls.cache_lifetime` by the three `pdscache`
      constructions inside `preload`, and every one of those is on a branch the
      suite does not take, so the lifetime function actually in use is the
      module-level `cache_lifetime_for_class` the class bodies hand to their
      class-level `DictionaryCache`. Mutating `cache_lifetime` to return 0 changes
      nothing.
    - **`is_preloading` is never executed and has no caller** anywhere in `src/`,
      `tests/`, `scripts/`, rms-opus or rms-viewmaster. Ground rule 9 keeps it.
    - **`cache_category_merged_dirs` can be made a no-op with no effect on the
      suite**, because `preload` caches the same merged directories itself and the
      session fixture always preloads. Its import-time call is a safety net for
      the never-preloaded case, which nothing tests.
    - **No test asserts a cache lifetime.** `cache_lifetime_for_class` is reached
      by 116 test functions, but returning "forever" for every argument, or moving
      `DEFAULT_FILE_CACHE_LIFETIME` from 12 h to 13 h, leaves the suite green.
    - **No test distinguishes a case-sensitive filesystem from a case-insensitive
      one.** `preload` computes `FS_IS_CASE_INSENSITIVE`; forcing it to the class
      default (`True`) instead of the computed `False` leaves the suite green. The
      flag gates `force_case_sensitive` handling in `_path_utils` and `_local_fs`.

    Separately, **30 of `preload`'s 113 statements and 8 of `get_permanent_values`'
    21 are never executed** (coverage's own statement set, `def` line included) —
    the whole memcached path, the `clear=True` and
    `force_reload=True` paths, the already-preloaded early return, and
    `get_permanent_values`' bundleset/bundle descent. That is not a gap a test in
    this repo can close (it needs a live memcached), and it is recorded so that a
    future reader knows what a green full-data run does and does not prove about
    `preload`.

    PR-21 may not act on any of it — its gate is the pass/fail set, and adding a
    test id is movement.
    **Owner: unassigned (a future test PR, not Phase 5).**

### Added by the PR-21 adversarial review (round 1)

60. **In-class banner rule-line widths in `pdsfile.py` are mixed, and the split
    propagates them into the extracted modules.** Measured over indented
    `#`-only lines — each banner contributes **two** of them, one above its text
    and one below:

    | tree | 80 cols | 84 cols | 90 cols |
    |---|---|---|---|
    | `2df25ab:src/pdsfile/pdsfile.py` | 18 | 2 | 4 |
    | HEAD `src/pdsfile/pdsfile.py` | 20 | 0 | 2 |
    | HEAD `src/pdsfile/_preload.py` | 0 | 2 | 2 |

    At HEAD the two 90-column rule lines are the single banner
    `# Set parameters for both Pds3File and Pds4File`. The parent's other
    90-column banner, `# Preload management`, moved into `_preload.py` with its
    block, which is also where the 84-column pair went — the interior
    `# Interior function to recursively preload one physical directory` banner
    inside `preload`, indented eight spaces rather than four. The banner PR-21
    adds at `src/pdsfile/pdsfile.py:496–498` is 80 columns, matching the file's
    majority and the banner PR-20 added.

    Nothing in force flags this: every line is under `line-length = 100`, and
    `python.mdc`'s formatting rules do not bind before PR-23 (§6.6's progressive
    compliance schedule). A moved banner may not be reflowed either — that would
    be a content edit inside a move commit. Normalizing the widths across the core
    modules is squarely PR-23's "ruff-clean and format core modules" scope, where
    the churn checkpoint puts it in front of the owner along with everything else.
    **Owner: PR-23.**

## From PR-22 (finalize the core, Phase 5)

### Added by the PR-22 executor's own measurements (2026-07-28)

61. **One of the suite's twenty monkeypatch sites is a portability guard whose
    removal is invisible on Linux, so "remove the patch" is not a valid
    forced-wrong control for it.** `tests/core/test_pdsfile_path_resolution.py:92`
    stubs `glob` inside `abspath_for_logical_path.__globals__` so that
    `glob.glob('/Library/WebServer/Documents/holdings*')` — the last-resort MacOS
    website-install branch — returns `[]`. On this machine the real call returns
    `[]` too, so **deleting the stub outright leaves the whole of `tests/core/`
    and `tests/pds3file/` green (531 passed)**, which reads exactly like "this
    patch is dead" and is not what it means. Forcing the stub to answer *wrongly*
    — a non-empty list — does turn
    `TestHoldingsEnvironmentVariable::test_a_class_does_not_borrow_another_class_holdings_root`
    red, which is the control the Phase-5 briefs actually ask for.

    Two consequences worth recording. The mechanical form of the monkeypatch
    audit that PR-17 through PR-21 used — remove the patch, watch the test go
    red — is sound for a patch that supplies a value the code needs, and unsound
    for a patch that *suppresses* a platform-specific value; both forms exist in
    this tree and only this one is of the second kind. And the branch the stub
    guards has **no coverage at all on Linux**: nothing in the suite reaches the
    non-empty-glob path of `abspath_for_logical_path`, on any machine that is not
    a MacOS Viewmaster host. PR-22 may not act on either — its gate is the
    pass/fail set, and adding a test id is movement beyond the ten the entry-42
    check required.
    **Owner: unassigned (a future test PR, not Phase 5).**

### Added by the PR-22 adversarial review (round 1)

62. **`filename_keylen` is the only slot-filling lazy property that never writes
    its filled object back to the cache.** `src/pdsfile/_properties.py` — 40 of
    the mixin's 64 properties fill an `_X_filled` slot, and 39 of those then call
    `self._recache()` so the shared cache keeps the filled object.
    `filename_keylen` assigns `self._filename_keylen_filled` and returns. The
    consequence is the same one PR-15's bug 1 had for `html_path`: every object
    re-fetched from the cache recomputes the value, because the fill never
    reaches the cached copy.

    It is **not** the same defect — `html_path`'s was `self._recache` written
    without its parentheses, a call that silently did nothing, whereas here there
    is no call at all, which may well be deliberate for a value this cheap
    (`FILENAME_KEYLEN.first(self.basename)`, a translator lookup). Deciding that
    needs the same treatment PR-15's bugs got: a regression test pinning the
    intended behavior first, then the change. PR-22 may not act on it — the code
    is byte-identical through the move, its gate is the pass/fail set, and adding
    a test id is movement beyond the ten the entry-42 check required.
    **Owner: unassigned (a future bug-fix PR, with a regression test).**

63. **The back-import guard covers the nine mixin modules and not `_path_utils.py`.**
    `tests/api/test_mixin_import_isolation.py` discovers its subjects from
    `PdsFile.__bases__`, which is what makes it pick up a future mixin for free —
    and which also means the one private module that is not a mixin is never
    probed. `pdsfile.py` imports `_path_utils` at module level exactly as it
    imports the mixins, so a module-level `from pdsfile.pdsfile import <name>`
    there is the same cycle and is unchecked. (Measured: `_path_utils.py` is clean
    today — the same probe run by hand reports `pdsfile.pdsfile` absent.)

    Entry 42's wording is "a mixin module must not import `pdsfile.pdsfile` at
    import time", so covering `_path_utils` is a **widening** of what was asked
    for rather than a gap in what was delivered, and PR-22 did not take it up for
    the same reason it did not take up entries 53 and 54. The robust form is to
    discover every `pdsfile._*.py` module that `pdsfile.py` imports, rather than
    every mixin base. **Owner: whichever PR next edits the mixin harness (with
    entry 53).**

64. **Six lines of commented-out code remain under `src/pdsfile/`, all in
    `pdscache.py`.** `src/pdsfile/pdscache.py:699` and `:1009–1013`, both in
    `MemcachedCache`, are the `self.mc.get_multi(...)` calls that the live
    one-key-at-a-time loops replaced, each under the comment
    `# Memcached->get_multi hangs on long lists; individual requests work fine`.
    PR-22's dead-code scope is `pdsfile.py` plus the ten modules Phase 5 created,
    and `pdscache.py` is neither, so they are out of scope there.

    They are also the one case where "commented-out code" and "a comment that
    documents behavior" are hard to separate: the commented-out call is the
    evidence for the workaround the comment describes, and it sits inside the
    `MemcachedCache`/pylibmc support that ground rule 9 protects and that no test
    in this repo can exercise. Removing them would need an owner decision rather
    than an executor's. **Owner: owner decision, then PR-23 (which is the next PR
    to touch `pdscache.py`).**

### Added by the PR-22 adversarial review (round 2)

65. **RESOLVED — owner decision, 2026-08-03**
    (`plans/2026-08-03-addendum-pr23-24-owner-decisions.md`): the waiver becomes
    an **explicit list of modules** — `pdsfile.py`, `_properties.py`,
    `pdscache.py`, and the rule modules — enumerated rather than described as a
    class, so that adding a file to it is a visible decision. `pdscache.py` stays
    at its current size, waived. Splitting `_properties.py` was rejected because
    it would reopen §8 settled decision 3. Recorded in
    `.cursor/rules/pdsfile_overrides.mdc` (3) and in §6.6's schedule. The
    original entry follows, unaltered.

    **The "modules < 1000 lines" waiver names `pdsfile.py` and the rule modules,
    and Phase 5 has now produced two other files over the line.** §6.6's
    progressive-compliance schedule reads: `python.mdc` "modules < 1000 lines" —
    **permanently waived** for `pdsfile.py` and rule modules. At the end of
    Phase 5, `src/pdsfile/_properties.py` is **1,686** lines and
    `src/pdsfile/pdscache.py` is **1,044**; `pdsfile.py` itself is 1,939 and stays
    inside the waiver by name.

    Nothing is broken: no gate enforces the rule (`ruff` has no such check in the
    project's select set), and `_properties.py`'s size is the direct consequence
    of settled decision 8.3, which puts the whole lazy-property block in one
    mixin. So this is a wording question about the schedule rather than a defect,
    and PR-22 may not answer it — the schedule is part of the plan, and amending
    the plan needs an addendum the owner acknowledges.

    It becomes actionable at **PR-23**, which is the PR that meets both files
    ("ruff-clean and format core modules") and whose churn checkpoint is already a
    mandatory owner decision. Either the waiver is extended to name every core
    module Phase 5 produced, or the owner wants `_properties.py` split further,
    which would be phase "b" work rather than PR-23's.
    **Owner: owner decision, before PR-23's churn checkpoint.**

### Added by the PR-23/PR-24 owner decisions (2026-08-03)

66. **Three maintenance-tool modules are over 1000 lines and are deliberately
    not waived.** Measuring the explicit waiver list for entry 65 turned up files
    the decision was not asked about:
    `src/pdsfile/holdings_maintenance/pds3/pdslinkshelf.py` (**1,779**),
    `src/pdsfile/holdings_maintenance/pds4/pds4linkshelf.py` (**1,274**) and
    `src/pdsfile/holdings_maintenance/pds3/pdsdependency.py` (**1,166**).
    (`src/pdsfile/pds3file/rules/VG_28xx.py` at 1,017 is already covered by the
    rule-module entry.)

    They were left off the waiver on purpose rather than by oversight. **Phase 6
    (PR-25 onward) consolidates the duplicated pds3/pds4 tool logic into
    `_common.py`**, so these sizes are expected to change; waiving them now would
    pre-empt that work with a statement about to stop being true. Nothing is
    broken in the meantime — no gate enforces module length (`ruff`'s select set
    has no such check), so this is a documentation question, not a failing check.

    Whether they end up waived, split, or shrunk by the consolidation is a
    Phase-6 question, answerable once PR-25 has established how much of each file
    is duplication.
    **Owner: Phase 6 (PR-25 onward).**

## From PR-23 (ruff-clean the core modules, Phase 5)

### Resolutions PR-23 owed

- **Entry 33 — resolved as documented, not as fixed.** `gen_ruff_ratchet.py` still
  cannot be exercised against a tree whose committed ignores suppress everything,
  so PR-23 derived the core block by hand: `ruff check` with the template select
  set and **no** `per-file-ignores`. The ratchet's header comment in
  `pyproject.toml` now says this, so the next executor does not discover it again.
  The script itself is untouched. **Still open** as a tooling gap, for whichever PR
  wants to teach it a `--no-ignores` mode.
- **Entry 45 — RESOLVED.** `A002`'s permanent home is `src/pdsfile/_derived_paths.py`,
  and the ratchet and `pdsfile_overrides.mdc` deviation (4) both now say so with the
  three sites (`:263`, `:280`, `:296`) named.
- **Entry 60 — RESOLVED.** The six outlying indented banner rule lines
  (`_preload.py` ×4, `pdsfile.py` ×2, at 90 and 84 columns) are now 80 columns like
  the other 34. Verified as comment-only by tokenizing all fifteen modules before
  and after and comparing the token streams with `COMMENT`/`NL` dropped: 15 files
  compared, 0 differing.
- **Entry 31 — still open, unchanged.** PR-23 fixed `__init__.py`'s `F841` and
  `I001` but did **not** touch the three star imports. `F403` stays in that file's
  ratchet entry. Both readings of `from pdsfile import *` (delete it, or correct it
  to `from .pdsfile import *`) change the frozen public surface, one shrinking and
  one growing, so the owner decision entry 31 asks for is still owed.
  **Owner: owner decision, then PR-24.**
- **Entry 37 — half resolved.** The `F841` half is fixed: `_get_shelf`'s
  `except Exception as e` no longer binds a name it never uses. The `B904` half is
  **not**, and is now a permanent ratchet entry: `raise ... from e` sets
  `__cause__` and `__suppress_context__` and `raise ... from None` suppresses the
  original traceback, so both change what a consumer sees, which §2 forbids in this
  PR. A future PR that adds `from e` — which is the right eventual change — must
  re-bind the name; that is one line. **Owner: phase "b" of issue #77.**
- **Entry 64 — untouched, and deliberately so.** The six commented-out
  `MemcachedCache.get_multi` lines in `pdscache.py` still need an owner decision
  that has not been given, and PR-23 did not remove them. The entry stays open.
  **Owner: owner decision.**

### Added by the PR-23 executor's own measurements (2026-08-03)

67. **`PdsFile.child()` looks a cache entry up and throws it away.**
    `src/pdsfile/pdsfile.py`, in `child()`: the comment reads "Create the logical
    path and return from cache if available", and the code is a `cls.CACHE[...]`
    subscript inside `try/except KeyError: pass` with **no `return`**. The looked-up
    object is discarded, so every `child()` call rebuilds an object the cache
    already holds. PR-23 could only remove the unused binding, not the defect: the
    subscript has an effect (a `DictionaryCache` lookup updates that key's
    bookkeeping) and adding the missing `return` is a behavior change — objects
    would start coming back from the cache instead of being reconstructed — which
    needs its own regression test and its own PR. The subscript is kept as an
    expression statement and the comment now says the result is discarded.
    **Owner: phase "b" of issue #77.**

68. **`version_ranks` returns `None` for a file that does not exist.**
    `src/pdsfile/_properties.py`, in the `version_ranks` property: the
    `if not self.exists:` branch assigned a **local** `version_ranks_filled = []`
    where every sibling branch assigns `self._version_ranks_filled`, so the
    instance slot stayed `None` and the property returned `None` rather than the
    empty list the docstring promises ("a list of the numeric version ranks"). This
    is the `F841` that `_properties.py`'s ratchet entry carried. PR-23 deleted the
    dead local — behavior-identical, since nothing ever read it — and left a comment
    at the site; it did **not** write the instance attribute, because that changes
    what the property returns on an existing input. Same shape as entry 30
    (`repair_case`'s `found`). **Owner: phase "b" of issue #77.**

69. **`_local_fs.py`'s `values` list and its `zip` are now visibly dead weight.**
    In `glob_glob`'s `SHELVES_ONLY` branch, `values = list(shelf.values())` feeds a
    `zip(interior_paths[...], values[...])` whose second element the loop body never
    uses — which is why PR-23 renamed the loop variable to `_value` and added
    `strict=False` rather than deleting anything. Iterating `interior_paths` alone
    would be equivalent (the two lists come from the same dict and cannot differ in
    length) and would drop one full materialization of every shelf value per call,
    but it is a code change rather than a style fix and belongs where the shelf
    read paths are being looked at anyway. **Owner: phase "b" of issue #77.**

70. **`src/pdsfile/tools/show_opus_products.py` still carries an `I001` ratchet
    entry and belongs to no PR.** PR-23's scope is the files directly under
    `src/pdsfile/`, so the `tools/` subpackage is out; PR-24's stated scope is the
    rule modules, the `pds{3,4}file/__init__.py` pair, `re_validate.py` and the
    other `holdings_maintenance/` tools, and does not name `tools/` either. One
    entry, one code. **Owner: PR-24, as the last ruff PR.**

### Added by the PR-23 adversarial review (round 1)

71. **`src/pdsfile/_version.py` carries a real `RUF022` and no gate can see it.**
    The generated file's `__all__` is not sorted, which `ruff check` would report —
    but the file is matched by `.gitignore`'s `**/_version.py`, and ruff respects
    `.gitignore` by default, so `ruff check src/pdsfile tests scripts` never looks
    at it. A lint run over an unpacked sdist, or one passing
    `--no-respect-gitignore`, would fail. PR-23 correctly excluded the file from
    its scope (generated by setuptools-scm's `write_to`, absent from a fresh
    checkout, and not a legitimate ratchet entry), so this is not a PR-23 defect;
    it is a gap between what the gate lints and what a consumer receives. Note that
    a violation count derived by pointing ruff at `src/pdsfile/*.py` in a tree
    where an install has regenerated the file will be one higher than one derived
    in a fresh checkout, which is a trap for the next executor.
    **Owner: whoever owns packaging/CI hardening (Phase 8).**

72. **One `MemcachedCache` method has a test; the rest of the class has no gate.**
    Measured during PR-23: **28 of the 37** lines that PR changed in `pdscache.py`
    are inside `MemcachedCache`, and the full-data suite executes exactly one of
    its methods — `set_multi`, because `tests/core/test_pdscache_set_multi.py`
    builds an instance with `__new__` and a stub client rather than a connection.
    Everything else in the class (`unblock`, `__contains__`, `get_multi`,
    `get_now`, `flush`, `clear`, `block`, …) is executed by no test here and by
    neither consumer smoke check. Ground rule 9 protects the class (Viewmaster
    passes `port=` to `preload`), so it cannot be deleted.

    PR-23 closed most of that gap for its own changes with a scratch differential
    probe that reuses the same `__new__`-plus-stub technique (see
    `critiques/phase5-validation.md`, PR-23 §2), and three changed lines remain
    reachable by nothing — `type(port) is str` in `__init__` and the two `F541`
    fragments inside `except pylibmc.TooBig` handlers, all of which need
    `pylibmc`, which is not a declared dependency. That the probe was easy to
    write is the point: **the stub-client technique already in
    `tests/core/` generalizes**, and a small `tests/core/test_pdscache_memcached.py`
    would give the class a real gate. PR-23 may not add it — its own gate is an
    identical test-id set, and a new test id is movement.

    It is also why PR-23 freeze-locked the two violations that live there
    (`UP031`, `RUF015`) rather than fixing them. Broader than, and related to,
    entries 33 and 64.
    **Owner: phase "b" of issue #77, or whoever revisits the cache layer.**

### Added by PR-23's differential probe of the untested fixes (2026-08-03)

73. **`PdsViewSet.append`'s recursive branch keeps an arbitrary one of the nested
    set's members, and which one is not deterministic.**
    `src/pdsfile/pdsviewable.py`, in `append`:

    ```python
    if isinstance(viewable, PdsViewSet):
        for sub_viewable in viewable.viewables:
            self.append(sub_viewable)
            return
    ```

    The `return` is **inside** the loop, so exactly one member of
    `viewable.viewables` is appended and the rest are dropped. `viewables` is a
    `set` and `PdsViewable` defines neither `__hash__` nor `__eq__`, so it is
    hashed by identity and the set's iteration order depends on where the objects
    landed in memory — it varies from one interpreter run to the next. Measured:
    appending a two-member `PdsViewSet` and reading back the surviving name gives
    `['a']` or `['b']` at random, **five runs on unmodified `rewrite` @ `96e5960`
    produced a-b-a-a-b**, and five on the PR-23 branch produced b-b-a-b-a. The
    behavior is identical in both trees; it is simply not a function of the input.

    PR-23 found this only because it renamed the loop variable (`B020`: the loop
    variable shadowed the iterable it walks) and then diffed the two trees'
    outputs. The rename is behavior-preserving; the defect is older. Dedenting the
    `return` — which is almost certainly the intent — changes what the method does
    and needs its own test.

    Also worth noting for whoever fixes it: an **empty** nested `PdsViewSet` falls
    through the loop and reaches `self.viewables.add(viewable)`, adding the
    *viewset* to a set of viewables, and then raises `AttributeError:
    'PdsViewSet' object has no attribute 'name'` — identically in both trees.
    **Owner: phase "b" of issue #77.**

### Added by the PR-23 adversarial review (round 2)

74. **`MemcachedCache.flush`'s error path calls `.sort()` on `dict_keys`.**
    `src/pdsfile/pdscache.py`, inside `flush`'s `except pylibmc.Error` handler:
    `keys = mydict.keys()` followed by `keys.sort()` raises
    `AttributeError: 'dict_keys' object has no attribute 'sort'`, so the handler
    fails with a second, unrelated error before it logs anything about the first —
    and `failures += keys` after it never runs either. PR-23 edited the two log
    lines that bracket it (the `F541` fixes) and could not repair it: the fix
    changes behavior, which §2 forbids here, and no gate can reach it (entry 72).
    The fix is `keys = sorted(mydict.keys())` plus dropping the separate `.sort()`.
    **Owner: phase "b" of issue #77.**

75. **`_opus.py` now spells the same concatenation two ways. — RESOLVED
    (2026-08-03), by reverting the fix that caused it.**
    As recorded in round 2: `src/pdsfile/_opus.py:246` had become
    `[pdsf, *fmt_pdsfiles]` after PR-23's `RUF005` fix while `:268` stayed
    `sublist = [pdsf] + label_pdsfiles[pdsf.label_abspath]`, which is the same
    shape. ruff does not flag `:268` — `RUF005` fires on `iterable + [literal]`,
    not on `[literal] + name` where the right operand is a subscript — so the file
    disagreed with itself. (The second site is `:268`, not `:271` as round 2's
    record and this entry's first draft said; re-measured 2026-08-03, and it is
    `:268` in `rewrite` @ `96e5960` as well.)

    The owner has since ruled that `RUF005`'s rewrite is not wanted at all
    (2026-08-03). All seven of PR-23's `RUF005` conversions were reverted to their
    `rewrite` spelling and `RUF005` became a permanent, owner-chosen exclusion in
    the ratchet and in `pdsfile_overrides.mdc` deviation (4). `:246` and `:268` now
    read alike again, and no PR will diverge them.

### Added by the PR-23 adversarial review (round 3)

76. **`pdscache.py`'s `flush` carries 6-space and 22-space indentation that no gate
    can see.** `src/pdsfile/pdscache.py`, inside `flush`'s `except pylibmc.TooBig`
    and `except pylibmc.Error` handlers, two blocks are indented off the 4-space
    grid. `python.mdc` forbids it, but ruff's `E1xx` indentation rules
    (`E111`/`E117`) are **preview-gated**, so they are not in the enforced `E` set
    and `ruff check` is silent. PR-23 edited the log lines at both sites (the
    `F541` fixes) and deliberately did not re-indent them, because re-indentation
    is not a violation the ratchet records and would enlarge a diff whose warrant
    is that it changes nothing.

    Recorded because the new ratchet header says the core modules are ruff-clean,
    and a reader may reasonably infer that `python.mdc`'s indentation rule is now
    in force for them. It is not, and enabling `--preview` `E1` anywhere is an
    owner-level decision about the whole tree, not a PR-23 one.
    **Owner: PR-24, or whoever proposes enabling preview rules.**

    **RESOLVED for `pdscache.py` by the owner, 2026-08-04: fix the indentation.**
    PR-24 re-indented both `flush` handlers onto the 4-space grid — the `try` /
    `except pylibmc.TooBig` pair inside the `for` loop and its `if self.logger:`
    body, and the `for key in keys:` body in the `except pylibmc.Error` handler.
    A fifth site in the same file was fixed with them: `class PdsCache:`'s `pass`
    sat at 8 columns.

    Indentation is semantic in Python, so the change is proved rather than
    asserted: `ast.dump(ast.parse(...))` of the file before and after is
    identical. `ruff check --select E1 --preview` on `pdscache.py` goes from 8
    findings to 3.

    The 3 that remain are `E115` on the commented-out `MemcachedCache.get_multi`
    block at `:1034-1036`, which **deferred entry 64 still owns** — those six
    lines need an owner decision that has not been given, and re-indenting a
    block that may simply be deleted is wasted motion.

    **RESOLVED tree-wide by the owner, 2026-08-04: fix all of it.** The same
    sweep over `src/pdsfile tests scripts` had found **112** findings across 23
    files — 56 code-indentation (`E111` 41, `E117` 15) and 56 comment-indentation
    (`E116` 48, `E114` 5, `E115` 3). PR-24 fixed **110** of them, in 22 files and
    473 lines.

    None of the 112 was auto-fixable, and fixing an `E111` means moving the whole
    block beneath it, so the work was done by a re-indenter rather than by hand:
    for each logical line the correct indent is `4 × (its INDENT-stack depth)`,
    and the whole logical line — first physical line and every continuation —
    shifts by the same delta, so alignment under an opening parenthesis survives.
    Physical lines inside a multi-line string are never touched. A standalone
    comment moves with its block when the block moved, and is otherwise aligned
    to the code it introduces.

    Because indentation is semantic, every file carries three proofs, checked
    independently of the tool that made the change: the `ast.dump(ast.parse(…))`
    of each file is identical before and after; the token stream is identical
    with `INDENT`/`DEDENT` dropped; and every changed line differs from its
    predecessor only in leading whitespace, with the line count unchanged. 22 of
    22 files pass all three, and the diff is 473 insertions against 473
    deletions. `ruff check` stays clean — worth checking rather than assuming,
    since shifting a line right can push it past 100 columns; the three files
    whose longest line grew end at 84, 85 and 84.

    The heaviest files are `pdslinkshelf.py` (281 lines — it was indented in
    2-space steps in places), `shelf_consistency_check.py` (45),
    `pds4linkshelf.py` (36), `_properties.py` (25) and `pdsfile.py` (24).

    **`re_validate.py`'s two findings were left at first** — an `E117` at `:149`
    and an `E116` at `:830` — because ground rule 7 and deviation (6) freeze the
    file. **The owner lifted that for whitespace on 2026-08-04**, so they are
    fixed too: 9 lines, same three proofs, and the file's ten-code
    `per-file-ignores` entry untouched. The freeze on its logic stands, and
    deviation (6) now records the exception. **`ruff check --preview --select
    E111,E112,E113,E114,E115,E116,E117` is clean over the whole tree with no
    per-file exemption at all.**

    **The gate is enabled (owner, 2026-08-04).** `run-all-checks.sh` runs it as a
    second `ruff check` invocation, recorded in the plan's §2 gate table and
    `pdsfile_overrides.mdc` deviation (12).

    It is a **separate invocation, not `preview = true` in `pyproject.toml`**,
    because preview mode is not selective: it changes the behaviour of the
    *stable* rules too, and `explicit-preview-rules` governs only which preview
    rules get selected, not that. Measured against a tree the configured gate
    reports clean, `--preview` raises **5,687** findings — 28 `F822`, and
    `RUF012` 33 → 49, `B006` 9 → 12, `RUF005` 4 → 12, among others. Absorbing
    those would be a large ratchet widen, which §6.4 forbids. Naming the seven
    codes keeps the new surface to indentation alone.

    Two things checked rather than assumed. The gate is **non-vacuous**: adding
    two spaces to one statement in `_sorting.py` makes it report `E111` and
    `E112` and `run-all-checks.sh` exit FAILURE. (The first attempt at this
    control mutated a *continuation* line, which `E1` does not check, and passed
    green — the control needed its own control.) And it is clean under **both**
    ruff 0.15.7, the development venv, and 0.16.1, which is what CI resolves
    `ruff>=0.8` to; a preview rule's behaviour can change between releases and
    the two versions are not pinned together.

77. **Whether prose may follow a mechanical fix is not written down anywhere.**
    Round 1's m8 had PR-23 change three `IOError` references to `OSError` in
    `_path_utils.py` comments and docstrings — accurate (`IOError` **is**
    `OSError`), manifest-invisible (`scripts/dump_public_api.py` records names and
    kinds, never docstrings), and a strictly better match for the code after
    `UP024`. But no ruff rule required them, and PR-23's stated scope is
    "`ruff check` only", so an equally reasonable executor would have left them and
    an equally reasonable reviewer could call them scope creep. PR-24 faces the
    same question at much larger scale (the rule modules' docstrings). One line in
    its sub-plan would settle it.
    **Owner: PR-24.**

### Added by the CodeRabbit review of PR #118 (2026-08-03)

78. **`MemcachedCache.unblock` releases a lock it does not own when no logger is
    configured.** `src/pdsfile/pdscache.py`, in `unblock`: both guard clauses put
    their `return` **inside** the `if self.logger:` block rather than beside it.
    On `rewrite` @ `96e5960`, with the original indentation shown by column:

    ```
    466:        if not test_pid:            # 8
    467:            if self.logger:         # 12
    468:                self.logger.error(…)# 16
    471:                return              # 16  <- inside the logger guard
    ```

    So when `self.logger` is `None`, neither guard returns. Both fall through to
    `self.mc.set('$OK_PID', 0, time=0)`, which clears the block — including when
    `test_pid` names **another live process**. A caller that constructed its cache
    without a logger can therefore release another process's lock and let cache
    operations overlap. The second guard (`test_pid != self.pid`) is the dangerous
    one; the first merely double-unblocks an already-unblocked cache.

    **This is pre-existing and PR-23 did not introduce it.** PR-23's `SIM102`
    collapse rewrote the pair as `if not test_pid and self.logger: … return`, which
    is **exactly equivalent** to the original for all four combinations of the two
    conditions, precisely because the `return` was already inside the inner guard.
    The collapse is correct and should stay.

    Surfaced by CodeRabbit on PR #118, which reported it as a Critical defect
    *introduced by* the collapse. That reading is wrong — but the hazard it
    describes is real, and its suggested patch (move each `return` out to the outer
    level, keep only the `logger.error` call guarded) is the correct fix. Applying
    it changes observable behavior, which §2 permits only in the enumerated PRs, so
    PR-23 cannot carry it: `pdscache.py` bug fixes were PR-15's licence (bugs 4 and
    5) and that PR has merged.

    Not covered by any test: `pylibmc` is not installed in this environment, so the
    whole of `MemcachedCache` is dark locally — the same reason PR-15's two
    `pdscache` defects survived to be found by reading. This is a third defect of
    that family.

    **Owner: a PR licensed to change behavior — Phase 6's PR-28 (`errors` fix) is
    the nearest, or a dedicated follow-up. It must add a regression test first, per
    §2.**

### Added by the owner's PR-23 revision corrections (2026-08-03)

79. **Logging calls across `src/pdsfile/` build their message eagerly instead of
    passing lazy `%`-style arguments.** The owner's rule, given on 2026-08-03, is
    that a logging call passes a `%`-style format string and the values as
    *arguments* — `logger.warn('Message: %s', the_message)` — and that f-strings
    belong in exception messages, not in logging calls. PR-23 converted the four
    calls it had itself turned into f-strings (`_preload.py` ×2, `_shelves.py`,
    `pdscache.py`) and swept the rest of the package. It did **not** convert them:
    they are pre-existing and outside a `ruff check` PR's warrant, and `ruff`
    has no rule that reports them (`G004`/`flake8-logging-format` is not in the
    selected set, and would not catch the `+` form anyway).

    Measured with an AST sweep over `src/pdsfile/**/*.py`, excluding the
    generated `_version.py`. The predicate, stated exactly so the count is
    reproducible: an `ast.Call` whose `func` is an `ast.Attribute` with `attr` in
    `{debug, info, warn, warning, error, critical, exception, log, fatal, open,
    close}` and whose receiver, as `ast.unparse`d text, contains `logger`
    (case-insensitive), counted once if its **first** argument is an
    `ast.JoinedStr`, an `ast.BinOp` with `Add` or `Mod`, or a `.format()` call.
    The core figure is stable under three variants of the predicate (first
    argument only, any argument, and dropping `open`/`close` from the method
    set); an independent sweep during review reported **98** rather than 96 for
    the subpackages, and the two extra sites were not identified, so treat the
    subpackage figure as ±2. Nothing in the decision this entry asks for turns on
    it.

    | Area | Sites | `+` concat | f-string | eager `%` |
    |---|---|---|---|---|
    | core, `src/pdsfile/*.py` | **34** | 30 | 2 | 2 |
    | subpackages, `src/pdsfile/**/` | **96** | 33 | 7 | 56 |
    | **total** | **130** | 63 | 9 | 58 |

    Core, by file: `pdscache.py` 20, `_preload.py` 8, `_sorting.py` 2, `_opus.py`
    1, `_properties.py` 1, `pdsfile.py` 1, `pdsviewable.py` 1. Most of
    `pdscache.py`'s are `+`-joined f-string fragments inside `MemcachedCache`,
    which no test here executes (entry 72). The subpackage total is dominated by
    the maintenance tools, which Phase 6 consolidates.

    Two things make this more than a style sweep, and are why it needs a decision
    rather than a mechanical pass:

    - **The messages must keep their `%` pattern.** `pdslogger`'s `log()` reads
      "if there are no substitution patterns (indicated by `%` or `{`) inside the
      message string, a single argument is interpreted as the `filepath`", so a
      conversion that drops the pattern silently turns its value into a path
      suffix instead of raising.
    - **Many of these calls already pass a real second argument that *is* a
      filepath** (`_opus.py:114`, `_properties.py:1582`, `pdscache.py:599`/`:610`,
      and most of the maintenance tools' `logger.error(..., abspath)` calls). A
      conversion has to distinguish a filepath argument from a value argument at
      every site. `pdsviewable.py:529` shows the failure mode already present:
      `logger.warn(f'Missing sizes for icon {icon_name} ({key})', str(missing)[1:-1])`
      has no `%` in the message, so the size list is being rendered through the
      filepath path rather than as a value.

    **Owner: owner decision on scope, then a dedicated style PR — the count is too
    large and too spread out for PR-24, whose warrant is `ruff check` on the
    subpackages.**

### Added by the owner, 2026-08-04

80. **Module-level comments and docstrings still narrate the port instead of
    describing the code.** The rule is the same one that governs every other
    comment: say what the code *is*, not how it got that way. The module headers
    were written during the decomposition and read accordingly.

    `src/pdsfile/pdsfile.py`'s module docstring is the main one. Its concrete
    tells, measured rather than characterised:

    - "re-exports every name it **has ever exported**" (:10) — a claim about the
      past. It re-exports the names it exports; that is all a reader needs.
    - "`preload_and_cache.py` … is **now** a re-export shim over `_preload.py`"
      (:47) — "now" is only meaningful against a previous state.
    - The whole closing paragraph (:80–82): "The split is invisible to a caller's
      code: `pdsfile.pdsfile.<name>` still resolves for every name it resolved
      for **before**, and nothing a caller imports or calls has **moved or been
      renamed**." This is a statement about a migration, not about the module.
    - "**What stays here, and why**" (:51) frames the contents as a residue of an
      extraction rather than as the module's subject matter.

    Elsewhere: `src/pdsfile/preload_and_cache.py:4` ("every name this module has
    **always** exported still resolves here"), and the same "stays"/"still"
    framing in the re-export blocks of `pdsfile.py`, `pdscache.py` and
    `pdsviewable.py`.

    The information in these headers is worth keeping — the module map, the
    mixin mechanics, the reason the `class PdsFile` statement cannot move, the
    reason an unreferenced import must not be deleted. **Only the framing
    changes:** written as description rather than as change history, every one of
    these facts still has a natural form. Rewrite them; do not delete them.

    Deliberately not done inside PR-23: it is a prose pass over fifteen module
    headers, wanted by the owner as its own piece of work rather than folded into
    a `ruff check` PR whose warrant is that it changes nothing. It also overlaps
    Phase 7, which owns docstrings.
    **Owner: owner-directed; Phase 7 (PR-29–PR-34) is the natural home.**

## From PR-24 (`style: ruff-clean rules and remaining files`, Phase 5)

**Line numbers in this block are at PR-24's head**, not at its base, because
these entries are read by the PRs that come after it.

### Added by the PR-24 executor's own measurements (2026-08-04)

81. **`LOGDIRS` is a module-level list that `main()` shadows with a bare local,
    so the "move old logs aside" step never runs.** Three pds3 tools carry the
    same shape: `pdschecksums.py` (`:25` global, read at `:387`, shadowed at
    `:854`), `pdsinfoshelf.py` (`:27` / `:440` / `:878`) and `pdslinkshelf.py`
    (`:29` / `:1393` / `:1727`). In each, `main()` writes `LOGDIRS = []` with no
    `global` declaration, so the appends that follow land on a **local** list;
    `move_old_checksums()` / `move_old_info()` / `move_old_links()`, called from
    `initialize`/`repair`/`update`, then iterate the still-empty module-level
    list and version nothing. The comment above each global — "Holds log file
    directories temporarily, used by `move_old_*()`" — describes an intent the
    code does not implement.

    PR-24 left the `N806` on each local rather than lowercasing it: the uppercase
    spelling is what makes the intended link to the global visible, and renaming
    it would make the shadowing read as deliberate. Adding `global LOGDIRS` is
    the fix and it **changes behavior** — old log files would start being renamed
    to `_v###` — which is outside a style PR.

    **Owner: PR-25 (Phase 6), which consolidates exactly this shared skeleton
    into `_common.py`; it needs an owner decision on whether the versioning was
    meant to run.**

    **DECIDED by the owner, 2026-08-04: the log files should be versioned.** The
    three pds3 tools are the defective copies and the pds4 twins are correct —
    `pds4checksums.py:824`, `pds4infoshelf.py:859` and `pds4linkshelf.py:1217`
    each declare `global LOGDIRS` in the same place.

    The fix is one line per tool. It stays assigned to **PR-25**, not PR-24,
    because it changes behavior: old log files begin being renamed to `_v###`,
    which is a new filesystem side effect that PR-13's tool tests observe, and
    PR-24's gate is an identical pass/fail set with no behavior change permitted.
    Per §2 a behavior change must be pinned by a regression test — here, that the
    second run of a task versions the first run's log rather than overwriting it,
    asserted for a pds3 tool and its pds4 twin so the two stay converged through
    the `_common.py` consolidation.

82. **Deferred entry 79's eager-logging inventory undercounts: it is 132 sites
    and 69 filepath-passing sites, not 130 and 67.** Entry 79 states its
    predicate exactly, and the `attr` set it uses —
    `{debug, info, warn, warning, error, critical, exception, log, fatal, open,
    close}` — omits `pdslogger.PdsLogger.normal()`, which is a real level method
    alongside `blankline`, `ds_store`, `dot_underscore`, `invisible` and
    `hidden`. Re-running the same sweep with the full method set adds
    `pds4checksums.py:119` and `:128`
    (`logger.normal('Selected MD5=%s' % md5, abspath)` and
    `logger.normal('MD5=%s' % md5, abspath)`) — both of which are also
    filepath-passing sites, so both counts move by two. Their pds3 counterparts
    at `pdschecksums.py:118`/`:127` use `logger.info` and were already counted,
    which is what makes the asymmetry easy to miss.

    This does not change entry 79's conclusion or PR-24's disposition; it is
    recorded so the figure a later PR works from is the measured one.
    **Owner: whoever executes the entry-79 conversion.**

83. **`pdsarchives.py` assigned `proceed` six times and never read it.** At
    `8cab66a` the five task functions' return values were bound to `proceed` at
    `:530`–`:542`, and `:554` set it to `False` in the exception handler; PR-24
    removed the six dead bindings and kept every call. Its four sibling tools use
    the same variable to gate a chained follow-on step (`pdschecksums.py:915`,
    `if proceed and args.infoshelf:`), but `pdsarchives` has no such option — its `argparse` block offers only the five task flags,
    `volume`, `--log` and `--quiet`. So the variable is a vestige of the shared
    skeleton rather than a missing feature, and PR-24 removed the dead bindings
    (`F841`) while keeping every call.

    Recorded because the vestige is evidence about how the five tools were
    written, which is the thing PR-25 is consolidating.
    **Owner: PR-25 (Phase 6).**

84. **`test_pds4file_blackbox.py:138` is a duplicate `parametrize` case.**
    `PT014` reports it as a duplicate of the case at index 34 — the same
    `uranus_occs_earthbased/.../u0_kao_91cm_734nm_radius_six_ingress_100m.xml`
    input appears twice in one table. It is permanently excluded in the ratchet
    rather than fixed, because removing a case removes a generated test id and
    PR-24's gate is an identical id set. Whether the duplicate was meant to be a
    different radius or should simply go needs someone who knows the bundle.
    **Owner: a test-content PR, not a style PR.**

85. **`uranus_occs_earthbased.py`'s module-level loop leaves its control
    variables bound as public module attributes.** The loop at `:537` runs at
    module scope, so `bundle_prefix`, `opus_id_prefix_e`, `opus_id_prefix_i` and
    `opus_id_prefix_a` survive it as attributes of
    `pdsfile.pds4file.rules.uranus_occs_earthbased` — and all four are in
    `tests/api/api_manifest.json`. That is why PR-24 could not take `B007`'s
    rename here: `_bundle_prefix` would remove a name the freeze records. The
    names are an accident of writing the loop at module level, not an intended
    API; wrapping the loop in a function would drop all four at once, which is a
    surface change needing sign-off.
    **Owner: owner decision; a natural fit for the Phase 7/8 surface tidy-up.**

### Added by the PR-24 adversarial review (round 1)

86. **`tests/rules/pds3/test_cocirs_xxxx.py`'s two association loops now differ in
    what their failure message reports.** The `F841` fix deleted the unused
    `trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]` from the first
    of two otherwise-identical loops; the surviving loop still builds `trimmed`
    and interpolates it into its assertion message, while the first now
    interpolates the full `abspaths`. The deletion is what `F841` asks for and is
    behavior-neutral — the text only appears on a failure — but it settles a
    pre-existing copy-paste inconsistency in the less informative direction.
    Either both loops should report the trimmed paths or neither should.
    **Owner: a test-content PR.**

87. **`src/pdsfile/pds3file/__init__.py`'s alias comment now introduces one
    method instead of eight.** After the `F811` de-duplication removed the seven
    shadowed definitions, `# Alias, compatible with old function/property names`
    at `:123` sits above `log_path_for_volset` alone, while its twin
    `log_path_for_volume` and the six alias properties live about fifty lines
    below under `# Override functions`. Nothing is wrong — the comment is still
    true of the method it introduces — but the two alias groups would read better
    merged under one heading. Moving code is not a `ruff check` fix, so it
    correctly stayed out of PR-24.
    **Owner: Phase 7 (PR-29–PR-34), which owns docstrings and module structure.**

### Added by the PR-24 adversarial review (round 2)

88. **The pds3 and pds4 tool twins have already diverged on their mutable
    defaults, so two of the nine permanent `B006`s are a divergence rather than a
    shared-skeleton property.** `pdschecksums.py:55` takes `oldpairs=[]` while
    `pds4checksums.py:56` takes `oldpairs=None` and writes `(oldpairs or [])`;
    `pdsinfoshelf.py:45` takes `old_infodict={}` while `pds4infoshelf.py:46`
    takes `old_infodict=None`. The pds4 side has already adopted the
    None-sentinel form that `B006` asks for.

    PR-24's exclusion still holds at the two pds3 sites — passing `None`
    explicitly raises `TypeError` today and would stop doing so, which is a
    behavior change — but the reason given, that the rewrite changes the
    signature a frozen tool reports, is one the pds4 twin already contradicts.

    This matters because **PR-25 consolidates exactly these two function pairs
    into `_common.py`** and will have to choose one signature for each. Choosing
    the pds4 form is the `B006` fix and removes two of the nine.
    **Owner: PR-25 (Phase 6).**

### Added by the PR-24 adversarial review (round 3)

89. **The maintenance tools now spell the same `logger.close()` unpacking three
    ways.** After PR-24's `RUF059` work, nine sites read
    `(fatal, errors, _warnings, _tests) = logger.close()`
    (`pdsarchives.py:558`, `pdschecksums.py:911`, `pdsdependency.py:1155`,
    `pdsindexshelf.py:545`, `pdsinfoshelf.py:935`, `pdslinkshelf.py:1776`,
    `pds4checksums.py:885`, `pds4indexshelf.py:535`, `pds4infoshelf.py:918`);
    two read `(fatal, errors, _, _)` (`pds4archives.py:583`,
    `pds4linkshelf.py:1271`); and `pdsdependency.py:322,347` still read
    `(fatal, errors, warnings, tests)` because those two sites do use the values.

    The two bare-`_` sites already used that spelling at `8cab66a` and carried no
    `RUF059`, so PR-24 had no ruff trigger to touch them and correctly did not.
    The divergence is worth recording because **PR-25 consolidates exactly this
    `finally` block into `_common.py`** and will have to choose one spelling —
    the same situation deferred observation 88 records for the `B006` defaults.
    **Owner: PR-25 (Phase 6).**

### Added by the CodeRabbit review of PR #119 (2026-08-04)

90. **Five exception tests pass vacuously when the call under test returns
    normally.** `tests/pds3file/test_pds3file_whitebox.py` wraps the call in a
    bare `try` and asserts only inside the `except` handler, with no `else` and
    no unconditional failure:

    ```python
    def test_data_set_id_exception(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        try:
            _ = target_pdsfile.data_set_id
        except ValueError as e:
            assert expected in str(e)
    ```

    If `data_set_id` ever stops raising, the handler never runs and the test
    passes green while checking nothing. Measured by walking the module's AST for
    `try` statements with no `else` and no unconditional failure in the body,
    there are five: `:324` (`data_set_id`), `:427` (`from_opus_id`), `:455`
    (`from_opus_id` with a wrong id), `:521` (`find_selected_row_key`) and `:554`
    (`data_abspath_associated_with_index_row`). It is the reason this file carries
    a `PT017` ratchet entry: `pytest.raises` is exactly the construct that makes
    the exception mandatory.

    Pre-existing — the shape is identical at `8cab66a`, and PR-24 changed only
    the `parametrize` argument form and, at `:324`, one `res1 =` to `_ =`. Fixing it means
    either adding an `else: raise AssertionError(...)` to each site or converting
    to `pytest.raises` and dropping the `PT017` entry, both of which change what
    the suite asserts — outside a `ruff check` PR whose gate is an identical
    pass/fail set. Note the sibling tests in `test_pds3file_blackbox.py` already
    use the stronger form (`assert False  # pragma: no cover` after the call), so
    the repair pattern is already in the tree.
    **Owner: PR-36 (the test-suite critique pass), or any PR that revisits these
    modules' assertions.**

91. **Two negative `from_lid` tests are parametrized with an `expected` value
    they never use.** `tests/pds3file/test_pds3file_blackbox.py`
    `test_from_lid_mismatched_lid` (:947) and `test_from_lid_invalid_lid` (:962)
    both take `(input_lid, expected)` and assert only on a fixed substring of the
    error message, so `expected` — in the first case the data-set ID the
    resolution is supposed to disagree with — is dead. The mismatch test would
    pass on a `ValueError` naming any other data-set ID.

    The stronger version asserts `expected` appears in the message; the invalid
    test has no data-set ID in its error contract at all and should simply drop
    the parameter. Both are pre-existing at `8cab66a`; PR-24 touched only the
    `parametrize` argument form. The unused parameter is invisible to the gate
    because `ARG002` is not in the select set.
    **Owner: PR-36, with entry 90 — the two are the same weakness at different
    strengths.**
