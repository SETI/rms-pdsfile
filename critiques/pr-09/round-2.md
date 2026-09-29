# PR-09 adversarial review — round 2 (confirming)

Reviewer: a second fresh, no-context Opus subagent, steered at the angles round 1
touched less: `--update`, xdist (`-n --dist loadscope`), worker resolution
consistency, strict-markers interaction with dynamically-added skips, placeholder
leakage (any test that RUNS rather than skips with no holdings), api-freeze under
plain `pytest tests`, and lint on the new file.

## Verdict: GOAL MET — zero Major, zero Minor findings

No fixes were made between round 1 and round 2 (round 1 found nothing), so this is
a confirming pass with a fresh reviewer per the "each round gets its own fresh
adversarial pass" discipline. Convergence reached.

## Additional angles proven (beyond round 1)
- `--update` regenerates goldens identically under full; under no-holdings the
  run skips and writes nothing (the golden write in
  `tests/support/pdsfile_test_helper.py` is never reached because items skip
  first). `git status tests/golden` clean afterward.
- xdist: `-n 2 --dist loadscope` under full → 555 passed / 3 skipped; under
  no-holdings → 558 skipped, no collection error. `pytest_configure` runs in every
  worker, so `config._pdsfile_holdings` is set per worker.
- Consistency: `resolve_holdings()` is a pure function of the environment, which
  all workers inherit identically → conftest and both helper modules always agree.
- `--strict-markers`/`--strict-config`: dynamically added `pytest.mark.skip` is a
  builtin, exempt from strict checking; all runs used the strict addopts and passed.
- Placeholder leakage: with no holdings, all 713 items skip (0 executed). No test
  module does filesystem work at import scope; the placeholder is crafted to
  satisfy the module-scope `.index('holdings')` / `.rindex('pdsdata')` / f-string
  joins so import never raises, and the nonsense paths are never dereferenced.
- api-freeze passes isolated, under whole-tree collection, and inside the full run;
  the new preload does not perturb the frozen import surface.
- `ruff check tests/support/holdings.py` (and the whole tree) clean; no new
  per-file-ignore needed.

## Minor (per-spec, no code change)
- With `PDS{3,4}_HOLDINGS_DIR` set but `PDSFILE_TEST_HOLDINGS` and
  `PDSFILE_TEST_DATA_DIR` unset, the suite silently skips everything — exactly the
  spec'd default. CI is safe (`pdsfile_main_test.sh` exports the full flavor). A
  one-line contributing/README note would help developers used to the old
  "set the holdings dirs and run pytest" habit. Documenting holdings env vars is a
  PR-32 (docs phase) deliverable; the resolver module docstring already states the
  semantics in-code. Deferred, not a PR-09 defect.

## Deferred
- The `full_holdings` marker mechanism is implemented but no committed test carries
  the marker yet; annotating the size/volume-count tests is later-PR work.
