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

The "head" column is what `critiques/pr-28/check_record_numbers.py` compares against the
tree it is run in, so it is the current line count rather than a frozen one, and a later
PR that changes one of these files updates its row. PR-30a's module docstring for
`show_opus_products.py` took that row from 199 to **265**; nothing else in the table has
moved since.

| file | base | head | today's entry point |
|---|---:|---:|---|
| `src/pdsfile/holdings_maintenance/pds3/crlf.py` | 121 | 169 | `build_arg_parser()`, `main(argv=None)`, `__main__` |
| `src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py` | 90 | 132 | same |
| `src/pdsfile/tools/show_opus_products.py` | 162 | 265 | same |
| `tests/holdings_maintenance/support.py` | 710 | 830 | — |
| `tests/holdings_maintenance/test_crlf.py` | 142 | 395 | — |
| `tests/holdings_maintenance/test_shelf_consistency_check.py` | 189 | 386 | — |
| `tests/holdings_maintenance/test_show_opus_products.py` | 134 | 259 | — |

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

The index branch had one test and now has two.
`test_an_index_shelf_whose_label_exists_is_counted_not_reported` covers the other
side of the same `if` — an index shelf is matched against a holdings `.lbl`, not a
directory — which nothing covered before, and runs the branch under `--verbose` as
well, because that branch prints the mapped path from its own line rather than the
one the info and link branches share.

### 2.3 `F821` retired — confirmed, not assumed

```
ruff check --config 'lint.per-file-ignores = {}' \
    src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py
```
→ `All checks passed!` at head. The `"…/shelf_consistency_check.py" = ["F821"]`
line is removed from `pyproject.toml`.

## 3. Behavior changes, enumerated

The gate is an 84-record transcript of all three tools, captured at base and head
and diffed record by record. It covers every output mode of each tool, every flag,
the flag combinations that select output, and the argument *shapes* — `-h`, an
abbreviated flag, a flag
given an explicit value, a repeated flag, `--`, a path beginning with `-` — that
argparse treats differently from argv read literally, on each tool and with the
holdings roots both set and unset. It is not a proof of completeness; it is 84
invocations chosen to include everything the three tools' code branches on plus
everything argparse decides for them.

**Base-vs-base control first: 0 of 84 records differ.** Base-vs-head: **26 of 84
differ**, +137 / −162 lines. The other 58 records are byte-identical: every
successful crlf run, every successful shelf run, and 27 of `show_opus_products`'
31 — both tables, `--pprint`, `--raw`, an abbreviated `--pat`, and every usage
error with the holdings roots set. The four that differ are its three no-holdings
records (change 5) and one traceback (change 3).

Six kinds of change across those twenty-six records.

### 1. `--help` and `-h` answer, on the two tools that had no parser (4 records)

`crlf/help`, `crlf/short-help`: base treated the flag as a file path and died with
`FileNotFoundError`, exit 1. Head prints the help and exits 0.
`shelf/help`, `shelf/short-help`: base treated it as a directory to walk, found
nothing, and printed `Tests performed: 0 / Errors found: 0`, exit 0. Head prints the
help and exits 0.

Attribution: this is what having a parser *is*. Neither line of base output was a
message the tool meant to emit; both were an accident of a path that did not exist.
`-h` is argparse's, not a flag this PR chose to add; the tests cover both
spellings.

### 2. A command line the parser cannot classify is a usage error, exit 2 (8 records)

Three shapes, on both migrated tools: an unrecognized option, an abbreviated one,
and one given an explicit value.

| record | base | head |
|---|---|---|
| `crlf/unknown-flag` (`--bogus`) | exit 1, `FileNotFoundError: '--bogus'` | exit 2, `unrecognized arguments: --bogus` |
| `crlf/abbreviated-repair` (`--rep`) | exit 1, file untouched | exit 2, file untouched |
| `crlf/abbreviated-verbose` (`--verb`) | exit 1 | exit 2 |
| `crlf/flag-with-a-value` (`--verbose=1`) | exit 1 | exit 2, `argument --verbose: ignored explicit argument '1'` |
| `crlf/repair-with-a-value` (`--repair=yes`) | exit 1, file untouched | exit 2, file untouched |
| `shelf/unknown-flag` (`--bogus`) | exit **0**, walked the other, valid root and reported `Tests performed: 2 / Errors found: 0` as though the command line were fine | exit 2 |
| `shelf/abbreviated-verbose` (`--verb`) | exit 0, ran non-verbose | exit 2 |
| `shelf/flag-with-a-value` (`--verbose=1`) | exit 0, ran non-verbose | exit 2 |

Attribution: unavoidable with a parser, and 2 is what the other eleven tools already
return for a usage error. The shelf rows are the ones worth naming: base *accepted* a
typo'd flag and reported a clean run, so a mistyped `--verbsoe` produced a
successful-looking check. **This is an exit-code change on a surface the plan calls
frozen; §7 records it as an owner decision.**

**The abbreviations are a choice, and the choice is `allow_abbrev=False`.** With
argparse's default, `crlf --rep f` would mean `--repair` and **rewrite every file
named after it**, where the base tool refused the command line outright. A
misspelling that silently modifies holdings is the worst outcome available here, so
both new parsers turn abbreviation off. Two tests pin it, and dropping either
`allow_abbrev=False` fails exactly one of them (§5.3, M8). `show_opus_products` is
**not** changed: its parser is the one that was already there, abbreviations and
all, and record `opus/abbreviated-paths` (`--pat …`) is byte-identical base to head,
which is what confines this to the two new parsers.

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

### 5. `show_opus_products` reaches its parser before it reads the environment (3 records)

With either holdings root unset, the base module died at import, before argparse
existed, whatever the command line was. Now the parser answers first.

| record | base | head |
|---|---|---|
| `opus/help-without-holdings-env` (`--help`) | exit 1, `KeyError: 'PDS3_HOLDINGS_DIR'` | exit 0, the help text |
| `opus/usage-error-without-holdings-env` (`--bogus`) | exit 1, the same `KeyError` | exit **2**, `the following arguments are required: --paths` |
| `opus/no-arguments-without-holdings-env` | exit 1, the same `KeyError` | exit **2**, the same message |

Attribution: the two `os.environ[…]` lookups moved from module level into `main()`,
after `parse_args`. Keeping them at module level would mean the module cannot be
imported without both variables — so no in-process test could reach `main()`, no
autodoc build could document it, and an entry point could not load it.

**This is a third tool whose exit code moves**, and it is confined to the
no-holdings environment: with both roots set, base and head agree on `--bogus`, on
no arguments, on `-h` and on a bare `--paths` (records `opus/unknown-flag`,
`opus/no-paths`, `opus/help`, `opus/empty-paths`, all byte-identical). A real run
with a root missing still raises the same `KeyError` from the same two lookups,
exit 1 (record `opus/no-holdings-env`, change 3 above). Deferred entry 135 names all
three tools.

### 6. An argument's *meaning* changes, not just its acceptance (6 records)

The two migrated tools handled their flags by searching `sys.argv` for the exact
string and calling `remove()`. Every other argument was a path, whatever it looked
like. A parser classifies arguments instead, and two shapes change meaning rather
than simply becoming errors:

| record | base | head |
|---|---|---|
| `crlf/repeated-flag` (`--verbose --verbose f`) | exit 1, `FileNotFoundError: '--verbose'` — `remove()` takes one occurrence and the other became a path | exit 0, verbose |
| `crlf/repeated-repair` (`--repair --repair f`) | exit 1, `FileNotFoundError: '--repair'`, **file untouched** | exit 0, **file repaired** |
| `crlf/dash-file-bare` (`-dash.txt`) | **exit 0, `-dash.txt INVALID`** | **exit 2** |
| `shelf/dash-root` (`-dashroot`) | **exit 0**, walked it, `Tests performed: 0` | **exit 2** |
| `crlf/dash-file-after-separator` (`-- -dash.txt`) | exit 1, `FileNotFoundError: '--'` | exit 2 on Python ≤ 3.12, exit 0 from 3.13 — see below |
| `crlf/dash-file-after-a-path` (`ok.txt -- -dash.txt`) | exit 1, `FileNotFoundError: '--'` | exit 0, both checked |

**A repeated flag now means the flag.** `crlf --repair --repair f` is the one that
matters: at base the second `--repair` became a path and the run died before
touching anything, and now the file is rewritten. It is the intended effect of the
command line either way — nobody types `--repair` twice meaning *do not repair* —
but it is a run that writes where the base run did not, so it is named here rather
than folded into "argparse accepts more".

**`crlf/dash-file-bare` and `shelf/dash-root` are the base-working invocations this
PR breaks.** An argument beginning with `-` was a path and is now an option. The
usual answer is `--`, and under `parse_intermixed_args` it works only when a plain
positional precedes it: `crlf ok.txt -- -dash.txt` checks both, everywhere.

**`crlf -- -dash.txt`, with nothing in front of the separator, is the one row in
this record whose head value depends on the interpreter.** `parse_intermixed_args`
splits argv at the first `--` and re-parses the remainder; through Python 3.12 the
remainder is read with the optionals still live and the command line is rejected
(exit 2), and from 3.13 it is not (exit 0). Measured on 3.12.3 — which is what the
transcript above was captured on — and on 3.14.5, and confirmed by CI's 3.13 leg,
which is where it was found: **every local run and all four review rounds used one
interpreter and could not have seen it.** The tests assert only the two outcomes
that hold on every supported version, and deferred entry 141 carries the split.

No file in either holdings root begins with `-`
(`find $PDS3_HOLDINGS_DIR $PDS4_HOLDINGS_DIR -name '-*'` finds none), which is why
all of this is recorded rather than treated as a blocker.

### What did not change, and was checked

| behaviour | records | preserved by |
|---|---|---|
| flags accepted anywhere among the positionals | `crlf/flag-after-path`, `crlf/flag-between-paths`, `shelf/verbose-after-path`, `shelf/verbose-between-roots` | `parse_intermixed_args`, not `parse_args` |
| naming no path at all succeeds silently | `crlf/no-arguments`, `shelf/no-arguments` | `nargs='*'`, not `'+'` |
| a misspelled flag does not become a real one | `crlf/abbreviated-repair`, `shelf/abbreviated-verbose` | `allow_abbrev=False` on the two new parsers |
| `--verbose --verbose root` reports the same as one | `shelf/repeated-verbose` | byte-identical: base removed one occurrence and walked the other as a path that does not exist |
| `show_opus_products`' usage errors, with the roots set | `opus/unknown-flag`, `opus/no-paths`, `opus/empty-paths`, `opus/help` | byte-identical: its parser is untouched, so only the no-holdings environment moves |
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
| `shelf_consistency_check` | **yes** | 18 tests: **15** call `main()` in-process, 2 call it directly to pin its `argv` parameter, 1 is the `python -m` subprocess. (The one full-holdings test also runs `pdschecksums` and `pdsinfoshelf` as subprocesses to build the tree it then checks in-process.) | imports `argparse`, `os`, `sys`. No PdsFile class, no holdings root, no cwd-relative path — the hazard cannot arise |
| `crlf` | **yes** | 35 tests: 16 call the classifier directly and always did, **15** are new in-process command-line tests, 2 call `main()` directly to pin its `argv` parameter and one more checks the runner restores `sys.argv`, and 2 are subprocesses | imports `argparse`, `sys`. Same |
| `show_opus_products` | **no** | 10 tests: 6 drive the tool as a subprocess against a dogfooded tree, 2 are new subprocess probes with no holdings, 1 inspects the parser and 1 calls `main()` directly to pin its `argv` parameter | calls `Pds3File.use_shelves_only(True)` and `Pds3File.preload()` / `Pds4File.preload()` on both roots. In-process it would preload a temporary tree into the same class-level cache the session preloaded the real tree into, and leave shelves-only set for every test that ran after it. Exactly the documented hazard |

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
| `--mode ns` | 1,097 | 1,134 | 38 | 1 | **0** |
| `--mode s` | 558 | 558 | 0 | 0 | **0** |

`--mode ns`: base 1,063 passed / 34 skipped; head 1,100 passed / 34 skipped.
`--mode s`: base and head both 555 passed / 3 skipped. No id that exists in both
runs changed outcome, in either mode, and nothing failed or errored in any of the
four runs.

Every one of the 38 added ids is a test this PR wrote, and every one passes. The
single removed id is `test_an_extraneous_index_shelf_raises`, the test that pinned
the bug §2 fixes. The full list is §5.2.

### 5.2 The 35 added test functions, 38 added ids, and the 1 removed

Removed: `test_shelf_consistency_check.py::test_an_extraneous_index_shelf_raises`
— the test that pinned the `NameError` as current behaviour, and whose docstring
said a fix has to invert it.

Added, by module — **test functions**. Three of them are parametrized over two
values each (`test_help_names_every_flag` and
`test_a_store_true_flag_rejects_an_explicit_value` in `test_crlf.py`,
`test_help_names_the_flag_and_the_positional` in
`test_shelf_consistency_check.py`), so 35 functions produce the 38 ids §5.1
counts:

- `test_crlf.py` (19): `TestCommandLine::` `test_only_invalid_files_are_listed`,
  `test_verbose_lists_every_file`, `test_repair_rewrites_the_file_and_reports_it`,
  `test_a_single_file_gets_no_summary_line`,
  `test_two_repairs_print_no_summary_at_all`,
  `test_flags_are_accepted_among_the_paths`, `test_no_arguments_prints_nothing`,
  `test_help_names_every_flag`, `test_an_unrecognized_flag_is_a_usage_error`,
  `test_an_abbreviated_flag_is_a_usage_error_and_rewrites_nothing`,
  `test_a_store_true_flag_rejects_an_explicit_value`,
  `test_a_repeated_flag_is_accepted`,
  `test_a_path_beginning_with_a_dash_needs_a_path_and_a_separator_before_it`,
  `test_an_unreadable_file_raises_rather_than_being_reported`; and, at module
  level, `test_the_module_is_runnable_as_python_m` and
  `test_an_unreadable_file_ends_the_process_with_a_traceback`; and `TestArgvContract::`
  `test_an_explicit_argv_is_what_gets_parsed`, `test_no_argument_means_sys_argv` and
  `test_the_in_process_runner_leaves_sys_argv_as_it_found_it`.
- `test_shelf_consistency_check.py` (12):
  `test_an_index_shelf_whose_label_exists_is_counted_not_reported`,
  `test_an_extraneous_index_shelf_is_counted_like_any_other`,
  `test_no_arguments_reports_an_empty_run`,
  `test_verbose_is_accepted_between_the_shelf_roots`,
  `test_an_unrecognized_flag_is_a_usage_error`,
  `test_an_abbreviated_flag_is_a_usage_error`,
  `test_help_names_the_flag_and_the_positional`,
  `test_a_flag_given_a_value_is_a_usage_error`,
  `test_a_shelf_root_beginning_with_a_dash_is_a_usage_error`,
  `test_an_explicit_argv_is_what_gets_parsed`, `test_no_argument_means_sys_argv`,
  `test_the_module_is_runnable_as_python_m`.
- `test_show_opus_products.py` (4):
  `test_the_parser_is_built_without_touching_the_environment`,
  `test_the_module_imports_with_neither_holdings_root_set`,
  `test_main_parses_the_argv_it_is_given_and_sys_argv_otherwise`,
  `test_the_module_is_runnable_as_python_m`.

### 5.3 Mutation probes: twenty-one, all caught

Run against `pytest tests/holdings_maintenance/test_crlf.py
tests/holdings_maintenance/test_shelf_consistency_check.py
tests/holdings_maintenance/test_show_opus_products.py --mode ns`, which sits at 67
passed. Each mutation was applied to a copy-restored file, never through `git`, and
**one file at a time**: a probe that changes the same construct in two files can be
caught by one file's test while the other's goes unguarded, and reads as covered.

| # | file | mutation | failures | caught by |
|---|---|---|---:|---|
| M1 | shelf | `errors += 1` → `error += 1` in the index branch | 1 | `test_an_extraneous_index_shelf_is_counted_like_any_other` |
| M2a | crlf | `__main__` guard neutralized | 2 | `test_the_module_is_runnable_as_python_m`, `test_an_unreadable_file_ends_the_process_with_a_traceback` |
| M2b | shelf | `__main__` guard neutralized | 1 | `test_the_module_is_runnable_as_python_m` |
| M2c | opus | `__main__` guard neutralized | 7 | 6 dogfooded tests **and** `test_the_module_is_runnable_as_python_m`, the holdings-free one |
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
| M10 | shelf | the index branch's `if verbose: print(...)` deleted | 1 | `test_an_index_shelf_whose_label_exists_is_counted_not_reported` |
| M11 | support | `sys.argv = list(argv)` deleted from the in-process runner | 6 | the four help ids and the two usage-error tests, which assert the `usage: <tool>.py` prefix argparse takes from `sys.argv[0]` |
| M12a | crlf | `main()` parses `sys.argv` instead of its `argv` argument | 1 | `TestArgvContract::test_an_explicit_argv_is_what_gets_parsed` |
| M12b | shelf | the same substitution | 1 | `test_an_explicit_argv_is_what_gets_parsed` |
| M12c | opus | `parse_args(argv[1:])` → `parse_args()` | 1 | `test_main_parses_the_argv_it_is_given_and_sys_argv_otherwise` |
| M13 | crlf | `argv = sys.argv` → a fixed list, when `argv is None` | 3 | `TestArgvContract::test_no_argument_means_sys_argv` and both `python -m` subprocess tests |
| M14 | support | `sys.argv = saved_argv` deleted, so the runner leaks its argv | 1 | `test_the_in_process_runner_leaves_sys_argv_as_it_found_it` |
| M15 | support | `no_holdings_env()` stops removing `PDS3_HOLDINGS_DIR` | 1 | `test_the_module_imports_with_neither_holdings_root_set` |

M4, M5 and M8 are the ones that matter: `parse_args`, `nargs='+'` and argparse's
default `allow_abbrev` are the three spellings a reader would reach for, and each
silently breaks a command line that works today. M7 matters for a different reason:
it is the "fix" that stops the crash without counting the error, and the regression
test rejects it too. M10 through M15 exist because each was a live gap — the index branch's verbose
line, the in-process runner's own `sys.argv` fidelity in both directions, the
`no_holdings_env()` scrub list, and, worst of the six, the `argv` parameter of all
three `main()`s. That last one is the half of the charter that says "testable": the
in-process runner sets `sys.argv` *and* passes `argv`, so every test that went
through it would pass whether or not `main()` read its argument at all.
`TestArgvContract` and its two siblings call `main()` directly, with `sys.argv`
holding a different command line, which is the only way to tell the two apart.

### 5.4 The rest

```
scripts/run-all-checks.sh -c -s          # with no holdings env vars
```
All checks passed, both trees. Its pytest leg: base **281 passed / 816 skipped**,
head **318 passed / 816 skipped**. The skip count does not move and the pass count
moves by exactly +37, which is §5.2's 38 added ids minus the 1 removed: every test this
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

## 7. Decisions the owner made, and the ones still open

The first two were put to the owner and **ruled on, 2026-08-07**. Both are recorded
where the next reader of the rule will be, not only here.

1. **RULED — `show_opus_products` keeps its subprocess tests.** The plan's PR-28
   entry required both `main()`-less tools to move in-process; only
   `shelf_consistency_check` did. `plans/2026-08-07-pr-28-deviation-addendum.md` is
   the §6.4 addendum and is **acknowledged by the owner** ("Yes use subprocces"), so
   the merge is clear on that count. §4 has the measurement. The reasoning that
   settled it: the harm is not that the tool would *fail* in-process, it is that it
   would succeed — `use_shelves_only(True)` and its two `preload()` calls are
   class-level, so the session would be left in shelves-only mode, which is the mode
   an `--mode ns` run exists not to be in, and every later test would inherit it.
   Silent, order-dependent, and green in isolation. The alternative — an autouse
   fixture snapshotting and restoring `LOCAL_PRELOADED`, `SHELVES_ONLY` and the
   caches — is new global-state machinery whose correctness is the hard part, for
   the runtime of six tests' worth of subprocesses.
2. **RULED — a malformed command line now exits 2 on all three tools** (§3, changes
   2, 5 and 6), accepted **on consistency grounds** ("accept consistency change").
   The three tools returned three different things for a bad flag, none of them
   designed: `crlf` exited 1 by treating the flag as a filename and dying in
   `FileNotFoundError`; `shelf_consistency_check` exited **0**, having walked the
   flag as a path that does not exist and reported a clean run; `show_opus_products`
   exited 1 on a `KeyError` for the holdings environment, at import, before argparse
   existed — and only with a root unset, since its parser is otherwise untouched.
   The eleven already-migrated console scripts all exit 2 on a bad flag today, so
   this brings the last three **into** line rather than away from anything.

   **The general rule the ruling establishes**, now in §6.4 and the Phase 6
   preamble as well as deferred entry 135: the exit-code freeze covers what a
   **valid** invocation returns, not what a malformed command line happens to
   produce. A status that falls out of an uncaught exception, or out of a tool
   treating an unrecognized argument as data, was never a designed part of the
   surface.

**Still open**, and the record's own judgements rather than anything ruled:
3. **`allow_abbrev=False` on the two new parsers, and not on `show_opus_products`.**
   The asymmetry is deliberate: the two new parsers get to choose, and `--rep`
   silently meaning `--repair` would let a misspelling rewrite files;
   `show_opus_products`' parser already existed with abbreviation on, so turning it
   off there would be a behaviour change this PR invented rather than inherited.
   If the owner wants one rule, it should be one rule applied in a PR that says so.
4. **Neither migrated tool can be given a path beginning with `-`** (§3, change 6,
   and deferred 141). These are the only base-working invocations the PR breaks. No
   file in either holdings root has such a name, and `crlf f -- -dash.txt` still
   reaches one, but it is a loss and not a wash. `crlf --repair --repair f` also
   now rewrites a file the base run left alone, having died on the second
   `--repair` as a path.
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
and `[project.scripts]` counts at base and head and the arithmetic on them, plus the
fact §8.4 actually asks for — that no console-script entry names any of the three
tools, which a count alone does not express; the finding count **at head**, by
running `ruff`, and if `ruff` is absent it says so rather than passing; every driver
figure in §8 and entry 130, including the block structure; §4's per-module test
breakdown, counted off the AST and cross-checked against the prose; and the presence
of every test function §5.2 names plus the absence of the one it says was removed,
with the function count reconciled against the id count through the three
parametrized cases.

**Two numbers are recorded constants, not derivations**: the base finding count
(2,250) and the base id counts, because neither can be read out of the head tree.
Both carry their command lines above, and both were re-measured at `3d044b2` for
this record. What the gate cannot re-derive at all is a number that comes from
running the suite or the transcript. Needles are matched with whitespace collapsed,
so a number that sits across a line break still matches.

**The gate has its own negative control**: ten perturbations, spread across all
four documents it reads and across every kind of number — a line count, the
shared-driver count, the driver block sizes, the plan's ratchet line,
`HOLDINGS_FREE_TOOLS`, one added test id, the added-id count, the
`[project.scripts]` base cell, §4's prose, and a test *renamed in the tree* rather
than in a document. Each was caught, and the tree was clean again afterwards. The
gate was written before the record was; the tenth perturbation is here because an
earlier version of the gate let it through, which is the shape of miss it exists to
prevent.
