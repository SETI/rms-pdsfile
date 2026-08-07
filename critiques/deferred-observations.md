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
   Both PDS4 bundle sets fail, one with `FileNotFoundError` and one with
   `ValueError: row count mismatch`. Pinned by
   `test_pds4_indexshelf.test_initialize_cannot_read_a_pds4_index`.

   **Re-scoped by PR-27, which corrected the diagnosis and left it open.** This
   entry said `pdstable.PdsTable` is "a PDS3 detached-label reader". It is not:
   `PdsTable.__init__` dispatches on `is_pds4_label(label_file)` and builds a
   `Pds4TableInfo` for a PDS4 label. There is no wrong reader to replace, and the
   two failures are two different things, neither of them in this tool.

   * `uranus_occs_earthbased`: the metadata `.csv` files have **no label at all**,
     so `label_abspath` is `''` and the read raises. Shelving them means deciding
     that a PDS4 index shelf is built from the `.csv`'s own header row instead of
     from a label -- a decision about the PDS4 metadata contract. It is also not
     enough on its own: `_index_rows.child_of_index()` builds
     `pdstable.PdsTable(label_file=self.label_abspath, ...)` to turn a shelved row
     number back into a row, so a shelf built without a label could not be read
     back. Any fix spans the tool and the core.
   * `cassini_uvis_solarocc_beckerjarmak2023`: `PdsTable` parses its `.xml`
     correctly as PDS4, and the mismatch is real. The label declares an 885-byte
     header and 35 fields; the file's header line is 1,074 bytes and carries 41
     columns. `PdsTable` seeks 885 bytes in, lands inside line 1, and reads 42
     lines where the label says 41. That is a stale label -- a data repair, or a
     `pdstable` change, not a `pdsfile` one.

   Corroborating: the PDS4 holdings root has no `_indexshelf-metadata/` directory,
   so no PDS4 index shelf has ever been built here either.
   **Owner: open -- a PDS4 metadata-contract decision plus a core change, not a
   tool repair.**
4. **`pds4linkshelf --update` raises against any existing shelf.**
   `generate_links()` is handed the *loaded* shelf as `old_links`, whose values are
   the plain tuples that were pickled, and then dereferences `info.linktext` on
   them — `AttributeError: 'tuple' object has no attribute 'linktext'`. The pds3
   twin merges the same data correctly, so this is pds4-only.

   **RESOLVED by PR-27.** `_linkshelf_common.link_text_of()` reads the link text of
   either shape, which is the idiom the merge step further down the same function
   already used. The pin was inverted to
   `test_pds4_linkshelf.test_update_picks_up_a_new_file`, and two tests were added
   beside it: `test_repair_also_picks_up_a_new_file` and
   `test_update_and_repair_agree_on_the_shelved_links`, the second because
   "`--update` does not raise" is a weak assertion -- `--validate` compares the
   shelf against a fresh scan of the same tree, so a merge that dropped or
   duplicated an entry would still validate clean.
5. **`pdschecksums` and `pds4checksums` never propagate errors into the exit
   code.** Both compute a `proceed` flag from `fatal or errors` and then use it
   only to gate the optional `--infoshelf` chain (`pdschecksums`'s `--infoshelf` chain,
   `pds4checksums`'s `--infoshelf` chain at PR-25's head); neither ends in `sys.exit(status)` the way the
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
   `test_shelf_consistency_check.py`. This entry named **PR-28**, which gives this
   tool a `main()`, as where the layout question had to be answered.

   **PR-28 fixed the typo and left the layout question open.** The two are not the
   same size: the typo is one identifier with a regression test, and teaching the
   walk about `_infoshelf-volumes/` and its siblings is a rewrite of what the tool
   looks for, on a tool nothing in this repository or in the sync scripts currently
   runs. Making that change inside a PR whose subject is three `main()` functions
   would have put the interesting decision — what a modern-layout run should
   *report* — under a heading nobody would look for it under.
   **Owner: open — the layout question needs a PR of its own, and no phase owns
   it.**
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
   targets are set, and PR-28 converts the `shelf_consistency_check` tests to
   in-process `main()` calls, which are measured with no subprocess machinery at
   all. (It leaves `show_opus_products` on subprocesses; that half of this
   sentence was a prediction, and
   `plans/2026-08-07-pr-28-deviation-addendum.md` says why it did not hold.)
   If it is taken up, `COVERAGE_CORE=sysmon`
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
    This entry named **PR-28**, which gives `crlf` a `main()`, as where deciding
    what an empty file should classify as ('OK'? 'BINARY'?) belonged.

    **PR-28 preserved it.** The decision is a behaviour change on a frozen surface
    with no obviously right answer — 'OK' says an empty file has no bad
    terminators, 'BINARY' says it is not text, and a third reading is that the
    tool should report it and move on — and the Phase-6 rule lets output move only
    where keeping it would force duplication or a flag, which this does not. The
    pin is unchanged and inverting it is still what a fix has to do.
    **Owner: open — one of three answers, and no phase owns the choice.**

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

    **Re-derived by PR-28, and the single pass still holds.** PR-28 converted
    `crlf` and `shelf_consistency_check`, not `show_opus_products` (see
    `plans/2026-08-07-pr-28-deviation-addendum.md`), so two tools now run inside
    the pytest process where the original justification assumed none did. The
    justification survives on its merits rather than by inheritance: neither
    migrated tool imports a PdsFile class at all — `crlf` imports `argparse` and
    `sys`, `shelf_consistency_check` adds `os` — so neither can read
    `use_shelves_only`, and `--mode` cannot change what either does. A second pass
    over them would execute byte-identical work, which is what the original
    argument claimed for the subprocess case. `support.HOLDINGS_FREE_TOOLS` is
    that property written down, and it is asserted by both in-process runners.
    The claim expires again if a tool that does read `use_shelves_only` is ever
    moved in-process.

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

    **Two of the three are answered by PR-27: shrunk, not waived.**
    `pdslinkshelf.py` is **471** lines and `pds4linkshelf.py` is **524**, from 1,730
    and 1,224 at PR-27's base — the shared code went into `_linkshelf_common.py`
    (729) and the 536-line `REPAIRS` table into `pds3/linkshelf_repairs.py` (555).
    Both are now comfortably under the limit and neither needs a waiver.
    `pdsdependency.py` is untouched at **1,165** and is the only module left in
    `holdings_maintenance/` over the limit; it has no pds3/pds4 twin, so the
    consolidation this entry was waiting on will never reach it.

    **The third is answered by PR-28 only in the sense that the wait is over.**
    PR-28 closes Phase 6 without touching `pdsdependency.py`, which is still 1,165
    lines: its subject is three scripts that had no `main()`, and splitting a
    1,165-line tool is neither in that subject nor a thing to do on the way past.
    What PR-28 does settle is that the deferral has expired — this entry parked the
    question until the consolidation had shown how much of each file was
    duplication, and for this file the answer is none, because there is nothing to
    consolidate it against. So it is a live question rather than a waiting one:
    waive it, or split it in a later phase. `pdsfile_overrides.mdc` deviation (3)
    now says the same rather than pointing at a phase that has ended.
    **Owner: open — `pdsdependency.py` needs a waiver-or-split decision, and no
    phase currently owns it.**

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

    Three `E115` findings remained after that first pass, on the commented-out
    `MemcachedCache.get_multi` block that **deferred entry 64 still owns**. The
    tree-wide sweep below then re-indented them with everything else; entry 64 is
    about whether those six lines should exist at all, which the whitespace does
    not prejudge.

    **RESOLVED tree-wide by the owner, 2026-08-04: fix the indentation, lift
    `re_validate.py`'s freeze for whitespace, and enable the gate.** The sweep
    over `src/pdsfile tests scripts` had found **112** findings across 23 files —
    `E111` 41, `E117` 15, `E116` 48, `E114` 5, `E115` 3. PR-24 fixes **59**, in
    11 files and 404 lines. `E111`, `E112` and `E113` — the three rules that fire
    on **code** — now measure **zero** across the whole tree.

    None was auto-fixable, and fixing an `E111` means moving the whole block
    beneath it, so a re-indenter did the work: for each logical line the correct
    indent is `4 × (its INDENT-stack depth)`, and the whole logical line — first
    physical line and every continuation — shifts by the same delta, so alignment
    under an opening parenthesis survives. Lines inside a multi-line string are
    never touched.

    **Comments are carried, never re-aligned.** A comment moves by exactly the
    delta of the nearest logical line at its own column, searching forwards first
    and stopping at the first line shallower than the comment, because that line
    ends the block the comment belongs to. If nothing in the block sits at the
    comment's column, the comment does not move. In practice that means comments
    move only inside a block whose code moved: of the 404 lines, 45 are comments,
    all in `pdslinkshelf.py` and `shelf_consistency_check.py`, the two files that
    were indented in 2-space steps.

    Getting there took three wrong rules, and the owner caught the third:

    - the first left comments behind while their block moved, stranding them at
      the old indent;
    - the second pulled every standalone comment to the code grid, which broke 32
      **trailing-comment continuations** — a comment hanging under the trailing
      comment of the line above continues *that* comment and belongs to its
      statement. `pdsfile.py:411-449`, the `__init__` attribute-documentation
      block, was the clearest casualty;
    - the third still re-aligned a comment whose own block had not moved, which
      damaged two more conventions the owner named: an **annotation placed after
      the statement it describes** (`"if c.isdir" is False for volset level
      readme files`, in `pdsarchives.py`, `pdschecksums.py`, `pdsinfoshelf.py`,
      `pds4checksums.py` and `pds4infoshelf.py`) and **commented-out code parked
      at column 0** so it reads as disabled (`pdsinfoshelf.py:155-157`,
      `pds4infoshelf.py:158-160`, `pdscache.py:701-702` and `:1011-1016`,
      `re_validate.py:828`).

    **53 findings remain, and every one is on a comment line** — `E116` 48,
    `E115` 3, `E117` 2. They are the three conventions above. Pulling them to the
    grid is not a fix; it detaches the text from what it documents. This is the
    `ruff format` conflict in miniature: a tool preference against a deliberate
    alignment style, where the style wins.

    **The gate is `E111,E112,E113`** — the three rules that fire only on code.
    `E114`/`E115`/`E116` are their comment-line counterparts and `E117` fires on
    both, so all four are out. The cost is that an over-indented *code* block
    would not be caught by `E117`; there are none today, and the only two `E117`
    findings in the tree are comment continuations
    (`_preload.py:453`, `_properties.py:528`).

    Because indentation is semantic, every file carries proofs checked
    independently of the tool: identical `ast.dump(ast.parse(…))`, identical
    token stream with `INDENT`/`DEDENT` dropped, every changed line differing
    only in leading whitespace, and an unchanged line count — **11 of 11 files
    pass all four**. `ruff check` stays clean, worth checking rather than
    assuming since shifting a line right can cross 100 columns. The heaviest
    files are `pdslinkshelf.py` (276 lines), `shelf_consistency_check.py` (44),
    `pds4linkshelf.py` (31) and `_properties.py` (19).

    **`re_validate.py` is included.** Its `E117` at `:149` is fixed — 7 lines —
    because the owner lifted the freeze for whitespace on 2026-08-04. Its
    ten-code `per-file-ignores` entry is untouched and the freeze on its logic
    stands; deviation (6) records the exception. This is what lets the gate run
    with **no per-file exemption at all**.

    **The gate is a separate `ruff check` invocation, not `preview = true` in
    `pyproject.toml`**, because preview mode is not selective: it changes the
    behaviour of the *stable* rules too, and `explicit-preview-rules` governs
    only which preview rules get selected, not that. Measured against a tree the
    configured gate reports clean, `--preview` raises **5,687** findings — 28
    `F822`, and `RUF012` 33 → 49, `B006` 9 → 12, `RUF005` 4 → 12, among others.
    Absorbing those is a large ratchet widen, which §6.4 forbids.

    Two things checked rather than assumed. The gate is **non-vacuous**: adding
    two spaces to one statement in `_sorting.py` makes it report `E111` and
    `E112` and `run-all-checks.sh` exit FAILURE. (The first attempt at this
    control mutated a *continuation* line, which `E1` does not check, and passed
    green — the control needed its own control.) And it is clean under **both**
    ruff 0.15.7, the development venv, and 0.16.1, which is what CI resolves
    `ruff>=0.8` to; a preview rule's behaviour can change between releases.

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

    **Re-owned (2026-08-07): Phase 6 has ended and PR-28 did not touch
    `pdscache.py`.** This entry named it as the nearest PR licensed to change
    behavior; that PR's licence covered one identifier in one maintenance tool, and
    reaching into the cache from it would have been a behavior change nothing in
    that PR's evidence covered. The question is unchanged and unowned.
    **Owner (superseded): a PR licensed to change behavior — Phase 6's PR-28
    (`errors` fix) was
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

    **Correction (measured 2026-08-04, while fixing it): it is not the log file
    that gets versioned.** `move_old_checksums` (`pdschecksums.py:374-405`),
    `move_old_info` (`pdsinfoshelf.py:428-462`) and `move_old_links`
    (`pdslinkshelf.py:1380-1419`) version the **superseded data file** — the
    checksum file, or the shelf file (`move_old_info` also copies its `.py`
    sidecar; `move_old_links` copies both the `.py` and the `.pickle`) — by
    `shutil.copy`ing it into each directory in `LOGDIRS` as `<name>_v###<ext>`,
    where `###` is one past the highest version already there.
    The copy is a copy, despite the name and despite the "moved from"/"moved to"
    message text; the original stays where it is and is then overwritten by the
    task. The log file of the run is not touched. So the observable change is new
    `_v###` files in the run's log directory, plus two `Checksum file moved …` (or
    `Info shelf file moved …` / `Link shelf file moved …`) lines per run.

    **RESOLVED in PR-25.** `global LOGDIRS` added at `pdschecksums.py:854`,
    `pdsinfoshelf.py:878` and `pdslinkshelf.py:1727`, matching the pds4 twins.
    Pinned by `test_reinitialize_versions_the_checksum_file_it_replaces` in
    `tests/holdings_maintenance/test_pds3_checksums.py` and
    `test_pds4_checksums.py`, which assert the `_v001` copy's name and bytes and
    that a second run adds `_v002` rather than overwriting `_v001`. The pds3 test
    was shown to fail before the fix and pass after it; the pds4 test passed
    before it, which is what proves the test can observe the versioning at all.
    See `critiques/phase6-validation.md`.

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
    the same variable to gate a chained follow-on step (`pdschecksums`'s `if proceed and args.infoshelf:` at
    PR-25's head,
    `if proceed and args.infoshelf:`), but `pdsarchives` has no such option — its `argparse` block offers only the five task flags,
    `volume`, `--log` and `--quiet`. So the variable is a vestige of the shared
    skeleton rather than a missing feature, and PR-24 removed the dead bindings
    (`F841`) while keeping every call.

    Recorded because the vestige is evidence about how the five tools were
    written, which is the thing PR-25 is consolidating.
    **Owner: PR-25 (Phase 6).**

    **CLOSED by PR-25.** Confirmed against `ab1fa3b`: no `proceed` binding remains
    in `pdsarchives.py`, and the shared driver `_common.run_main` calls the task
    function without binding its return value, so the vestige has no home to come
    back to. `pdschecksums`'s `if proceed and args.infoshelf:`'s use is untouched.

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
    shared-skeleton property.** `pdschecksums.generate_checksums` takes `oldpairs=[]` while
    `pds4checksums.py:56` takes `oldpairs=None` and writes `(oldpairs or [])`;
    `pdsinfoshelf.generate_infodict` takes `old_infodict={}` while `pds4infoshelf.py:46`
    takes `old_infodict=None`. The pds4 side has already adopted the
    None-sentinel form that `B006` asks for.

    PR-24's exclusion still holds at the two pds3 sites — passing `None`
    explicitly raises `TypeError` today and would stop doing so, which is a
    behavior change — but the reason given, that the rewrite changes the
    signature a frozen tool reports, is one the pds4 twin already contradicts.

    This matters because the PR that consolidates these two function pairs into
    `_common.py` will have to choose one signature for each. Choosing the pds4
    form is the `B006` fix and removes two of the nine.
    **Owner: PR-26 (Phase 6).** PR-25 migrated only the archives pair, whose
    functions carry no mutable default; both sites are in `pdschecksums.py` and
    `pdsinfoshelf.py`, which PR-26 owns.

### Added by the PR-24 adversarial review (round 3)

89. **The maintenance tools now spell the same `logger.close()` unpacking three
    ways.** After PR-24's `RUF059` work, nine sites read
    `(fatal, errors, _warnings, _tests) = logger.close()`
    (`pdsarchives.py:558`, `pdschecksums.py:911`, `pdsdependency.py:1155`,
    `pdsindexshelf`'s `main()`, `pdsinfoshelf.py:935`, `pdslinkshelf.py:1776`,
    `pds4checksums.py:885`, `pds4indexshelf`'s `main()`, `pds4infoshelf.py:918`, all
    cited at `ab1fa3b`); two read `(fatal, errors, _, _)` (`pds4archives.py:583`,
    `pds4linkshelf`'s `main()`); and `pdsdependency.py:322,347` still read
    `(fatal, errors, warnings, tests)` because those two sites do use the values.

    The two bare-`_` sites already used that spelling at `8cab66a` and carried no
    `RUF059`, so PR-24 had no ruff trigger to touch them and correctly did not.
    The divergence is worth recording because the PR that consolidates this
    `finally` block into `_common.py` has to choose one spelling — the same
    situation deferred observation 88 records for the `B006` defaults.

    **Decided for the archives pair by PR-25:** `_common.run_main` writes
    `(fatal, errors, _warnings, _tests) = logger.close()`, the spelling nine of
    the eleven sites already used. The two archives sites are gone with the
    `main()` bodies that held them, so the count is now eight named-underscore
    sites and one bare-`_` site. Re-cited at PR-25's head, since the six-module
    move renumbered most of them: `pdschecksums`'s `main()`, `pdsdependency.py:1155`,
    `pdsindexshelf`'s `main()`, `pdsinfoshelf`'s `main()`, `pdslinkshelf`'s `main()`,
    `pds4checksums`'s `main()`, `pds4indexshelf`'s `main()`, `pds4infoshelf`'s `main()`, and
    the bare `_` at `pds4linkshelf`'s `main()`.
    **Owner: PR-26/PR-27 for the remaining tools.**

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
    there are five: `:324` (`data_set_id`), `:427` (`from_path`), `:455`
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

## From PR-25 (shared maintenance-tool core, Phase 6)

### Added by the PR-25 executor's own measurements (2026-08-04)

92. **`pds4archives`'s four `*_LIMITS` constants constrain nothing.** The archive
    tools cap their per-file log lines with `{'info': N}` entries --
    `LOAD_DIRECTORY_INFO_LIMITS = {'info': 100}` and its three siblings, now one
    copy at `_common.py`'s archive `*_LIMITS`. But `pdsarchives` writes those lines through
    `logger.info` and `pds4archives` through `logger.normal`
    (`pdsarchives`'s `file_log_level` / `pds4archives`'s `file_log_level` carry the level as
    `file_log_level`), and **`normal` is not `info`**. Measured directly against
    `pdslogger` 3.2.1, four calls under `limits={'info': 2}`:

    | Called | Lines emitted | Closing summary |
    |---|---|---|
    | `logger.info` ×4 | 2, then `Additional INFO messages suppressed` | `2 INFO messages reported of 4 total` |
    | `logger.normal` ×4 | all 4 | `4 NORMAL messages` |

    So `pdsarchives` caps its per-file lines at 100 per scope and `pds4archives`
    emits one line per file with no ceiling, and the three constants
    `pds4archives` appears to be governed by are inert. The level difference is
    also visible in every log line (`| INFO |` vs `| NORMAL |`) and in the closing
    summary, so converging the two is a change to frozen log text, not a cleanup.
    PR-25 preserved both sides exactly rather than picking one.
    **Owner: needs a decision on whether pds4's per-file logging was meant to be
    capped; whichever way it goes, it changes log output.**

93. **`pdsarchives` names its per-volume log file `_links`, not `_archives`.**
    `pdsarchives`'s log-path spec fields passes `'_links'` to `log_path_for_volume`, so a run
    writes `.../HSTN0_7176_links_<timetag>_<task>.log`. Every other pds3 tool
    passes a suffix matching its own kind (`_md5`, `_info`, `_dependency`,
    `_re-validate`) and `pds4archives.py` passes `'_archives'`.

    `pdslinkshelf`'s `main()` passes the same `'_links'` suffix for the same
    volume and the same five task names, which raises the question of a collision.
    Measured: there is none. `_log_path_for` (`_derived_paths.py`'s `_log_path_for`) inserts the
    `dir=` argument as a directory component, and the two tools pass
    `dir='pdsarchives'` and `dir='pdslinkshelf'`, so for one volume and
    `task='validate'` the paths are

    ```
    <disk>/logs/pdsarchives/volumes/HSTNx_xxxx/HSTN0_7176_links_<t>_validate.log
    <disk>/logs/pdslinkshelf/volumes/HSTNx_xxxx/HSTN0_7176_links_<t>_validate.log
    ```

    Different directories, so neither run can overwrite or interleave with the
    other. What remains is a naming inconsistency: the basename of an archive log
    says `links`. Log file paths are frozen behavior, so PR-25 moved the suffix
    across unchanged.
    **Owner: cosmetic, but it is a frozen path -- renaming it to `_archives` needs
    a decision.**

94. **Deviation (4)'s core table enumerates 40 permanent findings where ruff
    reports 39.** Re-derived at `ab1fa3b` the way the deviation says
    (`ruff check` with the project config and `lint.per-file-ignores = {}`), the
    fifteen modules directly under `src/pdsfile/` report **39**, not the 40 the
    table's rows add up to. The row that is off is `__init__.py`, recorded as
    `F403 ×3` at `:10,:12,:13`; ruff reports `F403 ×2`, at `:14,:15`. The line
    numbers moved because the file changed after the table was written, and the
    third star import presumably went with them.

    Nothing is broken: `F403` is still in `__init__.py`'s `per-file-ignores` entry
    and the configured gate passes. It is recorded because the table is what a
    later shrink is measured against, and 2,316 total findings at `ab1fa3b` split
    39 + 2,277, not 40 + 2,277.
    **Owner: whichever PR next shrinks the core group's entries.**

95. **The two `move_old_checksums` twins differ in whether their two log lines are
    forced.** `pdschecksums.py:402,405` (at `ab1fa3b`) passes `force=True` to both
    `logger.info('Checksum file moved from: ' ...)` and
    `logger.info('Checksum file moved to', dest)`; `pds4checksums.py:400,403` (at `ab1fa3b`)
    passes neither. `force=True` bypasses the scope's limits, so under a limits
    dict that caps `info` the pds3 tool still reports the versioning and the pds4
    tool can silently drop it.

    Invisible until PR-25, because the pds3 lines were unreachable: `LOGDIRS` was
    empty, so the loop that emits them never ran. Now that both tools version, the
    divergence is live, and the PR that makes one copy of `move_old_checksums` has
    to choose one.

    **DECIDED (owner, 2026-08-05): `force=True`.** PR-25 moved
    `move_old_checksums` into `_common.py`, so the choice fell here rather than to
    PR-26. Versioning a file is a filesystem mutation, and the report of it should
    not be droppable by a limits cap; `force=True` is also the spelling that was
    already reachable, since the pds3 lines are the ones a run has been emitting
    since the `LOGDIRS` fix. **This is a behavior change on the pds4 side**: a
    `pds4checksums` run inside a scope that caps `info` now reports the versioning
    where before the cap could silence it. Pinned by
    `test_common_versioning.py::TestReportingUnderAnInfoCap`, whose control applies
    the same `{'info': 0}` cap to a shelf mover that does not force and asserts its
    two lines *are* dropped, so the checksum assertion cannot pass by the cap being
    inert. Reverting `force=True` in a scratch copy fails exactly that one test.

### Added by the PR-25 adversarial review (round 1)

96. **`read_archive_info` is still duplicated near-verbatim between the archives
    twins.** 34 statements in `pdsarchives.py`, 31 in `pds4archives.py`, and the
    only genuine divergence is the three-line existence guard at
    `pdsarchives.read_archive_info`'s existence guard (`logger.critical('File does not exist', tarpath)` then
    `return []`). The other two differences — the PdsFile class and the
    `info`/`normal` level — are already carried by `ToolSpec`.

    PR-25 left it alone under its own rule: sharing it would need a flag whose
    only job is to reinstate one side's guard, and forcing either behavior on the
    other tool is an observable change. That is a defensible call for one pair,
    and the plan's target interface leaves the `read_*` functions in the tool
    modules. It is worth revisiting once the other four pairs land and the shape
    of the whole family is visible: a `missing_input_action` spec **callable**
    (not a boolean) would collapse this without a shrug-flag, if the same shape
    recurs.
    **Owner: PR-26/PR-27, once five pairs are on the core.**

97. **`ToolSpec.extra_arguments` is unexercised in PR-25.** It defaults to `()`,
    neither archives tool supplies one, and so `build_arg_parser`'s loop over it
    never has a body to run. It is the plan's named hook for the tool-specific
    flags (`--archives`, `--infoshelf`), and PR-26 is the PR that needs it.
    Recorded so a later coverage or dead-code sweep does not read it as an
    oversight — and so that if PR-26 finds the hook is the wrong shape (those
    flags also gate chained follow-on steps in `main()`, which a flag-declaration
    hook does not reach), replacing it is a deliberate act rather than a surprise.

    **Updated 2026-08-05: the unexercised set is now three fields, not one.** On
    the owner's ruling ("if a future PR is going to need a field, might as well add
    it now") `holdings_sentinel` and `index_ext` joined `ToolSpec`, and neither
    archives tool reads either: `holdings_sentinel` belongs to the checksums and
    infoshelf tools and `index_ext` to the indexshelf tools. Unlike
    `extra_arguments`, these two are *carried* rather than merely defaulted — both
    archives specs give their flavor's value — so a sweep sees a value that is
    constructed and never read, which is the shape a dead-code check flags. The
    `ToolSpec` docstring says so in as many words.
    **Owner: PR-26 (Phase 6).**

98. **`_common.py` already mixes the generic driver with one family's constants,
    and there will be five families.** `_common.py`'s "Archive tools" section
    holds the four archive `*_LIMITS`, the description and help templates, and
    three archive functions, below a generic section holding `ToolSpec`,
    `build_arg_parser` and `run_main`. That follows the plan, whose target
    interface puts `hashfile()` and the three `move_old_<kind>()` functions — each
    belonging to one or two tools, not five — in the same file. At five pairs the
    file becomes the union of five families' constants and helpers.

    The question to settle **before** PR-26 rather than after: does each family
    get a section in `_common.py`, or its own module beside it
    (`_archives_common.py`, `_shelf_common.py`, …) with `_common.py` reduced to
    the genuinely cross-family driver?

    **Updated 2026-08-05: PR-25 has now pre-committed shelf-family code to
    `_common.py`.** The owner's ruling moved `hashfile()`, the three
    `move_old_<kind>()` functions and `LOGDIRS` into it, so the file holds a
    "Checksum and shelf file tools" section serving six tools that are **not** on
    the driver and call neither `run_main` nor `ToolSpec` nor `build_arg_parser`.
    The file now has two disjoint audiences.

    **DECIDED (owner's rule, applied 2026-08-05): one file, a section per family.**
    The owner's rule is to decide by volume — a little code stays in one file, a lot
    splits into separate files beside it. Measured at the final commit,
    `_common.py` is **666 lines** (486 before this round: `+190` when the
    versioning section arrived — `+151` for that section and `+39` for the
    `@dataclass` conversion, the two `ToolSpec` fields with their docstring,
    `log_paths_for` and the imports — and then `−10` when the three versioning
    functions became one), in a 31-line header plus four banner-separated
    sections — tool specification 75, command line 219, archive tools 214,
    checksum and shelf file tools 127.
    **The number the decision turns on is 1,000**, which is not arbitrary:
    overrides deviation (3) holds `holdings_maintenance/` modules to the repo's
    1,000-line module limit and explicitly declines to waive it for them. At 666
    the file is at 67% of its own governing limit, so the volume rule says keep it.

    **And the same number says PR-26 splits it.** The archives family contributed
    214 lines of family-specific code out of a pair that measured 1,155 lines at
    `ab1fa3b`, a rate of 18.5%. The four pairs still to migrate measure 1,687
    (checksums), 1,758 (infoshelf), 2,954 (linkshelf) and 1,086 (indexshelf) lines;
    at that rate they project **~1,400 more lines**, which puts `_common.py` near
    2,100, twice the limit. The linkshelf figure is the softest, because PR-27
    moves the pds3 `REPAIRS` table out to its own data module, but even halving the
    projection crosses 1,000. So the structure is decided and so is the trigger:
    the first family whose extraction takes `_common.py` past deviation (3)'s 1,000
    lines splits it, the driver staying in `_common.py` and each family taking a
    module beside it. On the projection that is PR-26.
    **Owner: recorded, not open. PR-26 executes the split when the measurement
    crosses.**

### Added by the PR-25 adversarial review (round 2)

99. **Nine of the eleven tools build `logfiles` as a `set` and iterate it, so
    their two `Log file:` lines and their two file handlers come out in a
    hash-dependent order.** All of the citations in this paragraph are **at
    `ab1fa3b`**, the state that produced the observation; the code has since moved.
    `_common.py:229` for the archives pair, and the same
    set literal at `pdschecksums.py:836` and `:844`, `pdsinfoshelf.py:860` and
    `:868`, `pdslinkshelf.py:1717`, `pdsdependency.py:1122`,
    `pds4checksums.py:808` and `:816`, `pds4infoshelf.py:841` and `:849`, and
    `pds4linkshelf.py:1210`; `re_validate.py:56` writes `set([…])` for the same
    thing. Each collects the `place='default'` and `place='parallel'` paths into a
    set, then loops over it to build the handlers and to log one `Log file: …`
    line each. The two indexshelf tools are **not** affected:
    `pdsindexshelf.py:489` and `pds4indexshelf.py:475` build a list, which is
    ordered.

    The two paths are equal strings when no log root is configured, so the set
    collapses to one and nothing is visible. **With `PDS_LOG_ROOT` set or `--log`
    given they are two distinct strings, and the iteration order is whatever
    `str.__hash__` gives under that process's `PYTHONHASHSEED`** — it was observed
    flipping between runs of the *baseline* tree, so this is pre-existing and not
    something PR-25 introduced.

    Consequences: "the log text is frozen" is true only up to that permutation;
    two invocations of the same task can disagree on the order of two adjacent
    log lines; and a future golden that captures a two-log run would be flaky.
    PR-25's own tool-run gate pins `PYTHONHASHSEED` so its comparison measures the
    code rather than the hash.

    The fix is one `sorted()` in one shared place now that the archives pair's
    copy has moved into `_common.py` — but it *is* a log-text change, and the six
    other tools still have their own copy — and `re_validate.py` is frozen.

    **Held by the owner on 2026-08-05** for PR-26/PR-27, on the reasoning that
    converging one copy while nine others kept the set would make the tools
    disagree with each other as well as with themselves.

    **RESOLVED the same day, as a consequence of a later ruling rather than a
    decision of its own — the owner should see this.** Ruling (3) of 2026-08-05
    sent all fifteen log-path sites through `_common.log_paths_for`, and one
    function has to return one type. A `set`, which nine of the eleven tools used,
    would have **introduced** hash-dependent ordering into the two indexshelf
    tools, which built an ordered list; there was no way to route all eleven
    through one helper and leave those two as they were. The helper returns an
    ordered list -- the default place first, the parallel place second, the second
    dropped when it equals the first -- which is exactly what the indexshelf pair
    already did, and which removes the nondeterminism from the other nine.

    Measured over five `PYTHONHASHSEED` values, one `--log` invocation of
    `pdschecksums` against a real volume:

    | seed | at `540447f` | at PR-25's head |
    |---|---|---|
    | 0, 1, 2, 4 | `logroot`, `logs` | `logroot`, `logs` |
    | **3** | **`logs`, `logroot`** | `logroot`, `logs` |

    So the order was observably hash-dependent and is now fixed. `re_validate.py`,
    which this entry noted was frozen and therefore out of reach, is included: the
    owner lifted that freeze the same day. The tool-run gate still pins
    `PYTHONHASHSEED`, which now has nothing left to pin down.
    **Owner: recorded, not open. Flagged because the owner had held it.**

### Added by the PR-25 executor's second round of owner rulings (2026-08-05)

100. **The three `move_old_<kind>()` functions are not one function with data
     differences.** Merging the pds3/pds4 twins of each was clean — `move_old_info`
     and `move_old_links` are byte-identical between flavors, and
     `move_old_checksums` needed only the `force=True` decision of entry 95 — but
     collapsing the three *kinds* into one is a different question, and the answer
     is no.

     Two of the three differences are data: the noun in the two messages
     (`'Checksum file'` / `'Info shelf file'` / `'Link shelf file'`), and which
     files are copied alongside (none / `.py` / `.py` and `.pickle`). The third is
     not. The "moved to" line is written two different ways:

     | Mover | Call | Rendered |
     |---|---|---|
     | `move_old_checksums`, `move_old_info` | `logger.info(noun + ' moved to', dest)` | `… moved to: /path` |
     | `move_old_links` | `logger.info(noun + ' moved to ' + dest)` | `… moved to /path` |

     Measured against `pdslogger` 3.2.1: the two-argument form inserts `': '` and
     passes the path as the filepath, so it is also subject to `replace_root`; the
     concatenated form does neither. Collapsing the three would need a flag
     selecting between two call shapes — the shrug-flag the PR-25 sub-plan §2
     forbids — and whichever shape won would rewrite frozen log text for two of the
     three tool families. So `_common.py` holds three functions in one section
     rather than one function with three configurations.

     What *is* collapsible without touching any log text is the ten-line
     version-numbering block the three share verbatim (glob the `_v???` template,
     take the highest, add one).

     **RESOLVED (owner, 2026-08-05): the blocker was lifted and the three are now
     one.** The owner relaxed the log-output freeze precisely so that a difference
     like this one stops forcing duplication (addendum §8). `_common.move_old(path,
     kind)` is one body of **17 statements**, with `next_version_dest()` at **7**
     for the shared version-numbering block, against **76** for the three bodies it
     replaces. What differs between the kinds is a `VersionedFile` record holding a
     noun and a tuple of companion extensions -- data, not control flow, so the
     sub-plan's §2 rule is satisfied rather than waived.

     **The two-argument call shape won everywhere**, including on the "moved from"
     line, which all three previously wrote as a concatenation with the colon baked
     into the message. Two of the three already used it for "moved to"; it renders
     the colon from one mechanism; and it passes the path as the filepath so the
     logger's root replacement applies. The resulting text change is 100 lines in
     two classes, enumerated in `critiques/phase6-validation.md` §5.3 and in
     addendum §8, with zero lines unattributed and no line added or removed.
     Pinned by `TestTheTwoLogLines` in `test_common_versioning.py`; reverting either
     half of the call-shape change fails three ids.

101. **`holdings_sentinel` hard-codes the *name* of the holdings directory.** The
     new `ToolSpec` field carries `'/holdings/'` and `'/pds4-holdings/'`, which is
     what five tools already do inline (`pdschecksums`'s command-line path split,
     `pdsdependency`'s command-line path split, `pdsinfoshelf`'s command-line path
     split, `pds4checksums`'s command-line path split and archives rebuild,
     `pds4infoshelf`'s command-line path split and archives rebuild). Each `partition()`s a command-line path on it and
     exits with `'Not a holdings subdirectory: '` when the separator is absent, and
     the two pds4 tools also rebuild an archives path by concatenating it back.

     So a holdings root whose last directory component is not literally `holdings`
     or `pds4-holdings` cannot be used with those five tools, whatever
     `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` say. The repo's own roots satisfy it,
     which is why nothing has noticed. Recorded because promoting the literal to a
     named spec field makes it look like a configuration point, and it is not.
     **Owner: whichever PR is willing to change what those five tools accept.**

102. **In one file, the versioning report is forced for checksums and droppable for
     shelves.** After entry 95's decision, `_common.move_old_checksums` passes
     `force=True` to both its log lines and `_common.move_old_info` /
     `_common.move_old_links` pass neither — three functions, one section, two
     policies. That is exactly today's behavior on both flavors, faithfully moved:
     the shelf movers' twins agree with each other, so there was no divergence to
     resolve and no licence to change them. But the argument that carried entry 95
     — versioning is a filesystem mutation and its report should not be droppable by
     a limits cap — applies word for word to the two shelf movers, and the
     inconsistency is now visible in a way it was not when the six copies sat in six
     files. Forcing them is a log-text change on four tools.

     **RESOLVED (2026-08-05): `force=True` for every kind.** With the three movers
     collapsed into one function there is one call site for each line, so the
     alternative was a `force` field on `VersionedFile` whose only job would be to
     re-create one side's behavior -- the shrug-flag the sub-plan's §2 rule forbids
     and the owner's 2026-08-05 ruling tells us not to pay for. Entry 95's reasoning
     applies unchanged: versioning is a filesystem mutation and its report should
     not be droppable by a limits cap. Invisible outside a capped scope, which is
     why no line of the real-holdings gate moved; pinned by
     `TestReportingUnderAnInfoCap`, which now covers all three kinds and whose
     control emits an unforced line in the same kind of scope and asserts it is
     dropped.

103. **`move_old_links` copies the shelf file twice, to the same destination.** It
     runs `shutil.copy(shelf_file, dest)` and then, as its `.pickle` sidecar step,
     `shutil.copy(pickle_src, pickle_dest)` — and the shelf file *is* the `.pickle`,
     so `pickle_src == shelf_file` and `pickle_dest == dest`. The second copy
     overwrites the first with identical bytes. Harmless, and the versioned output
     is the `.pickle` and `.py` pair the linkshelf tests already assert; recorded
     because the redundancy is only visible with the two flavors' copies merged into
     one, and because the obvious "fix" (dropping the sidecar step) would be wrong
     if a shelf file ever stops being a `.pickle`.

     **Carried into the merged function unchanged**, and now visible as data rather
     than as code: `LINK_SHELF.companions` is `('.py', '.pickle')`, and the
     `.pickle` entry names the shelf file itself. The `move_old()` docstring says
     so. Still a redundant copy; still not worth removing blind.

     **Looked at again by PR-27 and left alone.** The link shelf tasks moved into
     `_linkshelf_common.py` and still call `move_old(link_path, LINK_SHELF)`; the
     redundancy is entirely inside `move_old`, which this PR did not touch. The
     reason not to drop the `.pickle` companion is unchanged and is now the thing
     the versioned pair is asserted on:
     `test_pds3_linkshelf.test_update_versions_the_shelf_file_it_replaces` requires
     both a `_v001.pickle` and a `_v001.py` in the log directory, and the `.py` only
     gets there through the companion loop. Dropping the `.pickle` entry alone would
     be safe today and wrong the moment a shelf file is not a `.pickle`.
     **Owner: open.**

### Added by the PR-25 adversarial review (round 5)

104. **The log time-tag fix reaches one of the eleven tools, and two of the other
     ten are not scheduled to inherit it.** PR-25 fixed the one-second race by
     pinning the tag inside `_common.log_paths_for`, which only the archives pair
     reaches. Measured at PR-25's head, `grep -n "place='parallel'" src/` reports
     **15 sites at `540447f`**: `_common.py`'s `log_paths_for`, fixed, and **14 in
     ten tool modules**, not —
     `pdschecksums`'s two `main()` branches, `pdsinfoshelf`'s two `main()` branches, `pdslinkshelf`'s `main()`,
     `pds4checksums`'s two `main()` branches, `pds4infoshelf`'s two `main()` branches,
     `pds4linkshelf`'s `main()`, `pdsindexshelf`'s `main()`, `pds4indexshelf`'s `main()`,
     `pdsdependency`'s `main()` and `re_validate.validate_volume`.

     Eight of those ten reach `run_main` in PR-26 and PR-27 and inherit the fix
     then. **Two do not.** The plan's PR-25 entry leaves `pdsdependency`
     "**left as a standalone tool this phase**", and ground rule 7 with overrides
     deviation (6) freezes `re_validate.py`. So on the current plan two tools keep
     the race indefinitely.

     The two indexshelf tools are the sharpest case. They do not build a set; they
     build a list and dedupe it explicitly:

     ```
     if logfiles[0] == logfiles[1]:
         logfiles = logfiles[:-1]
     ```

     That comparison is string equality between two paths that each carry their own
     reading of the clock, so on a straddling second it is False when it should be
     True and the tool writes **one run's log twice into one directory**, under two
     names a second apart. Every other tool's `set` has the same defect for the
     same reason; the indexshelf pair is where the intent to dedupe is written down
     and defeated.

     **RESOLVED (owner, 2026-08-05): fix all fifteen now.** Every one of the ten
     tool modules now calls `_common.log_paths_for(pdsf, method, *args, **kwargs)`,
     which reads the clock once, builds both paths under that one tag, and returns
     them as an ordered list with the duplicate dropped. `grep -n "place='parallel'"
     src/` now reports **one** site, inside that helper.

     That includes the two the plan was never going to reach: `pdsdependency.py`,
     which Phase 6 leaves standalone, and `re_validate.py`, whose freeze the owner
     lifted the same day. Making the ten call the shared helper, rather than
     sprinkling `_pinned_log_timetag()` blocks through them, was the owner's
     instruction and it is also what removed the last `set([...])` from
     `re_validate.py`.

     The indexshelf dedupe now works: `log_paths_for` compares two paths built from
     **one** clock reading, so equal paths are equal. Pinned by
     `TestTheIndexshelfDedupe` in `tests/core/test_log_path_timetag.py`, whose
     control builds the pair the way the tool used to under a clock that advances a
     second per reading and asserts the two paths differ -- so the test cannot pass
     by the race failing to fire.
     **Owner: recorded, not open.**

105. **`scripts/check_runtime_imports.py` covers seven core modules and the two
     rules packages; it never imports a maintenance tool.** `_TOP_MODULES` lists
     `pdsfile`, `pdsfile.pdsfile`, `pdsfile.pdscache`, `pdsfile.pdsviewable`,
     `pdsfile.preload_and_cache`, `pdsfile.pds3file` and `pdsfile.pds4file`, plus
     everything under the two `rules` packages. Nothing under
     `holdings_maintenance/` is in the set, so a tool that grows an import outside
     the runtime dependencies passes the clean-install gate untouched.

     Now that `re_validate.py` imports cleanly — PR-25a — extending the gate to the
     tool modules is finally *possible*: before PR-25a, importing that one module
     ran a command line and called `sys.exit()`, so the gate could not have
     imported it at all. It is still not *free*: the tools import `pdslogger` and
     `translator`, and whether every one of those is a runtime dependency rather
     than a dev extra is a measurement nobody has made. Extending the gate can
     therefore legitimately turn CI red, which makes it its own measured change
     rather than a rider on this PR.
     **Owner: open.**

106. **Nine tool modules still carry a private `LOGROOT_ENV = 'PDS_LOG_ROOT'` and
     their own copy of the log-root resolution block.** `pdschecksums.py:24`,
     `pdsindexshelf.py:26`, `pdsinfoshelf.py:27`, `pdslinkshelf.py:25`,
     `pdsdependency.py:24`, `pds4checksums.py:25`, `pds4indexshelf.py:26`,
     `pds4infoshelf.py:27` and `pds4linkshelf.py:26`, each above the same five
     lines that read the variable and fall back to `None`.

     PR-25a extracted those five lines as `_common.resolve_log_root()` and pointed
     `run_main` and `re_validate` at it, so there are two callers today. The other
     nine are not this PR's to change — the brief forbids touching another tool
     module except where a shared constant moves — and PR-26 and PR-27 retire them
     as they migrate each tool onto `run_main`. This entry exists so that the count
     is on the record: if either of those PRs lands and the grep still finds nine,
     something was missed.
     **Owner: recorded, not open.**

107. **`re_validate` batch mode cannot handle a holdings root whose path contains
     a space.** `volume_abspath_from_log()` recovers the volume path from a log's
     first record as `parts[-1].strip().split(' ')[-1]` — the last
     whitespace-separated token. A path with a space in it is silently truncated to
     its final component.

     This is not hypothetical on this machine: `/seti/opus/pdsdata/holdings`
     resolves to a Dropbox path containing three spaces, and the tool intersects
     each log's recovered holdings prefix against the **realpath** of the
     command-line root. Measured at PR-25a's head, a log naming the resolved path
     yields the prefix `rfrench@rfrench.org/Shared/Shared-OPUS/pdsdata/holdings`,
     which matches nothing, so the missing-volume report stays silent whatever the
     logs say. PR-25a's B2 fix had to be demonstrated against a synthetic
     space-free holdings root for exactly this reason.

     The fix is not obvious and is not PR-25a's: the log's first record is written
     by `pdslogger` as `Re-validate <abspath>` with no quoting or delimiter, so
     recovering the path reliably means changing what is written, which changes a
     log format that older logs are already in. Anything that reads existing logs
     has to cope with both.

     **The same split has a second consequence, in the opposite direction.** Batch
     mode holds the holdings roots twice: `resolve_holdings_paths()` returns the
     canonicalized, deduplicated list, and that is what the missing-volume report
     intersects against — but `get_volume_info()` is called over the raw
     `args.volume` entries, so `holdings_info` and everything downstream of it carry
     the path *as the user typed it*. Naming one root twice globs it twice, and the
     abspath a batch run reports is not the abspath the report compares against.

     Identical at PR-25a's base and head; that PR did not introduce it and did not
     change it. Iterating the resolved list instead looks like a one-line fix and is
     not one: on a machine where the holdings root is a symlink, the canonical path
     is a different tree, and `Pds3File.from_abspath` has to recognize it as a
     holdings root for `--batch-status` to print anything at all. Which of the two
     forms is the right one to carry is the same question as the paragraph above,
     and should be settled once for both.
     **Owner: open.**

108. **`re_validate --batch` with no log root at all crashes with a `TypeError`.**
     Batch mode reads the existing logs with `get_all_log_info(args.log)`, and
     `args.log` is `None` when neither `--log` nor `PDS_LOG_ROOT` is set — that is
     what `_common.resolve_log_root` leaves. `os.walk(None)` then raises
     `TypeError: expected str, bytes or os.PathLike object, not NoneType`.

     Measured at PR-25a's base and at its head, against a holdings directory with
     an empty `volumes/`, with `PDS_LOG_ROOT` removed from the environment:

     ```
     $ python -m pdsfile.holdings_maintenance.pds3.re_validate --batch-status <holdings>
     base  rc=1  TypeError: expected str, bytes or os.PathLike object, not NoneType
     head  rc=1  TypeError: expected str, bytes or os.PathLike object, not NoneType
     ```

     Identical at both, so PR-25a neither introduces nor fixes it; it is recorded
     because that PR's review is what found it. Interactive mode is unaffected — it
     never reads the log root as a directory to walk.

     Not obviously a one-line fix. Batch mode's whole scheduling model is "read the
     logs, find what is stale", so with no log tree there is nothing to schedule
     from and every volume looks unvalidated. Whether the right behavior is to
     refuse with a message, or to treat it as "no logs yet" and validate
     everything oldest-first, is a decision about how the launch daemon should
     behave on a fresh install, not a defect with one obvious repair.
     **Owner: open.**

### Added by the PR-26 executor's own measurements (2026-08-06)

109. **The pds4 `--infoshelf` chain re-runs `pds4checksums`, not `pds4infoshelf`.**
     Both checksums tools build the chained command by rewriting their own argv:
     `[a.replace('pdschecksums', 'pdsinfoshelf') for a in sys.argv]`. The pds4 tool
     carries that line **verbatim from its pds3 twin**, and `'pdschecksums'` is not
     a substring of `'pds4checksums'` — `pds4c…` breaks the run of characters. So
     no element is rewritten, `--infoshelf`/`-i` is stripped, and the child is the
     same `pds4checksums` command over again with the chain flag removed:

     ```
     '/venv/bin/pdschecksums'.replace('pdschecksums', 'pdsinfoshelf')
         -> '/venv/bin/pdsinfoshelf'          # pds3: the other tool
     '/venv/bin/pds4checksums'.replace('pdschecksums', 'pdsinfoshelf')
         -> '/venv/bin/pds4checksums'         # pds4: itself
     ```

     `pds4checksums --initialize --infoshelf <bundle>` therefore runs the checksum
     task twice and never builds an info shelf; the second run's
     "Checksum file already exists" error is what it reports.

     Identical at PR-26's base and head. It was **not** fixed here: the plan
     enumerates PR-26's behavior changes and this is not among them, and rewriting
     the substitution changes what the pds4 chain *does* rather than how faithfully
     it reports. The migration deliberately left both tools' substitution strings
     alone. Whether the fix is `'pds4checksums'` → `'pds4infoshelf'` or dropping
     argv[0] rewriting for an explicit console-script name is worth settling once
     for both flavors, since argv[0] rewriting also assumes an installed console
     script — `python -m …` puts a module file path there and the chain then
     depends on that file's executable bit and shebang.
     **Owner: open.**

110. **`PYTHONPATH=<other tree>/src` does not redirect pytest's in-process
     imports, so the obvious differential probe silently measures the wrong tree.**
     `pyproject.toml` sets `pythonpath = [".", "src"]`, and pytest prepends those to
     `sys.path` **ahead of** `PYTHONPATH`. Measured from inside a test run as
     `PYTHONPATH=<base>/src:<work> pytest …` from the work tree:

     ```
     sys.path[:5] = ['<work>/tests', '<work>', '<work>/src', '<work>', '<base>/src']
     pdsfile.__file__ = <work>/src/pdsfile/__init__.py
     ```

     A plain `python -c "import pdsfile"` with the same `PYTHONPATH` resolves to
     `<base>`, which is what makes this easy to get wrong: the check that proves
     the tree is honest outside pytest and misleading inside it. Tests that shell
     out (`support.run_tool`, which runs `python -m <module>` in a subprocess) *are*
     redirected, because the subprocess never sees pytest's insertion. So a probe
     run this way exercises base for subprocess tests and head for in-process ones,
     in the same session, with nothing in the output saying so.

     PR-26's first base probe was wrong for this reason and was redone. Recorded
     because every future PR that wants "do my new tests fail at base?" will reach
     for the same command. The reliable forms are to run pytest **from** the base
     worktree with the head's test files, or to assert the measured path inside a
     test.
     **Owner: recorded, not open — but worth a line in the plan's gate section.**

111. **The pds4 tools identify themselves as their pds3 twins, in help text, in
     one error message, and in their log directory.** `pds4checksums --help` begins
     `pdschecksums: Create, maintain and validate MD5 checksum files…`, its missing
     task error is `pdschecksums error: Missing task`, and both its log root
     subdirectory and its per-target log directory are `pdschecksums/`. Same for
     `pds4infoshelf` and `pdsinfoshelf`. That is the behavior at base, it is not new,
     and PR-25 already carried it forward for the archive pair by giving
     `pds4archives` `progname='pdsarchives'`. PR-26 does the same for these four, so
     the logs of a PDS3 and a PDS4 run still land under one directory name and can
     collide only by holdings root, not by tool.

     It is now a **single, visible piece of data** — one `progname` field per spec —
     rather than five hand-copied strings per tool, so changing it is a one-line
     decision per tool rather than a hunt. Not changed here: the log directory name
     is a path that existing installations and the sync scripts already use.
     **Owner: open.**

112. **Two `ToolSpec` fields are carried by the checksum and shelf specs and read
     by nothing.** `index_ext` is declared for the indexshelf tools, which are not
     on the core yet (this is the standing case entry 97 records). `file_log_level`
     is different: it is *accurate* for these four tools — pds3 logs its per-file
     lines through `logger.info` and pds4 through `logger.normal` — but their domain
     functions hard-code the call rather than reading the spec, because those
     functions stayed in the tool modules. So the field states a true fact that the
     tool it describes ignores.

     Making the domain functions read it is not free: `generate_checksums` and
     `generate_infodict` would each need the spec threaded in, which is a bigger
     change than PR-26's scope and touches the functions the plan says to leave
     alone. Recorded so that a later PR can either wire it up or narrow the field's
     documented scope, rather than a sweep finding it and deleting it.
     **Owner: open.**

113. **Ten identical copies of `BACKUP_FILENAME`.** `_common.py` defines it, and so
     do all nine tool modules — `pdschecksums`, `pdsinfoshelf`, `pdsindexshelf`,
     `pdslinkshelf`, `pdsdependency` and their pds4 counterparts. Measured at PR-26's
     head: **one distinct pattern across ten definitions**, character for character:

     ```
     r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d' r'|backup|original)\.[\w.]+$'
     ```

     `_archives_common.load_directory_info` imports the `_common` one; every tool's
     own `generate_*` uses its local copy. PR-26 did not consolidate them: the
     copies live in the domain functions that stay in the tool modules, and
     replacing a module-level constant that nine files define is a sweep of its own,
     not a side effect of migrating four `main()`s. The risk it carries is the usual
     one for a duplicated constant — nine of the ten can be updated and the tenth
     left behind, with no gate that would notice.

     **Eight, not ten, from PR-27.** Both index shelf tools defined one and neither
     thin module does; the two link shelf tools still do, because each tool's own
     `generate_links` reads it. The sweep itself is still owed.
     **Owner: open.**

114. **`_shelf_common.py` serves two audiences, which is the question entry 98
     answered only for `_common.py`.** The split PR-26 performed put the checksum and
     shelf family's code in `_shelf_common.py`: the versioning helpers
     (`move_old`, `next_version_dest`, `VersionedFile`, `LOGDIRS`, `hashfile`) plus
     the new selection driver (`run_selection_main`, `resolve_holdings_paths`,
     `expand_selection_targets`, `modtimes_agree`). Measured at PR-26's head, six
     tool modules import it, but only four of them — the two checksums and the two
     infoshelf tools — are on the driver. `pdslinkshelf` and `pds4linkshelf` import
     it for `LINK_SHELF` and `move_old` alone, and call neither the driver nor
     `ToolSpec`.

     That is the same shape entry 98 flagged before the split: one file, two
     disjoint audiences. It is not urgent — the file is 529 lines against a limit of
     1,000 — but PR-27 migrates the linkshelf and indexshelf pairs and will add to
     it, so the measurement should be taken again there. If it crosses, entry 98's
     rule applies unchanged, and the natural seam is the one already visible: the
     versioning and hashing helpers serve six tools regardless of driver, while the
     driver serves four.

     **Re-measured by PR-27.** With both of this PR's families in it,
     `_shelf_common.py` measured 1,827 lines, so entry 98's rule fired and it split
     by family: `_shelf_common.py` 523, `_indexshelf_common.py` 620,
     `_linkshelf_common.py` 729. The two disjoint audiences are still there and the
     file is smaller than when this entry was written: 523 lines holding the
     versioning helpers six tools reach regardless of driver, plus
     `run_selection_main` and its two path helpers, which four tools use. The link
     shelf tools now reach it for `LINKSHELF_LOGNAME`, `LINK_SHELF`, `move_old` and
     `UNIT_LOG_PATH_METHOD` only. Nothing forces a second split; the seam this entry
     named is where it would go.
     **Owner: recorded, not open.**

115. **`pdschecksums` and `pds4checksums` still exit 0 after logging errors.**
     `support.TOOLS_WITHOUT_EXIT_STATUS` records this and PR-13's tests assert it:
     a `--validate` that reports checksum mismatches exits 0. PR-26 **preserved it
     deliberately**. The shared driver returns its status rather than exiting, and
     each tool decides: `pdsinfoshelf`/`pds4infoshelf` call `sys.exit(result.status)`,
     the two checksums tools do not, exactly as before.

     Preserved rather than fixed because it is pinned current behavior that the plan
     does not enumerate as a PR-26 change, and because changing it would change the
     exit code of every failing checksums run — the most externally visible thing
     these tools do, and something a sync script or a cron wrapper may depend on.
     The one change PR-26 did make here is adjacent and enumerated: a **chained**
     `pdsinfoshelf` run's exit code now reaches the caller intact, where
     `os.system`'s wait status previously truncated every failure to 0. So
     `pdschecksums --infoshelf` now reports the chained run's failure while still
     not reporting its own.

     Giving these two tools an exit status is now a two-line change in one place
     each, and `expected_error_exit_code()` is the single point the tests would move
     through.
     **Owner: open.**

### Added by the CodeRabbit review of PR #123 (2026-08-06)

116. **`archive_filter()` archives the backup files `load_directory_info()` skips.**
     In `_archives_common.py`, `load_directory_info()` skips any name matching
     `BACKUP_FILENAME` or containing `' copy'`, and `archive_filter()` — the filter
     the archive writers add members through — does not. So a volume holding
     `FOO_2021-01-01T00-00-00.LBL` or `BAR copy.TXT` has that file written into the
     tarball but left out of the directory listing, and `validate_tuples()` then
     reports it as `Missing from directory`.

     Both functions moved verbatim into `_archives_common.py` in PR-26's split and
     are otherwise untouched by it; the divergence is at PR-26's base and at its
     head alike. Not fixed here because it changes what the archive tools *write*,
     which is neither a PR-26 scope item nor an enumerated behavior change, and
     because the right repair is not obvious: excluding them changes existing
     archives' contents on the next `--repair`, while including them in the
     directory listing changes what `pdschecksums` and `pdsinfoshelf` record.
     **Owner: open.**

117. **`validate_tuples()` enters its mismatch branch on a `dirpath` difference and
     then reports nothing.** `_archives_common.py`: the branch is
     `elif (dirpath, nbytes, modtime) != tardict[abspath]:`, and inside it only
     `nbytes` and `modtime` are compared. If the archive-relative path is the only
     thing that differs, the branch runs, logs no error, leaves `valid` True, and
     `del`etes the entry — so an archive whose member path is wrong validates
     clean. Moved verbatim in PR-26's split; present at base and head alike.
     Not fixed here for the same reason as 116: the archive family is not this PR's
     scope, and adding an error changes the archive tools' observable output.
     **Owner: open.**

118. **The `--archives` help text reads "refer to the the archive file".** All four
     tools carried that duplicated word before PR-26, in four hand-copied copies;
     PR-26 replaced them with one shared constant and **kept the typo deliberately**,
     because reproducing the help text exactly is what makes all four tools'
     `--help` output byte-identical to base, which is the check that the shared
     constants did not quietly reword anything. Now that it is in one place, fixing
     it is a one-character decision rather than a four-file sweep — but it is a
     user-visible text change and so wants to be made on purpose rather than folded
     into a refactor.
     **Owner: open.**

119. **The chained-run substitution rewrites every argument, not just `argv[0]`.**
     Both checksums tools build the chained command as
     `[a.replace('pdschecksums', 'pdsinfoshelf') for a in sys.argv]`. The intent is
     to name the other tool in `argv[0]`, but the comprehension rewrites the
     substring wherever it appears — so `--log /var/logs/pdschecksums` becomes
     `--log /var/logs/pdsinfoshelf`, and any holdings path containing the tool's
     name is silently redirected. A log root named after the tool is the documented
     layout: `--help` says logs are created inside the "pdschecksums" subdirectory
     of each log root.

     Present at PR-26's base and head alike; PR-26 changed how the command is
     *executed* (`subprocess.run` on a list, an enumerated fix) but deliberately
     left what is *substituted* alone, since narrowing it changes which directory a
     chained run reads and writes. This is the same line as entry 109, so both
     should be settled together: restricting the substitution to `argv[0]` fixes
     this one, and naming the target tool explicitly per flavor fixes 109.
     **Owner: open.**

### Added by the PR-26 adversarial review (round 2)

120. **The modification-time tolerance was inclusive, so an exactly-one-second
     change was reported as no change.** As PR-26 first implemented it,
     `_shelf_common.modtimes_agree()` returned True when
     `abs((t1 - t2).total_seconds()) <= MODTIME_TOLERANCE`, with the tolerance at 1.
     That was the form the plan prescribed (`> 1` is an error) and the form
     `_archives_common.validate_tuples` has always used on epoch seconds. Measured
     end to end on a pds3 tree at that point, a label whose modification time moved
     by exactly 1.0 s:

     ```
     shift +1.0 s   exit 0, no modification-time error
     shift +1.5 s   exit 1, Modification time mismatch "…12:27:01" "…12:27:00"
     ```

     For **pds4** this is a detection the previous truncation would have made: two
     times exactly a second apart always fall in different whole seconds. So the
     class PR-26 stopped reporting is not purely false positives, as the PR
     description originally implied — it is `|Δ| ≤ 1 ∧ floor(t1) ≠ floor(t2)`,
     which is mostly boundary-straddle noise but includes exact whole-second
     shifts.

     **RESOLVED (owner, 2026-08-07): the boundary is strict.** `modtimes_agree()`
     returns True only when the difference is **less than** the tolerance, so a
     change of exactly one second is a mismatch again. Implemented in PR-26 before
     it merged; the parametrized boundary cases flip and
     `test_the_boundary_is_exclusive` pins it in both directions.

     The reasoning is not "strict is tidier", and it disposes of the consistency
     argument above rather than overruling it. That argument was that
     `validate_tuples()` allows a full second inclusively and the two should agree.
     But the two compare **different operands**. `validate_tuples()` puts a
     tarfile's whole-second modification time against a filesystem time carrying a
     fraction, so up to a second of slack genuinely exists and must be forgiven.
     Both operands in `modtimes_agree()` come from one generator at microsecond
     precision — `dt.strftime('%Y-%m-%d %H:%M:%S.%f')` — so the only discrepancy to
     forgive is sub-second. Strict forgives all of that and still catches a real
     one-second change, which on a filesystem storing whole seconds is the
     **typical** size of a real change rather than an edge case. The two boundaries
     differ because their operand pairs differ; that is a justified difference, not
     an inconsistency, and both the code comment and the plan now say so.

     The change also repairs a claim that was overstated in PR-26's brief and
     inherited by its record: that the new mismatch set was a strict subset of the
     old containing only false positives. Under `<=` the removed class was
     "one second apart **or less**", which included real one-second changes. Under
     `<` it is "strictly under one second apart", and the claim is true as stated.
     Measured over 300,000 random pairs at the strict head: 0 subset violations,
     and the largest difference among the reports the change removes is 0.999992 s.
     **Owner: resolved, not open.**

121. **A subprocess-based tool test used to exercise whichever `pdsfile` was
     installed, so a green run proved nothing about the tree it ran in.** Entry 110
     records the in-process half of this trap. The subprocess half is worse,
     because it is silent in both directions: `support.ToolTree.env` passed the
     ambient environment through without naming a `PYTHONPATH`, so
     `support.run_tool()` and `run_console_script()` launched tools that imported
     whatever the interpreter resolved — for an editable install, the tree that was
     installed rather than the tree under test. Measured in the PR-26 worktree
     before the fix, with no `PYTHONPATH` set:

     ```
     $ pytest tests/holdings_maintenance/ -q
     7 failed, 269 passed        # the installed tree's defects, not this tree's
     $ PYTHONPATH=$PWD/src pytest tests/holdings_maintenance/ -q
     276 passed
     ```

     PR-26 closed it: `ToolTree.env` now sets `PYTHONPATH` to `REPO_ROOT/src`, so a
     tool subprocess runs the code its tests belong to, and the no-`PYTHONPATH` run
     above is green. That also makes the in-process and subprocess halves agree,
     which is what entry 110's split-brain was.

     The consequence for entry 110 is that the **only** reliable differential probe
     is now to run pytest **from** the tree being probed, with the other tree's test
     files copied in — `REPO_ROOT` is derived from the test file's own location, so
     that form pins itself correctly. PR-26's own base probe was redone that way.
     **Owner: recorded, not open.**

## From PR-27 (migrate the indexshelf and linkshelf pairs, Phase 6)

### Added by the PR-27 executor's own measurements (2026-08-07)

122. **A stubbed collaborator hid a real break, for the second time in this
     subsystem.** The migration left the four thin tool modules with a task *table*
     and no task *names*, and `re_validate.validate_one_volume()` reaches
     `pdslinkshelf.validate()` by attribute. The full `--mode ns` data suite ran
     green in that state — 1,047 passed, 34 skipped — and so did
     `run-all-checks -c -s`. Nothing could have caught it: every test that drives
     `validate_one_volume` replaces all five sibling tools with `SimpleNamespace`
     stubs, which is what lets those tests run without holdings and is also what
     makes them silent about whether the real functions exist.

     Fixed here — each module binds its five tasks under the names it carries them
     as a library, and `test_re_validate.py` gains
     `test_the_sibling_tools_really_accept_what_this_module_calls_them_with`, which
     binds each of the seven calls against the real modules. The general shape is
     what is left open: `re_validate` is not the only module in this tree that
     stubs a collaborator wholesale, and a stub that outlives its subject is
     invisible to every gate. Entry 121 is the same failure mode one level down —
     a subprocess importing a different tree — and the fix is the same in kind: one
     test that exercises the real thing, however narrowly.
     **Owner: open.**

123. **The rate deferred entry 98 recorded is not a property of the migration.**
     Entry 98 projected family-specific shared code at 18.5% of a pair's combined
     line count and used that to decide where `_common.py` would split. Measured
     across the three Phase-6 migrations: 18.5% (archives, the entry's own basis),
     12.0% (checksums + infoshelf, PR-26), 33.4% (indexshelf + linkshelf, PR-27).
     It ran high for one PR and short for the next — entry 98 projected 748 lines
     for PR-27's two pairs and the measurement is 1,349, so the projection missed by
     601 lines, 45% of what was there.

     The reason is visible in the two pairs PR-27 migrated: the index shelf pair was
     almost identical between flavors (57.1% of its 1,086 lines became shared code),
     and the link shelf pair was not (24.7% of 2,954), because `generate_links` is
     the one function where a PDS3 label and a PDS4 label genuinely say different
     things. How much of a pair can be shared depends on how alike its two flavors
     happen to be, which is not something a rate carries. Entry 98's *rule* — split
     when a measurement crosses 1,000 lines — held up both times; its *projection*
     did not, either time.
     **Owner: recorded, not open. Whichever PR migrates a pair next measures its
     own rather than projecting.**

124. **`link_targets()` filters a unit set's non-directory children out of the
     target list, where the two link shelf `main()`s kept them in and skipped them
     in the loop.** The blank line between targets is emitted when there is more
     than one target, so a unit set holding one unit directory plus a readme file
     loses that blank line.

     **Measured over the wrong population first.** The original count here — "0 of
     54 unit sets have a non-directory child, so no line of the transcript moves" —
     covered `volumes`, `calibrated` and pds4 `bundles`, and left out `metadata`,
     which is one of the three voltypes a link shelf run is pointed at
     (`re_validate.py:44`, and `update_holdings_for_new_metadata.sh:40` runs
     `pdslinkshelf --initialize` on `metadata/$VOLSET`). Re-measured over every
     category `link_targets` accepts, on both roots: **158 unit sets, 96 with a
     non-directory child, 17 where the blank line moves** — every `metadata/*` set
     carries an `AAREADME.txt`, and 17 of them hold exactly one unit directory
     beside it. So this happens on 17 real targets of a documented workflow in this
     tree, not hypothetically.

     PR-27 added a 27th transcript scenario for a metadata unit set and enumerated
     the two lines it produces as change 13 in `critiques/pr-27-validation.md`. This
     is the same trade `pdsarchives.archive_targets()` has made since PR-25.
     **Owner: recorded, not open.**

125. **`pdsindexshelf` and `pds4indexshelf` both call themselves `pdsindexshelf`,
     and both link shelf tools call themselves `pdslinkshelf`.** The pds4 flavors'
     `--help` description, their "Missing task" error and the subdirectory of each
     log root are all the pds3 name, in both pairs. That is preserved rather than
     fixed: it is what a run looks like today, and the names of log directories are
     what a sync script would have been written against. It is recorded because a
     reader of `pds4indexshelf.py` now sees `progname='pdsindexshelf'` in the spec
     and could reasonably read it as a copy-paste error. The archives, checksums and
     infoshelf pairs do not share this: each of those names itself.
     **Owner: open — a rename is a CLI-visible change and needs a decision.**

### Added by the CodeRabbit review of PR #125 (2026-08-07)

126. **Two dead branches in the index shelf tasks, preserved rather than removed.**
     `_indexshelf_common.index_initialize` and `index_validate` both test the
     dictionary `generate_indexdict()` returned against `None`, and
     `generate_indexdict()` either returns a two-tuple or raises, so neither test
     can be true. Both flavors carried the same branch before the migration
     (`pdsindexshelf.py:224` and `pds4indexshelf.py:221` at `2265393`), so merging
     them forced no choice and PR-27 kept both. Contrast the one dead branch PR-27
     did remove — a `move_old()` in `pdslinkshelf.initialize` sitting after a guard
     that returns when the shelf exists — which only one of the two flavors had, so
     the merge had to pick. Removing provably-dead code that both flavors carry is a
     cleanup of its own.
     **Owner: open.**

127. **`run_index_main` assumes its log path contains the tool's own directory.**
     It computes the directory for the per-target handlers as
     `logfile.rpartition('/' + spec.progname + '/')[0] + '/' + spec.progname`, which
     yields `/pdsindexshelf` if that component is absent. It cannot be absent:
     `log_paths_for` is called with `dir=spec.progname`, a non-empty constant, and
     `_derived_paths._log_path_for` appends `[subdir.rstrip('/'), '/']` after a log
     root that always ends in `/`. This is the two base tools'
     `logfile.rpartition('/pdsindexshelf/')[0] + '/pdsindexshelf'` generalized, not
     new. It is deliberately not `os.path.split(logfile)[0]`, which the other two
     drivers use: `log_path_for_index` builds a path carrying the table's whole
     logical path, so splitting would put a copy of the tool's error handler in
     every per-table directory. Recorded because the assumption is implicit.
     **Owner: open.**

128. **`pds4linkshelf.generate_links` iterates a shelved value without checking it
     is a list.** In the "identify labels for files" loop, a value taken from
     `linkinfo_dict` — which starts as a copy of `old_links` — is iterated and each
     item's link text read. Every key that reaches that loop is filtered to the
     `.xml`/`.lblx` files of the current directory, and every one of those is put
     into `linkinfo_dict` with a list value by the loop above and keeps it through
     the merge, so a string value is not a state this code can produce or read back.
     Unreachable before PR-27 (`AttributeError` on `.linktext`) and unreachable
     after it. What it would do after it depends on the string: iterating a `str`
     yields one-character strings, so `info[1]` raises `IndexError` on every
     character — but a value that was a longer sequence of longer strings would
     return a character rather than raising, which is the worse of the two failure
     modes and the reason this is written down. An `isinstance` guard would add a
     branch no test can reach.
     **Owner: open.**


### Added by the PR-27 adversarial review (round 1)

129. **`pdsarchives` logs under a `_links` suffix.** `pds3/pdsarchives.py`'s spec
     carries `log_suffix='_links'` where `pds4/pds4archives.py` carries
     `'_archives'`, so a pds3 archive run writes
     `logs/pdsarchives/<category>/<set>/<unit>_links_<tag>.log`. Not a PR-25 slip:
     the tool wrote `pdsdir.log_path_for_volume('_links', …)` before PR-25 as well,
     so PR-25 preserved it faithfully and PR-27 does not touch it. Changing it moves
     a log file name, which is exactly the kind of thing a sync script or a log
     rotation rule can be written against.
     **Owner: open.**

130. **The `run_index_main` driver is about two thirds a copy of `run_main`.**
     Measured with each function's docstring, blank lines and `def` line dropped and
     the longest common subsequence taken: `run_index_main` is 69 lines against
     `run_main`'s 66, with 44 line-identical — 64%. `run_selection_main`, PR-26's
     second driver, is 78 lines with 46 identical — 59%. Two of the four differences are forced — the per-target
     backup skip, which has to sit inside the log hierarchy to reach the exit
     status, and the log directory, which is the tool's own rather than the
     target's — and two are preservation: the quoted task header both index tools
     wrote at the base, and passing the logger to the task explicitly. This is the
     same trade PR-26 made for `run_selection_main`, and it is now the second time
     it has been made. A third instance would be worth stopping for.

     **Answered once all five families had migrated — see the amendment to this
     entry at the end of this file.** The pairwise figures above are this entry's
     original measurement and are superseded there; the answer is that the three
     drivers do not collapse.
     **Owner: recorded, not open.**

### Added by the PR-27 adversarial review (round 2)

131. **The entry-4 fix left an eager `%` inside a logging call.** In
     `pds4linkshelf.generate_links`, the label-identification loop logs
     `logger.info('Label identified (by file_name tag) for %s' % linktext,
     label_abspath)` — the message is formatted before the call rather than passed
     as a lazy argument, which the standing logging rule is against. It is base
     code that PR-27's one-line fix edited in place rather than logging PR-27
     wrote, so converting it there would have been gratuitous churn inside an
     otherwise verbatim function. It is now a line this PR touched, though, and it
     belongs with the `UP031` residue still ratcheted in both `generate_links`
     functions — one sweep, not two.

     **Wider than one line.** Four more eager-`%` logging calls sit in the two new
     shared modules — the two "Index shelf file is out of date" lines in
     `_indexshelf_common.index_repair` and the two "Link shelf file is out of date"
     lines in `_linkshelf_common.link_repair`. Ruff's `UP031` does not flag any of
     them, because the operand is a parenthesized expression rather than a plain
     name, so they are outside the ratchet as well: a sweep that follows the ratchet
     alone would miss them.
     **Owner: open.**


### Added by the PR-27 adversarial review (round 4)

132. **Three behaviours the migration moved are pinned only by the out-of-repo tool
     transcript.** Probed by mutation against
     `pytest tests/holdings_maintenance/ --mode ns`, which sat at 297 passed for
     each: inverting `index_repair`'s `if latest_mtime > shelf_mtime`, which chooses
     between re-dating an up-to-date shelf and cancelling; and replacing
     `run_index_main`'s `rpartition`-based log directory with
     `os.path.split(logfile)[0]`, which is precisely the alternative entry 127
     rebuts. Both are moved code and pre-existing gaps rather than PR-27
     regressions, and both are covered by the 81-record transcript, which lives
     outside the repository. The two mutations PR-27 *did* have to argue for — the
     backup skip reporting as an error, and `link_targets` filtering a unit set's
     non-directory children — were in the same state and are now pinned by tests.
     **Owner: open.**

133. **`index_reinitialize` takes pds4's comment over pds3's.** pds3 wrote
     `# ing if shelf file does not exist`, a mangling of pds4's
     `# Warn if shelf file does not exist`; the merged function has pds4's. Like the
     dead `move_old` call PR-27 enumerates as change 10, this is a difference only
     one of the two flavors had, so merging had to pick. Recorded because PR-27's
     enumeration rule covers log and output text and says nothing about comments,
     and this is the one comment in the migration where the merge made a choice
     rather than carrying a block along with its code.
     **Owner: recorded, not open.**

## From PR-28 (main() for crlf, shelf_consistency_check, show_opus_products, Phase 6)

### Added by the PR-28 executor's own measurements (2026-08-07)

134. **`shelf_consistency_check` reported a clean run for a mistyped flag, and
     neither tool could answer `--help`.** Both tools handled their one option by
     searching `sys.argv` and calling `remove()`, which makes every other argument a
     path. A path that does not exist walks to nothing, so
     `shelf_consistency_check --verbsoe <root>` printed `Tests performed: 2 /
     Errors found: 0` and exited 0 — a successful-looking check of a command line
     the user got wrong. `crlf --bogus f.txt` degraded differently, dying with
     `FileNotFoundError: '--bogus'`, and `--help` on each did whichever of those two
     things its own missing-path handling did. Fixed here, by the argparse both
     tools now have; the two exit codes that move are entry 135.

     The shape is what is left open. Any tool that treats unrecognized argv as data
     reports success on a typo, and this repository had two of them because each
     grew its own two-line flag handling rather than a parser. The eleven console
     scripts and `re_validate` do not have it. Nothing else in the tree does either,
     as of this PR — this is the last of them.
     **Owner: recorded, not open.**

135. **Usage-error exit codes moved on all three tools — accepted by the owner on
     consistency grounds (2026-08-07).** A command line argparse cannot classify now
     exits **2**, where the three tools previously did three different things, none
     of them designed:

     | tool | a bad flag at `3d044b2` | now |
     |---|---|---|
     | `crlf` | exit **1** — the flag became a filename and the run died in `FileNotFoundError` | exit 2 |
     | `shelf_consistency_check` | exit **0** — the flag became a path that does not exist, was walked to nothing, and the run reported clean (entry 134) | exit 2 |
     | `show_opus_products` | exit **1** — `KeyError` on the holdings environment, at import, before argparse existed. Only with a root unset; with both set its usage errors are byte-identical base to head | exit 2 |

     What carried the ruling was that the eleven already-migrated console scripts
     all exit 2 on a bad flag today, so this brings the last three **into** line
     rather than moving them away from anything. The owner's words were "accept
     consistency change".

     **The general rule the ruling establishes, so the next tool does not
     re-litigate it: the exit-code freeze covers what a *valid* invocation returns,
     not what a *malformed* command line happens to produce.** A status that falls
     out of an uncaught exception, or out of a tool treating an unrecognized
     argument as data, was never a designed part of the surface and is not what the
     freeze protects. §6.4's hard-stop list and the Phase 6 preamble both carry that
     distinction now, so neither reads as contradicting this.
     **Owner: resolved 2026-08-07, not open.**

136. **`crlf` prints no summary at all when it repairs more than one file.** The
     summary block reads `if repairs: if repairs == 1: print(f'{repairs}/{nfiles}
     files repaired')`, so a run over three files that fixes two lists both
     `REPAIRED` lines and then says nothing, where a run that fixes one says
     `1/3 files repaired` and a run that fixes none says `2/3 files invalid`. The
     `elif invalid` branch is unreachable whenever anything was repaired, so a run
     that repairs one file and finds another invalid does not mention the invalid
     one either.

     Preserved, not fixed: the Phase-6 rule lets output text move only where keeping
     it would force duplication or a flag, and keeping this forces neither. Pinned
     as current behaviour by `test_two_repairs_print_no_summary_at_all` and by
     transcript record `crlf/repair-two-of-three`, whose docstring says a fix has to
     invert it.
     **Owner: open.**

137. **`crlf.test_crlf` keeps its name, and with it the last `PT028` entry that is
     not `pdsdependency`'s.** `PT028` fires twice on this function, for the `task`
     and `threshold` defaults, and only because the name matches pytest's collection
     pattern; it is the tool's line-terminator classifier. Measured before deciding:
     `grep -rn 'test_crlf\b' --include=*.py .` finds two callers, `crlf.main()` and
     `tests/holdings_maintenance/test_crlf.py`, so a rename is mechanically safe
     inside this repository.

     Not done, for three reasons that are judgement rather than obstacle: it is a
     public name on a shipped module; PR-32 is chartered to document `crlf` as a
     program, so the tool has a documented surface; and the entry marks a lint false
     positive rather than a defect. There is a real cost to keeping it —
     `test_crlf.py`'s header documents a live collection trap, that
     `from …crlf import test_crlf` makes pytest collect the imported function and
     fail it on a missing `filepath` fixture — which a rename would delete outright.
     Renaming would take the ratchet to 65 entries / 179 slots.
     **Owner: open.**

138. **`crlf` exits 0 whether or not it found anything.** Every transcript record
     that reaches the end of `main()` exits 0, including the ones that print
     `INVALID` for every file given. A caller that wants to know whether a tree is
     clean has to parse stdout; `find … -exec crlf {} +` in a shell script cannot
     branch on the result. `shelf_consistency_check` does return 1 on errors, and
     did before this PR, so the two halves of what is nominally the same job report
     differently. Preserved because an exit code is frozen and this one is
     load-bearing in the other direction: a tool that started exiting 1 on an
     invalid file would fail any pipeline that runs it over a tree expecting to read
     the report.
     **Owner: open.**

139. **Two `show_opus_products` flag quirks, both preserved.** `--debug` calls
     `traceback.print_exc()` at a point where the `ValueError` it means to show has
     already been caught by the `except` clause above it, so there is no active
     exception and it prints the string `NoneType: None` — the flag has never shown
     a traceback (transcript record `opus/unresolvable-path-debug`). And
     `--narrow-table` is read only inside the `if display_table:` branch, so
     `--narrow-table --pprint` and `--narrow-table --raw` accept the flag and ignore
     it; `--narrow-table` alone works, because none of the three display flags being
     set is what turns the table on. Both are base behaviour carried into `main()`
     verbatim.
     **Owner: open.**

140. **`support.HOLDINGS_FREE_TOOLS` is a hand-maintained claim, not a derived
     one.** It is the set that decides which tools may be driven in-process, and
     both `run_tool_in_process()` and `run_tool_without_holdings()` assert against
     it — but the assertion only catches a caller naming the wrong tool. It cannot
     catch the other direction: if `crlf` or `shelf_consistency_check` ever grows an
     import of a PdsFile class, the set is silently wrong and the in-process tests
     start resolving temporary-tree paths against the session's preloaded real tree,
     which is entry 121's failure mode with the subprocess boundary removed. Neither
     tool imports anything but `argparse`, `os` and `sys` today. A test that asserts
     that — over the module's own import list, not over behaviour — would make the
     set self-checking, and is not written here.
     **Owner: open.**

### Added by the PR-28 adversarial review (round 1)

141. **`crlf` can no longer be given a path that begins with `-`, and `--` only
     half-rescues it.** The tool took every argument literally before it had a
     parser, so `crlf -dash.txt` checked that file; argparse reads a leading `-` as
     an option, so it is now a usage error exiting 2. This is the only invocation
     that worked at the base and does not work now — every other changed record is
     an error path that changed shape.

     The usual answer is the `--` separator, and under `parse_intermixed_args` it
     works only when a plain positional comes first: `crlf ok.txt -- -dash.txt`
     checks both, and `crlf -- --verbose` turns verbose *on* rather than checking a
     file of that name. `parse_intermixed_args` parses the argv before the first
     `--` with `parse_known_args` and re-parses the remainder, so a `--` in first
     position leaves nothing in front of it and the remainder is read with the
     optionals still live. Plain `parse_args` handles `--` correctly and rejects a
     flag between two positionals; the two cannot both be had.

     **And `--` in first position is not even stable across the versions this
     package supports.** `crlf -- -dash.txt` exits 2 on Python 3.10 through 3.12
     and exits 0, checking the file, from 3.13 — measured on 3.12.3 and 3.14.5 and
     confirmed by CI's 3.13 leg, which is the only place it showed up: every local
     run and all four adversarial review rounds used a single interpreter. The
     tests assert only the two outcomes that hold everywhere (a bare leading-`-`
     argument is a usage error; a path, a `--` and then the dashed file works), so
     the suite does not pin one interpreter's answer to the third.

     The trade was made toward the flags: `crlf a --verbose b` is a plausible
     command line and a file named `-something` is not — `find` over both holdings
     roots for `-*` returns nothing. Pinned by
     `test_a_path_beginning_with_a_dash_needs_a_path_and_a_separator_before_it`,
     which asserts both so a later switch to `parse_args` has to invert
     them. `shelf_consistency_check` has the same property, pinned by
     `test_a_shelf_root_beginning_with_a_dash_is_a_usage_error` and by transcript
     record `shelf/dash-root`, where the base run walked the directory and reported
     on it.
     **Owner: open.**

142. **`show_opus_products --narrow-table` has no test at all.** Replacing
     `if not display_narrow_table:` with `if not False:` in the table branch leaves
     the three tool-test modules at their full pass count. The flag is exercised by
     the out-of-repo tool transcript
     (`opus/narrow-table`, byte-identical base to head) and by nothing in the
     repository. It is one of PR-13's gaps rather than a PR-28 regression — PR-13
     covered the default table, `--pprint` and the opus-type filter, and left this
     one — and it is worth a test of its own: the narrow branch builds its rows in a
     different shape, with an `if opus_type not in rows` guard comparing a string
     against a list of one-element lists, which is always true and so is dead as
     written. Deferred 139 records the flag's other quirk, that `--pprint` and
     `--raw` accept and ignore it.
     **Owner: open.**

### Added by the PR-28 adversarial review (round 2)

143. **`show_opus_products` never resolves a PDS4 path in any test.** Commenting out
     `Pds4File.preload(pds4_holdings_dir)` leaves
     `pytest tests/holdings_maintenance/test_crlf.py
     tests/holdings_maintenance/test_shelf_consistency_check.py
     tests/holdings_maintenance/test_show_opus_products.py --mode ns` at its full
     pass count. Every
     path the module's tests pass is a PDS3 one, so the second half of the tool's
     two-flavor fallback — try `Pds3File`, then `Pds4File`, each by abspath then by
     logical path — is exercised only for its failure. The tool tests declare a PDS3
     source subset (`subsets.PDS3_VOLUME_SOURCES`) and a PDS4 one exists, so the
     missing piece is a fixture that stages both under one tree, not new source
     data. Same class as entry 142: a PR-13 coverage gap in a tool PR-28
     restructured but did not otherwise change.
     **Owner: open.**

144. **`run_tool_in_process` captures into `io.StringIO`, which has no encoding.** A
     real `python -m` run writes through an encoded stream, so a byte the
     subprocess's locale cannot encode raises `UnicodeEncodeError` there and cannot
     here — an in-process test would pass where the tool it stands for would die.
     Neither migrated tool can reach that state in this repository's tests: `crlf`
     prints only paths the test itself created and four ASCII status words, and
     `shelf_consistency_check` prints only paths. It is written down because the
     runner's docstring lists its other fidelity caveats — the working directory,
     and that `sys.argv` is rebound for the call — and this is the third.
     **Owner: open.**

### Added by the PR-28 adversarial review (round 3)

145. **`pdsfile.tools.show_opus_products` is importable now, and it imports
     `tabulate` at module scope — a `dev`-only extra.** The module has always
     imported `tabulate`, so `python -m pdsfile.tools.show_opus_products` has always
     needed the dev extra; what changed is that the module can now be *imported*
     without running, which is what an autodoc build or a console-script entry point
     would do. `scripts/check_runtime_imports.py` walks the frozen public module set
     and does not reach `src/pdsfile/tools/`, and CI installs `.[dev]`, so the
     clean-install gate is green and stays green. The question this leaves is which
     way to settle it: move `tabulate` to the runtime dependencies, or import it
     inside the branch that renders a table so the other three output modes work in
     a bare install. Both are behaviour decisions about a shipped module rather than
     tidying.
     **Owner: open.**

146. **The maintenance tools' docstrings say `Args:` where the rules say
     `Parameters:`.** `python.mdc` and `doc_python.mdc` both call for
     `Parameters:`; every module under `holdings_maintenance/` uses `Args:`, and the
     three `main()`s and `build_arg_parser()`s PR-28 wrote follow their neighbours
     rather than the rule. `crlf.py` now carries both styles in one file, because
     `test_crlf`'s own docstring predates the convention and uses `Parameters:`.
     Sweeping the subsystem is Phase 7's job — it owns docstrings — and doing it
     piecemeal would leave the tree in three states rather than two.
     **Owner: recorded, not open — Phase 7.**

### Added by the PR-28 adversarial review (round 4)

147. **The help *text* of the two new parsers is pinned only by its flag names.**
     Replacing `crlf`'s whole `description=` literal, or any one help string, with
     junk leaves the three tool-test modules green: the help tests assert the
     `usage: crlf.py` prefix and that each flag name appears, and nothing else.
     That is deliberate for text this PR invented — a golden of a `--help` screen
     pins argparse's line-wrapping as much as the words, and argparse rewraps to
     the terminal width — but it means the text is documentation with no gate, and
     PR-32 is chartered to write a user-guide chapter per program from it. The
     out-of-repo transcript does capture both screens byte-for-byte at a pinned
     `COLUMNS`, which is where a reader can see what they currently say.
     **Owner: open.**

148. **The per-code table in `pdsfile_overrides.mdc` deviation (4) has drifted from
     the tree.** Spot-measured at PR-28's head with
     `ruff check --config 'lint.per-file-ignores = {}' --select <code> src/pdsfile
     tests scripts`: `UP031` 97 against the table's 124, `B006` 12 against 9,
     `B012` 2 against 3, `RUF015` 3 against 2. The drift is from the Phase-6
     migrations moving code between files rather than from any entry being wrong —
     the ratchet itself, which is the enforced copy, is exact. PR-28 removed the
     two rows that had become false statements (`F821`, and the `RUF059` row whose
     cited defect no longer exists) and did not re-derive the counts, because a
     table PR-24 owns is not a thing to half-refresh from inside another PR.
     **Owner: open — one re-derivation of the whole table, by whoever next edits
     it.**

### Amended by the PR-28 executor (2026-08-07) — entry 130

**Entry 130's question, answered.** PR-27 recorded that a third copy of the driver
loop should stop the line, and left the measurement for when all five families had
migrated. They have, so here it is. Method: each driver's body with its docstring,
`def` line, blank lines and comments dropped and the `_common.` qualifier
normalized away, since in one driver those names would be local:

| | code lines | vs `run_main` | vs `run_selection_main` | vs `run_index_main` |
|---|---:|---:|---:|---:|
| `_common.run_main` | 57 | — | 42 | 40 |
| `_shelf_common.run_selection_main` | 69 | 42 | — | 39 |
| `_indexshelf_common.run_index_main` | 55 | 40 | 39 | — |

Common to all three, as an ordered common subsequence: **39 lines** — 68.4% of
`run_main`, 56.5% of `run_selection_main`, 70.9% of `run_index_main`. On the raw
bodies (comments kept, qualifier kept) the same three are 66 / 78 / 69 lines with
43 common, which is where PR-27's 64% and PR-26's 59% pairwise figures came from.

**The 39 is not one block.** Scanning `run_main` left to right and taking, at each
position, the longest block of consecutive lines that also occurs consecutively in
both other drivers, the 39 fall into blocks of **15, 5, 5, 3, 2, 2, 2** lines and
five isolated lines. The 15 are one thing: the preamble, from
`build_arg_parser(spec)` through the `args.log` handler loop, and it is the only
block that is a stretch of the drivers' *work*. The other six are
try/except/finally scaffolding and two lines of handler construction — the `try:`
and its `logger.info('Log file', …)` loop, the `except`/`raise`/`finally`/
`logger.close()` pairs — wrapped around bodies that differ in all three. They are
identical because every driver has to open a log scope and close it, not because
the drivers agree on anything inside.

**What one driver would need, eight variation points:**

1. *Target resolution.* `run_main` expands command-line paths itself with an
   existence check; `run_selection_main` calls `resolve_holdings_paths` +
   `expand_selection_targets` and gets `(pdsdir, selection)` tuples;
   `run_index_main` calls `index_targets`. A hook — clean.
2. *Log-path derivation.* Three forms: a fixed method plus a suffix; a method chosen
   per target from `pdsf.bundlename`; a method whose suffix is passed only when
   non-empty. A hook — clean.
3. *`set_log_dirs(logfiles)`*, called by two of the three. Folds into (2).
4. *Per-target handler directory.* `os.path.split(logfile)[0]` versus the
   `rpartition('/' + progname + '/')` form, which entry 127 explains is not
   interchangeable. A hook — clean.
5. **The task header.** `Task X for` (`run_main`), `Task "X" for`
   (`run_index_main`), and `Task "X" for selection S` / `Task "X" for`
   (`run_selection_main`). This is the one variation point a merger would **not**
   have to keep: the owner's 2026-08-05 output-text ruling says text may move where
   keeping it would force a flag whose one job is to re-create one side's wording,
   which is exactly this, and PR-25 has already moved a log line on that basis.
   Unifying it is a log-text change on four tools, enumerable. So this is not a
   reason not to merge — it is a cost, not an obstacle, and the case rests on the
   other seven. (Note that once the header is unified, the `for selection S`
   variant remains, inside variation point 7.)
6. **The backup skip.** `run_index_main` only, and entry 132 records why it has to
   sit inside the log hierarchy rather than in the target list: the skip is reported
   as an error and has to reach the exit status. A guard hook or a flag.
7. *The task call.* `tasks[t](pdsdir)`, `tasks[t](pdsdir, selection)`,
   `tasks[t](pdsf, logger=logger)` — three signatures — plus
   `run_selection_main`'s rewrite of `reinitialize` to `update` when a selection is
   given.
8. *The return contract.* Two `sys.exit(status)` against one
   `RunResult(args, status, proceed)`, which exists because `pdschecksums
   --infoshelf` chains a second run off `proceed`. Unifying it changes the exit path
   of all eleven tools.

**Line arithmetic.** 181 code lines across the three today. A merged driver would be
the 39 shared lines plus the calls into seven hooks; the 64 residue lines do not
disappear, they become per-family functions with `def` lines and docstrings, and
`ToolSpec` grows five or more fields. The saving is on the order of 20%, bought
with seven variation points at the seams of a loop whose every semantic line
differs, plus a log-text change on four tools to retire the eighth.

**The measurement points somewhere else.** The 15-line preamble is contiguous,
identical in all three, and carries no per-family variation at all: it parses,
guards the missing task, resolves the log root, builds the logger and adds the
root handlers. Extracting it as a fourth `_common` helper takes 38% of the
commonality with **zero** new variation points and leaves the three loops alone.
That is a small PR with a small tool-run diff, and it is a different PR from the one
entry 130 was asking about. Its one wrinkle is `status = 0`, which sits inside the
block and is a local each driver reads later, so the helper returns `(args, logger)`
and the `status = 0` stays behind — 14 lines move, not 15.

**Answer: they do not collapse cleanly; do not merge them.** PR-28 measured and did
not act.
**Owner: recorded, not open — unless the owner wants the 15-line preamble
extraction, which would be its own PR.**
