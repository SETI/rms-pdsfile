# PR-33 round 3 — the correction passages, each named by hand

Reviewer: a fresh, no-context subagent given the same plan sections and mandate as
the earlier rounds, the exact diff `git diff 96de70a..c8d5256`, and a hand-written
list of all 26 passages the first two rounds' corrections wrote or rewrote, with the
instruction to check every one against the source and to sample nothing. The round
exists because this phase has measured, on PR after PR, that a correction pass
introduces new defects at about half the rate of the pass it corrects; rounds 1 and
2 of this PR had already reproduced the pattern once (round 2's M1 was inside
round 1's fix).

The reviewer checked all 26 passages, re-verified the five diagrams edge-by-edge
(including testing the version-suffix claim live against `BUNDLESET_PLUS_REGEX_I`
with `COISS_2xxx_v1` and `COISS_2xxx_peer_review`), reproduced the cheap gates
(both Sphinx builds 0 problem lines and 78 of 78; mmdc on all five diagram sources;
`tests/docs`/`tests/api` 30 passed; ruff clean; the greps 0 and 0; the CDN
measurement 71 of 107; record checkers 8 and 27 unmoved; frozen files
byte-identical; register arithmetic consistent), and confirmed every round-1 and
round-2 finding resolved in the pages as they stand.

Verdict: **goal not met** — 1 Major, 2 Minor, 1 Deferred, and the Major is again
inside a correction.

## Major finding, and its resolution

**M1. Correction passage 20 claimed "the parser texts and the log suffix are shared
from ``_archives_common``" — false for the suffix.** The three parser texts are
genuinely defined there; `log_suffix='_archives'` is a string literal written
independently in each spec, and `_archives_common.py` defines no suffix constant.
Equal is not shared-from: a developer building a new pair from that sentence would
look for the suffix in the common module and not find it. Round 1's fix introduced
the clause and round 2's fix corrected the field count in the same sentence without
catching it — the correction-pass pattern holding a third time, now measured three
rounds deep on one sentence. **Fixed**: "the parser texts are shared from
``_archives_common``, the log suffix is the same literal written in each spec".

## Minor findings, and their resolutions

**m1. The CI chapter's opening quantified over every automated job**, but the two
publish workflows run no gate at all. **Fixed**: scoped to the test workflows, with
the publish workflows' role stated.

**m2. "no mixin defines ``__init__`` or any state of its own" (architecture) sat in
tension with the subsystems chapter**, which correctly lists the memoized existence
cache — a `functools.lru_cache` decorating a method in the `_LocalFsMixin` body —
among the class-level mutable state. **Fixed**: "any per-object state of its own",
with the one stateful decorator named and pointed at the chapter that documents it.

## Deferred

**d1. `tests/docs/test_markup.py`'s one-colon-directive list does not include
`mermaid`**, and this PR introduces the repository's first `.. mermaid::` blocks; a
future `.. mermaid:` typo would silently delete a diagram past every gate. Recorded
as **observation 4317** (the fix is one word in the frozenset, out of scope for a
docs-only PR).

## What the reviewer could not verify

The full-data suite runs (evidence checked and coherent, runs not repeated); the
drafting-history claims in the record; the exhaustiveness of the mixin docstrings'
attribute enumerations; the Viewmaster-deployment and runner-environment claims;
`MemcachedCache.delete_multi` against a live pylibmc client.

## Gates after the fixes

The fixes touch three docs pages and the records. `sphinx-build -n -W` over the
corrected tree exits 0 with 0 problem lines and 78 of 78; `tests/docs` passes; the
full-data record carries forward under §6.6 step 5 (no `src/` change at any point
in this PR).
