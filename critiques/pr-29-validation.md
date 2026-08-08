# PR-29 validation — Google-style docstrings, the public modules

Base: `4edc7d1`. Branch: `pr-29-docstrings-public`. Base branch: `rewrite`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), from the tree being measured,
with `PYTHONPATH=$PWD/src`. Where holdings are needed the environment carried
`PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree
is a second worktree at the same commit, so "base" numbers were measured, not recalled.

Nothing in this record is inherited. Every number carries the command that produced it,
and section 9 lists the numbers this PR was handed that did **not** reproduce.

## 1. Scope

Five files, and only these:

| file | lines at base | at head | module docstring at base | classes without one | functions without one / total | parameters |
|---|---:|---:|---|---:|---:|---:|
| `src/pdsfile/pdsfile.py` | 1,949 | 2,435 | present | 1 | 2 / 37 | 56 |
| `src/pdsfile/pdscache.py` | 1,047 | 1,782 | absent | 3 | 2 / 60 | 58 |
| `src/pdsfile/pdsviewable.py` | 587 | 986 | absent | 0 | 8 / 26 | 36 |
| `src/pdsfile/__init__.py` | 15 | 39 | absent | 0 | 0 / 0 | 0 |
| `src/pdsfile/preload_and_cache.py` | 16 | 48 | absent | 0 | 0 / 0 | 0 |

Measured with `wc -l` and with a walk of each file's AST; the four counted columns are
at base. Totals: 123 functions,
6 classes, 5 modules, 150 parameters excluding `self` and `cls`.

`src/pdsfile/_version.py` is **not** in the table and is **not** an omission: it is a
`setuptools_scm` build artifact, gitignored at `.gitignore:170`, and is not a tracked
file. It was not touched.

The ten `_*.py` mixin and extracted modules are **not** in this PR. Measured at base,
they hold 156 functions and 131 parameters, and not one of them has a module docstring.
They are PR-29a; section 8 records the split and its reason.

### 1.1 What "documented" meant at base

Over all of `src/pdsfile/*.py` at base, 251 docstrings exist. **None** uses
`Parameters:`, **none** uses `Args:`, and 2 use `Input:` -- both of them the constructors
in `pdscache.py`. Under a strict match on the Google section names
(`Parameters:|Args:|Arguments:|Returns:|Return:|Yields:|Raises:|Input:`), 248 of the 251
have no section of any kind; the three that do are the two `Input:` constructors and
`_derived_paths._log_path_for`, which uses `Arguments:`. Of the 114 docstrings in the
five in-scope files, 112 have no section and the other two are those constructors.

    python critiques/pr-29/measure.py src/pdsfile/*.py
    python critiques/pr-29/measure.py src/pdsfile/pdsfile.py src/pdsfile/pdscache.py \
        src/pdsfile/pdsviewable.py src/pdsfile/__init__.py \
        src/pdsfile/preload_and_cache.py

So this was not a reformat. Nearly every parameter in the package was undocumented, and
this PR writes 150 parameter descriptions from the code.

## 2. What changed

Docstrings only. Five module docstrings (four new, one rewritten), six class docstrings
(four new, two rewritten), 123 function docstrings (12 new, 111 rewritten) -- 134 in all.
Section 3 proves that no executable statement moved.

Three comment lines were deleted and none was added or reworded; section 3.2 enumerates
them.

`critiques/pr-29/` carries the five scripts this record cites -- `measure.py`,
`strip_docstrings.py`, `check_docstrings.py`, `check_comments.py` and
`check_citations.py` -- and the Sphinx configuration section 5 used.

## 3. Proof that the change is docstrings only

### 3.1 The AST hashes

`critiques/pr-29/strip_docstrings.py` parses a module, deletes the docstring node of
every module, class and function, and hashes `ast.dump` of what is left with
`include_attributes=False`, so line and column shifts do not register.

    python critiques/pr-29/strip_docstrings.py src/pdsfile/pdsfile.py \
        src/pdsfile/pdscache.py src/pdsfile/pdsviewable.py \
        src/pdsfile/__init__.py src/pdsfile/preload_and_cache.py

| file | base | head |
|---|---|---|
| `pdsfile.py` | `b6b8ad8bd5dba452` | `b6b8ad8bd5dba452` |
| `pdscache.py` | `eccdfbc6d19a526d` | `eccdfbc6d19a526d` |
| `pdsviewable.py` | `46cc34775e969faa` | `46cc34775e969faa` |
| `__init__.py` | `d751ad7a1d483c2a` | `d751ad7a1d483c2a` |
| `preload_and_cache.py` | `121b4d4b28474396` | `121b4d4b28474396` |

All five pairs match.

**The check is not vacuous.** Five mutations of head's `pdsviewable.py`, whose unmutated
hash is `46cc34775e969faa`:

| mutation | expected | measured |
|---|---|---|
| a docstring summary line replaced with different words | same | `46cc34775e969faa` |
| trailing whitespace added after a `return` statement | same | `46cc34775e969faa` |
| `x_unused = 1` inserted inside a `Returns:` block | same | `46cc34775e969faa` |
| `x_unused = 1` inserted as a real statement in `__bool__` | **differs** | `ecfa13e9d5987665` |
| a code comment line deleted | same (blind spot) | `46cc34775e969faa` |

The mutation scripts are in the scratchpad, not the repo; the table above is the record
of them. The third row is the interesting one: an assignment written inside a docstring
is correctly ignored, so the check distinguishes prose from code rather than text from
text. The fifth row is the blind spot that section 3.2 closes.

### 3.2 The comment enumeration, which the AST cannot see

Comments are not AST nodes, so section 3.1 would not notice one being deleted, moved or
reworded. The five files' comments were extracted with `tokenize` at base and at head and
diffed:

    python critiques/pr-29/check_comments.py <base tree> <head tree>

Each comment is compared as a triple: its exact text, trailing whitespace included; its
column; and the nearest preceding line of *code*. String tokens are excluded from being
anchors, because rewriting a docstring is the whole point of this change and anchoring on
one would report every comment below a rewritten docstring as moved. Anchoring on code
instead is what makes the check specific, since the code cannot move without section
3.1's hash noticing.

| file | comment lines at base | at head | removed | added |
|---|---:|---:|---:|---:|
| `pdsfile.py` | 325 | 325 | 0 | 0 |
| `pdscache.py` | 98 | 98 | 0 | 0 |
| `pdsviewable.py` | 84 | 84 | 0 | 0 |
| `__init__.py` | 5 | 5 | 0 | 0 |
| `preload_and_cache.py` | 6 | 3 | 3 | 0 |

**Three lines removed in total, all of them one block, and all of them accounted for:**

    # Compatibility re-exports. The preload machinery lives in pdsfile/_preload.py; every
    # name this module has always exported still resolves here. The redundant `as` alias is
    # the explicit re-export form, so these do not read as unused imports.

That block is `preload_and_cache.py`'s module header, and it is exactly what deferred
entry 80 names at `preload_and_cache.py:4` at base ("every name this module has **always**
exported still resolves here"). The rule for that module is a module *docstring*, so the
comment could not stay where it was. Every fact it carried is in the docstring that
replaced it: where the implementation lives, and why the redundant `as` alias is there.

Every other comment in all five files is byte-identical to base and in the same place,
including all 325 in `pdsfile.py`.

**The check is not vacuous.** Two mutations of head, each of which the text-only version
of this check would have passed:

| mutation | measured |
|---|---|
| `# Core properties of a viewable` moved one line down, past the statement below it, leaving the comment sequence in the same order | reported: removed after `name='', pdsf=None):`, added after `self.abspath = abspath` |
| trailing whitespace added to that same comment | reported: removed and re-added under the same anchor |

## 4. The mechanical docstring checks

`critiques/pr-29/check_docstrings.py` enforces the checkable half of `doc_python.mdc`
section 4. It does not attempt semantic accuracy, which is not checkable; that is what
section 6's review rounds are for.

    python critiques/pr-29/check_docstrings.py src/pdsfile/pdsfile.py \
        src/pdsfile/pdscache.py src/pdsfile/pdsviewable.py \
        src/pdsfile/__init__.py src/pdsfile/preload_and_cache.py

| code | check | base | head |
|---|---|---:|---:|
| P1 | a `Parameters:` entry that is not a parameter of the signature | 0 | 0 |
| P2 | a parameter that does not appear in `Parameters:` exactly once | 139 | 0 |
| P3 | a section spelled `Args:`, `Arguments:`, `Keyword arguments:` or `Input:` | 26 | 0 |
| R1 | `Returns:` present without a value return, or absent with one | 75 | 0 |
| E1 | a `Raises:` entry the body neither raises nor attributes to a call it makes | 0 | 0 |
| E2 | a class raised in the body that `Raises:` does not name | 16 | 0 |
| D1 | a docstring line wider than 90 columns | 0 | 0 |
| U1 | a unicode smart quote, dash or arrow anywhere in the file | 0 | 0 |
| M1 | a module, class or function with no docstring | 20 | 0 |
| | **total** | **276** | **0** |

Per file at base: `pdsfile.py` 116, `pdscache.py` 106, `pdsviewable.py` 52,
`__init__.py` 1, `preload_and_cache.py` 1.

P2's 139 is smaller than section 1's 150 parameters because a function with no docstring
is reported once under M1 and its parameters are not then counted again; the 12
undocumented functions carry 11 parameters between them.

**Four of the nine codes are zero at base and zero at head**, so the base column cannot
show they work. Each was demonstrated on a deliberate mutation of head's
`pdsviewable.py` instead, together with the five that the base column does cover:

| mutation | finding |
|---|---|
| a `nosuch` entry added to `for_width`'s `Parameters:` | P1: "nosuch" is not a parameter of this signature |
| `size` removed from `for_height`'s `Parameters:` | P2: parameter "size" appears 0 times |
| `by_match`'s `Parameters:` renamed to `Args:` | P3: section "Args:" is not Google style |
| `__bool__`'s `Returns:` deleted | R1: body returns a value but there is no `Returns:` |
| a `RuntimeError` entry added to `for_width`'s `Raises:` | E1: the body neither raises nor attributes it |
| `from_pdsfile`'s `Raises:` deleted | E2: body raises ValueError but `Raises:` does not name it |
| `append`'s summary line widened to 156 columns | D1: docstring line 1 is 156 columns |
| an em-dash put in `copy`'s `Returns:` | U1: em-dash in a .py file |
| `__bool__`'s docstring deleted | M1: function has no docstring |

The unmutated control reports 0 findings. Every code fires on its own mutation and none
fires on the control.

The checker also passes over itself and over `strip_docstrings.py`, which is why the
banned characters in its own table are written as `\u` escapes.

### 4.1 Two conventions this record is stating rather than assuming

**Types in `Parameters:` entries are written only where the code proves them.** A
parameter used only in a boolean test and defaulted to `False` is `(bool)`; one only
concatenated with strings is `(str)`; one only iterated is left untyped. PR-35 writes
`.pyi` stubs and its rule is that a wrong narrow type is worse than a broad one, and
those stubs will be read partly off these docstrings, so a guess here becomes a wrong
stub there. Section 7 lists every omission as PR-35's queue.

**An exception raised by a mechanism other than a `raise` statement gets a `Raises:`
entry when the mechanism is one E1 can verify, and prose otherwise.** E1 accepts an
attribution to a call the body makes, to item syntax (which counts as the corresponding
dunder method), or to tuple unpacking, and checks each against the AST.

That rule is wider than the one this PR started with, which sent *every* operator-raised
exception to prose. Round 4 showed that convention was wrong: exceptions from subscripts
and unpacking -- `MemcachedCache.get()`'s `KeyError` when a rescued permanent value turns
out to be too large, `get()` and `get_now()`'s `TypeError` on a key that does not hold a
`(value, lifetime)` pair -- are exactly the failures a caller needs told about, and prose
buries them. So E1 was widened rather than the prose weakened, and the attribution stays
falsifiable: deleting it from `get_now`'s entry makes E1 report the entry again.

What still goes in prose is an exception no verifiable mechanism accounts for.
`PdsViewable.__init__` raises `ZeroDivisionError` on a zero height and
`PdsViewable.from_dict` raises `KeyError` on a missing `width`; both are stated in the
body of the docstring.

## 5. The Sphinx build

`docs/` does not exist and is not created here; PR-31 owns it, and `run_sphinx_build()`
in `scripts/run-all-checks.sh` stays dormant. A throwaway tree was built in the
scratchpad instead, with autodoc pages for exactly the five in-scope modules and an empty
`nitpick_ignore`.

    sphinx-build -W -b html . _build
    sphinx-build -n -b html . _build

| | base | head |
|---|---:|---:|
| `-n` warnings | 81 | **0** |
| `-W` | fails on the first warning | **build succeeded** |

Both builds succeed at head with zero warnings. The rendered pages were checked to
contain the new prose, so the builds are not succeeding over an empty tree: `api.html`
carries 59 matches for the three sample symbols and the exact sentence "Return a copy of
the best member for a target width".

**Nothing was mocked and nothing was ignored.** `nitpick_ignore` is empty,
`autodoc_mock_imports` is unset, and the five modules import headlessly as they are. The
only external requirement is network access for the intersphinx inventory; without it,
the builtin type names in `Parameters:` entries would not resolve under `-n`.

### 5.1 The `conf.py`, for PR-31 to inherit

```python
import os
import sys

sys.path.insert(0, os.environ['PDSFILE_SRC'])

project = 'pdsfile'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.viewcode',
              'sphinx.ext.intersphinx']
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
nitpick_ignore = []
autodoc_member_order = 'bysource'
```

A copy is at `critiques/pr-29/sphinx-conf.py`. `sys.path` is set from an environment
variable because the tree is outside the repo; PR-31 will point it at `src/` directly.
`doc_python.mdc` section 3 also requires `myst_parser` and a diagram extension, which
this build has no pages to use, and requires the version to come from installed package
metadata, which a throwaway tree has none of.

### 5.2 What PR-31 should know before it writes its own

Two hazards produced most of base's 81 warnings, and both are recorded as deferred
entries because PR-30 hits them again at a much larger scale.

* **A trailing underscore makes a reStructuredText reference.** Base's build reported
  `Unknown target name: "log_root"` from `pdsfile.py`'s mention of `LOG_ROOT_,` and
  `"document"` and `"folder"` from `load_icons`'s mention of `"document_"` and
  `"folder_"`. This package's path attributes all end in underscores. Double backticks
  remove the hazard, and every identifier in these five files is now written that way.
  Deferred entry 169.
* **Cross-reference roles cannot be used yet.** `doc_python.mdc` section 5 wants a role
  on every API symbol and section 6 wants a clean `-n` build; with autodoc pages for five
  modules only, a role naming anything else resolves to nothing and fails the gate.
  Inline literals are used instead, and the sweep belongs to PR-31. Deferred entry 168.

A third, smaller one: an indented block under a bare `Examples:` heading is a docutils
error, which is what base's `from_path` produced. That docstring's examples are now
running prose.

## 6. Standing gates

### 6.1 Test id sets, full data, both modes

The command lines are `scripts/automated_tests/pdsfile_main_test.sh`'s, plus `-rA` and
`--junitxml`. Run from each tree in turn.

    pytest tests/api/ tests/core/ tests/holdings_maintenance/ tests/pds3file/ \
           tests/rules/pds3/ tests/pds4file/ tests/rules/pds4/ --mode ns -rA --junitxml=...
    pytest tests/pds3file/ tests/rules/pds3/ --mode s -rA --junitxml=...

| mode | scope | base | head | ids only in base | ids only in head | outcome changed |
|---|---|---|---|---|---|---|
| `ns` | all seven directories | 1101 passed, 34 skipped (1135 ids) | 1101 passed, 34 skipped (1135 ids) | none | none | none |
| `s` | `tests/pds3file/ tests/rules/pds3/` only | 555 passed, 3 skipped (558 ids) | 555 passed, 3 skipped (558 ids) | none | none | none |

The `--mode s` scope is the script's own (`scripts/automated_tests/pdsfile_main_test.sh:75`),
not the full suite; it is labelled here so the next PR compares like with like. The
per-test id sets were diffed, not the counts: nothing added, nothing removed, no outcome
changed, in either mode.

### 6.2 The code checks with no holdings

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        bash scripts/run-all-checks.sh -c -s

All checks passed: ruff, pytest (318 passed, 817 skipped), pyroma 10/10, the API-freeze
check, and the clean-install gate. The script needs a `venv` in the repository root; a
symlink to the shared interpreter was made for the run and removed afterwards. It is
gitignored at `.gitignore:132` and is not part of this PR.

### 6.3 The API freeze

    pytest tests/api

26 passed. The four frozen files are byte-identical to `4edc7d1`, checked with
`git diff --quiet 4edc7d1 -- <file>` on each:

* `tests/api/api_manifest.json`
* `tests/api/manifest_allowlist.json`
* `scripts/dump_public_api.py`
* `tests/api/test_api_freeze.py`

This PR turns three `#` header comments into module docstrings, which moves `__doc__`
from None to a string on `pdscache`, `pdsviewable` and `preload_and_cache`, and adds
`__doc__` to four classes and twelve functions. That is freeze-neutral, verified two
ways rather than assumed: `tests/api` passes unchanged at head, and
`grep -c '__doc__' tests/api/api_manifest.json` is **0** -- the manifest records
name-to-kind pairs and has no docstring field for a docstring to appear in.

### 6.4 ruff

    ruff check .                                          # All checks passed
    ruff check --preview --select E111,E112,E113 .        # All checks passed
    ruff check . --config 'lint.per-file-ignores = {}'    # Found 2249 errors

### 6.5 The ratchet

Measured at base and at head, not inherited:

| | base | head |
|---|---:|---:|
| `per-file-ignores` entries | 66 | 66 |
| code slots across those entries | 180 | 180 |
| findings with `per-file-ignores = {}` | 2,249 | 2,249 |
| `[project.scripts]` entries | 11 | 11 |

    python -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb')); \
               pfi = d['tool']['ruff']['lint']['per-file-ignores']; \
               print(len(pfi), sum(len(v) for v in pfi.values()), len(d['project']['scripts']))"

Nothing moved. No entry was retired and no entry grew.

One finding was introduced and fixed inside this PR rather than shipped: the first draft
of `check_docstrings.py` opened a file without a context manager, which `ruff check .`
caught as SIM115 and which pushed the ratchet to 2,250. The fix was `pathlib.read_text`.
It is recorded here because the ratchet is a number this PR is judged on, and it did move
before it moved back.

`bandit` and `vulture` are disabled and not installed. This PR claims nothing about them.

### 6.6 The inherited record checker

    python critiques/pr-28/check_record_numbers.py

15 stale, at base and at head, and the two outputs are byte-identical. Those are PR-28's
own numbers about the three driver functions, invalidated by PR-28a's extraction; they
arrived that way at `4edc7d1` and this PR neither caused nor repaired them.

PR-29's own numbers are checked by `critiques/pr-29/check_citations.py`:

    python critiques/pr-29/check_citations.py

It reads the line every file-and-line citation in this record and in this PR's deferred
entries points at and requires a token that identifies what the prose says is there, so a
citation that has drifted by one line fails. It also refuses any citation the two
documents make that its own table does not cover, so a number added later cannot go
unchecked. On top of the citations it re-derives the scope table's head line counts, the
class, function, parameter and docstring totals for both halves of the split, the fact
that every in-scope definition is documented at head, all four ratchet numbers, the four
frozen files, and the absence of `__doc__` from the manifest. It reports 0 stale.

## 7. Type omissions -- PR-35's queue

`Parameters:` entries written without a type, because the code does not prove one. Each
line names what the code does constrain, which is what PR-35 has to work from.

**`pdsfile.py`**

| parameter | where | what the code shows |
|---|---|---|
| `info_first` | `sort_info_first` | stored unexamined; consumers accept True, False or an int above 1 |
| `lifetime` | `_complete`, `child`, `from_logical_path`, `from_abspath`, `from_relative_path`, `_from_absolute_or_logical_path`, `from_path` | passed through to a cache, where zero and None are both meaningful; a number of seconds otherwise |
| `logger` | `set_logger` | tested for truth, then assigned; any PdsLogger-shaped object |
| `rank` | `bundle_pdsfile`, `bundleset_pdsfile` | tested for truth, then used as a dictionary key against the version ranks, which are ints |
| `path` | `from_path` | passed through `str()`, so anything with a string form |

**`pdscache.py`**

| parameter | where | what the code shows |
|---|---|---|
| `key` | every method taking one | used as a dictionary key and, for `MemcachedCache`, as a memcached key, which constrains it to a string there but not here |
| `value` | `set`, `set_local`, `set_multi` | stored unexamined by `DictionaryCache`; pickled by `MemcachedCache` |
| `lifetime` | both constructors, `set`, `set_local`, `set_multi` | a number of seconds or a callable; the constructors branch on `type(...).__name__` |
| `keys` | `get_multi`, `delete_multi` | iterated; `MemcachedCache.get_multi` also builds a set from it |
| `logger` | both constructors | tested for truth, then called; any PdsLogger-shaped object |
| `clear_count` | `replicate_clear` | compared for equality and for identity with None; an int on the path that works |
| `port` | `MemcachedCache.__init__` | branches on `type(port) is str`: a string is a socket path, anything else is formatted with `%d` |

**`pdsviewable.py`**

| parameter | where | what the code shows |
|---|---|---|
| `exclude` | `PdsViewable.to_dict`, `PdsViewSet.to_dict` | only the `in` test is applied, so any container of names |
| `viewables` | `PdsViewSet.__init__` | iterated once |
| `viewable` | `PdsViewSet.append` | tested with `in` against a set, then `isinstance`-tested against `PdsViewSet` |
| `pdsf` | `PdsViewable.__init__`, `PdsViewable.from_pdsfile` | stored unexamined in the first; in the second, six attributes are read off it |
| `pdsfiles` | `PdsViewSet.from_pdsfiles`, `iconset_for` | type-tested against `list` and `tuple` respectively, then iterated |
| `logger` | `load_icons` | tested for truth, then called; any PdsLogger-shaped object |

Twenty-five entries in all. The pattern is that a type is omitted where the parameter is
stored rather than examined, or where the body branches on its type; it is written where
the body constrains it to one thing.

`PdsFile` is named as a type in prose rather than in a type slot inside `pdsviewable.py`,
because `pdsviewable` does not import it and a stub that declared the dependency would
create one that the code does not have.

## 8. The PR-29 / PR-29a split

The plan's PR-29 covered all of `src/pdsfile/*.py`. It is split here. This PR takes the
public half -- the five files above -- and PR-29a takes the ten `_*.py` modules.

The reason is review load, not size. There is no mechanical gate for semantic accuracy,
so every docstring in a docstring PR has to be read against the code by a person; section
4's checker proves shape and proves nothing about truth. The two halves together are
about 300 docstrings, which cannot be reviewed in one pass. This half is 134.

The split point is not arbitrary. Deferred entry 80, which is the owner's and is in scope
here, names exactly `pdsfile.py`, `preload_and_cache.py`, `pdscache.py` and
`pdsviewable.py` as the module headers that narrate the port. This PR is precisely the
set that entry covers, plus `__init__.py`, which is the package's front door and is 15
lines.

The plan's Phase 7 section carries the split and this reason.

## 9. Numbers this PR was handed that did not reproduce

Recorded because the executor's brief asked for every number to be re-derived rather than
inherited, and two did not survive it.

* **"242 of the 251 docstrings have no section of any kind."** Measured: **248** under a
  strict match on the Google section names, or **241** if `Note:`, `Example:`,
  `Attributes:` and `Format:` are also counted as sections. Neither is 242 and no
  definition tried reproduces it. The claim it supports -- that this is not a reformat --
  stands either way, and section 1.1 records the definition it uses.
* **"`pdscache.py` and `pdsviewable.py` carry the same 'stays'/'still' framing in their
  re-export blocks"** (deferred entry 80). At `4edc7d1` neither does. Both read "is not
  referenced below; it is re-exported for callers that reach it as ...". Entry 80's
  amendment records the correction, and both comment blocks are untouched by this PR,
  which section 3.2's table confirms.

Everything else reproduced exactly: the five-file table, the 150 parameters, PR-29a's 156
functions and 131 parameters, and all four ratchet numbers.

## 10a. CodeRabbit

CodeRabbit reviewed the first push, which was before the three review rounds, and posted
15 comments. Seven of them name defects rounds 1 to 3 had already found and fixed --
`DictionaryCache`'s stale trim keys, `del_multi`, `new_merged_dir`'s unfilled slots, the
category-level cache guard, `parent()`, the empty nested `PdsViewSet`, and
`load_icons`'s `UnboundLocalError`. Each of those threads was answered with the entry
number and the commit that fixed it.

Six were new and are fixed here:

* **`_recache`'s lifetime claim is class-dependent.** It said flatly that a permanent
  entry becomes an expiring one. That is true of a dictionary cache, whose `set()`
  resolves a None lifetime to the cache default, and false of a memcached cache, whose
  `set()` reuses the lifetime already recorded for the key. `PdsFile.CACHE` can be
  either. **All three review rounds missed this**, and it is the best single argument in
  this PR for running a tool alongside the readers rather than instead of them.
* **`check_comments.py` compared text without position**, and stripped trailing
  whitespace. Section 3.2 records the strengthened check and its two mutations.
* **`measure.py` matched section names as substrings**, so prose containing the word
  `Returns:` would have counted as a section. It now matches whole lines. Re-measured at
  base, every figure in section 1.1 is unchanged, so the defect was real and its effect
  on this record was nil.
* **`check_citations.py` skipped every citation naming a base-tree file**, not just the
  one base-tree line. Narrowed to the exact file-and-line pair.
* **Deferred entry 159 said "Four" unguarded log calls and listed three.** Corrected to
  three; three is what round 1 verified.
* **`preload_and_cache.py` named the four lifetime constants and their values in
  separate sentences.** Each constant now carries its own value.

A second pass over the amended tree brought five more, of which four were right and are
fixed: `DictionaryCache`'s key set is not "only ever added to" -- a trim does remove from
it; entry 177's remediation note was wrong, since dedenting the `return` out of the loop
does fix the empty-set case as well as the non-empty one; `load_icons`'s
`(icon_type, True)` claim was over-broad, because a later directory that has its own
`_open` file does replace that key and only the closed-set fallback is blocked; and a
sentence fragment in `measure.py`.

The fifth was declined on evidence. CodeRabbit read `from_path`'s second scanning loop as
recognizing trailing components, so that `COISS_2xxx/archives` would be an archive path.
Run, it is not: that call gives `volumes/COISS_2xxx/archives`, and `COISS_2xxx/checksums`
and `COISS_2xxx/previews` behave the same way. The loop reads `parts[0]` and pops from the
other end, so it re-tests the element the loop before it just failed on and breaks
immediately -- which round 3 established by tracing and this confirmed by running. Entry
187 records it and the thread carries the reproduction.

One was declined earlier. The plan's PR-29a line says "156 functions, 131 parameters"; CodeRabbit
read that as a count of `Parameters:` sections. It is a count of parameters, measured with
`critiques/pr-29/measure.py`, and it is the right metric for scoping PR-29a, which has to
write one description per parameter. The thread carries that reply.

## 10. Review

Four rounds, each run by a fresh reviewer subagent with no context from this session or
from the rounds before it. Records: `critiques/pr-29/review-round-1.md` through `-4`.

| round | slice | surface | findings | new deferred entries |
|---|---|---|---:|---|
| 1 | `pdscache.py` | 3 classes, 60 functions | 15 | 170-176, and 157 rewritten |
| 2 | `pdsviewable.py` | 2 classes, 26 functions | 11 | 177-183 |
| 3 | `pdsfile.py` | 1 class, 37 functions, the module map | 18 | 184-190 |
| 4 | `pdscache.py` again | the same 63 | ~20 | 191-198 |

Sixty-four findings, every one re-verified by the executor before acting on it. Only one
re-verification disagreed with the reviewer, and only in degree: round 1's finding 7
reproduced with a different key count, because trimming had fired during their setup; the
claim held and the entry records the cleaner reproduction.

**Rounds 1 to 3 are not a trend.** An earlier draft of this record read 15, 11 and 18 as
a sequence that failed to converge. That was wrong: they are three independent *first*
passes over three *different* files, so nothing about them rises or falls, and they say
nothing about what a second reading of any file returns. What they do establish is
simpler and more serious -- every file had had exactly one adversarial read, and each of
those reads found roughly fifteen real defects in prose written for this PR.

**Round 4 is the experiment that tested it, and the answer is that a second read does not
return zero.** A second reader over `pdscache.py`, pointed at the angles round 1 lacked,
found about twenty items: 13 defects in the new prose and 7 discoveries about the code.
That is comparable to round 1's yield on the same file.

The angle that paid was claims about a **relationship between two things** -- that one
method calls another, that one is safe because another checked first, that a lifetime or
a limit behaves the same way in both cache classes. Six of round 4's 13 prose defects were
of that kind, and so was the single thing CodeRabbit found that all three earlier rounds
missed. It is a systematic weak point of this prose, not a run of bad luck, and section
10a's `_recache` example is the same shape as round 4's finding 2.

The three highest-value classes of finding across all four rounds:

* **A described failure whose mechanism is wrong.** `delete_multi` fails one statement
  earlier than written *and* writes to the server first, `_wait_for_ok` breaks the block
  before raising rather than instead of it, `from_path` raises `UnboundLocalError` where
  the entry said `KeyError`, `_restore_permanent_to_cache` logs before it acts rather
  than after. These read as correct to anyone who does not re-derive them.
* **A claim that is true of the common case and false of the case the sentence exists
  for.** A named viewable "is never returned by a size lookup" -- except by a set that
  holds nothing else; instances "are cached" -- except the data files the sentence's own
  examples name; trimming runs "until exactly the limit remains" -- except when it
  discards nothing.
* **A statement inverted.** `_complete`'s case claim said the opposite of what the code
  does; `replicate_clear_if_necessary` named `set()` among the methods that do not reach
  it, when on an unpaused cache it does.

Twenty-nine defects that no deferred entry had recorded came out of the four rounds,
entries 170-198.
