# Validation — removal of `shelf_consistency_check`

Base `6f5c718` (`fix/archive-infoshelf-rebuild`). Branch
`chore/remove-shelf-consistency-check`. Owner instruction 2026-08-16, recorded in
`plans/2026-08-16-shelf-consistency-check-removal-addendum.md`; the capability gap
is issue #156, which this PR references and does not close. Every number below
carries the command line that produced it.

Environment for every measured run: `venv/bin/python` (3.12.3),
`PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`,
`PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings` (read-only),
`PDSFILE_TEST_HOLDINGS=full` where a full-tree pytest run is stated.

## 1. What the tool was, measured before deleting it

The program walked the trees named on its command line and examined a directory
only if `shelves` appeared in its path with `info`, `links` or `index` as the
first component below it, deriving each holdings counterpart by string
substitution on the path text. The holdings trees here have never used that
layout, and a run proves it:

```
$ python -m pdsfile.holdings_maintenance.pds3.shelf_consistency_check "$PDS3_HOLDINGS_DIR"
Tests performed: 0
Errors found: 0
```

(run at base `6f5c718`, read-only, exit 0 — a clean report about an empty search.)

The history behind that, each verified against git here and independently by both
review rounds:

- `git log --format="%H %ad %s" --date=short a6f3949 -1` — the tool arrived
  2023-12-06 in `a6f3949` ("Add validation directory (moved from rms-webtools
  repo)") as `validation/shelf-consistency-check.py`.
- At that same commit the package already used the current layout:
  `git grep -n 'holdings/_infoshelf' a6f3949 -- pdsfile/pdsfile.py` (line 1253,
  and the `('_infoshelf-', '_info')` table at line 348),
  `git grep -n '_infoshelf' a6f3949 -- validation/pdsdependency.py` (the
  `_infoshelf-%s` patterns at 323-332), and
  `git grep -n '_infoshelf-volumes' a6f3949` in
  `pdsfile/pds3file/tests/test_pds3file_blackbox.py` (line 659 and others). The
  layout the tool searched for did not exist in this repository on the day it
  was added.
- `git log --all -S'shelves/info'` — four commits, all touching the tool's own
  docstring, its user-guide chapter, or critique records. No other code ever
  carried the string.
- `git show a6f3949:validation/shelf-consistency-check.py` — the missing
  index-label branch read `error += 1` where every sibling branch read
  `errors += 1`: a `NameError` on the finding path. Fixed in `67f7b93`
  ("fix: count an extraneous index shelf instead of dying on it", 2026-08-06).

## 2. What was removed and edited

Deleted (3): `src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py`,
`tests/holdings_maintenance/test_shelf_consistency_check.py`,
`docs/user_guide/user_guide_shelf_consistency_check.rst`.

The deleted test file held 18 test functions collecting as **19** tests
(`pytest tests/holdings_maintenance/test_shelf_consistency_check.py
--collect-only -q` at base: "19 tests collected";
`test_help_names_the_flag_and_the_positional` is parametrized over
`--help`/`-h`).

Edited: every current-state reference and count found by
`grep -rniE "shelf_consistency_check|shelf-consistency-check|shelf consistency"`
over the tree, plus the indirect ones (tool pairings, "the two tools",
`allow_abbrev` prose, `HOLDINGS_FREE_TOOLS`). The PR diff is the authoritative
list. Historical records — `critiques/pr-*/`, `plans/archive/`, dated subplans
and addenda, `critiques/deferred-observations.md` (the frozen source register),
and dated narrative paragraphs inside open observations — keep their mentions by
design; both review rounds checked the classification.

Counts corrected by recounting, not decrementing:

| claim | before | after | where |
|---|---|---|---|
| command-line programs | fifteen | fourteen | README.md, installation, concepts, maintenance-tools, extending-tools |
| programs that resolve holdings paths | thirteen of the fifteen | thirteen of the fourteen | installation.rst |
| programs that never resolve one | two (crlf, this tool) | one (crlf) | installation.rst |
| take paths on the command line | the other fourteen | the other thirteen | installation.rst, show_opus_products.rst |
| programs that write log files | twelve of the fifteen | twelve of the fourteen | installation.rst |
| non-shared-command-line programs | five | four | maintenance_tools.rst |
| `python -m` programs | four | three | README.md, installation.rst, repository-layout |
| pds3 package modules | ten | nine | `pds3/__init__.py` |
| self-parsing pds3 tools | four (dividing two and two) | three | `holdings_maintenance/__init__.py`, `_common.py` |
| tool modules sharing `--log`/`--quiet` text | eleven of the fourteen | eleven of the thirteen | `re_validate.py` |
| tools with `allow_abbrev=False` | two | one (crlf; `git grep allow_abbrev src/` shows the single site) | `re_validate.py` docstring |
| never-console tools in `TOOL_MODULES` | three | two | `tests/holdings_maintenance/support.py` |
| `HOLDINGS_FREE_TOOLS` | {crlf, shelf_consistency_check} | {crlf} | support.py |
| API-reference modules | 78 of 78 | 77 of 77 | measured by both Sphinx builds, below |

Register upkeep: entries **3004** and **4033** discharged as superseded by issue
#156; `critiques/observations.md` now reads 212 open (10 + 0 + 16 + 134 + 52,
verified by `grep -c "^### "` per file) and the closure equation
375 − 28 − 119 − 24 + 8 = 212 balances. Plan upkeep: Phase 6 deferred-table
entry 6 marked superseded; ground rule 9 and settled decision 4 carry dated
owner-exception notes; the §6.4 addendum is
`plans/2026-08-16-shelf-consistency-check-removal-addendum.md`.

Not changed, verified: `tests/api/api_manifest.json`,
`scripts/dump_public_api.py`, `tests/api/test_api_freeze.py`,
`scripts/stubtest_allowlist.txt`, `[project.scripts]` (eleven entries),
`.github/`. `pyproject.toml` changed in comments only — the per-file-ignores
ratchet had no entry for either deleted file, so it neither shrank nor grew.
`grep -rln shelf_consistency scripts/ .github/` finds nothing;
`scripts/check_runtime_imports.py` never enumerated the module.

## 3. Gates, measured

`./scripts/run-all-checks.sh` (default full parallel run, both holdings roots
exported), log read in full, at `f6b9759`:

- ruff check and ruff indentation: passed.
- pytest, one `--mode ns` pass over `tests/`, holdings full:
  **`1190 passed, 34 skipped`** (was 1209/34 at base). The delta is **19**, which
  is exactly the deleted file's collected count: 1190 + 19 = 1209. The
  owner-stated expectation of "18 removals" was the function count; the
  parametrized help test collected twice. No other outcome changed: the two
  s-mode passes below are byte-identical to baseline and the ns skip count is
  unchanged (the deleted file's one holdings-marked test ran and passed in
  full-tree context, so no skip left with it).
- s-mode, pds3: `pytest tests/pds3file/ tests/rules/pds3/ --mode s -q` —
  **`555 passed, 3 skipped`**, the baseline exactly.
- s-mode, pds4: `pytest tests/pds4file/ tests/rules/pds4/ --mode s -q` —
  **`123 passed, 31 skipped`**, the baseline exactly.
- pyroma: 10/10. API-freeze: 1 passed (the manifest is untouched).
  Clean-install gate: passed. Stubtest: "Success: no issues found in 78 modules"
  (stubtest counts stub files, which never included the tool; the source-tree
  count is the Sphinx one below).
- Sphinx, both builds (`-W` and `-n -W`, separate build dirs): exit 0,
  0 problem lines each, and both report
  **`API reference: 77 of 77 modules under .../src documented`** — down from
  78 of 78, measured at the base branch with `docs/conf.py`'s own
  `_module_names_under()`. The drop is exactly one, the deleted module.
- PyMarkdown: 2 files scanned (README.md, CONTRIBUTING.md), passed.

`pytest tests/holdings_maintenance -q --mode ns` at head: **409 passed** in
166 s — no import error, no orphaned fixture (`legacy_tree` and `counts()` were
local to the deleted file; `fresh_tree`, the subsets and both in-process runners
are still used by the surviving modules).

## 4. Review rounds

§6.6 loop, fresh no-context reviewer each round, records in
`critiques/shelf-consistency-check-removal/`:

- **Round 1** (`f6b9759`): 1 Major (settled decision 4 unannotated), 5 Minor.
  All fixed except Minor 6 (the pyproject comment style), rebutted in the round
  record. The reviewer independently re-verified all five historical claims and
  every count.
- **Round 2** (`9c44730`): 1 Major (ground rule 9 unannotated — the same defect
  class as round 1's Major, one section over), 2 record-accuracy Minors, 1
  Deferred (the suite numbers traced to no recorded run — this record now
  carries them). All fixed or resolved.
- **Round 3**: see `round-3.md` — the terminating round.
