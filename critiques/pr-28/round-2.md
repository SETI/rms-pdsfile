# PR-28 adversarial review — round 2

Fresh reviewer, no development context and no knowledge of round 1. Verdict:
**goal not met**.

Independently re-run and confirmed: all three ruff invocations clean; the ratchet
shrinks only, with no new key and no widened entry; base and head finding counts
2,250 / 2,249, the base one measured by the reviewer itself; `PT028` fires exactly
twice on `crlf.py` and `shelf_consistency_check.py` is clean with the ratchet
emptied; the four frozen files byte-identical; `[project.scripts]` the same eleven
console scripts with none of the three tools added; `tests/api` 26 passed; the
holdings-free suite at the record's figures; no skip or xfail anywhere in the diff.
The bug fix's negative control was confirmed both ways — reverting `errors`, and a
`try/except NameError: pass` "fix" — and ten further mutations of the reviewer's own
were all caught with failure sets matching §5.3 row for row. Deferred 130 was
re-derived with an independent dynamic-programming LCS: every figure exact,
including the greedy block partition, and the eight variation points confirmed real.
`run_tool_in_process` was audited for fidelity and found faithful for these two
tools. The record was confirmed not stale.

Two Majors, seven Minors, three Deferred.

## Major

| # | Finding | Disposition |
|---|---|---|
| M1 | `show_opus_products` moved an exit code too, 1 → 2, for any malformed command line when a holdings root is unset — because `parse_args` now runs before the `os.environ` reads that used to kill the module at import. No document said so; deferred 135 said "both migrated tools" and §3's "what did not change" table told the reader that tool's parser was untouched | **Fixed.** Three transcript records added (`opus/usage-error-without-holdings-env`, `opus/no-arguments-without-holdings-env`, and the existing `--help` one), §3 change 5 restated as "reaches its parser before it reads the environment" with a base-vs-head table, and the scope named: with both roots set, that tool's usage errors are byte-identical, which four records now show. Entry 135 names all three tools and explains why the third is easy to miss; §7 item 2 does the same |
| M2 | Phase 6 was declared complete while deferred entry 66's third item — `pdsdependency.py`, 1,165 lines, over an unwaived limit — was explicitly routed "from PR-28" and unanswered, with `pdsfile_overrides.mdc` still saying Phase 6 would change its size | **Fixed.** The Phase 6 closure now carries a third paragraph: the deferral has expired rather than been discharged, because the consolidation can never reach a tool with no twin, so it is a live waiver-or-split question that no phase owns. Entry 66 says the same and its owner line is now **open**; `pdsfile_overrides.mdc` deviation (3) names the file and its size instead of pointing at a phase that has ended |

## Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | `--flag=value` is a fifth argument shape, unenumerated and untested: `shelf_consistency_check --verbose=1 .` ran the whole walk at base and is exit 2 now | **Fixed.** Two transcript records, and a test on each parser (`test_a_store_true_flag_rejects_an_explicit_value`, parametrized over both crlf flags, and `test_a_flag_given_a_value_is_a_usage_error`). §3 change 2 now covers all three rejection shapes in one table |
| m2 | `crlf --repair --repair f` **rewrites** a file base left untouched; only the `--verbose` twin was enumerated | **Fixed.** `crlf/repeated-repair` is its own transcript record and its own row in change 6, which now leads with the write side-effect |
| m3 | `-h` is a new flag on both tools; only `--help` was enumerated and tested | **Fixed.** Two transcript records, and both help tests parametrized over `('--help', '-h')` |
| m4 | Deferred entry 130 still read as unanswered, carrying its superseded figures, with the amendment 2,300 lines away | **Fixed.** Entry 130 now says it is answered at the end of the file and that its own figures are superseded |
| m5 | The gate hardcodes the base finding count and the base id counts while §9 advertises it as re-deriving "at base and head"; and it counts `[project.scripts]` without checking the thing §8.4 asks for | **Both fixed.** The gate now asserts that no console-script entry names any of the three tools and that the script *set* matches the base's, and §9 says plainly which two numbers are recorded constants and why neither can be read out of the head tree |
| m6 | `test_show_opus_products.run_without_holdings` duplicated the support helper with a divergent env-scrub list (missing `PDS_LOG_ROOT`) | **Fixed.** One `support.no_holdings_env()` builds the environment for both, and the local helper's docstring says why it exists at all — the support runner asserts `HOLDINGS_FREE_TOOLS`, which this tool deliberately is not |
| m7 | "Complete." asserted for a phase whose last PR is open and cannot merge until the owner rules on its deviation | **Fixed**: "Complete on PR-28's merge", with the outstanding acknowledgement named |

## Deferred

| # | Finding | Disposition |
|---|---|---|
| d1 | `show_opus_products` never resolves a PDS4 path in any test; commenting out `Pds4File.preload` leaves the suite green | **Recorded** as deferred entry 143. A PR-13 coverage gap; the PDS4 subset already exists, so what is missing is a fixture staging both flavors under one tree |
| d2 | `run_tool_in_process` captures into `io.StringIO`, which has no encoding, so a `UnicodeEncodeError` a real process would raise cannot happen in-process | **Recorded** as deferred entry 144, **and** written into the runner's docstring beside its other two fidelity caveats, since that is where a reader meets it |
| d3 | `shelf_consistency_check` has `crlf`'s leading-`-` loss and no test | **Fixed rather than deferred**: `test_a_shelf_root_beginning_with_a_dash_is_a_usage_error`, plus transcript record `shelf/dash-root`, where the base run walked the directory. Entry 141 now names both tools |

## What the round cost, in numbers

The transcript grew from 75 records to **84** and the differing set from 17 to
**26** — nine new records, seven of which differ, all in the two argparse classes
this round surfaced. Added ids went from 25 to **32** (29 test functions, three
parametrized over two values). The mutation matrix is unchanged at fourteen probes,
re-run at the new baseline of 61 passed.
