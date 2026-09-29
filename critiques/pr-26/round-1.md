# PR-26 adversarial review — round 1

Two fresh no-context reviewer subagents, plus CodeRabbit on PR #123. Reviewed at
head `edb055a`; fixes landed in `6124837`.

## Coverage given to the reviewers

Reviewer A was pointed at **behavioral correctness of the refactor**: the old
`main()` of each of the four tools against the new shared driver, statement by
statement, plus the log-path method equivalence, `resolve_holdings_paths` and
`expand_selection_targets`. Reviewer B was pointed at **the bug fixes and whether
the tests are real**: each fix's correctness, an attack on `modtimes_agree`, and an
instruction to establish test non-vacuity by *reverting each fix in a scratch copy
and running the test* rather than by reasoning about it.

Both were warned about the measurement trap recorded as deferred observation 110
(`pythonpath = [".", "src"]` in `pyproject.toml` defeats a `PYTHONPATH`-based
differential probe for in-process tests), because a reviewer that fell into it
would have drawn confident wrong conclusions about which tree it was measuring.

## CodeRabbit — 9 findings, all answered on their threads

| # | Finding | Disposition |
|---|---|---|
| 1 | The record says "Three commits" over a list of four, and gives 171 where the attribution rows sum to 170 | **Accepted.** Both were miscounts; the 171 counted a blank line. |
| 2 | `archive_filter()` archives the backup files `load_directory_info()` skips | **Declined**, recorded as deferred 116 |
| 3 | `validate_tuples()` enters its mismatch branch on a `dirpath` difference and reports nothing | **Declined**, recorded as deferred 117 |
| 4 | "refer to the the archive file" in the `--archives` help | **Declined**, recorded as deferred 118 |
| 5 | The chained-run substitution rewrites every argument, not only `argv[0]` | **Declined**, recorded as deferred 119 |
| 6 | The pds4 chain re-runs `pds4checksums`, not `pds4infoshelf` | **Already found**; deferred 109, added before the review |
| 7 | Four test docstrings name the removed `_common.move_old_*` functions | **Accepted.** |
| 8 | The empty-target regression has pds3 coverage only | **Accepted**, in the form that keeps it honest |
| 9 | The tolerance test asserts only the absence of one message | **Accepted**, and it led to the most useful finding of the round |

### Why 2, 3, 4 and 5 were declined rather than fixed

All four are real. All four are **present at this PR's base and at its head
alike**, and none is on the plan's enumerated list of PR-26 behavior changes.

2 and 3 are in the archive family, whose code this PR **moved verbatim** and does
not otherwise touch. Fixing either changes what the archive tools write or report,
and neither has an obvious repair — excluding backup files rewrites existing
archives' contents on the next `--repair`, while including them in the directory
listing changes what the checksums and infoshelf tools record instead.

4 is deliberate and is the one worth stating plainly: reproducing the old help
text *exactly*, typo included, is what allows the claim that all four tools'
`--help` output is byte-identical to base. That claim is the check that replacing
four hand-copied help texts with shared constants did not quietly reword anything
else. Fixing the typo in the same change would have forfeited the check that the
change was safe.

5 is the same source line as 6, so narrowing one while leaving the other is worse
than settling both at once.

### What finding 9 turned into

CodeRabbit asked for a stronger assertion in
`test_pds3_infoshelf.py::test_modification_time_within_one_second_agrees`. Adding
it exposed something the assertion strength was hiding: **on pds3 that test cannot
discriminate at all.** pds3's comparison was dead at base, so *no*
modification-time mismatch was ever reported for any input, and "no mismatch is
reported" therefore holds against base source too. It passed the base probe.

pds4 is the flavor whose truncation worked, so pds4 is where the change is
visible. The test now also exists in `test_pds4_infoshelf.py`, and against base
source it fails with exactly the false positive this PR removes:

```
ERROR | Modification time mismatch "2020-09-13 12:28:31" "2020-09-13 12:28:30"
```

Two times 0.6 s apart, on opposite sides of a whole second. That is the enumerated
pds4 behavior change, now pinned at the tool level rather than only in unit tests.
The pds3 test is kept as a "still agrees" check and is recorded in
`critiques/pr-26-validation.md` as non-discriminating rather than counted as
evidence.

This is the round's lesson: a test that passes at base is not necessarily wrong,
but it is not evidence, and the base probe is what tells the difference. The
space-in-the-path test earlier in this PR failed the same check and had to be
rewritten; this one could not be rewritten and had to be moved to the flavor where
it means something.

## Gates after the round

`ruff check .` clean, `ruff check --preview --select E111,E112,E113 .` clean,
`tests/holdings_maintenance/` + `tests/api/` 304 passed. All seven PR checks green
on Python 3.10, 3.11, 3.12 and 3.13 against real holdings.
