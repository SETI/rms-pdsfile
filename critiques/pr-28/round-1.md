# PR-28 adversarial review — round 1

Fresh reviewer, no development context, given the plan's PR-28 entry and Phase 6
preamble, the ground rules, the exact diff `3d044b2..HEAD`, and read access to both
worktrees, the holdings and the interpreter. Verdict: **goal not met**.

The reviewer re-ran every gate independently and confirmed each: ruff clean on all
three invocations, the ratchet only shrinks with no new key and no widened entry,
the four frozen files md5-identical to `3d044b2`, `[project.scripts]` eleven at both
ends, `tests/api` 26 passed, the holdings-free suite at the record's figure, no
skips or xfails added, and the record gate green. It re-derived the driver
measurement with its own true-LCS implementation and got every figure exactly. It
also independently confirmed the bug fix's negative control both ways: reverting
`errors` to `error` fails only the regression test, and so does a `try/except`
"fix" that stops the crash without counting.

Three Majors, six Minors, three Deferred.

## Major

| # | Finding | Disposition |
|---|---|---|
| M1 | A plan deliverable was dropped — the PR-28 entry required **both** `main()`-less tools' tests to move in-process, and only `shelf_consistency_check`'s did — and the plan's own text was edited to match, with no §6.4 addendum. The engineering reason is sound; the mechanism is the defect, since editing the requirement out makes the deviation invisible. §7 of the record listed five owner decisions and this was not one | **Fixed.** `plans/2026-08-07-pr-28-deviation-addendum.md` written, with the measurement, the alternative (an autouse fixture restoring `LOCAL_PRELOADED` / `SHELVES_ONLY` and the caches) and its cost. Both edited plan passages now name the departure and point at the addendum instead of reading as though nothing was dropped; the record's §4 and §7 do the same, and §7 lists it first |
| M2 | An entire class of CLI behavior change was unenumerated, and one direction of it was a regression. `crlf --rep f` crashed at base and **rewrites the file** at head, because argparse abbreviates by default; `crlf -dash.txt` worked at base and exits 2 now; a repeated flag, and `--`, also change. The record claimed "every mode" and "five kinds, all enumerated" | **Fixed and enumerated.** `allow_abbrev=False` on both new parsers, which makes the abbreviation cases the usage error the record already enumerates, with a test on each; `show_opus_products` deliberately not changed, since its parser predates the PR. The transcript grew ten scenarios covering the whole class and was re-run at base and head: **75 records, 17 differing, control 0 of 75**, and §3 gained a sixth kind with a record-by-record table. The `-dash.txt` loss is deferred entry 141, and §7 item 4 |
| M3 | Mutation probe M4 was vacuous for `shelf_consistency_check`: mutating only that file left the suite green, because the two-file probe was caught by the crlf test. The test meant to pin it, `test_verbose_is_accepted_after_the_shelf_roots`, put the flag *after* the last positional, which plain `parse_args` accepts identically | **Fixed.** The test is `test_verbose_is_accepted_between_the_shelf_roots` and puts the flag between two roots, which is exactly what `parse_args` rejects. Every mutation is now applied **one file at a time**: fourteen probes, each with its own row and its own failure list in §5.3 |

## Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | "Nothing at the tail is contiguous … the three share only `status = 1`" is false: besides the 15-line preamble there are two 5-line runs and a 3-line run identical in all three | **Fixed**, and re-measured with a stated method: the 39 shared lines fall into blocks of **15, 5, 5, 3, 2, 2, 2** and five isolated lines. The conclusion is unchanged and the text now says *why* the six small blocks are identical — they are the log scope's open and close, wrapped around bodies that differ. The gate computes the block structure rather than only the leading run |
| m2 | §4's "10 of 11 tests" is wrong | **Fixed**, and made re-derivable: §4 now carries a per-module breakdown counted off the AST — 13 / 31 / 9 tests, split by which runner each uses — and the gate checks both the table and the prose against the tree |
| m3 | The gate's `[project.scripts]` check used the head count for both cells, so "eleven at the base" could never fail | **Fixed.** The base column of that row, and of the whole line-count table, now comes from `git show 3d044b2:…` |
| m4 | Nothing pinned the *process* exit code of an uncaught exception any more; the in-process runner only catches `SystemExit` | **Fixed.** `test_an_unreadable_file_ends_the_process_with_a_traceback` is a subprocess and asserts exit 1, the traceback on stderr, and empty stdout |
| m5 | §7 omits M1's deviation — the item most likely to be ruled differently is the one not offered | **Fixed**; it is §7 item 1 |
| m6 | `crlf`'s header `Use:` block was rewritten without being enumerated, where the equivalent `shelf_consistency_check` correction was | **Fixed.** §7 item 8 covers both, and says why both had to move: the package went under `src/pdsfile/` in PR-06, so neither header's invocation had been a runnable command since |

## Deferred

| # | Finding | Disposition |
|---|---|---|
| d1 | `--narrow-table` has no test at all; mutating its branch leaves the suite green | **Recorded** as deferred entry 142, with the further observation that its `if opus_type not in rows` guard compares a string against a list of one-element lists and so is always true. One of PR-13's gaps, not a PR-28 regression |
| d2 | `show_opus_products`' `__main__` block was covered only by `full_holdings` tests, so a no-holdings runner could not notice its absence | **Fixed rather than deferred** — it is the entry point this PR adds. `test_the_module_is_runnable_as_python_m` runs `python -m … --help` with neither root set; mutation M2c now fails six tests including that one |
| d3 | Variation point 5 of the driver measurement — the task header's quoting — is arguably spurious, because the owner's 2026-08-05 output-text ruling says text may move rather than become a flag, and PR-25 has already moved a log line on that basis | **Accepted; the argument was overstated.** Entry 130 now says this is the one variation point a merger could dissolve, at the price of a log-text change on four tools, and that the case rests on the other seven. The conclusion — do not merge — is unchanged, and the line arithmetic was restated for seven hooks rather than eight |
