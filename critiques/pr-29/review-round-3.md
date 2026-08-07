# PR-29 adversarial review, round 3 — `pdsfile.py`

Reviewer: a fresh subagent with no context from the executor's session or from rounds 1
and 2, given the head and base copies of `src/pdsfile/pdsfile.py` and a working holdings
tree. Slice: that one file — the module docstring, the `PdsFile` class docstring, and 37
functions.

This round was pointed at two things the earlier ones were not. First, the module
docstring, because it makes many *checkable factual* claims — a map of ten sibling
modules, counts of properties, an alphabetical-bases claim, and claims about what two
named tests check. Second, exceptions from subscripts and attribute access rather than
from `raise` statements, which is where rounds 1 and 2 both found the docstrings drifting.

Eighteen findings. Every one was re-verified by the executor before acting on it, and
every re-verification agreed.

## The module docstring survived intact

The reviewer AST-parsed all ten sibling modules and could not break a single mechanical
claim. Confirmed exactly: 4 `associated_*` methods; `_local_fs`'s 5 methods plus
`PATH_EXISTS_CACHE_SIZE`; `_opus`'s 3; `_path_utils`'s 10 functions with 3 `_clean_*`,
plus its two constants and no class; `_preload`'s module functions and constants;
`_sorting`'s **12** conversions; `_shelves` isolating the only `eval()` in one named
function; and `_properties`'s **64** properties, **40** assigning a private slot, **39 of
those 40** calling `_recache()`, leaving **24** recomputed. The bases are alphabetical,
and both named tests check what the docstring says they check. The re-export claims hold:
the ten `import X as X` names and the twelve re-exports are referenced nowhere in the
file, and `pdstable`, `defaultdict` and `pdsparser` are used by the three modules named.

That is the one part of this PR whose numbers were carried forward from the prose being
replaced. They were re-measured before the rewrite, and this round is a second,
independent confirmation.

## What was fixed in the docstrings

| # | finding | fix |
|---:|---|---|
| 1 | `from_path` — the documented `KeyError` is right for a bundle*set* and wrong for a bundle *name*, which gives `UnboundLocalError` because the KeyError recovery path leaves the rank unassigned. `from_lid` inherits it, and lists only `ValueError`. Two more uncovered: `ValueError` from `index('_')` and `IndexError` from an empty rank list. | both rewritten; entry 184 |
| 2 | `_complete` — "a path that differs from the real one in case will not match the cache entry" is backwards. Both the read and the write lowercase the key, so two spellings reach the same entry and get the same object. | rewritten |
| 3 | `parent()` — documented to answer `None` for "an object whose parent's logical path would be empty". A *physical* category directory is exactly that and raises `ValueError` instead. `parent()` had no `Raises:` at all. | rewritten; entry 185 |
| 4 | class docstring — "instances are cached ... a later request for the same path gets the same object back". Under the default `'dir'` mode a data file is not cached, which is the case the sentence's own examples point at. And `CACHE` is not shared: each subclass defines its own. | rewritten |
| 5 | `new_merged_dir` — "every lazy property already set ... nothing about it is ever computed from a filesystem". Seven slots are left unset; `html_path` and `url` raise `IndexError`, `all_version_abspaths` raises `TypeError`, and `iconset_open` reads the icon directory out of the tree. | rewritten; entry 186 |
| 6 | `from_path` — "the pieces may appear in any order at either end". The trailing loop reads `parts[0]` and pops from the other end, so it breaks on its first iteration every time; only leading pieces are recognized. | rewritten; entry 187 |
| 7 | `child` — a `Raises:` cause the code cannot produce: the final "child asked for below the PDS root" `ValueError` is unreachable, because the two blocks above it are complements and each returns. | removed; entry 188 |
| 8 | `from_logical_path` — "which is the situation before a preload" is not the only time the fallback fires. An ancestor found but holding no absolute path takes it too, and merged category directories are permanent cache entries, so a preloaded tree reaches it and silently drops `must_exist`. | rewritten; entry 190 |
| 9 | `_update_ranks_and_vols` — "marked permanent, so the cache never evicts a path these dictionaries point at". `permanent` is written in four places and read in none, and `_complete` has already written the entry with an ordinary lifetime. | rewritten; entry 189 |
| 10 | `_complete` — three exclusions were listed and a fourth omitted: a path *at* category level is never cached either, in any mode. | rewritten |
| 11 | class docstring — "an attribute whose name ends in an underscore either is empty or ends in a slash" is broken by `new_merged_dir`, which sets three of them to None. | rewritten |
| 12 | `from_abspath` — the `ValueError` entry covers neither reachable case: the logical-path conversion runs before both documented checks and refuses a path with nothing below `holdings`, and an illegal component raises from `child()`. | rewritten |
| 13 | `is_bundleset_dir` / `is_bundleset_file` — "Reading it consults the filesystem" is unconditional; `and` short-circuits, so most objects answer without asking. | both rewritten |
| 14 | `is_logical_path` and `_from_absolute_or_logical_path` — the test needs a slash on *each* side and is case-sensitive, unlike the lookup `from_abspath` uses for the same component. | both rewritten |
| 15 | `__repr__` — the logical branch carries no class name; the branch tests `abspath is None`, so a blank object takes the other one; and both shipped subclasses override the method. | rewritten |
| 16 | `set_logger` — "the `CACHE` that `PdsFile` built with its own logger continues to use that one" is a non-sequitur. A cache holds a direct reference to its logger, so no assignment to any class's `LOGGER` reaches it. | rewritten |
| 17 | `child` — "the cache is paused for the duration" excludes the index-row path, which returns before the pause. | rewritten |
| 18 | module docstring — the `_preload` bullet omitted four mixin methods, one of them `cache_category_merged_dirs`, which is the call at the foot of this very file. | rewritten |

## Gates after the fixes

The AST hash is unchanged at `b6b8ad8bd5dba452`, the docstring checker reports 0
findings, `ruff check .` passes, the Sphinx build is still clean under `-W -n`, and the
citation checker reports 0 stale.

## Why there is no round 4

Round 3 found more than round 1 and more than round 2, so "the rounds have converged" is
not the reason to stop; the reason is that the three rounds have now covered all three
substantial files, and a fourth would be a second pass over a surface already read. The
brief's cap is three, and the honest report is that this file would still repay another
reader.
