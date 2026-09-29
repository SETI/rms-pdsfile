# PR-33 round 1 — full diff, deepest on the architecture and subsystem chapters

Reviewer: a fresh, no-context subagent given the PR-33 plan section, the Phase 7
preamble, the §2 ground rules, §6.1–§6.7 with the progressive-compliance schedule, the
exact diff `git diff 96de70a..e4128b3`, and read access to the repository and the
holdings roots, with the instruction to verify every prose claim against the source
rather than against the diff. It made no edits.

The reviewer independently reproduced the cheap gates: both Sphinx builds into its own
scratch directories (exit 0, 78 of 78), all five Mermaid sources re-extracted and
rendered with mmdc (five SVGs, no dead block), `pytest tests/docs tests/api` (30
passed), both ruff passes, the deferred-351 greps (0 and 0), the CDN measurement (71
of 107 pages, `mermaid@11.12.1` — matching the record exactly), both record checkers
(8 and 27 stale, unmoved), the frozen-file and `pyproject.toml` byte-identity, the
collection counts against the recorded suite numbers, and the register arithmetic. It
verified all five diagrams edge-by-edge against `pdsfile.py:185`, `_preload.py`,
`_shelves.py`, `new_pdsfile()`/`child()` and the rule-module registration tails, and
the subclass counts by import. **No diagram defect was found.**

Verdict: **goal not met** — five Major findings, six Minor, two Deferred.

## Major findings, and their resolutions

Every finding was re-verified against the source before any fix was made.

**M1. `dev_guide_extending_tools.rst` claimed `pds4archives` differs from
`pdsarchives`'s spec "in exactly [the identity group], plus the sentinel".** False:
comparing the two `SPEC` blocks shows nine differing fields — the four identity
fields, all three flavor fields (`.csv`, `normal`), `log_path_method` and
`handler_factories` (which adds a warning handler). **Fixed**: the passage now
enumerates the nine, states that the parser texts and log suffix are shared from
`_archives_common`, and that the two archive callables are each module's own function
of the same name (the reviewer's own "shared callables" reading would itself have
been wrong, which the fix avoids).

**M2. The cross-reference goal was not met: ~20 published API members appeared in
prose as bare inline literals** (`new_pdsfile`, the `associated_*` family, the index
row and filesystem methods, the sorting pair, three cache methods, `version_ranks`,
`is_category_dir`, `description`, `opus_id` and more), and validation-record §6
claimed literals were used only for unpublished names — a false record claim.
**Fixed**: all of the named members now carry `:meth:`/`:attr:` roles; the `-n -W`
build was re-run and exits 0 with 0 problem lines, which is the proof the new targets
resolve; record §6 was rewritten (and now names round 1 as the pass that caught it).

**M3. `dev_guide_ci.rst` called the self-hosted driver "a documented superset of the
script's pytest gate" running "the whole tree".** False: the driver enumerates seven
directories and `tests/docs/` is not among them, so it is neither the whole tree nor
a superset. **Fixed**: the chapter now states the enumeration and where the docs
gates actually run; the intro's "wrapper or documented superset" framing was
rewritten; the coverage gap is recorded as observation 4316.

**M4. Two pages said no mixin module imports `pdsfile.pdsfile` back, unqualified.**
Overstated: `_opus.py:290` holds a function-local `from pdsfile.pdsfile import
PdsFile`, which is the pattern `tests/api/test_mixin_import_isolation.py` explicitly
sanctions — the pinned rule forbids module-level back-imports only. **Fixed**: both
passages now say "at module level" and name the function-local escape hatch.

**M5. "The three star imports" in `pdsfile/__init__.py`.** The file holds two star
imports plus an explicit aliased re-export of `PdsFile`. **Fixed**: the sentence now
says so.

## Minor findings, and their resolutions

1. `delete_multi` "exists only on the dictionary flavor" — it is *defined* on both
   and raises `AttributeError` on every memcached call. **Fixed**: "works only",
   with the raise named.
2. "the configuration tables … are ``None`` on the base class" — the bundle-set
   regexes are absent from the base entirely, not ``None``. **Fixed**: "missing or
   ``None``", with both kinds named.
3. "each constructor consults the class-level cache before building anything" —
   `child()` touches the entry and rebuilds regardless; the cached object wins
   inside `_complete`. **Fixed**: the sentence now routes the claim through
   `_complete`.
4. "the dictionary flavor is the one every test here exercises" —
   `test_pdscache_set_multi.py` drives `MemcachedCache` against a stand-in client.
   **Fixed**: "no test here reaches a live memcached server".
5. "shelf keys are interior paths" unqualified — true of info/link shelves only.
   **Fixed**: qualified.
6. The `full_holdings` marker paragraph implied the tool tests use fingerprints
   *instead of* the marker — 15 of the 28 tool-test modules carry both. **Fixed**:
   the paragraph now states both guards and what each is for.

## Deferred

1. `tests/docs/` absent from the self-hosted driver's enumeration → **added as
   observation 4316** (Gates, tooling and CI).
2. The stale `__all__` in both `rules/__init__.py` modules → already recorded as
   observation 4111; no new entry.

## What the reviewer could not verify

The full-data run itself (per mandate it verified the evidence, not the suite); the
drafting-history claims in the record (the four markup-gate catches, the two
mmdc-caught diagram defects); the exhaustiveness of the mixin docstrings' attribute
enumerations; that the complete holdings carry the reference root's content; the
Viewmaster-deployment claims.

## Gates after the fixes

Every fix in this round touched only `docs/` pages and `critiques/` records, so the
full-data record carries forward under §6.6 step 5; `run-all-checks.sh` was
nonetheless re-run in full on the corrected tree and passed with the same numbers
(1205 / 34, both Sphinx builds 0 problem lines, 78 of 78), which is also the proof
that the ~20 new cross-reference targets resolve.
