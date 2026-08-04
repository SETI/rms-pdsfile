# PR-24 — adversarial review round 3

**Date:** 2026-08-04
**Reviewer:** a fresh, no-context opus-class subagent, per plan §6.6 and
`critiques/pr-24/topology.md`. It received rounds 1 and 2's records so it could
audit whether those findings were resolved.
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `629dba2`.
**Verdict returned:** **`goal not met`** — **1 Major**, 6 Minor, 1 Deferred. The
Major is a stale section of the evidence record; five of the six Minors are
records; one is code; one Minor is **rebutted with a measurement**.

## What the reviewer re-derived rather than read

`ruff check` clean over 139 of the 140 `.py` on disk — the one skipped is the
gitignored `_version.py` — with `RUFF_TARGETS` in `run-all-checks.sh:404`
confirmed identical, so the gate is not vacuous. 2,760 / 483 / 2,277 re-derived
exactly; §5 sums to 2,277 and §6 to 483; **every base line citation in §5 checked
against the base worktree**. Ratchet: 0 widens, 0 new keys, 0 stale entries at
HEAD, 0 uncovered violations, and no per-(file, code) count increased. The
round-2 `UP031` correction re-measured by AST and confirmed: 46 + 24 + 51 + 12 +
6 = 139. `re_validate.py` byte-identical to `origin/rewrite`. Manifest dumps
byte-identical at 733,876 bytes. Id sets 892/892 and 558/558, 0/0/0. The 339
changed executable lines and the 73 / 107 executed reproduced. No-holdings 92 /
800. Consumer check A 4/4.

It also confirmed the record is **not** stale in the way a naive check would
suggest: the head run's junit files are timestamped 12:51–12:54 and the last edit
under `src/`+`tests/` is 12:44–12:45 by file mtime; the commit carrying those
edits is dated 13:14, so a commit-timestamp check alone would misread it.

## Major

**M1 — `critiques/phase5-validation.md` §3 was not regenerated after round 1's
`re_validate.py` revert.**

Three defects, all in the one section that carries the evidence for the rewrites
the suite does not reach:

- its opening sentence still said "**53** tool lines and all of `re_validate.py`
  are unreached". The measured figure is **30**, stated correctly four lines
  earlier in the same document; 53 is exactly 30 + the 23 `re_validate.py` lines
  round 1 removed from the PR, and after the revert that file is not in the diff
  at all;
- the probe table still listed a `RUF051` row and a `UP034` row. Both codes have
  exactly one site in scope, both in `re_validate.py`, and both **survive** in
  the restored ten-code entry — so neither rewrite is in this PR;
- the headline therefore counted 15 checks when only 13 bear on the diff.

§10 of the same file asserts "the figures in §2–§8 above are the regenerated
ones", which was false of §3.

**Resolved — fixed, not rebutted.** The intro now reads 30; the two vestigial
rows are removed and the count restated as **13 checks, 13 agree**, with a
sentence saying the probe script still carries the `RUF051` and `UP034` checks
and why they are not counted. The reviewer is right that this is the Major class:
§6.6 step 3 names a stale or hand-waved behavior record as exactly that.

## Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | the breakdown of the 30 unreached tool lines enumerated only 26 and omitted the `F541` site; "every one is covered by the probe" was untrue of the 12 rename lines | **fixed**: re-measured — 12 `A001` rename lines, 4 `except` headers, 4 `E701` `return` splits, 3 `SIM102` lines, 3 set literals, 2 `raise OSError`, 1 `with open`, 1 `F541` `logger.info` — and the rename lines are now pointed at the `F821` dangling-name check, which is what actually covers them |
| m2 | `pyproject.toml` still carried round 2's superseded "69 aligned % blocks" — the one file the plan allows this commentary in, and the one a future ratchet shrink reads | **fixed**: 51 aligned / 12 plain `%` / 6 in `re_validate.py` |
| m3 | the new deferred entries mixed base- and head-frame line numbers with no frame stated, and entry 84's `:137` is `:138` at head | **fixed**: the PR-24 block in `deferred-observations.md` now states it is head-frame, entry 83 is reworded to say which frame its base citations are in, entry 84 is `:138`, and sub-plan §11's `:537` is `:535` to match §5's declared base frame |
| m4 | `pdsarchives.py:90` and `pds4archives.py:90` — the `dir` → `dirname` rename pushed the inline comment from column 47 to 51 while its three siblings sit at 48 | **fixed**: both now at 48. Same class as round 1's m1, and invisible to both prior audits — the whitespace audit compares changed-line counts and the bracket scan looks at brackets |
| m5 | `tests/holdings_maintenance/support.py:200` is a live `[*x, y]`, which deviation (4) says is "not wanted anywhere" | **REBUTTED — see below** |
| m6 | `check_runtime_imports.py:62`'s comment gained ", whatever its type", which §4.2's prose rule does not permit | **fixed**: back to `# report every import failure` |

### The rebuttal — m5

Converting `[*HOLDINGS_DIRNAME.values(), 'logs']` to the house
`list(HOLDINGS_DIRNAME.values()) + ['logs']` was tried and **reverted**, because
it is not available to this PR:

```
RUF005 Consider `[*list(HOLDINGS_DIRNAME.values()), 'logs']` instead of concatenation
   --> tests/holdings_maintenance/support.py:200:21
```

The house spelling is precisely what `RUF005` flags, and
`tests/holdings_maintenance/support.py` has **no `per-file-ignores` entry at
`8cab66a`**. Absorbing the new violation would mean creating one — a new entry
that is not a split of an existing one, which §6.4 and the plan's ratchet rule
make a hard stop. So the choice is between leaving the `[*x, y]` and widening the
ratchet, and the ratchet wins.

The finding is still worth something, and its second option is taken: deviation
(4)'s "not wanted **anywhere**" is about ruff's rewrite *of a concatenation*.
Where an author wrote the unpacking form directly and there is no concatenation
to preserve, converting it manufactures a `RUF005` the ratchet cannot hold. That
is now recorded, so the deviation's wording is not read as a claim of fact about
the tree.

## Deferred (non-blocking)

| # | Finding | Recorded as |
|---|---|---|
| d1 | the tool `main()`s now spell the `logger.close()` unpacking three ways; PR-25 will have to pick one when it consolidates the `finally` block | deferred observation **89**. The reviewer said one file uses bare `_`; measurement shows **two** (`pds4archives.py:583` as well as `pds4linkshelf.py:1271`), and the entry records the measured split |

## Re-validation after the round

This round changed `src/pdsfile/holdings_maintenance/pds3/pdsarchives.py`,
`pds4/pds4archives.py` (one comment column each) and
`scripts/check_runtime_imports.py` (one comment). All three are **comment-only**
edits: tokenizing each file before and after with `COMMENT`/`NL` dropped gives
identical token streams, so no executable line changed and `ruff check` is still
clean. The gates were nonetheless re-confirmed rather than assumed — see the
PR-24 section of `critiques/phase5-validation.md`.
