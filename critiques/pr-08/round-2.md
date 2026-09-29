# PR-08 adversarial review — round 2

Fresh, no-context Opus reviewer subagent (§6.6), on the round-1-updated diff
`origin/rewrite...pr-08-extract-rule-tests`. No knowledge of round 1.

## Reviewer verdict: **goal met** — zero Major, two Minor.

The reviewer independently AST-compared all 16 moved test bodies and every
touched rule module's production nodes against `origin/rewrite` (identical bar
the test-section removal and the `PRIMARY_FILESPEC_LIST` re-export alias),
confirmed `VG_28xx.py` keeps its CRLF terminators (no whole-file flip), the
ratchet has no grown entry, the clean-install gate genuinely catches a pytest
leak, api-freeze passes hermetically, and no goldens changed.

## Major
None.

## Minor

**M1 — `tests/api/manifest_allowlist.json`: category #2 predicate broader than
§6.1 enumerates; `pytestmark` not pre-approved.** The round-1 predicate (i) used
`kind:"*"` for the whole list including the `test_*` glob, where §6.1(a)
restricts `test_*` to `function`; and (ii) forgave `pytestmark`, which §6.1's
category-#2 enumeration does not list. `pytestmark` is genuinely test-only (the
`cassini_iss_fring_mosaics_rsfrench2025` module's `pytest.mark.skip` marker,
which correctly moved to the test file with its tests), so no production surface
is masked — but §6.4 forbids the executor from broadening a forgiveness category
on its own.
**Resolution:**
1. Rewrote the PR-08 category as **two records faithful to §6.1**: (a)
   `^pdsfile\.pds[34]file\.rules\.[^:]+::test_[A-Za-z0-9_]+$` with `kind:"function"`;
   (b) the exact enumerated name-list with `kind:"*"`. This removes the
   `test_*` over-breadth.
2. With the faithful allowlist, api-freeze surfaced **exactly one** uncovered
   diff — `pdsfile.pds4file.rules.cassini_iss_fring_mosaics_rsfrench2025::pytestmark`
   (removed, kind data). Per §6.4 (hard stop: an API diff outside the two
   pre-approved categories; executor may not add a forgiveness rule on its own)
   this was **escalated to the owner**. The owner confirmed the skip marker
   itself is untouched (it lives in `tests/rules/pds4/test_cassini_iss_fring_mosaics_rsfrench2025.py`,
   fring tests still skip — verified 7 skipped) and **approved extending
   category #2(b) to include `pytestmark`** (2026-07-25). Added `pytestmark` to
   the (b) name-list with the approval recorded in the entry's `reason`.
   api-freeze now passes hermetically.

**M2 — sub-plan prose error re COISS `os` (no code impact).**
`plans/2026-07-24-pr-08-subplan.md` (lines 34, 117) claimed COISS "keeps
`import os` (production use at :1031)", but old line 1031 is inside
`test_opus_id_to_primary_logical_path` — COISS's `os` was entirely test-only.
The implementation was already correct (COISS rule module has no `import os`; os
moved to the test file). **Resolution:** corrected both sub-plan lines to state
COISS's `os` is test-only and moved to the test file (implementation unchanged).

## Deferred (non-blocking)
None new. (The round-1 deferred COISS-prose item is now fixed, not deferred; the
`_is_forgiven` `pr`-field and PR-07 helper-double-import items remain in
`critiques/deferred-observations.md`.)

## Re-verification after the fixes (allowlist + docs only; no `src/pdsfile/`
change, so the limited-holdings record from round 1 carries forward per §6.6
step 5)
- api-freeze hermetic → passes (1 passed); manifest unchanged; the single
  `pytestmark` diff now forgiven under the owner-approved category #2(b).
- `ruff check src/pdsfile tests scripts` → clean.
- Limited-holdings behavior unchanged from round 1 (ns 679/34, s 555/3); no
  source touched this round.
