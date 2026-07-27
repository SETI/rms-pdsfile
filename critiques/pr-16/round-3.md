# PR-16 — adversarial review round 3

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 5), told not to
read the earlier round records and told that the branch is deliberately unpushed
because the loop precedes opening the PR.
**Diff reviewed:** `origin/pr-15-latent-bug-fixes`(`1a5d85c`)`...HEAD`(`ded2adb`)
**Verdict: goal met** — 0 Major, 6 Minor (all accepted and fixed, none rebutted),
2 Deferred.

## What the reviewer independently re-ran

| Check | Reviewer's result |
|---|---|
| Byte-for-byte, per definition and as one blob | 12/12 identical; the contiguous run identical as a single 6,562-byte blob |
| **`pdsfile.py` now has zero module-level functions**, and the parent had exactly the ten that moved | nothing left behind, nothing extra taken |
| The sweep, re-derived | matches the record's table exactly; no module-level class referenced, so no deferred import needed; `PATH_EXISTS_CACHE_SIZE` genuinely unreferenced by the moved code |
| Every reference, including the **consumer repos** | `rms-viewmaster/viewmaster/pdsiterator.py:104` uses `pdsfile.pdsfile.repair_case`; nothing in `rms-opus` or `rms-viewmaster` *rebinds* any moved name, so the re-export suffices |
| The round-1 test fix, reproduced with `glob.glob` forced to return a hit | old site → resolves (test would fail on a MacOS install); new site → `ValueError` |
| `dump_public_api.py`, `git archive` of the parent vs HEAD | byte-identical, 733,876 bytes each; `sorted(vars(pdsfile.pdsfile))` 45 names, set-identical; the only delta anywhere is each moved symbol's `__module__`, which the manifest does not record; `PdsFile.__module__` still `pdsfile.pdsfile` |
| Ratchet, per code, plus an independent `--config 'lint.per-file-ignores = {}'` run | `pdsfile.py` still triggers all 23 codes; `_path_utils.py` exactly 3 errors, all E701/F841; no `noqa` added; `gen_ruff_ratchet.py` only prints, so the hand-written comment in the block is safe |
| Full-data evidence: its own reduction of the four junit XMLs | byte-identical to the committed `.set` files; both diffs empty; counts match PR-15 §3b, i.e. the correct baseline |
| Provenance: `parent-ns.log` `rootdir`, the worktree's detached head, and `coverage.CoverageData.measured_files()` on both `.coverage` files | baseline measured `<worktree>/src/pdsfile/pdsfile.py` with **no** `_path_utils.py`; head measured both |
| No-holdings run; `tests/api/ tests/core/` | 59 passed / 800 skipped; 36 passed |
| `critiques/phase5-validation.md` is **append-only** (0 removed lines) | no baseline record was edited |
| LF, no CR, no trailing whitespace, `git diff --check`; packaging | clean |
| Deferred entry 30 | reproduced |

## Findings

### Major

**None.**

### Minor 1 — the record undercounted this PR's deferred entries

§10 said "Two new entries" and listed 29–30; the file had gained four (29–32),
and §11's own round-2 row said "2 new entries", contradicting it. The preamble of
the PR-16 section in `deferred-observations.md` still opened with "**Both**
raised by…".

**Accepted and fixed:** §10 is now a four-row table with a "raised in" and an
"owner" column, and the observations file's preamble covers all four and says
which round raised each.

### Minor 2 — the round-1 row's counts did not sum

"1 Major, 4 Minor, 2 Deferred — all **nine** accepted and fixed." 1 + 4 + 2 = 7,
and the Deferred pair is by definition not "fixed".

**Accepted and fixed:** "the Major and all four Minor accepted and fixed, none
rebutted" — which is what happened.

### Minor 3 — two wrong section cross-references

The §2 gate table's ruff row pointed at §5; the ratchet evidence is §7. The API
section's "See §5" for the F401/redundant-alias evidence should be §6.

**Accepted and fixed.**

### Minor 4 — the sub-plan's §8 header said "Four" and listed five

**Accepted and fixed:** "Five".

### Minor 5 — a committed record named distinctive components of the real holdings root

While describing the confidentiality grep, `critiques/pr-16/round-2.md:26` spelled
out a two-component absolute prefix of the real holdings roots and one further
distinctive path segment — the kind of fragment §3.4 says must appear in no
committed file, in a file category §3.4 names explicitly. No complete root
appeared anywhere, so this was a partial leak, which is why the reviewer
classified it Minor.

**Accepted and fixed:** the row now describes what was grepped by naming
`$PDS3_HOLDINGS_DIR` / `$PDS4_HOLDINGS_DIR` and "their distinctive path
components", quoting no literal.

**Round 4 caught that this write-up originally reintroduced the same three
literals in the course of describing them, so the fix is stated here without
them.** The check is now mechanical rather than a claim: a scan of every tracked
file for any run of two or more consecutive components of either real root
reports **no file this PR adds or modifies**. It does report six pre-existing
files that this PR does not touch; those are recorded as deferred entry 34 rather
than cleaned up here, since fixing them is outside this PR's goal.

### Minor 6 — the new module's header described contents it does not have

`src/pdsfile/_path_utils.py:3` said "Module-level path helpers shared by the
PdsFile classes", but two of the ten symbols are not path helpers:
`construct_category_list` builds the category-name cross-product and
`formatted_file_size` formats a byte count. The module *name* is plan-mandated
and is not a finding; the header sentence was the executor's, and was checkably
false.

**Accepted and fixed:** "Module-level path helpers and small support functions
shared by the PdsFile classes."

## Deferred (recorded, not fixed)

- **Extend entry 29 to module-level *data*, not just modules.** `FILE_BYTE_UNITS`
  is re-exported by `pdsfile.pdsfile` but read by `formatted_file_size` through
  `_path_utils`'s globals, so an in-place mutation still works while a *rebind* of
  `pdsfile.pdsfile.FILE_BYTE_UNITS` is now silently inert. Measured: no consumer
  does either, so nothing is broken. **Folded into entry 29** as an explicit
  extension, because PR-17 moves `PATH_EXISTS_CACHE_SIZE` into the same shape.
- **Commit `37d4246` carries three logical changes under one `fix:` subject** —
  the test stub site, the `_GLOB_CACHE_SIZE` re-export, and three comment
  rewordings. The reviewer noted it does **not** violate the plan's binding rule
  (the move commit `a5d2321` is clean of content edits, which is the rule §2
  states), that the commit body discloses all three, and raised it only so the
  pattern is visible for PR-17. Left as it stands: the branch's commit hashes are
  cited throughout the validation record and the round records, and rewriting
  history to split a disclosed round-1 fix would invalidate that evidence for a
  cosmetic gain. Carried into PR-17 as a discipline note.

## Rebuttals

**None.** All six findings were accepted and fixed.

## Regeneration

Minor 6 touched `src/pdsfile/_path_utils.py` — a comment line — so under §6.6
step 5 the full-data record was regenerated before round 4 rather than carried
forward. Only the **head** side was re-run: the baseline tree is a detached
worktree at `1a5d85c` that no round has touched, so its recorded set stands, and
re-running it would measure the same unchanged tree. Both set diffs are still
empty; the API dump is still byte-identical; `ruff` is clean.
