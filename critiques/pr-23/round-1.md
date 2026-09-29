# PR-23 — adversarial review round 1

**Date:** 2026-08-03
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 2)
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `b0dcb4f` (2,049 lines)
**Verdict returned:** **`goal not met`** — 1 Major, 9 Minor, 2 Deferred

The reviewer re-derived the violation set in both trees, re-ran the freeze dumper
in both trees, re-computed the junit set diff from the raw artifacts, tokenized
the banner commit, dumped the MROs in both trees, measured **line-level** coverage
of every changed line, and read all 119 fixes against the code.

## Major

### M1 — two of the eleven permanent ratchet codes were not freeze-locked

`src/pdsfile/_local_fs.py:98`, `:156`; `pyproject.toml`;
`.cursor/rules/pdsfile_overrides.mdc` deviation (4); sub-plan §5; validation §4/§5.

`SIM103` was frozen under classification rule (d) — collapsing
`elif f(): return True / else: return False` returns `f()`'s raw value rather than
the `True`/`False` singleton, and `os_path_exists` is not proven `bool`-returning.

**The reviewer showed the premise holds only for ruff's *bare* rewrite.** ruff's
own message for this shape names `return bool(cls.os_path_exists(shelf_abspath))`,
and the reviewer reproduced it on a synthetic copy of both blocks. `bool(x)`
invokes exactly the `__bool__`/`__len__` that `if x:` invoked and returns exactly
the singleton the branch returned, so the callee's return type never enters the
argument and no reachability claim about `os_path_exists` is needed. The fix is
provable from evidence local to the function — which is this PR's **own** §3 rule
for *fixing*.

Worse, the PR already used that idiom, in this PR, at `_shelves.py:337`
(`return bool(self.bundlename)`). So the classification was internally
inconsistent, and `pdsfile_overrides.mdc` was about to record, permanently and
under the heading "Why it can never be fixed", a claim that is false.

**Resolution: fixed** (`54e9380`). Both sites become
`return bool(cls.os_path_exists(shelf_abspath))` with the "every shelf file has an
entry with an empty key" comment promoted above the return. `_local_fs.py` loses
its ratchet entry entirely. Arithmetic restated everywhere it appears: permanent
**35 → 33**, fixed **119 → 121**, ratchet **8 entries / 11 slots → 7 / 10**. The
full-data record was regenerated afterwards, per §6.6 step 5.

## Minor

| # | Finding | Resolution |
|---|---|---|
| m1 | The non-vacuity claim is **file-level** and overstates the gate's reach. At line granularity only ~88 of ~168 changed executable lines were executed — every `MemcachedCache` edit, `PdsViewSet.append`'s B020 rename, all three `next(iter(...))` sites, `_get_shelf`'s failure path and `repair_case`'s not-found path were never run. | **Fixed.** Validation §2 now states the line-level figure, measured from the regenerated run, alongside the file-level one, and names the unexecuted regions. |
| m2 | Validation §5 printed `git diff … \| grep -c '^+.*noqa'` → `0`; the real value is 6, all prose (including the record's own line). The substantive claim — no inline `noqa` in any source file — is correct. | **Fixed.** The recorded command is now the one that answers the question asked. |
| m3 | The permanent records cite **pre-change** line numbers for the surviving ignores, including two the PR moved itself (`__init__.py` F403 `:11→:12`, `:12→:13`). Also the supporting cites for `_info_filled` and `childnames`. | **Fixed.** Every site in the sub-plan §5 table and in `pdsfile_overrides.mdc` is now a head line number, and both say so. |
| m4 | The sub-plan claims "an 'as executed' delta is appended rather than editing the sections", but §11 was still a placeholder while commit `f2f2416` edited §1 in place. | **Fixed.** §11 is written, and it records the in-place §1 edit as a deviation from the sub-plan's own method. |
| m5 | `plans/2026-07-27-addendum-phase5-mixin-base-order.md` and `test_mixin_collisions.py:174` still say "object last", which PR-23 made false. | **Fixed.** The addendum gains a "superseded in part" note under **The decision**; the test comment states the rule as alphabetical, full stop. |
| m6 | `pdscache.py`'s re-export note sat above the whole stdlib block, so "Nothing below references sys" appeared to cover `os`, `random` and `time`, all of which are used. | **Fixed.** The note sits directly above `import sys as sys`, matching `pdsfile.py:87-89`. (The no-blank-line placement is itself an `I001`; the blank-line form is what ruff's isort accepts, and the block is verified clean.) |
| m7 | `pdscache.py:73-74` — `f'DictionaryCache'` has an `f` prefix and no placeholder, exactly what `F541` targets; invisible to ruff because it evaluates the implicit concatenation as a whole. | **Fixed.** Prefix dropped; message text unchanged. |
| m8 | `_path_utils.py:87`, `:112`, `:134` still name `IOError` in prose, one of them directly above a line this PR edited. | **Fixed.** All three now say `OSError`. They were not *wrong* — `IOError` **is** `OSError` — so this is naming consistency, not a correction. |
| m9 | `_properties.py:1338-1341` has a branch whose only statement is `pass`. | **Fixed.** `if not self.exists: pass / else:` becomes `if self.exists:` with the comment promoted. No re-indentation is needed, because an `else:` body and an `if` body sit at the same depth. |

## Deferred (recorded, not fixed)

| # | Finding | Where it went |
|---|---|---|
| d1 | `src/pdsfile/_version.py` carries a real `RUF022` and is invisible to the gate only because ruff respects `.gitignore`; a lint run over an unpacked sdist, or with `--no-respect-gitignore`, would fail. | `critiques/deferred-observations.md` entry **71** |
| d2 | `MemcachedCache` has no gate at all — 28 of the 33 `pdscache.py` lines this PR changed are unreachable by any test in the repo and by both consumer smoke checks, and ground rule 9 forbids deleting the class. | entry **72** |

## What the reviewer independently confirmed

Recorded because it is the part of the round that is evidence rather than
instruction:

- `ruff check src/pdsfile tests scripts` clean; ratchet strictly shrinking
  (447 → 380 slots repo-wide); **no inline `noqa` in any source file**; the
  no-ignores re-derivation returns exactly the enumerated residual on both sides
  and the per-code table reconciles exactly.
- API freeze byte-identical, md5 `442428dafbdf30f291987a196b22a2ce` both sides;
  manifest, allowlist, dumper, freeze test, `run-all-checks.sh` and
  `gen_ruff_ratchet.py` all unedited.
- The §6.2 artifacts postdate the last `src/pdsfile/` change; re-running the
  set-diff independently: 892 vs 892 and 558 vs 558 ids, 0 only-in-baseline,
  0 only-in-head, 0 outcome changes.
- **Owner decision 3 held:** `ruff format --check` reports the *same* 13
  unformatted files at base and at head, so `ruff format` was not run; no
  `# fmt: off/on/skip` anywhere; `ENABLE_RUFF_FORMAT` still false.
- `UP004`: the three MROs identical entry for entry; the two in-repo `__bases__`
  consumers unaffected; no consumer repo reads `__bases__`; the
  `test_mixin_collisions.py` edit is the one the addendum names, the replacement
  still fails if `object` returns, and the **test id set is unchanged** (26 ids in
  `tests/api` both sides).
- Every one of the thirteen `%`→f-string conversions evaluated side by side:
  byte-identical strings, including the implicit-concatenation-then-`%` case.
- Entry 60's banner commit token-identical before/after; entry 64's six
  commented-out lines genuinely untouched.
