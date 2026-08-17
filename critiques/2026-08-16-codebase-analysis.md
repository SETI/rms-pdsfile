# Codebase analysis: rms-pdsfile

Date: 2026-08-16. Tree: branch `chore/critique-reports`, identical to `rewrite` at
commit `6525951`. Produced by the `python-codebase-analysis` skill
(`.cursor/skills/python-codebase-analysis/`), assessed against the project rules in
`.cursor/rules/` with `.cursor/rules/pdsfile_overrides.mdc` taking precedence where
they conflict. Findings carry stable identifiers CA-01 through CA-32 in order of
appearance. Every number below was measured in this session; the exact commands are
in the appendix. Anything not measured is marked "(unverified)".

Scope and method: all ten dimensions, whole repository. Read fully: the nine named
rule files plus `pdsfile_overrides.mdc`, `pyproject.toml`,
`scripts/run-all-checks.sh`, `src/pdsfile/holdings_maintenance/_common.py`,
`src/pdsfile/__init__.py`, `tests/conftest.py` (head), the CI workflow
`run-tests.yml`, and one full rule module (`ASTROM_xxxx.py`). Read in
representative part: `pdsfile.py`, `pdscache.py`, `_preload.py`, `_shelves.py`,
`_index_rows.py`, `re_validate.py`, `tests/support/holdings.py`,
`tests/holdings_maintenance/conftest.py`, `tests/docs/test_docstrings.py`,
`scripts/gen_ruff_ratchet.py`, `scripts/check_runtime_imports.py`. The other 52
pds3 and pds4 rule modules, the remaining maintenance tools, and the docs `.rst`
tree were covered by grep sweeps, line measurements, and mechanical pair diffs
rather than full reads.

## Summary

The package is in strong shape for a codebase of its history: the core library has
zero `print()`/`sys.exit()` sites, the configured lint gates pass clean, the
docstring and API-freeze machinery is unusually thorough, `pyroma` scores 10/10,
and the wheel contents are verified correct. The deliberate deviations recorded in
`pdsfile_overrides.mdc` (no inline typing, frozen public API, enumerated ruff
ratchet, two-limit module lengths) are respected throughout and are not
re-litigated here. The top actionable items are: (1) test coverage is 58% overall
against the project's 90% target, with the maintenance-tool drivers at 6-30% and
no enforcement anywhere (CA-13); (2) seven of eight runtime dependencies declare
no minimum version and no automated vulnerability scanning exists (CA-24, CA-21);
(3) eight text-mode `open()` calls rely on the platform default encoding (CA-04).

## 1. Structure and layout

- **CA-01** — **Finding**: Four modules exceed the project's two module-length
  limits; all four are waived. Measured with
  `critiques/pr-29a/measure_module_lines.py` over all 78 `.py` files under `src/`:
  `pdsfile.py` (2,469 total / 1,654 code), `_properties.py` (2,817 / 1,390),
  `holdings_maintenance/pds3/pdsdependency.py` (1,520 / 1,135) and
  `pds3file/rules/VG_28xx.py` (1,117 / 1,020); the other 74 files pass both
  limits. **Evidence**: measurement output; `pdsfile_overrides.mdc` deviation (3)
  enumerates exactly these four with issues #141-#144. **Suggestion**: none —
  waived by pdsfile_overrides.mdc deviation (3); the observation matches the
  recorded waiver list exactly, so the tree and the record agree.
  **Severity**: low.

- **CA-02** — **Finding**: The pds3/pds4 halves of two maintenance-tool pairs
  remain near-identical after the shared-core consolidation. A mechanical diff
  (rename `pds4`->`pds3`, `bundle`->`volume`) leaves 242 differing lines of 2,032
  total for `pdschecksums.py`/`pds4checksums.py` and 209 of 2,171 for
  `pdsinfoshelf.py`/`pds4infoshelf.py` (~90% identical modulo vocabulary); the
  link shelf pair differs more (368 of 1,278) and the archives pair most (558 of
  1,118). **Evidence**:
  `src/pdsfile/holdings_maintenance/pds3/pdschecksums.py`,
  `src/pdsfile/holdings_maintenance/pds4/pds4checksums.py`, and siblings; diff
  counts in the appendix. **Suggestion**: consider measuring a further
  consolidation of the checksum and info-shelf pairs into their `_shelf_common.py`
  family, on the same measure-first terms the existing consolidation used. The
  residual may be the measured stopping point of that work; if it was, recording
  that in the module docstrings would close the question. **Severity**: medium.

- **CA-03** — **Finding**: `run_tests_coverage.sh` at the repository root is
  tracked but cannot run: it invokes `pytest pdsfile/pds3file/tests/ ...`, paths
  that no longer exist (no `pdsfile/` directory at the root), and uses `exit -1`.
  The dev guide annotates it "names test paths that no longer exist; do not use",
  and the breakage is recorded as deferred observation 16. **Evidence**:
  `/seti/all_repos/rms-pdsfile/run_tests_coverage.sh` lines 4-16;
  `docs/dev_guide/dev_guide_repository_layout.rst:73`;
  `critiques/deferred-observations.md` item 16. **Suggestion**: delete the script
  in the root-scripts cleanup that owns it; a tracked, documented-broken script
  still costs every new reader the time to learn it is dead. **Severity**: low.

## 2. Best practices alignment

- **CA-04** — **Finding**: Eight text-mode `open()` calls pass no `encoding=`,
  so they read or write in the platform default encoding
  (`.cursor/rules/python.mdc` and the skill both require explicit encoding in
  library code). AST-measured over `src/`: `_shelves.py:475`,
  `pds3/pdschecksums.py:318` and `:469`, `pds3/re_validate.py:367` and `:463`,
  `pds4/pds4checksums.py:324` and `:471`, `pds4/pds4linkshelf.py:245`. All other
  `open()` sites are binary-mode or already pass `encoding=`. **Evidence**: AST
  sweep in the appendix. **Suggestion**: add `encoding='utf-8'` (or the encoding
  the sidecar format actually is) to these eight sites. The change is
  behavior-preserving on the Linux/macOS platforms the package supports and does
  not touch the ratcheted `SIM115` spelling of the two bare-`open` sites.
  **Severity**: medium.

- **CA-05** — **Finding**: The library defines no custom exception hierarchy;
  errors surface as `OSError`/`ValueError` with good contextual messages (e.g.
  `_shelves.py` raises `OSError(f'Pickle file not found: {shelf_path}')`).
  **Evidence**: `src/pdsfile/_shelves.py:338`, `src/pdsfile/_index_rows.py:125`.
  **Suggestion**: none — waived by pdsfile_overrides.mdc deviation (2): the raise
  types are documented behavior of the frozen public surface, and introducing a
  `PdsFileError` base would change what callers catch. The messages themselves
  already meet the error-message-quality bar. **Severity**: low.

- **CA-06** — **Finding**: Path handling uses `os.path` string manipulation
  throughout rather than `pathlib.Path`. **Evidence**: `src/pdsfile/_path_utils.py`
  and pervasive `os.path.join`/`os.path.split` usage. **Suggestion**: none —
  waived by pdsfile_overrides.mdc deviation (5): plain `os.path` handling stays,
  and `filecache.mdc` is deliberately absent from this repository's rules.
  **Severity**: low.

- **CA-07** — **Finding**: Library hygiene is clean where the rules require it.
  Grep sweeps found zero `print()` and zero `sys.exit()` in the core library
  (`src/pdsfile/*.py` and both `pds{3,4}file` subpackages); the 39 `print()` sites
  in `holdings_maintenance/` and 19 in `tools/` are CLI programs, and the 69
  `sys.exit()` sites are all in those CLI trees. No bare `except:` exists anywhere
  in `src/`, `tests/` or `scripts/`; the nine `except Exception` sites are narrow
  and either re-raise, log, or convert with context. **Evidence**: sweeps in the
  appendix. **Suggestion**: none; `holdings_maintenance/` console output is
  waived frozen behavior per pdsfile_overrides.mdc deviation (9), and the rest
  complies with `python.mdc` and `logging.mdc` as written. **Severity**: low.

- **CA-08** — **Finding**: `re_validate.py` hard-codes its mail relay and sender
  (`SERVER = 'list.seti.org'`, `FROM_ADDR = "PDS Administrator
  <pds-admin@seti.org>"`). These are module-level constants, so `python.mdc`'s
  magic-constant rule is met structurally, but a Node deployment on a different
  relay must edit source. **Evidence**:
  `src/pdsfile/holdings_maintenance/pds3/re_validate.py:105-106`. **Suggestion**:
  consider environment-variable overrides with these values as defaults; the
  module's freeze was lifted (deviation (6), 2026-08-05), so this is legal to
  change under the normal gates. **Severity**: low.

## 3. Types and static checks

- **CA-09** — **Finding**: No inline type annotations and no mypy type-checking
  of the implementation. **Evidence**: absence of annotations across `src/`;
  `ENABLE_MYPY=false` in `scripts/run-all-checks.sh:134`. **Suggestion**: none —
  waived by pdsfile_overrides.mdc deviation (1), permanently. The compensating
  machinery is in place and enforced: 43 hand-written `.pyi` stubs under
  `src/pdsfile/`, a `py.typed` marker, and a `mypy.stubtest` gate
  (`run-all-checks.sh:583-596`) that validates the stubs against the runtime
  surface on every full check run. **Severity**: low.

- **CA-10** — **Finding**: The lint gates pass clean as configured. This session
  ran both: `ruff check src/pdsfile tests scripts docs` exits 0, and the separate
  indentation pass `ruff check --preview --select E111,E112,E113 src/pdsfile
  tests scripts` exits 0 with no per-file exemption. The per-file-ignores ratchet
  in `pyproject.toml` is the enumerated permanent set of deviation (4)
  (`RUF005` repo-wide style, frozen names, hand-aligned tables); `ruff format` is
  never enforced per deviation (11). **Evidence**: command output; `pyproject.toml`
  lines 212-345. **Suggestion**: none; the observed state matches the recorded
  decisions. **Severity**: low.

- **CA-11** — **Finding**: The development venv now carries ruff 0.15.22, while
  `pdsfile_overrides.mdc` deviation (12) records the preview-rule indentation gate
  as verified under 0.15.7 and 0.16.1. The gate passes under 0.15.22 as measured
  in this session, so nothing is broken; the record's verified-version list is
  simply behind the venv. **Evidence**: `pip list` (ruff 0.15.22); clean E111/E112/
  E113 run above; `pdsfile_overrides.mdc` deviation (12). **Suggestion**: optional:
  when deviation (12) is next edited, refresh the verified-version note, since a
  preview rule's behavior may change between releases (the record's own reasoning).
  **Severity**: low.

## 4. Testing

This dimension is deliberately brief: a dedicated critique-test-suite report is
being produced in parallel and owns test quality, assertions, and gaps. Structure
and configuration only here.

- **CA-12** — **Finding**: Test structure and configuration follow
  `python_testing.mdc` where not deliberately deviated. `tests/` mirrors the
  package (`api/`, `core/`, `docs/`, `golden/`, `holdings_maintenance/`,
  `pds3file/`, `pds4file/`, `rules/pds{3,4}/`, `support/`), with 60 `test_*.py`
  files, 627 test functions, and five `conftest.py` files at appropriate scopes.
  Pytest is configured in `pyproject.toml` with `--strict-markers`,
  `--strict-config`, and both custom markers registered. `addopts` carries no
  `-n`/`--cov` — waived by pdsfile_overrides.mdc deviation (7) (serial `--update`
  and full-data runs). Holdings selection is centralized in
  `tests/support/holdings.py` with graceful full/mini/none resolution.
  **Evidence**: `pyproject.toml:109-121`; `tests/` listing; `tests/conftest.py`.
  **Suggestion**: none at this level; see the dedicated test-suite critique for
  depth. **Severity**: low.

- **CA-13** — **Finding**: Line-plus-branch coverage over the full suite (the
  `ns` pass plus both `--mode s` passes, one combined data file)
  is 58% (9,715 statements, 3,704 missed), against `python_testing.mdc`'s 90%
  target, and nothing enforces any floor: `[tool.coverage.report]` has no
  `fail_under` (the header comment in `run-all-checks.sh:51-52` explicitly points
  at configuring one) and `codecov.yml` marks both project and patch status
  `informational: true`. The distribution is sharply bimodal: every rule module
  measures 100%, the core mixins run 76-91% (`_properties.py` 89%, `pdsfile.py`
  87%, `_local_fs.py` 91%), but the maintenance-tool drivers sit at 6-30%
  (`pds4linkshelf.py` 6%, `_indexshelf_common.py` 8%, `pdslinkshelf.py` 8%,
  `pdsarchives.py` 13%, `_linkshelf_common.py` 14%) with `re_validate.py` (88%)
  and `crlf.py` (98%) the exceptions, and `pdscache.py` measures 27% — much of
  that is `MemcachedCache`, which plan ground rule 9 protects from removal and
  whose test gap register entry 4207 holds open (one stub-tested method; owner
  phase b of issue #77). **Evidence**: coordinator-run coverage
  summary (appendix); `pyproject.toml:133-136`; `codecov.yml`. **Suggestion**:
  the highest-leverage testing investment is the maintenance-tool task functions
  and the `_linkshelf_common`/`_indexshelf_common` drivers, which mutate holdings
  sidecars and are the least covered code in the package; and take the deferred
  decision on a coverage floor (`fail_under`) once a target is agreed, so the
  number cannot silently regress. The `MemcachedCache` share of the gap is
  recorded and excluded from this suggestion. **Severity**: high.

- **CA-14** — **Finding**: `filterwarnings = ["error", ...]` is not configured;
  `python_testing.mdc` section 4 asks that warnings be treated as errors with
  narrow ignores. No deviation covers this. **Evidence**: `pyproject.toml`
  `[tool.pytest.ini_options]` (no `filterwarnings` key). **Suggestion**: consider
  enabling warnings-as-errors and adding scoped ignores for third-party warnings;
  measure first against the full-data run, since a large dependency surface
  (numpy, pillow, pdstable) may emit warnings the suite would newly fail on.
  **Severity**: low.

## 5. Performance and resource use

- **CA-15** — **Finding**: The caching design is coherent and bounded. The shelf
  cache is LRU-bounded (`SHELF_CACHE_SIZE = 120`, `SHELF_CACHE_SLOP = 20`,
  `pdsfile.py:2416-2417`) with explicit eviction (`_shelves.py:363-369`);
  filesystem existence and glob answers are memoized with
  `functools.lru_cache` (`_local_fs.py:112`, `_path_utils.py:177`); the preload
  walks the stable top of the tree once and stops at the bundle
  (`_preload.py` module docstring). Info-shelf null-key values are cached
  separately to avoid reopening shelves for bundle-level questions
  (`_shelves.py:355-357`). **Evidence**: cited lines. **Suggestion**: none; this
  matches the skill's caching expectations. **Severity**: low.

- **CA-16** — **Finding**: Class-level mutable state is pervasive and unlocked
  (object cache, shelf cache and access stamps, memoized caches,
  `LOCAL_PRELOADED`, the icon registry `ICON_SET_BY_TYPE` in `pdsviewable.py:781`),
  and the thread-safety posture is explicitly documented: "Thread safety is a
  single-process, single-thread assumption... None of it is locked"
  (`docs/dev_guide/dev_guide_subsystems.rst:57-63`), with cross-process sharing
  delegated to `MemcachedCache`. **Evidence**: cited doc and sites. **Suggestion**:
  none — the skill asks that the library document its thread-safety guarantees or
  lack thereof, and it does. Introducing locking or a dependency-injected cache
  manager would contradict plan §2 ground rule 2 (mechanical decomposition only)
  and is not suggested. **Severity**: low.

- **CA-17** — **Finding**: `MemcachedCache` carries documented behavioral traps:
  `delete_multi()` raises `AttributeError` on it, a constant default lifetime of
  zero raises `TypeError` on either class, and lifetimes below 0.001 are dropped
  by `int(x + 0.999)`. All are stated plainly in the `pdscache.py` module
  docstring rather than smoothed over. **Evidence**: `src/pdsfile/pdscache.py`
  module docstring (lines 24-52). **Suggestion**: none — plan ground rule 9 keeps
  `MemcachedCache`/pylibmc support as-is, and the documentation-first treatment is
  the right disposition under that rule; the ratchet already records the two
  lint findings inside it (deviation (4)). **Severity**: low.

## 6. Maintainability and extensibility

- **CA-18** — **Finding**: The architecture is unusually legible for its size.
  The `PdsFile` class is decomposed into nine stateless mixins plus a path-helper
  module, with the module map, the mixin mechanics (no `__init__`, no back-import,
  alphabetical bases) and the enforcement tests named in the `pdsfile.py` module
  docstring; the ten maintenance tools share one `ToolSpec` dataclass and three
  drivers, and `_common.py` documents every spec field's actual readers, module by
  module. Mixin discipline is machine-checked (`tests/api/test_mixin_collisions.py`,
  `tests/api/test_mixin_import_isolation.py`, per the docstring and `tests/api/`
  listing). Extending the system follows documented recipes
  (`docs/dev_guide/dev_guide_extending_rules.rst`, `dev_guide_extending_tools.rst`).
  **Evidence**: `src/pdsfile/pdsfile.py:1-110`;
  `src/pdsfile/holdings_maintenance/_common.py:89-263`. **Suggestion**: none.
  **Severity**: low.

- **CA-19** — **Finding**: Documentation machinery exceeds the template's bar.
  Sphinx builds run under both `-W` and `-n -W` with the build verdict actually
  read (HTML produced, module-coverage line printed and compared between builds,
  `run-all-checks.sh:630-754`); `docs/api/*.rst` carries 77 `automodule`
  directives across core, subpackages, maintenance and tools; and a dedicated
  docstring gate (`tests/docs/test_docstrings.py`) catches signature drift that a
  clean Sphinx build cannot. Per-tool user guides exist for all eleven console
  scripts plus the shell scripts and `show_opus_products`. **Evidence**: cited
  files; `docs/` listing. **Suggestion**: none. README examples were not executed
  in this session (unverified) — the docstring and Sphinx gates cover the API
  reference, not README code blocks. **Severity**: low.

## 7. Security and robustness

- **CA-20** — **Finding**: The shelf subsystem executes and deserializes content
  from the holdings tree: `_read_info_shelf_line()` evaluates a sidecar line with
  `eval()` (`_shelves.py:97`), and five sites `pickle.load()` shelf files
  (`_shelves.py:341`, `_indexshelf_common.py:299`, `_linkshelf_common.py:477`,
  `pdsinfoshelf.py:423`, `pds4infoshelf.py:432`). A hostile or corrupted holdings
  tree therefore implies arbitrary code execution in any process that reads it.
  The trust boundary is documented exactly there: "the sidecar is executable
  input, and the trust boundary is the holdings tree, whose sidecars are written
  by this package's own maintenance tools" (`_shelves.py:63-76`). **Evidence**:
  cited lines. **Suggestion**: the pickle format is the frozen shelf format and is
  not actionable here; for the sidecar, consider `ast.literal_eval()` — the
  records the tools write are tuples of literals, so it is a drop-in for every
  well-formed record — but note the documented `Raises:` contract (SyntaxError,
  NameError) would change to ValueError on malformed input, which is a documented-
  behavior change needing an owner decision, not a style fix. **Severity**: medium.

- **CA-21** — **Finding**: No automated dependency vulnerability scanning exists:
  there is no `.github/dependabot.yml`, no `pip-audit` gate in
  `run-all-checks.sh` (its enabled set is ruff-check, pytest, pyroma, api-freeze,
  clean-install, stubtest, sphinx, pymarkdown), and none in CI. `security.mdc`
  section 2 and `dependency_management.mdc` section 5 both require it.
  `ENABLE_BANDIT=false` is a recorded owner decision and is not the subject here;
  dependency auditing is a separate check no recorded deviation covers.
  **Evidence**: `.github/` listing; `run-all-checks.sh:126-143`. **Suggestion**:
  add a Dependabot config, or add a `pip-audit` gate — per `environment.mdc`, add
  it to `run-all-checks.sh` first and bring CI into step in the same change.
  **Severity**: medium.

- **CA-22** — **Finding**: `re_validate.py` mails reports over an unauthenticated,
  unencrypted SMTP session to a fixed internal relay on port 25, documented as
  such ("which is what an internal mail relay accepts"). No credentials are
  involved and nothing sensitive beyond validation summaries is sent.
  **Evidence**: `src/pdsfile/holdings_maintenance/pds3/re_validate.py:747-778`.
  **Suggestion**: acceptable for an internal batch tool; if the relay ever moves
  outside the trust boundary, revisit together with CA-08. **Severity**: low.

- **CA-23** — **Finding**: The remaining security sweeps are clean: zero
  `shell=True` in `src/`, `tests/` and `scripts/`; `subprocess` is used with list
  arguments in tests and scripts only (plus the two checksum tools); no
  credentials or secrets found in code or config; `.env` is gitignored
  (`.gitignore:128`); and path input is validated at the boundary —
  `from_abspath()` raises for an existing path outside any holdings tree
  (documented in `_common.py:522-524`). **Evidence**: sweeps in the appendix.
  **Suggestion**: none. **Severity**: low.

## 8. Dependencies and tooling

- **CA-24** — **Finding**: Seven of the eight runtime dependencies declare no
  minimum version: `numpy`, `pillow`, `pyparsing`, `range_ex`, `rms-pdstable`,
  `rms-translator`, `rms-textkernel` are all unbounded; only
  `rms-pdslogger>=3.1.1` has a floor. `dependency_management.mdc` section 3 and
  `security.mdc` section 2 both require minimum compatible versions for direct
  dependencies. No recorded deviation covers this. **Evidence**:
  `pyproject.toml:11-25`. **Suggestion**: add minimums matching what the package
  actually needs (the versions the CI venvs resolve today are a defensible floor:
  numpy 2.4.2, pillow 12.1.0, pyparsing 3.3.2 per `pip list`); this is a
  `build:` change with no code impact. **Severity**: medium.

- **CA-25** — **Finding**: Tooling configuration is consistent and single-sourced.
  `pyproject.toml` is the only dependency declaration (`requirements.txt` is
  `-e .` as the rule prescribes); pytest, coverage, ruff, pymarkdown and the
  stubtest-only mypy config all live in `pyproject.toml`; the CI hosted job runs
  `scripts/run-all-checks.sh` itself so the gate set cannot drift, and the
  self-hosted job's extra coverage-plus-`--mode s` driver is recorded in
  pdsfile_overrides.mdc deviation (8); the CI matrix (3.11/3.12/3.13 self-hosted,
  3.11/3.13 hosted) is consistent with `requires-python = ">=3.11"`. The inert
  `[tool.ruff.format]` section is recorded harmless by deviation (11); the
  `[tool.mypy]` section documents itself as stubtest-only. Dev extras pin useful
  floors (`ruff>=0.8`, `mypy>=1.14`, `pytest>=7.0`). **Evidence**:
  `pyproject.toml`; `.github/workflows/run-tests.yml`; `run-all-checks.sh`.
  **Suggestion**: none. **Severity**: low.

## 9. Technical debt and risk

- **CA-26** — **Finding**: 13 TODO/FIXME comments exist across `src/` and
  `tests/`, none linked to a GitHub issue. Most are of one family — work blocked
  on holdings content not yet published (the
  `cassini_iss_fring_mosaics_rsfrench2025` bundle, missing previews/index
  shelves) — plus `pds4file/rules/__init__.py:4` ("all variables have placeholder
  values" for the pds4 general rules) and one self-described hack:
  `_properties.py:629` "XXX This is a real hack and should be looked at again
  later". **Evidence**: grep in the appendix. **Suggestion**: link each TODO to an
  issue or fold the blocked-on-data family into one tracking issue; the
  `_properties.py:629` hack in particular deserves an issue so it is a decision
  to defer rather than a comment to forget (`python.mdc` section 4 pattern).
  **Severity**: low.

- **CA-27** — **Finding**: `FOEVER_FILE_CACHE_LIFETIME` (missing "R") is a typo
  in a public constant name, re-exported through `preload_and_cache.py`, stubbed
  in `preload_and_cache.pyi:15`, and present in `tests/api/api_manifest.json`.
  **Evidence**: `src/pdsfile/_preload.py:100`;
  `tests/api/api_manifest.json:30266`. **Suggestion**: none — waived by
  pdsfile_overrides.mdc deviation (2): the name is part of the frozen surface and
  must not be renamed. Recorded here so the observation is not re-made.
  **Severity**: low.

- **CA-28** — **Finding**: Known debt is enumerated rather than latent: the four
  over-limit modules each carry an issue (#141-#144), the ruff ratchet is
  shrink-only with every permanent entry justified in deviation (4), and the
  frozen sync scripts and deferred splits are all recorded with owners and dates.
  No deprecated stdlib or third-party API usage surfaced in the sweeps run this
  session (unverified beyond those sweeps). **Evidence**:
  `pdsfile_overrides.mdc`; `pyproject.toml` ratchet comments. **Suggestion**:
  none; this is what managed debt looks like. **Severity**: low.

## 10. Packaging and distribution

- **CA-29** — **Finding**: Packaging is in excellent shape. `pyroma .` scores
  10/10. A wheel built this session contains 141 files (2.4 MB): the `py.typed`
  marker, all 43 `.pyi` stubs, no tests, no build artifacts. Eleven console
  scripts are declared for the maintenance tools. Version is single-sourced from
  `setuptools_scm` (`write_to = "src/pdsfile/_version.py"`, gitignored) with a
  clean fallback in `__init__.py`. `[project.urls]` carries Homepage,
  Documentation, Repository, Source and Issues; classifiers match the supported
  platforms (Linux, macOS; Windows deliberately absent per deviation (8)).
  **Evidence**: pyroma output; wheel listing in the appendix;
  `pyproject.toml:49-103`. **Suggestion**: none. **Severity**: low.

- **CA-30** — **Finding**: The license is declared as
  `license = {text = "Apache-2.0"}` (the pre-PEP 639 table form) alongside the
  `License :: OSI Approved :: Apache Software License` classifier, rather than
  the PEP 639 SPDX expression form (`license = "Apache-2.0"` plus
  `license-files`). **Evidence**: `pyproject.toml:26,41`. **Suggestion**:
  optional: migrate to the SPDX expression form when setuptools floors allow;
  purely a metadata modernization, and pyroma already scores the current form
  10/10. **Severity**: low.

- **CA-31** — **Finding**: `src/pdsfile/tools/show_opus_products.py` ships in the
  wheel but imports `tabulate` unconditionally at module level
  (`show_opus_products.py:32`), and `tabulate` is dev-only, so on a clean
  runtime install `python -m pdsfile.tools.show_opus_products` fails with
  ImportError. This is a recorded decision: the `pyproject.toml` dev-extra
  comment states the tool "stays a `python -m` tool (not a shipped console
  script), so tabulate is dev-only", and
  `docs/user_guide/user_guide_show_opus_products.rst:16-24` tells users it needs
  the dev extra. The clean-install gate covers the frozen public module set, not
  `pdsfile.tools`. **Evidence**: cited lines. **Suggestion**: none required — the
  behavior and its rationale are recorded and documented; if the failure mode
  ever bites, `python.mdc`'s inline-import exception for optional dependencies
  would permit a guarded import with a pointed error message. **Severity**: low.

- **CA-32** — **Finding**: The twelve `pds3` sync/copy/setup shell scripts ship
  inside the wheel (verified in the wheel listing). **Evidence**: wheel contents;
  `src/pdsfile/holdings_maintenance/pds3/*.sh`. **Suggestion**: none — the
  scripts are frozen document-only per pdsfile_overrides.mdc deviation (6), are
  documented in `docs/user_guide/user_guide_shell_scripts.rst`, and shipping them
  with the package that documents them is coherent. **Severity**: low.

## Recommended priorities

1. **Maintenance-tool test coverage (CA-13, high).** The drivers that rewrite
   holdings sidecars are the least-tested code in the package (6-30%); raising
   them dominates any other quality investment, and a `fail_under` decision
   should follow so the total (58%) cannot drift down silently.
2. **Dependency floors and audit tooling (CA-24 + CA-21, medium).** Add minimum
   versions for the seven unbounded runtime dependencies and stand up
   Dependabot or a `pip-audit` gate (script first, CI in step). Both are
   low-effort `build:`/`ci:` changes with no code impact.
3. **Explicit encodings (CA-04, medium).** Eight text-mode `open()` sites; a
   small, behavior-preserving sweep.
4. **Sidecar `eval` disposition (CA-20, medium).** Take an owner decision on
   `ast.literal_eval` for the info-shelf sidecar parser, or record keeping
   `eval` as the accepted trade so the observation is closed.
5. **Tool-pair consolidation measurement (CA-02, medium).** Measure whether the
   ~90%-identical checksum and info-shelf pair bodies have a shared-core
   remainder worth taking, on the same terms as the existing consolidation.
6. **Housekeeping (CA-03, CA-14, CA-26, low).** Delete `run_tests_coverage.sh`,
   evaluate `filterwarnings = ["error"]`, and give the 13 TODOs issue numbers.

## Severity tally

- Critical: 0
- High: 1 (CA-13)
- Medium: 5 (CA-02, CA-04, CA-20, CA-21, CA-24)
- Low: 26 (all others, including the waived observations CA-01, CA-05, CA-06,
  CA-09, CA-27, CA-31, CA-32)

## Appendix: Commands run

All commands from `/seti/all_repos/rms-pdsfile` with `source venv/bin/activate`.

- Tree identity: `git log -1 --format='%h %s'` (6525951), `git status -sb`.
- Lint gates: `python -m ruff check src/pdsfile tests scripts docs` (exit 0);
  `python -m ruff check --preview --select E111,E112,E113 src/pdsfile tests
  scripts` (exit 0).
- Module lengths: `python critiques/pr-29a/measure_module_lines.py $(find src
  -name '*.py' | sort)` — "4 of 78 files are over a limit", per-file numbers in
  CA-01.
- Line counts: `wc -l` over `src/pdsfile/*.py` and the `holdings_maintenance`
  trees; `find src -name '*.py' | xargs wc -l` (44,094 total); `find tests -name
  '*.py' | xargs wc -l` (18,765); `find src -name '*.py' | wc -l` (78);
  `find tests -name '*.py' | wc -l` (84); `find src -name '*.pyi' | wc -l` (43);
  rule-module counts `ls src/pdsfile/pds{3,4}file/rules/*.py | wc -l` (26 + 10).
- Hygiene sweeps: `grep -rn 'print('` by directory (core 0, subpackages 0,
  holdings_maintenance 39, tools 19); `grep -rn 'sys\.exit'` (core 0,
  maintenance+tools 69); `grep -rn -E 'except *:'` (0); `grep -rn 'except
  Exception'` (9 sites, listed); `grep -rn 'shell=True'` (0); `grep -rn -E
  '\beval\(|\bexec\('` (one code site, `_shelves.py:97`); `grep -rln 'import
  subprocess'` (12 files, tests/scripts/checksum tools); pickle sweep (5
  `pickle.load` sites).
- Encoding: AST walk over `src/**/*.py` counting text-mode `open()` calls
  without `encoding=` (8 sites, listed in CA-04).
- Module-level mutable state: `grep -rn -E '^[A-Za-z_]\w* *= *(\{\}|\[\]|...)'`
  over `src/pdsfile` (22 sites: tool LIMITS dicts, `LOGDIRS`,
  `ICON_SET_BY_TYPE`, rule-module tables).
- TODO/FIXME: `grep -rn -E '#.*\b(TODO|FIXME)\b' src/pdsfile tests scripts`
  (13); XXX inspection filtered for the `RPX/xxxx` false positives.
- Duplication: `diff <(sed 's/pds4/pds3/g;s/bundle/volume/g' pds4/<tool>.py)
  pds3/<tool>.py | grep -c '^[<>]'` for the four pairs (numbers in CA-02).
- Tests: `grep -c 'def test_'` summed over `find tests -name 'test_*.py'` (627
  functions, 60 files); `find tests -name conftest.py` (5).
- Coverage: coordinator-run summary at the session scratchpad
  `coverage-summary.txt` (total 58%, 9,715 stmts / 3,704 miss, branch on);
  per-module figures quoted in CA-13.
- Dependencies: `pip list` (101 packages; versions quoted in CA-11, CA-24).
- Packaging: `python -m pyroma .` (10/10); `python -m build --wheel` into the
  session scratchpad, then `unzip -l` (141 files; `py.typed`, 43 `.pyi`, 12
  `.sh`, no tests); `git status --porcelain` clean before and after.
- Config reads: `pyproject.toml`, `scripts/run-all-checks.sh`,
  `.github/workflows/run-tests.yml`, `codecov.yml`, `.gitignore` (`.env` at
  line 128), `requirements.txt` (`-e .`), `.vscode/settings.json` (present).
- Reference checks: `grep -rn 'run_tests_coverage'` (dev-guide "do not use"
  annotation, deferred observation 16, no workflow reference); `grep -rn
  'FOEVER'` (manifest line 30266); `grep -n 'automodule' docs/api/*.rst`
  (77 total); `grep -n 'thread' docs/dev_guide/dev_guide_subsystems.rst`.
