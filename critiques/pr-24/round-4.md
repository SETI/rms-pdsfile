# PR-24 — adversarial review round 4 (scoped)

**Date:** 2026-08-04
**Reviewer:** a fresh, no-context opus-class subagent, per plan §6.6 and
`critiques/pr-24/topology.md`.
**Scope:** §6.6's anti-thrash rule — "the 4th round (if reached) is a *scoped*
re-review: confirm the prior round's findings are resolved; raise only **new
Major** findings." The reviewer was told this is the last round the plan permits
and that a Major would stop the PR and go to the owner.
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `c0e99da`.

**Verdict returned: `goal met` — 0 Major, 6 Deferred.**

## Confirmation of rounds 1–3

The reviewer re-derived rather than read, keeping its own no-ignores derivation
at base and head to check every figure against.

**Round 1's Major — the `re_validate.py` freeze — confirmed resolved.** The file
md5s equal to `git show origin/rewrite:` (`5e761dce1a0f68d7daf0cd91ff59970b`) and
does not appear in the diff; its `pyproject.toml` entry is the exact `8cab66a`
ten-code list; and its derived set is **26 violations across exactly those ten
codes, identical at base and head** — so the restore is complete, not partial.

**Round 3's Major — the stale §3 of the validation record — confirmed resolved.**
The reviewer reproduced the 30 unreached tool lines line-for-line from
`p24cov/head2.coverage` intersected with the head diff, and got exactly the
published composition (12 + 4 + 4 + 3 + 3 + 2 + 1 + 1). The probe table has 13
rows, no `RUF051`/`UP034`, and reads 13/13.

**All 19 Minors confirmed resolved, and round 3's rebuttal confirmed sound.** The
reviewer applied the `[*x, y]` → `x + [y]` conversion itself, observed the fresh
`RUF005` at `support.py:200`, and confirmed the file has no entry in the base
`pyproject.toml` — so the rebuttal is measured and correct. It also confirmed
`tests/holdings_maintenance/support.py` is byte-identical to `origin/rewrite`,
i.e. the reverted experiment left no residue.

**No resolution introduced a defect.** Round 3's three source edits tokenize
identically with `COMMENT`/`NL` dropped — 3,130 / 3,135 / 275 tokens, exactly as
recorded.

## Gates re-verified independently

2,760 = **483** + **2,277**, measured; sub-plan §5 sums to 2,277, §6 to 483, and
deviation (4)'s table matches the measured head set **code-for-code across all 33
codes, zero mismatches**. Ratchet against `git show origin/rewrite:pyproject.toml`:
**0 widens, 0 new keys**, 89→70 / 383→198 whole-file and 78→59 / 369→184 in scope,
with **0 stale slots and 0 uncovered violations** at head, and the non-ratchet
`pyproject.toml` settings parsing identical. `ruff check` clean over 139 of the
140 `.py` on disk, the skipped one being the gitignored `_version.py`, with
`RUFF_TARGETS` unchanged from base and `ENABLE_RUFF_CHECK` defaulting true — not
vacuous. Id sets identical id-for-id in both modes (892/892, 558/558, 0/0/0), on
a record whose junit timestamps postdate the last `src/`+`tests/` edit. 339
changed executable lines split 77/137/124/1, with 73 and 107 executed. Fresh API
dumps at base and head, 733,876 bytes each, `diff` empty. No prohibited file in
the diff, no golden touched, no `noqa` added, no `[*x, y]` introduced, no
`# fmt:` guard.

## Checks this round added

Three that no earlier round ran, and which are the reason a fourth round was
worth having even scoped:

- **A rename-collision sweep.** Per-function binding sets compared base against
  head across every changed `.py`. Thirteen scopes changed size and all thirteen
  are accounted for; the four that *grew* are the real risk cases —
  `write_infodict`'s `_values` and `write_linkdict`'s `_recno`/`_interior_path`,
  where the old name survives elsewhere in the same function. The reviewer
  checked load/store positions and found every surviving load dominated by its
  own store, so no read sees a stale value. It also confirmed `md5`/`old_md5`
  shadow no module-level name and that `old_md5` was necessary because `md5` is
  already a local in `generate_checksums`.
- **The `E501` justification measured rather than accepted:** of the 41 files
  carrying the 1,638 permanent `E501`s, in **exactly one**
  (`tests/rules/pds4/test_uranus_occs_earthbased.py`, 5 sites) is every site a
  comment line — precisely the claim §5 makes.
- **Logging f-strings audited across the whole package:** the only f-strings this
  PR adds are 2 `print()`s and 3 exception messages; the 7 logging f-strings in
  `src/` are all pre-existing and untouched.

## Major (new)

**None.** The loop terminates here: a fresh reviewer returned zero Major and,
under the scoped mandate, no new Minor.

## Deferred (non-blocking)

Six, of which five were prose accuracy in records this PR itself wrote. They are
**not** required to be fixed — §6.6 says a Deferred finding is deferred — but
five were cheap and are corrected, because they are the same class of defect the
loop spent three rounds catching and leaving them would be inconsistent:

| # | Finding | Disposition |
|---|---|---|
| d1 | sub-plan §11's `I001` and `B007` "Executed" cells are the **pre-revert** figures (72/4 and 19/1); the final ones are 71/5 and 17/3, which §5, §6, deviation (4) and `pyproject.toml` all carry correctly | **corrected**: §11 now says the rows are the deltas as they arose and that the last row applies the revert, and names the final figures |
| d2 | §11 claimed "everything above is the plan as written before any code changed", but ~105 lines above it were edited after execution and after each round | **corrected**: §11 now says plainly what was edited and why, and tells the reader to treat §1–§10 as the final classification rather than the pre-execution plan |
| d3 | deferred entry 89 said "eight sites" and listed nine, and "the six tool `main()`s" where eleven tools have one | **corrected**: nine, and the count of tools dropped |
| d4 | `COUVIS_0xxx.py:286,295` — the two rewrapped `raise` statements use a hanging indent rather than align-under-the-paren. Rewritten as a unit by the `UP031` fix, so a style choice, not the broken-alignment class rounds 1 and 3 caught | **left**: no rule requires either spelling and the reviewer explicitly classes it as a choice |
| d5 | deviation (4) still read "`[*x, y]` is not wanted **anywhere**" unqualified, so round 3's measured qualifier lived only in the sub-plan and the round record — not in the document a future maintainer reads first | **corrected**: deviation (4) now states that the rule is about ruff's rewrite *of a concatenation*, and names `support.py:200` as the site left alone and why |
| d6 | the plan's "`__all__` for `support.py`" clause was satisfied vacuously but only the `__init__.py` half was written up | **corrected**: sub-plan §8 now discharges both halves |

These corrections touch **no file under `src/` or `tests/`** — only
`plans/2026-08-04-pr-24-subplan.md`, `critiques/deferred-observations.md` and
`.cursor/rules/pdsfile_overrides.mdc` — so under §6.6 step 5 the full-data record
(`runs/p24-head3`) carries forward unchanged, and no gate is affected.
