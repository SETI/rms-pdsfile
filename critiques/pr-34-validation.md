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

One file joined the list while the gates ran: `docs/conf.py`, nine lines, for the
reason section 5 measures — the rewritten README's sections reach the front page
as H2 under the page's own H1, and myst calls that a defect once per heading.

Verification, in order: the module example and the CLI invocation executed
against real holdings before being committed; the PyMarkdown gate run and its
full output read, with the set of files it scanned recorded (a scan of nothing
passes); `scripts/run-all-checks.sh` in full with holdings, every section's
output read; the rendered Sphinx front page opened and its README content
confirmed present (entry 1200 — both builds pass green with an emptied front
page, so exit statuses prove nothing here); then the §6.6 loop to convergence.

## 1. What changed

| | |
|---|---:|
| `README.md` | rewritten, 154 lines against the old 30 |
| `CONTRIBUTING.md` | testing section rewritten; three false claims corrected |
| `docs/user_guide/user_guide_installation.rst` | 1 sentence (3.10 → 3.11) |
| `docs/conf.py` | `suppress_warnings = ['myst.header']`, with its comment |
| `scripts/run-all-checks.sh` | `ENABLE_PYMARKDOWN` true; the scan names its files |
| files changed under `src/` | **0** |
| scheduled observations discharged | 2 (entries 1200, 1201) |
| observations added | 3 (3402, 4318, 4406) |

## 2. The README, claim by claim

The defect a README rewrite most easily ships is a fluent claim about the package
that the package does not honor. Every executable claim was executed:

* **The module example was run verbatim** (with the placeholder root replaced by
  a real one) before being written down. All four printed comments are that
  run's output: `Narrow-angle image, VICAR`, `co-iss-n1460960653`,
  `N1460960653_1.LBL`, and a four-viewable `PdsViewSet` for the preview line,
  whose comment describes rather than quotes because the literal `repr` embeds
  an absolute machine path.
* **The CLI invocation was run**: `pdsinfoshelf --validate` against a real
  `COUVIS_0001`, exit 0. The `--validate` flag and the positional volume path
  were also checked against the parser's own `--help`. The `$PDS3_HOLDINGS_DIR`
  spelling is the user guide's convention for the same command.
* **Python floor 3.11**: `pyproject.toml` `requires-python = ">=3.11"`,
  classifiers 3.11/3.12/3.13. (The overrides file still says 3.10; that is
  observation 3402, left to the owner.)
* **The eleven console-script names** are `[project.scripts]`, verbatim, and the
  four `python -m` programs are the user guide's list of four.
* **Badges**: every target is this repository's — the same shields.io set the
  README already carried (all `SETI/rms-pdsfile` URLs), plus the
  Documentation Status badge in the sibling `rms-cloud-tasks` pattern. The RTD
  project `rms-pdsfile` exists (its badge answers, reading "failing"); the
  `/en/latest` page 404s today because RTD last built a tree with no
  `docs/conf.py`. The Documentation links point there anyway because
  `pyproject.toml`'s `Documentation` URL is that address — the README follows
  the packaging metadata, and both go live when this branch merges and RTD
  rebuilds. The license and forks badges now carry links (rule: every badge
  links to its source); LICENSE and CONTRIBUTING links use absolute GitHub URLs
  so they resolve from the rendered docs as well as from the code host.
* **Marker discipline (entry 1200)**: the H1 stays the first heading, the marker
  stays after it (and after the badges, which `doc_readme.mdc` section 1
  requires); nothing below the marker was removed from the include. The proof
  is section 5's rendered-page check, not the build exit statuses.

`MD041` is fixed by the title opening the file; `MD025` by the second H1's
content surviving as the introduction's "product of the PDS Ring-Moon Systems
Node" line instead of a heading.

## 3. The PyMarkdown gate: what it scanned

`ENABLE_PYMARKDOWN` now defaults true in `run-all-checks.sh`, which is the whole
CI wiring: the hosted lint job runs the script itself, so the gate runs there on
the next push, exactly as the Sphinx enable worked.

**The gate scans two files, and says so on every run.** The plan's PR-34 section
records the scope as "`README.md`, `CONTRIBUTING.md` and the five `SKILL.md`
files"; measured, that is wrong about the last five. `pymarkdown scan` selects
by the `.md` extension **and does not recurse into directory arguments**, so of
the four scan paths — `docs/`, `.cursor/`, `README.md`, `CONTRIBUTING.md` — the
two directories contribute nothing: `docs/` holds no `.md` at any depth, and
`.cursor/`'s five Markdown files sit two levels down, unread. The plan's
"exactly two findings at `532f65d`" measurement was made with this same
non-recursive invocation, so the two-finding count and the seven-file scope
claim were never consistent with each other; the count was right, the scope
claim was not. Measured with `-r` added, the five nested files carry 130
findings — that and the front-matter artifact behind 95 of them are recorded as
observation 4318, for whoever ever widens the gate's scope.

So the honest statement is: **the gate reads `README.md` and `CONTRIBUTING.md`**
— no `.rst` page, no `.mdc` rule file, none of the `.cursor` skills' Markdown,
and not `CODE_OF_CONDUCT.md`. To keep that fact visible rather than implied, the
gate now prints the file list `--list-files` reports before scanning and fails
on an empty selection (the previous code returned success when it found nothing
to scan — the shape observation 3304 warns about). At head it prints both
files and passes:

    PyMarkdown will scan 2 file(s):
    /.../CONTRIBUTING.md
    /.../README.md
    PyMarkdown scan passed (2 file(s) scanned)

At base, the same configuration reports exactly the plan's two findings, both
in `README.md` (`MD041`, `MD025`), reproduced before the rewrite.

## 4. Gates at head

`scripts/run-all-checks.sh` was run in full, sequentially, with the holdings
variables set, and its output read end to end. The first full run failed — that
run is the evidence behind section 5 — and the run after the `conf.py` fix is
the one recorded here. Exit **0**. What each gate measured:

| gate | measured |
|---|---|
| `ruff check` | All checks passed (both passes: configured rules, and the E111/E112/E113 indentation pass) |
| pytest (`--mode ns`, full holdings) | **1205 passed, 34 skipped** — identical to the baseline |
| pyroma | 10/10 |
| API freeze | 1 passed |
| clean install | all runtime modules import with no dev extras |
| Sphinx `-W` | exit 0, **0 problem lines**, API reference 78 of 78 modules |
| Sphinx `-n -W` | exit 0, **0 problem lines**, API reference 78 of 78 modules |
| PyMarkdown | 2 files scanned (named above), 0 findings |

The two shelves-only suites, same environment:

| suite | result |
|---|---|
| `tests/pds3file tests/rules/pds3 --mode s` | **555 passed, 3 skipped** |
| `tests/pds4file tests/rules/pds4 --mode s` | **123 passed, 31 skipped** |

All at baseline. Nothing under `src/` changed
(`git diff 62c8192 --name-only -- src/` is empty), so nothing could move.

## 5. The front page

Entry 1200's point is that both Sphinx builds pass green over an emptied or
doubled front page, so the page itself was read, twice.

**The first full gate run failed, and the failure was real**: with the
rewritten README, both builds died on seven `myst.header` warnings — "Document
headings start at H2, not H1", one per README section, because the fragment
after the marker now begins at `## Introduction` where the old fragment had no
headings at all. That is the include working as designed (the H1 and the badges
above the marker are host-only by rule), so `docs/conf.py` suppresses
`myst.header`, with a comment scoping why; README.md is the only Markdown
source in the build. The suppression's cost is that a future Markdown page with
a genuinely broken heading hierarchy would not warn — accepted, because README
is the only such page and its headings are exactly the seven the rule requires.

**The rendered page, `docs/_build/html/index.html`, verified after the clean
run** by parsing the HTML:

* exactly **one `<h1>`**: `rms-pdsfile` (the page's own title);
* the seven README sections all present as `<h2>`: Introduction, Features,
  Installation, Quick Start, Documentation, Contributing, License;
* **no badge leaked**: `img.shields.io` does not appear in the page;
* the content is really there — the rendered text contains
  `pdsinfoshelf --validate`, `pip install rms-pdsfile`, `from_logical_path`,
  `Narrow-angle image, VICAR` and the introduction's opening sentence, quoted:

  > rms-pdsfile is the interface to a holdings tree: the directory tree in
  > which the PDS Ring-Moon Systems Node keeps the planetary data it
  > publishes …

## 6. Scheduled entries and the register

Entry **1200** is discharged: the marker constraint is honored, the second-H1
cost it recorded is gone (the rewrite ends the page with the License section,
not a bare heading), and the verification it demanded — looking at the rendered
page — is section 5. Entry **1201** is discharged by the CONTRIBUTING testing
section. Both entries and their PR-34 heading leave
`critiques/observations-scheduled.md`; the register arithmetic in
`critiques/observations.md` moves two entries out of scheduled and adds the
three found here (3402: the overrides file still gives the floor as 3.10;
4318: the Markdown gate's real scope; 4406: the `--mode` comment's stale
pds3-only claim, from round 1), leaving 213 open.

Also corrected while touching CONTRIBUTING, each a claim false against the
tree: the "run mypy" PR-checklist item (no check here runs mypy), the
type-hints mandate (this codebase does not use inline annotations), the
`NDArrayFloatType` example signature (a type from another repository), and the
Windows venv hint (Windows is not a supported platform).

## 7. Standing rules

- The four frozen files (`tests/api/api_manifest.json`,
  `tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py`,
  `tests/api/test_api_freeze.py`) and `pyproject.toml` are byte-identical to
  `62c8192`, verified by `git diff --quiet` per file.
- No golden or baseline was edited; no test was skipped or xfailed; the ratchet
  did not move; `ruff format` was not run.
- No absolute holdings path appears in any committed file: the diff's added
  lines were scanned for both roots' components; the only match is this
  record's interpreter line, which names the repository, not the holdings.
- Line endings are LF in every changed file.
- `git status --porcelain -uall` shows no untracked build artifacts after the
  full runs.

## 8. The reviews

Every round a fresh no-context subagent; recorded in
`critiques/pr-34/round-<k>.md`.

*(filled in as rounds complete)*
