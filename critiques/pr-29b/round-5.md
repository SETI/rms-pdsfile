# PR-29b review round 5 — `pdsfile.py` and `pdsviewable.py`, re-read

Fresh reviewer subagent, no context from this session or any other round. Same 63
functions, three class docstrings and two module docstrings as round 2, read again after
round 2's corrections were applied.

**The brief named the fourteen sentences round 2 had rewritten, one by one, and asked for a
verdict on each**, plus a `[CHANGED]` or `[ORIGINAL]` tag on every finding. That is the
whole point of the round: PR-29a measured that eleven of its round-4 findings were
correcting sentences round 2 had itself written, and a corrected sentence has been written
once and verified zero times.

**Nine findings. Five are `[CHANGED]` and four are `[ORIGINAL]`.**

## The verdict on round 2's fourteen sentences

| # | sentence | verdict |
|---|---|---|
| 1 | the `_local_fs.py` bullet, rewritten | correct |
| 2 | "Every name this module binds is part of the package's public surface" | **wrong** |
| 3 | the None `disk_`/`root_`/`html_root_` copied on to children | correct |
| 4 | `new_merged_dir()`'s four-that-answer and three-that-do-not | correct, all seven run |
| 5 | `from_abspath()`'s `ValueError:` entry, including "cannot be reached" | correct |
| 6 | the missing-voltype default and its `checksums/archives` example | **wrong for two of the three classes** |
| 7 | what an unanswerable `from_path()` description raises | correct, all four run |
| 8 | "every alternative of both bundle-name patterns requires an underscore" | correct |
| 9 | a scaled copy's dimensions matching where the request is an indexed size | correct, 3000 random sets |
| 10 | the `PdsViewSet` class docstring's account of which lookups serve a named-only set | **wrong, in both directions** |
| 11 | `append()`'s account of the damaged set | **wrong** |
| 12 | the `jpg-<n>` fallback being unreachable | correct |
| 13 | `iconset_for()`'s requirement and the closed `document_generic` | correct |
| 14 | the `_properties.py` bullet's 64 / 40 / 39 / 24 (unchanged by round 2) | correct, exact |

**Five of the fourteen did not survive**, and every one of the five is a sentence that
reads as freshly verified because it was.

## The five `[CHANGED]` findings

* **The public-surface claim contradicted its own next sentence.** Round 2 replaced "every
  public name of the package resolves as `pdsfile.pdsfile.<name>`" with "every name this
  module binds is part of the package's public surface", and then said two sentences later
  that the manifest defines the surface. By that authority the claim is false: the module
  binds 46 non-dunder names and the manifest lists 32, the fourteen it omits being the nine
  mixins and the five private path helpers -- which the file's own comment calls private.
  The direction was corrected and the new sentence was wrong in the other direction.

* **The `checksums/archives` worked example is PDS3's only.** The rule round 2 wrote is
  right -- the *voltype* defaults to `BUNDLE_DIR_NAME` -- and the example it derived with
  "so" is right for `Pds3File` and wrong for `Pds4File` and for `PdsFile` itself, the class
  the docstring is attached to. Run: `checksums-archives-volumes` and
  `checksums-archives-bundles`.

* **`full_size` has half the fallback chain the sentence gave it.** Round 2 wrote that a
  named-only set is served by `for_width()`, `for_height()`, `for_frame()` and `full_size`.
  The first three fall back to the member named "full" and then to an arbitrary member;
  `full_size` has only the first, and raises IndexError on a named-only set holding nothing
  called "full". `full_size`'s own docstring states this correctly -- the class-level
  summary was the copy still saying the old thing, which is the **partial fix** pattern
  PR-29a's record named and asked the next PR to watch for.

* **And it was wrong in the other direction about the other three.** `thumbnail`, `small`
  and `medium` go through `by_match()`, which iterates *every* member, named ones included,
  so a named viewable whose path carries `_thumb` is returned normally. Run: it is.

* **`append()`'s damaged set is not deterministic.** Round 2 wrote that the size lookups
  keep answering and that `by_match()` and the three properties built on it "fail
  permanently ... which walk every member". The members are held in a Python `set` and
  every search returns the **first** match in iteration order, which depends on identity
  hashes. Run 200 times each: `by_match` succeeded 195 and raised 5; `thumbnail` succeeded
  120 and raised 80; `for_width` on a set with nothing indexed succeeded 100 and raised 100.
  A sentence asserting "permanently" and "too" where the answer is a coin flip is the worst
  kind of correction, because it is more specific than the vague claim it replaced.

## The four `[ORIGINAL]` findings

* **The pickle rationale for keeping the `class PdsFile` statement in this file is false
  for every instance that is actually cached.** Pickle records the *instance's* class, and
  every object the package hands out is a rule subclass. Run:
  `type(p).__module__` is `pdsfile.pds3file.rules.COISS_xxxx`, and `pdsfile.pdsfile` does
  not appear in `pickle.dumps(p)` at all. Only an instance of `PdsFile` itself would record
  it. The constraint may still be right; the reason given for it is not. Deferred
  observation.
* **`IDX_EXT` and `LBL_EXT` are defined only on the subclasses**, which the module map's
  "the data a mixin reads is defined here" denies. Three sibling module docstrings --
  `_local_fs.py`, `_associations.py` and `_properties.py` -- say so explicitly, so this was
  the fourth copy of a claim already corrected in three places. The partial-fix pattern
  again, across modules this time.
* **`checksums_` and `archives_` end in a hyphen, not a slash**, so the rule "an attribute
  whose name ends in an underscore is empty or ends in a slash" is false for two attributes
  the same paragraph names two sentences earlier. The consequence the rule was stated for
  still holds.
* **`is_logical_path`'s case-sensitivity contrast draws the opposite conclusion from the
  same two lines as `from_abspath`'s `Raises:` entry.** Both docstrings are about the same
  pair of statements, one saying `from_abspath` finds the component case-insensitively and
  the other saying the case-insensitive lookup is unreachable. The second is right, and it
  is round 2's own finding 6.

All nine were re-verified by the executor before they were acted on; none was rejected.

## Discoveries about the code

1. `from_path('')` hardcodes `volumes` where every other voltype default uses
   `BUNDLE_DIR_NAME`, so `Pds4File.from_path('')` gives `volumes` rather than `bundles`.
2. `from_path`'s second scanning loop is dead, confirming round 2's finding independently.
3. `PdsViewSet.append` drops all but the first member of a `PdsViewSet` handed to it.
4. `load_icons` excludes every JPEG, because `'jpg'` in its extension test is missing a dot.

## What the reviewer checked hard and found correct

The `_properties.py` bullet's counts were re-derived from the AST for the second time in
this PR and are exact. `new_merged_dir()`'s seven slots were diffed programmatically
against `__init__`'s 42 and then all seven were run on a live merged directory. The
size-selection rule was brute-forced over 2,000 random width sets and 520 requests with
zero deviations, and the rounding claim over 3,000 more. The `rpartition()` reasoning behind
the unreachable `jpg-<n>` branch was confirmed by building a tree of PNGs under `jpg-999/`
and reading the nominal sizes back.
