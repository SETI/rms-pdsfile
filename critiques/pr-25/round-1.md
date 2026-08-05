# PR-25 adversarial review — round 1

**Reviewed:** `git diff ab1fa3b..d4e0020` (2,326 lines), branch
`pr-25-common-core`.
**Reviewer:** a fresh opus-class subagent with no development context, given the
plan's §2, §6.1, §6.2, §6.4, §6.6 (including the progressive-compliance
schedule), the Phase 6 preamble and the PR-25 section, the exact diff, and read
access to the head tree, the base tree, the holdings and the consumer repos.
**Verdict returned:** `goal not met` — 2 Major, 6 Minor, 3 Deferred.

## What the reviewer verified independently and found clean

Recorded because it is the part of a review that is easy to lose: the reviewer
re-derived the AST statement counts (623 → 499, −124), re-ran the id-set
comparison and the `measured_files()` check, re-derived the ruff ratchet delta
(2,316 → 2,305; `UP031` 140 → 132; `N806` 3 → 0; every other code unchanged),
confirmed the freeze/clean-install gates, confirmed no caller references the
moved names and that `re_validate.py:102` still resolves, and — most usefully —
built two holdings trees and ran `pdsarchives` through 20 scenarios and
`pds4archives` through 11 from each tree, finding stdout and every log file
identical after normalization. It also independently reverted the
`global LOGDIRS` line in a `/tmp` copy and confirmed the pds3 regression test
fails without it.

## Major findings

### M1 — the Phase-6 per-tool gate had no evidence in the record

The Phase 6 preamble requires "a real-holdings validate run of each migrated tool
against at least one real volume/bundle, recorded in
`critiques/phase6-validation.md`", and §6.2(2) requires that run "diffed against
the pre-PR output … mtime-normalized". The record had no such run for either
archives tool. What it had covered other ground: the tool-test count (which does
not pin log text — `tests/golden/full/holdings_maintenance/` holds archive
members, md5 files and shelf sidecars, not logs), the `--help` and parser dumps
(construction, not run output), the id-set diff (pass/fail, blind to log text),
and the versioning probe (the *other three* tools).

**Accepted and fixed.** `scratchpad/tool_run_diff.sh` now runs both migrated
tools over a real PDS3 volume and three real PDS4 bundles copied out of the
holdings, 27 invocations per tree covering all five tasks plus the volset
expansion, `--quiet`, a two-flag invocation, the rejection paths and `--help`;
`scratchpad/compare_toolruns.py` diffs stdout capture by capture and log file by
log file after normalizing the clock, elapsed times, the temporary disk path and
the log time tag. Result, now in `critiques/phase6-validation.md` §5: 25 of 27
stdout captures and 19 of 23 log files identical, 2,082 normalized lines
compared, and **the six that differ differ in exactly one thing** — the traceback
frame `pds4archives.py, in main / initialize(pdsdir)` became
`_common.py, in run_main / tasks[args.task](pdsdir)`.

That last part is a real difference, not a normalization artifact, and it is
recorded rather than argued away: extracting `main()` into a shared driver puts a
shared frame on the stack, and a Python traceback names the frames on the stack.
It is in the deviations addendum (§5) for the owner, and in the PR description.

### M2 — the `plans/` artifacts an (L) PR owes were missing

§6.4 step 1 requires a sub-plan in `plans/` for a PR marked **(L)** — every
PR from 13 onward has one — and §6.4's prohibitions require an **addendum in
`plans/`, acknowledged by the owner**, for deviations from the plan. PR-25 has
four deviations from the plan's spec'd design; they were written in
`critiques/phase6-validation.md`, which is the wrong file.

The reviewer additionally noted that deviation 2 was self-authorized: this PR had
edited `.cursor/rules/pdsfile_overrides.mdc` deviation (1) to say that the
annotation ban rules out `@dataclass` — extending the rules file that sanctions
its own departure from the plan — and that `collections.namedtuple` had not been
considered as an annotation-free alternative.

**Accepted and fixed.** `plans/2026-08-04-pr-25-subplan.md` and
`plans/2026-08-04-pr-25-deviations-addendum.md` are added, the addendum marked as
needing owner acknowledgement before merge and naming `namedtuple` as the
alternative considered and why it was not taken. **The `pdsfile_overrides.mdc`
deviation-(1) edit is reverted.**

## Minor findings

| # | Finding | Resolution |
|---|---|---|
| m1 | §9's comment accounting said one comment was removed; a token-level diff shows three removed (`#### Begin active code`, `# Set up parser`, the trailing `# update`) and one reworded (`# Generate a list of pdsfiles for volume directories` → `… for the target directories`) | **Accepted.** Re-measured with a multiset diff of every comment text, base pair vs head trio: four texts have no exact match at head and none is new. The record's §10 is rewritten as a table naming each |
| m2 | The record and deferred entry 92 say `pdslogger` 3.1.1; the environment has **3.2.1** | **Accepted.** Corrected in both. The probe's *content* was re-run under 3.2.1 and is unchanged |
| m3 | Three docstrings in `_common.py` misdescribe: `path` is the **absolute** path, not "the command line's own spelling" (`_common.py:213` reassigns it), and `run_main`'s "Raises: SystemExit: Always" is wrong — the outer handler re-raises, a path pinned by `test_pds4_archives.test_initialize_on_a_bundle_raises` | **Accepted.** All three corrected |
| m4 | The two records disagree on entry 83's citation: `:915` (a write to `proceed`) vs `:917` (the live read) | **Accepted.** Entry 83 corrected to `:917` |
| m5 | Only the checksums pair asserts the versioning, but three tools were fixed; `move_old_info`/`move_old_links` became reachable for the first time and each does an **unconditional** `shutil.copy` of a sidecar that would raise `FileNotFoundError` if absent, evidenced only by a one-off `/tmp` script no gate runs | **Accepted.** `test_pds3_infoshelf.py` and `test_pds3_linkshelf.py` each gain a versioning test that pins the `_v001` names, the copied bytes of both the shelf and its `.py` sidecar, and that the original survives. The negative control was re-run with all three `global` lines reverted: all three pds3 tests fail, the pds4 one passes |
| m6 | §5 said "82 lines of docstring that had no counterpart in either original"; 82 was the total, of which 6 did have counterparts | **Accepted.** Re-measured after the m3 docstring fixes: **84 total, 78 without a counterpart**; the record now says both |

## Deferred (appended to `critiques/deferred-observations.md` as 96–98)

- **96** — `read_archive_info` is still duplicated near-verbatim; the only real
  divergence is the three-line existence guard. Worth revisiting when all five
  pairs are on the core, with a spec **callable** rather than a boolean.
- **97** — `ToolSpec.extra_arguments` is unexercised until PR-26.
- **98** — `_common.py` already mixes the generic driver with one family's
  constants; where the per-family code should live wants deciding before PR-26,
  not after.

## Rebuttals

None. Every Major and Minor was accepted.

## Re-verification after the fixes

The round's fixes touched `src/pdsfile/holdings_maintenance/_common.py`
(docstrings only), so §6.6 step 5 requires the full-data record to be
regenerated before the next reviewer. It was; the numbers in
`critiques/phase6-validation.md` §3 are from the regenerated run, and the id set
grew from +2 to +4 with the two new shelf-versioning tests.
