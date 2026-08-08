# PR-29b review round 2 — `pdsfile.py` and `pdsviewable.py`, the second read of shipped prose

Fresh reviewer subagent, no context from this session or any other round. Brief: 63
functions, three class docstrings and two module docstrings, with the five angles named in
order. The reviewer was given the read-only base tree, so the prose it read is exactly what
PR-29 merged.

This is the round PR-29 asked for and could not fit inside its own round cap. **The prose
had had one adversarial read each and shipped.** PR-29's own round 4 measured that a second
read of an already-read file finds about twenty more items, of which thirteen were defects
in the prose rather than discoveries about the code, and recommended two reads per file. The
recommendation reproduces.

**Fourteen findings over 63 functions and five module- or class-level docstrings, and ten
discoveries about the code.** Every finding was re-verified by the executor before it was
acted on; one was accepted with its severity changed and none was rejected outright.

## The findings

| # | where | severity | what was wrong |
|---|---|---|---|
| 1 | `pdsfile.py` module map, `_local_fs` bullet | wrong | called it "the case-repairing filesystem layer"; `_local_fs.py` contains no case repair at all, and the same map attributes `repair_case` to `_path_utils` seven lines further down |
| 2 | `pdsfile.py` module docstring | wrong | "Every public name of the package resolves as ``pdsfile.pdsfile.<name>``" -- 94 names in the frozen manifest are not attributes of this module, `Pds3File`, `Pds4File`, `PdsViewable` and `PdsViewSet` among them. The claim was true in one direction only |
| 3 | `PdsFile` class docstring | incomplete | the None `disk_`, `root_` and `html_root_` are not confined to `new_merged_dir()`: `child()` copies them on, so everything built below a merged directory carries them |
| 4 | `new_merged_dir()` | wrong | "Seven storage slots are left unset, and the properties behind them do not degrade gracefully" -- four of the seven answer normally, measured |
| 5 | `new_merged_dir()` | wrong | "``iconset_open`` and ``iconset_closed`` read the icon directory out of the holdings tree" -- both subscript a module-level dictionary and raise KeyError until `load_icons()` has filled it |
| 6 | `from_abspath()` | incomplete | the `Raises:` listed "has no ``holdings`` component" as an outcome; the logical-path conversion runs first and rejects such a path, so the message written here cannot be reached |
| 7 | `from_path()` | incomplete | "A missing category is assumed to be the class's own bundle directory name" -- only the *voltype* defaults; a `checksums` or `archives` prefix is kept and concatenated |
| 8 | `from_path()` | incomplete | "A bundle*set* they do not hold gives KeyError" -- true only when no version suffix was given; with one, the rank comes from `version_info()` and the failure ends in ValueError |
| 9 | `from_path()` | unverifiable | the underscore-less bundle name does raise ValueError, but no bundle name either shipped subclass recognizes can reach it |
| 10 | `pdsviewable.py` module docstring | wrong | "so neither describes any file on disk" -- where the request equals an indexed size, which is the ordinary case of a page asking for a size it knows the set holds, both dimensions match the chosen file's |
| 11 | `PdsViewSet` class docstring | wrong | "a set holding named viewables alone serves them from every lookup" -- `thumbnail` raises IndexError and `small` and `medium` raise AttributeError, which their own docstrings describe |
| 12 | `PdsViewSet.append()` | wrong | "Every later size lookup on the damaged set fails too" -- the three size lookups keep answering from whatever is already indexed; what fails permanently is `by_match()` and the three properties built on it |
| 13 | `load_icons()` | wrong | the `jpg-<n>` nominal-size fallback is unreachable: `str.rpartition` returns the whole string as its third element when the separator is absent, so the test in front of the fallback is never true |
| 14 | `iconset_for()` | incomplete | "has loaded a ``document_generic`` icon **for the open state being asked for**" -- one closed `document_generic` covers both, because `load_icons()` files a closed set under the open key when nothing is there |

Finding 9 was accepted as a documentation change rather than rejected: the sentence is true
of the code and misleading about what is reachable, so it now says both. That is the one
place this round's severity and the executor's disagreed.

## The angles, and which paid

The brief named five angles in a fixed order, on PR-29a's measurement of which ones earn
their place. The order held.

* **Relationship claims were again the largest category** -- findings 1, 2, 3, 4, 5, 6, 8
  and 14, eight of fourteen. Every one was settled by reading the other end rather than by
  judging plausibility: finding 1 by grepping `_local_fs.py` for the thing it was credited
  with, finding 2 by walking the frozen manifest against this module's namespace, finding 5
  by reading what `iconset_open` actually subscripts.
* **Exceptions from something other than a `raise`** produced findings 6, 8 and 11 -- a
  ValueError from a helper that runs before the test that would have raised it, a KeyError
  from a dictionary subscript that a version suffix routes around, and an IndexError from
  an empty index list.
* **Arithmetic and boundaries** produced finding 10, and finding 13 is the same shape one
  level down: a claim about which branch a string operation selects, settled by running
  `rpartition` on the path in question.

## Discoveries about the code, not about the prose

1. `from_path()`'s second scanning loop is dead: it pops from the end and tests the front,
   so it re-tests the element the first loop just failed on and breaks immediately. The
   docstring's "Only the front is scanned" is accurate *because* of this.
2. `load_icons()`'s `jpg-<n>` branch is unreachable, and one line below it
   `ext.lower() not in ('.png', 'jpg')` is missing a dot, so JPEG files are skipped
   entirely. Both defects are in the same two statements.
3. `from_abspath()`'s "holdings directory not found" raise is unreachable.
4. `from_relative_path()`'s empty-path branch is dead, because `str.split('/')` never
   returns an empty list.
5. `child()` applies `if self.checksums_ or self.archives_:` twice with identical bodies.
6. `load_icons()` rebinds its own `url` parameter inside its walk.
7. `load_icons()` with no logger falls through to `im.size` on the previous iteration's
   closed image, storing a bad file with another file's dimensions, and raises
   UnboundLocalError when the bad file is the first one reached.
8. `PdsViewSet.append()` adds the object to the set before the attribute read that raises,
   so a failed append poisons the set permanently.
9. `PdsViewSet.small` and `.medium` can never take their fallback: each calls a method on
   the None it has just tested for.
10. A stale inline comment at `pdsfile.py` describes `$VOLS-` as returning a PdsFile; it
    stores an absolute path, and `_update_ranks_and_vols`' docstring gets it right.

Items 1, 2, 3, 5, 7, 8 and 9 already have deferred entries or are documented in the
docstrings that reach them; the rest are carried as deferred observations.

## What the reviewer checked hard and found correct

Fourteen substantial claims were verified rather than accepted, and the list is kept because
a settled claim is a result. Among them: the module map's per-module bullets, every one of
which enumerates a set that was counted; the `_properties.py` bullet's "64 properties, of
which 40 are lazy ... 39 of the 40 call `_recache()` ... 24 recomputed", every number exact;
`new_merged_dir()`'s count of seven unset slots, which is right even though the sentence
after it is not; `_recache`'s dictionary-cache-versus-memcached lifetime asymmetry;
`from_logical_path`'s "fallback silently loses `must_exist`" paragraph, reproduced both
ways; all four of `from_path`'s worked examples; every caching rule in `_complete()`;
`set_logger`'s "a cache is unaffected either way"; `bundle_abspath` and `bundleset_abspath`
across seven categories each, including the `''`-versus-None asymmetry; and `pdsviewable`'s
size-selection rule and its round-half-up-with-floor-1 arithmetic, measured at the
boundaries.
