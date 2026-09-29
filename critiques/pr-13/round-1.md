# PR-13 — adversarial review round 1

- Base: `origin/rewrite` @ `8d5cf16b8e16b60bfbcf2615d8a9ae54faec703d`
- Head reviewed: `c791111beae5c657006f387c86bbc1723842a11b`
- Diff handed to the reviewer: `git diff origin/rewrite...HEAD` (three-dot, merge-base)
- Reviewer: fresh no-context subagent, no implementation context, no prior rounds.

## Verdict

**goal met** — zero Major findings, 12 Minor.

## Independent evidence the reviewer generated

The reviewer did not take the PR's own record on trust. It re-ran and confirmed:

- 38 files changed, **no file under `src/`**; none of the four prohibited files
  (`api_manifest.json`, `manifest_allowlist.json`, `dump_public_api.py`,
  `test_api_freeze.py`) appears in the diff; all 12 goldens are new files.
- `ruff check` clean; the `per-file-ignores` ratchet block is absent from the
  diff entirely (neither widened nor touched); no `noqa` in any new file.
- API-freeze test passes.
- Tool tests: 101 passed against the goldens' reference root, 101 passed against
  the complete set, no skips against either.
- Pre-existing suite: `--mode ns` 679 passed / 34 skipped, `--mode s` 555 passed
  / 3 skipped — identical to the PR-09 baseline.
- No-holdings run: 22 passed / 792 skipped, collection clean.
- Re-hashed all declared source files against the complete set: zero mismatches,
  confirming the "byte-identical in both roots" premise the design rests on.
- Built a synthetic root with one declared file deleted: the affected modules
  **skipped** (44 skipped) rather than failing or silently passing.
- Ran the infoshelf modules with `TZ=Asia/Tokyo` in the outer environment: still
  green, confirming the `TZ=UTC` pin makes the sidecar goldens portable.
- Checked every pinned defect against the tool sources: all real, all at or
  within one line of the cited location, and each pin would fail when fixed.
- Confidentiality grep over every added/changed file: no holdings path leaks.

## Major findings

None. The reviewer could not prove the PR misses its goal.

## Minor findings and resolutions

All twelve were **accepted and fixed**; none was rebutted.

| # | Finding | Resolution |
|---|---|---|
| 3.1 | The committed sub-plan contradicts the delivered code: it names the superseded PDS4 subject, claims `PDS_LOG_ROOT` is *set* (it is removed), describes the archive tuple as `(name, size, isdir)`, and leaves every verification checkbox unticked. | Fixed. Sub-plan §1/§2.2/§5 updated to the delivered subject and behaviour; §8 ticked; a deviation register added (see 3.11). |
| 3.2 | Two `--update` assertions are hollow: `assert str(len(NEW_FILE_BYTES)) in text` looks for `"33"`/`"34"`, which already occur inside md5 digests in the pre-update sidecar, so they cannot fail. | Fixed. Both now locate the new file's own sidecar line and assert its byte-count field equals `len(NEW_FILE_BYTES)`. |
| 3.3 | Every task-cycle module is order-dependent: a single test cannot be rerun in isolation, and `-n auto` would break them. `python_testing.mdc` §2 ("independent and order-agnostic") is in force this phase. | Fixed. `ToolTree.reset()` rebuilds the tree from the local source stage, and every cycle module resets before each test, so each test is self-contained. Verified by running single test ids in isolation and by a `-n 4` xdist run. |
| 3.4 | Source line numbers and forward PR-number narration in test docstrings, against `python_testing.mdc` §10 ("never include line numbers, verbose rationale, or change history"). One citation was already stale. | Fixed. Docstrings reduced to a one-line statement of the pinned behaviour plus a pointer to the numbered entry in `critiques/deferred-observations.md`, which carries the rationale, the source locations and the owning PR. |
| 3.5 | `test_non_metadata_argument_is_rejected` (pds3) passes a path that *is* under `metadata/`, so the "outside metadata" branch is never exercised. | Fixed. Renamed to match what it tests, and a real outside-`metadata/` case added, matching the pds4 twin. |
| 3.6 | `TOOLS_WITHOUT_EXIT_STATUS` is referenced only from prose — dead code that enforces nothing. | Fixed. `support.expected_error_exit_code(tool)` now derives the expected code from it, and both checksum modules assert through it. |
| 3.7 | `show_opus_products_table.txt` pins `tabulate`'s grid rendering; `tabulate` has no version bound, so an unrelated release breaks the test. | Fixed. The table test now asserts structure (headers, each opus type, its products) and the byte-exact golden is kept for `--pprint` only. |
| 3.8 | `crlf.test_crlf` raises `ZeroDivisionError` on a zero-byte file; unpinned, so PR-28 could change it silently. | Fixed. Pinned with `pytest.raises(ZeroDivisionError)`. |
| 3.9 | `test_task_flags.py` docstring claims the chosen tasks are read-only and leave the tree alone; three cases resolve to `update`, which creates the tar. | Fixed. The claim is gone and the module resets the tree before each test. |
| 3.10 | A duplicated (strictly weaker) assertion in the pds3 linkshelf test; the pds4 infoshelf `--update` docstring describes stale-aggregate behaviour it never asserts. | Fixed. Duplicate removed; the pds4 module now asserts the stale-aggregate `--validate` result as its pds3 twin does. |
| 3.11 | `tests/conftest.py`'s collect-and-skip loop is PR-09 machinery, which §5 says no PR should touch; §6.4 asks for a `plans/` addendum for deviations. | Fixed. The sub-plan now carries an explicit deviation register recording the change, why PR-13's own spec requires it, and what was *not* touched. Called out in the PR description for owner sign-off. |
| 3.12 | Record inaccuracies: goldens reported as 52 KB (block usage; actual content ~12.5 KB) and the `show_opus_products` goldens described as containing `$DISK` (they do not — the tool prints logical paths). | Fixed in `critiques/pr-13/validation.md`. |

## Deferred (appended to `critiques/deferred-observations.md`)

- **Subprocess execution yields no measured coverage for the tools.** The suite
  driver runs `coverage run -m pytest`, but each tool runs in a child process
  with no `COVERAGE_PROCESS_START`. Subprocess invocation is load-bearing here
  (`PdsFile.CACHE` is class-level and the session preloads real holdings), so
  this cannot be fixed in PR-13 without giving up correctness. → PR-14.
- **`tests/api/test_api_freeze.py` is not marked `holdings_free`**, so PR-14's
  hosted no-holdings job would skip it although PR-14's spec names it as a test
  that must run there. PR-13 only owed the crlf tests. → PR-14.
