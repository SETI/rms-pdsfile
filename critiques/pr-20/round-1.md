# PR-20 — adversarial pre-PR review, round 1

**Reviewer:** fresh, no development context.
**Diff reviewed:** `git diff origin/pr-19-opus-index-rows...HEAD` (head `08ceb6f`,
base `bf42ae7`), 3,031 lines. Eight files: `pyproject.toml`,
`src/pdsfile/pdsfile.py`, `src/pdsfile/_sorting.py` (new),
`src/pdsfile/_associations.py` (new), plus four record/plan files.
**Date:** 2026-07-27
**Verdict:** **goal met** — 0 Major, 8 Minor, 0 new Deferred.

## What the reviewer verified independently, and how

It re-derived rather than read. Its own AST pass over
`git show bf42ae7:src/pdsfile/pdsfile.py` reports `PdsFile`'s own body going
137 → 110 `FunctionDef`s, with the 27 lost names **exactly** the 27 the two
mixins define (`lost - moved` and `moved - lost` both empty, zero names gained),
all 27 moved segments byte-identical **and all 110 remaining definitions
byte-identical too**, the three base windows appearing verbatim with banners and
blank lines intact, definition order preserved, and zero non-`FunctionDef`
statements in the moved window. It confirmed `is_logical_path` is still in
`vars(PdsFile)`, byte-identical, still owned by `PdsFile` per
`inspect.getattr_static`, and that the module-level tail is untouched.

On the gates it ran, not read: `scripts/dump_public_api.py` on a worktree at
`bf42ae7` and at HEAD (**733,876 bytes each, `diff` empty, both stderr empty**);
`pytest tests/api/` (16 collected on both sides); `git diff --stat` over the four
§6.4-prohibited paths and over `tests/` (both empty); all 18 ratchet codes with
`--isolated --output-format concise --line-length 100` on all four files (**every
code conserves**; only `E701` 11→10+1+0, `RUF005` 6→2+4+0, `UP024` 10→9+0+1 move;
total 80 both sides) plus the converse check with the full project select set and
no per-file entry. It re-derived both outcome sets from the raw junit XMLs with
its own reducer and reproduced ns 848/34 (882 ids) and s 555/3 (558 ids) on both
sides with an **empty set diff**, matched its reduction against the committed
`.set` files, and checked freshness against the mtime of the last change under
`src/pdsfile/`. It reproduced the whole of §9's per-test-context table from the
coverage database — 224 contexts, 20 modules, every per-method count including
the four zeros — the consumer call-site counts, both docstring contracts in both
directions, and the mixin/subclass intersections.

Its own sweeps found **zero bare `Name` references** to any of the 27 symbols
anywhere in `src/`, `tests/` or `scripts/`; no `PdsFile`/`Pds3File`/`Pds4File`
`Name` node or string constant in either new module; module-level imports at
column 0 only; `sorted(vars(pdsfile.pdsfile))` 50 → 52 with nothing lost;
`pdsfile.pdsfile._needs_glob is pdsfile._path_utils._needs_glob`; and the pickle
path `pdsfile.pdsfile.PdsFile` unchanged. It also checked the discipline rules:
no absolute holdings path in the diff, no inline annotations, no PR-number or
"moved from X" narration in code comments, Conventional Commit titles, move
commits pure apart from the itemized header and ratchet edits.

## Major

**None.**

## Minor — all eight accepted, none rebutted

Every one is a figure or a phrase in a committed record, the sub-plan or one new
docstring. **Each was re-measured by the executor before being fixed**, rather
than corrected on the reviewer's say-so; all eight measurements reproduced the
reviewer's.

| # | Finding | Measured | Fix |
|---|---|---|---|
| 1 | "Core → moved, **12** sites" | **11** — `islabel:1166`, `is_viewable:1186`, `split:1233`, `childnames:1367,1377`, `_info:1464`, `local_viewset:2145`, `all_versions:2541`, `viewset_lookup:2615,2644,2645`; the record's own enumeration in the same sentence already summed to 11 | 12 → 11 in `critiques/phase5-validation.md` and `plans/2026-07-27-pr-20-subplan.md` |
| 2 | "Within `_sorting.py`, **12** sites … within `_associations.py`, **4**" — two different counting rules in one sentence | **14** and **5**. 12 is the `self.`/`cls.`-only count and excludes `parent.sort_basenames:257` and `pdsf_dict[path].sort_basenames:333`, which the same sentence names; 4 is the distinct caller→callee-pair count and hides that `associated_abspaths` recurses at `:109` and `:131` | both counts restated as 14 and 5, with the rule stated and every site's line number given |
| 3 | sub-plan says "Sibling mixins → moved, **2** sites" and lists three | **3**: `_index_rows.py:163`, `_opus.py:105`, `_opus.py:244`. The validation record already said 3 | 2 → 3 in the sub-plan |
| 4 | "The **two** in-class banner comments moved with their blocks" | **3**: `# How to split and sort filenames` and `# Transformations` → `_sorting.py:64` and `:419`; `# Associations` → `_associations.py:72` | two → three, with the three destinations named |
| 5 | "a separate **three-line** commit (`48b0605`)" | `git show --stat` says **4 insertions** — three comment lines and the blank that separates them from the method | "four-line commit (three comment lines and the blank)" |
| 6 | deferred entry 56: "The other **four** green controls" | **5** — §10 records 7 class-(b) controls, 2 of which have the subset-assertion shape, and the clause itself then names five | four → five, and the category reworded, since `pdsfiles_for_basenames` is a caller that never checks a length rather than an unreached branch |
| 7 | §7 never measures the one class-shape property this PR changes | `PdsFile.__bases__[0]` moves `_DerivedPathsMixin` → `_AssociationsMixin`, and `_index_rows.py:254` sniffs `cls.__bases__[0].__name__` (deferred entry 49) while `test_mixin_collisions.py:72` pins only `__bases__[-1]` | the 34-class shape dump added to §7: `__bases__[0].__name__` differs for **`PdsFile` alone**, the sniff's verdict differs for **no class** and is `True` for the same six pds4 rule classes on both sides, `__bases__` differs only for `PdsFile`, and every MRO changes — which is why it had to be run rather than reasoned |
| 8 | `_sorting.py`'s docstring says "with no I/O of their own" 27 lines above a paragraph naming four methods that reach `_LocalFsMixin`'s `os_path_isdir` / `os_path_exists` | correct on both counts; the qualifier is defensible but reads as a contradiction | docstring reworded to "None of them reads the filesystem itself: the four that need to probe it delegate to `_LocalFsMixin`", and the same phrase replaced where it was reused as the rationale in the record and the sub-plan |

## Deferred

**None new.** The reviewer confirmed entries 55 and 56 (added by this PR) are
genuine and correctly scoped out, that the `__bases__[0]` fragility behind
Minor 7 is already fully covered by existing entry 49 — including its
"lists a mixin first" case — so it needs no new entry, and that entries 53 and 54
are correctly left open per the coordinator's direction.

## Consequence for the next round

Minor 8's fix touches `src/pdsfile/_sorting.py`, so §6.6 step 5 applies: the
full-data record is **regenerated** before round 2 rather than carried forward.
The other seven fixes touch `critiques/` and `plans/` only.
