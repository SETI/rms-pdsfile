# PR-17 — adversarial review round 5 (scoped, owner-authorized)

**Date:** 2026-07-27
**Reviewer:** a fresh opus-class subagent with no development context and no
knowledge of rounds 1–4.
**Scope:** "confirm round 4's Major is genuinely resolved; raise only **new
Major** findings."
**Diff reviewed:** `origin/pr-16-path-utils...70e0830`.
**Verdict:** **goal not met** — round 4's Major **fully resolved**; **1 new
Major**, verified and **not fixed** (see below).

## Why there is a fifth round at all

§6.6 sets a hard cap of four. **The owner authorized this round as an explicit
exception**, on the grounds recorded at the end of `round-4.md`: rounds 1–3 each
returned zero Major, so the loop was converging rather than thrashing, and round
4's Major sat in a **voluntary addition** rather than a plan deliverable — the
plan asks `tests/api/test_mixin_collisions.py` for a set-intersection check, and
`test_no_mixin_module_imports_pdsfile_at_import_time` is an extra, taken up from
round 1's Deferred bucket.

The round was scoped tightly on the owner's instruction: a fresh no-context
reviewer, pointed at the guard and its helpers, and told to **derive the case
matrix itself and evaluate the shipped code against it** rather than read the fix
— because the round-4 defect was a silent coverage *trade*, and "a green guard
that is blind" is the failure mode.

## Round 4's Major — **resolved**

The reviewer built a 22-case spelling matrix without reference to any record and
drove both the helpers directly and the shipped test against a mutated
`_shelves.py`:

- **14 of 14 back-import spellings caught**, including the two the round-4 fix was
  about — `from pdsfile.pdsfile import PdsFile` and its silent sibling
  `from pdsfile.pdsfile import repair_case`.
- **0 false positives** on 8 legitimate imports, including every import the two
  mixin modules actually use.
- It went further than the fix claimed and checked the *other* level direction:
  for a hypothetical mixin one package deeper, `from .. import pdsfile` and
  `from ..pdsfile import X` both resolve and flag.
- It independently re-derived the premise underneath the round-4 finding —
  injecting `from pdsfile.pdsfile import repair_case` at module level imports
  cleanly and silently, so the "absolute forms raise on their own" claim really
  was false and the guard really is the only thing that catches it.

## The new Major — verified, and deliberately left unfixed

**The guard is still green-but-blind for an import in a `class` body**, and its
own docstring states as fact that class bodies do not execute at import time.
Two smaller cells share the root cause: the `else` branch of an
`if TYPE_CHECKING:` (the walk skips the whole `ast.If`, not just its `body`), and
`match`/`case` (the walk never visits `cases`). Across the reviewer's full cross
product of spellings × nestings, **56 of 252 cells miss**, all in those four
nestings.

Reproduced here before recording, injecting into `src/pdsfile/_shelves.py`:

| injected | cycle real? | guard |
|---|---|---|
| `class _ShelfMixin:` + `from pdsfile.pdsfile import PdsFile` | **yes** — raises `ImportError … most likely due to a circular import`, *from the class body*, which is the proof the body executes at import time | n/a (collection fails) |
| `class _ShelfMixin:` + `from pdsfile.pdsfile import repair_case` | **yes**, and silent | **GREEN — all 14 ids pass** |
| `if TYPE_CHECKING: pass / else: from pdsfile.pdsfile import repair_case` | **yes**, and silent | **GREEN — all 14 ids pass** |

`ast.ClassDef` is in the skipped set alongside `FunctionDef`, and that is simply
wrong: a function body is deferred, a class body is not. It is the same defect
*shape* as the one round 4 found — an entire nesting class dropped, justified by
a confident but incorrect claim — and this time the incorrect claim is written
into the file as guidance PR-18–22's executors will read.

**It is not fixed.** The coordinator's instruction on authorizing this round was
explicit: if round 5 returns a new Major, stop and report rather than fixing,
because a second breach of the cap is a genuine mis-scope signal and the decision
is the owner's. The reviewer supplied a ~10-line fix and reports having verified
it takes the matrix to 0 misses and 0 false positives, but it is not applied here.

### What the owner is deciding between

1. **Strip the guard from this PR and defer it**, which is what round 1 originally
   proposed when it raised the item in the *Deferred* bucket. PR-17's plan
   deliverable — the set-intersection collision check — is untouched by this, and
   so is every other check in the file. This is the option that makes the mis-scope
   signal actionable: the guard has now consumed two of the five rounds and is not
   something the plan asked for.
2. **Apply the fix and re-review**, accepting a sixth round.
3. **Ship the guard as-is**, documenting the class-body hole. Not recommended: the
   whole objection to a blind guard is that later PRs trust it, and this one would
   tell them in a docstring that the uncovered case is safe.

Nothing under `src/pdsfile/` is affected by any of the three. The guard is a test.

## Everything else the round checked — clean

The reviewer re-verified, by its own measurement: all 14 moved methods
byte-for-byte (13 identical, the 14th the authorized `eval()` isolation, with
decorator lists and argument lists compared separately because
`get_source_segment` excludes decorators — all 14 identical there, including the
`lru_cache` decorator on `os_path_exists`); the parent's `PdsFile` had 170 methods
and HEAD has 156, the 14 lost being exactly the moved set; every call site
resolving through `cls.`/`self.`; the mixin mechanics; no new public name; the
four frozen files untouched and `pytest tests/api/` at 15; the ratchet a strict
split with `tests/api/test_mixin_collisions.py` ruff-clean and entryless as
required; and the full-data evidence, recomputed from the four junit XMLs to the
same 22 additions / 0 removals and empty `--mode s` diff, with the record's
enumerated ids `diff`-matching both its computation and what
`pytest --collect-only` produces.

## Non-blocking notes

The reviewer's one substantive note was a genuine record defect and **is fixed**:
the PR-17 section quoted head-run junit timestamps of 04:03:09 / 04:06:00 while
the artifacts on disk read 08:02:17 / 08:05:09, from the regeneration that
followed the round-5 guard change. The gate held either way — both postdate the
last `src/pdsfile/` change at 04:02:58 — but a stale number in a record whose
value is that its figures reproduce is exactly the defect round 3 flagged, so the
header now carries the artifacts' own timestamps and says why they were
regenerated.

Its other notes are out of scope and not actioned: the guard scans only the
modules of `PdsFile`'s *direct* bases, so a helper module a mixin imports could
carry the same cycle unguarded; `importlib.import_module` / `__import__` are not
`ast.Import` nodes and are uncoverable by construction; and `_is_type_checking`
matches any attribute named `TYPE_CHECKING`.
