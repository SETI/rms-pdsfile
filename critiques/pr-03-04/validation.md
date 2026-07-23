# PR-03+04 validation record — template adoption + pyproject consolidation

Combined per owner instruction (2026-07-23): PR-04 (adopt `repo_template` support
files) + PR-03 (consolidate tool config into `pyproject.toml`), one PR, pyproject
built from the template. Phase 1 is config-only — **no source under `pdsfile/`
was touched**.

## Gates active in Phase 1 for this PR
- `ruff check` (ratcheted) — introduced this PR.
- API-freeze manifest test — from Phase 0.
- pyroma — introduced this PR.
- Full-data suite — Phase-1 boundary check.
(ruff-format, hermetic pytest, sphinx, pymarkdown, mypy/bandit/vulture are NOT
gated yet — staged per the plan.)

## Results
- **`scripts/run-all-checks.sh`** (only the three PR-04 gates enabled): **all
  passed** — ruff check clean (ratchet), pyroma **10/10**, API-freeze passed
  hermetically in 0.64s (via `--confcutdir=tests`, no holdings).
- **`ruff check pdsfile holdings_maintenance utility scripts conftest.py`**:
  clean. The `[tool.ruff.lint.per-file-ignores]` ratchet (67 files, auto-generated
  by `scripts/gen_ruff_ratchet.py`) captures the 3097 pre-existing violations so
  the gate passes; it may only shrink later.
- **`pip install -e .`**: succeeds; `import pdsfile` works with no holdings env;
  all 11 console scripts resolve.
- **Full-suite collection** under the new pyproject (`--strict-markers`,
  `--strict-config`, `full_holdings` marker, `--mode ns`): the complete
  self-hosted path set (`tests/api/` + both `pds{3,4}file/tests/` + all
  `rules/*.py`) collects **713 tests, no errors** — the new config does not break
  collection or the custom options. (An earlier spot-check over a narrower path
  subset showed 629; both collect cleanly.)
- **Full-data `--mode ns` suite** (against the limited testing holdings copy,
  resolved from `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR` — the set the test
  goldens are tuned to): **679 passed, 34 skipped, 0 failed** (28s). The 34 skips
  are legitimate (PDS4 bundles not present in that holdings set; the tests skip
  gracefully). See `critiques/pr-03-04/fulldata_ns.md`.
  - **Root-dependent goldens (not caused by this PR):** the same suite run
    against the *complete* `/data/pdsdata` set showed **6 failures**
    (`test_opus_products` / `test_opus_id_to_primary_logical_path` /
    `test_label_basename` for COUVIS_0001, COCIRS_0406, CORSS_8001, COVIMS_8xxx,
    NHxxxx). All 6 are data/golden assertions (`assert abspath in
    opus_id_abspaths`, etc.) whose expected values are tuned to the limited
    testing copy, so they legitimately differ against the complete set. This is
    expected root-dependent behavior, not a rewrite regression (no `pdsfile/`
    source changed) — exactly the case the plan's Phase-0 baseline note
    anticipates. Local test runs use the limited testing copy from now until a
    later phase (owner, 2026-07-23).

## Behavior preservation
No file under `pdsfile/` was modified, so the full-data pass/fail set is
unchanged by construction. The self-hosted `run-tests.yml` now also triggers on
`pull_request` to `rewrite`, so opening this PR runs the full two-mode suite
(now including `tests/api/`) on the self-hosted runner as the belt-and-suspenders
full-data gate.

## Keep-green edits beyond the plan's literal PR-04 bullets (all licensed as
"minimal edits to keep gates green" by the config change)
- `requirements.txt` → `-e .` means the self-hosted suite no longer gets
  `coverage` from `requirements.txt`; so `pdsfile_main_test.sh` and
  `run-tests.yml` now install `-e ".[dev]"` (template pattern) instead of
  `-r requirements.txt`. Without this the self-hosted `python -m coverage` step
  would fail.

## Deviations from the template (flagged to owner)
1. **dev extra self-reference uses the distribution name `rms-pdsfile[docs]`**,
   not a literal `pdsfile[docs]` — the module is `pdsfile` but the distribution
   is `rms-pdsfile`; a literal `pdsfile` dependency would be a different /
   nonexistent distribution and break `pip install .[dev]`.
2. **Coverage config omits the template's `fail_under = 90` and `parallel =
   true`.** The self-hosted `pdsfile_main_test.sh` runs `coverage report` /
   `coverage run -a` without `coverage combine`, and current coverage is < 90
   (untested maintenance tools, issue #82); either option would turn the
   existing self-hosted gate red. `fail_under` can return in Phase 8 once #82
   raises coverage.

## Deferred
- `scripts/dump_public_api.py` (frozen post-PR-02) carries a `# noqa: BLE001`
  for a rule not in the `select` set, so it trips **RUF100** and is ratcheted
  (`["RUF100"]`). Not fixed here because the dumper is frozen (plan §6.4
  prohibition). Could be cleaned in a later PR with owner sign-off (comment-only,
  freeze-neutral). Logged in `critiques/deferred-observations.md`.

## Adversarial review
See `critiques/pr-03-04/round-*.md`.
