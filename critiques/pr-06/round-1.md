# PR-06 adversarial review — round 1 (to convergence)

Fresh, no-context reviewer subagent (§6.6), scoped to
`origin/rewrite...pr-06-tools-into-package`. Charged to find anything BROKEN,
INCONSISTENT, or STRANDED after moving the tools into the package — especially
stranded old-path imports that would ImportError post-move.

## Findings
**None.** Zero defects. Converged in one round.

## Verified clean by the reviewer
- **Stranded-reference hunt:** zero bare `from/import holdings_maintenance`
  anywhere in committed source/config/scripts; no `utility/show_opus_products`
  refs outside `plans/`; remaining `re-validate`/`shelf-consistency-check` hits
  are all DATA (log filenames, `dir='re-validate'`, header comments), not
  module/import/entry-point refs; no `sys.path.insert`/`REPO_ROOT` left in the
  moved tools; no old-root `pdsfile/` path in configs/scripts.
- **Imports resolve:** the six non-self-executing tool modules import cleanly;
  `re_validate.py` reaches its `Missing volume path` print without ImportError
  (all 5 top imports resolve — pre-existing import-time execution, not a
  finding).
- **Removed-import strands:** `sys` kept and used in both hack files; `pathlib`/
  `Path(` fully gone; `show_opus_products.py` imports/uses `os` and defines both
  `PDS{3,4}_HOLDINGS_DIR` before the `.preload()` calls.
- **Packaging:** `pip install -e .` exit 0; `find_packages('src',
  include=['pdsfile*'])` includes `pdsfile.holdings_maintenance`, `.pds3`,
  `.pds4`, `pdsfile.tools`; all 11 console scripts resolve and `--help` exit 0.
- **Ruff/ratchet:** `ruff check src/pdsfile scripts conftest.py` clean; no
  per-file-ignores key still starts with `holdings_maintenance/` or `utility/`;
  `gen_ruff_ratchet.py` runs exit 0, TARGETS reduced, self-consistent with the
  committed pyproject.
- **API-freeze:** passes.

## Convergence
No findings; loop converged immediately. Reviewer verdict: "No defects found.
PR is behavior-preserving as claimed."
