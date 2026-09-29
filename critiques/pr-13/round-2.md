# PR-13 — adversarial review round 2

- Base: `origin/rewrite` @ `8d5cf16b8e16b60bfbcf2615d8a9ae54faec703d`
- Head reviewed: `0dc8fb6a45060c549002ac8679be214ecad68b91`
- Diff handed to the reviewer: `git diff origin/rewrite...HEAD` (three-dot, merge-base)
- Reviewer: a **new** fresh no-context subagent — no implementation context, no
  knowledge of round 1 or its findings.

## Verdict

**goal met** — zero Major findings, 10 Minor, none of them a re-raise of anything
round 1 raised.

## Independent evidence the reviewer generated

This reviewer went further than round 1 and **mutation-tested the pins**, which is
the strongest available answer to "are these tests hollow?":

- Overlaying a patched `pdsinfoshelf.py` that fixes `checksum1 != checksum1` and
  `abs(modtime1 != modtime2) > 1` makes **both** `test_known_undetected_corruption`
  cases fail; fixing the `(count1, count1)` message makes
  `test_update_picks_up_a_new_file` fail; changing a shelved child count makes the
  sidecar golden test fail. The pins and goldens are live, not decorative.
- Re-ran the ns gate exactly as the suite driver now invokes it: 783 passed / 34
  skipped, i.e. 679 pre-existing + 104 new, baseline set untouched.
- 104 passed / 0 skipped against **both** holdings roots; re-hashed all 20
  declared fingerprints against the complete set — every one matches.
- Built a synthetic root with one declared file omitted: the affected modules
  skipped with the expected reason; no failure, no silent pass.
- `TZ=Asia/Tokyo` in the outer environment: still green (the `TZ=UTC` subprocess
  pin holds). `pytest -n 4`: green. Individually selected test ids: green.
- No `src/` file touched; no prohibited file touched; ratchet block absent from
  the diff; `ruff check` clean; API-freeze green; 11 goldens totalling 11,381
  bytes.
- Confirmed every pinned defect in the tool sources, and confirmed
  `support.TOOLS_WITHOUT_EXIT_STATUS` is accurate for both checksum tools.

## Major findings

None.

## Minor findings and resolutions

All ten were **accepted and fixed**; none was rebutted.

| # | Finding | Resolution |
|---|---|---|
| 2.1 | Four docstrings cite "entry 1" of the deferred observations, which is about a different tool, and the three `pdsinfoshelf` comparison defects they pin — plus the `crlf` empty-file pin — are documented in **no** entry at all. A maintainer whose fix breaks the pin would find the wrong record. | Fixed. Added entries **10** (the three `pdsinfoshelf` validate defects, owner PR-26 — noting that the `(count1, count1)` message defect is *not* on PR-26's list in the plan and should be folded in) and **11** (`crlf` `ZeroDivisionError` on a zero-byte file, owner PR-28), and repointed all four docstrings. |
| 2.2 | `pytest.raises` used without `match=`, against `python_testing.mdc` §7, which is in force this phase. `crlf.test_crlf` raises a bare `ValueError` for two different reasons. | Fixed. `match='invalid task'`, `match='invalid threshold'`, `match='division by zero'`. |
| 2.3 | `assert crlf.test_crlf(..., threshold=0.5) != 'BINARY'` asserts a negation; it would pass on any wrong-but-different result. | Fixed: `== 'OK'`. |
| 2.4 | The failing `--validate` in both checksum modules asserted log content but never the exit code, so the one call site that best represents the "exits 0 despite errors" defect had no pin. | Fixed. `assert run.returncode == ERROR_EXIT` added after every failing `--validate` in both modules. |
| 2.5 | `subsets.PDS4_SOURCES` is defined and never used. | Fixed: deleted. Its PDS3 counterpart is used and stays. |
| 2.6 | `support.md5_file_text` duplicates `md5_file_mapping`'s parser line for line. | Fixed: it now delegates. |
| 2.7 | `pdsindexshelf` had no `--update`-against-an-existing-shelf case, so the merge path the spec's cycle asks for was untested for that pair alone. | Fixed. A new test shelves the index table, runs `--update` over the metadata directory, and asserts the sibling table is shelved while the existing sidecar is byte-identical. |
| 2.8 | The sub-plan's deviation register quoted 792 skipped / 22 passed; the delivered head gives 794 / 23, which the validation record already had right. | Fixed. |
| 2.9 | The deviation was recorded as a sub-plan section, but `plans/README.md` and §6.4 require a **dated addendum file** in `plans/`. | Fixed. Added `plans/2026-07-25-addendum-holdings-free-marker.md`, referenced from the sub-plan, from `plans/README.md`, and from the PR description. |
| 2.10 | The register said "one deviation"; adding the tool tests to only one of the two suite invocations is a second one. | Fixed. Both are now listed, in the sub-plan and in the addendum. |

## Deferred (already recorded, or added to `critiques/deferred-observations.md`)

- No coverage measured for the tools (entry 8) → PR-14.
- `tests/api/test_api_freeze.py` not marked `holdings_free` (entry 9) → PR-14.
- Nothing pins `--archives`, `--infoshelf`, `--log` or `--quiet`; PR-13 was asked
  only for the two-flag task-resolution case, which it delivers → PR-25.
- `pds4archives` has no `--validate`-clean / `--repair` / `--update` coverage and
  `pds4indexshelf` has no task cycle, both blocked on the tools being broken
  (entries 1–3). When those are fixed the pins must be replaced by the same cycle
  the pds3 twins run → PR-25 / PR-27.
- Info-shelf sidecars are local-time dependent (entry 7) → Phase 6.
- `tests/holdings_maintenance/__init__.py` reproduces the repo's pre-existing
  double-package situation (`tests/` has no `__init__.py`). It matches the
  convention every other test package already uses, and is the same item already
  deferred from PR-07 → whichever PR adds `testpaths`.
