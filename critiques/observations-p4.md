# Observations — no action (P4)

Open observations recorded deliberately and needing no action: measured choices, frozen behaviour, and notes about method rather than code. Listed so that a later reader finds the reasoning instead of re-deriving it.

## Correctness

### 6000. The `Backup file skipped:` line's path is absolute or holdings-relative depending on where the…

**The `Backup file skipped:` line's path is absolute or holdings-relative depending
on where the skipped file falls in the run.** The index shelf driver decides the
skip before entering any task function, and it is the task functions that call
`logger.replace_root()`. So the first target of a run prints an absolute path and
every later one prints a logical path, in the same run and under the same message.
Measured in a sandbox: a backup table reached after another table had been shelved
printed `metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_index_backup.tab`; the same
file named alone printed the absolute path. Two PR-32 reviewers independently read
the published line as wrong because each had measured only one of the two positions.
The guide states the rule. **Owner: whoever next touches the index shelf driver.**

## Structure and duplication

### 6100. *`set_log_dirs(logfiles)`*, called by two of the three. Folds into (2)

*`set_log_dirs(logfiles)`*, called by two of the three. Folds into (2).

### 6101. *Log-path derivation.* Three forms: a fixed method plus a suffix; a method chosen per target…

*Log-path derivation.* Three forms: a fixed method plus a suffix; a method chosen
per target from `pdsf.bundlename`; a method whose suffix is passed only when
non-empty. A hook — clean.

### 6102. *Per-target handler directory.* `os.path.split(logfile)[0]` versus the `rpartition('/' +…

*Per-target handler directory.* `os.path.split(logfile)[0]` versus the
`rpartition('/' + progname + '/')` form, which observation 4044 explains is not
interchangeable. A hook — clean.

### 6103. *Target resolution.* `run_main` expands command-line paths itself with an existence check…

*Target resolution.* `run_main` expands command-line paths itself with an
existence check; `run_selection_main` calls `resolve_holdings_paths` +
`expand_selection_targets` and gets `(pdsdir, selection)` tuples;
`run_index_main` calls `index_targets`. A hook — clean.

### 6104. *The return contract.* Two `sys.exit(status)` against one `RunResult(args, status, proceed)`…

*The return contract.* Two `sys.exit(status)` against one
   `RunResult(args, status, proceed)`, which exists because `pdschecksums
   --infoshelf` chains a second run off `proceed`. Unifying it changes the exit path
   of all eleven tools.

**Line arithmetic.** 181 code lines across the three today. A merged driver would be
the 39 shared lines plus the calls into seven hooks; the 64 residue lines do not
disappear, they become per-family functions with `def` lines and docstrings, and
`ToolSpec` grows five or more fields. The saving is on the order of 20%, bought
with seven variation points at the seams of a loop whose every semantic line
differs, plus a log-text change on four tools to retire the eighth.

**The measurement points somewhere else.** The 15-line preamble is contiguous,
identical in all three, and carries no per-family variation at all: it parses,
guards the missing task, resolves the log root, builds the logger and adds the
root handlers. Extracting it as a fourth `_common` helper takes 38% of the
commonality with **zero** new variation points and leaves the three loops alone.
That is a small PR with a small tool-run diff, and it is a different PR from the one
observation 6114 was asking about. Its one wrinkle is `status = 0`, which sits inside the
block and is a local each driver reads later, so the helper returns `(args, logger)`
and the `status = 0` stays behind — 14 lines move, not 15.

**Answer: they do not collapse cleanly; do not merge them.** PR-28 measured and did
not act.
**Owner: recorded, not open — unless the owner wants the 15-line preamble
extraction, which would be its own PR.**

### 6105. *The task call.* `tasks[t](pdsdir)`, `tasks[t](pdsdir, selection)`, `tasks[t](pdsf…

*The task call.* `tasks[t](pdsdir)`, `tasks[t](pdsdir, selection)`,
`tasks[t](pdsf, logger=logger)` — three signatures — plus
`run_selection_main`'s rewrite of `reinitialize` to `update` when a selection is
given.

### 6106. 18 of the 34 rule modules define a module-level `opus_products` table, one namespace away from…

**18 of the 34 rule modules define a module-level `opus_products` table, one
namespace away from the mixin method of the same name.**
`src/pdsfile/pds3file/rules/COISS_xxxx.py:311` and the equivalent line in 17
other rule modules define `opus_products = translator.TranslatorByRegex([…])`
at module level, which the rule *class* then consumes as
`OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS` (`:795`).
Because the table is a module global and the class attribute is spelled in
upper case, it never shadows `_OpusMixin.opus_products` — verified: **zero**
rule modules have an indented `opus_products =`, and the mixin/subclass
intersection is empty across the whole 33-class hierarchy
(`critiques/phase5-validation.md`, PR-19 §11).

Nothing is broken. But the two names differ only in where they are bound, the
method is now defined in a different file from the class that inherits it,
and PR-24 already has to do delicate `F811` work in `COVIMS_0xxx.py` for the
same table-versus-method confusion one level down. A one-line comment at the
top of the rules' `OPUS_PRODUCTS` blocks, or a rename of the module-level
table, would remove the trap. **Owner: PR-24**, which is editing these files
anyway.

### 6107. `_common.py` already mixes the generic driver with one family's constants, and there will be…

**`_common.py` already mixes the generic driver with one family's constants,
and there will be five families.** `_common.py`'s "Archive tools" section
holds the four archive `*_LIMITS`, the description and help templates, and
three archive functions, below a generic section holding `ToolSpec`,
`build_arg_parser` and `run_main`. That follows the plan, whose target
interface puts `hashfile()` and the three `move_old_<kind>()` functions — each
belonging to one or two tools, not five — in the same file. At five pairs the
file becomes the union of five families' constants and helpers.

The question to settle **before** PR-26 rather than after: does each family
get a section in `_common.py`, or its own module beside it
(`_archives_common.py`, `_shelf_common.py`, …) with `_common.py` reduced to
the genuinely cross-family driver?

**Updated 2026-08-05: PR-25 has now pre-committed shelf-family code to
`_common.py`.** The owner's ruling moved `hashfile()`, the three
`move_old_<kind>()` functions and `LOGDIRS` into it, so the file holds a
"Checksum and shelf file tools" section serving six tools that are **not** on
the driver and call neither `run_main` nor `ToolSpec` nor `build_arg_parser`.
The file now has two disjoint audiences.

**DECIDED (owner's rule, applied 2026-08-05): one file, a section per family.**
The owner's rule is to decide by volume — a little code stays in one file, a lot
splits into separate files beside it. Measured at the final commit,
`_common.py` is **666 lines** (486 before this round: `+190` when the
versioning section arrived — `+151` for that section and `+39` for the
`@dataclass` conversion, the two `ToolSpec` fields with their docstring,
`log_paths_for` and the imports — and then `−10` when the three versioning
functions became one), in a 31-line header plus four banner-separated
sections — tool specification 75, command line 219, archive tools 214,
checksum and shelf file tools 127.
**The number the decision turns on is 1,000**, which is not arbitrary:
overrides deviation (3) holds `holdings_maintenance/` modules to the repo's
1,000-line module limit and explicitly declines to waive it for them. At 666
the file is at 67% of its own governing limit, so the volume rule says keep it.

**And the same number says PR-26 splits it.** The archives family contributed
214 lines of family-specific code out of a pair that measured 1,155 lines at
`ab1fa3b`, a rate of 18.5%. The four pairs still to migrate measure 1,687
(checksums), 1,758 (infoshelf), 2,954 (linkshelf) and 1,086 (indexshelf) lines;
at that rate they project **~1,400 more lines**, which puts `_common.py` near
2,100, twice the limit. The linkshelf figure is the softest, because PR-27
moves the pds3 `REPAIRS` table out to its own data module, but even halving the
projection crosses 1,000. So the structure is decided and so is the trigger:
the first family whose extraction takes `_common.py` past deviation (3)'s 1,000
lines splits it, the driver staying in `_common.py` and each family taking a
module beside it. On the projection that is PR-26.
**Owner: recorded, not open. PR-26 executes the split when the measurement
crosses.**

### 6108. `_shelf_common.py` serves two audiences, which is the question entry 98 answered only for…

**`_shelf_common.py` serves two audiences, which is the question observation 6107
answered only for `_common.py`.** The split PR-26 performed put the checksum and
shelf family's code in `_shelf_common.py`: the versioning helpers
(`move_old`, `next_version_dest`, `VersionedFile`, `LOGDIRS`, `hashfile`) plus
the new selection driver (`run_selection_main`, `resolve_holdings_paths`,
`expand_selection_targets`, `modtimes_agree`). Measured at PR-26's head, six
tool modules import it, but only four of them — the two checksums and the two
infoshelf tools — are on the driver. `pdslinkshelf` and `pds4linkshelf` import
it for `LINK_SHELF` and `move_old` alone, and call neither the driver nor
`ToolSpec`.

That is the same shape observation 6107 flagged before the split: one file, two
disjoint audiences. It is not urgent — the file is 529 lines against a limit of
1,000 — but PR-27 migrates the linkshelf and indexshelf pairs and will add to
it, so the measurement should be taken again there. If it crosses, observation 6107's
rule applies unchanged, and the natural seam is the one already visible: the
versioning and hashing helpers serve six tools regardless of driver, while the
driver serves four.

**Re-measured by PR-27.** With both of this PR's families in it,
`_shelf_common.py` measured 1,827 lines, so observation 6107's rule fired and it split
by family: `_shelf_common.py` 523, `_indexshelf_common.py` 620,
`_linkshelf_common.py` 729. The two disjoint audiences are still there and the
file is smaller than when this entry was written: 523 lines holding the
versioning helpers six tools reach regardless of driver, plus
`run_selection_main` and its two path helpers, which four tools use. The link
shelf tools now reach it for `LINKSHELF_LOGNAME`, `LINK_SHELF`, `move_old` and
`UNIT_LOG_PATH_METHOD` only. Nothing forces a second split; the seam this entry
named is where it would go.
**Owner: recorded, not open.**

### 6109. `PdsDependency.purge_cache()` has no caller

**`PdsDependency.purge_cache()` has no caller.**
`grep -rn 'purge_cache' --include=*.py src/ tests/ scripts/` finds the definition and
nothing else. It empties `MODTIME_DICT`, a class attribute that lives for the process,
so the only caller it could have is one that changes the tree between two dependency
tests, and nothing here does: the tool reports what to do and does not do it.
**Owner: recorded, not open.**

### 6110. `PdsDependency` writes two instance attributes that nothing reads

**`PdsDependency` writes two instance attributes that nothing reads.** `self.suite` and
`self.regex_pattern` are assigned in `__init__` and never read;
`grep -rnE 'regex_pattern|\.suite\b'` over `src/` and `tests/` finds only the two
assignments. What carries the suite membership is the registration in
`DEPENDENCY_SUITES` a few lines above, and what carries the pattern is `self.regex`.
**Owner: recorded, not open.**

### 6111. `re_validate.key_from_log_path()` is called only by tests

**`re_validate.key_from_log_path()` is called only by tests.** `get_all_log_info()`
performs the same derivation inline rather than calling it, and
`grep -rn 'key_from_log_path' --include=*.py src/ tests/` finds the definition and two
tests -- one of which,
`test_key_from_log_path_agrees_with_the_key_get_all_log_info_builds`, exists to hold
the inline derivation to the function. **Owner: recorded, not open.**

### 6112. The `__dict__` and `__weakref__` descriptors have moved off `PdsFile` onto its first mixin base

**The `__dict__` and `__weakref__` descriptors have moved off `PdsFile` onto
its first mixin base.** Measured: on the parent both are in
`vars(PdsFile)`; on this branch both are in `vars(_LocalFsMixin)` and
`vars(_ShelfMixin)` and neither is in `vars(PdsFile)`. That is ordinary
CPython behavior — the descriptors are created for the first class in a
hierarchy whose instances need them — and nothing observable changes:
`dir(PdsFile)`, the API manifest, instance `__dict__`, weak references and
pickling were each checked and are identical. The consequence worth recording
is that as Phase 5 adds mixins, the descriptors keep migrating to whichever
base sorts first, so any introspection of the form `'__dict__' in
vars(PdsFile)` is unstable across the phase's PRs. Nothing in `src/`,
`tests/`, `scripts/` or either consumer does that today.
`tests/api/test_mixin_collisions.py` excludes both names from what counts as
"defined by a mixin", which is why its collision check does not fire on them.
**Owner:** phase "b" of issue #77.

### 6113. The `cls.__bases__[0].__name__ == 'Pds4File'` string sniff is fragile, and the plan asks for it…

**The `cls.__bases__[0].__name__ == 'Pds4File'` string sniff is fragile, and
the plan asks for it to be recorded rather than fixed.**
`src/pdsfile/_index_rows.py`, inside
`data_abspath_associated_with_index_row`'s nested `get_keys`, chooses between
the PDS3 and PDS4 column-name tables by comparing the *name* of a class's
first direct base against a string literal. It is fragile in three separate
ways: it breaks for any class whose `__bases__[0]` is not exactly
`Pds3File`/`Pds4File` (a deeper subclass, or a class that lists a mixin
first); it silently takes the PDS3 branch for `Pds4File` itself, whose
`__bases__[0]` is `PdsFile`; and it is invisible to every static tool,
because the class is named only in a string.

The plan's PR-19 section is explicit that it must **not** be changed here:
"an inherited boolean would not be behavior-identical (it would differ for
`Pds4File` itself and for deeper subclasses), so replacing it here would
violate the freeze's spirit — record the string-sniff fragility as a
phase-'b' item instead and move on." PR-19 moved it byte-for-byte and
verified the premise the plan rests on: `__bases__[0].__name__` is identical
for all 34 classes in the hierarchy before and after the move, and the
sniff's verdict is `True` for exactly the same six pds4 rule classes on both
sides (`critiques/phase5-validation.md`, PR-19 §7).

The phase-"b" fix is an inherited class attribute (e.g. a private
`_IS_PDS4` set on `Pds3File`/`Pds4File`) read as `cls._IS_PDS4`, which is
correct for every class in the hierarchy rather than only for the direct rule
subclasses. It is an observable behavior change for `Pds4File` itself and for
any deeper subclass, which is exactly why it is not a phase-"a" change.
**Owner: phase "b" of issue #77.**

### 6114. The `run_index_main` driver is about two thirds a copy of `run_main`

**The `run_index_main` driver is about two thirds a copy of `run_main`.**
Measured with each function's docstring, blank lines and `def` line dropped and
the longest common subsequence taken: `run_index_main` is 69 lines against
`run_main`'s 66, with 44 line-identical — 64%. `run_selection_main`, PR-26's
second driver, is 78 lines with 46 identical — 59%. Two of the four differences are forced — the per-target
backup skip, which has to sit inside the log hierarchy to reach the exit
status, and the log directory, which is the tool's own rather than the
target's — and two are preservation: the quoted task header both index tools
wrote at the base, and passing the logger to the task explicitly. This is the
same trade PR-26 made for `run_selection_main`, and it is now the second time
it has been made. A third instance would be worth stopping for.

**Answered once all five families had migrated — see the amendment to this
entry at the end of this file.** The pairwise figures above are this entry's
original measurement and are superseded there; the answer is that the three
drivers do not collapse.
**Owner: recorded, not open.**

### 6115. The backup skip

**The backup skip.** `run_index_main` only, and observation 3203 records why it has to
sit inside the log hierarchy rather than in the target list: the skip is reported
as an error and has to reach the exit status. A guard hook or a flag.

### 6116. The task header

**The task header.** `Task X for` (`run_main`), `Task "X" for`
(`run_index_main`), and `Task "X" for selection S` / `Task "X" for`
(`run_selection_main`). This is the one variation point a merger would **not**
have to keep: the owner's 2026-08-05 output-text ruling says text may move where
keeping it would force a flag whose one job is to re-create one side's wording,
which is exactly this, and PR-25 has already moved a log line on that basis.
Unifying it is a log-text change on four tools, enumerable. So this is not a
reason not to merge — it is a cost, not an obstacle, and the case rests on the
other seven. (Note that once the header is unified, the `for selection S`
variant remains, inside variation point 7.)

## Test coverage

### 6200. `run_tool_in_process` captures into `io.StringIO`, which has no encoding

**`run_tool_in_process` captures into `io.StringIO`, which has no encoding.** A
real `python -m` run writes through an encoded stream, so a byte the
subprocess's locale cannot encode raises `UnicodeEncodeError` there and cannot
here — an in-process test would pass where the tool it stands for would die.
The one migrated tool cannot reach that state in this repository's tests: `crlf`
prints only paths the test itself created and four ASCII status words. It is
written down because the
runner's docstring lists its other fidelity caveats — the working directory,
and that `sys.argv` is rebound for the call — and this is the third.
**Owner: open.**

### 6201. `tests/rules/pds3/test_cocirs_xxxx.py`'s two association loops now differ in what their failure…

**`tests/rules/pds3/test_cocirs_xxxx.py`'s two association loops now differ in
what their failure message reports.** The `F841` fix deleted the unused
`trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]` from the first
of two otherwise-identical loops; the surviving loop still builds `trimmed`
and interpolates it into its assertion message, while the first now
interpolates the full `abspaths`. The deletion is what `F841` asks for and is
behavior-neutral — the text only appears on a failure — but it settles a
pre-existing copy-paste inconsistency in the less informative direction.
Either both loops should report the trimmed paths or neither should.
**Owner: a test-content PR.**

### 6202. One of the suite's twenty monkeypatch sites is a portability guard whose removal is invisible…

**One of the suite's twenty monkeypatch sites is a portability guard whose
removal is invisible on Linux, so "remove the patch" is not a valid
forced-wrong control for it.** `tests/core/test_pdsfile_path_resolution.py:92`
stubs `glob` inside `abspath_for_logical_path.__globals__` so that
`glob.glob('/Library/WebServer/Documents/holdings*')` — the last-resort MacOS
website-install branch — returns `[]`. On this machine the real call returns
`[]` too, so **deleting the stub outright leaves the whole of `tests/core/`
and `tests/pds3file/` green (531 passed)**, which reads exactly like "this
patch is dead" and is not what it means. Forcing the stub to answer *wrongly*
— a non-empty list — does turn
`TestHoldingsEnvironmentVariable::test_a_class_does_not_borrow_another_class_holdings_root`
red, which is the control the Phase-5 briefs actually ask for.

Two consequences worth recording. The mechanical form of the monkeypatch
audit that PR-17 through PR-21 used — remove the patch, watch the test go
red — is sound for a patch that supplies a value the code needs, and unsound
for a patch that *suppresses* a platform-specific value; both forms exist in
this tree and only this one is of the second kind. And the branch the stub
guards has **no coverage at all on Linux**: nothing in the suite reaches the
non-empty-glob path of `abspath_for_logical_path`, on any machine that is not
a MacOS Viewmaster host. PR-22 may not act on either — its gate is the
pass/fail set, and adding a test id is movement beyond the ten the a since-resolved observation
check required.
**Owner: unassigned (a future test PR, not Phase 5).**

### 6203. The help *text* of the two new parsers is pinned only by its flag names

**The help *text* of the two new parsers is pinned only by its flag names.**
Replacing `crlf`'s whole `description=` literal, or any one help string, with
junk leaves the three tool-test modules green: the help tests assert the
`usage: crlf.py` prefix and that each flag name appears, and nothing else.
That is deliberate for text this PR invented — a golden of a `--help` screen
pins argparse's line-wrapping as much as the words, and argparse rewraps to
the terminal width — but it means the text is documentation with no gate, and
PR-32 is chartered to write a user-guide chapter per program from it. The
out-of-repo transcript does capture both screens byte-for-byte at a pinned
`COLUMNS`, which is where a reader can see what they currently say.
**Owner: open.**

### 6204. The log-path golden tests stop matching in the year 2100

**The log-path golden tests stop matching in the year 2100.**
`tests/pds3file/test_pds3file_blackbox.py`'s 41 log-path cases match the
embedded time tag with the literal regex `20..-..-..T..-..-..`, so they assert
the format and the position of the tag rather than its value — which is what
lets them run without pinning the clock, and PR-18's §9 controls show they are
sensitive to everything around it. The leading `20` is the only part that is
not a wildcard, and it is a date assumption in a test rather than in the code:
`LOGFILE_TIME_FMT` is `'%Y-%m-%dT%H-%M-%S'` and has no such limit. Replacing
`20..` with `\d{4}` costs nothing and is behavior-neutral, but it is an edit to
a test file PR-18 does not otherwise touch, and PR-18's gate is an identical
pass/fail set. **Owner: PR-24**, which already edits the test tree's style.

## Gates, tooling and CI

### 6300. `critiques/pr-29/check_citations.py` reads every deferred entry written after PR-29's, not only…

**`critiques/pr-29/check_citations.py` reads every deferred entry written after
PR-29's, not only PR-29's.** It slices the file with
`block = text[text.index('## From PR-29 ('):]`, which runs to the end, so every entry
added by every later PR is inside its scope while `CITATIONS` still lists only
PR-29's files. Any later entry that writes a `path/file.py:NN` citation for a file
PR-29 did not cite therefore reports `cites <file>, which no entry covers` and the
count moves off the recorded 6. PR-31 hit it once, in observation 3101, and rewrote the
sentence to name the file and the import without the line number; the checker then
reproduced the base output byte for byte. This entry cannot quote the citation that
tripped it, for the same reason -- the pattern is a backticked path ending in `.py`
followed by a colon and a line number, so writing the example re-triggers the
finding. The alternative is to extend `CITATIONS`, which means a PR-29
tool acquiring later PRs' citations. **Owner: whoever next needs a line citation in
a deferred entry.**

### 6301. A local full run materializes `src/pdsfile/_version.py`, which makes the coverage check's…

**A local full run materializes `src/pdsfile/_version.py`, which makes the coverage
check's exemption load-bearing rather than theoretical.** The clean-install gate
builds the project, `setuptools_scm`'s `write_to` writes the file into the source
tree, and it stays there: it is gitignored, so nothing notices. With the file
present, `check_docstrings.py` over `find src/pdsfile -name '*.py'` reports **79
files and one M1 finding** (the generated file has no module docstring), and the
Sphinx build still reports **78 of 78 modules documented**, because
`_GENERATED_MODULES` excludes it. Any later checker that walks `src/pdsfile/*.py`
has to exclude it too, and any later measurement of "the number of modules" has to
say which of the two numbers it means. **Owner: whoever writes the next such
checker.**

### 6302. `scripts/read-docs.sh` is a reading tool, not a gate, and is not held to the gate's standard

**`scripts/read-docs.sh` builds the documentation with `SPHINXOPTS="-W"` and no `-n`,
which is less than `run-all-checks.sh` runs.** That is correct and settled, not a gap.
The script exists so a person can build the documentation and open it; its header says
so, and it ends by handing `docs/_build/html/index.html` to the platform's default
handler. It was never meant for automation and was never designed to check anything.

**Owner ruling (2026-08-15): the two are not meant to agree, and no change is wanted.**
A reading tool that failed the way a gate fails would be worse at the job it has --
someone reading new prose does not want the build refused over an unresolved
cross-reference. `run-all-checks.sh` is what the repository's enabled gate set means,
and it is the only thing that speaks for the documentation's correctness.

Recorded here rather than dropped because a no-context reviewer comparing the two
invocations will raise it again, and this is the answer.

## Documentation and records

### 6400. `_recache()` fills `_isdir_filled` as a side effect, so every "fills these slots" list in…

**`_recache()` fills `_isdir_filled` as a side effect, so every "fills these slots"
list in `_properties.py` is a lower bound for an object already in the cache.**
`_recache` calls `CACHE.set`, whose lifetime is computed by
`cache_lifetime_for_class`, which reads `arg.isdir` for any object with a non-empty
interior. So a property whose body never mentions `isdir` still fills that slot, by
way of the very call that makes the value survive.

This is worth recording beyond the docstrings it affects, because it is a cost that
does not appear anywhere in the module that pays it, and because it cost round 4 a
false lead before it was traced. Any future attempt to check the fills lists
mechanically -- which observation 6602 recommends -- has to account for it or it will report
one spurious omission per property.
**Owner: PR-30, as a note for the instrumentation observation 6602 asks for.**

### 6401. `index_reinitialize` takes pds4's comment over pds3's

**`index_reinitialize` takes pds4's comment over pds3's.** pds3 wrote
`# ing if shelf file does not exist`, a mangling of pds4's
`# Warn if shelf file does not exist`; the merged function has pds4's. Like the
dead `move_old` call PR-27 enumerates as change 10, this is a difference only
one of the two flavors had, so merging had to pick. Recorded because PR-27's
enumeration rule covers log and output text and says nothing about comments,
and this is the one comment in the migration where the merge made a choice
rather than carrying a block along with its code.
**Owner: recorded, not open.**

### 6402. An alias inherits its base member's undocumented hazards

**An alias inherits its base member's undocumented hazards.** `Pds3File`'s
`is_volset_dir` and `is_volset_file` forward to `is_bundleset_dir` and
`is_bundleset_file`, which read `isdir`, which `_properties.py` documents as raising
`KeyError` under `SHELVES_ONLY` "for a path the shelf covers and holds no entry
for"; `volset_pdsfile` and `volume_pdsfile` forward to base methods that call
`os_path_exists()` and `from_abspath()`, both of which can raise. None of the four
base members carries a `Raises:` section, so PR-30a's aliases do not either, and
round 2 could not construct a bundle-set-level path that is shelf-covered and absent
to demonstrate the first. The gap is in the base members rather than in the aliases,
which is why it was not closed on one side only. **Owner: a later PR that revisits
`pdsfile.py` and `_properties.py`, or PR-35 when it decides what the stubs
declare.**

### 6403. Forty-three docstrings are written, maintained, and never checked by anything, because they are…

**Forty-three docstrings are written, maintained, and never checked by anything,
because they are never published.** Measured against `objects.inv` and an AST walk:
52 objects carry a docstring in the source and are absent from the published
reference -- 25 private names and 27 dunders, and zero public objects. Nine of the
27 were `__init__` docstrings, six with a `Parameters:` block, and those are now
published by `autoclass_content = 'both'` (verified: 9 published, 0 missing). The
other 43 remain unpublished, so a broken `:meth:` target, malformed RST or a stale
`:class:` reference inside one of them is invisible to `-n -W`. Demonstrated: a
`:meth:` naming a method that does not exist, placed in `_clean_join`'s docstring,
passes the gate; the identical lines in a published function fail it. This is the
price of not publishing private members, and it is worth knowing before a later PR
promotes one of those objects to the public surface. **Owner: nobody yet; it is a
standing limit of the gate.**

## Accepted or frozen

### 6500. `uranus_occs_earthbased.py`'s module-level loop leaves its control variables bound as public…

**`uranus_occs_earthbased.py`'s module-level loop leaves its control
variables bound as public module attributes.** The loop at `:537` runs at
module scope, so `bundle_prefix`, `opus_id_prefix_e`, `opus_id_prefix_i` and
`opus_id_prefix_a` survive it as attributes of
`pdsfile.pds4file.rules.uranus_occs_earthbased` — and all four are in
`tests/api/api_manifest.json`. That is why PR-24 could not take `B007`'s
rename here: `_bundle_prefix` would remove a name the freeze records. The
names are an accident of writing the loop at module level, not an intended
API; wrapping the loop in a function would drop all four at once, which is a
surface change needing sign-off.
**Owner: owner decision; a natural fit for the Phase 7/8 surface tidy-up.**

### 6501. A traceback raised inside the preamble now names `setup_run`

**A traceback raised inside the preamble now names `setup_run`.** Extracting a
function adds a stack frame, and one input class reaches it: a `--log` root the
process cannot write into raises `PermissionError` from
`logger.add_handler(make_handler(path))`, the preamble's last line. On all ten
driver-backed tools the traceback gains three lines — the call site, its caret
row, and a `_common.py … in setup_run` frame — beneath the frame that still
names the driver. Nothing else moves: the 158-scenario tool-run capture
covering every tool, every task and the failure paths is byte-identical between
base and head. This is a change to what a tool prints, on an input no test and
no golden covers, so it is recorded rather than normalized away. Whether a
traceback's shape is part of the CLI contract at all is the owner's call.
**Owner: open.**

### 6502. The `--archives` help text reads "refer to the the archive file"

**The `--archives` help text reads "refer to the the archive file".** All four
tools carried that duplicated word before PR-26, in four hand-copied copies;
PR-26 replaced them with one shared constant and **kept the typo deliberately**,
because reproducing the help text exactly is what makes all four tools'
`--help` output byte-identical to base, which is the check that the shared
constants did not quietly reword anything. Now that it is in one place, fixing
it is a one-character decision rather than a four-file sweep — but it is a
user-visible text change and so wants to be made on purpose rather than folded
into a refactor.
**Owner: open.**

## Process notes

### 6600. `PYTHONPATH=<other tree>/src` does not redirect pytest's in-process imports, so the obvious…

**`PYTHONPATH=<other tree>/src` does not redirect pytest's in-process
imports, so the obvious differential probe silently measures the wrong tree.**
`pyproject.toml` sets `pythonpath = [".", "src"]`, and pytest prepends those to
`sys.path` **ahead of** `PYTHONPATH`. Measured from inside a test run as
`PYTHONPATH=<base>/src:<work> pytest …` from the work tree:

```
sys.path[:5] = ['<work>/tests', '<work>', '<work>/src', '<work>', '<base>/src']
pdsfile.__file__ = <work>/src/pdsfile/__init__.py
```

A plain `python -c "import pdsfile"` with the same `PYTHONPATH` resolves to
`<base>`, which is what makes this easy to get wrong: the check that proves
the tree is honest outside pytest and misleading inside it. Tests that shell
out (`support.run_tool`, which runs `python -m <module>` in a subprocess) *are*
redirected, because the subprocess never sees pytest's insertion. So a probe
run this way exercises base for subprocess tests and head for in-process ones,
in the same session, with nothing in the output saying so.

PR-26's first base probe was wrong for this reason and was redone. Recorded
because every future PR that wants "do my new tests fail at base?" will reach
for the same command. The reliable forms are to run pytest **from** the base
worktree with the head's test files, or to assert the measured path inside a
test.
**Owner: recorded, not open — but worth a line in the plan's gate section.**

### 6601. A `Raises:` section is not satisfied by prose elsewhere in the same docstring

**A `Raises:` section is not satisfied by prose elsewhere in the same docstring.**
`COUVIS_0xxx.DATA_SET_ID` described the two subscripts in its return expression and
said what does not guard them, and listed only `ValueError` and `FileNotFoundError`
under `Raises:`. Rounds 2 and 4 both raised the subscripts; neither asked for the
section to be amended, and the executor read the prose as discharging the obligation.
It does not: the generated API page renders `Raises:` as the contract.
`tests/docs/check_docstrings.py` cannot catch this, because E2 covers only
classes raised by a `raise` statement in the body -- a subscript that can raise is
invisible to it, which is exactly why PR-29 widened the *convention* to cover
mechanisms E1 can verify. **The convention was the thing not applied.**
**Owner: a reviewer-brief instruction for the next docstring PR -- ask explicitly
whether every mechanism the prose names appears in `Raises:`.**

### 6602. A claim about what a property costs, or about what a constructor pre-set, is mechanically…

**A claim about what a property costs, or about what a constructor pre-set, is
mechanically checkable, and checking it mechanically finds what reading does not.**
Round 3 established five of its twenty-two findings by instrumentation rather than by
reading: blanking every slot on a fresh object, reading one property and diffing the
slots, which found nine docstrings naming fewer slots than they fill; comparing each
body's assigned slots against `new_merged_dir()` and `new_index_row_pdsfile()`, which
found five saying nothing about a slot that is pre-set; counting the four link-path
prefixes over 400 real shelves, which found the resolution anchor the prose omitted;
and counting 5,972 volume-info entries, which found the 91 checksums that are not in
the documents tree.

None of those is reachable by careful reading, and all of them are cheap. **PR-30's
reviewer brief should ask for the instrumentation explicitly**, in the same way this
PR's briefs asked for relationship claims to be checked by reading the other end.
**Owner: PR-30, as a reviewer-brief instruction.**

### 6603. A claim stated in more than one place is corrected in one place, and this PR found four more…

**A claim stated in more than one place is corrected in one place, and this PR found
four more instances of it.** PR-29a's record named the partial fix as a pattern no
reviewer brief had asked about. This PR's briefs asked, and rounds 4 and 5 found it
four times, and in every case the copy left behind was the *summary* rather than the
detail. `full_size`'s own docstring correctly said it raises IndexError on a set with
nothing indexed by size; the `PdsViewSet` class docstring listed it among the lookups
a named-only set is served by. `IDX_EXT` and `LBL_EXT` being defined only on the
subclasses is stated explicitly in `_local_fs.py`, `_associations.py` and
`_properties.py`, and was denied by `pdsfile.py`'s module map, the fourth copy and the
one nobody looked at. `filename_keylen`'s own docstring said it is the one lazy
property with no `_recache()` and `_properties.py`'s module docstring said every lazy
property calls it. And **`filespec`'s body and its own `Returns:` disagreed after
round 3 fixed one and not the other**, which is the pattern inside a single
docstring.

**The rule this suggests is that a claim should be checked from the summary downward,
not from the detail upward**: the detailed docstring is the one whose author had the
code in front of them, and the summary is the one that gets stale. Both copies here
were found by a reviewer who was told to grep for other copies of a claim it had just
checked, which is the practice worth carrying into PR-30.
**Owner: PR-30, as a reviewer-brief instruction.**

### 6604. A probe can silently ignore the module it was asked to build, and report clean

**A probe can silently ignore the module it was asked to build, and report clean.**
`critiques/pr-29a/build_docs_probe.py` takes extra module names here so that
`_properties` can join its page list. Its first extended run reported a clean
fourteen-module build; it had in fact run a thirteen-module build, because it was
executed from the base tree, whose copy of the script predates the argument and drops
it. The repair is to verify the artifact rather than the exit status: the generated
`api.rst` is now grepped for the page. This is the same failure CodeRabbit caught in
PR-29a's probe -- a gate reporting success for work it did not do -- reached by a
different route, which is the argument for checking that a gate *ran* and not only what
it *said*.
**Owner: recorded, no action.**

### 6605. A second adversarial read must start from a frozen tree, and this one did not

**A second adversarial read must start from a frozen tree, and this one did not.**
Round 4 was launched while the executor was still applying round 3's corrections, so
sixteen of the forty-four sentences its brief named were absent from the text it first
read. The reviewer noticed, re-read all 68 members and re-ran every measurement, and
said so in its report. The cost was its time; had it not noticed, its verdicts on those
sixteen would have described prose that was never in the branch, and they would have
been indistinguishable from verdicts on prose that was.

The rule this suggests is procedural and cheap: **commit the previous round's
corrections, and confirm the corrected phrases are actually in the file, before
launching the round that reviews them.** The confirmation matters as much as the
commit -- a separate defect in this PR was that a batched edit aborted on its first
pair and wrote nothing, so eight of round 3's corrections were claimed by a commit
message and were not in the tree until a phrase-by-phrase grep found them.
**Owner: PR-30, as a process note.**

### 6606. A second read finds most of its yield in the first read's corrections, and the share is still…

**A second read finds most of its yield in the first read's corrections, and the
share is still rising.** PR-29a measured 11 of 23, PR-29b 10 of 21, PR-30 34 of 57.
PR-30a measures **15 of 22**, the highest yet as a share. The two second reads were
given the correction diff by commit range and told to attack it first, which is what
PR-30's record recommended and what produced the result; the eight round-3 findings
and seven round-4 findings in that class include the sharpest defects of the whole
PR, among them a claim about a link shelf triple that was **less** true than the
sentence it replaced.

The lesson is not that corrections are unusually error-prone in the abstract. It is
that a correction is written under the impression that the matter has just been
settled, and is therefore written more confidently and checked less. **Owner: a
reviewer-brief instruction, already followed here and worth keeping: give the second
reader the correction diff by commit range, name the claims it makes, and say that
they are unproven.**

### 6607. A subprocess-based tool test used to exercise whichever `pdsfile` was installed, so a green run…

**A subprocess-based tool test used to exercise whichever `pdsfile` was
installed, so a green run proved nothing about the tree it ran in.** observation 6600
records the in-process half of this trap. The subprocess half is worse,
because it is silent in both directions: `support.ToolTree.env` passed the
ambient environment through without naming a `PYTHONPATH`, so
`support.run_tool()` and `run_console_script()` launched tools that imported
whatever the interpreter resolved — for an editable install, the tree that was
installed rather than the tree under test. Measured in the PR-26 worktree
before the fix, with no `PYTHONPATH` set:

```
$ pytest tests/holdings_maintenance/ -q
7 failed, 269 passed        # the installed tree's defects, not this tree's
$ PYTHONPATH=$PWD/src pytest tests/holdings_maintenance/ -q
276 passed
```

PR-26 closed it: `ToolTree.env` now sets `PYTHONPATH` to `REPO_ROOT/src`, so a
tool subprocess runs the code its tests belong to, and the no-`PYTHONPATH` run
above is green. That also makes the in-process and subprocess halves agree,
which is what observation 6600's split-brain was.

The consequence for observation 6600 is that the **only** reliable differential probe
is now to run pytest **from** the tree being probed, with the other tree's test
files copied in — `REPO_ROOT` is derived from the test file's own location, so
that form pins itself correctly. PR-26's own base probe was redone that way.
**Owner: recorded, not open.**

### 6608. An extraction sweep must ask which module namespaces the tests *patch*, not only which globals…

**An extraction sweep must ask which module namespaces the tests *patch*, not
only which globals the code *reads*.** PR-16's free-variable sweep answered
"what must move with the code" correctly and completely. It could not have
caught what the review did: `tests/core/test_pdsfile_path_resolution.py`
replaced `glob` on `pdsfile.pdsfile`, so after the move the stub sat on a
namespace `abspath_for_logical_path` no longer resolves through, and the
test's outcome became a property of the machine rather than of the test. It
still *passed*, so §6.2's outcome-set diff — which compares pass/fail, not
what a test actually exercises — is structurally blind to it. The missing
step is a one-line grep for `monkeypatch.setattr` / `setattr(<module>` over
`tests/` and `scripts/` naming any module a PR moves code out of. PR-16 fixed
its own site by patching the function's `__globals__`, which follows the
function; the general step belongs in every later extraction PR's checklist.
It matters most for **PR-17**, which moves the `os`-resolving filesystem
helpers, where a stale `os` patch would be both likelier and harder to spot.

**Extended by the PR-16 round-3 review:** the same asymmetry exists one level
down, for module-level *data* rather than modules. `FILE_BYTE_UNITS` is
re-exported by `pdsfile.pdsfile` but read by `formatted_file_size` through
`_path_utils`'s globals, so mutating the list in place still works while
*rebinding* `pdsfile.pdsfile.FILE_BYTE_UNITS` is now silently inert. Measured:
no consumer anywhere does either, so nothing is broken today. PR-17 moves
`PATH_EXISTS_CACHE_SIZE` and hits the same shape, so the sweep step should
cover rebinding of re-exported data, not only of modules.
**Owner:** PR-17 onward (a step in each extraction PR's sweep).

### 6609. Documenting a module does not cost a fixed amount per function, and the spread is wide enough…

**Documenting a module does not cost a fixed amount per function, and the spread is
wide enough to matter to a projection.** Measured with an AST walk over the modules
already documented, each at the commit where its own PR left it so that this PR's
corrections are not folded into the figure they are compared against, a function
docstring runs **15.2** lines across PR-29's five public modules, **24.5** across
PR-29a's nine private ones and **18.6** across `_properties.py`'s 68 members.
Deviation (3)'s "roughly fourteen lines per function" is below all three. The figure
that made `_properties.py` a decision was not the length but the count: 68 members at
18.6 lines is 1,266 lines of function docstring, which is what took the file from
1,689 total lines to 2,817.

The method is worth keeping because it worked: ten representative members were
documented first, fitted to their code lines, and projected the finished file at about
2,720 against a ceiling of 2,000. Written out in full and then reviewed it landed at
**2,817**. The 97-line gap is the five review rounds' corrections, which a sample
cannot see because it is projected before it is read, so **a sample prices the
decision to within a few percent and should be read as a floor.** PR-30 has the rule
modules coming; the rule now carries the three per-module figures so the next
projection starts from a range rather than from an average.
**Owner: PR-30, as the next module-length question.**

### 6610. Entry 239's freeze rule was followed for the second reads and broken for the first

**observation 6605's freeze rule was followed for the second reads and broken for the
first.** PR-30a launched rounds 1 and 2 against `2fd40c4` and then kept committing
to `src/` while they ran; the tree reached `bd5b192`, eight commits on, before round
1 finished. Round 1 noticed, read the frozen text through `git show`, re-checked its
findings against the moved tree, and reported the drift in its own record, so the
experiment survived -- but only because the reviewer caught it, and two of its
fourteen findings had already been fixed by the executor independently, which makes
the yield harder to attribute. Rounds 3 and 4 were launched against a frozen
`e8af080` with nothing committed to `src/` until they returned.
**Owner: a reviewer-brief and executor instruction -- the freeze is the executor's
to hold, and "I found it myself first" is not a reason to break it, because it
destroys the measurement the round exists to produce.**

### 6611. Freeze is defeatable by editing the manifest/dumper/test

**Freeze is defeatable by editing the manifest/dumper/test.** Inherent to this
contract style; prohibited by plan §6.4 and documented in both docstrings and
the allowlist `_comment`. Process control, not a technical gap. Owner: process.

### 6612. No review round read this PR's own checker

**No review round read this PR's own checker.** Four rounds read 36 modules of prose
against the code; none was pointed at `critiques/pr-30/check_rule_tables.py`, and the
bypass in its `imported_names` (observation 3303's sibling, repaired in this PR) was found by
an outside reviewer instead. A gate built inside a PR is part of that PR's deliverable
and gets no independent read under the current round structure.
**Owner: a reviewer-brief instruction -- one round of any PR that ships a checker
should review the checker.**

### 6613. Only one option across the fifteen programs has a substantive default

**Only one option across the fifteen programs has a substantive default**, which is
what makes the third comparison in `critiques/pr-32/check_cli_coverage.py` narrow.
Of 108 optional actions, 107 default to `False`, `''`, `None` or `[]`; the one that
does not is `re_validate --minutes`, which defaults to 60. A `store_true` flag's
`False` is not a fact a chapter can get wrong, so the check has one subject. Recorded
so that "0 findings over ... 1 defaults" is not read as wider coverage than it is.
**Owner: nobody, unless a later option acquires a default.**

### 6614. The per-module cost of documenting a rule module, measured, for entry 223's method

**The per-module cost of documenting a rule module, measured, for observation 6609's
method.** observation 6609 asks that the cost be sampled per module rather than taken from
an average, and read as a floor. Measured over all 36 at this PR's head:
**2,005 lines added against 8 removed, for 74 docstrings**, which is 27.1 lines each
against PR-29's 15.2 for a public-module function, PR-29a's 24.5 for a private one
and PR-29b's 18.6 for a lazy property. **The review is 15% of that total**: the first
reads' corrections added 219 lines, the second reads' a further 79 and CodeRabbit's 13, because an
accurate sentence about a rule table is longer than an approximate one and a sentence
that has to say a table is unreachable is longer again.

The number that would actually price the next one is narrower than any of those. The
36 **module** docstrings occupy 1,499 lines, a mean of 41.6, and they run from 13
lines (`RES_xxxx.py`, which defines no rule tables) to 115 (`VG_28xx.py`, which
defines 32). **The correlation between a module's rule-table count and its docstring
length is 0.87**, and the module's own line count predicts nothing:
`uranus_occs_earthbased_primary_filespec.py` is 774 lines and needs 13.
So the unit to sample for a rule-shaped module is the table, not the module and not
the function. A least-squares fit over the 36 gives **2.55 lines of module docstring
per top-level table plus a fixed 11.3**, over 429 tables in all.
Whether that transfers to `holdings_maintenance/`, where the unit is a
function again, is exactly what PR-30b should sample rather than assume.
**Owner: PR-30a, PR-30b and PR-30c, which should sample rather than average.**

### 6615. The rate deferred entry 98 recorded is not a property of the migration

**The rate observation 6107 recorded is not a property of the migration.**
observation 6107 projected family-specific shared code at 18.5% of a pair's combined
line count and used that to decide where `_common.py` would split. Measured
across the three Phase-6 migrations: 18.5% (archives, the entry's own basis),
12.0% (checksums + infoshelf, PR-26), 33.4% (indexshelf + linkshelf, PR-27).
It ran high for one PR and short for the next — observation 6107 projected 748 lines
for PR-27's two pairs and the measurement is 1,349, so the projection missed by
601 lines, 45% of what was there.

The reason is visible in the two pairs PR-27 migrated: the index shelf pair was
almost identical between flavors (57.1% of its 1,086 lines became shared code),
and the link shelf pair was not (24.7% of 2,954), because `generate_links` is
the one function where a PDS3 label and a PDS4 label genuinely say different
things. How much of a pair can be shared depends on how alike its two flavors
happen to be, which is not something a rate carries. observation 6107's *rule* — split
when a measurement crosses 1,000 lines — held up both times; its *projection*
did not, either time.
**Owner: recorded, not open. Whichever PR migrates a pair next measures its
own rather than projecting.**

### 6616. Whether prose may follow a mechanical fix is not written down anywhere

**Whether prose may follow a mechanical fix is not written down anywhere.**
Round 1's m8 had PR-23 change three `IOError` references to `OSError` in
`_path_utils.py` comments and docstrings — accurate (`IOError` **is**
`OSError`), manifest-invisible (`scripts/dump_public_api.py` records names and
kinds, never docstrings), and a strictly better match for the code after
`UP024`. But no ruff rule required them, and PR-23's stated scope is
"`ruff check` only", so an equally reasonable executor would have left them and
an equally reasonable reviewer could call them scope creep. PR-24 faces the
same question at much larger scale (the rule modules' docstrings). One line in
its sub-plan would settle it.
**Owner: PR-24.**
