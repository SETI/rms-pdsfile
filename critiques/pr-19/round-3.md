# PR-19 — adversarial pre-PR review, round 3

**Reviewer:** fresh, no development context; no knowledge of any prior round.
**Diff reviewed:** `git diff origin/pr-18-derived-paths...HEAD` (base `80cd9ff`,
head `511bfcc`). I regenerated the diff myself and confirmed it matches the copy
I was handed.
**Date:** 2026-07-27

## What I verified independently, and how

I trusted nothing the diff or its records say about themselves. **Byte
equivalence:** an `ast`-driven extractor pulled all eight moved definitions
(decorators included) out of the parent worktree's `PdsFile` body and out of the
two new mixin bodies and compared them byte for byte — seven identical, and
`opus_products` differing by exactly the four deferred-import lines; the five
index-row definitions and the two OPUS classmethods also compare identical as
single first-to-last blobs, so nothing was reordered or dropped. The
`pdsfile.py` side of the diff is one 540-line deletion containing exactly those
eight `def`s and the two banner comments, plus header edits. **Free variables:**
`symtable` over both new modules (globals not assigned at module level) plus an
`ast` pass over every decorator expression and argument default reports **zero**
dangling names in either. **Cycle and load-bearing-ness:** I copied the tree,
hoisted the deferred import to module level, and got `ImportError: cannot import
name 'PdsFile' from partially initialized module 'pdsfile.pdsfile'`; with the
import simply deleted, `ruff --select F821` fires and the mutated full-tree copy
(pytest run from inside it, `_opus.__file__` asserted to point at the copy)
gives **39 failed / 682 passed**, matching the record. **Freeze:**
`pytest tests/api/` → 16 passed; `python scripts/dump_public_api.py` run against
the parent worktree (via `PYTHONPATH`, `pdsfile.__file__` checked) and against
HEAD gives **byte-identical** 733,876-byte dumps; `vars(pdsfile.pdsfile)` 48 →
50, gaining only the two underscore mixin names; `numbers`/`pdstable`/
`defaultdict` are frozen manifest members and their reference counts in
`pdsfile.py` are 0/0/0 while `_clean_join`/`abspath_for_logical_path`/
`_needs_glob` are 10/4/1, exactly as claimed. **Ratchet:** I re-ran the per-code
`ruff check --no-cache --isolated --select <code> --line-length 100
--target-version py310` loop over all 18 codes for parent `pdsfile.py`, HEAD
`pdsfile.py`, `_index_rows.py` and `_opus.py` — every code conserves exactly,
`RUF005` 8 → 6+1+1, `UP024` 13 → 10+2+1, total suppressed 85 → 85; both new
entries are strict subsets of `pdsfile.py`'s, nothing was dropped, and the
converse whole-select-set run against each new module reports exactly `RUF005`
and `UP024` and nothing else. **§6.2 evidence:** I re-reduced all eight junit
XMLs in `runs/p19-{base,head1,head2,head3}/` with the supplied `setdiff.py` and
diffed them: `--mode ns` 880 → 882 with **only** the two
`test_no_mixin_is_shadowed_by_a_pdsfile_subclass[Pds3File|Pds4File]` ids added,
no removals and no outcome changes; `--mode s` a zero-line diff; my reductions
are byte-identical to the `p19_*_{ns,s}.txt` files on disk; counts 846/34,
848/34, 555/3, 555/3 all reproduce. Freshness holds: the last `src/pdsfile/`
commit is `3ab1738` at 18:04:34 and head3's runs *start* at 18:04:45 / 18:07:39
and are written 18:07 / 18:09. Non-vacuity holds: the baseline
`measured_files.txt` carries only worktree paths and no `_index_rows.py` /
`_opus.py`; HEAD's carry only main-tree paths and both new modules. **Sniff:** I
dumped `__bases__`, `__bases__[0].__name__`, the sniff's verdict, the MRO and
`dir()` for all 34 classes in the hierarchy on both trees — `__bases__[0]`,
verdict (`True` for the same six pds4 rule classes) and `dir()` identical
everywhere; the only `__bases__` change is `PdsFile`'s own, and every MRO moves,
which is precisely the plan's premise. **New test:** mutation-tested — giving
`Pds3File` an `opus_products` turns *only*
`test_no_mixin_is_shadowed_by_a_pdsfile_subclass[Pds3File]` red. **Coverage:** I
ran my own `coverage run --rcfile` with `dynamic_context = test_function` over
`tests/pds3file/ tests/pds4file/ tests/rules/ tests/core/
tests/holdings_maintenance/` and reproduced §9's counts exactly (50 distinct
contexts; 9/12/9/4/0/2/19/28) — the *attribution* is where I found a defect
(Minor 2). **Gates:** `ruff check src/pdsfile tests scripts` → all passed;
`scripts/run-all-checks.sh` with every holdings env var unset → all six
sub-checks green; the holdings-free pytest leg is **82 passed / 800 skipped**.
**§6.4:** `api_manifest.json`, `manifest_allowlist.json`,
`scripts/dump_public_api.py`, `tests/api/test_api_freeze.py` and every golden are
untouched; no `noqa`, `skip`, `xfail` or `type: ignore` is added anywhere in the
diff; no inline annotations; no PR-number or "moved from" narration in any source
comment. **Consumers:** every rms-opus / rms-viewmaster call-site count and line
number in §12 reproduces exactly (rms-opus `73cb6de7`, rms-viewmaster `a0d05e2`),
as do all 20 monkeypatch sites and their line numbers, and the 18-of-34
rule-module `opus_products` figures.

## Major findings

**None.** The extraction is byte-for-byte, the freeze surface is unchanged to the
byte, the ratchet is a strict split, the `__bases__[0]` premise is true rather
than assumed, the deferred import is the pinned pattern and is load-bearing, and
the §6.2 record is present, fresh, non-vacuous and reproduces from the artifacts.
Everything below is record or documentation accuracy.

## Minor findings

### m1 — `src/pdsfile/_opus.py:20-30`: the mixin's "and nothing else" contract omits `version_rank`, and the record's claim that both docstrings are AST-derived is false because of it

`_OpusMixin`'s docstring opens "Every name these methods touch outside their own
bodies, **and nothing else**" and lists three instance attributes:
`abspath, logical_path, root_` (`src/pdsfile/_opus.py:29`). `opus_products` also
reads **`version_rank`**, three times — `src/pdsfile/_opus.py:283`, `:284` and
`:296` (`li[0].version_rank`, twice, and `key=lambda x: x[0].version_rank`).
`version_rank` is a plain instance attribute assigned in `PdsFile.__init__`
(`src/pdsfile/pdsfile.py:325`), i.e. exactly the category round 1 established the
list must distinguish, and `inspect.getattr_static(PdsFile, 'version_rank')`
confirms it is not a descriptor.

This falsifies two statements about method, not just one about content:
`critiques/phase5-validation.md:2821` says "the two docstrings are now
**derived** from an AST walk of their own modules rather than written by hand",
and commit `3ab1738`'s message says they "state their whole state contract,
derived from an AST walk". An AST attribute walk of `_opus.py` yields
`version_rank`; I ran one, and it is the only omission in either module. This PR's
own standard is that every figure in its records is measured, and this is the
third consecutive round to find the same class of defect in the same two
docstrings.

I checked the contract in **both** directions and in both modules, so the fix is
exactly one line: `_index_rows.py`'s list is complete and lists nothing it does
not touch (all eight "lazy properties" really are `property` objects on
`PdsFile`; all six "instance attributes" really are non-descriptors; `CACHE`,
`__bases__`, the two writes and the five method names all check out, and every
listed name resolves on `PdsFile` itself, not on a sibling mixin);
`_opus.py`'s lists nothing it does not touch either (`__base__` and all nine
class attributes/translators, all four properties, all four "other methods",
and `glob_glob`/`os_path_exists`/`shelf_lookup` from the siblings are each
genuinely read — `CROSS_PDS3_PDS4_PRODUCTS` is defined only on `Pds3File`/
`Pds4File`, which is why the "or on its subclasses" wording is right).

**Fix:** change `src/pdsfile/_opus.py:29` to
`instance attributes read    abspath, logical_path, root_, version_rank`, and
either actually re-derive both docstrings from the AST (the walk is ~15 lines:
collect `ast.Attribute` nodes inside the mixin's `FunctionDef`s, drop names bound
by module imports and stdlib method calls, classify each against
`inspect.getattr_static(PdsFile, name)`) or soften
`critiques/phase5-validation.md:2821` to describe what was actually done. A
`src/pdsfile/` change means §6.6 step 5 requires the full-data record to be
regenerated before the next round.

### m2 — `critiques/phase5-validation.md:2496-2498` and `:2502`: §9's "Where" column is wrong in four of eight rows

My own `dynamic_context = test_function` run reproduces every **count** in §9
exactly — 50 distinct contexts over the two modules, and 9 / 12 / 9 / 4 / 0 / 2 /
19 / 28 per method, with no `tests/core/` and no `tests/holdings_maintenance/`
context, exactly as recorded. The **attribution** does not hold up:

- `:2496` `get_indexshelf` (9), `:2497` `find_selected_row_key` (12) and `:2498`
  `child_of_index` (9) are each credited to three modules
  (`test_pds3file_blackbox.py`, `test_pds3file_blackbox_cached.py`,
  `test_pds3file_whitebox.py` / "same three"). All three methods **also** get a
  context from `tests/rules/pds3/test_corss_8xxx.py::test_associations`. So the
  index-row half of the extraction is reached from `tests/rules/` too, which the
  table denies.
- `:2502` `from_opus_id` (19) is credited to "**the two blackboxes**,
  `test_pds3file_whitebox.py`, and 15 of the 16 `tests/rules/pds{3,4}/`
  modules". `tests/pds4file/test_pds4file_blackbox.py` contributes **no**
  `from_opus_id` context — its only context on either module is
  `test_from_filespec`, which the row above (`:2501`) already and correctly
  records. The 19 are: `test_pds3file_blackbox.py` ×2
  (`test_from_opus_id1`, `test_from_opus_id2`), `test_pds3file_whitebox.py` ×1
  (`test_from_opus_id_with_wrong_id`), and 16 contexts across 15 rules modules
  (`test_go_0xxx.py` contributes two).

`opus_products`' "the same 15" is correct — all 28 of its contexts come from
those same 15 rules modules — and `data_abspath_associated_with_index_row`'s two
modules and `data_pdsfile_for_index_row`'s zero are correct. §9 is what deferred
entry 50 and the §10 "which parts are pinned" argument rest on, so it is the one
table where a wrong "where" could mislead a later reader about coverage.

**Fix:** add `tests/rules/pds3/test_corss_8xxx.py` to the three index-row rows
(e.g. "same three, plus `tests/rules/pds3/test_corss_8xxx.py`") and rewrite
`:2502`'s cell as "`test_pds3file_blackbox.py`, `test_pds3file_whitebox.py`, and
15 of the 16 `tests/rules/pds{3,4}/` modules".

### m3 — `critiques/phase5-validation.md:2354` and `:2371-2372`: three `_opus.py` line numbers are stale by exactly the docstring growth §5 itself records

§6 says the missing deferred import produces "`F821 Undefined name PdsFile` on
`_opus.py:162`", and that `_opus.py` has "exactly one" `PdsFile` `Name` node "at
line 166 ... bound by the deferred import at line 164". Measured at HEAD: with
the four lines removed, ruff reports **`_opus.py:179`**; in the delivered file
the deferred import is at **`src/pdsfile/_opus.py:181`** and the sole `PdsFile`
`Name` node at **`:183`**. All three are off by 17 — precisely the docstring
growth that §5 (`:2330-2332`) records as "the two new modules grew after the
extraction commits, by 18 and 17 lines respectively". The claims are true; the
citations were carried forward from the pre-round-2 file instead of re-measured.

**Fix:** re-measure the three numbers (179 / 181 / 183), or drop the line numbers
and cite the symbol, as §5 does for everything else.

### m4 — `critiques/phase5-validation.md:2096-2097`: the non-vacuity table's module list reads as exhaustive and is not

The row is headed "pdsfile modules measured" and gives
`{pdsfile,_path_utils,_shelves,_local_fs,_derived_paths}.py` for the baseline and
that set plus the two new modules for HEAD, then asserts "The lists are otherwise
identical, module for module." `coverage.CoverageData.measured_files()` on the
supplied `.coverage` files actually reports **nine** top-level `src/pdsfile/*.py`
modules on the baseline side and **eleven** at HEAD — the five listed plus
`__init__.py`, `pdscache.py`, `pdsviewable.py` and `preload_and_cache.py`.

The argument itself is sound and I reproduced it in full: baseline paths are all
under the worktree, HEAD paths all under the main tree, `_index_rows.py` and
`_opus.py` appear only at HEAD, the only baseline path matching `_opus` is
`tools/show_opus_products.py`, and the lists are otherwise identical. Only the
enumeration is short, and the `{...}` set notation is what makes it read as
complete.

**Fix:** list all nine/eleven, or write "among them" before the braces.

### m5 — `tests/api/test_mixin_collisions.py:105-110`: the new check's stated rationale claims more than the check can prove, and encodes a constraint that will false-fail a legitimate later move

The comment says a subclass–mixin name collision "would make the mixin's copy
unreachable on the class callers actually use: **the failure this module exists
to catch, one level down**". That framing is not right. This module exists to
catch failures the *mixin extraction* introduces; a name defined on `Pds3File`
shadowed `PdsFile`'s copy identically **before** the extraction, so no move can
create this condition and no move can be proved wrong by its absence. The check
is a useful hygiene assertion — it pins that the extracted method is the one that
runs on the classes callers instantiate — but it is not the "one level down"
version of `test_no_mixin_is_shadowed_by_pdsfile_itself`.

It also quietly forbids something legal and already widespread: `Pds3File` and
`Pds4File` between them redefine 34 and 35 names that `PdsFile` also defines,
including `__init__`, `__repr__`, `use_shelves_only`, `require_shelves`,
`set_logger` and `set_easylogger`. Every one of those is on PR-22's explicit
stay-list, so nothing collides today; but if a later Phase-5 PR ever moved one
into a mixin, this test would go red for a move that changes no behavior at all,
and the executor would have no way to tell that from a real finding.

**Fix (comment only, no behavior):** replace the "the failure this module exists
to catch, one level down" clause with what the check actually pins, e.g. "no
direct subclass currently redefines a name a mixin supplies, so every extracted
method is the one that runs on the classes callers instantiate; a subclass
override is legal Python and is not itself a move defect, so a failure here means
're-read the move', not 'the move is wrong'."

## Deferred findings

### D1 — make the subclass shadowing check express the invariant, and discover its subjects

Two things that belong together and are both out of scope here: deriving the
parameter list from `PdsFile.__subclasses__()` instead of the literal
`[Pds3File, Pds4File]` (already recorded as entry 53), and separating "a subclass
redefines a mixin name" from "the move left a copy unreachable" so the check
cannot false-fail a legal override (m5's underlying issue). Both are edits to the
mixin harness that add or rename ids, which PR-19's set-diff gate forbids.
**Owner: PR-20**, folded into entry 53.

### D2 — entry 54 (mechanically derive the mixin state contracts) is now three-for-three and should be treated as due, not optional

Rounds 1, 2 and 3 each found the hand-written "state contract" paragraph wrong or
incomplete — round 1 three misclassified names, round 2 two properties, a class
attribute and a write, round 3 `version_rank` in the *other* module. Entry 54
already records the read-side AST check and assigns it to PR-22. The third
independent hit is worth appending to the entry, because it is now the only part
of a mixin module that nothing verifies and the only place this PR series has
produced a defect. **Owner: PR-22**, per entry 54.

## Verdict

**goal met** — 0 Major, 5 Minor, 2 Deferred. The OPUS and index-row extraction is
byte-for-byte, the class statement and every class attribute stayed in
`pdsfile.py`, the mixins add no state, the bases are alphabetical with `object`
last, the public surface is unchanged to the byte, the ratchet only split, the
`__bases__[0].__name__` sniff moved untouched and its premise verifies
empirically for all 34 classes, and the full-data set diff is exactly the two ids
this PR adds and nothing else. Every Minor is a wrong sentence in a record or a
docstring, not a defect in the moved code.
