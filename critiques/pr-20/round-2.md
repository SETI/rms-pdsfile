# PR-20 — adversarial pre-PR review, round 2

**Reviewer:** fresh, no development context, no knowledge of round 1.
**Diff reviewed:** `git diff origin/pr-19-opus-index-rows...HEAD` (head `df542ec`,
base `bf42ae7`), 3,164 lines.
**Date:** 2026-07-27
**Verdict:** **goal met** — 0 Major, 7 Minor, 1 Deferred.

## What the reviewer verified independently, and how

It re-derived, and it went further than round 1 in three places. Its AST diff of
`PdsFile`'s body reports 27 definitions removed and 0 added, the removed set
exactly `_SortingMixin`(23) ∪ `_AssociationsMixin`(4), and it checked byte
equivalence **both per definition and as whole-window blobs with md5s** — base
`pdsfile.py:3808–4266` ≡ `_sorting.py`'s class body and base `:4267–4567` ≡
`_associations.py`'s, inter-definition comments, the four `#### … for <plural>`
sub-headers and blank lines included, definition order preserved. It then
subtracted the window from the base file and confirmed the **only** other change
to `pdsfile.py` is the header imports, the class statement and the new banner.

It ran, rather than read: `scripts/dump_public_api.py` in worktrees at `bf42ae7`
and HEAD, each proved to import its own `src/` (byte-identical, 733,876 B, md5
matching the one the record cites); all 18 ratchet codes with the isolated
invocation, plus `ruff check src/pdsfile tests scripts` **at the intermediate
commit `34837f6` as well as at HEAD**; `scripts/clean_install_check.sh`; the
no-holdings job **at both base and HEAD** (82 passed / 800 skipped on both); and
its own `dynamic_context` coverage pass, which reproduced **all 27 per-method
context counts and all 27 module counts** in §9 exactly. On the full-data gate it
did not re-run the suite — it re-reduced all four junit XMLs with its own reducer,
got byte-identical results to the committed `.set` files, confirmed the empty diff
in both modes, and checked freshness against the last change under `src/pdsfile/`.

Its whole-tree call-graph sweep found **0 bare `Name` references and 0 imports**
of any of the 27 names anywhere in `src/`, `tests/` or `scripts/` — all 88 sites
are attribute lookups — and it confirmed the per-file counts the record gives.
`git diff --numstat` shows **no `tests/` or `scripts/` change at all** and that
both record files are purely additive (0 deleted lines).

## Major

**None.**

## Minor — all seven accepted, none rebutted

| # | Finding | Measured | Fix |
|---|---|---|---|
| 1 | `_SortingMixin`'s subclass-only-attribute sentence is wrong **in both directions**: it says `split_basename` and `basename_is_label` are the methods that need a subclass | By AST: `split_basename` → `BUNDLENAME_PLUS_REGEX`/`BUNDLESET_PLUS_REGEX`, `basename_is_label` → `LBL_EXT`, **`sort_basenames` → `BUNDLESET_PLUS_REGEX_I`**. Executed on a bare `PdsFile`: `split_basename` returns `'a.lbl'` **without error** (`SPLIT_RULES` is `None`, so it returns before either regex), `basename_is_label` raises `AttributeError: … no attribute 'LBL_EXT'`, `sort_basenames` raises `AttributeError: … no attribute 'BUNDLESET_PLUS_REGEX_I'` | the sentence now names all three readers and says which two actually raise and why the third does not — measured by executing them, not by reading the code |
| 2 | "`_sorting.py` 522 … all counted at HEAD" is stale | 523 at that HEAD — the file was 522 at its extraction commit and round 1's docstring fix added a line | corrected, and the sentence now says the counts are re-counted each round and that the growth is entirely in the class docstrings |
| 3 | §16 "Review loop" is an empty section although `critiques/pr-20/round-1.md` is committed in the same diff | the round-1 record is 84 lines, committed at `6350859`; §16's own rule says a row is due once the record exists | §16 populated with the round-1 row and the account of what it found |
| 4 | the sub-plan's own preamble promises an "as executed" delta and the file ends at §12 | PR-17, PR-18 and PR-19 sub-plans all carry one; two §-claims were explicitly forward-looking and unclosed | §13 "As executed" appended: the fourth commit the plan did not anticipate, the ratchet entry that §10 expected to shrink and did not, and the eleven green negative controls §11 did not anticipate |
| 5 | "zero string literals naming any of the three as well" is false as written | 4 such string constants: 1 in `_sorting.py`, 3 in `_associations.py`, **all four docstrings** — the intent (no class resolved by a string in executable code) holds | restated as "no string literal is used to resolve a class by name", with the docstring classification measured by the parse, and contrasted with `_index_rows.py`, where PR-19's sniff really does |
| 6 | the contract's exhaustive out-of-scope list omits `set` | `sort_logical_paths` calls `set.add` on `top_level_names` and on `child_names[path]`; a receiver-type sweep names `set` and `os.path` as the only two categories the prose did not | "set" and "os.path" added — the list is now exactly the receiver types the sweep finds |
| 7 | the three banner citations mix conventions (two cite the `####` rule, one cites the text line) | correct; and worse, every line number in these two files moves whenever a review round edits a docstring, which is what had already happened | the line numbers are **removed**, not corrected: the project's own rule is to locate by symbol, and PR-19's round 3 established that a line number a later docstring fix will move is a defect generator. The three banners are now named by their text |

Minor 1 and Minor 6 touch `src/pdsfile/`, so §6.6 step 5 applies again: the
full-data record is **regenerated** before round 3.

## Deferred — one, recorded as entry 57

The reviewer found a **pre-existing** §3.4 confidentiality problem outside this
PR's diff: `plans/archive/2026-07-17-modernization-plan.md` carries a home-rooted
holdings path. The executor verified and bounded it without reproducing the
strings: **two distinct tokens, three occurrences**; **neither is the current
limited testing copy's root** (compared against `PDS3_HOLDINGS_DIR` /
`PDS4_HOLDINGS_DIR`); every other holdings path in that file is under
`/data/pdsdata`, which §3.4 names in the open; the same three occurrences are
present at `bf42ae7` and on `origin/rewrite` and the file does not exist on
`origin/main`; and a sweep of **every tracked file** for the current limited
copy's root returns **zero** hits. So it is stale history rather than a live
leak. It is `critiques/deferred-observations.md` entry 57 and is surfaced to the
owner, not fixed here: it is outside PR-20's diff, and scrubbing an archived plan
is an owner decision rather than something an extraction PR does in passing.

The reviewer explicitly declined to raise three things as findings, and was right
to: deferred entries 53 and 54 (settled as not PR-20's), the 3-blocks-into-2
mapping (settled by the coordinator, and it verified the execution and the
documentation of it), and the alphabetical base order (the addendum is the
authority; the Phase-5 preamble's contrary illustration on this branch is the
stale text §2.1 warns about).
