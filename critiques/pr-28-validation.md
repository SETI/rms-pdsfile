# PR-28 validation — `main()` for crlf, shelf_consistency_check, show_opus_products

Base `3d044b2`. Branch `pr-28-main-for-scripts`. Every number below carries the
command line that produced it. Anything inherited rather than re-measured here is
marked **inherited**.

Environment for every measured run: `PYTHONPATH=$PWD/src`, run from the tree being
measured, `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` pointing at the limited testing
copy, `PDSFILE_TEST_HOLDINGS=full`. Python 3.12.3.

## 1. What changed

Three scripts get an argparse parser and a `main()`, so each is runnable as
`python -m …` and callable from a test. No console script is added: `[project.scripts]`
had eleven entries at `3d044b2` and has eleven now.

| file | base | head | today's entry point |
|---|---:|---:|---|
| `src/pdsfile/holdings_maintenance/pds3/crlf.py` | 121 | 170 | `build_arg_parser()`, `main(argv=None)`, `__main__` |
| `src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py` | 90 | 132 | same |
| `src/pdsfile/tools/show_opus_products.py` | 162 | 199 | same |
| `tests/holdings_maintenance/support.py` | 710 | 805 | — |
| `tests/holdings_maintenance/test_crlf.py` | 142 | 333 | — |
| `tests/holdings_maintenance/test_shelf_consistency_check.py` | 189 | 296 | — |
| `tests/holdings_maintenance/test_show_opus_products.py` | 134 | 227 | — |

```
wc -l src/pdsfile/holdings_maintenance/pds3/crlf.py \
      src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py \
      src/pdsfile/tools/show_opus_products.py tests/holdings_maintenance/support.py \
      tests/holdings_maintenance/test_crlf.py \
      tests/holdings_maintenance/test_shelf_consistency_check.py \
      tests/holdings_maintenance/test_show_opus_products.py
```

Three shapes, one per script:

- **`crlf.py`** had a `__main__` block and no `main()`. The block moves into
  `main(argv=None)` verbatim except that it reads an argparse namespace instead of
  mutating `sys.argv` with `remove()`.
- **`shelf_consistency_check.py`** had neither: the whole tool ran at import, so
  importing it *was* running it. It now has both, and `main()` returns the status
  the module used to reach by falling off the end or calling `sys.exit(1)`.
- **`show_opus_products.py`** built its parser and did its work at import, and read
  both holdings roots into module-level constants at import. Parser and work move
  into `build_arg_parser()` and `main(argv=None)`; the two `os.environ[…]` lookups
  move with the work, so importing the module no longer needs either variable. The
  module also gains the `__main__` block that `python -m` now needs, since importing
  it no longer runs it.

`re_validate.py` is untouched; PR-25a modernized it.

## 2. The `shelf_consistency_check` bug

### 2.1 Reproduced at base, not assumed

`shelf_consistency_check.py:66` at `3d044b2` read `error += 1` where every other
site reads `errors` (`:40`, `:55`, `:77`). `error` is never assigned anywhere in
the module, so the index branch could only raise. What that costs was measured
rather than reasoned about: transcript record `shelf/index-extraneous`, an index
shelf whose holdings label is absent, at `3d044b2`:

```
EXIT 1
--- stdout ---
*** Extraneous shelf: $DISK/shelf/index-extra/shelves/index/metadata/VG_28xx/VG_9999_index.pickle
--- stderr ---
Traceback (most recent call last):
  ...
  File ".../shelf_consistency_check.py", line 66, in <module>
    error += 1
    ^^^^^
NameError: name 'error' is not defined. Did you mean: 'errors'?
```

So the tool did report the extraneous shelf, and *then* died — losing the summary
and, with it, the count of everything already walked in this and every later root.
The exit status happened to be 1 either way, which is why nothing downstream would
have noticed: an uncaught exception exits 1 and so does a run that found errors.

### 2.2 The fix and its test

One character: `errors`. Head, same record:

```
EXIT 1
--- stdout ---
*** Extraneous shelf: $DISK/shelf/index-extra/shelves/index/metadata/VG_28xx/VG_9999_index.pickle
Tests performed: 1
Errors found: 1
```

`test_an_extraneous_index_shelf_is_counted_like_any_other` replaces PR-13's
`test_an_extraneous_index_shelf_raises`, which pinned the crash deliberately so
that a fix would have to invert it. The new test puts an extraneous index shelf
**and** a valid info shelf in the same tree and asserts `(2, 1)`, so it fails both
if the error is not counted and if the exception truncates the walk — the second is
what the old behaviour actually did and what a `try/except` "fix" would have left
in place.

Two more tests were added around the same branch, because the branch had one test
and now has three: `test_an_index_shelf_whose_label_exists_is_counted_not_reported`
covers the other side of the same `if` (an index shelf is matched against a
holdings `.lbl`, not a directory), which nothing covered before.

### 2.3 `F821` retired — confirmed, not assumed

```
ruff check --config 'lint.per-file-ignores = {}' \
    src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py
```
→ `All checks passed!` at head. The `"…/shelf_consistency_check.py" = ["F821"]`
line is removed from `pyproject.toml`.

## 3. Behavior changes, enumerated

The gate is a 75-record transcript of all three tools, captured at base and head
and diffed record by record. It covers every output mode of each tool, every flag
and flag combination, and the argument *shapes* — an abbreviated flag, a repeated
flag, `--`, a path beginning with `-` — that argparse treats differently from argv
read literally. It is not a proof of completeness; it is 75 invocations chosen to
include everything the three tools' code branches on plus everything argparse
decides for them.

**Base-vs-base control first: 0 of 75 records differ.** Base-vs-head: **17 of 75
differ**, +92 / −100 lines. The other 58 records — every successful crlf run, every
successful shelf run, and all 27 `show_opus_products` records including both
tables, `--pprint`, `--raw` and an abbreviated `--pat` — are byte-identical.

Six kinds of change across those seventeen records.

### 1. `--help` answers, on the two tools that had no parser (2 records)

`crlf/help`: base treated `--help` as a file path and died with
`FileNotFoundError`, exit 1. Head prints the help and exits 0.
`shelf/help`: base treated it as a directory to walk, found nothing, and printed
`Tests performed: 0 / Errors found: 0`, exit 0. Head prints the help and exits 0.

Attribution: this is what having a parser *is*. Neither line of base output was a
message the tool meant to emit; both were an accident of a path that did not exist.

### 2. An unrecognized option is a usage error, exit 2 (2 records)

`crlf/unknown-flag`: exit 1 with a `FileNotFoundError` traceback for a file called
`--bogus` → exit 2 with `crlf.py: error: unrecognized arguments: --bogus`.
`shelf/unknown-flag`: exit **0**, having walked the other, valid root and reported
`Tests performed: 2 / Errors found: 0` as though the command line were fine →
exit 2 with the same argparse error.

Attribution: unavoidable with a parser, and 2 is what the other eleven tools already
return for a usage error. The shelf case is the one worth naming: base *accepted* a
typo'd flag and reported a clean run, so a mistyped `--verbsoe` produced a
successful-looking check. **This is an exit-code change on a surface the plan calls
frozen; §7 records it as an owner decision.**

### 3. An uncaught exception gains one stack frame (4 records)

`crlf/empty-file` (`ZeroDivisionError`), `crlf/missing-file` and
`crlf/directory-argument` (`FileNotFoundError`, `IsADirectoryError`), and
`opus/no-holdings-env` (`KeyError`). Same exception, same message, same exit code
1; the traceback now shows `sys.exit(main())` and a `main` frame where it showed
`<module>`, and the line numbers inside the module move. +5 / −2 lines each.

Attribution: mechanical. The code that raises is unchanged and still uncaught —
none of these tools grew an exception handler.

### 4. An extraneous index shelf is counted (1 record)

`shelf/index-extraneous`, §2 above. This is the bug fix.

### 5. `show_opus_products --help` works with no holdings roots set (1 record)

`opus/help-without-holdings-env`: exit 1 with a `KeyError: 'PDS3_HOLDINGS_DIR'`
traceback from module import → exit 0 with the help text.

Attribution: the two `os.environ[…]` lookups moved from module level into `main()`,
after `parse_args`. Keeping them at module level would mean the module cannot be
imported without both variables — so no in-process test could reach `main()`, no
autodoc build could document it, and an entry point could not load it. A real run
still raises the same `KeyError` from the same two lookups (record
`opus/no-holdings-env`, change 3 above).

### 6. argparse decides what an argument *is*, where argv used to be literal (7 records)

The two migrated tools handled their flags by searching `sys.argv` for the exact
string and calling `remove()`. Every other argument was a path, whatever it looked
like. A parser classifies arguments instead, and that changes four shapes:

| record | base | head |
|---|---|---|
| `crlf/abbreviated-repair` (`--rep f`) | exit 1, `FileNotFoundError: '--rep'`, **file untouched** | exit 2, `unrecognized arguments: --rep`, file untouched |
| `crlf/abbreviated-verbose` (`--verb f`) | exit 1, `FileNotFoundError` | exit 2 |
| `shelf/abbreviated-verbose` (`--verb root`) | exit 0, walked `--verb` as a path (nothing) and the root, non-verbose | exit 2 |
| `crlf/repeated-flag` (`--verbose --verbose f`) | exit 1, `FileNotFoundError: '--verbose'` — `remove()` takes one | exit 0, verbose |
| `crlf/dash-file-bare` (`-dash.txt`) | **exit 0, `-dash.txt INVALID`** | **exit 2** |
| `crlf/dash-file-after-separator` (`-- -dash.txt`) | exit 1, `FileNotFoundError: '--'` | exit 2 |
| `crlf/dash-file-after-a-path` (`ok.txt -- -dash.txt`) | exit 1, `FileNotFoundError: '--'` | exit 0, both checked |

**The abbreviations are a choice, and the choice is `allow_abbrev=False`.** With
argparse's default, `crlf --rep f` would mean `--repair` and **rewrite every file
named after it**, where the base tool refused the command line outright. A
misspelling that silently modifies holdings is the worst outcome available here, so
both new parsers turn abbreviation off, which folds these three records into change
2 above: an option that is not spelled out is not an option. Two tests pin it, and
dropping either `allow_abbrev=False` fails exactly one of them (§5.3, M8).
`show_opus_products` is **not** changed: its parser is the one that was already
there, abbreviations and all, and record `opus/abbreviated-paths` (`--pat …`) is
byte-identical base to head, which is what confines this to the two new parsers.

**`crlf/dash-file-bare` is the one base-working invocation this PR breaks.** A file
whose name begins with `-` was a path and is now an option. The usual answer is
`--`, and it half-works: under `parse_intermixed_args`, `--` is honoured only when a
plain positional precedes it, so `crlf -- -dash.txt` is still a usage error while
`crlf ok.txt -- -dash.txt` checks both. That is argparse's behaviour, not a design;
it is pinned by
`test_a_path_beginning_with_a_dash_is_reachable_only_after_another_path` and
recorded as deferred entry 141. No file in either holdings root begins with `-`
(`find $PDS3_HOLDINGS_DIR $PDS4_HOLDINGS_DIR -name '-*'` finds none), which is why
it is recorded rather than treated as a blocker.

### What did not change, and was checked

| behaviour | records | preserved by |
|---|---|---|
| flags accepted anywhere among the positionals | `crlf/flag-after-path`, `crlf/flag-between-paths`, `shelf/verbose-after-path`, `shelf/verbose-between-roots` | `parse_intermixed_args`, not `parse_args` |
| naming no path at all succeeds silently | `crlf/no-arguments`, `shelf/no-arguments` | `nargs='*'`, not `'+'` |
| a misspelled flag does not become a real one | `crlf/abbreviated-repair`, `shelf/abbreviated-verbose` | `allow_abbrev=False` on the two new parsers |
| `--verbose --verbose root` reports the same as one | `shelf/repeated-verbose` | byte-identical: base removed one occurrence and walked the other as a path that does not exist |
| a run that repairs 2+ files prints no summary | `crlf/repair-two-of-three` | left as it is; see deferred 136 |
| `show_opus_products --help` text | `opus/help` | byte-identical, though the description literal is re-indented — argparse collapses whitespace in a description |
| `show_opus_products` accepts an abbreviated flag | `opus/abbreviated-paths` | its parser is untouched, `allow_abbrev` included |
| `--debug` prints `NoneType: None` when nothing raised | `opus/unresolvable-path-debug` | left as it is |
| every `show_opus_products` output mode | 27 records | body moved verbatim into `main()` |

The first three "preserved by" rows are choices, not accidents: `parse_args`,
`nargs='+'` and argparse's default `allow_abbrev` are the obvious spellings and
each was measured to break a base behaviour (§5.3, mutations M4, M5 and M8).

## 4. Which tests moved in-process, and which did not

The plan says to update PR-13's subprocess tests for these tools to call `main()`
in-process. `tests/holdings_maintenance/__init__.py` documents why the tool tests
use subprocesses at all: `PdsFile.CACHE` is class-level and keyed by *logical* path
and the session preloads the real holdings tree, so an in-process call can resolve
a temporary-tree path back to the real tree. That reasoning was applied per tool
rather than across the board.

| tool | moved? | how its tests break down | why |
|---|---|---|---|
| `shelf_consistency_check` | **yes** | 13 tests: **12** call `main()` in-process, 1 is the `python -m` subprocess. (The one full-holdings test also runs `pdschecksums` and `pdsinfoshelf` as subprocesses to build the tree it then checks in-process.) | imports `argparse`, `os`, `sys`. No PdsFile class, no holdings root, no cwd-relative path — the hazard cannot arise |
| `crlf` | **yes** | 31 tests: 16 call the classifier directly and always did, **13** are new in-process command-line tests, 2 are subprocesses | imports `argparse`, `sys`. Same |
| `show_opus_products` | **no** | 9 tests: 6 drive the tool as a subprocess against a dogfooded tree, 2 are new subprocess probes with no holdings, 1 inspects the parser | calls `Pds3File.use_shelves_only(True)` and `Pds3File.preload()` / `Pds4File.preload()` on both roots. In-process it would preload a temporary tree into the same class-level cache the session preloaded the real tree into, and leave shelves-only set for every test that ran after it. Exactly the documented hazard |

**This last row is a departure from the plan**, which asked for both `main()`-less
tools to move. `plans/2026-08-07-pr-28-deviation-addendum.md` records it for the
owner, per §6.4's rule that a deviation needs an addendum; §7 lists it as the
decision the owner is most likely to make differently.

`support.HOLDINGS_FREE_TOOLS` is that criterion as a frozen set, and both
`run_tool_in_process()` and `run_tool_without_holdings()` assert against it:

```
>>> support.run_tool_in_process('pdsinfoshelf', '--validate', '/tmp')
AssertionError: pdsinfoshelf is not holdings-free; drive it with run_tool() instead
```

**Every one of the three tools keeps at least one subprocess test that runs without
holdings.** An in-process call imports the module and calls `main` by name, so it
passes whether or not the module has a `__main__` block — which is the very thing
this PR adds. `run_tool_without_holdings()` runs `python -m <module>` with both
holdings variables removed, and pins that the entry point exists, that the process
exit code is `main()`'s return value, and that neither migrated tool needs a
holdings root. `show_opus_products` gets the same guarantee from
`test_the_module_is_runnable_as_python_m`, which runs `python -m … --help` with no
holdings — without it, that tool's `__main__` block would be covered only by
`full_holdings` tests and a hosted runner with no holdings could not notice its
absence. Mutation M2 (§5.3) confirms all three are non-vacuous.

`crlf` also keeps a subprocess test for the one thing an in-process call cannot
show at all: `test_an_unreadable_file_ends_the_process_with_a_traceback` pins that
an uncaught exception leaves the *process* at exit 1 with the traceback on stderr.
In-process, `run_tool_in_process` lets any non-`SystemExit` exception propagate, so
the test would only see the exception type.

The package header in `tests/holdings_maintenance/__init__.py` now says which tool
is driven which way and why, instead of "every tool is driven as a subprocess",
which stopped being true here.

## 5. Gates

### 5.1 Full data suite, both modes, base and head

```
python -m pytest tests/api/ tests/core/ tests/holdings_maintenance/ tests/pds3file/ \
    tests/rules/pds3/ tests/pds4file/ tests/rules/pds4/ --mode ns -rA --junitxml=…
python -m pytest tests/pds3file/ tests/rules/pds3/ --mode s -rA --junitxml=…
```

| | base ids | head ids | added | removed | outcome changes |
|---|---:|---:|---:|---:|---:|
| `--mode ns` | 1,097 | 1,121 | 25 | 1 | **0** |
| `--mode s` | 558 | 558 | 0 | 0 | **0** |

`--mode ns`: base 1,063 passed / 34 skipped; head 1,087 passed / 34 skipped.
`--mode s`: base and head both 555 passed / 3 skipped. No id that exists in both
runs changed outcome, in either mode, and nothing failed or errored in any of the
four runs.

Every one of the 25 added ids is a test this PR wrote, and every one passes. The
single removed id is `test_an_extraneous_index_shelf_raises`, the test that pinned
the bug §2 fixes. The full list is §5.2.

### 5.2 The 25 added ids and the 1 removed

Removed: `test_shelf_consistency_check.py::test_an_extraneous_index_shelf_raises`
— the test that pinned the `NameError` as current behaviour, and whose docstring
said a fix has to invert it.

Added, by module:

- `test_crlf.py` (15): `TestCommandLine::` `test_only_invalid_files_are_listed`,
  `test_verbose_lists_every_file`, `test_repair_rewrites_the_file_and_reports_it`,
  `test_a_single_file_gets_no_summary_line`,
  `test_two_repairs_print_no_summary_at_all`,
  `test_flags_are_accepted_among_the_paths`, `test_no_arguments_prints_nothing`,
  `test_help_names_every_flag`, `test_an_unrecognized_flag_is_a_usage_error`,
  `test_an_abbreviated_flag_is_a_usage_error_and_rewrites_nothing`,
  `test_a_repeated_flag_is_accepted`,
  `test_a_path_beginning_with_a_dash_is_reachable_only_after_another_path`,
  `test_an_unreadable_file_raises_rather_than_being_reported`; and, at module
  level, `test_the_module_is_runnable_as_python_m` and
  `test_an_unreadable_file_ends_the_process_with_a_traceback`.
- `test_shelf_consistency_check.py` (7):
  `test_an_index_shelf_whose_label_exists_is_counted_not_reported`,
  `test_an_extraneous_index_shelf_is_counted_like_any_other`,
  `test_no_arguments_reports_an_empty_run`,
  `test_verbose_is_accepted_between_the_shelf_roots`,
  `test_an_unrecognized_flag_is_a_usage_error`,
  `test_an_abbreviated_flag_is_a_usage_error`,
  `test_the_module_is_runnable_as_python_m`.
- `test_show_opus_products.py` (3):
  `test_the_parser_is_built_without_touching_the_environment`,
  `test_the_module_imports_with_neither_holdings_root_set`,
  `test_the_module_is_runnable_as_python_m`.

### 5.3 Mutation probes: fourteen, all caught

Run against `pytest tests/holdings_maintenance/test_crlf.py
tests/holdings_maintenance/test_shelf_consistency_check.py
tests/holdings_maintenance/test_show_opus_products.py --mode ns`, which sits at 54
passed. Each mutation was applied to a copy-restored file, never through `git`, and
**one file at a time**: a probe that changes the same construct in two files can be
caught by one file's test while the other's goes unguarded, and reads as covered.

| # | file | mutation | failures | caught by |
|---|---|---|---:|---|
| M1 | shelf | `errors += 1` → `error += 1` in the index branch | 1 | `test_an_extraneous_index_shelf_is_counted_like_any_other` |
| M2a | crlf | `__main__` guard neutralized | 2 | `test_the_module_is_runnable_as_python_m`, `test_an_unreadable_file_ends_the_process_with_a_traceback` |
| M2b | shelf | `__main__` guard neutralized | 1 | `test_the_module_is_runnable_as_python_m` |
| M2c | opus | `__main__` guard neutralized | 6 | 5 dogfooded tests **and** `test_the_module_is_runnable_as_python_m`, the holdings-free one |
| M3 | opus | holdings roots read at import again | 2 | `test_the_module_imports_with_neither_holdings_root_set`, `test_the_module_is_runnable_as_python_m` |
| M4a | crlf | `parse_intermixed_args` → `parse_args` | 2 | `test_flags_are_accepted_among_the_paths`, `test_a_path_beginning_with_a_dash_…` |
| M4b | shelf | `parse_intermixed_args` → `parse_args` | 1 | `test_verbose_is_accepted_between_the_shelf_roots` |
| M5a | crlf | positional `nargs='*'` → `'+'` | 1 | `test_no_arguments_prints_nothing` |
| M5b | shelf | positional `nargs='*'` → `'+'` | 1 | `test_no_arguments_reports_an_empty_run` |
| M6 | shelf | `main()` returns 0 unconditionally | 5 | four report-an-error tests plus the `python -m` one |
| M7 | shelf | a *non-counting* fix: `try: error += 1 / except NameError: pass` | 1 | `test_an_extraneous_index_shelf_is_counted_like_any_other` |
| M8a | crlf | `allow_abbrev=False` dropped | 1 | `test_an_abbreviated_flag_is_a_usage_error_and_rewrites_nothing` |
| M8b | shelf | `allow_abbrev=False` dropped | 1 | `test_an_abbreviated_flag_is_a_usage_error` |
| M9 | — | `run_tool_in_process('pdsinfoshelf', …)` | — | the `HOLDINGS_FREE_TOOLS` assertion |

M4, M5 and M8 are the ones that matter: `parse_args`, `nargs='+'` and argparse's
default `allow_abbrev` are the three spellings a reader would reach for, and each
silently breaks a command line that works today. M7 matters for a different reason:
it is the "fix" that stops the crash without counting the error, and the regression
test rejects it too.

### 5.4 The rest

```
scripts/run-all-checks.sh -c -s          # with no holdings env vars
```
All checks passed, both trees. Its pytest leg: base **281 passed / 816 skipped**,
head **305 passed / 816 skipped**. The skip count does not move and the pass count
moves by exactly +24, which is §5.2's 25 added minus the 1 removed: every test this
PR wrote builds its own tree and runs on a machine with no holdings at all, so none
of them lands in the skipped column.

```
python -m pytest tests/api/                       # 26 passed
ruff check src/pdsfile tests scripts              # All checks passed!
ruff check .                                      # All checks passed!
ruff check --preview --select E111,E112,E113 .    # All checks passed!
```

The four frozen files are byte-identical to `3d044b2`:

```
git diff --name-only 3d044b2 -- tests/api/api_manifest.json \
    tests/api/manifest_allowlist.json scripts/dump_public_api.py \
    tests/api/test_api_freeze.py        # empty
```
and their md5s match the base tree's, file by file.

`bandit` and `vulture` are disabled and not installed; nothing is claimed about
them.

### 5.5 What the transcript harness is

Not in the repository — it lives with the run, like PR-25's through PR-27's. It
builds a temporary disk holding (a) a directory of fixed sample files for `crlf`,
rebuilt before every scenario because `--repair` rewrites them, (b) small legacy
`shelves/` + `holdings/` trees for `shelf_consistency_check`, one per branch of its
walk, and (c) a copy of the declared PDS3 source subset with
`pdschecksums --initialize` and `pdsinfoshelf --initialize` run over it, for
`show_opus_products`. Each tool is then run under `python -m` with the temporary
disk as both holdings roots, and stdout, stderr and the exit code are captured with
the disk path, the tree path and the interpreter path normalized out.

The base-vs-base control is what makes the walk order trustworthy: the shelf
scenarios' output order comes from `os.walk`, and two independent runs at `3d044b2`
produced byte-identical transcripts for all 75 records.

## 6. Ratchet

```
python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); \
  p=d['tool']['ruff']['lint']['per-file-ignores']; \
  print(len(p), sum(len(v) for v in p.values()), len(d['project']['scripts']))"
```

| | base | head |
|---|---:|---:|
| per-file-ignores entries | 67 | **66** |
| code slots | 181 | **180** |
| findings with the ratchet emptied | 2,250 | **2,249** |
| `[project.scripts]` entries | 11 | 11 |

```
ruff check --config 'lint.per-file-ignores = {}' src/pdsfile tests scripts
```
→ 2,250 at `3d044b2`, 2,249 at head. One entry retires: `F821` on
`shelf_consistency_check.py`, §2.3.

**`PT028` on `crlf.py` stays.** It fires twice, on `test_crlf`'s `task` and
`threshold` defaults, and only because the function's *name* looks like a pytest
test — it is the tool's classifier, which the module itself and
`tests/holdings_maintenance/test_crlf.py` are the only callers of
(`grep -rn 'test_crlf\b' --include=*.py .`). A rename is therefore mechanically
safe inside this repository, and it is not done here: the function is a public name
on a shipped module, PR-32 is chartered to document `crlf` as a program, and the
entry marks a lint false positive rather than a defect, which is what the ratchet
is for. The entry now carries the count and the reason as a comment, matching the
style of the neighbouring lines. Deferred entry 137 records the measurement so the
owner can spend a one-line PR on it if the trade looks different from there.

## 7. Decisions the owner might make differently

1. **`show_opus_products`' tests were not moved in-process**, though the plan's
   PR-28 entry required both `main()`-less tools to move. §4 has the measurement
   and `plans/2026-08-07-pr-28-deviation-addendum.md` is the §6.4 addendum, which
   this PR **cannot merge without the owner acknowledging**. The alternative — an
   autouse fixture that snapshots and restores `LOCAL_PRELOADED`, `SHELVES_ONLY`
   and the caches around each call — is new global-state machinery in the test tree
   whose correctness is the hard part, traded for the runtime of five subprocesses.
   That judgement is the deviation; the addendum exists so it is the owner's.
2. **An unrecognized or abbreviated option now exits 2 rather than 0 or 1** (§3,
   changes 2 and 6). CLI exit codes are frozen this phase. What is frozen in
   practice is what a *valid* invocation returns, and none of the base values was
   designed — one was an uncaught `FileNotFoundError`, the other was the tool
   cheerfully reporting a clean run after silently swallowing a typo'd flag. 2 is
   argparse's, and the eleven console scripts' already. Reverting would mean not
   using argparse for the flags, which is the PR.
3. **`allow_abbrev=False` on the two new parsers, and not on `show_opus_products`.**
   The asymmetry is deliberate: the two new parsers get to choose, and `--rep`
   silently meaning `--repair` would let a misspelling rewrite files;
   `show_opus_products`' parser already existed with abbreviation on, so turning it
   off there would be a behaviour change this PR invented rather than inherited.
   If the owner wants one rule, it should be one rule applied in a PR that says so.
4. **`crlf` can no longer be given a path beginning with `-`** (§3, change 6, and
   deferred 141). This is the only base-working invocation the PR breaks. No file
   in either holdings root has such a name, and `crlf f -- -dash.txt` still reaches
   one, but it is a loss and not a wash.
5. **`nargs='*'`, not `'+'`, on both positionals.** The documented syntax of
   `shelf_consistency_check` is `shelf_root [shelf_root ...]` — at least one — but
   the module as written prints an empty summary and exits 0 when given none, so
   `'+'` would be an exit-code change (0 → 2) on the no-argument invocation.
   Preservation won. If the owner prefers the documented contract, `'+'` on both is
   a two-character change and mutation M5 names the two tests that then invert.
6. **`crlf.test_crlf` keeps its name, and its `PT028` entry** (§6).
7. **The two-repair summary gap is preserved, not fixed** (deferred 136). It is a
   real defect — `if repairs == 1` inside `if repairs:` — but fixing it changes
   output text for a reason the Phase-6 rule does not cover: keeping it forces no
   duplication and no flag.
8. **Both header comment blocks were rewritten, and one of them corrected.** Both
   tools' `Use:` / `Syntax:` lines named an invocation that no longer works — the
   package moved under `src/pdsfile/` in PR-06, so `python crlf.py …` and
   `shelf-consistency-check.py …` are neither of them a command — and both now show
   the `python -m` form. `shelf_consistency_check`'s block was also carrying
   `# # shelf-consistency-check.py`, a stray `#` and a filename that is not the
   module's; the invocation line had to change and those went with it. Nothing else
   in either header moved.

## 8. Deferred entry 130 — can the three drivers become one?

Measured, not acted on; §4.3 of the brief is scope-only. The full write-up is
deferred entry 130's amendment. In brief:

```
# each function's body, docstring / def line / blanks / comments dropped,
# and the `_common.` qualifier normalized away
run_main 57 code lines, run_selection_main 69, run_index_main 55
common to all three (ordered common subsequence): 39
```

39 of 181 lines, 68.4% / 56.5% / 70.9% of the three. But **only 15 of those 39 form
a contiguous block identical in all three** — the preamble, from
`build_arg_parser(spec)` down to the log-root handler loop. The rest is
try/except/finally scaffolding and handler construction, in runs of five lines and
fewer, interleaved with statements that differ in all three. Eight variation points
would have to become hooks or flags; seven of them are forced, and the eighth — the
task header wording — is one the Phase-6 output-text ruling would let a merger
dissolve by unifying the text rather than carrying a flag, at the price of a log
line moving on four tools.

**Recommendation: no.** The measurement points somewhere else: extracting the
15-line preamble as a fourth `_common` helper takes 38% of the commonality with
zero new variation points, and leaves the three loops alone. That is a different,
much smaller PR, and it is the owner's to authorise.

## 9. When each record was taken

| record | at |
|---|---|
| base suite runs, base transcript ×2, base ratchet, base `run-all-checks` | `3d044b2` |
| head suite runs, head transcript, head ratchet, head `run-all-checks`, mutations | branch head |
| driver measurement (§8) | branch head; the three drivers are untouched by this PR, so it is also `3d044b2`'s answer |

`critiques/pr-28/check_record_numbers.py` re-derives from the tree every number in
this file, in PR-28's entries in `critiques/deferred-observations.md` and in the
plan's PR-28 entry **that the tree can answer**: the line-count table (both columns
— the base column comes from `git show 3d044b2:…`, not from a constant); the ratchet
and `[project.scripts]` counts at base and head and the arithmetic on them; the
finding count, by running `ruff` (if `ruff` is absent it says so rather than
passing); every driver figure in §8 and entry 130, including the block structure;
§4's per-module test breakdown, counted off the AST and cross-checked against the
prose; and the presence of every test id §5.2 names plus the absence of the one it
says was removed. What it cannot re-derive is a number that comes from running the
suite or the transcript; those carry their command lines above instead. Needles are
matched with whitespace collapsed, so a number that sits across a line break still
matches.

**The gate has its own negative control**: ten perturbations, spread across all
four documents it reads and across every kind of number — a line count, the
shared-driver count, the driver block sizes, the plan's ratchet line,
`HOLDINGS_FREE_TOOLS`, one added test id, the added-id count, the
`[project.scripts]` base cell, §4's prose, and a test *renamed in the tree* rather
than in a document. Each was caught, and the tree was clean again afterwards. The
gate was written before the record was; the tenth perturbation is here because an
earlier version of the gate let it through, which is the shape of miss it exists to
prevent.
