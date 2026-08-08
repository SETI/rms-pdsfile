# PR-29b validation — the `_properties.py` measurement, and the second reads Phase 7 owed

Base: `998a166`. Branch: `pr-29b-docstrings-properties`. Base branch: `rewrite`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), from the tree being measured, with
`PYTHONPATH=$PWD/src`. Where holdings are needed the environment carried
`PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree is
a second worktree at the same commit, so "base" numbers were measured, not recalled.

Nothing here is inherited. Every number carries the command that produced it.

## 1. This PR stopped short, on purpose, and section 2 is why

PR-29b was to document `_properties.py`'s 68 functions, write its module docstring, and
carry the second reads of `pdsfile.py` and `pdsviewable.py`. **It does the second reads and
it does not document the 68.** The measurement section 2 was asked for says the module
cannot carry docstrings at the standard of the other twelve and stay inside the 2,000-line
total the rule sets, and the choice between a waiver and a split belongs to the owner.

What is here:

| | |
|---|---|
| `src/pdsfile/_properties.py` | ten of 68 functions documented, as the measurement sample; the class docstring's contract block made a literal block; **58 functions and the module docstring not written** |
| `src/pdsfile/pdsfile.py` | second adversarial read, docstring corrections only |
| `src/pdsfile/pdsviewable.py` | second adversarial read, docstring corrections only |
| `critiques/pr-29a/build_docs_probe.py` | takes extra module names; default page list unchanged |

Deferred entry 80 stays open, because `_properties.py` is still the one module in the
package without a module docstring. So does entry 215.

## 2. The line-count projection

`.cursor/rules/pdsfile_overrides.mdc` deviation (3) sets **code lines <= 1,000** and
**total lines <= 2,000**. `_properties.py` is waived on code lines (1,392) by plan §8
settled decision 3. It has no waiver on total lines, and at base it is at 1,689.

    python critiques/pr-29a/measure_module_lines.py src/pdsfile/_properties.py

    src/pdsfile/_properties.py     total 1689   docstring 297   code 1392

Of those 297 docstring lines, 105 are the class docstring and **192 are spread over all 68
functions**, under three lines each, which is what makes this module the last one the
mechanical checker still reports findings on.

**Ten members were documented first and the cost measured**, per the brief's instruction to
measure before writing the bulk. The ten were chosen to span the file: a lazy property with
a trivial body (`exists`), two derived properties with no slot of their own
(`is_documents`, `extension`), a lazy property with three cases (`html_path`), the largest
body in the file (`_info`, 118 lines), a mid-sized lazy property (`mime_type`), the subject
of deferred entry 68 (`version_ranks`), the most branched derivation (`label_basename`),
its one-expression consumer (`label_abspath`), and the file's only static method, which
holds one of its two parameters (`version_info`).

| function | docstring lines at base | at head | delta |
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

Two projections, from the same ten:

* **Flat mean.** 19.1 added lines per function over 58 more functions is 1,108 lines, on
  top of the 1,880 the file already stands at, and before the module docstring: **about
  2,990 total.**
* **Weighted by body size**, because `_info` is the largest body in the file and a flat
  mean over-weights it. Fitting the ten to their code lines gives
  `docstring = 12.4 + 0.292 * code_lines`; over all 68 functions, whose bodies hold 1,231
  code lines between them, that is 1,202 lines of function docstring. With 1,392 code, a
  105-line class docstring and a module docstring of about 25: **about 2,720 total.**

The ten hold 26% of the file's function bodies, so neither projection is an extrapolation
from a corner of it.

**The standard the ten are written to is not inflated, which is the obvious objection.**
Measured at head over the twelve modules already documented, a function docstring runs

| | function-docstring lines | functions | per function |
|---|---:|---:|---:|
| PR-29's five public modules | 1,871 | 123 | 15.2 |
| PR-29a's nine private modules | 2,158 | 88 | **24.5** |
| this PR's ten | 216 | 10 | **21.6** |

The ten sit below the nine modules whose standard the brief asks this file to be brought to,
and above the five. Writing them at PR-29's 15.2 rather than PR-29a's 24.5 would still land
the file near 2,400 total. There is no version of this that fits.

The simplest way to see it needs no projection at all. At base the file had **311 lines of
headroom** under the 2,000 ceiling. Documenting ten of its 68 functions spent **191 of
them**, and `measure_module_lines.py` now reports the file at 1,880. Fifteen percent of the
work has consumed sixty-one percent of the budget, and the 58 functions left have 120 lines
between them: **2.1 lines each.**

**The ceiling is 2,000 and both projections clear it by 700 to 1,000 lines.** Turned around:
staying under 2,000 leaves `2000 - 1392 - 105 - 25 = 478` lines for 68 function docstrings,
which is **7.0 lines each** -- a summary line, a blank, a two-line `Returns:` and the
closing quotes, with nothing left for the cached-property lifecycle that is the whole
reason this module is hard to document. That is the thin docstring the brief forbids, and
writing 2,700 lines into a file with a 2,000-line ceiling is the silent breach it also
forbids. So the work stopped here.

The two ways out are the owner's, and the plan already defers the same question for
`pdsfile.py` (entry 199): a total-lines waiver for `_properties.py`, or splitting the mixin.
The measurement above is what either decision costs.

### 2.1 What the ten are worth on their own

They are not a throwaway. Every one was written from the code and read against it, they
close five docstrings that were wrong (section 6), and they are what makes the projection
reproducible rather than a guess: the owner can read them and judge whether the standard
they set is the one the other twelve modules are held to.

## 3. Proof that the change is docstrings only

### 3.1 The AST hashes

`critiques/pr-29/strip_docstrings.py` parses a module, deletes the docstring node of every
module, class and function, and hashes `ast.dump` of what is left with
`include_attributes=False`, so line and column shifts do not register.

| file | base | head |
|---|---|---|
| `_properties.py` | `c034278fc92c7fb2` | `c034278fc92c7fb2` |
| `pdsfile.py` | `b6b8ad8bd5dba452` | PENDING |
| `pdsviewable.py` | `46cc34775e969faa` | PENDING |

PR-29 established that this check is not vacuous, with five mutations of a documented file;
the same script is used here unchanged.

### 3.2 The comment enumeration, which the AST cannot see

    python critiques/pr-29/check_comments.py <base tree> <head tree> \
        _properties.py pdsfile.py pdsviewable.py

| file | comment lines at base | at head | removed | added |
|---|---:|---:|---:|---:|
| `_properties.py` | 125 | 125 | 0 | 0 |
| `pdsfile.py` | 325 | 325 | 0 | 0 |
| `pdsviewable.py` | 84 | 84 | 0 | 0 |

**No comment line was removed, added, reworded or moved.** Unlike PR-29 and PR-29a, this
PR turns no banner comment into a module docstring, because the one module that still needs
that is the one section 2 stopped on. Every comment in all three files is byte-identical to
base and sits under the same preceding line of code.

One comment is wrong and is left alone, because comment text is the author's: `version_info`
carries a worked example of its own arithmetic reading `_v2.1 -> 201000` and
`_v2.1.3 -> 201030`, and the code produces 20100 and 20103. Deferred observation, section 9.

## 4. The mechanical checks

### 4.1 The docstring checker

    python critiques/pr-29/check_docstrings.py src/pdsfile/_properties.py \
        src/pdsfile/pdsfile.py src/pdsfile/pdsviewable.py

| code | check | base | head |
|---|---|---:|---:|
| P1 | a `Parameters:` entry that is not a parameter of the signature | 0 | PENDING |
| P2 | a parameter that does not appear in `Parameters:` exactly once | 2 | PENDING |
| P3 | a section spelled `Args:`, `Arguments:`, `Keyword arguments:` or `Input:` | 2 | PENDING |
| R1 | `Returns:` present without a value return, or absent with one | 67 | PENDING |
| E1 | a `Raises:` entry the body neither raises nor attributes to a call it makes | 0 | PENDING |
| E2 | a class raised in the body that `Raises:` does not name | 1 | PENDING |
| D1 | a docstring line wider than 90 columns | 0 | PENDING |
| U1 | a unicode smart quote, dash or arrow anywhere in the file | 0 | PENDING |
| M1 | a module, class or function with no docstring | 1 | PENDING |
| | **total** | **73** | PENDING |

**All 73 belong to `_properties.py`.** `pdsfile.py` and `pdsviewable.py` report 0 at base
and 0 at head, which is the point of running the checker on them: their remaining defects
are semantic, and no checker sees those.

### 4.2 The checker is unchanged and still reproduces both earlier records

    python critiques/pr-29/check_docstrings.py <PR-29's five files at 4edc7d1>
      276 findings   E2 16, M1 20, P2 139, P3 26, R1 75
    python critiques/pr-29/check_docstrings.py <PR-29a's nine files at 9466dbc>
      249 findings   D1 2, E2 18, M1 37, P2 94, P3 44, R1 54
    python critiques/pr-29/check_docstrings.py <the fourteen files at head>
      0 findings

The first two are `critiques/pr-29-validation.md` section 4's and
`critiques/pr-29a-validation.md` section 4's numbers, with the identical per-code
breakdowns. `git diff --stat 998a166 -- critiques/` shows one file changed, and it is not a
checker.

### 4.3 The state-contract derivation

    python critiques/pr-29a/derive_state_contract.py src/pdsfile src/pdsfile/_properties.py

| | reached | read | written | listed | findings |
|---|---:|---:|---:|---:|---:|
| base | 114 | 114 | 41 | 94 | **0** |
| head | 114 | 114 | 41 | 94 | **0** |

`reached` is derived from the code, which this PR does not change. `listed` is derived from
the class docstring, which this PR does change -- section 5 -- so the identical 94 is the
result that matters: the contract block survived being turned into a literal block with
every name intact. Deferred entry 54 is amended with these numbers.

## 5. The Sphinx build

`docs/` does not exist and is not created here; PR-31 owns it. A throwaway tree is built
elsewhere, reproducibly:

    python critiques/pr-29a/build_docs_probe.py <tree>/src <build dir> [_properties]

The configuration is `critiques/pr-29/sphinx-conf.py` **unchanged**, with `nitpick_ignore`
empty and nothing mocked.

**The exit status is checked, twice over.** The probe appends a line of its own when
`sphinx-build` returns nonzero, so a build that never ran cannot report clean, and the
probe's own exit status was read rather than piped away.

### 5.1 The thirteen-module page set, which is the gate this PR must pass

| | base | head |
|---|---:|---:|
| `-n` warnings | 0 | **0** |
| `-W` warnings | 0 | **0** |

That set is PR-29's four modules and PR-29a's nine, and it covers both files this PR
finishes. It is clean at base because PR-29 and PR-29a left it clean, and this PR's
corrections to `pdsfile.py` and `pdsviewable.py` keep it so.

### 5.2 The fourteen-module page set, which measures what `_properties.py` still owes

| | base | head |
|---|---:|---:|
| `-n` warnings | 21 | **10** |
| `-W` warnings | 17 | **7** |

The 21 at base is the figure `critiques/pr-29a-validation.md` section 7 recorded for
including this module, reproduced. The class docstring accounts for ten of the eleven
warnings that go away; the remainder are in held-back function docstrings -- `lid` and
`lidvid`, whose worked examples indent under a bare paragraph, `opus_type`, whose
`Examples:` heading docutils reads as a definition list, and `viewset_lookup`, whose
`Keyword arguments:` section Napoleon does not recognize. None of the seven is reachable
without writing the docstrings section 2 stopped on.

**One hazard is worth recording for whoever runs this next.** The first run of the extended
probe reported a clean fourteen-module build, and the reason was that it was executed from
the base tree, whose copy of `build_docs_probe.py` predates the extra-module argument and
silently ignored it. The page set is now verified directly --
`grep -c 'automodule:: pdsfile._properties' <build>/api.rst` is 1 -- because "the gate ran
and found nothing" and "the gate did not run" look identical from the outside. This is the
same failure CodeRabbit caught in PR-29a's probe, arriving by a different route.

## 6. Every docstring that was wrong about the code

PENDING

## 7. Review

PENDING

## 8. Standing gates

### 8.1 Test id sets, full data, both modes

PENDING

### 8.2 The code checks with no holdings

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        bash scripts/run-all-checks.sh -c -s

All checks passed: ruff, the indentation pass, pytest, pyroma 10/10, the API-freeze check
and the clean-install gate. The script needs a `venv` in the repository root; a symlink to
the shared interpreter was made for the run and removed afterwards. It is gitignored and is
not part of this PR.

### 8.3 The API freeze

    pytest tests/api

PENDING. The four frozen files are byte-identical to `998a166`, checked with
`git diff --quiet 998a166 -- <file>` on each. This PR adds no name and removes none; it adds
`__doc__` text to ten functions that already had it, which the manifest has no field for.

### 8.4 ruff

    ruff check .                                          # All checks passed
    ruff check --preview --select E111,E112,E113 .        # All checks passed
    ruff check . --config 'lint.per-file-ignores = {}'    # Found 2249 errors

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

    python critiques/pr-28/check_record_numbers.py     # 15 stale at base and at head
    python critiques/pr-29/check_citations.py          # PENDING

The 15 are PR-28's own numbers, invalidated by PR-28a's extraction; they arrived that way
and this PR neither caused nor repaired them.

## 9. Deferred observations

PENDING

## 10. Type omissions -- PR-35's queue

PENDING
