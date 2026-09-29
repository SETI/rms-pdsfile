# PR-22 — adversarial review round 2

**Date:** 2026-07-28
**Reviewer:** a second fresh, no-context opus-class subagent (§6.6), given the
same materials as round 1 and no knowledge that round 1 happened.
**Diff reviewed:** HEAD `ee9a661` ("docs: record round 1 and point the record at
the regenerated full-data run").
**Verdict:** **goal met** — 0 Major, 8 Minor, 1 Deferred.

## What the reviewer re-derived independently

Again, nothing was taken on trust. It reproduced the 1,557-line byte comparison
and the per-definition one — arriving at 53,113 bytes by a different route, from
`ast.get_source_segment`'s 51,927 plus the decorator and indent bytes that
`get_source_segment` drops — and the 34-of-37 core remainder with its five-line,
zero-plus diff. It confirmed 0 class-level assigns in the mixin and 41 written
attributes all created by `PdsFile.__init__`; 61 → 61 class-level `Assign`
targets; the API dump on both tips **and** a full `dir()` comparison over seven
modules and three classes, which is stricter than the dump because it also sees
private names — the only additions are `pdsfile._properties` and
`PdsFile._PropertiesMixin`, both underscore-prefixed, and nothing is removed. It
re-derived every ratchet count and additionally checked that **both** entries are
*minimal* (every code listed still fires). It ran its own two-pass dead-code
detector over `pdsfile.py` and all ten private modules at the parent and at HEAD —
8 candidates and 1 respectively, the survivor being a data-shape doc comment in
`_opus.py` that is correctly kept. It diffed the recorded `.set` files itself,
re-ran the no-holdings pass at HEAD (92 passed / 800 skipped), checked freshness
against the last `src/` commit, reproduced the PR-15 bug-1 negative control and
the 641/24 unmutated baseline, re-derived the whole state contract including the
40/24 split and the 47 `_recache` sites, and **broke the entry-42 check both ways
on a scratch tree** — confirming again that the tail-placed import is caught only
by the `sys.modules` assertion. It also checked that **all eight commits** are
individually green (`ruff check`, `import pdsfile`, `tests/api/`).

Everything reproduced. All eight findings are text.

## Major

**None.**

## Minor — all eight accepted, all eight fixed

### Minor 1 — three docstring characterisations of the 24 no-slot properties are wrong

`src/pdsfile/_properties.py`. Round 1's fix enumerated the 24 properties that hold
no `_X_filled` slot and added a sentence about what the sixteen multi-statement
ones do: "the rest read a slot another property fills, or a shelf, and shape the
result". **Re-measured: false for four of the sixteen** — `filespec` reads only
`interior`/`bundlename_`/`bundlename`, `absolute_or_logical_path` only
`abspath`/`logical_path` (both plain `__init__` attributes), `parent_logical_path`
reads through `parent()`, and `has_neighbor_rule` reads the `NEIGHBORS` class
table.

A **second** attempt at the same sentence — "eight are a single `return`
statement; the other sixteen are two to seven statements each" — was measured
before committing and is **also false**: the statement counts are eleven 1s,
eleven 2s, one 4 and one 7, and three of the eleven single-statement properties
are not a bare `return`. The sentence is now **dropped**: the enumerated list of
24 is the claim and nothing summarises it.

This is round 1's Minor 1 one level down, and the same lesson: §15's derivation
verifies name coverage in both directions and is structurally blind to a sentence
about what the bodies *do*.

### Minor 2 — the module map's lazy-property parenthetical lost round 1's exception

`src/pdsfile/pdsfile.py`. The map said "40 of them lazy (fill an `_X_filled` slot,
then `_recache()` so the cache keeps the filled object)". 39 of the 40 do both
halves; `filename_keylen` fills its slot without the call, which is the subject of
new deferred observation 62. Round 1's fix carried the exception into
`_properties.py`'s class docstring and not into this one. Fixed.

### Minor 3 — two inventories in the module map are incomplete

`src/pdsfile/pdsfile.py`. The `_local_fs.py` entry named four of
`_LocalFsMixin`'s five methods (`_non_checksum_abspath` missing) and the
"constructors" list omitted `_from_absolute_or_logical_path`. Both are private, and
other entries in the map are avowedly summaries — but **round 1's Minor 7 made
this map a complete inventory** when it added `_needs_glob` and `_GLOB_CACHE_SIZE`
to the `_path_utils` line, so consistency requires completing these two rather
than marking them illustrative. Fixed.

### Minor 4 — §19's heading and the sub-plan's item 8 carry a stale total

`critiques/phase5-validation.md` §19's heading said "why HEAD is 1,935" while its
own body said 1,938; `plans/2026-07-27-pr-22-subplan.md` §7 item 8 said 1,935 and
its own decomposition summed to 1,938. Both were the count at `57134ac`, before
round 1's three docstring lines. After round 2's fixes the figure is **1,939** and
all three places now say so.

### Minor 5 — §11 says seven mutations and lists six

`critiques/phase5-validation.md`. The negative-control table has six rows
(`exists`, `html_path`, `mime_type`, `version_info`, `formatted_size`,
`abspath_for_logical_path`); the other five controls are the monkeypatch ones in
§12. Corrected to six.

### Minor 6 — "PR-16–21 removed 2,889 lines net" attributes PR-15's +4 to PR-16–21

`critiques/phase5-validation.md` §19 and `plans/2026-07-27-pr-22-subplan.md` §7.
§18's own per-PR deltas sum to **2,893** for PR-16–21; 2,889 is the net change
from `rewrite`, which silently absorbs PR-15's **+4**. The total was right and the
label was not. §19's table now carries PR-15's +4 as its own row and PR-16–21's
2,893 as another, which also makes the decomposition reconcile against §18 line by
line.

### Minor 7 — the sub-plan's §2.4 still says `_recache` is read at 46 sites

`plans/2026-07-27-pr-22-subplan.md`. Round 1 corrected this to 47 in the record's
§5.2 (46 through `self.`, one through the sibling `pdsf` in `all_versions`) and
did not carry the correction into the sub-plan. Fixed, and §7 now records it as a
delta.

### Minor 8 — figures that move with the docstring edits

The module line counts, the moved blob's destination range in `_properties.py`,
the RUF005 line number, §18's PR-22 row and the ten-module total, and §10's
coverage figures were all re-measured at the final HEAD rather than carried
forward — the rule round 1's Minor 3 established.

## Deferred — one, appended as observation 65

**The "modules < 1000 lines" waiver names `pdsfile.py` and the rule modules, and
Phase 5 has produced a 1,684-line `_properties.py`.** No gate enforces the rule
and the extraction is owner-decided (§8.3), so this is not PR-22's to fix — but
PR-23 meets both `_properties.py` and the 1,044-line `pdscache.py` during its
style pass and needs to know whether the waiver extends. **Owner: owner decision,
before PR-23's churn checkpoint.**

## Consequences for the record

Minors 1, 2 and 3 changed files under `src/pdsfile/`, so by §6.6 step 5 the
full-data record was **regenerated again** before round 3. Minors 4–8 are
corrections to `critiques/phase5-validation.md` and the sub-plan.

**Eight findings: three in `src/pdsfile/` docstrings and five in records. For the
fourth PR running, none is in the extracted code.**
