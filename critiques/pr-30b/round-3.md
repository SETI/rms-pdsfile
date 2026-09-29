# PR-30b round 3 — the checksum and info shelf pairs, re-read

Reviewer: a fresh subagent with no context from this session or from any other round.
Tree frozen at `748eae4`; nothing under `src/` moved while it ran. It was given the
correction range `5acbf85..748eae4`, the thirteen claims those corrections make, and the
instruction to treat every one as unproven and to attribute each finding with `git blame`.

## What it disproved: 7 claims, 5 of them in the corrections

**In the corrections:**

1. **The dashed-digest scan.** The corrected sentence cited "80 shelves and 391,444 entries
   in the test holdings". Those are the numbers of the slice actually run -- the first 80
   pickles of one category -- written up as though they were the tree. Unpickling every
   info shelf under the PDS3 test holdings gives **6,723 shelves and 21,711,938 entries, no
   dashed digest and 186,305 empty ones**, which the record and both docstrings now carry.
   The substantive claim held at the larger scale; the citation did not. The reviewer also
   noted that the sentence stood in `pds4infoshelf.py` citing a measurement the PDS4 tree
   cannot have produced, since it holds no info shelves at all.
2. **"its entry ... is always written first and is the file's second line."** The two
   mechanical halves are true and the word "always" is not: `write_infodict()` does not
   enforce the prefix property, its caller supplies it, and `reinitialize()` on a selection
   supplies one entry for the named file alone. The reviewer ran it on a sandbox copy: the
   sidecar holds one line, the pickle holds one key, there is no empty key, and
   `shelf_lookup()` returns that file's entry as the volume's because nothing on that path
   checks which key it got.
3. **"Every later operation on that pair then fails on the sidecar."** With the sidecar
   deleted, three of six operations run completed: `load_infodict()`, `validate()`, and an
   `update()` with nothing to write.
4. **"the ``EOFError`` a truncated pickle gives."** Truncating a real shelf at every one of
   its 14,355 prefixes gives **12,812 `UnpicklingError` and 1,543 `EOFError`**; the entry
   above it already names the common outcome. Reproduced independently by the executor over
   2,001 sampled prefixes: 1,758 to 243.
5. **"the three functions here that read or write a manifest."** Two do. Four open a log
   level, and two of those four never touch a manifest, so no reading of the module gives
   three without counting `checksum_dict()` itself.

**In the original prose:**

6. **The info shelf keys are volume-relative, not volume-set-relative**, in four sentences
   across the two modules. `shelf_path_and_lskip()` trims past the **bundle** on the
   non-archive path, and a real shelf's keys are `['', 'aareadme.txt', 'catalog', ...]`.
   Only an archive target, whose one shelf covers a whole set, is keyed the other way. The
   phrase is correct in the *checksum* modules, which is where it was carried from.
7. **`pdschecksums.main()` still said the `--infoshelf` chain is the only way to a nonzero
   exit status**, which round 1 had disproved and the correction pass had fixed in the same
   file's module docstring and in the PDS4 twin's `main()`, and missed here. Measured: 1
   for no task, 2 for an unclassifiable command line, 1 for a rejected path.

Finding 7 is the sharpest thing this round produced, and not because the claim is
important. **A correction pass applied one finding to three of the four places it belonged
and left the fourth contradicting its own module docstring 900 lines above it.**

## What it classed as misleading: 3

* `repair`'s corrected "**only where** the shelf and the walk agree", immediately followed
  by the clause saying where else it fails. Both halves of the mechanism were reproduced --
  `FileNotFoundError` from the `getmtime()` pair on one branch and from `move_old()`'s
  companion copy on the other -- so the sentence disproves its own first word.
* `update`'s corrected cross-reference, "``validate()`` reports those as a child count and
  a file size mismatch". Measured after adding a file and running `update`: three errors,
  not two. The stale directory keeps its modification time as well.
* the PDS3 sidecar naming rule's "a shelf file whose basename has fewer than two such parts
  is named for what there is", which is unreachable -- every path this builds ends in
  `_info.py`, so there are always at least two, and the minimum across 6,723 real shelves
  is three.

## What it could not verify: 3

* whether `size = im.size` can raise. It could not build an input either, and reports that
  in the installed Pillow the attribute is a plain property set during `_open()`. Both
  docstrings say no input was found rather than that none exists.
* that the sidecar shortcut is "what keeps a preload from opening every info shelf". The
  shortcut exists and is read; the reviewer did not trace `preload()` to it. That clause is
  removed rather than defended.
* which truncations of a preview image the holdings actually contain.

## Code defects, not documentation defects: 4

Two are new and are recorded as entries 310 and 311; two were already recorded.

* **`repair` logs "content is up to date" on the out-of-date branch**, immediately before
  "is out of date %.1f days". The two lines say opposite things about the same run.
* **The test holdings hold 6,723 info shelf pickles and no `.py` sidecars at all**, so
  `shelf_lookup()`'s shortcut raises `FileNotFoundError` against the tree this project
  tests on, and has no fallback to the pickle.

## What the reviewer measured

About 60 of the ~92 sentences the correction diff adds, covering all thirteen enumerated
claims, and about 75 original sentences. 7 disproved and 3 misleading, of which **5 and 2
respectively are in the corrections**: 7 of its 10 findings sit in prose the first read
wrote.
