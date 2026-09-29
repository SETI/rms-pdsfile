# PR-35 round 1 — full diff

Reviewer: a fresh, no-context subagent given the PR-35 plan section, the §2 ground
rules, §6.1–§6.2, the §6.6 procedure with the progressive-compliance schedule, the
exact diff `git diff docs/readme-rewrite..HEAD` (56 files at `f5626d9`), and read
access to the repository, the holdings roots, and the consumer repos, with the
central instruction that stubtest cannot check whether the annotated types are
TRUE, so its job was verifying stub types against the implementation — chasing
every narrow type, each wrong-narrow one a Major. It made no edits.

The reviewer independently reproduced: the stubtest gate (`Success: no issues
found in 79 modules`); a wheel build containing all 43 `.pyi` + `py.typed`; the
untouched freeze files and a passing `test_api_freeze.py`; both ruff invocations
with the per-file-ignores table unchanged; the `ENABLE_*` wiring and the hosted
lint job's `.[dev]` install reaching mypy; the two-entry allowlist's justifications
against the code; and that no file under `src/pdsfile/**/*.py` changed, so the
recorded suite numbers cannot be stale (record commit postdates the last stub
commit). It read the implementation behind every module stub and sampled six rule
stubs, plus consumer call sites in rms-opus and rms-viewmaster. It confirmed the
hard cases it checked (`Self` on `copy`/`new_merged_dir`, the `CACHE` union,
`abspath: str | None`, `viewset_lookup -> PdsViewSet | None`,
`internal_link_info`'s three shapes, `abspaths_for_basenames -> list[str | None]`,
`MemcachedCache.set -> bool | None`, `is_blocked -> int`, VG_28xx's `*_DICT: str`).

Verdict: **goal not met** — two Major, four Minor, no new Deferred.

## Major findings, and their resolutions

**M1. Wrong-narrow pair: `volume_publication_date`/`volume_version_id` declared
`str` while the base members they return verbatim are declared `Any`.**
`pds3file/__init__.pyi` said `-> str`; the implementations return
`bundle_publication_date`/`bundle_version_id` unchanged, and `_properties.py:2171`
returns the raw CACHE-derived `_volume_info[3]` unsliced whenever it is truthy
(only the fallbacks slice `[:10]`), `:2220` returns `_volume_info[2]` as-is. The
derivation row behind the `str` claimed "every path returns a str", which is false
against the code — the author's two derivation passes contradicted each other and
the wrong one won in the subclass stub. **Fixed:** both aliases now `-> Any`,
matching the base; the two derivation rows corrected with the false clause named
(`derivation-pds3file-pds4file.md`).

**M2. Wrong-narrow return: `pdsfiles_for_logicals -> list[PdsFile]` can contain
`None`.** `_sorting.py:778-782` maps `from_logical_path` — `PdsFile | None` by
these stubs' own declaration — over the input with no filter when
`must_exist=False` (the default); the reviewer reproduced `[None]` at runtime, and
the executor re-reproduced it before fixing. **Fixed:** `list[PdsFile | None]` in
`pdsfile.pyi`. The siblings were audited for the same hole before the fix:
`pdsfiles_for_abspaths` and `pdsfiles_for_basenames` delegate to `from_abspath`
and `child`, neither of which has a None path, so they stay `list[PdsFile]`.

## Minor findings, and their resolutions

**m1. `COUVIS_0xxx.DATA_SET_ID -> str` not derivable under the PR's own rule.**
The value is untyped pdstable row content, the same flow that made the base
`data_set_id` property `Any`. **Fixed:** `-> Any`, with the corrected row in the
new `derivation-rule-classes.md`.

**m2. Record miscounts.** "27 pds3 + 9 pds4" rule modules (the tree has 25 pds3),
and one "44 stubbed modules" against every other count's 43. **Fixed:** both
numbers corrected in `pr-35-validation.md`.

**m3. The seven hand-derived rule-class methods had no evidence rows,** and
`derivation-core.md` asserted "rule classes override with ints", contradicted by
the three method overrides. **Fixed:** `derivation-rule-classes.md` added with a
row per method and the generator's type-table rationale; the core row now names
both override shapes. Writing those rows surfaced one more instance of M1's
defect shape, fixed in the same pass: `COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH`
was declared `-> Pds3File`, narrower than its delegates' declared types
(`from_logical_path -> PdsFile | None` with the None path unreachable on nonempty
input, `from_abspath -> PdsFile`); it is now `-> PdsFile`.

**m4. `extend-exclude = ["*.pyi"]` was repo-wide.** A future `.pyi` outside the
package would silently escape ruff. **Fixed:** scoped to
`"src/pdsfile/**/*.pyi"`, with the comment noting the scope.

## Gates after the round's fixes

The fixes touch five `.pyi` files, `pyproject.toml`'s ruff exclusion, and records
— nothing under `src/pdsfile/**/*.py` — so per §6.6 step 5 the full-data record
carries forward. Re-run after the fixes: stubtest (`Success: no issues found in
79 modules`, exit 0), `ruff check src/pdsfile tests scripts docs` (passes; the
scoped exclusion still covers all 43 stubs), API-freeze (passes).
