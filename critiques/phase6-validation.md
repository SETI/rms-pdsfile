# Phase 6 validation record

Phase 6 consolidates the pds3/pds4 maintenance-tool pairs onto a shared core.
Gates: PR-13's tool tests, a real-holdings run of each migrated tool diffed
against its pre-PR output, and the full-data suite. CLI names, flags, output
text, log formats, log paths and exit codes are frozen.

## How to read a section

Each PR gets one section. The numbers in it were measured at the commit the
section names, and re-measured whenever a review round changed code under
`src/pdsfile/`. Where a claim is a measurement, the command or script that
produced it is named. Where a claim is a judgement, it says so.

---

## PR-25 — `refactor: shared maintenance-tool core (_common.py) + archives pair`

**Base:** `rewrite` at `ab1fa3b` (the PR-24 merge).
**Branch:** `pr-25-common-core`.
**Date:** 2026-08-04; re-measured in full 2026-08-05 after the owner's rulings.
**Sub-plan:** [`plans/2026-08-04-pr-25-subplan.md`](../plans/2026-08-04-pr-25-subplan.md).
**Deviations addendum:**
[`plans/2026-08-04-pr-25-deviations-addendum.md`](../plans/2026-08-04-pr-25-deviations-addendum.md)
— ruled on by the owner 2026-08-05; its new §7 (the log time-tag race) still needs
the owner's eye (§6.4).

**Every number in this section was re-measured at the final commit.** The owner's
rulings of 2026-08-05 widened the PR: `ToolSpec` became a `@dataclass` and gained
two fields, `hashfile()` / `move_old_<kind>()` / `LOGDIRS` moved into `_common.py`
out of six more tool modules, and a log time-tag race in the core was fixed.
Nothing here is carried over from the earlier rounds.

This PR is behavior-preserving **except for three deliberate changes**, each
pinned by a test and each confined to the ids §3 lists:

1. The three pds3 tools that shadowed `LOGDIRS` with a `main()` local no longer
   do, so the versioning step those tools have always contained starts running
   (deferred observation 81; owner-decided 2026-08-04).
2. `move_old_checksums`, now one copy, passes `force=True` to both its log lines.
   pds3 already did; **pds4 did not**, so a `pds4checksums` run inside a scope
   that caps `info` now reports the versioning where the cap could previously
   silence it (deferred observation 95; owner-decided 2026-08-05). §11.4.
3. A tool's two log paths now carry **one** time tag rather than two readings of a
   one-second clock (§11.5). Visible only when two calls straddle a second
   boundary, which is the bug.

Everything else the migration and the move touch is required to be invisible,
with the one unavoidable exception §5.1 measures and §12's row 6 names.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, the main tree's venv (`/seti/all_repos/rms-pdsfile/venv`), `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`, `PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings`, `PDSFILE_TEST_HOLDINGS=full` — the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at `ab1fa3b` (`/seti/all_repos/rms-pdsfile-pr25/base`), same interpreter, same holdings |
| Branch tree | `/seti/all_repos/rms-pdsfile-pr25/work` on `pr-25-common-core` |
| Third tree | a `git worktree` detached at `b84fe75` (`/seti/all_repos/rms-pdsfile-pr25/prev`) — the last commit before the six-module move, and so the right baseline for §5.2, which asks whether that move changed those six tools |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml`; `PYTHONPATH=<tree>/src` on each |
| ruff | 0.15.22 (the development venv) |
| pdslogger | rms-pdslogger 3.2.1 |

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — `pytest tests/api/`, 26 ids. No `holdings_maintenance` module is in the manifest, so this gate is silent about this PR's edits; it is run to prove nothing leaked out of them |
| Full-data suite, `--mode ns` | **passed** — **947 ids** vs the baseline's **892**; the 55 extra are the new tests, listed one by one in §3, and nothing else moved |
| Full-data suite, `--mode s` | **passed** — 558 ids, set diff **empty** (§3) |
| Phase-6 per-tool gate, archives pair vs `ab1fa3b` | **passed with one recorded difference** — 36 invocations and 39 log files per tree, 4,005 / 4,009 normalized lines; the six artifacts that differ differ only in Python traceback frames (§5.1) |
| Per-tool gate, the six moved-from tools vs `b84fe75` | **passed, no difference at all** — 32 invocations and 76 log files per tree, 3,594 normalized lines on both sides, **32 of 32** stdout captures and **76 of 76** log files identical (§5.2) |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet forgives **eighteen** fewer findings and gained no code slot (§9) |
| `ruff check --preview --select E111,E112,E113 …` | **passed**, no findings |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full manifest module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh -c -s`, no holdings env vars) | **passed**, **143 passed / 804 skipped**, pyroma 10/10 — against the baseline's 92 passed / 800 skipped. The 51 extra passes are the two new `holdings_free` modules, which must run on a machine with no holdings; the 4 extra skips are the `full_holdings` regression tests (§3) |
| PR-13 tool tests, with holdings | **passed** — inside the `ns` run, `tests/holdings_maintenance/` collects **154** ids (111 at the baseline) and `tests/core/` **55** (43), all passing |
| Adversarial review loop | `critiques/pr-25/round-<k>.md` (§14) |

### 3. Full-data suite — 55 added ids, nothing else

Both passes were run on the baseline worktree and on the branch with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to `classname::name` plus its outcome, and the two mappings were
compared as sets (`scratchpad/compare_runs.py`, which prints the symmetric
difference of the id sets, the ids whose outcome changed, and the symmetric
difference of the *passed* sets separately, so a test flipping in either
direction is visible).

| Run | baseline `ab1fa3b` | `pr-25-common-core` | id-set diff |
|---|---|---|---|
| `--mode ns` | 858 passed / 34 skipped (**892 ids**) | 913 passed / 34 skipped (**947 ids**) | **+55, all new and all passing** |
| `--mode s` | 555 passed / 3 skipped (**558 ids**) | 555 passed / 3 skipped (**558 ids**) | **empty** |

Ids whose outcome changed: **0** in both modes. Ids removed: **0** in both modes.
The 55 additions are three groups, and every one of them is a test this PR's own
changes required:

| Group | ids | What it pins |
|---|---:|---|
| `tests/core/test_log_path_timetag.py` | **12** | the log time-tag pin: 8 on the mixin (unpinned pair disagrees / pinned pair agrees, a rule subclass sees the pin, release on exit, release on a raise, nesting restores, the class dictionary is left as it was found, a flavor pinned once still sees a pin taken above it, the two flavors pin independently) and 4 parametrized over the two archives specs through `_common.log_paths_for` |
| `tests/holdings_maintenance/test_common_versioning.py` | **39** | the moved versioning code: **30** asserting that none of the six tool modules still defines its own `LOGDIRS`, `hashfile`, `move_old_checksums`, `move_old_info` or `move_old_links` (5 names × 6 modules), **3** that each mover versions one past the highest already there, **3** that a process with no recorded log directory versions nothing, and **3** for the `force=True` decision — 1 that the checksum mover still reports under an `{'info': 0}` cap and 2 that the shelf movers do not |
| the deferred-81 regression tests | **4** | `test_pds3_checksums`, `test_pds4_checksums`, `test_pds3_infoshelf`, `test_pds3_linkshelf`, each `…versions_the_…file_it_replaces` |

That is 12 + 39 + 4 = **55**, and the id-set diff contains nothing else. **Every
behavior change this PR makes is confined to those ids.** The archives migration
— still the bulk of the diff — moved no id and changed no outcome, and neither did
the move of the versioning code out of the six tool modules: apart from the ids
above, all 892 baseline ids are present with the same outcome.

`--mode s` does not run `tests/holdings_maintenance/`, which is why the four new
ids appear only in `ns`; the driver script's comment explains that the tools run
in their own subprocesses and `--mode` cannot reach them.

The hosted no-holdings run is the same arithmetic seen from the other side:
baseline 92 passed / 800 skipped (892), branch 143 passed / 804 skipped (947). The
51 new `holdings_free` ids **pass** there rather than skipping, which is the point
of that marker — they build their own inputs — and the 4 `full_holdings` ids skip.

### 4. Which source each run actually imported, proved rather than assumed

The only usable interpreter is the main tree's venv, whose editable install puts
`/seti/all_repos/rms-pdsfile/src` on `sys.path`. A worktree run could therefore
silently measure the **main tree's** source and make the entire comparison
vacuous. `PYTHONPATH` was set per run, and then
`coverage.CoverageData.measured_files()` was read for its **absolute** paths:

| Run | files measured | all under | `_common.py` measured |
|---|---|---|---|
| baseline `ns` | 72 | `/seti/all_repos/rms-pdsfile-pr25/base/` (72 of 72) | **no — the file does not exist at `ab1fa3b`** |
| baseline `s` | 72 | `/seti/all_repos/rms-pdsfile-pr25/base/` (72 of 72) | **no** |
| branch `ns` | 73 | `/seti/all_repos/rms-pdsfile-pr25/work/` (73 of 73) | **yes** |
| branch `s` | 73 | `/seti/all_repos/rms-pdsfile-pr25/work/` (73 of 73) | **yes** |

Re-read at the final commit, the branch run also measured
`work/src/pdsfile/_derived_paths.py` and all six moved-from tool modules
(`pdschecksums.py`, `pdsinfoshelf.py`, `pdslinkshelf.py` and their pds4 twins)
under the branch worktree, and **zero** files outside it. The baseline run
measured 72 files, every one under the base worktree, and no `_common.py`.

Not one measured file came from `/seti/all_repos/rms-pdsfile/src`. `_common.py`
is the decisive marker: it is a new file, so a run that had leaked into the main
tree's editable install would have shown the main tree's paths in the "all under"
column on both sides.

One caveat, stated so the table is not read as more than it is: `[tool.coverage.run]`
sets `source = ["pdsfile"]`, so an unexecuted module under the package is also
recorded. The table therefore proves **which tree** each run read, not that every
listed file ran. That is exactly the vacuity this check exists to rule out. The
proof that the tools' own code ran is the tool suite and §5's tool runs.

Coverage does **not** measure the tool subprocesses (`COVERAGE_PROCESS_START` is
unset; deferred observation 8 records this), so no claim anywhere in this section
rests on line-level coverage of a tool.

A word on how easy this is to get wrong: the first attempt at re-running
`tests/holdings_maintenance/` in this round set `PYTHONPATH=src` **relative**, and
`support.run_tool` spawns each tool with `cwd=` a temporary tree — so `src`
resolved to a directory that does not exist, the editable install won, and three
tests failed against the **main tree's** unmodified source. The failure was the
harness, not the code; it is recorded because a run that had happened to pass that
way would have been silently vacuous.

### 5. The Phase-6 per-tool gate: real-holdings runs, diffed against pre-PR

Two runs, against two different baselines, because this PR does two different
things to two different sets of modules:

* **§5.1** — the **archives pair**, which was migrated onto the shared driver,
  diffed against `ab1fa3b`. This is the gate the plan asks for.
* **§5.2** — the **six checksum/infoshelf/linkshelf tools**, which were not
  migrated but had `hashfile()`, `move_old_<kind>()` and `LOGDIRS` moved out of
  them, diffed against **`b84fe75`** — the last commit before that move, and so
  the baseline that isolates it. Diffing them against `ab1fa3b` instead would fold
  in the deferred-81 versioning change, which is a separate, already-recorded
  behavior change, and would tell us nothing about the move.

#### 5.1 The archives pair, against `ab1fa3b`

The Phase 6 preamble requires "a real-holdings validate run of each migrated tool
against at least one real volume/bundle, recorded in
`critiques/phase6-validation.md`", and §6.2(2) requires a real-volume tool run
"diffed against the pre-PR output (`.py` sidecars and logs, mtime-normalized)".
This is the gate that covers **log text**, which the full-data suite (a pass/fail
set) and PR-13's goldens (archive members, md5 files, shelf sidecars — not logs)
are both blind to.

**Inputs.** `scratchpad/tool_run_diff.sh` copies, with `cp -a` so modification
times are preserved:

- the real PDS3 volume `volumes/HSTNx_xxxx/HSTN0_7176` (6 files, 984 KB);
- three real PDS4 bundles — `uranus_occ_u36_sso_230cm`,
  `uranus_occ_u2_teide_155cm`, `uranus_occ_u23_teide_155cm` — into a
  `bundles/uranus_occs_earthbased/` bundle set.

Everything is copied into a temporary disk under `/tmp`, so the runs write
archives and logs there and never into the shared holdings tree. The whole
sequence runs twice, once with `PYTHONPATH=<base>/src` and once with
`PYTHONPATH=<work>/src`.

The temporary disk has a **fixed path**, `PYTHONHASHSEED` is pinned, and the
harness sleeps one second between invocations — a log file name carries a
one-second time tag, and two invocations inside the same second would share a
file. Pinning the hash seed is not enough to align the two runs' `logfiles` set
iteration, because the two strings in that set contain the run's own time tag and
so hash differently from one run to the next; the comparator sorts each run of
consecutive `Log file:` lines instead. That ordering is not a property of the
code — it flips between two runs of the **baseline** tree as readily as between
base and head — and it is recorded as deferred observation 99.

**The 36 invocations per tree** — 20 for `pdsarchives`, 16 for `pds4archives` —
cover both tools across all five tasks and the paths around them.

Shared by both tools (14 each): `--validate` with no archive present (which is
the pds3 "File does not exist" critical path and, for pds4, a `FileNotFoundError`
out of `tarfile.open`), `--initialize`, `--validate` again, `--initialize` a
second time (the already-exists error), `--repair`, `--update`, `--reinitialize`,
`--quiet`, a two-flag invocation, an archives path and a checksums path (the two
`reject_checksum_and_archive_paths` branches), a missing task, `--help`, and one
`--log <root>` invocation.

`pdsarchives` adds six: a **volset** path (the expansion-plus-`blankline` path),
a nonexistent path, a `PDS_LOG_ROOT` invocation, and three that corrupt the real
volume — truncate a table to 100 bytes and `--validate` (which renders
`Byte count mismatch: 100 (filesystem) vs. 746315 (tarfile)`), move a label's
modification time and `--validate` (`Modification time mismatch: 1500000000.0
(filesystem) vs. 1588638541.0 (tarfile)`), then `--reinitialize` to rebuild. Both
corruptions use pinned times, so the rendered numbers are the same on both sides.
Those two messages are the ones the `UP031` rewrite touched (§9), which is why
they are in the diffed evidence rather than left to the tool tests' prefix
assertions.

`pds4archives` adds two: a single-bundle path (which reaches the bare `raise` of
deferred entry 2) and a `PDS_LOG_ROOT` invocation.

The two `--log` / `PDS_LOG_ROOT` invocations matter out of proportion to their
number: they are the only ones where `run_main`'s top-level `if args.log:` block
runs — the one place the spec's handler-factory tuple is applied **at the log
root**, and so the only place pds4's `warning_handler`-before-`error_handler`
ordering is exercised at that scope — and the only ones where `logfiles` has two
elements and each run writes its log in two places. The tuple is also applied
per target (`_common.py:276-277`), which every invocation reaches, so the
ordering itself is not unexercised elsewhere; what these two add is the log-root
branch and the two-element `logfiles`.

**The comparison.** `scratchpad/compare_toolruns.py` normalizes the temporary
disk path, the source tree path, wall-clock timestamps, elapsed times, and the
time tag inside a log file name, then compares stdout capture by capture and log
file by log file. Traceback **line numbers** are normalized — no refactor can
hold those fixed — but traceback **file names are not**, so a frame that moved to
another module shows up as a difference. That is deliberate, and it is what the
one difference below is.

| | baseline `ab1fa3b` | `pr-25-common-core` | identical after normalization |
|---|---:|---:|---|
| stdout captures | 36 | 36 | **34 of 36** |
| log files written | 39 | 39 | **35 of 39** |
| normalized lines compared | 4,005 | 4,009 | — |

The branch's four extra lines are the disclosed traceback frames themselves:
the shared driver contributes two lines where the pre-PR stack had none, in each
of the two stdout captures that carry an outermost traceback.

**The six differing artifacts — two stdout captures and four log files — differ
in exactly one thing, and it is the same thing in all six.** Aggregating every
changed line across all six:

```
-  File ".../pds4/pds4archives.py", line <LINENO>, in main
-    validate(pdsdir)                     (or: initialize(pdsdir))
+  File ".../holdings_maintenance/_common.py", line <LINENO>, in run_main
+    tasks[args.task](pdsdir)
```

plus, in the two outermost stdout tracebacks, the extra frame
`pds4archives.py, in main / _common.run_main(SPEC, TASKS, sys.argv)`. Nothing
else changed anywhere: same message, same level, same counts, same summary lines,
same log file names, same exit codes. All six are pds4 artifacts, because
`pds4archives` is the only one of the two tools that raises in this capture set —
it hits deferred entries 1 and 2 — and **no pds3 artifact differs at all**.

This is not avoidable by any implementation. A Python traceback names the frames
on the stack, and the plan's own design puts a shared driver frame there.
`plans/2026-08-04-pr-25-deviations-addendum.md` §6 puts it in front of the owner.


#### 5.2 The six moved-from tools, against `b84fe75`

The owner's ruling widened this PR's file scope to `pds3/pdschecksums.py`,
`pds3/pdsinfoshelf.py`, `pds3/pdslinkshelf.py` and their pds4 twins, for one move:
`hashfile()`, `move_old_checksums()`, `move_old_info()`, `move_old_links()` and
the `LOGDIRS` list they read now live one copy each in `_common.py`. Those six
tools are **not** on the shared driver — they have their own `main()` and do not
call `run_main`, `ToolSpec` or `build_arg_parser` — so nothing about them should
change. `scratchpad/shelf_run_diff.sh` is the measurement of that claim.

**Inputs.** The same real PDS3 volume `HSTN0_7176` and one real PDS4 bundle,
`uranus_occ_u2_teide_155cm`, copied with `cp -a` into a temporary disk with a
fixed path, `PYTHONHASHSEED` pinned and a one-second sleep between invocations,
for the same reasons as §5.1.

**The 32 invocations per tree** — 6 for `pdschecksums`, 6 for `pds4checksums`, 5
for each of the other four — are chosen to *reach the moved code*, which a plain
`--validate` sweep would not:

* `hashfile` runs on every file of every checksum invocation.
* Each tool is driven `--initialize`, `--validate`, then `--reinitialize` **twice**
  for the checksum pair and once for the shelf pairs, so `move_old_*` runs against
  a file that already exists and the version number has to advance rather than
  just appear.
* Each tool gets one `--log <root>` invocation, which is the only shape in which
  `LOGDIRS` holds **two** directories, so a superseded file is versioned into both
  and the "moved to" line is written twice.
* `--help` for each, so the CLI text is in the diff.

The infoshelf runs depend on the checksums written by the runs before them, which
is why the sequence is ordered rather than six independent blocks.

**Result.**

| | `b84fe75` | `pr-25-common-core` | identical after normalization |
|---|---:|---:|---|
| stdout captures | 32 | 32 | **32 of 32** |
| log files written | 76 | 76 | **76 of 76** |
| normalized lines compared | 3,594 | 3,594 | — |

**Nothing differs.** Not a line, and not the line count either.

**Two normalizations were added for this run, and both are the clock or the hash,
not the code.** The comparator (`scratchpad/compare_runs3.py`) additionally:

1. normalizes a bare `YYYY-MM-DD HH:MM:SS` stamp inside a message body. Only the
   infoshelf tools write one — `Checksum file modification date = …` is the mtime
   of a checksum file the run itself wrote moments earlier — and it is the clock
   in exactly the sense the line-head timestamps are;
2. sorts each run of consecutive `… moved to` lines, the same treatment the
   `Log file:` lines already got and for the same reason. `LOGDIRS` is built from
   the `logfiles` **set**, whose two members contain the run's own time tag, so its
   order is `str.__hash__` of strings that differ between any two runs. Deferred
   observation 99; pre-existing, and it flips between two runs of the same tree.

Before those two normalizations the comparison reported 12 differing stdout
captures and 18 differing log files; every one of them was one of those two
classes, verified line by line — each `-` line had an identical `+` line elsewhere
in the same block, or differed only in a wall-clock stamp.

**A normalization that hides a real change is worse than no gate, so both were
controlled.**

* *The widened comparator still catches what it caught before.* Re-running §5.1's
  archives comparison through `compare_runs3.py` reports exactly the same result
  as before — 34 of 36 stdout captures, 35 of 39 log files, the same six
  traceback-frame differences. Neither new normalization touches them.
* *A deliberate mutation is caught.* `move_old_info`'s "moved to" line was changed
  from `logger.info(noun + ' moved to', dest)` to
  `logger.info(noun + ' moved to ' + dest)` — one character class of change, the
  exact slip a careless three-way merge of the movers would have made (deferred
  observation 100) — and the harness was re-run against the mutated tree. The gate
  reported **4 differing stdout captures and 6 differing log files**, and every one
  of them was a `pdsinfoshelf` artifact. So the 32-of-32 / 76-of-76 above is a
  measurement, not an artifact of over-normalizing.

**What this run does *not* show, and why that is expected.** The `force=True`
decision of deferred entry 95 is invisible here. `force=True` only matters inside
a scope whose `limits` cap `info`, and none of these 32 invocations opens one — so
the pds4 checksum tool emits the same two lines either way. That is why the
`force=True` change is pinned by a constructed unit test with an explicit
`{'info': 0}` cap (§11.4) rather than by this gate. Recorded so the absence of a
difference here is not read as evidence that the behavior did not change.

### 6. What moved into `_common.py`, and what deliberately did not

The two archives modules were 1,155 lines and 623 statements between them, most
of it the same code written twice. After the migration:

| File | lines before | lines after | statements before | statements after |
|---|---:|---:|---:|---:|
| `pds3/pdsarchives.py` | 565 | **260** | 307 | **140** |
| `pds4/pds4archives.py` | 590 | **280** | 316 | **146** |
| `_common.py` | — | **676** | — | **316** |
| total | 1,155 | **1,216** | 623 | **602** |

`_common.py`'s 676 lines and 316 statements are **not** all the archives pair's.
It grew by **190 lines / 103 statements** over `b84fe75`, and that growth splits
into the "Checksum and shelf file tools" section — **151 lines / 93 statements**,
the code moved out of six other tools, accounted for in §6.1 — and **39 lines / 10
statements** for everything else this round added: the `@dataclass` conversion,
the two new `ToolSpec` fields with their docstring paragraph, `log_paths_for`, and
the imports the move needed. Measured against the archives pair alone the shared core is
unchanged at **213 statements**, where the pair shed **337**: a net **−124
statements (−20%)**.

Counting statements as well as lines is deliberate — line counts move when a
docstring is added, statement counts do not.

Function by function (statements, excluding the `def` itself):

| Unit | pds3 before | pds4 before | after |
|---|---:|---:|---|
| `load_directory_info` | 43 | 43 | **44 in `_common`, one copy** |
| `validate_tuples` | 35 | 35 | **36 in `_common`, one copy** |
| the `archive_filter` closure (inside `write_archive`) | — | — | **22 in `_common.make_archive_filter`**; `write_archive` drops 44→26 (pds3) and 52→34 (pds4) |
| `main()` | 80 | 78 | **1 + 1**, delegating to `_common.run_main` (53) + `build_arg_parser` (12) + `reject_checksum_and_archive_paths` (7), plus 19 statements of per-tool spec callables and 15 for `ToolSpec` |
| `read_archive_info` | 34 | 31 | **unchanged, one copy each** |
| `write_archive` body | 44 | 52 | **26 / 34, one copy each** |
| the five task functions | 44 | 50 | **44 / 50, unchanged** |

**What stayed in the tool modules, and why.** The rule applied throughout: a
difference belongs in `ToolSpec` only if it is *data* — a class, a string, a log
level, a tuple of handler factories, or a callable that computes a path or a
target list. **A difference in control flow is not data, and if sharing a
function would need a boolean flag whose only job is to re-create one side's
quirk, the function is not shared.**

- **`read_archive_info`** — pds3 opens with an existence guard
  (`pdsarchives.py:41-43`: `logger.critical('File does not exist', tarpath)` then
  `return []`) that pds4 does not have. pds3 reaches it because `validate` calls
  `read_archive_info` on a path it never checked; pds4 only ever passes paths
  from `archive_paths()`, where a missing file raises out of `tarfile.open` —
  which §5's capture 15 exercises. Sharing this needs a flag that exists purely
  to reinstate one side's guard, and forcing either behavior on the other tool is
  an observable change. Left in place, one copy each.
- **`write_archive`** — pds3 writes one tarball per volume from a single
  `archive_path_and_lskip()`; pds4 walks `archive_paths()`, writes several, and
  adds each of `archive_dirs()[tarpath]` under its own basename. This is not a
  parameterization of one shape, it is two shapes.
- **The five task functions** — beyond the structural split above they differ in
  at least six observable ways, each verified against `ab1fa3b`: pds3
  `repair`/`update` pass `force=True` to `logger.info` and pds4 does not; pds3
  `update` calls `write_archive(clobber=True)` where pds4 calls `clobber=False`;
  pds3 `repair` returns after one decision where pds4 loops and `continue`s; pds4
  `update` accumulates `wrote_any` where pds3 returns immediately; pds4
  `validate`/`repair` filter `dir_tuples` per tarball; pds4 `validate`
  short-circuits on the first invalid tarball. Left in place.
- **Task-function signatures** were deliberately *not* unified. pds3 has
  keyword-only `logger`/`limits` and pds4 has a positional `logger` and no
  `limits`. `run_main` calls `tasks[args.task](pdsdir)` with one positional
  argument, which both forms accept, so unification would buy nothing — and
  `pdsarchives.validate(temp_pdsdir, limits=ARCHIVES_LIMITS)` is called from
  `re_validate.py:102`, which ground rule 7 freezes.

**What `_common.py` holds**, in four banner-separated sections:

| Section | lines | Holds |
|---|---:|---|
| module header | 31 | the file's own comment block |
| tool specification | 72 | `LOGROOT_ENV`, `BACKUP_FILENAME`, `ToolSpec` |
| command line | 208 | `TASK_FLAGS`, `LOG_HELP`, `QUIET_HELP`, `build_arg_parser`, `reject_checksum_and_archive_paths`, `log_paths_for`, `run_main` |
| archive tools | 214 | the four `*_LIMITS` defaults, the description/help templates, `load_directory_info`, `make_archive_filter`, `validate_tuples` |
| checksum and shelf file tools | 151 | the three `*_LOGNAME` constants, `LOGDIRS`, `set_log_dirs`, `hashfile`, `move_old_checksums`, `move_old_info`, `move_old_links` |
| **total** | **676** | |

#### 6.1 The versioning code moved out of six tools

The owner overruled the deferral recorded in the addendum's §3 ("if a future PR is
going to need a field, might as well add it now" applies to the code too), so
`hashfile()`, the three `move_old_<kind>()` functions and the `LOGDIRS` list they
read are now one copy each. The six tool modules that held them shrank:

| File | lines at `b84fe75` | lines now | statements at `b84fe75` | statements now |
|---|---:|---:|---:|---:|
| `pds3/pdschecksums.py` | 924 | **869** | 497 | **462** |
| `pds3/pdsinfoshelf.py` | 943 | **900** | 504 | **475** |
| `pds3/pdslinkshelf.py` | 1,784 | **1,735** | 666 | **632** |
| `pds4/pds4checksums.py` | 897 | **842** | 484 | **451** |
| `pds4/pds4infoshelf.py` | 925 | **882** | 498 | **469** |
| `pds4/pds4linkshelf.py` | 1,278 | **1,229** | 711 | **677** |
| total | 6,751 | **6,457** | 3,360 | **3,166** |
| `_common.py` versioning section | — | **151** | — | **93** |

**−294 lines and −194 statements out of the tools, +151 / +93 back in as one
copy: a net −143 lines and −101 statements.** The saving is smaller than the raw
duplication because the versioning code was six copies of four functions, and the
four functions themselves survive; what is gone is the sixfold repetition.

Each module also lost the imports the move stranded — `shutil` in all six,
`hashlib` in the two checksum tools, `glob` in the two linkshelf tools — and each
gained one, `from pdsfile.holdings_maintenance import _common`. Each module's
`LOGNAME` now reads the shared constant (`LOGNAME = _common.CHECKSUMS_LOGNAME`
and its two siblings) rather than repeating the string, because the moved
functions' `logger=None` fallback needs the name and there should be one copy of
it; both flavors of a kind already used the same string, so no value changed.

`main()` in each module now calls `_common.set_log_dirs(logfiles)` where it used
to assign and append to a module-level list. That is where the `global LOGDIRS`
declaration this PR added went: the list is shared state and now has one setter,
which is the same shape as `PdsFile.set_log_root`.

**Three divergences had to be resolved to make one copy, and each is a behavior
change on the side that lost.** They are enumerated in the addendum §3 and
summarized here: `move_old_checksums` takes the pds3 `force=True` on both its log
lines (§11.4, deferred entry 95 — the one observable change); `hashfile` takes the
pds4 `with`-block spelling, which leaks no descriptor and computes the same digest
(and removes one `SIM115` from the ratchet); and `move_old_checksums` keeps the
pds3 keyword-only `logger`, which every call site in both trees already used.
`move_old_info` and `move_old_links` needed no decision: their pds3 and pds4
twins are **byte-identical to the character**, verified by extracting each with
`ast` from `b84fe75` and diffing.

**"Verbatim" needs one qualification.** The plan says "moved verbatim, one copy",
and the twin comparison above is exact, but each moved function differs from the
copies it replaces in **two lines**: `LOGNAME` became the shared
`_common.<KIND>_LOGNAME` (the same string, one source of truth), and
`'%03d' % new_version` became `f'{new_version:03d}'` — required, because
`_common.py` must be ruff-clean and can carry no `UP031` ignore, and identical
output for every `int`. `move_old_checksums` differs in those two plus the
signature and the two `force=True`. Nothing else in any of the four functions
changed.

**What was not merged: the three kinds stay three functions.** They are not one
function with data differences. Two of their three differences are data (the noun
in the messages; which sidecars are copied). The third is a call shape: the "moved
to" line is `logger.info(noun + ' moved to', dest)` in the checksums and info
movers and `logger.info(noun + ' moved to ' + dest)` in the links mover, and
`pdslogger` 3.2.1 renders those differently — `… moved to: /path` against
`… moved to /path`, and only the two-argument form's path is subject to
`replace_root`. Collapsing them would need a flag choosing between two call
shapes, and either choice would rewrite frozen log text for two tool families.
That is the hard stop the addendum's own rule calls for, taken rather than
forced; §5.2's mutation control measures what forcing it would have cost.

**What that leaves, stated plainly rather than left to the deferred entry.** The
three functions still share **18 identical non-blank lines** once variable names
are set aside — the existence guard, the basename/`splitext` pair, the whole
`for log_dir in LOGDIRS` version-numbering block, the `shutil.copy` and the
`from_logged` latch — three copies of them, in the one section of the one file
whose purpose is one copy each. The stop is real but it is narrower than the
whole question: sub-plan §2 forbids "a **boolean flag** whose only job is to
re-create one side's quirk", and the same document admits "a **tuple** of handler
factories" as data, so a per-kind emitter callable is a shape the rule does not
reach. PR-25 did not take it, because its instruction for this move was
"verbatim" and because the version-numbering block can be lifted without touching
any log text — which is a smaller, safer change for the PR that has all the
callers in front of it. Deferred entry 100 owns it.

### 7. The `ToolSpec` fields, and the rule that admitted each

`ToolSpec` is a `@dataclass(kw_only=True)`, which is what the plan specified. An
earlier revision of this PR made it a plain keyword-only class, on the reading
that overrides deviation (1)'s annotation ban rules out a construct that declares
its fields by annotation; the owner lifted the ban for this case on 2026-08-05
and deviation (1) now says so, so the deviation is withdrawn rather than argued
(addendum §2). Fifteen field annotations, and the spec holds exactly what it held.

**Two generated behaviors came with the decorator**, neither of which any caller
in the tree uses, both recorded because "no other change" would be false: the
dataclass generates `__eq__` and `__repr__`, and because it does, Python sets
`__hash__ = None` — so `hash(SPEC)` now raises `TypeError: unhashable type:
'ToolSpec'` where the plain class hashed by identity. Nothing in the tree hashes a
spec or puts one in a set (checked), and construction is still keyword-only with
every field required except the two that default.

| Field | pds3 | pds4 | Why it is data |
|---|---|---|---|
| `progname` | `'pdsarchives'` | `'pdsarchives'` | a string; both halves already print `pdsarchives` and log under `logs/pdsarchives/` |
| `logname` | `'pds.validation.archives'` | same | a string |
| `pdsfile_cls` | `Pds3File` | `Pds4File` | a class |
| `unit` | `'volume'` | `'bundle'` | a string: names the positional, and is substituted into the help text |
| `holdings_sentinel` | `'/holdings/'` | `'/pds4-holdings/'` | a string. **Read nowhere today** — see below |
| `index_ext` | `'.tab'` | `'.csv'` | a string. **Read nowhere today** — see below |
| `file_log_level` | `'info'` | `'normal'` | a level name. **Not interchangeable** — see below |
| `description`, `task_help`, `positional_help` | the shared archive templates | same | strings |
| `log_path_for` | `log_path_for_volume('_links', …)` | `log_path_for_bundle('_archives', …)` | a callable that computes a path |
| `expand_target` | volume, else the volset's directory children | the PdsFile itself | a callable returning the target list |
| `handler_factories` | `(error_handler,)` | `(warning_handler, error_handler)` | a tuple of factories, applied in order |
| `lskip_for` | `archive_path_and_lskip()[1]` | `len(root_)+len(category_)+len(bundleset_)` | a callable returning an int |
| `extra_arguments` | `()` | `()` | the plan's hook for tool-specific flags (`--archives`, `--infoshelf`); empty here because the archives pair has none |

**Two fields are carried and not read.** The owner ruled on 2026-08-05 that a
field a future PR will need should be added now, so `holdings_sentinel` and
`index_ext` are fields. Neither archives tool reads either: the sentinel belongs
to the checksums and infoshelf tools, the extension to the indexshelf tools. Both
are properties of the **flavor**, not of a tool, so each archives spec carries its
flavor's value, and the `ToolSpec` docstring says in as many words that they are
declared for tools not yet on this core. Deferred entry 97 records that the
unexercised set is now three fields rather than one, so a later dead-code sweep
does not read them as an oversight.

The plan's parenthetical values were **checked against the code rather than taken
on trust, and both are right.** `holdings_sentinel` is `'/holdings/'` at
`pdschecksums.py:697`, `pdsdependency.py:1107` and `pdsinfoshelf.py:734`, and
`'/pds4-holdings/'` at `pds4checksums.py:669,680` and `pds4infoshelf.py:715,726`;
each of those tools `partition()`s a command-line path on it, and **four** of
them — `pdschecksums.py:708`, `pdsinfoshelf.py:745`, `pds4checksums.py:680` and
`pds4infoshelf.py:726` — also rebuild an archives path by concatenating it back,
so the value is the literal including both slashes. Note for the PR that migrates
them: those four build `<sentinel>archives-`, so the field is a *component* of
that literal rather than the whole of it. `index_ext` is `'.tab'` at
`pdsindexshelf.py:459,461,464,473` and `'.csv'` at
`pds4indexshelf.py:445,447,450,459`, used both as a `glob` suffix and in an
`endswith` test, so the value includes the dot. One thing the plan does not say
and the code assumes: the sentinel hard-codes the **name** of the holdings
directory, so a root not called `holdings` or `pds4-holdings` fails those five
tools' `Not a holdings subdirectory` guard whatever the environment variables
say. Pre-existing, not this PR's to change, recorded as deferred entry 101 so the
new field is not mistaken for a configuration point.

**`info` and `normal` are different levels, and the difference is observable.**
Measured directly against `pdslogger` 3.2.1 — four calls in a scope opened with
`limits={'info': 2}`:

| Called | Lines emitted | Closing summary |
|---|---|---|
| `logger.info` ×4 | 2, then `Additional INFO messages suppressed` | `2 INFO messages reported of 4 total` |
| `logger.normal` ×4 | all 4 | `4 NORMAL messages` |

Every line also renders its own level name (`| INFO |` vs `| NORMAL |`), which
§5's captures show directly. So the level had to be carried, not converged:
converging it would rewrite frozen log text *and* change how many lines a pds4
run emits. A consequence worth naming — `pds4archives`'s `{'info': N}` limits
constrain nothing, because it logs `normal`. That is recorded as new deferred
observation 92, flagged for the owner; it is not this PR's to fix.

### 8. Evidence the CLI surface is unchanged

The task flags are five independent `store_const` actions into one `task`
destination, so passing more than one is accepted and the last wins. Turning that
into an `add_mutually_exclusive_group` would make a two-flag invocation an
argparse hard error — an observable CLI change. Three independent checks:

1. **`--help`, byte-identical.** `python -m …pdsarchives --help` and
   `python -m …pds4archives --help` were captured under `COLUMNS=80` from the
   baseline worktree and from the branch. `diff` is empty for both tools. §5's
   captures 14 and 27 re-confirm it under the tool-run harness.
2. **The parser construction itself, byte-identical.** `--help` output is
   whitespace-collapsed by argparse's formatter, so a trailing-space difference
   would hide in it. `scratchpad/parser_probe.py` monkeypatches
   `ArgumentParser.__init__` and `.add_argument` to record every call's arguments
   and keywords in order, then intercepts `parse_args`. Run against both trees
   for both tools, the four JSON dumps diff **empty** — same description, same
   option strings in the same order, same `const`/`default`/`action`/`dest`/
   `nargs`/`type`, same help strings character for character.
3. **`tests/holdings_maintenance/test_task_flags.py`** (13 ids) passes, including
   the four two-flag cases that assert `not allowed with argument` never appears
   and that the rightmost flag wins.

### 9. Ruff ratchet — eighteen fewer findings forgiven, no code slot gained

`_common.py` is a new file, so any `per-file-ignores` entry for it would be a new
key, which is a widen. It has **no entry**: measured with
`lint.per-file-ignores = {}`, `_common.py` reports zero findings.

Nor does the versioning section that arrived in it, which had two obstacles of its
own: `UP031` on `'%03d' % new_version`, six copies of it, now
`f'{new_version:03d}'` — the same three digits, zero-padded, for the same `int` —
and `SIM115` on `hashfile`'s bare `open`, which is gone because the merged copy is
the pds4 twin's `with` block.

The archives migration's obstacle was `UP031` too. The four `%`-format sites that
moved out of each archives module are:

| Site (at `ab1fa3b`) | Now |
|---|---|
| `'%d (filesystem) vs. %d (tarfile)' % (nbytes, …)` | `str(nbytes) + ' (filesystem) vs. ' + str(…) + ' (tarfile)'` |
| `'%s (filesystem) vs. %s (tarfile)' % (modtime, …)` | the same, with `str()` |
| `'environment variable "%s" ' % LOGROOT_ENV` | `LOG_HELP.format(env=LOGROOT_ENV, …)` on a named template |
| `'Task %s for' % args.task` | `'Task ' + args.task + ' for'` |

Concatenation, not an f-string: `'%s' % x` is `str(x)` exactly, and
`'Task "' + args.task + '" for'` is already the spelling `pdschecksums.py:815`
uses for the same header, so this is the house idiom rather than a new one. For
the two `%d` sites, both operands are integers at every construction site
(`os.path.getsize`, a literal `0`, and `TarInfo.size`), and `'%d' % n` is `str(n)`
for an `int`. The rendered text is identical: §8's parser dump proves it for the
help string, and §5's two corruption invocations render both error messages
against a real volume, inside the diffed evidence, identically from both trees.

Measured with `lint.per-file-ignores = {}` over `src/pdsfile tests scripts`:

| | baseline `ab1fa3b` | branch |
|---|---:|---:|
| total findings | 2,316 | **2,298** |
| `UP031` | 140 | **126** |
| `N806` | 3 | **0** |
| `SIM115` | 3 | **2** |
| every other code | — | **unchanged, code for code** |
| `per-file-ignores` entries | 70 | **69** |
| code slots | 198 | **193** |

The eighteen are findings, not codes: **fourteen** `UP031` — the eight archives
sites above and one `'%03d' % new_version` in each of the six checksum and shelf
tools — **three** `N806`, the `LOGDIRS` locals, which are gone along with the
module-level lists they shadowed; and **one** `SIM115`, `pdschecksums`'s second
bare `open`, which was `hashfile`'s. `pds4archives.py` came off the ratchet
entirely and no entry gained a code. `pdsarchives.py` keeps its `SIM115` — that
one is `f = tarfile.open(...)` in `write_archive`, which did not move.

Every ratchet entry was re-derived at the final commit and **none is stale**:
each listed code still has at least one site in the file it is listed for, so the
ratchet forgives nothing it no longer needs to. Split by group, the REST group
(PR-24's) goes 2,277 → **2,259** over an unchanged 58 entries and 179 code slots,
and the CORE group is unchanged at 39.

`pyproject.toml`'s ratchet header and `.cursor/rules/pdsfile_overrides.mdc`
deviation (4) were updated to match; the deviation's `N806` row is deleted, its
`SIM115` row drops from 3 to 2, and its `UP031` row now reads **125** over 10
maintenance tools plus `COCIRS_xxxx.py` (the 126 measured above less
`pdscache.py:324`, which belongs to the core group). Deviation (1) also gained the
owner's 2026-08-05 sentence permitting field annotations on a `@dataclass` — the
only edit to that file this PR is authorized to make, and made because otherwise
PR-26 and PR-27 would re-litigate §7's construct.

While re-deriving those figures the core group was measured too, and it reports
**39** permanent findings where deviation (4)'s core table enumerates 40; the
`__init__.py` row says `F403 ×3` at `:10,:12,:13` and ruff reports `×2` at
`:14,:15`. That predates this PR and is recorded as new deferred observation 94
rather than quietly corrected, because the table is what the next shrink will be
measured against.

### 10. Comments: three removed, one reworded, the rest travelled with their block

Comment placement is the author's, and a comment moves only if its block moves.
Measured with a `tokenize`-based multiset diff of every comment text in the base
pair against every comment text in the head trio, **five texts have no exact match
at head**, in four dispositions (the last row covers the pds3 and pds4 spellings
of one comment):

| Base text | What happened |
|---|---|
| `#### Begin active code` (both files) | **removed.** It marked the boundary between `write_archive`'s nested `archive_filter` definition and the function body. The nested definition is gone — the filter comes from `_common.make_archive_filter` — so the comment has no boundary left to mark |
| `# Set up parser` (both files) | **removed.** It labelled the argparse block, which is now a named function with a docstring, `_common.build_arg_parser` |
| `# update` (the trailing comment on `else:       # update`, both files) | **removed** with the `if`/`elif` chain it annotated; the driver now dispatches through `tasks[args.task]` |
| `# Generate a list of pdsfiles for volume directories` / `… for bundle directories` | **reworded** to `# Generate a list of pdsfiles for the target directories` at `_common.py:249`, because the one shared loop serves both vocabularies |

Nothing was added to either tool module: against the head **pair** alone the same
diff shows 18 base texts absent and **zero** new. `_common.py` of course carries
comments of its own — its module header, its four section banners, and notes on
`LOGROOT_ENV`, `BACKUP_FILENAME`, `TASK_FLAGS` and `LOGDIRS` — which is what a new
file is for.

Everything else travelled with its block at the same relative position,
including the two that annotate the statement *above* them —
`# "if c.isdir" is False for volset level readme files`, now inside
`pdsarchives.archive_targets`, and pds4's `# pdsdirs: a list, each element is …`.

#### 10.1 The same diff over the six moved-from tools

Run again over the six checksum/infoshelf/linkshelf modules, `b84fe75` against
head: **zero comment texts are new**, and the ones absent are exactly four blocks
whose code left:

| Base text | ×  | What happened |
|---|---:|---|
| `####…` (the 80-column banner) | 8 | the separators around `hashfile` and the three `move_old_<kind>()` definitions, which went with them |
| `# Holds log file directories temporarily, used by move_old_<kind>()` | 6 | the `LOGDIRS = []` declarations. One reworded copy is now in `_common.py`, describing the one shared list |
| `# From http://stackoverflow.com/…` + `#   generating-an-md5-checksum-of-a-file` | 4 | `hashfile`'s attribution, travelling with it — two copies in, one copy out |
| `# used by move_old_<kind>()` | 6 | the trailing comment on `main()`'s `LOGDIRS = []`, which is now one call to `_common.set_log_dirs(logfiles)`. What it said is on that function's docstring |

`_common.py` gained one section banner and five comment lines for the new section;
`pdsfile.py` gained the two that explain `_LOG_TIMETAG`; `_derived_paths.py`
gained none at all — its new code is documented in docstrings.

#### 10.2 Docstrings corrected rather than moved

`_derived_paths.py`'s mixin docstring said the mixin "defines no state of its own"
and named `LOG_ROOT_` and `LOGFILE_TIME_FMT` as the class attributes its methods
read. Both halves are now incomplete, so the sentence names `_LOG_TIMETAG` too and
says which method writes it back onto the class, mirroring how it already
described `set_log_root`. That is a correction to a statement this PR made false,
not a rewrite.

### 11. The three behavior changes, and tests built so they cannot pass vacuously

#### 11.1 The deferred-81 fix

**The fix.** `global LOGDIRS` was added to `main()` in `pdschecksums.py`,
`pdsinfoshelf.py` and `pdslinkshelf.py` — one line each, matching the three pds4
twins, which already had it. The owner's later ruling then moved `LOGDIRS` itself
into `_common.py`, so at the final commit all six tools instead call
`_common.set_log_dirs(logfiles)`, and the `global` declaration the fix consists of
lives once, inside that function. The fix is the same fix; it now has one home
rather than six, which is what makes §11.3's control stronger than it was.

**What it actually does**, read out of the code rather than taken from entry 81's
wording, which is looser: `move_old_checksums`, `move_old_info` and
`move_old_links` — all three now in `_common.py`'s "Checksum and shelf file tools"
section — do not version *log* files. Each versions the
**superseded data file** — the checksum file, or the shelf file (`move_old_info`
also copies its `.py` sidecar; `move_old_links` copies the `.py` and the
`.pickle`) — by `shutil.copy`ing it into every directory in `LOGDIRS` as
`<name>_v###<ext>`, `###` being one past the highest already there, and then
emitting two log lines. The copy is a copy, despite the function names and the
"moved from" / "moved to" message text: the original stays and is then
overwritten by the task. Entry 81 has been corrected in place.

#### 11.2 The three-step construction

PR-24's negative control passed vacuously
because it exercised something the gate did not check, so the test here was built
in the order that makes that impossible:

| Step | What was run | Result |
|---|---|---|
| 1 | the new test written for the **pds4** tool, against **unmodified** code | **1 passed** — proving the test can observe `_v###` versioning at all |
| 2 | the identical test for the **pds3** twin, against **unmodified** code | **1 failed** — `assert 'Checksum file moved from: ' in <the tool's whole output>`; no `_v###` file and neither log line |
| 3 | both tests, after the one-line fix | **2 passed** |

The step-2 failure is the load-bearing one: a pds3 test that passed before the
fix would be a broken test, not a lucky one.

#### 11.3 The control, re-run against the finished branch

The three-step construction above was done when the fix was three `global` lines.
At the final commit the fix is one `global` line inside `_common.set_log_dirs`,
so the control was re-run in the shape the code now has: the head tree was copied
to `/tmp/pr25-revert2`, `__pycache__` was cleared, and the `global LOGDIRS` line
inside `set_log_dirs` was deleted — which reproduces the original bug exactly, an
assignment to a local that leaves the module-level list empty. Then the four
regression tests, plus the 51 new unit ids, were run against that copy:

```
FAILED tests/holdings_maintenance/test_pds3_checksums.py::test_reinitialize_versions_the_checksum_file_it_replaces
FAILED tests/holdings_maintenance/test_pds3_infoshelf.py::test_update_versions_the_shelf_file_it_replaces
FAILED tests/holdings_maintenance/test_pds3_linkshelf.py::test_update_versions_the_shelf_file_it_replaces
FAILED tests/holdings_maintenance/test_pds4_checksums.py::test_reinitialize_versions_the_checksum_file_it_replaces
4 failed, 51 passed, 111 deselected
```

**All four fail now, where three failed before**, because the plumbing is shared:
breaking it once breaks both flavors, which is the point of moving it. And all 51
unit ids still **pass**, because `test_common_versioning.py`'s 39 set
`_common.LOGDIRS` themselves and the 12 time-tag ids do not touch it at all — so
the unit tests are testing the movers and the pin, the four tool tests are testing
the plumbing, and neither can stand in for the other.

#### 11.4 The `force=True` decision, and a control that cannot be inert

The owner decided deferred entry 95 on 2026-08-05: the merged
`move_old_checksums` passes `force=True` to both its log lines, as the pds3 copy
did. **This changes pds4 behavior**, so it is pinned rather than asserted.

`force=True` is only observable inside a scope whose `limits` cap `info` — which
is why §5.2's 32 real-holdings invocations, none of which open such a scope, show
no difference at all. The test therefore constructs one. Measured directly against
`pdslogger` 3.2.1, inside `logger.open('inner', limits={'info': 0})`:

| Called | In the log |
|---|---|
| `logger.info(msg, path)` | dropped; `Additional INFO messages suppressed` instead |
| `logger.info(msg, path, force=True)` | emitted in full |

`TestReportingUnderAnInfoCap::test_the_checksum_move_still_reports` opens exactly
that scope, versions a checksum file, and asserts both lines are in the log. On
its own that could pass because the cap does nothing, so the control is the
**other** test in the class:
`test_a_shelf_move_is_silenced_by_the_same_cap`, parametrized over
`move_old_info` and `move_old_links`, which applies the *same* `{'info': 0}` cap
to the two movers that do **not** force and asserts their lines are gone and
`Additional INFO messages suppressed` is there instead — while the `_v001` file
they wrote **is** on disk. So the cap is proven live in the same test class that
proves the forced lines survive it.

Reverting `force=True` in a scratch copy of `_common.py` fails
`test_the_checksum_move_still_reports` and **only** that test: `1 failed, 38
passed`.

#### 11.5 The log time-tag race

**The bug.** `LOGFILE_TIME_FMT` is `'%Y-%m-%dT%H-%M-%S'` — one-second resolution —
and `_log_path_for` read the clock on **every** call. A tool builds its two log
paths with two separate calls, so a run whose calls straddle a second boundary
wrote its two copies of one log under time tags one second apart and they stopped
naming one run. Rare, since the calls are microseconds apart, and real: it would
make any future golden over a two-log run flaky at that rate.

**The fix, and why it is freeze-safe.** `PdsFile` gains a private class attribute
`_LOG_TIMETAG`; the derived-paths mixin gains `_log_timetag()`, which reads the
clock, and `_pinned_log_timetag()`, a context manager that reads it once on the
way in, holds it for the block and restores the previous value in a `finally`.
`_log_path_for` uses the pinned tag when there is one. `_common.log_paths_for` is
new, wraps its two calls in the pin, and `run_main` calls it. The pin is class
state, and on the way out the class dictionary is put back exactly as it was —
restored if the class had its own value, **deleted** if the value was inherited.
Writing it back unconditionally would leave a shadowing entry, and a class holding
its own value stops seeing one set on a base class, so a flavor pinned once would
quietly become immune to a pin taken above it; that is measured by
`test_the_pin_leaves_the_class_dictionary_as_it_found_it` and
`test_a_flavor_pinned_once_still_sees_a_pin_taken_above_it`, both of which fail
against the unconditional restore. Otherwise the pin is the same shape as
`set_log_root`, which already writes `LOG_ROOT_` onto the class it is called on.

**The fix reaches one of the eleven tools, and the record must not imply more.**
Measured at this head, `grep -n "place='parallel'" src/` reports **15 sites**:
`_common.py:200`, which is fixed, and **14 in ten tool modules**, which are not —
`pdschecksums.py:789,797`, `pdsinfoshelf.py:825,833`, `pdslinkshelf.py:1676`,
`pds4checksums.py:761,769`, `pds4infoshelf.py:806,814`, `pds4linkshelf.py:1169`,
`pdsindexshelf.py:493`, `pds4indexshelf.py:479`, `pdsdependency.py:1126` and
`re_validate.py:60`. Six of those files are edited by this PR, for the versioning
move, with the racing lines a few hundred lines away and untouched. Eight of the
ten tools reach `run_main` in PR-26 and PR-27 and inherit the fix then; **two do
not** — the plan leaves `pdsdependency` a standalone tool this phase, and ground
rule 7 freezes `re_validate.py`. The two indexshelf tools are the sharpest case:
they dedupe explicitly with `if logfiles[0] == logfiles[1]: logfiles =
logfiles[:-1]`, and that comparison is defeated by exactly this race, so on a
straddling second they write one run's log twice into one directory. Deferred
entry 104 records the scope so the owner can decide it rather than inherit it.

Every name added is underscore-prefixed. `_log_path_for` appears **zero** times in
`tests/api/api_manifest.json`, `tests/api/consumer_used_private_names.json` is
`[]`, and `pytest tests/api/` passes with its 26 ids and an **untouched**
allowlist — which is the proof, rather than a hand-diff of the dumper. The owner
relaxed the frozen-signature rule for this fix on 2026-08-05; it was not needed,
and addendum §7 records why taking it would have cost **154** `exact` allowlist
entries (five method names across 34, 34, 34, 26 and 26 manifest classes).

**The test is a real control, not a lucky one.** The clock
`tests/core/test_log_path_timetag.py` installs advances **one second on every
reading**, so the race is certain rather than rare. Each test that asserts the pin
holds also builds the same pair *unpinned* in the same test and asserts those two
disagree; one of them additionally asserts the clock was read exactly three times
for four paths, which is what "read once inside the block" means. Run against the
unfixed reader — `_log_path_for` reading the clock unconditionally — **8 of the 12
ids fail**. The four that pass assert only the pin's own bookkeeping — released on
exit, released on a raise, and the class dictionary left as it was found — which
the reader does not touch. They are not idle either: the round-5 reviewer broke the
fix **eleven** independent ways and every one was caught, with those four catching
the mutations that drop or misplace the `finally` (§14).

The suite is `holdings_free` and builds its own `PdsFile` objects, including one
of a **rule subclass** (`Pds3File.SUBCLASSES['ASTROM_xxxx']`), because a real
target is a subclass instance while the pin is set on `Pds3File` — so the test
covers the MRO lookup production actually depends on. A further id asserts that
pinning `Pds3File` leaves `Pds4File` dating its paths from the clock, so the two
flavors cannot leak into each other.

**What the tests assert.** More than "a file appeared": the `_v001` copy's
**name** is pinned exactly (`sorted(...) == [...]`, so a stray extra file fails
it), its **bytes** are compared against what the previous run wrote, the original
is asserted still to exist (it is a copy, not a move), both log lines are
asserted, and for the checksums pair a **second** run is asserted to add `_v002`
rather than overwrite `_v001` — which is what pins the version-numbering rule
entry 81 asks for. The infoshelf and linkshelf tests additionally pin that the
`.py` sidecar (and, for links, the `.pickle`) is copied alongside: those
`shutil.copy` calls are unconditional and would raise `FileNotFoundError` if
either file were absent, and they had never been reachable in these two tools
before.

**One tool per pair is asserted, as entry 81 requires**, and the checksums pair
carries the pds3/pds4 convergence requirement. The pds4 infoshelf and linkshelf
twins are not duplicated here: their `global` is present at `ab1fa3b`, so their
versioning is pre-existing behavior this PR does not change.

A cross-check on all three fixed tools, from the differential probe
`scratchpad/versioning_probe.py`, run against both worktrees with the same
holdings:

| Tool and task | baseline `ab1fa3b` | branch |
|---|---|---|
| `pdschecksums --reinitialize` | *(nothing)* | `HSTN0_7176_md5_v001.txt` |
| `pdsinfoshelf --repair` | *(nothing)* | `HSTN0_7176_info_v001.pickle`, `…_info_v001.py` |
| `pdsinfoshelf --update` | *(nothing)* | `HSTN0_7176_info_v001.pickle`, `…_info_v001.py` |
| `pdslinkshelf --repair` | *(nothing)* | `HSTN0_7176_links_v001.pickle`, `…_links_v001.py` |
| `pdslinkshelf --update` | *(nothing)* | `HSTN0_7176_links_v001.pickle`, `…_links_v001.py` |

Every run exits 0 on both sides. The table lists each probed tool's own
versioned files; the four infoshelf and linkshelf rows also produce
`HSTN0_7176_md5_v001.txt`, because the probe's setup step runs
`pdschecksums --repair`, which this PR makes version too.

Two divergences surfaced by making the pds3 lines reachable are recorded rather
than resolved: `pdschecksums` forces its two log lines and `pds4checksums` does
not (new deferred observation 95, owned by PR-26, which merges the two).

### 12. Design note — the deviations, and how the owner ruled on each

Written up in full in
[`plans/2026-08-04-pr-25-deviations-addendum.md`](../plans/2026-08-04-pr-25-deviations-addendum.md),
which §6.4 requires to be an addendum in `plans/` acknowledged by the owner
before merge. The owner ruled on 2026-08-05:

| Addendum § | The deviation | Ruling |
|---|---|---|
| 1 | **`write_archive` is not a spec hook.** The divergence between the two `write_archive`s and the ten task functions is larger than a hook can carry (§6); all of it stays in the tool modules | **Accepted**, and the plan's PR-25 entry was amended to say so, so PR-26/27 do not re-derive it. The requirement that governs — no `if pds4:` branch in `_common.py` — was met and still stands |
| 2 | **`ToolSpec` is a plain class, not a `@dataclass`**, because a dataclass declares its fields by annotation | **Moot.** The owner lifted the annotation ban for `@dataclass` fields; `ToolSpec` is now the dataclass the plan asked for, and deviation (1) records the permission. The deviation was withdrawn, not rejected on its merits |
| 3 | **`hashfile()` and `move_old_<kind>()` did not move**, being owed by PR-26/27 | **Overruled — move them now.** §6.1. Three divergences had to be resolved, one of them observable (§11.4), and the three *kinds* were **not** collapsed into one function, which is the hard stop the addendum's own rule requires (deferred entry 100) |
| 4 | **The task-flag help text is spec data.** `build_arg_parser` owns the semantics; the wording is archives-specific and lives in the spec as `{unit}`/`{units}` templates | **Not objected to**, stands as written |
| 5 | **Three `ToolSpec` fields differ from the plan's list** | **Partly overruled.** `holdings_sentinel` and `index_ext` are now fields, with the plan's values confirmed against the code (§7). `handler_factories` as an ordered tuple rather than a boolean **stands** — the owner did not object, and the order is what is observable |
| 6 | The shared driver adds a frame to a **traceback** inside a tool log | Not a design choice; §5.1 measures it |
| 7 | **New, and it needs the owner's eye.** The log time-tag race, the private fix, and the 154 allowlist entries the public fix would have cost | §11.5 and addendum §7 |

**One thing the owner has ruled on that this PR did *not* act on.** Deferred entry
99 — the hash-dependent order of the two `Log file:` lines — was **held** for
PR-26/PR-27 on the owner's decision, because converging one copy while nine tools
keep theirs would make the tools disagree with each other. No ordering change was
made here. §5's comparator sorts those lines instead, and §5.2 extends the same
treatment to the `… moved to` lines for the same reason.

### 13. Deferred observations

**Dispositions of the entries assigned to PR-25:**

| Entry | Disposition |
|---|---|
| **66** — three maintenance modules over 1,000 lines | **Re-measured, and two of the three shrank.** At this head `pdslinkshelf.py` is **1,735**, `pds4linkshelf.py` **1,229**, `pdsdependency.py` **1,167**; at `ab1fa3b` they measure 1,783 / 1,278 / 1,167. The two linkshelf modules lost 48 and 49 lines to the versioning move, which is not enough to bring either under 1,000, and `pdsdependency.py` is untouched. `_common.py` is 676 lines and `pdsarchives.py`/`pds4archives.py` are 260 and 280, all under the limit that overrides deviation (3) declines to waive for this package. The waiver question stays open for the phase, as entry 66 intends; deferred entry 98 records that 1,000 is also the number that decides when `_common.py` splits |
| **81** — `LOGDIRS` shadowing | **Resolved**, with its description corrected. §11.1–11.3 |
| **83** — `proceed` vestige | **Closed.** Confirmed: no `proceed` binding remains in `pdsarchives.py`, and `_common.run_main` calls the task function without binding its result, so the vestige has no home to return to. `pdschecksums.py:862`'s live use is untouched |
| **88** — divergent mutable defaults | **Carried to PR-26.** Both `B006` sites are `pdschecksums.py:37` and `pdsinfoshelf.py:42`; neither archives module has a mutable default anywhere, so PR-25 has no signature to choose |
| **89** — three spellings of the `logger.close()` unpacking | **Decided for the archives pair; carried for the rest.** `_common.run_main` uses `(fatal, errors, _warnings, _tests)`, the spelling nine of the eleven sites already used. The two archives sites are gone with the `main()` bodies that held them, leaving eight named-underscore sites and one bare-`_` (`pds4linkshelf.py:1222`) for PR-26/27 |
| **1** — `pds4archives` cannot round-trip | **Not fixed, deliberately.** It is a behavior defect pinned by `test_pds4_archives.test_validate_cannot_round_trip`, and this PR is behavior-preserving. The two functions involved — `write_archive`'s `arcname` and `read_archive_info`'s prefix — are exactly the two that stayed in the tool module, so neither was touched. Still owned by a PR that may change behavior |
| **2** — `pds4archives`'s bare `raise` | **Not fixed, deliberately**, same reason; pinned by `test_pds4_archives.test_initialize_on_a_bundle_raises`. The line stayed inside `write_archive`, which did not move, so it is byte-identical at `pds4archives.py:105`; §5's capture 22 shows it still raising `RuntimeError: No active exception to reraise` against a real bundle |

**New entries: 92 – 103.** 92 — `pds4archives`'s `*_LIMITS` are inert because it
logs `normal` (**Owner**). 93 — `pdsarchives` names its log `_links`, not
`_archives`; the collision with `pdslinkshelf` that this looks like was checked
and does not exist, because the `dir=` component separates them, so it is a
naming inconsistency in a frozen path (**Owner**). 94 — deviation (4)'s core
table enumerates 40 findings where ruff reports 39. 96 comes from the round-1
reviewer (the residual `read_archive_info` duplication).

**Four entries were decided by the owner on 2026-08-05 and are now closed:**

| Entry | Decision |
|---|---|
| **95** — the two `move_old_checksums` twins differ on `force=True` | **`force=True`.** Versioning is a filesystem mutation and its report should not be droppable by a limits cap. A pds4 behavior change, pinned by §11.4 |
| **97** — `ToolSpec.extra_arguments` is unexercised | **Updated, still open for PR-26.** The unexercised set is now **three** fields: `extra_arguments`, plus `holdings_sentinel` and `index_ext`, which are *carried* and not read |
| **98** — one `_common.py` or a module per family | **Decided now, not deferred: one file, a section per family.** The number is **1,000**, deviation (3)'s module limit, which it does not waive for this package; `_common.py` measures **676**. The same number says PR-26 splits it: the four remaining pairs project ~1,400 more lines at the archives family's own extraction rate |
| **99** — the hash-dependent order of the two `Log file:` lines | **Held for PR-26/PR-27**, where all the copies converge. No ordering change was made here |

**Five entries are new to this round: 100 – 104.** 100 — the three
`move_old_<kind>()` functions are **not** one function with data differences; the
"moved to" line has two call shapes that `pdslogger` renders differently, so
collapsing them needs a flag and rewrites frozen log text for two families
(**PR-26/27**). 101 — `holdings_sentinel` hard-codes the *name* of the holdings
directory, so the new field is not a configuration point (**Owner**). 102 — with
the movers in one file, the versioning report is forced for checksums and
droppable for shelves; entry 95's argument applies to both, but changing the shelf
movers is an unforced log-text change on four tools (**Owner**). 103 —
`move_old_links` copies the shelf file twice to the same destination, because the
shelf file *is* its own `.pickle` sidecar (**PR-27**). 104 comes from the round-5
reviewer: the time-tag fix reaches one of the eleven tools, eight of the other ten
inherit it by migration in PR-26/27, and **two — `pdsdependency` and the frozen
`re_validate.py` — are not scheduled to inherit anything** (**Owner**).

### 14. Review loop

**A durability limit on the evidence, stated so no one reads the numbers as
reproducible from the branch alone.** The harness scripts §3, §5.1, §5.2, §8 and
§11.5 name — `compare_runs.py`, `tool_run_diff.sh`, `compare_toolruns.py`,
`shelf_run_diff.sh`, `compare_runs3.py`, `parser_probe.py`,
`versioning_probe.py` — live in a session scratch directory outside the
repository and are not committed; `git ls-files | grep scratchpad` is empty. A
reader at this head cannot re-derive "32 of 32 / 76 of 76" or "4,005 / 4,009"
from anything the branch contains. What they can do instead is what round 5 did:
rebuild the harness from §5.2's description and re-run it. That reproduced the
pds3 half independently — 15 invocations of the six moved-from pds3 tools from
both trees, 15 of 15 stdout captures and all 823 normalized log lines identical —
which is a stronger result than a committed script would have given, because it
was an independent implementation.

`critiques/pr-25/round-1.md` … `round-5.md`. Rounds 1–4 ran against the PR as it
stood at `b84fe75`; **round 5** is a fresh no-context adversarial review of the
diff the owner's rulings produced, pointed specifically at the `move_old_<kind>()`
merge and at whether §11.5's time-tag test is a real control.

**Round 5 returned 3 Major and 7 Minor, every one of them against this record
rather than against `src/`, and both of the things it was pointed at held.** It
diffed each moved function against *both* pre-move copies with `ast` and confirmed
the twin-identity claims to the character; it measured the `pdslogger` call-shape
difference directly and confirmed the hard stop is real; it broke the time-tag fix
**eleven** ways — four of them the record never tried — and all eleven were caught
by the ids; it reverted `force=True` three ways and attacked the control by
forcing the shelf movers; and, because §5.2's harness lives outside the repository,
it **rebuilt the harness and re-ran the gate independently**: 15 invocations of the
six moved-from pds3 tools from both trees, 15 of 15 stdout captures and all 823
normalized log lines identical. Every ruff, ratchet, line, statement and id number
in this record reproduced exactly.

Its findings, and what was done:

| # | Finding | Disposition |
|---|---|---|
| M1 | Four regression-test docstrings still described the `main()`-shadows-`LOGDIRS` design this PR abolished; §10's comment audit never covered those four files | **Fixed.** All four rewritten to describe `_common.set_log_dirs` |
| M2 | "`log_paths_for` … the one place in the tree that builds the pair" is false — 15 sites, 14 unfixed — and the claim was in §11.5, the addendum and a test docstring | **Fixed in all three, and escalated.** §11.5 and addendum §7 now enumerate the 14 and name the two tools no PR is scheduled to fix; deferred entry 104 puts the scope in front of the owner |
| M3 | 22 stale `<file>.py:<n>` citations, three past EOF, under a sentence promising every number was re-measured | **Fixed.** Every citation re-derived at this head and verified to land on the construct it names; the historical ones in entry 89 now say which commit they are cited at |
| m1 | §6's growth split said 151 + 38 where the measurement is 151 + 39 | **Fixed** (entry 98 already said 39) |
| m2 | "moved verbatim" understates two changed lines per mover | **Fixed** — §6.1 now qualifies it and names both |
| m3 | The pin left a shadowing class-dict entry, so a flavor pinned once stopped seeing a base-class pin | **Fixed in `src/`**, with two new ids that fail against the old restore |
| m4 | The hard stop is real, but 18 lines are still triplicated and §6.1's prose implied the stop covered the whole question | **Fixed** — §6.1 now states the 18 lines and the narrower scope of the rule |
| m5 | `@dataclass` made `ToolSpec` unhashable; §7 said "no other change" | **Fixed** — §7 records `__eq__`, `__repr__` and `__hash__ = None` |
| m6 | §7 said two pds4 tools rebuild the archives path; four do | **Fixed**, with the four cited |
| m7 | The harness scripts the biggest numbers rest on are not in the repository | **Recorded** above, with round 5's independent reproduction as the answer |

Two CodeRabbit comments were posted on PR #120 and both were **verified against
the code before being accepted**:

| Comment | Verdict |
|---|---|
| `phase6-validation.md` overstated the handler-order claim: `handler_factories` is applied per target as well as at the log root, so the ordering is not exercised only by the two `--log` invocations | **Valid.** `_common.py:276-277` runs on every invocation. §5.1's paragraph now scopes the claim to the log root and says where else the tuple is applied |
| `critiques/pr-25/round-2.md` said "four differing artifacts" where its own numbers give two stdout captures plus four log files | **Valid.** 32 of 34 and 35 of 39 is six. Corrected, with a note that the final counts live in §5.1 |
Round 1 returned `goal not met` (2 Major, 6 Minor); rounds 2 and 3 returned
`goal met` with zero Major and Minor findings only in the evidence prose, all
accepted; round 4 was the scoped confirmation §6.6 allows at the cap.
