# PR-18 — adversarial review, round 1

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 2), given the
PR-18 section of the plan, the Phase-5 preamble including the mixin mechanics and
the alphabetical base-order rule, §2, §6.1, §6.2, the progressive `.cursor/rules`
schedule, the exact diff `git diff origin/pr-17-shelves-local-fs...HEAD`, and read
access to the repo at HEAD and to the real holdings.
**Diff reviewed:** through `85b1cc8` ("docs: record the PR-18 validation evidence
and topology").
**Verdict:** **goal met** — 0 Major, 4 Minor, 2 Deferred.

## What the reviewer verified independently

It did not take the record's word for anything. It re-derived, with its own
scripts:

- the byte-for-byte move, by AST-extracting all eleven definitions from
  `origin/pr-17-shelves-local-fs:src/pdsfile/pdsfile.py` and from
  `26afe09:src/pdsfile/_derived_paths.py` — 11/11 identical, none left behind in
  `pdsfile.py`, no extra definition in the mixin, no class-level assignment in it;
  and 8/11 still identical at HEAD, the three `log_path_for_*` differing only in
  the separate content commit;
- the freeze, by re-running `scripts/dump_public_api.py` itself — byte-identical
  at 733,876 bytes;
- the set diff, by recomputing it from the stored `--junitxml` files — 880 ids and
  558 ids, zero diff lines in both modes — and by checking the junit timestamps
  against the last `src/pdsfile/` commit, and the `measured_files()` non-vacuity
  proof;
- the ratchet, both directions: per-code conservation across all 19 codes, and the
  converse run of the whole project select set against `_derived_paths.py` with no
  per-file entry, which reports exactly three `A002` and nothing else;
- `ruff check`, the no-holdings job (80 passed / 800 skipped), and a wheel build
  containing `pdsfile/_derived_paths.py`;
- the runtime shape: bases alphabetical with `object` last, `__module__` still
  `pdsfile.pdsfile`, `LOG_ROOT_` / `LOGFILE_TIME_FMT` / `SHELF_CACHE` still in
  `PdsFile.__dict__`, `vars(pdsfile.pdsfile)` 47 → 48 with only
  `_DerivedPathsMixin` gained, no subclass shadowing a mixin name, and a
  cross-tree pickle round-trip producing identical bytes;
- the deduplication, with **48,649** differential cases of its own plus a second
  2,160-case probe using a non-empty bundleset suffix.

Its two substantive findings both came out of that last probe, which is the point
of the round.

## Major

**None.**

## Minor

### M1 — the dedup did change evaluation order, and the justification was the wrong proof

**Finding.** `_log_path_for` received the target parts as an already-built list,
so `category_` / `bundleset_` / `bundlename` / `bundleset` / `suffix` /
`logical_path` were read *before* the `place` option was validated instead of
after. On an instance missing any of the six, the parent raised
`ValueError('unrecognized place option: …')` and the branch raised
`AttributeError` — 6 of the reviewer's 48,649 cases. Unreachable through the
package's constructors, since `PdsFile.__init__` assigns all six and `copy()`
carries the whole `__dict__`. But the record and the sub-plan justified the
reorder with "no read can raise or have a side effect", supported only by "no data
descriptor of that name in any MRO" — **an argument that rules out side effects,
not raising, which is exactly the axis that moved.**

**Resolution: accepted, and fixed in the code rather than in the prose**
(`10fa308`). The reviewer offered the prose correction as its primary fix and
exact order preservation as an alternative "at the cost of re-duplicating three
lines". Neither was necessary: making the parameter a **callable** the helper
invokes at the point the parts are appended puts every read back where it was,
costs three `lambda:` prefixes and no duplication, and turns a documented residual
into no residual. §2's "a PR that changes observable behavior is wrong" has no
reachability qualifier, and `PdsFile.__new__` instances are a pattern this repo's
own tests use (`tests/pds4file/test_pds4file_blackbox.py:448`), so the difference
was better removed than described.

Measured after the fix: a **666-case** cross-tree probe — the three log-path
methods, `archive_logpath` and the six checksum/archive builders, over both
`place` values plus an invalid one, four subdirectory shapes, three suffix shapes,
two task shapes, three log roots, the default and keyword spellings, both
`Pds3File` alias methods, and **48 cases against a `__new__`-built instance that
has none of the six attributes** — is byte-identical between the parent tree and
this branch. The three cases the finding named now report `ValueError` on both
sides. `critiques/phase5-validation.md` PR-18 §6 records the callable form and the
666-case probe in place of the earlier claim; `plans/2026-07-27-pr-18-subplan.md`
§11 records the divergence from what §4 planned.

### M2 — moved members' `__qualname__`, and their wrong-arity `TypeError` text, name the mixin

**Finding.** `PdsFile.archive_logpath.__qualname__` is now
`_DerivedPathsMixin.archive_logpath`, so a wrong-arity call reports
`_DerivedPathsMixin.archive_logpath() missing 1 required positional argument`
where it used to say `PdsFile.…`. Inherent to the mandated mixin technique and
already true of PR-17's `_ShelfMixin` on the parent branch; the manifest records
no member qualnames and nothing in `src/`, `tests/` or `scripts/` matches on that
text. The record's "behavior identity, measured" claim did not carry the caveat.

**Resolution: accepted; recorded.** `critiques/phase5-validation.md` PR-18 §4
gains the caveat, states that it is phase-wide rather than PR-18-specific, and
gives the measurement that nothing depends on it.

### M3 — `plans/README.md` still describes a three-deep stack

**Finding.** `plans/README.md` enumerates the addendum files and says "(owner
instruction to stack PR-15 → PR-16 → PR-17)". This PR adds
`plans/2026-07-27-addendum-phase5-stack-extension.md` and did not add it to that
list, so the directory's own index understates the arrangement it documents.

**Resolution: accepted; fixed.** The sentence now names both 2026-07-27 addenda.
The reviewer noted that `2026-07-27-addendum-phase5-mixin-base-order.md` is also
missing and called it out of scope because that file arrives in PR-17's diff. It
is listed anyway: PR-17 does not touch `plans/README.md` (verified —
`git diff --stat origin/pr-16-path-utils...origin/pr-17-shelves-local-fs --
plans/README.md` is empty), so there is no conflict, and leaving one of the two
2026-07-27 addenda out of the sentence this PR is already rewriting would be a
worse index than either state.

### M4 — an orphaned banner is left in `pdsfile.py`

**Finding.** `pdsfile.py`'s `# Log path associations` banner now has a body of
`LOG_ROOT_ = None` and nothing else; every method it names lives in
`_derived_paths.py`. Keeping the constant is correct and mirrors the shelf block
PR-17 left, but a reader of `pdsfile.py` alone sees a section header for a section
that is not there, and `_DerivedPathsMixin`'s docstring points only one way.

**Resolution: accepted; fixed** (`10fa308`). Two comment lines under the banner
say where the methods that use `LOG_ROOT_` live and that `set_log_root` writes it
back onto the class. That is current state, not change history, so it satisfies
the comment rule.

## Deferred (non-blocking)

### D1 — entries 43, 44 and 45 confirmed

The reviewer independently confirmed entry 43's factual core — no assertion
anywhere in `tests/holdings_maintenance/` mentions a log filename — and flagged
entry 45 as the one a future executor is most likely to trip over. No action;
they are already recorded with owners.

### D2 — the PR's only content edit has no holdings-free coverage

The no-holdings job exercises none of `_log_path_for`; the entire regression net
for the deduplication is `tests/pds3file/test_pds3file_blackbox.py` under full
data, so CI without holdings cannot catch a regression in this code at all.
Correct, and out of scope: PR-18's gate is an identical pass/fail set, so it may
not add a test. **Appended as entry 46, owner Phase 6**, alongside entry 43 which
covers the same test surface. Per the common brief's scope-discipline rule, a
Deferred finding is deferred — it is not taken up here.

## Regeneration

Round 1's fixes touched `src/pdsfile/_derived_paths.py` and
`src/pdsfile/pdsfile.py`, so under §6.6 step 5 the full-data record was
regenerated before round 2. `critiques/phase5-validation.md` PR-18 §3 reports the
regenerated run.
