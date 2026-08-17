# Owner four-items fix — validation

Base: `b8c1ac1` (`rewrite`). Branch: `fix/owner-ruling-four-items`. Owner
instruction of 2026-08-16, recorded in
`plans/2026-08-16-addendum-owner-four-items.md`: fix the four items each parked
for a ruling — observation 3402 (the Python floor in the rules), the ruff
`.pyi` exclusion, observation 4064 (`exit -1` in the copy/setup scripts) and
observation 4062 (no PDS4 archive product can be built) — verifying each
against the current tree before acting.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3, ruff 0.15.7), from the
tree being measured. Where holdings are needed the environment carried
`PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`,
resolving to the limited testing copy the goldens are tuned to. The real
holdings roots were never written; every build ran in a `tmp_path` tree or a
scratch copy.

## 1. Observation 3402 — the Python floor

**The sweep, recounted rather than assumed.** `git grep -l "3\.10"` at the
base over every tracked `*.md`, `*.mdc`, `*.rst`, `*.toml`, `*.yml`, `*.cfg`,
`*.py`, `*.txt` and `*.sh` returned 28 files. They classify as:

- **Claims about this tree's floor or matrices — fixed, 4 files.**
  - `.cursor/rules/pdsfile_overrides.mdc` — deviation (8) said the self-hosted
    matrix runs 3.10–3.13 and the hosted job 3.10/3.13; the workflow runs
    3.11/3.12/3.13 and 3.11/3.13 (`.github/workflows/run-tests.yml:92-96,49`).
    Deviation (10) said "The Python floor is 3.10". Both now state the 3.11
    matrices and the 3.11 floor with `pyproject.toml`
    (`requires-python = ">=3.11"`, line 10) as the authority. Deviation (10)
    no longer overrides `python.mdc`; the entry says so and why it stays.
  - `plans/2026-07-25-modernization-plan.md:243,442,453` — the CI-state line,
    PR-14's matrix line and PR-14's "record the actual matrix" parenthetical,
    all written when the floor was 3.10, now carry the 3.11 values with a
    note naming #146 as when the floor moved. The third of these was found by
    review round 1 after the first sweep's classification pass missed it.
  - `.cursor/rules/environment.mdc:54` — the `requires-python` example read
    `>=3.10`; in this repository's rules an example that contradicts the tree
    reads as a claim, so it now reads `>=3.11`.
  - `.github/workflows/run-tests.yml:89` — "MacOS: Python 3.8-3.10 does not
    currently work on MacOS" explained a macOS matrix bound that the 3.11
    floor now implies; the stale line is removed.
- **Illustrative scenarios in the skills, not claims — left, 2 files.**
  `.cursor/skills/critique-test-suite/SKILL.md:163` ("Old `skipif` for Python
  3.8 when the project requires `>=3.10` is dead code") and
  `.cursor/skills/python-codebase-analysis/reference.md:53` (a worked example
  whose fictional CI matrix is "3.12 only", which this repository's never was)
  are self-contained teaching examples; neither states this tree's floor.
- **Historical records — left, 22 files.** 21 `critiques/` round, validation
  and register files, and the archived v1 plan, all of which measure what was
  true when they were written (several literally record runs on CPython
  3.10); rewriting a measurement is falsifying it. Two of the register's
  matches were the 3402 entry itself, which leaves with the discharge.

After the fix, `git grep -l "3\.10"` over the same set returns the 22
historical records, the two skills files, the active plan (whose two
remaining mentions are the self-describing "3.10 until the floor moved with
#146" parentheticals this fix added at lines 243 and 443), and this fix's
own records — the addendum, this file, and whichever round records under
`critiques/owner-four-items/` quote the literal digits (round 1's does) —
all naming 3.10 referentially. No claim survives; the matching set grows
with rounds that quote the digits, which is why this sentence names the
sets rather than a total.

The digits are not the only spelling. A second sweep for ruff's form,
`git grep -ln "py310"` under `plans/`, returns nine completed-PR subplans —
the seven `2026-07-27-pr-16` through `-22` files, `2026-08-03-pr-23` and
`2026-08-04-pr-24` — each recording the `--target-version py310`
configuration their ratchet re-derivations actually ran under, which was
`pyproject.toml`'s value at the time (plus the archived v1 plan and its
archived subplan, and three `critiques/` round records). They are records of
completed work (historical, like the archived v1 plan, though they live in
`plans/`); pr-23's "i.e. `pyproject.toml`'s" clause is the one reading
closest to a present-tense claim, and whether it warrants an annotation is
left to the owner with this note.

## 2. The ruff `.pyi` exclusion

**The measurement.**
`ruff check $(git ls-files ':(glob)src/pdsfile/**/*.pyi')` (explicit paths
bypass `extend-exclude`; project configuration otherwise) over all 43 stubs,
taken with ruff 0.15.7 and re-taken under the venv's 0.15.22 with the
identical distribution. The command's shape is load-bearing twice over, and
both traps were caught by a review round measuring rather than reading: a
shell without `globstar` expands a bare `**` to one level (2 findings over 2
stubs), and git's default pathspec makes `**/` match only names containing a
real slash, dropping the five top-level stubs (75 findings over 38 — without
`pdsfile.pyi`, which holds 23 of the 26 uncovered findings below). The
`:(glob)` form returns 43 files, verified by count:

```
31 N801   29 E501   25 N999   5 N802   5 A002   2 RUF022   1 N805
Found 98 errors.
```

Every code is one the permanent ratchet already carries somewhere in the
runtime tree. Mapping each stub's findings against **its own** `.py`
counterpart's `per-file-ignores` entry:

- **72 findings are covered**: every N801/N999/N802/N805 in the rule stubs,
  `pds3file/__init__.pyi`'s A002 x2, both RUF022, and the E501 in stubs whose
  counterpart entry lists E501.
- **26 findings are not**: `pdsfile.pyi` E501 x20 and A002 x3 — the class
  surface aggregates mixin modules (`_derived_paths.py` carries the A002
  entry for the same frozen `dir=` parameters), and `pdsfile.py`'s own entry
  is `["B904", "I001", "RUF012"]` — plus one E501 each in
  `cassini_iss_fring_mosaics_rsfrench2025_primary_filespec.pyi` (counterpart
  entry `["W191"]`),
  `cassini_uvis_solarocc_beckerjarmak2023_primary_filespec.pyi` and
  `uranus_occs_earthbased_primary_filespec.pyi` (counterparts have no entry).

**The decision the measurement makes.** Linting the stubs with the same
permanent ignores their counterparts carry would still fail on those 26, so
bringing the stubs under the gate requires new ratchet entries — and the
ratchet may only shrink, with inline `noqa` prohibited. The exclusion
therefore stays, and its comment now states this measurement instead of the
previous unmeasured claim (which was also wrong: it said "only the naming
codes", and E501/RUF022 are not naming codes). `stubtest` remains the stubs'
gate and passed in the full run (section 5).

## 3. Observation 4064 — `exit -1` in the copy/setup scripts

**Every site verified reachable only by an invalid invocation.** The twelve
sites, re-read in the current tree before the change: `setup_new_holdings.sh`
lines 11, 18; `copy_documents.sh` 10, 19, 24; `copy_shelves.sh` 10, 20, 25;
`copy_all_except_metadata.sh` 9; `create_fake_volumes_for_metadata.sh` 11,
19, 24. Each is either the argument-count guard or a
directory-does-not-exist check on a command-line argument, and each precedes
the script's first `mkdir`/`cp`. None is reachable by a valid invocation —
the same test PR #155 applied under the 2026-08-07 exit-code ruling
(deferred-observations entry 135). All twelve became `exit 1`.

**What documents and tests say about the status.** The user guide's shell
scripts chapter says only that the scripts "print their usage and exit"
(`docs/user_guide/user_guide_shell_scripts.rst:52`) — no numeric status
anywhere in `docs/`. No test asserted 255: the only 255 mentions under
`tests/` are `test_update_holdings_script.py`'s comments explaining why that
script's guards are pinned at 1. The new
`tests/holdings_maintenance/test_copy_setup_scripts.py` runs each script's
argument-count guard for real (status 1, usage printed) and pins the absence
of `exit -1` across all five texts.

**Out of scope, deliberately.** `scripts/automated_tests/pdsfile_main_test.sh`
carries eight `exit -1` sites of its own, but they are failure paths of valid
invocations (a gate failing), not usage guards; the observation, the ruling
and the owner's lift name the five holdings-maintenance scripts only.

## 4. Observation 4062 — the PDS4 archive products

**Reproduction, before the fix.** At `b8c1ac1`:

```
>>> Pds4File.from_logical_path('checksums-archives-bundles/uranus_occs_earthbased_md5.txt')
ValueError: Illegal bundle set directory "uranus_occs_earthbased_md5.txt": checksums-archives-bundles
  (pdsfile.py:1486, in child)
```

and the same ValueError from `child()` directly. Tool-level, the three tests
of `tests/holdings_maintenance/test_pds4_archive_products.py`, run with the
fix stashed, all fail in it: `pds4checksums --initialize` over
`archives-bundles/<set>`, the same with `--archives` over `bundles/<set>`,
and `pds4infoshelf --initialize` over `archives-bundles/<set>` each die
logging `**** ValueError Illegal bundle set directory
"uranus_occs_earthbased_md5.txt": checksums-archives-bundles`. That is the
negative control: the new tests fail for the recorded reason against the old
pattern.

**The fix, derived from PDS3.** `Pds3File.BUNDLESET_PLUS_REGEX` appends three
groups to the volset name — version, category suffix, `_md5.txt`/`.tar.gz`
ending — yielding five groups: (name, version, combined tail, category,
ending). The PDS4 pattern appended only a repeating version group, two groups
in all, and no ending, which is the whole defect. It now appends the same
tail with the version alternatives PDS4 admits (`_vN.N`/`_vN.N.N`, still
star-quantified) and the category alternatives a `pds4-holdings` tree has
beside `bundles/` (`_diagrams`, `_metadata`, `_previews` — the tree has no
`calibrated/`), giving the identical five-group structure. That structure
matters because the consumers index by position through shared code:
`child()` (twice) and `from_path()` in `pdsfile.py`, and `split_basename()`
and `sort_keys()` in `_sorting.py`, all take the PDS3 arm when
`len(groups) > 2`.

**Observable deltas beyond the intended one, measured.**

- Acceptance is a strict superset: `((?:A|B)*)` accepts exactly what
  `(A|B)*` accepts, so every previously-resolving basename still resolves.
- For unversioned names, group 2 is now `''` where it was `None` (the star
  group's last-iteration capture). `child()` already guarded
  (`'' if group(2) is None`), `version_info(None)` and `version_info('')`
  both return the "Current version" rank, and `split_basename()` on a PDS4
  bundle set now returns `(name, '', '')` where it returned `(name, None,
  '')` — the PDS3 shape. No test pinned the `None`.
- For names with **repeated** version suffixes, group 2 is now the whole run
  (`_v1.0_v2.0`) where it was the last repetition (`_v2.0`), so
  `version_info` on it raises ValueError and `child()` now rejects such a
  name where it previously resolved it under the last suffix's rank. No such
  name exists in any holdings tree (no PDS4 bundle set is versioned at all),
  and the name itself still matches the pattern, which the regex test pins.

**The freeze gate.** `pytest tests/api/` — 26 passed; `git diff` over
`tests/api/api_manifest.json` empty. The manifest records names and
signatures, and the change is the value of a module-level pattern.

**Both directions pinned.** `tests/pds4file/test_pds4file_bundleset_plus.py`:
15 accepted names with their exact five groups (checksum and archive endings,
category suffixes, versioned and repeated-version names, the hyphenated
bundle set, the prefix-of-three `cassini_iss`), 10 still-rejected names
(arbitrary word, trailing garbage, PDS3 volset and version shapes,
`_volumes`/`_calibrated`/`_bundles` suffixes, a bundle name), the
case-insensitive twin, and the PDS3/PDS4 group-structure parity.

**The products, built for real.** In the module's temporary tree
(`test_pds4_archive_products.py`): `pds4archives --initialize` writes
`archives-bundles/uranus_occs_earthbased/uranus_occs_earthbased.tar.gz`;
`pds4checksums --initialize` over `archives-bundles/<set>` then writes
`checksums-archives-bundles/uranus_occs_earthbased_md5.txt` whose one entry
is the tar's md5, recomputed independently by the test; `--initialize
--archives` over `bundles/<set>` writes the identical manifest; and
`pds4infoshelf --initialize` over `archives-bundles/<set>` writes
`_infoshelf-archives-bundles/uranus_occs_earthbased_info.pickle` and its
sidecar, whose line for the tar records the tar's on-disk size. Separately,
the user guide's build chain for `cassini_uvis_solarocc_beckerjarmak2023`
(the concepts chapter's example) was run against a scratch copy of that
bundle set: the five build commands — both checksum-and-shelf pairs and the
archive between them — exit 0 and both archive-side products exist. The
sixth command, `pds4linkshelf`, writes its shelf and exits 1 carrying the
bundle's documented recurring link error, exactly as the chapter's own text
below the code block states (round 3 measured it; the first version of this
sentence claimed exit 0 for all six, having run only the five). The
chapter's build-order section previously documented the archive-side gap as
a fact of the tree and now shows the full chain.

**The s-mode skips, checked as directed.** `pytest tests/pds4file/
tests/rules/pds4/ --mode s -rs`: 31 skips before the change, 31 after, and
every one is a `cassini_iss_fring_mosaics_rsfrench2025` /
`cassini_iss_spokes_hedman-hamilton-2024` rule/viewset/opus-type skip
(those bundle sets are not in the limited holdings). None relates to missing
archive-side shelves.

## 5. Gates

`./scripts/run-all-checks.sh -w auto` with full holdings, run to green and
the whole log read (456 lines, no gate's output truncated):

- ruff check and ruff indentation: passed. (The first run failed on the PR's
  own new code — 4 em-dashes in the pds4file docstring against the U1
  docstring rule, PT006 and PT018 in the new test module — all fixed; no
  ratchet entry touched.)
- pytest `--mode ns`: **1227 passed, 34 skipped** = baseline 1191 + exactly
  the 36 new ids (6 in `test_copy_setup_scripts.py`, 3 in
  `test_pds4_archive_products.py`, 27 in
  `test_pds4file_bundleset_plus.py`); skips unchanged. The only warnings are
  `julian`'s pyparsing deprecations, present at base.
- pyroma 10/10; API-freeze passed; clean-install gate passed; stubtest
  passed; both Sphinx builds 0 problem lines, 77 of 77 modules; PyMarkdown 2
  files passed.
- `--mode s` pds3 (`tests/pds3file/ tests/rules/pds3/`): **555 passed,
  3 skipped** — the baseline exactly.
- `--mode s` pds4 (`tests/pds4file/ tests/rules/pds4/`): **150 passed,
  31 skipped** = baseline 123 + the 27 regex ids; skips unchanged.

## 6. The register

Entries 3402 (p2), 4062 and 4064 (p3) are discharged, and the review rounds
added three: 4065 (two cosmetic defects in the copy scripts' guard messages,
out of the lifted freeze's scope), 4066 (`from_path`'s extension assembly
misreads category-suffixed checksum basenames — pre-existing, and exact
PDS3/PDS4 parity after this fix) and 4129 (the two-group regex arms and the
`None` guard in the shared consumers no longer have a caller). Counts
verified by `grep -c "^### "`: scheduled 10, p1 0, p2 15, p3 136, p4 52 —
**213 open**, and the index's closure arithmetic moves 24 → 27 since closed
with the three entries named against the addendum and 9 → 12 found during
the later work. The p2 range tightens to 3000–3401 (3402 was its last
entry).
