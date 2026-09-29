# Owner four-items fix, round 3 — adversarial review

Reviewed: `git diff b8c1ac1..271e195` (the four fixes with rounds 1 and 2
resolved). A fresh no-context reviewer, given the owner's instruction, plan
§2/§6.1/§6.2/§6.6, the exact diff, the prior round records (to avoid
re-litigating, not to inherit conclusions) and repository read access. No
edits by the reviewer.

**Counts.** 1 Major, 3 Minor, 0 Deferred. Verdict: goal not met, solely on
the Major — which, like round 2's, is in the records, not the code: the
reviewer probed the regex against live holdings and every consumer, re-took
the ruff measurement as the comment now writes it (43 files, 98 findings),
re-counted the register (10/0/15/136/52 = 213, equation balancing),
confirmed the staleness rule was honored (nothing under `src/` or `tests/`
moved after the §5 regeneration), and collected the suite counts
(1261/558/181) to the recorded arithmetic.

---

## Major 1 — the record claimed all six chain commands exit 0; the sixth exits 1 — FIXED

`critiques/owner-four-items-validation.md` §4 said the user guide's chain for
`cassini_uvis_solarocc_beckerjarmak2023`, run against a scratch copy, ended
with "all commands exit 0". The reviewer rebuilt the chain faithfully: the
five build commands exit 0 and both archive-side products are written, but
`pds4linkshelf --initialize` writes its shelf and exits 1 with the bundle's
documented recurring link error — which the edited chapter itself states ten
lines below the new code block. The measurement behind the record had run
only the five build commands and the sentence claimed all six.

**Resolution.** §4 now states the five-command result as measured, the
sixth command's exit-1 as round 3 measured it, and that the first version of
the sentence overclaimed. The user guide needed no change: its text was
already correct, in both directions.

## Minor 1 — entry 4065 cited the source guard's lines for the destination guard's defect — FIXED

`copy_shelves.sh`'s misprinting destination guard is lines 23–25; the entry
said 20–22, which is the (correct) source guard. The register entry now
cites 23–25. Round 1's record carries the same numbers and stays as written:
round records are frozen history.

## Minor 2 — the after-sweep set listing named files the grep does not return — FIXED

Round 2's record contains no literal `3.10` (only the escaped pattern), so
"the review-round records" overcounted. The sentence now says "whichever
round records quote the literal digits (round 1's does)".

## Minor 3 — the sweep was blind to the `py310` spelling — FIXED (recorded)

`git grep "3\.10"` cannot see ruff's `target-version = "py310"`. The second
sweep is now in §1: nine completed-PR subplans (pr-16 through pr-24) record
the configuration their ratchet re-derivations ran under — historical, like
the archived v1 plan, though they live in `plans/` — and pr-23's "i.e.
`pyproject.toml`'s" clause, the one reading closest to a present-tense
claim, is flagged to the owner rather than edited.

---

This round's fixes touched only `critiques/` records, so the full-data
evidence of `ee89c16` carries forward per §6.6 step 5.
