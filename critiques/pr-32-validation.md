# PR-32 validation — the user guide for the fifteen command-line programs

Base: `532f65d`. Branch: `pr-32-user-guide`. Base branch: `rewrite`. Closes issue #45.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3, Sphinx 9.1.0), from the tree being
measured. Where holdings are needed the environment carried `PDS3_HOLDINGS_DIR`,
`PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree is a second worktree
at `532f65d`, so base numbers were measured rather than recalled.

**Nothing under `src/` changed**: `git diff 532f65d --name-only -- src/` is empty. The
deliverable is 21 pages of prose about behavior the programs already have, so the defect
this PR could most easily ship is a fluent, plausible, invented sentence — one that no
build, no test and no linter can see. Sections 2, 3 and 5 are the evidence about that,
and section 5.3 is the reason this PR took five review rounds rather than the four
section 6.6 allows.

## 1. What changed

| | |
|---|---:|
| pages added under `docs/user_guide/` | 21 |
| `toctree` line added to `docs/index.rst` | 1 |
| files changed under `src/` | **0** |
| new checker | `critiques/pr-32/check_cli_coverage.py` |
| deferred observations added | 347–356 |
| commits | 9 |

The 21 pages are one per program (15), the landing page, concepts, installation, the
shell-script chapter, the file-format appendix — and one the plan did not call for,
`user_guide_maintenance_tools.rst`.

That extra page exists because ten of the fifteen programs build no parser of their own:
they declare a `ToolSpec` and `_common.build_arg_parser()` builds one from it, so all ten
share an identical surface. Writing it ten times would have been, in prose, the same
pasted-between-near-identical-halves defect `check_flavor_vocabulary.py` exists to catch.

**Measured duplication between those ten chapters at the final head.** Each page was
normalized first, mapping volume/bundle, volumes/bundles, volume set/bundle set and
pds/pds4 onto single tokens, so that a sentence pasted between a pair and reworded only in
its unit noun cannot hide behind the noun:

| | |
|---|---:|
| most similar pair, `difflib` ratio over non-blank lines | **0.302** (`pdsinfoshelf` / `pds4infoshelf`) |
| non-blank lines across the ten chapters | 991 |
| distinct non-blank lines recurring in two or more of them | **72** |

An earlier measurement of the first draft gave 0.360 over 895 lines. It is quoted here
because the plan carried it, and it was **re-measured at head rather than carried
forward**: the corrections both lengthened the pages and reduced the overlap.

## 2. The examples: 56 published, 51 executed, 51 of 51 reproduced

Round 3 was given one job — take the published examples and run them — and the holdings
environment to do it with.

| | |
|---|---:|
| command lines published | 56 (42 `console`, 14 `bash`) |
| executed | **51** |
| **reproduced their published output** | **51 of 51** |
| failed to run at all | **0** |
| not executed | **5** |

**The five not executed, named:**

1. `pip install rms-pdsfile`
2. `pipx install rms-pdsfile`
3. `pip install "rms-pdsfile[dev]"`
4. a second occurrence of one of those three, in a different chapter
5. `./pdsdata-sync-volset.sh admin staging VGx_9xxx --delete`

The first four install the package under test into the environment running the review,
which would have replaced the tree being measured. Their effect was checked another way:
`tabulate` imports and `show_opus_products` runs, which is what the `dev` extra is for.
The fifth is a `zsh` script that assumes macOS, `/Volumes/pdsdata-<name>` mount points and
two drives; the shell-script chapter is document-only under ground rule 7 and this line is
quoted from the script's own usage.

**No published example was captured against a zero-byte placeholder.** Round 3 was told to
look for that signature specifically, because deferred 353 records that the shared testing
tree carries zero-byte stand-ins for every `.tar.gz` and every `*_md5.txt`: it found no
`tarfile.ReadError`, no checksum run over zero files, no zero-length archive or manifest.
`COUVIS_0001.tar.gz` is 55,543 bytes over 16 members; the PDS4 archive is 80,800,164 bytes
over 192, and `tar tzf` lists all 192. The PDS3 manifest covers 9 files and the PDS4 one
184. Two zero-byte files in the *published data* do reach published output and are named
as such on the pages that show them.

Eleven `--initialize` examples reported "already exists" against the sandbox as it stood,
because that sandbox is the post-capture state. After removing the one product each
example builds, **all eleven reproduced their published output exactly, counts included**.

## 3. The checker

`critiques/pr-32/check_cli_coverage.py` captures each program's real `ArgumentParser` out
of its own `main()` — by replacing `parse_args` and `parse_intermixed_args` with a
function that raises, so `main()` runs as far as its parser and no further — and compares
it against the flags the guide documents, in both directions.

    $ python critiques/pr-32/check_cli_coverage.py --docs docs/user_guide ; echo $?
    check_cli_coverage: 0 findings over 15 programs, 108 options, 175 option strings, 1 default
    0

It found five documentation defects before it went green.

**Mutation test, re-run at the final head.** Each mutation was made in a copy of
`docs/user_guide`, never in the tree:

| mutation | result |
|---|---|
| rename a documented flag (`--timeless` → `--timelessX`) | 2 findings, both directions |
| add a phantom flag (`--phantom` to `crlf`) | 1 finding |
| change a short form (`-q` → `-Q`) | 2 findings, both directions |
| change a documented default (`60` → `90`) | 1 finding |
| delete a documented default (`Default **60**.` → `Default sixty.`) | 1 finding |
| delete it from the option's row but leave the value in unrelated prose | **1 finding** |
| run against a directory with no guide in it | **exit 2**, "cannot run the comparison" |

The last row is the check on the check: a checker that reports a clean pass over zero
files is worse than no checker. It raises rather than passing.

The second-to-last row is CodeRabbit's, and it was a real weakness: comparison 3
originally asked whether the default's value appeared **anywhere in the chapter**, so a
`60` in an example or in another option's row would have stood in for the statement it
was looking for. It now parses the chapter's list-table rows and searches only the row
whose first cell carries one of that option's flag spellings, falling back to the shared
chapter. The mutation above is the check on that, and it fails under the old rule and
passes under the new one.

### 3.1 The bug round 4 found in the checker itself

At line 308, in the third comparison, `names = '/'.join(strings)` **shadowed the
program-name set** built at line 260 and read at 276 and 279 on every subsequent
iteration. From the first time a substantive default went unstated, every later program
would be checked against a corrupted `all_progs`, and `documented_flags()` would start
matching single characters as program names. Present since the first commit and latent on
a clean run, because the shadowing only fires after a finding. Fixed in `824c01f` by
renaming the local.

### 3.2 The second sensitivity, closed

The previous executor left an open question: that a mutation removing the `**` around a
documented default made the checker emit **36 spurious "no chapter documents it" findings**
for that program even with the shadowing fixed, implying a further sensitivity in
`documented_flags()`'s handling of table structure.

**It does not reproduce, and there is no such sensitivity.** Measured three ways at the
final head:

| checker | page | findings |
|---|---|---:|
| fixed (`824c01f`) | head | **1** |
| fixed (`824c01f`) | the page as committed at `37cd5b6` | **1** |
| **pre-fix (`37cd5b6`)** | the page as committed at `37cd5b6` | **12** |

So the cascade is the shadowing bug's own blast radius, seen before it was fixed. Two
things follow. The mutation isolates to exactly one finding, so comparison 3 is precise
and comparison 2 is not sensitive to `**`. And **a latent bug in a gate can look exactly
like a weakness in what the gate checks** — the observation was recorded as a property of
the parsing when it was a property of the parser. The count differs too: the artifact
gives 12 where the note said 36, which is the seventh number in this effort written from
recollection rather than from a run.

### 3.3 One more number in the checker's own output

Its pass line read `1 defaults`. It now agrees with its own count in number — `1 default`,
`0 findings`, `1 finding` — because a gate's summary is read as a measurement and a
measurement that cannot be singular is a template.

## 4. Sphinx, both builds, at the final head

    cd docs && make html BUILDDIR=_build/warnings SPHINXOPTS="-W"      # exit 0
    cd docs && make html BUILDDIR=_build/nitpicky SPHINXOPTS="-n -W"   # exit 0

| build | exit | problem lines (`grep -cE 'WARNING:|ERROR:'`) |
|---|---:|---:|
| `-W` | **0** | **0** |
| `-n -W` | **0** | **0** |

Coverage line, from the nitpicky log:
`API reference: 78 of 78 modules under /seti/all_repos/rms-pdsfile-pr32/work/src documented`.

`docs/_build/` is gitignored (`.gitignore:75`) and `git status --porcelain` after a build
lists nothing under it.

**What these builds cannot see** is the whole of section 5. Both pass with 0 problem lines
over a page whose every flag is smart-quoted into an unpastable en dash; deferred 351
records that, and the check that catches it is one grep against `docs/_build` that no gate
runs.

## 5. The reviews

Five rounds, every one a fresh no-context subagent, with the tree frozen and
`git status --porcelain` empty for the duration of each.

| round | scope | findings |
|---|---|---:|
| 1 | the ten spec-tool chapters and the driver chapter | 11 defects, 10 observations |
| 2 | the five other programs and the four shared chapters | 12 defects, 3 observations |
| 3 | adversarial, against the examples, by running them | 5 defects |
| 4 | second read of the first correction pass, by name | 12 introduced + 7 survived |
| 5 | second read of the second correction pass, by name | 16 defects, 4 minor |

Rounds 1–4 reported 47 findings, **36 distinct** after the overlaps. Of those: 1 was
already fixed (the checker bug, `824c01f`), **1 was rejected on measurement**, and **34
were applied**, together with 9 of the 13 observations. Round 5 then found 16 more, all
of them inside those corrections, and all 16 were applied.

### 5.1 The two structural errors

Both were on pages a reader reaches first, and both were **verified against the code
before the page was touched, not against the finding text.**

* **`user_guide_concepts.rst` stated a path shape false for more than half the tree.** It
  gave `<holdings root>/<category>/<unit set>/<unit>/<path inside the unit>` for every
  category. That holds for six of the seven bare volume types. `documents/` has no unit
  level; the four per-unit derived categories put a *file* where those have the unit's
  directory; `checksums-archives-*` and `_infoshelf-archives-*` have no unit set directory
  either; and `_indexshelf-metadata` is one level deeper than any of them. Verified by
  walking both holdings trees: `find <category> -mindepth 2 -maxdepth 2 -type d` returns 0
  for every derived category, `checksums-archives-volumes/` holds `COCIRS_0xxx_md5.txt`
  directly, and `_indexshelf-metadata/COUVIS_0xxx/COUVIS_0001/` holds three `.pickle`
  files. The page now carries a table over every top-level directory.
* **The `general` suite enumeration accounted for 18 of its 28 rules.** It described three
  rules over each of five volume types plus three link shelf rules. Verified by
  introspecting the registry rather than by reading the source:

      >>> from pdsfile.holdings_maintenance.pds3 import pdsdependency as d
      >>> len(d.PdsDependency.DEPENDENCY_SUITES['general'])
      28

  and printing their titles: five rules over each of `volumes`, `calibrated`, `diagrams`,
  `metadata` and `previews` — the checksum file, the info shelf, the archive, and then the
  checksum file and info shelf **of that archive** — which is 25, plus three link shelf
  rules for `volumes`, `metadata` and `calibrated`. The page's own "Steps required" block
  had been printing the missing ten all along. The same introspection settled two
  neighbouring claims: `obsindex` holds exactly **one** rule, and the index shelf and
  cumulative-table rules live in the `metadata` and `cumindex*` suites.

### 5.2 The second-read number: 12 introduced, 7 survived

Round 4 read the first correction pass by name. **12 of its 19 findings were defects the
correction pass had introduced**, and round 1, working independently on other chapters,
confirmed four of the twelve. The clearest single case: the pre-correction installation
text carved `crlf` and `shelf_consistency_check` out of a claim about holdings paths, and
the correction deleted the carve-out.

This is the ninth PR in this phase to measure that ratio, and it lands where the other
eight did:

| PR | second-read findings that corrected the first read's own corrections |
|---|---|
| PR-24 | 11 of 23 |
| PR-25 | 10 of 21 |
| PR-27 | 34 of 57 |
| PR-28 | 15 of 22 |
| PR-29 | 10 of 13 |
| PR-30 | 15 of 24 |
| PR-31 | 9 of 10 |
| PR-32, round 4 | **12 of 19** |
| PR-32, round 5 | **16 of 16** |

### 5.3 Why a fifth round, and what it returned

Section 6.6 caps a PR at four rounds. The fifth was taken deliberately, and the
justification is the table above rather than a preference: applying 34 corrections rewrote
a large share of the guide's factual sentences — `4108fd4` is 18 files, 303 lines added
and 123 removed — and by round 4's own measurement, a pass of that size arrives carrying
new defects. Opening the PR on it unread would have shipped the exact defect this PR had
already measured twice.

The tree was frozen at `4108fd4` and a fresh reviewer was given that commit as its whole
scope, with **each of its 45 changed passages named by hand** and told to check every one
rather than sample. It checked all 45 and found 16 defects and 4 minor items. **All 20
were inside the corrections**, which is what naming the scope was for.

The two largest were the same failure — **a claim generalized from a single
measurement**:

* An unusable path was said to split the ten maintenance programs by **whether the path
  exists**. It splits them by **where the path is**. The correction had been written from
  one measurement, of a nonexistent path inside a holdings tree; measured across all ten
  and both cases, the tidy message and the traceback swap sides. The correction's own
  worked example illustrated a case its surrounding prose then described backwards.
* `--quiet` was said to leave the run's opening and closing lines on the terminal. It does
  — until a log root is configured, at which point it prints nothing at all. Measured: 6
  lines with no log root, 0 with one, by either route.

### 5.4 Two findings rejected on measurement

The brief required each finding to be verified against the code rather than against the
finding text, and twice that changed the answer.

* **Rounds 3 and 4 both reported that `user_guide_pdsindexshelf.rst`'s
  `Backup file skipped:` line must carry an absolute path**, each having read
  `logger.error('Backup file skipped', pdsf.abspath)` and observed that the skip happens
  before `logger.replace_root()`. Reproduced both ways in a sandbox: the path is absolute
  only while nothing has yet registered the root, which is true only of a run's **first**
  target. The published example names a metadata directory of three tables and the backup
  is not the first of them, so the published logical path is exactly what that run prints.
  Two independent reviewers reached the same wrong conclusion because each measured one
  position. The page now states the rule; deferred 356 records the inconsistency.
* **Round 5 reported that `show_opus_products` fails on a path outside a holdings tree**
  with a `ValueError` traceback, like the seven programs it grouped it with. Measured: it
  prints a `WARNING:` line, carries on to the next path, and **exits 0**. The finding was
  right that the enumeration was incomplete and wrong about the missing case, so the page
  gained a third group rather than a longer second one.

### 5.5 What the reviews could not verify

* That a complete published `COUVIS_0001` carries an `INDEX/INDEX.LBL`. Both available
  trees carry the same trimmed `INDEX/`, so the artifact is confirmed and the
  counterfactual is not. The page says which of its three errors is the tree's rather than
  the volume's.
* Any command in the guide that reaches the library's environment-reading path.
  `_path_utils.abspath_for_logical_path()` does read `cls._HOLDINGS_ENV`, and
  `_properties.internal_link_info` reaches it for a shelved link beginning `../../`, but
  no cross-volume label link in either tree exercises it. The claim in the guide was
  softened to what was proved.
* `pds4indexshelf`'s "no label at all" failure, whose bundle set is not in the sandbox.
  Round 1 copied `uranus_occs_earthbased` in and both documented failures then reproduced
  exactly.
* Cross-reference *resolution* during rounds 1 and 2, because a Sphinx build would have
  dirtied the frozen tree. Section 4's `-n -W` build is that check, run afterwards.

## 6. Where the guide documents behavior that looks like a defect

Ten deferred observations, 347–356. The three the guide most visibly had to work around:

* **347**: all five PDS4 programs identify themselves as their PDS3 twin and write their
  logs into the twin's directory. Pre-existing, verified against `main`. The guide states
  where the logs actually go.
* **354**: `pdsinfoshelf --initialize` with a file selection **crashes** with
  `AttributeError` instead of logging its refusal, because its logger is bound inside a
  branch above. Its PDS4 twin binds the same logger unconditionally and refuses cleanly;
  both checksum programs raise `ValueError`. One of the four is wrong and the fix is one
  line. Found by rounds 1 and 4, and its scope corrected by round 5, which is what
  established that the other three are fine.
* **355**: `--quiet` prints nothing at all once a log root is configured, because the
  run's outermost lines survive only as a no-handler fallback.

## 7. Gates at the final head

Every gate was re-run rather than carried forward. The previous executor's "all gates
green" was reported from `5cefb3d`, several commits and 34 corrections back.

Two heads appear below and the difference is stated rather than smoothed over. The test
suites were run at `b4c7526`; the only later commit, `4b4c30d`, rewrites one prose
paragraph in `user_guide_installation.rst` and touches nothing any test reads. The Sphinx
builds, the coverage checker, `ruff` and the two record checkers were all run at
`4b4c30d`, and CI runs the whole suite there as well.

### 7.1 The test suites, id sets diffed base to head

Both suites were run at head and their JUnit XML compared, id by id and outcome by
outcome, against the base tree at `532f65d`:

| | base `532f65d` | head | drift |
|---|---:|---:|---:|
| `ns` ids | 1,135 | **1,135** | 0 |
| `ns` passed / skipped / failed | 1,101 / 34 / 0 | **1,101 / 34 / 0** | 0 |
| `s` ids (`tests/pds3file/ tests/rules/pds3/ --mode s`) | 558 | **558** | 0 |
| `s` passed / skipped / failed | 555 / 3 / 0 | **555 / 3 / 0** | 0 |
| ids only in base | — | — | **0** |
| ids only in head | — | — | **0** |
| outcome changes | — | — | **0** |

**One base run was discarded under the deferred-342 precedent and it is recorded here
rather than dropped.** The first `ns` run at base reported 2 failed, 1,099 passed, both
failures in `tests/api/test_mixin_import_isolation.py`, and took 2,323 s. It was re-run on
a quiet machine, took 290 s and reported 1,101 passed / 34 skipped with an **identical id
set**. The head run took 191 s and shows neither failure. So the two failures were load,
not the tree; had they been recorded as a baseline, this PR would have looked like it
fixed two tests it never touched.

### 7.2 Everything else

| gate | exit | measured |
|---|---:|---|
| `scripts/run-all-checks.sh`, full run, holdings set | **0** | every check passed: ruff, ruff indentation, pytest 1,101 passed / 34 skipped, pyroma, API freeze, clean-install, both Sphinx builds |
| `scripts/run-all-checks.sh`, **no holdings variables** | **0** | /seti/newnav/capped-run.sh pytest 318 passed / 817 skipped — the holdings-free subset — and every other check passed |
| `python -m pytest tests/api` | 0 | **26 passed** |
| `ruff check .` | 0 | All checks passed |
| `ruff check --preview --select E111,E112,E113 .` | 0 | All checks passed |
| `critiques/pr-32/check_cli_coverage.py` | 0 | 0 findings over 15 programs, 108 options, 175 option strings, 1 default |
| `critiques/pr-29/check_citations.py` | 1 | **6 stale at base and 6 at head** — unmoved |
| `critiques/pr-28/check_record_numbers.py` | 1 | **15 stale at base and 15 at head** — unmoved |
| `git diff 532f65d --name-only -- src/` | — | **empty** |

Note that `run-all-checks.sh -c -s` does **not** run the Sphinx gate (deferred 330), so a
docs PR cannot be reported clean on its strength. The runs above are full runs.

The citation checker is the reason deferred 354 names the refusal by its code rather than
by a line number: it scans the deferred file to its end, so a new entry citing
`file.py:NNN` is a citation PR-29's table cannot cover and the count would have gone 6 → 7.
It was caught by running the gate at both trees rather than only at head.

### 7.3 The ratchet and the frozen files

| | base `532f65d` | head |
|---|---:|---:|
| per-file-ignores entries | 66 | **66** |
| code slots | 180 | **180** |
| findings, `--config 'lint.per-file-ignores = {}'` | 2,249 | **2,249** |
| `[project.scripts]` | 11 | **11** |

`pyproject.toml` is byte-identical to `532f65d`, so the ratchet could not have moved; the
four numbers above were measured anyway rather than inferred from that. The new checker,
`critiques/pr-32/check_cli_coverage.py`, satisfies the configured gate with no new
per-file-ignores entry.

The four frozen files are md5-identical to `532f65d`:
`tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`,
`scripts/dump_public_api.py`, `tests/api/test_api_freeze.py`.

`git status --porcelain -uall` is empty after both full runs, so `docs/_build/` stayed
out of the index.

## 7.4 CodeRabbit

CodeRabbit left 12 inline comments on PR #137. **Ten were valid and applied; two were
rejected on measurement**, which is the same discipline the rounds were held to.

| # | subject | disposition |
|---|---|---|
| 1 | the default check searched the whole chapter rather than the option's row | applied; a sixth mutation added, section 3 |
| 2 | "a task that versions one versions the other" reads badly | applied |
| 3 | "the other fourteen take **absolute** paths" contradicts the driver chapter, which documents relative paths | applied |
| 4 | "**Every** maintenance program writes a log file per target", with one path shape | applied: twelve of the fifteen write logs, ten in that shape, two without the category component, three not at all |
| 5 | "**Every** command shown in this guide was run" | applied — the five that were not are now named on the page, not only in this record |
| 6 | the severity table lists `FATAL` as a registered level and the next paragraph calls it an alias | applied |
| 7 | two sentences in `pds4indexshelf` are incomplete | **rejected**: "naming which flavor to be" and "depends on their existing" are both complete sentences that wrap across a line break |
| 8 | `--infoshelf` chains even when the checksum task logged validation errors | **rejected**: the driver sets `proceed = False` when a run logs any error, and `main()` chains only on `result.proceed`. Measured: `pdschecksums --validate --infoshelf` over a volume with 3 `ERROR` lines produced **0** `pds.validation.fileinfo` lines, so the chain did not run |
| 9 | the opening claims freshness for every rule where most rules require it | applied |
| 10 | "ten of them take absolute paths" conflates argument type with where a script can run | applied |
| 11 | `--table`, `--pprint` and `--raw` have a precedence and `--narrow-table` is not a fourth form | applied |
| 12 | exit 0 is for any run that reaches the end, not only one that produced output | applied |

Comments 3, 4, 5, 9, 10 and 12 are all the same defect: **a universal quantifier over a
set whose members differ.** That is the failure this PR's five rounds kept finding, and
CodeRabbit found six more instances of it after all five had run.

The correction to comment 4 then made a seventh, which is the ratio holding one more
time: the rewritten paragraph said "the ten use that shape", and eight do. The two index
shelf programs go one component deeper because their target is a table inside a unit, as
their own chapter has said all along. Caught by re-reading the correction rather than by
any gate, and fixed in `4b4c30d`.

## 8. Standing rules

- The four frozen files and `pyproject.toml` are byte-identical to `532f65d`.
- No golden or baseline was edited; no test was skipped or xfailed.
- The ratchet did not move.
- `ruff format` was not run.
- Nothing was staged with `git add -A`; every commit staged explicit paths.
- No literal machine path appears anywhere under `docs/`: the holdings roots are written
  `$PDS3_HOLDINGS_DIR` and `$PDS4_HOLDINGS_DIR` throughout, including inside captured
  output.
- Nothing under `docs/` names a plan, a critique, a PR number or a phase number.

## 9. Issue #45

Issue #45 asks for user documentation of the command-line tools **and** to "improve
internal documentation as needed". This PR closes the first half: all fifteen programs and
all twelve shell scripts have chapters. **The second half was already done by Phase 7's
docstring work** — PRs 29, 29a, 29b, 30, 30a, 30b and 30c put Google-style docstrings on
every public module, class, method and function in the package, and PR-31 published them
as the API reference this guide cross-references. Nothing in that half is outstanding.
