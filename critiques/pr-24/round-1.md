# PR-24 — adversarial review round 1

**Date:** 2026-08-04
**Reviewer:** a fresh, no-context opus-class subagent, per plan §6.6 and
`critiques/pr-24/topology.md`.
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `2706ad5`
(82 files, +1,631 / −792).
**Verdict returned:** **`goal not met`** — 1 Major, 9 Minor, 3 Deferred.

## What the reviewer verified independently

Not taken from the record: `ruff check src/pdsfile tests scripts` clean over 139
files; the no-ignores re-derivation reproducing 2,760 → 2,259 in scope; the
ratchet arithmetic and the zero-widen property against
`git show origin/rewrite:pyproject.toml`; that every code in every head entry
actually fires and no head violation lacks an entry; that `pyproject.toml` and
deviation (4) agree code-for-code; the junit id sets (892/892 and 558/558, 0
added / 0 removed / 0 changed) against **both** recorded baselines; that the head
run postdates the last `src/`+`tests/` commit; a fresh `dump_public_api.py` dump
byte-identical to base at 733,876 bytes; that no prohibited file is in the diff;
that no inline `noqa` was added and no `[*x, y]` appears anywhere; that the only
added f-strings are two `print()`s and three exception messages, none in a
logging call; and the 132/69 logging sweep, the 15/15 probe, the 111-passed tool
coverage run, the 92/800 no-holdings run, the MRO dumps and both consumer checks.

## Major

**M1 — `re_validate.py` was ruff-fixed against ground rule 7, overrides deviation
(6), and the plan's own PR-24 instruction, with no owner addendum.**

Three authorities say the file is not to be edited:

- §2 ground rule 7: "**`re_validate.py` is left alone for now** … its internals
  … are untouched", and ground rules are "not open for re-interpretation by the
  executor";
- `pdsfile_overrides.mdc` deviation (6): "**frozen** (document-only): do not
  refactor their internals (email/batch logic, **ordering**)" — and the `I001`
  fix reorders its imports;
- the plan's PR-24 section: "`re_validate.py` **also gets a permanent `ruff
  check` per-file-ignore set** (its full derived violation set — UP031, E402,
  RUF059, E701, I001, B007, RUF005, C405, RUF051, E721, UP034) … for the same
  freeze reason", and "cleaning *other* `holdings_maintenance/` tools here is
  behavior-preserving style only".

The PR had fixed exactly the codes that sentence enumerates as permanent and
shrunk the entry from ten codes to two. The sub-plan's §1 justified inclusion as
"named in the plan, including `re_validate.py`", which inverts what the plan
says. §6.4 requires an owner-acknowledged addendum for a deviation; none exists.

The reviewer also noted the aggravating fact, which the PR's own record had
already written down without drawing the conclusion: `re_validate.py` is the
**only** edited module in the package with no test coverage of any kind, so 23
changed executable lines would have shipped on a probe alone.

**Resolved — fixed, not rebutted.** `re_validate.py` is restored byte-for-byte
from `origin/rewrite` (verified by `diff` against `git show
origin/rewrite:<path>`), and its `pyproject.toml` entry is back to its `8cab66a`
value `["B007", "C405", "E701", "E721", "I001", "RUF005", "RUF051", "RUF059",
"UP031", "UP034"]`. Restoring is not a ratchet widen: the shrink property is
measured against `origin/rewrite`, where all ten codes are present. The
arithmetic is re-derived throughout: **2,760 = 483 fixed + 2,277 permanent**
(was 501/2,259), ratchet slots 369 → **184** (was 175). Sub-plan §1 gains a row
stating the freeze and a rule **(h)**; §5 gains a rule-(h) table.

## Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | `pdschecksums.py:616`, `pdslinkshelf.py:1583`, `pds4checksums.py:585` — the `latest_mtime` → `_latest_mtime` rename moved each call's opening paren one column right and the continuation line was not re-indented | **fixed**: one space added to each. The §11 whitespace audit compared `git diff` against `git diff -w` line counts and was structurally blind to this, because the misaligned lines did not change at all |
| m2 | `pdsinfoshelf.py:373` `checksum2` → `_checksum2` asserts the binding is deliberately unused, when it is unused because `:395` reads `checksum1 != checksum1` — a defect the plan already assigns to Phase 6 | **fixed**: rename reverted, `RUF059` kept on the file with that reason. This is the same call the PR made for `LOGDIRS`, applied consistently |
| m3 | deviation (4) filed `N806` ×3, `F821` and `PT014` under "Why it can never be fixed" when the PR's own records assign each to a named later PR | **fixed**: the table gained a **Locked by** column separating `frozen`/`aligned`/`prohibited` from `behavior`, and names PR-25, PR-28 and "a test-content PR" |
| m4 | sub-plan §5 and deviation (4) filed `B006` and `PT028` under rule (a), but the manifest covers no `holdings_maintenance` module | **fixed**: re-filed under rules (d)/(e), with the real lock stated (defaults flowing into `pdslogger`; `pdsdependency.test` called by name from the frozen `re_validate.py`) |
| m5 | sub-plan §4.1 pointed at `critiques/pr-24/` for the corrected logging sweep, which contains only `topology.md` | **fixed**: repointed to deferred observation 82, where the figures actually live |
| m6 | `critiques/phase5-validation.md` said two stale ratchet slots; there are three, and the unit was wrong | **fixed**: `tests/conftest.py`'s `F401` added (re-measured: 3 stale code slots at `8cab66a`), unit corrected from "removals" to "code slots" |
| m7 | sub-plan §5 said `RUF012` "rule modules (29)" and `pdsdependency.py` `UP031` ×38; measured is 26 + 3 and ×39 | **fixed** |
| m8 | four `except (ValueError, IOError)` became `except (OSError, ValueError)` — `UP024` asks only for the alias, not the reorder | **fixed**: now `except (ValueError, OSError)`, so the diff is one token per site |
| m9 | the plan's "`__init__.py` star imports get `__all__` + targeted `noqa`" clause was neither delivered nor explicitly rebutted | **fixed**: sub-plan §8 now states that the clause resolves to PR-23's file plus the permanent `F401`, that both `rules/__init__.py` files already have `__all__`, and that an inline `noqa` may not be added at all |

None of the nine was rebutted; all nine were accepted and fixed.

## Deferred (non-blocking)

| # | Finding | Recorded as |
|---|---|---|
| d1 | `test_cocirs_xxxx.py` — the `F841` deletion settles a copy-paste inconsistency between two loops in the less informative direction | deferred observation **86** |
| d2 | `tests/rules/pds4/test_uranus_occs_earthbased.py`'s five `E501`s are all commented-out parametrize rows — the one `E501` entry held by prose rather than a live table row | already stated in sub-plan §5; no separate entry |
| d3 | `pds3file/__init__.py:123` — after the `F811` de-duplication the alias comment introduces one method while the rest of the alias group sits fifty lines below | deferred observation **87** |

## Re-validation after the round

Because the round changed `src/pdsfile/`, the full-data record is regenerated
before round 2, per §6.6 step 5. Results are in the PR-24 section of
`critiques/phase5-validation.md`.
