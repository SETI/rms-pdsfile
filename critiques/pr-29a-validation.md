# PR-29a validation — Google-style docstrings, the private modules

Base: `9466dbc`. Branch: `pr-29a-docstrings-mixins`. Base branch: `rewrite`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), from the tree being measured,
with `PYTHONPATH=$PWD/src`. Where holdings are needed the environment carried
`PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree
is a second worktree at the same commit, so "base" numbers were measured, not recalled.

Nothing here is inherited. Every number carries the command that produced it, and
section 11 lists the numbers this PR was handed that did **not** reproduce.

## 1. Scope

Nine files, and only these:

| file | lines at base | at head | funcs without a docstring / total | parameters |
|---|---:|---:|---:|---:|
| `src/pdsfile/_sorting.py` | 526 | 864 | 14 / 25 | 49 |
| `src/pdsfile/_preload.py` | 583 | 777 | 6 / 10 | 12 |
| `src/pdsfile/_local_fs.py` | 434 | 565 | 0 / 5 | 7 |
| `src/pdsfile/_associations.py` | 373 | 517 | 2 / 5 | 9 |
| `src/pdsfile/_shelves.py` | 353 | 560 | 0 / 10 | 12 |
| `src/pdsfile/_derived_paths.py` | 350 | 564 | 0 / 14 | 18 |
| `src/pdsfile/_index_rows.py` | 330 | 456 | 1 / 6 | 6 |
| `src/pdsfile/_opus.py` | 304 | 402 | 0 / 3 | 3 |
| `src/pdsfile/_path_utils.py` | 221 | 418 | 5 / 10 | 13 |

    python critiques/pr-29/measure.py src/pdsfile/_sorting.py src/pdsfile/_preload.py \
        src/pdsfile/_local_fs.py src/pdsfile/_associations.py src/pdsfile/_shelves.py \
        src/pdsfile/_derived_paths.py src/pdsfile/_index_rows.py src/pdsfile/_opus.py \
        src/pdsfile/_path_utils.py

3,474 lines at base, 88 functions, 8 classes, 129 parameters excluding `self` and `cls`.
**28 of the 88 functions had no docstring at all and not one of the nine modules had
one.** All 8 classes had one. Of the 68 docstrings that existed, 67 carried no Google
section of any kind; the one that did used `Arguments:`.

`src/pdsfile/_properties.py` is **not** in this PR and its absence is section 10.

## 2. What changed

Docstrings only. Nine module docstrings (all new), eight class docstrings (all
rewritten) and 88 function docstrings (28 new, 60 rewritten) — 105 in all, carrying 139
parameter descriptions. Section 3 proves that no executable statement moved.

Seventeen comment lines were deleted and none was added or reworded; section 3.2
enumerates them.

`critiques/pr-29a/` carries the three scripts this record cites that PR-29 did not
already have: `derive_state_contract.py`, `measure_module_lines.py` and
`build_docs_probe.py`. Section 4.1 records the two changes made to PR-29's own checkers.

## 3. Proof that the change is docstrings only

### 3.1 The AST hashes

`critiques/pr-29/strip_docstrings.py` parses a module, deletes the docstring node of
every module, class and function, and hashes `ast.dump` of what is left with
`include_attributes=False`, so line and column shifts do not register.

    python critiques/pr-29/strip_docstrings.py src/pdsfile/_sorting.py ...

| file | base | head |
|---|---|---|
| `_sorting.py` | `92ee840e7da3c67d` | `92ee840e7da3c67d` |
| `_preload.py` | `8c566381bad62049` | `8c566381bad62049` |
| `_local_fs.py` | `e400117465c687b2` | `e400117465c687b2` |
| `_associations.py` | `cc35f688d5ef5edb` | `cc35f688d5ef5edb` |
| `_shelves.py` | `73ae6ede256a2224` | `73ae6ede256a2224` |
| `_derived_paths.py` | `63340eaa9ceec83b` | `63340eaa9ceec83b` |
| `_index_rows.py` | `a30e0f8bdc6e278d` | `a30e0f8bdc6e278d` |
| `_opus.py` | `2e25f1d9e84e1482` | `2e25f1d9e84e1482` |
| `_path_utils.py` | `d927dd549cf1ab76` | `d927dd549cf1ab76` |

All nine pairs match. PR-29 established that this check is not vacuous, with five
mutations of a documented file; the same script is used here unchanged.

Section 6 also edits `.cursor/rules/pdsfile_overrides.mdc`, which is prose and which the
AST check does not cover. Its diff is read directly.

### 3.2 The comment enumeration, which the AST cannot see

    python critiques/pr-29/check_comments.py <base tree> <head tree> _sorting.py ...

| file | comment lines at base | at head | removed | added |
|---|---:|---:|---:|---:|
| `_sorting.py` | 62 | 60 | 2 | 0 |
| `_preload.py` | 133 | 131 | 2 | 0 |
| `_local_fs.py` | 67 | 65 | 2 | 0 |
| `_associations.py` | 54 | 52 | 2 | 0 |
| `_shelves.py` | 40 | 38 | 2 | 0 |
| `_derived_paths.py` | 22 | 20 | 2 | 0 |
| `_index_rows.py` | 40 | 39 | 1 | 0 |
| `_opus.py` | 43 | 41 | 2 | 0 |
| `_path_utils.py` | 31 | 29 | 2 | 0 |

**Seventeen lines removed in total, and all seventeen are the same thing:** the one or
two lines of description inside each file's banner comment, which the rule requires be a
module docstring and which therefore could not stay where they were. Every file's banner
rules and its `# pdsfile/<name>.py` line are untouched, and every fact the removed
description carried is in the module docstring that replaced it. The exact text, by file:

    _sorting.py         # Splitting, sorting, and bulk conversion between PdsFile objects, abspaths, logical
                        # paths and basenames
    _preload.py         # Preload management: the cache the PdsFile classes share, the lifetimes it assigns,
                        # and the traversal that fills it from one or more holdings directories
    _local_fs.py        # Local implementations of basic filesystem operations, which consult info shelf
                        # files instead of the file system when SHELVES_ONLY is set
    _associations.py    # The category-crossing lookup layer: given one PdsFile, the files associated with it in
                        # another category of the holdings tree
    _shelves.py         # Shelf file support: locating a shelf file and the key into it, opening and
                        # caching shelf files, and looking up the values they hold
    _derived_paths.py   # Paths a PdsFile derives from its own path: the checksum file that covers it, the
                        # archive file that contains it, and the log files written about it
    _index_rows.py      # Support for PdsFile objects that represent one selected row of an index table
    _opus.py            # OPUS support: the constructors that resolve an OPUS ID or a file specification, and the
                        # product dictionary OPUS consumes
    _path_utils.py      # Module-level path helpers and small support functions shared by the PdsFile
                        # classes

Every other comment in all nine files is byte-identical to base and sits under the same
preceding line of code, including all 131 that remain in `_preload.py`.

## 4. The mechanical docstring checks

    python critiques/pr-29/check_docstrings.py src/pdsfile/_sorting.py ...

| code | check | base | head |
|---|---|---:|---:|
| P1 | a `Parameters:` entry that is not a parameter of the signature | 0 | 0 |
| P2 | a parameter that does not appear in `Parameters:` exactly once | 94 | 0 |
| P3 | a section spelled `Args:`, `Arguments:`, `Keyword arguments:` or `Input:` | 44 | 0 |
| R1 | `Returns:` present without a value return, or absent with one | 54 | 0 |
| E1 | a `Raises:` entry the body neither raises nor attributes to a call it makes | 0 | 0 |
| E2 | a class raised in the body that `Raises:` does not name | 18 | 0 |
| D1 | a docstring line wider than 90 columns | 2 | 0 |
| U1 | a unicode smart quote, dash or arrow anywhere in the file | 0 | 0 |
| M1 | a module, class or function with no docstring | 37 | 0 |
| | **total** | **249** | **0** |

M1's 37 is 9 module docstrings plus 28 function docstrings; all 8 classes had one.

### 4.1 PR-29's checker has been extended, and this is what changed

Two of the five scripts in `critiques/pr-29/` are edited here. Both changes are
corrections the private modules expose and neither was made to let this code pass — over
the nine modules at base they take the findings **up** from 245 to 249, and over all
fifteen modules under `src/pdsfile/` from 318 to 322.

* **`check_comments.py` takes the module basenames as arguments**, defaulting to the
  five it was written for. Nothing else changed; it is the same comparison.
* **A module-level function's `cls` is a parameter.** The checker stripped `self` and
  `cls` from every signature. On a method that is right: the interpreter supplies the
  receiver and a caller passes nothing. On a module-level function it is wrong, and nine
  such functions in `_preload.py` and `_path_utils.py` take a `cls` argument that the
  caller must hand in. P2 now requires those be documented and P1 no longer rejects them.
  `cls` on a method is still a P1.
* **`raise <local>` names a variable, not a class.** `_index_rows.get_indexshelf` catches
  an exception into `saved_e` and re-raises it, which E2 reported as "body raises
  saved_e but `Raises:` does not name it" — a finding no docstring can satisfy. Names the
  body binds are now excluded. `raise SomeClass(...)` is unaffected, and `bound_names`
  stops at a nested definition exactly as `raised_names` does, so a name bound only
  inside a closure cannot mask a class of the same spelling raised outside it.

**The five modules of PR-29 are unaffected.** Run against their state before PR-29
documented them, the amended checker reports **276** findings with the identical
per-code breakdown (P2 139, R1 75, P3 26, M1 20, E2 16), and **0** against their current
state. Those are the two numbers `critiques/pr-29-validation.md` section 4 records, so
the two records do not disagree.

**Each new behavior fires on its own mutation and none fires on the control.**

| mutation | finding |
|---|---|
| `repair_case`'s `cls` entry deleted (a module-level function) | P2: parameter "cls" appears 0 times |
| `cls` added to a method's `Parameters:` | P1: "cls" is not a parameter of this signature |
| `raise saved_e` replaced by `raise RuntimeError(saved_e)` | E2: body raises RuntimeError but `Raises:` does not name it |
| unmutated copies of the same two files | 0 findings |

### 4.2 Two conventions this record states rather than assumes

**Types in `Parameters:` entries are written only where the code proves them**, as in
PR-29. Section 9 lists every omission as PR-35's queue: 25 of the 139 entries.

**An exception raised by a mechanism other than a `raise` statement gets a `Raises:`
entry when the mechanism is one E1 can verify, and prose otherwise.** This is PR-29's
widened rule, used unchanged.

## 5. The state-contract derivation — deferred observation 54

Each mixin class opens with a paragraph naming every `PdsFile` attribute, property and
sibling-mixin method its bodies reach. Entry 54 records that this is the only part of a
mixin module nothing checks, and that PR-19 found `_IndexRowsMixin`'s version wrong in
three consecutive rounds. `critiques/pr-29a/derive_state_contract.py` derives it from the
AST and compares it against the docstring in both directions.

    python critiques/pr-29a/derive_state_contract.py src/pdsfile src/pdsfile/_*.py

### 5.1 What the derivation had to get right

**The receiver decides, not the name.** `split` is a `PdsFile` property
(`_properties.py:263`) and also `str.split`; `copy` is a `PdsFile` method
(`pdsfile.py:872`) and also `list.copy`; `abspath`, `basename`, `exists` and `isdir` are
`PdsFile` members and also `os.path` functions. There are **19** `.split(` calls in
these nine modules. Matching on the attribute name would score every one of them as a
`PdsFile` read. Resolving the root of each attribute chain instead scores **none** of
them, while `self.split` written directly still counts.

**A module-level function a mixin calls by name is not an attribute read.** `_sorting.py`
calls `sort_dirs_first` and three siblings, which are defined in its own module body.
Those are subtracted rather than reported as contract entries the docstring failed to
claim.

**A module of free functions carries its contract in the module docstring.**
`_path_utils.py` has no class, so a class-docstring-only check skipped it entirely.

### 5.2 The controls

`_properties.py` and `_opus.py` are read-only controls: their contracts measure clean at
base, so a derivation that reports findings on them is wrong.

    _properties.py: 114 reached (114 read, 41 written), 94 listed    0 findings
    _opus.py:        26 reached ( 26 read,  0 written), 20 listed    0 findings

### 5.3 The table, measured at base

| module | reached | listed in a contract block | MISSING | UNCLAIMED | STRANDED |
|---|---:|---:|---:|---:|---:|
| `_associations.py` | 34 | 34 | 0 | 0 | 0 |
| `_derived_paths.py` | 22 | 0 | **18** | 0 | 0 |
| `_index_rows.py` | 24 | 20 | 0 | 0 | 0 |
| `_local_fs.py` | 11 | 0 | **3** | 0 | 0 |
| `_opus.py` | 26 | 20 | 0 | 0 | 0 |
| `_path_utils.py` | 9 | — | — | — | — |
| `_preload.py` | 26 | 21 | **1** | 0 | 0 |
| `_shelves.py` | 23 | 0 | **13** | 0 | 0 |
| `_sorting.py` | 22 | 15 | 0 | 0 | 0 |

`reached` is derived from the code, which this PR does not change, so it is the same
number at base and at head. It is the union of reads and writes, and so is smaller than
their sum wherever a name is both. `listed` counts only the names enumerated in a
contract block; a name the docstring mentions in running prose satisfies MISSING without
appearing here, which is why `_index_rows.py` reaches 24 and lists 20 with nothing
missing — the other four are named in sentences.

`_path_utils.py` has no row because at base there was nothing to compare against: it has
no class, and no module docstring either, so the derivation reports that and stops. Its
nine reaches all arrive through the `cls` argument its functions take.

**Four of the nine modules had no state-contract paragraph at all** at base:
`_derived_paths.py`, `_local_fs.py`, `_shelves.py` and `_path_utils.py`. That is what the
MISSING column counts for the first three, and it is entry 54's prediction holding. The
run reports 39 findings over the ten modules at base: 35 MISSING, three VACUOUS and the
one module with no docstring to read.

### 5.4 Is it fit to be a standing gate

Yes, with the caveats below. All four report kinds fire on a deliberate mutation and the
unmutated control reports nothing:

| mutation | finding |
|---|---|
| `label_basename` scrubbed from `_AssociationsMixin`'s docstring | MISSING label_basename (line 301) |
| `LOCAL_PRELOADED` added to that docstring's class-attributes line | UNCLAIMED LOCAL_PRELOADED |
| a synthetic `self.no_such_slot_xyz` | STRANDED, and MISSING |
| a synthetic `self.split` written directly | MISSING split |
| a synthetic `self.abspath.split('/')`, and `.copy()` on the result | not reported |
| a synthetic module reaching only names its docstring lists | 0 findings |

Three caveats, stated because a gate that is silently half-running is worse than none:

* **The UNCLAIMED direction reads only enumerated blocks**, which the script finds by
  looking for a paragraph ending in a colon that contains `not in scope` or
  `sibling mixin`. A docstring that writes its block with a different lead-in would pass
  UNCLAIMED vacuously. The script therefore reports **VACUOUS** when a module reaches
  PdsFile-side names and has no block at all, rather than passing it.
* **The universe is a name filter, not a resolution.** An attribute whose receiver cannot
  be resolved counts if its name is one of the 347 that a PdsFile-side class body
  defines. That is a heuristic; it is why the universe stops at the classes a mixin can
  reach through `self` rather than including the rule modules, where a name as ordinary
  as `name` would let anything through.
* **It is not wired into any gate here.** `run-all-checks.sh` does not run it. Whether it
  becomes a gate, and over which files, is a decision for whoever wires it up.

## 6. Module length is two limits

`.cursor/rules/pdsfile_overrides.mdc` deviation (3) is rewritten. The rule and its
reasoning are in that file; the measurements behind it are here.

    python critiques/pr-29a/measure_module_lines.py $(find src -name '*.py')

Code lines are total lines minus the lines the module, class and function docstrings
occupy, with each span taken from its constant node's `lineno` through `end_lineno` so
that a string which is not a docstring is not deducted. `total` agrees with `wc -l` on
every file checked.

Measured at `9466dbc`. These four files, and only these, are over a limit:

| file | total | docstring | code | over |
|---|---:|---:|---:|---|
| `pdsfile.py` | 2,435 | 781 | 1,654 | **both** |
| `_properties.py` | 1,689 | 297 | 1,392 | code |
| `holdings_maintenance/pds3/pdsdependency.py` | 1,165 | 30 | 1,135 | code |
| `pds3file/rules/VG_28xx.py` | 1,019 | 0 | 1,019 | code |

And the three the old single limit would also have caught, which now pass:

| file | total | docstring | code | verdict |
|---|---:|---:|---:|---|
| `pdscache.py` | 1,914 | 977 | 937 | passes both |
| `pdsviewable.py` | 986 | 458 | 528 | passes both |
| `holdings_maintenance/pds3/re_validate.py` | 987 | 119 | 868 | passes both |

Four consequences, and the fourth is the one that matters most:

1. **`pdscache.py`'s waiver retires.** It passes both limits, so its line comes off the
   enumerated list. The list means less the longer it gets.
2. **`pdsfile.py` exceeds both and its split is deferred** (owner, 2026-08-07). Its
   waiver stands, and the measurement says plainly that this is a code problem: the file
   is one class occupying 2,247 of its 2,435 lines (`pdsfile.py:174`–`:2420`), 37 methods
   holding 1,920 lines between them, against a module docstring of 87. There is no prose
   to relocate. Deferred observation 199.
3. **`_properties.py` keeps its waiver** on code lines, per plan §8 settled decision 3.
4. **`pdsdependency.py` is over on code alone**, with 30 lines of docstring against
   1,135 of code, so the new measure shows it is a structural problem rather than a
   documentation artifact. Entry 66 is amended, not resolved.

**No gate enforces module length.** `run-all-checks.sh` has no such check and neither
does CI, and this PR does not add one. That absence is deliberate and is stated in the
rule so it does not read as an oversight.

The nine modules this PR documents all pass both limits with room to spare. The largest
is `_sorting.py` at 864 total and **397 code**; the second largest is `_preload.py` at
777 total and 475 code.

## 7. The Sphinx build

`docs/` does not exist and is not created here; PR-31 owns it. A throwaway tree is built
elsewhere instead, reproducibly:

    python critiques/pr-29a/build_docs_probe.py <tree>/src <build dir>

The configuration is `critiques/pr-29/sphinx-conf.py` **unchanged**, with `nitpick_ignore`
empty and nothing mocked. What is extended is the page list: the nine private modules
join PR-29's four. `pdsfile.pdsfile` has to be among them, or a `PdsFile` written in a
`Parameters:` type slot resolves to nothing and fails `-n` — a property of a partial page
set rather than of the prose. `_properties.py` is left out; its docstrings are not
revised here and including it adds 21 warnings that belong to that module.

| | base | head |
|---|---:|---:|
| `-n` warnings | 173 | **0** |
| `-W` | 35 warnings, build fails | **build succeeded** |

The rendered pages carry the new prose, so the build is not succeeding over an empty
tree: `api.html` holds 19 matches for "shelf file" and the exact sentence "Return the
shelf dictionary mapping each row key of an index to its rows".

## 8. Standing gates

### 8.1 Test id sets, full data, both modes

The command lines are `scripts/automated_tests/pdsfile_main_test.sh`'s, plus `--junitxml`.
Run from each tree in turn.

| mode | scope | base | head | ids only in base | ids only in head | outcome changed |
|---|---|---|---|---|---|---|
| `ns` | all seven directories | 1101 passed, 34 skipped (1135 ids) | 1101 passed, 34 skipped (1135 ids) | none | none | none |
| `s` | `tests/pds3file/ tests/rules/pds3/` only | 555 passed, 3 skipped (558 ids) | 555 passed, 3 skipped (558 ids) | none | none | none |

The per-test id sets were diffed, not the counts: the two junit files were parsed and
compared id by id with the outcome attached, so a test that changed from passed to skipped
would show even though the totals would not. The `--mode s` scope is the script's own
(`scripts/automated_tests/pdsfile_main_test.sh:75`), not the full suite.

### 8.2 The code checks with no holdings

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        bash scripts/run-all-checks.sh -c -s

All checks passed: ruff, the indentation pass, pytest (318 passed, 817 skipped), pyroma
10/10, the API-freeze check and the clean-install gate. The script needs a `venv` in the
repository root; a symlink to the shared interpreter was made for the run and removed
afterwards. It is gitignored and is not part of this PR.

### 8.3 The API freeze

    pytest tests/api

26 passed. The four frozen files are byte-identical to `9466dbc`, checked with
`git diff --quiet 9466dbc -- <file>` on each. This PR turns nine `#` header comments into
module docstrings and adds `__doc__` to 28 functions, which is freeze-neutral: the
manifest records name-to-kind pairs and has no docstring field.

### 8.4 ruff

    ruff check .                                          # All checks passed
    ruff check --preview --select E111,E112,E113 .        # All checks passed
    ruff check . --config 'lint.per-file-ignores = {}'    # Found 2249 errors

Two findings were fixed inside this PR rather than shipped, both in checker scripts
rather than in `src/`, and both therefore invisible to the configured gate, which covers
`src/pdsfile tests scripts` only: `SIM102` in `check_docstrings.py` and `SIM114` in
`derive_state_contract.py`. The bare `ruff check .` is clean at head.

### 8.5 The ratchet

| | base | head |
|---|---:|---:|
| `per-file-ignores` entries | 66 | 66 |
| code slots across those entries | 180 | 180 |
| findings with `per-file-ignores = {}` | 2,249 | 2,249 |
| `[project.scripts]` entries | 11 | 11 |

Nothing moved. No entry was retired and no entry grew.

`bandit` and `vulture` are disabled and not installed. This PR claims nothing about them.

### 8.6 The record checkers

    python critiques/pr-28/check_record_numbers.py

15 stale at base and 15 at head, byte-identical outputs. Those are PR-28's own numbers,
invalidated by PR-28a's extraction; they arrived that way and this PR neither caused nor
repaired them.

    python critiques/pr-29/check_citations.py

**0 stale at head — but it took a repair.** It reports 0 at base and reported **7** at
head before the repair, all of them citations into `_preload.py` whose lines this PR's
docstrings pushed down: deferred entries 163, 164, 167, 189 and 191 between them cite
`_preload.py` at seven places. Each was re-derived against the current file and the
checker's own table updated to match. This is the one way a docstring-only PR can break
something, and the checker caught it.

## 9. Type omissions — PR-35's queue

Twenty-five of the 139 `Parameters:` entries are written without a type, because the code
does not prove one. 114 carry a type. The pattern is PR-29's: a type is written where the
body constrains the parameter to one thing, and omitted where it is stored rather than
examined, where it is a class object, or where the body branches on its type.

| parameter | where | what the code shows |
|---|---|---|
| `cls` | `cache_lifetime_for_class`, `is_preloading`, `pause_caching`, `resume_caching`, `_preload_dir`, `logical_path_from_abspath`, `_clean_glob`, `repair_case`, `abspath_for_logical_path`, `selected_path_from_path` | a PdsFile subclass, passed as an ordinary argument because these are module-level functions and one closure; class attributes and classmethods are read off it |
| `arg` | `cache_lifetime_for_class`, `_PreloadMixin.cache_lifetime` | tested with `isinstance` against `str` and against the class, so anything; each branch is what constrains it |
| `info_first` | `sort_basenames`, `sort_sibnames`, `sort_siblings` | stored unexamined and then compared; False, True, None and an int above 1 are all meaningful |
| `holdings_list` | `get_permanent_values`, `preload` | a string or a sequence of them; `preload` normalizes a lone string into a list |
| `icon_url` | `preload` | tested for truth, then passed through to the icon loader |
| `pdsdir` | `_preload_dir` | a PdsFile; six attributes are read off it, but nothing constrains it to a type this module names |
| `rank` | `associated_parallel` | compared against the version ranks, which are ints, and passed to `all_versions().get()`; None is a distinct case |
| `pdsf` | `_cache_and_return` | a PdsFile or None; the None case is what the function exists to handle |
| `target` | `_log_path_for` | a callable returning a path, invoked once |
| `voltypes` | `construct_category_list` | iterated four times and each name concatenated, so a re-iterable sequence of strings; a one-shot iterator fails (entry 207) |
| `path` | `_clean_abspath` | joined and split as text, so anything with a string form |
| `size` | `formatted_file_size` | divided and compared, so any real number |

`PdsFile` is named as a type in prose rather than in a type slot wherever the module does
not import it, for the same reason PR-29 gave: a stub that declared the dependency would
create one the code does not have.

## 10. The PR-29a / PR-29b split

The plan's PR-29a covered all ten `_*.py` modules. It is split here. This PR takes nine
of them; `_properties.py` is PR-29b.

`_properties.py` holds **68 functions** on its own — more than `pdscache.py` carried in
PR-29, which needed two adversarial reads of that one file and still found about twenty
defects on the second. The reason is review load and it is the same reason PR-29 was
split from PR-29a: there is no mechanical gate for semantic accuracy, so every docstring
has to be read against the code, and the review budget is what is scarce.

PR-29b therefore carries `_properties.py` **together with the second reads of
`pdsfile.py` and `pdsviewable.py`** that PR-29 recommended and could not fit inside its
round cap. `_properties.py` is also the only `_*.py` module left without a module
docstring, so deferred entry 80 stays open until PR-29b lands.

## 11. Numbers this PR was handed that did not reproduce

Recorded because every number was re-derived rather than inherited.

* **The state-contract table.** It arrived flagged as an upper bound pending two fixes, and
  it was right to be. Once the receiver is resolved rather than the name matched, and once
  module-level functions are subtracted, every column moves:

  | module | handed: derived / named / missing / stale | measured: reached / listed / MISSING / UNCLAIMED |
  |---|---|---|
  | `_associations.py` | 34 / 37 / 1 / 0 | 34 / 34 / 0 / 0 |
  | `_derived_paths.py` | 21 / 8 / 17 / 0 | 22 / 0 / **18** / 0 |
  | `_index_rows.py` | 23 / 25 / 0 / 0 | 24 / 20 / 0 / 0 |
  | `_local_fs.py` | 12 / 7 / 5 / 0 | 11 / 0 / **3** / 0 |
  | `_opus.py` | 22 / 23 / 0 / 0 | 26 / 20 / 0 / 0 |
  | `_preload.py` | 27 / 30 / 3 / 1 | 26 / 21 / **1** / 0 |
  | `_shelves.py` | 25 / 10 / 15 / 0 | 23 / 0 / **13** / 0 |
  | `_sorting.py` | 20 / 36 / 2 / 4 | 22 / 15 / 0 / 0 |

  The two flagged as upper bounds land at 18 and 13 rather than 17 and 15. Every "stale"
  goes to zero: `_sorting.py`'s four were module-level functions the module defines itself,
  and `_preload.py`'s one went the same way. The "named" column is not comparable to
  `listed`, which counts only the enumerated block; the MISSING column is the one that
  tests the same thing in both, and it is what moved.

  The prose that came with the table said `_IndexRowsMixin` derives "22 reads + 2 writes".
  Measured, it is 23 reads and 2 writes, 24 distinct names. Its own table said 23. Neither
  figure reproduces, and the claim they were supporting -- that the module's contract
  paragraph is complete in both directions -- does, at 0 MISSING and 0 UNCLAIMED.

* **`check_record_numbers.py` is at `critiques/pr-28/`, not `critiques/pr-29/`.** PR-29's
  own record cites it correctly; the instruction to reuse it named the wrong directory.

* **`pdsfile_overrides.mdc` deviation (4)'s line numbers**, which turned out to have been
  stale at `9466dbc` in five of eleven rows, one of them by a count rather than a line.
  Deferred observation 200 carries the measurement.

Everything else reproduced exactly: the nine-file scope table and its 3,474 lines, 88
functions, 129 parameters and 28 undocumented functions; all six rows of the two-limit
table; `pdsfile.py`'s 2,247-line class, 37 methods, 1,920 lines of method definitions and
87-line module docstring; the `ns` 1135 and `s` 558 baselines; all four ratchet numbers;
and the handover measurement of 88 of 88 functions documented with 71 `Parameters:`
sections.
