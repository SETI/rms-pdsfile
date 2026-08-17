# Test Suite Critique Report

**Generated:** 2026-08-16
**Scope:** tests/ (and every conftest.py), at tree commit 6525951 (branch
identical to `rewrite`)
**Standards cited:** `.cursor/rules/python_testing.mdc` (primary),
`.cursor/rules/python.mdc`, `.cursor/rules/logging.mdc`, with
`.cursor/rules/pdsfile_overrides.mdc` taking precedence where they conflict.
`logging_nav.mdc` and `filecache.mdc` do not exist in this repository, so the
checks that depend on them are skipped per the skill's instructions.

**What was read.** All five conftest.py files (tests/, tests/api/, tests/core/,
tests/docs/, tests/holdings_maintenance/), all support modules
(tests/support/holdings.py, tests/support/pdsfile_test_helper.py,
tests/core/support.py, tests/rules/support.py, tests/holdings_maintenance/
support.py, subsets.py, readonly_roots.py, _subprocess_guard/sitecustomize.py,
tests/pds3file/helper.py, tests/pds4file/helper.py), tests/rules/README.md, and
`pyproject.toml`'s `[tool.pytest.ini_options]` and `[tool.coverage.*]` were read
in full. Read fully: every file under tests/api/, tests/core/, tests/docs/
(check_docstrings.py sampled to its rule list, lines 1-70), all 24 test modules
under tests/holdings_maintenance/, tests/pds3file/test_pdsviewable_blackbox.py,
tests/pds4file/test_pds4file_bundleset_plus.py, tests/rules/pds3/test_vg_28xx.py
and tests/rules/pds4/test_uranus_occs_earthbased.py and
test_cassini_iss_fring_mosaics_rsfrench2025.py. Sampled systematically (contiguous
excerpts plus a `grep` of every `def test_`, `class Test`, `except`, `raises`,
`skip`, `xfail`, `assert False` and `monkeypatch` line): tests/pds3file/
test_pds3file_blackbox.py (lines 1-400, 900-1059, 1892-1952),
test_pds3file_blackbox_cached.py (lines 1-200), test_pds3file_whitebox.py (lines
300-530, 895-927), tests/pds4file/test_pds4file_blackbox.py (lines 1-140,
700-770), tests/rules/pds3/test_coiss_xxxx.py (lines 1-80),
test_corss_8xxx.py (lines 1-120), test_go_0xxx.py (test_duplicated_products
excerpt); the remaining rule-test modules were surveyed by the same grep, which
shows they carry the uniform three-test shape the README documents.

## Executive summary

The suite is two suites in one tree. The newer tiers — tests/api/, tests/core/,
tests/docs/, tests/holdings_maintenance/, tests/pds4file/
test_pds4file_bundleset_plus.py — are exemplary: descriptive names, docstrings
that say why a case exists (often citing a numbered observation), exact-value
assertions, `pytest.raises(..., match=)`, negative controls for vacuity, a
read-only-holdings guard that reaches tool subprocesses, and disposable
fingerprint-verified holdings subsets. The legacy tiers — the pds3file
blackbox/whitebox/cached files and most of tests/rules/ — predate the rewrite
and carry the classic defects: a vacuous `list.sort()` comparison (TS-01),
try/except blocks that pass when the expected exception is never raised (TS-05),
a test that is vacuous in the default `--mode ns` session (TS-06), duplicate
parametrize rows (TS-11), and golden helpers that silently create a missing
golden instead of failing (TS-15).

- **Coverage:** Measured over the entire suite (ns pass + both s passes,
  serial, real holdings, branch coverage, `source=pdsfile`): **58% total**
  (9,715 statements, 3,704 missed). The 90% target of `python_testing.mdc` §9
  is **not met as measured**, but the headline number is dominated by a
  measurement blind spot: the eleven maintenance tools and show_opus_products
  are deliberately driven as subprocesses (for cache-isolation reasons the
  package header documents), and the coverage run does not instrument
  subprocesses, so tool modules with full task-cycle tests report 6-24%
  (TS-19, TS-20). Core `pdsfile` modules measure 76-91%.
- **Exception messages:** the modern tiers assert message content via `match=`
  or substring checks on the raised value; the legacy blackbox/whitebox files
  contain seven try/except tests that assert content only when the exception
  happens to be raised and pass silently otherwise (TS-05).
- **High priority:** TS-01, TS-05, TS-06, TS-15 (vacuous or silently-passing
  assertions), TS-17 (no `filterwarnings`), TS-20 (subprocess coverage blind
  spot). **Nice to have:** naming/DRY consistency (TS-07, TS-08), parametrize
  conversions (TS-14), testpaths (TS-21), docstring coverage of legacy tests
  (TS-18 context).
- **Waived items** are marked inline: real-holdings dependence (locked owner
  decision, modernization plan §2 ground rule 3 and §6.6), no `-n`/`--cov` in
  addopts (pdsfile_overrides.mdc deviation 7), the PT017/PT015/B011/PT012/PT014
  ruff-locked test shapes (deviation 4), and MemcachedCache's untested body
  (deviation 4's pdscache row, ground rule 9).

## 1. Return values and assertions

The modern tiers assert exact values and shapes throughout (e.g.
tests/core/test_pdsfile_path_resolution.py::test_each_class_names_its_own_holdings_variable
compares a whole dict; tests/holdings_maintenance/test_pds3_checksums.py
::test_initialize_writes_the_expected_checksum_file checks every declared md5
and the exact mapping length). Findings are concentrated in the legacy files:

**TS-01** — Vacuous content comparison via `list.sort()`.
tests/pds3file/test_pds3file_blackbox.py:110:
`assert res.sort() == expected.sort()` — `list.sort()` returns `None`, so this
asserts `None == None` and always passes. Only the preceding `len` check (line
109) does any work; the 116-entry COISS_2xxx listing above it is never actually
compared. Violates `python_testing.mdc` §7 ("assert precise expected values").

**TS-02** — Subset-only assertions where equality is known.
tests/pds3file/test_pds3file_blackbox_cached.py:123-131 (`test_childnames`)
checks `expected ⊆ res1` and `res1 ⊆ res2` but never `res1 == expected` nor an
exact length, so extra children would pass. Compare with the blackbox
`test_viewset_lookup` (tests/pds3file/test_pds3file_whitebox.py:377-388), which
checks only that each viewable's URL is in the expected list, not that all
expected URLs appear.

**TS-03** — A test with no expected value at all.
tests/pds3file/test_pds3file_blackbox_cached.py:142-147 (`test__info`) asserts
only `res1 == res2` (the cache-stability half) and nothing about what `_info`
contains. `python_testing.mdc` §7: "NEVER write a test whose only purpose is to
execute a code path without asserting on the result." The sibling tests in the
same file (test_date, test_formatted_size) show the intended shape: expected
value plus stability.

**TS-04** — Dead recompute-the-expected branches under `# pragma: no cover`.
tests/pds3file/test_pds3file_blackbox.py:227-228 (`test_absolute_or_logical_path`),
:255-262 (`test_extension`), :276-284 (`test_parent_logical_path`) each carry an
`if expected is None:` branch that re-derives the expected value from the input
with the same string logic as the implementation. No parametrize row passes
`None`, the branches are pragma-excluded, and if they ever ran they would test
the code against itself. They should be deleted.

## 2. Success and failure conditions

Success paths are well covered everywhere; the maintenance suite runs full
init -> validate -> corrupt -> validate -> repair -> validate cycles per tool,
and failure paths there are explicit (`run.error_lines`, exit codes, refusal
messages). The failure-path defects are in the legacy files:

**TS-05** — try/except tests that pass when nothing is raised.
Seven tests wrap the call in try/except and assert on the message only inside
the `except` clause, so if the code stops raising, the test silently passes:
- tests/pds3file/test_pds3file_whitebox.py:321-327
  (`test_data_set_id_exception` — no assertion at all outside the except)
- tests/pds3file/test_pds3file_whitebox.py:426-430 (`test_from_path2`)
- tests/pds3file/test_pds3file_whitebox.py:454-458
  (`test_from_opus_id_with_wrong_id`)
- tests/pds3file/test_pds3file_whitebox.py:519-524
  (`test_find_selected_row_key2`, OSError)
- tests/pds3file/test_pds3file_whitebox.py:549-556
  (`test_data_abspath_associated_with_index_row1`, OSError)
- tests/pds3file/test_pds3file_blackbox.py:902-908 (`test_from_abspath` —
  `except ValueError: assert True` also absorbs a raise for rows that were
  expected to succeed)
- tests/pds3file/test_pds3file_blackbox.py:1923-1928
  (`test_logical_path_from_abspath`, same shape)

Two further sites (`test_from_lid_mismatched_lid` :947-953 and
`test_from_lid_invalid_lid` :962-968) use `assert False` in the try arm and do
assert message content, so they cannot pass vacuously; their *shape* is the
PT017/PT015/B011 set recorded in pdsfile_overrides.mdc deviation (4) as
behavior-locked ruff entries. Note the interplay: deviation (4) forbids the
mechanical `pytest.raises` rewrite as a *style* change under the ratchet, but
the seven silently-passing tests above are a correctness defect, and fixing
them (adding `pytest.raises(..., match=)` or a `pytest.fail()` fall-through) is
a test-content change, not ruff cleanup. A fix PR should shrink, not widen, the
PT017 ratchet rows as a side effect.

**TS-06** — A test that is vacuous in the default session mode.
tests/pds3file/test_pds3file_whitebox.py:439-446 (`test_from_path3`) runs its
body only `if pds3file.Pds3File.SHELVES_ONLY:` and otherwise executes
`assert True`. In the default `--mode ns` pass (1,234 of the suite's passing
tests) it asserts nothing, and nothing in its name or reporting says so. It
should be split out with an explicit skip (`pytest.skip('shelves-only mode
only')`) so the vacuous pass is visible in the skip report, mirroring how the
other mode-dependent behavior is handled.

Edge cases: well represented in the modern tiers (empty file in test_crlf.py
:131-143, empty tree in test_pds4_checksums.py:216-239, blank manifest record,
unreadable directory, boundary mtimes in test_shelf_common.py:49-117).

## 3. Consistency

**TS-07** — Two naming generations coexist.
The modern tiers use sentence-style behavioral names
(`test_the_pin_is_released_when_the_block_raises`); the legacy tiers use
`test_<member>` with numeric suffixes for variants
(`test_associated_parallel1/2/3`, `test___repr__1/2`,
tests/pds3file/test_pds3file_whitebox.py:846-878, test_pds3file_blackbox.py
:835-840). The numeric-suffix names say nothing about which condition each
variant covers. Low priority; rename opportunistically when files are touched.

**TS-08** — Three copies of `instantiate_target_pdsfile`, two `--update` access
patterns. tests/support/pdsfile_test_helper.py:16 (takes `cls`),
tests/pds3file/helper.py:15 and tests/pds4file/helper.py:16 (bind their class
and holdings root; the pds4 copy also silently prepends `bundles/`). Same
concept, three signatures — `python.mdc` §2 DRY. Similarly, the rule tests read
`request.config.option.update` directly (tests/rules/pds3/test_vg_28xx.py:39)
while tests/holdings_maintenance/ uses the `golden_update` fixture
(conftest.py:86-90); one shared fixture would serve both.

Fixture and assertion style are otherwise consistent within each tier;
tests/holdings_maintenance/ in particular has a strong uniform structure
(module-level SOURCE_* declaration, `fresh_tree`, Corruption namedtuples).

## 4. Completeness

Coverage map by area (see section 18 for numbers):

- **Public API surface:** frozen and enforced (tests/api/test_api_freeze.py,
  manifest + allowlist), plus mixin-collision and import-isolation tests that
  guard the class-assembly blind spots the manifest cannot see. Strong.
- **Core class behavior:** properties and constructors are covered broadly by
  the blackbox/cached/whitebox files plus targeted core tests for caching,
  path resolution, shelves-only fallbacks, log-path time tags, sidecar records.
- **Maintenance tools:** every tool has a full task-cycle module; shared-core
  behaviors (versioning, task flags, naming, exception handling, limits) have
  dedicated modules.
- **Rule modules:** every pds3 rule with data in the reference tree has
  opus_products/associated_abspaths/opus-id-round-trip tests against goldens.

**TS-09** — A 31-test skip cluster is gated on TODOs that nothing will re-check.
tests/rules/pds4/test_cassini_iss_fring_mosaics_rsfrench2025.py:15 applies an
unconditional `pytestmark = pytest.mark.skip(...)` (7 skips);
tests/pds4file/test_pds4file_blackbox.py:732-735 and :957-962 skip 24 more
cases by substring test on the parametrize input. The ns run shows 34 skips, 31
of them from this cluster plus tests/rules/pds3/test_coiss_xxxx.py:55's 3
golden-content-conditional skips. All are annotated "when the bundle is
available, remove this skip" — but the skips are unconditional (or keyed to
golden text, not to the bundle's presence), so when the bundle does arrive the
tests stay skipped until someone remembers. Converting them to
`pytest.mark.skipif(not os.path.isdir(<bundle dir>), ...)` would make them
self-lifting. Related: tests/pds4file/test_pds4file_blackbox.py:31-60 and
tests/rules/pds4/test_uranus_occs_earthbased.py:41-62,77-111 carry large
commented-out case blocks (see TS-18).

**TS-10** — Untested non-exception code in core modules. From the term-missing
report: `pdsviewable.py` 64% (PdsViewable/PdsViewSet methods at 551-610,
633-641, 845-933 largely dark; only iconset_for and the four viewset-size
properties have dedicated tests), `_index_rows.py` 76% (120-131, 228-233,
521-527), `_associations.py` 77%, `_preload.py` 79% (579-604, 623-653: the
category-walk branches), `_opus.py` 81%. These are the highest-value targets
for new in-process tests. `pdscache.py` 27% is dominated by `MemcachedCache`
(770-1914), which no test environment can exercise — waived by
pdsfile_overrides.mdc deviation (4) (pdscache row: "ground rule 9 protects
MemcachedCache and no test here exercises it"); the DictionaryCache half is
covered.

Documentation alignment: tests/docs/ actively enforces docstring-to-code
agreement for src/, which is the reverse direction most suites never check.

## 5. Redundancy

**TS-11** — Duplicate case rows.
- tests/pds4file/test_pds4file_blackbox.py:138 duplicates the parametrize case
  at index 34 (`u0_kao_91cm_734nm_radius_six_ingress_100m.xml`, verified with
  `ruff --isolated --select PT014`). This is the PT014 ratchet row that
  pdsfile_overrides.mdc deviation (4) marks "a test-content PR owns it"
  (deferred observation 84) — report it here as that PR's work item, not as a
  ruff cleanup.
- tests/rules/pds3/test_coiss_xxxx.py:80-81: the same
  `W1294561143_1.IMG` logical path appears twice in
  `test_opus_id_to_primary_logical_path`'s case list.
- tests/rules/pds3/test_go_0xxx.py:329-332: two pairs in
  `test_duplicated_products`' table are exact duplicates of the row above them.
- tests/pds3file/test_pds3file_blackbox.py:115-169: the four `test_sort_*`
  tests each parametrize the *same* input path twice (True/False rows), which
  is intentional toggling, but the second row of each depends on the first
  having run against the same cached object (see TS-12).

Overlap between test_pds3file_blackbox.py and test_pds3file_blackbox_cached.py
is deliberate (first-fill vs cached-fill of the same properties) and is not
flagged, though the cached file's weaker assertions (TS-02, TS-03) mean the
overlap is not yet equivalence.

## 6. Parallel execution

The suite is serial by design: pdsfile_overrides.mdc deviation (7) records that
`addopts` deliberately carries no `-n`/xdist because `--update` runs and
full-data runs must be serial, so findings here are recorded, not actionable —
**waived by pdsfile_overrides.mdc deviation (7)** as to the default
configuration.

**TS-12** — Facts that make `pytest -n auto` unsafe today (recorded for anyone
tempted): the session-autouse `setup` fixture (tests/conftest.py:62-79)
preloads class-level caches shared by every test; `instantiate_target_pdsfile`
returns session-cached objects, and the blackbox `test_sort_*` tests mutate
`SORT_ORDER` on those cached instances (the setter copies to the instance, but
the instance itself lives in the session cache, so the last parametrize row's
value persists for any later reader); tests/pds3file/test_pds3file_whitebox.py
:920-922 (`test_from_abspath`) deletes entries from the live class CACHE.
Where isolation matters it is handled well: tests/core/conftest.py's
`pds3_cache` swaps in a throwaway cache, tests/holdings_maintenance drives
tools as subprocesses against per-module trees, and the read-only-roots guard
makes a stray write into real holdings a hard error in-process and in
subprocesses (tests/holdings_maintenance/conftest.py:93-123,
readonly_roots.py, _subprocess_guard/sitecustomize.py).

## 7. Mocking and dependency isolation

There is no `unittest.mock` anywhere in the tree (0 hits); everything uses
`monkeypatch` (15 files), stub classes, or subprocesses — internally consistent
and compliant with `python_testing.mdc` §5/§8. Time-sensitive logic is handled
properly: the `TickingClock` fixture (tests/core/test_log_path_timetag.py:42-63)
makes the one-second race deterministic instead of freezing time, with an
unpinned control case proving the clock is read where claimed. Patch targets
are correct and documented — see tests/core/test_pdsfile_path_resolution.py
:88-93, which patches `glob` through the function's own `__globals__` precisely
so the patch survives module moves.

Real-filesystem/holdings dependence: data-dependent tests deliberately use real
holdings resolved from PDS3_HOLDINGS_DIR/PDS4_HOLDINGS_DIR with no fixture tree
— **waived**: locked owner decision, modernization plan §2 ground rule 3, and
§6.6 places the hermetic aspects of python_testing.mdc out of scope. Env-var
handling inside tests is clean (monkeypatch.setenv/delenv; tmp roots).

**TS-13** — The stub-drift defense depends on a comment convention.
tests/core/test_stubbed_surfaces.py binds every fabricated PdsFile member
against the real class (excellent), but the registry of "where each stub
lives" (lines 61-66) is a comment, and nothing fails when a new test fabricates
a stub without adding a row. Acceptable residual risk; worth a line in the
contributing notes rather than machinery.

Mock return values: stubs consistently return realistic shapes (StubLogger's
`close_result=(7, 5, 3, 1)` chosen so positions are distinguishable,
test_re_validate.py:968-974); no bare-MagicMock hazards exist because MagicMock
is never used.

## 8. Security and input validation

No test data contains credentials; the one email-shaped constant is the tool's
own FROM_ADDR. Input validation of the CLIs is tested thoroughly
(tests/holdings_maintenance/test_crlf.py's argparse suite including
`allow_abbrev=False` protection at :268-281, test_task_flags.py,
test_copy_setup_scripts.py driving every guard). Path handling: the
read-only-roots guard is itself tested against symlink aliasing
(tests/holdings_maintenance/test_readonly_roots.py:86-100), which is the
path-traversal case that matters in this codebase. No findings.

## 9. Parameterization and data-driven tests

301 `@pytest.mark.parametrize` decorators across the tree; boundary values are
tested where they matter (crlf threshold at 0.05/0.5, modtime tolerance at
±0.999999/±1.0/±1.000001 in test_shelf_common.py:49-59).

**TS-14** — Table-driven loops that should be parametrized.
tests/rules/pds3/test_corss_8xxx.py:31-77 (`test_default_viewables`, 18 rows x
6 translators in one test) and :79-130 (`test_associations`, ~40 rows),
tests/rules/pds3/test_go_0xxx.py:314+ (`test_duplicated_products`),
tests/rules/pds3/test_vg_28xx.py:76-92 and every rule module's
`test_opus_id_to_primary_logical_path` loop over case lists inside a single
test body, so the first failing row hides all later rows and the reports carry
one test id for dozens of cases. `python_testing.mdc` §6. Mechanical to
convert; each case already carries a self-explanatory path id.

## 10. Async (if applicable)

Not applicable: the package and the suite contain no async code, no
`pytest_asyncio`, and no async fixtures. The one hang defense that matters —
tool subprocesses — carries explicit timeouts (support.py TOOL_TIMEOUT=600,
and the 60 s timeout in tests/api/test_mixin_import_isolation.py:101).

## 11. Output and contract

Return shapes are asserted where contracts are defined: the api tier pins the
whole public surface; test_pdscache_set_multi asserts internal dict states;
maintenance goldens pin whole artifacts. Exception types and messages: the
modern tiers consistently use `pytest.raises(..., match=)`
(test_log_path_timetag.py:147, test_crlf.py:124-129,
test_pdsfile_path_resolution.py:95-100) or assert `raised.value is exception`
(identity, test_pdsfile_path_resolution.py:140-145). Legacy message assertions
use substring-in-`str(e)` inside try/except — content is checked, but only
when the raise happens (TS-05 covers the vacuous-pass half). No new findings
beyond TS-05/TS-06.

## 12. Error handling and messages

Error specificity in the maintenance tier is a model: `ToolRun.error_lines`
parses only `| ERROR |`/`| FATAL |` lines from stdout (support.py:293-301), so
tests distinguish tool errors from interpreter noise, and tests assert both
the message and the file it names (e.g. test_pds3_checksums.py:111-114).
Exit-code contracts are pinned explicitly, including the deliberate batch-mode
exit-0-after-fatal (test_re_validate.py:1168-1195). The `finally: return`
swallowing family is regression-tested directly
(test_validate_exceptions.py, test_shelf_common.py:318-354), asserting both the
log and the re-raise. Cross-reference TS-05 for the legacy gaps.

## 13. State and workflow

Lifecycle transitions are the maintenance suite's core competence: every tool's
init/validate/repair/update cycle, clobber refusals, versioning of superseded
artifacts (one past the highest, twice in a row —
test_pds3_checksums.py:164-199), idempotency (crlf repair-then-OK at
test_crlf.py:77-83, pds4archives repair-cancels at test_pds4_archives.py
:106-124), and side effects (what lands on disk, what the log says, both
asserted). The update-vs-rebuild agreement test
(test_pds4_linkshelf.py:181-215) is a particularly good equivalence check. No
findings.

## 14. Test data and fixtures

Fixture hygiene is generally strong: narrow scopes, `tmp_path` everywhere,
monkeypatch auto-restore, and the two autouse fixtures (session preload,
read-only guard) are both justified infrastructure. Conftest placement follows
the "closest conftest" rule; nothing in the root conftest is misplaced.

**TS-15** — The rules-tier golden helper silently creates a missing golden and
conflates it with an empty result.
tests/support/pdsfile_test_helper.py:53 (`if update or not path.exists():`)
writes the golden from the *current* output on any run where the file is
absent — no `--update` required — then returns 0, and the callers
(opus_products_test:116-117, associated_abspaths_test:155-156) treat that falsy
return as "just written" and skip every assertion. Consequences: (a) a deleted
or mistyped golden path converts a rule test into a silent self-approval that
also writes into the repository during an ordinary run; (b) a legitimately
empty golden (`{}`/`[]`) is indistinguishable from the sentinel and would also
skip comparison. The maintenance tier's check_golden
(tests/holdings_maintenance/support.py:792-839) already does this right —
missing golden is an AssertionError unless `--update` was passed. The rules
helper should adopt the same contract.

**TS-16** — Fixture chains reach four to five levels in the maintenance tier:
`shelved_tree -> tree -> fresh_tree -> tool_tree -> source_stage`
(tests/holdings_maintenance/test_pds3_infoshelf.py:75-90 plus conftest.py).
Each level is documented and single-purpose, so this is noted per the checklist
rather than flagged for change; the docstrings carry the trace a reader needs.

Realistic data: the declared subsets are real PDS products with pinned sizes,
md5s and mtimes (subsets.py), deliberately distinct mtimes to exercise rollup;
test_pds3_checksums.py:256-284 covers a path with spaces. Cleanup: everything
tools write goes to tmp trees; the guard enforces it.

## 15. Flakiness indicators

- Time: the one wall-clock race is made deterministic (TickingClock); mtime
  comparisons use pinned epochs.
- Order: fresh_tree rebuilds per test; the pdsdependency unordered-glob hazard
  is handled by sorted-multiset comparison plus an ordered subsequence pin
  (test_pds3_dependency.py header and :49-63,105-111) — a defect worked
  around, documented as such, rather than asserted.
- External dependencies: the real holdings roots — **waived** (plan §2 ground
  rule 3); the fingerprint check (conftest tool_tree) turns drifted data into
  a skip with a reason rather than a flaky failure, and the goldens are tuned
  to the reference copy.
- Randomness: none; no `random`/`uuid4` in tests.
- Warning noise: 5 PyparsingDeprecationWarnings from the third-party `julian`
  package appear in every session (see TS-17).

## 16. Regression and documentation

Bug references are a strength few suites match: regression tests cite numbered
observations and describe the prior failure in the docstring (observation 3999
in the guard, 4062 in test_pds4_archive_products.py, 6607 in
test_stubbed_surfaces.py, 2100's general form, the CRLF empty-file
ZeroDivisionError ruling). Spec alignment runs in both directions —
tests/docs/ checks the docs against the code. There are no deprecated APIs, so
`pytest.warns` (0 uses) is not a gap.

**TS-17** — No `filterwarnings` configuration.
`pyproject.toml` `[tool.pytest.ini_options]` has no `filterwarnings` key
(grep count 0), so warnings are never escalated and the 5 julian
PyparsingDeprecationWarnings print in every run (pytest-ns.txt:86-107;
identical in both s passes). `python_testing.mdc` §4 requires
`filterwarnings = ["error", ...]` with narrowly-scoped ignores for third-party
warnings you cannot fix. Adding `"error"` plus one documented
`ignore::...PyparsingDeprecationWarning` entry would make the next new warning
a failure instead of noise. This is a config-strictness item, not one of the
hermetic aspects plan §6.6 defers, so it is actionable.

## 17. Other good practices

Clarity: the modern tiers' docstrings routinely explain what a vacuous pass
would look like and add negative controls (e.g. test_markup.py
::test_the_check_reports_the_mistakes_it_exists_for; the "collection trap"
note in test_crlf.py:18-21). Measured against the tree: 627 test functions, of
which 308 lack docstrings, 96 of those in test_pds3file_blackbox.py and 52 in
test_pds3file_whitebox.py — the legacy files are the entire tail
(`python.mdc` §6 / `python_testing.mdc` preamble; note that inline *type
annotations* on tests, which `python_testing.mdc` §2 also asks for, are
forbidden — **waived by pdsfile_overrides.mdc deviation (1)**; 0 annotated
test functions is correct here).

**TS-18** — Debug leftovers and dead case blocks.
13 bare `print(...)` calls remain in test bodies (e.g.
tests/pds3file/test_pds3file_blackbox.py:55, test_pds3file_whitebox.py:384,
:443); pytest captures them, but they are noise on failure and
`python.mdc` §2 bans stray diagnostics. Large commented-out parametrize/case
blocks persist: tests/pds4file/test_pds4file_blackbox.py:31-60,
tests/rules/pds4/test_uranus_occs_earthbased.py:41-62 and :77-111 (most of the
round-trip test's body). Either promote to skipped cases with reasons (visible
in reports, TS-09) or delete with the TODO retained.

Speed: full-suite wall time is acceptable for a data suite — ns 221.84 s,
s pds3 107.52 s, s pds4 6.90 s (serial, from the run outputs). Single
responsibility and AAA are followed in the modern tiers; the legacy loops
(TS-14) are the main multi-act offenders.

## 18. Code coverage

**Measurement:** full suite — the ns pass over all of tests/ plus the two
`--mode s` passes (pds3: tests/pds3file + tests/rules/pds3; pds4:
tests/pds4file + tests/rules/pds4), serial, against the real holdings roots,
appended into one data file; branch coverage with `source=["pdsfile"]` per
`[tool.coverage.run]`. Results: ns 1234 passed / 34 skipped; s pds3 555 / 3;
s pds4 150 / 31 — all matching the recorded baseline.

**TS-19** — **Total measured coverage is 58%** (9,715 statements, 3,704
missed, 3,542 branches, 329 partial). The 90% target (`python_testing.mdc`
§9) is not met as measured.

**TS-20** — The dominant cause is a measurement blind spot, not missing tests.
The maintenance-tool tests deliberately drive their tools as subprocesses
(tests/holdings_maintenance/__init__.py explains why in-process calls are
unsafe), and `coverage run` does not instrument child processes, so modules
with comprehensive task-cycle suites report near-zero: pds4linkshelf.py 6%,
pdslinkshelf.py 8%, _indexshelf_common.py 8%, pds4archives.py 12%,
pdsarchives.py 13%, _linkshelf_common.py 14%, pds4infoshelf.py 17%,
pdsinfoshelf.py 21%, pdschecksums.py 23%, pds4checksums.py 24%,
show_opus_products.py 62%. The contrast proves the point: re_validate.py, the
one tool tested in-process, measures 88%. Enabling subprocess coverage
(`COVERAGE_PROCESS_START` in `ToolTree.env` plus a `coverage.process_startup()`
hook — the existing `_subprocess_guard/sitecustomize.py` is already on every
tool subprocess's PYTHONPATH and is the natural place) would make the number
honest without changing a single test.

Modules below 90% (full list from coverage-summary.txt, excluding the
subprocess-shadowed tools above): `pdscache.py` 27% (MemcachedCache — waived,
deviation (4) pdscache row / ground rule 9; DictionaryCache is covered),
`pdsviewable.py` 64%, `__init__.py` 71%, `_index_rows.py` 76%,
`_associations.py` 77%, `_preload.py` 79%, `_opus.py` 81%, `_path_utils.py`
83%, `pdsindexshelf.py`/`pds4indexshelf.py` 83%, `_derived_paths.py` 84%,
`_sorting.py` 84%, `_shelves.py` 85%, `pdsfile.py` 87%,
`pds4file/__init__.py` 87%, `re_validate.py` 88%, `_properties.py` 89%,
`pds3file/__init__.py` 89%. At or above 90%: `_local_fs.py` 91%, crlf.py 98%,
every rule module 100%, `preload_and_cache.py` 100%. Genuine in-process gaps
worth new tests are listed in TS-10 (pdsviewable first).

## 19. Pytest markers and registration

Both custom markers (`full_holdings`, `holdings_free`) are registered with
descriptions in `pyproject.toml`, and `--strict-markers` plus
`--strict-config` are in `addopts` — a typo'd mark fails fast. Marker
application is layered sensibly: file-level `pytestmark` in test modules,
directory-level injection via the api/ and docs/ conftest hooks (with a
`tryfirst` ordering note). There are no `xfail` marks (0 hits) and therefore
nothing to audit. Skips: the `skipif(os.geteuid() == 0)` pair
(test_pds3_checksums.py:361, test_pds4_checksums.py:332) is valid; the stale
risk is the TODO-gated unconditional cluster already reported as TS-09.
Categorization: `full_holdings`/`holdings_free` double as the fast-subset
mechanism (`-m holdings_free` selects 433 of 1268 collected tests), so a
separate `slow` marker is not needed.

## 20. Test boundary (public API vs internals)

Seven import statements across six test modules import `_`-prefixed modules
(test_log_path_timetag.py:24-25, test_shelf_sidecar_record.py:21,
test_common_versioning.py:24, test_pds3_archives.py:19,
test_shelf_common.py:19, test_tool_naming.py:22). Each is a deliberate
whitebox test of shared internals that no public surface reaches (the sidecar
parser, the shelf-versioning core, the archive filter), each documents why,
and the public API is independently guarded by the freeze/mixin tests — so
this is recorded per the checklist, not flagged: refactors that move these
internals will break these tests, and that appears to be the intent.
Over-mocking is well defended: test_re_validate.py stubs five sibling tools
but pairs the stubs with a real-signature binding test (:1424-1451), and
test_stubbed_surfaces.py does the same for the PdsFile class members. No
findings.

## 21. Logging assertions

(`logging.mdc` exists and is cited; `logging_nav.mdc` does not, so the
logger-wiring checks are skipped.) `caplog` is never used (0 hits), and that is
the right call here: the code logs through `pdslogger.PdsLogger`, and the suite
asserts logging at the level that matters for these tools — the rendered log
file (pdslogger.file_handler into tmp_path, test_common_versioning.py:64-97,
test_validate_exceptions.py:60-93) and the tool's console stream parsed by
level marker (`ToolRun.error_lines` matches `| ERROR |`/`| FATAL |` only, so
level *is* verified, not just message text). Absence-of-logging is asserted
routinely (`run.error_lines == []` after every clean validate). Force/limits
semantics — the one place a log line can silently vanish — have a dedicated
test with a negative control
(test_common_versioning.py::TestReportingUnderAnInfoCap). No findings.

## 22. Pytest configuration

`[tool.pytest.ini_options]` sets `pythonpath = [".", "src"]` and
`addopts = ["--strict-markers", "--strict-config"]`, registers both markers,
and there is no competing pytest.ini/setup.cfg. The absence of `-n`/`--cov`
from addopts is a recorded owner decision — **waived by pdsfile_overrides.mdc
deviation (7)**.

**TS-21** — `testpaths` is not set (grep count 0). A bare `pytest` works today
because the default `norecursedirs` excludes `venv` and no stray test files
exist elsewhere, but collection scans from the repo root, and a stray
`test_*.py` dropped anywhere (scripts/, critiques/) would silently join the
suite. One line (`testpaths = ["tests"]`) closes it. Low effort, real
protection.

Missing `filterwarnings` is TS-17. Plugin inventory: pytest-cov 7.1.0 and
pytest-xdist 3.8.0 are installed and both used per-invocation (coverage runs,
optional workers), so neither is dead weight; pytest-randomly is absent, which
is consistent with the serial deterministic design rather than a gap.

## 23. Snapshot and golden-file testing

Golden files are used exactly where inline assertion would be unmaintainable:
75 golden files are committed under tests/golden/full/ (verified equal via
`git ls-files`, so none is untracked). Management in the maintenance tier is
the model: `check_golden` fails on a missing golden with regeneration
instructions, compares line lists (with a documented reason for not joining),
prints a unified diff, restricts `unordered=True` to the one artifact whose
producer genuinely does not order (pdsdependency), and `--update` is an
explicit opt-in flag registered in tests/conftest.py. "Approve and forget" is
countered by pairing every golden comparison with structural assertions on the
same artifact (declared md5s, child counts, link edges), so a wrongly-updated
golden still has to satisfy independent checks. The one management defect is
the rules-tier helper's auto-create-on-missing (TS-15), which bypasses all of
these protections.

## Prompt for an AI agent to fix tests

You are working in rms-pdsfile at branch `rewrite` (or a branch cut from it).
Fix the test suite according to the findings below **without changing any
production code under src/** and without weakening any existing assertion.
Preserve existing passing behavior: after your changes,
`pytest tests --mode ns`, `pytest tests/pds3file tests/rules/pds3 --mode s`,
and `pytest tests/pds4file tests/rules/pds4 --mode s` must pass with the same
or stricter assertions (run them with
PDS3_HOLDINGS_DIR/PDS4_HOLDINGS_DIR/PDSFILE_TEST_HOLDINGS=full set; the
reference baseline is ns 1234 passed/34 skipped, s pds3 555/3, s pds4 150/31 —
fixed vacuous tests may legitimately change these counts, explain any delta).
Read `.cursor/rules/pdsfile_overrides.mdc` first; it overrides the template
rules. Never edit tests/api/api_manifest.json, manifest_allowlist.json,
test_api_freeze.py, or scripts/dump_public_api.py. Do not add inline type
annotations or mypy. Do not add `-n`/`--cov` to addopts. Do not write into
/seti/opus/pdsdata. Keep `x + [y]` spellings (RUF005 is owner style). Do not
widen any per-file-ignores ratchet entry; shrinking one as a side effect of a
test fix is welcome but must be reflected in pyproject.toml and noted.

Apply, in priority order:

1. **Vacuous assertions** — tests/pds3file/test_pds3file_blackbox.py:110:
   replace `assert res.sort() == expected.sort()` with
   `assert sorted(res) == sorted(expected)`.
   test_pds3file_blackbox_cached.py:123-131: assert
   `sorted(res1) == sorted(expected)` and `res1 == res2` for childnames;
   :142-147: add expected-value assertions for `_info` (derive once from the
   current correct output, then pin). Delete the dead `expected is None`
   branches at test_pds3file_blackbox.py:227-228, 255-262, 276-284.
2. **Silently-passing exception tests** — rewrite the seven try/except sites
   listed in TS-05 (whitebox :321-327, :426-430, :454-458, :519-524, :549-556;
   blackbox :902-908, :1923-1928) so a missing raise fails: use
   `pytest.raises(<type>, match=...)` where every parametrize row expects a
   raise, or split raising and non-raising rows into separate tests. Where the
   pyproject per-file-ignores PT017/PT012 entries for these files stop firing,
   shrink those ratchet entries. test_pds3file_whitebox.py:439-446: make
   `test_from_path3` `pytest.skip` when `SHELVES_ONLY` is False instead of
   passing vacuously.
3. **Golden helper** — tests/support/pdsfile_test_helper.py: make
   read_or_update_golden_copy write only when `update` was requested; when the
   golden is absent and update is False, fail with the regeneration command
   (mirror tests/holdings_maintenance/support.py::check_golden). Replace the
   falsy-sentinel protocol (`return 0` / `if not expected_data: return`) with
   an explicit `None` sentinel so an empty golden still compares.
4. **filterwarnings** — add to `[tool.pytest.ini_options]`:
   `filterwarnings = ["error", "ignore::DeprecationWarning:julian.*"]` (match
   the actual PyparsingDeprecationWarning category emitted by
   julian/time_pyparser; keep the ignore as narrow as possible and comment
   why). Fix or narrowly-ignore anything new that "error" surfaces.
5. **Subprocess coverage** — in tests/holdings_maintenance/support.py, set
   `COVERAGE_PROCESS_START` in `ToolTree.env` (and no_holdings_env) when
   coverage is active, and add `import coverage; coverage.process_startup()`
   guarded by that env var to _subprocess_guard/sitecustomize.py, so tool
   subprocesses are measured. Re-measure; report the new total.
6. **Skip hygiene** — convert the unconditional skip in
   tests/rules/pds4/test_cassini_iss_fring_mosaics_rsfrench2025.py:15 and the
   substring-keyed skips in tests/pds4file/test_pds4file_blackbox.py:732-735,
   :957-962 into `skipif` on the bundle directory's existence so they
   self-lift. Delete the duplicate parametrize rows:
   test_pds4file_blackbox.py:138 (coordinate with deferred observation 84 —
   this is the sanctioned test-content change that removes the PT014 ratchet
   row), test_coiss_xxxx.py:80-81, test_go_0xxx.py:329-332.
7. **Parametrize conversions** — convert the case-list loops in
   tests/rules/pds3/test_corss_8xxx.py (both tests), test_go_0xxx.py
   ::test_duplicated_products, and each rule module's
   test_opus_id_to_primary_logical_path into `@pytest.mark.parametrize` with
   path-based ids.
8. **Config** — add `testpaths = ["tests"]`.
9. **Cleanups** — remove the 13 bare `print()` calls from test bodies; delete
   or convert to skipped cases the commented-out blocks at
   test_pds4file_blackbox.py:31-60 and test_uranus_occs_earthbased.py:41-62,
   :77-111; deduplicate the three instantiate_target_pdsfile helpers behind
   tests/support/pdsfile_test_helper.py; add docstrings to legacy tests as you
   touch them (do not mass-edit files you are not otherwise changing).
10. **Coverage target** — after step 5's re-measurement, add in-process tests
    for the genuine gaps: pdsviewable.py (PdsViewable/PdsViewSet methods,
    lines 551-610, 633-641, 845-933), _index_rows.py (120-131, 228-233,
    521-527), _associations.py, _preload.py (579-604, 623-653), _opus.py.
    Coverage must be checked over the **entire suite** (all three passes,
    combined data file); target at least 90% with almost all non-exception
    lines covered. MemcachedCache (pdscache.py) is exempt by owner decision;
    do not try to test it.
11. **Exception messages** — wherever you touch an exception test, assert on
    the message content (`pytest.raises(...)` with `match=` or on
    `str(exc_info.value)`), never on the type alone.

## Commands run

Every number in this report comes from one of the following commands, run in
this session at commit 6525951 (`git rev-parse --short HEAD`), with
`source venv/bin/activate; export PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings
PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings PDSFILE_TEST_HOLDINGS=full`
in /seti/all_repos/rms-pdsfile, except the full-suite/coverage runs, which were
executed by the coordinator's `run_suite_coverage.sh` (same env; script text
read and reproduced below in essentials):

- `git rev-parse --short HEAD; git status --short` — commit 6525951, clean.
- `find tests -type f | sort` and
  `find tests -name '*.py' ! -path '*__pycache__*' | xargs wc -l | sort -n` —
  file inventory; 84 .py files, 18,765 total lines; per-file line counts.
- `find tests -name 'test_*.py' | wc -l` — 60 test files.
- `grep -rn 'caplog' tests --include='*.py' | wc -l` — 0.
- `grep -rn 'pytest.warns' tests --include='*.py' | wc -l` — 0.
- `grep -rn 'mock.patch\|unittest.mock\|MagicMock' tests --include='*.py' | wc -l` — 0.
- `grep -rln 'monkeypatch' tests --include='*.py' | wc -l` — 15 files.
- `grep -rn '@pytest.mark.parametrize' tests --include='*.py' | wc -l` — 301.
- `grep -rn 'xfail' tests --include='*.py' | wc -l` — 0.
- `grep -rn 'def test_.*-> None' tests --include='*.py' | wc -l` — 0.
- `grep -c 'testpaths' pyproject.toml` — 0; `grep -c 'filterwarnings'
  pyproject.toml` — 0; `[tool.pytest.ini_options]` and `[tool.coverage.*]`
  read via `sed -n` over pyproject.toml.
- `pytest --collect-only -q` — 1268 collected;
  `... -m holdings_free` — 433/1268; `... -m full_holdings` — 129/1268;
  collection warnings inspected via `grep -B8 'Docs:'` (5
  PyparsingDeprecationWarning lines, all from venv julian/time_pyparser.py).
- `pip list | grep -i 'pytest\|coverage\|xdist'` — pytest 9.0.2, pytest-cov
  7.1.0, pytest-xdist 3.8.0, coverage 7.13.3.
- Full-suite outputs read in full from the coordinator run (script:
  `coverage run -m pytest tests --mode ns -rs`, then `coverage run -a` for
  `tests/pds3file tests/rules/pds3 --mode s` and
  `tests/pds4file tests/rules/pds4 --mode s`, then `coverage report [-m]`):
  pytest-ns.txt — 1234 passed, 34 skipped, 5 warnings, 221.84 s, with the
  per-reason skip list; pytest-s-pds3.txt — 555 passed, 3 skipped, 107.52 s;
  pytest-s-pds4.txt — 150 passed, 31 skipped, 6.90 s;
  coverage-summary.txt / coverage-term-missing.txt — TOTAL 9715 stmts, 3704
  miss, 3542 branch, 329 partial, 58%, plus every per-module figure and
  missing-line range quoted in sections 4 and 18.
- `python - <<'EOF' ...ast walk...` — 627 test functions, 308 without
  docstrings, per-file tail (96 blackbox, 52 whitebox, 23 test_crlf, ...).
- `grep -n 'res.sort() == expected.sort()' tests/pds3file/test_pds3file_blackbox.py`
  — line 110.
- `grep -n 'assert False\|except \|raises\|xfail\|skip\|def test_\|class Test'
  tests/pds3file/test_pds3file_blackbox.py` (and the equivalent for the
  cached, whitebox and pds4 blackbox files) — structural surveys behind the
  sampled-file claims and the TS-05 site list.
- `ruff check tests/pds4file/test_pds4file_blackbox.py --isolated --select
  PT014 --no-cache` — PT014 at line 138, duplicate of index 34.
- `ruff check tests --select PT --no-cache` — 1 finding (PT011, whitebox
  test_child), confirming the configured gate's ignores; context via
  `sed -n '895,927p' tests/pds3file/test_pds3file_whitebox.py` (CACHE deletion
  at :920-922).
- `grep -rn 'import.*\b_[a-z]' tests --include='*.py' | grep pdsfile` — the 7
  private-module import statements in 6 files (section 20).
- `find tests/golden -type f | wc -l` and `git ls-files tests/golden | wc -l`
  — 75 and 75.
- `grep -n 'print(' tests/pds3file/*.py tests/pds4file/*.py
  tests/rules/pds3/*.py | wc -l` — 13.
- `grep -n 'SORT_ORDER' src/pdsfile/pdsfile.py src/pdsfile/_sorting.py` and
  `grep -n 'def sort_labels_after' -A 6 src/pdsfile/_sorting.py` — the
  copy-then-mutate behavior behind TS-12's cached-object note.
- `sed -n '1,80p' tests/rules/pds3/test_coiss_xxxx.py`,
  `grep -n 'def test_duplicated_products' -A 20 tests/rules/pds3/test_go_0xxx.py`
  — TS-11 evidence.
- `ls -la <scratchpad>` polls — coordinator output presence and timestamps.

Claims not backed by a command above are direct quotations of file content
read in this session (file:line citations throughout). No test, conftest,
golden, or configuration file was modified; this report is the only file
written.
