# PR-28 adversarial review — round 4

Fresh reviewer, no development context and no knowledge of rounds 1-3. Verdict:
**goal not met** — three Majors, one of them a real coverage hole, two documentary.

Everything the record claims about the code and the gates reproduced exactly: all
three ruff invocations, the ratchet, the findings counts with the base re-measured,
the four frozen files, the eleven console scripts, both suite modes, the
holdings-free leg, all sixteen §5.3 probes row for row, and deferred 130 re-derived
independently. The reviewer built its own 68-invocation base-vs-head transcript that
snapshots on-disk bytes as well as output — base-vs-base control 0, 31 differing,
**every one inside the six enumerated kinds** — and ran `show_opus_products` against
the real holdings root across nine output modes and four usage errors, all
byte-identical.

## Major

| # | Finding | Disposition |
|---|---|---|
| M1 | **The `argv` parameter of all three new `main()`s was covered by nothing, and the runner this PR wrote is what hid it.** `run_tool_in_process` sets `sys.argv` *and* passes `argv`, so the two paths are indistinguishable: four separate mutations — each of the three tools ignoring its argument, and the runner ceasing to pass one — all left the suite green. That parameter is the "testable" half of the charter, and PR-25a's `re_validate` tests pin exactly these two halves for the same signature | **Fixed.** Six direct calls to `main()` across five tests, with `sys.argv` holding a different command line, for all three tools — two tests apiece for `crlf` and `shelf_consistency_check`, and one for `show_opus_products` that makes both calls: an explicit argv wins, and `main()` with no argument reads `sys.argv`. Four new mutation probes (M12a-c, M13) fail them and passed before |
| M2 | `pyproject.toml` still described the `F821` this PR deleted, in the future tense — "owned by a later PR that gives the script a `main()`" — and listed it among the entries "locked for now rather than for ever". The mdc says the two files must agree; round 3 fixed the mdc's copy of this and missed pyproject's | **Fixed.** The bullet is gone and the "locked for now" list names the two that remain, with the two that have since gone and why |
| M3 | The Phase 6 closure claimed **one** leftover question. Six more deferred entries still routed work at Phase 6 or at one of its PRs, and entry 72 named PR-28 itself as the nearest PR licensed to change behavior — a completed PR as a future owner, the exact defect round 2 raised | **Fixed.** The closure now tabulates **nine** deferred observations by number — the six the round named, plus entries 6 and 11, which round 3 had re-owned as open, and entry 66 — grouped into six rows because four of them are one question. Entry 72 is re-owned as unowned, with the reason PR-28's licence did not reach `pdscache.py` |

## Minor

| # | Finding | Disposition |
|---|---|---|
| m4 | "all 27 `show_opus_products` records … byte-identical" contradicted §3's own changes 3 and 5 | **Fixed**: 27 of its 31, with the four that differ named |
| m5 | The addendum and §7 costed the alternative at "five subprocesses"; the tool has six such tests | **Fixed** in both, phrased as tests rather than a subprocess count. The reviewer also noted the gate never opens the addendum — true, and the addendum carries no derived numbers now that this one is gone |
| m6 | The mdc's `RUF059` row was stale four ways — no such ratchet entry, no such finding in the tree, a cited defect that has since been fixed, and "a defect Phase 6 owns". Its per-code counts have also drifted broadly | **Row removed** (`ruff --select RUF059` with the ratchet emptied reports nothing). The count drift is **recorded** as deferred 148 with four measured examples, rather than half-refreshed from inside another PR's diff |
| m7 | `no_holdings_env()`'s scrub list was asserted by nothing; deleting `PDS3_HOLDINGS_DIR` from it left the suite green | **Fixed**: the no-holdings probe now asserts both variables are absent from its own environment. New probe M15 |
| m8 | CodeRabbit finding 3 was re-anchored but left without a disposition, and its re-anchor orphaned a wrap | **Fixed**: dispositioned like finding 2, naming the test and the deferred entry that hold it |
| m9 | Three prose lines this PR introduced ran 103-118 characters | **Fixed**; those three now wrap |
| m10 | The addendum overstated the PR-25a precedent as "the same deviation" | **Fixed**: PR-25a met the same wall from the other side and recorded it in a validation record, because departing from a convention is not dropping a stated deliverable — which is why that one needed no addendum and this one does |

## Deferred

| # | Finding | Disposition |
|---|---|---|
| d1 | `test_logical_paths_are_accepted` compares two runs and passes when both are empty; that is why M2c read "5 dogfooded tests" of six | **Fixed rather than deferred** — one assertion that the absolute run produced output. M2c now fails **7** |
| d2 | `run_tool_in_process` restoring `sys.argv` was unasserted, so it could leak into every later test | **Fixed rather than deferred**: `test_the_in_process_runner_leaves_sys_argv_as_it_found_it`, over both a normal return and an argparse exit. New probe M14 |
| d3 | The help *text* of both new parsers is pinned only by its flag names | **Recorded** as deferred 147, with why a byte-exact golden of a `--help` screen is the wrong instrument and where the text is captured instead |
| d4 | `Args:` vs `Parameters:` | Already deferred 146, routed to Phase 7 |

## What the round cost, in numbers

Added ids 32 → **38** (35 test functions), the mutation matrix sixteen → **twenty-one**,
and the three tool-test modules 61 → **67 passed**. The transcript is unchanged at
84 records and 26 differing — this round found no unenumerated behavior, which two
independent transcripts now agree on.

## After the round: what CI found that four rounds of review could not

The 3.13 leg of `Lint and holdings-free tests` failed on
`test_a_path_beginning_with_a_dash_is_reachable_only_after_another_path`. The
assertion it failed is one this PR added and one the round-4 reviewer, the three
before it and every local run had confirmed: `crlf -- -dash.txt` exits 2.

It exits 2 on Python 3.10 through 3.12 and **0** from 3.13.
`parse_intermixed_args` splits argv at the first `--` and re-parses the remainder;
through 3.12 the remainder is read with the optionals still live and the command
line is rejected, and from 3.13 it is not. Measured directly on 3.12.3 and 3.14.5.

Nothing in the review loop could have caught it: every reviewer, and every run of
the transcript and the suite, used the one interpreter the worktrees have. Only the
CI matrix runs four. The test is now
`test_a_path_beginning_with_a_dash_needs_a_path_and_a_separator_before_it` and
asserts only the two outcomes that hold on every supported version; the record's §3
and deferred entry 141 both carry the split and say which interpreter the transcript
was captured on.

This is the one finding of the whole PR that came from a gate rather than a reader,
and it is worth the note: a single-interpreter measurement is silent about a
version-dependent library behaviour, however adversarially it is read.
