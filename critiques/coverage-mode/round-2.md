# Coverage mode, round 2 — full diff

Reviewer: a fresh, no-context subagent given the same brief as round 1, plus
`critiques/coverage-mode/round-1.md` with instructions to check whether its fixes were
real fixes or only reworded claims, and a weighting toward what a first reviewer would be
least likely to reach: the shell code under failure and unusual flag combinations,
`set -euo pipefail` interactions, the `TOTAL` parsing across both report shapes, the
register entry as prose, and behavior on the Python versions CI uses. Diff:
`git diff 02dd774..3c4bb61`. It made no edits.

The reviewer re-derived, deliberately choosing different numbers from round 1: 9,715 total
statements and 4,310 tool-tree statements, both exact with `exclude_lines` applied;
1,277 collected = 1,243 + 34; `tests/core` = 73 ids; PyMarkdown's 2-file selection; the
register at 8/0/15/131/50 = 204; eleven console scripts; and every ratio in the record.
It ran the 13-id module end to end (13 passed, 20 data files, 20 distinct pids), drove the
real `_coverage_report` over the result, and confirmed `pdsarchives.py` at 82% from that
module alone. It established two things the executor had not: that a `-S` child which does
*not* import `sitecustomize` writes **no** data file (the negative control the `-S` tests
lack), and that the parent does not double-write, so `tool_files = data_files - 1` is
right. It also confirmed the new tests pass with no holdings at all — the hosted-CI
posture the `holdings_free` marker promises.

Verdict: **goal not met** — four Major, fifteen Minor, five Deferred.

## Major findings, and their resolutions

**M1. The headline number misdescribed itself under branch coverage.** The verdict line
took `Stmts` and `Cover` from the same `TOTAL` row and printed `56% of 9715 statements`,
but coverage's branch `Cover` is executed statements *and* taken branches over statements
plus branches — a different denominator. The PR's own evidence carried the refutation: the
same execution is 56% branch and **60%** line-only, so the line understated the statement
figure by four points while appearing to state it. **Fixed:** the wording now follows the
`has_arcs()` read-back that was already there — branch prints
`56% of 9715 statements and 3542 branches together`, line-only keeps
`81% of 9715 statements`, and the comment says why the two shapes cannot share a sentence.

**M2. The stated reason for not exporting the coverage variables was false, and the
record's check on it was vacuous.** The comment claimed an exported
`COVERAGE_PROCESS_START` would reach Sphinx "only in sequential mode"; a backgrounded
subshell inherits the exported environment exactly as a sequential one does, so it would
reach Sphinx in both. The record then offered the parallel and sequential totals agreeing
as the check — a check that cannot fail either way. The decision was right and the code
was always safe; the reasoning and the evidence were not. **Fixed** with a measurement
that can fail: the docs gate run *alone* with the subprocess-mode variables in its
environment writes **three data files, 77 pdsfile modules, 6,851 lines**, none of it
executed by a test. That is what an export would have added, in either mode. The comment,
the record's finding 2 and the parallel-run paragraph all now say this, and the
parallel/sequential agreement is explicitly demoted to what it is.

**M3. The §6.6 section of the validation record was still a placeholder.** Round 1's m12
swapped `ADVERSARIAL_LOOP` for `ROUNDS_SUMMARY` and reported it fixed, which it was not.
**Fixed:** the section is written, and it names each round's file.

**M4. The record quoted an output line the program cannot produce**
(`Coverage report passed: … line-only, 319 subprocesses`), left behind when round 1
renamed both the verdict and the noun. **Fixed**, and the surrounding paragraph now also
carries M1's distinction.

## Minor findings, and their resolutions

**m5.** `support.py`'s docstring — the function that *supplies* the variables — still
credited `sitecustomize` alone. **Fixed:** it names both readers.

**m6.** Entry 4214 did the same. **Fixed:** the entry now says the `.pth` acts first from
7.10 and what the hook is therefore for. This matters because PR-37 is the entry's reader.

**m7. No test covered the branch every real tool subprocess takes.** Both subprocess tests
pass `-S`, which skips the `.pth`, so `process_startup()` always returned a live object
and the `Coverage.current()` fallback was never exercised — tightening that line to reject
`None` would have killed every tool subprocess under `--coverage-subprocess` with all nine
tests still green. **Fixed:** `test_the_hook_measures_a_child_that_processes_site` runs a
child *without* `-S` and asserts exit 0 and a data file.

**m8.** The "coverage first" comment in `sitecustomize.py` described a situation that
cannot arise — the only later import is outside `source` and inside `omit`. **Fixed:** the
comment is gone; the ordering claim that remains is the true one, that coverage must start
before the tool module is imported.

**m9.** The header said `COVERAGE_CORE` was the one setting the script names outright;
`COVERAGE_FILE` is another. **Fixed:** both are named, with what each is for.

**m10.** The overrides deviation claimed `coverage run` is "what lets a subprocess be
measured through `COVERAGE_PROCESS_START`", which is false — coverage reads that variable
whatever started the parent. **Fixed:** the true reasons (the data gate already uses it;
`-a`, `combine` and `erase` are that CLI's verbs), with the independence stated.

**m11. "sys.monitoring cannot measure branches on Python 3.12" was wrong in five files.**
Coverage 7.13.3 gates it at `PYVERSION > (3, 14, 0, 'alpha', 5, 0)` (`coverage/env.py`),
so it holds below 3.14 — including CI's 3.13 leg, where a reader would have concluded the
constraint had lapsed. **Fixed** in all five, and entry 4214 now cites the gate.

**m12.** "this tree measures 34%" in the *test* package's header reads as the test package,
which coverage never measures. **Fixed:** the measured trees are named.

**m13.** `coverage html` ran before the verdict was printed, so an unwritable `htmlcov/`
would have cost the run its number as well as its HTML. **Fixed:** the verdict is printed
first.

**m14.** Writing `htmlcov/` was an undocumented side effect. **Fixed** in the option line
and in the dev guide.

**m15.** With `set -o pipefail`, a `tee` that could not write would have made a successful
`coverage report` look like a failed one. **Fixed:** the report is captured into a variable
and printed, with no temp file and no pipeline.

**m16.** A stray line break left an orphan line in `--help`. **Fixed** and re-read.

**m17.** The record said both data-gate differences were written in both places; one of
them is only in the data gate's own comment. **Fixed.**

**m18. A developer who exports `COVERAGE_PROCESS_START` without `PDSFILE_COVERAGE_PARALLEL`
gets a silently small total**, because every child then overwrites the one shared data
file. The hook named the hazard and checked nothing. **Fixed:** the hook now reads
`parallel` back off the config it was given and exits 70 if it is false, and
`test_the_hook_refuses_to_start_without_per_process_data_files` pins it.

**m19.** The whole-suite timing table gave single runs to 0.01s, and its control row is
*below* the uninstrumented row. **Fixed:** the table now says where its noise floor is.

## Deferred

The reviewer's five were the same five round 1 raised, plus one: the data gate never runs
`coverage erase`. All are left alone as PR-37's or as dependency changes. It also
re-confirmed round 1's finding that an interrupted run leaves suffixed data files with no
contamination path.
