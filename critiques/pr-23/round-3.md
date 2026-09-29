# PR-23 — adversarial review round 3

**Date:** 2026-08-03
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 2) — the third
distinct reviewer, given no reasoning from rounds 1 or 2 beyond their records
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `1bc3b13` (2,604 lines)
**Verdict returned:** **`goal met`** — **0 Major**, 6 Minor, 2 Deferred

New Minors, so the loop again does not terminate here. All six are fixed below
and a fourth — the §6.6 **scoped** round, hard cap — follows.

## Two checks this reviewer invented, which are stronger than anything the record had

Recorded because they are the round's real contribution:

1. **An AST control-flow skeleton diff, base vs head, over all thirteen changed
   source files.** The only structural differences are the intended ones —
   `SIM102` ×2, `SIM103` ×3, `SIM114` ×2, the `version_ranks` inversion, and index
   shifts from the two removed dead assignments. `_sorting.py`, `_opus.py`,
   `_path_utils.py`, `_preload.py`, `_index_rows.py`, `_associations.py`,
   `__init__.py` and **`pdsviewable.py` are skeleton-identical**. That is direct,
   mechanical evidence for the thing the 20 `E701` splits are most likely to get
   wrong: none of them moved a statement into or out of a block.

2. **Mutation-testing the differential probe**, in a scratch copy. Reverting
   `iconset_for`'s `E721` to `isinstance` flips a probe line from `AttributeError`
   to `KeyError`; reverting `__repr__`'s collapses
   `'PdsFile._PdsFileSubclass("/a/b")'` to `'PdsFile("/a/b")'`; hoisting
   `unblock`'s `return` out of the collapsed `and` makes `('$OK_PID', 0, 0)`
   disappear; undoing the `B020` rename blows the probe up. **The probe is not
   passing vacuously** — which is exactly the check §6.6 asks for and which the
   record could not have supplied about itself.

It also re-derived every gate: 892/892 and 558/558 with zero movement; the record
timely (last `src/pdsfile/` change `b5811c6` at 15:27:53, artifacts at 15:30 and
15:32); the API dump byte-identical; the ratchet 447 → 379 slots repo-wide with no
inline `noqa`; head's no-ignores derivation exactly the 33 with exactly the
recorded sites; `ruff format --check` reporting the same 13 files on both sides;
`linecov.py` reproducing 143/81/62 row for row and the probe's 36 and 105; the
banner commit token-identical; the MROs identical; the test id set unchanged. And
it applied the sub-plan's own "is there **any** provably-identical spelling" test
to all 33 freeze-locks itself and found them all sound.

## Minor

| # | Finding | Resolution |
|---|---|---|
| m1 | **§2's characterisation of the 38 unreached lines is false, and §2 contradicts itself 40 lines later.** It said none of the 38 is an `E721` fix; `pdscache.py:322` is one, as §2's own closing paragraph says. Three more (`_path_utils.py:136`, `_preload.py:201`, `_shelves.py:171`) are `F841` binding removals, which the sentence's list also did not cover. | **Fixed.** §2 now says 35 of the 38 fall into five named kinds and **names the other three** rather than folding them in, and says how the unreached `E721` is discharged instead (the metaclass argument plus the probe's direct evaluation of the predicate on a `str`, a `str` subclass, an `int` and a `bool`). |
| m2 | **Two governing documents describe a test assertion that is not in the tree.** Both `plans/2026-07-27-addendum-phase5-mixin-base-order.md` and the validation record still said the replacement was `object not in PdsFile.__bases__` **plus `PdsFile.__mro__[-1] is object`**; round 2 removed the second as a tautology. The addendum is the more serious: it is a plan document future PRs read. | **Fixed** in both, naming the `__module__` check that actually replaced it, and the record says why the earlier draft's assertion went. |
| m3 | **`pdsviewable.py` has round-1 m6's defect in the sibling file round 1 did not check.** Its re-export note sat directly above `import os`, so "Nothing below references pdslogger" read as covering `os`, which is used. | **Fixed**, matching `pdscache.py`. Block stays `I001`-clean. |
| m4 | **The sub-plan's "as executed" delta is two rounds stale** — 10 commits (branch has 15) and a 39-value probe (it has 55). | **Fixed**, including the round-2/3 rows and the probe's coverage figures. |
| m5 | **Mixed line-number conventions plus two wrong cites.** §5 of the sub-plan declares head numbers and is right; §4 still used base numbers unlabelled (7 cites). The record cited `_info_filled` at `pdsfile.py:635`/`:691` (really 634/690) and `_shelves.py:337` (really 338) — the latter load-bearing, since it is the precedent round 1's Major rests on. | **Fixed.** §4 now says "line numbers here, as in §5, are at the merge commit" and all seven are head numbers; both record cites corrected. |
| m6 | **The same `F841`-with-effect idiom is spelled two ways, and the record describes the old spelling.** Round 2 changed `_preload.py:201` to `_ = cls.CACHE[key]`; `pdsfile.py:1116` was still bare, and §4 still called both "bare subscript expression statements … only the `STORE_FAST` goes". | **Fixed.** Both sites are `_ = cls.CACHE[…]`; §4 says so. |

## Deferred (recorded, not fixed)

| # | Finding | Where it went |
|---|---|---|
| d1 | `pdscache.py`'s `flush` carries 6-space and 22-space indentation, invisible because ruff's `E1xx` rules are preview-gated. PR-23 edited the log lines at both sites and correctly did not re-indent. But the new ratchet header may lead a reader to think `python.mdc`'s indentation rule is now in force for core; it is not. | entry **76** |
| d2 | Whether prose may follow a mechanical fix is written down nowhere — round 1's m8 had PR-23 change three `IOError` mentions to `OSError` in comments and a docstring, which no ruff rule required. PR-24 faces the same question at much larger scale. | entry **77** |

## Effect on the deliverable

Two source edits, both one-liners and both cosmetic (`pdsviewable.py`'s comment
position, `pdsfile.py`'s `_ =`). Everything else is prose in the record, the
sub-plan and a plan addendum. The behavior of the package is what it was after
round 1.
