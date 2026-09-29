# Modernization Plan vs. the 2025 Code-Quality Analysis

**Date:** 2026-07-19
**Compares:** `plans/2026-07-17-modernization-plan.md` against
`critiques/2025-08-15-code-quality-analysis.md` (the issue #79 analysis).
**Question answered:** which of the analysis's findings does the plan fix,
and which remain after the rewrite?

## Summary

The plan fixes the analysis's **testing** complaints in full and its
**monolith** complaint at the file/module level, fixes its **error-handling
examples** as targeted bugs, and **deliberately defers or rejects** its
architectural-redesign items. The deferrals are not oversights: the owner's
locked ground rules (100% public-API freeze; issue #77 "phase a now, phase b
later"; no YAML rule-data extraction) exclude exactly the changes the analysis
says require breaking the API. The analysis's closing recommendation — "a
complete architectural redesign rather than incremental improvements" — is the
one thing the plan explicitly does **not** do; the owner chose the opposite
strategy (compatibility-preserving mechanical modernization first, redesign as
a possible phase "b").

## Finding-by-finding disposition

### Fixed by this plan

| Analysis finding | Where fixed | Notes |
|---|---|---|
| §8 Testing complexity: brittle hard-coded expectations, huge test files, poor isolation, dependence on external data | Phases 3–4 (PR-08–PR-14) | The plan's centerpiece. Hermetic fixture tree in a separate public repo; dual golden sets (full/mini); graceful skip without holdings; `full_holdings` markers; per-dataset rule tests extracted and standardized (issue #37); pytest-xdist parallelism; hermetic GitHub CI on 3 OSes; nightly full-data runs retained. Mechanism differs from the analysis's factory/fixture suggestion — goldens are kept but machine-regenerated (`--update`), never hand-edited — and isolation from real holdings is achieved. |
| §1 Monolithic god class (6,300 lines) — *file-level aspect* | Phase 5 (PR-16–PR-22) | `pdsfile.py` decomposes into ~10 focused modules (shelves, local-fs, OPUS, index rows, associations, sorting, derived paths, preload, properties, path utils); core lands at ~1,750 lines. See "partially" below for the class-design aspect. |
| §7 Error handling — the *specific defects* | PR-15, PR-26, PR-28 | Bare `except:` at `pdsfile.py:3020`; the silent `self._recache` no-op; `resume_caching()` missing arg; `iconset_for` undefined name; pdscache `set_multi` bugs; the maintenance tools' `LOGDIRS` shadowing, `checksum1 != checksum1`, `abs(str != str) > 1`, and `shelf_consistency_check`'s undefined `error` — each fixed with a regression test. |
| No tests for the maintenance tools (implicit in §8) | PR-13 (+PR-10) | Full init/validate/corrupt/repair/update cycle tests per tool pair, on the fixture tree. (The analysis did not call this out directly; it falls under its test-strategy umbrella.) |

### Partially addressed

| Analysis finding | What the plan does | What remains |
|---|---|---|
| §1 God class — *single-responsibility design* | Method groups become mixins in separate private modules; each module has a stated contract in the dev guide (PR-33). | The class surface is unchanged (API freeze): one `PdsFile` still exposes everything. True separation into `FilePathParser`/`FileMetadata`/`FileCache`-style collaborating classes is an API break — explicitly deferred to phase "b" (§7 risk table of the plan records this). |
| §6 Rule-file complexity (data mixed with code) | PR-27 isolates the large `REPAIRS` table into a data module; PR-30 adds standard header docstrings to every rule module; PR-24 lint-cleans them; PR-33 ch. 4 documents how to write one. | The `TranslatorByRegex` tables stay in Python. Extraction to YAML/config was **rejected by owner decision** (ground rule 2), not deferred by omission. |
| §7 Error handling — *systematic design* | The concrete silent-failure bugs are fixed (above); behavior is otherwise frozen. | No custom exception hierarchy, no consistent raise-vs-warn policy, no recovery strategy — changing what raises is a behavior/API change, phase "b". |

### Remaining after this plan (deliberate, per locked decisions)

| Analysis finding | Why it remains |
|---|---|
| §2 Attribute explosion (~40 `_X_filled` slots per instance; memory waste; no invalidation strategy; no thread safety) | The lazy-property block moves to `_properties.py` verbatim (PR-22). Redesigning the fill/cache mechanism changes observable behavior; phase "b". The dev guide documents the single-process assumption. |
| §3 `from_path` complexity | Ground rule 2 explicitly excludes the structured path-parser rewrite. |
| §4 Multi-layer caching strategy (class + instance caches, arbitrary limits, cleanup) | Ground rule 2 explicitly excludes a dependency-injected cache manager / caching-library adoption. Only the two concrete pdscache bugs are fixed. |
| §5 Regex pattern explosion | The regexes *are* the frozen behavior; nothing replaceable without behavior change. The dev guide documents the resolution flow instead. |
| Performance section (synchronous I/O, repeated fs calls, no batching, regex compile cost, parse complexity) | All are behavior-adjacent optimizations outside a compatibility-preserving rewrite; none scheduled. |
| Success metrics: core class < 500 lines; cyclomatic complexity < 10/method; per-instance memory −50% | Not adopted. The plan's own targets are ~1,750-line core, ≥90% hermetic test ratio, identical full-data pass/fail set vs. baseline, and 100% API-manifest identity. |

### Plan work outside the analysis's scope

The plan also delivers items the analysis never raised: the mechanically
enforced public-API freeze manifest; consolidation of the 70–85%-duplicated
pds3/pds4 maintenance-tool pairs onto a shared core (Phase 6); complete user
and developer documentation (Phase 7); CI/packaging modernization to the
repo-template conventions (Phases 1–2, 4); and public-API type stubs (PR-35).

## Bottom line

Of the analysis's seven "critical issues": #8 (testing) is fixed outright;
#1 (monolith) is fixed at the granularity the API freeze permits; #7 (error
handling) is fixed where it was concretely broken; #2, #3, #4, #5 (attributes,
parsing, caching, regexes) and #6's data-extraction half remain by explicit
owner decision, reserved for a possible phase "b" once the modernized,
fully-tested, documented baseline from this plan exists. That sequencing is
the point: after this plan, any future redesign starts from a hermetically
tested, API-manifested codebase instead of an untested monolith.
