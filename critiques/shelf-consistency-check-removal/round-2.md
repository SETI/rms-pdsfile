# shelf_consistency_check removal, round 2 — adversarial review

Reviewed: `git diff fix/archive-infoshelf-rebuild..HEAD` at `9c44730` (the removal
plus round 1's fixes), by a fresh no-context reviewer with the owner's
instruction, plan §2/§6.1/§6.2/§6.6, the exact diff and repository read access.
No edits by the reviewer.

**Counts.** 1 Major, 2 Minor, 1 Deferred. The reviewer re-swept the tree
(no missed references), recomputed every count from scratch (all correct,
including the interlocking installation.rst set, support.py's "two tools", the
automodule sum 15+22+2+11+27 = 77, and the register index and closure equation),
re-verified all five historical claims against git and a live read-only run, and
confirmed round 1's six resolutions landed as recorded.

---

## Major 1 — ground rule 9 ("no feature removal") left unannotated — FIXED

`plans/2026-07-25-modernization-plan.md:155-159`: §2's locked decision "Leave
all functionality in place … no feature removal" was still unqualified while the
PR removed a feature — the same defect class round 1 found in §8, one section
over. **Resolution:** the rule now carries a dated owner-exception note: the
removal was the owner's explicit instruction, not the rule's "probably dead"
heuristic, pointing at the addendum and issue #156.

## Minor 2 — round 1's record miscounted its own diff — FIXED

`critiques/shelf-consistency-check-removal/round-1.md`: "3 files deleted, 25
edited" for a 28-file diff that was 3 deleted, 24 edited, 1 added. Now states
all three numbers.

## Minor 3 — the addendum's "Edited:" list read as complete and was not — FIXED

`plans/2026-08-16-shelf-consistency-check-removal-addendum.md`: the scope
paragraph omitted the register and closed-log annotations and (after round 1)
the plan's own settled-decision and ground-rule notes. It now names those
groups, defers the authoritative file list to the PR diff, and points at the
validation record for the measured gate numbers.

## Deferred 4 — the suite pass counts traced to no recorded run — RESOLVED BY THE VALIDATION RECORD

Round 1's "1209 -> 1190" appeared in no run record at the time of review. The
validation record (`critiques/shelf-consistency-check-removal-validation.md`,
written after this round) carries the measured runs: the full-gate log's
`1190 passed, 34 skipped` line, both s-mode passes at their baselines, and the
arithmetic tying 1190 + 19 collected-in-the-deleted-file to the 1209 baseline.

---

**Verdict (reviewer's, verbatim):** "the removal itself is complete and every
historical claim true; goal not met as it stands — one Major: ground rule 9 …
is live locked-decision text left unannotated by the PR that removed a feature —
plus two record-accuracy Minors and one Deferred."

All findings fixed or resolved above; round 3 gets a fresh reviewer and the
updated diff.
