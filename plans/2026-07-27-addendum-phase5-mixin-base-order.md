# Addendum: the order of `PdsFile`'s mixin bases is alphabetical

**Date:** 2026-07-27
**Status:** **AWAITING OWNER ACKNOWLEDGEMENT** — §6.4 requires an addendum in
`plans/` acknowledged by the owner before the deviating PR merges. PR-17 may be
reviewed and opened without it; it may not **merge** without it.
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

## Why this needs a decision rather than only a record

`_OpusMixin` sorts **before** `_ShelfMixin`, so the preamble's illustration is in
the opposite order to the rule. Nothing is wrong today, but an executor of
PR-18–PR-22 who reads only the plan will write a class statement the test
rejects, and the round is wasted discovering why.

## The two forms the decision can take

Either is one line of work; PR-17 is green under (a) as delivered.

**(a) Keep the rule.** Reorder the preamble's illustration and say so — e.g.
`class PdsFile(_LocalFsMixin, _OpusMixin, _ShelfMixin, …)  # bases listed
alphabetically`. Nothing in the branch changes.

**(b) Drop the rule.** Delete
`test_the_mixin_bases_are_listed_alphabetically` from
`tests/api/test_mixin_collisions.py`; each later PR then appends its mixin
wherever it likes. The convention stays documented in the sub-plan and the
validation record but is not enforced.

Both are behaviorally identical: PR-17's full-data set, its empty manifest diff
and every other gate are unaffected either way, because the mixins are disjoint.

## Cross-references

- `critiques/deferred-observations.md` entry 35 — the same item in the deferred
  list, pointing here.
- `plans/2026-07-27-pr-17-subplan.md` §4 — the reasoning, written before the code.
- `critiques/phase5-validation.md`, PR-17 §6 — the delivered statement and the
  mutation evidence that the assertion is not tautological.
