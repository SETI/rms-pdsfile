# PR-34 round 1 — full diff

Reviewer: a fresh, no-context subagent given the PR-34 plan section, the Phase 7
preamble, the §2 ground rules, §6.1–§6.7 with the progressive-compliance schedule,
the exact diff `git diff 62c8192..a612220`, and read access to the repository and
the holdings roots, with the instruction to verify every claim against the tree
rather than against the diff or the records. It made no edits.

The reviewer independently reproduced the cheap gates and measurements: the
PyMarkdown gate at head (pass, 2 files named) and at base in its own worktree at
`62c8192` (exactly the plan's two findings, `MD041` and `MD025`, both `README.md`);
the empty-selection failure path (`pymarkdown scan --list-files docs/` exits 1);
the 130-finding `-r` measurement with its 95/35 split, including the front-matter
attribution (95 findings vanish with the extension enabled — a stronger check than
this PR's own, which inferred the attribution rather than toggling it); both Sphinx
builds (exit 0, 0 problem lines, 78 of 78); the rendered front page (one `<h1>`,
seven `<h2>`, no shields.io, content present); the quick-start module example
verbatim against the real holdings (all four outputs match); `pdsinfoshelf --help`
against the README's invocation; the eleven console-script names against
`[project.scripts]`; the badge and link targets (RTD project answers, `/en/latest`
404s — as the record admits); the freeze files and `pyproject.toml` byte-identity;
LF endings; the absence of holdings paths in added lines; and the register
arithmetic (12/0/17/131/52 = 212 at that head). On the full-data suite it verified
the evidence rather than re-running: no file under `src/` changes, so the recorded
baseline cannot be stale.

Verdict: **goal not met** — one Major, four Minor, three Deferred.

## Major finding, and its resolution

**M1. `CONTRIBUTING.md`'s testing block did not work as written — the entry-1201
discharge was unsound.** The section exported the two holdings roots and ran
`pytest tests --mode ns`, but `tests/support/holdings.py::resolve_holdings` never
consults the roots unless `PDSFILE_TEST_HOLDINGS=full` is set: with the selector
unset the session is `_skip_config()`, and the reviewer proved it empirically —
CONTRIBUTING's exact environment produces `SKIPPED ... no holdings available (set
PDSFILE_TEST_HOLDINGS)` on a data test. A contributor following the section would
get precisely the mostly-skipped run entry 1201 complained about, under a
paragraph explaining why such a run proves nothing. (`run-all-checks.sh` fills the
selector in automatically, which is how this PR's own gate runs passed and how
the omission survived the author's testing — the author never ran the block as a
contributor would.) **Fixed**: the block now exports `PDSFILE_TEST_HOLDINGS=full`,
with a sentence saying the selector is what makes a bare `pytest` run use the
roots, matching the dev guide's setup block.

## Minor findings, and their resolutions

1. The gate's failure path printed "found no Markdown files" for *any* nonzero
   `--list-files` exit, misdiagnosing a config or plugin error as an empty
   selection. **Fixed**: the message is now neutral ("empty selection or scan
   error") and pymarkdown's own output is printed under it.
2. Record §1 said "129 lines against the old 31" — a diff insertion count posing
   as a file length. **Fixed**: 153 against 30, both measured.
3. Two README links whose text names a specific chapter ("installation chapter",
   "has a chapter on each") pointed at the docs root. **Fixed**: both now point
   at the chapter pages (`user_guide/user_guide_installation.html`,
   `user_guide/user_guide.html`), whose paths the built tree confirms.
4. Observation 4318's residue sentence read as if the `MD040` sat in
   `reference.md`. **Fixed**: the finding's file (the run-all-checks skill's
   `SKILL.md`) is named.

## Deferred

1. `tests/conftest.py`'s `--mode` comment says "'s' covers pds3 only", which the
   pds4 `--mode s` baseline (123 passed) contradicts → **added as observation
   4406** (Documentation and records).
2. No automated check guards the front-page include against an emptied fragment
   → already deferred entry 341; the plan's chosen mitigation is the
   rendered-page check this PR performed and recorded. No new entry.
3. `pymarkdownlnt>=0.9.35` is unbounded, so a future release can change the CI
   gate's findings without a tree change → the same accepted class as
   `ruff>=0.8` and `sphinx>=7`, none of which carries an entry; the repository
   pins no gate tool. No new entry.

## Gates after the fixes

The fixes touched `CONTRIBUTING.md`, `README.md`, `scripts/run-all-checks.sh` and
records only — nothing under `src/`, so the full-data record carries forward
under §6.6 step 5. The PyMarkdown gate, both Sphinx builds and the rendered
front-page check were re-run on the corrected tree and pass with the same
numbers (2 files scanned, 0 findings; 0 problem lines, 78 of 78).
