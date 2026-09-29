# PR-03+04 adversarial review — round 1

Fresh, no-context Opus reviewer given the PR-03/PR-04 plan sections, ground
rules, PR discipline, the sub-plan, the claimed validation, the diff
(`git diff rewrite..HEAD`), and read access to the repo + holdings + template.
Mandate: assume the goal was not met and try to prove it.

## Verdict: goal met (0 Major, 2 Minor, 2 Deferred)

Independently verified by running commands: no leftover `REPONAME`/`MODULENAME`;
`filecache.mdc` absent; `pdsfile_overrides.mdc` has all 10 deviations; the ruff
ratchet is **byte-for-byte** the true current violation set (regenerated with an
empty per-file-ignores and diffed — identical, 67 files), no inline noqa masking;
`ruff check` exits 0; pyproject correct (no mypy/bandit/vulture, no `-n`/`--cov`,
`full_holdings` registered, no src assumptions, no `py.typed`, dev self-ref =
`rms-pdsfile[docs]`, coverage without `fail_under`/`parallel`); `pip install -e .`
+ `import pdsfile` (no holdings) + all 11 console scripts OK; `run-all-checks.sh`
passes with exactly ruff-check + pyroma (10/10) + api-freeze; `--confcutdir=tests`
is load-bearing (without it the freeze test dies on `KeyError PDS3_HOLDINGS_DIR`);
`--api-freeze`/`RUN_API_FREEZE` fully wired; keep-green install edits present;
`run-tests.yml` triggers on `pull_request:[rewrite]` and `pdsfile_main_test.sh`
includes `tests/api/`; **no file under `pdsfile/` modified**; full suite collects
(713 tests, exit 0) under the new config with real holdings; no confidentiality
leak in the diff.

## Minor findings and disposition (both FIXED — comment/record only)

1. **`scripts/run-all-checks.sh` pytest-branch comment referenced `--cov=psfmodel`**
   (a different project) and claimed coverage comes from addopts (false for
   pdsfile). **Fix:** reworded the comment to reflect pdsfile reality (`-n`/`--cov`
   passed here, not in addopts; branch disabled until the hermetic pytest phase,
   which re-points the target). No behavior change (disabled branch, comment only).
2. **`critiques/pr-03-04/validation.md` recorded "629 tests collected"** while the
   full self-hosted path set collects 713. **Fix:** corrected the record to 713
   (the full path set) and noted the 629 was a narrower spot-check. Record-only.

## Deferred (out of scope; logged)

- `validation.md` mentions `/data/pdsdata` in prose — an already-established
  record-keeping convention (present on `rewrite` in the plan and
  `critiques/pr-02/validation.md`); not a functional config path, not new here.
- `scripts/dump_public_api.py` RUF100 ratchet entry — frozen post-PR-02,
  already logged in `critiques/deferred-observations.md`.

## Owner decisions (confirmed 2026-07-23)
Both flagged template deviations approved by the owner: (1) dev self-ref uses the
distribution name `rms-pdsfile[docs]`; (2) coverage omits `fail_under`/`parallel`
to keep the existing self-hosted gate green.

## Convergence
Sole findings were two cosmetic comment/record Minors on a `goal met` verdict,
both resolved without any logic or config change (gates re-confirmed green).
Loop converged.
