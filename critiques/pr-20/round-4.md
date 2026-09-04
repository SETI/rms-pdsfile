# PR-20 — adversarial pre-PR review, round 4 (scoped)

**Reviewer:** fresh, no development context, no knowledge of rounds 1–3 beyond the
list of their findings it was asked to confirm.
**Diff reviewed:** `git diff origin/pr-19-opus-index-rows...HEAD` (head `4d59196`,
base `bf42ae7`), 3,527 lines.
**Date:** 2026-07-27
**Verdict:** **goal met** — **0 Major, 0 new Minor**, 20 of 20 prior findings
confirmed resolved, 4 Deferred.

This is the *scoped* re-review §6.6's anti-thrash rule prescribes for a fourth
round: "confirm the prior round's findings are resolved; raise only **new
Major** findings." The reviewer was given the list of all 20 prior findings
(19 Minor plus round 2's Deferred) and asked to confirm each **by re-measuring,
not by reading the record's claim that it was fixed**, and to note anything that
would have been a Minor as Deferred instead.

## The loop terminates here

A fresh reviewer returned **zero Major and no new un-rebutted Minor**, which is
§6.6's termination condition, at the four-round cap. **Nothing was rebutted in any
round**: every one of the 19 Minor findings across rounds 1–3 was accepted and
fixed, and each was re-measured by the executor before being fixed rather than
corrected on the reviewer's say-so.

## The 20 prior findings — all confirmed resolved

The reviewer re-measured every one. The confirmations worth naming because they
required running something rather than reading something:

| # | How it was confirmed |
|---|---|
| 7 | its own 34-class shape dump on both trees: `__bases__[0]` differs for **`PdsFile` alone**, the `== 'Pds4File'` sniff verdict differs for **no** class, all 34 MROs differ only by insertion of the two mixins |
| 9 | **executed** on a bare `PdsFile`: `split_basename('FOO.LBL')` returns `'FOO.LBL'`; `basename_is_label` raises `AttributeError … 'LBL_EXT'`; `sort_basenames` raises `AttributeError … 'BUNDLESET_PLUS_REGEX_I'` |
| 10 | `wc -l` 525 / 373 at HEAD against `git show 34837f6:` 522 and `71ae46b:` 370, plus a `git diff` of each showing the growth is **entirely inside the class docstring** |
| 13 | its own parse: 4 matching string constants, **all 4 classified as docstrings**, and **0** `Name` nodes spelling any of the three classes |
| 15, 17 | a regex sweep confirming **no line number into either new module appears anywhere** in the record or the sub-plan, and a one-by-one check of the five line numbers that remain (into `_index_rows.py`, `_opus.py` and the two index-shelf tools), all correct at HEAD |
| 19 | **executed**: `associated_abspaths` on a bare `PdsFile` raises `TypeError: 'NoneType' object is not subscriptable` at the `ASSOCIATIONS[category]` line, never reaching `IDX_EXT` |
| 20 | re-measured without reproducing strings: the archived plan holds 2 distinct `~`-rooted tokens (3 occurrences) that denote **one** directory, and `normpath(expanduser(token))` equals `dirname()` of **both** current roots, each root being that directory plus exactly one component; present identically at `bf42ae7` and `origin/rewrite`, absent from `origin/main`; **0** tracked files contain either root verbatim |

## Independent re-verification of the gates

The reviewer re-derived, rather than read: all 27 moved definitions byte-identical
and all three contiguous runs identical as blobs; **the 110 definitions that
stayed also all byte-identical**; `is_logical_path` and the module-level tail in
place; the API dump byte-identical (733,876 B, md5 `442428da…`, both stderr
empty); all 18 ratchet codes conserving with totals **80 → 74 + 5 + 1 = 80** and
the converse check; **all ten junit XMLs re-reduced with its own parser**, base and
all four head pairs at 848/34 (882 ids) and 555/3 (558 ids), the base↔head-4 diff
empty in both modes, all four head pairs byte-identical, and **its reduction
matching the executor's committed `.set` files in all ten cases**; the provenance
counts; the no-holdings gate at 82/800; `vars(pdsfile.pdsfile)` 50 → 52 with
nothing lost; the empty mixin/subclass intersections; the `symtable` sweep and its
per-definition breakdown; both docstring contracts in direction 1 (22/22 and
34/34); the consumer call-site table (37 rms-viewmaster sites over twelve names,
1 rms-opus site); and zero `.py` call sites in `tests/` for the four zero-coverage
methods. Freshness: the last change under `src/pdsfile/` is `a529d26` at 21:09:41
and pair 4's XMLs are 21:12:38 / 21:14:29.

**It also checked four mixin-move hazards no prior round and no part of the record
had checked**, and all four are clean: **no `super()`, no `__class__`, no
`__`-name-mangled attribute, and no `getattr`/`hasattr`-by-string reference to any
of the 27 anywhere in `src/`.** Those are the four ways moving a body into a
different defining class can change its meaning, and none of them is present — so
the move is semantically inert, which is a stronger statement than
byte-equivalence alone.

## New Major findings

**None.**

## Deferred — four, of which three were fixed in place rather than deferred

The reviewer declined to raise these as Minors, per its scoped mandate. Three are
corrections to text this PR itself wrote, so they are fixed here rather than
carried forward — deferring a wrong sentence of one's own is not what the
Deferred bucket is for:

- **(a)** §14 described direction 2's residue as including the words "I/O" and
  "WRITTEN". `I/O` occurs **zero** times in either module — round 1's own fix
  deleted the phrase — and the list omitted `AttributeError` and `TypeError`,
  which rounds 2 and 3 added. The substantive claim (the residue is prose only)
  still held, and the reviewer recomputed it to confirm. **Fixed:** the residue is
  now re-derived at HEAD and the sentence says it is re-derived at every round.
- **(b)** `_AssociationsMixin`'s out-of-scope receiver list omitted `os.path`,
  which is a receiver in `associated_abspaths`. This is exactly the defect round
  2's Minor 6 fixed in `_SortingMixin`'s twin sentence, not carried across.
  **Fixed** in `src/pdsfile/_associations.py`.
- **(c)** the byte totals are one byte per definition below a
  `splitlines(keepends=True)` measurement, because the source segment is taken
  without its trailing newline. The convention is uniform and defensible but was
  unstated, so a re-deriving reader got different numbers. **Fixed:** the
  convention is now stated in §5.
- **(d)** §5 cites `pdsfile.py` line numbers in the **parent-tip** frame and §10
  cites one in the **HEAD** frame; both are correct in their own frame and the
  parent-tip frame is declared once, fifty lines earlier. **Not changed** — this
  is the frame the whole of §5 is written in, and renumbering half of it to HEAD
  would make it disagree with the windows it exists to document.

Fix (b) touches `src/pdsfile/`, so the full-data record is **regenerated** once
more even though no further reviewer follows: §6.6's freshness rule is about the
record, not only about the next round, and a record predating the last `src/`
change is a Major by that rule.
