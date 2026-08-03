# PR-17 — adversarial review round 3

**Date:** 2026-07-27
**Reviewer:** a fresh opus-class subagent with no development context and no
knowledge of rounds 1–2, per §6.6 step 5. Same inputs, on the updated diff.
**Diff reviewed:** `origin/pr-16-path-utils...69529c3` (12 files, +2,270 / −719).
**Verdict:** **goal met** — 0 Major, 3 Minor, 3 Deferred.

The reviewer re-derived, from its own commands: the byte-for-byte comparison at
HEAD and at the extraction commit; the module-level name sets of both new
modules; `vars(PdsFile)`, `dir()` and `getattr_static` kinds on both sides;
`from pdsfile.pdsfile import *` (32 names, unchanged); the empty manifest diff;
all per-code ratchet triggers; the set-diff arithmetic and coverage provenance;
the no-holdings counts on both sides; the mutation kills for both new test files;
the monkeypatch audit with its own forced-wrong controls; the wheel contents; and
the §3.4 path scan.

Three of its measurements went beyond anything this executor ran, and all three
came back clean:

- **A 140-probe differential against the complete holdings set**, in *both*
  `SHELVES_ONLY` modes, over `os_path_exists` / `os_path_isdir` / `os_listdir` /
  `glob_glob` / `_non_checksum_abspath`, across bundles, bundlesets, archives,
  checksums, checksums-archives, documents, metadata, previews, PDS4 and six glob
  patterns. Parent and head JSON identical; 90 of the 140 probes return
  non-trivial values. That is a stronger behavior check than the suite provides,
  because the suite runs against the limited copy.
- **The sidecar shortcut end to end on the complete set**: `shelf_lookup('info')`
  on a bundle calls `_eval_null_key_record` exactly once and returns a value equal
  to both the `.pickle`'s `''` entry and the parent tree's answer.
- **A `from pdsfile.pdsfile import *` comparison**, which this executor had not
  done — the star-export surface is unchanged at 32 names.

## Findings and resolutions

### Minor

**M1 — the sub-plan promised an "as executed" delta and had none, and three of
its statements had gone stale.** Its own opening cites PR-16's model "including
the 'as executed' delta appended at the end"; the file ended at §9. Meanwhile the
Scope line, §3 step 4 and §8 check 6 all say "one new test file" and the delivery
has two.

**Accepted and fixed.** `plans/2026-07-27-pr-17-subplan.md` now ends with
`## 10. As executed — where the work diverged from §1–§9`, appended rather than
edited in place, naming the second test file and why round 2 added it, the
addendum M3 produced, the audit row round 2 added, and the two checks the new
test file grew.

**M2 — two numbers in the §6.2 record did not reproduce.** The freeze gate was
recorded as "passed (14 tests)"; measured, `tests/api/test_api_freeze.py` collects
**1** and `pytest tests/api/` collects **15** on this branch (1 freeze + 14
collision) and 1 on the parent. And `_shelves.py` was recorded at 355 lines; `wc
-l` says **356**.

**Accepted and fixed.** Both reproduced before acting. The record now states the
1 and the 15 separately and says where each comes from, and the line count is 356.
The point is well taken beyond the two numbers: a record whose value is that its
figures are checkable pays a real cost for one that is not.

**M3 — the alphabetical base-order rule is enforced by a test before the owner
decision the PR itself defers.** Raised in round 1 (as Deferred), round 2 (as
Minor 5, rebutted in part) and now round 3. Round 2's rebuttal stands on its
substance — a class statement cannot be written without *some* order, so "surface
it, do not choose" cannot be satisfied literally, and the choice is behaviorally
inert — but round 3 named a resolution neither earlier round proposed and that
the plan itself provides: **§6.4's addendum route.** "Deviations from this plan
require an addendum file in `plans/` acknowledged by the owner before the
deviating PR merges."

**Accepted, by that route.**
`plans/2026-07-27-addendum-phase5-mixin-base-order.md` records the rule, the
reasoning, the conflict with the preamble's illustration, and the two one-line
forms the owner's decision can take — (a) keep the rule and reorder the
illustration, or (b) drop the assertion. Its status is **AWAITING OWNER
ACKNOWLEDGEMENT**: PR-17 may be reviewed and opened without it, and may not merge
without it. That is stronger than either of round 2's options — it keeps the
convention enforced while making the decision blocking at exactly the point §6.4
says it should be. Deferred entry 35 and the PR description both point at it.

Three rounds raising the same item is the signal the anti-thrash rule exists to
read: it is a Minor, so it does not escalate on its own, but a third independent
reviewer reaching for it is why the answer moved from "recorded" to "blocking".

### Deferred

Appended to `critiques/deferred-observations.md` as entries 39–41: the
`__dict__` / `__weakref__` descriptors migrating onto the first mixin base
(verified — nothing observable changes, and it is why the collision check
excludes those two names); the back-import check reading literal import
statements only, so a dynamic `importlib.import_module` would evade it; and the
sidecar shortcut being dark in the reference holdings root, which is a property
of the root rather than of this PR.

Entry 39's mechanism is now also stated in the test file, next to the exclusion
list it explains.

## Regeneration

This round's fixes touched `plans/`, `critiques/` and one comment in
`tests/api/test_mixin_collisions.py`. **Nothing under `src/pdsfile/` changed**, so
under §6.6 step 5 the round-2 record carries forward unchanged: the head runs at
04:03:09 and 04:06:00 still postdate the last source change (`5320d83`,
04:02:58), and the recorded 22-addition set diff, the empty `--mode s` diff and
the empty manifest diff still describe the tree.
