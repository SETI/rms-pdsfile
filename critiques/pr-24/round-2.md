# PR-24 — adversarial review round 2

**Date:** 2026-08-04
**Reviewer:** a fresh, no-context opus-class subagent, per plan §6.6 and
`critiques/pr-24/topology.md`. It received round 1's record, so that it could
audit whether those findings were actually resolved.
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `593fa06`
(82 files, +1,836 / −765).
**Verdict returned:** **`goal not met`** — **0 Major**, 4 Minor, 1 Deferred. All
four Minors are arithmetic or citation slips in the records; none touches the
code, the gates or the ratchet.

## What the reviewer re-derived rather than read

`ruff check` clean over 139 files, and that the one `.py` on disk it skips is the
gitignored `_version.py` — with `scripts/run-all-checks.sh:404`'s
`RUFF_TARGETS` confirmed identical, so the gate is not vacuous. The ratchet
parsed from `git show origin/rewrite:pyproject.toml` versus HEAD: **0 widens, 0
new keys**, 19 entries removed, 89→70 / 383→198 whole-file and 78→59 / 369→184 in
scope. **0** stale entries at head and **0** uncovered violations. The
2,760 / 483 / 2,277 arithmetic re-derived exactly, and every per-code figure in
sub-plan §2/§5/§6 and deviation (4) matched. The manifest dumps byte-identical at
733,876 bytes and `tests/api/` 26 passed. Both junit pairs parsed independently:
892/892 and 558/558 ids, 0 added / 0 removed / 0 outcomes changed. The 339
changed executable lines and the 73 / 107 executed counts reproduced exactly. The
no-holdings run re-run: 92 / 800. Consumer check A 4/4 with the two flat names
still absent. `re_validate.py` byte-identical to `origin/rewrite` by md5.

It also checked the things a claim cannot settle: that no `UP031` site surviving
in the ratchet sits in a `raise` or `print()` context (0 of 139), that the
`pdslogger` filepath argument really does resolve as described (read in the venv
source), that `PdsViewSet` defines `__bool__`/`__len__` but no `__eq__` — so
`is not False` is right and ruff's `if res:` would differ — that the deleted
`F811` definitions are provably the dead copies, that `pdsdependency.test` really
is called by name from the frozen `re_validate.py`, that `bundle_prefix` and its
siblings really are manifest members, and that the `LOGDIRS` shadowing bug is
real. It confirmed all ten of round 1's findings are genuinely resolved and that
no resolution introduced a new defect — including a delta-scan over every changed
line that opens a bracket, which found no misalignment beyond the three round 1
caught.

## Major

**None.**

## Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | `critiques/phase5-validation.md:6897` still said the no-ignores re-derivation reports "2,259" permanent violations — round 1's pre-revert figure — in a file whose §10 asserts every figure above it was regenerated | **fixed**: 2,277 |
| m2 | sub-plan §2 said "fifteen codes with one site each" and then named **eleven**; taken at its word the breakdown summed to 2,764, not 2,760 | **fixed**: "eleven" |
| m3 | sub-plan §5 mixed base and head line frames without saying which, and its `A002` row cited `pds3file/__init__.py:151` — a line this PR's own `F811` fix deletes | **fixed**: §5 now states once that its line numbers are at `8cab66a`, `A002` cites `:148,204`, `N806` and `B007` are converted to base numbers, `RUF059`'s `:395` corrected to `:394`, and `PT028` gains its ×2/×4 split |
| m4 | the `UP031` composition was mis-allocated in three places: `re_validate.py`'s seventh site is a logging call and was counted twice; §5's rule-(c) row did not account for its own total; and twelve plain `%` expressions in no aligned block were filed under "hand-aligned blocks" | **fixed**: re-measured and restated as **46** logging + **24** `file.write` + **51** aligned (37 `PdsDependency(...)` + 11 `--log` help + 3 `COCIRS_xxxx`) + **12** plain `%` (their own row, under rule (f)) + **6** in `re_validate.py` = 139. Deviation (4)'s "39 of them" corrected to 38/37. The rule-(h) row now counts 25, not 26, with the double-count stated |

None was rebutted; all four were accepted and fixed. §5 sums to 2,277 and §6 to
483 after the corrections — re-checked mechanically.

## Deferred (non-blocking)

| # | Finding | Recorded as |
|---|---|---|
| d1 | the pds3/pds4 tool twins have already diverged on their `B006` defaults — `pds4checksums.py` and `pds4infoshelf.py` already use the None-sentinel form the rule asks for, so two of the nine permanent `B006`s are a divergence rather than a shared property, and PR-25 must pick one signature when it consolidates them | deferred observation **88** |

## Re-validation after the round

This round changed **only** `plans/`, `critiques/` and
`.cursor/rules/pdsfile_overrides.mdc` — no file under `src/` or `tests/`, and no
ratchet entry. Under §6.6 step 5 the prior full-data record therefore carries
forward unchanged: `runs/p24-head2` remains the record of the code as it stands,
and it postdates the last change under `src/` and `tests/`.
