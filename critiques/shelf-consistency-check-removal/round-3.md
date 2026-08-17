# shelf_consistency_check removal, round 3 — adversarial review

Reviewed: `git diff fix/archive-infoshelf-rebuild..HEAD` at `758a330` (the
removal, rounds 1-2's fixes, and the validation record), by a fresh no-context
reviewer with the owner's instruction, plan §2/§6.1/§6.2/§6.6, the exact diff
and repository read access. The round's explicit mandate included auditing the
new records themselves. No edits by the reviewer.

**Counts.** 1 Major, 2 Minor, 0 Deferred — all three against the validation
record, none against the removal. The reviewer re-measured the register
arithmetic, the count table, the full-suite collection delta (1243 base -> 1224
head, exactly the 19 collected tests of the deleted file), the tool-test run
(409 passed, matching the record to the second), every quoted git command, and
the scope/hygiene checks, and found the removal itself clean.

---

## Major 1 — the record's stubtest sentence invented a mechanism — FIXED

`critiques/shelf-consistency-check-removal-validation.md`: "(stubtest counts
stub files, which never included the tool; the source-tree count is the Sphinx
one below)" was false on both counts, and measurably: there are 43 stub files,
stubtest counts the package's modules, and the gate's exact invocation reports
**79** modules at base against **78** at head — the removal moved this count by
one too, and the base branch's own records (`pr-35-validation.md`,
`pr-33a-validation.md`) say 79. The real reason 78 differs from Sphinx's 77 is
the generated `pdsfile._version`, which `docs/conf.py` excludes via
`_GENERATED_MODULES` and stubtest checks. **Resolution:** the sentence now
states the measured 79 -> 78 with its two sources and the `_version`
explanation. A validation record inventing a mechanism instead of measuring one
is precisely the failure mode this project's records exist to prevent; the
reviewer was right to grade it Major.

## Minor 2 — the pickaxe result was not dated to where it reproduces — FIXED

"`git log --all -S'shelves/info'` — four commits" is true at base `6f5c718` and
returns seven at head, because this branch's own commits delete and quote the
occurrences. The record now dates the command to base and notes that the
branch's commits add themselves without touching code.

## Minor 3 — the record pre-declared round 3 as terminating — FIXED

"Round 3: see `round-3.md` — the terminating round" was written before the round
ran, cited a file that did not yet exist, and §6.6 makes termination a measured
event. This round's Major proves the point. The record now summarizes round 3's
actual findings and leaves termination to round 4's measured verdict.

---

**Verdict (reviewer's, verbatim):** "Goal not met as it stands. The removal
itself is complete, every count is right, and the git history is honestly told —
but the validation record, the PR's own instrument of proof, contains one
measurably false mechanism claim (stubtest, Major), one command that no longer
reproduces its stated result (pickaxe, Minor), and one pre-declared outcome for
this round (Minor). Fix the three sentences and the branch is done: nothing else
survived attack."

All three fixed; round 4 gets a fresh reviewer and the updated diff.
