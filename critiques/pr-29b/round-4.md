# PR-29b review round 4 — all 68 members of `_properties.py`, re-read

Fresh reviewer subagent, no context from this session or any other round. Surface: the
module docstring and all 68 members, every one of which had had exactly one adversarial
read -- the ten by round 1 and the other 58 by round 3.

**The brief listed the forty-four sentences those two rounds had rewritten, by member and
by claim**, and asked for a verdict on each plus a `[CHANGED]` or `[ORIGINAL]` tag on every
finding. That is what the round exists for.

**Twelve findings. Five are `[CHANGED]`, six are `[ORIGINAL]`, and one is
`unverifiable`.** Every finding was re-verified by the executor before it was acted on;
none was rejected.

## The process note the reviewer opened with, which is a finding about this PR

The file changed under the reviewer mid-read, because the executor was still applying round
3's corrections when round 4 started: sixteen of the forty-four listed sentences were absent
from the text it first read. It noticed, re-read all 68 after the change, and re-ran every
measurement rather than reporting against a tree that no longer existed.

That is the executor's mistake and it is recorded here rather than glossed. **A second read
must start from a frozen tree.** The cost this time was the reviewer's time and nothing
else, because it caught the change itself; had it not, its verdicts on those sixteen would
have described prose that was never in the branch.

## The five `[CHANGED]` findings

* **`local_viewset` can store None, and round 1's correction said it could not.**
  `PdsViewSet.from_pdsfiles()` returns None when nothing it was handed is displayable, and
  an existing viewable whose recorded width is zero -- which is what an image PIL could not
  open gets -- is exactly that. The slot's guard tests `is not None`, so such an object
  re-derives on every access. `viewset` converts the same None to False and `local_viewset`
  does not, which makes the two look symmetric when they are not. Reproduced by forcing the
  shape to `(0, 0)`: the property returns None twice and the slot stays None. The reviewer
  also scanned 2,086,994 preview shelf entries and found no zero-width viewable, so in this
  tree it takes a PIL failure to reach; the claim was absolute regardless.

* **`filespec`'s `Returns:` contradicted its own body.** Round 3 corrected the body to say
  the prefix is `bundlename_`, empty in the archive and checksum trees, and left the
  `Returns:` listing two cases neither of which is what an archive file gets. The partial
  fix, inside a single docstring this time.

* **`viewset_lookup`'s "'default' is the one every other property asks for."** Of its two
  callers, `viewset` asks for `default` and `all_viewsets` asks for every key *except*
  that one, three times, each guarded by `if key != 'default'`.

* **The module docstring's list of which properties name their slots by the property they
  read.** Round 3's correction named four. Measured, only `viewset` does it; `local_viewset`
  names them one by one and its list is exact rather than a lower bound, and `all_viewsets`
  and `data_abspaths` name none.

* **The module docstring's "wherever that changes the answer."** Five members --
  `opus_id`, `opus_type`, `opus_format`, `is_index` and `indexshelf_abspath` -- name only
  the merged directory, and an index row pre-sets all five. For `opus_type` that changes the
  answer: the row reports nothing where the rules would give it
  `('metadata', 5, 'rms_index', 'RMS Node Augmented Index', False)`. The promise is narrowed
  again and this time the five docstrings are made to keep it.

## The six `[ORIGINAL]` findings

* **`width`'s "the only two properties that reach the filesystem"** is true of `_info`'s
  readers and false as written of the module: seven other members reach it by their own
  routes.
* **`all_versions` named the wrong collision mechanism.** It credited `version_info()`'s
  three-part truncation. A fourth version part can never reach `version_rank`, because
  `BUNDLESET_PLUS_REGEX` captures at most three; the reachable collision is the arithmetic
  one, `_v1.100` and `_v2` both ranking 20000. **Deferred entry 224 made the same mistake
  and is corrected with it** -- the entry and the docstring were written from the same
  wrong reading, which is what makes a record no safer than the prose it describes.
* **`label_basename` fills five other-property slots, not four**, because
  `internal_link_info` reads `isdir` on its way.
* **`has_neighbor_rule`'s "both shipped subclasses carry one rule"** ignores the nineteen
  per-bundle-set rule modules that prepend their own. The conclusion survives, which the
  reviewer established by checking every prepended rule rather than by assuming.
* **`version_info`'s worked-example comment** is wrong by a factor of ten, found
  independently for the third time in this PR. It is comment text and stays; entry 225.
* **`absolute_or_logical_path`'s second case is unverifiable.** The reviewer could not
  build an object with no absolute path other than a merged directory:
  `from_logical_path` either resolves one against the preloaded root or raises. The clause
  is dropped rather than kept on a guess.

## Discoveries about the code

1. **`_recache()` silently fills `_isdir_filled`.** It calls `CACHE.set`, whose lifetime
   function reads `arg.isdir` for any object with a non-empty interior, so for an object
   already in the cache *every* lazy property here fills that slot as a side effect of its
   own `_recache()`, whether or not its body touches `isdir`. Every "fills these slots" list
   in the file is short by one under that condition. The reviewer reports it cost it a false
   lead before it traced it.
2. `PdsViewSet.from_pdsfiles` returns None rather than an empty set, which is finding 1's
   root.
3. A physical category directory is a live hazard at four call sites and two now document
   it; `global_anchor` and an index row's `anchor` inherit it undocumented.
4. `filename_keylen` is confirmed the only slot-writer with no `_recache()`, 41 of 42.

## What the reviewer checked hard and found correct

Twenty claims, most of them freshly written by rounds 1 and 3. Among them: `childnames`'
info-first threshold, verified against an 11-row table and a 3,745-row one, which fills
exactly the eight slots the docstring lists; `internal_link_info`'s four anchors, with the
real occurrence counts for each of the four prefixes across the link shelves, and the
two-level case resolving through the category and dropping the version suffix;
`index_pdslabel`'s PDS4 `SyntaxError`, reproduced; `_info`'s "with any children"
qualification, reproduced on both a two-child and a zero-child checksums bundle set;
`multipage_view_allowed`'s claim about the shipped rules, by tallying every `VIEW_OPTIONS`
tuple in both rule packages; `global_anchor`'s unescaped space, by finding the real
basename that carries one; and `filename_keylen` reporting 8 on a bundle-set directory with
no rows at all.
