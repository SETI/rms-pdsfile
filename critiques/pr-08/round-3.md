# PR-08 adversarial review — round 3 (convergence)

Fresh, no-context Opus reviewer subagent (§6.6), on the round-2-updated diff
`origin/rewrite...pr-08-extract-rule-tests`. No knowledge of prior rounds.

## Reviewer verdict: **goal met** — zero Major, zero Minor. Loop converged.

The reviewer wrote an AST comparator over all 16 extracted modules (every
`test_*` body AST-identical to `origin/rewrite`, none dropped/added), ran the
clean-install gate (PASS), confirmed `tests/` collects 713, ran ns (679 passed /
34 skipped) and the pds3-only s-mode CI subset (555 passed / 3 skipped) —
matching the claims — regenerated the manifest diff (194 diffs, all removed, 0
added/changed/unmatched; every removed name is §6.1's enumeration + the
owner-approved `pytestmark`; no production name forgiven), confirmed api-freeze
hermetic, verified no ratchet entry grew (rule-module entries shrank to strict
subsets), confirmed `VG_28xx.py` stays fully CRLF, and confirmed the fring skip
marker moved to the test file with its tests still skipping.

## Major — none. ## Minor — none.

## Deferred (non-blocking, out of scope — both pre-existing, verified on origin)
- **Full `pytest tests --mode s` has 5 failures in
  `tests/pds4file/test_pds4file_blackbox.py`** (uranus_occ, a
  `KeyError`→`UnboundLocalError` around `pdsfile.py:4254/4265`). The reviewer
  reproduced them **identically on `origin/rewrite`** in a worktree — they are
  pre-existing and unrelated to this PR, and are **not** exercised by the CI
  s-mode invocation, which is pds3-only (`tests/pds3file tests/rules/pds3 --mode
  s`, per `scripts/automated_tests/pdsfile_main_test.sh`). This sits in the
  full-holdings golden/shelf-reproducibility area the owner explicitly deferred
  from this split PR. Recorded in `critiques/deferred-observations.md`.
- The allowlist has no PR-07 "category #1" (subpackage-removal) predicate, but
  `origin/rewrite` has none either and §6.1 documents PR-07 as
  manifest-invisible (belt-and-braces only); not a PR-08 obligation.

## Convergence
Round 1: 2 Minor (F401 ratchet grow on 3 pds4 modules → re-export alias;
VG_28xx CRLF flip → restored) — fixed. Round 2: 2 Minor (allowlist broader than
§6.1 + un-pre-approved `pytestmark` → faithful two-clause category #2 +
owner-approved `pytestmark` extension; sub-plan COISS `os` prose → corrected) —
fixed. Round 3: **zero Major, zero Minor, goal met.** Per §6.6 the loop
terminates; the PR may be opened.
