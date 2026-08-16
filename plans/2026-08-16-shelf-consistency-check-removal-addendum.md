# Addendum — `shelf_consistency_check` removed by owner instruction

**Status: OWNER-DIRECTED, 2026-08-16.** The owner instructed that
`shelf_consistency_check` be deleted, together with its documentation, references
and tests. This addendum records the instruction per §6.4, because the plan did not
schedule the removal: the tool was carried through PR-06 (the move into the
package), PR-28 (its `main()` and the `error`/`errors` fix), PR-30c (its
docstrings), PR-32 (its user-guide chapter) and PR-13's test conventions, and the
open question about it lived in the Phase 6 deferred table.

## What was removed and why

The program searched any tree named on its command line for directories whose path
contains the substring `shelves` with a first component `info`, `links` or `index`
below it, and derived each shelf's holdings counterpart by textual substitution on
the path. This repository's holdings trees have never used that layout: at
`a6f3949` (2023-12-06), the commit that brought the tool in from rms-webtools as
`validation/shelf-consistency-check.py`, the package code and tests already
addressed shelves as `holdings/_infoshelf-volumes/` and siblings. A run against a
real tree walks everything, examines nothing, and reports `Tests performed: 0` /
`Errors found: 0`. Nothing in the repository or the sync scripts ran it.

## Where its open questions went

- Phase 6 deferred entry 6 (should the walk learn the current directory names?) is
  superseded: **issue #156** now records the capability gap — the holdings trees
  have no orphan-shelf check — and owns any future design.
- Register observations 3004 (the layout mismatch) and 4033 (the `rpartition`
  empty-string case) are discharged as superseded by issue #156;
  `critiques/observations.md` carries the arithmetic.

## Scope of the removal

Deleted: the module, its 18 tests, its user-guide chapter. Edited: the package and
test docstrings that enumerated it, the API-reference page, the user- and
developer-guide program counts (fifteen programs to fourteen; the API reference
drops from 78 to 77 modules), `README.md`, the `.cursor` print-waiver example, and
one `pyproject.toml` ratchet comment. The console-script set is untouched: the tool
never had one.
