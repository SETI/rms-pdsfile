# Register reconciliation — adversarial review round 1

Reviewer: fresh no-context subagent, given this PR's brief, plan §2 and §6.1/§6.2,
the exact diff (`git diff rewrite...9e7ccb2`, 502 lines) and read access to the repo.
Tree reviewed: `9e7ccb2` on base `002509e`.

The reviewer's central jobs were the four the brief names: prove a discharged entry
still reproduces, prove a surviving entry is actually stale, prove a count wrong by
recounting, and prove the index arithmetic inconsistent.

**Result: 1 Major, 6 Minor, 3 Deferred. The Major and five Minors are fixed; one
Minor is rebutted with evidence.**

## Major

**M1. Entry 4029's discharge credited the wrong PR.** The index read "entry 4029 by
the info-shelf comparison fix in #148". All three defects 4029 recorded were removed
by `fc9bfb3` ("fix: the info shelf comparison, and how a chained run is executed"),
which merged as **#123 — PR-26**, the owner entry 4029 itself named. Confirmed
independently: `git log -S` on each of the three strings
(`checksum1 != checksum1`, the `abs(...)` modtime test, the `(count1, count1)`
message) over `pdsinfoshelf.py` returns `fc9bfb3` and the original move `cb3ca7a`
and nothing else; `git show 8e4124b -- .../pdsinfoshelf.py` (that is #148) contains
zero hunks matching `checksum1|modtime1|count1`.

The discharge itself stands — `pdsinfoshelf.py:658-670` now reads `count1 != count2`,
`_shelf_common.modtimes_agree(...)` and `checksum1 != checksum2`, and the two
`test_known_undetected_corruption` pins are inverted into `DETECTED_CORRUPTIONS`.
Only the attribution was false, in the one sentence that also asserts "each
reproduced against the tree before it was discharged".

**Fixed:** the sentence now credits PR-26's fix `fc9bfb3`, merged as #123, and says
it is the owner the entry itself named.

## Minor

**m1. "entries 4202 and 4210 by the mixin harness the entries asked for"
over-claimed for 4202.** 4210 did ask for exactly what landed. 4202 did not: its
owner line was "whichever Phase-5 PR first adds a dynamic import to a mixin module,
if any does", and none has. The harness was rebuilt behaviorally regardless, which
is what closes it. **Fixed:** the two are now described separately — 4210 got its
per-subclass intersection; 4202's AST walk was replaced wholesale by a behavioral
`sys.modules` check that the dynamic import it worried about cannot fool.

**m2. "entries 4103 and 4120 by consolidations" was loose for 4103.** 4103's subject
went away in `eee15d6` (PR-09, #103), which stopped the root conftest importing the
helpers — earlier than the eight PRs this reconciliation is against, and while the
entry's own stated trigger never fired (`pyproject.toml` still has no `testpaths`;
the test modules still use `from .helper`). **Fixed:** 4103 is now credited to
PR-09's conftest rewrite and the sentence says it closed the entry incidentally
rather than by the change the entry was waiting for.

**m3. "the third `logger.close()` unpacking spelling … removed their subjects" read
as if the divergence were gone.** Two spellings remain: the named-underscore form at
six sites and `(fatal, errors, warnings, tests)` at `pdsdependency.py:531,593`. Only
the bare-`_` form is gone. Entry 4120 explicitly blessed the pdsdependency pair for
using the values, so the discharge holds. **Fixed:** the sentence now says the
migration took the bare-`_` spelling out with the `main()` bodies that held it and
left the one `run_main` chose plus the two sites the entry blessed.

**m4. Ruff-version attribution.** Three new measurements named "ruff 0.15.22", the
venv's binary, where `pyproject.toml:176` and `critiques/owner-four-items-validation.md`
name 0.15.7 — a live split that CA-11 already flags. **Fixed:** every one of the
three now records that the number is identical under both binaries and names both.

**m5. `observations-p2.md` entry 3200 read "alongside observations 4214 and 4214".**
A duplicate number, introduced by the renumbering commit `d57d6e8` itself; the entry
the second reference meant is not recoverable from the record. **Fixed** by dropping
the duplicate rather than guessing, and the line now also records that its
`Owner: Phase 6` is stale — Phase 6 ended without adding the test — while leaving the
successor open, because naming one is a decision rather than a measurement.

**m6 (REBUTTED). Entry 1400's closing sentence.** The reviewer held that "the sibling
tests in `test_pds3file_blackbox.py` already use the stronger form
(`assert False  # pragma: no cover`)" is now partly false, because TS-05 found two
blackbox sites of the vacuous shape. The sentence is true as written: the stronger
form is present at `tests/pds3file/test_pds3file_blackbox.py:950` and `:965`, spelled
`assert False # pragma: no cover` with one space before the comment, which is why a
two-space grep returns zero. Those two sites are the bodies of the very tests entry
1401 is about. The two sites TS-05 names (`:902`, `:1923`) are a *different* shape —
`except ValueError: assert True`, which swallows rather than omits — and recording
them here would import a PR-36 critique finding, which this PR is explicitly barred
from doing. The new PR-36 section heading already points at TS-05 for them.
**No change.**

## Deferred

- **`pyproject.toml:112-114` still lists `tests.pds{3,4}file.helper`** among the
  `tests.*` absolute imports that `pythonpath` exists to resolve. No such import
  exists at head — it is the import whose removal discharges 4103. A candidate
  register entry; not added here, because this PR's warrant is reconciliation and a
  new entry for a newly-found defect is a different act from recording one the
  triage already identified.
- **`observations-p2.md` entry 3007** frames its measurement as "not even stable
  across the versions this package supports … exits 2 on Python 3.10 through 3.12"
  while the floor is 3.11. Left deliberately: #159's sweep classified the register's
  3.10 matches as dated measurements and ruled that rewriting a measurement falsifies
  it (`critiques/owner-four-items-validation.md`, §1).
- **Five entries still name a completed phase as owner** (`Owner: Phase 6`). Stale,
  but re-homing each is an owner decision rather than a measurement; recorded in the
  PR body instead of edited.

## What the reviewer checked and could not break

All ten discharges reproduce as gone, each verified at a named file:line. Counts
recounted independently per file (8 / 0 / 15 / 131 / 50 = 204) and the table's number
ranges verified against the actual first and last entry in each file. The arithmetic
checks in both directions: 375 − 28 − 119 − 37 + 13 = 204; 27 previous + 10 discharged
= 37; 12 + 1 = 13; and the found-breakdown itself sums to 13. Per-file deltas reconcile
exactly. No dangling reference to any discharged number survives anywhere in the
register, in `plans/`, `docs/`, `.cursor/`, `src/` or `tests/`; the only surviving
references to re-homed numbers are the three deliberate provenance mentions. All four
"a since-resolved observation" repairs are grammatical and true. Every quoted string
and every number in the new entries 4407 and 4130 and in the 1503 addition was checked
against the file quoted. Scope is five files, all under `critiques/`, with exactly two
new entries and no import of the 71 critique findings.
