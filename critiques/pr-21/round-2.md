# PR-21 — adversarial review round 2

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6), given the same
inputs as round 1 and no knowledge of it: the PR-21 section of the plan, the
Phase-5 preamble and mixin mechanics including the alphabetical base-order rule
and the note that the preamble's illustration on this branch is stale, §2,
§6.1/§6.2/§6.4, the progressive `.cursor/rules` compliance schedule, the exact
diff `git diff origin/pr-20-associations-sorting...HEAD`, and read access to the
repo at HEAD and to the real holdings.
**Diff reviewed:** HEAD `ff2e644` ("docs: record round 1 and replace two figures
with measurements"), 9 files, +2,314 / −522.
**Verdict:** **goal met** — 0 Major, 3 Minor, 0 new Deferred.

## What the reviewer re-derived independently

It re-derived every statically derivable figure in the record from the parent
commit and from HEAD rather than reading them: the 419-line and 77-line moved
blocks byte-for-byte, all five byte totals in §5, all nine stay-list byte counts,
the `vars()` comparison across seven modules plus `dir()` across
`PdsFile`/`Pds3File`/`Pds4File` and all three MROs, the API dump (byte-identical,
same MD5), the whole §8 ratchet table cell by cell, the `symtable` sweep and the
`Name`-load counts, §7's 34-class shape figures, §11's 20 patch sites, §15's
docstring contract in both directions, and every `file:line` citation in the
record. It additionally **ran** the clean-install gate and the no-holdings job
(82 passed / 800 skipped on both sides), imported eight modules first-in-a-fresh-
interpreter, and checked all three code commits for importability, ruff
cleanliness and a green `tests/api`.

Two of its checks are worth naming because this PR's record did not make them:

- it recomputed the **minimal** per-file ruff code set with per-file-ignores
  disabled and confirmed `_preload.py` needs *exactly* its six and `pdsfile.py`
  *exactly* its seventeen;
- it located each of `_preload.py`'s eight suppressed violations by line and
  confirmed **all eight are on moved lines** — none in the new header or the new
  docstring.

It also corroborated §10's control baseline without re-running it: `tests/`
collects 882 ids in `--mode ns`, and §10's subset collects 771 = 737 + 34.

## Major

**None.** The reviewer states it could not construct the "goal not met" case.

## Minor — all three accepted, all three fixed

Every one is record wording; none is in the extracted code. Each was re-measured
by the executor before being fixed, and each measurement reproduced the finding.

### Minor 1 — entry 60 cited the blank line before the banner, not the banner

`critiques/deferred-observations.md` said the banner PR-21 adds is at
`src/pdsfile/pdsfile.py:495`. Measured: line 495 is blank and the banner occupies
**496–498**. **Fixed** to `496–498`.

### Minor 2 — entry 60's width figures were HEAD's while its identifying clause described the parent's

The entry said `pdsfile.py` has "20 banner rule lines at 80 columns and 2 at 90;
the two 90-column ones are `# Set parameters for both Pds3File and Pds4File` and
— until PR-21 — `# Preload management`". Each banner contributes **two** rule
lines, so a two-banner list cannot describe two rule lines. Re-measured:

| tree | 80 | 84 | 90 |
|---|---|---|---|
| `2df25ab:pdsfile.py` | 18 | 2 | **4** |
| HEAD `pdsfile.py` | 20 | 0 | **2** |
| HEAD `_preload.py` | 0 | **2** | **2** |

So the 20/2 pair is HEAD's and correct, but at HEAD both 90-column rule lines are
the *single* `# Set parameters…` banner; the parent had four. The entry also
framed the file as two-width while `_preload.py` carries a third — the 84-column
interior banner inside `preload`, indented eight spaces.

**Fixed:** the entry now carries the three-tree table above and names the
84-column pair.

### Minor 3 — §15's "30 others" was a whole-module count in a mixin-scoped sentence

§15 wrote "`_PreloadMixin`'s PdsFile-side receivers are `cls`, `pdsdir`, `pdsf0`
and `pdsf1`, against 30 others that are strings, lists, dicts, files, …".
Re-measured: scoped to the mixin's five methods — which is what the sentence says
and what the contract covers — there are **31 distinct receiver expressions, 4
PdsFile-side and 27 others**. The figure 30 reproduces only from a walk over the
whole module, and the three extra receivers are `arg`, `arg.interior` and
`arg.interior.lower()` inside `cache_lifetime_for_class`, where **`arg` is a
PdsFile object** — so they are not "strings, lists, dicts, files" either.

This is the one sentence in §15 whose job is to make the scoping checkable, which
is exactly why it is worth fixing. Nothing in §15's substantive result moves: the
reviewer independently re-derived Direction 1 and Direction 2 and got **25 of 25,
zero residue in either direction**, matching the docstring name for name.

**Fixed:** §15 now gives 4 of 31 and 27 others, and states the whole-module figure
and what the three extra receivers are, so the two scopings cannot be confused.

## Deferred

**None new.** The reviewer checked the existing entries against the code and
confirmed each is where it belongs: 29 (the rebinding asymmetry, which §11 acts
on), 31 (`__init__.py`'s self-import), 54 (the hand-written contracts, PR-22), 58
(`pylibmc`'s environment-dependent manifest presence — it independently confirmed
`pdscache.py:7` has its own optional import and that the gate therefore stays red
after this PR), 59 (the preload coverage gaps) and 60 (banner widths).

## Owner decision applied in this round

Not a review finding — an owner ruling delivered by the coordinator on
2026-07-27, while this round was running: **absolute holdings paths in plan and
critique files are not confidential.** Verbatim: "I don't care about absolute
paths in plan or critique files. They aren't confidential."

**Deferred entry 57 is therefore withdrawn.** It is kept rather than deleted —
its measurement is still an accurate record of what was found — and marked closed
by owner decision, with the ruling quoted and the reason no edit to
`plans/archive/2026-07-17-modernization-plan.md` is required. The entry also
records what the ruling does *not* change: `src/`, `tests/` and `.github/` still
resolve holdings roots through `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR`, on
portability grounds rather than confidentiality ones.

Both reviewers checked §3.4 compliance and both found nothing to report, so the
ruling changes no finding in this loop.

## What this round did not change

**No fix in this round touched anything under `src/pdsfile/`.** All three Minor
fixes and the entry-57 withdrawal are in `critiques/phase5-validation.md` and
`critiques/deferred-observations.md`. By §6.6 step 5 the full-data record
therefore **carries forward** without regeneration: the runs at 22:08:52 and
22:10:41 still postdate `a8f4cb3`, which is still the last commit to touch
`src/pdsfile/`.
