# Addendum: four owner decisions taken before PR-23

**Date:** 2026-08-03
**Status:** **ACKNOWLEDGED** — these are owner instructions, recorded here for
provenance. They are not requests for a decision.
**Amends:** `plans/2026-07-25-modernization-plan.md` §2 (gate table), §5 (PR-23
and PR-24), §6.5 and §6.6 (compliance schedule), and
`.cursor/rules/pdsfile_overrides.mdc` deviations (3) and (4).

Phase 5's decomposition (PR-15 … PR-22) merged to `rewrite` on 2026-08-03 at
`a179163`. PR-23 and PR-24 are the two ruff PRs that close Phase 5. Four
questions were put to the owner before PR-23 began, because each of them changes
what PR-23 is allowed to do; all four were answered the same day.

## 1. The module-length waiver becomes an explicit list

Deferred observation 65 asked how to reconcile the waiver with what Phase 5
produced. `python.mdc` requires modules under 1000 lines;
`pdsfile_overrides.mdc` deviation (3) waived it for `pdsfile.py` and the rule
modules — a list written before the decomposition existed.

**Decision: enumerate the waived modules explicitly** rather than describing them
as a class. A named list has to be amended when a module joins it, and that is
the point: an addition is a visible decision rather than something that quietly
qualifies.

Splitting `_properties.py` was the alternative and was rejected. It would reopen
§8 settled decision 3, which deliberately puts the whole lazy-property block in a
single mixin so that core lands near ~1,750 lines.

## 2. `pdscache.py` stays at its current size, waived

**Decision: leave `pdscache.py` as it is and waive it.** It was over the line
before this effort began (1,044 lines, unchanged by Phase 5), and no phase in
this plan has splitting it as a deliverable.

## 3. The `ruff format` requirement is dropped

The plan made the one-time reformat conditional on an owner churn checkpoint at
PR-23 and PR-24 (§5, both PRs, step 2: "Stop and present the churn numbers and
diff samples to the owner. The owner decides: proceed as scoped, reduce the
scope, or **drop the reformat entirely**").

**The churn was measured on merged `rewrite` and presented: 14 of 15 files in
PR-23's target set would be reformatted, ~2,310 changed lines** — an upper bound,
taken before any `# fmt: off` guards.

What the diff showed is not cleanup but a house-style conflict. This codebase
aligns continuation lines under the opening parenthesis; `ruff format` breaks
each element onto its own line with a trailing comma. The change would therefore
rewrite the multi-line imports, the nine-mixin `class PdsFile(...)` statement,
and every multi-line signature — including those inside the nine modules whose
entire warrant is that their bodies moved byte-for-byte, a property four
adversarial review rounds per PR were spent establishing.

**Decision: drop the reformat entirely.** Consequences, per the plan's own step 3
("If the owner drops or reduces formatting, the gate matches the reduced scope
(or is never enabled) and the decision is recorded in `pdsfile_overrides.mdc`"):

- The one-time `ruff format` is **not run**, in PR-23, in PR-24, or later.
- The `ruff format --check` gate is **never enabled**. `ENABLE_RUFF_FORMAT` stays
  `false` in `scripts/run-all-checks.sh` and no CI job adds it.
- PR-23 and PR-24 keep their **`ruff check`** halves in full: deriving each
  file's violations, fixing the fixable ones, and shrinking the ratchet to the
  enumerated freeze-locked set. That work is unaffected.
- The `# fmt: off` / `# fmt: on` guards the checkpoint would have required are
  **not needed** and should not be added — they exist only to protect aligned
  blocks from a formatter that will not run.
- `[tool.ruff.format]`'s `quote-style = "single"` setting is inert but harmless;
  it stays, and its comment already says formatting is not enforced.

## 4. PR-23 and PR-24 are executed one at a time

Phase 5's decomposition was executed as an eight-deep stack of PRs, each based on
its predecessor (`plans/2026-07-26-addendum-phase5-stacked-prs.md`,
`plans/2026-07-27-addendum-phase5-stack-extension.md`).

**Decision: PR-23 and PR-24 are not stacked.** Each branches from `rewrite`,
opens against `rewrite`, and merges before the next begins — the topology §6.7
describes by default. Stacking existed only to avoid blocking on review, and its
one real cost is now understood: a squash-merge of any stack element rewrites the
history its children are built on and forces a rebase of everything above it.

Consequences: PR-24's §6.2 baseline is `rewrite` after PR-23 merges, not PR-23's
branch tip; each PR's reviewer diff is against `rewrite`; no forward-merging
between them.

## An open item this addendum does not decide

Measuring the waiver list turned up **three maintenance-tool modules over 1000
lines that decision 1 was not asked about**:
`holdings_maintenance/pds3/pdslinkshelf.py` (1,779),
`holdings_maintenance/pds4/pds4linkshelf.py` (1,274) and
`holdings_maintenance/pds3/pdsdependency.py` (1,166). One rule module,
`pds3file/rules/VG_28xx.py` (1,017), is already covered by the rule-module entry.

They are deliberately **not** added to the waiver here. Phase 6 (PR-25 onward)
consolidates the duplicated pds3/pds4 tool logic into `_common.py`, so their
sizes are expected to change; waiving them now would pre-empt that work with a
statement that is about to stop being true. Whether they end up waived or split
is a Phase-6 question. Recorded as deferred observation 66.
