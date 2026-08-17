# shelf_consistency_check removal, round 1 — adversarial review

Reviewed: `git diff fix/archive-infoshelf-rebuild..HEAD` at `f6b9759` (the whole
removal in one commit: 28 files — 3 deleted, 24 edited, 1 added, the addendum). A fresh no-context reviewer
was given the owner's instruction, plan §2/§6.1/§6.2/§6.6, the exact diff and
repository read access, and told to prove a missed reference, a wrong count, or a
false historical claim. No edits by the reviewer.

**Counts.** 1 Major, 5 Minor, 0 Deferred. The reviewer independently re-verified
all five historical claims against git (commits `a6f3949` and `67f7b93`, the
`-S'shelves/info'` pickaxe, and a read-only run of the parent-branch tool against
the real holdings root reporting `Tests performed: 0`), recounted every count in
the diff (fourteen programs, nine pds3 modules, eleven-of-thirteen in
`re_validate.py`, 78 -> 77 automodule entries, register index 10/0/16/134/52 = 212
with the closure equation balancing), and swept the tree for missed references,
finding none in `docs/`, `src/`, `tests/`, `scripts/`, `.cursor/` or `README.md`.

---

## Major 1 — plan §8 settled decision 4 still names the deleted tool — FIXED

`plans/2026-07-25-modernization-plan.md:1877`: "**No new console scripts** for
`crlf`/`shelf_consistency_check`/`show_opus_products`" was left unannotated,
while the same document strikes through or annotates superseded decisions
(items 1 and 2) and the PR annotated the deferred-table row the same way. A
standing constraint is current-state text.

**Resolution.** The decision now names the two surviving tools and carries a
dated note that the third was removed outright, pointing at the addendum and
issue #156.

## Minor 2 — "Entries 6, 11, 66 and 72 carry that disposition in their own text" — FIXED

`plans/2026-07-25-modernization-plan.md:767`: entry 6's own text (in the frozen
source register) still carries the old PR-28 routing, so the sentence was no
longer true of it. Now reads "Entries 11, 66 and 72 …; entry 6's supersession is
recorded in its table row above and in the addendum."

## Minor 3 — coderabbit-findings.md Critical 1 cites a pinning test that no longer exists — FIXED

The closed entry described the fix's regression test in the present tense, and
the log's header instructs verification against current code. A bracketed status
note now records that the tool, its tests and the pinning test were removed
(owner decision 2026-08-16, issue #156), so the entry is moot as well as fixed.

## Minor 4 — observation 4201's measured command was edited rather than annotated — FIXED

`critiques/observations-p3.md` (entry 4201): the PR dropped
`test_shelf_consistency_check.py` from a recorded pytest invocation without
saying so, where this register marks re-derivations explicitly. A parenthetical
now records the original command and why the reduced one carries the same claim
(none of the removed tests touched `Pds4File` or its preload; round 4 tightened
this wording — one of the 19 was `full_holdings`-marked, so "holdings-free" was
an overstatement).

## Minor 5 — the addendum's "18 tests" is the function count, not the collected count — FIXED

`plans/2026-08-16-shelf-consistency-check-removal-addendum.md`: one test was
parametrized over `--help`/`-h`, so 18 functions collect as 19 tests, and the
suite's pass count drops by 19 (1209 -> 1190), not 18. The addendum now states
both numbers.

## Minor 6 — the pyproject ratchet comment adds history narration — REBUTTED

`pyproject.toml:255-256`: the edited sentence ("the F821 on the shelf
consistency checker, a tool since removed outright (issue #156)") sits inside a
pre-existing deviation-history block whose whole purpose is to explain entries a
reader of deviation (4) would otherwise expect to find; every sentence around it
is the same kind of prose, and the alternative — keeping the old text — would
name a file path that no longer exists. The edit conforms to the block's
established style and cites the issue number, which the comment rules allow. No
change.

---

**Verdict (reviewer's, verbatim):** "the removal is thorough and every
historical claim it makes is true; one Major — the plan's live settled-decision
4 (line 1877) still names the deleted tool unannotated — plus five judgment-call
Minors."

All findings fixed or rebutted above; round 2 gets a fresh reviewer and the
updated diff.
