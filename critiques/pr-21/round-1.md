# PR-21 — adversarial review round 1

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6), given the PR-21
section of the plan, the Phase-5 preamble and mixin mechanics including the
alphabetical base-order rule and the note that the preamble's illustration on this
branch is stale, §2, §6.1/§6.2/§6.4, the progressive `.cursor/rules` compliance
schedule, the exact diff `git diff origin/pr-20-associations-sorting...HEAD`, and
read access to the repo at HEAD and to the real holdings.
**Diff reviewed:** HEAD `f2f4fc5` ("docs: record the PR-21 validation evidence and
topology").
**Verdict:** **goal met** — 0 Major, 5 Minor, 2 Deferred.

## What the reviewer re-derived independently

It did not take the record's word for anything: it re-extracted every moved
definition's source segment from `2df25ab` and from HEAD and compared them byte by
byte (all five classmethods, all four module functions, and the nine stay-list
definitions); ran a definition-level diff of the parent and HEAD `pdsfile.py` (5
removed, 0 added, 0 differing); compared `vars()` across seven modules **and**
`inspect.getattr_static` over all of `dir(PdsFile)`; imported nine modules
first-in-a-fresh-interpreter and additionally checked that all three commits
import cleanly from an isolated `git archive` tree; ran the API dumper on both
trees **and at all three commits**; re-counted all 18 ruff codes and re-ran the
converse check, including at commit 1 before `_preload.py`'s entry existed;
re-ran the no-holdings job (82 passed / 800 skipped, reproduced) and §10's
unmutated control baseline (737 passed / 34 skipped, reproduced); and reproduced
the byte totals, the `Name`-load counts, the `symtable` sweep, the mixin figures,
the 34-class shape dump and §15's docstring derivation.

## Major

**None.**

## Minor — all five accepted, all five fixed

### Minor 1 — "exactly one extra name: `pylibmc`" is wrong; there are two, and the second survives this PR

Raised against `critiques/phase5-validation.md`, `critiques/deferred-observations.md`
entry 58 and `plans/2026-07-27-pr-21-subplan.md` §5.3.

**Re-measured by the executor before fixing, and the finding reproduces.** With a
stub `pylibmc` on `PYTHONPATH`, the full manifest diff on the **parent** tree is

```
GAINED pdsfile.pdscache ['pylibmc']
GAINED pdsfile.pdsfile  ['pylibmc']
```

and on **HEAD** it is `GAINED pdsfile.pdscache ['pylibmc']` alone.
`src/pdsfile/pdscache.py:7` has its own optional `import pylibmc` behind a `try`,
and `pdsfile.pdscache` is one of the dumper's seven fixed modules
(`scripts/dump_public_api.py:37`), which Phase 5 does not touch.

This is the most consequential finding of the round, and not because of the
arithmetic: the record's framing implied that removing the `pdsfile.pdsfile`
occurrence was the whole story, when in fact **the freeze gate stays red on a
memcached-capable host after this PR**, via `pdscache`. Deferred entry 58 is the
artifact the owner acts on, and as written it pointed at the smaller half.

**Fixed** in all three places with the measured two-name result, plus an explicit
statement that only one half is PR-21's, that the other is untouched by Phase 5,
and that any fix must cover `pdscache` too — which, since editing the dumper or
the manifest is a §6.4 prohibition for the executor, makes it an owner decision.

### Minor 2 — the coverage statement totals were not reproducible and mixed two conventions

Raised against §9 and §12 of the validation record and entry 59.

**Re-measured, and the finding reproduces.** The first draft's totals came from an
AST statement count, which counts `try:` and other headers CPython emits no line
event for. Re-derived from **coverage's own** statement set
(`coverage.Coverage(data_file=…).analysis2(path)` against the head run's
`.coverage`), definition span = AST `def` line through end, decorators excluded:

| Definition | statements | hit | missing | first draft said |
|---|---|---|---|---|
| `preload` | **113** | **83** | **30** | 80 of 109, 29 missing |
| `get_permanent_values` | **21** | 13 | 8 | 8 of 20 |
| `load_volume_info` | 53 | 52 | 1 | 52 of 53 ✓ |
| `cache_category_merged_dirs` | 4 | 4 | 0 | 4 of 4 ✓ |
| `cache_lifetime` | 2 | 1 | 1 | 1 of 2 ✓ |
| `is_preloading` | 2 | 1 | 1 | 1 of 2 ✓ |
| `cache_lifetime_for_class` | 12 | 10 | 2 | — |

`preload`'s 113 include the 14 statements of its nested `_preload_dir`, all 14
hit. The file is 226 statements, 43 missing, 5 excluded (the `pragma: no cover`
lines of the `pylibmc` try/except).

**Fixed:** §9 now states the convention explicitly, names the AST-count mistake so
a reader can see which figures changed and why, and §9, §12 and entry 59 carry the
re-derived numbers. Nothing about §12's *conclusion* moves: the 30 uncovered
statements are the same memcached / `clear=` / `force_reload=` / early-return
branches the first draft enumerated line by line.

### Minor 3 — §8's heading and its body gave two counts for the same phrase

The heading says "17 codes conserve exactly, one shrinks"; the body said "Sixteen
codes conserve exactly and one code — UP015 — leaves `pdsfile.py` entirely".
Re-counted: of the 18 codes, **17 conserve** (11 unchanged, plus E501, E701, F841,
RUF005, UP031 which split, plus UP015 which conserves *by* moving entirely) and
**1 (I001) shrinks**. The heading and the commit message are right; the body was
the odd one out.

**Fixed:** the body now reads "Seventeen codes conserve exactly; one of those
seventeen — UP015 — conserves by leaving `pdsfile.py` entirely".

### Minor 4 — the sub-plan's "As executed" section was empty although the work did diverge

**Fixed:** §13 now records four items — I001's failure to meet §7 step 1's
"each code must conserve" criterion (and why a shrink is nonetheless compliant),
UP015 leaving as §7 step 3 anticipated, commit 3's title and banner text differing
from §6's placeholder wording and why, and the `pylibmc` count this round
corrected.

### Minor 5 — off-by-one line count in the sub-plan

`plans/2026-07-27-pr-21-subplan.md` §1.4 said `preload_and_cache.py` was 83 lines.
`git show 2df25ab:src/pdsfile/preload_and_cache.py | wc -l` is **82** (3,086
bytes), the section's own table bottoms out at line 82, and the validation record
already said "82 → 16". **Fixed** to 82.

## Deferred — both appended, neither built

1. **The freeze manifest is environment-dependent in `pdsfile.pdscache` too.**
   Folded into **entry 58**, which Minor 1 rewrote: the fix has to cover
   `pdscache` as well, and editing the dumper or the manifest is a §6.4
   prohibition for the executor, so it is an owner decision. Owner: unassigned.
2. **In-class banner rule-line widths are mixed.** Added as **entry 60**, owner
   **PR-23**, with the measurement behind it: `pdsfile.py` has 20 banner rule
   lines at 80 columns and 2 at 90, and the 90-column `# Preload management` pair
   moved into `_preload.py` with its block because reflowing a moved banner would
   be a content edit inside a move commit.

Neither is taken up here. A Deferred finding is deferred (common brief §5.1); the
rule exists because PR-17 spent two rounds on a voluntarily adopted one.

## What this round did not change

**No fix in this round touched anything under `src/pdsfile/`.** All five Minor
fixes are in `critiques/phase5-validation.md`,
`critiques/deferred-observations.md` and `plans/2026-07-27-pr-21-subplan.md`. By
§6.6 step 5 the full-data record therefore **carries forward** without
regeneration: the runs at 22:08:52 and 22:10:41 still postdate `a8f4cb3`, which is
still the last commit to touch `src/pdsfile/`.

All five findings were in records, the sub-plan or their own measurements — none
was in the extracted code. That is now the third PR in a row with that result.
