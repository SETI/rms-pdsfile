# Addendum: Phase 5's stack extends through PR-22

**Date:** 2026-07-27
**Status:** **ACKNOWLEDGED** — this is an owner instruction, recorded here for
provenance. It is not a request for a decision, and no executor should re-surface
it as a hard stop.
**Amends:** `plans/2026-07-25-modernization-plan.md` §6.7 (execution topology)
for PR-18 through PR-22.
**Extends:** `plans/2026-07-26-addendum-phase5-stacked-prs.md`, which did the
same for PR-15, PR-16 and PR-17.

## What §6.7 says

> **PRs within a phase are strictly ordered** (a later PR-executor starts only
> after the prior PR is merged to `rewrite`, unless the plan marks them
> independent); per-PR subagents bound *context*, not concurrency.

## The instruction

On **2026-07-27** the repo owner directed that PR-18 through PR-22 **continue the
existing stack** — each branching off its predecessor and opened against it —
rather than each merging to `rewrite` before the next begins.

| PR | Branch | GitHub base |
|---|---|---|
| PR-18 `refactor: extract checksum/archive/log path builders → _derived_paths.py` | `pr-18-derived-paths` | `pr-17-shelves-local-fs` |
| PR-19 `refactor: extract OPUS and index-row support → _opus.py, _index_rows.py` | `pr-19-opus-index-rows` | `pr-18-derived-paths` |
| PR-20 `refactor: extract associations, split/sort, transformations` | `pr-20-associations-sorting` | `pr-19-opus-index-rows` |
| PR-21 `refactor: extract preload machinery → _preload.py` | `pr-21-preload` | `pr-20-associations-sorting` |
| PR-22 `refactor: finalize pdsfile.py core` | `pr-22-core-finalize` | `pr-21-preload` |

§6.4 requires that a deviation from the plan carry "an addendum file in `plans/`
acknowledged by the owner before the deviating PR merges". **The instruction is
the acknowledgment**; this file is the record of it.

## Consequences each of the five executors must honor

These are identical to the PR-15–17 regime; they are restated rather than
cross-referenced because an executor reading only its own PR's brief has to be
able to act on them.

1. **Open the PR with `--base <parent branch>`, never `rewrite`.** GitHub then
   shows only the incremental diff, and it retargets the base automatically when
   the parent merges.
2. **Every diff handed to a §6.6 adversarial reviewer is
   `git diff <parent-branch>...HEAD`**, not a diff against `rewrite`. A reviewer
   shown the cumulative diff would correctly flag the parents' changes as scope
   creep, and the round would be wasted.
3. **The §6.2 comparison baseline is the parent's recorded result**, read out of
   that PR's section of `critiques/phase5-validation.md` and **re-measured on the
   parent tip** rather than copied from a table. PR-18 diffs against PR-17's
   recorded set, PR-19 against PR-18's, and so on. Each section of
   `critiques/phase5-validation.md` states which set it compared against.
4. **No rebase and no force-push of a branch that has a child.** Rewriting a
   parent's history would orphan its children. If a parent pushes a review fix
   after a child branched, the child merges it forward and says so in its PR
   description.
5. **Human review still happens at every PR boundary** (§6.4, §8.6). Stacking
   changes the merge order, not the review cadence.

## What is new relative to the 2026-07-26 addendum

Two things, and only two.

1. **The stack is now eight PRs deep, not three.** PR-15 (#108), PR-16 (#109) and
   PR-17 (#111) are open and unmerged when PR-18 branches, so the `--base` chain
   and the chain of §6.2 baselines both run the full length
   `rewrite → PR-15 → PR-16 → PR-17 → PR-18 → PR-19 → PR-20 → PR-21 → PR-22`.
   Every link is a place where an executor can silently measure the wrong tree:
   the branches share one editable install, so a worktree run at a parent tip can
   import the main tree's `src/` and make the whole set diff vacuous. PR-16 and
   PR-17 both defended against this with
   `coverage.CoverageData.measured_files()`, printing the **absolute** path of
   every `pdsfile` module each run actually imported and showing that the modules
   the PR creates are **absent** on the baseline side. That check is now part of
   the regime, not an optional flourish.

2. **PR #110's plan corrections merged to `rewrite` after the stack branched.**
   `docs: correct two Phase-5 plan statements…` landed on `rewrite` on
   2026-07-27, so its two corrections are **not** in
   `plans/2026-07-25-modernization-plan.md` as that file appears on any branch in
   this stack. Do **not** merge `rewrite` forward to obtain them — that drags
   #110's diff into the PR. The corrections are:

   - PR-15's bug 2 is not dead code (memcached with a warm cache reaches it).
     Historical; it affects nothing PR-18–22 do.
   - **The order of `PdsFile`'s mixin bases is alphabetical by mixin class name**
     (owner, 2026-07-27). The preamble's illustration on these branches reads
     `class PdsFile(_ShelfMixin, _OpusMixin, …)`, which is the opposite order.
     **Read the rule from
     `plans/2026-07-27-addendum-phase5-mixin-base-order.md`, not from the plan
     text on the branch.** It is enforced by
     `tests/api/test_mixin_collisions.py::test_the_mixin_bases_are_listed_alphabetically`,
     so an executor who follows the stale illustration writes a class statement
     the suite rejects.

## What does not change

Everything else in §6.7 stands: one PR-executor subagent per PR, a fresh
no-context adversarial reviewer per §6.6 round under it, records in
`critiques/pr-<NN>/`, and the same §2 gate table for every PR.
`tests/api/test_mixin_collisions.py` **discovers** the mixins from
`PdsFile.__bases__` rather than listing them, so each new mixin inherits its
collision, shadowing, reachability, no-`__init__` and base-order checks for free.
