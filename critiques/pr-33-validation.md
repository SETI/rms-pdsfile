# PR-33 validation — the developer guide

Base: `96de70a`. Branch: `docs/dev-guide`. Base branch: `rewrite`. Closes issue #43.
Sub-plan: `plans/2026-08-16-pr-33-subplan.md`.

Python and Sphinx commands below were run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3, Sphinx 9.1.0,
sphinxcontrib-mermaid 2.1.0); `mmdc`, `grep`, `git` and the shell checks ran as
plain CLI commands, all from the tree being measured. Where holdings are needed
the environment carried `PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and
`PDSFILE_TEST_HOLDINGS=full`.

**Nothing under `src/` changed**: `git diff 96de70a --name-only -- src/` is empty. The
deliverable is nine pages of prose and five diagrams about machinery the package
already has, so the defect this PR could most easily ship is a fluent, plausible,
false relationship claim — one that every build and every test passes over. Sections 3
and 5 are the evidence about that.

## 1. What changed

| | |
|---|---:|
| pages added under `docs/dev_guide/` | 9 (landing page + 8 chapters) |
| Mermaid diagrams | 5, all in `dev_guide_architecture.rst` |
| `toctree` line added to `docs/index.rst` | 1 |
| `extensions` line added to `docs/conf.py` | 1 (`sphinxcontrib.mermaid`), plus its comment |
| files changed under `src/` | **0** |
| scheduled observations discharged | 1 (entry 1100) |

The chapter set is exactly the plan's list: (1) repository layout, (2) architecture
with diagrams a–e, (3) subsystem reference, (4) extending part A — a rules file,
(4b) extending part B — the maintenance tools, (5) test-suite guide, (6) the goldens
how-to, (7) CI/release. The five diagrams are the plan's five: the `classDiagram` of
the mixins and subclasses, the cache-layer `flowchart`, the shelf-subsystem
`flowchart`, the `preload()` `sequenceDiagram`, and the rules-resolution `flowchart`.
One name in the plan's diagram spec does not exist in the tree and the diagram uses
the real one: the plan writes `_IndexRowMixin`, the class is `_IndexRowsMixin`
(`src/pdsfile/pdsfile.py:185`, pinned alphabetical by
`tests/api/test_mixin_collisions.py`).

## 2. Scheduled entry 1100, and the mermaid decision

Entry 1100 scheduled enabling `sphinxcontrib.mermaid` to whichever PR drew the first
diagram; this PR draws five, enables the extension, and removes the entry
(`critiques/observations.md` now counts 212 open: 19 closed since the renumbering
plus three later additions, two of them this PR's review observations 4316 and
4317). The owner decision of
2026-08-09 stands as recorded in the plan and issue #136: **the CDN configuration** —
no vendored `mermaid.esm.min.mjs`, no `mmdc` pre-rendering, no committed SVGs.

The accepted consequences were measured rather than restated:

| | |
|---|---:|
| built pages carrying the CDN script tag | **71 of 107** |
| script URL | `https://cdn.jsdelivr.net/npm/mermaid@11.12.1/dist/mermaid.esm.min.mjs` |
| pages with a diagram | 1 |

The 70 script-carrying pages without a diagram are the ones whose doctree the
extension cannot inspect (viewcode pages, generated indexes), which is the behavior
PR-31 measured at 70 of 77 when it decided to keep the extension off until a page
drew a diagram. The published diagrams do not render where the CDN is unreachable;
`docs/conf.py`'s comment states both consequences.

## 3. The diagrams: validated outside Sphinx, because Sphinx does not parse them

The Sphinx builds treat a `.. mermaid::` body as opaque text, so a syntax error
publishes a dead grey block with both gates green. Each of the five diagram sources
was therefore extracted from the page and rendered with `mmdc` (mermaid-cli against
mermaid 11), and each of the five produced an SVG:

    diag1.mmd OK   (classDiagram)
    diag2.mmd OK   (cache flowchart)
    diag3.mmd OK   (shelf flowchart)
    diag4.mmd OK   (preload sequenceDiagram)
    diag5.mmd OK   (rules-resolution flowchart)

Two defects this caught before any review round, both invisible to every gate:

* a `;` inside a `sequenceDiagram` message is a statement separator, so one message
  reading "… else DictionaryCache; set DEFAULT_CACHING" made the whole fourth
  diagram unparseable — rendered as a dead block, gates green;
* `\n` inside a flowchart label renders as a literal backslash-n in mermaid 11; all
  17 were replaced with `<br/>` and the rendered SVGs re-checked.

The rendered class diagram was also read: PdsFile with the nine mixin bases above it,
the two concrete classes below, and the rule-subclass leaves below those.

Diagram content was verified against source while drafting: the nine mixin names and
their base order against `src/pdsfile/pdsfile.py:185`; the cache choice, the four
`$`-key families and the walk order against `src/pdsfile/_preload.py` (the
`preload()` body, in source order); the lifetimes against the four constants and
`cache_lifetime_for_class()`; the shelf lookup edges against
`_shelves.py::shelf_lookup`/`_get_shelf` (null-key store, info-only sidecar branch,
fall-through to the pickle); the resolution steps against
`pdsfile.py::new_pdsfile` (direct `SUBCLASSES` hit, else
`VOLSET_TRANSLATOR.first()`) and the registration tails of the rule modules. The
subclass-registry counts in the prose were measured by importing the package:
`len(Pds3File.SUBCLASSES)` = 26 (25 + `default`), `len(Pds4File.SUBCLASSES)` = 7
(6 + `default`).

## 4. Gates at head `f9fd1f5`

`scripts/run-all-checks.sh` was run once, in full, with the holdings variables set,
and its output read end to end rather than tailed. Exit **0**. What each gate
measured:

| gate | measured |
|---|---|
| `ruff check` | All checks passed (both passes: configured rules, and the E111/E112/E113 indentation pass) |
| pytest (`--mode ns`, full holdings) | **1205 passed, 34 skipped** in 192 s — identical to the base suite at `96de70a` |
| pyroma | 10/10 |
| API freeze | 1 passed |
| clean install | all runtime modules import with no dev extras |
| Sphinx `-W` | exit 0, **0 problem lines**, API reference 78 of 78 modules |
| Sphinx `-n -W` | exit 0, **0 problem lines**, API reference 78 of 78 modules |

The two shelves-only suites were run separately, same environment:

| suite | result |
|---|---|
| `tests/pds3file tests/rules/pds3 --mode s` | **555 passed, 3 skipped** |
| `tests/pds4file tests/rules/pds4 --mode s` | **123 passed, 31 skipped** |

Both match the baseline at `96de70a` (the pds3 pair 555/3 and the pds4 pair 123
passed, recorded when the s-mode fix landed). Nothing moved in any suite, which is
what a docs-only PR must show.

The docs-specific gates in the pytest run did their job once during drafting:
`tests/docs/test_markup.py` failed the tree on **4** instances of inline markup
nested inside a strong span (the rendered-with-visible-backticks fault the gate was
built for after it shipped on a user-guide page), all four in the new chapters, all
four fixed before commit. The two greps the Sphinx gate cannot make were run against
both built trees at head:

    grep -chE '<strong>[^<]*``' docs/_build/*/dev_guide/*.html    # 0
    grep -ohE '–[a-z-]+'        docs/_build/*/dev_guide/*.html    # 0 lines

## 5. What was verified by hand against source, and what was corrected

Every factual claim in the chapters was drafted against a named source location, and
the draft was then re-read against the code once whole. Corrections made before any
reviewer saw the pages, each a claim that read plausibly and was false:

* "a child of a rule-subclass object is built by that same class **without
  consulting the tables again**" — false: `child()` derives the key from the
  parent's `bundleset` and goes through the same `SUBCLASSES`/translator lookup
  (`pdsfile.py:1480-1494`). Rewritten to say the same route, not a skipped one.
* `PdsCache` described as a base "whose methods raise NotImplementedError" —
  false: the class body is `pass`; it constrains nothing (`pdscache.py:85-94`).
* "every rule module has a test module" — false: 13 of the 25 PDS3 rule modules
  have one (`tests/rules/pds3/`).
* the PDS4 rules directory holds **9** modules, not the 10 first written.
* `run_tests_coverage.sh` annotated as a working wrapper — it names test paths that
  no longer exist (observation 4304); the tree annotation now says not to use it.
* "the merged directories mean an un-preloaded process still resolves paths, just
  slowly" — overclaim not supported by `_preload.py`; replaced with what the module
  docstring states (the entries exist and are empty; `preload()` rebuilds them
  unconditionally).
* the goldens chapter first claimed `--update` writes a missing rule golden — a
  plain run does too (`read_or_update_golden_copy()`,
  `tests/support/pdsfile_test_helper.py:53`), while a missing *tool-test* golden
  fails without `--update` (`tests/holdings_maintenance/support.py:793-821`); the
  chapter now states both mechanisms.
* `holdings_free` marking attributed to directory conftests everywhere — true for
  `tests/api/` and `tests/docs/`, but `tests/core/` carries per-module
  `pytestmark` lines.

## 6. Cross-reference discipline

Every API symbol named in the chapters' prose carries a Sphinx role, and the `-n -W`
build is the checker that they all resolve. **This section's first version claimed
that before it was true**: round 1 found about twenty published members written as
bare inline literals and refuted the claim (`critiques/pr-33/round-1.md`, M2); all
twenty now carry `:meth:`/`:attr:` roles and the nitpicky build over them exits 0
with 0 problem lines. The build also caught two wrong targets during drafting
(`preload` and `cache_lifetime_for_class` written against the class and the
re-export module rather than against the mixin and `_preload`, where autodoc
publishes them). Inline literals remain for file paths, CLI tokens, environment
variables, class attributes, and the private names the API reference does not
publish (`_eval_null_key_record()`, `_update_ranks_and_vols`,
`_pinned_log_timetag()`) — the two known non-resolver families of observations
1001/6403 are not depended on. No cross-reference appears inside a diagram block,
code block or literal block.

## 7. The record checkers, base to head

| checker | base `96de70a` | head |
|---|---:|---:|
| `critiques/pr-29/check_citations.py` | 8 stale | **8 stale** — unmoved |
| `critiques/pr-28/check_record_numbers.py` | 27 stale | **27 stale** — unmoved |

Base numbers were measured in a second worktree at `96de70a`, not recalled.

## 8. Standing rules

- The four frozen files (`tests/api/api_manifest.json`,
  `tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py`,
  `tests/api/test_api_freeze.py`) and `pyproject.toml` are byte-identical to
  `96de70a`, verified by diff against `git show`.
- No golden or baseline was edited; no test was skipped or xfailed; the ratchet did
  not move; `ruff format` was not run.
- No literal machine path appears anywhere under `docs/`: holdings roots are
  written as `$PDS3_HOLDINGS_DIR`/`$PDS4_HOLDINGS_DIR` placeholders or
  `/path/to/...` stand-ins throughout.
- Nothing under `docs/` names a plan, a critique, a PR number or a phase number;
  issue #136 is named in a `conf.py` comment as the record of the mermaid
  alternatives, which is the referential use the comment rules allow.
- `git status --porcelain -uall` is empty after the full gate run, so
  `docs/_build/` stayed out of the index.
- Line endings are LF in every added file.

## 9. The reviews

Every round a fresh no-context subagent; recorded in `critiques/pr-33/round-<k>.md`.

| round | scope | findings |
|---|---|---:|
| 1 | full diff, deepest on the architecture and subsystem chapters | 5 Major, 6 Minor, 2 Deferred |
| 2 | full diff, deepest on chapters 1, 4, 4b, 5, 6, 7 | 2 Major, 1 Minor, 0 Deferred |
| 3 | the 26 correction passages, each named by hand | 1 Major, 2 Minor, 1 Deferred |
| 4 | scoped: round-3 resolutions + new Majors only | 1 Major |
| 5 | scoped: the round-4 correction, clause by clause | **0 findings — goal met** |

Round 1's Major findings were all factual prose claims verified false against
source — the pair-spec difference set, the cross-reference goal itself, the CI
driver's coverage, the mixin back-import rule stated without its sanctioned
exception, and a miscounted import list — and zero of them were in the diagrams,
which the reviewer verified edge-by-edge and reproduced with mmdc. All five were
fixed, all six Minors fixed, one Deferred became observation 4316 and the other was
already recorded as 4111.

Round 2's two Majors both landed in the extending-tools chapter, and one of them
was introduced by round 1's own correction — the measured Phase 7 pattern (a
correction pass carries new defects at about half the rate of the pass it corrects)
holding on this PR too, which is why round 3 read only the correction passages,
each named by hand. Round 3 then found the pattern a third time, in the same
sentence rounds 1 and 2 had each rewritten: a provenance claim ("shared from
``_archives_common``") that was true of the parser texts and false of the log
suffix. One sentence, three rounds, three different defects is the starkest local
measurement of the pattern this effort has produced.

Round 4 then measured it a fourth time — its one Major was inside round 3's own
fix — which put the loop at §6.6's hard cap with a finding still open. **The fifth
round was taken anyway, deliberately and narrowly**, on the grounds PR-32's fifth
was: the finding class was measured rather than mysterious, the plan's PR-32
section directs this PR to budget for the second read of its own corrections, and
opening on an unread correction would have shipped the exact defect the loop had
just measured four times. Round 5 read the two rewritten passages clause by clause
against the workflow files and returned zero findings, verdict **goal met**, which
is the §6.6 termination condition. The cap excess is called out in the PR
description for the owner rather than only here.

The loop's totals: 9 Major, 9 Minor, 3 Deferred across five rounds; every Major
was a factually false prose claim (none was ever in a diagram, a build, or a
gate), and three of the nine were introduced by a correction pass — each round
from 2 on found exactly one Major inside the previous round's fixes.
