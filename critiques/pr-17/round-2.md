# PR-17 — adversarial review round 2

**Date:** 2026-07-27
**Reviewer:** a fresh opus-class subagent with no development context and no
knowledge of round 1, per §6.6 step 5. Same inputs as round 1, on the updated
diff.
**Diff reviewed:** `origin/pr-16-path-utils...ddad67c`.
**Verdict:** **goal met** — 0 Major, 6 Minor, 3 Deferred.

The reviewer independently re-derived the byte-for-byte comparison, the empty
manifest diff, all 23 per-code ratchet counts, the set-diff arithmetic from the
raw artifacts, the coverage provenance, the no-holdings counts on both sides, the
6,753-sidecar scan, and the §3.4 path scan. Two of its own measurements are worth
keeping:

- **The moved code is genuinely exercised.** The head run's coverage data has 224
  executed lines in `_local_fs.py` and 128 in `_shelves.py`, including the
  `SHELVES_ONLY` branches that make the cross-mixin `cls.` calls. The set-diff
  gate is not blind to this move.
- **A differential test of the eval isolation.** Over the first 400 real
  sidecars, the old inline expression and `_eval_null_key_record` gave 0
  mismatches.

## Findings and resolutions

### Minor

**1 — the back-import guard missed the relative form, which is the only form that
actually works.** `test_no_mixin_module_imports_pdsfile_at_module_level` compared
`node.module` against the literal `'pdsfile.pdsfile'`, so relative imports — the
spelling this package uses everywhere — were invisible to it.

**Accepted and fixed** (`5320d83`). Reproduced first, then extended to all six
spellings. Measured, per mixin module:

| injected | outcome before the fix | after |
|---|---|---|
| `from pdsfile.pdsfile import PdsFile` | ImportError at collection | unchanged |
| `from .pdsfile import PdsFile` | ImportError at collection | unchanged |
| `import pdsfile.pdsfile` | caught | caught |
| `import pdsfile.pdsfile as _core` | caught | caught |
| `from . import pdsfile as _core` | **green — not caught** | caught |
| `from pdsfile import pdsfile as _core` | **green — not caught** | caught |

The check now resolves each statement to the absolute module names it reaches,
resolving relative levels against the importing module's own package.

**2 — the PR's one content edit was executed by no automated test.** The
reviewer read the head run's coverage data and found `_eval_null_key_record`'s
body unexecuted: the holdings copy the goldens are tuned to carries the `.pickle`
half of each info shelf and no `.py` sidecar, so `shelf_lookup`'s sidecar branch
is dark in every full-data run. The record disclosed that and rested the
equivalence claim on a one-off instrumented run against the complete set, which
CI cannot reproduce.

**Accepted and fixed** (`5320d83`). `tests/core/test_shelf_sidecar_record.py`
builds its own two-line sidecar in `tmp_path` — ground rule 3 permits exactly
this — and pins the contract the docstring states, including all three malformed
shapes and the silent one (`"": 123` → `12`, because the trailing comma is
removed by position). Eight holdings-free ids, enumerated in the §6.2 record.

**3 — the sub-plan asked for a wider sweep than the record's §11 delivered.**
Sub-plan §2 direction 2 lists "direct module-attribute assignment" alongside the
monkeypatch forms; §11's table enumerated only the 20 monkeypatch sites and
omitted `tests/pds4file/test_pds4file_blackbox.py:448`,
`dummy.glob_glob = lambda …`.

**Accepted and fixed.** Verified independently: a regex over `tests/`, `scripts/`
and `src/` for direct assignment to any of the fourteen moved names or
`PATH_EXISTS_CACHE_SIZE` returns exactly that one site, and it is safe — the
target is an *instance* attribute on a `Pds4File.__new__`-built dummy, which wins
over the MRO both before and after the move. §11 now carries the row and the
reasoning, so the audit's coverage claim matches what was searched.

**4 — the documented contract omitted that `eval` sees the function's locals
first.** `eval(expr)` resolves locals → globals → builtins.

**Accepted and fixed** (`5320d83`): the clause now names `rec` and `parts`.

**5 — the base-ordering convention was chosen and enforced without owner
sign-off.** The reviewer reads §6.4's "any new decision not already settled in
§8 or elsewhere in this plan" as covering the alphabetical rule, and would either
hold `test_the_mixin_bases_are_listed_alphabetically` until the owner rules or get
sign-off before merge.

**Partly accepted; the proposed fix is rebutted.** The rebuttal:

- A class statement cannot be written without *some* base order, so "surface it,
  do not choose" cannot be satisfied literally here — every possible delivery of
  this PR embodies a choice. §6.4's hard stops enumerate behavior, file formats,
  CLI flags, log formats, exit codes and freeze diffs; the reviewer itself
  measured the ordering to be behaviorally inert, which is the category §6.4 is
  not about.
- Holding the test until the owner rules would leave the convention documented
  and unenforced, which is precisely the failure mode that produced the finding
  in the first place.
- The PR-executor's brief for this PR states the base order is its to decide:
  "Establish the base order deliberately and say why in the PR… you are setting
  the pattern for PR-18 through PR-22."

What was accepted is the surfacing, which was too quiet. Deferred entry 35 is now
an explicit owner decision with its two one-line forms spelled out — (a) keep the
rule and correct the plan's illustration, or (b) drop the assertion — so the owner
can rule either way with a single edit, before PR-18 appends the next mixin. The
PR description carries it too.

**6 — a commit typed `docs:` added a test function.** `114a5c1` edited
`_shelves.py`'s docstrings *and* added
`test_no_mixin_module_imports_pdsfile_at_module_level`;
`.cursor/rules/git_workflow.mdc:26` defines `docs` as "Documentation-only
change", and §6.6's schedule puts `git_workflow.mdc` in force on every PR.

**Accepted and fixed.** Nothing was published yet, so the commit was split rather
than relabelled: `a024bf4` `docs: sharpen the two _shelves.py docstrings` and
`7ca54db` `test: guard the half of the mixin back-import rule that raises
nothing`. `git diff` between the pre-split and post-split heads is empty, so the
resplit changed no content.

### Deferred

All three are pre-existing conditions of code that moved byte-for-byte, so none
is fixable inside this PR. They are appended to
`critiques/deferred-observations.md` as entries 36–38.

## Regeneration

The round's fixes touched `src/pdsfile/` (`_shelves.py`'s docstring clause), so
under §6.6 step 5 the full-data record was regenerated before round 3: the head
runs at 04:03:09 and 04:06:00 postdate the last source change (`5320d83`,
04:02:58). The baseline runs stand — the baseline worktree is detached at
`2ff83a4` and no round has touched it. The set diff is now 22 additions and
nothing else, the `--mode s` diff is still empty, the manifest diff is still
byte-empty, and the no-holdings run is 81 passed / 800 skipped — the parent's 59
plus exactly those 22.
