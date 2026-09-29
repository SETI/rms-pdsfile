# PR-23 — adversarial review round 4 (scoped)

**Date:** 2026-08-03
**Reviewer:** a fourth fresh, no-context opus-class subagent
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `a67aaf0` (2,737 lines)
**Verdict returned:** **`goal met`** — **0 Major**, 0 Minor (scoped round), 4
would-be-Minor recorded as explicitly non-blocking

This is §6.6's **scoped** fourth round — "confirm the prior round's findings are
resolved; raise only **new Major** findings" — and it is the hard cap. It returned
no Major, so the loop terminates here and the PR is opened.

## Round-3 resolution audit

| Finding | Status | Evidence the reviewer cited |
|---|---|---|
| m1 — §2's characterisation of the 38 unreached lines | **resolved** | re-derived the set independently (suite coverage ∪ a fresh probe coverage run ∩ the head-side `-U0` diff): **exactly 38**, split UP024 ×9 / f-string ×5 / E701 ×14 / rename ×3 / F841 ×4, and the three named exceptions are exactly the three that need `pylibmc` |
| m2 — two governing docs described an assertion not in the tree | **resolved** | the addendum and the record both name the `__module__` check, matching `test_mixin_collisions.py:75-80` verbatim |
| m3 — `pdsviewable.py`'s re-export note above `import os` | **resolved** | the note sits above `import pdslogger as pdslogger`; the block is still `I001`-clean under the no-ignores config |
| m4 — the sub-plan's "as executed" delta | **resolved** | 15 commits (`git log origin/rewrite..HEAD` = 15) and 55 probe values (the probe emits exactly 55 lines) |
| m5 — mixed line-number conventions and two wrong cites | **resolved** | all seven §4 cites checked at head and correct; `pdsfile.py:634`/`:690` and `_shelves.py:338` correct |
| m6 — the `F841`-with-effect idiom spelled two ways | **resolved** | `_preload.py:201` and `pdsfile.py:1116` are both `_ = cls.CACHE[…]`, and §4 says so |
| d1, d2 | **recorded** | deferred entries **76** and **77** |

"Did resolving them introduce anything new? **No.**"

## New Major findings

**None**, explicitly. What the reviewer re-derived rather than trusted:

- **§6.2** — `setdiff.py` re-run: ns **892 vs 892**, s **558 vs 558**, zero
  movement in all three directions, exit 0 both modes. It additionally
  cross-validated the script against the raw XML (`failures="0" errors="0"` in all
  four files, testcase counts 892/558, skips 34/3) **so that no failure could be
  masked by the script's last-child-wins outcome rule** — a check no earlier round
  made. Timeliness: last `src/pdsfile/` change `f8bdcbd` 15:54:06; `ns.xml`'s
  pytest start 15:54:10; `a67aaf0` (16:01) touches only `critiques/` and `plans/`.
- **§6.1** — dump re-run in both trees: 733,876 B, md5
  `442428dafbdf30f291987a196b22a2ce`, `diff` empty; `api_manifest.json`,
  `manifest_allowlist.json`, `consumer_used_private_names.json`,
  `tests/api/conftest.py`, `test_api_freeze.py` and `scripts/dump_public_api.py`
  **byte-identical to base**.
- **Ratchet** — both `pyproject.toml`s parsed with `tomllib`: 92 → 85 entries,
  447 → 379 slots, **no file gained, no entry gained a code**, `select`,
  `extend-ignore`, `target-version` and `line-length` unchanged;
  `grep -rn noqa src/pdsfile/` no matches; head's no-ignores derivation exactly
  **33**, base exactly **154**; deviation (4) agrees file-by-file, code-by-code,
  site-by-site.
- **Owner decision 3** — no `# fmt:` anywhere in `src/`, `tests/`, `scripts/`;
  `ENABLE_RUFF_FORMAT` still `false` and `run-all-checks.sh` unedited.
- **Behavior** — every hunk of all 13 changed source files, with the ten
  `%`→f-string conversions executed side by side (byte-identical, including the
  two implicit-concatenation traps), the `F541` literals confirmed brace-free, the
  `SIM102` fall-throughs, the `RUF015` guards, the `B020` rename, all four
  `RUF005` operands traced to their assignments, the `version_ranks` inversion,
  the `_ =` probes, and `_get_shelf` confirmed to return a plain `dict` for
  `SIM118`.
- **The probe** — re-run with `PYTHONPATH` pinned per tree and verified via
  `pdsfile.__file__`: 55 values, `diff` empty.
- **Line coverage** — 143 / 81 / 62 reproduced row for row; probe 36, probe-only
  24, union 105, neither 38, per-file breakdown matching. "Nothing in §2 is false."
- **The test edits** — "strictly **stronger** than what it replaced and cannot
  pass vacuously": `object not in __bases__` catches the degenerate empty-mixin
  case that would otherwise make the `all(...)` vacuous.
- **Holdings-free gate** — current run, after the last `src/` change: ruff clean,
  **92 passed / 800 skipped**, pyroma, API freeze and clean-install green.

## would-be-Minor (non-blocking, and fixed anyway)

The scoped round may not raise Minors, so these were listed for information. All
four are one-line record corrections and were made rather than carried:

1. `phase5-validation.md` cited `pdsfile.py:429/633/689` for `_childnames_filled`
   — base numbers; head is `:428`/`:632`/`:688`, and `:428` assigns `None`, not a
   list (the substance holds through the property). **Fixed.**
2. The `F841` parenthetical in §2 named three of the four binding removals among
   the 38; `__init__.py:7` is the fourth. **Fixed.**
3. The sub-plan's "deferred entries this PR produced" still listed 67–73; it now
   owns 67–77. **Fixed.**
4. The sub-plan's `E721` bullet named two of the three sites; `pdscache.py:322` —
   the one neither the suite nor the probe can execute — was missing. **Fixed.**

Since all four are records only, §6.6 step 5's regeneration rule does not apply:
the full-data record from `runs/pr23-r4` carries forward unchanged.

## Loop arithmetic

| Round | Major | Minor | Deferred | Verdict |
|---|---|---|---|---|
| 1 | **1** | 9 | 2 | `goal not met` |
| 2 | 0 | 6 | 2 | `goal met` (new Minors → continue) |
| 3 | 0 | 6 | 2 | `goal met` (new Minors → continue) |
| 4 (scoped) | **0** | — | — | **`goal met`** |

**1 Major and 21 Minor across four rounds.** Four Minors were in the code — a
tautological assertion, two one-character idiom mismatches and a comment above the
wrong import. The Major and the other seventeen were figures, claims or
classifications in the validation record, the sub-plan, `pdsfile_overrides.mdc`
and one plan addendum. No round found a defect in the behavior of the code this
PR changed.
