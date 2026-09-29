# PR-15 — adversarial review round 4 (scoped, terminating)

**Date:** 2026-07-27
**Reviewer:** a fourth fresh, no-context opus-class subagent. Scope per §6.6's
hard cap: confirm the three earlier rounds' findings are resolved, and raise
**only new Major** findings.
**Diff reviewed:** `origin/rewrite`(`807956a`)`...HEAD`(`eacec4a`)
**Verdict: goal met** — **0 new Major.** The loop terminates here.

## Confirmation of the prior rounds

**All twelve findings from rounds 1–3 confirmed resolved against the tree**, not
against the records. Two verifications worth keeping:

- The reviewer re-derived the movers question independently for the modules most
  exposed to bug 1 — `test_pds3file_whitebox.py`, `test_pds3file_blackbox_cached.py`
  and `test_pdsviewable_blackbox.py` — running them against real holdings on both
  `807956a` and HEAD: 204 ids each side, junit outcome sets **identical**.
- It confirmed `UNKNOWN` is the unique priority-0 entry in `REQUIRED_ICONS`, so
  `_priority_of_icon_type`'s `return 0` fallback means exactly "no better than
  `UNKNOWN`" — the semantics `iconset_for` starts from.

## Gates, reproduced independently for the fourth time

`pytest tests/core` 35 passed; red-then-green reproduced in a throwaway worktree
(`b646aee` 20 failed / 13 passed, `a6496f8` 33 passed); collect-only on all three
driver invocations giving 824 / 859 / 558 ids exactly as recorded; no-holdings
59 passed / 800 skipped / 859 collected; the API dump 733,876 bytes with neither
new private name present and all four §6.4-prohibited files untouched; the
ratchet shrink re-verified with `ruff --isolated --select` and zero `noqa`
anywhere in `src/` or `tests/`; record freshness checked against
`git log --name-only` (last `src/pdsfile/` commit `4fdadb0`, counts regenerated
at `eacec4a`).

It also re-audited the source diff itself: `DictionaryCache.set()` genuinely has
no `pause` parameter, `MemcachedCache.get_multi` genuinely returns a dict,
`resume_caching(cls)` matches `pause_caching(cls)` and `resume()` is guarded
against going negative, every caller of `abspath_for_logical_path` passes a
`PdsFile` subclass, and `shelf_path_and_key_for_abspath` raises only `Exception`
subclasses.

## New Major

**None.** In the reviewer's words: the behavior-affecting fix is bounded exactly
as claimed, the six dead-path fixes are minimal and correct, and the evidence
record is real rather than asserted.

## Non-blocking items, all resolved anyway

1. **Three prose figures lagged round 3's 35th test.** §3c said the final
   numbers were "one higher (824/34, 858 ids; 58/800)"; deferred entry 15 said
   "24 to 58 … 34 tests"; entry 20 said "858 after PR-15". The headline gate
   numbers in §2, §3b and §4 were all correct — only the narrative asides were
   stale. **Fixed:** two higher (825/34, 859 ids; 59/800), 24 to 59 with 35
   tests, and 859.
2. **The website-glob stub reached further than it needed to.** The new test
   patched `pdsfile_module.glob.glob`, i.e. an attribute of the standard
   library's own `glob` module, for the duration of the test. **Fixed:** it now
   replaces the `glob` name in `pdsfile.pdsfile`'s namespace with a
   `SimpleNamespace`, so the stub cannot reach anything outside the module under
   test. The test id is unchanged, so no recorded set moves.
3. **Deferred entry 24's headline read as a regression.** **Fixed:** it now says
   the `pause` parameter "has never suppressed the per-key trim, and still does
   not", which is what its body always said.
4. **No PR was open yet.** That is the next step, and this record is what its
   description is written from.

None of these touched `src/pdsfile/`, so under §6.6 step 5 the full-data record
carries forward unchanged; `pytest tests/core` and `ruff check` were re-run after
the edits.

## Loop outcome

| Round | Major | Minor | Rebuttals |
|---|---|---|---|
| 1 | 0 | 3, all fixed | none |
| 2 | 0 | 5, all fixed | none |
| 3 | 0 new | 4, all fixed | none |
| 4 | **0 new** | 4 non-blocking, all fixed | none |

Four rounds, four independent reviewers, **no Major finding at any round and no
finding rebutted**. §6.6's termination condition — a fresh reviewer returning
zero Major and no new un-rebutted Minor — is met, within the four-round cap.
