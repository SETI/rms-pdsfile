# PR-15 — adversarial review round 1

**Date:** 2026-07-26
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 2), given only
the PR-15 section of the plan, the Phase-5 preamble, §2 ground rules, §6.1/§6.2,
the §6.6 rules including the progressive `.cursor/rules` schedule, the exact
`git diff origin/rewrite...HEAD`, and read access to the repo at HEAD and to the
real holdings.
**Diff reviewed:** `origin/rewrite`(`807956a`)`...HEAD`(`7c20a73`)
**Verdict: goal met** — 0 Major, 3 Minor, 3 Deferred (all three already recorded
by the PR).

## What the reviewer independently re-ran

Not a paper review: the reviewer reproduced the gate evidence rather than
reading it off the record.

| Check | Reviewer's result |
|---|---|
| `tests/core` at `b646aee` (tests-only commit, fresh worktree) | 20 failed / 13 passed, and each failure traced to the right defect's own error |
| `tests/core` at `a6496f8` | 33 passed |
| ns baseline invocation, `807956a` vs HEAD, junit sets diffed | 824 ids each, 0 only-base, 0 only-head |
| `--mode s`, `807956a` vs HEAD | 558 ids each, empty diff |
| ns driver invocation on HEAD | 857 ids, 33 added / 0 removed / 0 changed, all under `tests.core` |
| No-holdings whole-tree run | 57 passed / 800 skipped / 857 collected |
| `dump_public_api.py`, base worktree vs HEAD | byte-identical, 733,876 bytes each |
| Ratchet shrink | each removed code had exactly the instances at the fixed sites |
| State-leak probe (class `__dict__`s + `pdsviewable` globals around a `tests/core` run) | clean, no residue |
| Bug-1 mitigation claim, probed on both trees | confirmed: `description` already flips `volumes` to expiring on the base tree |
| Bug-7 audit | confirmed: no `BaseException` source in the `try` block |

## Findings

### Major

None.

### Minor 1 — the prediction's provenance is unauditable

`critiques/phase5-validation.md` §3c said the prediction was "Recorded at commit
`b646aee`", but `b646aee` contains only `tests/core/*` and the driver script; the
prediction lived only in a machine-local scratchpad, so no later reader could
check it. "reproduced here verbatim in substance" is also self-contradictory.

**Resolution: fixed.** The prediction is committed verbatim as
`critiques/pr-15/prediction.md`, with an honest provenance header (written at
`b646aee`, before any `src/` change; committed later with the rest of the
records, because a record commit cannot precede the thing it records). §3c now
cites that file and no longer claims the text was committed at `b646aee`.

### Minor 2 — §7's "three test ids read html_path" understates the exposure

`html_path` is also reached indirectly through `PdsFile.url` (`pdsfile.py:1797`),
which `pdsviewable.PdsViewable.from_pdsfile` and `exact_archive_url` /
`exact_checksum_url` consume, so the restored write-back fires far more widely
than three test ids. The conclusion is unaffected — the reviewer's own set diff
is empty — but the sentence is inaccurate in the document that serves as gate
evidence.

**Resolution: fixed.** §7 now states the invariant that actually holds (no test
inspects `DictionaryCache` expirations or the trimmable key set, and trimming
cannot fire at these sizes) and describes the indirect reach through `url`
instead of implying the write-back is confined to three tests.

### Minor 3 — `_priority_of_icon_type` misses the open-only key

`src/pdsfile/pdsviewable.py`: the helper probes `ICON_SET_BY_TYPE[icon_type]`
then `[(icon_type, False)]`, never `[(icon_type, True)]`. `load_icons` registers
the bare key only for closed icons, so an icon type whose only file ends in
`_open` is reachable solely under `(name, True)` and would silently score 0 —
including for `iconset_for(..., is_open=True)`, which would then return a
lower-priority set. No shipped icon tree hits this, but it is new code.

**Resolution: fixed.** The helper now falls back to `(icon_type, True)` as a
third probe, and its docstring says which keys it consults. A new regression
test, `test_an_open_only_icon_type_is_still_ranked`, builds an icon set
registered only under `(name, True)` — exactly what `load_icons` produces for an
`_open`-only file — and asserts it wins.

Because this fix touches `src/pdsfile/`, the full-data record was regenerated
before round 2, per §6.6 step 5.

### Deferred (non-blocking)

All three were already recorded by the PR before the review; no new entry was
needed:

- `MemcachedCache.set_multi` applies one key's lifetime to the whole batch —
  entry 25.
- `_recache()` downgrades permanent cache entries to expiring — entry 26. The
  reviewer added a useful consequence: those category keys now enter
  `DictionaryCache.keys`, so a process that ever exceeded `limit + slop`
  (220,000) could evict them, which was previously impossible. Folded into
  entry 26.
- `DictionaryCache.set_multi`'s `pause` is now near-vacuous — entry 24.

## Rebuttals

None. All three Minor findings were accepted and fixed.
