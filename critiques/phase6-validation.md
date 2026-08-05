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
**Date:** 2026-08-04.
**Sub-plan:** [`plans/2026-08-04-pr-25-subplan.md`](../plans/2026-08-04-pr-25-subplan.md).
**Deviations addendum:**
[`plans/2026-08-04-pr-25-deviations-addendum.md`](../plans/2026-08-04-pr-25-deviations-addendum.md)
— needs owner acknowledgement before merge (§6.4).

This PR is behavior-preserving **except for one deliberate change**: the three
pds3 tools that shadowed `LOGDIRS` with a `main()` local now declare it `global`,
so the versioning step those tools have always contained starts running (deferred
observation 81; owner-decided 2026-08-04). That change adds exactly four test ids
and nothing else. Everything the archives migration touches is required to be
invisible, with the one unavoidable exception §5 measures and §12.5 explains.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, the main tree's venv (`/seti/all_repos/rms-pdsfile/venv`), `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`, `PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings`, `PDSFILE_TEST_HOLDINGS=full` — the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at `ab1fa3b` (`/seti/all_repos/rms-pdsfile-pr25/base`), same interpreter, same holdings |
| Branch tree | `/seti/all_repos/rms-pdsfile-pr25/work` on `pr-25-common-core` |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml`; `PYTHONPATH=<tree>/src` on each |
| ruff | 0.15.7 (the development venv) |
| pdslogger | rms-pdslogger 3.2.1 |

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — `pytest tests/api/`, 15 ids. No `holdings_maintenance` module is in the manifest, so this gate is silent about this PR's edits; it is run to prove nothing leaked out of them |
| Full-data suite, `--mode ns` | **passed** — 896 ids vs the baseline's 892; the four extra are the new regression tests and nothing else moved (§3) |
| Full-data suite, `--mode s` | **passed** — 558 ids, set diff **empty** (§3) |
| Phase-6 per-tool gate: real-holdings run of each migrated tool, diffed against pre-PR | **passed with one recorded difference** — 27 stdout captures and 23 log files per tree; the six artifacts that differ differ only in Python traceback frames (§5) |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet shrank by eleven codes and gained none (§9) |
| `ruff check --preview --select E111,E112,E113 …` | **passed**, no findings |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full manifest module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh -c -s`, no holdings env vars) | **passed**, pyroma 10/10; the four new tests collect and skip without holdings, as their `full_holdings` marker requires (§3) |
| PR-13 tool tests, with holdings | **passed** — `pytest tests/holdings_maintenance/` |
| Adversarial review loop | `critiques/pr-25/round-<k>.md` (§14) |

### 3. Full-data suite — four added ids, nothing else

Both passes were run on the baseline worktree and on the branch with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to `classname::name` plus its outcome, and the two mappings were
compared as sets (`scratchpad/compare_runs.py`, which prints the symmetric
difference of the id sets, the ids whose outcome changed, and the symmetric
difference of the *passed* sets separately, so a test flipping in either
direction is visible).

| Run | baseline `ab1fa3b` | `pr-25-common-core` | id-set diff |
|---|---|---|---|
| `--mode ns` | 858 passed / 34 skipped (**892 ids**) | 862 passed / 34 skipped (**896 ids**) | **+4, all new and all passing** |
| `--mode s` | 555 passed / 3 skipped (**558 ids**) | 555 passed / 3 skipped (**558 ids**) | **empty** |

Ids whose outcome changed: **0** in both modes. Ids removed: **0** in both modes.
The passed-set difference is exactly the four additions:

```
tests.holdings_maintenance.test_pds3_checksums::test_reinitialize_versions_the_checksum_file_it_replaces
tests.holdings_maintenance.test_pds4_checksums::test_reinitialize_versions_the_checksum_file_it_replaces
tests.holdings_maintenance.test_pds3_infoshelf::test_update_versions_the_shelf_file_it_replaces
tests.holdings_maintenance.test_pds3_linkshelf::test_update_versions_the_shelf_file_it_replaces
```

All four are the regression tests §11 requires for the deferred-81 behavior
change, and each is justified there. **That exception is confined to these four
ids.** The archives migration — the bulk of the diff — moved no id and changed no
outcome, which is what a behavior-preserving refactor has to show.

`--mode s` does not run `tests/holdings_maintenance/`, which is why the four new
ids appear only in `ns`; the driver script's comment explains that the tools run
in their own subprocesses and `--mode` cannot reach them.

The hosted no-holdings run is the same arithmetic seen from the other side:
baseline 92 passed / 800 skipped, branch 92 passed / 804 skipped — the four new
tests collect and skip.

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

### 5. The Phase-6 per-tool gate: a real-holdings run of each migrated tool, diffed against pre-PR

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

**The 27 invocations per tree** cover both tools across all five tasks and the
paths around them: for `pdsarchives` — `--validate` with no archive present (the
pds3 "File does not exist" critical path), `--initialize`, `--validate` clean,
`--initialize` again (already-exists error), `--repair` (files match, canceled),
`--update` (exists, skipping), `--reinitialize`, a **volset** path (the
expansion-plus-`blankline` path), `--quiet`, a two-flag invocation, a
nonexistent path, an archives path (the rejection), a missing task, and
`--help`; and the same thirteen for `pds4archives` against the bundle set, plus
a single-bundle path (which reaches the bare `raise` of deferred entry 2).

**The comparison.** `scratchpad/compare_toolruns.py` normalizes the temporary
disk path, the source tree path, wall-clock timestamps, elapsed times, and the
time tag inside a log file name, then compares stdout capture by capture and log
file by log file. Traceback **line numbers** are normalized — no refactor can
hold those fixed — but traceback **file names are not**, so a frame that moved to
another module shows up as a difference. That is deliberate, and it is what the
one difference below is.

| | baseline `ab1fa3b` | `pr-25-common-core` | identical after normalization |
|---|---:|---:|---|
| stdout captures | 27 | 27 | **25 of 27** |
| log files written | 23 | 23 | **19 of 23** |
| normalized lines compared | 2,082 | 2,082 | — |

**The six differing artifacts differ in exactly one thing, and it is the same
thing in all six.** Aggregating every changed line across all six:

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
`plans/2026-08-04-pr-25-deviations-addendum.md` §5 puts it in front of the owner.

### 6. What moved into `_common.py`, and what deliberately did not

The two archives modules were 1,155 lines and 623 statements between them, most
of it the same code written twice. After the migration:

| File | lines before | lines after | statements before | statements after |
|---|---:|---:|---:|---:|
| `pds3/pdsarchives.py` | 565 | **258** | 307 | **140** |
| `pds4/pds4archives.py` | 590 | **278** | 316 | **146** |
| `_common.py` | — | **486** | — | **213** |
| total | 1,155 | **1,022** | 623 | **499** |

So the pair shed **337 statements** and the one shared copy costs **213**: a net
**−124 statements (−20%)** and **−133 lines**, while `_common.py` also carries 84
lines of docstring, **78 of which have no counterpart** in either original (the
other 6 came with `load_directory_info`, `validate_tuples` and the
`archive_filter` closure). Counting statements as well as lines is deliberate —
line counts move when a docstring is added, statement counts do not.

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

**What `_common.py` holds.** `LOGROOT_ENV` and `BACKUP_FILENAME` (shared by every
tool); `ToolSpec`; `TASK_FLAGS`, `LOG_HELP`, `QUIET_HELP`, `build_arg_parser`,
`reject_checksum_and_archive_paths` and `run_main` (the driver); and an archives
section holding the four `*_LIMITS` defaults, the description/help templates,
`load_directory_info`, `make_archive_filter` and `validate_tuples`. The
archives-specific half is there by the plan's own design — its target interface
puts `hashfile()` and the three `move_old_<kind>()` functions, which belong to
single families, in the same file.

### 7. The `ToolSpec` fields, and the rule that admitted each

| Field | pds3 | pds4 | Why it is data |
|---|---|---|---|
| `progname` | `'pdsarchives'` | `'pdsarchives'` | a string; both halves already print `pdsarchives` and log under `logs/pdsarchives/` |
| `logname` | `'pds.validation.archives'` | same | a string |
| `pdsfile_cls` | `Pds3File` | `Pds4File` | a class |
| `unit` | `'volume'` | `'bundle'` | a string: names the positional, and is substituted into the help text |
| `file_log_level` | `'info'` | `'normal'` | a level name. **Not interchangeable** — see below |
| `description`, `task_help`, `positional_help` | the shared archive templates | same | strings |
| `log_path_for` | `log_path_for_volume('_links', …)` | `log_path_for_bundle('_archives', …)` | a callable that computes a path |
| `expand_target` | volume, else the volset's directory children | the PdsFile itself | a callable returning the target list |
| `handler_factories` | `(error_handler,)` | `(warning_handler, error_handler)` | a tuple of factories, applied in order |
| `lskip_for` | `archive_path_and_lskip()[1]` | `len(root_)+len(category_)+len(bundleset_)` | a callable returning an int |
| `extra_arguments` | `()` | `()` | the plan's hook for tool-specific flags (`--archives`, `--infoshelf`); empty here because the archives pair has none |

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

### 9. Ruff ratchet — eleven codes dropped, none gained

`_common.py` is a new file, so any `per-file-ignores` entry for it would be a new
key, which is a widen. It has **no entry**: measured with
`lint.per-file-ignores = {}`, `_common.py` reports zero findings.

The obstacle was `UP031`. The four `%`-format sites that moved out of each
archives module are:

| Site (at `ab1fa3b`) | Now |
|---|---|
| `'%d (filesystem) vs. %d (tarfile)' % (nbytes, …)` | `str(nbytes) + ' (filesystem) vs. ' + str(…) + ' (tarfile)'` |
| `'%s (filesystem) vs. %s (tarfile)' % (modtime, …)` | the same, with `str()` |
| `'environment variable "%s" ' % LOGROOT_ENV` | `LOG_HELP.format(env=LOGROOT_ENV, …)` on a named template |
| `'Task %s for' % args.task` | `'Task ' + args.task + ' for'` |

Concatenation, not an f-string: `'%s' % x` is `str(x)` exactly, and
`'Task "' + args.task + '" for'` is already the spelling `pdschecksums.py:873`
uses for the same header, so this is the house idiom rather than a new one. For
the two `%d` sites, both operands are integers at every construction site
(`os.path.getsize`, a literal `0`, and `TarInfo.size`), and `'%d' % n` is `str(n)`
for an `int`. The rendered text is identical: §8's parser dump proves it for the
help string, and §5's runs exercise both error messages against a real volume.

Measured with `lint.per-file-ignores = {}` over `src/pdsfile tests scripts`:

| | baseline `ab1fa3b` | branch |
|---|---:|---:|
| total findings | 2,316 | **2,305** |
| `UP031` | 140 | **132** |
| `N806` | 3 | **0** |
| every other code | — | **unchanged, code for code** |
| `per-file-ignores` entries | 70 | **69** |
| code slots | 198 | **193** |

The eleven are the eight `UP031` above and the three `N806` `LOGDIRS` locals,
which stop being locals once `main()` declares them `global`. Three entries lost
`N806`, `pdsarchives.py` lost `UP031`, and `pds4archives.py` came off the ratchet
entirely. `pdsarchives.py` keeps `SIM115` — its `f = tarfile.open(...)` is in
`write_archive`, which did not move.

`pyproject.toml`'s ratchet header and `.cursor/rules/pdsfile_overrides.mdc`
deviation (4) were updated to match; the deviation's `N806` row is deleted and
its `UP031` row now reads 131 over 10 maintenance tools plus `COCIRS_xxxx.py`
(the 132 measured above less `pdscache.py:324`, which belongs to the core group).

While re-deriving those figures the core group was measured too, and it reports
**39** permanent findings where deviation (4)'s core table enumerates 40; the
`__init__.py` row says `F403 ×3` at `:10,:12,:13` and ruff reports `×2` at
`:14,:15`. That predates this PR and is recorded as new deferred observation 94
rather than quietly corrected, because the table is what the next shrink will be
measured against.

### 10. Comments: three removed, one reworded, the rest travelled with their block

Comment placement is the author's, and a comment moves only if its block moves.
Measured with a multiset diff of every comment text in the base pair against
every comment text in the head trio, **four texts have no exact match at head**,
and no comment text is new:

| Base text | What happened |
|---|---|
| `#### Begin active code` (both files) | **removed.** It marked the boundary between `write_archive`'s nested `archive_filter` definition and the function body. The nested definition is gone — the filter comes from `_common.make_archive_filter` — so the comment has no boundary left to mark |
| `# Set up parser` (both files) | **removed.** It labelled the argparse block, which is now a named function with a docstring, `_common.build_arg_parser` |
| `# update` (the trailing comment on `else:       # update`, both files) | **removed** with the `if`/`elif` chain it annotated; the driver now dispatches through `tasks[args.task]` |
| `# Generate a list of pdsfiles for volume directories` / `… for bundle directories` | **reworded** to `# Generate a list of pdsfiles for the target directories` at `_common.py:209`, because the one shared loop serves both vocabularies |

Everything else travelled with its block at the same relative position,
including the two that annotate the statement *above* them —
`# "if c.isdir" is False for volset level readme files`, now inside
`pdsarchives.archive_targets`, and pds4's `# pdsdirs: a list, each element is …`.

### 11. The deferred-81 fix, and a test built so it cannot pass vacuously

**The fix.** `global LOGDIRS` added at `pdschecksums.py:854`,
`pdsinfoshelf.py:878` and `pdslinkshelf.py:1727` — one line each, matching
`pds4checksums.py:826`, `pds4infoshelf.py:859` and `pds4linkshelf.py:1220`, which
already had it. Nothing else in those three files was touched.

**What it actually does**, read out of the code rather than taken from entry 81's
wording, which is looser: `move_old_checksums` (`pdschecksums.py:374-405`),
`move_old_info` (`pdsinfoshelf.py:428-462`) and `move_old_links`
(`pdslinkshelf.py:1380-1419`) do not version *log* files. Each versions the
**superseded data file** — the checksum file, or the shelf file (`move_old_info`
also copies its `.py` sidecar; `move_old_links` copies the `.py` and the
`.pickle`) — by `shutil.copy`ing it into every directory in `LOGDIRS` as
`<name>_v###<ext>`, `###` being one past the highest already there, and then
emitting two log lines. The copy is a copy, despite the function names and the
"moved from" / "moved to" message text: the original stays and is then
overwritten by the task. Entry 81 has been corrected in place.

**The three-step construction.** PR-24's negative control passed vacuously
because it exercised something the gate did not check, so the test here was built
in the order that makes that impossible:

| Step | What was run | Result |
|---|---|---|
| 1 | the new test written for the **pds4** tool, against **unmodified** code | **1 passed** — proving the test can observe `_v###` versioning at all |
| 2 | the identical test for the **pds3** twin, against **unmodified** code | **1 failed** — `assert 'Checksum file moved from: ' in <the tool's whole output>`; no `_v###` file and neither log line |
| 3 | both tests, after the one-line fix | **2 passed** |

The step-2 failure is the load-bearing one: a pds3 test that passed before the
fix would be a broken test, not a lucky one.

**And the control was re-run against the finished branch.** The head tree was
copied to `/tmp/pr25-revert`, the three `global LOGDIRS` lines were deleted
there, `__pycache__` was cleared, and all four versioning tests were run against
that copy:

```
FAILED tests/holdings_maintenance/test_pds3_checksums.py::test_reinitialize_versions_the_checksum_file_it_replaces
FAILED tests/holdings_maintenance/test_pds3_infoshelf.py::test_update_versions_the_shelf_file_it_replaces
FAILED tests/holdings_maintenance/test_pds3_linkshelf.py::test_update_versions_the_shelf_file_it_replaces
3 failed, 1 passed, 28 deselected
```

Every pds3 test fails with the fix reverted; the pds4 test — whose tool was
already correct — still passes. The four runs are kept at
`scratchpad/runs/logdirs-step{1,2,3,3b}-*.txt` and
`scratchpad/runs/logdirs-negative-control-fix-reverted.txt`.

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

Every run exits 0 on both sides.

Two divergences surfaced by making the pds3 lines reachable are recorded rather
than resolved: `pdschecksums` forces its two log lines and `pds4checksums` does
not (new deferred observation 95, owned by PR-26, which merges the two).

### 12. Design note — where this deviates from the plan's PR-25 sketch

Four deviations, written up in full in
[`plans/2026-08-04-pr-25-deviations-addendum.md`](../plans/2026-08-04-pr-25-deviations-addendum.md),
which §6.4 requires to be an addendum in `plans/` acknowledged by the owner
before merge. In brief:

1. **`write_archive` is not a spec hook.** The divergence between the two
   `write_archive`s and the ten task functions is larger than a hook can carry
   (§6). All of it stays in the tool modules. The plan's actual requirement — no
   `if pds4:` branch — is met: `_common.py` contains no test on which flavor is
   running.
2. **`ToolSpec` is a plain class, not a `@dataclass`.** A dataclass declares its
   fields by annotation, which ground rule 5 and overrides deviation (1) forbid.
   `collections.namedtuple` was considered and rejected (it makes the spec a
   tuple, inviting positional construction of a twelve-field record). An earlier
   revision of this PR extended deviation (1) in `pdsfile_overrides.mdc` to say
   so; **that edit was reverted**, because a PR should not extend the rules file
   that authorizes its own departure from the plan.
3. **`hashfile()` and `move_old_<kind>()` did not move**, though the plan's
   target interface lists them: they belong to the tools PR-26 and PR-27
   migrate, and moving them now would put code in `_common.py` that no migrated
   tool calls.
4. **The task-flag help text is spec data.** `build_arg_parser` owns the
   semantics; the wording is archives-specific and lives in the spec as
   `{unit}`/`{units}` templates. The plan's `vocab` field is that substitution
   under a shorter name.

And one consequence that is not a design choice: §5's traceback frames.

### 13. Deferred observations

**Dispositions of the entries assigned to PR-25:**

| Entry | Disposition |
|---|---|
| **66** — three maintenance modules over 1,000 lines | **Re-measured, not waived.** `pdslinkshelf.py` **1,784**, `pds4linkshelf.py` **1,278**, `pdsdependency.py` **1,167** at this head. Entry 66 recorded 1,779 / 1,274 / 1,166; at `ab1fa3b` they measure 1,783 / 1,278 / 1,167, so four, four and one line of drift arrived between that measurement and this PR's base, and this PR adds the one `global LOGDIRS` line to `pdslinkshelf.py`. PR-25 migrates only the archives pair, so it shrinks none of the three. `_common.py` is 486 lines and `pdsarchives.py`/`pds4archives.py` are now 258 and 278, all well under the limit. The waiver question stays open for the phase, as entry 66 intends |
| **81** — `LOGDIRS` shadowing | **Resolved**, with its description corrected. §11 |
| **83** — `proceed` vestige | **Closed.** Confirmed: no `proceed` binding remains in `pdsarchives.py`, and `_common.run_main` calls the task function without binding its result, so the vestige has no home to return to. `pdschecksums.py:917`'s live use is untouched |
| **88** — divergent mutable defaults | **Carried to PR-26.** Both `B006` sites are `pdschecksums.py:55` and `pdsinfoshelf.py:45`; neither archives module has a mutable default anywhere, so PR-25 has no signature to choose |
| **89** — three spellings of the `logger.close()` unpacking | **Decided for the archives pair; carried for the rest.** `_common.run_main` uses `(fatal, errors, _warnings, _tests)`, the spelling nine of the eleven sites already used. The two archives sites are gone with the `main()` bodies that held them, leaving eight named-underscore sites and one bare-`_` (`pds4linkshelf.py:1271`) for PR-26/27 |
| **1** — `pds4archives` cannot round-trip | **Not fixed, deliberately.** It is a behavior defect pinned by `test_pds4_archives.test_validate_cannot_round_trip`, and this PR is behavior-preserving. The two functions involved — `write_archive`'s `arcname` and `read_archive_info`'s prefix — are exactly the two that stayed in the tool module, so neither was touched. Still owned by a PR that may change behavior |
| **2** — `pds4archives`'s bare `raise` | **Not fixed, deliberately**, same reason; pinned by `test_pds4_archives.test_initialize_on_a_bundle_raises`. The line stayed inside `write_archive`, which did not move, so it is byte-identical at `pds4archives.py:105`; §5's capture 22 shows it still raising `RuntimeError: No active exception to reraise` against a real bundle |

**New entries: 92 – 98.** 92 — `pds4archives`'s `*_LIMITS` are inert because it
logs `normal` (**Owner**). 93 — `pdsarchives` names its log `_links`, not
`_archives`; the collision with `pdslinkshelf` that this looks like was checked
and does not exist, because the `dir=` component separates them, so it is a
naming inconsistency in a frozen path (**Owner**). 94 — deviation (4)'s core
table enumerates 40 findings where ruff reports 39. 95 — the two
`move_old_checksums` twins differ on `force=True` (**PR-26**). 96, 97, 98 come
from the round-1 reviewer: the residual `read_archive_info` duplication,
`extra_arguments` being unexercised until PR-26, and where `_common.py`'s
per-family sections should live once five pairs have landed.

### 14. Review loop

`critiques/pr-25/round-1.md` and the rounds after it.
