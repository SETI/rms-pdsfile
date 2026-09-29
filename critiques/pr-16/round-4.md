# PR-16 — adversarial review round 4 (the scoped re-review)

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent. §6.6 makes the fourth
round a *scoped* re-review — "confirm the prior round's findings are resolved;
raise only **new Major** findings" — so this reviewer, unlike the first three,
was given the three prior round records and asked to check each recorded finding
against the tree rather than trust the record.
**Diff reviewed:** `origin/pr-15-latent-bug-fixes`(`1a5d85c`)`...HEAD`(`8db74f7`)
**Verdict: goal met** — **0 new Major**. 15 of 16 prior findings confirmed
resolved and the one rebuttal confirmed sound; 1 prior Minor found only partly
resolved; 2 non-blocking notes. All three are fixed below.

## What the reviewer re-derived rather than reading off the records

| Check | Reviewer's result |
|---|---|
| Byte-for-byte move, its own AST extraction | 12/12 identical; none of the twelve still defined in `pdsfile.py` |
| **The rest of `pdsfile.py` is untouched** — parent `:249–6308` vs HEAD `:66–6125`, and the header on both | equal `md5` on both sides; the only changed region is the import block, no restyling rode along |
| Nothing left behind, nothing extra taken | parent had exactly ten module-level functions; HEAD `pdsfile.py` has **zero**, one class, and `PATH_EXISTS_CACHE_SIZE`, still consumed |
| The sweep, re-implemented from scratch | reproduces the record exactly, and confirms the decorator pass is load-bearing for `_GLOB_CACHE_SIZE` |
| No cycle | `_path_utils.py`'s module-level imports are five stdlib `Import` nodes and nothing else |
| API freeze — its own dump on a clean worktree at `1a5d85c` and on HEAD | byte-identical, 733,876 bytes each; the four prohibited files untouched |
| **Namespace identity across all seven frozen top modules** | identical on both trees; the only additions to the `pdsfile` package namespace are `_path_utils` (underscore ⇒ skipped by the dumper and by `from pdsfile import *`) and the worktree's `_version` |
| `sorted(vars(pdsfile.pdsfile))` | 45 names each side; all twelve the same objects; `PdsFile.__module__` unchanged |
| Every reference, repo-wide and in both consumer repos | all resolve; **no file anywhere rebinds a moved name on `pdsfile.pdsfile`** |
| Full-data evidence, its own reduction of all four junit XMLs | byte-equal to the committed `.set` files; both diffs empty id-by-id; counts match PR-15 §3b |
| Freshness and provenance | head runs postdate `b86adba`; `rootdir` lines and the worktree's detached, clean `1a5d85c` with no `_path_utils.py` confirm the round-3 decision to re-run only the head side |
| Ratchet code by code, plus an independent `--config 'lint.per-file-ignores = {}'` run | E701 16 → 14+2, F841 7 → 6+1, the other 21 codes unchanged and still triggered; `_path_utils.py` exactly 3 errors, all E701/F841 |
| F401 with ignores cleared | 0 on HEAD `pdsfile.py`; the redundant-alias form is doing the work |
| Round 1's Major fix, reproduced adversarially | only the committed stub site neutralizes the last-resort branch |
| `tests/api/ tests/core/` **with all four holdings env vars unset** | 36 passed — the `holdings_free` promise holds |
| Records are append-only | `phase5-validation.md` and `deferred-observations.md` both 0 removed lines, so PR-15's baseline section is untouched |
| Hygiene, packaging, commit discipline | LF-only, no trailing whitespace, `git diff --check` clean; eight Conventional subjects; the move commit clean of content edits; the sub-plan precedes it |

## New Major findings

**None.** The reviewer's words: "I tried to break this PR on every axis a pure
extraction can fail — a body altered in transit, a symbol left behind or dragged
along, a missed module constant, an import cycle, a lost namespace entry, a
manifest delta, a ratchet grow, a call site or patch site pointing at the vacated
namespace, a vacuous baseline measurement, a stale or self-referential evidence
set — and every one came back clean under my own recomputation."

## Prior findings — 15 of 16 resolved, 1 rebuttal sound, 1 partly resolved

Rounds 1 (Major 1, Minor 2–5), 2 (Minor 1–4) and 3 (Minor 1–4, 6) were each
confirmed resolved **against the tree**, not against the record: the stub site by
re-running the three-way simulation, the PR-number rule by
`grep -rn "PR-[0-9]"` over `src/`, `scripts/` and `pyproject.toml` (no hits), the
line count by re-measuring, the ruff command by running it verbatim and
reproducing every number, the provenance by reading the four `rootdir` lines and
the worktree's SHA, and `_GLOB_CACHE_SIZE` by the 45-name comparison.

Round 2's Minor 5 rebuttal — "the PR does not exist yet" — was confirmed sound
against the plan text: §6.6 terminates the loop and *then* opens the PR, so a
reviewer cannot see the description at review time by construction.

### Round 3's Minor 5 — only partly resolved, now fixed

The offending row in `round-2.md` was correctly reworded, but the same commit
wrote the three literals back into the tree in the sentence that *described* the
finding, in `round-3.md`. The record's own "re-grepped afterwards: the tokens
appear in no file this PR touches" was therefore false as written.

**Accepted and fixed.** `round-3.md`'s Minor 5 is restated without any literal,
and its verification is now a measurement rather than a claim: a scan of every
tracked file for any run of two or more consecutive components of either real
root reports **no file this PR adds or modifies**.

The reviewer's classification of this as Minor rather than Major is recorded and
accepted: no complete root appears anywhere in this PR's files (the longest run
was 2 of 7 components), and the same scan finds **longer** runs already committed
in six pre-existing files this PR does not touch — so this PR is not the
disclosure vector. Those six are now deferred entry 34 rather than cleaned up
here, since §6.6 makes "fix the pre-existing ones too" an invalid finding against
a pure move PR.

## Non-blocking notes — both actioned

1. **A paragraph in §11 of the validation record contradicted its own preamble.**
   It said "later rounds changed only `plans/` and `critiques/` … so the runs in
   §3 carry forward", which stopped being true when round 3 touched
   `_path_utils.py` and §3's head runs were *replaced* rather than carried
   forward. The preamble said so correctly; commit `8db74f7` missed this
   paragraph. **Fixed:** the paragraph now states which of the two regenerations
   §3 records and why the baseline side was not re-run.
2. **`scripts/gen_ruff_ratchet.py` emits an empty block against the current
   tree**, because the committed `per-file-ignores` already suppress every
   violation, so its documented "re-run and confirm the diff only removes codes"
   workflow cannot be exercised without first clearing the table. Pre-existing,
   not this PR's doing, and PR-23/PR-24 both depend on that workflow. **Recorded
   as deferred entry 33.**
3. The commented-out line inside `_clean_join` that rode along in the move is
   already deferred entry 32; the reviewer agreed leaving it is correct in a
   byte-for-byte move.

## Regeneration

This round's fixes touched only `critiques/`. Under §6.6 step 5 that does not
stale the full-data record, so the runs recorded in
`critiques/phase5-validation.md` §3 — regenerated after `b86adba`, both set diffs
empty — stand as the evidence for the PR.

## Termination

§6.6's condition is met: a fresh reviewer returned **zero Major** findings with
verdict `goal met`, inside the four-round cap. No Major was ever rebutted, so
there is nothing to escalate under the anti-thrash rule.
