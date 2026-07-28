# PR-22 — adversarial review round 4 (scoped)

**Date:** 2026-07-28
**Reviewer:** a fourth fresh, no-context opus-class subagent, run as §6.6's
**scoped** fourth round: "confirm the prior round's findings are resolved; raise
only **new Major** findings". It was given the three prior round records and asked
to verify by measurement that each of the 23 Minor fixes is in the tree and
correct — because a fix that introduces a new wrong figure is exactly what this
round exists to catch.
**Diff reviewed:** HEAD `a5d8105` ("docs: record round 3 and regenerate the
full-data record a third time").
**Verdict:** **goal met** — **0 Major**, 3 Minor, **0 new Deferred**.

## The 23 prior findings, re-verified by measurement

**21 of 23 fully resolved.** Two — round 1's Minor 3 and round 2's Minor 8, which
are the same finding (a figure about `_properties.py`'s size and the moved blob's
offset within it, re-measured at HEAD rather than carried forward) — had
**regressed by two lines**, because round 3's own docstring fix added two lines to
`_properties.py` after the round-3 recording commit had already updated the
neighbouring figures. That is Minor 1 below.

The reviewer re-derived, rather than read: the 40/39/24 property split and the 24
names; the ten-import block; the 63-properties table row; the seven dead-code
lines and which five fall inside an AST span; the 47 `_recache` sites; all three
module-map inventories against `vars()` of the live classes; the `timeout=60`; the
absence of the dropped summarizing sentence; the "in 39 of the 40" clause;
`_LocalFsMixin`'s five methods and the 13-name constructor list; 1,939; six
mutation rows; the nine boundary counts and 183+689+311+532+756+422 = 2,893; the
sub-plan's 47; the four slot-free core properties; `all_viewsets` as `child`'s
method; the banner's "(in all but one case)"; **1,774 lines and MD5 `e2be29a1…`,
rebuilt from the parent by deleting 672–2230 and splicing `LATEST_VERSION_RANKS`
plus one blank line, then compared**; the 8-of-71 receivers and the five genuine
ones; the two-missed-plus-one-mis-classified split; and the sub-plan's +82 term.

## New Major

**None.**

Everything load-bearing re-derived independently for the fourth time: the
1,557-line blob and 68/68 definitions byte-identical; 34 of 37 core definitions
unchanged with a five-minus, zero-plus diff; 61 → 61 class-level assigns and 0 in
the mixin; 41 written slots all created by `PdsFile.__init__`; the seven-name free
variable sweep with **0 unsatisfied and 0 unused** imports and each name the same
object in both namespaces; no `PdsFile` class-object reference anywhere in the
mixin; the API dump byte-identical with provenance proved, plus a full `dir()`
sweep over seven modules and three classes that adds only the two
underscore-prefixed names and removes nothing; all 17 ratchet codes conserving,
both entries minimal *and* complete, 65 → 63, and the ten-module union inside
`rewrite`'s 25; its own two-pass dead-code sweep finding the same 8 lines on
`rewrite` and **0** code-like comments at HEAD, with every line number in §7 exact;
the stay-list complete at 98 body names; the recorded set diffs; freshness; §15's
114-name contract; §10's statement counts (which reproduce once the two
`# pragma: no cover` clauses are excluded); consumer smoke Check A at 4/4 with both
rms-viewmaster flat-name failures still failing; the four frozen files untouched.

It broke the entry-42 check again — tail-placed import red on the `sys.modules`
assertion, function-local deferred import green — for the fourth independent
confirmation that the check is neither vacuous nor exit-code-only.

## New Minor — three, all accepted, all fixed

### Minor 1 — `_properties.py` is 1,686 lines and the blob is at 130–1686

Round 3's fix commit `11ddf91` added two docstring lines; the round-3 recording
commit `a5d8105` updated §3, §5.1(c), §15 and §20 but not the size and offset
figures, which had been set two commits earlier. Measured: `wc -l` is **1,686**,
and brute-forcing the recorded MD5 over every line range finds the blob at
**130–1686** and nowhere else (the digest of 128–1684 is a different value
entirely). The byte-equivalence *conclusion* was never in doubt; only the
coordinates were stale. Fixed in four places — §5, §5.1(a), §18's module total
(5,118 → 5,120) and deferred observation 65, which PR-23 consumes.

**This is round 1's Minor 3 recurring for the third time**, so the fix is not only
the number: §5.1(a) now says the offset is obtained by searching every line range
for the digest, rather than by adding up how much the docstring above it has
grown. That is the method that cannot go stale.

### Minor 2 — the sub-plan's round summary still describes two rounds

`plans/2026-07-27-pr-22-subplan.md` §7 item 9 said "Two review rounds produced
sixteen findings … regenerated twice". Item 8 beside it was updated at `a5d8105`
and item 9 was not. Now four rounds, twenty-six findings, three regenerations, and
the note that round 4's findings changed only records so no fourth regeneration was
needed.

### Minor 3 — `time`'s three textual matches are two comments and a docstring

`critiques/phase5-validation.md` §5.3. Measured in the moved block: `# Convert
formatted time to datetime`, `# Don't look for PdsViewSets at bundle root; saves
time`, and `"""Return the modification date/time of this file …`. The substantive
claim — no code site, so the free-variable sweep's "nothing else" holds — is
correct either way. Corrected.

## Deferred

**None new.** The reviewer confirmed entries 61–65 cover everything out of scope
that it found, and that entries 32 and 42 are correctly marked RESOLVED.

## Termination

§6.6's hard cap is four rounds, and this is round 4. It returned **zero Major**;
its three Minors are stale or imprecise figures in `critiques/` and `plans/`, all
three fixable in place, and **none of them touches `src/pdsfile/`** — so the
full-data record above carries forward unregenerated (§6.6 step 5) and **no fifth
reviewer was run**, which the cap forbids.

The loop's arithmetic across four rounds: **26 findings, 0 Major**. Ten were
statements in docstrings under `src/pdsfile/`, fifteen were figures or labels in
this validation record and the sub-plan, and one was a missing subprocess timeout
in the new test. **Not one was in the extracted code** — the same result PR-19,
PR-20 and PR-21 each produced, on the largest single move of the phase.
