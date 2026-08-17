# PR-36 (reports half) round 2 — full diff

Reviewer: a fresh, no-context subagent with the same brief shape as round 1 —
the PR-36 plan entry with the reports-only scope, §2, §6.1-§6.2, §6.6 with the
compliance schedule, the three SKILL.md files, the exact diff
`git diff 6525951..507a262` (five files under `critiques/`, 2,422 insertions),
repo and register read access, and the recorded gate and coverage evidence —
plus the instruction to sample DIFFERENT claims than the headline ones:
section-interior figures, the appendix command entries, the parser
cross-checks. It also checked that every fix the round-1 record claims was
actually applied. It made no edits.

The reviewer independently reproduced: the scope and base (`6525951` = head of
`rewrite`); the full gate log end to end; the suite and coverage evidence
(including the 34-skip decomposition and ~30 per-module percentages); every
TS defect site including the round-1 corrections (COISS triple row, PT014 via
ruff, the 8-vs-7 import count); the DOC drift sites against
`run-all-checks.sh` and its own AST walks for the docstring measurements; the
CA measurements including both tool-pair diffs (242/2,032 and 209/2,171,
exact), the 8 no-encoding sites by its own sweep, and the wheel contents; 21
register entries read in full against the triage's characterizations, with
negative searches confirming the "new" claims for TS-15, TS-17/CA-14, CA-20,
CA-21 and CA-24; the triage arithmetic recomputed by hand; and the presence
of all four round-1 fixes.

Verdict: **goal met** — zero Major, five Minor, one Deferred. Per §6.6 the
loop continues until a fresh round returns no *new, un-rebutted* Minor, so
all five were fixed and round 3 re-reviews the result.

## Minor findings, and their resolutions

**m1. CA-15's "LRU-bounded" is contradicted by open register entry 4056**,
which demonstrates the shelf-cache access counter rebinds per subclass, so
eviction order is not actually least-recent-use; the size bound itself is
real. A positive health claim contradicted by an open entry had escaped the
triage's overlap sweep. **Fixed:** CA-15 now says "size-bounded ... intended
as least-recent-use" and cites 4056; the triage's CA-15 row and register
table carry the entry.

**m2. An appendix command names the wrong file.** `sort_labels_after` is
defined in `pdsfile.py:404`, not `_sorting.py`; the command as recorded
returns nothing, though TS-12's substantive claim is correct via the entry's
first command. **Fixed:** file name corrected.

**m3. The appendix's "7 private-module import statements" went stale against
round 1's §20 fix** (eight statements; the grep pattern cannot see the
`from ..._common import` form). **Fixed:** the appendix entry now states the
command's undercount and the corrected figure.

**m4. The triage's TS-02 row said "different tests" where half of TS-02
restates entry 3202's own recorded content** (`viewset_lookup` never checks a
length). **Fixed:** the row and the register table now split the claim — the
`viewset_lookup` half restates 3202, the cached `test_childnames` half is
new.

**m5. The test report's fix-prompt step 5 unconditionally instructed the
`COVERAGE_PROCESS_START` wiring that register entry 4214 measured at 8.6x
and deferred to PR-37.** The triage said so; the prompt — the artifact an
agent would execute — did not. **Fixed:** step 5 now leads with 4214's
ownership and cost, forbids wiring it in the fix pass, and keeps the shape
only as PR-37 reference material.

## Deferred (recorded, no register edits in this PR)

- Register entry 1000 appears stale: both `_derived_paths.py` docstring
  defects it records are fixed in the tree (verified at `:562` and `:301`).
  Added to the triage's register-grooming list alongside round 1's items.

## Gates after the round's fixes

The fixes touch only record files under `critiques/` — nothing under `src/`,
`tests/`, `docs/` or configuration — so per §6.6 step 5 the full-data record
carries forward: the gate log (`run-all-checks.sh` green in full, ns 1234/34)
and the session's s-mode runs (555/3, 150/31) remain the evidence of record.
