# Register reconciliation — adversarial review round 2

Reviewer: a second fresh no-context subagent, given the brief, plan §2 and §6.1/§6.2,
the exact diff (`git diff rewrite...811ea8a`, 632 lines) and read access to the repo.
Tree reviewed: `811ea8a`. The reviewer was told what round 1 found and directed to
attack round 1's *fixes* first, on the principle that a fix written to close a finding
is where the next defect lands.

**Result: 0 Major, 2 Minor, 3 Deferred. Both Minors fixed.**

Both Minors were in a single sentence of `critiques/observations.md`, and both were
introduced by round 1's m3 fix rather than by the original reconciliation — which is
exactly the failure mode the round was aimed at.

## Minor

**m1. "the Phase-6/7 driver migration" credited Phase 7 with work that is entirely
Phase 6.** Re-measured: `git log -S '(fatal, errors, _, _)' -- src/` returns three
commits, and the two removals are `e6efd7f` (PR-25, first containing merge `10ad9d5`
= #120) and `2d2809a` (PR-27, first containing merge `3d044b2` = #125). Both are
Phase 6. No Phase 7 PR touches a `logger.close()` unpacking at all. The "/7" was an
unverified half-attribution written while fixing a different attribution defect.
**Fixed:** the clause now names the Phase-6 core migration and both commits with
their merge numbers.

**m2. "left only the one `run_main` chose" invited a recount that returns six.** The
named-underscore spelling is at six sites (`_common.py:589`, `_shelf_common.py:645`,
`_indexshelf_common.py:820`, `re_validate.py:333` and `:1065`,
`pdsdependency.py:1508`). The sentence was true read as "the one spelling" and false
read as "the one site", and its parallel construction — "and the two **sites** the
entry blessed" — pushed the reader to the second. This PR's own round-1 record says
"six sites" three pages away. **Fixed:** the clause now says "the named-underscore
form `run_main` chose at six sites" and names `pdsdependency.py:531` and `:593` as
the two the entry blessed.

A third loose figure the reviewer noted in passing — "Two re-homings do not move the
total", covering three re-homed entries across two events — is now "Re-homing does not
move the total", since the two sentences that follow enumerate them exactly.

## Deferred

- **About 24 live `Owner:` lines still name merged PRs** — `PR-30b` ×5 (#133),
  `PR-30` ×5 (#131), `PR-26` ×3 (#123), `PR-24` ×3 (#119), `PR-23` ×2 (#118), and one
  each for PR-30a/25/22/20/17/14 — on top of the five `Owner: Phase 6` lines round 1
  deferred. The register's owner column is stale far beyond the eight PRs this
  reconciliation was scoped to. Not edited here: re-homing an entry whose owning PR
  has merged without closing it is a decision about who owns it next, not a
  measurement, and there is no successor the plan names for most of them. Recorded in
  the PR body for the owner.
- **`pyproject.toml:112-114`** still names `tests.pds{3,4}file.helper` among the
  `tests.*` absolute imports `pythonpath` exists to resolve; no such import exists at
  head. Independently confirmed by both rounds. A candidate register entry, not added,
  for the reason round 1 gave.
- **Entry 3007's Python-floor framing**, left deliberately per #159's ruling that a
  dated measurement is not rewritten.

## What the reviewer checked and could not break

Every link in all four round-1 attribution rewrites: `fc9bfb3` → `0f1476c`
("Merge pull request #123 from SETI/**pr-26**-checksums-infoshelf") → PR-26, and
`git show 002509e:critiques/observations-p3.md` confirms the discharged entry 4029 did
read "**Owner: PR-26.**"; `eee15d6` is PR-09 (#103) and its diff deletes the absolute
helper imports; the 4202/4210 split holds at `test_mixin_collisions.py:111` and
`test_mixin_import_isolation.py`.

The ruff claim was checked by **running both binaries**: `pyproject.toml:176` does name
0.15.7, the `PATH` ruff is 0.15.7 and the venv's is 0.15.22, and all three measurements
return byte-identical output under each — `_shelves.py` one `B904` at `:343`;
`pdscache.py` `UP031` at `:775` and `RUF015` at `:1201`; `src/pdsfile/__init__.py`
`F403` at `:38` and `:39`.

All ten discharges reproduce as gone at named sites. Counts recounted per file
(8 / 0 / 15 / 131 / 50 = 204) and reconciled against the base at `002509e`
(10 / 0 / 15 / 136 / 52 = 213, deltas −2 / −5 / −2). Arithmetic checks in both
directions. No dangling reference to any discharged number. Every quoted string and
number in entries 4407, 4130 and the 1503 addition verified against the file quoted.
Scope is six files, all under `critiques/`, and `critiques/register-reconciliation/`
follows the existing non-PR-numbered precedent of `critiques/owner-four-items/` and
`critiques/shelf-consistency-check-removal/`. None of the 71 critique findings is
imported; the one TS-05 mention is a pointer whose wording matches the triage's own
summary row.

Round 1's m6 rebuttal was independently confirmed: `assert False # pragma: no cover`
is at `test_pds3file_blackbox.py:950` and `:965`, one space before the comment, in the
bodies of the two tests entry 1401 names.

## Termination

Zero Major and no new un-rebutted Minor: both round-2 Minors are fixed and neither
touched a discharge, a count or an arithmetic step. The loop terminates here under
§6.6, at two rounds.
