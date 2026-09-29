# PR-30a validation — Google-style docstrings, the tool core and the two subclasses

Base: `80f5e52`. Branch: `pr-30a-docstrings-tool-core`. Base branch: `rewrite`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), from the tree being measured, with
`PYTHONPATH=$PWD/src`. Where holdings are needed the environment carried
`PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree is
a second worktree at the same commit, so "base" numbers were measured, not recalled.

Nothing here is inherited. Every number carries the command that produced it, and section
12 lists the numbers this PR was handed that did **not** reproduce.

**Every gate was run with its output to a file, its exit status read, and its totals line
grepped out of that file.** PR-30's record says why: a checker of its own reported 24
findings for hours while the record said it passed, because every re-run was read through
`tail -2` and the totals line fell above the cut. No result below was judged by a tail.

## 1. Scope

Ten modules, and only these:

    python critiques/pr-29/measure.py \
        src/pdsfile/holdings_maintenance/__init__.py \
        src/pdsfile/holdings_maintenance/_common.py \
        src/pdsfile/holdings_maintenance/_archives_common.py \
        src/pdsfile/holdings_maintenance/_indexshelf_common.py \
        src/pdsfile/holdings_maintenance/_linkshelf_common.py \
        src/pdsfile/holdings_maintenance/_shelf_common.py \
        src/pdsfile/pds3file/__init__.py src/pdsfile/pds4file/__init__.py \
        src/pdsfile/tools/__init__.py src/pdsfile/tools/show_opus_products.py

| group | files | lines at base | classes | funcs | undocumented funcs | params |
|---|---:|---:|---:|---:|---:|---:|
| `holdings_maintenance/_*.py` and its `__init__.py` | 6 | 2,468 | 4 | 47 | 3 | 142 |
| `pds3file/__init__.py`, `pds4file/__init__.py` | 2 | 510 | 2 | 33 | 23 | 20 |
| `tools/` | 2 | 199 | 0 | 2 | 0 | 1 |
| | **10** | **3,177** | **6** | **82** | **26** | **163** |

**None of the ten had a module docstring**, and two of the ten -- `holdings_maintenance/__init__.py`
and `tools/__init__.py` -- were zero-byte files.

**The handed scope table omitted the classes**, exactly as PR-30's did. There are six:
`ToolSpec`, `VersionedFile`, `RunResult` and `LinkInfo` in the shared core, all documented
at base, and `Pds3File` and `Pds4File`, neither documented. Section 12 records it.

`params` counts parameters excluding `self` and `cls` and includes nested functions, which
is what `measure.py` counts; the 163 is the 142 of the core plus the 20 of the two
subclasses plus the one of `show_opus_products.main`.

Not in scope, each its own later PR: the 17 per-tool modules under
`holdings_maintenance/pds3/` and `pds4/`.

## 2. What changed

Docstrings only. **Ten module docstrings** (all new), **six class docstrings** (two new,
four rewritten) and **82 function docstrings** (26 new, 56 rewritten) -- 98 in all.
Section 3 proves that no executable statement moved.

42 comment lines were deleted and one was added; section 3.2 enumerates every one.

`critiques/pr-30a/` carries one script this record cites that no earlier PR had:
`check_spec_readers.py`, described in section 4, and the four round records. No script of
PR-28's, PR-29's, PR-29a's or PR-30's is edited here except `check_citations.py`, whose
own citation table moved with the lines this PR moved; section 10.6 records that.

## 3. Proof that the change is docstrings only

### 3.1 The AST hashes, and the two files where the hash cannot answer

`critiques/pr-29/strip_docstrings.py` parses a module, deletes the docstring node of every
module, class and function, and hashes `ast.dump` of what is left with
`include_attributes=False`, so line and column shifts do not register.

    python critiques/pr-29/strip_docstrings.py <the ten files>

| file | base | head |
|---|---|---|
| `holdings_maintenance/__init__.py` | `3543b4693a36a109` | **`5c04595997820c90`** |
| `holdings_maintenance/_common.py` | `efc7aeef4aea6793` | `efc7aeef4aea6793` |
| `holdings_maintenance/_archives_common.py` | `2c60982b42ce37b8` | `2c60982b42ce37b8` |
| `holdings_maintenance/_indexshelf_common.py` | `1905bd57b9cd2b13` | `1905bd57b9cd2b13` |
| `holdings_maintenance/_linkshelf_common.py` | `e924a53b7b75f574` | `e924a53b7b75f574` |
| `holdings_maintenance/_shelf_common.py` | `fac6270fcbf9a589` | `fac6270fcbf9a589` |
| `pds3file/__init__.py` | `0b1042c0fb87c234` | `0b1042c0fb87c234` |
| `pds4file/__init__.py` | `49f5e249ba195c00` | `49f5e249ba195c00` |
| `tools/__init__.py` | `3543b4693a36a109` | **`5c04595997820c90`** |
| `tools/show_opus_products.py` | `0c151b3e91fb7b4d` | `0c151b3e91fb7b4d` |

**Eight of the ten pairs match. Two do not, and the reason is a property of the script
rather than of the change.** `strip_docstrings.strip()` replaces a body left empty by the
removal with a single `pass`, so that the tree stays valid:

    node.body = body[1:] or [ast.Pass()]

A zero-byte module has no body at all, so the guard above it never fires and its stripped
tree is `Module(body=[])`. A module whose whole content is a docstring strips to
`Module(body=[Pass()])`. The two hash differently, and they differ for any docstring
whatever -- both new `__init__.py` files hash to the same `5c04595997820c90` although
their docstrings share not one sentence. **The hash for those two files measures nothing
about this change, and it is not treated as evidence.** The script was not amended: it is
inherited, three earlier records depend on its numbers, and amending a gate so that it
passes is a hard stop.

What is offered instead is a stronger check, which is available precisely because the
files were empty:

    base 0 bytes, base AST body 0 nodes;
    head AST body 1 node, sole node is the module docstring: True

for both files. A module whose entire abstract syntax tree is one string constant cannot
carry an executable statement, so nothing needs to be compared: the head file is a
docstring and nothing else, and the base file was nothing at all.

PR-29 established that the hash check is not vacuous, with five mutations of a documented
file; the script is used here unchanged.

### 3.2 The comment enumeration, which the AST cannot see

    python critiques/pr-29/check_comments.py <base tree> <head tree> \
        holdings_maintenance/__init__.py ... tools/show_opus_products.py

`check_comments.py` joins its module arguments under `src/pdsfile/`, so the ten names are
given with their package path.

| file | comment lines at base | at head | removed | added |
|---|---:|---:|---:|---:|
| `holdings_maintenance/__init__.py` | 0 | 0 | 0 | 0 |
| `holdings_maintenance/_common.py` | 42 | 31 | 11 | 0 |
| `holdings_maintenance/_archives_common.py` | 18 | 13 | 5 | 0 |
| `holdings_maintenance/_indexshelf_common.py` | 47 | 39 | 8 | 0 |
| `holdings_maintenance/_linkshelf_common.py` | 73 | 65 | 8 | 0 |
| `holdings_maintenance/_shelf_common.py` | 53 | 46 | 7 | 0 |
| `pds3file/__init__.py` | 26 | 25 | 2 | 1 |
| `pds4file/__init__.py` | 31 | 30 | 1 | 0 |
| `tools/__init__.py` | 0 | 0 | 0 | 0 |
| `tools/show_opus_products.py` | 14 | 14 | 0 | 0 |
| | | | **42** | **1** |

**41 of the 42 removals are the same thing**: the description paragraph inside each file's
banner comment, which `doc_python.mdc` section 4 requires be a module docstring and which
therefore could not stay where it was, together with the bare `#` separators those
paragraphs sat between. Every file's `# pdsfile/<name>.py` line is untouched, and every
fact each removed line carried is in the module docstring that replaced it -- with three
exceptions, all of them corrections, recorded in section 8.

**The 42nd removal and the one addition are a single banner rule.**
`pds3file/__init__.py`'s closing banner rule was 89 `#` characters where its opening rule,
and every other banner in the package, is 90. It is replaced by a 90-character rule. That
is a comment change and is reported as one rather than passed over as cosmetic.

## 4. The spec-reader checker -- the mechanical gate this PR needed

`ToolSpec` is data only: nothing in the module that defines it reads a field, and every
read happens in one of the other five. Its docstring therefore claims, per field, which
function reads it, because "the spec carries this field" and "this tool acts on it" are
different claims and only the second is useful to a reader. That map is prose about which
of twenty-odd functions reads which of twenty-one fields, it is the densest concentration
of relationship claims in the PR, and nothing checked it.

`critiques/pr-30a/check_spec_readers.py` derives it from the AST and compares it against
the docstring in both directions.

| code | check |
|---|---|
| S1 | the entry for a field names a reader that does not read it |
| S2 | a reader of a field is not named in the entry for it |
| S3 | a field is read nowhere under the source root |

**S2's unit depends on how widely the field is read, and that is a decision rather than an
oversight.** For a field with five readers or fewer the unit is the function: every one
must be named, so an entry cannot name the reader that supports its story and stay silent
about one that would contradict it. Above that, the unit is the module -- `logname` is read
by twenty functions across four modules and an entry listing all twenty would be
unreadable, while the claim that matters, which shared module acts on this field and
therefore which of the ten tools it reaches, is settled at module granularity. An entry
that names one reader per module and describes the rest in prose passes there; an entry
silent about a whole module does not.

**A documented reader must carry its module qualifier**, checked as S4. A bare name would
match a function of that name in any module, and this tree has several: `link_targets`
exists in `_linkshelf_common` and in both link shelf tools, and `initialize` through
`update` in all ten tool modules.

**Every `name()` token in an entry is read as a claim**, including one written for some
other reason. That is deliberate: an entry that names a function in parentheses reads as
though that function acts on the field, and S1 fired on exactly that during this PR.

### 4.1 What it found

    python critiques/pr-30a/check_spec_readers.py src/pdsfile

| | base | head, before repair | head |
|---|---:|---:|---:|
| S1 entry names a non-reader | 1 | 4 | 0 |
| S2 module with no named reader | 38 | 20 | 0 |
| S3 field read nowhere | 0 | 0 | 0 |
| | **39** | **24** | **0**, exit status 0, over 21 fields |

The base column is measured against the base tree's own `_common.py` with this PR's
script, and it is what an entry set written without the gate looks like.

The four S1 findings are the ones worth naming, because each is a sentence that reads as a
relationship claim and is not one:

* `logname`'s entry said each helper "falls back to `PdsLogger.get_logger()` on it".
  `get_logger` is the call the fallback makes; it reads no spec field.
* `pdsfile_cls`'s entry named `set_log_root()` and `close_all_shelves()`. Both are called
  **on** the class the field holds. Neither reads the field.
* `log_path_method`'s entry said every tool "reaches `log_paths_for()` the same way".
  `log_paths_for` is handed the method name by its callers and never touches a spec.

### 4.2 The mutations

Each mutation was applied to a copy of the head tree, the checker run over it, and the
copy discarded.

| mutation | finding |
|---|---|
| unmutated control, before and after | 0 findings over 21 fields, exit 0 |
| the reader name deleted from `index_ext`'s entry | S2 read in `_indexshelf_common.py`, by `index_targets` |
| `read_links()` changed to `load_links()` in `link_target_regex`'s entry | S1 names a non-reader, **and** S2 |
| `spec.index_ext` replaced by a literal, making the field inert | S3 read nowhere, **and** S1 |
| a synthetic `spec.index_ext` read added to `_archives_common.py` | S2 read in `_archives_common.py` |

## 5. The Google-style docstring checks

    python critiques/pr-29/check_docstrings.py <the ten files>

| code | check | base | head |
|---|---|---:|---:|
| P1 | a `Parameters:` entry that is not a parameter of the signature | 0 | 0 |
| P2 | a parameter that does not appear in `Parameters:` exactly once | 144 | 0 |
| P3 | a section spelled `Args:`, `Arguments:`, `Keyword arguments:` or `Input:` | 34 | 0 |
| R1 | `Returns:` present without a value return, or absent with one | 7 | 0 |
| E1 | a `Raises:` entry the body neither raises nor attributes to a call it makes | 11 | 0 |
| E2 | a class raised in the body that `Raises:` does not name | 1 | 0 |
| D1 | a docstring line wider than 90 columns | 0 | 0 |
| U1 | a unicode smart quote, dash or arrow anywhere in the file | 0 | 0 |
| M1 | a module, class or function with no docstring | 38 | 0 |
| | **total** | **235** | **0**, exit status 0, over 10 files |

M1's 38 is 10 modules plus 2 classes plus 26 functions.

The checker is used **unchanged**. Run against the state each earlier PR's modules were in
before that PR documented them, it still reports the numbers those records carry:

| record | modules | commit | reported |
|---|---|---|---:|
| PR-29 | its five | `4edc7d1` | **276** over 5 files |
| PR-29a | its nine | `9466dbc` | **249** over 9 files |
| PR-29b | `_properties.py` | `998a166` | **73** over 1 file |
| PR-30 | the 36 rule modules | `c4811d8` | **78** over 36 files |
| PR-30 | the same 36 at `80f5e52` | `80f5e52` | **0** over 36 files |

`critiques/pr-30/check_rule_tables.py` also still reports **0 findings over 36 files**,
exit 0, at `80f5e52`, so PR-30's repaired gate is still passing.

## 6. Module length

    python critiques/pr-29a/measure_module_lines.py <the ten files>

Neither limit is in question here and all ten pass both at both ends, but the measurement
is recorded rather than left unaddressed.

| file | total base | total head | docstring head | code base | code head |
|---|---:|---:|---:|---:|---:|
| `holdings_maintenance/__init__.py` | 0 | 36 | 36 | 0 | 0 |
| `_common.py` | 398 | 576 | 335 | 251 | 241 |
| `_archives_common.py` | 242 | 378 | 163 | 219 | 215 |
| `_indexshelf_common.py` | 598 | 816 | 323 | 500 | 493 |
| `_linkshelf_common.py` | 729 | 1,113 | 464 | 655 | 649 |
| `_shelf_common.py` | 501 | 650 | 271 | 384 | 379 |
| `pds3file/__init__.py` | 273 | 626 | 359 | 246 | 267 |
| `pds4file/__init__.py` | 237 | 407 | 222 | 183 | 185 |
| `tools/__init__.py` | 0 | 12 | 12 | 0 | 0 |
| `tools/show_opus_products.py` | 199 | 265 | 83 | 181 | 182 |

The largest is `_linkshelf_common.py` at 1,113 total against a limit of 2,000 and 649 code
lines against a limit of 1,000, so the tightest margin in the PR is 887 lines.

**Five of the ten lose code lines and three gain them**, which needs saying because a
docstring-only change should not move a measure defined as "total minus docstring lines".
Both directions have the same two causes and they run opposite ways. A banner description
line is a comment and counts as code, so moving one into a docstring takes a code line
away: that is the whole of the five decreases, and `_common.py`'s eleven removed comment
lines against one added blank gives exactly the ten it loses. A docstring inserted above a
body that had no blank line adds one, and the blank is not part of the docstring's own
span: `pds3file/__init__.py` gains 21 code lines for the 21 new function docstrings that
needed one, and `pds4file/__init__.py` two for its two.

## 7. The Sphinx build

`docs/` does not exist and is not created here; PR-31 owns it. A throwaway tree is built
elsewhere instead, reproducibly, with `critiques/pr-29a/build_docs_probe.py` and
`critiques/pr-29/sphinx-conf.py` **both unchanged**. What is extended is the page list: the
ten modules join the thirteen the probe already carries.

    python critiques/pr-29a/build_docs_probe.py $PWD/src <build dir> \
        holdings_maintenance holdings_maintenance._common ... tools.show_opus_products

| | base | head |
|---|---:|---:|
| `-n` problems | 47 | **27** |
| `-W` problems | 29 | **28** |
| probe exit status | 1 | **1** |

**The exit status is 1 at both ends and this record says so rather than rounding it to a
pass.** It was read from the probe's own return value, not inferred from the absence of
warning lines; the probe appends a line of its own when `sphinx-build` exits nonzero, and
that line is one of the 28.

### 7.1 What is left, and why it is not this PR's prose

**All 27 remaining problems at head are one warning repeated**, and the 28th is the probe's
own exit line:

    <unknown>:1: WARNING: duplicate object description of
    pdsfile.holdings_maintenance._common.ToolSpec.progname, other instance in api,
    use :no-index: for one of them

one for each of `ToolSpec`'s 21 fields, `VersionedFile`'s three and `RunResult`'s three.
**All 27 are present at base too**, unchanged in text and in count.

The cause was isolated with a two-class control rather than argued from the message. A
throwaway package holding one dataclass whose docstring has an `Attributes:` section and
one whose docstring describes its field in prose, built with the same `conf.py` and the
same page directives, reports the warning for the first and nothing for the second. So:
Napoleon renders an `Attributes:` entry as an attribute directive, autodoc renders the
same dataclass field again because it is annotated and the probe's page carries
`:undoc-members:`, and the two collide.

Two fixes were measured on that control and **both take it to zero**: `napoleon_use_ivar =
True` in `conf.py`, which renders the entries as a field list that creates no target, or
dropping `:undoc-members:` from the page. Neither is applied here. The configuration and
the probe are inherited, four earlier records depend on their behavior, and `conf.py`
belongs to PR-31. Deferred observation 276 carries it.

### 7.2 What the Sphinx gate caught in this PR's own prose

Four defects, all in prose written for this PR, all fixed:

* two bare trailing-underscore tokens, ``bundletype_`` and ``root_``, which
  reStructuredText reads as references to targets that do not exist. Both builds failed
  with `ERROR: Unknown target name`. This is the same shape PR-30 section 7.1 recorded and
  it recurred anyway;
* a bare `*` inside a signature sketch, `(dirpath, old_links=None, *, logger, limits)`,
  read as an inline emphasis start with no end. The base carried this one too, so the
  repair also removes a warning that arrived with the file;
* `callable` written in a `Returns:` type slot, which resolves to nothing under `-n`. It
  is now `collections.abc.Callable`, which the Python inventory carries.

The base build's other 19 `-n` problems are the malformed `Raises:` and
`Keyword arguments:` blocks these docstrings replaced: a `Raises:` whose continuation
lines were not indented under the entry name made Napoleon read each line as its own
exception type, so `py:exc reference target not found: that returns from here has one to
run;` was a real warning at base.

### 7.3 The head build is not vacuous

`api.html` from the `-n` build holds 19 matches for "The PDS3 name for", against **zero**
on the base page, and one each for the exact sentences "Three drivers serve the ten" and
"OPUS products of the paths".

## 8. What the docstrings had to correct about the code they describe

Three claims in the banner comments this PR replaced were wrong, and the replacements do
not carry them forward. Each was settled by grep or by reading the tool modules, not by
reading the banner:

* **`_shelf_common.py`'s banner said it was "the part only the checksums, infoshelf,
  indexshelf and linkshelf tools use".** The index shelf tools import nothing from it:
  `_indexshelf_common.py` imports `_common` alone, and neither `pdsindexshelf.py` nor
  `pds4indexshelf.py` names `_shelf_common`. The module docstring now says which six of
  the ten tools reach it and which parts each of them reaches.
* **`ToolSpec`'s docstring said the pds4 name matches the pds3 name "for the pds4 index and
  link shelf tools".** It is all five: `pds4archives`, `pds4checksums`, `pds4indexshelf`,
  `pds4infoshelf` and `pds4linkshelf` set `progname` to `pdsarchives`, `pdschecksums`,
  `pdsindexshelf`, `pdsinfoshelf` and `pdslinkshelf` respectively.
* **`ToolSpec`'s docstring said `log_path_method` is "read by run_main"** and that
  `expand_target` is likewise. `log_path_method` is also read by
  `_indexshelf_common.run_index_main`; `expand_target` is read by `run_main` alone, and the
  sentence explaining which tools leave it unset named only four of the six that do.

## 9. Contracts in the shared core that had to be read out of the code

These are the sentences section 4.1 of the brief predicted would be the defect
concentration. Each was settled by running something or by reading both ends, and each is
recorded because none of them is derivable from a name.

* **`setup_run()` returns `(args, logger)` and the exit status is not among them.** Each of
  the three drivers declares its own `status = 0` after the call, and the three do not agree
  on what to do with it: `run_main` and `run_index_main` end in `sys.exit(status)`, while
  `run_selection_main` returns a `RunResult` and leaves the decision to the tool. The four
  tools on that driver then disagree in turn -- both info shelf tools call
  `sys.exit(result.status)`, and both checksum tools exit with a status only through the
  `pdsinfoshelf` subprocess they may chain, and otherwise fall off the end of `main()` and
  exit 0. Deferred observation 115 already records that last one.
* **`ToolSpec.index_ext` is read, in exactly one place.** `_indexshelf_common.index_targets`
  reads it to build the glob that finds a metadata directory's tables. The field is not
  inert; what is true of it is that it is read for two of the ten tools and set on all ten.
  Section 12 records that the brief said otherwise.
* **Which driver serves which tool**, settled from the ten `main()` functions:
  `run_main` for `pdsarchives`, `pds4archives`, `pdslinkshelf` and `pds4linkshelf`;
  `_shelf_common.run_selection_main` for `pdschecksums`, `pds4checksums`, `pdsinfoshelf`
  and `pds4infoshelf`; `_indexshelf_common.run_index_main` for `pdsindexshelf` and
  `pds4indexshelf`.
* **No tool module reads its own spec.** Grepping `SPEC.` and `spec.` across
  `holdings_maintenance/pds3/` and `pds4/` returns nothing but the `SPEC = ToolSpec(...)`
  constructions themselves. Every read is in one of the five shared modules, which is what
  makes the per-field reader map of section 4 the whole story.
* **An index shelf is overwritten without being versioned.** The checksum, info shelf and
  link shelf tools all call `_shelf_common.move_old()` before replacing a file.
  `_indexshelf_common.py` imports `_shelf_common` not at all, and `run_index_main` is the
  one driver that never calls `_common.set_log_dirs()`, so even if it did call `move_old()`
  there would be nowhere to copy to.
* **`_linkshelf_common.link_targets` takes a spec and reads no field of it**, and
  `read_links` takes a logger and logs nothing. Both are documented as accepted-and-unused.
  `link_targets` is also not itself any tool's `expand_target`: each link shelf tool defines
  a two-argument wrapper of the same name and names the wrapper, because `run_main` calls
  `expand_target` with the PdsFile and the path alone.
* **`validate_links()` sorts its list values in place before comparing and
  `validate_indexdict()` does not**, so a link recorded in a different order is not a
  disagreement and a row list in a different order is. The two are three files apart and
  neither says so about the other; both docstrings now do.
* **`_archives_common.validate_tuples()` compares two of the tuple's four fields.** The
  interior path is carried, is what the "Validated" line prints, and is in neither
  comparison: an entry agreeing on absolute path, byte count and modification time is
  accepted whatever its interior path is.
* **The modification-time tolerances differ deliberately and by one boundary.**
  `_shelf_common.modtimes_agree()` rejects a difference of one second exactly, because both
  its operands come from the same generator at microsecond precision;
  `validate_tuples()` accepts one, because one operand is a whole-second time recovered
  from a tarfile. The comment above `MODTIME_TOLERANCE` already said this and the two
  docstrings now say it from both ends.
* **`resolve_log_root()` exists because an empty string is not "unset" downstream.**
  `PdsFile.set_log_root()` stores `None` as "no root" but stores `''` as `'/'`, which would
  build every log path at the filesystem root. The parser's default for `--log` is `''`.
* **`next_version_dest()` has no upper bound.** The number is one past the highest the glob
  matched; above 999 the name grows a fourth digit that the same three-character glob no
  longer matches, so a directory holding 999 versions is handed the same `_v1000` path every
  time.
* **`_linkshelf_common.locate_nonlocal_link()` stops at the unit directory.** Its loop
  condition is `holdings in parts[:-3]`, and the three components after the holdings
  component are the category, the unit set and the unit, so the search covers the unit
  directory and everything below it and never reaches another unit.

## 10. Standing gates

### 10.1 Test id sets, full data, both modes

The command lines are `scripts/automated_tests/pdsfile_main_test.sh`'s, plus `--junitxml`.
Run from each tree in turn.

| mode | scope | base | head | ids only in base | ids only in head | outcome changed |
|---|---|---|---|---|---|---|
| `ns` | all seven directories | 1101 passed, 34 skipped (1135 ids) | 1101 passed, 34 skipped (1135 ids) | none | none | none |
| `s` | `tests/pds3file/ tests/rules/pds3/` only | 555 passed, 3 skipped (558 ids) | 555 passed, 3 skipped (558 ids) | none | none | none |

The per-test id sets are diffed, not the counts: the junit files are parsed and compared id
by id with the outcome attached, so a test that changed from passed to skipped would show
even though the totals would not. The `--mode s` scope is the script's own
(`scripts/automated_tests/pdsfile_main_test.sh:75`), not the full suite.

### 10.2 The code checks with no holdings

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        VENV=/seti/all_repos/rms-pdsfile/venv bash scripts/run-all-checks.sh -c -s

All checks passed, exit status 0: ruff, the indentation pass, pytest (**318 passed, 817
skipped**), pyroma, the API-freeze check and the clean-install gate. The script looks for a
`venv` in the repository root; `VENV` was set to the shared interpreter for the run instead
of making a symlink, which is what that variable is for (`scripts/run-all-checks.sh:136`).

### 10.3 The API freeze

    pytest tests/api

**26 passed.** The four frozen files are byte-identical to `80f5e52`, checked with
`git diff --quiet 80f5e52 -- <file>` on each of `tests/api/api_manifest.json`,
`tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py` and
`tests/api/test_api_freeze.py`.

**The two empty `__init__.py` files were the one freeze risk in this PR and they are
freeze-neutral.** The brief asked for this to be verified rather than assumed, because
adding a docstring makes a zero-byte module non-empty. It is: the manifest records
name-to-kind pairs and has no docstring field, an empty module and a module holding only a
docstring export the same names, and no manifest entry moved.

### 10.4 ruff

    ruff check src/pdsfile tests scripts                  # All checks passed
    ruff check .                                          # All checks passed
    ruff check --preview --select E111,E112,E113 .        # All checks passed
    ruff check . --config 'lint.per-file-ignores = {}'    # Found 2249 errors

`ruff format` was not run, in any form, per deviation (11).

### 10.5 The ratchet

| | base | head |
|---|---:|---:|
| `per-file-ignores` entries | 66 | 66 |
| code slots across those entries | 180 | 180 |
| findings with `per-file-ignores = {}` | 2,249 | 2,249 |
| `[project.scripts]` entries | 11 | 11 |

Nothing moved. No entry was retired and no entry grew. Every docstring line is wrapped at
90 columns, which is what keeps the third row from moving.

`bandit` and `vulture` are disabled and not installed. This PR claims nothing about them.

### 10.6 The record checkers, and the three citations this PR moved

    python critiques/pr-28/check_record_numbers.py

**15 stale at base and 15 at head, byte-identical outputs -- after a repair.** Before it,
head reported 16. The extra one was PR-28's line-count table, whose "head" column that
checker compares against the tree it runs in rather than against PR-28's head:
`show_opus_products.py` went from 199 lines to 249 when it gained a module docstring. The
row is re-derived, and the table now says in its own text which number that column is.
The other 15 are PR-28's own, invalidated by PR-28a's extraction; they arrived that way and
this PR neither caused nor repaired them.

    python critiques/pr-29/check_citations.py

**6 stale at base and 6 at head, byte-identical outputs -- after a repair.** Before it,
head reported 8. The two extra were deferred observation 164's citations of
`DICTIONARY_CACHE_LIMIT` at `pds3file/__init__.py:59` and `pds4file/__init__.py:48`, both
pushed down by this PR's docstrings to `:134` and `:116`. The entry and the checker's own
citation table are updated to match, which is the repair PR-29a made for the same reason.

The 6 that remain at both ends are deferred-observation citations into files outside the
checker's own scope list. Section 12 records that this number was handed as zero.

## 11. Review

Four rounds, each run by a fresh reviewer subagent with no context from this session or
from any other round. Records: `critiques/pr-30a/round-1.md` through `-4`.

| round | slice | surface | disproved | of those, in the corrections | code defects |
|---|---|---|---:|---:|---:|
| 1 | the six shared-core modules | 4 classes, 47 functions | 14 | — | 5 |
| 2 | the two subclasses and `tools/` | 2 classes, 35 functions | 14 | — | 3 |
| 3 | the same six, re-read | the same | 11 | **8** | 5 |
| 4 | the same four, re-read | the same | 11 | **7** | 4 |
| | | | **50** | **15 of 22** | **17** |

Rounds 1 and 2 include seven findings each that the reviewer classed as misleading rather
than false; all were acted on. Every finding was re-verified by the executor before it was
acted on, and six further defects were found by the executor between rounds and are
counted in neither column.

### The second reads found most of their yield in the first reads' corrections

**Fifteen of the second reads' 22 disproved claims are in sentences the first reads'
corrections wrote** -- eight of round 3's eleven and seven of round 4's. PR-29a measured
11 of 23 on this question, PR-29b 10 of 21 and PR-30 34 of 57; **as a share this is the
highest yet, and the trend the previous three records describe is unbroken.**

Both second-read briefs were given the correction commits by range, told which claims
those commits make, and told to treat every one as unproven until measured. That is what
PR-30's record recommended, and it is what produced the result: round 3's own tally
separates the two classes without being asked twice, and round 4 attributed every finding
with `git blame`.

**The sharpest of them made a sentence less true than the one it replaced.** Round 1
found that a link shelf triple's middle element is not a basename and produced 313
counterexamples out of 431,386 real triples; the correction said it is "the text the file
was written with ... it carries a directory wherever the link did". Round 3 then
instrumented `LinkInfo.remove_path()` and ran the real scan over 493 volumes: **1,412
calls truncate that text in place**, speculatively, while a repair is looked for, and
nothing restores it when none is found. So the element is the text as written for most
links and the basename for a link that carried a directory and reached the repair table,
and the word the correction removed -- "basename" -- was closer to the truth than what
replaced it. Deferred observation 290 holds the code defect behind it.

Four more of the same shape are worth naming because each reads as freshly checked:

* `run_main()`'s handler directory was corrected to "the directory of the target's own
  log file, so each target gets its own". The directory is the **bundle set's**, shared by
  every unit in it, and expanding a unit set into its units is exactly what that driver
  does -- so the contrast the correction drew with `run_index_main` does not separate the
  two drivers at all.
* `setup_run()` was said to attach the spec's handler factories "once at the log root".
  It attaches none when no log root is configured, and the drivers attach them once per
  **log file**, which is twice per target when one is.
* `new_pdsfile()` was said to build its result with `__new__` and never reach `__init__`.
  It runs `__init__` on every call, through `source = cls()`.
* The OPUS-type collision in `show_opus_products` was softened, on the strength of two
  scans that found none, to "nothing here prevents the collision; a scan of 6,674 files
  produced none". Round 4 found six files that do collide, and the rule that makes them is
  two lines apart in `VG_28xx.py`: two categories differing only in rank both carry the
  type `vgrss_occ_inv0_2`.

### What the angles returned

* **Relationship claims** were the largest category in all four rounds, as they were in
  all four earlier docstring PRs. The ones that failed were almost never the ones a
  careful reading would catch: which of two directories a driver builds handlers in, which
  of five tasks writes a file, whether a mutation is undone. Section 9 lists the contracts
  that had to be measured to get right in the first place.
* **Exceptions from something other than `raise`** produced two whole contracts that were
  missing: `setup_run()` raises `ValueError` when a logger of the spec's logname already
  exists, which round 3 demonstrated in one process and which means two tools of a kind
  cannot share one; and both `run_main()` and `run_selection_main()` can raise
  `ValueError` or `OSError` out of path resolution before any logging is open. It also
  produced the `EOFError` that escapes `load_indexdict()` unlogged, and the `IndexError`
  that ends a `show_opus_products` run on four real holdings paths.
* **Inert or unread parameters** held up: `read_links`'s logger and `link_targets`'s spec
  are both accepted and unused, confirmed by AST over all 22 functions in the six modules
  that take a logger. What did not hold up was the reverse direction -- `pdslogger`
  classifies by level value, not by level name, so a dot-underscore file gives a run a
  nonzero exit status exactly as a backup file does, and the contrast a correction drew
  between them was false.
* **Arithmetic and boundaries** were mostly confirmed rather than broken, which is the one
  angle that behaved differently here: the modification-time tolerances, the tenth-of-a-day
  threshold, the `_v###` collision above 999, the `../` arithmetic round-tripped through
  `load_links`, and the walk that stops at the unit directory all measured as documented.
  The counts did not: nineteen aliases rather than a dozen, four tasks that write rather
  than three, five spec fields differing rather than one, three rule tables without a
  `PdsFile` counterpart rather than two.

### One round read this PR's own checker, and it was worth it

Deferred entry 275 asks that a PR shipping a checker point one round at the checker.
Round 3 did, found the map it derives correct, and then answered the question that
matters -- can it pass while the prose is wrong -- with five ways it can. Two are closed
here: a documented reader must now carry a module qualifier, since this tree has
same-named functions in several modules, and for a field with five or fewer readers every
one must be named rather than one per module. The other three are written into the
script's own docstring rather than left to be found, and the first of them is the honest
limit of the whole idea: **the gate checks attribution and never assertion**, so the two
`handler_factories` defects above sat inside an entry it scored as fully correct
throughout.

### The freeze rule was followed once and broken once

Deferred entry 239 asks that the previous round's corrections be committed, and the tree
left alone, before the round that reviews them is launched. **Rounds 1 and 2 were launched
against `2fd40c4` and the tree then moved under them**, reaching `bd5b192` eight commits
later before round 1 finished. Round 1 noticed, read the frozen text through `git show`,
re-checked its findings against the moved tree and reported the drift at the top of its
own record, so the experiment survived -- but two of its fourteen findings had already
been fixed by the executor independently, which makes its yield harder to attribute.
Rounds 3 and 4 were launched against a frozen `e8af080` with nothing committed to `src/`
until both returned, and they are the two rounds whose numbers this section relies on.
Deferred observation 289 records it.

## 12. Numbers this PR was handed that did not reproduce

Recorded because every number was re-derived rather than inherited.

* **`ToolSpec.index_ext` was handed as "declared and read nowhere", with the instruction
  not to document it as if it drove behavior. It is read**, at
  `_indexshelf_common.index_targets()`, where it is the extension a metadata directory is
  globbed for and a command-line file is checked against. It is the one field of the
  twenty-one that is read in exactly one place, and it acts on two of the ten tools. The
  instruction was right about the risk and wrong about this field: what is true of
  `index_ext` is that all ten specs set it and eight tools never reach a line that reads
  it. Section 4's checker reports **S3: 0** -- no field is read nowhere.

* **The two subclass `__init__.py` files do not carry `N801`, `N999` or `N802`.** They
  were handed as carrying "`N801`/`N999`/`N802`/`A002`/`F401`" on account of frozen
  names. Measured with the ratchet emptied over just those two files, the codes are
  `F401` ×31, `RUF012` ×4, `I001` ×4 and `A002` ×2, and `pyproject.toml`'s two entries
  list exactly those four for pds3file and three of them for pds4file. `N` is in the
  selected rule set, so the absence is a measurement and not a gap in coverage:
  `Pds3File` is CapWords, `pds3file` is lower case and every method is snake_case. The
  underlying instruction stands -- the names are frozen and no docstring suggests a
  rename -- but the reason given for it does not.

* **The scope table omitted the classes**, exactly as PR-30's did. Six are in scope:
  `ToolSpec`, `VersionedFile`, `RunResult` and `LinkInfo`, all documented at base, and
  `Pds3File` and `Pds4File`, neither documented. The handed count of 82 functions and
  26 undocumented ones is right; what it left out is that documenting a module means
  documenting its classes too, and that `doc_python.mdc` section 4 requires it. The base
  `M1` count of 38 is the arithmetic check: 10 modules + 2 classes + 26 functions.

* **`critiques/pr-29/check_citations.py` reports 6 stale at `80f5e52`, not 0.**
  PR-30's record section 8.6 says "0 stale at base and 0 at head, with no repair needed".
  Run at `80f5e52`, which is PR-30's merge commit, it reports six, all of them of the
  form "[deferred] cites `<file>`, which no entry covers" for `_opus.py`,
  `COVIMS_0xxx.py` twice, `uranus_occs_earthbased.py`, `COCIRS_xxxx.py` and
  `_properties.py`. They are outside this PR's scope and are not repaired here; what is
  recorded is that the number handed forward as zero is six, so a later PR comparing
  against zero would read its own six as a regression.

Everything else reproduced exactly:

* the ten-file scope and its **3,177 lines**, 82 functions, 26 undocumented, 163
  parameters, and none of the ten with a module docstring;
* the `ns` **1135** and `s` **558** baselines, id for id, at base and at head;
* all four ratchet numbers, **66 / 180 / 2,249 / 11**;
* the four checker reproductions -- PR-29's **276**, PR-29a's **249**, PR-29b's **73**
  and PR-30's **78** at `c4811d8` and **0** at `80f5e52` -- and PR-30's
  `check_rule_tables.py` at **0 findings over 36 files**;
* `critiques/pr-28/check_record_numbers.py` at **15 stale**, which is what PR-28's and
  PR-29a's records both say;
* `critiques/deferred-observations.md` continuing from **276**: the last entry at
  `80f5e52` is 275.
