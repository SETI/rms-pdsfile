# Addendum: Phase 5's first three PRs are stacked, not merged one at a time

**Date:** 2026-07-26
**Status:** **ACKNOWLEDGED** — this is an owner instruction, recorded here for
provenance. It is not a request for a decision.
**Amends:** `plans/2026-07-25-modernization-plan.md` §6.7 (execution topology)
for PR-15, PR-16 and PR-17 only.

## What §6.7 says

> **PRs within a phase are strictly ordered** (a later PR-executor starts only
> after the prior PR is merged to `rewrite`, unless the plan marks them
> independent); per-PR subagents bound *context*, not concurrency.

## The instruction

On **2026-07-26** the repo owner directed that the first three Phase-5 PRs be
**stacked** — each branching off its predecessor and opened against it — rather
than each merging to `rewrite` before the next begins.

| PR | Branch | GitHub base |
|---|---|---|
| PR-15 `fix: repair latent bugs in rarely/never-exercised core paths` | `pr-15-latent-bug-fixes` | `rewrite` |
| PR-16 `refactor: extract module-level path helpers → _path_utils.py` | `pr-16-path-utils` | `pr-15-latent-bug-fixes` |
| PR-17 `refactor: extract shelf and local-filesystem subsystems` | `pr-17-shelves-local-fs` | `pr-16-path-utils` |

§6.4 requires that a deviation from the plan carry "an addendum file in `plans/`
acknowledged by the owner before the deviating PR merges". The instruction *is*
the acknowledgment; this file is the record of it. No executor should re-surface
the stacking as a hard stop.

## Consequences each of the three executors must honor

1. **Open the PR with `--base <parent branch>`, never `rewrite`.** GitHub then
   shows only the incremental diff, and it retargets the base automatically when
   the parent merges.
2. **Every diff handed to a §6.6 adversarial reviewer is
   `git diff <parent-branch>...HEAD`**, not a diff against `rewrite`. A reviewer
   shown the cumulative diff would correctly flag the parent's changes as scope
   creep, and the round would be wasted.
3. **The §6.2 comparison baseline is the parent's recorded result, not
   `rewrite`'s.** PR-15 diffs against the `rewrite` @ `807956a` baseline; PR-16
   diffs against PR-15's recorded post-fix set; PR-17 against PR-16's. This
   matters because **PR-15 is explicitly permitted to change the set** (§5,
   PR-15, bug 1) and it also adds a test directory, so inheriting `rewrite`'s
   numbers downstream would manufacture a false failure. Each section of
   `critiques/phase5-validation.md` states which set it compared against.
4. **No rebase and no force-push of a branch that has a child.** PR-16 branches
   off PR-15's tip and PR-17 off PR-16's; rewriting a parent's history would
   orphan its children. If a parent pushes a fix after a child branched, the
   child merges it forward and says so in its PR description.
5. **Human review still happens at every PR boundary** (§6.4, §8.6). Stacking
   changes the merge order, not the review cadence.

## What does not change

Everything else in §6.7 stands: one PR-executor subagent per PR, a fresh
no-context adversarial reviewer per §6.6 round under it, records in
`critiques/pr-<NN>/`, and the same §2 gate table for every PR.
