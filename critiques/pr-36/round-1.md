# PR-36 (reports half) round 1 — full diff

Reviewer: a fresh, no-context subagent given the PR-36 plan entry with this
half's reports-only scope, the §2 ground rules, §6.1-§6.2, the §6.6 procedure
with the progressive-compliance schedule, the three skills' own SKILL.md
instructions, the exact diff `git diff 6525951..def7c2c` (four new files under
`critiques/`, 2,285 lines, nothing else), read access to the repository, the
holdings roots, the open observation register, and the session's recorded gate
and coverage evidence. Its central mandate: prove a report figure was asserted
rather than measured, prove a triage verdict wrong, prove a missed overlap
with the register. It made no edits.

The reviewer independently reproduced: the scope (`git diff --name-only` is
exactly the four files; `6525951` is the head of `rewrite`); the full gate log
read end to end (every verdict, ns 1234/34, pyroma 10/10, stubtest clean,
both Sphinx builds 0 problem lines and 77 of 77 modules, PyMarkdown 2 files);
the evidence files' internal consistency (suite outputs, coverage totals
9,715/3,704/3,542/329/58%); the three reports' conformance to their skills'
prescribed formats; the triage arithmetic (21+18+32 = 71, tally rows sum to
71 with each ID once); and roughly ninety figures and claims across the three
reports — every TS defect site, the skip arithmetic (2+22+3+2+4+1 = 34), the
grep and AST counts, all three Sphinx build results, the DOC drift sites
against `run-all-checks.sh`, the module-length measurement, all eight
no-encoding `open()` sites, the checksums pair diff (242 of 2,032, exact),
the wheel contents, and the register entries behind every overlap row,
including negative searches confirming the triage's "new" claims for TS-15,
TS-17/CA-14, CA-20, CA-21 and CA-24.

Verdict: **goal not met** — one Major, four Minor, three Deferred.

## Major findings, and their resolutions

**M1. The MemcachedCache test-coverage "waiver" cited a deviation that does
not cover it, asserted an owner decision that does not exist, and the triage
missed the register entry that holds the question open.** The test report
(TS-10, §18, and its fix prompt's "exempt by owner decision; do not try to
test it") presented the class's coverage gap as waived by
`pdsfile_overrides.mdc` deviation (4) and ground rule 9. Deviation (4)'s
pdscache row waives exactly two lint findings (`RUF015`, `UP031`); ground
rule 9 protects the class from removal, not testing; "no test environment
can exercise it" is refuted by `tests/core/test_pdscache_set_multi.py`'s
`__new__`-plus-stub-client technique; and register entry 4207 records the
gap as an open deferral owned by phase b of issue #77 — an entry the triage's
otherwise meticulous cross-reference table omitted. The executor re-verified
the whole chain (the deviation row, the stub test, 4207's text) before
fixing. **Fixed:** the test report's executive summary, TS-10, §18 and
prompt step 10 now state the open-deferral status with 4207 and its owner;
CA-13's equivalent phrasing corrected; the triage's ranked item 3, tally
caveat, TS-10 row and register table now carry 4207, and its report-defects
section records the miss.

## Minor findings, and their resolutions

**m1. §18's "full list" of sub-90% modules omitted four subprocess-shadowed
shared modules** (`pdsdependency.py` 30%, `_shelf_common.py` 39%,
`_archives_common.py` 45%, `_common.py` 50%), which TS-20's enumeration did
not name either, so the exclusion clause did not cover them. Figures
re-verified against `coverage-summary.txt`. **Fixed:** TS-20's enumeration
now names the four.

**m2. "re_validate.py, the one tool tested in-process" was wrong** — `crlf`
is also tested in-process (register 4214 records the PR-28 conversion) and
measures 98%; the CA report had it right. **Fixed:** "the two tools tested
in-process, measure 88% and 98%".

**m3. CA-13 described its measurement basis as the ns run alone**; the 58% is
the ns pass plus both `--mode s` passes in one data file. The number was
right; the description contradicted the sibling report. **Fixed.**

**m4. §20's private-import count was seven; it is eight** —
`test_pds3_archives.py:20` (`from ..._common import is_backup_name`) was
invisible to the report's own grep pattern. Re-verified at the file.
**Fixed:** eight statements across six modules, citation now `:19-20`.

## Deferred (recorded here, no register edits in this PR)

- The plan's §6.6 compliance-schedule row for module lengths still names the
  pre-deviation-(3) waiver list (`pdscache.py`, "the rule modules"); CA-01
  reports the current state correctly.
- Deviation (4)'s pdscache-row phrasing ("no test here exercises") is
  imprecise given the stub-tested method; belongs with entry 1503's
  deviation-drift family when that table is next revised.
- Register entry 6404 (maintenance tools' docstrings say `Args:`) appears
  stale: the reviewer measured 0 `Args:` sections under `src/`, matching the
  doc report.

These are listed in the triage's closing section as candidate
register-grooming items for the owner.

## Gates after the round's fixes

The fixes touch only the four record files under `critiques/` — nothing under
`src/`, `tests/`, `docs/` or configuration — so per §6.6 step 5 the full-data
record carries forward: the gate log at the round's base (`run-all-checks.sh`
green in full, ns 1234/34) and the session's s-mode runs (555/3, 150/31)
remain the evidence of record.
