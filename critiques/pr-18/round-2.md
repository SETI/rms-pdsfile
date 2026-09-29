# PR-18 — adversarial review, round 2

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 5), given the same
material as round 1 — the PR-18 section of the plan, the Phase-5 preamble
including the mixin mechanics and the alphabetical base-order rule, §2, §6.1,
§6.2, the progressive `.cursor/rules` schedule, the exact diff
`git diff origin/pr-17-shelves-local-fs...HEAD`, and read access to the repo at
HEAD and to the real holdings. It received no implementation conversation and no
summary of round 1; round 1's record is inside the diff it audits, and the brief
told it to treat that record as a claim to check rather than as settled.
**Diff reviewed:** through `aa2093d` ("docs: record round 1 and refresh the
validation record").
**Verdict:** **goal met** — 0 Major, 5 Minor, 3 Deferred.

## What the reviewer verified independently

Again nothing was taken on trust. Its own measurements:

- move fidelity by AST extraction against the parent commit — 11/11 byte-identical
  at `26afe09`, nothing left behind, no unlisted definition in the mixin, and
  `pdsfile.py`'s whole diff is 5 added lines (the import, the class statement and
  three comment lines) against 316 deleted;
- a **909,837-comparison** cross-tree differential probe over **167 instances** —
  real PDS3 and PDS4 objects from every category, `__new__`-built instances missing
  each target attribute in turn, and a 120-case checksum/archive grid — across the
  `place` / `dir` / `suffix` / `task` / log-root / keyword / alias / default axes.
  **Zero differences** except one shape, the `__qualname__` consequence (D1);
- the freeze, by running the dumper on both trees with the import source proved —
  byte-identical at 733,876 bytes; `vars(pdsfile.pdsfile)` 47 → 48 gaining only
  `_DerivedPathsMixin`; identical pickle bytes and a cross-tree load in both
  directions; the MRO `PdsFile, _DerivedPathsMixin, _LocalFsMixin, _ShelfMixin,
  object`;
- the ratchet in both directions, including the converse run with
  `_derived_paths.py`'s entry removed;
- the set diff, recomputed from the stored junit XMLs — 880 and 558 ids, identical
  lists — plus the timestamp and `measured_files()` non-vacuity checks;
- `scripts/run-all-checks.sh` with no holdings env vars, run itself: 80 passed /
  800 skipped, exit 0;
- its own mutation matrix against `tests/pds3file/`, patching the loaded mixin in
  memory, reproducing all seven of the record's negative controls;
- its own `symtable`+AST sweep of the new module.

**It found no behavioral, freeze, ratchet or gate violation.** All five Minors are
accuracy defects in the records and one comment.

## Major

**None.**

## Minor

### M1 — the record's HEAD byte-identity count was wrong, and self-contradictory

**Finding.** `critiques/phase5-validation.md` §5 said "At HEAD, seven of the
eleven are still byte-identical. The four that are not are `set_log_root`'s three
siblings and the block that contains them". Measured: **eight** are identical (the
seven checksum/archive definitions **plus `set_log_root`**, which the
deduplication does not touch) and **three** are not. The sentence also contradicted
itself — "four that are not" against "three siblings" — and contradicted
`critiques/pr-18/round-1.md`, which says 8/11.

**Resolution: accepted; fixed.** Confirmed by re-running the byte check: eight
identical, three differing, and the check also reports the one definition in the
mixin that is not on the move list — `_log_path_for` itself. The corrected
paragraph names all three differing methods and accounts for `_log_path_for`
explicitly, which the old wording did not.

### M2 — the record's line counts were stale

**Finding.** §5 said "`pdsfile.py`: 5,436 → 5,123 lines; `_derived_paths.py` 311".
Actual at HEAD: **5,125** and **313** — the round-1 fix added two lines to each
file and the refresh commit updated the substantive sections but not this line.

**Resolution: accepted; fixed.** `wc -l` confirms 5,125 and 313.

### M3 — the sub-plan had no "as executed" section, and round 1 cited one

**Finding.** `plans/2026-07-27-pr-18-subplan.md` ended at §10, but its own preamble
promises the PR-17 model "including the 'as executed' delta appended at the end",
and `critiques/pr-18/round-1.md` cites "§11" as recording the divergence. Worse,
§4 still asserted the **superseded** design — the pre-built list and the "cannot
raise" argument round 1 rejected — so the sub-plan read as a description of code
that was not shipped.

**Resolution: accepted; fixed.** §11 "As executed" now records three divergences:
divergence 4 shipping as a callable and the §4 evaluation-order bullet being
superseded; §8 check 13 becoming a cross-*tree* comparison rather than a
same-tree before/after, which is the question §6.2 actually asks; and the plan's
"golden-tested via the tool tests from PR-13" premise not surviving measurement.
The earlier sections are left as written, per the convention.

### M4 — the record's review-loop table was empty

**Finding.** §16 was a header and a separator with no rows, while the equivalent
sections for PR-15, PR-16 and PR-17 are all populated.

**Resolution: accepted; fixed.** The table now carries a row per round, with a
paragraph recording what each reviewer re-derived for itself and how §6.6 step 5's
regeneration rule was applied at each boundary.

### M5 — wording nit in the new `pdsfile.py` comment

**Finding.** `src/pdsfile/pdsfile.py`'s new comment said `set_log_root` "writes it
back **there**", where the nearest named place is `_derived_paths.py`; what it
actually writes is `cls.LOG_ROOT_`, i.e. the class.

**Resolution: accepted; fixed** — "writes it back onto the class". This is the one
round-2 change under `src/pdsfile/`. It is two words inside a comment and cannot
alter behavior, but §6.6 step 5's regeneration rule is mechanical, so the
full-data record was regenerated before round 3 rather than argued about.

## Deferred (non-blocking)

All three are items already recorded; the reviewer confirmed each independently
and added no new one.

### D1 — moved members' `__qualname__` and their wrong-arity `TypeError` text

The only difference in the reviewer's 909,837-comparison probe: 164 cases, all
that one shape. It agreed the consequence is inherent to the mandated mixin
technique, is already true of `_ShelfMixin` and `_LocalFsMixin` on the parent
branch, is invisible to a manifest that records kind and signature, and is matched
by nothing in `src/`, `tests/`, `scripts/` or either consumer. Recorded in
`critiques/phase5-validation.md` §4 (round 1's M2); no action.

### D2 — the deduplicated code has no holdings-free coverage

Independently confirmed: the no-holdings job's 80 ids reach none of
`_derived_paths.py`. Already **entry 46**, owner Phase 6. The reviewer agreed it is
correctly not taken up here, because a new test id would be movement in a gate that
requires an identical set.

### D3 — `A002`'s freeze-locked home moved

Already **entry 45**, owner PR-23; the reviewer confirmed the entry is accurate as
written.

## Regeneration

Round 2's fixes touched `src/pdsfile/pdsfile.py` (M5's two-word comment
correction), so under §6.6 step 5 the full-data record was regenerated before
round 3. `critiques/phase5-validation.md` PR-18 §3 reports the regenerated run.
