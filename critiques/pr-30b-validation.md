# PR-30b validation — Google-style docstrings, the five maintenance tool-family pairs

Base: `4a59b74`. Branch: `pr-30b-docstrings-tools`. Base branch: `rewrite`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), from the tree being measured, with
`PYTHONPATH=$PWD/src`. Where holdings are needed the environment carried
`PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree is
a second worktree at the same commit, so "base" numbers were measured, not recalled.

Nothing here is inherited. Every number carries the command that produced it, and section
13 lists the numbers this PR was handed that did **not** reproduce.

**Every gate was run with its output to a file, its exit status read, and its totals line
grepped out of that file.** PR-30 shipped a checker reporting 24 findings for hours while
its record said it passed, because each re-run was read through `tail -2` and the totals
line fell above the cut. No result below was judged by a tail, and every pass line below
says what was measured rather than that nothing was found.

## 1. Scope

Eleven modules, and only these:

    python critiques/pr-29/measure.py \
        src/pdsfile/holdings_maintenance/pds3/pdsinfoshelf.py \
        src/pdsfile/holdings_maintenance/pds4/pds4infoshelf.py \
        src/pdsfile/holdings_maintenance/pds3/pdschecksums.py \
        src/pdsfile/holdings_maintenance/pds4/pds4checksums.py \
        src/pdsfile/holdings_maintenance/pds3/pdsarchives.py \
        src/pdsfile/holdings_maintenance/pds4/pds4archives.py \
        src/pdsfile/holdings_maintenance/pds3/pdslinkshelf.py \
        src/pdsfile/holdings_maintenance/pds4/pds4linkshelf.py \
        src/pdsfile/holdings_maintenance/pds3/pdsindexshelf.py \
        src/pdsfile/holdings_maintenance/pds4/pds4indexshelf.py \
        src/pdsfile/holdings_maintenance/pds3/linkshelf_repairs.py

| file | lines at base | classes | funcs | undocumented | params |
|---|---:|---:|---:|---:|---:|
| `pds3/pdsinfoshelf.py` | 651 | 0 | 12 | 9 | 43 |
| `pds4/pds4infoshelf.py` | 630 | 0 | 12 | 9 | 38 |
| `pds3/pdschecksums.py` | 621 | 0 | 11 | 7 | 42 |
| `pds4/pds4checksums.py` | 589 | 0 | 11 | 7 | 36 |
| `pds3/pdsarchives.py` | 255 | 0 | 10 | 6 | 26 |
| `pds4/pds4archives.py` | 275 | 0 | 10 | 6 | 21 |
| `pds3/pdslinkshelf.py` | 471 | 0 | 3 | 1 | 6 |
| `pds4/pds4linkshelf.py` | 524 | 0 | 3 | 1 | 6 |
| `pds3/pdsindexshelf.py` | 53 | 0 | 1 | 1 | 0 |
| `pds4/pds4indexshelf.py` | 57 | 0 | 1 | 1 | 0 |
| `pds3/linkshelf_repairs.py` | 555 | 0 | 0 | 0 | 0 |
| | **4,681** | **0** | **74** | **48** | **218** |

**None of the eleven had a module docstring**, none defines a class, and 26 of the 74
functions had a docstring, none of which carried a Google section of any kind.

Not in scope, and its own later PR: the four standalone tools under `pds3/` --
`re_validate.py`, `pdsdependency.py`, `crlf.py` and `shelf_consistency_check.py` -- which
declare no `ToolSpec`, reach no shared driver, and hold 31 functions and 73 parameters
between them. Section 12 records what that leaves of Phase 7.

## 2. What changed

Docstrings only. **Eleven module docstrings** (all new) and **74 function docstrings** (48
new, 26 rewritten) -- 85 in all. Section 3 proves that no executable statement moved.

71 comment lines were deleted and 10 were added; section 3.2 enumerates every one.

`critiques/pr-30b/` carries one script this record cites that no earlier PR had:
`check_flavor_vocabulary.py`, described in section 4, and the four round records. No script
of PR-28's, PR-29's, PR-29a's, PR-30's or PR-30a's is edited here; all are used unchanged.

## 3. Proof that the change is docstrings only

### 3.1 The AST hashes

`critiques/pr-29/strip_docstrings.py` parses a module, deletes the docstring node of every
module, class and function, and hashes `ast.dump` of what is left with
`include_attributes=False`, so line and column shifts do not register.

    python critiques/pr-29/strip_docstrings.py <the eleven files>

Run in both trees, the two eleven-line outputs are byte-identical: **all eleven pairs of
hashes match**, `diff` reporting nothing.

**The known blind spot does not apply to any of the eleven.** PR-30a found that
`strip_docstrings.strip()` replaces a body left empty by the removal with a single `pass`,
so a module whose entire content is a docstring hashes the same as any other such module
and the hash says nothing about it. That is a property of a file with no statements. Each
of these eleven has statements, counted mechanically as the top-level nodes that are not
the module docstring:

| file | top-level statements after the docstring |
|---|---:|
| `pdsinfoshelf.py` | 29 |
| `pds4infoshelf.py` | 29 |
| `pdschecksums.py` | 28 |
| `pds4checksums.py` | 28 |
| `pdsarchives.py` | 21 |
| `pds4archives.py` | 21 |
| `pdslinkshelf.py` | 25 |
| `pds4linkshelf.py` | 26 |
| `pdsindexshelf.py` | 14 |
| `pds4indexshelf.py` | 14 |
| `linkshelf_repairs.py` | 3 |

A second, independent measurement says the same thing from the other direction. Counting
every physical line that is outside a docstring, is not blank and is not a comment gives
the same number at base and at head for **all eleven files** -- 431/431 for
`pdsinfoshelf.py`, 163/163 for `pdsarchives.py`, 498/498 for `linkshelf_repairs.py`, and so
on down the list. A statement cannot have been added, removed or rewrapped.

PR-29 established that the hash check is not vacuous, with five mutations of a documented
file; the script is used here unchanged.

### 3.2 The comment enumeration, which the AST cannot see

    python critiques/pr-29/check_comments.py <base tree> <head tree> \
        holdings_maintenance/pds3/pdsinfoshelf.py ... \
        holdings_maintenance/pds3/linkshelf_repairs.py

Exit status 1, as it must be where any comment moved. **71 comment lines removed, 10
added**, and every one of them is in the banner block at the top of a file.

| file | comments at base | at head | removed | added |
|---|---:|---:|---:|---:|
| `pdsinfoshelf.py` | 66 | 61 | 6 | 1 |
| `pds4infoshelf.py` | 67 | 62 | 6 | 1 |
| `pdschecksums.py` | 56 | 51 | 6 | 1 |
| `pds4checksums.py` | 56 | 51 | 6 | 1 |
| `pdsarchives.py` | 27 | 22 | 6 | 1 |
| `pds4archives.py` | 31 | 26 | 6 | 1 |
| `pdslinkshelf.py` | 77 | 72 | 6 | 1 |
| `pds4linkshelf.py` | 101 | 96 | 6 | 1 |
| `pdsindexshelf.py` | 14 | 9 | 6 | 1 |
| `pds4indexshelf.py` | 18 | 13 | 6 | 1 |
| `linkshelf_repairs.py` | 37 | 26 | 11 | 0 |
| | | | **71** | **10** |

**60 of the 71 removals are the same six lines, ten times over**: each tool module's banner
carried a `# <name>.py library and main program` line, a `# Syntax:` block naming the
command line, a `# Enter the --help option to see more information.` line and the bare `#`
separators between them. `doc_python.mdc` section 4 requires a module's description to be
its docstring, so that block could not stay where it was; this is the decision PR-30a made
for the same reason and recorded in its own section 3.2. Each of the ten gains one comment
line in its place, `# pdsfile/holdings_maintenance/<flavor>/<name>.py`, which is the banner
form every module PR-25 onward carries. The `####` rules above and below are untouched, and
so is every other comment in every file, including the mid-file section banners and the two
`progname` notes in `pds4indexshelf.py` and `pds4linkshelf.py`.

**Three of those ten banners named the wrong file**, which is why the name line is replaced
rather than kept: `pds4archives.py` said `# pdsarchives.py`, `pds4checksums.py` said
`# pdschecksums.py`, and `pds4infoshelf.py` said `# pdsinfoshelf.py`. Keeping the line
would have kept a falsehood at the top of three files whose new module docstring says
otherwise two lines below.

**`linkshelf_repairs.py`'s eleven removals and no addition** are the other case: its banner
already carried the correct package path, and what was removed is the description paragraph
under it, which is now the module docstring. One claim in that paragraph was wrong and
section 9 records the correction.

## 4. The flavor-vocabulary checker -- the mechanical gate this PR needed

Ten of the eleven modules are five near-identical pairs. Writing ten docstring sets in one
sitting is the task where a sentence written for one half is pasted onto the other, and
the paste is invisible to every gate the earlier docstring PRs shipped, because the two
files are near-identical to begin with. PR-30's 36 rule modules had the same shape of
risk and it was worth a purpose-built gate there.

`critiques/pr-30b/check_flavor_vocabulary.py` reads **every** docstring in a module --
module, function and nested function -- and reports each term belonging to the other
flavor's vocabulary, in both directions.

| code | check |
|---|---|
| V0 | the module has no docstring, so nothing else about it can be evaluated |
| V1 | a docstring in a `pds4` module uses a PDS3 term |
| V2 | a docstring in a `pds3` module uses a PDS4 term |
| V3 | the module docstring does not name the module it documents |
| V4 | a docstring names a module of the other flavor that is not its own twin |

V1 and V2 are the two directions. V3 catches a wholesale copy whose vocabulary happens to
be neutral, and reads the whole module docstring rather than its summary line, because
these tools announce themselves by their `progname` and for all five `pds4` tools that is
the `pds3` tool's name. V4 catches a docstring that names some other tool of the other
flavor; naming its **own twin** is not a finding, because saying what a specification
declares is largely saying how it differs from the other half of the pair.

**The bare version numbers are deliberately not in either vocabulary, and that is the one
judgment in the script.** Every docstring here has to contrast its tool with its twin, so
"PDS3" or "PDS4" by itself is not evidence of anything, while a `pds4` docstring saying
"volume" is. The cost is stated in the script rather than hidden: a paste carrying only
the version number would pass V1 and V2. Nothing in this PR is in that position, because a
docstring long enough to be worth pasting names its unit several times.

### 4.1 What it found

    python critiques/pr-30b/check_flavor_vocabulary.py <the eleven files>

| | base | head |
|---|---:|---:|
| V0 module with no docstring | 11 | 0 |
| V1 pds4 docstring using a PDS3 term | 0 | 0 |
| V2 pds3 docstring using a PDS4 term | 0 | 0 |
| V3 module docstring not naming its module | 11 | 0 |
| V4 docstring naming a non-twin of the other flavor | 0 | 0 |
| | **22**, exit 1 | **0**, exit status 0, over 11 files |

The base column is what the 26 pre-existing docstrings look like: none of them says enough
to get a vocabulary wrong. **Three findings were raised against this PR's own prose while
it was being written and all three were acted on**, which is the whole reason the gate was
built before the prose rather than after it:

* `pdsindexshelf.py`'s module docstring said "differs between PDS3 and PDS4" and "the pds4
  tool adds a warning handler", and named `pds4indexshelf` -- V2 twice and V4 once. The V4
  finding was correct and the exception now covers a twin; the two V2 hits went away with
  the version numbers.
* `pdslinkshelf.py`'s module docstring said the specification names "the bundle-named
  method on the shared PdsFile base". It now names `log_path_for_bundle`, which is the
  method it actually means, and the sentence is both shorter and checkable.
* `pds4checksums.py`'s `main()` docstring names `pdsinfoshelf`, and
  `pds4linkshelf.py`'s module docstring names `linkshelf_repairs`. Both are true and
  load-bearing; each is now an entry in the exception table, scoped to that one module.

### 4.2 The accepted exceptions, with a reason each

The table is printed with every run, so it cannot grow silently, and each entry licenses
the exact string it names in the scope it names -- `log_path_for_bundle` is allowed and the
bare word "bundle" left behind by an edit to it is not.

| scope | term | reason | used in |
|---|---|---|---|
| `pds3` | `log_path_for_bundle` | `_shelf_common.UNIT_LOG_PATH_METHOD` is that string, and `pdslinkshelf`'s specification names it; `Pds3File.log_path_for_volume` forwards to the same method | `pdslinkshelf.py` module docstring |
| `pds3` | `log_path_for_bundleset` | `_shelf_common.UNITSET_LOG_PATH_METHOD` is that string, which `run_selection_main` picks for a pds3 target naming only a volume set | nowhere |
| `pds3` | `is_bundle_dir` | `PdsFile.is_bundle_dir` has no volume-spelled alias | nowhere |
| `pds3` | `is_bundleset_dir` | the same | nowhere |
| `pds3` | `is_bundle_file` | the same | nowhere |
| `pds3` | `bundlename` | what `run_selection_main` tests to pick a log path method | nowhere |
| `pds3` | `bundletype_` | what `resolve_holdings_paths` compares against `spec.unit` | nowhere |
| `pds4linkshelf` | `linkshelf_repairs` | the pds3 repair table has no counterpart here, because this tool's own `REPAIRS` is an empty translator, and this module is where a reader looking for the missing one arrives | `pds4linkshelf.py` module docstring |
| `pds4checksums` | `pdsinfoshelf` | `pds4checksums.main()` substitutes that literal into its own argv, so the docstring describing the substitution has to name it. The substitution never fires for this tool, and saying so is the point | `pds4checksums.py` `main` docstring |

**Five of the nine are used nowhere**, which is worth saying rather than tidying away: they
are the PdsFile members a PDS3 docstring would have to spell in the PDS4 vocabulary if it
named them, and this PR's prose happens not to name them. They are left in the table
because removing an entry that is not currently exercised is how a gate quietly tightens
into a trap for the next PR.

### 4.3 The mutations

Each mutation was applied to a copy of the head tree, the checker run over it, and the copy
discarded. The unmutated control is the first row.

| mutation | result | codes |
|---|---|---|
| unmutated control | 0 findings over 11 files, exit 0 | none |
| `pdsarchives`'s module docstring copied onto `pds4archives` | 3 findings, exit 1 | V1 ("volume", 8 times); V3; V4 ("pdslinkshelf") |
| `pds4checksums.generate_checksums`'s docstring copied onto `pdschecksums`'s | 1 finding, exit 1 | V2 ("bundle", 3 times) |
| one "bundle" changed to "volume" in a `pds4infoshelf` task docstring | 1 finding, exit 1 | V1 ("volume", once) |
| `log_path_for_bundle` cut back to `bundle` in `pdslinkshelf` | 1 finding, exit 1 | V2 ("bundle", once) |
| `pdsindexshelf`'s module docstring copied onto `pdsinfoshelf`, **same flavor** | 2 findings, exit 1 | V3; V4 ("pds4indexshelf") |
| `pds4linkshelf`'s module docstring copied onto `pds4infoshelf`, **same flavor** | 3 findings, exit 1 | V3; V4 ("pdslinkshelf", "linkshelf_repairs") |

The last two rows are the ones worth having: a copy between two modules of the **same**
flavor is exactly what V1 and V2 cannot see, and V3 and V4 catch both. The fourth row is
the smallest possible defect -- one word -- and the fifth shows that an exception licenses
its own exact string and not the flavor word inside it.

## 5. The Google-style docstring checks

    python critiques/pr-29/check_docstrings.py <the eleven files>

| code | check | base | head |
|---|---|---:|---:|
| P1 | a `Parameters:` entry that is not a parameter of the signature | 0 | 0 |
| P2 | a parameter that does not appear in `Parameters:` exactly once | 98 | 0 |
| P3 | a section spelled `Args:`, `Arguments:`, `Keyword arguments:` or `Input:` | 0 | 0 |
| R1 | `Returns:` present without a value return, or absent with one | 20 | 0 |
| E1 | a `Raises:` entry the body neither raises nor attributes to a call it makes | 0 | 0 |
| E2 | a class raised in the body that `Raises:` does not name | 0 | 0 |
| D1 | a docstring line wider than 90 columns | 0 | 0 |
| U1 | a unicode smart quote, dash or arrow anywhere in the file | 0 | 0 |
| M1 | a module, class or function with no docstring | 59 | 0 |
| | **total** | **177**, exit 1 | **0**, exit status 0, over 11 files |

M1's 59 is 11 modules plus 48 functions.

The checker is used **unchanged**. Run against the state each earlier PR's modules were in
before that PR documented them, it still reports the numbers those records carry. Each row
below was produced by extracting that commit's files into a throwaway directory with
`git show` and running the checker there.

| record | modules | commit | reported |
|---|---|---|---:|
| PR-29 | its five | `4edc7d1` | **276** over 5 files |
| PR-29a | its nine | `9466dbc` | **249** over 9 files |
| PR-29b | `_properties.py` | `998a166` | **73** over 1 file |
| PR-30 | the 36 rule modules | `c4811d8` | **78** over 36 files |
| PR-30 | the same 36 | `80f5e52` | **0** over 36 files, exit 0 |
| PR-30a | its ten | `80f5e52` | **235** over 10 files |
| PR-30a | the same ten | `4a59b74` | **0** over 10 files, exit 0 |

`critiques/pr-30/check_rule_tables.py` reports **0 findings over 36 files**, exit 0, at
`80f5e52`, and 36 at `c4811d8`. `critiques/pr-30a/check_spec_readers.py` reports **0
findings over 21 fields**, exit 0, at this PR's head, so PR-30a's gate is still passing over
a `_common.py` this PR does not touch.

## 6. Module length

    python critiques/pr-29a/measure_module_lines.py <the eleven files>

**All eleven pass both limits at both ends**, and `pdsdependency.py`, the one maintenance
module over a limit, is not in this PR.

| file | total base | total head | docstring head | code base | code head |
|---|---:|---:|---:|---:|---:|
| `pdsinfoshelf.py` | 651 | 1,091 | 458 | 636 | 633 |
| `pds4infoshelf.py` | 630 | 1,063 | 451 | 615 | 612 |
| `pdschecksums.py` | 621 | 1,006 | 412 | 597 | 594 |
| `pds4checksums.py` | 589 | 962 | 400 | 565 | 562 |
| `pdsarchives.py` | 255 | 519 | 270 | 249 | 249 |
| `pds4archives.py` | 275 | 552 | 283 | 270 | 269 |
| `pdslinkshelf.py` | 471 | 602 | 152 | 453 | 450 |
| `pds4linkshelf.py` | 524 | 679 | 176 | 506 | 503 |
| `pdsindexshelf.py` | 53 | 105 | 55 | 53 | 50 |
| `pds4indexshelf.py` | 57 | 115 | 61 | 57 | 54 |
| `linkshelf_repairs.py` | 555 | 614 | 69 | 555 | 545 |

The largest is `pdsinfoshelf.py` at 1,091 total against a limit of 2,000 and 633 code
lines against a limit of 1,000, so the tightest margin in the PR is 367 lines.

**Ten of the eleven lose code lines and one holds level**, which needs saying because a
docstring-only change should not move a measure defined as "total minus docstring lines".
Two causes run opposite ways and both are accounted for above. A banner description line is
a comment and counts as code, so moving one into a docstring takes a code line away: that
is 5 per tool module and 11 for `linkshelf_repairs.py`. A docstring inserted above a body
that had no blank line before it adds one blank, and the blank is not part of the
docstring's own span: `pdsarchives.py` gains 5 blanks against its 5 lost comments and comes
out level, and every other file gains between 1 and 3. The statement counts of section 3.1
are unchanged in every file, which is what says the movement is entirely comments and
blanks.

## 7. The Sphinx build

`docs/` does not exist and is not created here; PR-31 owns it. A throwaway tree is built
elsewhere instead, reproducibly, with `critiques/pr-29a/build_docs_probe.py` and
`critiques/pr-29/sphinx-conf.py` **both unchanged**. What is extended is the page list: the
eleven modules join the twenty-three the probe already carries, and the same page list is
used at both ends, so the base build renders these eleven modules' undocumented members
exactly as the head build renders their documented ones.

    python critiques/pr-29a/build_docs_probe.py $PWD/src <build dir> \
        holdings_maintenance ... holdings_maintenance.pds3.linkshelf_repairs

| | base | head |
|---|---:|---:|
| `-n` problems | 27 | **27** |
| `-W` problems | 28 | **28** |
| probe exit status | 1 | **1** |

**The exit status is 1 at both ends and this record says so rather than rounding it to a
pass.** It was read from the probe's own return value; the probe appends a line of its own
when `sphinx-build` exits nonzero, and that line is the 28th `-W` problem.

The corrections rounds 3 and 4 produced were measured through the probe again and moved
neither number.

**All 27 remaining problems at each end are one warning repeated**, filtered mechanically
by dropping every line matching "duplicate object description" and finding nothing left:

    <unknown>:1: WARNING: duplicate object description of
    pdsfile.holdings_maintenance._common.ToolSpec.progname, other instance in api,
    use :no-index: for one of them

one for each of `ToolSpec`'s 21 fields, `VersionedFile`'s three and `RunResult`'s three.
PR-30a isolated the cause with a two-class control and measured two fixes that each take it
to zero; neither is applied here, because `conf.py` belongs to PR-31 and four earlier
records depend on the probe's behavior. **Deferred observation 276 already carries it, and
this PR adds nothing to it.**

### 7.1 What the Sphinx gate caught in this PR's own prose

One defect, in prose written for this PR, fixed in commit `5acbf85`:

    src/pdsfile/holdings_maintenance/pds3/pdslinkshelf.py:docstring of
    pdsfile.holdings_maintenance.pds3.pdslinkshelf:12:
    WARNING: Inline literal start-string without end-string. [docutils]

The literal was ``keyword = `` -- an inline literal whose last character before the closing
markup is a space, which reStructuredText does not close. It is now ``KEYWORD =``. This is
the same shape of defect PR-30 section 7.1 and PR-30a section 7.2 each recorded once, and
it recurred anyway; it is the third PR in a row where the only Sphinx finding in new prose
was an inline-markup token rather than anything about the content.

### 7.2 The head build is not vacuous

`api.html` from the `-n` build holds two matches for "Return the MD5 digest of every file",
one for "shelve the row numbers" and one for "known-bad links in the published PDS3
volumes", against **zero** for each on the base page.

## 8. Standing gates

### 8.1 Test id sets, full data, both modes

The command lines are `scripts/automated_tests/pdsfile_main_test.sh`'s, plus `--junitxml`.
Run from each tree in turn, one at a time: two runs in parallel put the tool subprocesses
that `tests/holdings_maintenance/` drives into uninterruptible I/O wait for minutes at a
time, so the parallel attempt was killed and both modes were re-run serially.

| mode | scope | base | head | ids only in base | ids only in head | outcome changed |
|---|---|---|---|---|---|---|
| `ns` | all seven directories | 1101 passed, 34 skipped (1135 ids) | 1101 passed, 34 skipped (1135 ids) | none | none | none |
| `s` | `tests/pds3file/ tests/rules/pds3/` only | 555 passed, 3 skipped (558 ids) | 555 passed, 3 skipped (558 ids) | none | none | none |

The per-test id sets are diffed, not the counts: the junit files are parsed and compared id
by id with the outcome attached, so a test that changed from passed to skipped would show
even though the totals would not. The `--mode s` scope is the script's own
(`scripts/automated_tests/pdsfile_main_test.sh:75`), not the full suite.

### 8.2 The code checks with no holdings

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        VENV=/seti/all_repos/rms-pdsfile/venv bash scripts/run-all-checks.sh -c -s

All checks passed, exit status 0: ruff, the indentation pass, pytest (**318 passed, 817
skipped**), pyroma, the API-freeze check and the clean-install gate.

### 8.3 The API freeze

    /seti/newnav/capped-run.sh pytest tests/api

**26 passed**, exit status 0. The four frozen files are byte-identical to `4a59b74`,
checked with `git diff --quiet 4a59b74 -- <file>` on each of `tests/api/api_manifest.json`,
`tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py` and
`tests/api/test_api_freeze.py`. None of the eleven modules gains, loses or renames a name,
so there was no freeze risk to check beyond that.

### 8.4 ruff

    ruff check src/pdsfile tests scripts                  # All checks passed, exit 0
    ruff check .                                          # All checks passed, exit 0
    ruff check --preview --select E111,E112,E113 .        # All checks passed, exit 0
    ruff check . --config 'lint.per-file-ignores = {}'    # Found 2249 errors, exit 1

`ruff format` was not run, in any form.

### 8.5 The ratchet

| | base | head |
|---|---:|---:|
| `per-file-ignores` entries | 66 | 66 |
| code slots across those entries | 180 | 180 |
| findings with `per-file-ignores = {}` | 2,249 | 2,249 |
| `[project.scripts]` entries | 11 | 11 |

Nothing moved. Seven of the eleven files carry an entry, and between them those entries
name `B006`, `B012`, `RUF005`, `RUF015`, `SIM115` and `UP031` -- none of which a docstring
can retire, and each of which is described in the docstring of the function that carries
it rather than silently left to the ratchet. Every docstring line is wrapped at 90 columns,
which is what keeps the third row from moving.

`bandit` and `vulture` are disabled and not installed. This PR claims nothing about them.

### 8.6 The record checkers

    python critiques/pr-28/check_record_numbers.py
    python critiques/pr-29/check_citations.py

**15 stale at base and 15 at head, byte-identical outputs, with no repair needed**, and
**6 stale at base and 6 at head, byte-identical outputs, with no repair needed.** Both were
run again after this record, the two round records and the fifteen deferred observations
were written, and both were still byte-identical to base.

The 15 are PR-28's own, invalidated by PR-28a's extraction; the 6 are deferred-observation
citations into files outside the citation checker's scope list. Both numbers arrived that
way and this PR neither caused nor repaired them. PR-30a's section 12 records that the 6
were handed forward as zero.

**No line-count table in this record cites a number the checker reads**, which is why
nothing needed the repair PR-29a, PR-30a and PR-30 each had to make: the tables here are
this PR's own base and head measurements rather than a re-derivation of another PR's.

## 9. What the docstrings had to correct about the code they describe

Two claims in the prose this PR replaced were wrong, and the replacements do not carry them
forward. Both are in `linkshelf_repairs.py`'s banner description, the one block of prose
these eleven files carried that said anything about behavior.

* **"The keys are volume paths."** They are matched against the absolute path of the
  **file being scanned**, not of the volume: `pdslinkshelf.generate_links()` calls
  `REPAIRS.all(abspath)` once per file it reads for links, and nearly every pattern in the
  table ends in a basename. The distinction matters to a maintainer adding an entry, since
  a pattern written for a volume matches nothing.
* **"a substring that looks like a link is looked up here first."** True, and it says less
  than it should: the lookup happens before the link is resolved at all, so a repair
  overrides a name that would have matched a file in the same directory. Round 2
  demonstrated it on a synthetic volume. The module docstring now says so, and so does
  `pdslinkshelf.generate_links()`.

The other nine banners carried a name, a syntax line and a pointer to `--help`; three of
the ten named the wrong file and section 3.2 records those.

## 10. Contracts that had to be read out of the code

Each of these was settled by running something or by reading both ends, and each is
recorded because none is derivable from a name. They are the sentences the brief predicted
would be the defect concentration, and several of them are where the reviewers found one.

* **`_shelves.shelf_lookup()` reads the info shelf's `.py` sidecar**, taking its second
  line to answer a question about the unit rather than unpickling the shelf. Two properties
  of `write_infodict()` are load-bearing for that and neither is obvious from it: the
  entries are sorted by absolute path, and where the dictionary covers a whole unit the
  unit directory's own path is a prefix of every other, so its entry -- the one keyed by
  the empty string -- is written first and is the file's second line. Confirmed against a
  production sidecar. **The ordering is the caller's to supply and not this function's to
  enforce**, and one caller does not: `reinitialize()` on a selection hands it a
  single-entry dictionary, and the pair it writes has no empty key at all.
* **`file_log_level` is set by all four checksum and info shelf specifications and read by
  none of them.** Its four readers are all in the archive and link shelf machinery, and the
  per-file lines in those four modules name `info()` and `normal()` directly. The field is
  what a reader would take for the cause of the difference between the two flavors' log
  levels, and it is not.
* **`holdings_sentinel` has two readers serving three families**, not two: path resolution
  for the checksum and info shelf tools, and the stopping condition of the link shelf
  tools' upward search.
* **An `update` never removes anything, in the checksum and info shelf families.** The
  result is rebuilt from the whole of what the shelf held, so an entry for a deleted file
  survives and the run then reports the shelf complete. The link shelf tools do drop such
  an entry, because their scan assembles its result from the paths the walk found. Three
  families, two behaviors, one task name.
* **The info shelf merge writes a key only where the old dictionary lacks it**, so a
  directory the walk recomputed is discarded if it was already shelved. That is what makes
  `update` and `validate` disagree about the same shelf.
* **`pdsinfoshelf.initialize()` resolves its logger inside one branch only**, so refusing a
  selection calls `error()` on None. Demonstrated against a stub; `pds4infoshelf` resolves
  first and reports.
* **`pds4checksums`'s `--infoshelf` chain re-runs `pds4checksums`.** The substitution
  replaces the literal "pdschecksums", which no PDS4 command line carries.
* **Neither checksum tool's exit status reports what a task found**, and both do exit
  nonzero for what is settled before a task starts: 1 for a missing task, 2 for an
  unclassifiable command line, 1 for a rejected path. Measured by driving `main()` four
  ways.
* **`pds4archives`'s member naming and its path reconstruction agree only for one of the
  three archive shapes installed in this repository.** Round 2 wrote an archive and
  validated it immediately on all three; two of them report every file as missing from one
  side or the other.
* **The repair table is reached once per file, not once per link.** With an empty table --
  which is `pds4linkshelf`'s -- the per-link loop never runs, so no link is looked up at
  all, and `LinkInfo.remove_path()`, which lives inside that loop, is unreachable.
* **A label is credited only where it mentions the file**, in both flavors, and neither
  flavor's first crediting path asks how the mention was matched: a file named in a prose
  note or an XML comment credits the label as surely as one named in a target position.
  Only the last path, the candidate list, requires a target position. A name match with no
  mention produces a "does not point to file" error and a missing-label report, and only
  where a label is required.
* **`pds4linkshelf` credits by name first and by any mention second.** The later pass
  compares the file's basename against every link the label yielded, general-pattern
  matches included, and skips any file the earlier pass credited; the log line calls it a
  file_name tag and the comparison never reads one.
* **`get_info()`'s `checkdict` parameter is never read for its value**: it is passed to
  the recursive call and nowhere else, and the digest lookup is in `get_info_for_file()`,
  a **sibling** nested function whose closure reaches `generate_infodict()`'s local of the
  same name. Handing the recursive call a decoy dictionary leaves every digest
  unchanged.
* **`generate_checksums()`'s modification time is the newest among every file the walk
  sees**, taken before any skip test, so a `.DS_Store` touched today dates the unit. The
  same is true of both link shelf scans. It is what makes the "out of date" comparison in
  three repair tasks mean "has anything under here changed" rather than "has anything
  covered here changed".

## 11. Review

Four rounds, each run by a fresh reviewer subagent with no context from this session or
from any other round. Records: `critiques/pr-30b/round-1.md` through `-4`.

| round | slice | surface | disproved | of those, in the corrections | misleading | code defects |
|---|---|---|---:|---:|---:|---:|
| 1 | the checksum and info shelf pairs | 4 files, 46 functions, 159 parameters | 10 | -- | 9 | 7 |
| 2 | the archive, link shelf and index shelf pairs, and the repair table | 7 files, 28 functions, 59 parameters | 11 | -- | 7 | 7 |
| 3 | the same four, re-read | the same | 7 | **5** | 3 | 4 |
| 4 | the same seven, re-read | the same | 6 | **5** | 5 | 5 |
| | | | **34** | **10 of 13** | **24** | |

Every finding was re-verified by the executor before it was acted on, and the four with
the widest consequences in each round were re-derived from scratch rather than read. Both
second-read briefs carried the correction commit range, an enumeration of the claims those
commits make -- thirteen for round 3 and seventeen for round 4 -- and the instruction to
treat every one as unproven and to attribute each finding with `git blame`.

### The second reads found most of their yield in the first reads' corrections

**Ten of the second reads' thirteen disproved claims are in sentences the first reads'
corrections wrote**, five of round 3's seven and five of round 4's six; and of the eight
sentences they classed as misleading, seven are, including all five of round 4's. PR-29a
measured 11 of 23 on this question, PR-29b 10 of 21, PR-30 34 of 57 and PR-30a 15 of 22.
**As a share this is the highest yet -- 10 of 13, where the previous high was 15 of 22 --
and the trend the four previous records describe is unbroken.**

The sharpest of them is not the largest. Round 1 disproved
`pdschecksums`'s "that is the only way a run of this tool reaches a nonzero exit status",
and the correction pass applied that finding to the module docstring of the same file and
to the PDS4 twin's `main()` and **missed the PDS3 `main()` it came from**, leaving one
docstring contradicting another 900 lines above it in the same file. Round 3 found it. A
correction pass is not only more error-prone than a first draft; it is prone to a kind of
error a first draft cannot make, which is applying a finding to three of the four places it
belongs.

Four more of the same shape are worth naming because each reads as freshly checked:

* **the shelf-scan citation.** Round 1's finding that no shelf carries a dashed digest was
  right, and the correction wrote up the numbers of the slice actually run -- "80 shelves
  and 391,444 entries in the test holdings" -- as though they were the tree. Round 3
  measured the tree: 6,723 shelves and 21,711,938 entries. It also noticed that the same
  sentence stood in the PDS4 module citing a measurement the PDS4 tree cannot produce,
  since it holds no info shelves at all.
* **"is always written first."** The correction built a load-bearing property out of two
  mechanical facts and asserted it of every call. `reinitialize()` on a selection hands
  `write_infodict()` one entry, and round 3 ran it: no empty key at all, and
  `shelf_lookup()` returning the named file's entry as the volume's.
* **the label-crediting grounds, in both flavors.** Round 2 disproved "a name match alone
  credits a label" and the correction replaced it with "the label named it in a target
  position", which is the *other* branch's condition. Round 4 demonstrated it with a label
  whose only mention of the file is inside a prose note, and with a PDS4 label whose only
  mention is inside a `<comment>`: both credit, and neither is a target-position match.
* **the `re.I` reason.** Round 2 disproved "the two entries that match a lower-case
  basename" by finding that one is upper-case. The correction invented a reason -- that
  they must match either case -- and round 4 measured it against 5,912 published files:
  each pattern matches exactly the same files with the flag and without it.

### What the angles returned

* **Relationship claims** were the largest category in all four rounds, as in all five
  earlier docstring PRs. The one that mattered most is the one that told a maintainer a
  file nothing reads is read on the preload path, and that two properties of the write that
  the shortcut depends on do not matter.
* **Cross-version claims** produced the defect the vocabulary checker cannot see, twice in
  each direction: a sentence true of `pds4infoshelf.initialize` asserted of `pdsinfoshelf`,
  a repair ordering stated correctly in the PDS4 scan and backwards in the PDS3 one, an
  "update drops a deleted entry" that is true of the link shelf family and false of the
  other two, and a "shortest of the ten" true in one twin and false in the other. **The
  gate caught none of these and was never going to: it checks the vocabulary and never the
  meaning**, which is what section 4 says of it and what these four findings are the
  evidence for.
* **Exceptions from something other than `raise`** produced two whole contracts that were
  missing -- the `IndexError` a blank line in a manifest gives, and the `AttributeError`
  `pdsinfoshelf --initialize` on a file ends in -- and one that was wrong, the `EOFError`
  attributed to a truncated pickle that gives `UnpicklingError` seven times out of eight.
* **Arithmetic and counts** behaved as they did in PR-30a: the boundary claims held --
  the tenth-of-a-day threshold, the strict comparison at equal times, the 32-and-35
  character manifest offsets, the modification-time tolerance -- and the counts did not.
  Three, four, five and "the fifth of four" were each wrong somewhere.

### The counted claims about the repair table held twice

`linkshelf_repairs.py`'s module docstring makes eight counted claims, and rounds 2 and 4
each measured all eight independently by importing the table. All eight held both times:
141 entries, 2 carrying `re.I`, 77 dictionary translators and 64 nested regular-expression
ones, 267 dictionary entries of which 24 map to the empty string, 90 nested regex entries,
and a comprehension over `range(0, 50)`. **Every prose claim in that docstring that a round
disproved was about what the table means rather than about what is in it** -- which
translator loop runs, when a truncation is reachable, why two entries carry a flag, what
order the groups are in. The numbers were never the risk.

### The freeze rule was followed

Deferred entry 239 asks that the previous round's corrections be committed and the tree
left alone before the round that reviews them is launched, after PR-29b and PR-30a each
broke it. Rounds 1 and 2 were launched against a frozen `5acbf85` and rounds 3 and 4
against a frozen `748eae4`; `git diff --stat <sha> -- src/` was empty at every check while
a round was running. Records, deferred observations and the plan amendment were written
during rounds 3 and 4, and none of them is under `src/` or reachable from the diff the two
reviewers were given.

## 12. What remains of Phase 7's docstring work

Measured at `4a59b74` over all 17 files under `holdings_maintenance/pds3/` and `pds4/` --
15 tool modules and the two zero-byte `__init__.py` beside them: **271 findings over 17
files**, 105 functions, 54 of them undocumented, 291 parameters.
**177 of the 271 are this PR's eleven files**, and they are now zero.

What is left is the four standalone tools -- `re_validate.py`, `pdsdependency.py`,
`crlf.py` and `shelf_consistency_check.py` -- which hold **31 functions, one class, 73
parameters and 92 of the findings**, and the two zero-byte `__init__.py` files, which hold
one finding each. Unlike this PR's eleven, they are not undocumented prose deserts: 25
docstrings already exist and 13 of those carry a Google section, nine of them spelled
`Args:`, which `check_docstrings.py` counts as ten `P3` findings. The plan gains a **PR-30c** for them, and
this PR's entry in it is rewritten to say what it actually took.

None of the four declares a `ToolSpec` or reaches a shared driver; each parses its own
command line. So nothing PR-30a or PR-30b documented carries over, and the vocabulary
checker has nothing to compare, since none of the four has a pair. `pdsdependency.py` is
1,165 lines and is the one maintenance module over a length limit, which makes PR-30c the
place where that is either recorded again or acted on.

With PR-30c done, `check_docstrings.py` reports zero over every module under
`src/pdsfile/` except `_version.py`, which setuptools_scm generates and `.gitignore`
excludes.

## 13. Numbers this PR was handed that did not reproduce

Recorded because every number was re-derived rather than inherited.

* **`ToolSpec.index_ext` is read at `_indexshelf_common.py:667`, not `:464`.** The brief
  gave the line number along with the instruction to verify it; the fact is right and the
  citation is 203 lines out.

* **The plan's PR-30b entry says the 17 modules hold "105 functions, 72 of them
  undocumented".** 105 is right and 72 is not: **54** functions have no docstring, and 17
  modules have none, which is 71 `M1` findings and not 72 by any reading. The other three
  numbers in that entry -- 291 parameters, 271 findings over 17 files -- reproduce exactly.
  Section 12 records the correction and the plan now carries it.

* **The brief's scope table omitted nothing and every one of its numbers reproduced**,
  which is worth saying because the last two briefs each carried an error the executor had
  to find: 651/630/621/589/255/275/471/524/53/57/555 lines, 74 functions, 48 undocumented,
  218 parameters, no module docstring anywhere, and no classes. The 4,681-line total and
  the 26 pre-existing docstrings are this PR's own additions to it.

* **`critiques/pr-29/check_citations.py` reports 6 stale at `4a59b74`, and PR-30a's record
  says so.** The brief did not carry the number; it is repeated here because PR-30's record
  says zero, and a later PR comparing against that would read six as a regression.

Everything else reproduced exactly:

* the `ns` **1135** and `s` **558** baselines, id for id, at base and at head;
* all four ratchet numbers, **66 / 180 / 2,249 / 11**;
* the five checker reproductions -- PR-29's **276**, PR-29a's **249**, PR-29b's **73**,
  PR-30's **78** at `c4811d8` and **0** at `80f5e52`, and PR-30a's **235** at `80f5e52` and
  **0** at `4a59b74`;
* PR-30's `check_rule_tables.py` at **0 findings over 36 files**, exit 0, and PR-30a's
  `check_spec_readers.py` at **0 findings over 21 fields**, exit 0, at this PR's head;
* `critiques/pr-28/check_record_numbers.py` at **15 stale**;
* PR-30a's Sphinx measurement of **27** `-n` problems from one dataclass-attribute cause,
  and its exit status of 1;
* `critiques/deferred-observations.md` continuing from **295**: the last entry at
  `4a59b74` is 294.
