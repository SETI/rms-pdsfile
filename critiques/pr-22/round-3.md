# PR-22 — adversarial review round 3

**Date:** 2026-07-28
**Reviewer:** a third fresh, no-context opus-class subagent (§6.6), given the same
materials as rounds 1 and 2 and no knowledge that either happened. It was
additionally asked to check that **every number** stated in the record, the
sub-plan and the docstrings is currently true of the tree at HEAD, which is where
the two earlier rounds' findings had clustered.
**Diff reviewed:** HEAD `6305f02` ("docs: record round 2 and regenerate the
full-data record a second time").
**Verdict:** **goal met** — 0 Major, 7 Minor, **0 new Deferred**.

## What the reviewer re-derived independently

The third full re-derivation, and it went further than the first two in one
place that matters. Besides reproducing the byte comparisons (1,557 lines; 68/68
definitions; 53,113 bytes; 34-of-37 core remainder with a five-line, zero-plus
diff), the class-attribute conservation (61/61, mixin 0), the free-variable
sweep, the API dump on both tips, all seventeen ratchet codes and the ten-module
union, all three set diffs, the freshness chain, the eight dead-code lines at
three different commits, all nine boundary line counts and the §19 decomposition,
the whole 114-name contract derivation, the 40/39/24 property split, **all six**
negative controls and **all four** forced-wrong monkeypatch controls plus entry
61's green one — it broke the entry-42 check **three** ways rather than two:

| Mutation | Caught by |
|---|---|
| head-placed `from pdsfile.pdsfile import repair_case` in a mixin | the subprocess return code (circular `ImportError`) |
| tail-placed, after the class | **only** the `sys.modules` assertion, `assert 'True' == 'False'` |
| **`importlib.import_module('pdsfile.pdsfile')` at module level** | the `sys.modules` assertion — **and no AST walk over import statements could see it at all** |

and confirmed the two controls the design needs: a *function-local* deferred
import stays green, and the naive probe (no stub package) is red for all ten
private modules, so the stub-package construction is necessary rather than
decorative. It also re-ran the probe against `_path_utils.py` and
`preload_and_cache.py` by hand, confirming deferred observation 63's parenthetical
that `_path_utils.py` is clean today.

## Major

**None.**

## Minor — all seven accepted, all seven fixed

All seven are consequences of rounds 1 and 2's own fixes, not of the move.

### Minor 1 — "core lazy properties read" labels four properties that are not lazy

`src/pdsfile/_properties.py`. `is_bundle`, `is_bundle_dir`, `is_bundleset` and
`is_bundleset_dir` hold no `_X_filled` slot and recompute on every access —
measured — so under the definition of "lazy" the same docstring gives four
paragraphs earlier, they are not lazy. Relabelled `core properties read`, with the
distinction stated on the row.

### Minor 2 — "viewset_lookup reads through child" names the wrong method

`src/pdsfile/_properties.py`. `viewset_lookup`'s non-`self` PdsFile-side receivers
are `pdsf` (`isdir`, `viewset_lookup`) and `parent` (`pdsfiles_for_basenames`,
`viewable_childnames_by_anchor`). `child` is **`all_viewsets`**' receiver, and it
contributes only `VIEWABLES`, `isdir` and `viewset_lookup`, all of which are also
reached through `self` — so `child` is not one of the receivers that *justifies*
the widened walk. Corrected, and `all_viewsets` named.

### Minor 3 — the file banner kept the pre-round-1 claim

`src/pdsfile/_properties.py:3–4`. Round 1's 39-of-40 correction reached both
docstrings and not the two-line banner above them, which still said the lazy
properties fill a slot "and" write the object back to the cache. Fixed.

### Minor 4 — the core remainder is 1,774 lines, not 1,775

`critiques/phase5-validation.md` §5.1(c). The figure counted the elements of a
`str.split('\\n')` list, whose last element is the empty string a trailing newline
produces. The MD5 `e2be29a1…` quoted in the same sentence is the digest of exactly
that region and is unchanged, so the digest was right and the count was not.
Corrected.

### Minor 5 — "the six genuine non-`self`/`cls` receivers" is five

`critiques/phase5-validation.md` §15. Eight receivers carry a PdsFile-surface
attribute; two of the eight are `self` and `cls`, leaving six, and one of those six
is the `os.path` false positive the same sentence names. Five are genuine, and
they are now listed by name.

### Minor 6 — "three names a `self.`-only walk would have missed, one of them a write"

`critiques/phase5-validation.md` §15. Measured, a `self.`-only walk would have
missed **two** names outright (`pdsfiles_for_basenames`,
`viewable_childnames_by_anchor`, both reached through `parent`).
`_all_version_abspaths` is read through `self` in `all_version_abspaths`, so such a
walk finds the *name* and mis-classifies it as read-only, missing the write on
`pdsf` in `all_versions`. The distinction is worth keeping because it is the more
interesting failure. Rewritten.

### Minor 7 — the sub-plan's +82 term subtracts the wrong dead-code count

`plans/2026-07-27-pr-22-subplan.md` §7 item 8. The +82 is ~89 minus
`pdsfile.py`'s **seven**; eight is the count across the whole module set and would
give +81. §2.6 of the same document and §19 of the record both have it right.
Corrected, with both numbers stated.

## The one finding not fixed in place, with its reason

The reviewer also noted, marking it optional and in the same class, that the move
commit `a9a6053`'s message says "64 lazy properties" where 40 are lazy and 24
recompute on every access.

**Not amended, deliberately.** Changing that message means rewriting eight commits
on this branch, and `critiques/phase5-validation.md`, the three round records and
five commit messages all cite the current hashes (`a9a6053`, `930c8c4`,
`59a6405`, `edba42c`, `57134ac`, `32d50e7`, `0a2925c`, `1490fdb`, `6305f02`). A
rebase would invalidate every one of those citations to fix one adjective, which
trades a small inaccuracy for a large one. The reviewer's own suggestion — state
it correctly in the PR description — is what was done, and this paragraph is the
record of the decision.

## Deferred

**None new.** The reviewer confirmed that entries 61–65 already cover everything
it found that is out of scope, and verified entry 63's parenthetical by running
the probe itself.

## Consequences for the record

Minors 1, 2 and 3 changed `src/pdsfile/_properties.py`, so by §6.6 step 5 the
full-data record was **regenerated a third time** before round 4. Minors 4–7 are
corrections to the record and the sub-plan.

**Seven findings: three in a `src/pdsfile/` docstring and four in records. Across
three rounds and 23 findings, not one has been in the extracted code.**
