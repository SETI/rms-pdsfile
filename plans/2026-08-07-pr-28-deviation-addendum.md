# PR-28 deviation addendum — `show_opus_products` keeps its subprocess tests

**Status:** written by the PR-28 executor 2026-08-07. **Needs the owner's
acknowledgement before PR-28 merges** (§6.4: "Deviations from this plan require an
addendum file in `plans/` acknowledged by the owner before the deviating PR
merges").

## The deliverable this deviates from

`plans/2026-07-25-modernization-plan.md`, the PR-28 entry as written before this
PR:

> **Update the PR-13 subprocess tests** for these two tools to call `main()`
> in-process and keep them green (the behavior under test is unchanged; only the
> invocation path moves).

and the PR-13 entry, which named the same two tools:

> …a stable interface that survives the PR-28 refactor (which then switches these
> tests to call `main()` in-process).

"These two tools" is `shelf_consistency_check` and `show_opus_products`.
`plans/2026-07-25-pr-13-subplan.md` repeats it: "PR-28 will still convert the two
`main()`-less tools to in-process calls as the parent plan says; that is
orthogonal."

## What PR-28 did instead

`shelf_consistency_check` moved. **`show_opus_products` did not**: its tests still
drive it as `python -m` subprocesses.

## Why

`tests/holdings_maintenance/__init__.py` has documented since PR-13 why the tool
tests use subprocesses at all: `PdsFile.CACHE` is a **class-level** cache keyed by
**logical** path, and the pytest session preloads the real holdings tree, so an
in-process call against a temporary tree can resolve a temporary-tree path back to
the real one. That reasoning applies to `show_opus_products` and does not apply to
the other two:

| tool | what it imports | what it does to class state |
|---|---|---|
| `crlf` | `argparse`, `sys` | nothing |
| `shelf_consistency_check` | `argparse`, `os`, `sys` | nothing |
| `show_opus_products` | `Pds3File`, `Pds4File` | `Pds3File.use_shelves_only(True)`, `Pds3File.preload(root)`, `Pds4File.use_shelves_only(False)`, `Pds4File.preload(root)` |

Called in-process, `show_opus_products.main()` would preload a temporary tree into
the same class-level cache the session preloaded the real tree into, and would
leave `SHELVES_ONLY` set for every test that ran after it — in a suite where
`--mode` is exactly the knob that sets it. The failure mode is silent: a test that
measures the wrong tree still passes.

PR-25a met the same wall from the other side: it drove its own new module
**in-process**, against this package's subprocess convention, on the same reasoning
about which tools can touch class-level state. It recorded that in its validation
record rather than in a §6.4 addendum, because departing from a convention is not
the same as dropping a stated deliverable — which is why this file exists and that
one did not need to.
`tests/holdings_maintenance/__init__.py`'s header, `support.HOLDINGS_FREE_TOOLS`,
and the assertion in both new in-process helpers now carry the criterion, so the
next person does not have to re-derive it.

## What it would take to do it anyway

An autouse fixture that snapshots and restores `Pds3File`/`Pds4File`
`LOCAL_PRELOADED`, `SHELVES_ONLY` and the caches around each call — new global-state
machinery in the test tree, whose correctness is exactly the thing that is hard to
be sure of, in exchange for the runtime of the six tests that drive this tool as a
subprocess. The executor judged
that a bad trade for a PR whose subject is three `main()` functions, and this
addendum exists so the owner can disagree.

## The alternative, if the owner wants the letter of the plan

Move the tests and add that fixture, in a PR of its own — the fixture is the risky
part, not the move, and it deserves its own evidence. `src/pdsfile/_preload.py`
already resets `LOCAL_PRELOADED`, which is where such a fixture would start.

## What was changed in the plan, and what this replaces

Four passages predicted the move. PR-28 corrected three of them and left the
fourth:

| where | what it said | now |
|---|---|---|
| the plan's PR-28 entry | "**Update the PR-13 subprocess tests** for these two tools" | says only `shelf_consistency_check`'s moved, and points here |
| the plan's PR-13 note | "which then switches these tests to call `main()` in-process" | says the same, and points here |
| `critiques/deferred-observations.md` entry 8 | a coverage note assuming both tools would be measured with no subprocess machinery | corrected, and points here |
| `plans/2026-07-25-pr-13-subplan.md` | "PR-28 will still convert the two `main()`-less tools to in-process calls as the parent plan says" | **left alone** — a sub-plan records what its own PR was told, and this file is where the change of direction lives |

`critiques/deferred-observations.md` entry 13 is a fifth passage, and it is not a
prediction: it required PR-28 to **re-derive** the single-`--mode`-pass
justification for whichever tools it converted. That re-derivation is written into
entry 13 and holds — neither migrated tool imports a PdsFile class, so neither can
observe `use_shelves_only`.

`critiques/pr-28-validation.md` §4 carries the measurement and §7 lists this as the
decision the owner is most likely to make differently.
