# Addendum: the order of `PdsFile`'s mixin bases is alphabetical

**Date:** 2026-07-27
**Status:** **ACKNOWLEDGED — owner, 2026-07-27.** §6.4 requires an addendum in
`plans/` acknowledged by the owner before the deviating PR merges; this is that
acknowledgement. The rule below stands and
`tests/api/test_mixin_collisions.py::test_the_mixin_bases_are_listed_alphabetically`
stays.
**Amends:** `plans/2026-07-25-modernization-plan.md` §5, the Phase-5 preamble
(the one illustrative line quoted below).
**Raised by:** the PR-17 adversarial review, rounds 1–3, all three rounds
independently.

## The gap

The Phase-5 preamble states the technique and illustrates it:

> method groups move to **mixin classes** in new private modules
> (`class PdsFile(_ShelfMixin, _OpusMixin, …)`)

It fixes no ordering for the bases, and it could not — the illustration lists two
mixins that never arrive in the same PR and ends in an ellipsis. But **the class
statement cannot be written without some order**, so PR-17, which creates the
first two mixins, had to choose one. §6.4's "surface it rather than choosing
unilaterally" cannot be satisfied literally by a PR whose deliverable is that
statement; what it can do is choose deliberately, say why, and surface the choice
before the PR merges. This file is that.

## The rule PR-17 adopted

**Alphabetical by mixin class name, with `object` last.**

```python
class PdsFile(_LocalFsMixin, _ShelfMixin, object):
```

Asserted by
`tests/api/test_mixin_collisions.py::test_the_mixin_bases_are_listed_alphabetically`,
and reasoned in `plans/2026-07-27-pr-17-subplan.md` §4 and
`critiques/phase5-validation.md`'s PR-17 §6. In short:

1. **MRO order is behaviorally inert here, and is kept that way deliberately.**
   The mixins share no attribute name and none shadows a name `PdsFile` defines
   itself — the same test file asserts both. So the ordering rule cannot be
   chosen for semantics; it should be chosen for reviewability.
2. **Append-on-arrival would encode PR chronology** into the class statement: by
   PR-22 the list is eight entries whose order means "the sequence six executors
   happened to run in". A reader cannot derive that and a reviewer cannot check
   it.
3. **Alphabetical gives every future mixin exactly one legal position**, derivable
   without knowing anything about PR order, and it is machine-checkable — so the
   convention survives without each executor having read this file.
4. **Dependency order would be a lie.** `_LocalFsMixin` calls into `_ShelfMixin`,
   but through `cls.`, so no ordering of bases expresses or affects it.
5. `object` stays last, where it already was, so `PdsFile.__bases__[-1] is object`
   is unchanged.

## What `object` is doing in that list

`object` is **not a mixin**, and it is **not required** — in Python 3 every class
derives from `object` whether or not it is written down, so
`class PdsFile(_LocalFsMixin, _ShelfMixin)` would produce the identical MRO.

It is in the list for one reason only: **it was already in the class statement
before this PR** (`class PdsFile(object):`), and PR-17 is a move PR, which changes
nothing it does not have to. Nothing about the mixin decomposition needs it, and
nothing about the alphabetical rule depends on it — `tests/api/test_mixin_collisions.py`
discovers mixins by filtering `object` out of `PdsFile.__bases__`, so the rule and
the collision checks read the same either way.

**Removing it is an unrelated cleanup and belongs to a later PR.** `ruff`'s
`UP004` already flags it and that code sits in `pdsfile.py`'s permanent ratchet
entry, so PR-23 — which owns the core modules' ruff cleanup — is the natural home.
Whoever does it should also drop the one line that depends on it:
`test_the_class_statement_stays_in_pdsfile_pdsfile` asserts
`PdsFile.__bases__[-1] is object`, which pins that no mixin was appended *after*
`object` and which stops being meaningful once `object` is gone.

## Why this needs a decision rather than only a record

`_OpusMixin` sorts **before** `_ShelfMixin`, so the preamble's illustration is in
the opposite order to the rule. Nothing is wrong today, but an executor of
PR-18–PR-22 who reads only the plan will write a class statement the test
rejects, and the round is wasted discovering why.

## The decision

**The rule stands** (owner, 2026-07-27), and the assertion stays in
`tests/api/test_mixin_collisions.py`.

**The preamble's illustration is being corrected separately, in PR #110**, which
targets `rewrite` directly. `plans/2026-07-25-modernization-plan.md` is therefore
**not** edited on the `pr-17-shelves-local-fs` branch — doing so would conflict
with that PR. Anyone reading the preamble before #110 lands should read the
illustration as showing the technique, not the ordering.

## Cross-references

- `critiques/deferred-observations.md` entry 35 — the same item in the deferred
  list, pointing here.
- `plans/2026-07-27-pr-17-subplan.md` §4 — the reasoning, written before the code.
- `critiques/phase5-validation.md`, PR-17 §6 — the delivered statement and the
  mutation evidence that the assertion is not tautological.
