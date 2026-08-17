# Owner four-items fix, round 4 — scoped re-review, and the loop terminates

Reviewed: `git diff b8c1ac1..5db3966`. Per §6.6 the fourth round is scoped:
confirm the prior rounds' findings are resolved, raise only new Majors. A
fresh no-context reviewer checked every one of the eleven prior findings
(3 Major, 6 Minor, 2 Deferred) against the tree, re-taking each measurement
rather than reading it. No edits by the reviewer.

**Counts. 0 Major.** All eleven prior findings verified resolved:

- Round 1 — the plan's matrix parenthetical reads 3.11–3.13 since #146; the
  base sweep reproduces at 28 files / 22 historical and every head match
  falls in a named set; the `_sorting.py` arm comments state the five-group
  contract; entries 4065/4129 exist.
- Round 2 — the `:(glob)` re-measure command, run as written, returns 43
  files and 98 findings in exactly the recorded distribution (ruff 0.15.22);
  the after-sweep sentence carries sets, not a total; the consumers are
  cited by symbol; entry 4066 matches `from_path`'s code.
- Round 3 — the record's chain sentence now matches both the measurement
  (five commands exit 0; `pds4linkshelf` writes its shelf and exits 1) and
  the chapter's own text; 4065 cites `copy_shelves.sh:23-25`, confirmed
  against the script; the `py310` sweep reproduces at exactly the nine
  named subplans.
- Register re-counted: 10/0/15/136/52 = 213, equation balancing. Staleness
  rule honored: nothing under `src/` or `tests/` moved after the §5
  regeneration the record cites. Ruff clean; the 33 holdings-free new test
  ids pass.

**One Minor-class residue, fixed after the round.** `split_basename`'s
docstring (`_sorting.py:122-123`) still attributed the two-group spelling to
PDS4 — the same falsified fact round 1's Minor 2 fixed in the two inline
comments, missed in the docstring three paragraphs above. The reviewer rated
it the residue of an already-adjudicated Minor, not a new finding class, and
the loop's termination does not turn on it. The clause now reads that both
shipped classes use the five-group spelling and a two-group one would be a
subclass's own. Because the fix touches `src/pdsfile/`, the full-data
evidence was regenerated afterwards: ns 1227 passed / 34 skipped, s pds3
555/3, s pds4 150/31, every other gate green — the same numbers the
validation record §5 records for the tree committed as `92bc27e`. (The regeneration itself caught two em-dashes
in the first version of the reclause, U1 findings the docstring gate
reported and the second run confirmed gone.)

**Verdict: the loop terminates** — zero Major, no new un-rebutted Minor,
eleven of eleven prior findings resolved, every re-taken measurement
reproducing.
