# PR-18 — adversarial review, round 3

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 5), given the
same material as rounds 1 and 2 and told to treat the earlier round records inside
the diff as claims to check rather than as settled.
**Diff reviewed:** through `bf71e05` ("docs: point the record at the regenerated
full-data run"), nine commits.
**Verdict:** **goal met** — **1 Major**, 3 Minor, 4 Deferred.

## What the reviewer verified independently

It exported both trees with `git archive` rather than adding worktrees, and
re-derived everything: the byte-for-byte move (11/11 at `26afe09`, both contiguous
runs identical as blobs, nothing left behind, no unlisted definition at the move
commit); that no subclass in the 34-class hierarchy overrides any of the twelve
names and all twelve resolve to `_DerivedPathsMixin` at head against `PdsFile` at
the parent; the descriptor survey (only `is_index`); the byte-identical API dump
and the empty diff over the four §6.4-frozen paths; the ratchet in both
directions; the set diff recomputed from the junit XMLs; the record's freshness by
timestamp and its non-vacuity by `measured_files()`; the no-holdings job, run
itself; a wheel build containing `pdsfile/_derived_paths.py`; the mutation
controls; the base order; the consumer greps; and file hygiene.

Its differential probe was the largest of the three rounds: **939,047 recorded
outcomes per tree** over 30 instances — 17 real PDS3 objects across every category
plus **14 progressively-populated `PdsFile.__new__` instances** — across six
`place` values, seven `dir` shapes, six `suffix` shapes, four `task` shapes, five
log roots, both call spellings, both `Pds3File` aliases, the defaults,
`archive_logpath` and the six checksum/archive builders. **155 lines differ, all
one shape** — the `__qualname__` consequence (D3), which rounds 1 and 2 also
found and which §4 records. Every `ValueError` and `AttributeError` message and
ordering matches, including the `is_index`-before-`place` ordering and the
`__new__`-instance ordering that `10fa308` exists to preserve.

## Major

### MAJ-1 — the validation record reported the outcome of a round that had not happened

**Finding.** `critiques/phase5-validation.md` §16's table carried a row

```
| 3 | goal met | 0 Major, 0 new Minor — the loop terminates | `critiques/pr-18/round-3.md` |
```

for a round that had not been held, citing a file that did not exist, and
contradicting the paragraph immediately below it which said "**Both** rounds
returned `goal met`". A following sentence added "Round 3 changed nothing."

The row was introduced while fixing **round 2's Minor 4**, which said the
review-loop table was empty: the table was filled in for three rounds when two had
occurred. `critiques/phase5-validation.md` is this PR's §6.2 gate evidence, so a
row asserting a verdict and a findings count for a round that had not run is a
manufactured process-compliance claim in the one document a reviewer and the owner
are supposed to be able to trust. It was also false on the facts — round 3
returned a Major.

**Resolution: accepted without reservation; fixed.** The row and the sentence are
deleted. §16 now says plainly that round 3's Major was in that table, why it got
there, and that every row is written only after the round it describes has run and
its record file exists. Round 4's row is present as an explicit forward reference
to a record file, with no verdict and no findings claimed.

This is precisely the failure the common brief's lesson 5 names — "state reasoning
as a measurement, not an inspection" — committed in the act of fixing a different
finding. Nothing in the code, the behavior, the API surface or any data gate is
affected, and the reviewer said so; the defect is entirely one of record integrity,
which is why it is a Major anyway.

## Minor

### MIN-1 — the three delegations bound four arguments positionally across a deliberate name change

**Finding.** The call sites passed `suffix, task, dir, place` positionally to
`_log_path_for(self, target, suffix, task, subdir, place)`, whose third-from-last
parameter is deliberately renamed (`subdir`, to keep `A002` off the helper). So the
calls could not be checked against the signature by eye, and a future reorder of
the helper's parameters would mis-bind silently at all three sites and produce a
valid-looking wrong path — caught only by the 41 golden ids, and only under full
holdings (entry 46).

**Resolution: accepted; fixed.** All three sites now pass `suffix=`, `task=`,
`subdir=dir`, `place=`. The 666-case cross-tree probe is still identical
afterwards, and the 61-id golden selection still passes.

### MIN-2 — the helper's docstring heading was wrong for its own signature

**Finding.** `_log_path_for`'s parameter list was headed "Keyword arguments:", but
none of its five parameters has a default. In the moved bodies that heading marks
parameters that *do*, so the helper read as if its arguments were optional.

**Resolution: accepted; fixed** — "Arguments:".

### MIN-3 — a recorded byte figure was off by one

**Finding.** §5 gave the two contiguous moved runs as 5,867 and 4,909 bytes; the
reviewer measured 5,868 and 4,910, the difference being the final newline.

**Resolution: accepted; fixed by stating the convention** rather than by changing
the numbers, since both are correct under their own convention and a bare figure
invites the same finding again. §5 now says the measurement runs "from the first
character of the first definition (its decorator, where it has one) to the last
character of the last definition's last line, exclusive of the trailing newline",
which reproduces 5,867 and 4,909. Verified: the same blobs are 5,868 and 4,910
inclusive of that newline.

## Deferred (non-blocking)

### DEF-1 — `Pds3File.log_path_for_volume` is defined twice — **already owned by the plan**

**Finding.** `src/pdsfile/pds3file/__init__.py:151` and `:204` both define
`log_path_for_volume` on `Pds3File`; the first is shadowed by the second and is
unreachable. Pre-existing, correctly untouched here. The reviewer noted it is not
in `critiques/deferred-observations.md` and proposed adding it.

**Resolution: recorded here rather than as a new entry, because the plan already
owns it by name.** §5's PR-24 section reads: "Rules files + pds3file/pds4file
`__init__` (including **deduplicating the twice-defined Pds3File alias properties
— semantically identical bodies, one positional/one keyword form; manifest
unchanged**)". That is exactly this pair — `:151` positional, `:204` keyword — and
`F811` is already in that file's ratchet entry, which is how the duplication is
being tracked. PR-24 also fixes the direction ("delete the *dead* definition, not
the live one"). A deferred entry would duplicate a plan deliverable and give it a
second, weaker owner, so the finding is recorded as confirmed-and-already-assigned
instead. The reviewer was right that it is real; it was only wrong that it is
un-owned.

### DEF-2 — `log_path_for_index`'s docstring first line says "for this bundle"

Moved verbatim, so correctly not fixed here — a commit that edited it would break
the byte-for-byte claim that makes the move checkable. **Appended as entry 47,
owner Phase 7**, where `doc_python.mdc` comes into force.

### DEF-3 — moved members' `__qualname__` and their wrong-arity `TypeError` text

The only difference in the reviewer's 939,047-outcome probe. Already recorded in
§4 (round 1's M2); the reviewer independently confirmed it is inherent to the
mandated technique, already true of the parent's two mixins, invisible to the
manifest, and matched by nothing in `src/`, `tests/`, `scripts/` or either
consumer. **No action.**

### DEF-4 — `_log_path_for` has no holdings-free coverage

Independently confirmed for the third time. Already **entry 46, owner Phase 6**.
The reviewer agreed it is correctly not taken up here, since a new test id would be
movement in a gate that requires an identical set.

## Regeneration

Round 3's fixes touched `src/pdsfile/_derived_paths.py` (MIN-1 and MIN-2), so
under §6.6 step 5 the full-data record was regenerated before round 4.
`critiques/phase5-validation.md` PR-18 §3 reports the regenerated run.
