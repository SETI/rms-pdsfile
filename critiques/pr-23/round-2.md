# PR-23 — adversarial review round 2

**Date:** 2026-08-03
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 2) — not the
round-1 reviewer, and given no round-1 reasoning beyond the round-1 record itself
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `bba2bc5` (2,420 lines)
**Verdict returned:** **`goal met`** — **0 Major**, 6 Minor, 2 Deferred

Because the round returned new Minors, the loop does **not** terminate here
(§6.6: "zero Major findings *and* no new, un-rebutted Minor findings"). All six
are fixed below and a third round follows.

## What the reviewer reproduced independently

Recorded because it is evidence, not instruction. The reviewer re-derived every
gate from scratch in both worktrees rather than reading the record: `ruff check`
clean; the derived set **154 at base, 33 at head**, matching the enumerated §5
list **including every line number**; the ratchet 14 entries/78 slots → 7/10 with
no code added and no file gained; no inline `noqa` in source; no `# fmt:` guards;
`ENABLE_RUFF_FORMAT` false; **`ruff format --check` reports the same 13 files at
base and at head**, which is the direct evidence that owner decision 3 held; the
API dump byte-identical at 733,876 B with manifest, allowlist, dumper and freeze
test unedited; the §6.2 record timely (last `src/pdsfile/` change `54e9380` at
14:53, artifacts at 14:56/14:57) and its set diff reproducing exactly (892 vs 892,
558 vs 558, zero movement in all three directions); `linecov.py` reproducing
143/81/62 row for row; the differential probe reproducing with `PYTHONPATH` pinned
per tree (it verified the import came from the worktree, not the installed
package — the §9 `pythonpath` trap); the banner commit comment-only; the test id
set unchanged.

It also read all 121 fixes against the code and confirmed the equivalence
arguments, including that the `RUF015` asymmetry is justified rather than an
oversight: all three fixed `pdsviewable` sites are dominated by a non-empty guard,
which is exactly why `pdscache.py:623` could not be fixed the same way.

## Minor

| # | Finding | Resolution |
|---|---|---|
| m1 | **The differential probe does not exercise a single changed line of `pdscache.py`, and §2 said it did.** The `DictionaryCache` round trip goes through `DictionaryCache`'s own `get_multi`/`set_multi`/`__contains__`/`__len__`, which this PR never touched; the renamed loops are `MemcachedCache`'s. And `E721` #3 evaluated `type(v) is str` written *in the probe*, never calling `pdscache`. A false evidence claim in a validation record. | **Fixed, and then some.** §2 is rewritten with measured numbers, and the probe is **extended** to drive `MemcachedCache` directly, borrowing `tests/core/test_pdscache_set_multi.py`'s `__new__`-plus-stub-client technique: `__contains__` ×5, `get_multi`, `get_now`, `unblock` on all five logger/pid combinations, plus `DictionaryCache._trim`'s `F541` message. Probe grows 39 → **55** values; measured under `coverage` it now reaches **36** changed executable lines, **24 of which the suite does not**. Union **105 of 143**; **38** reached by neither, each named by kind. §2 also now records the one `MemcachedCache` region the *suite* does reach — `set_multi`, via that same test. |
| m2 | `24 of the 24` in §10 contradicts entry 72's `28 of the 33`. | **Fixed**, and entry 72 was itself wrong: **28 of the 37** changed lines in `pdscache.py` are inside `MemcachedCache`, and the class is not wholly ungated — `set_multi` has a test. Entry 72 is rewritten. |
| m3 | `Pds3File`/`Pds4File` MRO lengths recorded as 13; they are 12. | **Fixed.** The conclusion ("identical entry for entry") was never in doubt. |
| m4 | The sub-plan's §6 ratchet table still showed `_local_fs.py → SIM103`, contradicting six other places including its own section header. §11 claimed §3–§6 were updated after round 1; §6's prose was, this row was not. | **Fixed.** |
| m5 | `assert PdsFile.__mro__[-1] is object` cannot fail for any Python 3 class — a tautology wearing an `assert`, which §6.6 asks specifically about. | **Fixed.** Replaced by a check that every base's `__module__` starts with `pdsfile._`, which fails both if `object` returns and if any non-mixin base is added. `assert object not in PdsFile.__bases__` stays. |
| m6 | `_preload.py:201`'s bare `cls.CACHE[key]` differs from the `_ = cls.CACHE[…]` idiom the same function uses eighteen lines above. Raised as optional. | **Fixed** rather than rebutted: it is one character, it matches the file, and the `_ =` form is also robust to a future `B018` widening. |

## Deferred (recorded, not fixed)

| # | Finding | Where it went |
|---|---|---|
| d1 | `MemcachedCache.flush`'s `except pylibmc.Error` handler calls `.sort()` on a `dict_keys`, so it fails with a second unrelated error before logging the first. PR-23 edited the two log lines bracketing it and may not repair it (behavior change, and no gate reaches it). | entry **74** |
| d2 | `_opus.py` now spells the same concatenation two ways (`:246` fixed by `RUF005`, `:271` not flagged). | entry **75** |

## Effect on the deliverable

Nothing in the code's behavior changed as a result of this round. m5 and m6 are
the only source edits: a test assertion with teeth replacing a tautology, and a
one-character consistency change. The substantive outcome is that §2's evidence
claim is now true and considerably stronger than it was — the probe covers 24
changed lines the suite never touches, where before it covered none of them.
