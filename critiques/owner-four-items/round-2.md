# Owner four-items fix, round 2 — adversarial review

Reviewed: `git diff b8c1ac1..ee89c16` (the four fixes with round 1's
resolutions in). A fresh no-context reviewer — no development context, no
knowledge of round 1 beyond its record for avoiding re-litigation — was given
the owner's instruction, plan §2/§6.1/§6.2/§6.6 with the compliance schedule,
the exact diff and repository read access, with the same central mandates.
No edits by the reviewer.

**Counts.** 1 Major, 2 Minor, 1 Deferred. Verdict: goal not met, solely on
the Major. The reviewer independently verified the regex against every name
`_derived_paths.py` can produce for a PDS4 tree and every consumer's group
indexing, confirmed the freeze surfaces untouched, collected and ran all 36
new test ids, re-counted the register to the equation, and confirmed round
1's four resolutions present in the tree.

---

## Major 1 — round 1's own fix under-measures: git's `**` needs `:(glob)` — FIXED

`pyproject.toml`'s re-measure command, corrected in round 1 to
`git ls-files 'src/pdsfile/**/*.pyi'`, returns 38 files, not 43: git's
default pathspec makes `**/` match only names containing a real slash, so
the five top-level stubs are dropped — among them `pdsfile.pyi`, which holds
23 of the 26 findings the keep-the-exclusion decision rests on. The command
as shipped reports 75 findings, and the record claimed it produced 98.

**Resolution.** Both the comment and the record now use
`git ls-files ':(glob)src/pdsfile/**/*.pyi'`, verified here to return 43
files and reproduce exactly 98 findings with the recorded distribution under
both ruff 0.15.7 and 0.15.22; the record states both traps — shell globstar
and git pathspec — and that each was caught by a round measuring the
command rather than reading it. The decision itself was never at risk: even
the 38-file run shows uncovered findings, so the exclusion stays either way.

## Minor 1 — the after-sweep total goes stale with every round — FIXED

The record said 27 files match `3\.10` at head; round 1's own record made it
28, and each further round record quoting the number adds one.

**Resolution.** The after-state sentence now names the sets — the 22
historical records, the two skills files, the plan's self-describing
parentheticals, and this fix's own records including the round records —
and says why it carries no brittle total.

## Minor 2 — a line citation the PR's own edits shifted — FIXED

The record cited `_sorting.py:147,282`; the round-1 comment fix moved
`sort_keys`'s match to 284.

**Resolution.** The record cites the consumers by symbol.

## Deferred — `from_path`'s extension assembly misreads category-suffixed checksum names — RECORDED

`pdsfile.py`'s bundle-set parse concatenates `group(3) + group(4)`, so
`<set>_previews_md5.txt` never sets `checksums_` — identically for PDS3
before this PR and for PDS4 after it, which is the parity the ruling asked
for. Register entry 4066 records it (with 4065 and 4129, the register's
found-during-later-work count moves to 12; **213 open**).

---

This round's fixes touched no file under `src/pdsfile/`, so the round-1
full-data evidence carries forward per §6.6 step 5; the ruff gate alone was
re-run against the changed `pyproject.toml` and is clean.
