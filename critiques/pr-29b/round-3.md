# PR-29b review round 3 — the other 58 members of `_properties.py`, and its module docstring

Fresh reviewer subagent, no context from this session or any other round. Surface: the
module docstring and the 58 members round 1 did not cover. The ten of round 1 were named
and excluded. The class docstring was excluded as a mechanically derived state contract.

**Twenty-two findings and six discoveries about the code.** All are `[ORIGINAL]`: these 58
docstrings were on their first read, so the round carried no changed-sentence list. Every
finding was re-verified by the executor before it was acted on; none was rejected.

One finding was spent before it was filed. The reviewer measured that
`has_neighbor_rule`'s "in practice this is True for everything below the category level"
was false -- a bundle set directory is below the category level and answers False, because
the rule is applied to the *parent's* path -- and found on re-grepping that the sentence had
already been replaced by exactly that correction. The executor had found the same defect by
its own re-verification an hour earlier. Two independent readers, the same sentence, the
same measurement.

## The findings

| # | member | severity | what was wrong |
|---|---|---|---|
| 1 | `index_pdslabel` | wrong | the described failure does not happen and a worse one does: the extension substitution is a no-op when the path lacks the extension being replaced, so on PDS4 the index file itself is handed to the parser and **every PDS4 index raises SyntaxError** out of the property |
| 2 | `opus_type` | wrong | the second example tuple, `'Extra preview (full-size)'`, exists nowhere in the rules; the real text is `'Extra Preview (full)'`, which `_opus.py`'s parallel example already had right |
| 3 | `filespec` | wrong | the prefix is `bundlename_`, not `bundlename`, and it is empty in the archive and checksum trees, so an archive file's filespec is its basename alone |
| 4 | `indexshelf_abspath` | wrong | "the holdings directory renamed to the parallel ``_indexshelf-`` tree" -- the holdings directory keeps its name and the **category** below it is prefixed |
| 5 | `internal_link_info` | incomplete | four resolution anchors, three named; the missing one is the category, which is the case that crosses into another bundle set. All four occur in the real link shelves |
| 6 | `filename_keylen` | wrong | "what every object outside an index uses" -- it is a bundle-set class attribute, so a data file in `COISS_2xxx` reports 11 |
| 7 | `lid` | incomplete | the four conditions are tested with `and`, so `_data_set_id_filled` is filled only where the LID rules answer first |
| 8 | `childnames` | incomplete | the fills list omitted `_split_filled`, which is filled on every object, and three more that a large index table fills through the sort |
| 9 | `multipage_view_allowed` | wrong | "the three flags are independent" -- every triple in every shipped rule is nested, so nothing allows multipage without the grid |
| 10 | `bundle_publication_date` | wrong | "a file above the bundle level, for which the first two have no object to ask" -- `bundleset_pdsfile()` answers at bundle-set level, so only the first fallback is unavailable there |
| 11 | `checksum`, `_volume_info` | incomplete | the volume-info MD5 is not the documents tree's alone: it is kept for any basename in EXTRA_README_BASENAMES too, and those are exactly the files no info shelf covers, so for them it is the only source |
| 12 | `description` | incomplete | the icon fallbacks fire on a stored None, and a bundle the tables do not cover gets `UNKNOWN` and reaches neither; five such objects exist and come out described as `'Metadata for '` |
| 13 | `parent_logical_path`, `has_neighbor_rule`, `global_anchor` | incomplete | all three raise ValueError on a *physical* category directory, and the first advertises itself as the safe substitute for exactly that call |
| 14 | `global_anchor` | wrong | "no character an HTML fragment identifier would object to" -- only slashes are replaced, and the tree holds a basename with a space in it |
| 15 | module docstring | wrong | both "Each docstring ..." promises are broken; measured mechanically, nine members fill slots they do not name and five do not say what their slot holds on the two prefilled object kinds |
| 16 | module docstring | incomplete | "calls ``self._recache()``" -- `filename_keylen` does not, which the class docstring and the property's own docstring both say. The partial fix, in the copy nobody re-reads |
| 17 | `size_bytes`, `modtime` | incomplete | the `Returns:` types are wrong for the two prefilled kinds: a merged directory gives None for both and an index row gives the integer zero |
| 18 | `viewset`, `local_viewset`, `all_viewsets` | incomplete | undeclared cost: `local_viewset` reads `url`, `width`, `height` and `size_bytes`, so it can open the image with PIL; `all_viewsets` calls itself the expensive one and names no slot, and fills eleven |
| 19 | `parent_logical_path` | incomplete | "builds the parent object twice" -- `parent()` returns the cached object, so the second call is a lookup |
| 20 | `description` | wrong | "a fixed phrase naming how many rows it stands for" -- it names no number, only singular or plural |
| 21 | `continuous_view_allowed` | unverifiable | the relation to `has_neighbor_rule` is about a Viewmaster behavior; no consumer of either exists in this repository |
| 22 | five smaller ones | mixed | `viewset`'s gate is the interior path, so a directory below the bundle does reach the lookup; `viewset_lookup`'s "three misses" take two values; `all_viewsets`' `default` key is not unconditional; `_repair_width_height` logs before every measurement; `_volume_info`'s key carries the version suffix |

Findings 1, 3, 4, 6, 9, 14 and 20 are the ones a reader would have acted on and been wrong.
Finding 1 is the largest thing this PR found in the code.

## The method, which is why the round was worth its length

The reviewer did not read the claims and judge them. It **instrumented** them. For the
side-effect audit it blanked every slot on a fresh object, read one property, and diffed
the slots; for the prefill audit it compared each body's assigned slots against
`new_merged_dir()` and `new_index_row_pdsfile()` and against the docstring text; for the
link-anchor census it read 400 real link shelves and counted the four prefixes; for the
volume-info claims it counted 5,972 loaded entries and separated the 223 documents-tree MD5s
from the 91 that are not. Findings 5, 8, 12, 15 and 17 are results no amount of reading
would have produced.

That is worth carrying into PR-30: **a claim about what a property costs, or about what a
constructor pre-set, is mechanically checkable, and checking it mechanically finds things
reading does not.**

## Discoveries about the code

1. **`index_pdslabel` parses the index file as its own label on PDS4**, and every PDS4 index
   in the tree raises `SyntaxError` out of the property. A code defect, not only a prose
   one.
2. **`childnames` on an index table caches an `info_basename` derived from a half-built
   child list.** The index branch sorts with the class defaults, which reads
   `info_basename`, which reads `childnames` -- and at that moment the slot still holds the
   pre-index list.
3. A bundle or bundle set the volinfo tables do not cover gets a description that is only
   the volume-type prefix: `'Metadata for '`, trailing space.
4. `_repair_width_height` would raise TypeError on a merged directory or index row if it
   ever ran, which it cannot, because their shape is a two-tuple.
5. `all_versions` stores `self.abspath` for its own rank without testing it, so an object
   with no absolute path writes None and the next call passes None to `from_abspath()`.
6. `checksum_path_if_exact()` and `archive_path_if_exact()` do not accept the same shapes,
   although one docstring calls itself the other's shape. The reviewer declined to file it,
   because the semantic condition really is the same; recorded here as the judgment it made.

## What the reviewer checked hard and found correct

Twenty-five claims, listed in full in the round's own report. The ones worth naming: that
`icon_type` is never empty, established by scanning 4,006 objects across every category and
finding 30 distinct types and no blank; that `opus_format`'s miss is None where `opus_id`'s
and `opus_type`'s are `''`, which is a three-way distinction the prose draws and the code
keeps; that `viewset_lookup`'s twenty caps *candidates* while `all_viewsets`' twenty caps
*child names*, which are genuinely different and which both docstrings got right; that
`bundle_publication_date`'s None short-circuit corresponds to the volinfo loader turning an
all-dashes date into None and leaving a blank one as `''`, 82 entries of 5,972; and that
`filename_keylen` is the one lazy property with no `_recache()`, checked against all 40.
