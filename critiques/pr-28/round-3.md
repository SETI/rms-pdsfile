# PR-28 adversarial review — round 3

Fresh reviewer, no development context and no knowledge of rounds 1 or 2. Verdict:
**goal not met** — all three Majors documentary, none requiring a code change.

The reviewer re-ran every gate and every numeric claim about the code and found
them exact: all three ruff invocations clean, ratchet 67→66 / 181→180, findings
2,250→2,249 with the base re-measured, `PT028` twice on `crlf.py`, no `F821`
anywhere, the four frozen files md5-identical, eleven console scripts and none of
them the three tools, `tests/api` 26 passed. Suite: base 1,097 ids / 1,063 passed,
head 1,128 / 1,094, **32 added, 1 removed, 0 outcome changes**; holdings-free 281 →
312. The bug fix's negative control confirmed both ways. All fourteen §5.3 probes
reproduced row for row.

Two independent constructions are worth recording because they are stronger than
this PR's own: the reviewer built its **own** 71-invocation base-vs-head transcript
that snapshots on-disk file state as well as output, found 35 differing records and
confirmed **every one falls inside the six enumerated kinds** — including shapes
this PR's transcript does not have (`crlf --repair=`, `crlf -- --verbose`,
`crlf --verbose -- -dash.txt`, `crlf -`, a relative `shelf -dashroot`) — and ran
`show_opus_products` against the **real** holdings root, byte-identical base to head
across nine output modes. It also re-derived deferred 130 with a true
dynamic-programming three-way LCS rather than `difflib`, reproducing every figure
including the greedy block partition, and confirmed all eight variation points are
real in the source.

## Major

| # | Finding | Disposition |
|---|---|---|
| M1 | `.cursor/rules/pdsfile_overrides.mdc` still listed the `F821` this PR deleted, marked "**PR-28 owns it**" — in a file that says the ratchet and it "must agree". Round 2 fixed exactly this defect one table up, in deviation (3), and missed this row | **Fixed.** The row is gone; `ruff` with the ratchet emptied emits no `F821` anywhere |
| M2 | Three deferred entries were explicitly owned by PR-28 and unanswered — entry 6 (the legacy-layout question), entry 11 (what an empty file should classify as), entry 13 (**re-derive** the single-`--mode`-pass justification for whichever tools were converted) — and two more, entries 8 and 13, still asserted that `show_opus_products` would move in-process, which the deviation makes false. The addendum's own list of where the departure lives named only two of four places | **All five fixed.** Entries 6 and 11 are answered by saying plainly that PR-28 did *not* answer them and why, and both are re-owned as open with no phase holding them. Entry 13's re-derivation is written out: neither migrated tool imports a PdsFile class, so neither can observe `use_shelves_only`, and the single pass survives on its merits rather than by inheritance — with the condition under which it expires again. Entry 8's prediction is corrected. The addendum now carries a four-row table of every passage that predicted the move, including the one deliberately left alone, plus entry 13 as a fifth of a different kind |
| M3 | Deferred entry 142 cited "54 passed" — round 1's baseline, which round 2 raised to 61. The finding survived; the evidence number did not | **Fixed**, and the entry now names the baseline by description rather than restating a number that moves under it |

## Minor

| # | Finding | Disposition |
|---|---|---|
| m4 | §2.2's "the branch had one test and now has three" — it has two | **Fixed**, and the sentence now says what the second test adds |
| m5 | The index branch's `if verbose: print(...)` was dead to the suite; deleting both lines left 61 passed | **Fixed.** `test_an_index_shelf_whose_label_exists_is_counted_not_reported` now runs the branch under `--verbose` too and asserts the mapped path. New mutation probe **M10**: deleting the two lines fails it |
| m6 | `run_tool_in_process`'s `sys.argv` rebinding — the fidelity property its docstring argues for — was asserted by nothing; deleting it left 61 passed | **Fixed.** Both help tests and both usage-error tests now assert the `usage: <tool>.py` prefix argparse takes from `sys.argv[0]`. New mutation probe **M11**: deleting the rebinding fails six ids |
| m7 | `critiques/coderabbit-findings.md` still listed the `NameError` as an open 🔴 Critical, and three findings carried line citations this PR invalidated | **Fixed.** Finding 1 is struck through and marked fixed with the test that pins it; findings 2, 3 and 12 are re-anchored to construct names rather than line numbers, which is the anchoring rule PR-27 adopted after three rounds of stale citations |
| m8 | `Args:` where `python.mdc` says `Parameters:` | **Recorded** as deferred 146: the whole `holdings_maintenance/` tree uses `Args:`, so the new docstrings match their neighbours; sweeping it is Phase 7's, and doing it piecemeal would leave three states rather than two |
| m9 | Change-history narration in code comments and test docstrings, against the standing current-state-only rule | **Fixed.** Both `# No abbreviations:` comments and both `# Intermixed,` comments say what the parser does rather than what the tools used to do, and five test docstrings were rewritten the same way. The pointer at "the deferred observations" is gone |
| m10 | §3 claimed the transcript covers "every flag and flag combination" | **Fixed**: "every flag, the flag combinations that select output" |
| m11 | The plan's PR-13 note was rewritten to say PR-13 tested via `python -m`, where the entry had said `python <path>.py` — retconning what PR-13 was told | **Fixed.** The entry now carries the correction as a correction: it specified `python <path>.py`, PR-13 used `python -m`, and that is the invocation the tools kept |

## Deferred

| # | Finding | Disposition |
|---|---|---|
| d1 | `pdsfile.tools.show_opus_products` is importable now and imports `tabulate`, a `dev`-only extra, at module scope | **Recorded** as deferred 145, with the two ways to settle it and the reason the clean-install gate stays green either way |
| d2 | Entries 142 and 143 independently confirmed by the reviewer's own probes | Noted; both stand |
| d3 | `support.no_holdings_env()`'s scrub list is load-bearing only in combination with other mutations | Entry 140's family, already recorded |
