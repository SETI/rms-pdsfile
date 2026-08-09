# PR-30c validation — Google-style docstrings, the four standalone maintenance tools

Base: `0f5d9ae`. Branch: `pr-30c-docstrings-standalone`. Base branch: `rewrite`.

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

**Six files, not the four the brief named.** The four standalone tools, and the two
zero-byte package initializers beside them:

    python critiques/pr-29/measure.py \
        src/pdsfile/holdings_maintenance/pds3/pdsdependency.py \
        src/pdsfile/holdings_maintenance/pds3/re_validate.py \
        src/pdsfile/holdings_maintenance/pds3/crlf.py \
        src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py \
        src/pdsfile/holdings_maintenance/pds3/__init__.py \
        src/pdsfile/holdings_maintenance/pds4/__init__.py

| file | lines at base | classes | funcs | undocumented | params |
|---|---:|---:|---:|---:|---:|
| `pds3/pdsdependency.py` | 1,165 | 1 | 8 | 5 | 29 |
| `pds3/re_validate.py` | 987 | 0 | 18 | 1 | 39 |
| `pds3/crlf.py` | 169 | 0 | 3 | 0 | 4 |
| `pds3/shelf_consistency_check.py` | 132 | 0 | 2 | 0 | 1 |
| `pds3/__init__.py` | 0 | 0 | 0 | 0 | 0 |
| `pds4/__init__.py` | 0 | 0 | 0 | 0 | 0 |
| | **2,453** | **1** | **31** | **6** | **73** |

**None of the six had a module docstring**, and the one class, `PdsDependency`, had none
either. Unlike PR-30b's eleven these are not prose deserts: 25 docstrings existed, 13 of
them carrying a Google section, nine spelled `Args:` and one `Inputs:`.

Section 13 records why the two `__init__.py` files are here: without them the plan's own
completion claim for PR-30c is false, because `check_docstrings.py` over
`src/pdsfile/` at `0f5d9ae` reports **94 findings over 78 files** and only **92** of them
are the four tools.

## 2. What changed

Docstrings only. **Six module docstrings** (all new), **one class docstring** (new) and
**31 function docstrings** (6 new, 25 rewritten) -- 38 in all. Section 3 proves that no
executable statement moved.

31 comment lines were deleted and 4 were added; section 3.2 enumerates every one.

`critiques/pr-30c/` carries the four round records and no script. No script of PR-28's,
PR-29's, PR-29a's, PR-30's, PR-30a's or PR-30b's is edited here; all are used unchanged.
The one record this PR edits that is not its own is `critiques/pr-28-validation.md`, whose
line-count table the record checker re-derives against the tree it runs in; section 8.6
records the repair.

## 3. Proof that the change is docstrings only

### 3.1 The AST hashes, and the two files where the hash cannot answer

`critiques/pr-29/strip_docstrings.py` parses a module, deletes the docstring node of every
module, class and function, and hashes `ast.dump` of what is left with
`include_attributes=False`, so line and column shifts do not register.

    python critiques/pr-29/strip_docstrings.py <the six files>

| file | base | head |
|---|---|---|
| `pds3/pdsdependency.py` | `b43d35a8c1377bda` | `b43d35a8c1377bda` |
| `pds3/re_validate.py` | `f072dd0a9da354b4` | `f072dd0a9da354b4` |
| `pds3/crlf.py` | `8b36600b0f91e39a` | `8b36600b0f91e39a` |
| `pds3/shelf_consistency_check.py` | `88583c9454e9779a` | `88583c9454e9779a` |
| `pds3/__init__.py` | `3543b4693a36a109` | **`5c04595997820c90`** |
| `pds4/__init__.py` | `3543b4693a36a109` | **`5c04595997820c90`** |

**The four tool modules match. The two package initializers do not, and the reason is a
property of the script rather than of the change** -- the same one PR-30a hit and
recorded. `strip_docstrings.strip()` replaces a body left empty by the removal with a
single `pass`, so a zero-byte module strips to `Module(body=[])` and a module whose whole
content is a docstring strips to `Module(body=[Pass()])`. The two hash differently, and
they differ for any docstring whatever: both files hash to the same `5c04595997820c90`
although their docstrings share not one sentence. **The hash for those two files measures
nothing about this change and is not treated as evidence.** The script was not amended: it
is inherited, five earlier records depend on its numbers, and amending a gate so that it
passes is a hard stop.

What is offered instead is the stronger check PR-30a used, available precisely because the
files were empty:

    pds3/__init__.py: base 0 bytes, base AST body 0 nodes;
                      head AST body 1 node, sole node is the module docstring: True
    pds4/__init__.py: base 0 bytes, base AST body 0 nodes;
                      head AST body 1 node, sole node is the module docstring: True

A module whose entire abstract syntax tree is one string constant cannot carry an
executable statement.

A second, independent measurement says the same thing about the four tool modules from the
other direction. Counting every physical line that is outside a docstring, is not blank and
is not a comment gives the same number at base and at head for **all four**, and so does
counting the top-level statements after the module docstring:

| file | non-comment non-docstring lines, base / head | top-level statements, base / head |
|---|---|---|
| `pdsdependency.py` | 902 / **902** | 61 / **61** |
| `re_validate.py` | 587 / **587** | 45 / **45** |
| `crlf.py` | 82 / **82** | 13 / **13** |
| `shelf_consistency_check.py` | 67 / **67** | 6 / **6** |

A statement cannot have been added, removed or rewrapped.

PR-29 established that the hash check is not vacuous, with five mutations of a documented
file; the script is used here unchanged.

### 3.2 The comment enumeration, which the AST cannot see

    python critiques/pr-29/check_comments.py <base tree> <head tree> \
        holdings_maintenance/pds3/pdsdependency.py ... holdings_maintenance/pds4/__init__.py

Exit status 1, as it must be where any comment moved. **31 comment lines removed, 4
added**, and every one of them is in the banner block at the top of a file.

| file | comments at base | at head | removed | added |
|---|---:|---:|---:|---:|
| `pdsdependency.py` | 76 | 71 | 6 | 1 |
| `re_validate.py` | 91 | 86 | 6 | 1 |
| `crlf.py` | 27 | 16 | 12 | 1 |
| `shelf_consistency_check.py` | 23 | 17 | 7 | 1 |
| `pds3/__init__.py` | 0 | 0 | 0 | 0 |
| `pds4/__init__.py` | 0 | 0 | 0 | 0 |
| | | | **31** | **4** |

Every removal is a description or syntax line, or a bare `#` separator between them, from
the banner block that `doc_python.mdc` section 4 requires be the module's docstring. Each
of the four gains one comment line in its place, `# pdsfile/holdings_maintenance/pds3/<name>.py`,
which is the banner form every module PR-25 onward carries. The `####` rules above and
below are untouched, and so is every other comment in every file, including
`shelf_consistency_check.py`'s closing rule and the mid-function notes PR-28 wrote in
`crlf.py` and `shelf_consistency_check.py`.

**One removed line was wrong, and section 9 records the correction.**
`shelf_consistency_check.py`'s banner said the tool confirms "that every info shelf file
has a corresponding directory in holdings/". It examines link and index shelves as well,
and for an index shelf what has to exist is a label file rather than a directory.

## 4. The flavor-vocabulary checker, run because the brief asked and reported rather than passed

    python critiques/pr-30b/check_flavor_vocabulary.py <the six files>

| | base | head, before review | head |
|---|---:|---:|---:|
| V0 module with no docstring | 6 | 0 | 0 |
| V1 pds4 docstring using a PDS3 term | 0 | **1** | 0 |
| V2 pds3 docstring using a PDS4 term | 0 | 0 | 0 |
| V3 module docstring not naming its module | 6 | **2** | **2** |
| V4 docstring naming a non-twin of the other flavor | 0 | 0 | 0 |
| | **12**, exit 1 | **3**, exit 1 | **2**, exit 1 |

**Over the four tool modules alone the head result is 0 findings over 4 files, exit status
0.** Both remaining findings are the two `__init__.py` files, and both are the checker
applied outside the premise its own docstring states. It exists to catch a sentence pasted
between the two halves of a near-identical **pair**; nothing in this PR has a pair, and a
package initializer is the one kind of file in the subpackage whose job is to describe
both halves. V3 asks that a module docstring name the module it documents, and a package
initializer's module name is `__init__`, which no useful docstring writes. The finding is
a property of the name, not of the prose.

**The V1 finding was real and is gone, and not because it was argued away.**
`pds4/__init__.py` said "What differs is the unit a target names -- a bundle rather than a
volume". Round 2 disproved that sentence for a different reason -- the index shelf pair's
unit is a table on both sides -- and the replacement does not name either unit, so the
vocabulary finding went with it. The gate and the reviewer reached the same sentence from
opposite directions, which is the one thing a vocabulary checker cannot be relied on to
do.

**The script was not amended and no exception was added to its table.** Its `ALLOWED`
table is scoped by flavor or by module stem, and both files have the stem `__init__`, so
an entry meant for the PDS4 initializer would silently license the PDS3 one as well. And
PR-30b's record depends on the table's contents: it prints the whole table with every run
precisely so that it cannot grow silently, and growing it to make a different PR's
unrelated file pass is what that design exists to prevent.

The base column is what six undocumented files look like: 6 V0 and 6 V3, and no vocabulary
finding at all, because none of the 25 pre-existing docstrings says enough to get a
vocabulary wrong.

## 5. The Google-style docstring checks

    python critiques/pr-29/check_docstrings.py <the six files>

| code | check | base | head |
|---|---|---:|---:|
| P1 | a `Parameters:` entry that is not a parameter of the signature | 0 | 0 |
| P2 | a parameter that does not appear in `Parameters:` exactly once | 54 | 0 |
| P3 | a section spelled `Args:`, `Arguments:`, `Keyword arguments:` or `Inputs:` | 10 | 0 |
| R1 | `Returns:` present without a value return, or absent with one | 11 | 0 |
| E1 | a `Raises:` entry the body neither raises nor attributes to a call it makes | 4 | 0 |
| E2 | a class raised in the body that `Raises:` does not name | 2 | 0 |
| D1 | a docstring line wider than 90 columns | 0 | 0 |
| U1 | a unicode smart quote, dash or arrow anywhere in the file | 0 | 0 |
| M1 | a module, class or function with no docstring | 13 | 0 |
| | **total** | **94**, exit 1 | **0**, exit status 0, over 6 files |

M1's 13 is 6 modules plus 1 class plus 6 functions. P3's 10 is nine `Args:` and one
`Inputs:`.

**E1's four are worth naming, because they are the check working on prose written by an
earlier PR of this same phase.** `re_validate`'s `run_interactive`, `resolve_holdings_paths`,
`run_batch` and `main` each documented `SystemExit` without saying what raises it. E1 does
not recognize `sys.exit()` as a mechanism unless the entry names it, which is the point:
an entry that names the call can be checked against the AST and an entry that does not
cannot. All four now name it. `print_batch_status`, whose entry already said "raised by
sys.exit()", never fired.

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
| PR-30b | its eleven | `4a59b74` | **177** over 11 files |
| PR-30b | the same eleven | `0f5d9ae` | **0** over 11 files, exit 0 |

## 6. Module length, and the file that was already over a limit

    python critiques/pr-29a/measure_module_lines.py <the six files>

| file | total base | total head | docstring head | code base | code head |
|---|---:|---:|---:|---:|---:|
| `pdsdependency.py` | 1,165 | 1,509 | 374 | **1,135** | **1,135** |
| `re_validate.py` | 987 | 1,442 | 577 | 868 | 865 |
| `crlf.py` | 169 | 246 | 116 | 140 | 130 |
| `shelf_consistency_check.py` | 132 | 198 | 85 | 118 | 113 |
| `pds3/__init__.py` | 0 | 34 | 34 | 0 | 0 |
| `pds4/__init__.py` | 0 | 20 | 20 | 0 | 0 |

**`pdsdependency.py` fails the code-line limit at both ends and this PR did not move it.**
Deviation (3) sets code lines at 1,000 and total lines at 2,000. The file measures 1,135
code lines at base and **1,135 at head** -- the same number, not a similar one -- while its
total goes from 1,165 to 1,509. Docstrings move the total and leave the code count alone,
which is what the two limits are for; a reader seeing this file grow past 1,400 in a
docstring PR should read the last two columns. It is still under the total limit by 491
lines, and deferred **66** still holds the waiver-or-split decision, which is not this
PR's to make.

The other three lose code lines, between 3 and 10 each, and the causes are the two PR-30a
and PR-30b each recorded running opposite ways. A banner description line is a comment and
counts as code, so moving one into a docstring takes a code line away: that is 5 lines for
`pdsdependency.py` and `re_validate.py`, 11 for `crlf.py` and 6 for `shelf_consistency_check.py`.
A docstring inserted above a body that had no blank line before it adds one blank, and the
blank is not part of the docstring's own span. `pdsdependency.py` gains exactly as many
blanks as it loses comments and comes out level; the other three gain fewer. The statement
counts of section 3.1 are unchanged in every file, which is what says the movement is
entirely comments and blanks.

## 7. The Sphinx build

`docs/` does not exist and is not created here; PR-31 owns it. A throwaway tree is built
elsewhere instead, reproducibly, with `critiques/pr-29a/build_docs_probe.py` and
`critiques/pr-29/sphinx-conf.py` **both unchanged**. What is extended is the page list:
these six modules join the thirty-four the probe carried for PR-30b, and the same page list
is used at both ends.

    python critiques/pr-29a/build_docs_probe.py $PWD/src <build dir>         holdings_maintenance ... holdings_maintenance.pds3.shelf_consistency_check

| | base | head |
|---|---:|---:|
| `-n` problems | 33 | **27** |
| `-W` problems | 34 | **28** |
| probe exit status | 1 | **1** |

**The exit status is 1 at both ends and this record says so rather than rounding it to a
pass.** It was read from the probe's own return value; the probe appends a line of its own
when `sphinx-build` exits nonzero, and that line is the 28th `-W` problem.

**The head numbers are PR-30a's and PR-30b's exactly**, and the base numbers are those plus
six. All 27 remaining problems at each end are one warning repeated, filtered mechanically
by dropping every line matching "duplicate object description" and finding nothing left:

    <unknown>:1: WARNING: duplicate object description of
    pdsfile.holdings_maintenance._common.ToolSpec.progname, other instance in api,
    use :no-index: for one of them

one for each of `ToolSpec`'s 21 fields, `VersionedFile`'s three and `RunResult`'s three.
PR-30a isolated the cause with a two-class control and measured two fixes that each take it
to zero; neither is applied here, because `conf.py` belongs to PR-31 and five earlier
records depend on the probe's behavior. **Deferred observation 276 already carries it, and
this PR adds nothing to it.**

### 7.1 The six problems this PR removes, which were in prose it replaced

The base build's six extra problems are all malformed reStructuredText in docstrings this
PR rewrote, four in `PdsDependency.__init__`'s `Inputs:` block and two in
`get_all_log_info`'s indented return-value list:

    ERROR: Unexpected indentation. [docutils]
    WARNING: Block quote ends without a blank line; unexpected unindent. [docutils]
    WARNING: Definition list ends without a blank line; unexpected unindent. [docutils]

A hand-aligned column block is not a definition list, and Napoleon does not read it as
one. Both blocks are now `Parameters:` and `Returns:` sections and both render.

### 7.2 What the Sphinx gate caught in this PR's own prose

**Eleven `-n` problems, all of them type slots rather than content**, fixed before the
first review round:

* `pdslogger.PdsLogger` written as the type of a `logger` parameter, nine times. `pdslogger`
  publishes no Sphinx inventory, so the target does not resolve. The convention already in
  the tree is to give a logger no type slot at all -- `_linkshelf_common.py` and
  `_common.py` both do -- and these nine now follow it.
* `pdsfile.Pds3File` written as the type of a `pdsdir` parameter, twice. The class is
  defined as `pdsfile.pds3file.Pds3File` and re-exported, and the re-export is not a target.
  `_common.log_paths_for` documents its own PdsFile parameter without a type for the same
  reason.
* `SMTPException`, once, which is `smtplib.SMTPException` and resolves under that name.

This is the fourth PR in a row where the only Sphinx findings in new prose were markup or
reference tokens rather than anything about the content.

### 7.3 The head build is not vacuous

`api.html` from the `-n` build holds one match each for "Check that every file a PDS3
volume implies exists", "Re-run five of the PDS3 maintenance validations over whole
volumes", "Report every shelf file that has nothing left in holdings to describe",
"Report, and optionally repair, the line terminators of PDS3 text files" and "The
maintenance tools for a PDS3 holdings tree", against **zero** for each on the base page.


## 8. Standing gates

### 8.1 Test id sets, full data, both modes

The command lines are `scripts/automated_tests/pdsfile_main_test.sh`'s, plus `--junitxml`.
Run from each tree in turn, one at a time, per PR-30b's note that two runs in parallel put
the tool subprocesses `tests/holdings_maintenance/` drives into uninterruptible I/O wait.

| mode | scope | base | head | ids only in base | ids only in head | outcome changed |
|---|---|---|---|---|---|---|
| `ns` | all seven directories | 1101 passed, 34 skipped (1135 ids) | 1101 passed, 34 skipped (1135 ids) | none | none | none |
| `s` | `tests/pds3file/ tests/rules/pds3/` only | 555 passed, 3 skipped (558 ids) | 555 passed, 3 skipped (558 ids) | none | none | none |

The per-test id sets are diffed, not the counts: the junit files are parsed and compared id
by id with the outcome attached, so a test that changed from passed to skipped would show
even though the totals would not. The `--mode s` scope is the script's own, not the full
suite.

### 8.2 The code checks with no holdings

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        VENV=/seti/all_repos/rms-pdsfile/venv bash scripts/run-all-checks.sh -c -s

All checks passed, exit status 0: ruff, the indentation pass, pytest (**318 passed, 817
skipped**), pyroma, the API-freeze check and the clean-install gate.

### 8.3 The API freeze

    /seti/newnav/capped-run.sh pytest tests/api

**26 passed** inside the `ns` run above, and again inside `run-all-checks.sh`. The four
frozen files are byte-identical to `0f5d9ae`, checked with `git diff --quiet 0f5d9ae --
<file>` on each of `tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`,
`scripts/dump_public_api.py` and `tests/api/test_api_freeze.py`.

**The two zero-byte `__init__.py` files were the one freeze risk here and they are
freeze-neutral, measured rather than assumed.** Adding a docstring makes a zero-byte module
non-empty, so `scripts/dump_public_api.py` was run in both trees and the two outputs are
**byte-identical, 733,876 bytes each**. The manifest records name-to-kind pairs and has no
docstring field, and an empty module and a module holding only a docstring export the same
names.

### 8.4 ruff

    /seti/newnav/capped-run.sh ruff check src/pdsfile tests scripts                  # All checks passed, exit 0
    /seti/newnav/capped-run.sh ruff check .                                          # All checks passed, exit 0
    /seti/newnav/capped-run.sh ruff check --preview --select E111,E112,E113 .        # All checks passed, exit 0
    /seti/newnav/capped-run.sh ruff check . --config 'lint.per-file-ignores = {}'    # Found 2249 errors, exit 1

`ruff format` was not run, in any form.

### 8.5 The ratchet

| | base | head |
|---|---:|---:|
| `per-file-ignores` entries | 66 | 66 |
| code slots across those entries | 180 | 180 |
| findings with `per-file-ignores = {}` | 2,249 | 2,249 |
| `[project.scripts]` entries | 11 | 11 |

Nothing moved. Two of the six files carry an entry. `pdsdependency.py` names `B006`,
`PT028`, `RUF012` and `UP031`; `re_validate.py` names `RUF005` and `UP031`; `crlf.py`
names `PT028`; `shelf_consistency_check.py` names nothing, its `F821` having gone when
PR-28 fixed the undefined name behind it.

**`crlf.py`'s `PT028` cannot be retired by a docstring and is not left unexplained.** It
fires twice, on `test_crlf(filepath, task='test', threshold=0.01)`'s two defaulted
parameters, and only because the function's name matches pytest's collection pattern. It
is the tool's line-terminator classifier and not a test; deferred **137** records the
decision to keep the name and the reasons. `pdsdependency.py`'s `PT028` is the same shape
on `test1`, `test_suite` and `test`. The module docstring of `crlf.py` names `test_crlf()`
as the classifier a caller should use, which is the most a docstring can do about it.

`bandit` and `vulture` are disabled and not installed. This PR claims nothing about them.

### 8.6 The record checkers

    python critiques/pr-28/check_record_numbers.py
    python critiques/pr-29/check_citations.py

**15 stale at base and 15 at head, byte-identical outputs -- after a repair**, and **6
stale at base and 6 at head, byte-identical outputs, with no repair needed.**

Before the repair, head reported 17. The two extra were PR-28's own line-count table, whose
"head" column that checker compares against the tree it runs in rather than against PR-28's
head: `crlf.py` went from 169 lines to 246 and `shelf_consistency_check.py` from 132 to 194
when they gained module docstrings. Both rows are re-derived and the paragraph above the
table, which already named PR-30a's move of the `show_opus_products.py` row, now names
these two as well. This is the repair PR-29a, PR-30 and PR-30a each had to make for the
same reason.

The 15 that remain are PR-28's own, invalidated by PR-28a's extraction; the 6 are
deferred-observation citations into files outside the citation checker's scope list. Both
numbers arrived that way and this PR neither caused nor repaired them. Both checkers were
run again after this record, the four round records, the ten deferred observations and the
plan amendment were written, and both were still byte-identical to base.

**No line-count table in this record cites a number the record checker reads.** The tables
here are this PR's own base and head measurements.

## 9. What the docstrings had to correct about the code they describe

**Unlike PR-30b's eleven, these six carried 25 docstrings already, and the brief asked that
every existing claim be verified rather than reformatted.** Six of them were wrong. Four
are in prose PR-25a and PR-28 wrote and one in a banner comment; the sixth is the one the
whole review turns on.

* **`PdsDependency.__init__`: `"[x]" marks where to truncate the message if the command is
  "initialize" or "reinitialize"`.** Measured on a synthetic rule carrying both markers.
  Truncation happens for **initialize** and for **repair**, and does **not** happen for
  reinitialize, which is the one case the sentence named: the stale branch deletes the
  marker and keeps the tail whenever the message carries `[C]`. The sentence is inverted
  with respect to the case it names and silent about the case it covers.
* **`PdsDependency.__init__`: `newer  True if the file file must be newer`.** The doubled
  word is the visible half; the claim is also loose, because the comparison is
  `requirement_modtime < source_modtime`, so equal times pass and "must be newer" is "must
  not be older". Both are fixed.
* **`crlf.test_crlf`: `If the the fraction of non-ASCII characters exceeds this value, the
  file is not modified and "binary" is returned`.** Three things: the doubled word again,
  the returned value is `BINARY` and not `binary`, and "non-ASCII" is not what the table
  counts -- byte 127 is spared. Measured: a file half made of delete characters returns
  `OK`, the same file built from `0x01` returns `BINARY`.
* **`crlf.test_crlf`'s `Returns:` gave four verdicts with no condition on the task.**
  `INVALID` is unreachable under `repair` and `REPAIRED` unreachable under `test`, which is
  what a caller needs told; the docstring listed all four as though any run could produce
  any of them.
* **`shelf_consistency_check.py`'s banner: "Confirm that every info shelf file has a
  corresponding directory in holdings/".** It examines link and index shelves too, and for
  an index shelf what must exist is a `.lbl` file rather than a directory -- and for the
  other two kinds only existence is asked, so a plain file satisfies it. Three errors in
  one sentence, in the one line of prose that file carried.
* **`re_validate.get_all_log_info`: "skipping those that recorded a FATAL error".** True and
  incomplete in a way that matters: a log with no elapsed time at all is treated as fatal
  whether or not it holds a fatal record, which is how an interrupted run is kept out of the
  schedule. The docstring said nothing about it, and the mechanism is the whole reason the
  scheduler does not treat a killed run as a completed validation.

Two more claims in existing prose held up under measurement and are recorded because they
looked wrong and were not: `re_validate`'s comment that `MAX_INFO` is "read nowhere in this
module" is exact, and `crlf.main`'s comment that a run repairing two or more files prints
no summary at all is exact, including the case it does not mention -- a run repairing one
file and finding another invalid prints the repair summary and never mentions the invalid
one.

## 10. Contracts that had to be read out of the code

Each of these was settled by running something or by reading both ends, and each is
recorded because none is derivable from a name. They are where the reviewers found most of
what they found.

* **`pdsdependency`'s repair-message markers do not mean what the constructor said.** The
  original docstring said `[x]` "marks where to truncate the message if the command is
  initialize or reinitialize". Measured on a synthetic rule carrying both markers: the
  message is cut at `[x]` for a **missing** file whichever marker it carries, and cut for a
  **stale** file whose message carries `[c]`, and **not** cut for a stale file whose message
  carries `[C]`, where the marker is deleted and the tail kept. So truncation happens for
  initialize and for repair and not for reinitialize -- the one case the sentence named.
* **A `pdsdependency` rule's glob is filled in from the left and only twice.** The first
  `$` becomes the volume set directory name and a second becomes the volume name. Eight of
  the 117 rules carry one `$`; five of those cover a whole volume set, and **three spell a
  VG_28xx volume into the pattern**, so running the `vg_28xx` suite against `VG_2801` globs
  `VG_2803`'s and `VG_2810`'s files as well.
* **A suite a volume's path matches twice runs once.** `TranslatorByRegex.all()` drops a
  name it has already collected. Four volumes exercise it -- `GO_0xxx/GO_0020` through
  `GO_0023` name `body` through two rows -- and they run it once.
* **`get_modtime()` classifies two kinds of file and skips a third only in appearance.** A
  `.DS_Store` is logged at `pdslogger` level 10 and a dot-underscore file at level 40, so
  **one dot-underscore file anywhere below a volume gives the whole run a nonzero exit
  status** and a `.DS_Store` does not. The backup-file exclusion beside them is dead code;
  deferred **313** holds it.
* **`get_log_info()` scans for a marker no log this tool writes contains.** It looks for
  `| FATAL |`, and pdslogger renders a fatal record as `| CRITICAL |` and a logged
  exception as `| EXCEPTION |`. So its fatal flag is true exactly when the log has no
  elapsed time, and a validation whose every test raised writes a log that reads back as a
  clean completed run. Found by round 3, in prose round 1 had read and left. Deferred
  **323**.
* **`re_validate` returns the log beside the holdings tree, always.**
  `_common.log_paths_for` builds `[default, parallel]` and dedupes, `default` is the
  configured log root and `parallel` is the tree beside holdings, so `logfiles[-1]` is the
  latter whether or not a root is configured. That is the path a batch run puts in its
  error mail, so a reader of a failure report is sent to the tree beside holdings and not
  to the log root.
* **`re_validate` runs five of the checks this package offers and not all of them.**
  `pdsindexshelf` exports a `validate` task under the same name as the four it does call
  and is neither imported nor run, so a volume's metadata index shelves are never
  re-validated by this tool; `shelf_consistency_check` and `crlf` are two more checks it
  never reaches, having no task to call. Round 1 found the first and round 3 found that
  the correction naming the second had stopped one short of the third.
* **A failing test in `re_validate` costs the whole volume, not the group.** The handler is
  around the entire sequence, so a raise on the first test leaves every later one unrun and
  the volume still reports as done, with a count of 1. **How many that is depends on the
  volume**: three per volume-type directory present, two per archive group that found a
  tarball, one per link-shelf type and one for the dependency check. Round 3 measured 8 to
  16 across five real volumes, 29 for a fully populated one, and 19 for the test fixture --
  which is where the number the first correction quoted as a fact about volumes came from.
* **`re_validate`'s batch status is insulated from what a run found and not from whether it
  could mail the report.** `send_email()` is called from the same `finally` that reaches
  `sys.exit(0)` and nothing catches it, so an unreachable relay ends the run in an
  exception and status 1 -- the outcome the design exists to prevent. Deferred **321**.
* **`shelf_consistency_check` matches `shelves` as a substring of the whole path.** A tree
  holding `myshelves-backup/` reports one error per directory in it, and a root whose own
  path contains `shelves` reports most of the tree below it -- not all, because a directory
  whose own name ends in `shelves` is skipped by a guard the prose had not mentioned, and
  one that does sit under a recognized kind is examined instead. Round 4 measured four of
  seven. Its counterpart derivation drops everything after the **last** underscore rather
  than a `_info` or `_links` suffix, so a path with no underscore anywhere maps to the empty
  string and is always reported; and it asks only that the result exist, so a plain file
  satisfies a check the prose called a directory.
* **`crlf` counts byte 127 as text.** `NON_ASCIIS` spares `range(32, 128)`, so a file that
  is half delete characters classifies `OK` while the same file built from `0x01`
  classifies `BINARY`. The word "printable ASCII" is wrong for exactly one byte value, and
  the docstring now states the ranges instead.
* **`crlf`'s codec is `latin8`, which is ISO-8859-14 and not Latin-1.** It decodes all 256
  byte values and round-trips them unchanged, which is the property the prose needs -- every
  byte is one character, so a repair cannot corrupt one -- and it is not the codec the name
  suggests.
* **`pdsdependency` writes its per-volume log through handlers attached per suite.** They
  are handed to `test()` and on to each `test_suite()`, which attaches them at its own
  `logger.open()`; `PdsLogger.close()` removes them. So the lines `main()` logs to announce
  where a volume's log is -- one per log path, before the first suite opens -- reach none
  of them. **And they name paths nothing writes**: the category component is stripped from
  each path as its handler is built, and the announcement iterates the list from before
  that. Round 2 found the first half and round 4 the second.

## 11. Review

Four rounds, each run by a fresh reviewer subagent with no context from this session or
from any other round. Records: `critiques/pr-30c/round-1.md` through `-4`.

| round | slice | surface | disproved | misleading | code defects | of the findings, in the corrections |
|---|---|---|---:|---:|---:|---:|
| 1 | `re_validate.py` | 18 functions, 39 parameters | 5 | 9 | 1 | -- |
| 2 | the other five files | 1 class, 13 functions, 34 parameters | 9 | 5 | 1 | -- |
| 3 | `re_validate.py`, re-read | the same | 2 | 8 | 1 | **8 of 11** |
| 4 | the same five, re-read | the same | 3 | 9 | 1 | **7 of 13 written, 10 of 13 owed** |
| | | | **19** | **31** | **4** | **15 of 24, or 18 of 24** |

Every finding was re-verified by the executor before it was acted on. The four with the
widest consequences -- the returned log path, the `| FATAL |` scan, the dead backup block
and the three corrections that never landed -- were each re-derived from scratch rather
than read. Both second-read briefs carried the correction commit by name, an enumeration
of the claims that commit was said to make -- fifteen for round 3 and thirteen for round 4
-- and the instruction to treat every one as unproven and to attribute each finding with
`git blame`.

### The failure this PR is the clearest case of

**Round 4's first act was to check whether the corrections it had been sent to review were
in the file, and three of them were not.** The brief listed thirteen claims commit
`d7bcff3` was said to have written. `git show` touches `pdsdependency.py` in three hunks,
and `git blame` puts every line of the module docstring and of the `glob_pattern`
parameter at `3bddc99`, the original draft. Three of the thirteen -- "It creates nothing
and repairs nothing", "a volume picks up as many suites as its path matches", and "a
pattern with one `$` covers a whole volume set" -- were still there, still wrong, and
announced as fixed in a commit message.

The mechanism is worth recording exactly, because it is not a lapse of attention. The
corrections were applied by a script that accumulated six substitutions in memory and
wrote the file once at the end. The fourth substitution's search string did not match, the
assertion fired, and the process exited **before the write**, discarding the three that had
succeeded. A second script then applied the remaining three, and the commit message was
written from the list of findings rather than from the diff. Every later script in this PR
writes the file after each substitution, so a failure loses nothing that came before it.

**PR-30b's lesson was that a correction reaches three of the four places it belongs. This
is the same defect one level up: a correction that reaches the commit message and the round
record and not the code at all.** Section 5 of this PR's brief asked for a grep of the whole
repository after every correction pass; had that grep been run against the *corrected*
wording rather than assumed, it would have found nothing and said so. It is now run, and
section 11.2 reports it.

Round 4 also found the same shape inside the corrections that did land:
`shelf_consistency_check`'s count of what a run examines is stated twice, ten lines apart,
and the correction qualified the statement in `main()`'s docstring and left the module
docstring's version unqualified. Round 3 found three more of it in `re_validate` --
`UnicodeDecodeError` added to one of the two docstrings that needed it, `OSError` added to
`main()`'s `Raises:` while three sibling entries stayed missing, and the one-or-two log
paths distinction written into a `Returns:` block twelve lines below a `Parameters:` entry
that describes the same pair and still said "the volume's own file handler and error
handler" where four are attached.

### 11.1 The second reads found most of their yield in the first reads' corrections

**Eight of round 3's eleven findings and seven of round 4's thirteen are in sentences the
first reads' corrections wrote** -- 15 of 24. Counting the three corrections round 4 found
missing, which the correction pass is equally answerable for, it is 18 of 24. PR-29a
measured 11 of 23 on this question, PR-29b 10 of 21, PR-30 34 of 57, PR-30a 15 of 22 and
PR-30b 10 of 13. **This is 0.63 by the strict count and 0.75 by the second, against
PR-30b's 0.77, so it is not the highest share measured -- and it is the first of the six to
find a whole class of correction that was never applied at all.** The trend the five
previous records describe is unbroken in substance: the correction pass, not the first
draft, is where a docstring PR's remaining defects are.

The sharpest of them is not the largest. Round 3 found that `get_log_info()` scans each
record for `| FATAL |`, a string pdslogger never writes: a fatal record renders as
`| CRITICAL |` and a logged exception as `| EXCEPTION |`. So the flag is true exactly when
there is no elapsed time, and a volume whose every test raised writes a log the next batch
run reads back as a clean completed validation. That is a code defect in prose **round 1
had read and left alone**, six lines above a `Raises:` block the correction rewrote.

Four more of the same shape are worth naming because each reads as freshly checked:

* **"twelve of the fourteen".** Round 1 disproved "every tool in the package" and the
  correction replaced it with a count. Round 3 measured eleven, and pointed out that the
  sentence's own semicolon names three of fourteen as exceptions, so it contradicts itself
  as well as the measurement.
* **"the one way a batch run ends nonzero".** Round 1 found that an unreachable mail relay
  defeats the exit-status guarantee, and the correction wrote it up as the only way. Round
  3 got exit 1 four ways with no relay involved, three of them documented by the entry
  immediately above this one in the same `Raises:` block and one by the entry immediately
  below it.
* **"eighteen of nineteen tests unrun".** Round 1 found that a failing test costs the whole
  volume, and the correction quoted the number its own stub run produced. Round 4's slice
  is elsewhere, but round 3 measured the real thing: 8 to 16 tests on five real volumes, 29
  on a fully populated one, and 19 exactly for the test fixture, which builds five
  volume-type directories and no tarballs.
* **`sys.exit(0)` "from the same `finally`".** The correction placed the exit inside the
  block it is after, and glossed `OSError` as unreachability when `smtplib.SMTPException`
  is a subclass of `OSError` and covers refusal too -- which `send_email`'s own docstring,
  two hundred lines above, already said.

### 11.2 The grep section 5 asked for

After the final correction pass, the whole repository was searched for every disproved
claim, by its own words. Seventeen strings were searched: the four module summaries, the
two counts, the two exit-status claims, the marker claims and the rest.

**Every one survives only inside `critiques/pr-30c/round-*.md`, where it is quoted as a
finding.** None is in `src/`, in `tests/`, in `plans/` or in this record. Two of the
seventeen appear in two round records each, which is the two reads of one slice reaching
the same sentence.

The count worth reporting is the other one. **Of the 34 corrections this PR made, five had
to reach more than one place**: the `| FATAL |` finding reached four sentences in one file,
the log-path finding reached a `Returns:` block and a `Parameters:` entry, the
`UnicodeDecodeError` finding reached two docstrings, the "what a run examines" count
reached a module docstring and a function docstring, and the "five validations" finding
reached the module docstring twice. In four of those five the first attempt reached one
place and a later round found the other. **That is the number the brief asked for, and it
says the answer is routinely more than one.**

### 11.3 The freeze rule was followed

Deferred entry 239 asks that the previous round's corrections be committed and the tree
left alone before the round that reviews them is launched. Rounds 1 and 2 were launched
against a frozen `3bddc99` and rounds 3 and 4 against a frozen `d7bcff3`;
`git diff --stat <sha> -- src/` was empty at every check while a round was running, and
both second-read reviewers independently reported the head commit they measured. This
record, the round records, the deferred observations and the plan amendment were written
while rounds 3 and 4 ran, and none of them is under `src/` or reachable from the diff the
two reviewers were given.

## 12. What this closes, and what remains of Phase 7

    python critiques/pr-29/check_docstrings.py $(find src/pdsfile -name '*.py' \
        ! -name '_version.py' | sort)

**94 findings over 78 files at `0f5d9ae`, and 0 over 78 at head, exit status 0.** That is
every module the package ships except `_version.py`, which setuptools_scm generates and
`.gitignore` excludes. **Phase 7's docstring work on `src/` is finished with this PR.**

What is left of Phase 7 is PR-31's `docs/` tree -- `conf.py`, the API reference pages, the
README include marker -- and the Sphinx gate in `run-all-checks.sh` and the CI lint job,
then PR-32 through PR-34's guides. The plan's PR-31 entry now says so, and says one more
thing it did not: **deferred observation 276's two measured fixes are waiting for it.**
Every docstring PR from PR-30a onward has reported the same 27 `-n` problems from the
throwaway build probe, PR-30a isolated the cause with a two-class control, and both fixes
it measured take the count to zero. Neither could be applied while `conf.py` did not exist.
PR-31 is the PR that owns them, so its first build should not rediscover the warning.

## 13. Numbers this PR was handed that did not reproduce

Recorded because every number was re-derived rather than inherited.

* **The brief's scope was four files and the correct scope is six.** Its table -- 1,165 /
  987 / 169 / 132 lines, 8 / 18 / 3 / 2 functions, 5 / 1 / 0 / 0 undocumented, 29 / 39 / 4
  / 1 parameters, no module docstring anywhere -- reproduces exactly, and so does its "31
  functions, 73 parameters". What it leaves out is the two zero-byte
  `holdings_maintenance/pds3/__init__.py` and `pds4/__init__.py`, which carry one `M1`
  finding each. **Measured before deciding:** `check_docstrings.py` over every module under
  `src/pdsfile/` except `_version.py` reports **94 findings over 78 files** at `0f5d9ae`,
  and 92 of the 94 are the four tools. So the four-file scope would have left the plan's
  own completion claim -- "the checker reports zero over every module under `src/pdsfile/`
  except `_version.py`" -- false by two findings, in a PR whose stated purpose is to close
  that work. The two files are in scope here and section 1 measures them.

  The brief is not the only place that says four: the plan's PR-30c entry did too, while
  the same entry named "one finding each for the two zero-byte `__init__.py` files" two
  lines above. PR-30b's section 12 had it right. The plan now says six.

* **The brief's scope table omits the class**, exactly as PR-30's and PR-30a's did. There
  is one, `PdsDependency`, and it had no docstring, so the base `M1` count of 13 is 6
  modules plus 1 class plus 6 functions rather than 6 plus 7. PR-30b's section 12 named it
  ("31 functions, one class, 73 parameters"); the brief dropped it in the copy. This is the
  third scope table in a row to leave the classes out, which is now a pattern rather than
  an oversight.

* **The brief projected `pdsdependency.py` at "roughly 1,280" total lines and it is
  1,475.** The projection was offered as an estimate rather than a measurement, and the
  point it was making -- that the total moves and the code count does not -- holds exactly:
  1,135 code lines at both ends. The estimate is 195 lines low, which is the same direction
  and roughly the same share as PR-29b's ten-member sample, and for the same reason: a
  projection cannot see the review rounds' corrections.

Everything else reproduced exactly:

* the base `check_docstrings.py` total of **92 findings over 4 files**, which is what the
  plan and PR-30b's record both carry, and the breakdown behind it -- 54 `P2`, 11 `M1` over
  the four, 11 `R1`, 10 `P3`, 4 `E1`, 2 `E2`;
* the 25 pre-existing docstrings, 13 of them carrying a Google section, nine spelled
  `Args:`; the tenth `P3` is an `Inputs:` the brief did not mention and PR-30b's record
  did not either;
* the `ns` **1135** and `s` **558** baselines, id for id, at base and at head;
* all four ratchet numbers, **66 / 180 / 2,249 / 11**;
* `crlf.py`'s `PT028`, which is on the file for the reason the brief gives and which no
  docstring can retire; section 8.5 says so rather than leaving the entry unexplained;
* the seven checker reproductions -- PR-29's **276**, PR-29a's **249**, PR-29b's **73**,
  PR-30's **78** at `c4811d8` and **0** at `80f5e52`, PR-30a's **235** at `80f5e52` and
  **0** at `4a59b74`, and PR-30b's **177** at `4a59b74` and **0** at `0f5d9ae`;
* `critiques/pr-28/check_record_numbers.py` at **15 stale** and
  `critiques/pr-29/check_citations.py` at **6 stale**, both at base;
* PR-30a's and PR-30b's Sphinx measurement of **27** `-n` problems and **28** `-W`, and the
  probe's exit status of 1. This PR's base measures 33 and 34 because its page list carries
  six more modules, and the six extra are malformed reStructuredText in the two docstrings
  this PR replaced;
* `critiques/deferred-observations.md` continuing from **313**: the last entry at `0f5d9ae`
  is 312.
