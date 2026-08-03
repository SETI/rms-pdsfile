# PR-19 — adversarial pre-PR review, round 1

**Reviewer:** fresh, no development context.
**Diff reviewed:** `git diff origin/pr-18-derived-paths...HEAD` (head `bc5147e`, base
`80cd9ff`). Nine files: `pyproject.toml`, `src/pdsfile/pdsfile.py`,
`src/pdsfile/_index_rows.py` (new), `src/pdsfile/_opus.py` (new),
`tests/api/test_mixin_collisions.py`, plus four record/plan files.
**Date:** 2026-07-27

## What I verified independently, and how

I re-derived the byte-equivalence claim myself rather than reading the table:
an `ast` pass extracted every `FunctionDef` source segment (decorators included)
from `PdsFile`'s body at the parent tip and from `_IndexRowsMixin` /
`_OpusMixin` at HEAD and compared them byte for byte — **seven of the eight are
identical, and the eighth (`opus_products`) differs only by the four sanctioned
deferred-import lines**, shown as a unified diff by my own tool. The same pass
confirms the set of definitions removed from `PdsFile`'s body is exactly the set
of definitions added to the two mixins, and that **no method remaining in
`PdsFile` changed one character**. I ran a free-variable analysis over both new
modules (module-bound names vs. `Load`ed names per function): every free name
resolves to a module-level import in its own module, none is left dangling, and
neither module contains a module-level `from pdsfile.pdsfile import` of any
spelling; `python -c "import pdsfile._opus"`, `pdsfile._index_rows`,
`pdsfile.pdsfile` and `pdsfile` each import cleanly **in any order**, so there is
no cycle. I dumped, for all 34 classes in the hierarchy (rule modules force-imported)
on the parent worktree and at HEAD, each class's `__bases__`, `__bases__[0].__name__`,
`__base__`, full MRO, `dir()` surface with the owning class of every name, and the
`__bases__[0].__name__ == 'Pds4File'` sniff's own verdict: **`__bases__[0].__name__`,
`__base__`, the sniff verdict (`True` for exactly six classes) and every class's
`dir()` name-set are identical on both sides**; the only difference anywhere is
`PdsFile`'s own `__bases__`/MRO gaining the two mixins and each moved method's
owner moving from `PdsFile` to its mixin. The plan's premise for leaving the
sniff alone therefore holds, measured rather than argued.

On the gates: `ruff check src/pdsfile tests scripts` → *All checks passed*;
`pytest tests/api/` → 16 passed; `python scripts/dump_public_api.py` run against
the parent worktree and against HEAD produced **byte-identical** dumps (733,876
bytes each, `diff` empty); `scripts/run-all-checks.sh` with every holdings env
var unset → **82 passed / 800 skipped**, all six sub-checks green including the
clean-install gate (so both new modules are packaged). For the ratchet I ran
`ruff check --config 'lint.per-file-ignores = {}'` against `pdsfile.py` on both
sides — the **same 18 codes fire before and after**, so nothing could be dropped
— and `ruff check --isolated --select RUF005,UP024` per file, which shows
`_index_rows.py` genuinely triggers both codes (3 violations) and `_opus.py` both
(2): the two new entries are a strict subset of `pdsfile.py`'s entry and neither
is a vacuous suppression. I confirmed the deferred import is load-bearing for the
gate as claimed by deleting it from a copy and running ruff: `F821 Undefined name
PdsFile` at `_opus.py:162`, exactly as the record states. I checked out the
intermediate commit `2d2de4a` in a throwaway worktree and confirmed it is green
too (ruff clean, imports, `tests/api/` 14 passed, bases alphabetical).

On the §6.2 evidence I verified the record rather than re-running the suite: I
re-reduced all four junit XMLs in `runs/p19-base/` and `runs/p19-head1/` with the
supplied `setdiff.py` and diffed them myself — `--mode ns` 880 → 882 ids with
**exactly the two `test_no_mixin_is_shadowed_by_a_pdsfile_subclass` ids added and
nothing else moving in either direction**, `--mode s` 558 → 558 with a **zero-line**
diff; my reductions are byte-identical to the ones on disk. Non-vacuity: the
baseline run's `measured_files` contains only worktree paths and **no**
`_index_rows.py`/`_opus.py`, the head run's only main-tree paths, with zero
cross-tree leakage in either direction. Freshness: last `src/pdsfile/` change is
`174fe7a` at 17:00:33, the head junit XMLs are 17:04/17:06. I also mutation-tested
the new test in-process (giving `Pds3File` its own `opus_products`): it fails with
the right message, so it is not hollow, and the whole-hierarchy intersection
against all five mixins is genuinely empty. Finally I ran my own
`dynamic_context = test_function` coverage pass over `tests/pds3file/
tests/pds4file/ tests/rules/ tests/core/` (721 passed / 34 skipped) and
**reproduced §9's table exactly**: 9 / 12 / 9 / 4 / **0** / 2 / 19 / 28 contexts
and 50 distinct contexts overall. §6.4 is respected: `git diff --stat` over
`api_manifest.json`, `manifest_allowlist.json`, `scripts/dump_public_api.py` and
`tests/api/test_api_freeze.py` is empty, no golden or baseline file is touched,
no `noqa`/`skip`/`xfail` is added, and the new modules carry no type annotations,
no CRLF and no trailing whitespace.

## Major findings

**None.** I could not construct a case where the move changes behavior, loses a
name, widens the ratchet, breaks the freeze, or where a figure in the gate
evidence is unbacked.

## Minor findings

### M1 — `_index_rows.py:30-33`: three of the nine names the docstring calls "lazy properties" are plain instance attributes, and one of them the mixin *writes*

The class docstring says:

> The lazy properties these methods read -- is_index, is_index_row,
> indexshelf_abspath, index_pdslabel, filename_keylen, childnames,
> childnames_lc, row_dicts and column_names -- are defined on PdsFile

Six of those nine are real lazy properties (`indexshelf_abspath`, `is_index`,
`index_pdslabel`, `childnames`, `childnames_lc`, `filename_keylen` — `def` at
`src/pdsfile/pdsfile.py:1270, 1295, 1322, 1350, 1381, 2425`). The other three are
**plain instance attributes** initialized in `PdsFile.__init__`
(`src/pdsfile/pdsfile.py:333, 335, 337`) and rewritten in
`new_index_row_pdsfile` (`:1065-1067`); none of them exists in `vars(PdsFile)` as
a descriptor, which I checked. Worse for a reader, the docstring frames all nine
as things the methods *read*, but `child_of_index` **assigns** to one of them —
`self.column_names = [c.name for c in table.info.column_info_list]`
(`src/pdsfile/_index_rows.py:199-200`). That assignment is legitimate under the
Phase-5 rule (the mixin defines no new state; it writes state `PdsFile` owns),
but the docstring as written would lead a maintainer to believe the mixin never
mutates instance state — the one thing a Phase-5 reader is checking for.

**Fix:** split the sentence, e.g. "The lazy properties these methods read —
`is_index`, `indexshelf_abspath`, `index_pdslabel`, `filename_keylen`,
`childnames`, `childnames_lc` — and the instance attributes they read and, for
`column_names`, write — `is_index_row`, `row_dicts`, `column_names` — are all
defined on `PdsFile`."

### M2 — `critiques/phase5-validation.md:2579` and `critiques/deferred-observations.md:1040-1041`: the rule-module count is asserted, not measured, and is wrong

§11 says "**Every rule module** defines a module-level `opus_products =
translator.TranslatorByRegex([…])` table", and deferred entry 52 says
"`COISS_xxxx.py:263` and the equivalent line in **24 other** rule modules" —
i.e. 25 modules. Measured: there are **34 rule modules** (25 pds3 + 9 pds4) and
**18** of them define a module-level `opus_products` table
(`grep -rl '^opus_products' src/pdsfile/pds{3,4}file/rules/*.py | wc -l` → 18;
`grep -rli opus_products` over the same set → 20 files mentioning the name at
all). No counting scheme I tried yields 25 or "every". The *conclusion* of both
passages is sound and I re-verified it independently — zero indented
`opus_products =` anywhere under `src/pdsfile/`, and the mixin/subclass name
intersection is empty across the entire 33-subclass hierarchy — but the count in
front of it is the one number in this PR's records I could show to be false, and
this PR's own standard is that every figure is measured.

**Fix:** change §11 to "18 of the 34 rule modules define …" and entry 52 to
"`COISS_xxxx.py:263` and the equivalent line in **17** other rule modules (18 of
34)".

### M3 — `critiques/phase5-validation.md:2474-2475`: "every `tests/rules/pds3/` and `tests/rules/pds4/` module" is off by one

Both rows attribute contexts to "every" rule-test module. My independent
`dynamic_context` run reproduces the context *counts* exactly (19 and 28), but
the contributing modules are **13 of 13 pds3 and 2 of 3 pds4** — 15 of 16.
`tests/rules/pds4/test_cassini_iss_fring_mosaics_rsfrench2025.py` is
module-skipped ("cassini_iss_fring_mosaics_rsfrench2025 rule tests skipped",
visible in both driver logs) and therefore contributes no context at all. Since
§10's deferred entry 51(b) leans on exactly this kind of skip to explain a green
control, the imprecision is in the one place it could mislead.

**Fix:** "every `tests/rules/pds3/` module and the two runnable
`tests/rules/pds4/` modules (the third is module-skipped on this holdings copy)".

## Deferred findings

### D1 — the new shadowing check is hard-coded to two subclasses and would not notice a third

`tests/api/test_mixin_collisions.py:102-113` parametrizes over a literal
`[Pds3File, Pds4File]` and asserts each is in `PdsFile.__subclasses__()`. That
assertion protects against *looking at the wrong class*, but not against a future
**third** direct subclass being added and silently escaping the check — the
non-vacuity guard the sibling `_mixins()` discovery has (it derives its subjects
from `PdsFile.__bases__`) is absent here. The PR measured the intersection over
the whole 33-class hierarchy as empty and deliberately did not turn that into a
test, correctly citing the scope of deferred entry 48; deriving the parameter
list from `PdsFile.__subclasses__()` instead of a literal would close the gap at
zero cost. Out of scope for PR-19's stated goal.
**Owner:** whichever Phase-5 PR next edits the mixin harness (PR-20).

### D2 — `critiques/phase5-validation.md` PR-19 §12's consumer "reference" counts are substring counts

The 11 / 3 / 3 / 2 figures for rms-opus reproduce exactly, but only as substring
greps: 7 of the 11 `from_filespec` hits are the local helper
`_pdsfile_from_filespec`, and 2 of the 3 `opus_products` hits are
`get_opus_products_rows_for_filespec`. The actual call sites are 4, 2, 1 and 1,
and every line number the record cites is correct. Not wrong, but "references"
reads as call sites. Worth pinning the definition once for the remaining Phase-5
records rather than editing this one.
**Owner:** PR-20's validation record (convention note).

## Verdict

**goal met** — 0 Major, 3 Minor, 2 Deferred.
