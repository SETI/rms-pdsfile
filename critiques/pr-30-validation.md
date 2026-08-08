# PR-30 validation — Google-style docstrings, the 36 rule modules

Base: `c4811d8`. Branch: `pr-30-docstrings-rules`. Base branch: `rewrite`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), from the tree being measured, with
`PYTHONPATH=$PWD/src`. Where holdings are needed the environment carried
`PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree is
a second worktree at the same commit, so "base" numbers were measured, not recalled.

Nothing here is inherited. Every number carries the command that produced it, and section
11 lists the numbers this PR was handed that did **not** reproduce.

## 1. Scope

The 36 rule modules, and only these: 26 under `src/pdsfile/pds3file/rules/` and 10 under
`src/pdsfile/pds4file/rules/`. Both counts include the package's `__init__.py`; the pds4
count includes the three `*_primary_filespec.py` modules, which hold one literal list each.

    python critiques/pr-29/measure.py src/pdsfile/pds3file/rules/*.py \
                                      src/pdsfile/pds4file/rules/*.py

Measured at base: **12,595 lines**, 31 classes, **7 functions**, 3 parameters excluding
`self` and `cls`. **Not one of the 36 modules had a docstring, not one of the 31 classes
had one, and 3 of the 7 functions had none.** The four function docstrings that existed
were one line each and carried no Google section of any kind.

## 2. What changed

Docstrings only. **36 module docstrings, 31 class docstrings and 7 function docstrings**
(3 new, 4 rewritten) -- 74 in all, 1,992 lines added against 8 removed. Section 3 proves
that no executable statement moved.

Three comment lines were deleted and none was added or reworded; section 3.2 enumerates
them.

`critiques/pr-30/` carries the one script this record cites that PR-29 and PR-29a did not
already have: `check_rule_tables.py`, described in section 4, and the four round records.
No script of PR-29's or PR-29a's is edited here; both are used unchanged.

## 3. Proof that the change is docstrings only

### 3.1 The AST hashes

`critiques/pr-29/strip_docstrings.py` parses a module, deletes the docstring node of every
module, class and function, and hashes `ast.dump` of what is left with
`include_attributes=False`, so line and column shifts do not register.

    python critiques/pr-29/strip_docstrings.py src/pdsfile/pds3file/rules/*.py \
                                               src/pdsfile/pds4file/rules/*.py

Run in both trees and sorted, the two 36-line outputs are byte-identical: **all 36 pairs
of hashes match.** PR-29 established that this check is not vacuous, with five mutations of
a documented file; the script is used here unchanged.

### 3.2 The comment enumeration, which the AST cannot see

    python critiques/pr-29/check_comments.py <base tree> <head tree> \
        pds3file/rules/ASTROM_xxxx.py ... pds4file/rules/uranus_occs_earthbased.py

`check_comments.py` joins its module arguments under `src/pdsfile/`, so the 36 names are
given with their package path. **Three comment lines were removed and none added**, and
all three are in the two `rules/__init__.py` modules:

| file | comment lines at base | at head | removed | added |
|---|---:|---:|---:|---:|
| `pds3file/rules/__init__.py` | 158 | 156 | 2 | 0 |
| `pds4file/rules/__init__.py` | 176 | 175 | 1 | 0 |

The exact text:

    pds3file/rules/__init__.py    #
                                  # Definitions of Translator objects used by the PdsFile class.
    pds4file/rules/__init__.py    # Subclasses of PdsFile, encompassing dataset-specific information

Both description lines are what `doc_python.mdc` section 4 requires be a module docstring,
and every fact each carried is in the docstring that replaced it. The bare `#` removed
from the pds3 banner is the separator that line sat under; the pds4 banner keeps its `#`
because its `TODO` line still sits under it. **The `TODO` line itself is untouched**, and
so is every other comment in all 36 files: 33 of the 36 report identical counts, and the
diff over the other three is the three lines above.

## 4. The rule-table checker -- the mechanical gate this PR needed

`critiques/pr-30/check_rule_tables.py` was written and mutation-tested **before any of the
prose**, because the defect this PR risks is the copy-paste one: 36 near-identical headers,
sharing a vocabulary in which `description_and_icon_by_regex` appears in 26 modules,
`associations_to_metadata` in 22, `default_viewables` in 22 and `opus_products` in 18,
while `s_rings_viewables`, `spice_lookup`, `dsntrack_viewables`, `skyview_viewables` and
`_f_ring_cross_products_list` each appear in exactly one.

| code | check |
|---|---|
| T0 | the module has no docstring, so nothing else can be evaluated |
| T1 | the docstring names a rule table this module does not define and a sibling does |
| T2 | the module defines a top-level rule table its docstring does not name |
| T3 | the docstring backquotes an identifier no rule module defines and this one does not import |
| T4 | the docstring's summary line does not name the module it documents |

A "rule table" is **any top-level assignment to a plain name**, dunders excluded from T2
and permitted in T1 and T3. That includes `VG_28xx.py`'s eighteen lookup dictionaries and
the `PRIMARY_FILESPEC_LIST` of the three `_primary_filespec.py` modules, which are not
translator objects. Drawing the line anywhere else would need a judgment about which
assignments matter, and a check that exercises judgment is a check that can be argued with.

### 4.1 Base and head

    python critiques/pr-30/check_rule_tables.py src/pdsfile/pds3file/rules/*.py \
                                                src/pdsfile/pds4file/rules/*.py

| | base | head |
|---|---:|---:|
| T0 no docstring | **36** | 0 |
| T1 wrong-file table name | not evaluated | 0 |
| T2 table not named | not evaluated | 0 |
| T3 unknown identifier | not evaluated | 0 |
| T4 summary line | not evaluated | 0 |
| | **36** | **0**, exit status 0 |

**The base run measures one thing: that no rule module has a docstring at all.** T1 through
T4 all read the docstring, so the base run does not exercise them and it would be wrong to
report base as "36 findings, all of one kind" without saying so.

### 4.2 The mutations

Each mutation was applied to a copy of the head tree, the checker run over all 36 files,
and the copy restored.

| mutation | finding |
|---|---|
| unmutated control, before and after | 0 findings, exit 0 |
| `s_rings_viewables` renamed to `dsntrack_viewables` in `COCIRS_xxxx.py`'s docstring | T1 names "dsntrack_viewables", defined by `CORSS_8xxx.py`; **and** T2 `s_rings_viewables` not named |
| `s_rings_viewables` misspelled `s_ring_viewables` | T3 no rule module defines it; **and** T2 |
| `dsntrack_viewables` dropped from `CORSS_8xxx.py`'s docstring | T2 module defines it, docstring does not name it |
| `COVIMS_8xxx.py`'s whole docstring pasted onto `COUVIS_8xxx.py` | T4 summary line does not name "COUVIS_8xxx" |
| `cassini_iss_fring_mosaics_rsfrench2025.py`'s whole docstring pasted onto `cassini_iss.py` | T1 ×1 and T2 ×3 -- **not** T4; see below |

### 4.3 T4 reads the summary line, and the reason is a gate that was half-running

T4 first compared the module's name against the **whole** docstring, and the copy mutation
passed it. `COVIMS_8xxx.py` and `COUVIS_8xxx.py` define **identical sets of fifteen
tables**, so T1 and T2 are both silent on a straight swap between them, and T4 was the only
check that could fire -- but `COVIMS_8xxx.py`'s docstring names `COUVIS_8xxx.py` in its
last paragraph, because the two modules cross-reference each other. The whole-docstring
form of T4 therefore passed vacuously on exactly the copy it exists to catch. It now reads
the summary line, and eight summary lines were reworded so that each names its own module.

**The check has one hole left, and it is stated in the script rather than left to be
found.** A module key that is a prefix of another key is satisfied by the longer one, so a
docstring copied from `cassini_iss_fring_mosaics_rsfrench2025.py` onto `cassini_iss.py`
passes T4. T1 and T2 both fire on that pair, which is the last row of the table above, so
the hole is left open rather than closed with a special case.

## 5. The Google-style docstring checks

    python critiques/pr-29/check_docstrings.py src/pdsfile/pds3file/rules/*.py \
                                               src/pdsfile/pds4file/rules/*.py

| code | check | base | head |
|---|---|---:|---:|
| P1 | a `Parameters:` entry that is not a parameter of the signature | 0 | 0 |
| P2 | a parameter that does not appear in `Parameters:` exactly once | 2 | 0 |
| P3 | a section spelled `Args:`, `Arguments:`, `Keyword arguments:` or `Input:` | 0 | 0 |
| R1 | `Returns:` present without a value return, or absent with one | 4 | 0 |
| E1 | a `Raises:` entry the body neither raises nor attributes to a call it makes | 0 | 0 |
| E2 | a class raised in the body that `Raises:` does not name | 2 | 0 |
| D1 | a docstring line wider than 90 columns | 0 | 0 |
| U1 | a unicode smart quote, dash or arrow anywhere in the file | 0 | 0 |
| M1 | a module, class or function with no docstring | 70 | 0 |
| | **total** | **78** | **0** |

M1's 70 is 36 modules plus 31 classes plus 3 functions. The checker is used **unchanged**;
this PR edits none of PR-29's or PR-29a's scripts. Run against the state the five modules
of PR-29 were in before that PR documented them it still reports **276**; against PR-29a's
nine, **249**; against `_properties.py` before PR-29b, **73**. All three reproduce.

### 5.1 One parameter is documented in prose rather than in a `Parameters:` block

`COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)` is defined in a class body and takes
no `self`. `_opus.py:157` reaches it as `pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)`,
off the class, so `opus_id` is an argument the caller supplies. The checker drops the first
positional parameter of any function in a class body that is not a `@staticmethod`,
"whatever it is named", so a `Parameters:` entry for `opus_id` would be a P1. The argument
is therefore described in the docstring's prose instead. **The checker was not amended to
accommodate this**, because its rule is deliberate and documented and because amending it
would put PR-29's, PR-29a's and PR-29b's reproduced totals at risk for one call site.
Deferred observation 241.

## 6. Module length

`.cursor/rules/pdsfile_overrides.mdc` deviation (3) waives `src/pdsfile/pds{3,4}file/rules/*.py`
**as a class**, so length is not a constraint on this PR. It is measured anyway, because
the deviation's table carries a row for `VG_28xx.py` whose numbers this PR moves.

    python critiques/pr-29a/measure_module_lines.py src/pdsfile/pds3file/rules/*.py \
                                                    src/pdsfile/pds4file/rules/*.py

| file | total base | total head | docstring head | code base | code head |
|---|---:|---:|---:|---:|---:|
| `VG_28xx.py` | 1,019 | 1,116 | 96 | 1,019 | 1,020 |
| `GO_0xxx.py` | 822 | 918 | 96 | 821 | 822 |
| `COCIRS_xxxx.py` | 786 | 855 | 68 | 786 | 787 |
| `COISS_xxxx.py` | 766 | 846 | 78 | 766 | 768 |

`VG_28xx.py` is the only one of the 36 over a limit at either end, and it is over on code
lines at both. **Every module's code-line count goes up by one or two**, which needs saying
because a docstring-only change should not move a measure defined as "total minus docstring
lines": the measure deducts the docstring's own span, and the blank line that separates the
docstring from the code below it is not part of that span. One blank per module docstring,
and one more per function docstring inserted above a body that had no blank line, is the
whole of it. The deviation's `VG_28xx.py` row is updated to the head numbers.

## 7. The Sphinx build

`docs/` does not exist and is not created here; PR-31 owns it. A throwaway tree is built
elsewhere instead, reproducibly, with `critiques/pr-29a/build_docs_probe.py` and
`critiques/pr-29/sphinx-conf.py` **both unchanged**. What is extended is the page list: the
36 rule modules join the thirteen modules the probe already carries.

    python critiques/pr-29a/build_docs_probe.py $PWD/src <build dir> \
        pds3file.rules pds3file.rules.ASTROM_xxxx ... pds4file.rules.uranus_occs_earthbased

| | base | head |
|---|---:|---:|
| `-n` warnings | 0 | **0** |
| `-W` warnings | 0 | **0** |
| probe exit status | 0 | **0** |

**The base column is not evidence and is reported as such.** At base these 36 modules have
no docstrings at all, so there is no prose for either gate to warn about; a clean base
build is what an empty documentation surface produces. The exit status was read from the
probe's own return value, not inferred from the absence of warning lines -- the probe
appends a line of its own when `sphinx-build` exits nonzero, for exactly that reason.

What makes the head build non-vacuous is the rendered page. `api.html` holds 64 matches for
"rule table", two for `spice_lookup`, and the exact sentence "Voyager photopolarimeter
(PPS) ring profiles".

### 7.1 What the Sphinx gate caught

Four docstrings wrote a double-quoted token ending in an underscore -- `"cassini_iss_"`,
`"cassini_vims_"`, `"uranus_occ_"` and a bare `JNOSRU_` -- which reStructuredText reads as
a reference to a target that does not exist. Both builds failed with
`ERROR: Unknown target name`. All four are reworded; none is escaped with a backslash,
because `\_` in a non-raw Python string is a syntax warning in 3.12.

## 8. Standing gates

### 8.1 Test id sets, full data, both modes

The command lines are `scripts/automated_tests/pdsfile_main_test.sh`'s, plus `--junitxml`.
Run from each tree in turn.

| mode | scope | base | head | ids only in base | ids only in head | outcome changed |
|---|---|---|---|---|---|---|
| `ns` | all seven directories | 1101 passed, 34 skipped (1135 ids) | 1101 passed, 34 skipped (1135 ids) | none | none | none |
| `s` | `tests/pds3file/ tests/rules/pds3/` only | 555 passed, 3 skipped (558 ids) | 555 passed, 3 skipped (558 ids) | none | none | none |

The per-test id sets are diffed, not the counts: the junit files are parsed and compared id
by id with the outcome attached, so a test that changed from passed to skipped would show
even though the totals would not. The `--mode s` scope is the script's own
(`scripts/automated_tests/pdsfile_main_test.sh:75`), not the full suite.

### 8.2 The code checks with no holdings

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        VENV=/seti/all_repos/rms-pdsfile/venv bash scripts/run-all-checks.sh -c -s

All checks passed, exit status 0: ruff, the indentation pass, pytest (**318 passed, 817
skipped**), pyroma **10/10**, the API-freeze check and the clean-install gate. The script
looks for a `venv` in the repository root; `VENV` was set to the shared interpreter for
the run instead of making a symlink, which is what that variable is for
(`scripts/run-all-checks.sh:136`).

### 8.3 The API freeze

    pytest tests/api

**26 passed.** The four frozen files are byte-identical to `c4811d8`, checked with
`git diff --quiet c4811d8 -- <file>` on each of
`tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`,
`scripts/dump_public_api.py` and `tests/api/test_api_freeze.py`. This PR adds `__doc__` to
36 modules, 31 classes and 3 functions and rewrites four more, which is freeze-neutral:
the manifest records name-to-kind pairs and has no docstring field.

### 8.4 ruff

    ruff check src/pdsfile tests scripts                  # All checks passed
    ruff check .                                          # All checks passed
    ruff check --preview --select E111,E112,E113 .        # All checks passed
    ruff check . --config 'lint.per-file-ignores = {}'    # Found 2249 errors

`ruff format` was not run, in any form, per deviation (11).

### 8.5 The ratchet

| | base | head |
|---|---:|---:|
| `per-file-ignores` entries | 66 | 66 |
| code slots across those entries | 180 | 180 |
| findings with `per-file-ignores = {}` | 2,249 | 2,249 |
| `[project.scripts]` entries | 11 | 11 |

Nothing moved. No entry was retired and no entry grew. The rule modules carry the largest
entries in the project -- `E501` alone accounts for 1,638 findings across 41 files -- so
every docstring line was wrapped at 90 columns, which is what keeps the third row from
moving.

`bandit` and `vulture` are disabled and not installed. This PR claims nothing about them.

### 8.6 The record checkers, and the one citation this PR moved

    python critiques/pr-28/check_record_numbers.py

15 stale at base and 15 at head, byte-identical outputs. Those are PR-28's own numbers,
invalidated by PR-28a's extraction; they arrived that way and this PR neither caused nor
repaired them.

    python critiques/pr-29/check_citations.py

0 stale at base and 0 at head, with no repair needed. **That result is weaker evidence than
it looks and is reported as such:** the checker's citation table covers
`critiques/pr-29-validation.md` and PR-29's block of `critiques/deferred-observations.md`,
and none of those citations points into a rule module. It is a regression guard for PR-29's
record, not a check of this PR's.

The citations into rule modules were therefore found by grep and checked by hand. **Nine
records cite a line inside one of the 36 modules; one of them is live and eight are
snapshots.**

* **Live, and repaired here:** deferred observation 52 cites
  `src/pdsfile/pds3file/rules/COISS_xxxx.py:263` for the module-level `opus_products`
  table and `:737` for the class attribute that consumes it. **Both were already off by
  one at `c4811d8`** -- the real lines there are 264 and 738 -- and this PR moves them to
  311 and 795. The entry is updated to the head lines and its "18 of the 34 rule modules"
  claim was re-derived and still holds at **18**.
* **Snapshots, left alone:** the per-round records under `critiques/pr-16/`,
  `critiques/pr-19/`, `critiques/pr-24/` and `critiques/pr-29a/`, and
  `plans/archive/2026-07-17-modernization-plan.md`, record what a reviewer saw at the time
  and are not corrected after the fact.
* **Live but stale before this PR, and left alone:** `plans/2026-07-25-modernization-plan.md`
  cites `COVIMS_0xxx.py:324` for `OPUS_ID_TO_PRIMARY_LOGICAL_PATH`, which was line **326**
  at `c4811d8` and is 377 at head; `plans/2026-08-04-pr-24-subplan.md` cites four more.
  Both are records of a decision already taken. Deferred observation 247.
* `.cursor/rules/pdsfile_overrides.mdc` deviation (4) carries line numbers too, but it says
  in its own text that they are "at the merge commit", so they are anchored and not stale.

## 9. Where each dataset claim came from

**This is the accuracy risk no gate here can catch**, so every factual claim about a
mission, an instrument, a target, a date range or a product type was taken from one of
five sources, all of them in the repository or under the holdings roots.

1. **`$PDS3_HOLDINGS_DIR/_volinfo/*.txt`** -- 40 files, one per PDS3 volume set, each
   holding one pipe-delimited line per volume set and per volume: description, icon type,
   version, publication date, and the data set IDs. **Every PDS3 module's opening
   paragraph comes from here**, and each names the file it came from. Examples: VG_28xx's
   four volumes and their four data set IDs; EBROCC_0001's six observatory data set IDs;
   RPX_xxxx's split into five HST WFPC2 volumes and four ground-based campaigns with the
   telescopes named; COISS_0xxx through COISS_3xxx; the NHxxLO_xxxx and NHxxMV_xxxx
   volume descriptions and the raw/calibrated 1nnn/2nnn pairing.
2. **The PDS4 bundles' own `readme.txt`** under
   `$PDS4_HOLDINGS_DIR/bundles/<bundleset>/<bundle>/`. Two bundle sets are present in this
   holdings copy and both were read. `cassini_uvis_solarocc_beckerjarmak2023`'s readme is
   where "derived radial occultation profiles of the rings of Saturn based on solar
   occultation observations made with the Cassini UVIS instrument between June 2005 and
   June 2017" comes from; `uranus_occs_earthbased`'s is where "each of which contains data
   files associated with a single occultation observation of the Uranian system" and the
   role of the support bundle come from.
3. **The modules' own tables**, read as data rather than as code: the description strings
   returned by `description_and_icon_by_regex`, the category and title strings in
   `opus_type`, the data set IDs returned by `data_set_id`, the volume set patterns in each
   class's `VOLSET_TRANSLATOR` entry, and the `prefix_mapping` of
   `uranus_occs_earthbased.py`, which is where the telescopes, detectors, dates and event
   numbers of the Uranus occultations come from.
4. **The modules' own comments**, where they describe layout: the archive-layout header
   comments in the four pds4 modules that have them, `GO_0xxx.py`'s enumeration of the
   reprocessed images, `NHxxxx_xxxx.py`'s per-code comments in `FILE_CODE_PRIORITY`, and
   the section banners of the two `rules/__init__.py` modules, which say what each rule
   attribute is for.
5. **The two package initializers**, `pds3file/__init__.py` and `pds4file/__init__.py`,
   for the claim that the modules are imported by an explicit list rather than through
   `__all__`.

**What was deliberately not written: acronym expansions the tree does not give.** ISS,
VIMS, RSS, LORRI, MVIC, JIRAM, SRU, SSI, WFPC2, ACS, STIS, NICMOS and WFC3 appear in these
docstrings unexpanded, because no file in the repository or under either holdings root
expands them. Where the tree does expand one, its wording is used verbatim: COUVIS_0xxx is
"the Cassini UVIS (Ultraviolet Spectrometer) data collection" because that is what
`_volinfo/COUVIS_0xxx.txt` says; VG_2801 is "Voyager photopolarimeter (PPS) ring profiles"
and VG_2802 "Voyager ultraviolet (UVS) ring profiles" for the same reason; CIRS and IRIS
are described as "thermal infrared" rather than expanded. This costs the reader a
sentence of context per module and it is the trade the plan asks for.

## 10. What could not be described beyond the rule tables

Six modules are described from their volume-set description line and their tables and
nothing more, because nothing more is derivable:

| module | what is missing, and why |
|---|---|
| `RES_xxxx.py` | The volume set has no `volumes/` directory in this holdings copy and the module defines no tables at all. Everything said about it is the one `_volinfo` line and the subclass registration. |
| `ASTROM_xxxx.py` | One table. The `_volinfo` lines name the instrument and the date ranges; nothing in the tree says what an astrometry product looks like, so nothing is said. |
| `COSP_xxxx.py`, `JNOSP_xxxx.py`, `NHSP_xxxx.py` | SPICE kernel collections with three tables each and no description table. What each says is the `_volinfo` line, the data set ID, the curated document directory, and the three tables. |
| `VG_20xx.py` and `VGIRIS_xxxx.py` | Two tables each. The directory structure is derivable from `description_and_icon_by_regex`; the instrument is named only as the `_volinfo` line names it. |

Four more are described **without a holdings tree to check against**, because their bundle
sets are not in this copy: `cassini_iss.py`, `cassini_vims.py`,
`cassini_iss_fring_mosaics_rsfrench2025.py` and
`cassini_iss_spokes_hedman_hamilton_2024.py`. Every layout claim in those four comes from
the module's own archive-layout header comment and from the paths its tables build, and
the docstrings say so where it matters. `cassini_iss.py` and `cassini_vims.py` also have
the PDS3 volume sets they mirror, which is what `_volinfo/COISS_0xxx.txt` and
`_volinfo/COVIMS_0xxx.txt` supply.

**`cassini_vims.py` is the one module where the honest description is uncomfortable.**
Eight of its eighteen tables are byte-identical to `COISS_xxxx.py`'s and are written
against PDS3 `volumes/COISS_*` paths: its `description_and_icon_by_regex` returns Cassini
ISS descriptions naming narrow- and wide-angle images and the CISSCAL software, and its
`opus_type` files products under the "Cassini ISS" OPUS category. The docstring says that
rather than describing those tables as VIMS behavior. Deferred observation 242.

## 10a. Review

Four rounds, each run by a fresh reviewer subagent with no context from this session or
from any other round. Records: `critiques/pr-30/round-1.md` through `-4`.

| round | slice | surface | prose defects | code defects |
|---|---|---|---:|---:|
| 1 | the 26 pds3 rule modules | 26 modules, 25 classes, 4 functions | 57 | 16 |
| 2 | the 10 pds4 rule modules and all 7 functions | 10 modules, 6 classes, 7 functions | 33 | 7 |
| 3 | the same 26, re-read | the same | 31 | 10 |
| 4 | the same 10 plus the 7, re-read | the same | 26 | 6 |
| | | | **147** | **39** |

Every finding was re-verified by the executor before it was acted on. The 39 code defects
are recorded as deferred observations 240 through 272; none was fixed here, because this
PR changes no executable statement.

### The second reads found more of the first reads' work than of the original

**Thirty-four of the second reads' 57 prose defects are in sentences the first reads'
corrections wrote** -- 21 of round 3's 31 and 13 of round 4's 26. PR-29a measured 11 of
23 on this question and PR-29b 10 of 21; this PR measures 34 of 57, a higher rate than
either, on a surface where the first reads had 36 files to get through rather than nine
or one.

**The largest correction of round 1 and round 2 was itself wrong, in the opposite
direction.** Both first reads found the same defect: the class-docstring boilerplate said
the class body puts every table in front of the inherited one, and four attributes are
assigned outright. The correction said so in all 31 class docstrings and in both
`rules/__init__.py` modules. Rounds 3 and 4 then measured the merge order by locating each
module's own tuples inside the merged translator, and `ASSOCIATIONS` goes the other way:
`ASSOCIATIONS[key] += <module table>` evaluates the addition with the **inherited** table
on the left, so for "bundles", "metadata" and "documents" the default patterns are tried
first. The only keys where the module wins are the three whose default is a null
translator, and those win because the merge discards the null outright rather than because
anything is prepended.

So the sentence was wrong before the correction, wrong after it, and wrong in opposite
directions. It is now stated **once**, in each `rules/__init__.py`, as four measured
routes with the module counts that take each; the 31 class docstrings point at that
paragraph instead of restating it. That is the answer to the "partial fix" pattern PR-29a
named: a claim stated in 31 places gets corrected in one.

Round 3 then found the same shape a second time -- the correction that noticed
`ASTROM_xxxx.py` installs its one table at module level, below the class, wrote that
module a bespoke sentence and left the same generic claim standing in the other ten
modules that do it.

### What the angles returned

* **Instrumentation over reading.** Deferred entry 236 asked that the PR-30 briefs
  demand it explicitly, and all four did. It is what produced the merge-order table, the
  `ast.unparse` hash showing `VGIRIS_xxxx.py`'s description table is `VG_20xx.py`'s, the
  translator runs that showed six of `GO_0xxx.py`'s rules never fire, the count of 163
  OPUS-ID patterns and the three-way split behind it, and the stub-object runs that
  reproduced all five exceptions the two prioritizers document. Round 3's own summary is
  blunt about it: the claims that failed were almost never the ones a careful reading
  would catch.
* **Unverifiable dataset claims** were the smallest category and the cheapest to fix,
  because the answer was always the same: say what the tree says. "Shoemaker-Levy 9" for
  the code's SL9, "command and data handling units" for its CDH, and a list of detector
  codes that the comment it cited did not contain.
* **Relationship claims** were again the largest, and the sharpest of them are the ones
  where the prose described the intent of a table rather than the table.
  `JNOJIR_xxxx.py`'s association rule was documented as pairing a raw file with its
  reduced counterpart; it rewrites the volume digit and the product tag independently and
  crossed, so both paths it emits are always absent, and the reviewer found that 888 of one
  volume's 976 timestamps do have the counterpart the sentence promised. The prose
  described the fix the code is missing.
* **Numbers** were rewritten twice. "Sixteen" lookup dictionaries became eighteen in round
  1, and survived. "Four of this module's five tables" became "five of its nine" in round
  3. The first correction of `COISS_xxxx.py`'s scope narrowed "all four volume sets" to
  "the three image volume sets", and round 3 measured that COISS_0xxx does not name its
  files that way either.

### The one process rule that was followed, and what it bought

Deferred entry 239 asks that the previous round's corrections be committed, and confirmed
present in the tree, before the round that reviews them is launched. Both second reads were
launched against `d108bae` with `src/` untouched since, and both were given that commit
hash and told to read it first. Twenty-one of round 3's 31 findings and 13 of round 4's 26
are in its diff, which is the yield that rule exists to make available.

## 11. Numbers this PR was handed that did not reproduce

Recorded because every number was re-derived rather than inherited.

* **The scope was handed as "36 module docstrings and 3 function docstrings", and it is
  74 docstrings.** The 31 rule classes were not counted, and neither were the four
  function docstrings that existed but were one line each with no Google section, all four
  of which had to be rewritten to clear P2, R1 or E2. The handed figure of **7 functions,
  3 of them undocumented** is right; what it left out is that documenting a module means
  documenting its class too, and that `doc_python.mdc` section 4 requires it. Measured:
  **36 modules + 31 classes + 7 functions**, and the base `M1` count of 70 is the
  arithmetic check on it.

* **The Sphinx comparison was expected to show a base-to-head improvement and does not.**
  The brief asked for `-W` and `-n` at base and head. Both are clean at base, because the
  36 modules have no docstrings there and a build over no prose has nothing to warn about.
  The base column is reported in section 7 as no evidence, and the non-vacuity of the head
  build is established from the rendered page instead.

Everything else reproduced exactly:

* the 36-module scope and its **12,595 lines**;
* the vocabulary counts the brief used to state the defect mode --
  `description_and_icon_by_regex` in **26** modules, `associations_to_metadata` in **22**,
  `default_viewables` in **22**, `opus_products` in **18**;
* the later-PR scopes: `holdings_maintenance/` at **23 files and 152 functions**, the two
  subclass initializers at **33 functions**, `tools/` at **2 files**;
* the `ns` **1135** and `s` **558** baselines, id for id;
* all four ratchet numbers, **66 / 180 / 2,249 / 11**;
* the three checker reproductions. Run against the state each PR's modules were in before
  it documented them -- `4edc7d1` for PR-29's five, `9466dbc` for PR-29a's nine,
  `998a166` for `_properties.py` -- `critiques/pr-29/check_docstrings.py` reports
  **276**, **249** and **73**;
* `critiques/deferred-observations.md` continuing from **240**: the last entry at
  `c4811d8` is 239.
