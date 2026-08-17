# Owner four-items fix, round 1 — adversarial review

Reviewed: `git diff b8c1ac1..c11c1d0` (the four fixes, the lint follow-up and
the validation record). A fresh no-context reviewer was given the owner's
instruction (the addendum), plan §2/§6.1/§6.2/§6.6 with the compliance
schedule, the exact diff and repository read access, and told to prove the
PDS4 regex change incomplete or too permissive, to prove a surviving 3.10
claim or a wrong count, and to prove any recorded measurement asserted rather
than taken. No edits by the reviewer.

**Counts.** 1 Major, 3 Minor, 1 Deferred. Verdict: goal not met, solely on
the Major. The reviewer independently reproduced the observation-4062 failure
and the fix, verified the five-group parity against `Pds3File`, walked every
consumer of the pattern, re-took the ruff stub measurement (98 findings, the
identical per-code distribution, under ruff 0.15.22 where the record's run
used 0.15.7), re-counted the register (10/0/15/133/52 = 210 with the closure
equation balancing), confirmed the API manifest diff is empty, and confirmed
the new tests execute the scripts and assert content rather than existence.

---

## Major 1 — a surviving 3.10 claim in the active plan — FIXED

`plans/2026-07-25-modernization-plan.md:453`: PR-14's "record the actual
matrix (self-hosted Linux 3.10–3.13 full-data …)" parenthetical states the
matrix as present fact and contradicted deviation (8) as this PR corrected
it — eleven lines below a line the PR did fix. The validation record's §1
claimed the after-sweep was clean, which this line falsified.

**Resolution.** The parenthetical now reads "self-hosted Linux full-data over
the supported versions, 3.11–3.13 since #146"; the record's §1 names the
third plan line and how it was found.

## Minor 1 — the sweep's counts did not reproduce — FIXED

The record said 29 files at base with 23 historical; `git grep -l` at
`b8c1ac1` over the stated extension set returns 28, with 22 historical (21
`critiques/` files + the archived v1 plan). The after-state sentence was also
too strong: the active plan's new self-describing parentheticals, the
addendum and the record itself still match `3\.10`.

**Resolution.** §1 now carries the measured 28/22 split, notes that two of
the register's matches were the 3402 entry itself, and states the after-state
as the measured 27 files with what each remaining match is.

## Minor 2 — the "two groups" comments in `_sorting.py` were falsified by the diff — FIXED

`_sorting.py:149` and `:285` said "For PDS4, we capture bundle set + version,
so two groups"; after the fix both shipped classes yield five groups and the
two-group arms serve no caller, as does the `None` guard at `pdsfile.py`'s
suffix assignment in `child()`.

**Resolution.** Both comments now state the current contract (five
PDS3-shaped groups from both classes; the arm serves only a subclass defining
a two-group pattern). The dead arms and guard are register entry 4129 rather
than a removal here: the owner's scope for item 4 is the regex, and deleting
defensive branches from shared consumers is behavior-adjacent cleanup that
deserves its own change.

## Minor 3 — the re-measure command under-measures without globstar — FIXED

`pyproject.toml`'s comment said `ruff check src/pdsfile/**/*.pyi`; in a shell
with `globstar` off that expands to the two `*/__init__.pyi` stubs and
reports 2 findings, not 98.

**Resolution.** The comment and the record now use
`ruff check $(git ls-files 'src/pdsfile/**/*.pyi')` and say why; the record
also notes the measurement reproduces under both ruff 0.15.7 (the run) and
0.15.22 (the venv, re-taken by review).

## Deferred — two cosmetic defects in the still-frozen copy scripts — RECORDED

`copy_shelves.sh:20-22` prints a deeper path than the one its guard tested;
`copy_documents.sh:9`'s usage line names `copy_documentation.sh`. Both
predate this PR and the freeze was lifted for the exit statuses only.
Register entry 4065 records them.

---

Fixes touched `src/pdsfile/_sorting.py` (comments only), so the full-data
evidence was regenerated after this round; the numbers are in the validation
record §5.
