# PR-05 validation record — move `pdsfile` to `src/` layout

Phase 2, first move. `git mv pdsfile src/pdsfile`. **Move-only: no source
under the package was edited** — the 119 tracked package files are pure renames
(`git diff --find-renames`: 119 R, 0 unpaired add/delete, 0 content lines
changed).

## Mechanical path updates (licensed move-PR edits to keep gates green)
- `pyproject.toml`: `[tool.setuptools]` explicit package list → dual-discovery
  `[tool.setuptools.packages.find] where = ["src", "."]`, `include =
  ["pdsfile*", "holdings_maintenance*"]` (console-script guard: the 11
  `[project.scripts]` still target `holdings_maintenance.*` at the repo root
  until PR-06, so `where = ["src"]`-only would un-package them).
- `setuptools_scm write_to` → `src/pdsfile/_version.py` (`.gitignore`'s
  `**/_version.py` already ignores it).
- `[tool.ruff.lint.per-file-ignores]` ratchet keys reprefixed `pdsfile/` →
  `src/pdsfile/` (50 keys); `scripts/gen_ruff_ratchet.py` `TARGETS` and
  `scripts/run-all-checks.sh` `RUFF_TARGETS` repointed to `src/pdsfile`.
- `scripts/automated_tests/pdsfile_main_test.sh` pytest paths repointed to
  `src/pdsfile/...`.
- `[tool.coverage.run] source = ["pdsfile"]` left as-is — it is an import
  package name, not a path, and resolves correctly to `src/pdsfile` under the
  editable install (verified).

`run_tests_coverage.sh` intentionally left stale (no workflow references it; the
plan deletes it in a later phase).

## Not done here (by design)
- No `py.typed` (deferred to PR-35 with the stubs; an empty marker would
  advertise `Any` for the whole package).
- No `pythonpath`/`testpaths` (PR-07).

## Gates
- `pip install -e .` succeeds; `import pdsfile` resolves to
  `src/pdsfile/__init__.py`; `setuptools_scm` writes `src/pdsfile/_version.py`.
- All 11 `[project.scripts]` resolve on PATH and import/run (`--help`
  spot-checked on `pdsinfoshelf`, `pds4infoshelf`).
- `scripts/run-all-checks.sh` green: ruff check (ratchet) clean, pyroma
  **10/10**, API-freeze manifest unchanged (the move adds/removes no public
  name).
- Full `--mode ns` suite (`tests/api/` + both `src/pdsfile/pds{3,4}file/tests/`
  + all `rules/*.py`) against the limited testing holdings: **679 passed, 34
  skipped, 0 failed** — unchanged from the pre-move baseline.

## Behavior preservation
No package source changed, so the full-data pass/fail set is unchanged by
construction. Opening the PR also fires the self-hosted `run-tests.yml`
full-data run on the `rewrite` PR trigger.

## Adversarial review
See `critiques/pr-05/round-1.md`. One finding (stale comment in
`gen_ruff_ratchet.py`), fixed; no functional defects.
