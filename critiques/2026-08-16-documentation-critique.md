# Documentation Critique Report

**Generated:** 2026-08-16
**Tree:** `rewrite` at commit 6525951 (branch `chore/critique-reports`, identical tree)
**Scope:** README, CONTRIBUTING, docs/ (user guide, developer guide, how-to, API
reference, Sphinx setup), and docstrings under src/pdsfile/
**Rules applied:** all five documentation rule files exist and were applied —
`doc_python.mdc`, `doc_readme.mdc`, `doc_user_guide.mdc`, `doc_dev_guide.mdc`,
`doc_how_to.mdc` — read in full, plus `pdsfile_overrides.mdc` (alwaysApply), which
takes precedence where they conflict. No rule file was absent, so no checklist area
was skipped.

Findings carry stable identifiers **DOC-01** through **DOC-18** in order of
appearance. A finding marked *waived* records a conflict between a template rule and
a decision the project has recorded; it is not actionable. Every number in this
report comes from a command run against this tree; the appendix lists the commands.

## Executive summary

This is documentation in unusually good health. The docs tree is one Sphinx tree
with one `conf.py`; the build is gated in `scripts/run-all-checks.sh` and passes
here with **zero warnings under all three build forms** (`-W`, `-n`, `-n -W`), with
the coverage line reporting **"API reference: 77 of 77 modules under
/seti/all_repos/rms-pdsfile/src documented"**. Docstring coverage measured over
every module, class and function under `src/` (excluding the generated
`_version.py`) is complete: **0 missing docstrings**, **0 docstring lines over 90
columns**, **0 `Args:` sections** (all Google-style `Parameters:`). The user guide
documents all fourteen programs, and every option table I checked against the
actual argument parsers matched exactly — including the short spellings
(`--init`/`--reinit`, `-l`, `-q`, `-a`, `-i`), `crlf`'s `allow_abbrev=False`, and
`re_validate`'s twenty options. Counts asserted in prose (141 repair entries, 64
properties, 11 console scripts, 25/6 rule subclasses, 15 core modules) all
reproduce against the code.

**Build health:** `sphinx-build -W` exit 0, 0 warnings; `sphinx-build -n` exit 0,
0 warnings (this is the complete unresolved-cross-reference inventory — it is
empty); `sphinx-build -n -W` (the project's gate form) exit 0, 0 warnings.

The genuine defects are drift, not absence. The highest-priority findings are the
developer guide's CI gate table, which is stale against `run-all-checks.sh` on two
gates (PyMarkdown shown off but enabled; the stubtest gate missing entirely,
DOC-12), and the repository-layout chapter, which does not mention the 43 shipped
`.pyi` stubs or `scripts/stubtest_allowlist.txt` (DOC-13) — both introduced by the
two most recent merges (#153, #154) without same-change doc updates. Below those:
a contradictory stale comment block in `conf.py` (DOC-01), a small set of
time-anchored phrasings the prose rule bans (DOC-04, DOC-05), and structural gaps
against the how-to and dev-guide templates (DOC-14 through DOC-17).

## 1. Documentation system and build

The tree satisfies `doc_python.mdc` sections 1, 3 and 6 almost completely:

- Single source tree: 36 `.rst` sources under `docs/` with one `conf.py`;
  `docs/_build/` is git-ignored (`git check-ignore docs/_build` matches), and
  `git ls-files docs` shows no build output committed.
- `conf.py` enables `autodoc`, `napoleon` (Google style, `napoleon_use_param`,
  `napoleon_use_rtype`, `napoleon_use_ivar` with an in-file rationale), `viewcode`,
  `myst_parser`, and `sphinxcontrib.mermaid`; `source_suffix` covers `.rst` and
  `.md`; the source root goes on `sys.path` (`docs/conf.py:31-32`); the version
  derives from `importlib.metadata.version` with a documented fallback
  (`docs/conf.py:50-56`); `tabulate` is mocked (`docs/conf.py:110`). `conf.py`
  additionally registers its own API-reference coverage check on `build-finished`
  (`docs/conf.py:186-237`), which is what makes the module-coverage claim
  mechanical rather than asserted.
- All three builds were run into fresh scratch directories and their full logs
  read: each exits 0 with `grep -c WARNING` = 0 and prints the coverage line
  quoted above. `suppress_warnings = ['myst.header']` is the one suppression; its
  comment (`docs/conf.py:82-89`) correctly scopes it to the single README include,
  the only Markdown source in the build.
- `nitpick_ignore` (`docs/conf.py:135-147`) holds 11 entries, every one a
  standard-library symbol the package does not own, under a comment explaining the
  policy — compliant with the rule that owned symbols are never silenced.

**DOC-01 — `conf.py` carries a stale comment block describing configuration that
no longer exists.** `docs/conf.py:112-117` reads "Reaching this inventory is what
makes the standard-library names ... resolve under `-n`, so the build needs
network access to it, and a build that cannot reach it fails ... The timeout
bounds that failure" — but there is no inventory and no timeout in this file: the
paragraph describes the `intersphinx_mapping`/`intersphinx_timeout` configuration
that PR #139 (commit cefae61) removed, and it directly contradicts the paragraph
below it (`docs/conf.py:120-129`), which says intersphinx is deliberately not
enabled precisely so the build does not depend on the network. The orphan
paragraph should be deleted. (`doc_python.mdc` section 7: never leave stale or
contradictory documentation.)

**DOC-02 — intersphinx is not enabled — waived.** `doc_python.mdc` section 3
requires `sphinx.ext.intersphinx` "at minimum". This tree deliberately omits it:
the removal is a merged, owner-approved change (PR #139, commit cefae61, "drop
intersphinx", 2026-08-15), with the rationale recorded in the commit body, in
`docs/conf.py:120-129`, and in deferred observation 329's history (an unreachable
`docs.python.org` inventory failed the gate and bought only hyperlinks on
standard-library names; the 11 names now sit in `nitpick_ignore`). Recorded here
as a template conflict; waived by that decision.

**DOC-03 — em-dashes inside `.py` files outside `src/`.** `doc_python.mdc`
section 2 bans unicode em-dashes inside `.py` files. `src/` is clean (a
`grep -rPln` for em-dashes, smart quotes and arrows over `src --include='*.py'`
matches nothing), but two files elsewhere carry em-dashes:
`scripts/check_runtime_imports.py:66` (inside a user-visible failure message:
`'CLEAN-INSTALL IMPORT CHECK FAILED — runtime-dependency leak:'`) and
`tests/holdings_maintenance/test_shelf_common.py:323` (a comment). The
`tests/docs/test_markup.py` gate scans docstrings under `src/` only, which is why
these survive. Low priority; two one-character fixes.

**DOC-04 — time-anchored phrasing in seven places.** `doc_python.mdc` section 2
bans anchoring prose to a moment in time ("now", "today", "currently", ...).
Measured by grep over `docs/*.rst`:

- `docs/dev_guide/dev_guide_testing.rst:48` — "no `PDSFILE_TEST_DATA_DIR` is set
  anywhere today"
- `docs/dev_guide/dev_guide_testing.rst:53` — "(it does not, today)"
- `docs/user_guide/user_guide_pds4archives.rst:116` — "To check a PDS4 archive
  today, unpack it and compare"
- `docs/user_guide/user_guide_concepts.rst:247` — "what today's two testable
  bundle sets do"
- `docs/user_guide/user_guide_pdslinkshelf.rst:60` — "It covers 141 path patterns
  today and grows whenever ..."
- `docs/dev_guide/dev_guide_extending_rules.rst:122` — "the recorded `__all__`
  currently trails the import block"
- `docs/dev_guide/dev_guide_extending_rules.rst:145` — "thirteen of the PDS3
  modules currently have one"

Each can be rewritten in the timeless present ("It covers 141 path patterns", "no
`PDSFILE_TEST_DATA_DIR` is set anywhere in the repository"). Other grep hits
("no older than", "cancel the older one", "no longer conforms") are semantic uses,
not time anchors, and are fine.

**DOC-05 — three "older log layout" notes are migration framing.** The `.. note::`
at `docs/user_guide/user_guide_maintenance_tools.rst:261-267` ("An existing log
tree carries an older layout ... The five PDS4 programs wrote under their PDS3
counterpart's name"), the note at `docs/user_guide/user_guide_pdsarchives.rst:73-78`
("Older logs of this program carry `_links` instead"), and
`docs/user_guide/user_guide_pds4checksums.rst:93-96` ("older log trees are the
exception") narrate previous program behavior. Unlike DOC-04 these carry
operational value — a reader will meet such trees on disk — so the fix is to
describe the artifact rather than the history ("A log tree may contain
`pds4archives` logs under `logs/pdsarchives/`; the program writes only under its
own name"), not to delete the information.

**DOC-06 — British spellings.** `docs/dev_guide/dev_guide_extending_rules.rst:18`
("catalogued") and `docs/dev_guide/dev_guide_subsystems.rst:210` ("the catalogue").
American forms are "cataloged"/"catalog" (`doc_python.mdc` section 2). No other
British forms matched (behaviour/colour/initialise/organised/whilst/analyse: 0).
Sentence spacing is clean: a grep for double-space-after-period across `docs/`
matched 0 lines.

## 2. Docstrings and API reference

Measured over every `.py` under `src/` except `_version.py` (77 modules; 78 files
on disk, with `_version.py` excluded by `conf.py`'s `_GENERATED_MODULES`):

- **0 missing docstrings** on modules, classes and functions (AST walk).
- **0 docstring lines over 90 columns** (and therefore 0 over 100).
- **0 `Args:` sections**; the style is Google with `Parameters:`, as
  `pdsfile_overrides.mdc` records. No inline type annotations, and per deviation
  (1) their absence is not a finding.

Cross-section actually read for this report: `src/pdsfile/pdsfile.py` (module
docstring), `src/pdsfile/_properties.py` (the `description` property),
`src/pdsfile/pdscache.py` (module docstring), `src/pdsfile/pds3file/rules/
COISS_xxxx.py` (module docstring), `src/pdsfile/pds4file/rules/
cassini_iss_spokes_hedman_hamilton_2024.py` (spot checks),
`src/pdsfile/holdings_maintenance/_common.py` (the `ToolSpec` docstring,
`build_arg_parser`, `setup_run`, `resolve_log_root`),
`src/pdsfile/holdings_maintenance/_shelf_common.py` (argument constants),
`src/pdsfile/holdings_maintenance/pds3/{crlf,pdschecksums}.py` and
`src/pdsfile/tools/show_opus_products.py` (parser builders). Quality is
consistently high: behavior-focused, `Returns:`/`Raises:` where applicable, and
claims that checked out against the code (e.g. the module docstring's "64
properties" matches 64 `@property` decorators in `_properties.py`; the
`COISS_xxxx` docstring's hyphenated bundle-set name
`cassini_iss_spokes_hedman-hamilton-2024` is the on-disk name, deliberately
distinct from the underscored module name, as that module's own docstring line 7
explains).

The API reference satisfies `doc_dev_guide.mdc` section 6: five pages plus a
landing page, one `automodule` per module (core 15, holdings_maintenance 22,
pds3file 27, pds4file 11, tools 2), every directive carrying `:members:`,
`:undoc-members:` and `:show-inheritance:`, plus `:special-members: __init__` and
a scoped `:private-members:` naming exactly one mixin class per mixin module. The
`conf.py` coverage check makes "a module with no page entry" a build failure, and
`docs/api/index.rst:4-9` honestly states the limit of that guarantee (modules,
not members).

**DOC-07 — "the the" typo in user-visible help text.**
`src/pdsfile/holdings_maintenance/_shelf_common.py:280`: the `--archives` help
string reads "refer to the the archive file". This renders in the `--help` of all
four checksum/info-shelf tools and on the autodoc page. Help text is not among
the frozen console output (the log-text freeze was lifted in Phase 6, and PR-25a
already rewrote a `--log` help string), so this is fixable.

## 3. Cross-reference completeness

The narrative `.rst` pages use Sphinx roles correctly: a grep for bare
inline-literal spellings of the principal classes (` ``PdsFile`` `,
` ``Pds3File`` `, etc.) in prose matches **0** lines, and the `-n` build reports
**0** unresolved references, so every role in the tree resolves. Spot checks
confirm heavy, correct use of `:class:`/`:meth:`/`:attr:`/`:mod:`/`:doc:`
throughout the guides (e.g. `docs/dev_guide/dev_guide_architecture.rst`,
`docs/user_guide/user_guide_show_opus_products.rst:5-7`).

**DOC-08 — docstrings use inline literals, not roles — waived.** Inside `src/`
docstrings, API symbols appear as inline literals rather than cross-reference
roles, which `doc_python.mdc` section 5 calls a violation. This is measured and
owned: the plan records 3,651 inline-literal occurrences (1,260 distinct) and the
sweep (PR-31a) is **permanently deferred by the owner (2026-08-16) to issue
#149** (`plans/2026-07-25-modernization-plan.md`, PR-31a entry). Recorded here;
waived by that decision. No stale references were found in the pages themselves
(the `-n` inventory is empty).

## 4. README

`README.md` satisfies `doc_readme.mdc` in structure and content:

- Markdown, one top-level `#` title, and the `<!-- start-after-point -->` marker
  at line 27, included by `docs/index.rst:11-13` so the badge block stays
  host-only.
- Sections in the required order: title, grouped badges (five `<br />`-separated
  groups covering release, CI, docs, coverage, PyPI, activity, issues/PRs,
  license), introduction, features, installation, quick start, documentation,
  contributing, license.
- Claims check out against `pyproject.toml`: "requires Python 3.11 or later"
  matches `requires-python = ">=3.11"`; the eleven named console scripts match
  `[project.scripts]` exactly; the three `python -m` programs match the modules
  that ship without scripts; "fourteen command-line programs" = 11 + 3; the
  license badge and section match `Apache-2.0`; `pipx` guidance matches the
  packaging shape. Every command-line program is mentioned once with a pointer to
  the user guide, and the README stays a summary, not a manual.
- The user guide's `installation` chapter states which five of its 56 published
  command lines were not run and why
  (`docs/user_guide/user_guide_installation.rst:215-247`) — an unusually honest
  runnability contract that the quick-start examples inherit.

**DOC-09 — the local docs-build instruction names the heavier extra.**
`README.md:145` says "install the `dev` extra and run `make html` in `docs/`".
That works (`dev` includes `rms-pdsfile[docs]` per `pyproject.toml:76`), but the
minimal extra for building docs is `docs`, which is also what
`.readthedocs.yaml` installs; `CONTRIBUTING.md:146-153` likewise assumes Sphinx
arrived via the earlier `pip install -e ".[dev]"`. Nice-to-have: name `docs` as
the docs-build extra (or state that `dev` includes it).

## 5. User guide

Layout follows `doc_user_guide.mdc` section 1: a dedicated `docs/user_guide/`
directory, a landing page with a `toctree` of 19 chapters, one chapter per
program (all fourteen), an installation chapter, a shared-command-line
chapter, a concepts chapter, a shell-scripts chapter, and a clearly named
appendix (`user_guide_appendix_file_formats.rst`). Absolute `:doc:` targets are used for
cross-directory links (`/api/index`, `/user_guide/user_guide` from the dev guide)
and relative ones within the guide.

Required content (section 2) is present and strong: purpose and concepts before
mechanics; a mermaid dependency graph of the build order
(`user_guide_concepts.rst:174-199`); installation with versions, `pip`/`pipx`,
the full environment-variable table including `PDS_LOG_ROOT` precedence
("`--log` wins", verified against `resolve_log_root()` in
`_common.py:288-307` and `LOGROOT_ENV = 'PDS_LOG_ROOT'` at `_common.py:60`); the
expected directory layout as literal blocks; and end-to-end examples whose output
is captured from real runs.

**CLI option tables were checked against the parsers and match exactly.**
Verified: the five task flags with `--init`/`--reinit` short spellings
(`_common.py:273-277`), the positional unit with `nargs='+'`, `--log`/`-l` and
`--quiet`/`-q` (`_common.py:344-350`); "more than one task is accepted, the last
one wins" matches the `store_const` implementation; `--archives`/`-a` and
`--infoshelf`/`-i` (`_shelf_common.py:278-286`); `pdsdependency`'s two options
(`pdsdependency.py:1367-1387`); `re_validate`'s twenty options in four groups,
including the repeatable `--email`/`--error-email` (`action='append'`,
`re_validate.py:807-895`); `crlf`'s two long-only options with
`allow_abbrev=False` (`crlf.py:157-171`) — the guide's "abbreviations are
rejected" contrast with `re_validate` is real; and `show_opus_products`'s seven
options including required `--paths` (`show_opus_products.py:75-102`). No option
drift was found anywhere.

**DOC-10 — no API-usage chapter — waived by plan scope.** `doc_user_guide.mdc`
section 2 requires API usage "for any importable surface", and this package's
importable surface is its primary product. The user guide declares itself the
manual for the command-line programs (`docs/user_guide/user_guide.rst:4-8`), and
that scope is the recorded plan decision — PR-32 is titled "docs: user guide (CLI
tools)" (`plans/2026-07-25-modernization-plan.md:1449`). Waived accordingly. The
residual fact worth recording: the only narrative API walkthrough anywhere is the
README quick start; a future API-usage chapter (preload, `from_path`,
associations, OPUS lookups as runnable snippets) remains the largest genuinely
missing piece of user documentation.

**DOC-11 — landing-page prose exceeds the template's budget.**
`doc_user_guide.mdc` section 1 wants a 1-2 sentence introduction and "no other
prose"; `docs/user_guide/user_guide.rst:4-8` is about four sentences (including
reading-order advice). Trivial; arguably the extra sentences earn their keep.

## 6. Developer guide

Layout: dedicated `docs/dev_guide/` directory; landing page with an audience
statement and an 8-chapter `toctree`; chapters share the `dev_guide_` prefix;
reachable from the root `toctree`. Required chapters largely present:
annotated repository tree as a `::` literal block with per-entry comments and the
public/private boundary stated (`dev_guide_repository_layout.rst`); environment
setup, test tiers, `--mode`, `--update`, markers and the sandbox
(`dev_guide_testing.rst`); architecture with five mermaid diagrams each followed
by narrative (`dev_guide_architecture.rst`); per-module contracts for all fifteen
core modules plus the cross-cutting invariants (`dev_guide_subsystems.rst`); two
extension recipes with code skeletons and registration wiring, including the
API-freeze consequence (`dev_guide_extending_rules.rst`,
`dev_guide_extending_tools.rst`); CI/release (`dev_guide_ci.rst`) with coding
conventions as a pointer to `CONTRIBUTING.md` and `.cursor/rules/`, which the
rule permits.

**DOC-12 — the CI gate table is stale against `run-all-checks.sh` on two
gates.** `docs/dev_guide/dev_guide_ci.rst:20-40` presents the `ENABLE_*` defaults
as "the canonical record of which gates this repository runs", and two rows are
wrong today:

- PyMarkdown is listed "not yet — off until the README complies"
  (`dev_guide_ci.rst:39`), but `scripts/run-all-checks.sh:143` sets
  `: "${ENABLE_PYMARKDOWN:=true}"` — enabled since the README rewrite merged
  (PR #153, commit f81a231, which is the change the row was waiting on).
- The stubtest gate does not appear in the table at all:
  `scripts/run-all-checks.sh:139` sets `: "${ENABLE_STUBTEST:=true}"` (PR #154,
  commit 7787a1c, "public API type stubs"). The chapter's only related text is
  the mypy row's "the public API is stubbed instead" (`dev_guide_ci.rst:27-28`),
  which predates the gate.

This is exactly the drift `doc_python.mdc` section 7 forbids: both merges changed
what "all checks" means without updating the chapter that documents it.

**DOC-13 — the repository-layout chapter omits the shipped type stubs and the
stubtest allowlist.** PR #154 added 43 `.pyi` files under `src/pdsfile/` (counted
with `find src -name '*.pyi'`) and `scripts/stubtest_allowlist.txt`; neither
appears in `docs/dev_guide/dev_guide_repository_layout.rst` (the `scripts/`
listing at lines 59-66 and the package tree at lines 13-45 predate them), and a
grep for `.pyi`/"stub" over `docs/` finds only the half-sentence in
`dev_guide_ci.rst:28`. The stubs are shipped, public-surface artifacts with their
own gate and their own editing rules (`pyproject.toml:172-194` excludes them from
ruff with a long rationale); the dev guide should say what they are, where they
live, and that stubtest is their gate. Same root cause as DOC-12.

**DOC-14 — the dev-guide `toctree` does not end with the API reference and the
contribution guide.** `doc_dev_guide.mdc` section 1 wants the landing page's
chapter list to end with those two; `docs/dev_guide/dev_guide.rst:11-21` ends
with `dev_guide_ci`. The landing prose does link `/api/index`, and the API
reference is a top-level `toctree` section of its own in `docs/index.rst` — a
reasonable structure, but a recorded template deviation nobody has recorded.
Low priority: either append the two entries (the contribution pointer could be a
short chapter or the existing CI chapter's closing section) or note the layout
choice deliberately.

**DOC-15 — no introduction chapter, and the runtime dependencies are named
nowhere.** `doc_dev_guide.mdc` section 2 asks for an introduction with a package
overview including "the runtime and key dependencies". The landing page carries
the audience statement, but no chapter names what the package runs on: a grep for
`numpy|pillow|pyparsing|rms-pdstable|rms-translator|pdslogger` over `docs/*.rst`
matches only a `pdslogger` token inside a code block
(`dev_guide_extending_tools.rst:46`). A developer meeting `pdslogger`,
`translator` or `pdstable` objects in the source gets no orientation. A short
introduction section (what the runtime deps are and what each is for) would close
this.

**DOC-16 — the class diagram carries no abstract/dataclass markers.**
`doc_dev_guide.mdc` section 3 wants abstract classes marked in the diagram. The
architecture diagram (`docs/dev_guide/dev_guide_architecture.rst:16-61`) draws
the hierarchy but the abstract-in-practice status of `PdsFile` lives only in the
prose below it (lines 66-72, which state it precisely); `ToolSpec`, the one
dataclass in the documented surface, appears in no diagram (its chapter is
prose-and-code, which reads well). Low priority: an `<<abstract>>` annotation on
`PdsFile` in the diagram would make the diagram self-contained.

## 7. How-to articles

The tree contains one how-to, `docs/dev_guide/dev_guide_goldens.rst` ("How-To:
Regenerating Goldens"), plus strongly task-shaped chapters inside the user guide
(the concepts chapter's build sequence, the crlf walkthrough with its
`printf` reproduction recipe at `user_guide_crlf.rst:68-82`). Consistency between
the how-to and the guides is good: it links `dev_guide_testing` and the golden
mechanisms it describes match that chapter's account.

**DOC-17 — the goldens how-to lacks the template's required elements as
sections.** Against `doc_how_to.mdc` section 2: the intro and the numbered steps
(four, at `dev_guide_goldens.rst:74-96`) are present and good; but there is no
explicit **Prerequisites** block (the env-var exports at lines 59-63 serve the
purpose implicitly), no **Expected Results** summary, no **Troubleshooting**
section (the fingerprint-skip trap at lines 76-82 and the "wrong root" advice at
lines 47-49 are troubleshooting content embedded in prose), and no closing
related-material links. The content exists; the structure the rule prescribes
would make it scannable. Also, the title's gerund form ("Regenerating Goldens")
is slightly off the rule's imperative pattern ("How To Regenerate Goldens") —
cosmetic.

## 8. Diagrams and figures

Six mermaid diagrams: five in `dev_guide_architecture.rst` (class hierarchy,
cache layers, shelf lookup, preload sequence, rules resolution) and one in
`user_guide_concepts.rst` (the derived-products dependency graph). Each sits
inline beside the prose that narrates it, and each renders in the built pages
(verified by the clean builds; mermaid is text-based so there are no image files
to name or alt-text — `find docs -name '*.png'` outside `_build` finds none).
Diagram use matches the rule's "where a visual is clearer than prose" test.

**DOC-18 — diagrams render via a CDN, so offline copies show none — waived.**
`sphinxcontrib.mermaid` loads its runtime from `cdn.jsdelivr.net`, the script tag
lands on every built page, and an offline copy of the docs renders no diagrams.
This is the recorded owner decision (2026-08-09): use the CDN, do not vendor,
pre-render or commit SVGs; alternatives and costs live in issue #136 and the
decision is restated in `docs/conf.py:60-68` and the plan's PR-31 record. Waived.

## 9. Change discipline and consistency

The same-change rule (`doc_python.mdc` section 7) is enforced mechanically for
the API reference (the `conf.py` coverage check) and held well through the guide
PRs — but the two merges landed after the guides were written broke it in the dev
guide: **DOC-12** (gate table stale on PyMarkdown and stubtest) and **DOC-13**
(layout chapter silent on the 43 stubs and the allowlist) are both products of
PRs #153/#154 shipping without doc updates. **DOC-01** is the same failure inside
`conf.py` itself, left by the intersphinx removal (#139).

Everything else I could measure is consistent across documents and metadata:
Python floor 3.11 in README, `user_guide_installation.rst`, `CONTRIBUTING.md` and
`pyproject.toml`; the eleven console scripts identical in README, installation
chapter and `[project.scripts]`; `.readthedocs.yaml` installs the `docs` extra as
`dev_guide_ci.rst:101-103` and the repo-layout annotation say; the repair table
really has 141 entries (`len(REPAIRS.tuples)` = 141) as claimed in two places;
`_properties.py` really has 64 `@property` members as claimed in three places;
`scripts/run_tests_coverage.sh` is flagged stale by the layout chapter rather
than silently wrong. The removed `shelf_consistency_check` tool (issue #156) has
no ghost chapter — the guides never mention it.

## Recommended priorities

1. **Fix the dev guide's drift from the last two merges** (DOC-12, DOC-13):
   correct the PyMarkdown row, add a stubtest row to the gate table in
   `dev_guide_ci.rst`, and document the `.pyi` stubs and
   `scripts/stubtest_allowlist.txt` in `dev_guide_repository_layout.rst` (and a
   sentence in the frozen-surface section of `dev_guide_subsystems.rst`). This is
   the only place the docs actively misinform a contributor today.
2. **Delete the stale intersphinx paragraph in `conf.py`** (DOC-01) — a
   five-line deletion that removes a self-contradiction in the build's own
   configuration file.
3. **Sweep the prose-convention violations** (DOC-04, DOC-05, DOC-06, DOC-03,
   DOC-07): seven time-anchored phrasings, three migration-framed notes to
   rephrase as artifact descriptions, two British spellings, two em-dashes in
   `.py` files, one "the the" in help text.
4. **Bring the goldens how-to onto the `doc_how_to` skeleton** (DOC-17) and
   settle the two structural dev-guide deviations (DOC-14, DOC-15, DOC-16):
   add the missing sections, an introduction naming the runtime dependencies,
   and either extend the dev-guide `toctree` or record the layout choice.
5. **Nice-to-have:** name the `docs` extra in the README/CONTRIBUTING build
   notes (DOC-09); trim or keep the user-guide landing prose (DOC-11). The
   waived items (DOC-02, DOC-08, DOC-10, DOC-18) need no action; DOC-10's
   residual — a narrative API-usage chapter — is the best candidate if the docs
   are ever extended beyond the current scope.

## Prompt for an AI agent to fix the documentation

You are working in /seti/all_repos/rms-pdsfile (branch from `rewrite`). Fix the
documentation defects recorded in
`critiques/2026-08-16-documentation-critique.md`, findings DOC-01 through
DOC-18. Read that report first; it contains file:line evidence for every item.

Ground rules:

- Follow the five doc rules in `.cursor/rules/` (`doc_python.mdc`,
  `doc_readme.mdc`, `doc_user_guide.mdc`, `doc_dev_guide.mdc`,
  `doc_how_to.mdc`) and `.cursor/rules/pdsfile_overrides.mdc`, which takes
  precedence. Do not add inline type annotations; do not change production code
  behavior; do not touch `tests/api/api_manifest.json`, its allowlist,
  `scripts/dump_public_api.py`, or the freeze test.
- Do NOT act on findings marked waived: DOC-02 (intersphinx stays out), DOC-08
  (docstring inline literals stay; issue #149), DOC-10 (user-guide scope is CLI
  by plan decision), DOC-18 (mermaid CDN stays; issue #136).
- Actionable set: DOC-01 (delete `docs/conf.py:112-117`, the stale intersphinx
  paragraph), DOC-03 (replace the em-dash in `scripts/check_runtime_imports.py:66`
  and `tests/holdings_maintenance/test_shelf_common.py:323` with `--`), DOC-04
  (rewrite the seven time-anchored phrasings in the timeless present), DOC-05
  (rephrase the three older-log-layout notes to describe the on-disk artifact,
  keeping the operational information), DOC-06 (cataloged/catalog), DOC-07 (fix
  "the the" in `src/pdsfile/holdings_maintenance/_shelf_common.py:280`), DOC-09
  (mention the `docs` extra for local docs builds in README.md and
  CONTRIBUTING.md), DOC-11 (optional: trim the user-guide landing prose), DOC-12
  (correct the PyMarkdown row and add a stubtest row in
  `docs/dev_guide/dev_guide_ci.rst`, matching `scripts/run-all-checks.sh`'s
  ENABLE_* defaults exactly — re-derive them from the script, do not copy this
  report), DOC-13 (document the 43 shipped `.pyi` stubs and
  `scripts/stubtest_allowlist.txt` in `docs/dev_guide/
  dev_guide_repository_layout.rst`, with a sentence in `dev_guide_subsystems.rst`'s
  frozen-surface section), DOC-14 (extend the dev-guide toctree to end with the
  API reference and a contribution pointer, or record the deviation), DOC-15
  (add a short introduction naming the runtime dependencies and what each is
  for — read them from `pyproject.toml` `[project] dependencies`), DOC-16 (mark
  `PdsFile` `<<abstract>>` in the architecture class diagram), DOC-17
  (restructure `docs/dev_guide/dev_guide_goldens.rst` onto the `doc_how_to.mdc`
  skeleton: Prerequisites, numbered Steps, Expected Results, Troubleshooting,
  related links — reuse the existing content, do not invent new claims).
- Every factual claim you add must be verified against the code or a command you
  ran, in the spirit of the guides' existing measured style. If a symbol or page
  is renamed or moved, update every cross-reference, the README and the guides in
  the same change.
- Build gate: when done, the docs must build clean —
  `sphinx-build -W -b html docs <fresh-dir>` and
  `sphinx-build -n -W -b html docs <fresh-dir>` both exit 0 with zero warnings
  and print the "77 of 77 modules" coverage line (use fresh build directories;
  a reused directory re-reads nothing). Also run `scripts/run-all-checks.sh` and
  confirm the docs-related gates pass. Read the full build output; do not tail
  it.

## Appendix: Commands run

Environment: `cd /seti/all_repos/rms-pdsfile && source venv/bin/activate`;
Sphinx 9.1.0 from the venv. Build directories were fresh scratchpad paths.

Builds (full logs read; warning counts by `grep -c WARNING`):

    sphinx-build -W -b html docs <scratch>/docs-w      # exit 0, 0 warnings
    sphinx-build -n -b html docs <scratch>/docs-n      # exit 0, 0 warnings
    sphinx-build -n -W -b html docs <scratch>/docs-nw  # exit 0, 0 warnings
    grep -c 'WARNING' <scratch>/build-{w,n,nw}.log     # 0 / 0 / 0
    grep -n 'API reference' <scratch>/build-*.log
      # "API reference: 77 of 77 modules under /seti/all_repos/rms-pdsfile/src
      #  documented" in all three

Inventory and tree state:

    git rev-parse --short HEAD                          # 6525951
    find docs -type f \( -name '*.rst' -o -name '*.md' \) | sort   # 36 .rst
    git ls-files docs | sort                            # no _build files tracked
    git check-ignore docs/_build                        # matches (ignored)
    wc -l docs/*.rst docs/*/*.rst README.md CONTRIBUTING.md        # 5,848 total
    find src -name '*.py' | grep -v __pycache__ | wc -l # 78 (77 + _version.py)
    find src -name '*.pyi' | wc -l                      # 43
    ls src/pdsfile/holdings_maintenance/pds3/           # 12 shell scripts present

Docstring measurements (AST walks over src/, excluding _version.py):

    python3 <AST walk counting missing docstrings>      # 0 missing
    python3 <AST walk measuring docstring line widths>  # 0 lines > 90
    grep -rn '^\s*Args:$' src --include='*.py'          # no matches
    grep -c '@property\|@functools.cached_property' src/pdsfile/_properties.py
                                                        # 64

Prose-convention greps:

    grep -rPln '[\x{2013}\x{2014}\x{2018}\x{2019}\x{201C}\x{201D}\x{2192}\x{2190}]' \
        src --include='*.py'                            # no matches
    grep -rPln '...same class...' scripts tests --include='*.py'
        # scripts/check_runtime_imports.py, tests/holdings_maintenance/test_shelf_common.py
    grep -rniE '\b(currently|today|legacy|recently|backwards.compatible|...)\b' \
        docs --include='*.rst'                          # DOC-04/DOC-05 sites
    grep -rniE '\b(behaviour|colour|initialise|organised|catalogue[sd]?|whilst|analyse)\b' \
        docs src --include='*.rst' --include='*.py' --include='*.md'
        # 2 hits: catalogued / catalogue
    grep -rnE '[a-z]\.  [A-Z]' docs --include='*.rst' | wc -l      # 0
    grep -rn '``PdsFile``|``Pds3File``|...' docs --include='*.rst' # 0 in prose

Parser cross-checks (option-table drift):

    grep -n "add_argument(\|ArgumentParser(" src/pdsfile/holdings_maintenance/pds3/{pdsdependency,re_validate,crlf}.py \
        src/pdsfile/tools/show_opus_products.py
    sed -n '155,175p' src/pdsfile/holdings_maintenance/pds3/crlf.py  # allow_abbrev=False
    Read of _common.py:180-419 (TASK_FLAGS, build_arg_parser, setup_run,
        resolve_log_root, LOGROOT_ENV='PDS_LOG_ROOT')
    grep -n -A8 "ARCHIVES_ARGUMENT" src/pdsfile/holdings_maintenance/_shelf_common.py
        # -a / -i short forms; "the the" typo at :280

Consistency measurements:

    python -c "from pdsfile.holdings_maintenance.pds3.linkshelf_repairs import REPAIRS; ..."
        # {'tuples': 141}
    grep -c "automodule" docs/api/*.rst                 # 15/22/27/11/2
    grep -n "ENABLE_PYMARKDOWN\|ENABLE_STUBTEST" scripts/run-all-checks.sh
        # both default true (lines 139, 143)
    git log --oneline -S intersphinx -- docs/conf.py    # cefae61 (#139)
    git log --oneline -S "ENABLE_PYMARKDOWN:=true" -- scripts/run-all-checks.sh
        # f81a231 (#153)
    git log --oneline -3 -- 'src/pdsfile/*.pyi'         # 7787a1c (#154)
    grep -rn "\.pyi\|stub" docs --include='*.rst'       # 1 hit (dev_guide_ci.rst:28)
    grep -rn "numpy\|pdslogger\|pyparsing\|rms-pdstable\|rms-translator\|pillow" \
        docs --include='*.rst'                          # 1 hit, in a code block
    grep -rno "hedman[_-]hamilton[_-]2024" src --include='*.py' | sort | uniq -c
        # 30 hyphenated (on-disk name), 9 underscored (module name)
    cat .readthedocs.yaml; cat docs/Makefile            # docs extra; SPHINXOPTS pass-through
    ls tests/docs/                                      # check_docstrings.py, test_docstrings.py, test_markup.py

Decision-record lookups (for waiver classification):

    grep -rln intersphinx plans/ critiques/ .cursor/rules/
    sed -n '6134,6151p' critiques/deferred-observations.md      # observation 329
    grep -n "PR-31a" plans/2026-07-25-modernization-plan.md     # deferred, issue #149
    grep -n "PR-32" plans/2026-07-25-modernization-plan.md      # "user guide (CLI tools)"

Files read in full: all 36 `.rst` sources, `docs/conf.py`, `docs/Makefile`,
`README.md`, `CONTRIBUTING.md`, `pyproject.toml`, `.readthedocs.yaml`, the five
doc rule files, `pdsfile_overrides.mdc`, and the docstring cross-section listed
in section 2.
