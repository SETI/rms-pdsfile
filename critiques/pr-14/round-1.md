# PR-14 — adversarial review round 1

**Date:** 2026-07-26
**Reviewer:** fresh opus-class subagent, no development context, no prior rounds.
**Input:** the PR-14 section + Phase-4 preamble + §2 + §6.1/§6.2/§6.4/§6.6 of
`plans/2026-07-25-modernization-plan.md`, the two relayed owner decisions
(#102 → drop the classifier; `--mode` → `default='ns'` + `choices`), the exact
`git diff origin/rewrite...HEAD`, and read access to the repo at HEAD.
**Verdict:** `goal not met` (1 Major, 5 Minor, 4 Deferred).

## Major

### M1 — Deferred entry 9 was closed on a survey conclusion that is false

The records claimed "the survey for other genuinely holdings-free tests found
none: everything else under `tests/` either instantiates a `PdsFile` against a
holdings root or needs the copied tool tree". The reviewer showed that
`from_abspath` / `from_logical_path` only parse a path — they do not stat — and
measured **291 tests outside `tests/api/` passing with no holdings** once the
blanket skip is lifted. The PR-14 bullet names "any other no-data tests", so the
claim is both in scope and hollow.

**Disposition: the false claim is FIXED; the demand to mark them is REBUTTED.**

*Fixed.* The reviewer is right that the stated reason was wrong, and the
measurement was reproduced independently: `315 passed / 387 failed /
122 skipped` with a throwaway `tryfirst` plugin marking everything
`holdings_free` and all four holdings env vars unset. Per function: 124
all-cases-pass, 41 mixed, 126 all-fail. Not order-dependent (each module alone
yields the same passing set as inside the whole-tree run). §4 of
`critiques/pr-14/validation.md` now carries the measurement instead of the
inspection claim, and the entry-9 note in `critiques/deferred-observations.md`
no longer asserts an empty search.

*Rebutted.* Marking them is not the right answer, for reasons the measurement
itself supplies:

1. They fail the marker's own registered definition ("test builds its own inputs
   and needs no holdings tree"). They concatenate the **resolved** holdings root,
   which with no holdings is PR-09's synthetic placeholder — visible in the test
   ids, e.g.
   `test_logical_path_from_abspath[/pdsfile-no-holdings/pdsdata/holdings/volumes/...]`.
   Passing against a root that does not exist is a different property from
   needing no root.
2. There is no boundary to mark along: 41 functions are **mixed** at the
   parametrized-case level, so the split runs through the middle of the inline
   `@parametrize` tables. Splitting those is issue **#92**, which §9 of the plan
   lists as future work outside this effort. The reviewer concedes this point
   ("the fix is not trivially 'mark the modules'").
3. Nothing pins the no-filesystem-access property, so a mark is a hosted-CI-only
   tripwire — the failure class that cost PR-13 three CI-only failures — placed
   immediately before Phase 5 rewrites those very paths (PR-15 bug 3 changes the
   holdings-env lookup in `abspath_for_logical_path`; PR-16 moves
   `logical_path_from_abspath`, `repair_case`, `selected_path_from_path`).
4. §1 G3 enumerates the subset as "API freeze, tool unit tests,
   import/collection smoke". The Phase-4 bullet's "any other no-data tests" reads
   against that enumeration; the blackbox/whitebox suites are the data suite.

The reviewer's own supporting observations argue the same way: some of the passes
are tautological (`test__info` asserts `res1 == res2`;
`test_logical_path_from_abspath` swallows `ValueError` into `assert True`).

The option is preserved rather than dropped: **entry 15** in
`critiques/deferred-observations.md` records the numbers, the four reasons, and
assigns it to issue #92 / post-merge.

## Minor

### m2 — The PR rewrote owner-locked deviation (7) on one run's evidence

Valid. **Fixed by removing the cause rather than the record.** Deviation (7) is
reverted to its original wording, and `scripts/run-all-checks.sh` now defaults
`PYTEST_WORKERS` to **1 (serial)** instead of `auto`, so enabling the gate does
not quietly make full-data runs parallel. This also matches the plan's retirement
of PR-12 ("xdist … adds shared-state risk") and removes the unmeasured memory bet
the reviewer flagged (one preload measured at 105 MB peak RSS against the limited
copy; `-n auto` on a 30-core machine means 30 of them). `-w auto` remains
available and its measured equivalence (33.9 s vs 142.1 s, identical pass/skip
set) is recorded in `critiques/pr-14/validation.md` §3. Re-validated after the
change: with holdings 790/34 in 3 m 15 s; without holdings 24/800 in 21 s. No
plan addendum is needed, because no rule is now being deviated from.

### m3 — Round records referenced but absent

Valid and expected — this file is the first one. `round-<k>.md` files are
committed as each round completes, before the PR is opened.

### m4 — The nightly-alerting deliverable was unrecorded

Valid. §9 of `critiques/pr-14/validation.md` now states that settled decision
§8.7 (GitHub built-in notifications) stands, that this is a no-work deliverable,
and that the cron and its notification behavior are unchanged. The branch-
protection deliverable (§8.8) is recorded alongside it.

### m5 — The entry-8 re-deferral rested on an unreproducible measurement

Valid. Both `critiques/pr-14/validation.md` §7 and entry 8 of
`critiques/deferred-observations.md` now carry the exact command line, the exact
one-line code change that is the only variable, and the verbatim pytest summary
lines (`8 passed, 5 warnings in 16.06s` vs `8 passed, 5 warnings in 138.84s`).

### m6 — The new comments re-list the gate set the script is meant to own

Valid — enumerating the gates in a comment is the hand-maintained parity
`environment.mdc` exists to avoid, and it goes stale at PR-23/24 and PR-31. Both
the workflow comment and deviation (8) now point at the script instead of listing
its contents.

## Deferred (appended to `critiques/deferred-observations.md`)

| # | Item | Owner |
|---|---|---|
| 15 | ~291 data-suite tests pass with no holdings; measurement + why they are not marked | issue #92 / post-merge |
| 16 | `run_tests_coverage.sh` uses pre-`src/`-layout paths and cannot run | next root-scripts PR / PR-37 |
| 17 | `CONTRIBUTING.md` documents `pytest` with no holdings env vars or `--mode` | Phase 7 (PR-33/PR-34) |
| 18 | `tests/pds{3,4}file/helper.py` resolve holdings at import time, not from the session config | the `tests/pds{3,4}file/` restructure PR |

The reviewer also flagged the stale `plans/2026-07-17-modernization-plan.md`
reference at `.cursor/rules/pdsfile_overrides.mdc:12`. That file is already being
edited by this PR and the fix is a one-word path change, so it was fixed here
rather than deferred: it now points at the active v2 plan.

## Confirmed satisfied by the reviewer

Workflow YAML parses and the diff to `run-tests.yml` is additions only (the
self-hosted matrix, its triggers and the codecov step byte-identical);
`run-tests-and-opus.yml` untouched; the exact CI command passes with no holdings;
the freeze marker works in both invocations, including `--strict-markers` under
`--confcutdir=tests/api`; the no-holdings before/after independently reproduced
as exactly one added passing test; freeze artifacts untouched; ruff ratchet not
widened; `--mode` hardening behavior-preserving with every call site surveyed;
full-data evidence present, non-stale (nothing under `src/pdsfile/`) and matching
the PR-13 baseline; no absolute holdings path anywhere; commit hygiene clean.
