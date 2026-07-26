# PR-13 — adversarial review round 5 (after the CI failure)

- Focus diff: `git diff e89ba3a..HEAD` — the commits responding to the CI failure
  of PR #105 and to CodeRabbit's five findings.
- Head reviewed: `3fab1ed23ddb4a2092c9d1540e8e693af71fa60a`
- Reviewer: a **fifth** fresh no-context subagent, briefed on what the follow-up
  claimed and told to attack the determinism changes specifically.

## Verdict

**`goal not met`** — 2 Major, 4 Minor. The first non-clean round of this PR, and
it earned it: both Major findings were real and neither was cosmetic.

## What the reviewer verified by running

- Whole suite under a **forced-reversed enumeration harness** of its own
  construction: 111/111 passed, with the harness confirmed active in 222 tool
  subprocesses. That independently reproduces the fix *and* re-runs the whole
  cross-module audit in one shot.
- The four-cell reproduction: the shipped (ordered) comparison passes under native
  and ascending enumeration and **fails** under descending — the CI symptom — while
  the fixed comparison passes all three.
- Mutation-tested the weakened comparison: dropping a step, altering a step's text,
  and **duplicating** a step all still fail; only reordering passes. So it is a
  multiset comparison, not a set comparison.
- `unordered=True` appears at exactly 1 of 12 `check_golden` call sites.
- No file under `src/` in the whole-PR diff; `ruff check` clean; API-freeze green;
  `--mode ns` 790 passed / 34 skipped (= baseline 679 + 111), `--mode s` identical
  to baseline; holdings-free run 23 passed / 801 skipped.
- Confirmed the root cause in the tool itself, and confirmed the CodeRabbit fixes'
  premises (validation precedes `open()` in `crlf`; `pdsarchives` really has five
  task flags with two aliases).

## Major findings and resolutions

Both accepted; neither rebutted.

### 5.1 — Duplicate entry number in the deferred-observations registry

The new CI entry was appended as **12**, but entries 12 and 13 already existed:
the coordinator had added two process observations in `e89ba3a` while this work
was in flight, and I appended without re-reading the file after pulling. So
`test_pds3_dependency.py` cited "entry 12", which resolved to an unrelated entry
about `--mode` defaults.

The reviewer landed the point hardest where it stung: this **falsified the PR's
own rebuttal** of CodeRabbit finding 1, which argued that entry numbers must never
be renumbered *precisely because they are cited by number*.

**Fixed.** The entry is now **14**; the lead-in, the test module's citation and the
`ci-and-coderabbit.md` reference all updated, and the lead-in now says explicitly
that 12-13 are process observations rather than tool defects. Verified no duplicate
numbers remain by extracting every list marker in the file.

### 5.2 — The unordered comparison unpinned far more than the instability required

The sharpest finding of the whole PR. The reviewer measured what actually moves:
of the 18 emitted steps, **12 are byte-identical in position** under either
enumeration, and only the 6 naming an individual metadata table move. Comparing
the whole list as a multiset therefore surrendered ordering guarantees that the
tool really does make — including that `pdsarchives --initialize <volumes>`
precedes `pdschecksums --initialize archives-volumes/...`, i.e. that an archive is
built before anything tries to checksum it. A Phase 6 consolidation reordering a
rule's message list would have gone undetected, which is the exact regression class
this golden exists to catch.

**Fixed.** I confirmed the 12/6 split myself by running the tool with its
enumeration forced both ways: the 12 steps that do not name a `.tab` are
order-invariant, the 6 that do are not. The test now:

- compares the golden as a sorted multiset (set and text of all 18 pinned), **and**
- compares the subsequence of order-deterministic steps against the golden **in
  exact order**, plus spells out the two relationships that matter most
  (archive before its checksums; checksums before info shelf).

Verified by construction: swapping two stable steps is accepted by the multiset
comparison alone and **rejected** by the new ordered assertion, while moving a
`.tab` step is still tolerated. The reviewer's caveat that the stable/unstable
split is a property of this one-volume fixture is recorded in the test module's
header, which states how it was measured.

The reviewer also corrected the *mechanism* I had given for the ordering guarantee
(Minor 5.4): the checksums and infoshelf steps come from a **single** rule's
message list emitted in source order, not from separate rules. The guarantee is
stronger than I had described.

## Minor findings and resolutions

| # | Finding | Resolution |
|---|---|---|
| 5.3 | `validation.md` claimed "5 rounds, every round `goal met`" and cited a `round-5.md` that did not exist — a verdict pre-declared before the review ran. | **Fixed.** The row now states rounds 1-4 clean, round 5 `goal not met` with 2 Major fixed, round 6 confirming. The dangling "sample output is in the round-5 record" pointer in `ci-and-coderabbit.md` is removed. |
| 5.4 | Four places said the checksums-before-infoshelf ordering holds "because those come from different rules"; they come from one rule's message list. | **Fixed** in the test module header, the deferred entry, and the CI record. |
| 5.5 | `return pytest.fail(...)` — `pytest.fail` never returns, so the `return` is dead and mislabels the helper's contract (it raises `Failed`, not `AssertionError`). | **Fixed**: `return` dropped. |
| 5.6 | `''.join(sorted(lines))` is not injective on multisets when a side lacks a trailing newline, so `"b\\na"` and `"ab\\n"` would compare equal. Unreachable at today's only call site, but a trap for the next opt-in. | **Fixed**: `check_golden` now compares line **lists**, never a joined string. |

## Note for the coordinator

This round exceeded the §6.6 four-round cap. That cap governs the pre-PR loop,
which converged cleanly at round 4; round 5 was commissioned separately after CI
exposed a defect class none of the first four could have seen without running on a
different filesystem. Round 6 is a scoped confirmation of these six fixes.
