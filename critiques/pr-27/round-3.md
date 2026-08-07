# PR-27 adversarial review — round 3 (scoped)

One fresh no-context opus-class reviewer, briefed per §6.6's anti-thrash rule for a
third round: confirm the prior rounds' findings are resolved, and raise only **new
Major** findings.

**Verdict: `goal not met` — "narrowly, and in the evidence rather than the code,
for the third round running."** One Major, and five the reviewer classified as
Deferred. The finding was accepted; nothing was rebutted, and nothing stayed
deferred either — the five are recorded below under the reviewer's own heading,
and every one was fixed or had already been corrected.

The reviewer confirmed **every** prior finding resolved except one, and did so by
re-measuring rather than reading: it independently reproduced the 158 / 96 / 17
unit-set census, built a metadata unit set with an `AAREADME.txt` and measured the
10 changed lines of which 2 are the blank line, re-derived the `REPAIRS` md5 and
canonical fingerprint at both trees, diffed every moved function against both base
originals by AST, reproduced **four** of the record's negative controls, compared
`--help` byte for byte at both revisions, ran 17 of its own scenarios base-vs-base
(0 differing lines) and base-vs-head (240 lines, all falling under the enumerated
changes), and checked all three of the record's line tables against each other and
against `wc -l`.

## M1 — a load-bearing measurement invalidated by round 1's own fixes, restated three times, and asserted as checked. Fixed.

The §2 figure justifying the third driver's existence — "`run_index_main` is 67
lines against `run_main`'s 66, and 45 of them are line-identical, 67%
duplication" — was measured at the head **before** round 1. Round 1's own m5
(dropping the dead `set_log_dirs` call) and m6 (reading `log_path_method` and
`log_suffix` from the spec, with its comment) then changed `run_index_main`, and
the figure was carried forward into `pr-27-validation.md` §2, `round-1.md` m9 and
deferred entry 130 without being re-derived.

Re-derived at the final head with the method now stated in §2 — each function
extracted by AST, docstring and blank lines and the `def` line dropped, longest
common subsequence taken:

```
run_index_main    : run_main 66 lines, run_index_main 69 lines,
                    44 line-identical = 64% of run_index_main
run_selection_main: run_main 66 lines, run_selection_main 78 lines,
                    46 line-identical = 59% of run_selection_main
```

The conclusion survives — the third driver duplicates about the same fraction as
PR-26's second one, which is the point entry 130 makes — but the number did not,
and the reviewer is right that this is the same defect class round 2 raised as
Major and that was accepted without rebuttal. Two things changed as a result: the
figure is now given as the command's output rather than a hand-copied number, and
`run_selection_main` is measured alongside it so the comparison entry 130 draws is
a measurement rather than an impression.

The reviewer also found two instances of the `wc -l` table going stale again — once
in the commit that closed round 2's M2 (which itself edited `_common.py`), and once
more at the head it reviewed. Both are real and both are the same lesson: the table
has to be the last thing written. It now is, and it is checked mechanically against
`wc -l`, the ratchet and the split arithmetic rather than re-read.

## Deferred

The reviewer's classification, kept as it filed them. None was in fact deferred.

1. **The propagation test asserted less than its docstring claimed** — "logs and
   re-raises", with only the re-raise asserted. Fixed rather than deferred: it now
   reads the log file too, and a control that removes `logger.exception(e)` while
   leaving the `raise` fails it.
2. **§5 change 11's "all four pds4 sites" should have been six.** Already corrected
   in `d81c136`, from the CodeRabbit pass.
3. **§7.4 sat underneath §8.** Already corrected in `c685d66`.
4. **§8 said both unconverted `%s` sites were in `write_linkdict`.** One is in
   `write_indexdict`. Fixed.
5. **The branch was moving faster than the record could be re-taken.** The reviewer
   is right, and it is the mechanism behind M1 and behind round 2's M2. The order is
   now fixed: source first, then the gates, then the tables, then a mechanical check
   of every reproducible number in the record, the plan and the deferred entries
   against the tree.

## What this round did not find

No Major in the code, for the third round. The reviewer re-derived the equivalence
of every moved function against both originals, the freeze, the ratchet
decomposition, both data-suite runs id for id, four negative controls, the
`REPAIRS` fingerprint, the census, and enough of the transcript to attribute every
line it could produce, and reported all of it sound.
