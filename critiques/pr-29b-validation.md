# PR-29b validation — `_properties.py`, and the second reads Phase 7 owed

Base: `998a166`. Branch: `pr-29b-docstrings-properties`. Base branch: `rewrite`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), from the tree being measured, with
`PYTHONPATH=$PWD/src`. Where holdings are needed the environment carried
`PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree is
a second worktree at the same commit, so "base" numbers were measured, not recalled.

Nothing here is inherited. Every number carries the command that produced it, and section
12 lists the numbers this PR was handed that did **not** reproduce.

## 1. Scope

Three files, and two different jobs.

| file | lines at base | at head | job |
|---|---:|---:|---|
| `src/pdsfile/_properties.py` | 1,689 | 2,720 | 68 function docstrings and the module's first, all written here |
| `src/pdsfile/pdsfile.py` | 2,435 | 2,459 | a second adversarial read of prose that shipped with PR-29 |
| `src/pdsfile/pdsviewable.py` | 986 | 999 | the same |

    python critiques/pr-29/measure.py src/pdsfile/_properties.py src/pdsfile/pdsfile.py \
        src/pdsfile/pdsviewable.py

At base: 131 functions, 4 classes, 2 of the 3 modules documented, 94 parameters excluding
`self` and `cls`. **`_properties.py` held 68 of those functions, all 68 already carrying a
docstring, and 2 of the 94 parameters.** So unlike PR-29 and PR-29a this was not mostly
writing from nothing; it was 68 thin docstrings, dominated by `Returns:` and behavior
rather than by `Parameters:`, that had to become accurate ones.

`_properties.py` was the last module in the package without a module docstring and the only
one the mechanical checker still reported findings on. Both are closed here, and with them
deferred entry 80.

## 2. The line-count measurement, and the waiver it produced

`.cursor/rules/pdsfile_overrides.mdc` deviation (3) sets **code lines <= 1,000** and
**total lines <= 2,000**. `_properties.py` was waived on code lines (1,392) by plan §8
settled decision 3 and had no waiver on total lines, standing at 1,689 with 192 lines of
function docstring spread over 68 functions -- under three lines each.

**Ten members were documented first and the cost measured**, before the other 58 were
written, because the answer decided whether the work could proceed at all. The ten were
chosen to span the file: a lazy property with a trivial body (`exists`), two derived
properties with no slot (`is_documents`, `extension`), a lazy property with three cases
(`html_path`), the largest body in the file (`_info`, 118 lines), a mid-sized lazy property
(`mime_type`), the subject of deferred entry 68 (`version_ranks`), the most branched
derivation (`label_basename`), its one-expression consumer (`label_abspath`), and the
file's only static method, which holds one of its two parameters (`version_info`).

| function | docstring lines at base | after the sample | delta |
|---|---:|---:|---:|
| `exists` | 1 | 16 | +15 |
| `is_documents` | 1 | 10 | +9 |
| `extension` | 1 | 18 | +17 |
| `html_path` | 3 | 21 | +18 |
| `_info` | 1 | 46 | +45 |
| `mime_type` | 3 | 17 | +14 |
| `version_ranks` | 5 | 23 | +18 |
| `label_basename` | 3 | 27 | +24 |
| `label_abspath` | 1 | 11 | +10 |
| `version_info` | 6 | 27 | +21 |
| **ten together** | **25** | **216** | **+191** |

The ten hold 26% of the file's function bodies. Fitting them to their code lines gives
`docstring = 12.4 + 0.292 * code_lines`; over all 68 functions, whose bodies hold 1,231
code lines between them, that projected 1,202 lines of function docstring, and with 1,392
code lines, a 105-line class docstring and a module docstring of about 25, **a total of
about 2,720 against a ceiling of 2,000**. The flat mean of the ten projected about 2,990.

The simplest way to see it needed no projection: at base the file had **311 lines of
headroom**, and documenting ten of 68 functions spent **191 of them**. Fifteen percent of
the work had consumed sixty-one percent of the budget.

That was reported and the work stopped there, because the two ways out -- a waiver or a
split of the mixin -- were the owner's to choose and a thin docstring was the one answer
that was not available. **The owner waived `_properties.py` on total lines** (2026-08-08),
and the remaining 58 were written.

### 2.1 What it actually cost

    python critiques/pr-29a/measure_module_lines.py src/pdsfile/_properties.py

| | total | docstring | code |
|---|---:|---:|---:|
| base | 1,689 | 297 | 1,392 |
| head | **2,720** | 1,330 | **1,390** |

**The projection landed within four lines of the outcome**, which is the result worth
keeping: 2,720 projected from a tenth of the work, 2,720 measured over all of it. A
per-module projection from a representative sample is reliable enough to price this
decision, and PR-30 has the rule modules coming.

Two other numbers matter for that. **Code lines went down by two**, because the three
description lines inside the banner comment became part of the module docstring, so nothing
about the complexity the 1,000-line limit exists to bound has changed. And the per-function
cost is not a constant: measured at head, a function docstring runs **15.2** lines across
PR-29's five public modules, **24.5** across PR-29a's nine private ones, and **17.3** across
these 68. What makes 17.3 add up to 1,175 lines is the count, not the length.

The standard the 68 are written to therefore sits between the two earlier PRs rather than
above them. Writing them at PR-29's 15.2 would still have landed the file near 2,400.

Deviation (3) is amended with the waiver, the reason, and these numbers. It is the first
entry waived on total lines, which is stated in the rule because it makes it the precedent
`pdsfile.py`'s deferred split (entry 199) will be argued against.

## 3. Proof that the change is docstrings only

### 3.1 The AST hashes

`critiques/pr-29/strip_docstrings.py` parses a module, deletes the docstring node of every
module, class and function, and hashes `ast.dump` of what is left with
`include_attributes=False`, so line and column shifts do not register.

| file | base | head |
|---|---|---|
| `_properties.py` | `c034278fc92c7fb2` | `c034278fc92c7fb2` |
| `pdsfile.py` | `b6b8ad8bd5dba452` | `b6b8ad8bd5dba452` |
| `pdsviewable.py` | `46cc34775e969faa` | `46cc34775e969faa` |

All three pairs match. PR-29 established that this check is not vacuous, with five
mutations of a documented file; the same script is used here unchanged.

### 3.2 The comment enumeration, which the AST cannot see

    python critiques/pr-29/check_comments.py <base tree> <head tree> \
        _properties.py pdsfile.py pdsviewable.py

| file | comment lines at base | at head | removed | added |
|---|---:|---:|---:|---:|
| `_properties.py` | 125 | 122 | 3 | 0 |
| `pdsfile.py` | 325 | 325 | 0 | 0 |
| `pdsviewable.py` | 84 | 84 | 0 | 0 |

**Three lines removed in total, all of them one block, and all of them accounted for:**

    # The derived values of a PdsFile: the lazy properties, which fill an _X_filled slot
    # and (in all but one case) write the object back to the shared cache, and the ones
    # recomputed on each access

That is the description inside `_properties.py`'s banner comment, which the rule requires be
a module docstring and which therefore could not stay where it was. This is the same
removal PR-29a made in each of its nine files. The banner's rules and its
`# pdsfile/_properties.py` line are untouched, and every fact the removed description
carried is in the module docstring that replaced it. Every other comment in all three files
is byte-identical to base and sits under the same preceding line of code, including all 325
in `pdsfile.py`.

**One comment is wrong and is left alone**, because comment text is the author's:
`version_info` carries a worked example of its own arithmetic reading `_v2.1 -> 201000` and
`_v2.1.3 -> 201030`, and the code produces 20100 and 20103. Deferred observation, section
10.

## 4. The mechanical checks

### 4.1 The docstring checker

    python critiques/pr-29/check_docstrings.py src/pdsfile/_properties.py \
        src/pdsfile/pdsfile.py src/pdsfile/pdsviewable.py

| code | check | base | head |
|---|---|---:|---:|
| P1 | a `Parameters:` entry that is not a parameter of the signature | 0 | 0 |
| P2 | a parameter that does not appear in `Parameters:` exactly once | 2 | 0 |
| P3 | a section spelled `Args:`, `Arguments:`, `Keyword arguments:` or `Input:` | 2 | 0 |
| R1 | `Returns:` present without a value return, or absent with one | 67 | 0 |
| E1 | a `Raises:` entry the body neither raises nor attributes to a call it makes | 0 | 0 |
| E2 | a class raised in the body that `Raises:` does not name | 1 | 0 |
| D1 | a docstring line wider than 90 columns | 0 | 0 |
| U1 | a unicode smart quote, dash or arrow anywhere in the file | 0 | 0 |
| M1 | a module, class or function with no docstring | 1 | 0 |
| | **total** | **73** | **0** |

**All 73 belonged to `_properties.py`.** `pdsfile.py` and `pdsviewable.py` reported 0 at
base and 0 at head, which is the point of running the checker over them: their remaining
defects are semantic, and no checker sees those. With this PR the checker reports **0 over
all fifteen modules under `src/pdsfile/`**.

### 4.2 The checker is unchanged and still reproduces both earlier records

    python critiques/pr-29/check_docstrings.py <PR-29's five files at 4edc7d1>
      276 findings   E2 16, M1 20, P2 139, P3 26, R1 75
    python critiques/pr-29/check_docstrings.py <PR-29a's nine files at 9466dbc>
      249 findings   D1 2, E2 18, M1 37, P2 94, P3 44, R1 54

Those are `critiques/pr-29-validation.md` section 4's and `critiques/pr-29a-validation.md`
section 4's numbers, with the identical per-code breakdowns. `check_docstrings.py`,
`check_comments.py`, `strip_docstrings.py` and `measure.py` are byte-identical to base.

### 4.3 The state-contract derivation -- deferred observation 54

    python critiques/pr-29a/derive_state_contract.py src/pdsfile src/pdsfile/_properties.py

| | reached | read | written | listed | findings |
|---|---:|---:|---:|---:|---:|
| base | 114 | 114 | 41 | 94 | **0** |
| head | 114 | 114 | 41 | 94 | **0** |

`reached` is derived from the code, which this PR does not change. `listed` is derived from
the class docstring, which this PR **does** change -- section 5 -- so the identical 94 is
the result that matters: the contract block survived being turned into a literal block with
every name intact. Entry 54 is amended with these numbers, which are the first measurement
of `_properties.py` under the derivation from the PR that owns the module.

The derivation also settled a claim that appears in three places at once. It reports 64
properties, 40 of them writing a slot, exactly one of those 40 (`filename_keylen`) not
calling `_recache()`, 24 properties with no slot, and exactly four non-property members.
That is what `pdsfile.py`'s module map says, what `_PropertiesMixin`'s class docstring says,
and what the new module docstring says, so the three agree and all three are right.

## 5. The Sphinx build

`docs/` does not exist and is not created here; PR-31 owns it. A throwaway tree is built
elsewhere, reproducibly:

    python critiques/pr-29a/build_docs_probe.py <tree>/src <build dir> [_properties]

The configuration is `critiques/pr-29/sphinx-conf.py` **unchanged**, with `nitpick_ignore`
empty and nothing mocked. The probe now takes module names after the build directory and
adds them to its page list; its default list is unchanged, so PR-29a's recorded run still
reproduces exactly.

**The exit status is checked, two ways.** The probe appends a line of its own when
`sphinx-build` returns nonzero, so a build that never ran cannot report clean, and the
probe's own exit status was read rather than piped away.

| page set | | base | head |
|---|---|---:|---:|
| the thirteen PR-29 and PR-29a modules | `-n` | 0 | **0** |
| | `-W` | 0 | **0** |
| those thirteen plus `_properties` | `-n` | 21 | **0** |
| | `-W` | 17 | **0** |

The 21 at base is the figure `critiques/pr-29a-validation.md` section 7 recorded for
including this module, reproduced. Eleven of them were the class docstring's contract block,
whose trailing-underscore attribute names read as reStructuredText references and whose
indentation read as a definition list; making it a literal block removed all eleven without
changing a character of its content, which section 4.3's derivation confirms. The other ten
were in function docstrings this PR rewrote.

One warning survived until the end and is worth stating, because it is a convention rather
than a defect: `index_pdslabel`'s `Returns:` named `pdsparser.PdsLabel` in the type slot,
which resolves to nothing under `-n` because `pdsparser` has neither an autodoc page nor an
intersphinx inventory. It is named in prose instead, exactly as PR-29 does with `PdsFile`
inside `pdsviewable.py`, and it is listed in section 11 as PR-35's.

**One hazard is worth recording for whoever runs this probe next.** Its first extended run
reported a clean fourteen-module build, and the reason was that it was executed from the
base tree, whose copy of the script predates the extra-module argument and silently ignored
it. The page set is now verified directly -- `grep -c 'automodule:: pdsfile._properties'`
over the generated `api.rst` is 1 -- because "the gate ran and found nothing" and "the gate
did not run" look identical from outside. This is the same failure CodeRabbit caught in
PR-29a's probe, arriving by a different route.

## 6. Every docstring that was wrong about the code

PENDING

## 7. Review

PENDING

## 8. Standing gates

### 8.1 Test id sets, full data, both modes

The command lines are `scripts/automated_tests/pdsfile_main_test.sh`'s, plus `--junitxml`.
Run from each tree in turn.

| mode | scope | base | head | ids only in base | ids only in head | outcome changed |
|---|---|---|---|---|---|---|
| `ns` | all seven directories | 1101 passed, 34 skipped (1135 ids) | 1101 passed, 34 skipped (1135 ids) | none | none | none |
| `s` | `tests/pds3file/ tests/rules/pds3/` only | 555 passed, 3 skipped (558 ids) | 555 passed, 3 skipped (558 ids) | none | none | none |

The per-test id sets were diffed, not the counts: the two junit files were parsed and
compared id by id with the outcome attached, so a test that changed from passed to skipped
would show even though the totals would not. The `--mode s` scope is the script's own, not
the full suite.

### 8.2 The code checks with no holdings

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        bash scripts/run-all-checks.sh -c -s

All checks passed: ruff, the indentation pass, pytest, pyroma 10/10, the API-freeze check
and the clean-install gate. The script needs a `venv` in the repository root; a symlink to
the shared interpreter was made for the run and removed afterwards. It is gitignored and is
not part of this PR.

### 8.3 The API freeze

    pytest tests/api

26 passed. The four frozen files are byte-identical to `998a166`, checked with
`git diff --quiet 998a166 -- <file>` on each. This PR turns three `#` header comment lines
into part of a module docstring and rewrites 137 docstrings, which is freeze-neutral two
ways rather than by assumption: the manifest has no docstring field, and
`tests/api/test_mixin_collisions.py` lists `__doc__` among the structural names it ignores,
so the one test that walks a class body cannot see a docstring either.

### 8.4 ruff

    ruff check .                                          # All checks passed
    ruff check --preview --select E111,E112,E113 .        # All checks passed
    ruff check . --config 'lint.per-file-ignores = {}'    # Found 2249 errors

Two findings were introduced and fixed inside this PR rather than shipped, both in
`critiques/pr-29b/remap_citations.py` and both therefore invisible to the configured gate,
which covers `src/pdsfile tests scripts` only: `E401` and `I001` on a single import line.
The bare `ruff check .` is clean at head, which is the check that caught them.

### 8.5 The ratchet

| | base | head |
|---|---:|---:|
| `per-file-ignores` entries | 66 | 66 |
| code slots across those entries | 180 | 180 |
| findings with `per-file-ignores = {}` | 2,249 | 2,249 |
| `[project.scripts]` entries | 11 | 11 |

Nothing moved. No entry was retired and no entry grew. `bandit` and `vulture` are disabled
and not installed; this PR claims nothing about them.

### 8.6 The record checkers

    python critiques/pr-28/check_record_numbers.py

15 stale at base and 15 at head, byte-identical outputs. Those are PR-28's own numbers,
invalidated by PR-28a's extraction; they arrived that way and this PR neither caused nor
repaired them.

    python critiques/pr-29/check_citations.py

**0 stale at head, and it took two repairs.** It reports 0 at base. A docstring-only PR
moves every citation below a docstring it grows, and this one grew docstrings in all three
files that PR-29's record and PR-29's deferred entries cite: 47 citations drifted on the
first pass and 45 more when round 5's corrections changed six docstrings again, 92 in all.

Each was **re-derived rather than renumbered**. `critiques/pr-29b/remap_citations.py`
aligns the file at a commit where the citations were correct against the working tree with
`difflib`, which is exact here because no statement moved; carries each citation to the
line its own line became; and **requires the citation's own token to be present there**,
refusing to write anything at all if any citation cannot be resolved. The checker's table
and the two documents are rewritten in one pass so they cannot disagree. The refusal is
mutation-tested: corrupting one entry's token makes the run report it and leave every file
untouched.

One number in PR-29's record could not be repaired that way and should not have been.
The checker compared `pdsfile.py`'s and `pdsviewable.py`'s line counts against the working
tree, and PR-29's record states them "at head", meaning its own head. A later PR that adds
a docstring does not make that record wrong. The check now reads those two files out of
PR-29's merge commit, which keeps it falsifiable -- editing the record's table still fails
it, verified by mutation -- without demanding that every later PR rewrite an earlier record.

## 9. What the second reads found that the first reads had introduced

This is the measurement section 5 of the brief exists for, and the one PR-29a's record asked
this PR to make. Rounds 3, 4 and 5 were each handed **the list of sentences the earlier
round had rewritten, by name**, and asked to judge each against the code as if it were new
prose, and to tag every finding `[CHANGED]` or `[ORIGINAL]`.

PENDING

## 10. Deferred observations

Entries 223 to 231, and amendments to 54, 68, 80 and 215. The amendments are the four this
PR closes or measures; the new entries divide into what the executor measured (223 to 228)
and what the review rounds found in the code rather than in the prose (229 onward).

The one worth naming here is **223**, because the owner asked that the line-count
measurement be kept as evidence after the waiver removed it as a gate. It records the three
per-module costs, the ten-member sampling method, and the fact that the projection landed
within four lines of the outcome.

## 11. Type omissions -- PR-35's queue

This PR writes two `Parameters:` entries, because `_properties.py` declares two parameters
in the whole file, and `pdsfile.py` and `pdsviewable.py` are corrections to prose that
already carries its own. One of the two is written without a type.

| parameter | where | what the code shows |
|---|---|---|
| `suffix` | `version_info` | compared against string literals and then split and sliced as text, so a `str` -- except that None is accepted explicitly and short-circuits before any string operation, so a `(str)` slot would be a narrower type than the code has |

`name` in `viewset_lookup` is written `(str)`: it is used as a key into the class's
VIEWABLES dictionary and compared with `'default'`, and nothing else is reachable.

**One return type is omitted for a different reason.** `index_pdslabel` returns the
`PdsLabel` object `pdsparser` builds, and naming it in the type slot fails the `-n` Sphinx
build, because `pdsparser` has neither an autodoc page in the probe's page set nor an
intersphinx inventory. It is named in prose instead, which is PR-29's convention for
`PdsFile` inside `pdsviewable.py`, used unchanged. PR-35's stub can write the type; a
docstring here cannot, until PR-31 decides what the doc tree's intersphinx mapping holds.

## 12. Numbers this PR was handed that did not reproduce

Recorded because every number was re-derived rather than inherited.

* **The brief said `_properties.py` had "no module docstring, one class whose docstring is
  105 lines".** Both reproduce. So do 1,689 lines, 68 functions, all 68 already documented,
  2 parameters, the `ns` 1135 and `s` 558 baselines, the ratchet's 66 / 180 / 11, the base
  checker's 73 findings, and PR-29a's 21 Sphinx warnings for including this module.

* **The brief said deferred observations continue from 223.** They do; the last entry at
  base is 222.

* **`critiques/pr-29a-validation.md` section 6 records `_properties.py` at 1,689 total, 297
  docstring, 1,392 code, and deviation (3) repeats it.** All three reproduce.

* **What did not reproduce is in deviation (3)'s own prose, not in the brief.**
  "Documenting a module costs roughly fourteen lines per function" is below every module
  measured: 15.2 for PR-29's five, 24.5 for PR-29a's nine, 17.3 for these 68. The rule now
  carries the three figures. Entry 223.

* **And one claim in a rule file was wrong about the code.** Deviation (4)'s `RUF005` note
  said `self._info[:4] + (shape,)` "raises today" because `_info_filled` is a list on two
  construction paths. It cannot: the line is reached only where the recorded shape has more
  than two elements, and both those paths pre-set a two-element one. Raised by CodeRabbit,
  reproduced on a live merged directory, and corrected to say the hazard is latent.
