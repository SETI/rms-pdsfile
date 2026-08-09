# PR-30b round 1 — the checksum and info shelf pairs

Reviewer: a fresh subagent with no context from this session or from any other round.
Tree frozen at `5acbf85`; nothing under `src/` moved while it ran.

Surface: four files, 46 functions, 159 documented parameters. The reviewer's own AST count
of the parameter lists matched the brief's exactly, and **every documented parameter list
matched its signature in name and order**, so nothing in the mechanical dimension was left
for it to find.

## What it disproved: 10 claims

Every one was re-verified by the executor before it was acted on, and the four with the
widest consequences were re-derived from scratch rather than read.

1. **"Nothing in this package reads the sidecar"**, in `write_infodict` in both tools.
   `_shelves.shelf_lookup()` reads the readable `.py` file's **second line** to answer a
   question about the unit itself, in preference to unpickling the shelf, and
   `_shelves.py`'s own module docstring says so. Confirmed at
   `src/pdsfile/_shelves.py:471-481` and by reading a production sidecar, whose second line
   is the `""` entry. This is the sharpest finding of the round: the claim not only was
   false but told a maintainer that two properties of the write -- sorted keys, and the
   unit's own path sorting first -- do not matter, when the shortcut depends on both.
2. **"A record shorter than that yields a short digest and an empty path rather than an
   error"**, in `read_checksums` in both tools. A blank line in a manifest gives an empty
   basename and `basename[0]` then raises. Reproduced: `IndexError: string index out of
   range`. The claim was exactly inverted, and `IndexError` was missing from `Raises:`.
3. **"an entry for a file that has since been deleted is dropped"**, in `update` in **all
   four** tools. `generate_checksums` rebuilds from the whole of `oldpairs` and
   `generate_infodict` starts from `old_infodict.copy()`, so the entry survives. Measured
   in both families with a stale entry. The reviewer went further than the disproof and
   noted the consequence: because it survives, the comparison still holds and the run
   reports "update canceled", so a deletion is invisible rather than merely un-removed.
4. **"an update does notice a directory whose child count or total size has changed"**, in
   `update` in both info shelf tools. The merge writes a key only where the old dictionary
   lacks it, so the recomputed directory entry is discarded. Measured with a deliberately
   stale directory entry: the walk computed one value and the result carried the other.
5. **"unlike the info shelf tool's ``initialize``, which logs and returns"**, in
   `pdschecksums.initialize`. True of `pds4infoshelf` and false of `pdsinfoshelf`, which
   ends in `AttributeError`. A cross-version claim asserted of the wrong twin, and one that
   contradicted a correct sentence this same PR wrote 300 lines away.
6. **"That is the only way a run of this tool reaches a nonzero exit status"**, in `main()`
   in both checksum tools. Measured: 1 for a command line naming no task, 2 for one the
   parser cannot classify, 1 for a path outside a holdings tree.
7. The same error inside those two `main()` docstrings' `Raises:` sections.
8. **"Every function below therefore takes a ``selection``"** in both checksum module
   docstrings. Eight of eleven do. The info shelf modules say "Every task", which is true
   of all five.
9. **"where every other function in this module logs it first"**, about a
   `KeyboardInterrupt`, in `read_checksums` in both tools. Three of the ten others log one;
   seven install no handler at all.
10. **"The shelf format marks a directory's absent digest that way"**, about a dashed
    digest, in `load_infodict` in both tools. `write_infodict` stores the empty string for
    a directory, and a scan of production shelves found no dashed digests at all.

## What it classed as misleading: 9

All nine were acted on. Three are worth naming because each is a true sentence that a
reader takes the wrong way:

* `repair`'s "the one state this task cannot proceed from", about a missing sidecar. The
  two `getmtime()` calls that read it are **inside the agreement branch**, so a missing
  sidecar stops the task only where the shelf and the walk agree; where they differ, the
  same exception comes out of `move_old()` instead.
* the module docstrings' "**Three fields** of the specification are **set here** and read
  nowhere", followed four lines later by "``log_path_method`` is left at its empty
  default", which says it is not set here. Self-contradicting inside one paragraph, in all
  four files.
* `load_infodict`'s `Raises:`, which listed `pickle.UnpicklingError` inside the `OSError`
  entry. It is not an `OSError`, so a caller guarding against the entry as written does not
  catch it.

## What it could not verify: 7

Recorded because the list is as useful as the findings. The two that matter:

* **the `--infoshelf` chain actually running.** It reads correctly and the console-script
  names check out, but running it writes shelves and the reviewer would not. Settled by a
  run against a copied holdings subset.
* **`get_info_for_file`'s "a file that fails after being opened stays open"**. No input was
  found that raises between the open and the close: one statement sits between them and it
  is an attribute read. The sentence may describe an unreachable state, which would make
  the PDS4 twin's contrast vacuous rather than wrong. Both docstrings now describe the
  difference in shape and say that no input reaching it was found.

## Code defects, not documentation defects: 7

All seven are recorded in `critiques/deferred-observations.md`, entries 295 to 301 and 306
to 307. The three the reviewer ranked highest:

* a blank line in a checksum manifest ends the read with `IndexError`;
* `update` cannot see a deletion, in all four tools, and reports "canceled" because of it;
* the info shelf `update` never refreshes a directory entry, so `validate` and `update`
  disagree about the same shelf.

## What the reviewer measured

Roughly 120 sentences: about 52 relationship claims, all 16 cross-version claims, 14
implicit-exception paths of which six were constructed and run, and about 38 counts and
boundaries. 10 disproved, 9 misleading, 7 unverified.
