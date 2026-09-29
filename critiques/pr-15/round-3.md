# PR-15 — adversarial review round 3 (scoped re-review)

**Date:** 2026-07-27
**Reviewer:** a third fresh, no-context opus-class subagent, with no knowledge of
rounds 1 and 2 beyond the two round records it was told to verify against the
tree. Scope per §6.6's anti-thrash rule: confirm the prior rounds' findings are
genuinely resolved, and raise only **new Major** findings.
**Diff reviewed:** `origin/rewrite`(`807956a`)`...HEAD`(`88f2f71`)
**Verdict: goal met** — 0 new Major, 4 new Minor, 1 new Deferred.

## Confirmation of the prior rounds

The reviewer checked all eight earlier findings against the code rather than
against the round records, and found **all eight genuinely resolved**. Two
confirmations are worth keeping:

- It re-derived the round-1 version of `_priority_of_icon_type` by hand and
  confirmed that the current test fails against it — specifically that the
  test's second assertion (`is_open=False`) raises `KeyError` on
  `('PDSINFO', False)`. So the round-2 replacement is pinned by a test that
  provably fails against **both** earlier helpers.
- It checked the chosen semantics against the only real consumer: rms-viewmaster
  ranks icons in `pdsgroup.py` off the priority recorded on the loaded
  `PdsViewSet`, which is the same source `_priority_of_icon_type` now reads.

## Gates, reproduced independently

The reviewer ran the driver's `--mode ns` invocation itself and got a junit set
**byte-identical** to the recorded one (859 ids after this round's addition; 858
at the time it ran), confirmed the last `src/pdsfile/` commit predates the
recorded runs, reproduced 59/800 with no holdings, the 733,876-byte manifest,
the ratchet shrink on both trees, zero `noqa` anywhere in `src/` or `tests/`,
and the round-1 reviewer's independently produced baseline set matching the
recorded one byte for byte.

It also tried and failed to break five specific things: `_HOLDINGS_ENV` reaching
a class that lacks it; deferred entry 23's `DictionaryCache(lifetime=0)` trap
firing through the newly live `html_path` write-back (all three construction
sites pass a lifetime *function*); `resume_caching(cls)` unbalancing the pause
counter; `tests/core` leaking class state into later suites; and a consumer
supplying the missing `ICON_FILENAME_VS_TYPE` at runtime.

## New findings

### Major

None.

### Minor 1 — "no caller anywhere in `src/`" is false for bug 2

`critiques/phase5-validation.md` §3c and `critiques/pr-15/prediction.md` both
say bugs "2, 4, 5 and 6 have no caller anywhere in `src/` or `tests/`" and then,
in the next clause, name bug 2's caller. `get_permanent_values` **is** called
from `preload` (`pdsfile.py:945`), unguarded, whenever `MEMCACHE_PORT` is
non-zero and the holdings are already cached — so on a memcached deployment
`preload()` raised `TypeError` out of its own `finally` every time it found the
cache warm. Bug 2 is not dead code in production.

**Resolution: fixed, by correction rather than edit.** The prediction file is a
historical record and is left verbatim; §3c now carries an explicit correction
paragraph stating what is wrong, what bug 2's real production reach is, and why
the gate conclusion is unaffected (the suite never sets `MEMCACHE_PORT`). The PR
description says the same rather than repeating the plan's "genuinely dead"
framing for bug 2.

### Minor 2 — §11 listed only four of the six deferred entries

Entries 27 and 28 were added in round 2 and appeared only in §12's narrative.

**Resolution: fixed.** §11 is now a two-part table covering 23–26 (found while
fixing) and 27–28 (found by the review loop), and it carries the entry-15/20
count caveat that `deferred-observations.md`'s own preamble gained in round 2.

### Minor 3 — entry 15's new arithmetic was wrong

The annotation said the ~291 surplus "shrinks by the same 34". It does not: the
315-passed figure was measured on the pre-PR-15 tree, and a re-run of the
forced-marker experiment would collect the 34 new tests among its passes too, so
the surplus stays 291.

**Resolution: fixed.** Entry 15 now says the surplus stays 291 and the
observation is unchanged.

### Minor 4 — two `pytest.raises` without an assertion on the message

`python_testing.mdc` §7 is in force and requires asserting message content. The
weaker of the two was material: `abspath_for_logical_path` has a second
`ValueError` ("No holdings directory for logical path"), so the
not-a-logical-path test would still have passed if the category guard were
removed entirely.

**Resolution: fixed.** The category-guard test uses
`match='Not a logical path'`. The interrupt test asserts something stronger than
a message: `raised.value is exception`, i.e. the exact object propagated rather
than a lookalike raised on the way out of the handler.

### Deferred → promoted to a test

The reviewer noted, as a non-blocking observation, that with `PDS3_HOLDINGS_DIR`
set and `PDS4_HOLDINGS_DIR` unset, `Pds4File` used to resolve into the PDS3 root
and now falls through to the MacOS-website glob and raises — the intended
consequence of bug 3, but stated nowhere and untested.

**Resolution: pinned rather than deferred**, because it is the core of bug 3's
enumerated behavior change rather than a new issue.
`test_a_class_does_not_borrow_another_class_holdings_root` sets only the PDS3
root, stubs the website glob so the test does not depend on what the host
happens to have, and asserts the `ValueError`. It was confirmed to fail against
the base tree, where the PDS4 path silently resolved into the PDS3 root.

## Effect on the record

This round's changes touch `tests/` and `critiques/` only — **no file under
`src/pdsfile/`** — so under §6.6 step 5 the full-data record carries forward.
The recorded counts were nevertheless regenerated, because the new test changes
the *set*: ns 824→825 passed (858→859 ids), no-holdings 58→59. The movers check
is unaffected and still empty in both modes.

## Rebuttals

None. All four Minor findings were accepted and fixed; the Deferred item was
accepted and pinned by a test instead of being deferred.
