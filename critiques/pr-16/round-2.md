# PR-16 — adversarial review round 2

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 5), given the
same brief as round 1 and explicitly told not to read the round-1 record.
**Diff reviewed:** `origin/pr-15-latent-bug-fixes`(`1a5d85c`)`...HEAD`(`7e44938`)
**Verdict: goal met** — 0 Major, 5 Minor (4 accepted and fixed, 1 rebutted),
3 Deferred.

## What the reviewer independently re-ran

| Check | Reviewer's result |
|---|---|
| Moved block, parent lines 47–247 vs `_path_utils.py` lines 19–219 | identical, `md5 9f41eed24bffb48918ea7f33b96fc386` on both sides |
| **The rest of `pdsfile.py`** — parent :253–6308 vs HEAD :70–6125 | identical, `md5 e0e6fdee5f64ed8ae6135e188149e7f5`; the only other edits are the import block and the deleted region |
| Repo-wide grep for all twelve moved names, every call site resolved | in-package callers via the plain import, external callers (`COVIMS_0xxx.py:6`, `test_pds3file_blackbox.py:4-6`, `pdsfile_test_helper.py:8`) via the re-export |
| `pdsfile.pdsfile.X is pdsfile._path_utils.X`; `sorted(vars(pdsfile.pdsfile))` | same objects for all twelve; 45 names, identical to the parent's list |
| The sweep, re-derived | `_GLOB_CACHE_SIZE` reachable only through the decorator argument and correctly moved; `PATH_EXISTS_CACHE_SIZE`'s only consumer stayed; `HAS_PYLIBMC` referenced by no moved symbol; `_path_utils.py` stdlib-only, no cycle |
| `dump_public_api.py` on a parent worktree and on HEAD | 733,876 bytes each, byte-identical; the delta vs the committed manifest is confined to §6.1 forgiveness category (2) and is **identical on both sides**, so it is pre-existing |
| The four prohibited files | untouched (numstat) |
| Full-data evidence: junit timestamps vs `37d4246`; its own reduction of the four XMLs | all four runs postdate the last `src/pdsfile/` change; parent-ns 825/34/859 = head-ns, parent-s 555/3/558 = head-s, **both diffs empty id-by-id**, and its recomputation matches the committed `.set` files |
| That the comparison is not vacuous | probed that the baseline worktree at `1a5d85c` imports `<worktree>/src/pdsfile/pdsfile.py`, not the editable install |
| Ratchet, per code, under the project config | E701 16 → 14+2, F841 7 → 6+1; `_path_utils.py` triggers exactly those two; `pdsfile.py`'s 23 codes all still triggered, so its entry could not shrink; no inline `noqa` in the diff |
| Holdings-free run; `pytest tests/core/ tests/api/` | 59 passed / 800 skipped; 36 passed |
| Sub-plan precedence (§6.4 step 1) | `e955a22` 00:45:52 precedes the code commit `a5d2321` 00:54:38 |
| Confidentiality — the values of `$PDS3_HOLDINGS_DIR` / `$PDS4_HOLDINGS_DIR` and their distinctive path components, grepped against every file this PR adds | clean, no literal root anywhere |
| The round-1 test fix | `abspath_for_logical_path.__globals__` **is** `_path_utils.__dict__`; `monkeypatch.setitem` restores it; the removed import has no remaining references |

## Findings

### Major

**None.**

### Minor 1 — §11 of the validation record was an empty heading

**Accepted and fixed:** the round table is filled, in the shape PR-15's §12 uses,
with the regeneration note and the one rebuttal.

### Minor 2 — a stale line count

`critiques/phase5-validation.md` said "`pdsfile.py`: 6,308 → 6,122 lines". 6,122
was right at `3df19d9`; the round-1 fix added three lines. The reviewer noted
that every other figure in the section re-measured correctly.

**Accepted and fixed:** 6,308 → **6,125**, re-measured.

### Minor 3 — the sub-plan contradicts the delivered code in four places

`plans/2026-07-27-pr-16-subplan.md` still said `_GLOB_CACHE_SIZE` is "not
re-exported", that the extraction commit is "the only commit that touches
`src/pdsfile/`", that "nothing else in the PR touches `src/`", and that the PR
has "no test change" — all made false by the round-1 fix.

**Accepted and fixed by appending an "as executed" section (§8) rather than
editing §1–§7.** The sub-plan's purpose under §6.4 is to be the thing that was
decided *before* the mechanical work; silently rewriting it to match the outcome
would destroy exactly the evidence it exists to provide. §8 lists each divergence
and why it happened.

### Minor 4 — the sub-plan's verification check 9 is unsatisfiable as worded

"`import pdsfile._path_utils` as the first pdsfile import → imports without
touching `pdsfile.pdsfile`" cannot hold: importing any submodule runs
`pdsfile/__init__.py`, which star-imports `.pds3file`, which imports
`pdsfile.pdsfile`. The reviewer measured `'pdsfile.pdsfile' in sys.modules` as
True and correctly noted that nothing false was *recorded* — the validation
record never claims check 9's result, and states instead what was actually
verified.

**Accepted and fixed** in the same §8: the check is restated as "`_path_utils`'s
module-level imports are stdlib-only and it contains no
`from pdsfile.pdsfile import`", which is what §5 of the record verifies by
parsing the module. A fifth item was added in the same pass: §5 of the sub-plan
gave the ruff command without `--line-length 100`, the same imprecision round 1
found in the record.

### Minor 5 — "the PR does not exist yet" — **rebutted**

The reviewer observed that `pr-16-path-utils` is unpushed and no PR exists, so
`pull_request.mdc` compliance and the description's path-cleanliness cannot be
verified.

**Rebuttal:** this is the plan's own sequencing, not an omission. §6.6 states
that the loop runs *before* the PR is opened — "Termination — the loop ends when
a fresh reviewer returns zero Major findings and no *new, un-rebutted* Minor
findings (verdict `goal met`). **Then open the PR.**" A reviewer therefore cannot
see the PR description at review time by construction, in this PR or any other.
Acting on the finding would mean opening the PR before the loop converges, which
inverts the protocol. The substance the reviewer could check — that no absolute
holdings path appears in any committed file — it did check, and found clean; the
description reuses those same committed figures and names the holdings roots only
by their environment variables.

Recorded rather than actioned. Per §6.6's anti-thrash rules a re-raised Minor
that was reasonably rebutted does not escalate.

## Deferred (recorded, not fixed)

| # | Item |
|---|---|
| 31 | `src/pdsfile/__init__.py:10`'s `from pdsfile import *` is a self-import that binds nothing. Reproduced in a throwaway package. Not simply fixable — deleting it and correcting it to `from .pdsfile import *` are both public-surface changes, one shrinking and one growing. Owner: PR-24 |
| 32 | The commented-out `#     joined = _clean_join(a,b)…` line rode along in the byte-for-byte move. PR-22's dead-code line list was drawn against `pdsfile.py` and must be rebuilt against the post-Phase-5 module set. Owner: PR-22 |

The reviewer also independently reproduced deferred entry 30
(`repair_case('/', Pds3File)` → `UnboundLocalError`) and agreed entries 29 and 30
are correctly scoped.

## Regeneration

This round's fixes touched only `plans/` and `critiques/`. Under §6.6 step 5 that
does not stale the full-data record, so the runs recorded in
`critiques/phase5-validation.md` §3 — generated after `37d4246`, both trees, both
modes, both diffs empty — carry forward unchanged to round 3.
