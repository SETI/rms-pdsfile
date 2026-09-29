# PR-05 adversarial review — round 1 (to convergence)

Fresh, no-context reviewer subagent (§6.6), scoped to the move diff
(`origin/rewrite...pr-05-src-layout`). Charged to find anything BROKEN or
INCONSISTENT after the move; move-only, nothing stranded at the old path.

## Findings

1. **`scripts/gen_ruff_ratchet.py:18` — stale comment (low, cosmetic).** The
   `TARGETS` line was updated to `src/pdsfile`, but its annotating comment still
   read `(no src/ layout yet)`, contradicting the code and out of step with the
   sibling comments in `run-all-checks.sh` and `pyproject.toml` that were
   rewritten for PR-05. **Fixed** — comment rewritten to describe the src/ move.
   Non-breaking; no code change.

No functional defects found.

## Verified clean by the reviewer
- 119 renamed files, 0/0 line changes; no renamed source file carries a content
  edit.
- Non-rename edits all correct: dual-discovery `packages.find`
  `where = ["src", "."]` + `include`; `write_to = src/pdsfile/_version.py`; all
  50 per-file-ignores keys reprefixed; `RUFF_TARGETS`/`TARGETS`/CI pytest paths
  repointed.
- No stranded old-path refs in executable/config files (only knowingly-stale
  `run_tests_coverage.sh`, historical docs, and URL substrings — all expected).
- Packaging TESTED: `pip install -e .` → `import pdsfile` under `src/pdsfile`;
  console scripts resolve; `holdings_maintenance` still imports (dual discovery).
- Ruff ratchet clean at the new path; setuptools_scm + gitignore correct;
  API-freeze passes; coverage `source = ["pdsfile"]` correct as an import name.

## Convergence
One cosmetic finding, fixed. Reviewer's verdict: "the move is functionally
sound; no functional defects." Loop converged in one round.
