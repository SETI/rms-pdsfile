# PR-14 validation record

**PR:** `ci: hosted lint/no-holdings job; keep self-hosted full-data gate`
**Branch:** `pr-14-hosted-lint-ci`, based on `origin/rewrite` @ `0d588b3`
(PR-13, "test: maintenance-tool test suite (#105)")
**Date:** 2026-07-26

## 0. Scope of the change (for the §6.6 staleness rule)

**This PR touches no file under `src/pdsfile/`** (`git diff --name-only
origin/rewrite -- src/` is empty). Per §6.6 step 5, the full-data records below
therefore cannot go stale for any follow-up round that changes only
`tests/`, CI, docs or records; they carry forward unless `src/` is touched.

Files changed: `.github/workflows/run-tests.yml`, `scripts/run-all-checks.sh`,
`tests/conftest.py`, `tests/api/conftest.py` (new), `pyproject.toml`,
`.cursor/rules/pdsfile_overrides.mdc`, `critiques/`.

## 1. Environment

- Holdings resolved entirely from `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` with
  `PDSFILE_TEST_HOLDINGS=full`. The roots used are the **limited testing copy the
  goldens are tuned to**; its location is machine-local and appears in no
  checked-in file (§3.4). No absolute holdings path appears in this record, in
  the diff, or in the PR description.
- Local interpreter: CPython 3.12 in the repo venv, `pip install -e ".[dev]"`.
- Baselines compared against: the same two runs executed in a clean `git
  worktree` at `origin/rewrite` (`0d588b3`) with the identical command lines,
  captured in the same format and diffed line by line.

## 2. Active §2 gates

| Gate | Result |
|---|---|
| `ruff check src/pdsfile tests scripts` | **passed** — ratchet unchanged; the new `tests/api/conftest.py` needed no `per-file-ignores` entry |
| pyroma | **10/10** (re-confirmed after the Windows trove classifier was dropped, issue #102) |
| API-freeze | **passed** in both invocations: `pytest tests/api/test_api_freeze.py --confcutdir=tests/api` (hermetic) and as part of the whole-tree run |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports) |
| Full-data suite, both modes | **per-test pass/fail set identical to `origin/rewrite`** — see §3 |
| `scripts/run-all-checks.sh` end to end | **passed** with holdings (pytest 790/34) and without holdings (pytest 24/800) — see §3a for how the two are told apart |
| Adversarial review loop | see `critiques/pr-14/round-<k>.md` |

## 3. Full-data suite — must not change

Command lines are exactly those in `scripts/automated_tests/pdsfile_main_test.sh`,
run serially (the driver's own form), with `-rA` added so every outcome is
recorded per test id.

| Run | `origin/rewrite` @ `0d588b3` | this branch | diff |
|---|---|---|---|
| `--mode ns` (api, holdings_maintenance, pds3file, rules/pds3, pds4file, rules/pds4) | 790 passed / 34 skipped | **790 passed / 34 skipped** | **empty** |
| `--mode s` (pds3file, rules/pds3) | 555 passed / 3 skipped | **555 passed / 3 skipped** | **empty** |

The comparison is not a count check: the sorted `PASSED`/`SKIPPED`/`FAILED`
lines of each run were diffed against the base worktree's, and both diffs are
empty. This matches the baseline recorded by PR-13 (790/34 and 555/3), which
superseded PR-09's 679/34.

The script's own invocation covers the whole `tests/` tree in one pass
(`pytest -q -n "$PYTEST_WORKERS" --dist loadscope tests --mode ns`) and also
reproduces **790 passed / 34 skipped**. The gate's default worker count is
**1 (serial)**, not `auto`: deviation (7) in
`.cursor/rules/pdsfile_overrides.mdc` says full-data runs are serial, and the
plan retired xdist adoption outright (PR-12, "adds shared-state risk"), so
turning the gate on must not quietly make the data suite parallel. Each xdist
worker runs the session fixture, i.e. its own full `Pds3File.preload` +
`Pds4File.preload`; measured peak RSS for one preload against the limited copy is
**105 MB**, and the complete set is larger, so `-n auto` on a many-core machine
is a memory bet nobody asked for. `-w auto` remains available and was measured at
33.9 s vs 142.1 s serial, with an identical pass/skip set — recorded here so the
tradeoff is known, not so the default depends on it.

## 3a. The gate must not pass vacuously

The plan's wording is "with holdings env vars it runs the full suite; without,
the holdings-free subset". That is not what the two roots alone produce:
`tests/support/holdings.py::resolve_holdings` only reads
`PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR` when `PDSFILE_TEST_HOLDINGS=full`, so a
developer who followed §3.4 literally (export the two roots, nothing more) got
**24 passed / 800 skipped** and a green `✓ SUCCESS` — 3% of the suite, reported
as a pass. Reproduced before fixing.

`scripts/run-all-checks.sh` now sets `PDSFILE_TEST_HOLDINGS=full` for its own
invocation when **either** root is exported and no selector is set, and **prints
what the resolver resolved** in every case. Either, not both: with only one root
exported the resolver then fails the session and names the missing variable,
which is the right outcome — half-configured is a mistake, not a
3%-of-the-suite pass. An explicit `PDSFILE_TEST_HOLDINGS` always wins, and
`PDSFILE_TEST_DATA_DIR` is never set, so the mini flavor stays dormant (ground
rule 3). This uses PR-09's selector exactly as
`scripts/automated_tests/pdsfile_main_test.sh` already does; it changes nothing
in `tests/support/holdings.py`.

The reported flavor comes from `resolve_holdings()` itself rather than from a
second policy written in shell, so the log cannot disagree with the session. That
matters for the dormant mini path: with `PDSFILE_TEST_DATA_DIR` pointing at real
trees the resolver returns `mini`, and the script says `holdings: mini` — an
inferred-in-shell message would have said "no holdings".

Verified afterwards, on the same machine:

| environment | script's pytest line | result |
|---|---|---|
| both roots exported, no selector | `holdings: full` | **790 passed / 34 skipped** |
| `PDSFILE_TEST_HOLDINGS=full` + both roots | `holdings: full` | **790 passed / 34 skipped** |
| one root only, no selector | `holdings selection is invalid, pytest will report it` | **fails**: `ERROR: PDSFILE_TEST_HOLDINGS=full requires PDS4_HOLDINGS_DIR to be set` |
| `PDSFILE_TEST_DATA_DIR` set (dormant path) | `holdings: mini` | matches `resolve_holdings().flavor` |
| no holdings env vars at all | `no holdings: holdings-free subset only` | **24 passed / 800 skipped** |

## 4. No-holdings run — this is what changes

Command: `pytest tests` with `PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR`,
`PDSFILE_TEST_HOLDINGS` and `PDSFILE_TEST_DATA_DIR` all unset.

| | `origin/rewrite` | this branch |
|---|---|---|
| passed | 23 | **24** |
| skipped | 801 | **800** |
| collected | 824 | **824** |
| collection errors | 0 | **0** |

`passed + skipped == collected` in both. The set difference of passing test ids
is exactly one test, in one direction:

```text
+ PASSED tests/api/test_api_freeze.py::test_public_api_frozen
```

Nothing stopped passing. Justification: the freeze test regenerates the manifest
in a clean child interpreter and compares it to the committed file — it reads no
holdings at all (its own module docstring says so), and PR-13's addendum named it
as the test PR-14 owed the marker to.

**Survey for other holdings-free tests (deferred entry 9 asks for one).** This
was measured, not eyeballed. The blanket skip was lifted with a throwaway
`tryfirst` plugin marking every collected item `holdings_free`, and the whole
tree was run with all four holdings env vars unset:

```text
315 passed, 387 failed, 122 skipped
```

So **291 tests beyond the 24 the hosted job runs today do pass with no holdings
present.** Grouped by test function: 124 functions have every parametrized case
passing, **41 are mixed** (some cases pass, some fail), 126 fail outright. They
live in four modules: `tests/pds3file/test_pds3file_blackbox.py`,
`test_pds3file_blackbox_cached.py`, `test_pds3file_whitebox.py`, and
`tests/pds4file/test_pds4file_blackbox.py`. The effect is not an artifact of
ordering: each module run alone produces exactly the same passing set as it does
inside the whole-tree run (134 / 43 / 46 / 68, zero differing lines).

**They are still not marked `holdings_free`, deliberately.** Four reasons:

1. **They do not satisfy the marker's definition.** `pyproject.toml` registers it
   as "test builds its own inputs and needs no holdings tree". These build their
   inputs by concatenating the *resolved* holdings root — which, with no
   holdings, is PR-09's synthetic placeholder. The test ids say so out loud, e.g.
   `test_logical_path_from_abspath[/pdsfile-no-holdings/pdsdata/holdings/volumes/...]`.
   They pass against a root that does not exist, which is not the same property
   as needing no root.
2. **There is no boundary to mark along.** 41 functions are mixed at the
   parametrized-case level, so the split runs through the middle of the inline
   `@parametrize` tables, not along module, class or function lines. Splitting
   those tables is issue **#92**, listed in §9 of the plan as future work outside
   this effort.
3. **Nothing pins the property, and Phase 5 is next.** No assertion says "this
   must not touch the filesystem", so a mark silently becomes a hosted-CI-only
   tripwire — the exact failure class that cost PR-13 three CI-only failures.
   Phase 5 rewrites these very paths: PR-15 bug 3 changes the holdings-env lookup
   in `abspath_for_logical_path`, and PR-16 moves `logical_path_from_abspath`,
   `repair_case` and `selected_path_from_path` into `_path_utils.py`.
4. **The plan enumerates the subset and this is not in it.** §1 G3: "the
   holdings-free subset (API freeze, tool unit tests, import/collection smoke)".
   The Phase-4 bullet's "any other no-data tests" is read against that
   enumeration; the blackbox/whitebox suites are the data suite.

Some of the 291 are also hollow on inspection — `test__info` asserts
`res1 == res2`, `test_logical_path_from_abspath` swallows `ValueError` into
`assert True` — which is a reason to be wary of them as a hosted-CI signal, not a
reason on its own.

The measurement and the option are recorded as entry 15 of
`critiques/deferred-observations.md` so this is a decision on the record rather
than a search that came up empty. No test was marked to make a number go up.

## 5. How the marker is applied without editing the frozen test

§6.4 forbids editing `tests/api/test_api_freeze.py`. Two mechanisms were
considered:

1. **A path predicate inside `tests/conftest.py`'s existing skip loop.** Rejected:
   it edits PR-09's collect-and-skip machinery, which ground rule 3 says stays as
   merged (PR-13 already needed an owner-accepted addendum to add the
   `holdings_free` exemption at all), and it splits the "is this holdings-free"
   answer across a marker *and* a hard-coded path.
2. **A new `tests/api/conftest.py`** that marks every item collected from that
   directory `holdings_free`. **Chosen.** It touches no frozen and no PR-09 file,
   the fact lives next to the tests it describes, and it covers later additions
   to `tests/api/` — `tests/api/test_mixin_collisions.py` arrives there in PR-17
   and is equally holdings-free.

Two properties of the chosen form were verified rather than assumed:

- **Hook order.** `tests/conftest.py`'s `pytest_collection_modifyitems` adds the
  skip to everything not already marked, so the marker must be applied first.
  Conftest hook order is otherwise unspecified, so the new hook is declared
  `@pytest.hookimpl(tryfirst=True)`. Verified by the run in §4: the freeze test
  passes rather than skipping.
- **Hermeticity under `--confcutdir=tests/api`.** That flag (used by the
  API-freeze gate in `run-all-checks.sh`) loads `tests/api/conftest.py` but not
  `tests/conftest.py`. The new file imports only `pathlib` and `pytest`, declares
  no options — so `--mode`/`--update` still come from `tests/conftest.py` alone —
  and registers no marker of its own (`holdings_free` is registered in
  `pyproject.toml`, which `--strict-markers` reads). Verified: the hermetic
  invocation passes.

## 6. `--mode` hardening (deferred entry 12)

Owner decision relayed 2026-07-26: `choices=('s', 'ns')` **and** `default='ns'`.

- Survey of **every** `--mode` invocation in the repo — `scripts/automated_tests/
  pdsfile_main_test.sh` (both passes), `scripts/run-all-checks.sh`,
  `run_tests_coverage.sh`, `tests/rules/README.md`, `.cursor/rules`, the plans and
  the critique records — found that all of them already pass an explicit `s` or
  `ns`. No existing invocation changes behavior; both full-data set diffs in §3
  are empty, which is the mechanical confirmation. (`run_tests_coverage.sh` at the
  repo root passes valid modes but references pre-`src/`-layout paths that no
  longer exist; it is stale independently of this PR and is left alone.)
- Because the option can no longer hold any value but `s` or `ns`, the mixed
  `else` branch (`Pds3File` shelves-only, `Pds4File` not — a state no invocation
  ever selected and `# pragma: no cover` acknowledged) is **deleted**, not left
  unreachable. `setup` now computes one `shelves_only` boolean and applies it to
  both classes, so the two can no longer disagree.
- Verified loud failure: `pytest tests/api --mode NS` now exits with
  `error: argument --mode: invalid choice: 'NS' (choose from 's', 'ns')`.
- `scripts/run-all-checks.sh` passes `--mode ns` explicitly, so the script does
  not depend on the default and reads as its own documentation.

## 7. Deferred entry 8 (subprocess coverage) — measured, then re-deferred

Implemented as a spike and measured before deciding. Command, run twice with the
limited holdings copy exported:

```sh
PDSFILE_TEST_HOLDINGS=full python -m coverage run -m pytest \
    tests/holdings_maintenance/test_pds3_archives.py --mode ns -q -p no:cacheprovider
```

The only variable is whether `tests/holdings_maintenance/support.py::run_tool`
prefixes each tool subprocess with
`-m coverage run --parallel-mode --rcfile <repo>/pyproject.toml` and sets an
absolute `COVERAGE_FILE` in the subprocess environment:

| tool subprocesses | pytest summary line |
|---|---|
| uninstrumented (today) | `8 passed, 5 warnings in 16.06s` |
| instrumented | `8 passed, 5 warnings in 138.84s` |

**8.6x**, paid on every PR and nightly across four Python versions of the
self-hosted gate. The cost is the tracer inside each tool, so the
`sitecustomize`/`COVERAGE_PROCESS_START` route named in the entry measures the
same and costs the same; it additionally needs parallel data files and a guarded
`coverage combine` inside the data-gate driver. The spike was reverted; the entry
is re-assigned to PR-37 with the measurements and the `COVERAGE_CORE=sysmon` lead
recorded in `critiques/deferred-observations.md`. Nothing was half-landed.

## 8. Workflow YAML — how it was validated, and what it cannot prove

- Parsed with `yaml.safe_load`; the job graph was asserted programmatically:
  `run-tests.yml` now has jobs `lint` (ubuntu-latest, matrix 3.10/3.13) and
  `test` (self-hosted-linux, matrix 3.10–3.13, unchanged, including its codecov
  upload gated on 3.13). `run-tests-and-opus.yml` is **unmodified**:
  `test_pdsfile` still `uses: ./.github/workflows/run-tests.yml` and `test_opus`
  still `needs: [test_pdsfile]`.
- Effect of the new job on the OPUS workflow, checked explicitly: `needs` on a
  reusable-workflow caller waits for the *whole* called workflow, so `test_opus`
  now also waits for `lint`. Harmless and desirable — the OPUS leg no longer
  starts behind a lint failure. No job id changed and no job was renamed, so the
  existing check names are preserved and only new ones are added.
- The lint job runs `scripts/run-all-checks.sh --sequential` rather than
  re-listing the gates, which is how "CI runs exactly the set the script enables,
  no more, no less" (`environment.mdc` §2/§3, tightened at PR-14) is satisfied by
  construction rather than by hand-maintained parity.
- Correspondence holds at the **workflow** level, i.e. over the union of the two
  jobs, not per job: the self-hosted job runs
  `scripts/automated_tests/pdsfile_main_test.sh`, which the PR-14 bullet says to
  leave exactly as it is. That driver adds coverage and a second, pds3-only
  `--mode s` pass which the script does not have, so a shelves-only-specific
  failure is caught by CI and not by the script. Recorded in the script's
  `# Environment:` header and in deviation (8) so nobody assumes the script
  reproduces the data gate exactly.
- The script was executed locally in exactly the hosted job's condition — all
  four holdings env vars unset — and passed end to end in 21 s (§2). What that
  does **not** prove is the stock-runner environment itself: a different
  filesystem, TZ, locale and a fresh pip resolution on 3.10 and 3.13. The tests
  that job runs were audited for that class of assumption (the `crlf` classifier
  units build their own bytes in `tmp_path`; the holdings-free
  `shelf_consistency_check` cases build their own tiny tree; the freeze test
  shells out to the dumper and compares JSON). First real proof comes from the
  CI run on this PR — see §8b.

## 8b. First real CI run (PR #107, run 30217863593) — all six jobs green

The stock-runner unknown is now closed. Every job succeeded on the first attempt;
no PR-13-style environment-pinning failure appeared.

**Hosted `Lint and holdings-free tests`**, both legs, on `ubuntu-latest` with no
holdings and a fresh pip resolution:

| leg | pytest line | result | wall |
|---|---|---|---|
| 3.10 | `Running pytest (-n 1; no holdings: holdings-free subset only)...` | **24 passed, 800 skipped** | 24 s total for all five gates |
| 3.13 | same | **24 passed, 800 skipped** | comparable |

Both legs also show `Final rating: 10/10` (pyroma), `✓ Ruff check passed`,
`✓ API-freeze check passed`, and the clean-install gate building its throwaway
venv and importing the full module surface — the first time that gate has run on
a machine with no holdings env vars at all. The printed flavor line is the
no-holdings branch, so the job is demonstrably running the subset it claims and
not silently something else.

**Self-hosted `Test pdsfile`**, all four Python versions green; the 3.13 leg's
two passes read:

```text
790 passed, 34 skipped in 378.62s      (--mode ns)
555 passed,  3 skipped in 282.15s      (--mode s)
```

Identical to the baseline in §3 and to the local runs, on a different machine and
a different holdings root — which independently corroborates the "no behavior
change" claim rather than merely repeating it.

The six check names GitHub produced match the ones given to the owner for branch
protection exactly: `Lint and holdings-free tests (3.10)`, `(3.13)`, and
`Test pdsfile (self-hosted-linux, 3.10 … 3.13)`.

## 8a. The Windows classifier, and why macOS keeps its own

Owner decision (issue #102): drop `Operating System :: Microsoft :: Windows`.
The reason is that the package is **not supported** on Windows — that is why
PR-08 removed it from the matrix and why the issue exists. `Operating System ::
MacOS :: MacOS X` is deliberately kept: macOS is a supported platform whose
matrix entries are commented out in `run-tests.yml`, not deleted, and are
re-enablable. "Untested in CI right now" is not the criterion; "unsupported" is.
pyroma still scores 10/10 with the classifier list as it now stands.

## 9. Not changed, deliberately

- `scripts/automated_tests/pdsfile_main_test.sh` — the self-hosted full-data
  driver, untouched (both passes, the `PDSFILE_TEST_HOLDINGS=full` export, the
  coverage invocation and the codecov artifact).
- The self-hosted matrix, its triggers (`pull_request` to `rewrite`, `push` to
  `main`, nightly cron, `workflow_dispatch`, `workflow_call`), and the codecov
  upload step.
- PR-09's holdings-flavor machinery: `tests/support/holdings.py`, the
  `PDSFILE_TEST_HOLDINGS` / `PDSFILE_TEST_DATA_DIR` env vars, the `full_holdings`
  marker and its mini branch, `tests/golden/full/`. Nothing sets
  `PDSFILE_TEST_DATA_DIR`.
- Coverage thresholds and `codecov.yml` (targets stay informational until Phase
  8).
- **Nightly-failure alerting.** Settled decision §8.7 is GitHub's built-in
  notifications for now, so this deliverable is "no work"; the nightly cron and
  its notification behavior are unchanged, and nothing was added.
- **Branch protection.** Settled decision §8.8 makes protecting `rewrite` an
  owner/admin action. The check names to require once this lands are in the PR
  description.
