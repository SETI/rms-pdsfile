# rms-pdsfile Modernization Plan

**Date:** 2026-07-17
**Status:** DRAFT — all §8 decisions settled (2026-07-18); open to further
fine-tuning
**Executor:** an opus-class AI — a thin coordinator → one phase-coordinator per
phase → **one PR-executor subagent per PR** (all phases), each PR gated by a
fresh no-context adversarial review loop (§6.6–6.7), one PR at a time, merged to
a single integration branch, with human review at PR boundaries
**Rewrite branch:** `rewrite` (all PRs target it; it merges to `main` once complete)

### How to read this document (start here)

You are the executor. This document is the **complete, self-contained**
specification — you need no other context, no prior conversation, and none of
the `critiques/` records to carry it out. Read it in full once, then:
1. Do the **Prerequisites** (start of §5) — environment, holdings env vars,
   GitHub access, and capture the two Phase-0 baselines *before* PR-01.
2. Read the **locked ground rules** (§2) — these are non-negotiable and
   override the repo's cursor rules where they conflict.
3. Read the **execution protocol** (§6.4), the **adversarial review loop**
   (§6.6), and the **subagent topology** (§6.7) — these govern *how* every PR
   is done.
4. Execute the phases in order (§5, PR-01 → PR-37), one PR per PR-executor
   subagent, each gated by the §6.6 loop, all merging into the `rewrite`
   branch.
When the plan and a repo cursor rule disagree, the plan wins (see
`.cursor/rules/pdsfile_overrides.mdc`, created in PR-04). When you are unsure or
hit a **hard stop** (§6.4), stop and ask the owner — do not guess. Line numbers
are indicative; locate code by symbol name.

**Repositories and paths referenced by this plan** (this repo is at
`/seti/all_repos/rms-pdsfile`; siblings are under `/seti/all_repos/`):
the modernization template `rms-devenv/repo_template` and its realized example
`rms-cloud-tasks`; the API consumers `rms-opus` and `rms-viewmaster`; the
public fixture repo `SETI/rms-pdsfile-test-data` (exists). Complete real
holdings are at `/data/pdsdata/{holdings,pds4-holdings}`. GitHub remote is
`SETI/rms-pdsfile`; PRs are opened with `gh`.

## 1. Goals

Modernize rms-pdsfile to match the conventions in `rms-devenv/repo_template`
(as realized in `rms-cloud-tasks`, the best CLI-bearing precedent), while:

- **G1** Splitting the 6,304-line `PdsFile` class file into focused modules (issue #77, phase "a" — mechanical decomposition; deep redesign deferred).
- **G2** Creating a test suite for the maintenance tools (issue #82).
- **G3** Making the default test suite hermetic: runs on stock GitHub-hosted runners with **no access to real holdings**, in parallel via pytest-xdist.
- **G4** Keeping the full-data tests: the real holdings must still be tested periodically (nightly, self-hosted).
- **G5** Writing full developer documentation for the module and CLI tools, and full user documentation for the CLI tools (issues #43, #45).
- **G6** Making the code clean and ruff-clean, with Google-style docstrings.
- **G7** Standardizing the per-dataset rules tests (issue #37).

## 2. Ground rules (locked decisions)

These were decided with the repo owner on 2026-07-17 and are **not** open for
re-interpretation by the executor:

1. **The public API may not change at all — 100% compatibility.** Everything
   reachable today via `import pdsfile` (including `pdsfile.pdsfile`,
   `pdsfile.pdscache`, `pdsfile.pdsviewable`, `Pds3File`/`Pds4File` and all
   their methods/properties/class attributes, and the volset/volume alias
   properties) must keep working with identical names, signatures, and
   behavior. **Exception — test infrastructure is not external API:**
   `pdsfile.pdsfile_test_helper` and the two `rules/pytest_support.py` modules
   exist only to support this repo's own test suite; they are excluded from
   the freeze manifest (PR-02) and are free to change or move out of the
   package (PR-08 moves them into the test tree). Consumer that must not break:
   **rms-opus** (verified: class-based API only, no module-level or
   underscore names). **rms-viewmaster mostly uses the class-based API, but
   has two pre-existing flat-name usages that already fail against *current*
   pdsfile** (not caused by, and not fixable by, this rewrite):
   `viewmaster.py:411,421` reference `pdsfile.cache_lifetime`, which does not
   exist — `get_page_cache()` raises `AttributeError` at startup today; and
   `:58` sets `pdsfile.DEFAULT_CACHING` (a no-op, since `DEFAULT_CACHING` is a
   *class* attribute at `pdsfile.py:353`). The manifest cannot protect names
   that are already gone. **This means PR-37's consumer smoke checks compare
   against a Phase-0 baseline (below), not against "passes," exactly like the
   test suite** — otherwise the Opus executor hits an unexplained failure at
   the finish line. Whether to add `pdsfile.cache_lifetime`/`DEFAULT_CACHING`
   at package level (additive, allowlisted) or to patch viewmaster is an owner
   decision, out of scope here. **rms-webserver is explicitly out of scope (owner-confirmed retired,
   2026-07-17):** its `webapps/viewmaster.py` (last touched 2022),
   `webapps/viewmaster-without-pause.py`, and `validation/spider.py` are the
   old Viewmaster/crawler, superseded by the standalone **rms-viewmaster**
   repo. They call a pre-split *flat-module* pdsfile API that no longer exists
   (`pdsfile.use_shelves_only`, `pdsfile.set_logger`, `pdsfile.preload`,
   `pdsfile.pause_caching`, `pdsfile.DEFAULT_CACHING` as a module attribute)
   and are already incompatible with current pdsfile. The freeze cannot
   protect an API that is already gone, so rms-webserver is neither a
   compatibility target nor a PR-37 smoke-check target.
   Enforced mechanically (§6.1).
2. **Issue #77 scope:** mechanical decomposition only ("a now, b later").
   No dependency-injected cache manager, no structured path parser rewrite,
   no extraction of rule data to YAML/config files.
3. **Test data:** keep this repo clean. Large fixture data lives in a separate
   repo, kept as small as possible: files made small or empty where content is
   not needed; only limited copies of directories.
4. **Keep the existing full-data tests.** Real holdings are tested periodically
   (nightly self-hosted), forever.
5. **Skip type annotations for now.** No inline typing effort, no mypy gate.
   Provide a type stub for the public API instead.
6. **No FCPath.** Do not adopt rms-filecache, and do not copy `filecache.mdc`
   into this repo's cursor rules.
7. **CLI names unchanged** (all 11 console scripts keep their names).
   **`re-validate.py` is left alone for now** (moved/renamed with its package,
   but its internals — including email/batch logic — are untouched).
   **Sync shell scripts are document-only** (no port, no rewrite).
8. **Single package:** the maintenance tools fold into the `pdsfile` package
   (`src/pdsfile/holdings_maintenance/`); no separate top-level package.
9. **Leave all functionality in place** — including `MemcachedCache`/pylibmc
   support (Viewmaster passes `port=` to `preload`). Nothing is deleted for
   being "probably dead." Latent *bugs* in existing code may be fixed (PR-15,
   plus the tool-bug fixes in PR-26/PR-28), each with a test, but no feature
   removal.
10. **Record keeping:** `plans/` holds plans (this file); `critiques/` holds
    critique reports, baselines, and per-phase validation records. Every phase
    leaves a record.

### PR discipline

- Every PR targets `rewrite`. One logical change per PR. **File moves/renames
  are always their own PRs** (pure `git mv`, plus the minimal edits required to
  keep the package importable **and every active gate green** — CI script
  paths, conftest import paths, packaging config, **and the `ruff`
  `per-file-ignores` path globs** (renaming a glob to the moved path is a
  rename, not a ratchet *widen*, and is allowed) — each itemized explicitly in
  the PR description. A move PR that leaves a gate red is not "pure"; the edits
  that keep it green are part of the same PR, not deferred.
- **Commit granularity inside a move/rename PR: never mix renames and fixes
  in the same commit.** Rename commits contain only pure `git mv` operations
  (one or several renames per commit is fine) so `git log --follow` tracks
  history cleanly across the rename. The minimal keep-green edits (CI paths,
  imports, packaging, ignore globs) go in separate content-edit commits —
  which may each bundle several fixes — never in a commit that also renames
  files.
- Conventional Commit titles (per `git_workflow.mdc`).
- Every PR description records: what was validated (which suites, which tree),
  and a link to the critiques/ record if the phase produced one.
- **PRs are behavior-preserving. A PR that changes observable behavior is
  wrong** — the only exceptions are the bug fixes this plan explicitly
  enumerates (PR-15's list, PR-26's pds3 bug fixes and `os.system` →
  `subprocess.run`, PR-28's `errors` fix), and each of those must first add a
  regression test pinning the intended (corrected) behavior and call the
  change out in the PR description.

### Validation gates (apply to every PR from the phase where each gate exists)

| Gate | Introduced | What it checks |
|---|---|---|
| API-freeze manifest test | Phase 0 (PR-02) | Public surface identical to the pre-rewrite manifest (modulo the two pre-approved forgiveness categories, §6.1) |
| Full-data suite (local or self-hosted) | Phase 0 (baseline) | No behavior change against real holdings; required after every Phase 5/6 PR, and at each phase boundary otherwise |
| `ruff check` (ratcheted) | Phase 1 (PR-03) | Style; per-file-ignores may only shrink |
| `ruff format --check` | Phase 5 (PR-23 core, PR-24 rest) — **conditional on the owner churn checkpoints in those PRs**; scope may be reduced or the gate dropped entirely | Formatting; not gated before the one-time reformat lands |
| Hermetic suite on GitHub CI | Phase 4 (PR-14) | Everything testable without holdings, 3 OS × 4 Python |
| sphinx -W -n build | Phase 7 (PR-31) | Docs build clean |
| Adversarial pre-PR review loop | Phase 0 (every PR) | A fresh, no-context Opus reviewer cannot prove the PR misses its stated phase goal — zero Major and no new un-rebutted Minor findings (§6.6) |

## 3. Current-state summary (facts about the current code)

This section is **self-contained** — everything needed to act is here; the
historical analysis and review records that produced this plan are committed
under `critiques/` for reference but are **not** required reading. Verify any
line number by symbol before relying on it (see the note at the end of this
section). The load-bearing facts:

- `pdsfile/pdsfile.py` (6,304 lines): one class, ~70 lazy properties backed by
  `_X_filled` slots + `_recache()` write-back into class-level `CACHE`.
  Clean seams: module-level path helpers (lines 47–247), local-filesystem ops
  (1259–1661), shelf subsystem (5061–5359), checksum/archive path builders
  (4898–5059), log paths (5361–5516), split/sort (5518–5871), transformations
  (5873–5977), associations (5979–6289), OPUS support (4642–4896), index-row
  support (4358–4640), preload machinery (662–1079). Entangled core:
  constructor, lazy properties (1667–3220), bundle utilities (3226–3397),
  `_complete`/`_update_ranks_and_vols`/`_recache` (3403–3520), alternative
  constructors (3536–4356). **All line numbers in this plan are indicative and
  were accurate at 2026-07-17; the executor locates code by symbol name, not
  by line, since lines shift as PRs land.**
- Zero type annotations. Ad-hoc docstring styles. Known ruff issues: UP004
  (`(object)` bases), E722 (bare except at 3020), E721, B006 (mutable
  defaults in pdsviewable), UP031 (% formatting), F403 (star imports).
- Latent bugs in unexercised paths (see Phase 5 list).
- Rules mechanism: per-dataset modules registering `TranslatorByRegex` tables
  onto subclasses via `SUBCLASSES['<key>']`; each rule module ends with
  `from .pytest_support import *` and contains inline `test_*` functions —
  this is why `pytest` is currently a **runtime** dependency.
- Tests: ~217 test functions; import-time `KeyError` without
  `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR`; session-autouse preload; two serial
  pytest invocations (`--mode s` / `--mode ns`) because `SHELVES_ONLY` is
  global class state; goldens under `pdsfile/pds{3,4}file/test_results/`
  (64 files) regenerated with `--update`; CI is self-hosted runners with
  holdings mounted (the runner environment provides the holdings env vars).
- Maintenance tools: 11 console scripts + 4 scripts without `main()`
  (`re-validate.py`, `crlf.py`, `shelf-consistency-check.py`,
  `utility/show_opus_products.py`). pds3/pds4 pairs are 70–85% duplicated;
  the pds4 copies fixed bugs the pds3 originals still have (`LOGDIRS` global
  shadowing, `abs(modtime1 != modtime2)`, `checksum1 != checksum1`).
  Outputs are deterministic iff file mtimes are pinned and runs use a
  disposable tree; `.tar.gz` bytes and `os.walk` order are not portable.
- Dependency inconsistencies: `requirements.txt` ≠ `pyproject.toml`;
  `tabulate` used but not declared in pyproject; `pytest` in runtime deps.
- Local resources for the executor: full real holdings at
  `/data/pdsdata/holdings` and `/data/pdsdata/pds4-holdings`; a limited set
  (mainly shelf files) at `~/DS/Shared/Shared-OPUS/pdsdata` for machines
  without full access. Both are private paths — they appear in this plan only
  and must never be hardcoded in code, tests, docs, or CI; everything resolves
  them via the `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR` env vars.

## 4. Target end state

```
rms-pdsfile/
├── src/pdsfile/
│   ├── __init__.py                  # unchanged public surface (+ __all__)
│   ├── __init__.pyi                 # public API type stub (+ py.typed)
│   ├── pdsfile.py                   # PdsFile core (constructor, lazy props,
│   │                                #   child/from_*, _complete/_recache);
│   │                                #   re-exports every name it exports today
│   ├── _path_utils.py               # module-level path helpers
│   ├── _shelves.py                  # shelf open/cache/lookup subsystem
│   ├── _local_fs.py                 # os_path_exists/isdir/listdir/glob_glob
│   ├── _derived_paths.py            # checksum/archive/log path builders
│   ├── _opus.py                     # opus_products / from_opus_id / from_filespec
│   ├── _index_rows.py               # index-shelf row support
│   ├── _associations.py             # associated_* / associated_parallel
│   ├── _sorting.py                  # split/sort + bulk transformations
│   ├── _preload.py                  # preload machinery
│   ├── pdscache.py                  # unchanged API (bug fixes only)
│   ├── pdsviewable.py               # unchanged API (bug fixes only)
│   ├── preload_and_cache.py         # kept as compat re-export shim
│   ├── pds3file/{__init__.py, rules/...}
│   ├── pds4file/{__init__.py, rules/...}
│   ├── holdings_maintenance/
│   │   ├── _common.py               # shared tool core (Phase 6)
│   │   ├── pds3/  pds4/             # thin, parametrized tools; same CLI names
│   │   └── sync_scripts/            # the zsh scripts, moved verbatim, documented
│   └── tools/show_opus_products.py
├── tests/
│   ├── conftest.py                  # skip-aware, marker-driven, xdist-safe
│   ├── api/test_api_freeze.py       # + api_manifest.json
│   ├── pds3file/  pds4file/         # moved blackbox/whitebox/cached tests
│   ├── support/pdsfile_test_helper.py  # golden read/update helpers
│   │                                #   (moved out of the package in PR-08)
│   ├── rules/pds3/  rules/pds4/     # extracted, standardized per-dataset tests
│   ├── holdings_maintenance/        # NEW: tool tests (issue #82)
│   └── golden/{full,mini}/...       # base full set + sparse mini overrides
├── docs/                            # Sphinx: index, user_guide/, dev_guide/, api/
├── plans/  critiques/               # records (this file, baselines, reports)
├── scripts/
│   ├── run-all-checks.sh  read-docs.sh
│   ├── make_test_holdings.py        # fixture-tree generator
│   └── automated_tests/             # nightly self-hosted driver (updated)
├── .cursor/{rules,skills}/          # template rules minus filecache.mdc
├── .github/workflows/               # run-tests (hermetic), nightly-full-tests,
│                                    # run-tests-and-opus, publish_to_*
├── pyproject.toml                   # ALL tool config; no .flake8/.coveragerc/setup.cfg
├── requirements.txt                 # "-e ."
└── README.md, CONTRIBUTING.md, codecov.yml, .readthedocs.yaml, ...

rms-pdsfile-test-data/   (separate repo, name TBD)
├── holdings/            # mini PDS3 tree (skeleton + stubs + real metadata + shelves)
├── pds4-holdings/       # mini PDS4 tree
├── manifest.json        # source paths, sizes, pinned mtimes, stub/real flags
└── README.md            # what this is, how to regenerate
```

## 5. Phases and PRs

Phases are strictly ordered; PRs within a phase are ordered unless marked
independent. Sizes: S (< 300 changed lines of hand-written diff), M (< 1500),
L (larger, usually mechanical).

### Prerequisites (operator setup before PR-01 — not PRs)

Verified on the execution machine 2026-07-18; do these first:
1. **Dev environment.** The existing `venv/` has the core runtime deps and an
   editable `pdsfile` (imports OK), and `pytest`/`coverage` are present; `ruff`
   0.15.7 is available. **Missing and needed:** `pytest-xdist`, `pytest-cov`,
   `pymarkdownlnt`, `pyroma`, `sphinx`+extensions — install them (they become
   the `.[dev]` extra at PR-03, but the executor needs ruff/pytest/coverage
   from PR-02). Ensure `ruff` is on the venv's PATH.
2. **Holdings env vars + confidentiality.** Not exported in a bare shell.
   Export `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` pointing at the chosen
   holdings root. Two real holdings roots exist and the PdsFile tests must
   pass against **either**: `/data/pdsdata/{holdings,pds4-holdings}` is the
   **complete** set (use it for the Phase-0 full-data baseline and the
   self-hosted nightly), and `~/DS/Shared/Shared-OPUS/pdsdata/…` is a **limited
   set (mainly shelf files)** for machines without full access. **The
   Shared-OPUS path is user-local and confidential: it must appear in NO
   checked-in file or doc — only in this plan.** More generally, **no absolute
   holdings path (Shared-OPUS or `/data/pdsdata`) may be hardcoded in committed
   code, tests, docs, CI, or the fixture repo** — every holdings root is
   resolved from the `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR`/`PDSFILE_TEST_DATA_DIR`
   env vars, and docs/examples use those variable names as placeholders. (This
   is already how the test helpers resolve holdings; keep it that way.)
3. **Test-data repo — DONE.** `SETI/rms-pdsfile-test-data` exists and is public
   (confirmed 2026-07-18). PR-10 fills it.
4. **GitHub access.** Already set up — no action needed (`gh` can create the
   `rewrite` branch, open PRs, and push to both `SETI/rms-pdsfile` and
   `SETI/rms-pdsfile-test-data`).
5. **Harness.** Confirm the runtime supports the four-level subagent nesting
   (§6.7) and that subagents can run `git`/`gh`/`pytest`/`ruff`.
   **Fallback if nesting is capped:** collapse levels from the **top**, never
   the bottom — the interactive session itself plays the coordinator (and, if
   needed, the phase-coordinator) role, so what remains spawned is always
   "one PR-executor subagent per PR" and, under it, the fresh no-context
   §6.6 reviewer per round. The per-PR executor isolation and the truly-fresh
   reviewer are the two properties that must survive; the upper coordination
   layers may run in the main session. Record the chosen topology in
   `critiques/` before PR-01.
6. **Capture the two Phase-0 baselines FIRST** (§Phase 0): the pre-rewrite
   full-data test baseline (against the **complete** `/data/pdsdata` holdings)
   and the consumer-smoke baseline, committed to `critiques/baselines/`. These
   run before PR-01 changes anything and are the comparison target for every
   later gate.
7. **Two owner micro-defaults** (both defaults stand unless overridden):
   PR-26's modtime semantics (default = real 1-second tolerance), and the
   rms-viewmaster compatibility question (its `pdsfile.cache_lifetime` startup
   failure, per ground rule 1) — **the owner will patch rms-viewmaster
   separately when needed**, so the default holds: do **not** add
   `pdsfile.cache_lifetime`/`DEFAULT_CACHING` at package level; viewmaster's
   pre-existing breakage stays out of scope.
Self-hosted runners with holdings already exist (current CI uses them) and
codecov upload is already configured; the nightly + 3-OS hosted matrix are
created in PR-14, needing no pre-setup.

### Phase 0 — Records and guardrails

**PR-01 (S)** `chore: add plans/ and critiques/ record directories`
Create the `rewrite` branch from `main`. Then `git add` **this plan file**
(`plans/2026-07-17-modernization-plan.md`) and **every file already present in
the working tree under `plans/` and `critiques/`** (the historical analysis and
review records that produced this plan — they may be untracked; add them all).
Add `plans/README.md` and `critiques/README.md` (one-paragraph each: what the
directory holds). The issue #79 code-quality analysis already lives at
`critiques/2025-08-15-code-quality-analysis.md` (moved there before execution
began) and is added along with the rest. None of the `critiques/` records are
required reading to execute; they are provenance.

**PR-02 (M)** `test: public-API freeze manifest and checker`
- `scripts/dump_public_api.py` — the exact algorithm (no executor discretion):
  1. Import `pdsfile` (works without holdings env vars — verify first).
  2. Module set: `pdsfile`, `pdsfile.pdsfile`, `pdsfile.pdscache`,
     `pdsfile.pdsviewable`, `pdsfile.preload_and_cache`,
     `pdsfile.pds3file`, `pdsfile.pds4file`,
     plus **every module under `pdsfile.pds3file.rules` and
     `pdsfile.pds4file.rules`** (rule subclasses like `COISS_xxxx` are public
     surface), **including the two `rules` package `__init__` modules
     themselves** (they hold the ~20 shared `TranslatorByRegex` default tables
     — public surface). **Exclude** `pdsfile._version`, the `tests`
     subpackages, **`pdsfile.pdsfile_test_helper`** (test infrastructure, not
     external API — the ground rule 1 exception; it leaves the package in
     PR-08, and excluding it here makes that move manifest-invisible),
     **and the two `rules/pytest_support.py` modules** (they are
     test support, deleted in PR-08 — dumping them would record `os`/`re`/
     `translator`/`pds3file` names whose PR-08 removal category #2's carve-out
     would otherwise treat as an unforgivable break, forcing a spurious hard
     stop). Enumerate modules explicitly (walk the two `rules` package
     directories for `*.py`, minus `pytest_support.py` and `__pycache__`) so
     the set is deterministic across machines.
  3. For each module: record every attribute name not starting with `_`,
     with its *kind*: `class`, `function`, `translator`
     (`type(obj).__name__` containing `Translator`), `module`, or `data`.
     Record **names and kinds only — never values** (translator tables,
     dicts, and other data compare by name alone).
  4. For each class defined in these modules: record every member name from
     `dir(cls)` **that does not start with `_`** (so dunders and all
     single-underscore internals are excluded — the freeze targets the
     *public* surface only), with kind
     (`method`/`classmethod`/`staticmethod`/`property`/`data`) resolved via
     `inspect.getattr_static`, and for callables the string form of
     `inspect.signature` (on `TypeError`/`ValueError`, record
     `"<unsignaturable>"`). Do **not** record which class in the MRO defines
     the member — mixin refactoring must not show up here.
     - **The one manual addition:** a hand-maintained
       `tests/api/consumer_used_private_names.json` (seeded empty). If a
       consumer is ever found to import an underscore-prefixed name, add it
       here and the dumper includes it. As of this plan the live consumers
       (rms-opus, rms-viewmaster) use no underscore-prefixed names, so the
       list starts empty (rms-webserver is out of scope — see ground rule 1).
  5. Output: JSON, keys sorted, 2-space indent, trailing newline
     (byte-reproducible across runs and platforms).

**Corollary rule for the whole rewrite (freeze-invisibility of internals):**
any *new* attribute, helper, method, or config constant introduced during the
rewrite is given a **leading underscore** so it is invisible to the manifest
and free to change (e.g. PR-15's `_HOLDINGS_ENV`).
Introducing a genuinely *public* new name (no leading underscore) is an
additive API change: allowed only with an allowlist entry and owner sign-off,
never silently. Renaming or removing an existing public name is forbidden
outright (that is what the freeze protects).
- Commit the dump as `tests/api/api_manifest.json`; add
  `tests/api/test_api_freeze.py` asserting the fresh dump equals the
  manifest, modulo `tests/api/manifest_allowlist.json`. The allowlist has two
  kinds of entries: **exact** `{module, name, reason, pr}` records, and
  **category predicates** `{pattern, kind, reason, pr}` that forgive a whole
  class of expected diffs (needed because PR-08 removes hundreds of incidental
  test-only names — see §6.1). The checker forgives a diff if it matches any
  exact record or any category predicate. This test needs no holdings; it is
  enforced **locally from Phase 0** (run it directly), **via `run-all-checks.sh`
  from PR-04** (that script does not exist earlier), and by GitHub CI from
  PR-14 — see §6.1 for the exact timing.
  - **Heads-up for the Phase-0 dump:** because the rule modules do
    `from .pytest_support import *` (and `pytest_support.py` has **no
    `__all__`**, confirmed), the raw manifest will initially record many
    incidental names per rule module (`os`, `pytest`, `TEST_RESULTS_DIR`,
    every `test_*`, and the star-imported helpers). That is expected; PR-08's
    category predicate (§6.1) covers their removal. Do **not** hand-filter the
    Phase-0 dump to pre-empt this — the dump is a faithful snapshot; the
    allowlist, not the dump, encodes the forgiveness.
- **This manifest, generated before any other change, is the compatibility
  contract for the whole rewrite.** Neither the manifest nor the allowlist
  may be edited to make a build pass; allowlist entries are added only under
  the two pre-approved forgiveness categories (§6.1) or with new owner approval.

**Baseline record (no PR):** run the full existing suite on this machine with
`PDS3_HOLDINGS_DIR=/data/pdsdata/holdings` and
`PDS4_HOLDINGS_DIR=/data/pdsdata/pds4-holdings`, exactly:
`pytest pdsfile/pds3file/tests/ pdsfile/pds3file/rules/*.py pdsfile/pds4file/tests/ pdsfile/pds4file/rules/*.py --mode ns`
then the same collection with `--mode s` limited to pds3 (mirroring
`scripts/automated_tests/pdsfile_main_test.sh`). Save the **full
`-v -rA` output** (the per-test pass/fail list, not just counts) to
`critiques/baselines/2026-07-17-pre-rewrite-baseline.md` plus raw logs in
`critiques/baselines/`. This per-test list is the comparison target for every
later full-data gate: "green" means *the identical pass/fail set*, so
pre-existing failures (if any) are neither blamed on the rewrite nor silently
"fixed" without a recorded explanation. **Use the same holdings root (the
complete `/data/pdsdata`) for this baseline and every later full-data gate** so
the pass/fail-set comparison is apples-to-apples; the suite passes against
either root, but the baseline and its comparators must match. (A self-hosted
runner's environment may point at the limited Shared-OPUS set on
some machines — confirm the CI runner's root matches the baseline's, or record
that a `full_holdings`-marked subset legitimately differs between the two.)

**Consumer-smoke baseline (no PR, same time):** run the PR-37 consumer smoke
checks against the *current* (pre-rewrite) pdsfile — the rms-opus import-path
smoke and the rms-viewmaster startup — and record their outcomes in
`critiques/baselines/2026-07-17-consumer-smoke-baseline.md`. This captures the
pre-existing rms-viewmaster `cache_lifetime` startup failure (ground rule 1) so
PR-37 compares against *this* baseline, not against unconditional success.

### Phase 1 — Template adoption (config only; no source moves)

**PR-03 (M)** `build: consolidate all tool configuration into pyproject.toml`
- Port `.coveragerc` → `[tool.coverage.*]` (`source` updated to the src
  layout when Phase 2 lands); port `.flake8` → `[tool.ruff]`
  (template settings: `target-version = "py310"`, `line-length = 100`,
  single quotes, `select = ["E","F","W","I","UP","B","SIM","C4","A","N","PT","RUF"]`,
  **and adopt the template's `extend-ignore = ["PT011","SIM105","SIM108"]`** —
  the faithful choice; it keeps ~9×SIM105 + 22×SIM108 out of the ratchet and
  out of PR-23's fix scope — exact counts re-derived by the executor, not
  trusted from here),
  with an **initial `per-file-ignores` ratchet**: run
  `ruff check --output-format json`, group violations by (file, rule code),
  and emit one `per-file-ignores` entry per file listing exactly its current
  rule codes (scripted, committed as part of the PR) so `ruff check` passes
  immediately. The ratchet may only shrink in later PRs — never grow, never
  gain inline `noqa` as a substitute. Delete `.flake8`, `.coveragerc`,
  `setup.cfg`.
- **`ruff format` is deferred**: no formatting in this PR and no
  `ruff format --check` gate until PR-23/24 perform the one-time
  reformatting (see those PRs for scope, the rules-table exclusion, and the
  mandatory owner churn checkpoint that may reduce or drop the reformat).
  Configure `[tool.ruff.format]` now (single quotes) but nothing enforces it
  yet.
- `[tool.pytest.ini_options]`: `--strict-markers`, `--strict-config`,
  registered markers (`full_holdings`, more added later). **Do not** set
  `filterwarnings = ["error"]` (the legacy code emits warnings; revisit in
  Phase 8 as a ratchet, not now). **Never** put `-n`/xdist options in
  `addopts` — worker counts are chosen per invocation by scripts/workflows
  (`--update` and full-data runs need serial).
- Dependencies: `requirements.txt` → `-e .`; add
  `[project.optional-dependencies]` `dev` (coverage, pytest, pytest-cov,
  pytest-xdist, ruff, pymarkdownlnt, pyroma, tabulate) and `docs` (sphinx>=7,
  sphinx-rtd-theme, myst-parser, sphinxcontrib-mermaid). **`tabulate` lives in
  the `dev` extra** (§8.5 — only `show_opus_products` uses it, and it stays a
  `python -m` tool, not a shipped console script, so it is not a runtime dep).
  **`pytest` stays in runtime deps until PR-08 removes the rules→pytest
  coupling** (note in pyproject comment).
- No mypy config (ground rule 5).
- **Fatten `[project].description`** (currently `"pdsfile"`, `pyproject.toml:8`)
  to a real one-line summary — pyroma (enabled in `run-all-checks.sh` from
  PR-04) docks trivially short descriptions; verify the pyroma score clears
  before flipping that gate on.

**PR-04 (M)** `chore: adopt repo_template support files`
- `.cursor/rules/` — copy all template rules **except `filecache.mdc`**;
  keep `logging.mdc` (PdsLogger is used throughout). `.cursor/skills/`,
  `.cursor/settings.json`, `.vscode/settings.json`.
- Add `.cursor/rules/pdsfile_overrides.mdc` (`alwaysApply: true`) stating the
  repo-specific deviations that **take precedence over the template rules**,
  so any AI following the rules doesn't fight the locked decisions:
  (1) no inline type annotations and no mypy — public-API `.pyi` stubs only;
  (2) the public API is frozen — see `tests/api/api_manifest.json`;
  (3) module-length limits are waived for `pdsfile.py` and rule files;
  (4) rule modules are excluded from `ruff format` (aligned tables) **and**
      carry permanent `ruff check` per-file-ignores; core and the subpackage
      `__init__`s carry a smaller frozen set. The freeze-/table-/typing-locked
      sets (derived from an actual `ruff check`, re-derived in PR-23/24, not
      hardcoded on faith) as of 2026-07-17:
      rules/`*.py` → `E501,W191,N801,N999,N802,N805,RUF012`;
      `pds{3,4}file/__init__.py` → `F401,A002,RUF012`;
      core (`pdsfile.py`,`pdscache.py`,`pdsviewable.py`) → `B006,A002,RUF012`;
      `re_validate.py` → its full derived set (frozen by (6), not tables);
      the new `tests/rules/**` files → any residue after PR-24's shrink.
      `RUF012` is repo-wide permanent because its only fix (`ClassVar`) is an
      inline type annotation, forbidden by (1);
  (5) no FCPath — plain `os.path` handling stays;
  (6) `re_validate.py` and the sync shell scripts are frozen (document-only);
  (7) `pytest` `addopts` carries **no** `-n`/xdist or `--cov` flags (unlike the
      template) — worker count and coverage are chosen per invocation
      (`--update` and full-data runs need serial); (8) the CI test matrix is
      3-OS (ubuntu/windows/macos), a deliberate extension of the template's
      ubuntu-only matrix; (9) `logging.mdc`'s "never bare `print()`" is waived
      for `holdings_maintenance/` — the tools' console output (including the
      `print()`-driven `shelf_consistency_check`) is frozen behavior; (10) the
      Python floor is **3.10** (matching the template's `requires-python`),
      overriding `python.mdc`'s "minimum 3.11".
  Without this file, `python.mdc`'s "annotate everything / run mypy" mandate
  directly contradicts ground rule 5.
- `.github/ISSUE_TEMPLATE/`, `pull_request_template.md`.
- `scripts/run-all-checks.sh` and `scripts/read-docs.sh`, with **staged
  enables** so the "single source of truth" is never red (each gate turns on
  only once it can pass — mirrors the §6.6 compliance table):
  | Check | ENABLE from |
  |---|---|
  | ruff-check (ratcheted), api-freeze, pyroma | PR-04 |
  (The template's `run-all-checks.sh` hardcodes `ruff check src tests`; at PR-04
  there is no `src/` — adapt the check targets to the current tree
  (`pdsfile holdings_maintenance utility scripts conftest.py`) and **re-point
  them in each Phase-2 move PR**; ensure `scripts/` stays in scope so
  `dump_public_api.py` and later `make_test_holdings.py` are linted.)
  | pytest (hermetic) | PR-11 (green locally) / PR-14 (in CI) |
  | ruff-format --check | PR-23 (core) / PR-24 (rest), only as approved at those PRs' owner churn checkpoints |
  | sphinx (`-W -n`) | PR-31 |
  | pymarkdown | PR-31 (docs) / PR-34 (README compliant) |
  | mypy, bandit, vulture | never (per ground rules / overrides) |
  Each enabling PR flips its row and updates CI to match (`environment.mdc`
  requires CI to run exactly the enabled set). At PR-04 the script is green
  with only its three PR-04 gates on.
- `CONTRIBUTING.md` from template; refresh `.gitignore` and remove any
  tracked build/coverage artifacts it now covers (`htmlcov/`, `.coverage*`,
  `coverage.xml`, egg-info — verify with `git ls-files` before deleting);
  `.readthedocs.yaml` (docs come in Phase 7; RTD build may be red until then
  — acceptable on the rewrite branch).
- Align `publish_to_pypi.yml` / `publish_to_test_pypi.yml` with the template
  versions (adds `twine check`); triggers unchanged.
- Update existing `run-tests.yml` triggers: also run on `pull_request`
  targeting `rewrite`, so every rewrite PR gets the self-hosted full-data run
  until Phase 4 replaces the PR gate. **And** add `tests/api/` to the pytest
  invocation in `scripts/automated_tests/pdsfile_main_test.sh` (its current
  paths exclude `tests/api`), so the API-freeze test runs in the self-hosted
  gate from PR-04 rather than waiting for PR-14 (§6.1).

### Phase 2 — Moves and renames (pure `git mv` PRs)

Each PR here is validated by: editable install works, `import pdsfile` works,
API-freeze test passes, and a local full-data suite run. Commit granularity
per the PR-discipline rule: rename-only commits (pure `git mv`, one or many
renames per commit) kept strictly separate from the keep-green edit commits —
never mixed.

**PR-05 (L, mechanical)** `refactor: move pdsfile package to src/ layout`
`git mv pdsfile src/pdsfile`. Update `setuptools_scm`
`write_to = "src/pdsfile/_version.py"`, gitignore `**/_version.py`.
- **Packaging (console-script guard):** do **not** switch discovery to `src`-only yet —
  `holdings_maintenance` is still at repo root until PR-06, and all 11
  `[project.scripts]` entry points target it, so a `where = ["src"]` switch now
  would un-package the CLI tools. Keep both discoverable this PR:
  `packages.find where = ["src", "."]` with an include filter for `pdsfile*`
  and `holdings_maintenance*` (or retain the explicit `holdings_maintenance`
  package entry). PR-06 collapses discovery to `src` once the tools move.
- **CI-gate guard:** update `scripts/automated_tests/pdsfile_main_test.sh`
  pytest paths from `pdsfile/…` to `src/pdsfile/…` **in this PR**, so the
  PR-04 self-hosted gate stays green (this is a licensed move-PR edit per the
  PR-discipline rule).
- Add `src/pdsfile/py.typed`? — **No** (deferred to PR-35 with the stubs; an
  empty py.typed with zero annotations would advertise `Any` for everything).

**PR-06 (L, mechanical)** `refactor: move maintenance tools and utility into the package`
- `git mv holdings_maintenance src/pdsfile/holdings_maintenance`;
  `git mv utility/show_opus_products.py src/pdsfile/tools/show_opus_products.py`.
- Rename hyphenated modules (rename only, content untouched):
  `re-validate.py` → `re_validate.py`,
  `shelf-consistency-check.py` → `shelf_consistency_check.py`.
- Minimal required edits, itemized in the PR: update the 11
  `[project.scripts]` targets to `pdsfile.holdings_maintenance.…:main`;
  replace the `REPO_ROOT` sys.path hacks in `pdsinfoshelf.py` and
  `re_validate.py` with package-relative imports (the only content lines
  touched in `re_validate.py`); update `show_opus_products.py`'s
  `from pdsfile.pds3file.tests.helper import …` env-var lookups to read the
  env vars directly (its current import target is the tests helper, which
  leaves the package in PR-07).
- Move the `.sh` scripts with their directories (sync scripts into
  `holdings_maintenance/sync_scripts/`, holdings helpers stay beside the
  tools). No script content changes.
- **Now collapse packaging discovery to `src`-only** (`packages.find
  where = ["src"]`) — `holdings_maintenance` now lives under `src/pdsfile/`, so
  the transient dual-discovery from PR-05 is no longer needed. Confirm all 11
  console scripts still resolve (`pip install -e .` then run each `--help`).

**PR-07 (L, mechanical)** `refactor: move tests to top-level tests/ tree`
- `git mv` `src/pdsfile/pds3file/tests` → `tests/pds3file`,
  `src/pdsfile/pds4file/tests` → `tests/pds4file`; `test_results/` goldens →
  `tests/golden/full/pds3/` and `tests/golden/full/pds4/` (path constants in
  the two `pytest_support.py` files updated to match — minimal edits).
- **The root `conftest.py` does NOT move in this PR** (it moves in PR-08).
  Pytest only applies a conftest to collection args beneath it; the rule-module
  tests still live under `src/…/rules/` until PR-08, and moving the conftest
  now would unregister `--mode`/`--update` for them. **But it must be edited
  here:** the root `conftest.py` imports
  `from pdsfile.pds3file.tests.helper import PDS3_HOLDINGS_DIR` (and the pds4
  equivalent), and those `tests` subpackages move out to `tests/` in *this* PR
  — so repoint those imports to the moved location (`tests/pds3file/helper.py`
  etc., importable because `pythonpath=["src"]` plus the repo root is on the
  path during collection). This is a licensed move-PR edit; itemize it.
- Keep the moved directories' `__init__.py` files (they exist today) so the
  two `helper.py` modules can't collide during collection.
- Inline rule-module tests are NOT moved yet (still collected via
  `pytest src/pdsfile/pds3file/rules/*.py` in the nightly script; update
  `scripts/automated_tests/pdsfile_main_test.sh` paths accordingly).
- Set `[tool.pytest.ini_options] pythonpath = ["src"]` (not `testpaths` yet).
- **API-manifest forgiveness category #1 (pre-approved, §6.1):** the
  `pdsfile.pds3file.tests*` / `pdsfile.pds4file.tests*` subpackages leave the
  installed package.

### Phase 3 — Test restructure and hermetic fixtures

**PR-08 (L)** `test: extract rule-module tests and standardize per-dataset suites`
(closes issue #37)
- Move every inline `test_*` + parametrize table from
  `src/pdsfile/pds{3,4}file/rules/*.py` into `tests/rules/pds3/test_<dataset>.py`
  / `tests/rules/pds4/test_<dataset>.py`.
- Standardize (the #37 fix). **First, ground truth as of 2026-07-17** (the
  executor re-confirms by grep before acting; the examples in issue #37 itself
  are stale — the HST extra-parameter, the COUVIS_0xxx "stray HST tests," and
  the "COVIMS_0xxx has no `test_associated_abspaths`" it cites have all already
  been resolved):
  - The **three core tests are already signature-uniform** across all 13 pds3
    rule modules that have tests: `test_opus_products(request, input_path,
    expected)`, `test_associated_abspaths(request, input_path, category,
    expected)`, `test_opus_id_to_primary_logical_path()`. **No signature
    harmonization is needed** — do not invent one.
  - The real inconsistency is **which extra tests exist where**: `test_versions`
    only in `COUVIS_8xxx`; `test_duplicated_products` only in `GO_0xxx`;
    `test_default_viewables` only in `CORSS_8xxx`; `test_associations` only in
    `CORSS_8xxx`; `test_associations_to_volumes` / `test_associations_to_diagrams`
    only in `COCIRS_xxxx` (COCIRS has **no** plain `test_associations`).
  - Concrete standardization rule: (a) the three core tests remain uniform and
    ordered first in every dataset's file; (b) the extra tests are **retained
    verbatim as dataset-specific supplements**, appended after the core three
    (uniformity of the core is a floor, not a ceiling — never drop an existing
    test, per §6.4); (c) *additive coverage* — where a dataset plausibly could
    have `test_versions`/`test_duplicated_products`/`test_associations` and the
    underlying rule table (`VERSIONS`/`OPUS_PRODUCTS`/`ASSOCIATIONS`) is
    non-null, add it and generate its golden with `--update` against full
    holdings; where the rule table is null/absent, record dataset + reason in
    `tests/rules/README.md` (the applicability table). No behavior change —
    only test presence changes.
- Root `conftest.py` content moves to `tests/conftest.py` in this PR (all
  tests now live under `tests/`); the root file is deleted.
- Remove `from .pytest_support import *` from all rule modules. **Before
  deleting the star-import from each module, add explicit imports for every
  name its *non-test* code still uses that the star-import currently supplies.**
  Known instance: `COVIMS_0xxx.py:347` calls `os.path.basename` in production
  code (`opus_id_to_primary_logical_path`), but the module imports no `os` —
  it comes only via the star-import; add `import os` there. Procedure: for
  each rule module, after removing the star-import, run `ruff check` (F821
  undefined-name) and the full-data suite; any `NameError`/F821 marks a name
  that needs an explicit import. The two
  `rules/pytest_support.py` modules are **internal** test support
  (`TEST_RESULTS_DIR`, `translate_all`, `unmatched_patterns`, `versions_test`)
  and move to `tests/rules/support.py`. **`src/pdsfile/pdsfile_test_helper.py`
  also leaves the package in this PR** — it is test infrastructure, not
  external API (ground rule 1 exception; PR-02 excluded it from the manifest,
  so the move is manifest-invisible). `git mv` it to
  `tests/support/pdsfile_test_helper.py` (with a `tests/support/__init__.py`),
  then update every test-tree import of `pdsfile.pdsfile_test_helper` to the
  new location (as of 2026-07-19 its only importers are the two
  `rules/pytest_support.py` modules, which this PR merges into
  `tests/rules/support.py`; re-verify by grep). After the move, nothing
  under `src/pdsfile/` may import it — the PR-08 clean-install gate proves the
  installed package no longer references it.
- **Drop `pytest` from runtime dependencies — AND delete the now-dead
  test-only top-level imports it leaves behind.** Every tested rule module (and
  even `cassini_iss.py`/`cassini_vims.py`, which import pytest with *zero* test
  functions) has a top-level `import pytest`; after the test functions move
  out, that import is dead but ruff only warns (F401, tolerated by the
  ratchet) and the manifest *forgives* `pytest` disappearing — so nothing
  forces removal, yet a clean `pip install rms-pdsfile` (no `[dev]`) would then
  raise `ModuleNotFoundError: pytest` at `import pdsfile`. Explicitly remove
  `import pytest` (and any import left unused after the test move) from every
  rule module.
- **New permanent gate (added this PR):** a clean-install import check — build
  a fresh venv, `pip install .` with **no extras**, then `import pdsfile` and
  import every module in the PR-02 manifest module set. This is the only gate
  that catches a runtime-dep leak; add it to `run-all-checks.sh` and CI. (No
  environment the plan otherwise uses lacks pytest, so without this gate the
  leak is invisible.)
- **Underscore test-helpers move with the tests:** module-level helpers
  and constants used *only* by test functions are not `test_*` names and the
  F821 sweep can't re-import them (their home is the test tree). Move them to
  the dataset's new test file. Known instance:
  `COISS_xxxx.py` `_coiss_opus_products_golden_references_pds4_reproj` +
  `_PDS4_REPROJ_BUNDLE_MARKERS` (:782-793), which consume `TEST_RESULTS_DIR`
  and `os` — move them into `tests/rules/pds3/test_COISS_xxxx.py`, do not try
  to re-import `TEST_RESULTS_DIR` into the rule module.
- **API-manifest forgiveness category #2 (pre-approved, §6.1):** rule modules
  lose their `test_*` / fixture attributes and the `pytest_support` /
  `pytest` / `os` test-only names (hundreds of diffs, all matched by the
  category predicate — not individual records).
- **ruff disposition for the new test files (not a ratchet widen):** the
  extracted `tests/rules/**`, `tests/rules/support.py`, and the relocated
  `tests/conftest.py` inherit the ruff violations that travel with the moved
  content (E501 on long parametrize/path-string lines, PT006, N806, E701,
  F841, I001, F401). **Test files are NOT frozen** (unlike the aligned
  translator tables and `re_validate.py`), so the rule is: *migrate* the
  relevant `(path, code)` `per-file-ignores` entries from the source rule-file
  glob to the new test-file paths — this is a migration accompanying content,
  **not** a widen (same principle as the move-PR glob-rename license) — then
  **PR-24 shrinks them toward zero** where cheap (split long strings via
  implicit concatenation, PT006 tuple form, N806 local renames, add `__all__`
  to `support.py`). Any residue that survives PR-24 is enumerated like the
  other permanent ignores. State this in the PR so a §6.6 reviewer does not
  read the new entries as a prohibited widen.

**PR-09 (M)** `test: holdings-aware conftest, markers, graceful skip`
- `tests/conftest.py`: a `holdings_flavor` session concept with exact
  resolution semantics:
  - `PDSFILE_TEST_HOLDINGS=full` → holdings roots from
    `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR` (error out loudly if unset).
  - `PDSFILE_TEST_HOLDINGS=mini` → roots are
    `$PDSFILE_TEST_DATA_DIR/holdings` and
    `$PDSFILE_TEST_DATA_DIR/pds4-holdings` (error if `PDSFILE_TEST_DATA_DIR`
    unset or the trees are missing).
  - Unset → `mini` if `PDSFILE_TEST_DATA_DIR` resolves, else every
    data-dependent test **skips** with reason
    `"no holdings available (set PDSFILE_TEST_HOLDINGS)"`. Collection never
    raises.
- Markers: `full_holdings` (only meaningful against real data — sizes,
  volume counts, etc.; auto-skipped under `mini`), plus keep `--mode s|ns`
  and `--update`.
- Remove import-time `KeyError` from the helper modules.

**PR-10 (L)** `feat: fixture-tree generator (scripts/make_test_holdings.py)`
The generator runs on a machine with real holdings and produces the mini tree
for the separate test-data repo. Design (ground rule 3: as small as possible):
- **Manifest seeding — dynamic, not static.** Do not try to statically parse
  parametrize tables. Instead: run the full suite against real holdings with
  a `sys.addaudithook` recorder (hooking `open` and `os.*` stat/listdir/glob
  audit events) that logs every path accessed under the holdings roots to a
  file. That access log, reduced to holdings-relative paths, seeds
  `fixture_manifest.toml`. Then close over: parent directories, label
  companions, and each file's original size + mtime.
- **Copy policy per file class (exact, in precedence order):**
  1. Directory skeleton: always real names (the regexes depend on them).
  2. **Link-source text files — always copied real:** any file
     `pdslinkshelf.generate_links` parses for links (per its docstring:
     `.LBL`, `.CAT`, `.TXT`, case-insensitive; the executor confirms the
     definitive extension list from the code before writing the policy),
     plus `.FMT` includes, PDS4 labels (`.xml`/`.lblx`), `_volinfo/*.txt`,
     and documents the tests touch. Zeroing any of these would corrupt
     linkshelf generation.
  3. Metadata index tables (`.tab`/`.csv`) + labels: copied real; tables
     over 2,000 rows are truncated to the referenced rows plus the first
     100 rows for context, with the label's `ROWS` (and `FILE_RECORDS`)
     rewritten; validated by a `pdstable.PdsTable` round-trip read.
  4. Previews/diagrams: regenerated tiny valid PNGs/JPGs at the original
     pixel dimensions (PIL width/height paths must work), not copies.
  5. Icons (`_icons` tree): copied real (small, needed by preload).
  6. Everything else (binary data products — images, cubes, etc.):
     **zero-filled stubs of the original byte size** (zlib makes them nearly
     free in git; sizes flow into info shelves and some tests).
- **mtimes:** pinned in the manifest (captured from source), applied with
  `os.utime` after generation; the test-data repo README documents that
  consumers (tests) re-apply them from the manifest after checkout (git does
  not preserve mtimes).
- **Then dogfood:** run the actual maintenance tools over the mini tree to
  produce its derived trees, self-consistent with the stub bytes. Use this
  **normative** order and invocation set (do not defer to any shell script —
  `update_holdings_for_new_metadata.sh` uses a different, metadata-only order
  and is not the reference), for pds3 then pds4:
  1. `pdsarchives --initialize <volumes-or-bundles-dir>` (build `archives-*`)
  2. `pdschecksums --initialize <archives-dir>` (archive checksums)
  3. `pdschecksums --initialize <data-dir>` (data checksums; needed by infoshelf)
  4. `pdsinfoshelf --initialize <data-dir>` (reads the checksum file)
  5. `pdsinfoshelf --initialize --archives <archives-dir>` (archive info shelves)
  6. `pdsindexshelf --initialize <metadata-dir>`
  7. `pdslinkshelf --initialize <data-dir>`
  (pds4 uses the `pds4*` tools; map `<data-dir>` to `volumes/…` for pds3 and
  `bundles/…` for pds4.) The exact `--archives` flag spellings are confirmed
  from each tool's argparse before use.
  Write `.tar.gz` archives with a fixed gzip mtime (`gzip.GzipFile(mtime=0)`
  route or equivalent). Note: full byte-for-byte archive reproducibility also
  requires deterministic tar **member order**; `pdsarchives` uses `os.walk`
  order, which is filesystem-dependent. Do **not** rely on committed archives
  being byte-identical across regenerations — the tool tests compare archives
  by member tuples (PR-13), never bytes, so member-order churn is immaterial.
  If churn in git is undesirable, the PR may add a sorted-walk to the
  fixture-generation path only (not to the shipped tool, which is frozen
  until Phase 6).
- **PR-10 delivers the generator + a first tree; it does NOT run the module
  test suite for convergence** (the tests are not hermetic until PR-11 — that
  ordering trap is why convergence lives in PR-11, below). PR-10's own
  acceptance check is *self-consistency*: after dogfooding, every
  maintenance-tool `--validate` over the mini tree passes (checksums/shelves/
  archives agree with the stub bytes). That is fully checkable at PR-10 time.
- **Convergence loop — a PR-11 activity** (stated here so the generator is
  built to support it): generate → run the now-hermetic suite against the
  tree → for each failure caused by a *missing path*, add it to the manifest
  → regenerate (re-run the PR-10 generator against real holdings) → repeat
  until the missing-path failure set is empty. Because PR-10 and PR-11 both
  write the separate test-data repo, the generator must be re-runnable from
  an expanded manifest without manual steps. Failures that are *not* missing
  paths (wrong expected values, real-tree-only facts) are PR-11's
  mini-override / `full_holdings` work, not reasons to grow the tree.
- **Audit-hook completeness caveat:** `os.stat`-only existence probes
  (`os.path.exists`) may not emit an audit event on every platform, so the
  seeded manifest can miss a few stat-only paths. This is expected and
  harmless — the PR-11 convergence loop adds any such path the moment a test
  references it. The seed is a starting point, not a guarantee of coverage.
- **Tree validation steps (before committing):** no two paths differing only
  by case (Windows/macOS checkouts); a `.gitattributes` with `* -text` at
  the data-repo root (line-ending conversion would silently corrupt sizes
  and checksums on Windows); generator unit tests for the copy-policy and
  truncation logic live in this repo.
- **Output repo:** **`rms-pdsfile-test-data`, public** (§8.1 — so CI clones it
  without secrets), containing the two trees + manifest + README (regeneration
  instructions). Size budget: aim well under 100 MB checked out; report actual
  size in the PR. **The README's regeneration commands take the source holdings
  root from `$PDS3_HOLDINGS_DIR`/`$PDS4_HOLDINGS_DIR`, never a literal path**
  (prerequisite-2 confidentiality rule) — the fixture repo is public, so a
  committed absolute path would be doubly wrong.
- Dataset coverage: every dataset that has golden tests today (13 PDS3
  volsets, 3+ PDS4 bundles), one or two volumes/bundles each, limited to the
  files the access log demands.

**PR-11 (L)** `test: override-model goldens and hermetic parametrization`
- **Golden model — single base set plus sparse mini overrides (NOT two
  parallel trees).** `tests/golden/full/…` (moved in PR-07, regenerated only
  against real holdings) is the **authoritative base**: every golden-backed
  test has its file here. `tests/golden/mini/…` holds **only overrides** — a
  file appears there **iff** that test's expected value genuinely differs when
  computed against the mini fixture tree (i.e. a case-(b) tree-shape fact).
  Resolution in the golden helper:
  - `holdings_flavor == full` → always read `tests/golden/full/<path>`.
  - `holdings_flavor == mini` → read `tests/golden/mini/<path>` **if it
    exists, else fall back to** `tests/golden/full/<path>`.
  - `--update` under `full` writes `full/<path>`. `--update` under `mini`
    computes the value, **compares it to the base** `full/<path>`, and writes
    `mini/<path>` **only when it differs** (and deletes a now-redundant
    `mini/<path>` when it no longer differs) — so the override set never
    accumulates byte-identical copies.
  Rationale: most mini/full goldens would be byte-identical (the fixture is
  seeded from the tests' own access log, so the files a case resolves to are
  present in both trees), and duplicating them is exactly the "dual
  maintenance" drift risk (§7). The presence of a `mini/` file is itself the
  self-documenting signal "this assertion depends on the shape of the tree."
  A genuinely-differing answer with no override fails **loudly** against the
  base golden — the correct prompt to add one — so there is no silent pass.
- **Inline `@parametrize` expected values must be converted to golden files
  (finishing the unfinished half of issue #40).** The golden mechanism above —
  `test_results/` + `--update` + `pdsfile_test_helper` — was built for issue
  #40 ("PdsFile needs a different test framework", **closed**) but was only
  applied to the **rules** tests. The blackbox/whitebox tests still carry their
  expected values inline in the parametrize tables (e.g. `test_childnames`'s
  100+ COISS_2xxx volume names at `test_pds3file_blackbox.py:75`), so they have
  no golden file to key by flavor and cannot be ported by a flavor switch
  alone. **Scope for THIS PR: only the case-(b) tests** — those whose inline
  expected value is a full-tree fact that the mini tree changes. For each,
  finish #40's prescription: remove the inline expected value, put the golden's
  identifier in its place, generate the base `full/<path>` with `--update`
  against real holdings, then generate any needed `mini/<path>` override with
  `--update` under `mini`. Tests whose inline values are **not** tree-dependent
  (case (a) — they already pass against mini unchanged) are **left inline** in
  this PR; converting the entire blackbox/whitebox suite to the golden-file
  framework is tracked separately as **issue #92** (already filed), not done
  here, so PR-11 does not balloon. Reference #92 in the PR description. #92
  fully specifies the follow-up on its own — background, the override model,
  the per-test method, the "no expected value may change during conversion"
  guardrail (regenerate, then diff against the pre-conversion value; any
  difference is a conversion bug, not a new golden), and a grep-clean
  acceptance criterion — so it needs no context from this plan to execute.
- Walk every existing test with this decision rule: (a) passes against mini
  unchanged → done (leave it as is — inline values stay inline; no golden
  conversion); (b) fails only because expected values are full-tree
  facts (childname lists, counts) → convert to the golden framework (above)
  and write a `mini/<path>` override for the differing value; (c) fails
  because data is missing → expand the fixture **iff** the
  additional payload is < 5 MB compressed and < 500 files, else (d) mark
  `full_holdings` (whole function, or individual `pytest.param` cases —
  case-level marking is preferred when only some cases need real data).
  Audit specifically for real-tree literals that stubs invalidate: grep the
  test tree for 32-hex MD5 literals and byte-size integers and classify each
  occurrence as (b) or (d). **Subtlety:** an MD5 or size literal is usually
  case **(b)** (base golden from real holdings + a mini override), *not* (d) —
  the mini tree's
  checksums/shelves were regenerated by dogfooding (PR-10) over the *stub*
  bytes, so they are internally consistent and the mini override captures the
  stub-correct value. Reserve (d) for assertions that genuinely need real file
  *content or real byte sizes* (e.g. a test that opens a data product and reads
  pixels). Expect to approach the ≥90% target; pre-classify the size/count
  assertions in the cached-behavior and whitebox test files (the
  `*_blackbox_cached` and `*_whitebox` test modules under `tests/pds3file/`) in
  the PR's audit appendix.
- Target: **≥ 90% hermetic**, where the ratio's **denominator is defined
  precisely** as: all `test_` functions collected under `tests/` after PR-08
  (~273 functions = the original 217 + the ~56 rule tests moved in PR-08 +
  any additive coverage tests PR-08 adds), counting each parametrized
  function as **one** unless it is marked at the `pytest.param` case level, in
  which case its hermetic and `full_holdings` cases count separately. The PR
  reports the actual split and lists every `full_holdings`-only test with a
  reason. **If the achievable ratio is below 75%, stop and bring the numbers
  to the owner** (fixture-size vs. coverage trade-off is an owner decision).
- **Create `tests/test_data_version.txt`** in this PR (no earlier PR can — it
  needs the finalized test-data-repo commit SHA, which exists only once the
  tree is complete and the hermetic invariant first holds). It records that
  SHA and is the single source of the CI pin consumed by PR-14.
- CI-facing invariant after this PR: with this repo installed, the test-data
  repo checked out at the pinned SHA, its manifest mtimes re-applied, and
  `PDSFILE_TEST_DATA_DIR` pointing at it, `PDSFILE_TEST_HOLDINGS=mini pytest`
  passes with no access to real holdings.

**PR-12 (M)** `test: pytest-xdist parallel execution`
- Add `-n auto --dist loadfile` for hermetic runs (file-level distribution
  keeps the cached-behavior tests, which depend on within-file ordering of
  cache state, on one worker). Per-process preload of the mini tree is
  cheap; each xdist worker preloads independently — verify memory/time.
- Audit and fix ordering/shared-state hazards: the cached-behavior tests
  must be self-contained within their file; conftest **errors out** if
  `--update` is combined with more than one xdist worker; `s`/`ns` modes
  remain separate pytest invocations (global `SHELVES_ONLY` — accepted
  limitation of phase "a").
- Nightly full-data runs get a conservative worker count (preload cost ×
  workers; start serial, tune later).

**PR-13 (L)** `test: maintenance-tool test suite` (closes issue #82)
- `tests/holdings_maintenance/`: for each pds3/pds4 tool pair —
  copy the mini tree into `tmp_path`, re-apply manifest mtimes, then exercise
  the full task cycle: `--init` from scratch → compare to committed goldens →
  `--validate` (clean) → corrupt → `--validate` (must fail with the right
  log content) → `--repair` → `--validate` (clean) → `--update` after adding
  a file. Corruptions are **fixed scenarios declared in a table at the top
  of each test module** (e.g. "overwrite byte 0 of `<specific file>` with
  0xFF", "delete `<specific entry>` from the md5 file", "touch `<file>` to
  mtime+100"), never randomized. Compare `.py` sidecars (sorted, text)
  rather than pickles where possible; compare archives by member tuples,
  never bytes.
- `crlf.py` unit tests (its pure classifier `test_crlf`). **Collection trap:**
  `crlf.test_crlf` is named `test_*`, so `from …crlf import test_crlf` makes
  pytest collect the *imported* function and fail on a missing `filepath`
  fixture — import the **module** (`from pdsfile...holdings_maintenance.pds3
  import crlf`) and call `crlf.test_crlf(...)`, never import the name. `shelf_consistency_check`
  and `show_opus_products` have no `main()` yet at this phase (that is PR-28,
  Phase 6), so test them here **via `subprocess`** invoking
  `python <path>.py` — a stable interface that survives the PR-28 refactor.
  PR-28 then adds an in-process `main()` and switches these tests to call it
  directly (see PR-28). `re_validate` and the shell scripts: explicitly out
  of scope (ground rule 7); an import-safety exclusion is documented.
- `pdsdependency` tests: run against the mini tree with deliberately removed
  derived files; assert the emitted "Steps required" commands.

### Phase 4 — CI

**PR-14 (L)** `ci: hermetic PR gate + nightly full-data + opus integration`
- `run-tests.yml` (PR gate, GitHub-hosted): jobs —
  `lint` (ubuntu, py3.13: `ruff check` + the API-freeze test; `pymarkdown`
  activates with PR-31/34, `ruff format --check` with PR-23/24 **to whatever
  scope the owner approves at those PRs' churn checkpoints (possibly none)**,
  the sphinx gate
  with Phase 7 — matching PR-04's staged-enable table and keeping CI in exact
  correspondence with `run-all-checks.sh`) and `test` matrix
  `[ubuntu-latest, windows-latest, macos-latest] × [3.10, 3.11, 3.12, 3.13]`:
  checkout this repo + the test-data repo at the commit SHA recorded in
  `tests/test_data_version.txt` (single source of the pin; bumping it is a
  normal reviewed change in this repo), set `PDSFILE_TEST_DATA_DIR`, install
  `.[dev]`, run the hermetic suite as two invocations matching the current
  script's scope — `--mode ns` over pds3+pds4, then **`--mode s` over pds3
  only** (the shelves-only mode is a pds3-only run today; do not add pds4 under
  `s`, whose pass/fail the baseline never measured) — `-n auto --dist loadfile`,
  coverage combined; upload to codecov on ubuntu/3.13. **Path set (pin it so
  coverage doesn't drift between executor runs):** the `ns` invocation collects
  `tests/` in full (`tests/api/`, `tests/pds3file/`, `tests/pds4file/`,
  `tests/rules/`, `tests/holdings_maintenance/`); the `s` invocation collects
  only the pds3 paths carrying `--mode`-sensitive tests (`tests/pds3file/`,
  `tests/rules/pds3/`), matching today's split. Triggers: PRs to `rewrite` and
  `main`, push to both, dispatch.
- Delete `run_tests_coverage.sh` (superseded by `run-all-checks.sh`; its
  `--update` pass-through is documented in the dev guide instead).
  `run-all-checks.sh` checks for `PDSFILE_TEST_DATA_DIR` before its pytest
  gate and prints the one-line clone/export instruction if missing.
- `nightly-full-tests.yml` (self-hosted, cron): the current full-data run,
  preserved — holdings env vars come from the runner environment (never
  hardcoded in the workflow), runs the complete suite
  including `full_holdings` tests against real holdings
  (`PDSFILE_TEST_HOLDINGS=full`), both modes, linux + windows runners.
  This satisfies ground rule 4 permanently.
- `run-tests-and-opus.yml`: OPUS integration stays **self-hosted**, triggered
  as today (`workflow_dispatch` already present + PRs to main). Rewire its
  `test_pdsfile` job — currently `uses: ./.github/workflows/run-tests.yml` —
  to invoke the **full-data** path (the new `nightly-full-tests.yml`'s callable
  form) rather than the now-hermetic `run-tests.yml`, so the OPUS leg still
  runs against real holdings. (No workflow references `run_tests_coverage.sh`;
  that file is deleted for being a superseded *local* helper, not a CI script.)
- `scripts/run-all-checks.sh` and CI kept in exact correspondence
  (`environment.mdc`); `codecov.yml` stays informational until the hermetic
  suite's coverage stabilizes, then targets are set (Phase 8).

### Phase 5 — Core module decomposition (issue #77a)

Every PR in this phase: hermetic suite green on CI, API-freeze green, plus a
**local full-data run whose per-test pass/fail set is diffed against the
Phase-0 baseline and recorded in `critiques/phase5-validation.md`** (both
modes; "green" = identical set, §6.2). Technique: method groups move to
**mixin classes** in new private modules
(`class PdsFile(_ShelfMixin, _OpusMixin, …)`), module-level functions move to
private modules; `pdsfile/pdsfile.py` keeps re-exporting every name it
exports today so `pdsfile.pdsfile.X` access is unchanged. Fixed mechanics for
every extraction PR:
- The `class PdsFile` statement itself **stays in `pdsfile/pdsfile.py`**
  (pickled instances and `PdsFile.__module__` keep their path; memcached
  pickles depend on it).
- Mixins define **no `__init__` and no new state** — methods/properties
  only, referencing existing instance/class attributes; class attributes
  (e.g. `SHELF_CACHE`) stay defined on `PdsFile`.
- Before merging: assert no method-name collisions across mixins (a simple
  set-intersection check in a **separate** test, `tests/api/test_mixin_collisions.py`,
  created in PR-17 — **not** inside `test_api_freeze.py`, which §6.4 forbids
  editing), and confirm the manifest diff is empty (it records
  names/signatures, not defining classes, so a clean mixin move is invisible to
  it — any diff means a mistake).
- **Class-object references (pinned pattern, no executor discretion):** a
  mixin module must **not** do a module-level `from pdsfile.pdsfile import
  PdsFile` — `pdsfile.py` imports the mixin modules to build the class, so a
  top-level back-import is a cycle. Any extracted method that needs a *class
  object* (not just a name) uses a **function-local deferred import**:
  `from pdsfile.pdsfile import PdsFile` inside the method body. The known
  instance is `opus_products`' `PdsFile.__subclasses__()` (`pdsfile.py:4778`),
  extracted in PR-19 — verified to be the **only** bare class-object reference
  inside any extraction seam, so this rule is cheap and complete. (Names, by
  contrast, are still resolved by `__name__` as the code does today — e.g. the
  PR-19 `__bases__` sniff.)

**PR-15 (M)** `fix: repair latent bugs in rarely/never-exercised core paths`
Each fix gets a regression test first (hermetic where possible). **Note bug #1
is behavior-affecting** (it changes cache population for a live property), so
unlike the genuinely dead bugs below it may legitimately shift the pass/fail
set of the cached-behavior full-data tests — call that out in the PR with a
recorded explanation (returned *values* are unchanged; only cache state is):
1. `html_path` property: `self._recache` missing `()` (pdsfile.py:1785) — a
   no-op today, so `html_path` results are never cached; fixing to
   `self._recache()` (as the correct call at :3023 does) restores cache
   writeback for this live, commonly-used property.
2. `get_permanent_values`: `resume_caching()` called without its `cls`
   argument (:712 — inside `get_permanent_values`, lines 665–714, **not**
   `preload`, which starts at :840).
3. `abspath_for_logical_path`: hard-coded `PDS3_HOLDINGS_DIR` env lookup in
   shared base breaks Pds4 resolution (:197–198). Fix semantics, exactly: add
   a **private** class attribute `_HOLDINGS_ENV` (`'PDS3_HOLDINGS_DIR'` on
   `PdsFile` and `Pds3File`, `'PDS4_HOLDINGS_DIR'` on `Pds4File`; private so it
   is freeze-invisible) and look that up instead of the literal.
   `abspath_for_logical_path` is a module-level function taking `cls`, so it
   reads `cls._HOLDINGS_ENV`. PDS3 and base-class behavior are bit-identical;
   Pds4 gains the env fallback it was always supposed to have (new tests cover
   both).
4. `DictionaryCache.set_multi` passes unsupported `pause=` kwarg (pdscache:224).
5. `MemcachedCache.set_multi` iterates a dict as tuples (pdscache:798).
6. `pdsviewable.iconset_for` references undefined `ICON_FILENAME_VS_TYPE` (:547–559).
7. Bare `except:` at pdsfile.py:3020 → `except Exception` (behavior-audited).
(Maintenance-tool bug twins — `LOGDIRS`, `abs(bool)`, `checksum1 != checksum1`,
`shelf-consistency-check` undefined `error`, `re_validate` untouched ones
documented only — are fixed in Phase 6 where those files are being edited.)

**PR-16 (L)** `refactor: extract module-level path helpers → _path_utils.py`
Lines 47–247 (`construct_category_list`, `logical_path_from_abspath`,
`_clean_join/_clean_abspath/_clean_glob/_needs_glob`, `repair_case`,
`formatted_file_size`, `abspath_for_logical_path`, `selected_path_from_path`).
**Also carry the module constants these helpers use that sit *before* line 47**
— `FILE_BYTE_UNITS` (:40-42, used by `formatted_file_size` at :170) moves here;
`PATH_EXISTS_CACHE_SIZE` (used by `_local_fs`'s `lru_cache` at :1280) moves with
`_local_fs.py` in PR-17. Both are public, so `pdsfile.py` re-exports them (like
every other extracted name). Sweep for any other pre-:47 module constant a
moved symbol references, and move/re-export it with its consumer.

**PR-17 (L)** `refactor: extract shelf and local-filesystem subsystems`
Two mixins in this PR (both call each other, so they move together):
- `_shelves.py` (5061–5359): `shelf_path_and_lskip`, `shelf_path_and_key`,
  `_get_shelf`, `_close_shelf`, `close_all_shelves`, `shelf_lookup`,
  `shelf_path_and_key_for_abspath`, `info_shelf_expected`,
  `shelf_exists_if_expected`. The `SHELF_CACHE`/`SHELF_ACCESS`/
  `SHELF_NULL_KEY_VALUES` class attributes remain on `PdsFile`. The `eval()`
  of the `.py` sidecar line is kept (behavior) but isolated in one named
  function with a documented contract.
- `_local_fs.py` (1259–1661): `_non_checksum_abspath`, `os_path_exists`,
  `os_path_isdir`, `os_listdir`, `glob_glob` — the case-repair /
  `SHELVES_ONLY`-branching filesystem layer. It calls into `_shelves.py`,
  which is why it moves in the same PR. (These ~400 lines were unassigned in
  earlier drafts; they belong here, not in the residual core.)
Both are mixins under the Phase-5 mechanics preamble (no new state, class
attributes stay on `PdsFile`).

**PR-18 (M)** `refactor: extract checksum/archive/log path builders → _derived_paths.py`
(4898–5059, 5361–5516.) This is the file-location half of issue #47:
`set_log_root` and the three `log_path_for_*` methods (used only by the
maintenance tools) move physically into `_derived_paths.py` as a mixin.
Because of the API freeze they stay reachable as `PdsFile.set_log_root` /
`PdsFile.log_path_for_*`, and the tools keep calling them exactly as today
(e.g. `pdsdir.log_path_for_volume(...)`, `Pds3File.set_log_root(...)`) — the
move is invisible to callers. Actually *removing* them from the public class
surface (what #47 ultimately wants) is an API break deferred to phase "b".
Deduplicate the three near-identical `log_path_for_*` bodies into one private
`_log_path_for(...)` helper the three methods delegate to (behavior-identical,
golden-tested via the tool tests from PR-13).

**PR-19 (L)** `refactor: extract OPUS and index-row support → _opus.py, _index_rows.py`
(4642–4896, 4358–4640.) **Leave the `cls.__bases__[0].__name__ == 'Pds4File'`
sniff (:4566) behaviorally unchanged.** It is *not* broken by this refactor:
there `cls = type(self)` is a rule subclass whose `__bases__[0]` is
`Pds3File`/`Pds4File`, and extracting methods into mixins on `PdsFile` does
not alter a rule subclass's direct base. An inherited boolean would **not** be
behavior-identical (it would differ for `Pds4File` itself and for deeper
subclasses), so replacing it here would violate the freeze's spirit — record
the string-sniff fragility as a phase-"b" item instead and move on. If the
extracted code must reference `Pds4File` by name across module boundaries,
resolve it the same way the code does today (by `__name__`), not by importing
`Pds4File` into the base module (which would create an import cycle). Keep
`PdsFile.__subclasses__()` sibling discovery as-is.

**PR-20 (L)** `refactor: extract associations, split/sort, transformations → _associations.py, _sorting.py`
(5979–6289, 5518–5871, 5873–5977.) Note `is_logical_path` (classmethod at
:6281) falls inside the associations line window but is a generic path
predicate, not an association. It is a **public `PdsFile` classmethod** (frozen
as `PdsFile.is_logical_path`), so it cannot become a plain module function in
`_path_utils.py` without vanishing from the class surface — **leave it in
core** (or, if a path mixin is later introduced, there); just do not sweep it
into `_associations.py`. The associations proper end at `associated_parallel`
(ends :6280).

**PR-21 (L)** `refactor: extract preload machinery → _preload.py`
(662–1079: `get_permanent_values`, `load_volume_info`,
`cache_category_merged_dirs`, `preload`, `cache_lifetime`. Note `_preload_dir`
is a **nested** local function inside `preload` (defined :965, called :987/
:1049), not a class method — it moves automatically with `preload`, not as a
separate target.) `preload_and_cache.py` becomes a compat re-export shim
(public surface kept).

**PR-22 (M)** `refactor: finalize pdsfile.py core`
Two moves in this PR:
- **Extract the ~1,550-line lazy-property block to a `_properties.py` mixin**
  (`_PropertiesMixin`) — owner-decided (§8.3). Each `@property` only reads
  `self._X_filled` and calls `self._recache`/`self._complete`, which remain in
  core, so this is a pure relocation and manifest-neutral (same Phase-5 mixin
  mechanics: no new state, class attributes stay on `PdsFile`).
- Finalize core. **Explicit stay-list (nothing else is extracted in phase
  "a" — do not over-extract):** class config/registries and the sort-config
  setters (`sort_labels_after`/`sort_dirs_first`/… :415–449); the
  `use_shelves_only`/`require_shelves`/`set_logger`/`set_easylogger`
  classmethods (:606–657); the constructor + `_X_filled` slots;
  `new_merged_dir` (:1082), `new_index_row_pdsfile` (:1166), `copy`,
  `__repr__`; the bundle/bundleset utilities (:3226–3397);
  `_complete`/`_update_ranks_and_vols`/`_recache` (:3403–3520); the
  `child`/`parent`/`from_*` constructors (:3536–4356); and `is_logical_path`
  (:6281, per PR-20). **Target: ~1,750 lines** (down from 6,304; ~2,930 lines
  leave in PR-16–21, the ~1,550-line property block leaves here, ~89 lines of
  dead code removed).
Add a module docstring mapping the decomposition (feeds the dev guide). Remove
commented-out dead code (~89 lines) — listed line-by-line in the PR.

**PR-23 (L, mechanical)** `style: ruff-clean and format core modules`
Clean `src/pdsfile/*.py` (core: `pdsfile.py`, `pdscache.py`, `pdsviewable.py`;
not rules). **Do not assume a fixed violation list — derive it:** run
`ruff check --select E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF` and classify each
violation as **fixable** or **freeze-locked** (fixing it would change a frozen
public signature/name, add an inline type annotation forbidden by ground rule
5, or require reformatting an aligned table). Fix the fixable ones (UP004,
E721, E722, UP031, RUF005/015, C405, local-var naming, etc.). **Freeze-locked
violations in core become an enumerated, justified permanent per-file-ignore**
(the lint half of this PR proceeds regardless of the formatting decision below)
— as of 2026-07-17 these are: **`B006`** (`pdsviewable.py` `to_dict(exclude=[])`,
`PdsViewSet.__init__(viewables=[])` — public frozen signatures; **do NOT
"fix" B006, it is a manifest break**), **`A002`** (`log_path_for_*(…, dir='')`
in `pdsfile.py`, called by keyword `dir='…'` from the tools — frozen param
name), and **`RUF012`** (mutable class-attribute defaults like
`SUBCLASSES = {}`, `SHELF_CACHE = {}`, `VOLTYPES = [...]` — the only ruff fix is
a `ClassVar` annotation, forbidden by ground rule 5). The ratchet shrinks to
**only** this enumerated freeze-locked set for these files, not to zero.
**Formatting — mandatory owner checkpoint (hard stop) before committing any
reformat:**
1. First run `ruff format --diff` over the target file set and measure the
   churn (files touched, lines changed, and a skim of *what kind* of change
   dominates). Before measuring, protect deliberately aligned code: any block
   that is vertically aligned to look good (aligned assignment columns,
   hand-shaped tables or literals) gets `# fmt: off` / `# fmt: on` guards so
   the formatter leaves it alone.
2. **Stop and present the churn numbers and diff samples to the owner.** The
   owner decides: proceed as scoped, reduce the scope (more exclusions / more
   `fmt: off` guards), or **drop the reformat entirely**. Do not commit any
   reformatting before this decision.
3. Only on an explicit go: run the one-time `ruff format` over the approved
   set and enable the `ruff format --check` gate (CI lint + run-all-checks)
   scoped to it. If the owner drops or reduces formatting, the gate matches
   the reduced scope (or is never enabled) and the decision is recorded in
   `pdsfile_overrides.mdc`.
No behavior change; full-data run to prove it. Record the freeze-locked set in
`pdsfile_overrides.mdc`.

**PR-24 (L, mechanical)** `style: ruff-clean and format rules and remaining files`
Rules files + pds3file/pds4file `__init__` (including deduplicating the
twice-defined Pds3File alias properties — semantically identical bodies, one
positional/one keyword form; manifest unchanged). `__init__.py` star imports
get `__all__` + targeted `noqa` where the re-export pattern is intentional.
**Freeze trap (do not "clean up"):** the `pds3file`/`pds4file` `__init__`
modules carry incidental top-level names that are in the manifest (e.g. `re`,
`pdslogger`, `pdscache`, `cache_lifetime_for_class` on `pdsfile.pds3file`).
ruff flags them as unused imports (F401), but removing them is a manifest break
outside both forgiveness categories (a hard stop). Keep them (permanent F401
ignore per deviation (4)); never delete a manifested name to satisfy the
linter.
**F811 fix direction (do not guess):** where a name is defined twice, delete
the *dead* definition, not the live one — for the twice-defined `Pds3File`
alias properties delete the redundant copy (bodies are semantically identical);
for `COVIMS_0xxx.py` `OPUS_ID_TO_PRIMARY_LOGICAL_PATH` (a translator table at
:287 shadowed by the live method at :324) delete the **dead table assignment
at :287**, keeping the method (deleting the method would change behavior and
the manifest kind). The COVIMS test + manifest catch a wrong choice, but
choosing right saves a review cycle.
- **The ratchet shrinks to a permanent, enumerated per-file-ignores block for
  the rule modules** (derive it by running `ruff check` with the template
  select set, same method as PR-23 — do not hardcode blindly). As of
  2026-07-17 the freeze-/table-locked set for `pds{3,4}file/rules/*.py` is:
  **`E501`** (~1,533 hand-aligned table lines >100 cols), **`W191`** (~302 tab
  indents in the pds4 tables — retabbing = the forbidden table rewrite),
  **`N801`** (rule class names `COISS_xxxx` …, frozen), **`N999`** (invalid
  module names `COISS_xxxx.py` …, frozen public modules), **`N802`** (frozen
  uppercase methods `DATA_SET_ID`/`FILENAME_KEYLEN` …), **`N805`**
  (`COVIMS_0xxx.py:324` `OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)` — no `self`;
  `@staticmethod` would change the manifest kind), and **`RUF012`** (mutable
  class-default tables like `VIEWABLES = {...}`; `ClassVar` forbidden by ground
  rule 5). Everything else in rule modules (I001 import-sort, E701, UP031,
  F403/F405/F401 after the PR-08 star-import removal, RUF022, N806 local vars,
  F811/F841) **is fixable and fixed** — the star-import-related F403/F405 mostly
  vanish once PR-08 replaces `import *` with explicit imports. Also the
  `pds{3,4}file/__init__.py` files keep permanent `F401` (manifested
  incidental re-exports, kept per the PR-24 freeze-trap note), `A002` (frozen `dir=` alias params),
  and `RUF012`. **Record the full per-file-class freeze-locked set in
  `pdsfile_overrides.mdc` deviation (4).**
- Formatting: **same mandatory owner checkpoint as PR-23** — `ruff format
  --diff` first, churn numbers and samples to the owner, no reformat committed
  before an explicit go/reduce/drop decision. Scope: everything remaining
  **except the rule modules and `re_validate.py`** (both in
  `[tool.ruff.format] exclude`; the rule modules for the hand-aligned tables,
  `re_validate.py` because ground rule 7 / deviation (6) freeze it —
  `ruff format --check` confirms it *would* be reformatted). Additionally,
  **vertically aligned code is never reformatted**: the aligned
  `pytest.mark.parametrize` tables in the test tree and any other block lined
  up for readability get `# fmt: off` / `# fmt: on` guards before the churn
  measurement. If the owner approves, the format gate covers the whole repo
  minus the exclusions and guards; if not, the gate stays at whatever scope
  (possibly none) the owner approved, recorded in `pdsfile_overrides.mdc`.
- **`re_validate.py` also gets a permanent `ruff check` per-file-ignore set**
  (its full derived violation set — UP031, E402, RUF059, E701, I001, B007,
  RUF005, C405, RUF051, E721, UP034 as of 2026-07-17), for the same freeze
  reason, not tables. Add it to `pdsfile_overrides.mdc` deviation (4). Note:
  cleaning *other* `holdings_maintenance/` tools here is behavior-preserving
  style only and does not conflict with PR-10's "shipped tool frozen until
  Phase 6" (that concerns runtime behavior like walk order, not formatting).

### Phase 6 — Maintenance tools consolidation

Gates: PR-13's tool tests + a real-holdings validate run of each migrated tool
against at least one real volume/bundle, recorded in
`critiques/phase6-validation.md`. CLI names, flags, output formats, log
formats, and exit codes are all frozen (tests assert them).

**PR-25 (L)** `refactor: shared maintenance-tool core (_common.py) + archives pair`
Extract the shared skeleton the **five** pds3/pds4 tool-pairs re-implement
(archives, checksums, indexshelf, infoshelf, linkshelf). `pdsdependency` is
**pds3-only** and does not fit the five-task/`ToolSpec` shape; it is **left as
a standalone tool this phase** (only its Phase-5 latent-bug note applies) —
stated so no one hunts for a pds4 twin or a sixth migration. **Concrete target
interface for `holdings_maintenance/_common.py`** (so the design is not
re-invented per implementer):
- `BACKUP_FILENAME` regex, the `*_LIMITS` defaults, `hashfile()`, and
  `move_old_<kind>()` version-numbering — moved verbatim, one copy.
- A `@dataclass ToolSpec` capturing everything that varies between a pds3 and
  pds4 tool: `pdsfile_cls` (`Pds3File`/`Pds4File`), `vocab`
  (`{'bundle': 'volume'|'bundle', ...}` for log text), `holdings_sentinel`
  (`'/holdings/'` vs `'/pds4-holdings/'`), `index_ext` (`.tab`/`.csv`),
  `logname` (e.g. `'pds.validation.archives'`), and a `log_extra_handlers`
  flag (pds4 adds a `warning_handler`; pds3 does not).
- `build_arg_parser(spec)` → the argparse parser with the five task flags with
  **today's exact semantics** — they are independent `store_const`-into-`task`
  flags, **not** an `add_mutually_exclusive_group` (do not introduce one; that
  would turn a multi-flag invocation from today's last/first-wins into an
  argparse hard error) — plus the `volume/bundle` positional + `--log`/`--quiet`
  and a hook for tool-specific flags (`--archives`, `--infoshelf`). PR-13 adds
  a two-flag invocation case pinning the current resolution behavior.
- `run_main(spec, task_table, argv)` → the `main()` driver loop (resolve log
  root from `PDS_LOG_ROOT`, build the `PdsLogger` + handlers, resolve the
  pdsfile list, run nested `logger.open`/`close` scopes, set exit code from
  fatal/errors). `task_table` maps `'initialize'|'reinitialize'|'validate'|
  'repair'|'update'` → the tool's callables.
- Each thin tool module (`pdsarchives.py`, …) shrinks to: its `generate_*`/
  `read_*`/`write_*`/`validate_*` domain functions, a `SPEC = ToolSpec(...)`,
  a `TASKS = {...}`, and `def main(): return run_main(SPEC, TASKS, sys.argv)`.
Migrate `pdsarchives`/`pds4archives` first (hardest divergence: pds3
single-tar vs pds4 one-bundle-→-many-tarballs — modelled as a `write_archive`
hook on the spec, not an `if pds4:` branch). The CLI surface, output, log
format, and exit codes are asserted unchanged by PR-13's tests.

**PR-26 (L)** `refactor: migrate checksums and infoshelf pairs onto the core`
Fix the pds3 bugs, each with a test — but **decide the intended semantics; do
not blindly inherit pds4's version:**
- `LOGDIRS` global-shadowing (pds3 assigns it as a `main()` local; pds4
  correctly `global`s it) → adopt pds4's fix.
- `checksum1 != checksum1` (pds3 `pdsinfoshelf.py:399`, compares a var to
  itself → always False) → pds4's `checksum1 != checksum2` is the correct
  intent; adopt it.
- `abs(modtime1 != modtime2) > 1` (pds3 `pdsinfoshelf.py:394`) — pds4 replaced
  this with bare `modtime1 != modtime2` (`pds4infoshelf.py:393`). The `> 1`
  clearly intended a **1-second tolerance**, but note the operands are **ISO
  time strings** (truncated to seconds at `pdsinfoshelf.py:380-381` via
  `.rpartition('.')[0]`), so both `abs(str != str)` (the original bug) and a
  literal `str - str` (a naïve "fix") are wrong — the latter raises
  `TypeError`. Implementable fix (the intended semantics): parse the two
  **untruncated** modtime strings with `datetime.fromisoformat` and compare
  `abs((t1 - t2).total_seconds()) > 1`; drop the now-unneeded second-truncation
  lines. Pin the 1-second tolerance with a test. **Owner-confirmable:** if the
  intended semantics is instead pds4's coarser "same truncated second"
  (string equality after truncation), say so and adopt that — but the default
  is the real 1-second tolerance, since exact/second equality risks
  false-positive validate mismatches from mtime drift on real holdings.
  Whichever is chosen, pds3 and pds4 share it via `_common.py`.
Preserve the pds3 `--infoshelf` chaining behavior (modernize `os.system` →
`subprocess.run` as pds4 already does — flagged behavior change, tested).

**PR-27 (L)** `refactor: migrate indexshelf and linkshelf pairs onto the core`
Migrate `pdsindexshelf`/`pds4indexshelf` and `pdslinkshelf`/`pds4linkshelf`
onto `_common.py`, same pattern as PR-25/26 (ToolSpec + task table + thin
`main()`); CLI surface, output, log formats, and exit codes asserted unchanged
by PR-13's tests. The large pds3 `REPAIRS` table is moved **content-unchanged**
into its own data module, `pds3/linkshelf_repairs.py`, imported by the thin
linkshelf tool.

**PR-28 (M)** `refactor: main() for crlf, shelf_consistency_check, show_opus_products`
Proper argparse + `main()` so they are testable and runnable via
`python -m pdsfile.…`. **No new console-script names** (§8.4 — `python -m`
only; `[project.scripts]` is not extended). Also fixes the
`shelf_consistency_check` `undefined error` bug (the
undefined `error` name that should be `errors`, noted in PR-15's bug list) with
a regression test. **Update the PR-13
subprocess tests** for these two tools to call `main()` in-process and keep
them green (the behavior under test is unchanged; only the invocation path
moves from subprocess to direct call). `re_validate.py`: untouched (ground
rule 7).

### Phase 7 — Docstrings and documentation

**PR-29 (L)** `docs: Google-style docstrings — core modules`
Per `doc_python.mdc`: every module/class/method/function in
`src/pdsfile/*.py` (core, pdscache, pdsviewable); `Parameters:` sections,
wrap at 90; fix the known typos. Content must be accurate to behavior —
verified against the code, not the old docstrings.

**PR-30 (L)** `docs: docstrings — rules, subclasses, maintenance tools`
Rule modules get a standard header docstring (dataset, what each rule table
does); tools get module + function docstrings.

**PR-31 (M)** `docs: Sphinx scaffolding + API reference`
`docs/` per template: `conf.py` (autodoc/napoleon/intersphinx/mermaid/myst),
`index.rst` including the README past its `<!-- start-after-point -->` marker,
`api/` autodoc pages per subpackage. **The current README has no such marker;**
add a minimal one to the existing README in this PR (the full `doc_readme`
rewrite is PR-34) so the include target exists. Builds clean under `-W` and
`-n`. Enable the sphinx gate in `run-all-checks.sh` and the CI lint job;
`.readthedocs.yaml` goes live.

**PR-32 (L)** `docs: user guide (CLI tools)` (closes issue #45)
`docs/user_guide/`: concepts chapter (holdings layout, volumes vs bundles,
shelves, checksums, archives — with the directory taxonomy from
`setup_new_holdings.sh`); installation & environment (env vars, precedence —
**document holdings roots only as `$PDS3_HOLDINGS_DIR`/`$PDS4_HOLDINGS_DIR`
placeholders, never a literal machine path**, per the prerequisite-2
confidentiality rule);
**one chapter per CLI program** — all 11 entry points plus `crlf`,
`shelf_consistency_check`, `re_validate` (documented as-is), and
`show_opus_products` — every option documented (flag, effect, default),
runnable examples against the mini tree; a chapter documenting the sync
shell scripts (document-only, per ground rule 7); appendix: file formats
(shelf `.pickle`/`.py` sidecar, `*_md5.txt`, `_volinfo`).

**PR-33 (L)** `docs: developer guide` (closes issue #43)
`docs/dev_guide/`, with an **explicit required chapter + diagram list** (so the
synthesis is bounded, not open-ended):
1. *Repository layout* — annotated literal-block dir tree (from §4 of this
   plan, kept current).
2. *Architecture* — narrative + exactly these Mermaid diagrams:
   (a) `classDiagram` of `PdsFile` and its mixins (`_ShelfMixin`,
   `_LocalFsMixin`, `_OpusMixin`, `_IndexRowMixin`, `_AssociationsMixin`,
   `_SortingMixin`, `_DerivedPathsMixin`, `_PreloadMixin`, `_PropertiesMixin`)
   + `Pds3File`/`Pds4File`/rule-subclass leaves; (b) `flowchart` of the cache layers and
   their lifetimes (`DictionaryCache`/`MemcachedCache`, the `$RANKS`/`$VOLS`/
   `$VOLINFO` permanent keys, per-lifetime buckets); (c) `flowchart` of the
   shelf subsystem (info/link/index shelves + the `.py` sidecar `eval`);
   (d) `sequenceDiagram` of `preload()`; (e) `flowchart` of rules resolution
   (volset ID → `VOLSET_TRANSLATOR` → `SUBCLASSES` key → subclass).
3. *Subsystem reference* — one section per extracted module, each stating its
   contract and invariants (logical vs abs paths; ranks/vols bookkeeping;
   merged vs physical category dirs; the `SHELVES_ONLY` global-state
   limitation; thread-safety = single-process assumption).
4. *Extending, part A: writing a rules file for a new volume/bundle* — a
   copy-paste skeleton (module docstring, the translator tables to define, the
   `SUBCLASSES[...] =` registration, the standard test set from PR-08) walked
   through against one real small example.
4b. *Extending, part B: modifying the maintenance tools for a new dataset*
   (the second half of issue #45) — how the `_common.py` `ToolSpec` is filled,
   and how to author the `pdslinkshelf` `REPAIRS` regex table for a dataset
   with nonstandard internal links (the "complicated regular expressions" the
   issue calls out), with one worked example.
5. *Test-suite guide* — flavors (`full`/`mini`/`none`), `--mode s|ns`,
   markers, xdist (`-n auto --dist loadfile`), the override-model goldens
   (base `full/` set + sparse `mini/` overrides, with the fall-back and
   write-only-if-different resolution), and `--update` (both flavors).
6. *How-to: regenerating the fixture tree and goldens* — the two-repo dance
   (edit manifest → run `make_test_holdings.py` against real holdings → commit
   the data repo → bump `tests/test_data_version.txt`).
7. *CI/release workflow* — the three workflows, `run-all-checks.sh` as source
   of truth, setuptools_scm tagging.
Builds under `-W` and `-n`; every API symbol named in prose uses the correct
Sphinx cross-reference role (per `doc_python.mdc`).

**PR-34 (M)** `docs: README rewrite` per `doc_readme.mdc`
Badges, plain-prose introduction, features, installation, quick start (module
usage AND a CLI invocation), documentation/contributing/license links.

**PR-35 (M)** `feat: public API type stubs`
Hand-written `.pyi` stubs for the public surface (ground rule 5): `__init__.pyi`
plus stubs for `pdsfile.pdsfile`, `pds3file`, `pds4file`, `pdscache`,
`pdsviewable` covering exactly the manifest names; add `py.typed`. Typing
rule for the (unannotated) implementation: derive types from code and
docstrings; where genuinely uncertain, use the broadest type that is
provably correct (`str | None`, `list[str]`, `Any` as last resort) — a wrong
narrow type in a stub is worse than a broad one. Validated with
`mypy.stubtest` (which checks stub names/kinds against runtime — the same
guarantee level as the manifest; an allowlist covers unstubable dynamics)
run locally/CI-lint. No inline annotations.

### Phase 8 — Critique, hardening, merge

**PR-36 (M, possibly split)** `chore: run critique skills and address findings`
Run the template's `.cursor/skills` — `critique-test-suite`,
`critique-documentation`, `python-codebase-analysis` — save the full reports
in `critiques/`; triage findings with the owner; fix the accepted ones.

**PR-37 (S)** `chore: finalization`
- Verify: `run-all-checks.sh` fully green; hermetic CI green on all 12 matrix
  cells; nightly full-data green; OPUS integration green; API manifest
  identical to the Phase-0 dump (modulo the reviewed allowlist).
- Consumer smoke check: on this machine, run rms-opus import-path smoke and
  rms-viewmaster startup against the rewrite branch, and **diff the outcomes
  against the Phase-0 consumer-smoke baseline** — the gate is "same outcome as
  baseline," so the pre-existing rms-viewmaster `cache_lifetime` startup
  failure does not count against the rewrite (record in critiques/).
- Set codecov targets; CHANGELOG/release notes summarizing the rewrite.
- Open the `rewrite` → `main` PR; after merge, tag and release; close
  issues #77 (phase a), #82, #43, #45, #37, referencing #79.

## 6. Cross-cutting mechanisms

### 6.1 API-freeze enforcement
The manifest (PR-02) is the contract. The checker is enforced **locally from
Phase 0** (PR-02 ships `tests/api/test_api_freeze.py`; run it directly), **via
`run-all-checks.sh` from PR-04** (the script does not exist before then), and
**in GitHub CI from PR-14** (the existing `run-tests.yml` invokes pytest on
explicit paths that exclude `tests/api/` until PR-14 builds the lint/hermetic
jobs; PR-04 also adds `tests/api/` to the self-hosted invocation to close the
gap earlier).
Forgiven deviations live in `tests/api/manifest_allowlist.json`. Exactly
**two pre-approved forgiveness rules** exist, both expressed as **category
predicates** (not per-name records — the diffs number in the hundreds):
1. **Subpackage removal (PR-07):** the module paths
   `pdsfile.pds3file.tests*` / `pdsfile.pds4file.tests*` leaving the installed
   package.
2. **Rules test-cleanup (PR-08):** for modules matching
   `pdsfile.pds{3,4}file.rules.*`, forgive the disappearance of a name that is
   **either** (a) a `function` whose name matches `test_*`, **or** (b) one of
   the test-only names PR-08 removes — the module's own top-level `pytest`
   (a **direct** `import pytest` in each tested rule module, **not** a
   `pytest_support` star-export; `pytest_support.py` does not import pytest),
   plus the star-supplied `os`, `TEST_RESULTS_DIR`, `translate_all`,
   `unmatched_patterns`, `opus_products_test`, `associated_abspaths_test`,
   `versions_test`, `instantiate_target_pdsfile`. The predicate is expressed
   purely in the
   dump's own encoding (module-glob + name-list/`test_*`-glob + kind); there is
   no "fixture" kind (and no rules module defines a `@pytest.fixture` —
   confirmed). **Carve-out:** if any table-needed name (`translator`, `re`,
   `range_regex`, `pds3file`/`pds4file`, the rule subclass itself) disappears,
   that is a real break and a hard stop — but after PR-08's re-import step
   (which explicitly re-imports every production-needed name before removing
   the star-import) such a name never disappears, so this carve-out should
   never fire. `os` appears in list (b) *and* is production-needed in
   `COVIMS_0xxx` — there PR-08 re-imports it, so it does not disappear and (b)
   is simply not exercised; the forgiveness applies only where `os` was truly
   test-only.
Both categories carry a `pr` field and the checker **activates each category
only from its named PR** (category #1 from PR-07, #2 from PR-08) — so an
accidental rules-name loss in PRs 03–06 is *not* pre-forgiven and correctly
hard-stops. **Any diff outside these two categories stops work and goes to the
owner** — the executor may not add a third forgiveness rule (exact or category)
on its own.

(Note: PR-07 is in practice **manifest-invisible** — PR-02 excludes the `tests`
subpackages from the module set, so their removal produces no diff at all.
Category #1 is kept as belt-and-braces; do not go hunting for a PR-07 diff that
won't appear.)

### 6.2 Behavior-preservation evidence
For every Phase 5/6 PR: (1) hermetic suite, (2) full-data suite both modes on
this machine, with the **per-test pass/fail set diffed against the Phase-0
baseline — the gate passes only if the sets are identical** (a test newly
passing is as much a flag as one newly failing; both require a recorded
explanation), (3) for tool PRs, a real-volume tool run diffed against the
pre-PR output (`.py` sidecars and logs, mtime-normalized). Results appended
to the phase validation file in `critiques/`.

### 6.3 Record keeping
`plans/` — this plan; any per-phase detailed sub-plans the executor writes
before a phase. `critiques/` — the historical code-quality analysis, baselines,
per-phase validation records, the per-PR adversarial-review rounds
(`critiques/pr-<NN>/round-<k>.md`, §6.6), critique-skill reports, and the
post-merge retrospective.

### 6.4 Execution protocol for the AI executor
The plan assumes an opus-class executor working without a supervising model.
The protocol per PR:
1. Re-read the PR's section of this plan and its phase preamble. For PRs
   marked L, write a short sub-plan into `plans/` first (files to touch,
   order, verification steps) and follow it.
2. Implement; run every gate active for the phase (§2 table); record what
   the gates showed in the PR description and, where required, in
   `critiques/`.
3. **Run the adversarial pre-PR review loop (§6.6) to convergence** before
   opening the PR. Do not open a PR that has not passed a clean, zero-finding
   fresh review.
4. Open the PR against `rewrite`; do not start the next PR in a way that
   stacks unmerged behavior changes (mechanical follow-ups may proceed).

**Human-review cadence (§8.6):** every refactor/test/docs PR gets full
line-by-line human review at its boundary. The **pure `git mv` PRs of Phase 2
(PR-05–07)** may be lighter-touch — the §6.6 adversarial loop plus the
phase-boundary gates suffice, with human review optional — because they change
no logic. This does not relax any automated gate; it relaxes only the human
read on move-only diffs.

**Hard stop conditions — halt and ask the owner instead of deciding:**
- Any API-manifest diff not covered by the two pre-approved allowlist
  **categories** (§6.1). The expected large rules-cleanup diff at PR-08 is
  covered by category #2 and is **not** a hard stop; a diff touching a
  non-underscore name the tables need, or any name outside the two categories,
  **is**.
- Any full-data run whose pass/fail set differs from the baseline without a
  cause the executor can prove is the intended, documented change of that PR.
- The PR-11 hermetic ratio landing below 75%.
- **The PR-23 and PR-24 formatting churn checkpoints** (mandatory owner
  decision — go / reduce scope / drop — before committing any reformat).
- Any situation where following the plan would require changing behavior,
  file formats, CLI flags, log formats, or exit codes not explicitly listed
  as changing.
- Any new decision not already settled in §8 (all §8 items are decided) or
  elsewhere in this plan — surface it rather than choosing unilaterally.

**Prohibitions (absolute):** never edit `api_manifest.json`, the allowlist, or
— **after PR-02 lands** — `scripts/dump_public_api.py` / `tests/api/test_api_freeze.py`
(editing the dumper or the checker makes any diff vanish while both sides agree
— a silent freeze defeat; put any *new* API-adjacent test assertions in a
separate file, never in these two); never edit golden files or the baseline
records to make a gate pass;
never disable, skip, or mark-xfail a failing test to get to green; never widen
the ruff ratchet. Golden files change only via `--update` runs whose necessity the PR
description justifies. Deviations from this plan require an addendum file in
`plans/` acknowledged by the owner before the deviating PR merges.

### 6.5 Highest-judgment sections (where an Opus executor must slow down)

Most PRs are mechanical. These five carry the most design judgment; each has
been given a concrete spec above so an opus-class executor can do them without
a more-capable model. If, while executing one, the concrete spec still leaves
a genuine design fork the plan doesn't resolve, that is a §6.4 hard stop —
write the options into `plans/` and get the owner's pick rather than guessing.

- **PR-10 fixture generator** — spec'd: audit-hook seeding, six-class copy
  policy, dogfood order, `.gitattributes`/case/mtime rules.
- **PR-11 hermetic audit** — spec'd: the (a)–(d) per-test decision rule, the
  <5 MB/<500-file expand threshold, the MD5/size-literal grep audit, the
  ≥90% target with a <75% hard stop.
- **PR-22 core finalization** — spec'd: ~1,750-line target after moving the
  lazy-property block to `_PropertiesMixin` (§8.3).
- **PR-25 `_common.py` design** — spec'd: the `ToolSpec`/`build_arg_parser`/
  `run_main` target interface and the pds3/pds4 divergence-as-hook rule.
- **PR-33 developer guide** — spec'd: the exact chapter list and the five
  required Mermaid diagrams.

The remaining creative-writing work (PR-29/30 docstrings, PR-32 user guide) is
bounded by `doc_python.mdc`/`doc_user_guide.mdc` structural mandates and the
`critique-documentation` skill run in PR-36; it needs care but not a
design decision, so it is left to normal execution.

### 6.6 Adversarial pre-PR review loop (mandatory for every PR)

Before opening **any** PR, the executor runs a self-contained adversarial
review loop. Its purpose is to catch, with fresh eyes, the class of defect the
author is blind to — the kind a fresh no-context reviewer reliably finds that
the implementer does not. (This plan itself was hardened by repeated no-context
reviews; the records are in `critiques/` if useful, but nothing here depends on
reading them.)

**Round procedure:**
1. Finalize the code; confirm every phase gate (§2) passes locally.
2. Spawn a **fresh Opus subagent as adversarial reviewer, with no development
   context** — it must not receive the implementation conversation, the
   executor's reasoning, or prior review rounds. Give it exactly:
   - the PR's section of this plan (its deliverables), the phase preamble, the
     ground rules (§2), and the relevant cross-cutting rules (§6.1 freeze,
     §6.2 behavior evidence, and for refactor PRs the Phase-5 mixin mechanics);
   - the **exact diff** of the PR: `git diff <pr-base>..<pr-head>`, where
     `<pr-base>` is this PR's branch point on `rewrite`;
   - read access to the whole repo at `<pr-head>`, to `/data/pdsdata` holdings,
     and to the consumer repos, so it can **verify claims against the code, not
     against the diff's own comments**;
   - the **progressive-compliance schedule** (below), so it does not flag
     `.cursor/rules` violations that this and earlier PRs were never meant to
     fix yet.
3. The reviewer's mandate is **adversarial**: assume the phase goal was NOT met
   and try to prove it. It must check, at minimum: does the diff actually
   deliver the PR's stated goal; are all phase gates genuinely satisfied (not
   just claimed) — freeze diff within the two forgiveness categories, ruff
   ratchet not widened, behavior preserved. **On the full-data gate the
   reviewer does NOT re-run the multi-hour suite** (that would wreck the
   schedule); instead it verifies the *evidence*: the recorded run in
   `critiques/` exists, was generated **at or after the PR's last change under
   `src/pdsfile/`** (a record predating the last `src/` change is stale; a
   later change touching only tests/docs/records does not stale it — see step
   5), and its
   diff-vs-baseline computation is present and shows the identical set — and it
   spot-checks that computation for soundness. A missing, stale, or hand-waved
   record is a Major finding. For **refactor** PRs the reviewer also checks: is
   moved code byte-for-byte equivalent and
   are all references updated; for **test** PRs, do new tests assert real
   values or are they hollow/tautological; is there dead code, a missed file,
   an ambiguity, or scope creep. It verifies line/symbol claims against the
   actual source. **Output:** findings split into **Major** (goal not met;
   correctness / behavior / freeze / gate violation; missing deliverable) and
   **Minor** (clarity, incompleteness, style, weak test) — each with
   `file:line` evidence and a concrete fix — plus an explicit verdict
   (`goal met` / `goal not met`). A third, **non-blocking** bucket —
   **Deferred** — may hold genuine issues that are out of scope for this PR
   (e.g. a later-phase cursor-rule violation the reviewer wants on record);
   Deferred items do **not** block convergence and are appended to
   `critiques/deferred-observations.md` for the phase that owns them, so
   nothing is lost. The reviewer makes **no edits**.
4. The executor resolves **every** Major and Minor finding, one of two ways:
   (a) fix it; or (b) if the finding is provably wrong or is scope-creep beyond
   the PR's stated goal + ground rules, write a short **rebuttal** instead of
   fixing. Both fixes and rebuttals are recorded (below).
5. Spawn a **new** fresh reviewer (again no context, and no knowledge of prior
   rounds) on the updated diff. **Repeat from step 1** — i.e. re-confirm the
   §2 gates on the changed code first. **Full-data-record regeneration rule:**
   if the round's fixes touched any source under `src/pdsfile/` (any PR whose
   gates or procedure include a full-data run — Phase 2/5/6 **and PR-08**, whose
   F821/NameError detection relies on that run), regenerate the full-data run
   and its baseline-diff record before the next reviewer; if the round changed
   only `tests/`, docs, or records (no `src/pdsfile/` edit), the prior
   full-data record carries forward (note that in the PR). This exactly matches
   step 3's "record ≥ last `src/pdsfile/` change" check, so a tests-only round
   never makes the carried-forward record read as stale, and no multi-hour
   re-run happens on a trivial round.

**Termination — the loop ends when a fresh reviewer returns zero Major
findings and no *new, un-rebutted* Minor findings** (verdict `goal met`;
previously-recorded rebuttals do not re-block). Then open the PR.

**Anti-thrash / anti-oscillation rules (so "clean of minor issues" cannot loop
forever):**
- If the executor rebutted a **Major** finding and the **next independent fresh
  reviewer raises the same Major finding**, it is a genuine disagreement —
  **hard-stop to the owner** (§6.4) with both the finding and the rebuttal; do
  not loop it again. A re-raised **Minor** that was reasonably rebutted does
  **not** escalate (two same-model reviewers correlate, so re-raises are
  expected noise): the executor records the rebuttal once and the loop may
  proceed; it converges when a round returns no *new* Minor and no Major.
- **The 4th round (if reached) is a *scoped* re-review:** "confirm the prior
  round's findings are resolved; raise only **new Major** findings." This
  prevents an endless tail of fresh subjective Minors on a 1,000-line diff from
  blocking a correct PR.
- A reviewer may only judge against the PR's stated goal + the ground rules; a
  finding that demands work beyond this PR's scope is invalid — the executor
  rebuts it and, if re-raised, escalates rather than expanding scope.
- **Hard cap: 4 rounds.** Mechanical PRs converge in 1–2. If a fourth round
  still finds issues, stop and bring all round records to the owner — this
  signals the PR is mis-scoped or the goal is ambiguous, an owner decision.
- Purely subjective nits (naming taste with no rule behind it) are Minor only
  if tied to a `.cursor/rules` mandate; otherwise the reviewer must not raise
  them, and the executor rebuts if it does.
- **Progressive `.cursor/rules` compliance.** The repo starts non-compliant
  and is brought into compliance over the phases. A cursor-rule violation is a
  valid finding **only if bringing the repo into compliance with that rule was
  a stated deliverable of this PR or an already-merged earlier PR.** A
  violation of a rule whose compliance is scheduled for a *later* PR — or is
  permanently waived — is **out of scope**: the reviewer must not raise it, and
  the executor rebuts it if raised (and escalates per the rebuttal rule only
  if a fresh reviewer re-raises it). The authorities on "what is in force
  when" are: each PR's stated goals, the §2 gate table, and the permanent
  waivers/deviations in `.cursor/rules/pdsfile_overrides.mdc` (PR-04). The
  compliance schedule (a rule is out of scope until the PR shown, unless the
  current PR's goal explicitly touches it):

  | `.cursor/rule` area | In force from |
  |---|---|
  | `dependency_management.mdc` (pyproject single source of config/deps) | PR-03 |
  | `environment.mdc` (`run-all-checks.sh` = CI source of truth) | PR-04, tightened at PR-14 |
  | `python.mdc` style/naming/line-length (`ruff check`) | ratcheted from PR-03; from PR-23 (core) / PR-24 (rest) reduced to the **enumerated freeze-/table-/typing-locked per-file-ignore sets plus the frozen `re_validate.py` set** (overrides deviation (4); not literally zero — frozen public names, aligned tables, frozen `re_validate.py`, and `RUF012`-vs-`ClassVar` make some ignores permanent) |
  | `python.mdc` `ruff format` | PR-23 (core) / PR-24 (rest) — only to the extent the owner approves at those PRs' churn checkpoints; may be reduced or waived entirely |
  | `python.mdc` type annotations / mypy | **permanently waived** (ground rule 5); `.pyi` stubs at PR-35 only |
  | `python.mdc` "modules < 1000 lines" | **permanently waived** for `pdsfile.py` and rule modules (`pdsfile_overrides.mdc`) |
  | `python_testing.mdc` (pytest/xdist/markers/coverage/hermetic) | Phases 3–4 (PR-08–PR-14) |
  | `doc_python.mdc` docstrings; `doc_readme`/`doc_dev_guide`/`doc_user_guide`/`doc_how_to` | Phase 7 (PR-29–PR-34) |
  | `logging.mdc` (PdsLogger) | already followed; enforced only where a PR edits logging |
  | `git_workflow.mdc`, `pull_request.mdc` | every PR from the start |
  | `filecache.mdc` (FCPath) | **permanently excluded** (ground rule 6; never copied into the repo) |

  So e.g. "this module has no type annotations," "this function lacks a
  docstring" (before Phase 7), "`pdsfile.py` exceeds 1000 lines," or "paths
  should use FCPath" are all **invalid** findings and are rebutted, not fixed.

**Records:** every round (the reviewer's findings + the executor's fix/rebuttal
disposition) is saved to `critiques/pr-<NN>/round-<k>.md`; the final clean
review is linked from the PR description. This loop **precedes and does not
replace** the human review at the PR boundary.

### 6.7 Execution topology (phase and reviewer subagents)

To keep any single context small, execution is a strict four-level subagent
nesting (coordinator → phase-coordinator → PR-executor → per-round reviewer),
and **every PR runs in its own dedicated PR-executor subagent — in all phases,
without exception**:
- A thin **top-level coordinator** owns only this plan, the branch state, and
  the phase-boundary gates. It executes no code itself.
- For each phase it spawns **one phase-coordinator subagent**, passing it the
  plan, the phase to run, and the current branch state. The phase coordinator
  **does not implement PRs itself** — it spawns **one child PR-executor
  subagent per PR** (in the phase's PR order), passing each only that PR's
  section of the plan + branch state, and collects each PR-executor's short
  summary + `critiques/pr-<NN>/` links. This holds even for one- or two-PR
  phases; there is no "batch several PRs in one executor" path.
- Each **PR-executor subagent** carries exactly one PR end to end
  (implementation + the §6.6 loop) and returns only a concise summary — so no
  single context ever holds more than one PR's working state (implementation
  plus up to four review rounds).
- Each §6.6 **adversarial reviewer is its own short-lived, no-context
  subagent** (a new one per round), hanging off the PR-executor, so reviewers
  are always genuinely fresh.
- So the live nesting is: coordinator → phase-coordinator → PR-executor →
  per-round reviewer (four levels of subagent, one PR per PR-executor).
- At each phase boundary the top-level coordinator independently confirms the
  §2 phase-boundary gates (API-freeze, full-data set identical to baseline,
  and for Phase 5/6 the recorded validation file) before launching the next
  phase-coordinator. A failed boundary gate is a hard stop, not an auto-retry.
- **PRs within a phase are still strictly ordered** (a later PR-executor starts
  only after the prior PR's is merged to `rewrite`, unless the plan marks them
  independent); per-PR subagents bound *context*, not concurrency.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Mini-tree goldens drift from full-tree goldens (dual maintenance) | Override model (PR-11): one authoritative base `full/` golden per test; `mini/` holds only genuinely-differing overrides, written by `--update` only when they differ from base — so identical values are never duplicated. Goldens are regenerated, never hand-edited; regeneration how-to in dev guide; nightly full run catches drift |
| Stubbed data breaks a test that secretly reads content | PR-11 audits every test individually; anything content-dependent is either given real (small) data or marked `full_holdings` |
| Windows/macOS hermetic CI surfaces latent path/case bugs | Treat as found bugs: fix with tests; the mini tree is checked for case-collision safety before commit |
| xdist nondeterminism in cache-behavior tests | Cached tests grouped per worker (`--dist loadfile`); `--update` forces serial |
| Mixin split preserves file-level modularity but not true SRP | Accepted: that is phase "a" of #77 by decision; phase "b" is future work |
| Fixture generator is itself substantial new code | It gets its own unit tests (manifest parsing, stub policies) and its output is validated by the entire hermetic suite |
| `run-tests-and-opus` / consumers break subtly despite manifest | Manifest covers names/signatures, not semantics — hence the full-data gates and the Phase 8 consumer smoke checks |
| RTD/docs red mid-rewrite | Acceptable on `rewrite`; gates activate when their phase lands |
| Adversarial review loop thrashes or never converges | 4-round hard cap + rebuttal-then-escalate on repeated findings + scope-locked to the PR's goal (§6.6); non-convergence escalates to the owner as a mis-scope signal |
| Per-PR review loop adds latency/token cost | Bounded: mechanical PRs converge in 1–2 rounds; reviewers are short-lived and scoped to one diff; the cost buys the fresh-eyes defect class that passes 2–3 of this plan's own review proved most valuable |

## 8. Settled decisions (owner-confirmed 2026-07-18)

All the discussion items are now decided. Each is folded into the relevant
PR; they are listed here as the authoritative record.

1. **Test-data repo:** created **public** as **`rms-pdsfile-test-data`** (so
   GitHub-hosted CI clones it without secrets). Wired into PR-10 (creation)
   and PR-14 (CI checkout).
2. **Fixture index tables may be row-truncated** above 2,000 rows (referenced
   rows + 100-row context, `ROWS`/`FILE_RECORDS` rewritten, `pdstable`
   round-trip validated). Affects only the *mini* indexshelf goldens. PR-10
   copy policy #3.
3. **`PdsFile` split depth:** take the **optional lazy-property mixin
   extraction** — PR-22 moves the ~1,550-line lazy-property block into
   `_properties.py` (manifest-neutral), landing core at **~1,750 lines**,
   closer to issue #77's intent. No longer optional; it is the PR-22 target.
4. **No new console scripts** for `crlf`/`shelf_consistency_check`/
   `show_opus_products` — `python -m` invocation only. PR-28.
5. **`tabulate`** ships in the **`dev` extra** (only `show_opus_products`
   uses it, and it stays `python -m`, not a shipped console script). PR-03.
6. **Human-review cadence:** full human review on every refactor/test/docs
   PR; **lighter-touch** (adversarial loop + phase-boundary gates, no
   mandatory line-by-line human read) permitted on the **pure `git mv` PRs of
   Phase 2** (PR-05–07). §6.4 / §6.7.
7. **Nightly-failure alerting:** GitHub's built-in notifications for now;
   revisit if noisy. PR-14.
8. **Branch protection:** protect `rewrite` with the hermetic checks required
   once Phase 4 (PR-14) lands (owner/admin action, not an executor task).

## 9. Issue mapping

| Issue | Where addressed |
|---|---|
| #77 PdsFile split | Phase 5 (phase "a"); "b" explicitly deferred |
| #82 maintenance-tool tests | PR-10/PR-13 |
| #79 architecture analysis | Historical record at `critiques/2025-08-15-code-quality-analysis.md` (committed in PR-01); deep redesign deferred |
| #45 maintenance-tool docs | PR-32 |
| #43 module docs/docstrings | PR-29/30/31/33 |
| #37 inconsistent rules tests | PR-08 |
| #40 golden-file test framework | **Closed** (rules tests). PR-11 extends the framework to the case-(b) blackbox/whitebox tests and files **#92** to finish the rest. |
| #92 finish #40 for all inline `@parametrize` values | Filed by PR-11; converting the remaining (non-tree-dependent) blackbox/whitebox inline values is future work, fully specified in the issue. |
| #47 log-path functions don't belong in PdsFile | PR-18 handles only the **refactoring** half. #47's *primary* `is_index`/`log_path_for_index` bug was **already fixed via #48** (per the issue thread), so it is not re-addressed here and is **not** in PR-15's bug list. PR-18 moves the log-path methods to `_derived_paths.py` as a mixin; tools keep calling them as `PdsFile` methods, names stay on PdsFile per the freeze — full removal from the class surface deferred to phase "b". #47 stays open. |
| #71 sync scripts | Document-only (PR-32), by decision |
| #85 re-validate email | Explicitly out of scope ("leave re-validate alone for now") |

**Deliberately out of scope (open issues this rewrite does not address — listed
so their omission is a decision, not an oversight):** #88 (LIDs/VIDs/file
paths), #76 (separate archive from shelf files), #31 (PDS4 versions), #14
(pickle files for documents), #8 (CORSS VERSIONS rules), #6 (pickle ordering),
#4 (random associations), #3 (NH multiple previews), #2
(`primary_data_abspath` normalization). These are behavior/feature issues
untouched by a compatibility-preserving modernization; they remain open after
merge. Note #45 is closed with a documented **partial-scope** caveat: PR-33 ch.4
documents extending pdsfile *rules files*, but the issue's comment also asks
for a guide to extending the *maintenance tools* (e.g. `pdslinkshelf` REPAIRS
regexes) — that sub-topic is added to PR-33 (below) so #45 closes fully.
