# PR-34 validation — the README rewrite, and the PyMarkdown gate

Base: `62c8192` (`docs/dev-guide`, the PR-33 head — this PR stacks on #152 and
retargets to `rewrite` after it merges). Branch: `docs/readme-rewrite`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3, Sphinx 9.1.0, PyMarkdown
0.9.39), from the tree being measured. Where holdings are needed the environment
carried `PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`.

## 0. Plan of record

PR-34 is marked M, so this section is the plan. Files, in the order they are
touched:

1. `README.md` — rewritten per `doc_readme.mdc`: title first (fixes `MD041` by
   construction), badges second, the `<!-- start-after-point -->` marker after the
   badge block and still after the one H1 (entry 1200: before the H1 it doubles the
   front-page title; past any content it silently removes that content from the
   front page), then introduction, features, installation, quick start with one
   module example and one CLI invocation, documentation, contributing, license.
   The second H1 is dropped (fixes `MD025` by construction).
2. `CONTRIBUTING.md` — the testing section documents the holdings environment
   variables (placeholders only), `--mode`, and the graceful-skip behavior
   (entry 1201); false claims in the sections around it are corrected against the
   tree (mypy does not run here; inline type annotations are not used).
3. `docs/user_guide/user_guide_installation.rst` — one supported-version sentence:
   the floor moved to 3.11 when `rewrite` merged #146, which updated
   `pyproject.toml`, both CI matrices, `README.md` and `CONTRIBUTING.md` but not
   this page; `doc_readme.mdc` section 3 requires the README's supported-version
   statement to be consistent with the packaging metadata *and* the user guide,
   so the page moves with it.
4. `scripts/run-all-checks.sh` — `ENABLE_PYMARKDOWN` defaults true, and the
   header comments say so. That is the whole CI change as well: both CI jobs run
   this script or a wrapper of it, and the script is the single source of truth
   for the enabled set (`environment.mdc`), which is exactly how the Sphinx gate
   was enabled at `8840ebb`.
5. `critiques/pr-34/round-<k>.md`, this record, and the register files —
   entries 1200 and 1201 are discharged.

Verification, in order: the module example and the CLI invocation executed
against real holdings before being committed; the PyMarkdown gate run and its
full output read, with the set of files it scanned recorded (a scan of nothing
passes); `scripts/run-all-checks.sh` in full with holdings, every section's
output read; the rendered Sphinx front page opened and its README content
confirmed present (entry 1200 — both builds pass green with an emptied front
page, so exit statuses prove nothing here); then the §6.6 loop to convergence.

## 1. What changed

*(measured at head — filled in as the work lands)*

## 2. The README, claim by claim

*(filled in after the rewrite)*

## 3. The PyMarkdown gate: what it scanned

*(filled in after the gate is enabled)*

## 4. Gates at head

*(filled in after the full run)*

## 5. The front page

*(filled in after the rendered-page check)*

## 6. The reviews

*(filled in as rounds complete)*
