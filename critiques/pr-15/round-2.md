# PR-15 — adversarial review round 2

**Date:** 2026-07-26
**Reviewer:** a fresh, no-context opus-class subagent (a different one from
round 1, with no knowledge of round 1 or its findings), given only the PR-15
section of the plan, the Phase-5 preamble, §2 ground rules, §6.1/§6.2, the §6.6
rules including the progressive `.cursor/rules` schedule, the exact
`git diff origin/rewrite...HEAD`, and read access to the repo at HEAD and to the
real holdings.
**Diff reviewed:** `origin/rewrite`(`807956a`)`...HEAD`(`bc41364`)
**Verdict: goal met** — 0 Major, 5 Minor, 2 Deferred.

## What the reviewer independently re-ran

Again a measured review, not a paper one. It reproduced every headline number:
`b646aee` red at 20 failed / 13 passed with the per-defect grouping matching
§8's table; `a6496f8` green at 33; the round-1 test confirmed to fail against
the pre-round-1 helper by copying HEAD's test file onto the `a6496f8` tree; both
modes' set diffs empty against the base (824 and 558 ids); the driver run at 858
with 34 `tests.core` additions; 58/800 with no holdings; the two API dumps
byte-identical at 733,876 bytes; the ratchet shrink verified with
`ruff --isolated --select` on both trees and zero `noqa` in `src/`; §7's probe
reproduced exactly (1,910 objects, 11,242/474 entries, 0 value differences, 14
expiration flips); §7's "already happens on the base tree" claim confirmed on
`807956a`; and a state-leak probe over class `__dict__`s, cache identity,
`ICON_SET_BY_TYPE` and the environment showing no residue, plus a check that
adding `tests/core` to a session moves zero other ids.

## Findings

### Major

None.

### Minor 1 — the round-1 fix introduced a `KeyError` the two-key version could not produce

`src/pdsfile/pdsviewable.py`: round 1 added `(icon_type, True)` as a third probe
so an open-only icon type would be ranked, but `iconset_for` still ends with the
unguarded `ICON_SET_BY_TYPE[icon_type, is_open]`. An icon type registered only
under its open key could therefore **win** the comparison and then raise on the
closed lookup — and `load_icons` gives any name outside `REQUIRED_ICONS`
priority 99999, so such a type wins everything. The reviewer demonstrated it.
The round-1 test covered only `is_open=True`, so nothing pinned the other
direction.

**Resolution: fixed, and the round-1 approach abandoned rather than patched.**
`_priority_of_icon_type(icon_type, is_open)` now takes the open state and looks
up `(icon_type, is_open)` alone. That makes the invariant structural instead of
defensive: **a type can win only if the set that would then be returned
exists**, so the terminal lookup cannot raise for a winner. It is also simpler
than either previous version. The test is renamed
`test_an_open_only_icon_type_wins_only_when_open_is_requested` and asserts both
directions; it was confirmed to fail against the round-1 helper.

### Minor 2 — test-module headers narrated the pre-fix source

`python_testing.mdc` ("never include line numbers, verbose rationale, or change
history") is in force, and §2's "comments record current state, not change
history" says the same. Four module headers and two inline comments described
code that no longer exists, in the past tense.

**Resolution: fixed.** Every header and comment in `tests/core/` is restated as
a present-tense invariant — what the module pins, not what used to be wrong. The
genuinely current facts are kept (that neither `set_multi` nor `iconset_for` has
an in-repo caller, so these tests are their only coverage; that a
`DictionaryCache` has no `permanent_values`, so `get_permanent_values` only runs
against memcached).

### Minor 3 — §7 overstated the probe's coverage

`critiques/phase5-validation.md` §7 said the probe "reads `html_path` and `url`
on every object reached". 36 of the 1,910 raise `IndexError` instead and are
recorded as a sentinel. Identical on both trees, so the conclusion is
unaffected, but the record should say so.

**Resolution: fixed.** §7 now states that 36 probed categories are empty in the
reference root, that they raise identically on both sides, and that the
comparison therefore covers 1,874 values plus 36 identical raises. The
underlying defect is recorded as deferred entry 27.

### Minor 4 — deferred entries 15 and 20 cite counts this PR moves

Entry 15 is anchored on "the 24 the hosted job runs today" and entry 20 on
"0 passed, 824 skipped"; after this PR those are 58 and 858. The observations
themselves stand — the ~291 unmarked data-suite tests are still unmarked and the
hosted job still has no floor — only the illustrative figures drift.

**Resolution: fixed.** Both entries are annotated in place with the new figures
and a note that the observation is unchanged, and the PR-15 preamble in
`deferred-observations.md` says so explicitly instead of claiming nothing in
1–22 is affected at all.

### Minor 5 — two forward references that could not be true at HEAD

§12 cited `critiques/pr-15/round-2.md` before it existed, and no PR had been
opened, so "call the change out in the PR description" was only half satisfied.

**Resolution: fixed.** This file is the cited record; §12 now lists rounds 1 and
2 with their outcomes and points forward only to the round that has yet to run.
The PR description is written from this record when the PR is opened against
`rewrite`, per `plans/2026-07-26-addendum-phase5-stacked-prs.md`.

### Deferred (non-blocking)

Both accepted and recorded as new entries in
`critiques/deferred-observations.md`:

- **Entry 27** — `html_path` raises `IndexError` on an empty merged category
  (`self.child(self.childnames[0])` on an empty list). Measured: 36 of the 1,910
  probed objects, identical before and after this PR. Fixing it means deciding
  what a childless merged category's URL is, which is a behavior decision
  outside the enumerated list.
- **Entry 28** — `iconset_for`'s terminal lookup assumes an `UNKNOWN` icon set
  exists. After Minor 1's fix no *winner* can raise, but the starting value can
  if `load_icons()` was never called. Pre-existing shape, newly reachable only
  because the function no longer raises `NameError` first.

## Rebuttals

None. All five Minor findings were accepted and fixed; both Deferred items were
accepted and recorded.
