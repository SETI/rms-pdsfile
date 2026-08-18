# Coverage-mode validation record — a coverage mode for `run-all-checks.sh`

Branch `feat/coverage-mode`, based on `rewrite` at `02dd774`. Everything below is
measured on this tree, against the limited holdings copy at `/seti/opus/pdsdata`,
Python 3.12.3, coverage 7.13.3, ruff 0.15.7. Nothing is projected.

## What was asked for

Coverage off for day-to-day testing and on for deliberate coverage runs, driven from
`scripts/run-all-checks.sh`; the maintenance tools measurable as an **option**, because
they run as subprocesses that `coverage run` does not follow; the observation register's
entry 4214 corrected, because its "prohibitive at 8.6x" conclusion measured one
configuration and generalized it to all of them. `pyproject.toml`'s `addopts` were
already right (no `--cov`, no `-n auto`), so nothing about the default posture moves.

## What was built

**`--coverage`** runs the pytest gate under `coverage run` and reports. It takes every
measurement setting from `[tool.coverage.*]` — the script names no source, omit or
exclude — so it produces the branch coverage the repository has always configured and
the data gate has always produced.

**`--coverage-subprocess`** adds the tool subprocesses, through `COVERAGE_PROCESS_START`
in `ToolTree.env`, acted on by a `coverage.process_startup()` hook in the tool
subprocesses' existing `sitecustomize.py` — and, on coverage 7.10 and later, by
coverage's own `a1_coverage.pth` first (finding 3 below). It is internally consistent and says so in its own output:
the whole run is line-only under `COVERAGE_CORE=sysmon`, and the data files are
per-process and combined afterwards.

Neither flag sets `SCOPE_SPECIFIED`. Coverage is a **mode of the pytest gate, not a check
of its own**, and it deliberately carries no `RUN_*`/`ENABLE_*` pair: a no-scope run sets
every `RUN_*` true, so a `RUN_COVERAGE` would turn coverage on for exactly the day-to-day
run it must stay out of. It rides on `RUN_PYTEST` × `ENABLE_PYTEST` instead, and asking
for it when that gate is not scheduled exits 1 rather than reporting 0% — the rule the
PyMarkdown gate already applies to an empty file selection.

## The three findings that shaped the implementation

**1. `-n 1` is not serial.** The gate's default `-n 1` starts one xdist worker, which is
a subprocess `coverage run` does not follow. Measured on `tests/core` (73 ids, same tests
both times):

| workers | TOTAL |
|---|---|
| `-n 1` | 15% |
| `-n 0` | 24% |

Under `-n 1` the report is the controller's imports. Both coverage modes therefore run
pytest with `-n 0` whatever `-w` asked for, and both the header line and the invocation
line say so. (The data gate is unaffected: `pdsfile_main_test.sh` passes no `-n` at all,
so xdist is not active there.)

**2. Exporting the coverage variables would have made the numbers depend on `-p` versus
`-s`.** In sequential mode the code checks, the Sphinx build and the Markdown scan share
one shell, so an exported `COVERAGE_PROCESS_START` would reach Sphinx — whose autodoc
imports `pdsfile` — and fold that import into the total, while the parallel branch, which
runs each check in its own subshell, would not. The variables are passed per command
(`env "${COVERAGE_ENV[@]}" python -m coverage …`), never exported.

**3. Coverage 7.10+ ships its own `a1_coverage.pth`**, which calls the same
`coverage.process_startup()` from site processing whenever `COVERAGE_PROCESS_START` is
set (`venv/lib/python3.12/site-packages/a1_coverage.pth`, owned by
`coverage-7.13.3.dist-info/RECORD`). On this machine it fires *before* `sitecustomize`,
so the repository's hook is not the only thing that could start the measurement. The hook
is still worth having and is still what this PR relies on, for two reasons that are
properties of the file rather than opinions: the `.pth` swallows every exception
(`except: pass`), so a coverage that could not start leaves the child running unmeasured
and the report quietly short, where the hook exits 70; and the dev extra floor is
`coverage>=7.0`, which predates the `.pth`. Both are recorded here because the
before/after totals below would look the same either way, and a reader is entitled to
know which mechanism they are seeing.

## Does the hook fire?

Two of the new tests answer this, and they pass `-S` so that the answer is attributable:
`-S` skips site processing, so coverage's own `.pth` never runs and anything observed can
only have come from the repository's hook.

* `test_the_hook_starts_coverage_in_a_child` runs `python -S -c 'import sitecustomize;
  import pdsfile.pdscache'` with `COVERAGE_PROCESS_START` set, and asserts exactly one
  suffixed data file, `pdscache.py` among its measured files, and recorded lines in it.
  Reproduced by hand before the test was written: `measured:
  ['/seti/all_repos/rms-pdsfile/src/pdsfile/pdscache.py']`.
* `test_the_hook_refuses_to_start_when_coverage_is_missing` runs the same child with only
  the guard directory on `PYTHONPATH`, and asserts exit **70** with `refusing to start
  without coverage measurement` on stderr. Reproduced by hand: both.

And in the whole-suite run the script counted the data files itself: **320 (1 pytest
process + 319 measured children)** — children, not tool runs, because
`COVERAGE_PROCESS_START` reaches every subprocess the suite starts, and the whole-suite
320 against `tests/holdings_maintenance`'s own 308 puts twelve of them elsewhere.

One blind spot, small and deliberate. `support.no_holdings_env()` puts only `src/` on
`PYTHONPATH`, so its children get no `sitecustomize` and are measured only by coverage's
own `.pth` — meaning that on coverage 7.0–7.9 they would not be measured at all, and the
fail-closed guarantee does not reach them. It has **three** call sites, not one:
`support.run_tool_without_holdings()` (`support.py:475`), reached by
`test_crlf.py::test_the_module_is_runnable_as_python_m` and
`::test_an_unreadable_file_ends_the_process_with_a_traceback`, and
`test_show_opus_products.py:58`, reached by
`::test_the_module_imports_with_neither_holdings_root_set` and
`::test_the_module_is_runnable_as_python_m`. The second pair matters more, because
`show_opus_products` is one of the twelve subprocess-driven programs this mode exists to
measure. Extending the path would also install the read-only guard in those children,
changing what those tests do, which is not this PR's to change; both modules are measured
through their other tests (`crlf.py` 100%, `show_opus_products.py` 81%).

## What the subprocess mode measures, before and after

The naive comparison — `--coverage` 56% against `--coverage-subprocess` 81% — mixes two
effects, because the subprocess mode is also line-only and a branch denominator is
larger. A third run isolates them: line-only, parent only, no subprocesses. All three are
the same 1243 ids over the same tree.

| run | pytest summary | package TOTAL | tool tree |
|---|---|---|---|
| uninstrumented | 199.02s | — | — |
| `--coverage` (branch, parent only) | 224.34s | 56% of 9,715 | — |
| control (line-only, parent only) | 193.53s | 60% | 34% of 4,310 |
| `--coverage-subprocess` (line-only, 319 children) | 224.76s | **81%** | **78%** |

So of the 25 points between 56% and 81%, **4 are the branch denominator leaving and 21
are the subprocesses arriving**. In statements: the control never attributes 3,843 of
9,715, the subprocess run never attributes 1,841 — 2,002 statements the tests were
already executing and no report could see.

Per module, line-only both times:

| module | parent only | with subprocesses |
|---|---|---|
| `pds3/pdsarchives.py` | 16% | 90% |
| `pds4/pds4archives.py` | 15% | 80% |
| `pds3/pdslinkshelf.py` | 11% | 68% |
| `pds4/pds4linkshelf.py` | 9% | 64% |
| `_indexshelf_common.py` | 11% | 78% |
| `_linkshelf_common.py` | 18% | 75% |
| `_common.py` | 55% | 98% |
| `tools/show_opus_products.py` | 66% | 81% |
| `pds3/crlf.py` | 99% | 100% |

`crlf.py` and `re_validate.py` barely move, which is the expected result and a useful
negative control: PR-28 converted the `crlf` tests to in-process `main()` calls and
`test_re_validate.py` never ran a subprocess, so neither had anything to gain.

## The cost of each mode

Wall clock, `./scripts/run-all-checks.sh --sequential --pytest [--coverage…]`, and
pytest's own summary line inside it:

| mode | script total | pytest summary |
|---|---|---|
| (no coverage flag) | 3m 48s (whole run, all gates) | 199.02s |
| `--coverage` | 3m 53s | 224.34s |
| `--coverage-subprocess` | 3m 50s | 224.76s |

Re-run at the final commit, these reproduce: 201.25s, 225.56s and 224.49s, with the two
totals (56% and 81%) identical to the digit. Over the whole suite the two modes cost the
same 1.13x, because the suite is dominated by tests that are not tool subprocesses. The
difference between them shows on the arm that is:
`tests/holdings_maintenance/test_pds3_archives.py`, 13 ids, varying only how the children
are measured.

| tool subprocesses | core | branch | pytest summary |
|---|---|---|---|
| uninstrumented | — | — | 10.60s |
| measured | C tracer | yes | 79.68s |
| measured | C tracer | no | 79.94s |
| measured | `sysmon` | yes | 79.26s |
| measured | `sysmon` | no | **12.49s** |

**1.2x against 7.5x**, and only the pair is cheap. Dropping branch analysis alone buys
nothing (79.94s). Asking for `sysmon` alone buys nothing (79.26s) — `sys.monitoring`
cannot measure branches on this Python, so coverage warns `Can't use core=sysmon` and
falls back to the C tracer, and in a captured-stderr subprocess that warning reaches
nobody. That is why `_coverage_kind()` checks `sys.monitoring` directly and prints
`core sysmon UNAVAILABLE on this Python` when the request cannot be met.

The whole maintenance-tool arm, `tests/holdings_maintenance` (435 ids), in the mode this
PR delivers:

| run | pytest summary | data files |
|---|---|---|
| uninstrumented | 176.00s | — |
| `--coverage-subprocess` settings | 203.49s | 308 (1 + 307 children) |

**1.16x** on the arm that pays the whole cost. The same arm in the rejected
configuration — branch coverage, C tracer — was started and **stopped rather than
completed**: at 389s, already 2.2x what the entire arm takes uninstrumented, it had
reached 33% of its ids. That is a lower bound rather than a measurement, and it is
recorded as one; the completed measurement of that configuration is the 13-id module
above.

## Why the whole run has to be line-only

`coverage combine` refuses to mix the two kinds:

```
Can't combine statement coverage data with branch data
```

so a run cannot measure the parent with branches and the children without. That makes
line-only a property of `--coverage-subprocess` as a whole rather than of its children,
and it is why the mode announces itself: `Running pytest (-n 0 under coverage, line-only
coverage, core sysmon, subprocesses measured; holdings: full)`, and
`Coverage report passed: 81% of 9715 statements, line-only, 319 subprocesses`. The
`line-only` in that verdict is read back out of the combined data file
(`CoverageData.has_arcs()`), not out of the flags that were meant to produce it.

## How the two settings reach a child that has no command line

`--parallel-mode` and `--branch` are `coverage run` options, and a child started by
`coverage.process_startup()` is not started by `coverage run`. Its only input is
`COVERAGE_PROCESS_START`, which names a config file — so the two settings are written in
`pyproject.toml` as environment substitutions, which coverage resolves in config values:

```toml
branch = "${PDSFILE_COVERAGE_BRANCH-true}"
parallel = "${PDSFILE_COVERAGE_PARALLEL-false}"
```

One config file, read by the parent and by every child, and no second copy of `source`,
`omit` or `exclude_lines` anywhere. **The fallbacks are the repository's existing
defaults**, so with neither variable set nothing changes: branch coverage into one
unsuffixed data file. That is pinned by a test rather than asserted
(`test_the_configured_default_is_still_branch_coverage_in_one_data_file`), and confirmed
by the `--coverage` run above reporting branch columns.

## The `coverage combine` guard

`--coverage-subprocess` counts the data files before combining and prints the count. Zero
subprocesses is legitimate — the tool tests skip when the holdings root lacks the source
subset they declare, and a skipped test starts no subprocess — so that case prints
`Coverage: no subprocess ran, so this total is the same one --coverage produces` and
carries on. Zero data files *at all* fails: the pytest process itself must have been
measured.

## Reconciliation with `scripts/automated_tests/pdsfile_main_test.sh`

Read in full. What it does: `python -m coverage run -m pytest … --mode ns`, then
`python -m coverage run -a -m pytest tests/pds3file/ tests/rules/pds3/ --mode s`, then
`coverage report` and `coverage xml`; the XML is uploaded to codecov from the 3.13 leg
only (`.github/workflows/run-tests.yml`).

The two do not disagree, and this PR does not make them:

* **Same mechanism.** Both use `coverage run` — not `pytest --cov` — and both take every
  measurement setting from `[tool.coverage.*]`.
* **Same posture by default.** The data gate sets neither `PDSFILE_COVERAGE_BRANCH` nor
  `PDSFILE_COVERAGE_PARALLEL`, so it still gets branch coverage in one unsuffixed data
  file, which is what its `coverage run -a` append and its combine-free `coverage report`
  require. Its numbers are unchanged by this PR.
* **Subprocess measurement is off there, and stays off.** The hook keys on
  `COVERAGE_PROCESS_START`; nothing in CI sets it. The data gate pays none of the cost.
* **Two real differences, now written down** in a comment in that script and in
  `run-all-checks.sh`'s header: the data gate's total covers two passes (ns + s) where
  `--coverage`'s covers one, and the data gate measures the pytest process only.
* **`-n`**: the data gate passes none, so xdist is not active and finding 1 does not
  apply to it. This was checked rather than assumed.
* One thing it does *not* do, and this PR does not change it: it never runs
  `coverage erase`, so its first `coverage run` overwrites and the append follows. Left
  alone — changing the data gate's coverage posture is PR-37's business.

Also read: `run_tests_coverage.sh` in the repository root, which is untracked
(`.gitignore`) and refers to `pdsfile/pds3file/tests/`, a layout that no longer exists.
Not touched.

## Observation 4214

Rewritten in `critiques/observations-p3.md`. The 8.6x figure is kept and attributed —
it is a true measurement of the C tracer — and the conclusion drawn from it is replaced
by the five-row table above, the `combine` constraint, and the real trade: line-only at
1.2x against branch coverage plus a permanent blind spot. What remains open is the
posture (should the uploaded number include the tools, and at what target), which is
still PR-37's, not the mechanism, which now exists. The entry's other halves — the tool
tests not pinning log-path values, and the log-path builders having no holdings-free
coverage — are untouched and still open.

Register counts are unchanged: no entry was added or removed, and
`command grep -cE '^### [0-9]+\.'` still gives 8 / 0 / 15 / 131 / 50 = **204**.

## Gate results (this tree, holdings `/seti/opus/pdsdata`)

`./scripts/run-all-checks.sh --sequential`, exit **0**, every section read in full:

| Gate | Result |
|---|---|
| ruff check | passed, ratchet untouched (no entry added, widened or renamed) |
| ruff check (indentation, `--preview --select E111,E112,E113`) | passed |
| pytest `--mode ns` (holdings: full) | **1243 passed, 34 skipped** in 201.25s |
| pyroma | 10/10 |
| API-freeze | 1 passed |
| clean-install | passed (throwaway venv, runtime deps only, full module surface imports) |
| stubtest | Success: no issues found in 78 modules |
| Sphinx `-W` | exit 0, 0 problem lines, API reference 77 of 77 modules |
| Sphinx `-n -W` (own BUILDDIR) | exit 0, 0 problem lines, API reference 77 of 77 modules |
| PyMarkdown | passed, 2 files scanned |

Shelves-only, run separately:

| Suite | Result |
|---|---|
| `tests/pds3file tests/rules/pds3 --mode s` | **555 passed, 3 skipped** — baseline |
| `tests/pds4file tests/rules/pds4 --mode s` | **150 passed, 31 skipped** — baseline |

**Baseline movement, and why.** ns goes 1234 → **1243**: nine new ids, all in
`tests/holdings_maintenance/test_subprocess_coverage.py`, all `holdings_free`, and each
one a test of this PR's own plumbing (the environment builder, `ToolTree.env`, the hook
firing, the hook failing closed, and the two configured postures). No pre-existing id
changed outcome; the skip count is unmoved at 34, and both `--mode s` suites are
identical to baseline. Nothing under `src/pdsfile/` was touched by this PR at all —
`git diff --stat` names `pyproject.toml`, two scripts, three files under
`tests/holdings_maintenance/`, one new test module and one register file — so the
§6.2 behavior-preservation evidence is the unchanged suite outcome above.

## Coverage-mode outputs, for the record

`./scripts/run-all-checks.sh --sequential --pytest --coverage`, exit 0:

```
ℹ Pytest workers: 0 (coverage mode; -w 1 is overridden)
ℹ Coverage: pytest process only (--coverage-subprocess adds the tools)
ℹ Running pytest (-n 0 under coverage, branch coverage; holdings: full)...
1243 passed, 34 skipped, 5 warnings in 225.56s (0:03:45)
✓ Pytest passed
TOTAL   9715  3843  3542  337  56%
Wrote HTML report to htmlcov/index.html
✓ Coverage measured: 56% of 9715 statements, branch coverage
```

`./scripts/run-all-checks.sh --sequential --pytest --coverage-subprocess`, exit 0:

```
ℹ Pytest workers: 0 (coverage mode; -w 1 is overridden)
ℹ Coverage: pytest process and the maintenance-tool subprocesses
ℹ Running pytest (-n 0 under coverage, line-only coverage, core sysmon,
  subprocesses measured; holdings: full)...
1243 passed, 34 skipped, 5 warnings in 224.49s (0:03:44)
✓ Pytest passed
ℹ Coverage data files: 320 (1 pytest process + 319 measured children)
TOTAL   9715  1841  81%
Wrote HTML report to htmlcov/index.html
✓ Coverage measured: 81% of 9715 statements, line-only coverage, 319 measured children
```

**Parallel mode, which is the default, was run too** — `./scripts/run-all-checks.sh
--coverage-subprocess` with no scope, so the Sphinx build and the Markdown scan ran
concurrently with the measured pytest gate. Exit 0, all nine verdicts green, and the
coverage total was **81% of 9715, 319 measured children — identical to the sequential run**.
That is the check on finding 2: had the coverage variables been exported, Sphinx's
autodoc import of `pdsfile` would have landed in one of these two totals and not the
other.

`coverage combine` names every file it merges, which was 320 lines between the verdicts
in the first parallel run; it is now called with `-q`, and the data-file count carries
what those lines carried. Verified: 0 `Combined data file` lines in the run above.

Refusal path, exit 1:

```
$ ./scripts/run-all-checks.sh --coverage --sphinx
Error: --coverage measures the pytest gate, which this run does not schedule
(RUN_PYTEST=false, ENABLE_PYTEST=true)
```

## Documentation and rule records

`docs/dev_guide/dev_guide_ci.rst` gains a `Coverage` section — what each mode measures,
why the subprocess mode is opt-in, what it costs, and the fact that nothing in CI sets
`COVERAGE_PROCESS_START` — and its options sentence names the two flags;
`dev_guide_testing.rst` gains one sentence pointing there. Both Sphinx builds still
report 0 problem lines and 77 of 77 modules.

Two entries in `.cursor/rules/pdsfile_overrides.mdc` deviation (7), because
`python_testing.mdc` is in force from Phase 3 and this PR would otherwise leave two
undeclared deviations from it: coverage is produced with `coverage run` rather than the
`pytest-cov` section 2 asks for (which is what the repository already did, and what makes
`COVERAGE_PROCESS_START` usable), and `--coverage-subprocess` measures lines where
section 9 asks for branches (with the measurement that forces it, and the note that the
configured default is unchanged).

One incidental correction: the same dev-guide table recorded PyMarkdown as `not yet`
enabled. It has been enabled since PR-34, `ENABLE_PYMARKDOWN` defaults to true in the
script, and this PR's own gate run shows the scan passing over 2 files — so the row now
says `yes`. `environment.mdc` makes the script authoritative and the guide is describing
it, so leaving a false row in a table this PR edits was not an option.

## Scope held

No repo-wide coverage target was set and no `fail_under` was added — that is PR-37's.
The default coverage posture is unchanged. `api_manifest.json`, the manifest allowlist,
`scripts/dump_public_api.py`, `tests/api/test_api_freeze.py` and the golden tree were not
touched; the ruff ratchet was not widened; no committed file names an absolute holdings
path.

## The adversarial loop (§6.6)

ROUNDS_SUMMARY
