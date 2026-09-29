# PR-18 — adversarial review, round 4

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 5), given the
same material as rounds 1–3 and told to reach its own conclusions before reading
the earlier round records inside the diff, and to treat their claims as claims.
**Diff reviewed:** through `5f60c3b` ("docs: refresh the PR-18 record's figures
and re-measure its negative controls"), eleven commits.
**Verdict:** **goal met** — **0 Major**, 1 Minor, 3 Deferred.
**Cap:** §6.6's hard cap is four rounds. This is the fourth.

## What the reviewer verified independently

It re-derived the move fidelity by AST extraction from
`git show origin/pr-17-shelves-local-fs:src/pdsfile/pdsfile.py`: **11/11
byte-identical at `26afe09`**, both contiguous runs identical as single blobs
under **both** byte conventions (5,867 / 4,909 exclusive of the trailing newline,
5,868 / 4,910 inclusive), 8/11 still identical at HEAD, nothing left behind, and
exactly one unlisted definition in the mixin — `_log_path_for`. It confirmed
`26afe09` is a pure move by checking that its only *additions* to `pdsfile.py`
are the import, the class statement and one word in a comment.

It also re-derived: the class shape (all eleven names resolving to
`_DerivedPathsMixin` on `PdsFile`, `Pds3File` and `Pds4File`, signatures
byte-identical to the parent; mixins pairwise disjoint; **pickle bytes identical
across protocols 0–5** and `__module__` still `pdsfile.pdsfile`); the
byte-identical API dump (733,876 bytes each) and the four §6.4-frozen paths
untouched; the ratchet in both directions (`_derived_paths.py` needs exactly three
`A002` and nothing else, `pdsfile.py` now reports zero `A002`); the
`run-all-checks.sh` no-holdings job, run itself, **80 passed / 800 skipped**; the
§6.2 record's freshness by junit timestamp, its non-vacuity by `measured_files()`,
and the set diff **recomputed from the stored XMLs** — 880 ids (846 p / 34 s) and
558 ids (555 p / 3 s), identical in both modes; the consumer greps; and file
hygiene (no `noqa`, LF, trailing newline).

**It re-ran all seven §9 negative controls itself**, in a `git archive` copy of
HEAD, from inside that tree, with a `conftest.py` asserting the imported
`_derived_paths.__file__` — the harness discipline §9 records. Unmutated 61
passed; mutated **41, 41, 21, 5, 3, 4, 1**, reproducing every recorded count.

Its differential probe was **42,577 lines per tree**, run against the parent
worktree and against this tree with the import source asserted: seven `place`
values including non-strings, nine `dir` shapes, seven `suffix` shapes, four
`task` shapes, five log roots, positional and keyword spellings, arity and
keyword errors, **a full missing-attribute matrix over all thirteen read
attributes plus an all-missing instance**, `is_index` both ways, and a 2,160-case
checksum/archive grid. **Every return value, exception type and exception message
is identical**, including the `is_index`-before-`place` ordering and the
`AttributeError`-vs-`ValueError` ordering that `10fa308`'s lazy `target` exists to
preserve. The only differences it found are the three already recorded in §4 and
§5: the innermost traceback *frame* name, member `__qualname__` in wrong-arity
`TypeError` text, and `_DerivedPathsMixin` appearing in `vars(pdsfile.pdsfile)`
(47 → 48, nothing lost). All three are inherent to the mandated mixin technique.

## Major

**None.** The reviewer's statement of what is delivered: the checksum, archive and
log path builders move physically into `src/pdsfile/_derived_paths.py` as
`_DerivedPathsMixin`; `set_log_root` and the three `log_path_for_*` stay reachable
as `PdsFile.*` with frozen signatures; the three near-identical bodies are
deduplicated into `_log_path_for` with every one of their five divergences
reproduced by a parameter; `LOG_ROOT_` and `LOGFILE_TIME_FMT` stay on `PdsFile`;
and issue #47's API-break half is explicitly not done.

## Minor

### MIN-1 — the round-3 record asserted a state of the validation record that no longer held

**Finding.** `critiques/pr-18/round-3.md:61` read "Round 4's row **is present** as
an explicit forward reference to a record file, with no verdict and no findings
claimed." That row was removed in `5f60c3b`; §16 records the removal, but the
round-3 record still asserted its presence in the present tense. Round 3's own
Major was a validation-record claim that did not match reality, so leaving this
is the same defect one notch weaker, in the very file that documents it.

**Resolution: accepted; fixed.** The sentence is rewritten in the past tense and
now says the row was raised again by round 4 and removed in `5f60c3b`, with a
pointer to this record and to §16. The original account of what round 3 found and
why is untouched — the correction is additive, not a rewrite of the history.

**Context the executor adds.** The row was removed *before* round 4 ran, as a
self-raised correction: the coordinator's standing instruction after round 3 was
that a row is written only once its round has run and its record exists on disk,
and a pointer to a file that does not exist fails that test in a weaker form.
Round 4 then independently caught the one place the removal had not been
propagated. That is the loop working.

## Deferred (non-blocking)

### DEF-1 — a second wrong docstring in the same module

`src/pdsfile/_derived_paths.py:167` — `dirpath_and_prefix_for_archive` says
"Return the absolute path to the directory associated with this archive path."
and returns the 2-tuple `(dirpath, parent)`; its sibling
`dirpath_and_prefix_for_checksum` says "Return tuple (…)" correctly. Moved
verbatim, so correctly untouched here for the same reason entry 47 gives.
**Folded into entry 47** rather than opened as a new one, on the reviewer's own
recommendation, so the Phase-7 docstring pass treats `_derived_paths.py` as a file
with more than one of these. **Owner: Phase 7.**

### DEF-2 — the mixin shadowing check does not look at the subclasses

`tests/api/test_mixin_collisions.py:89` intersects each mixin's names with
`_defined_names(PdsFile)` only, but `Pds3File` and `Pds4File` are where the method
surface is extended (`log_path_for_volume`, `log_path_for_volset`) and are what
the maintenance tools instantiate. A name added to a subclass that a mixin also
defines would make the mixin's copy unreachable on the class callers actually use.
Measured at this head: the intersection is **empty** for both subclasses against
all three mixins, so nothing is broken. The test file is PR-17's, is outside this
PR's diff, and PR-18's gate is an identical pass/fail set, so a new assertion here
is not PR-18's to add. **Appended as entry 48, owner PR-19** or whichever Phase-5
PR next edits the mixin harness. Recorded and not taken up, per the group's
scope-discipline rule.

### DEF-3 — the already-recorded entries, independently confirmed

The reviewer checked entries 43, 44, 45 and 47 and found them accurate as
written, and measured entry 46 directly: `_derived_paths.py` runs at **14 %
statement coverage** under the no-holdings job — class and `def` lines only, no
method body executed. That is the sharpest statement of entry 46 so far and is
noted here; the entry itself already carries the finding and its Phase-6 owner.
**No action.**

## Regeneration

Round 4's one fix touches `critiques/` only. Under §6.6 step 5 the prior full-data
record therefore **carries forward** unchanged: the last change under
`src/pdsfile/` is still `5115c38` and §3's runs still postdate it.

## Termination

A fresh reviewer returned **zero Major and no new un-rebutted Minor**; the one
Minor is fixed. The §6.6 loop terminates here, one round inside its four-round cap.
