# rms-pdsfile Modernization Plan (v2)

**Date:** 2026-07-25
**Status:** ACTIVE — supersedes `plans/archive/2026-07-17-modernization-plan.md`
(v1). PR-01 through PR-09 of v1 are merged and are recorded here as completed;
this document fully specifies the remaining work.
**Executor:** an opus-class AI — a thin coordinator → one phase-coordinator per
phase → **one PR-executor subagent per PR** (all phases), each PR gated by a
fresh no-context adversarial review loop (§6.6–6.7), one PR at a time, merged to
a single integration branch, with human review at PR boundaries.
**Rewrite branch:** `rewrite` (all PRs target it; it merges to `main` once complete)

### What changed from v1 (owner decision, 2026-07-25)

**The mini-holdings concept is removed from this effort entirely.** No
manufactured fixture tree, no `rms-pdsfile-test-data` content, no
hermetic-on-GitHub-hosted-runners data suite, no mini-flavor goldens. Testing
continues the way it works today: against **real holdings** — the complete set
or a limited copy — on self-hosted runners and on machines that have them,
resolved via env vars, with graceful skip everywhere else (PR-09). All
mini-holdings design work is preserved for future discussion in
`plans/2026-07-25-mini-holdings-plan.md`; nothing in this plan depends on it.

**The already-merged mini-ready plumbing stays in place, dormant** (owner,
2026-07-25): the full/mini/skip resolver in `tests/support/holdings.py`, the
`PDSFILE_TEST_HOLDINGS`/`PDSFILE_TEST_DATA_DIR` env vars, the `full_holdings`
marker, and the `tests/golden/full/` directory layout are **not** removed —
mini-holdings will happen in the future, and a revival plugs directly into
them. With no `PDSFILE_TEST_DATA_DIR` set anywhere, the mini flavor is simply
never selected; no PR in this plan touches or depends on it.

Everything else — the decomposition (#77a), maintenance-tool tests (#82),
documentation (#43/#45), rules-test standardization (#37, done), ruff/style,
API freeze — proceeds unchanged.

**PR numbering:** completed PRs keep their v1 numbers (PR-01–PR-09). v1's
PR-10 (fixture generator), PR-11 (mini-override goldens + hermetic audit), and
PR-12 (pytest-xdist) are **withdrawn and their numbers retired**: PR-10's and
PR-11's scope moved to the mini-holdings plan; PR-12 is dropped outright (the
suite runs in ~30 s against the limited holdings copy and preload dominates
complete-set runs, so xdist buys nothing here and adds shared-state risk —
revisit only if the hermetic plan is ever revived). Do not reuse PR-10–PR-12.
Remaining work starts at **PR-13**; PR-13 onward keep their v1 numbers and
content (PR-13 and PR-14 re-specified for real holdings; PR-15–PR-37 carried
with mini references scrubbed).

### How to read this document (start here)

You are the executor. This document is the **complete, self-contained**
specification for the remaining work — you need no other context and none of
the `critiques/` records to carry it out. The archived v1 plan documents the
already-merged PRs in detail; you do not need it either (merged code + this
plan's §3 current-state summary suffice). Read this document in full once,
then:
1. Check the **standing prerequisites** (§3.4).
2. Read the **locked ground rules** (§2) — non-negotiable; they override the
   repo's cursor rules where they conflict (see
   `.cursor/rules/pdsfile_overrides.mdc`).
3. Read the **execution protocol** (§6.4), the **adversarial review loop**
   (§6.6), and the **subagent topology** (§6.7) — these govern *how* every PR
   is done.
4. Execute the remaining PRs in order (§5, PR-13 → PR-37), one PR per
   PR-executor subagent, each gated by the §6.6 loop, all merging into
   `rewrite`.
When the plan and a repo cursor rule disagree, the plan wins. When you are
unsure or hit a **hard stop** (§6.4), stop and ask the owner — do not guess.
Line numbers are indicative; locate code by symbol name.

**Repositories and paths referenced by this plan** (this repo is at
`/seti/all_repos/rms-pdsfile`; siblings are under `/seti/all_repos/`):
the modernization template `rms-devenv/repo_template` and its realized example
`rms-cloud-tasks`; the API consumers `rms-opus` and `rms-viewmaster`. Complete
real holdings are at `/data/pdsdata/{holdings,pds4-holdings}`. GitHub remote is
`SETI/rms-pdsfile`; PRs are opened with `gh`.

## 1. Goals

Modernize rms-pdsfile to match the conventions in `rms-devenv/repo_template`
(as realized in `rms-cloud-tasks`, the best CLI-bearing precedent), while:

- **G1** Splitting the 6,304-line `PdsFile` class file into focused modules
  (issue #77, phase "a" — mechanical decomposition; deep redesign deferred).
- **G2** Creating a test suite for the maintenance tools (issue #82).
- **G3** Keeping the test suite holdings-aware and runnable anywhere without
  failure: data-dependent tests run against real holdings (complete or limited
  copies) resolved via env vars; machines without holdings collect cleanly and
  skip (delivered by PR-09); the holdings-free subset (API freeze, tool unit
  tests, import/collection smoke) also runs on stock GitHub-hosted runners
  (PR-14). *(v1's hermetic-data-suite goal is withdrawn — see the scope note
  above.)*
- **G4** Keeping the full-data tests as the primary suite: real holdings are
  tested on every PR (self-hosted) and nightly, forever.
- **G5** Writing full developer documentation for the module and CLI tools, and
  full user documentation for the CLI tools (issues #43, #45).
- **G6** Making the code clean and ruff-clean, with Google-style docstrings.
- **G7** Standardizing the per-dataset rules tests (issue #37 — **done**,
  PR-08).

## 2. Ground rules (locked decisions)

Decided with the repo owner (2026-07-17, amended 2026-07-25) and **not** open
for re-interpretation by the executor:

1. **The public API may not change at all — 100% compatibility.** Everything
   reachable today via `import pdsfile` (including `pdsfile.pdsfile`,
   `pdsfile.pdscache`, `pdsfile.pdsviewable`, `Pds3File`/`Pds4File` and all
   their methods/properties/class attributes, and the volset/volume alias
   properties) must keep working with identical names, signatures, and
   behavior. **Exception — test infrastructure is not external API** (already
   exercised: PR-08 moved the test helpers out of the package under this
   exception). Consumer that must not break: **rms-opus** (class-based API
   only). **rms-viewmaster** mostly uses the class-based API but has two
   pre-existing flat-name usages (`pdsfile.cache_lifetime`,
   module-level `DEFAULT_CACHING`) that already fail against *current* pdsfile
   — not caused by, and not fixable by, this rewrite; the owner will patch
   rms-viewmaster separately, so do **not** add package-level
   `cache_lifetime`/`DEFAULT_CACHING`. PR-37's consumer smoke checks compare
   against a recorded baseline, not against "passes" (§3.4). **rms-webserver
   is out of scope** (owner-confirmed retired; it uses a pre-split flat-module
   API that no longer exists). Enforced mechanically (§6.1).
2. **Issue #77 scope:** mechanical decomposition only ("a now, b later").
   No dependency-injected cache manager, no structured path parser rewrite,
   no extraction of rule data to YAML/config files.
3. **Test data: real holdings only.** No manufactured fixture tree and no
   fixture-data repo in this effort (owner, 2026-07-25 — supersedes v1's
   ground rule 3). Data-dependent tests resolve holdings from
   `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR`; machines without holdings
   collect-and-skip (PR-09). Small test-owned scratch data (a test writing a
   few files into `tmp_path`, or copying a bounded, explicitly-declared subset
   of real holdings into `tmp_path` as PR-13 does) is normal test practice,
   not a fixture tree, and is fine. The mini-holdings concept lives in
   `plans/2026-07-25-mini-holdings-plan.md` for future discussion; the merged
   mini-ready plumbing (flavor resolver, env vars, `full_holdings` marker,
   `tests/golden/full/` layout) **stays in place, dormant** — do not remove
   it, extend it, or build anything on the mini flavor in this effort.
4. **Keep the existing full-data tests.** Real holdings are tested on every PR
   (self-hosted CI) and nightly, forever.
5. **Skip type annotations for now.** No inline typing effort, no mypy gate.
   Provide a type stub for the public API instead.
6. **No FCPath.** Do not adopt rms-filecache, and do not copy `filecache.mdc`
   into this repo's cursor rules.
7. **CLI names unchanged** (all 11 console scripts keep their names).
   **`re_validate.py` is no longer frozen** (owner, 2026-08-05). It was left
   alone through PR-06 to PR-24 — moved and renamed with its package, then given
   a whitespace-only exemption on 2026-08-04 — and the freeze is now lifted
   outright: its internals, including the email and batch logic, may be changed
   like any other module, under the same gates. PR-25 changes it only for the
   log time-tag race; PR-25a gives it a `main()`, a test module and ten bug
   fixes, and shrinks its `ruff check` per-file-ignore entry to the two codes
   that are permanent everywhere else in the tree.
   **Sync shell scripts are document-only** (no port, no rewrite).
8. **Single package:** the maintenance tools live in the `pdsfile` package
   (`src/pdsfile/holdings_maintenance/` — done, PR-06); no separate top-level
   package.
9. **Leave all functionality in place** — including `MemcachedCache`/pylibmc
   support (Viewmaster passes `port=` to `preload`). Nothing is deleted for
   being "probably dead." Latent *bugs* in existing code may be fixed (PR-15,
   plus the tool-bug fixes in PR-26/PR-28), each with a test, but no feature
   removal.
10. **Record keeping:** `plans/` holds plans (this file); `critiques/` holds
    critique reports, validation records, and per-PR review rounds. Every
    phase leaves a record. Superseded plans move to `plans/archive/`.

### PR discipline

- Every PR targets `rewrite`. One logical change per PR. **File moves/renames
  are always their own PRs** (pure `git mv`, plus the minimal edits required to
  keep the package importable **and every active gate green** — CI script
  paths, conftest import paths, packaging config, and `ruff`
  `per-file-ignores` path globs (renaming a glob to the moved path is a
  rename, not a ratchet *widen*, and is allowed) — each itemized explicitly in
  the PR description.
- **Commit granularity: never mix renames and fixes in the same commit.**
  Rename commits contain only pure `git mv` operations (one or several renames
  per commit is fine) so `git log --follow` tracks history cleanly. The
  minimal keep-green edits (CI paths, imports, packaging, ignore globs) go in
  separate content-edit commits — which may each bundle several fixes — never
  in a commit that also renames files.
- Conventional Commit titles (per `git_workflow.mdc`).
- Every PR description records: what was validated (which suites, which
  holdings root), and a link to the `critiques/` record if the phase produced
  one.
- **PRs are behavior-preserving. A PR that changes observable behavior is
  wrong** — the only exceptions are the changes this plan explicitly
  enumerates (PR-15's bug-fix list, PR-26's pds3 bug fixes and `os.system` →
  `subprocess.run`, PR-28's `errors` fix), and each of those must first add a
  regression test pinning the intended behavior and call the change out in
  the PR description.

### Validation gates (apply to every PR from the phase where each gate exists)

| Gate | Status | What it checks |
|---|---|---|
| API-freeze manifest test | **Active** (PR-02) | Public surface identical to the pre-rewrite manifest (modulo the two pre-approved forgiveness categories, §6.1) |
| Full-data suite (self-hosted CI on every PR; also run locally) | **Active** (Phase 0) | No behavior change against real holdings; per-test pass/fail set identical to the recorded baseline (§6.2); additionally run locally after every Phase 5/6 PR and at each phase boundary |
| `ruff check` (ratcheted) | **Active** (PR-03) | Style; per-file-ignores may only shrink |
| `ruff check --preview --select E111,E112,E113` (indentation) | **Active** (PR-24, owner 2026-08-04) | Every logical line of **code** on the 4-space grid. A separate invocation because the `E1` rules are preview-gated and enabling preview wholesale in `pyproject.toml` also changes the stable rules' behaviour — measured at 5,687 findings against a tree the configured gate reports clean. The comment-line counterparts (`E114`/`E115`/`E116`, and `E117` which fires on both) are left out: comment placement is the author's here, and this codebase's conventions — a trailing comment continued under its own column, an annotation after the statement it describes, commented-out code parked at column 0 — all read worse pulled to the code grid. `re_validate.py` is included with no exemption: the owner lifted ground rule 7 for **whitespace only** on 2026-08-04 and lifted it **entirely** on 2026-08-05, so nothing about that file is exempt from this gate or any other (`pdsfile_overrides.mdc` deviation (6)) |
| Clean-install import check | **Active** (PR-08) | `pip install .` with no extras; `import pdsfile` + every manifest module imports (runtime-dep leak guard) |
| `ruff format --check` | **Never enabled** — the churn checkpoint ran on 2026-08-03 and the owner dropped the reformat entirely (`plans/2026-08-03-addendum-pr23-24-owner-decisions.md`) | — |
| Hosted lint/no-holdings CI job | **Active** (PR-14) | ruff + pyroma + API-freeze + clean-install + the holdings-free test subset on stock GitHub runners (it runs `run-all-checks.sh`, so it is whatever that enables) |
| sphinx -W -n build | PR-31 | Docs build clean |
| Adversarial pre-PR review loop | **Active** (every PR) | A fresh, no-context reviewer cannot prove the PR misses its stated goal — zero Major and no new un-rebutted Minor findings (§6.6) |

`scripts/run-all-checks.sh` is the single source of truth for the enabled set
(`ENABLE_*` flags; currently on: ruff-check, pytest, pyroma, api-freeze,
clean-install). Each PR that introduces a gate flips its flag and keeps CI in
exact correspondence (`environment.mdc`). `ENABLE_MYPY`, `ENABLE_BANDIT`,
`ENABLE_VULTURE` stay false permanently (ground rules / overrides).

## 3. Current state (after PR-09, 2026-07-25)

### 3.1 Completed PRs (v1 numbering; all merged into `rewrite`)

| PR | Delivered |
|---|---|
| PR-01 | `plans/` + `critiques/` record directories; `rewrite` branch created |
| PR-02 | Public-API freeze manifest (`tests/api/api_manifest.json`, 43 modules / 39 classes), dumper `scripts/dump_public_api.py`, checker `tests/api/test_api_freeze.py`, allowlist with the two category predicates (§6.1) |
| PR-03 | All tool config consolidated into `pyproject.toml`; ruff ratchet seeded (`scripts/gen_ruff_ratchet.py`); deps/extras cleaned up |
| PR-04 | repo_template support files; `.cursor/rules/` incl. `pdsfile_overrides.mdc` (10 deviations); `scripts/run-all-checks.sh` with staged `ENABLE_*` flags; CI triggers on PRs to `rewrite`; `tests/api/` added to the self-hosted pytest invocation |
| PR-05 | `src/` layout (`git mv pdsfile src/pdsfile`) |
| PR-06 | Maintenance tools + utility moved into the package (`src/pdsfile/holdings_maintenance/`, `src/pdsfile/tools/`); hyphenated modules renamed (`re_validate.py`, `shelf_consistency_check.py`); console-script targets updated |
| PR-07 | Tests moved to top-level `tests/` tree; goldens to `tests/golden/full/pds{3,4}/` |
| PR-08 (#100) | Rule-module tests extracted to `tests/rules/pds{3,4}/`, standardized (#37 closed); `pytest` runtime coupling dropped; clean-install gate added; Windows removed from the CI matrix (→ open issue #102) |
| — (#101) | LF normalization + `.gitattributes` (source files LF; PDS3 data keeps CRLF) |
| PR-09 (#103) | Holdings-aware conftest: `tests/support/holdings.py` resolver (full / mini / skip via `PDSFILE_TEST_HOLDINGS`), graceful collect-and-skip with no holdings, `full_holdings` marker registered, import-time `KeyError` removed from helpers |

### 3.2 Repo facts the remaining PRs rely on

- Layout: `src/pdsfile/` (package incl. `holdings_maintenance/`, `tools/`),
  `tests/` (api, pds3file, pds4file, rules, support, golden/full,
  conftest.py), `scripts/` (run-all-checks.sh, dump_public_api.py,
  gen_ruff_ratchet.py, clean_install_check.sh, check_runtime_imports.py,
  automated_tests/), `plans/`, `critiques/`.
- `src/pdsfile/pdsfile.py` is still the 6,304-line single-class module; the
  Phase 5 seams and line windows in §5 were verified 2026-07-17 (locate by
  symbol, not line).
- CI (`run-tests.yml`): self-hosted Linux matrix, Python 3.10–3.13, triggers
  on PRs to `rewrite`, push to `main`, nightly cron, dispatch/call. Windows
  was removed from the matrix in PR-08 (issue #102 tracks the pyproject
  classifier decision); macOS entries are commented out.
  `run-tests-and-opus.yml` calls `run-tests.yml` for its pdsfile leg.
  `scripts/automated_tests/pdsfile_main_test.sh` is the suite driver (exports
  `PDSFILE_TEST_HOLDINGS=full` since PR-09 — kept).
- Test-suite baseline (the §6.2 comparison target): against the limited
  holdings copy the goldens are tuned to — `--mode ns`: **679 passed /
  34 skipped**; `--mode s` (pds3 only): **555 passed / 3 skipped**
  (recorded in `critiques/pr-09/`; the 34 ns skips are PDS4 bundles absent
  from that copy). The authoritative baseline is always the most recent
  recorded validation run in `critiques/`.
- Holdings resolution (PR-09): `PDSFILE_TEST_HOLDINGS=full` → roots from
  `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR`; `mini` → `PDSFILE_TEST_DATA_DIR`
  trees; unset → mini if available else skip-all. **This machinery stays as
  merged** (owner, 2026-07-25): the mini flavor is dormant — no
  `PDSFILE_TEST_DATA_DIR` is set anywhere, so it is never selected — and it
  is reserved for the deferred mini-holdings plan.
- Open follow-ups, tracked, not blocking: issue #102 (Windows classifier —
  owner decision, surfaced in PR-14); `critiques/coderabbit-findings.md`
  (backlog from PR-06 review); `critiques/deferred-observations.md`
  (per-phase deferred items — the PR-09 entry about removing the
  `PDSFILE_TEST_HOLDINGS` selector **stays deferred**: that machinery is now
  intentionally retained until the mini-holdings plan is revisited).

### 3.3 Not in scope (moved out on 2026-07-25)

The fixture-tree generator, the `rms-pdsfile-test-data` content, mini-flavor
goldens/overrides, the hermetic GitHub-hosted data matrix, test-data SHA
pinning, and pytest-xdist — all withdrawn from this effort. Design record and
future options: `plans/2026-07-25-mini-holdings-plan.md` (which also indexes
the measured size audit in `critiques/2026-07-21-unified-mini-holdings-analysis.md`
and the archived v1 specs). The `SETI/rms-pdsfile-test-data` repo exists,
public and empty; it stays empty for now. The merged mini-ready plumbing
(§3.2) is retained, dormant — withdrawn scope means "don't build on it," not
"remove it."

### 3.4 Standing prerequisites (operator + executor)

1. **Holdings env vars + confidentiality.** Export `PDS3_HOLDINGS_DIR` /
   `PDS4_HOLDINGS_DIR` for data runs. Two real roots exist and the tests must
   pass against **either**: `/data/pdsdata/{holdings,pds4-holdings}` is the
   complete set; a **limited testing copy** (the set the goldens are tuned to)
   serves machines without full access. **No absolute holdings path may be
   hardcoded in committed code, tests, docs, or CI** — everything resolves via
   the env vars; docs use the variable names as placeholders. The limited
   copy's location is machine-local and confidential (appears in no checked-in
   file).
2. **Dev environment.** The repo venv has the runtime deps, editable install,
   pytest/coverage/ruff; Phase 7 additionally needs `sphinx` + extensions
   (part of the `docs` extra).
3. **Consumer-smoke baseline.** PR-37 compares the rms-opus import smoke and
   rms-viewmaster startup against a recorded baseline. **Captured** at
   `critiques/baselines/consumer-smoke-baseline.md` (2026-07-26, against
   `rewrite` at the end of Phase 3, while every merged PR is still
   behavior-preserving). It records the rms-opus import paths as 4/4 resolving
   and the rms-viewmaster startup as 5 stages ok / 3 pre-existing failures —
   the ground-rule-1 flat names `cache_lifetime` (raises) and `DEFAULT_CACHING`
   (silently assigns onto pdsfile and is never read). **PR-37's gate is "same
   outcome as baseline", so fewer failures is as much a flag as more.**
4. **Harness.** The four-level subagent nesting (§6.7) with `git`/`gh`/
   `pytest`/`ruff` available to subagents; fallback collapse rules in §6.7.

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
│   ├── _properties.py               # lazy-property mixin (§8.3)
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
│   ├── conftest.py                  # holdings-aware (full/mini/skip; mini dormant)
│   ├── api/test_api_freeze.py       # + api_manifest.json (+ test_mixin_collisions.py, PR-17)
│   ├── pds3file/  pds4file/         # blackbox/whitebox/cached tests
│   ├── support/                     # holdings resolver, golden helpers
│   ├── rules/pds3/  rules/pds4/     # standardized per-dataset tests (PR-08)
│   ├── holdings_maintenance/        # tool tests (issue #82, PR-13)
│   └── golden/full/pds3/  .../pds4/ # goldens ("full/" level reserved for a
│                                    #   future mini/ override set — kept)
├── docs/                            # Sphinx: index, user_guide/, dev_guide/, api/
├── plans/  plans/archive/  critiques/   # records
├── scripts/
│   ├── run-all-checks.sh  read-docs.sh  dump_public_api.py  ...
│   └── automated_tests/             # self-hosted suite driver (PR-gate + nightly)
├── .cursor/{rules,skills}/          # template rules minus filecache.mdc
├── .github/workflows/               # run-tests (self-hosted full-data + hosted
│                                    #   lint/no-holdings job), run-tests-and-opus,
│                                    #   publish_to_*
├── pyproject.toml                   # ALL tool config
├── requirements.txt                 # "-e ."
└── README.md, CONTRIBUTING.md, codecov.yml, .readthedocs.yaml, ...
```

(No separate test-data repo. `tests/golden/full/` keeps its name so the
deferred mini-override model can add `golden/mini/` later without churn.)

## 5. Remaining phases and PRs

Phases are strictly ordered; PRs within a phase are ordered unless marked
independent. Sizes: S (< 300 changed lines of hand-written diff), M (< 1500),
L (larger, usually mechanical). PR-10, PR-11, and PR-12 are retired numbers
(see the scope note); do not reuse them. **The merged holdings-flavor
machinery (PR-09) is intentionally left exactly as it is** — no PR here
touches it.

### Phase 3 (completion) — Test restructure

**PR-13 (L)** `test: maintenance-tool test suite` (closes issue #82)
Tool tests run against **bounded, explicitly-declared subsets of real
holdings copied into `tmp_path`** — deterministic, disposable, and identical
across machines because the limited copy is a copy of the complete set.
- **Source-subset model (the load-bearing design):** each test module declares
  `SOURCE_PATHS` — an explicit list of holdings-relative paths (one designated
  small volume's data files, labels, and metadata; keep each module's subset
  under ~50 files / ~50 MB; the executor picks the volume — smallest suitable
  with both `volumes/` and `metadata/` present, verified against the goldens'
  reference root). A module-scoped fixture resolves the holdings root via
  `tests/support/holdings.py`, verifies every declared path exists — **any
  missing path → skip the module** (mark these modules with the existing
  `full_holdings` marker) — then copies the subset into `tmp_path`
  preserving the holdings layout and **pins mtimes from a table in the test
  module** (`os.utime`) so shelf/checksum outputs are deterministic.
- For each pds3/pds4 tool pair — exercise the full task cycle over the copied
  tree: `--init` from scratch → compare to committed goldens → `--validate`
  (clean) → corrupt → `--validate` (must fail with the right log content) →
  `--repair` → `--validate` (clean) → `--update` after adding a file.
  Corruptions are **fixed scenarios declared in a table at the top of each
  test module** (e.g. "overwrite byte 0 of `<specific file>` with 0xFF",
  "delete `<specific entry>` from the md5 file", "touch `<file>` to
  mtime+100"), never randomized. Compare `.py` sidecars (sorted, text) rather
  than pickles where possible; compare archives by **member tuples, never
  bytes** (`.tar.gz` bytes and `os.walk` order are not portable). Committed
  goldens are small text artifacts (sidecars, md5 lists) — keep the total
  well under 1 MB; they are stable because the source bytes and pinned mtimes
  are.
- `crlf.py` unit tests (its pure classifier `test_crlf`) — **holdings-free**;
  these run everywhere, including the PR-14 hosted job. **Collection trap:**
  `crlf.test_crlf` is named `test_*`, so `from …crlf import test_crlf` makes
  pytest collect the *imported* function and fail on a missing `filepath`
  fixture — import the **module** and call `crlf.test_crlf(...)`, never
  import the name.
- `shelf_consistency_check` and `show_opus_products` have no `main()` yet
  (that is PR-28), so test them here **via `subprocess`** invoking
  `python <path>.py` against the copied tree's dogfooded shelves — a stable
  interface that survives the PR-28 refactor (which then switches these tests
  to call `main()` in-process).
- `pdsdependency` tests: run against the copied tree with deliberately
  removed derived files; assert the emitted "Steps required" commands.
- the shell scripts: explicitly out of scope (ground rule 7). `re_validate` was
  out of scope under the old ground rule 7 and was left untested here because it
  executed its whole command line at import; PR-25a is the piece of work that
  gave it a `main()` and its own test module.
- Update `scripts/automated_tests/pdsfile_main_test.sh` to include
  `tests/holdings_maintenance/` in the suite paths.
- Validation: tool tests green against both holdings roots (or module-skip
  where the limited copy lacks the declared sources — record which); full
  suite unchanged vs. baseline.

### Phase 4 — CI

**PR-14 (M)** `ci: hosted lint/no-holdings job; keep self-hosted full-data gate`
The self-hosted full-data workflow is already the PR gate and nightly run
(§3.2); this PR adds the stock-runner coverage and tightens correspondence.
- `run-tests.yml`: add a **`lint` job on `ubuntu-latest`** (no holdings):
  `ruff check`, the API-freeze test, the clean-install import check, and the
  holdings-free pytest subset — run `pytest` with no holdings env vars set,
  which must collect everything, run the holdings-free tests (api freeze,
  crlf units, any other no-data tests), and skip the rest cleanly (this is
  itself the regression test for PR-09's graceful skip). Matrix
  `python 3.10` and `3.13` (floor + ceiling; the self-hosted matrix already
  covers all four versions with data).
- Keep the self-hosted full-data matrix exactly as it is (PR gate on
  `rewrite`, nightly cron, dispatch). `run-tests-and-opus.yml` continues to
  call `run-tests.yml` unchanged — its pdsfile leg remains a full-data run.
- Enable the pytest row in `run-all-checks.sh` (`ENABLE_PYTEST=true`): with
  holdings env vars it runs the full suite; without, the holdings-free
  subset. CI and the script stay in exact correspondence (`environment.mdc`).
- Update `.cursor/rules/pdsfile_overrides.mdc` deviation (8): the v1 "3-OS
  hosted matrix" aim is withdrawn — record the actual matrix (self-hosted
  Linux 3.10–3.13 full-data + hosted ubuntu lint/no-holdings job; Windows
  dropped in PR-08, macOS commented out for possible re-enablement).
- **Surface issue #102 to the owner** (drop or keep the Windows trove
  classifier) — an owner decision; implement whichever is decided, or leave
  the issue open if no decision, noting it in the PR.
- codecov: keep the current upload; targets stay informational until Phase 8.
- Nightly-failure alerting: GitHub built-in notifications (§8.7).

### Phase 5 — Core module decomposition (issue #77a)

Every PR in this phase: API-freeze green, ruff/clean-install green, plus a
**full-data run (both modes, against the goldens' reference root) whose
per-test pass/fail set is diffed against the recorded baseline and recorded in
`critiques/phase5-validation.md`** ("green" = identical set, §6.2). Technique:
method groups move to **mixin classes** in new private modules
(`class PdsFile(_OpusMixin, _ShelfMixin, …)`), module-level functions move to
private modules; `pdsfile/pdsfile.py` keeps re-exporting every name it
exports today so `pdsfile.pdsfile.X` access is unchanged. Fixed mechanics for
every extraction PR:
- The `class PdsFile` statement itself **stays in `pdsfile/pdsfile.py`**
  (pickled instances and `PdsFile.__module__` keep their path; memcached
  pickles depend on it).
- **Base order is alphabetical by mixin class name** (owner, 2026-07-27;
  established by PR-17, which created the first two mixins and had to pick an
  order to write the statement at all). The mixins are disjoint — the
  collision test asserts they share no names and shadow nothing `PdsFile`
  defines — so MRO order is behaviorally inert and the rule is chosen for
  reviewability: every future mixin has exactly one legal position, derivable
  without knowing which PR added what, and it is machine-checkable.
  `tests/api/test_mixin_collisions.py` asserts it, so a base list in any other
  order fails the gate. The illustration above is in that order. Trailing
  `object` is **not** a mixin and is not required in Python 3; it predates
  this effort and is left alone until PR-23's ruff cleanup, which already
  carries `UP004` for that line.
- Mixins define **no `__init__` and no new state** — methods/properties
  only, referencing existing instance/class attributes; class attributes
  (e.g. `SHELF_CACHE`) stay defined on `PdsFile`.
- Before merging: assert no method-name collisions across mixins (a simple
  set-intersection check in a **separate** test,
  `tests/api/test_mixin_collisions.py`, created in PR-17 — **not** inside
  `test_api_freeze.py`, which §6.4 forbids editing), and confirm the manifest
  diff is empty (it records names/signatures, not defining classes, so a
  clean mixin move is invisible to it — any diff means a mistake).
- **Class-object references (pinned pattern, no executor discretion):** a
  mixin module must **not** do a module-level `from pdsfile.pdsfile import
  PdsFile` — `pdsfile.py` imports the mixin modules to build the class, so a
  top-level back-import is a cycle. Any extracted method that needs a *class
  object* (not just a name) uses a **function-local deferred import**:
  `from pdsfile.pdsfile import PdsFile` inside the method body. The known
  instance is `opus_products`' `PdsFile.__subclasses__()` (`pdsfile.py:4778`),
  extracted in PR-19 — verified to be the **only** bare class-object reference
  inside any extraction seam. (Names, by contrast, are still resolved by
  `__name__` as the code does today — e.g. the PR-19 `__bases__` sniff.)
- **Freeze-invisibility of internals:** any *new* attribute, helper, method,
  or config constant introduced during the rewrite gets a **leading
  underscore** (invisible to the manifest, free to change — e.g. PR-15's
  `_HOLDINGS_ENV`). A genuinely *public* new name is an additive API change:
  allowed only with an allowlist entry and owner sign-off, never silently.

**PR-15 (M)** `fix: repair latent bugs in rarely/never-exercised core paths`
Each fix gets a regression test first. **Two of these are not dead code.**
Bug #1 is behavior-affecting (it changes cache population for a live
property), so it may legitimately shift the pass/fail set of the
cached-behavior full-data tests — call that out in the PR with a recorded
explanation (returned *values* are unchanged; only cache state is). Bug #2 is
a live crash on one deployment configuration (see its entry). The remaining
five are genuinely unreached today, which is why they survived; their
regression tests must be shown failing against the unfixed code, or they
demonstrate nothing.
1. `html_path` property: `self._recache` missing `()` (pdsfile.py:1785) — a
   no-op today, so `html_path` results are never cached; fixing to
   `self._recache()` (as the correct call at :3023 does) restores cache
   writeback for this live, commonly-used property.
2. `get_permanent_values`: `resume_caching()` called without its `cls`
   argument (:712 — inside `get_permanent_values`, lines 665–714, **not**
   `preload`, which starts at :840). **This is reached in production, not
   dead** (established while executing PR-15, 2026-07-27): `preload` calls
   `get_permanent_values` at :941, on the `if cls.MEMCACHE_PORT:` branch taken
   when nothing is missing from the cache — so on a **memcached deployment
   with a warm cache**, `preload()` raises `TypeError` for the missing
   positional argument. The bad call sits in a `finally:`, so it fires on the
   success path too. Non-memcached deployments never reach it, which is how it
   survived.
3. `abspath_for_logical_path`: hard-coded `PDS3_HOLDINGS_DIR` env lookup in
   shared base breaks Pds4 resolution (:197–198). Fix semantics, exactly: add
   a **private** class attribute `_HOLDINGS_ENV` (`'PDS3_HOLDINGS_DIR'` on
   `PdsFile` and `Pds3File`, `'PDS4_HOLDINGS_DIR'` on `Pds4File`; private so
   it is freeze-invisible) and look that up instead of the literal.
   `abspath_for_logical_path` is a module-level function taking `cls`, so it
   reads `cls._HOLDINGS_ENV`. PDS3 and base-class behavior are bit-identical;
   Pds4 gains the env fallback it was always supposed to have (new tests
   cover both).
4. `DictionaryCache.set_multi` passes unsupported `pause=` kwarg (pdscache:224).
5. `MemcachedCache.set_multi` iterates a dict as tuples (pdscache:798).
6. `pdsviewable.iconset_for` references undefined `ICON_FILENAME_VS_TYPE`
   (:547–559).
7. Bare `except:` at pdsfile.py:3020 → `except Exception` (behavior-audited).
(Maintenance-tool bug twins — `LOGDIRS`, `abs(bool)`, `checksum1 != checksum1`,
`shelf-consistency-check` undefined `error`, `re_validate` untouched ones
documented only — are fixed in Phase 6 where those files are being edited.)

**PR-16 (L)** `refactor: extract module-level path helpers → _path_utils.py`
Lines 47–247 (`construct_category_list`, `logical_path_from_abspath`,
`_clean_join/_clean_abspath/_clean_glob/_needs_glob`, `repair_case`,
`formatted_file_size`, `abspath_for_logical_path`, `selected_path_from_path`).
**Also carry the module constants these helpers use that sit *before* line
47** — `FILE_BYTE_UNITS` (:40-42, used by `formatted_file_size` at :170) moves
here; `PATH_EXISTS_CACHE_SIZE` (used by `_local_fs`'s `lru_cache` at :1280)
moves with `_local_fs.py` in PR-17. Both are public, so `pdsfile.py`
re-exports them (like every other extracted name). Sweep for any other
pre-:47 module constant a moved symbol references, and move/re-export it with
its consumer.

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
  which is why it moves in the same PR.
Both are mixins under the Phase-5 mechanics preamble (no new state, class
attributes stay on `PdsFile`). Also create
`tests/api/test_mixin_collisions.py` in this PR (see preamble).

**PR-18 (M)** `refactor: extract checksum/archive/log path builders → _derived_paths.py`
(4898–5059, 5361–5516.) This is the file-location half of issue #47:
`set_log_root` and the three `log_path_for_*` methods (used only by the
maintenance tools) move physically into `_derived_paths.py` as a mixin.
Because of the API freeze they stay reachable as `PdsFile.set_log_root` /
`PdsFile.log_path_for_*`, and the tools keep calling them exactly as today —
the move is invisible to callers. Actually *removing* them from the public
class surface (what #47 ultimately wants) is an API break deferred to phase
"b". Deduplicate the three near-identical `log_path_for_*` bodies into one
private `_log_path_for(...)` helper the three methods delegate to
(behavior-identical, golden-tested via the tool tests from PR-13).

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
`Pds4File` into the base module (import cycle). Keep
`PdsFile.__subclasses__()` sibling discovery as-is (deferred function-local
import per the preamble).

**PR-20 (L)** `refactor: extract associations, split/sort, transformations → _associations.py, _sorting.py`
(5979–6289, 5518–5871, 5873–5977.) Note `is_logical_path` (classmethod at
:6281) falls inside the associations line window but is a generic path
predicate, not an association. It is a **public `PdsFile` classmethod**
(frozen as `PdsFile.is_logical_path`), so it cannot become a plain module
function without vanishing from the class surface — **leave it in core**;
just do not sweep it into `_associations.py`. The associations proper end at
`associated_parallel` (ends :6280).

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
  `self._X_filled` and calls `self._recache`/`self._complete`, which remain
  in core, so this is a pure relocation and manifest-neutral (same Phase-5
  mixin mechanics).
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

**PR-23 (L, mechanical)** `style: ruff-clean core modules`
Clean `src/pdsfile/*.py` (core: `pdsfile.py` + extracted `_*.py` modules,
`pdscache.py`, `pdsviewable.py`; not rules). **Do not assume a fixed violation
list — derive it:** run `ruff check` with the template select set and classify
each violation as **fixable** or **freeze-locked** (fixing it would change a
frozen public signature/name, add an inline type annotation forbidden by
ground rule 5, or require reformatting an aligned table). Fix the fixable ones
(UP004, E721, E722, UP031, RUF005/015, C405, local-var naming, etc.).
**Freeze-locked violations in core become an enumerated, justified permanent
per-file-ignore** — as of 2026-07-17 these are: **`B006`** (`pdsviewable.py`
`to_dict(exclude=[])`, `PdsViewSet.__init__(viewables=[])` — public frozen
signatures; **do NOT "fix" B006, it is a manifest break**), **`A002`**
(`log_path_for_*(…, dir='')` in `pdsfile.py`, called by keyword `dir='…'` from
the tools — frozen param name), and **`RUF012`** (mutable class-attribute
defaults like `SUBCLASSES = {}`, `SHELF_CACHE = {}`, `VOLTYPES = [...]` — the
only ruff fix is a `ClassVar` annotation, forbidden by ground rule 5). The
ratchet shrinks to **only** this enumerated freeze-locked set for these files,
not to zero.
**Formatting — settled, no checkpoint remains.** The churn checkpoint this
section used to require **ran on 2026-08-03 against merged `rewrite`** (14 of 15
files, ~2,310 changed lines) and the owner **dropped the reformat entirely**
(`plans/2026-08-03-addendum-pr23-24-owner-decisions.md`). So: do **not** run
`ruff format`, do **not** enable the `ruff format --check` gate, and do **not**
add `# fmt: off` / `# fmt: on` guards — they exist only to protect aligned blocks
from a formatter that will not run. `ENABLE_RUFF_FORMAT` stays `false`. PR-23 is
a **`ruff check` PR only**.
No behavior change; full-data run to prove it. Record the freeze-locked set in
`pdsfile_overrides.mdc`.

**Branch and base:** PR-23 and PR-24 are **not stacked** (owner, 2026-08-03).
Each branches from `rewrite`, opens against `rewrite`, and merges before the next
begins; PR-24's §6.2 baseline is `rewrite` after PR-23 lands.

**PR-24 (L, mechanical)** `style: ruff-clean rules and remaining files`
Rules files + pds3file/pds4file `__init__` (including deduplicating the
twice-defined Pds3File alias properties — semantically identical bodies, one
positional/one keyword form; manifest unchanged). The `__init__.py` star imports keep the frozen names they bind; the
violations they raise are carried by permanent per-file ignores. **No inline
`noqa` is added** — §6.4 forbids it, and PR-24 added none.
**Freeze trap (do not "clean up"):** the `pds3file`/`pds4file` `__init__`
modules carry incidental top-level names that are in the manifest (e.g. `re`,
`pdslogger`, `pdscache`, `cache_lifetime_for_class` on `pdsfile.pds3file`).
ruff flags them as unused imports (F401), but removing them is a manifest
break outside both forgiveness categories (a hard stop). Keep them (permanent
F401 ignore per deviation (4)); never delete a manifested name to satisfy the
linter.
**F811 fix direction (do not guess):** where a name is defined twice, delete
the *dead* definition, not the live one — for the twice-defined `Pds3File`
alias properties delete the redundant copy; for `COVIMS_0xxx.py`
`OPUS_ID_TO_PRIMARY_LOGICAL_PATH` (a translator table at :287 shadowed by the
live method at :324) delete the **dead table assignment at :287**, keeping
the method (deleting the method would change behavior and the manifest kind).
- **The ratchet shrinks to a permanent, enumerated per-file-ignores block for
  the rule modules** (derive it by running `ruff check`, same method as
  PR-23 — do not hardcode blindly). As of 2026-07-17 the freeze-/table-locked
  set for `pds{3,4}file/rules/*.py` is: **`E501`** (~1,533 hand-aligned table
  lines >100 cols), **`W191`** (~302 tab indents in the pds4 tables —
  retabbing = the forbidden table rewrite), **`N801`** (rule class names
  `COISS_xxxx` …, frozen), **`N999`** (invalid module names, frozen public
  modules), **`N802`** (frozen uppercase methods `DATA_SET_ID`/
  `FILENAME_KEYLEN` …), **`N805`** (`COVIMS_0xxx.py:324`
  `OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)` — no `self`; `@staticmethod`
  would change the manifest kind), and **`RUF012`** (mutable class-default
  tables; `ClassVar` forbidden by ground rule 5). Everything else in rule
  modules (I001, E701, UP031, residual F403/F405/F401, RUF022, N806, F811/
  F841) **is fixable and fixed**. Also the `pds{3,4}file/__init__.py` files
  keep permanent `F401` (manifested incidental re-exports), `A002` (frozen
  `dir=` alias params), and `RUF012`. The `tests/rules/**` per-file-ignores
  migrated in PR-08 are **shrunk toward zero** here where cheap (split long
  strings via implicit concatenation, PT006 tuple form, N806 renames,
  `__all__` for `support.py`); any residue is enumerated like the other
  permanent ignores. **Record the full per-file-class freeze-locked set in
  `pdsfile_overrides.mdc` deviation (4).**
- Formatting: **none — dropped by the owner on 2026-08-03 along with PR-23's**
  (`plans/2026-08-03-addendum-pr23-24-owner-decisions.md`). No `ruff format`, no
  `ruff format --check` gate, no `# fmt: off` guards. PR-24 is a **`ruff check`
  PR only**. The aligned `pytest.mark.parametrize` tables in the test tree and
  the rule modules' `TranslatorByRegex` tables need no protection, because
  nothing will reformat them.
- **Branch and base:** PR-24 branches from `rewrite` **after PR-23 has merged**
  and opens against `rewrite`; the two are not stacked (owner, 2026-08-03). Its
  §6.2 baseline is `rewrite` at that point.
- **`re_validate.py` gets a `ruff check` per-file-ignore set** (its full derived
  violation set), not tables. The set this line first listed was the 2026-07-17
  snapshot and named eleven codes including `E402`; by the time PR-24 ran, the
  entry was the ten `B007`, `C405`, `E701`, `E721`, `I001`, `RUF005`, `RUF051`,
  `RUF059`, `UP031`, `UP034`, and `E402` had no site left — measured at `02f07a8`,
  where `ruff check --select E402` on that file reports nothing. It was permanent
  under the old ground rule 7; the owner lifted that freeze on 2026-08-05 and
  PR-25a then cleaned the entry to `RUF005` and `UP031`.
  It is in `pdsfile_overrides.mdc` deviation (4).
  Cleaning *other* `holdings_maintenance/` tools here is behavior-preserving
  style only.

### Phase 6 — Maintenance tools consolidation

Gates: PR-13's tool tests + a real-holdings validate run of each migrated tool
against at least one real volume/bundle, recorded in
`critiques/phase6-validation.md`. **CLI names, flags and exit codes are frozen**
(tests assert them). **Log and output *text* is not** — owner, 2026-08-05:
having versions that do and do not render a colon is not worth preserving, a
small change in logged text is acceptable, and the code should be as common as
possible rather than shaped by the text it emits.

**The limit, so this is not read as licence.** Output text may move **only where
keeping it would force duplication or a flag whose one job is to re-create one
side's wording.** It is not licence to reword, reformat or drop messages, to
change which events are logged or at what level, or to change a log file's path
or name. Every text change is enumerated line by line in
`critiques/phase6-validation.md`, each attributed to the commonality it bought;
a differing line that cannot be attributed is a defect. The tool-run gate still
diffs every captured line — it is the enumeration that changed, not the
measurement. `plans/2026-08-04-pr-25-deviations-addendum.md` §8 records the
ruling in full, with the changed lines PR-25 itself produced.

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
  pds4 tool: `pdsfile_cls` (`Pds3File`/`Pds4File`), `unit` (`'volume'` vs
  `'bundle'`, substituted into the help text — the `vocab` field under a name
  that says what it holds), `holdings_sentinel` (`'/holdings/'` vs
  `'/pds4-holdings/'`), `index_ext` (`.tab`/`.csv`), `logname` (e.g.
  `'pds.validation.archives'`), and `handler_factories`, an **ordered tuple** of
  `pdslogger` handler factories — `(error_handler,)` for pds3,
  `(warning_handler, error_handler)` for pds4. A tuple rather than an
  "extra handlers" boolean because the order the handlers are added in is
  observable and a boolean does not carry it.
- `build_arg_parser(spec)` → the argparse parser with the five task flags with
  **today's exact semantics** — they are independent `store_const`-into-`task`
  flags, **not** an `add_mutually_exclusive_group` (do not introduce one; that
  would turn a multi-flag invocation from today's last/first-wins into an
  argparse hard error) — plus the `volume/bundle` positional +
  `--log`/`--quiet` and a hook for tool-specific flags (`--archives`,
  `--infoshelf`). PR-13 adds a two-flag invocation case pinning the current
  resolution behavior.
- `run_main(spec, task_table, argv)` → the `main()` driver loop (resolve log
  root from `PDS_LOG_ROOT`, build the `PdsLogger` + handlers, resolve the
  pdsfile list, run nested `logger.open`/`close` scopes, set exit code from
  fatal/errors). `task_table` maps `'initialize'|'reinitialize'|'validate'|
  'repair'|'update'` → the tool's callables.
- Each thin tool module (`pdsarchives.py`, …) shrinks to: its `generate_*`/
  `read_*`/`write_*`/`validate_*` domain functions, a `SPEC = ToolSpec(...)`,
  a `TASKS = {...}`, and `def main(): return run_main(SPEC, TASKS, sys.argv)`.
Migrate `pdsarchives`/`pds4archives` first (hardest divergence: pds3 single-tar
vs pds4 one-bundle-→-many-tarballs). **`write_archive` is not a spec hook**: the
divergence proved larger than a hook — measured at `ab1fa3b`, the two
`write_archive`s and the ten task functions differ in six further observable
ways, so a shared one would carry a flag per difference. Both implementations
and all ten task functions stay in their own tool modules; the reasoning and the
measurements are in `plans/2026-08-04-pr-25-deviations-addendum.md` §1. The
requirement that stands, and is met, is **no `if pds4:` branch anywhere** in
`_common.py`. The CLI surface and exit codes are asserted unchanged by PR-13's
tests. **Log text changes in three enumerated places**, each under the Phase 6
rule above and each listed line by line in `critiques/phase6-validation.md`: a
traceback inside a tool log names the shared driver frame rather than the tool's
own `main()`; the link shelf's "moved to" line gains the colon the other two
kinds already rendered, which is what let the three versioning functions become
one; and the "moved from" line of all three reports its path relative to the
logger's root, for the same reason. The traceback change is the one no
implementation can avoid — a traceback names the frames on the stack and this
design puts a shared frame there. Any later comparison of tool output must
normalize traceback **line numbers** but must **not** normalize traceback file
names, which is what makes that difference visible rather than hidden.

**PR-25a (M)** `refactor: main() and a test module for re_validate`
Brings the last unmodernized tool up to the standard of the others, now that
ground rule 7's freeze is lifted. The whole program ran at module level, so
importing the module parsed a command line and could call `sys.exit()` from
inside the import; it is decomposed into `build_parser()`, `derive_options()`,
`run_interactive()`, `run_batch()` and `main(argv=None)`, with
`if __name__ == '__main__'`. **No new console-script name** (§8.4): `python -m
pdsfile.holdings_maintenance.pds3.re_validate` stays the only invocation. It does
**not** migrate onto `run_main`/`ToolSpec` — it has no five-task flag set, its
positional is `nargs='*'`, and its driver loop is nothing like `run_main`'s — so
what it shares with `_common.py` is the four things that were genuinely duplicated:
`LOGROOT_ENV`, `LOG_HELP`, `QUIET_HELP`, and a new `resolve_log_root()` extracted
from `run_main` and called by both. **Ten bugs fixed, each with a test**, two of
them forced by the move into a function scope because they read module globals a
function scope does not supply; an eleventh finding, a constant read nowhere, is
recorded rather than removed, because ground rule 9 forbids deleting it. New
`tests/holdings_maintenance/test_re_validate.py`, marked `holdings_free` and run
in-process. The ruff entry shrinks from ten codes to two. **Two `--help` lines are
reworded**, because the hand-copied help text is replaced by the `_common` constant
it near-duplicated, and **six log message sites** lose the misspelling
`re-validatation`. How many rendered lines that is depends on the tree: each firing
of a site renders two lines carrying the text, and on a full five-volume-type tree
with archive tarballs the six sites fire 28 times. Every changed line is enumerated
and attributed in `critiques/pr-25a-validation.md`.

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
  clearly intended a **1-second tolerance**, but the operands are **ISO time
  strings** (truncated to seconds at `pdsinfoshelf.py:380-381`), so both the
  original bug and a naïve `str - str` "fix" are wrong. Implementable fix
  (the intended semantics, owner-defaulted): parse the two **untruncated**
  modtime strings with `datetime.fromisoformat` and compare
  `abs((t1 - t2).total_seconds()) > 1`; drop the now-unneeded
  second-truncation lines. Pin the 1-second tolerance with a test. Whichever
  is chosen, pds3 and pds4 share it via `_common.py`.
Preserve the pds3 `--infoshelf` chaining behavior (modernize `os.system` →
`subprocess.run` as pds4 already does — flagged behavior change, tested).
CLI surface and exit codes asserted unchanged by PR-13's tests; log text held to
the Phase 6 rule above — it may move only where keeping it would force
duplication or a shrug-flag, and every changed line is enumerated and attributed.
**Note:** PR-25 already made the `LOGDIRS` fix listed above, and already merged
`hashfile()` and the three `move_old_<kind>()` functions into one, so those
items are done rather than owed here.

**PR-27 (L)** `refactor: migrate indexshelf and linkshelf pairs onto the core`
Migrate `pdsindexshelf`/`pds4indexshelf` and `pdslinkshelf`/`pds4linkshelf`
onto `_common.py`, same pattern as PR-25/26 (ToolSpec + task table + thin
`main()`); CLI surface and exit codes asserted unchanged by PR-13's tests, and
log text held to the Phase 6 rule above — it may move only where keeping it
would force duplication or a shrug-flag, and every changed line is enumerated.
The large pds3 `REPAIRS` table is moved **content-unchanged** into its own data
module, `pds3/linkshelf_repairs.py`, imported by the thin linkshelf tool.

**PR-28 (M)** `refactor: main() for crlf, shelf_consistency_check, show_opus_products`
Proper argparse + `main()` so they are testable and runnable via
`python -m pdsfile.…`. **No new console-script names** (§8.4 — `python -m`
only; `[project.scripts]` is not extended). Also fixes the
`shelf_consistency_check` undefined-`error` bug (should be `errors`, noted in
PR-15's bug list) with a regression test. **Update the PR-13 subprocess
tests** for these two tools to call `main()` in-process and keep them green
(the behavior under test is unchanged; only the invocation path moves).
`re_validate.py`: not touched by this PR. PR-25a is the one that modernizes it.

### Phase 7 — Docstrings and documentation

**PR-29 (L)** `docs: Google-style docstrings — core modules`
Per `doc_python.mdc`: every module/class/method/function in
`src/pdsfile/*.py` (core + extracted modules, pdscache, pdsviewable);
`Parameters:` sections, wrap at 90; fix the known typos. Content must be
accurate to behavior — verified against the code, not the old docstrings.

**PR-30 (L)** `docs: docstrings — rules, subclasses, maintenance tools`
Rule modules get a standard header docstring (dataset, what each rule table
does); tools get module + function docstrings.

**PR-31 (M)** `docs: Sphinx scaffolding + API reference`
`docs/` per template: `conf.py` (autodoc/napoleon/intersphinx/mermaid/myst),
`index.rst` including the README past its `<!-- start-after-point -->` marker,
`api/` autodoc pages per subpackage. **The current README has no such
marker;** add a minimal one in this PR (the full `doc_readme` rewrite is
PR-34) so the include target exists. Builds clean under `-W` and `-n`. Enable
the sphinx gate in `run-all-checks.sh` and the CI lint job;
`.readthedocs.yaml` goes live.

**PR-32 (L)** `docs: user guide (CLI tools)` (closes issue #45)
`docs/user_guide/`: concepts chapter (holdings layout, volumes vs bundles,
shelves, checksums, archives — with the directory taxonomy from
`setup_new_holdings.sh`); installation & environment (env vars, precedence —
**document holdings roots only as `$PDS3_HOLDINGS_DIR`/`$PDS4_HOLDINGS_DIR`
placeholders, never a literal machine path**, per §3.4's confidentiality
rule); **one chapter per CLI program** — all 11 entry points plus `crlf`,
`shelf_consistency_check`, `re_validate` (documented as-is), and
`show_opus_products` — every option documented (flag, effect, default),
runnable examples shown against a holdings tree via the env-var placeholders;
a chapter documenting the sync shell scripts (document-only, per ground
rule 7); appendix: file formats (shelf `.pickle`/`.py` sidecar, `*_md5.txt`,
`_volinfo`).

**PR-33 (L)** `docs: developer guide` (closes issue #43)
`docs/dev_guide/`, with an **explicit required chapter + diagram list** (so
the synthesis is bounded, not open-ended):
1. *Repository layout* — annotated literal-block dir tree (from §4 of this
   plan, kept current).
2. *Architecture* — narrative + exactly these Mermaid diagrams:
   (a) `classDiagram` of `PdsFile` and its mixins (`_ShelfMixin`,
   `_LocalFsMixin`, `_OpusMixin`, `_IndexRowMixin`, `_AssociationsMixin`,
   `_SortingMixin`, `_DerivedPathsMixin`, `_PreloadMixin`, `_PropertiesMixin`)
   + `Pds3File`/`Pds4File`/rule-subclass leaves; (b) `flowchart` of the cache
   layers and their lifetimes (`DictionaryCache`/`MemcachedCache`, the
   `$RANKS`/`$VOLS`/`$VOLINFO` permanent keys, per-lifetime buckets);
   (c) `flowchart` of the shelf subsystem (info/link/index shelves + the
   `.py` sidecar `eval`); (d) `sequenceDiagram` of `preload()`;
   (e) `flowchart` of rules resolution (volset ID → `VOLSET_TRANSLATOR` →
   `SUBCLASSES` key → subclass).
3. *Subsystem reference* — one section per extracted module, each stating its
   contract and invariants (logical vs abs paths; ranks/vols bookkeeping;
   merged vs physical category dirs; the `SHELVES_ONLY` global-state
   limitation; thread-safety = single-process assumption).
4. *Extending, part A: writing a rules file for a new volume/bundle* — a
   copy-paste skeleton (module docstring, the translator tables to define,
   the `SUBCLASSES[...] =` registration, the standard test set from PR-08)
   walked through against one real small example.
4b. *Extending, part B: modifying the maintenance tools for a new dataset*
   (the second half of issue #45) — how the `_common.py` `ToolSpec` is
   filled, and how to author the `pdslinkshelf` `REPAIRS` regex table for a
   dataset with nonstandard internal links, with one worked example.
5. *Test-suite guide* — holdings resolution (env vars, the full/mini/skip
   flavor machinery with the mini flavor documented as dormant/reserved for
   the deferred mini-holdings plan; collect-and-skip without holdings),
   `--mode s|ns`, markers (incl. `full_holdings` and the PR-13 source-subset
   skip model), the golden mechanism and `--update` (regenerated only against
   real holdings; never hand-edited), and the tool-test `tmp_path` copy
   model.
6. *How-to: regenerating goldens* — when `--update` is legitimate, which
   holdings root to use (the goldens' reference root), and how to present the
   diff for review.
7. *CI/release workflow* — the workflows (self-hosted full-data + hosted
   lint job + nightly + OPUS integration), `run-all-checks.sh` as source of
   truth, setuptools_scm tagging.
Builds under `-W` and `-n`; every API symbol named in prose uses the correct
Sphinx cross-reference role (per `doc_python.mdc`).

**PR-34 (M)** `docs: README rewrite` per `doc_readme.mdc`
Badges, plain-prose introduction, features, installation, quick start (module
usage AND a CLI invocation), documentation/contributing/license links. Enable
the pymarkdown gate (run-all-checks + CI) once README/docs comply.

**PR-35 (M)** `feat: public API type stubs`
Hand-written `.pyi` stubs for the public surface (ground rule 5):
`__init__.pyi` plus stubs for `pdsfile.pdsfile`, `pds3file`, `pds4file`,
`pdscache`, `pdsviewable` covering exactly the manifest names; add `py.typed`.
Typing rule for the (unannotated) implementation: derive types from code and
docstrings; where genuinely uncertain, use the broadest type that is provably
correct (`str | None`, `list[str]`, `Any` as last resort) — a wrong narrow
type in a stub is worse than a broad one. Validated with `mypy.stubtest`
(checks stub names/kinds against runtime; an allowlist covers unstubable
dynamics) run locally/CI-lint. No inline annotations.

### Phase 8 — Critique, hardening, merge

**PR-36 (M, possibly split)** `chore: run critique skills and address findings`
Run the template's `.cursor/skills` — `critique-test-suite`,
`critique-documentation`, `python-codebase-analysis` — save the full reports
in `critiques/`; triage findings with the owner; fix the accepted ones.

**PR-37 (S)** `chore: finalization`
- **Strip the rewrite scaffolding from `pyproject.toml`.** The owner permits
  plan-related commentary there — the ratchet header and the per-entry notes
  naming sub-plans, deferred observations and PR numbers — **on the condition
  that it is deleted once the rewrite is finished** (owner, 2026-08-03). Before
  the `rewrite` → `main` PR opens, `pyproject.toml` must carry no reference to
  `plans/`, `critiques/`, `deferred-observations.md`, a PR number, or the frozen
  public surface / API freeze / `api_manifest.json` — the same list source files
  are held to continuously; `pyproject.toml` is merely exempt until here. The
  per-file-ignores entries themselves stay; only the commentary explaining how
  the port derived them goes, and what survives of the reasoning lives in
  `.cursor/rules/pdsfile_overrides.mdc` deviation (4), which is a rules file
  rather than a build file. Source files are already held to this rule
  continuously: code comments describe the current state of the code and may
  never name a plan, a critique, a PR or the API freeze.
- Verify: `run-all-checks.sh` fully green; hosted lint/no-holdings job green;
  self-hosted full-data matrix green with the per-test pass/fail set
  identical to the recorded baseline; nightly green; OPUS integration green;
  API manifest identical to the Phase-0 dump (modulo the reviewed allowlist).
- Consumer smoke check: run the rms-opus import-path smoke and the
  rms-viewmaster startup against the rewrite branch, and **diff the outcomes
  against the recorded consumer-smoke baseline** (§3.4) — the gate is "same
  outcome as baseline," so the pre-existing rms-viewmaster `cache_lifetime`
  startup failure does not count against the rewrite (record in critiques/).
- Set codecov targets; CHANGELOG/release notes summarizing the rewrite.
- Open the `rewrite` → `main` PR; after merge, tag and release; close
  issues #77 (phase a), #82, #43, #45 (already-closed #37 referenced),
  referencing #79.

## 6. Cross-cutting mechanisms

### 6.1 API-freeze enforcement
The manifest (PR-02) is the contract. The checker runs locally
(`run-all-checks.sh`), in the self-hosted CI (since PR-04), and in the hosted
lint job (from PR-14). Forgiven deviations live in
`tests/api/manifest_allowlist.json`. Exactly **two pre-approved forgiveness
rules** exist, both **category predicates**, both already exercised by the
merged PRs they belong to: (1) the `pdsfile.pds{3,4}file.tests*` subpackages
leaving the installed package (PR-07); (2) rule modules losing their
`test_*`/test-only names (PR-08). **Any new diff outside these two categories
stops work and goes to the owner** — the executor may not add a third
forgiveness rule (exact or category) on its own. New internals are
underscore-prefixed (freeze-invisible, §5 preamble); a genuinely public new
name requires an allowlist entry and owner sign-off.

### 6.2 Behavior-preservation evidence
For every Phase 5/6 PR: (1) full-data suite, both modes, against the goldens'
reference root, with the **per-test pass/fail set diffed against the recorded
baseline (§3.2) — the gate passes only if the sets are identical** (a test
newly passing is as much a flag as one newly failing; both require a recorded
explanation), (2) for tool PRs, a real-volume tool run diffed against the
pre-PR output (`.py` sidecars and logs, mtime-normalized). Results appended
to the phase validation file in `critiques/`.

### 6.3 Record keeping
`plans/` — this plan; any per-phase detailed sub-plans the executor writes
before a phase; `plans/archive/` — superseded plans. `critiques/` — the
historical code-quality analysis, validation records, the per-PR
adversarial-review rounds (`critiques/pr-<NN>/round-<k>.md`, §6.6),
critique-skill reports, `deferred-observations.md`, and the post-merge
retrospective.

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
   opening the PR.
4. Open the PR against `rewrite`; do not start the next PR in a way that
   stacks unmerged behavior changes (mechanical follow-ups may proceed).

**Human-review cadence (§8.6):** every refactor/test/docs PR gets full
line-by-line human review at its boundary.

**Hard stop conditions — halt and ask the owner instead of deciding:**
- Any API-manifest diff not covered by the two pre-approved allowlist
  categories (§6.1).
- Any full-data run whose pass/fail set differs from the baseline without a
  cause the executor can prove is the intended, documented change of that PR.
- ~~The PR-23 and PR-24 formatting churn checkpoints.~~ **Discharged
  2026-08-03**: the checkpoint ran and the owner dropped the reformat entirely
  (`plans/2026-08-03-addendum-pr23-24-owner-decisions.md`). Running `ruff format`
  is now itself the hard stop.
- Any situation where following the plan would require changing behavior,
  file formats, CLI flags, or exit codes not explicitly listed as changing.
  **Log and output text is no longer on this list** (owner, 2026-08-05) — but
  only under the Phase 6 rule: it may move where keeping it would force
  duplication or a shrug-flag, every changed line is enumerated and attributed,
  and a change that buys no commonality is still a stop.
- Any new decision not already settled in §8 or elsewhere in this plan —
  surface it rather than choosing unilaterally.

**Prohibitions (absolute):** never edit `api_manifest.json`, the allowlist, or
`scripts/dump_public_api.py` / `tests/api/test_api_freeze.py` (editing the
dumper or the checker makes any diff vanish while both sides agree — a silent
freeze defeat; put any *new* API-adjacent test assertions in a separate file);
never edit golden files or baseline records to make a gate pass; never
disable, skip, or mark-xfail a failing test to get to green; never widen the
ruff ratchet. Golden files change only via `--update` runs whose necessity the
PR description justifies. Deviations from this plan require an addendum file
in `plans/` acknowledged by the owner before the deviating PR merges.

### 6.5 Highest-judgment sections (where the executor must slow down)

Most PRs are mechanical. These carry the most design judgment; each has a
concrete spec above. If, while executing one, the spec still leaves a genuine
design fork, that is a §6.4 hard stop — write the options into `plans/` and
get the owner's pick rather than guessing.

- **PR-13 tool-test source subsets** — spec'd: explicit `SOURCE_PATHS`,
  pinned-mtime table, fixed corruption scenarios, member-tuple archive
  comparison, module-skip on missing sources.
- **PR-22 core finalization** — spec'd: ~1,750-line target after moving the
  lazy-property block to `_PropertiesMixin` (§8.3).
- **PR-25 `_common.py` design** — spec'd: the `ToolSpec`/`build_arg_parser`/
  `run_main` target interface and the pds3/pds4 divergence-as-hook rule.
- **PR-33 developer guide** — spec'd: the exact chapter list and the five
  required Mermaid diagrams.

### 6.6 Adversarial pre-PR review loop (mandatory for every PR)

Before opening **any** PR, the executor runs a self-contained adversarial
review loop to catch, with fresh eyes, the defect class the author is blind
to.

**Round procedure:**
1. Finalize the code; confirm every phase gate (§2) passes locally.
2. Spawn a **fresh opus-class subagent as adversarial reviewer, with no
   development context** — it must not receive the implementation
   conversation, the executor's reasoning, or prior review rounds. Give it
   exactly:
   - the PR's section of this plan (its deliverables), the phase preamble,
     the ground rules (§2), and the relevant cross-cutting rules (§6.1
     freeze, §6.2 behavior evidence, and for refactor PRs the Phase-5 mixin
     mechanics);
   - the **exact diff** of the PR: `git diff <pr-base>..<pr-head>`;
   - read access to the whole repo at `<pr-head>`, to the real holdings, and
     to the consumer repos, so it can **verify claims against the code, not
     against the diff's own comments**;
   - the **progressive-compliance schedule** (below), so it does not flag
     `.cursor/rules` violations that this and earlier PRs were never meant to
     fix yet.
3. The reviewer's mandate is **adversarial**: assume the phase goal was NOT
   met and try to prove it. It checks, at minimum: does the diff actually
   deliver the PR's stated goal; are all phase gates genuinely satisfied (not
   just claimed) — freeze diff within the two forgiveness categories, ruff
   ratchet not widened, behavior preserved. **On the full-data gate the
   reviewer does NOT re-run the suite**; it verifies the *evidence*: the
   recorded run in `critiques/` exists, was generated **at or after the PR's
   last change under `src/pdsfile/`** (a record predating the last `src/`
   change is stale; a later change touching only tests/docs/records does not
   stale it — see step 5), and its diff-vs-baseline computation is present
   and shows the identical set — and it spot-checks that computation. A
   missing, stale, or hand-waved record is a Major finding. For **refactor**
   PRs the reviewer also checks: is moved code byte-for-byte equivalent and
   are all references updated; for **test** PRs, do new tests assert real
   values or are they hollow/tautological; is there dead code, a missed file,
   an ambiguity, or scope creep. **Output:** findings split into **Major**
   (goal not met; correctness / behavior / freeze / gate violation; missing
   deliverable) and **Minor** (clarity, incompleteness, style, weak test) —
   each with `file:line` evidence and a concrete fix — plus an explicit
   verdict (`goal met` / `goal not met`). A third, **non-blocking** bucket —
   **Deferred** — may hold genuine issues out of scope for this PR; Deferred
   items are appended to `critiques/deferred-observations.md` for the phase
   that owns them. The reviewer makes **no edits**.
4. The executor resolves **every** Major and Minor finding: (a) fix it; or
   (b) if the finding is provably wrong or is scope-creep beyond the PR's
   stated goal + ground rules, write a short **rebuttal**. Both are recorded.
5. Spawn a **new** fresh reviewer (no context, no knowledge of prior rounds)
   on the updated diff; **repeat from step 1** (re-confirm the §2 gates on
   the changed code first). **Full-data-record regeneration rule:** if the
   round's fixes touched any source under `src/pdsfile/`, regenerate the
   full-data run and its baseline-diff record before the next reviewer; if
   the round changed only `tests/`, docs, or records, the prior record
   carries forward (note that in the PR).

**Termination — the loop ends when a fresh reviewer returns zero Major
findings and no *new, un-rebutted* Minor findings** (verdict `goal met`).
Then open the PR.

**Anti-thrash rules:**
- A rebutted **Major** re-raised by the next independent reviewer is a
  genuine disagreement — **hard-stop to the owner** with both the finding and
  the rebuttal. A re-raised **Minor** that was reasonably rebutted does
  **not** escalate; the loop converges when a round returns no *new* Minor
  and no Major.
- **The 4th round (if reached) is a *scoped* re-review:** "confirm the prior
  round's findings are resolved; raise only **new Major** findings."
- A reviewer may only judge against the PR's stated goal + the ground rules;
  a finding demanding work beyond this PR's scope is invalid — rebut, and
  escalate only if re-raised.
- **Hard cap: 4 rounds.** If a fourth round still finds issues, stop and
  bring all round records to the owner (mis-scope signal).
- Purely subjective nits are Minor only if tied to a `.cursor/rules` mandate.
- **Progressive `.cursor/rules` compliance.** A cursor-rule violation is a
  valid finding **only if** compliance with that rule was a stated
  deliverable of this PR or an already-merged earlier PR. The authorities on
  "what is in force when" are: each PR's stated goals, the §2 gate table, and
  `.cursor/rules/pdsfile_overrides.mdc`. The schedule:

  | `.cursor/rule` area | In force from |
  |---|---|
  | `dependency_management.mdc` (pyproject single source) | **Active** (PR-03) |
  | `environment.mdc` (`run-all-checks.sh` = CI source of truth) | **Active** (PR-04), tightened at PR-14 |
  | `python.mdc` style/naming/line-length (`ruff check`) | ratcheted since PR-03; from PR-23 (core) / PR-24 (rest) reduced to the enumerated freeze-/table-locked permanent ignore sets |
  | `python.mdc` `ruff format` | **never enforced** (owner, 2026-08-03 — the churn checkpoint ran and the reformat was dropped) |
  | `python.mdc` type annotations / mypy | **permanently waived** (ground rule 5); `.pyi` stubs at PR-35 only |
  | `python.mdc` "modules < 1000 lines" | **permanently waived** for the explicit list in `pdsfile_overrides.mdc` (3): `pdsfile.py`, `_properties.py`, `pdscache.py`, and the rule modules. Everything else is held to the limit |
  | `python_testing.mdc` (pytest/markers/coverage) | Phase 3–4 (PR-08–PR-14); the hermetic aspects are out of scope (see the scope note) |
  | `doc_python.mdc` docstrings; `doc_readme`/`doc_dev_guide`/`doc_user_guide` | Phase 7 (PR-29–PR-34) |
  | `logging.mdc` (PdsLogger) | already followed; enforced only where a PR edits logging; waived for the tools' frozen `print()` output |
  | `git_workflow.mdc`, `pull_request.mdc` | every PR |
  | `filecache.mdc` (FCPath) | **permanently excluded** (ground rule 6) |

**Records:** every round is saved to `critiques/pr-<NN>/round-<k>.md`; the
final clean review is linked from the PR description. This loop **precedes
and does not replace** the human review at the PR boundary.

### 6.7 Execution topology (phase and reviewer subagents)

To keep any single context small, execution is a strict four-level subagent
nesting, and **every PR runs in its own dedicated PR-executor subagent — in
all phases, without exception** (owner-reaffirmed 2026-07-25 after PR-09 was
executed inline):
- A thin **top-level coordinator** owns only this plan, the branch state, and
  the phase-boundary gates. It executes no code itself.
- For each phase it spawns **one phase-coordinator subagent**, passing it the
  plan, the phase to run, and the current branch state. The phase coordinator
  **does not implement PRs itself** — it spawns **one child PR-executor
  subagent per PR** (in order), passing each only that PR's section of the
  plan + branch state, and collects each PR-executor's short summary +
  `critiques/pr-<NN>/` links. This holds even for one- or two-PR phases.
- Each **PR-executor subagent** carries exactly one PR end to end
  (implementation + the §6.6 loop) and returns only a concise summary.
- Each §6.6 **adversarial reviewer is its own short-lived, no-context
  subagent** (a new one per round), hanging off the PR-executor.
- At each phase boundary the top-level coordinator independently confirms the
  §2 phase-boundary gates before launching the next phase-coordinator. A
  failed boundary gate is a hard stop, not an auto-retry.
- **PRs within a phase are strictly ordered** (a later PR-executor starts
  only after the prior PR is merged to `rewrite`, unless the plan marks them
  independent); per-PR subagents bound *context*, not concurrency.
- **Fallback if nesting is capped:** collapse levels from the **top**, never
  the bottom — the interactive session plays the coordinator (and, if
  needed, the phase-coordinator) role; what remains spawned is always "one
  PR-executor subagent per PR" and, under it, the fresh no-context §6.6
  reviewer per round. Record the chosen topology in `critiques/`.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Contributors without holdings can't run data tests | Graceful collect-and-skip (PR-09); the hosted lint job (PR-14) gives them ruff + freeze + clean-install + holdings-free tests; the self-hosted PR gate runs the data suite on every PR regardless |
| Tool tests depend on real-holdings source files that a limited copy may lack | PR-13's explicit `SOURCE_PATHS` + availability check → module skip with the `full_holdings` marker; the complete-set nightly always runs them |
| Mixin split preserves file-level modularity but not true SRP | Accepted: that is phase "a" of #77 by decision; phase "b" is future work |
| `run-tests-and-opus` / consumers break subtly despite manifest | Manifest covers names/signatures, not semantics — hence the full-data gates and the Phase 8 consumer smoke checks |
| RTD/docs red mid-rewrite | Acceptable on `rewrite`; gates activate when their phase lands |
| Adversarial review loop thrashes or never converges | 4-round hard cap + rebuttal-then-escalate on repeated findings + scope-locked to the PR's goal (§6.6) |
| Per-PR review loop adds latency/token cost | Bounded: mechanical PRs converge in 1–2 rounds (borne out by PR-02–PR-09: all converged in ≤3) |

## 8. Settled decisions (owner-confirmed; updated 2026-07-25)

1. ~~Test-data repo `rms-pdsfile-test-data`~~ — **superseded 2026-07-25**: the
   repo exists (public, empty) but stays empty; all fixture-tree work moved to
   `plans/2026-07-25-mini-holdings-plan.md`.
2. ~~Fixture index-table truncation~~ — **superseded 2026-07-25**: moved to
   the mini-holdings plan.
3. **`PdsFile` split depth:** PR-22 moves the ~1,550-line lazy-property block
   into `_properties.py` (`_PropertiesMixin`, manifest-neutral), landing core
   at **~1,750 lines**.
4. **No new console scripts** for `crlf`/`shelf_consistency_check`/
   `show_opus_products` — `python -m` invocation only (PR-28).
5. **`tabulate`** ships in the **`dev` extra** (done, PR-03).
6. **Human-review cadence:** full human review on every refactor/test/docs PR
   (the Phase-2 lighter-touch allowance is history — Phase 2 is merged).
7. **Nightly-failure alerting:** GitHub's built-in notifications for now;
   revisit if noisy (PR-14).
8. **Branch protection:** protect `rewrite` with the required checks once
   PR-14 lands (owner/admin action, not an executor task).
9. **(2026-07-25)** Mini-holdings removed from this effort entirely; testing
   stays on real holdings; the design record and future options live in
   `plans/2026-07-25-mini-holdings-plan.md`. The merged mini-ready plumbing
   (flavor resolver, env vars, `full_holdings` marker, `tests/golden/full/`
   layout) is retained dormant for the future work — not removed.

## 9. Issue mapping

| Issue | Where addressed |
|---|---|
| #77 PdsFile split | Phase 5 (phase "a"); "b" explicitly deferred |
| #82 maintenance-tool tests | PR-13 |
| #79 architecture analysis | Historical record at `critiques/2025-08-15-code-quality-analysis.md`; deep redesign deferred |
| #45 maintenance-tool docs | PR-32 (+ PR-33 ch. 4b for the extending guide, closing the issue fully) |
| #43 module docs/docstrings | PR-29/30/31/33 |
| #37 inconsistent rules tests | **Closed** (PR-08) |
| #40 golden-file test framework | **Closed** (rules tests). Extending it to the blackbox/whitebox inline values is tracked by #92 |
| #92 move inline `@parametrize` values into golden files | **Future work, not in this plan** (its hermetic motivation is withdrawn with the mini-holdings scope; it remains a valid consistency cleanup on its own and stays open) |
| #47 log-path functions don't belong in PdsFile | PR-18 handles only the refactoring half (mixin move; names stay on `PdsFile` per the freeze); full removal deferred to phase "b"; #47 stays open |
| #71 sync scripts | Document-only (PR-32), by decision |
| #85 re-validate email | Still out of scope. PR-25a modernizes the module and splits the message construction out of `send_email()` so it can be tested without a socket, but it does not redesign the email feature |
| #102 Windows classifier | Owner decision surfaced in PR-14 |

**Deliberately out of scope** (open issues this rewrite does not address —
listed so their omission is a decision, not an oversight): #88, #76, #31,
#14, #8, #6, #4, #3, #2 — behavior/feature issues untouched by a
compatibility-preserving modernization; they remain open after merge.
