# PR-17 — adversarial review round 4 (scoped)

**Date:** 2026-07-27
**Reviewer:** a fresh opus-class subagent with no development context and no
knowledge of rounds 1–3.
**Scope:** §6.6's fourth-round form — "confirm the prior round's findings are
resolved; raise only **new Major** findings".
**Diff reviewed:** `origin/pr-16-path-utils...ba64cda`.
**Verdict:** **goal not met** — **1 new Major**, 0 new Minor (3 non-blocking
notes). Of the twelve prior findings it re-checked, **eleven resolved**, one
(R2-1) partly.

## The round-4 cap — read this first

§6.6 sets a **hard cap of 4 rounds** and says: "If a fourth round still finds
issues, stop and bring all round records to the owner (mis-scope signal)."

**The Major was fixed** — §6.6 step 4 requires every Major to be resolved, and
leaving a known, reproduced defect in place is not an option — **and no fifth
round was run.** The cap situation is surfaced to the owner in the PR description
and in this record rather than being worked around. What the owner is being asked
is whether the fix, whose proof is below, is sufficient, or whether a fifth round
is wanted despite the cap.

Two things argue this is not the mis-scope signal the cap is designed to catch:

1. **The loop was converging, not thrashing.** Rounds 1–3 returned 0 Major each,
   with 3 / 6 / 3 Minor, and the reviewer's own summary here reads: "The
   extraction itself is, by every measurement I could make, exactly what the plan
   asked for … and no behavior change I could provoke."
2. **The Major is in a voluntary addition, not in a plan deliverable, and it is a
   regression this executor introduced in round 2.** The plan asks
   `tests/api/test_mixin_collisions.py` for "a simple set-intersection check".
   `test_no_mixin_module_imports_pdsfile_at_module_level` is extra — it was round
   1's *Deferred* item, which this executor chose to take up rather than defer.
   Had it been deferred as that reviewer proposed, this Major would not exist.

## The Major

**The back-import guard stopped catching the exact spelling the plan writes
down**, and the validation record asserted the opposite.

`_modules_named_by` prefixed the importing module's package onto the target even
when `node.level == 0`, so an absolute `from pdsfile.pdsfile import X` resolved to
`pdsfile.pdsfile.pdsfile` and never matched. Round 2 introduced this while fixing
the relative-import hole: it traded coverage rather than adding it. Reproduced
before acting, by evaluating the shipped helper directly:

```
CAUGHT  'import pdsfile.pdsfile'                → ['pdsfile.pdsfile']
CAUGHT  'from . import pdsfile'                 → ['pdsfile', 'pdsfile.pdsfile']
MISSED  'from pdsfile.pdsfile import PdsFile'   → ['pdsfile.pdsfile.pdsfile', …]
```

The reviewer's second half is the part that makes it a Major rather than a nit,
and it corrects a claim this executor had recorded as settled. **Whether an
absolute `from` raises depends on whether the name is already bound, not on the
shape of the statement.** `pdsfile.py` imports the first mixin at its line 60, and
**33** of its module-level names exist by then — measured — including
`repair_case`, `abspath_for_logical_path`, `logical_path_from_abspath`,
`construct_category_list`, `pdscache`, `pdsviewable`, `os`. Any of those, written
as `from pdsfile.pdsfile import <name>` at a mixin module's top level, establishes
exactly the cycle the preamble forbids, **raises nothing**, and left the guard
green. Those 33 names are precisely the helpers PR-18–PR-22's mixins will reach
for, so the miss was aimed at the future PRs the check exists to protect.

The record's §6 compounded it: it stated "only the two that bind a name out of the
partially-initialized module raise", generalising from a two-case sample.

### The fix, and its proof

`level == 0` is treated as already absolute. Nine back-import spellings were then
injected into **each** mixin module in turn and the suite re-run:

| injected | `_shelves` | `_local_fs` |
|---|---|---|
| `import pdsfile.pdsfile` | caught by the check | caught by the check |
| `import pdsfile.pdsfile as _core` | caught by the check | caught by the check |
| `from . import pdsfile as _core` | caught by the check | caught by the check |
| `from pdsfile import pdsfile as _core` | caught by the check | caught by the check |
| `from .pdsfile import repair_case` | caught by the check | caught by the check |
| `from pdsfile.pdsfile import repair_case` | caught by the check | caught by the check |
| `from pdsfile.pdsfile import logical_path_from_abspath` | caught by the check | caught by the check |
| `from .pdsfile import PdsFile` | ImportError at collection | ImportError at collection |
| `from pdsfile.pdsfile import PdsFile` | ImportError at collection | ImportError at collection |

The last two never reach the check in a live run, so the helper was additionally
evaluated directly: it flags **all nine**, and does **not** flag six legitimate
imports (`os`, `pickle`, `bisect`, `from ._path_utils import _clean_glob,
_needs_glob`, `from pdsfile import pdscache`, `from . import pdscache`). The
record's §6 now carries the nine-row table, the 33-name measurement, and the
corrected statement about what decides whether a spelling raises.

## Resolution check on the prior rounds

The reviewer verified each against the code rather than the claim.

| | Finding | Verdict |
|---|---|---|
| R1-a | `_ShelfMixin` docstring attribute list | **resolved** — its AST scan finds 9 read, 9 named; `_LocalFsMixin` 6 and 6 |
| R1-b | sidecar count out of the docstring | **resolved**; and it re-ran the audit: 6,753 sidecars, 0 `Name` nodes, 6,753/6,753 of the recorded shape — the record's figure reproduces |
| R1-c | test rename | **resolved**; no occurrence of the old name survives |
| R1-d | a repeatable back-import check exists | **resolved as to existence**, not as to coverage — the Major |
| R2-1 | back-import spellings | **partly resolved** — the Major |
| R2-2 | the content edit is executed by a test | **resolved** — 8 ids, imports the production symbol, holdings-free, and `tests/core/` was already in the `--mode ns` leg |
| R2-3 | the direct-assignment audit row | **resolved**; it re-derived the enumeration: 20 monkeypatch sites, 0 `unittest.mock`, exactly one direct assignment |
| R2-4 | the eval contract names the locals | **resolved** |
| R2-5 | base order | folded into R3-3 |
| R2-6 | the commit resplit | **resolved and content-neutral** — `git diff 114a5c1 7ca54db` is empty |
| R3-1 | sub-plan "as executed" | **resolved** |
| R3-2 | the two figures | **resolved** — `pytest tests/api/` 15, `_shelves.py` 356, both reproduce |
| R3-3 | base-order addendum | **resolved** |

## Gates the reviewer re-verified independently — all green

Byte-for-byte (13 of 14 identical, the 14th being the authorized `eval`
isolation); no stray name in either new module and no new public name; the four
frozen files untouched and the manifest diff confined to the pre-approved PR-08
forgiveness category; `vars(pdsfile.pdsfile)` 45 → 47 with none lost;
`dir(PdsFile)` 256 → 256, `dir(Pds3File)` 298 → 298, `dir(Pds4File)` 271 → 271,
zero lost and zero gained; the ratchet a conserving split with no over-listing;
the full-data record fresh (head junit 04:03:09 / 04:06:00 after the last source
change `5320d83` at 04:02:58) and its set diff recomputed from the XMLs to the
same 22 additions / 0 removals / 0 outcome changes, `--mode s` empty; no-holdings
59 → 81; coverage provenance; MRO safety including the `__bases__[0]` sniff,
`__subclasses__()`, `super().__init__()` and a pickle round-trip; a live smoke
against real holdings; and its own mutation of the collision tests.

## Non-blocking notes the reviewer raised

Recorded, not actioned — they are explicitly outside the scoped round's verdict.

1. Two **pre-existing** records this PR does not touch (`critiques/pr-08/round-1.md`,
   `critiques/pr-09/round-1.md`) carry the limited copy's path. This is the file
   set deferred entry 34 already owns; nothing new to add.
2. Deferred entry 38 (the `os_path_exists` / `os_path_isdir` fallback asymmetry)
   was independently confirmed to be byte-identical to the parent, so the move
   introduces nothing. Already recorded.
3. `PATH_EXISTS_CACHE_SIZE` is a public name inside a private module —
   freeze-invisible only while `_local_fs` stays underscore-prefixed. That is the
   plan's own arrangement and is correct as delivered.

## Regeneration

The fix touched `tests/api/test_mixin_collisions.py` and `critiques/` only.
**Nothing under `src/pdsfile/` changed**, so under §6.6 step 5 the round-2 record
carries forward: the head runs at 04:03:09 and 04:06:00 still postdate the last
source change (`5320d83`, 04:02:58), and the recorded 22-addition set diff, the
empty `--mode s` diff and the empty manifest diff still describe the tree. The
fix changes no test id — the file's count is unchanged at 14 — which was
re-measured after it.
