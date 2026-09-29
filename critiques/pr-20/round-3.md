# PR-20 — adversarial pre-PR review, round 3

**Reviewer:** fresh, no development context, no knowledge of rounds 1 or 2.
**Diff reviewed:** `git diff origin/pr-19-opus-index-rows...HEAD` (head `118bd1c`,
base `bf42ae7`), 3,373 lines.
**Date:** 2026-07-27
**Verdict:** **goal met** — 0 Major, 4 Minor, 3 Deferred (two of which are
confirmations rather than new items).

## What the reviewer verified independently

The same battery as the first two rounds, re-derived with its own scripts: the
27-in / 0-out AST diff of `PdsFile`'s body; byte equivalence per definition **and
as whole-window blobs** (18,426 bytes for `_sorting.py`'s class body, 12,089 for
`_associations.py`'s, identical on both sides), which is what rules out a lost
comment, sub-header, blank line or reordering; all 110 remaining definitions
unchanged; `is_logical_path` and the module-level tail in place; the API dump
byte-identical with the md5 the record cites; all 18 ratchet codes conserving and
the converse check; the full-data evidence re-reduced from the raw junit XMLs with
its own reducer (empty diff both modes) and checked for freshness against the last
`src/pdsfile/` change; the provenance counts; a whole-tree call-graph sweep
finding **0 bare `Name` references and 0 imports** of any of the 27 names against
88 attribute sites; the mixin mechanics; `vars(pdsfile.pdsfile)` 50 → 52 with
nothing lost; the alphabetical base order; and the intermediate commit `34837f6`
green on ruff, import, base order and the no-holdings job.

Two things it did that the earlier rounds did not. It **executed** every runtime
claim the two class docstrings make — on a bare `PdsFile`, `split_basename` returns
without error, `basename_is_label` and `sort_basenames` raise `AttributeError` on
their subclass-only attributes, and `associated_abspaths` raises `TypeError` at
the `ASSOCIATIONS` lookup — and it **md5-checked the saved diff against a live
`git diff`** before reviewing it.

It states plainly what it did not do: it did not re-derive §9's 224-context
coverage table, because re-running the suite is outside a reviewer's mandate; it
checked the cheap falsifiable parts of it instead.

## Major

**None.**

## Minor — all four accepted, none rebutted

| # | Finding | Measured | Fix |
|---|---|---|---|
| 1 | §6 cites seven line numbers that are stale at HEAD — `_sorting.py:257`/`:333` and `_associations.py:77,82,109,131,158` | measured `_sorting.py:260`/`:336` and `_associations.py:79,84,111,133,160`, every one off by exactly the +3/+2 the rounds-1-and-2 docstring fixes added. `_sorting.py:257` now lands on `if self.basename not in basenames:`; `_associations.py:158` on a comment | the line numbers are **removed**, not corrected, and the callers named instead — which is exactly what round 2's own Minor 7 did one section up, and the same rule now covers §6. A parenthetical says why |
| 2 | §16 is missing the round-2 row although `critiques/pr-20/round-2.md` is committed in the same diff | the record exists and §3 of the same file already cites "round 2's Minor-1 and Minor-6 fixes", so the section contradicted the rest of the file: a reader saw a one-round loop with 8 findings where there were two rounds and 15 | round-2 row added, with its account. This is the second time §16 lagged its own rule; it is now written as part of the same commit as each round's record |
| 3 | `_AssociationsMixin`'s corrected paragraph is still inaccurate in shipped source: "raises TypeError on **the line above**", and "**neither** method … **they** have always behaved" with only one method named | the `ASSOCIATIONS` read is at `:155` and the `IDX_EXT` read at `:168` — thirteen lines and several statements apart, including a call to `cls.abspaths_for_logicals`; and the paragraph names exactly one method, so "neither"/"they" have no antecedent (leftover from the pre-round-2 text, which named two) | rewritten: "raises `TypeError` earlier, at the `ASSOCIATIONS` lookup, and never reaches `IDX_EXT`", with the closing clause singular |
| 4 | **deferred entry 57's bounding measurement is too weak and would steer the owner wrong** | the entry said "neither token is the current limited testing copy's root … stale history rather than a live leak", which holds only under literal string equality. Measured: `os.path.dirname()` of **both** `PDS3_HOLDINGS_DIR` and `PDS4_HOLDINGS_DIR` **equals** the committed token, and each root is that token plus exactly **one** further component. So the archived plan does disclose the location §3.4 calls confidential, one obvious component short of exact | entry 57 rewritten with the stronger measurement, "stale history rather than a live leak" removed, and the owner line changed from "unassigned" to **the repo owner**, as an item needing a decision. Still not fixed here: it is outside PR-20's diff and pre-existing |

Minor 3 touches `src/pdsfile/`, so §6.6 step 5 applies again: the full-data record
is **regenerated** before round 4.

## Deferred

- **D1** — the archived-plan scrub behind entry 57 should be prioritised as an
  actual confidentiality fix rather than filed as hygiene. **Folded into entry 57
  itself** by Minor 4's rewrite rather than given a number, because it is the same
  item at a corrected severity.
- **D2** — a confirmation, explicitly not a new item: nothing pins
  `PdsFile.__bases__[0]`, which this PR changes, while `_index_rows.py:254` reads
  it and `tests/api/test_mixin_collisions.py:72` asserts only `__bases__[-1]`. The
  reviewer confirmed the record's 34-class shape dump shows the sniff's verdict
  unchanged for every class, and that **deferred entry 49 already owns the
  fragility**, so no new entry is needed. Nothing to do.
- **D3** — a confirmation of entries 55 and 56. The reviewer independently
  reproduced the falsifiable half: `sort_sibnames`, `sort_siblings`,
  `associated_logical_paths` and `associated_pdsfiles` have **zero** call sites in
  `tests/` (every grep hit is an `api_manifest.json` entry) and 7 + 1 call sites in
  rms-viewmaster. Nothing to do.

## Findings the reviewer considered and rejected as invalid

It listed them, which is worth recording because it is the discipline §6.6's
anti-thrash rules ask for: the alphabetical base order versus the Phase-5
preamble's stale illustration; the three-blocks-into-two mapping and
`_sorting.py`'s name (settled by the coordinator — it checked the *execution* and
the *documentation* of the mapping instead, and both hold, including that the
dependency is one-way: 3 `cls.` sites associations→sorting and 0 back); deferred
entries 53 and 54 not being taken up; and commit `48b0605` as scope creep — it is
the "comment left describing a section that moved away" fix, and §2's granularity
rule is why it is its own commit.
