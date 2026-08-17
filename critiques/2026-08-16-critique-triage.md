# Critique-skill triage — 2026-08-16

The three template critique skills were run against the tree at `6525951`
(branch `chore/critique-reports`, identical to `rewrite`), each producing a
full report in this directory:

| Report | Skill | Findings |
|---|---|---|
| [2026-08-16-test-suite-critique.md](2026-08-16-test-suite-critique.md) | `critique-test-suite` | TS-01 – TS-21 |
| [2026-08-16-documentation-critique.md](2026-08-16-documentation-critique.md) | `critique-documentation` | DOC-01 – DOC-18 |
| [2026-08-16-codebase-analysis.md](2026-08-16-codebase-analysis.md) | `python-codebase-analysis` | CA-01 – CA-32 |

This document is the triage of all 71 findings. **This PR delivers reports and
triage only; nothing was fixed.** Every finding below records what the report
claims, what an independent verification against the code found (the check run,
not the report's own prose), a severity judgment, whether the finding restates
an entry of the open observation register (`observations*.md`, 213 open), and a
recommended disposition for the owner. Where a finding contradicts a decision
recorded in `.cursor/rules/pdsfile_overrides.mdc` or the plan, the decision is
cited and the finding is not treated as actionable.

Verification method: every cited site was re-read at `6525951`; every count was
re-measured (grep/sed/ruff/AST or the suite run recorded below) rather than
copied from the report. The full-suite measurement behind the coverage claims
is this session's own run: `--mode ns` over `tests/` (1234 passed / 34
skipped), `--mode s` pds3 (555 / 3), `--mode s` pds4 (150 / 31) — all equal to
the recorded baseline — under `coverage run` (branch mode, `source=pdsfile`),
totaling **58%** (9,715 statements, 3,704 missed).

## Tally

| Verdict | Count | Findings |
|---|---:|---|
| Verified, new, actionable | 31 | TS-01..04, TS-06, TS-08, TS-09, TS-14, TS-15, TS-17, TS-18, DOC-01, DOC-03..06, DOC-09, DOC-12..17, CA-04*, CA-08, CA-11, CA-14, CA-20, CA-21, CA-24, CA-26 |
| Verified, restates an open register entry | 10 | TS-05*, TS-10*, TS-11*, TS-20, TS-21, DOC-07, CA-02*, CA-03, CA-17, CA-31 |
| Verified, umbrella over recorded entries | 2 | TS-19, CA-13 |
| Waived by a recorded decision (correctly marked by the reports) | 10 | DOC-02, DOC-08, DOC-10, DOC-18, CA-01, CA-05, CA-06, CA-09, CA-27, CA-32 (the test report additionally carries section-level waiver notes against deviations 1/4/7 and ground rule 3; those are correctly cited, with one exception review round 1 caught and the reports now correct — the MemcachedCache test gap is register 4207, an open deferral, not a waiver) |
| Positive/no-action observations (state of health, nothing to do) | 15 | TS-12, TS-13, TS-16, CA-07, CA-10, CA-12, CA-15, CA-16, CA-18, CA-19, CA-22, CA-23, CA-25, CA-28, CA-29 |
| Recommend decline | 3 | TS-07, DOC-11, CA-30 (defer) |
| Outright wrong | 0 | — |

`*` = partial overlap: the finding adds sites or measurements the register does
not have; the overlapping entry is named in the finding's row. Counts by
category overlap (a `*` finding appears once, under its dominant verdict); the
per-finding rows below are authoritative.

Report defects found by verification (all small, none invalidating):

- **TS-18** says "13 bare `print()` calls"; the grep count is 13 but one hit
  (`tests/pds3file/test_pdsviewable_blackbox.py:27`) is a commented-out line.
  The live count is **12**.
- **TS-11** says the COISS duplicate logical path appears "twice at :80-81";
  `test_coiss_xxxx.py:79-81` carries the same `W1294561143_1.IMG` row **three**
  times. The defect stands, slightly understated.
- **TS-20** proposes subprocess coverage "without changing a single test" —
  correct about the tests, but register entry **4214** already measured the
  cost of exactly that instrumentation at **8.6x** on the per-PR data gate and
  deferred it to PR-37 with `COVERAGE_CORE=sysmon` named as the lever to
  measure first. The recommendation is not new and must not be re-decided
  without that measurement.
- **CA-31** closes the `tabulate` question as "none required — recorded and
  documented". The current shape is indeed recorded in `pyproject.toml` and
  the user guide, but register entries **3100/3101** hold it as an *open*
  owner decision (runtime dependency vs guarded import); the finding
  understates that the question is still open.
- **Review round 1** caught a fifth, larger defect the triage's own
  verification had repeated rather than caught: the test report presented
  the `MemcachedCache` coverage gap as "waived by deviation (4) / ground
  rule 9" and its fix prompt as "exempt by owner decision — do not try to
  test it". No such decision exists: deviation (4)'s pdscache row waives two
  lint findings, ground rule 9 forbids removal (not testing), one method is
  already stub-tested (`tests/core/test_pdscache_set_multi.py`), and
  register entry **4207** holds the gap open with phase b of issue #77 as
  owner. Both reports and this triage were corrected in the round-1 fix
  pass; round 1 also corrected four smaller report inaccuracies (the §18
  below-90% list omitted four subprocess-shadowed shared modules; `crlf` is
  a second in-process-tested tool at 98%; CA-13 misdescribed its measurement
  basis as ns-only; the §20 private-import count is eight, not seven).

## What needs the owner's decision, ranked

1. **Accept the vacuous-test fixes (TS-01, TS-05, TS-06, TS-15; register
   1400/1401).** The one genuinely sharp new discovery of the whole exercise
   is TS-15: the rules-tier golden helper writes a missing golden from current
   output on an ordinary run — no `--update` — and then skips every assertion,
   so a mistyped or deleted golden path self-approves and writes into the
   repository. TS-01 (`assert res.sort() == expected.sort()` compares
   `None == None`), TS-05 (seven try/except tests that pass when nothing
   raises; five are register entry 1400, the two blackbox sites are new), and
   TS-06 (a test whose ns-mode body is `assert True`) are the same defect
   class the register already scheduled for this PR's fixes half. Recommended:
   fix now (the PR-36 fixes pass), together with register 1401 (unused
   `expected` parameters), which **no skill re-found** and must be picked up
   from the register.
2. **Accept the dev-guide drift fixes (DOC-12, DOC-13, DOC-01).** The gate
   table in `dev_guide_ci.rst` misinforms today (PyMarkdown shown off but
   defaulting true since #153; the stubtest gate absent since #154), the
   repository-layout chapter is silent on the 43 shipped `.pyi` stubs, and
   `docs/conf.py:112-117` is a stale paragraph contradicting the one below it.
   All three verified. Recommended: fix now; these are the only places the
   documentation actively misleads.
3. **Coverage posture (TS-19/CA-13 umbrella; TS-20 = 4214).** The 58% total
   against the 90% target decomposes into: the subprocess blind spot (tool
   suites uninstrumented — entry 4214, cost measured, owner PR-37), the
   `MemcachedCache` body (an **open deferral, register 4207** — one method is
   stub-tested and the entry's owner is phase b of issue #77; deviation (4)'s
   pdscache row waives two lint findings only, and ground rule 9 protects the
   class from removal, not from testing), and genuine in-process gaps
   (TS-10: `pdsviewable.py` 64% is the largest; parts overlap entries
   4205/3200/3201). Recommended: no new decision here — PR-37 already
   owns codecov targets and the `fail_under` question; add the TS-10 targets
   to the fixes-half backlog or a test PR after the merge; the MemcachedCache
   gate stays with 4207's owner.
4. **Dependency floors and audit tooling (CA-24, CA-21).** Verified: seven of
   eight runtime dependencies unbounded; no Dependabot config and no
   `pip-audit` anywhere, both required by `dependency_management.mdc` §3/§5
   and `security.mdc` §2, and neither covered by a recorded deviation
   (`ENABLE_BANDIT`/`ENABLE_VULTURE` permanently false is a different
   decision). Recommended: owner decision; if accepted, a small `build:`/`ci:`
   PR (floors from the versions CI resolves today; gate wired
   script-first per `environment.mdc`).
5. **The info-shelf sidecar `eval` (CA-20).** Verified at `_shelves.py:97`,
   with the trust boundary documented at `_shelves.py:63-76`.
   `ast.literal_eval` would be a drop-in for well-formed records but changes
   the documented `Raises:` contract for malformed ones — a documented-
   behavior change that ground rule 9-style caution puts with the owner, not
   a style pass. Recommended: owner decision; either take it with a
   regression test in a bug-fix PR, or record keeping `eval` and close it.
6. **`filterwarnings` (TS-17 = CA-14).** Verified absent; the suite prints
   the same 5 third-party `julian`/pyparsing deprecation warnings every run.
   Not one of the hermetic aspects §6.6 defers. Recommended: accept,
   measure-first (turn on `"error"` plus one narrow documented ignore; the
   full-data run is the arbiter of what else surfaces).
7. **Further tool-pair consolidation (CA-02).** The measured residue is real
   (242 differing lines of 2,032 for the checksums pair under mechanical
   rename — reproduced exactly). Whether it is worth another Phase-6-style
   pass is a scope decision the plan does not currently own; the residual-
   duplication family is already registered (4108, 4122-4125, 6107, 6114).
   Recommended: owner decision; if declined, record the stopping point.
8. **Small accepted-fix batch (if the owner concurs):** TS-02, TS-03, TS-04,
   TS-08, TS-09, TS-11, TS-14, TS-18, TS-21 (= register 4300), DOC-03,
   DOC-04, DOC-05, DOC-06, DOC-09, DOC-14..17, CA-03 (= 4304, plus its dev-
   guide annotation), CA-08, CA-11, CA-26. Each is verified, cheap, and
   carries no behavior question; the natural vehicles are the PR-36 fixes
   pass (test items) and one docs-sweep PR (prose items).
9. **Deliberate one-liners parked in the register:** DOC-07 (= 6502, the
   `--archives` "the the" — kept deliberately by PR-26 so the shared constant
   was provably byte-identical; fixing it is a user-visible text change to
   make on purpose) and CA-31 (= 3100/3101, the `tabulate` runtime-vs-guarded
   question, still open). Both need only a yes/no.
10. **Recommended declines:** TS-07 (two naming generations — a mass rename
    churns test ids for cosmetic gain; rename opportunistically), DOC-11
    (landing-page prose slightly over a template budget; the sentences earn
    their keep), CA-30 (PEP 639 license form — wait for the setuptools floor
    to make it free; pyroma already scores 10/10).

**Item the skills missed that the register assigns to this PR:** entry
**3401** names PR-36 as owner of scrubbing the holdings-root fragment from
`tests/pds3file/test_pds3file_whitebox.py` (verified still present at line
393). No skill flagged it. The fixes half must take it from the register, not
from the reports.

## Per-finding triage

Format: **ID — claim** | verification | severity | register overlap |
disposition.

### critique-test-suite (TS-01 – TS-21)

- **TS-01 — `assert res.sort() == expected.sort()` always passes.** Verified:
  `test_pds3file_blackbox.py:110`, `list.sort()` returns None; only the
  length check above it does any work. High. New. **Fix now** (PR-36 fixes
  pass).
- **TS-02 — subset-only assertions in cached `test_childnames` (and whitebox
  `test_viewset_lookup`).** Verified at
  `test_pds3file_blackbox_cached.py:123-131`: `expected ⊆ res1` and
  `res1 ⊆ res2`, no equality or length. Medium. Split overlap: the
  `test_viewset_lookup` half restates recorded content of entry 3202
  ("`viewset_lookup` ... never checks a length"); the cached
  `test_childnames` half is new. **Fix now** with TS-01.
- **TS-03 — `test__info` asserts only `res1 == res2`.** Verified at
  `:142-147`; no expected value at all. Medium. New. **Fix now.**
- **TS-04 — pragma-excluded branches that would test the code against
  itself.** Verified at `test_pds3file_blackbox.py:227-228, 255-262,
  276-284`: `if expected is None` recomputes the expectation with the
  implementation's own logic; no row passes None. Low. New. **Fix now**
  (delete the branches).
- **TS-05 — seven try/except tests that pass when nothing raises.** Verified
  all seven sites (whitebox `:321-327, :426-430, :454-458, :519-524,
  :549-556`; blackbox `:902-908, :1923-1928` — the blackbox pair's
  `except ValueError: assert True` also absorbs raises on rows expected to
  succeed). High. **Restates register 1400** (the five whitebox sites; the
  two blackbox sites are new). **Fix now** — 1400 is already assigned to this
  PR's fixes half; do 1401 in the same pass (see ranked item 1).
- **TS-06 — `test_from_path3` is vacuous in `--mode ns`.** Verified at
  whitebox `:439-446`: `else: assert True`. Medium. New. **Fix now**
  (explicit skip so the report shows it).
- **TS-07 — two naming generations coexist.** Verified (numeric-suffix names
  in legacy files). Cosmetic. New. **Decline** as a sweep; rename only when a
  file is otherwise touched.
- **TS-08 — three `instantiate_target_pdsfile` copies with two `--update`
  access patterns.** Verified: `tests/support/pdsfile_test_helper.py:16`
  (takes `cls`), `tests/pds3file/helper.py:15`, `tests/pds4file/helper.py:16`
  (binds root, prepends `bundles/`). Low-medium. Related register entries
  4103 (helper.py's two module names) and 4110 (import-time resolution) are
  different defects in the same files. **Fix later** — a test-infrastructure
  PR; coordinate with 4103/4110.
- **TS-09 — the 31-skip cluster is TODO-gated and will not self-lift.**
  Verified: unconditional `pytestmark` at
  `test_cassini_iss_fring_mosaics_rsfrench2025.py:15`, substring-keyed skips
  at `test_pds4file_blackbox.py:732-735, :957-962`. Medium. New (the TODO
  family is CA-26's). **Fix later** (skipif on bundle presence) — behavior of
  the suite when the bundle lands changes, so do it deliberately.
- **TS-10 — in-process coverage gaps worth new tests.** Verified against this
  session's `coverage report -m`: `pdsviewable.py` 64%, `_index_rows.py` 76%,
  `_associations.py` 77%, `_preload.py` 79%, `_opus.py` 81%. Medium.
  **Partial overlap**: `_preload` gaps are register 4205; entries 3200/3201
  hold the zero-coverage public methods; the `pdscache` share is register
  4207 (open, phase b of #77). `pdsviewable` as the largest target
  is new. **Fix later** (a test PR; see ranked item 3).
- **TS-11 — duplicate case rows.** Verified: `test_pds4file_blackbox.py:138`
  (= **register 4203** / deferred 84 / the PT014 ratchet row);
  `test_coiss_xxxx.py:79-81` (three identical rows, report said two);
  `test_go_0xxx.py:329-332` (two duplicate pairs). Low. **Fix later** with
  the test PR that owns 4203's sanctioned id removal.
- **TS-12 — facts that make `pytest -n auto` unsafe.** Verified (session
  cache mutation, whitebox CACHE deletion at `:920-922`). Informational; the
  serial design is deviation (7). **No action** (recorded).
- **TS-13 — stub registry is a comment convention.** Verified at
  `test_stubbed_surfaces.py:61-66`. Informational. **No action.**
- **TS-14 — table-driven loops that should be parametrized.** Verified
  (`test_corss_8xxx.py:31-77` and siblings). Low. New. **Fix later**
  (mechanical; changes test-id counts, so it belongs to a deliberate test
  PR, not a rider).
- **TS-15 — the rules-tier golden helper auto-creates a missing golden and
  conflates it with an empty result.** Verified:
  `tests/support/pdsfile_test_helper.py:53-58`
  (`if update or not path.exists(): ... return 0`) and both callers'
  `if not expected_data: return`. **High — the sharpest new finding of the
  three reports.** New (no register entry; the maintenance tier's
  `check_golden` already implements the correct contract). **Fix now.**
- **TS-16 — fixture chains reach 4-5 levels.** Verified; each level
  documented. **No action** (checklist note).
- **TS-17 — no `filterwarnings`; 5 third-party warnings every run.**
  Verified (`grep -c filterwarnings pyproject.toml` = 0; "5 warnings" on all
  three suite summary lines). Medium. New. **Owner decision → fix**
  (ranked item 6). Same finding as CA-14.
- **TS-18 — debug leftovers and dead case blocks.** Verified with one
  correction: **12 live** `print()` calls, not 13 (one hit is a comment);
  commented-out case blocks confirmed. Low. New. **Fix later** (with TS-09's
  file pass).
- **TS-19 — total coverage 58% vs the 90% target.** Verified — this
  session's own measurement. Umbrella finding; decomposition and ownership
  in ranked item 3. **Already owned** (PR-37 targets + register entries).
- **TS-20 — subprocess coverage blind spot; wire `COVERAGE_PROCESS_START`.**
  Mechanism verified (tools subprocess-driven; in-process `re_validate`
  measures 88% vs 6-24% for subprocess-driven tools). **Restates register
  4214**, which measured the fix at 8.6x on the data gate and deferred to
  PR-37 (`COVERAGE_CORE=sysmon` first). **Already recorded — PR-37 owns**;
  do not re-decide without 4214's measurements.
- **TS-21 — no `testpaths`.** Verified (grep = 0). Low. **Restates register
  4300.** **Fix later** (one line; belongs to whatever PR next touches pytest
  config — the fixes half may take it with 4300 closed in the same change).

### critique-documentation (DOC-01 – DOC-18)

- **DOC-01 — stale intersphinx paragraph in `conf.py`.** Verified at
  `docs/conf.py:112-117`: describes an inventory/timeout that no longer
  exists and contradicts `:120-129`. Medium. New. **Fix now** (delete).
- **DOC-02 — intersphinx not enabled.** Verified waived: deliberate removal
  (PR #139), rationale in `conf.py:120-129`. **Waived — correctly marked.**
- **DOC-03 — em-dashes in two non-`src` `.py` files.** Verified
  (`scripts/check_runtime_imports.py:66`,
  `tests/holdings_maintenance/test_shelf_common.py:323`). Low. New. **Fix
  later** (docs/prose sweep).
- **DOC-04 — seven time-anchored phrasings.** All seven verified by grep.
  Low. New. **Fix later** (same sweep).
- **DOC-05 — three "older log layout" notes are migration framing.**
  Verified (`user_guide_maintenance_tools.rst:261-267` quoted exactly).
  Low. New. **Fix later**, keeping the operational content, as the report
  itself prescribes.
- **DOC-06 — two British spellings.** Verified (`catalogued`, `catalogue`).
  Low. New. **Fix later** (same sweep).
- **DOC-07 — "the the" in the `--archives` help.** Verified at
  `_shelf_common.py:278-281`. **Restates register 6502**, which records the
  typo as *deliberately kept* so the shared constant reproduced all four
  tools' help byte-identically; fixing is a user-visible text change to make
  on purpose. **Owner yes/no** (ranked item 9).
- **DOC-08 — docstrings use inline literals, not roles.** Verified waived:
  register 1003 → PR-31a permanently deferred to **issue #149** with the
  sweep measured (3,651 occurrences). **Waived — correctly marked.**
- **DOC-09 — README names the heavier extra for docs builds.** Verified
  (`README.md:145`; the `docs` extra suffices and is what RTD installs).
  Low. New. **Fix later** (one sentence).
- **DOC-10 — no API-usage chapter in the user guide.** Verified waived: the
  guide's scope is the CLI programs by plan decision (PR-32's title). The
  report's residual note (an API walkthrough is the largest genuinely
  missing doc) is fair and worth remembering post-merge. **Waived —
  correctly marked.**
- **DOC-11 — landing-page prose over the template budget.** Verified
  (~4 sentences vs "1-2"). Trivial. **Decline** — the report itself says the
  sentences earn their keep.
- **DOC-12 — the CI gate table is stale on two gates.** Verified:
  `dev_guide_ci.rst:39` says PyMarkdown "not yet" while
  `run-all-checks.sh:143` defaults it true; no stubtest row anywhere in the
  table while `:139` defaults it true. **High (docs actively misinform).**
  New — drift from merges #153/#154. **Fix now.**
- **DOC-13 — repository-layout chapter omits the 43 stubs and the stubtest
  allowlist.** Verified (`grep '\.pyi\|stub' docs/dev_guide/*.rst` → one
  half-sentence in `dev_guide_ci.rst:28`). Medium. New — same root cause as
  DOC-12. **Fix now** with DOC-12.
- **DOC-14 — dev-guide toctree does not end with API reference +
  contribution guide.** Verified (`dev_guide.rst` ends with `dev_guide_ci`).
  Low. New. **Fix later** — or record the layout choice; owner's pick.
- **DOC-15 — no introduction chapter; runtime dependencies named nowhere.**
  Verified by grep (one `pdslogger` token in a code block). Low-medium. New.
  **Fix later** (short section naming the runtime deps).
- **DOC-16 — class diagram lacks abstract/dataclass markers.** Verified (the
  abstract-in-practice statement lives in prose at
  `dev_guide_architecture.rst:66`, not in the diagram). Low. New. **Fix
  later** (one annotation).
- **DOC-17 — goldens how-to lacks the template's required sections.**
  Verified (headings present: "When --update is legitimate", "Which holdings
  root to use", etc.; no Prerequisites / Expected Results / Troubleshooting
  sections — the content exists in prose). Low. New. **Fix later**
  (restructure, no new claims).
- **DOC-18 — mermaid renders via CDN; offline copies show no diagrams.**
  Verified waived: recorded owner decision (2026-08-09), issue #136,
  restated in `conf.py`. **Waived — correctly marked.**

### python-codebase-analysis (CA-01 – CA-32)

- **CA-01 — four modules over the length limits, all waived.** Verified: the
  measurement reproduces deviation (3)'s table exactly (issues #141-#144).
  **No action — tree and record agree.**
- **CA-02 — checksum and info-shelf pds3/pds4 pairs ~90% identical under
  mechanical rename.** Verified: the 242/2,032 checksums-pair measurement
  reproduced exactly this session. Medium. **Partial overlap** with the
  residual-duplication family (4108, 4122-4125, 6107, 6114); the pair-diff
  numbers are new evidence. **Owner decision** (ranked item 7).
- **CA-03 — `run_tests_coverage.sh` is tracked but cannot run.** Verified
  (dead paths, `exit -1`). Low. **Restates register 4304** (and deferred 16;
  the dev guide already annotates it "do not use"). **Fix later** — deletion
  plus the dev-guide line, in the fixes half or PR-37's sweep.
- **CA-04 — eight text-mode `open()` calls without `encoding=`.** Spot-
  verified (`_shelves.py:475` confirmed; site list from the report's AST
  sweep). Medium. **Partial overlap**: the `re_validate.py` reader is
  inside register 4042 (its `UnicodeDecodeError` death is recorded there);
  the other sites are new. **Fix later** — a small sweep, but it touches
  frozen-format writers, so per-site care and a regression test where
  behavior could shift.
- **CA-05 — no custom exception hierarchy.** **Waived** (deviation (2):
  frozen raise types) — correctly marked.
- **CA-06 — `os.path` throughout.** **Waived** (deviation (5)) — correctly
  marked.
- **CA-07 — library hygiene clean (no print/sys.exit/bare except in core).**
  Positive; spot-checked. **No action.**
- **CA-08 — `re_validate` hard-codes mail relay and sender.** Verified
  (`re_validate.py:105-106`). Low. New. **Owner decision** — env-var
  override is legal now that the file is unfrozen; fold into the next
  maintenance-tool PR (register 4042's family).
- **CA-09 — no annotations / no mypy.** **Waived** (deviation (1)) —
  correctly marked; stubs + stubtest verified present.
- **CA-10 — both ruff gates pass clean.** Verified independently this
  session (both invocations exit 0). Positive. **No action.**
- **CA-11 — deviation (12)'s verified-ruff-version note is behind the
  venv.** Verified: venv ruff is 0.15.22; the deviation names 0.15.7/0.16.1.
  Gate still passes. Trivial. New (same drift family as register 1503).
  **Fix later** — when deviation (12) is next edited, with 1503.
- **CA-12 — test structure/config compliant.** Positive. **No action.**
- **CA-13 — coverage 58%, bimodal, no floor.** Verified (this session's
  run; `fail_under` absent; codecov informational). High as stated, but the
  decomposition (ranked item 3) sends it to PR-37 + existing register
  entries; the genuinely new actionable slice is TS-10's in-process list.
  **Already owned (PR-37) + fix later (TS-10).**
- **CA-14 — no `filterwarnings`.** Duplicate of TS-17. **Owner decision →
  fix** (ranked item 6).
- **CA-15 — caching design coherent and bounded.** Positive as to the
  bounds; round 2 caught that its original "LRU-bounded" phrasing was
  contradicted by open register entry 4056 (the shelf-cache access counter
  rebinds per subclass, so the eviction order is not actually LRU) — the
  report now says so and cites 4056. **No action beyond 4056's own entry.**
- **CA-16 — class-level mutable state, single-thread posture documented.**
  Positive (the docs state the contract; ground rule 2 forbids the
  alternative). **No action.**
- **CA-17 — `MemcachedCache` behavioral traps documented.** Verified
  present in the module docstring. **Restates register 4051** (sixteen
  defects, open) — the docstring treatment is the current recorded
  disposition; 4051 remains the tracking entry. **No new action.**
- **CA-18 — architecture legible; mixin discipline machine-checked.**
  Positive. **No action.**
- **CA-19 — documentation machinery exceeds the bar.** Positive. **No
  action.** (Its honest "(unverified)" on README examples is noted.)
- **CA-20 — sidecar `eval()` and five `pickle.load` sites.** Verified
  (`_shelves.py:97`; trust boundary documented at `:63-76`). Medium.
  New (no register entry). **Owner decision** (ranked item 5).
- **CA-21 — no Dependabot / pip-audit anywhere.** Verified (no
  `.github/dependabot.yml`; no audit gate in script or CI; `security.mdc`
  §2 and `dependency_management.mdc` §5 verified to require it; no recorded
  deviation covers it). Medium. New. **Owner decision** (ranked item 4).
- **CA-22 — unauthenticated SMTP to an internal relay.** Verified
  (`re_validate.py`, port 25, documented). Low. **No action** (internal
  batch tool; revisit only with CA-08).
- **CA-23 — security sweeps clean.** Positive. **No action.**
- **CA-24 — seven of eight runtime deps unbounded.** Verified
  (`pyproject.toml:11-25`; only `rms-pdslogger>=3.1.1` floored;
  `dependency_management.mdc` §3 verified). Medium. New. **Owner decision →
  small build PR** (ranked item 4).
- **CA-25 — tooling config consistent and single-sourced.** Positive. **No
  action.**
- **CA-26 — 13 TODO/FIXMEs, none issue-linked.** Verified (grep = 13; the
  `_properties.py:629` "real hack" confirmed). Low. New. **Fix later** —
  one tracking issue for the blocked-on-bundle family (TS-09's cluster) and
  one for the hack.
- **CA-27 — `FOEVER_FILE_CACHE_LIFETIME` typo is frozen.** Verified
  (`_preload.py:100`, manifest). **Waived** (deviation (2)) — correctly
  marked; recorded so it is not re-found.
- **CA-28 — debt is enumerated, not latent.** Positive. **No action.**
- **CA-29 — packaging excellent (pyroma 10/10, wheel verified).** Positive;
  pyroma re-confirmed by this session's gate run. **No action.**
- **CA-30 — license declared in pre-PEP-639 table form.** Verified
  (`pyproject.toml:26`). Trivial. New. **Decline for now** — take it when
  the setuptools floor makes it free.
- **CA-31 — `show_opus_products` ships but needs dev-only `tabulate`.**
  Verified (module-level import; pyproject comment; user-guide note).
  **Restates register 3100/3101, which hold it as an open owner decision**
  — the report's "none required" is too strong. **Owner yes/no** (ranked
  item 9).
- **CA-32 — the twelve pds3 shell scripts ship in the wheel.** Verified
  (wheel listing). **Waived** (deviation (6): frozen document-only; shipping
  documented scripts is coherent). **No action.**

## Register cross-reference summary

Findings that restate open register entries (no new entries are added by this
PR; this table is the input to that later decision):

| Register entry | Restated by | Notes |
|---|---|---|
| 1400 (five vacuous exception tests) | TS-05 | TS-05 adds two blackbox sites |
| 1401 (unused `expected` params) | — | **not re-found by any skill**; fixes half takes it from the register |
| 3100/3101 (`tabulate` dev-only import) | CA-31 | still an open decision |
| 3202 (subset-only transformation asserts) | TS-02 | the `viewset_lookup` half restates 3202's recorded content; the cached `test_childnames` half is new |
| 3401 (holdings fragments in tracked files) | — | **not re-found**; whitebox:393 verified still present; PR-36 fixes half owns the test module |
| 4042 (re_validate defects incl. encoding) | CA-04 (one site), CA-08 (family) | |
| 4056 (shelf-cache trim is not LRU; per-subclass counter) | CA-15 (contradicted its original "LRU-bounded" phrasing; caught by round 2) | |
| 4051 (MemcachedCache defects) | CA-17 | |
| 4103/4110 (helper.py issues) | TS-08 (related) | different defects, same files |
| 4203 / deferred 84 (PT014 duplicate row) | TS-11 | |
| 4205 (preload coverage gaps) | TS-10 (part) | |
| 4207 (MemcachedCache has one stub-tested method, no gate) | TS-10, TS-19/CA-13 (pdscache share) | open deferral, phase b of #77 — not a waiver |
| 4214 (tool tests contribute no measured coverage; 8.6x cost) | TS-20, CA-13 (part) | PR-37 owns |
| 4300 (no `testpaths`) | TS-21 | |
| 4304 / deferred 16 (`run_tests_coverage.sh` dead) | CA-03 | |
| 6502 (`--archives` "the the") | DOC-07 | deliberate; owner yes/no |
| 1003 → issue #149 (docstring roles sweep) | DOC-08 | waived, correctly |

Entries 3200/3201 (zero-coverage public methods rms-viewmaster calls) were not
individually restated but sit inside the TS-19/CA-13 umbrella; they remain the
register's own.

The review rounds surfaced four candidate register-grooming items, recorded
in `critiques/pr-36/` per §6.6 and left for the owner (no register edits in
this PR): entry 6404 appears stale (the maintenance tools' docstrings now
carry 0 `Args:` sections, matching the doc report's measurement); entry 1000
appears stale (both `_derived_paths.py` docstring defects it records are
fixed in the tree — "Return the log file path for this index file." and the
returns-a-tuple wording); deviation (4)'s pdscache-row phrasing ("no test
here exercises") is imprecise given the stub-tested method and belongs with
entry 1503's deviation-drift family; and the plan's §6.6
compliance-schedule row for module lengths still names the
pre-deviation-(3) waiver list.
