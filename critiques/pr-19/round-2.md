# PR-19 — adversarial pre-PR review, round 2

**Reviewer:** fresh, no development context; no knowledge of any prior round.
**Diff reviewed:** `git diff origin/pr-18-derived-paths...HEAD` (base `80cd9ff`,
head `82e57fe`). I regenerated the diff myself and confirmed it is byte-identical
to the copy I was handed.
**Date:** 2026-07-27

## What I verified independently, and how

I did not take a single claim in the diff or its records on trust. **Byte
equivalence:** a `difflib.SequenceMatcher` pass over the parent worktree's
`src/pdsfile/pdsfile.py` and HEAD's reduced the whole change to one 540-line
deletion (base `3780–4319`) plus the header edits; concatenating
`_index_rows.py`'s and `_opus.py`'s post-docstring bodies and running `diff -u`
against that deleted block shows **exactly three** differences — the two banner
comment blocks that became class docstrings, and the four deferred-import lines
in `opus_products`. Nothing else moved, was reordered or was dropped.
**Free variables:** an `ast` pass over both new modules (module-bound names vs.
`Load`ed names, with lambda/comprehension binders handled) finds **zero**
dangling free names in either. **Cycle:** I copied the tree to scratch, hoisted
the deferred import to module level, and got
`ImportError: cannot import name 'PdsFile' from partially initialized module
'pdsfile.pdsfile'` — the deferred form is load-bearing, not decorative.
**Surface:** `dir(pdsfile.pdsfile)` gains only `_IndexRowsMixin`/`_OpusMixin` and
loses nothing; `dir(PdsFile)` is identical; `dir(pdsfile)` gains only the two
underscore submodules (plus the gitignored build artifact `_version`, absent from
the worktree); `python scripts/dump_public_api.py` run against both trees gives
**byte-identical** 733,876-byte dumps; the manifest confirms `numbers`,
`pdstable` and `defaultdict` are frozen `pdsfile.pdsfile` members and that the
re-export form preserves them. **Ratchet:** `ruff check --isolated --line-length
100 --target-version py310 --select E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF --ignore
PT011,SIM105,SIM108` per file gives parent `pdsfile.py` 85 violations over 18
codes and HEAD 80 + 3 (`_index_rows`) + 2 (`_opus`) = 85 over the same 18 codes;
`RUF005` 8 → 6+1+1 and `UP024` 13 → 10+2+1; both new entries are strict subsets
of `pdsfile.py`'s entry, and no code could have been dropped from `pdsfile.py`
because every one still fires there. **Gates:** `ruff check src/pdsfile tests
scripts` → all passed; `pytest tests/api/` → 16 passed; `run-all-checks.sh` with
every holdings env var unset → all six sub-checks green, **82 passed / 800
skipped** (the parent worktree gives **80 passed / 800 skipped**, so +2 exactly).
**§6.2 evidence:** I re-reduced all six junit XMLs in `runs/p19-{base,head1,head2}/`
with my own `xml.etree` reducer and diffed them: `--mode ns` 880 → 882 with
**only** the two `test_no_mixin_is_shadowed_by_a_pdsfile_subclass[Pds3File|Pds4File]`
ids added and nothing moving in either direction; `--mode s` 558 → 558 with a
zero-line diff; head1 and head2 reduce identically; my reductions are byte-identical
to the `p19_*_{ns,s}.txt` files on disk. Non-vacuity holds: the baseline
`measured_files.txt` contains only worktree paths and **no** `_index_rows.py` /
`_opus.py`, HEAD's only main-tree paths. Freshness holds: last `src/pdsfile/`
commit `cf35a0f` at 17:39:31, the head2 XMLs are written 17:42:28 / 17:44:16
(and started 17:39:41 / 17:42:34 per their `timestamp=` attributes). **Sniff:** I
dumped `__bases__[0].__name__` and the sniff's verdict for all 34 classes in the
hierarchy on both trees — identical everywhere, `True` for the same six pds4 rule
classes; the only difference anywhere is `PdsFile`'s own `__bases__`. **New
test:** mutation-tested in process — giving `Pds3File` an `opus_products` or
`Pds4File` a `get_indexshelf` turns *only* the new test red, with the right
message. **Behavior, beyond the set diff:** I wrote three probes and ran each
against both trees (holdings from `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR`,
`PDSFILE_TEST_HOLDINGS=full`): 8 real `opus_products` dictionaries + 5
`from_opus_id` + 2 `from_filespec` + 2 index tables exercised through
`get_indexshelf` / `child_of_index` / `find_selected_row_key(<,>)` /
`data_abspath_associated_with_index_row` / `data_pdsfile_for_index_row`
(**25,143 bytes of JSON, `diff` empty**); the same probe under
`use_shelves_only(True)` (**26,078 bytes, `diff` empty**); and a synthetic
index-row probe that forces the sniff's **PDS4** branch — the one the record
honestly reports as unpinned by the goldens — which is likewise identical between
the two trees. **§6.4:** `api_manifest.json`, `manifest_allowlist.json`,
`scripts/dump_public_api.py` and `tests/api/test_api_freeze.py` are untouched; no
golden or baseline record is edited; no `noqa`, `skip` or `xfail` is added; no
type annotations, no CRLF, no trailing whitespace, no PR-number narration in any
source or test comment.

## Major findings

**None.** I could not construct a case where this refactor changes behavior,
loses a reachable name, breaks the freeze, widens the ratchet, introduces a
cycle, or where a figure in the gate evidence is unbacked by an artifact I could
point at. The two added test ids are real, non-vacuous and are the ones deferred
entry 48 (raised by PR-18, owner PR-19) asks for.

## Minor findings

### m1 — `critiques/phase5-validation.md:2311`: the `_index_rows.py` line count is stale, in a sentence that says it is not

> `pdsfile.py`: 5,125 → 4,593 lines; `_index_rows.py` 308, `_opus.py` 284. All
> counted at HEAD.

Measured at HEAD: `wc -l src/pdsfile/_index_rows.py` → **313**. 308 is the count
at the extraction commit `2d2de4a`; round 1's docstring fix (`cf35a0f`) added 5
net lines and this figure was not refreshed. The other three numbers reproduce
exactly (5,125 / 4,593 / 284). It is a small number in a record whose whole
standing is that its numbers are measured, and it sits under the words "All
counted at HEAD".

**Fix:** change `308` to `313`.

### m2 — `critiques/phase5-validation.md:2623`: the `from_filespec` consumer count is 3 where the same PR's round-1 measurement says 4

> `| from_filespec | 3: obs_base_pds3.py:90, obs_base_pds4.py:33, do_import.py:1480,1482 (two on adjacent lines) |`

The column is headed **call sites** and the paragraph below it says "These are
**call sites**". The row lists four distinct call sites on four distinct lines,
and `critiques/pr-19/round-1.md:166` records the measurement as "The actual call
sites are **4**, 2, 1 and 1". I re-greped rms-opus and confirm four:
`opus/import/obs_base_pds3.py:90`, `opus/import/obs_base_pds4.py:33`,
`opus/import/do_import.py:1480`, `opus/import/do_import.py:1482`. The 3/2/1/1 row
set is otherwise correct, as is the rms-viewmaster 3. This is the one table the
record says it corrected in place *because* a wrong figure here is the defect
class PR-18's round-3 Major was about — and the correction landed one short.

**Fix:** `4:` instead of `3:`, and drop the "(two on adjacent lines)" parenthetical
or reword it to "two of them on adjacent lines".

### m3 — `critiques/phase5-validation.md:2453-2454`: "21 suppressed violations across the three files" is not a number that reproduces

> The distinct (file, code) pairs move 18 → 18 + 2 + 2, and the number of
> suppressed violations is unchanged at **21** across the three files.

Read as written — violations across `pdsfile.py`, `_index_rows.py` and
`_opus.py` — the number is **85** on both sides (parent `pdsfile.py` 85; HEAD
80 + 3 + 2). 21 is the subtotal of just the two codes that move
(`RUF005` 8 + `UP024` 13 = 21 → 6+1+1 + 10+2+1 = 21). PR-18's equivalent sentence
(`:1711`) wisely carries no number at all. As written the figure cannot be
reproduced from the stated scope.

**Fix:** either "…is unchanged, at 85 across the three files" or "…and the two
codes that move account for 21 violations before and after".

### m4 — `src/pdsfile/_index_rows.py:29-35`: the class docstring's state contract is presented as exhaustive and omits three things the code touches

> The state these methods touch all lives on PdsFile, in two kinds. The lazy
> properties they read are is_index, indexshelf_abspath, index_pdslabel,
> filename_keylen, childnames and childnames_lc. […] child_of_index also
> *writes* column_names […]

Measured with `inspect.getattr_static` over every `self.`/`cls.` attribute the
module's AST touches, the moved code also reads two further **lazy properties**
on `PdsFile` — `exists` (`_index_rows.py:56`, in `get_indexshelf`) and
`label_abspath` (`:197`, in `child_of_index`) — and one **class attribute**,
`CACHE` (`:185`). It also writes a second attribute besides `column_names`:
`pdsf._exists_filled` on the freshly built row object (`:212`, `:217`). The
sibling `_opus.py:19-23` docstring does enumerate its class attributes, so the
omission of `CACHE` is also an inconsistency between the two modules this PR
adds. Nothing is broken — all four resolve through `PdsFile` at run time — but
this is the same "enumeration stated rather than measured" shape that round 1
already corrected in this exact docstring, and a Phase-5 reader uses this
paragraph to check that the mixin adds no state.

**Fix:** add `exists` and `label_abspath` to the lazy-property list, name `CACHE`
as the class attribute the methods read (matching `_opus.py`'s form), and extend
the write clause to "…also *writes* `column_names` … and sets `_exists_filled` on
the row object it constructs".

### m5 — `critiques/phase5-validation.md:2150-2151`: the superseded head run is attributed to a commit that did not exist when it ran

> The superseded head pair (17:04:18 and 17:06:10, taken at `bc5147e`)…

`bc5147e` was authored at **17:22:39**, sixteen minutes *after* those XMLs were
written. The tree's `src/` at run time was `b554c77` (17:01:22), which is
byte-identical under `src/pdsfile/` to `bc5147e` — so the substantive claim (the
superseded run measured the same source) is true, and round 1's own record dates
that run against `174fe7a` correctly. But the label as written is checkably
false, and this record's freshness argument is exactly the place where commit-vs-run
ordering has to be right.

**Fix:** "taken at `b554c77` (the last `src/` commit before the regeneration; its
`src/pdsfile/` content is what `bc5147e` also carries)".

## Deferred findings

### D1 — the mixins' hand-written "state contract" docstrings drift, and a mechanical check is cheap

m4 is the second round in a row to correct the same paragraph in the same file by
measuring it. Every one of these enumerations is derivable: an AST pass collecting
`self.`/`cls.` attribute names per mixin module, classified with
`inspect.getattr_static(PdsFile, …)`, is ~20 lines and would additionally catch a
genuinely **stranded** attribute — a name a moved method reads that no longer
resolves on `PdsFile` — which is a real failure mode the current
`test_mixin_collisions.py` does not cover (it checks what mixins *define*, never
what they *read*). That is a new assertion in a test file, so it adds ids and
this PR's gate forbids it.
**Owner:** PR-22 (core finalization), or whichever Phase-5 PR next edits the
mixin harness.

### D2 — the PDS4 branch of the `__bases__` sniff is testable without an index shelf

The record's deferred entry 51(a) reports, correctly, that forcing the sniff
*off* changes no test outcome on this holdings copy, and traces it to the PDS4
metadata shelves being absent (I confirmed: `get_indexshelf` on both PDS4 index
tables under `PDS4_HOLDINGS_DIR` raises `OSError: Pickle file not found`). But
the branch does not need a shelf. Constructing a rule-subclass instance with
`cls.__new__(cls)`, setting `is_index_row`/`row_dicts`/`column_names` by hand and
calling `data_abspath_associated_with_index_row` exercises `get_keys` directly —
I did exactly that for a pds3 and a pds4 rule class over four synthetic row
dictionaries, got visibly different answers on the two sides of the branch
(`BUNDLE`/`PATH_NAME` handling), and confirmed the results are identical between
the parent tree and HEAD. A test of that shape would close 51(a) at near-zero
cost and with no holdings dependency at all.
**Owner:** Phase 6, alongside entries 50 and 51.

### D3 — `_version` in `dir(pdsfile)` is a gitignored build artifact, not a name

Not an issue with this PR; recorded only so the next reviewer who diffs
`dir(pdsfile)` between the main tree and a `git worktree` does not spend time on
it. `src/pdsfile/_version.py` is generated by setuptools-scm and matched by
`.gitignore:169`, so it exists in the main tree and not in a fresh worktree, and
any package-namespace diff between the two will show it.
**Owner:** nobody; informational.

## Verdict

**goal met** — 0 Major, 5 Minor, 3 Deferred. The extraction is byte-for-byte
apart from the four sanctioned deferred-import lines, every reference is updated,
the freeze and the ratchet are intact, the behavior evidence reproduces exactly
from the artifacts on disk, and the two added test ids are the ones the PR is
entitled to add. All five Minors are record- or docstring-accuracy defects; none
touches behavior, and fixing them requires no change under `src/pdsfile/` except
m4's docstring.
