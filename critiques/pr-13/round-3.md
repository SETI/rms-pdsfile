# PR-13 — adversarial review round 3

- Base: `origin/rewrite` @ `8d5cf16b8e16b60bfbcf2615d8a9ae54faec703d`
- Head reviewed: `121b5360f4a7ec0f50a5b026d93784df8c13320b`
- Diff handed to the reviewer: `git diff origin/rewrite...HEAD` (three-dot, merge-base)
- Reviewer: a **third** fresh no-context subagent. It was told only that two
  earlier reviewers had returned `goal met`, deliberately not what they found.

## Verdict

**goal met** — zero Major findings, 5 Minor, none a re-raise from round 1 or 2.
Four of the five are record/documentation consistency; one is a test-helper
routing slip.

## Independent evidence the reviewer generated

- Diff modifies exactly five pre-existing files (`critiques/deferred-observations.md`,
  `plans/README.md`, `pyproject.toml`, `scripts/automated_tests/pdsfile_main_test.sh`,
  `tests/conftest.py`); everything else is new. **No `src/` file**, no prohibited
  file, ratchet block absent from the diff. `ruff check` clean.
- 105 passed / 0 skipped against the goldens' reference root; 105 passed / 0
  skipped against the complete set under `-n 4`.
- Re-hashed all 20 declared fingerprints against the complete set: 20/20 match.
- Synthetic root with one declared file omitted: the affected module skipped all
  7 items with the expected reason, while a module not declaring that file still
  ran green — the skip is per-module and per-declaration, as specified.
- **Mutation-tested again, and further than round 2**: fixing each of the three
  `pdsinfoshelf` comparison defects fails exactly the pinning test; and renaming
  a *log string* (`'Checksum mismatch'` → `'Checksum differs'`) in `pdschecksums`
  fails both corruption tests. So the suite catches log-format regressions, not
  only behavioural ones — which is the thing PR-25/26/27 are forbidden to change.
- Confirmed sidecar and archive comparisons are deterministic and
  machine-independent; re-ran the infoshelf goldens under `TZ=Asia/Tokyo`: green.
- Verified the baseline-diff claim structurally: no pre-existing test file is
  modified, and `tests/conftest.py`'s change is confined to the no-holdings
  branch, so pre-existing outcomes cannot move. Arithmetic checks out
  (818 = 713 + 105, 784 = 679 + 105).
- Confidentiality: no holdings path in any file this PR adds or changes.

## Major findings

None.

## Minor findings and resolutions

All five were **accepted and fixed**; none was rebutted.

| # | Finding | Resolution |
|---|---|---|
| 3.1 | The "From PR-13" lead-in in `critiques/deferred-observations.md` still said "Five pre-existing defects" (there are now seven, 10 and 11 having been added during review) and still claimed each pin "names, in its docstring, the source line" — which round 1 deliberately removed. | Fixed: seven, with the split between "while writing the tests" and "during review" stated, and the docstrings described as pointing at the numbered entry. |
| 3.2 | The no-holdings figure "794 skipped / 23 passed" was stale in three files; the delivered head gives **795 / 23** (the 105th test was added during round 2). | Fixed in the validation record, the sub-plan and the addendum. |
| 3.3 | `support.sidecar_text`'s docstring justified portability with "the tools already write sidecar entries sorted by path", which is false for the link shelves (list-valued entries precede str-valued ones) and for index shelves (table-row order). The order is still deterministic, so the goldens were never at risk — only the stated reason was wrong. | Fixed: "deterministic, machine-independent order (sorted keys, or table-row order for index shelves)". |
| 3.4 | The deviation register the owner is asked to sign listed two deviations; two more letter-level ones existed, documented only in the sub-plan: the source tables living in `subsets.py` rather than copied per module, and `python -m <module>` rather than `python <path>.py`. | Fixed: the addendum now carries all four, each with its rationale and an "if rejected" one-liner, and the sub-plan summary matches. |
| 3.5 | `test_update_creates_a_missing_archive` read the golden file directly instead of going through `support.check_golden`, so it ignored `--update` and would raise a bare `FileNotFoundError` rather than the helper's regenerate-the-goldens message. | Fixed: routed through the helper. |

## Deferred (already recorded)

- The addendum is "awaiting owner acknowledgement"; §6.4 requires that sign-off
  before merge. Correctly surfaced, not a code defect.
- No coverage measured for the tools (entry 8) and `test_api_freeze.py` not marked
  `holdings_free` (entry 9) → PR-14.
- `pds4archives` / `pds4indexshelf` have no full task cycle and
  `pds4linkshelf --update` is pinned broken, all blocked on entries 1–4 →
  PR-25 / PR-27.
- CI cost: the not-shelves-only invocation gains 105 subprocess-heavy tests. Worth
  watching when PR-14 tunes the jobs.
