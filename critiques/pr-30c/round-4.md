# PR-30c, round 4: second independent read of the prose

Tree: `/seti/all_repos/rms-pdsfile-pr30c/work` at `d7bcff3`. Base: `.../base` at `0f5d9ae`.
Interpreter `/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), `PYTHONPATH=<tree>/src`.
Holdings reached read-only through a symlink sandbox under the scratchpad, so that the log
files a run writes land outside `/seti/opus/pdsdata`.

Slice: `pds3/pdsdependency.py`, `pds3/crlf.py`, `pds3/shelf_consistency_check.py`,
`pds3/__init__.py`, `pds4/__init__.py`.

Premise check first. Stripping every module, class and function docstring and comparing the
resulting ASTs, `crlf.py`, `shelf_consistency_check.py` and `pdsdependency.py` are
byte-identical to base; the two `__init__.py` files were empty in base. **No executable
statement changed.**

---

## Framing: three of the thirteen claims are not in the tree

The brief lists thirteen claims "commit `d7bcff3` wrote". `git show d7bcff3` touches
`pdsdependency.py` in exactly three hunks: `get_modtime`'s backup paragraph, `test1`'s
"four" -> "five", and `main()`'s two paragraphs. But the commit *message* announces six
pdsdependency corrections. Three of them -- brief claims 1, 2 and 3 -- were never written
into the prose:

```
$ grep -n "three of the eight\|every distinct suite\|one file per volume\|drops a name" \
      src/pdsfile/holdings_maintenance/pds3/pdsdependency.py
(no matches)
```

`git blame` puts every line of the module docstring and of the `glob_pattern` parameter at
`3bddc99`, the original draft. So the three sentences the correction commit claims to have
fixed are still there, uncorrected, and each of them is still wrong. They are findings 1, 2
and 3 below. This is the correction-pass failure mode in its purest form: the finding was
understood, written down in the commit message, and applied to none of the places it
belonged.

---

## Findings

### 1. `pdsdependency` module docstring: "It creates nothing and repairs nothing."

*(line 12; original prose, `3bddc99`; the commit message of `d7bcff3` claims this was
corrected)*

> "-- and reports whatever is missing or stale. **It creates nothing and repairs nothing.**
> What it produces instead is a list of the commands an operator would have to type"

**What I did.** Built a sandbox holdings root of symlinks and ran the tool on `VG_2810`,
once with no log root and once with `--log`.

**What the code does.** Every run creates files. With no log root configured:

```
sandbox/pdsdata/logs/pdsdependency/VG_28xx/VG_2810_dependency_2026-08-08T21-08-59.log
sandbox/pdsdata/logs/pdsdependency/VG_28xx/ERRORS.log
```

With `--log <root>`, five files across two trees: a per-volume log and an `ERRORS.log` in
each of the two places, plus an `ERRORS.log` at the log root's `pdsdependency/`. The tool
also creates the directories to hold them.

The correction the commit message describes ("what it writes is its log, one file per
volume and a second copy under the log root when one is configured") would itself have been
incomplete: the `ERRORS.log` files are neither one-per-volume nor a copy of the volume log.

**Rating: disproved.**

### 2. `PdsDependency.__init__`, `glob_pattern`: a one-`$` pattern "covers a whole volume set"

*(lines 195-197; original prose, `3bddc99`; the commit message of `d7bcff3` claims this was
corrected)*

> "**A pattern with one "$" is deliberate rather than incomplete: it is how a rule is
> written to cover a whole volume set at once.**"

**What I did.** Imported the module, walked `DEPENDENCY_SUITES`, counted `$` in every
distinct rule's `glob_pattern`, then built the glob the way `test1` builds it for
`volumes/VG_28xx/VG_2810` and ran `glob.glob` on the result.

**What the code does.** Of 117 rules, 109 have two `$` and 8 have one. Five of the eight are
the `checksums-archives-<thing>/$*<thing>_md5.txt` rules, which do cover a volume set. The
other three spell a *volume* into the pattern:

```
vg_28xx  volumes/$/VG_280[12]/*DATA/*/[PU][SUN][0-9]*.LBL
vg_28xx  volumes/$/VG_2803/*RINGS/*DATA/*/R[SUN][0-9]*.LBL
vg_28xx  volumes/$/VG_2810/DATA/IS[0-9]_P[0-9][0-9][0-9][0-9]*.LBL
```

Because `test1` substitutes the volume name only `if '$' in pattern` after the volset
substitution, a one-`$` pattern never sees the volume the command line named. Running on
`VG_2810` therefore globs, and tests, 241 files inside `VG_2802` and 698 inside `VG_2803` --
volumes the operator did not name. That is not "covering a volume set"; it is testing a
different volume.

**Rating: misleading.**

### 3. `pdsdependency` module docstring: "a volume picks up as many of them as its path matches"

*(lines 38-39; original prose, `3bddc99`; the commit message of `d7bcff3` claims this was
corrected)*

> "``TESTS`` has 49 rows and names 41 suites between them, and **a volume picks up as many of
> them as its path matches.**"

**What I did.** Counted rows (49) and distinct suite names (41) -- both correct. Then, for
every volume directory in the holdings tree, compared the concatenation of the replacement
lists of all matching rows against `TESTS.all(path)`.

**What the code does.** `TranslatorByRegex.all()` appends `if item not in results`, so a
name collected twice is kept once. Four volumes exercise it:

```
volumes/GO_0xxx/GO_0020  ['body']   volumes/GO_0xxx/GO_0022  ['body']
volumes/GO_0xxx/GO_0021  ['body']   volumes/GO_0xxx/GO_0023  ['body']
```

`.*/GO_0xxx/GO_00[2-689].*` and `.*/GO_0xxx/GO_00[12][0-9].*` both match `GO_0020` and both
name `body`; the volume picks it up once, not twice.

**Rating: misleading.**

### 4. `main`: "the two lines naming that file ... do not [reach it]"

*(lines 1296-1297; **correction**, `d7bcff3`)*

> "A volume's findings therefore reach its own file, and **the two lines naming that file**,
> logged from here before the suites start, do not."

**What I did.** Ran with `--log` and without `--quiet`, then compared the paths the two
`Log file` lines print against the files on disk.

**What the code does.** Announced:

```
| INFO | Log file: .../logroot2/pdsdependency/volumes/VG_28xx/VG_2810_dependency_....log
| INFO | Log file: .../sandbox/pdsdata/logs/pdsdependency/volumes/VG_28xx/VG_2810_....log
```

Written:

```
.../logroot2/pdsdependency/VG_28xx/VG_2810_dependency_....log
.../sandbox/pdsdata/logs/pdsdependency/VG_28xx/VG_2810_dependency_....log
```

The lines name paths with a `volumes/` component that the written files do not have, and
that do not exist. The cause is in `main()`: the handler loop rebinds the loop variable,

```python
for logfile in logfiles:
    logfile = logfile.replace('/volumes/', '/')
    local_handlers.append(pdslogger.file_handler(logfile))
```

and the reporting loop then re-iterates the *original* `logfiles`:

```python
for logfile in logfiles:
    logger.info('Log file', logfile)
```

So the lines do not name that file; they name a path nothing writes. Three further errors in
the same sentence: there are two lines only when a log root is configured (with none there
is one -- `grep -c "Log file"` on the run-1 log and stdout confirms a single line), and when
there are two they name two *different* places, so no pair of them ever names one file.

The part of the sentence the correction was actually reaching for is right: `grep -c "Log
file"` inside every per-volume log is 0, because the handlers go on per suite, in
`test_suite`'s `logger.open(..., handler=handlers)`, and the two lines are logged before the
first suite opens.

**Rating: misleading, and a code defect (the announced log path is not the written one).**

### 5. `shelf_consistency_check` module: "every directory under it is reported instead"

*(lines 27-29; **correction**, `d7bcff3`)*

> "**Name a root that happens to have ``shelves`` in its own path, though, and every
> directory under it is reported instead.**"

**What I did.** Built a root named `Bshelvesroot` holding `x/y`, `sub/shelves` and
`shelves/info`, and ran the tool on it.

**What the code does.** Four of the seven directories were reported:

```
*** Not a valid shelves directory: .../Bshelvesroot
*** Not a valid shelves directory: .../Bshelvesroot/sub
*** Not a valid shelves directory: .../Bshelvesroot/x
*** Not a valid shelves directory: .../Bshelvesroot/x/y
Tests performed: 4
Errors found: 4
```

Three were not. `Bshelvesroot/shelves` and `Bshelvesroot/sub/shelves` are skipped outright by
`if root.endswith('shelves'): continue` -- a guard the docstring never mentions -- and
`Bshelvesroot/shelves/info` partitions to a recognized kind, so it is examined rather than
reported. "Every directory under it" is false.

**Rating: disproved.**

### 6. `shelf_consistency_check` module: what the "things examined" count counts

*(lines 43-44; **correction**, `d7bcff3`)*

> "The run prints how many things it examined -- **files, plus one for each directory of an
> unrecognized kind** -- and how many errors it found"

**What I did.** Built `G/shelves/bogus/a/b` (three directories of an unrecognized kind) with
one file, `G/shelves/bogus/junk.txt`, plus an empty `G/shelves/index`.

**What the code does.**

```
*** Not a valid shelves directory: .../G/shelves/bogus
*** Not a valid shelves directory: .../G/shelves/bogus/a
*** Not a valid shelves directory: .../G/shelves/bogus/a/b
Tests performed: 3
```

The sentence's formula predicts 1 + 3 = 4. It reports 3, because a directory of an
unrecognized kind `continue`s before the file loop, so the file inside it is never counted.
Only files inside a directory of a *recognized* kind count.

This is the "three of the four places" error exactly: the same correction commit wrote the
qualified version into `main()`'s docstring -- "files, **one per file inside a directory of a
recognized kind**, plus one for each directory of an unrecognized kind" -- and left the
module docstring's unqualified restatement of the same fact ten lines above it.

**Rating: disproved.**

### 7. `shelf_consistency_check` module: "everything after the last underscore goes too"

*(lines 34-38; **correction**, `d7bcff3`)*

> "For ``info`` and ``links``, **everything after the last underscore goes too** -- which is
> the ``_info`` or ``_links`` on a shelf named the way these tools name them, and **is
> whatever else follows an underscore on one that is not**"

**What I did.** Built `D/shelves/info/abc.pickle` under a scratch path containing no
underscore anywhere, with `D/holdings/abc` present, and ran with `--verbose`.

**What the code does.**

```
*** Extraneous shelf: .../scc2/D/shelves/info/abc.pickle
Errors found: 1
```

`str.rpartition('_')` on a string with no separator returns `('', '', s)`, so `[0]` is the
empty string. The counterpart becomes `''`, `os.path.exists('')` is False, and the shelf is
reported extraneous however complete the holdings tree is. What goes is not "whatever else
follows an underscore" -- there is no underscore -- it is the whole path. The correction
enumerated two cases and the boundary between them is a third the reader is left to guess
wrong about. (The other two halves of the same sentence, "wherever it occurs" and "as a file
or a directory alike", I confirmed; see below.)

**Rating: misleading.**

### 8. `test1`: "Each required file is logged as one of five things"

*(lines 344-345; the clause "as one of five things:" is the **correction**, `d7bcff3`; the
sentence stem is `3bddc99`)*

> "**Each required file is logged as one of five things:**
>   * skipped, if the file that implies it matches one of the rule's exceptions;
>   * an invalid test, if the rule's regular expression does not match the file the rule's
>     own glob found ..."

**What I did.** Constructed a `PdsDependency` whose glob finds `volumes/.../DATA/*.LBL` and
whose regex only matches `metadata/...`, ran `test1` against `VG_2810` with a capturing
handler, and read what was logged.

**What the code does.** Five is the right count of verdicts. But the first two are not about
a required file at all:

* `logger.info('Test skipped', abspath)` fires before any substitution runs; `abspath` is
  the *source* file, and no required path is ever computed for it.
* when `subn` returns `count == 0` it returns the subject unchanged, so
  `absreq = pdsdir.root_ + requirement` is the source path re-rooted -- which, since
  `lskip_ == len(pdsdir.root_)`, is the source path itself. Measured:

  ```
  ERROR | Invalid test: volumes/VG_28xx/VG_2810/DATA/IS1_P0001_V01_KM002.LBL
  ```

  That is the file the glob found, not a file that must exist.

The docstring two paragraphs later gets it right -- "a **skipped file** is logged once for
each substitution" -- so the umbrella sentence is the one out of step with both the code and
its own following text. The correction rewrote that sentence's predicate and did not notice.

**Rating: misleading.**

### 9. `test_suite()` and `test()`: `Raises:` blocks omit what they re-raise

*(lines 542-548 and 1265-1267; original prose, `3bddc99`)*

> `test_suite` -- "Raises: KeyError ... ValueError ..."
> `test` -- "Raises: ValueError: from ``test_suite()`` ..."

**What I did.** Replaced `get_modtime` with a function that raises `OSError` and called
`PdsDependency.test_suite('general', vol)` with a capturing logger.

**What the code does.**

```
escaped: OSError boom
logger.exception calls: 3
```

`test1`'s own `Raises:` block documents this `OSError`, and both `test1` and `test_suite`
log-and-re-raise, so the exception leaves `test_suite` and leaves `test()`. Neither block
mentions it. `main()` covers it only through a blanket "whatever ``test()`` raises escapes",
which is the one place the chain is documented.

Incidentally the three-times claim in `test1` -- "twice here, and again by the suite above,
so one failure appears three times in the log" -- measures exactly right.

**Rating: misleading (incomplete `Raises:`).**

### 10. `get_modtime`: "whatever the dependencies turn out to be"

*(lines 276-278; original prose, `3bddc99`)*

> "A dot-underscore file is logged at error level, so **one of them anywhere below a
> directory gives the whole run a nonzero exit status**, whatever the dependencies turn out
> to be."

**What I did.** Confirmed the levels first: `PdsLogger.ds_store` emits at 10 and
`dot_underscore` at 40, and `close()` counts the latter as an error -- so the mechanism is
real. Then counted `get_modtime` calls over a whole run of `VG_2810`, and checked which
directories ended up in `MODTIME_DICT`.

**What the code does.** `get_modtime` is only reached from

```python
if self.newer and check_newer:
    source_modtime = PdsDependency.get_modtime(abspath, logger)
```

which sits *after* `if not os.path.exists(absreq): ... continue`. So a directory is walked,
and the dot-underscore files below it logged, only when the rule asks for a date check, the
run has date checks on, and the required file already exists. Measured:

```
get_modtime calls with check_newer=False: 0

volumes/VG_28xx/VG_2810             exists=True  timed=True
previews/VG_28xx/VG_2810            exists=True  timed=False
metadata/VG_28xx/VG_2810            exists=True  timed=True
```

A `._` file under `previews/VG_28xx/VG_2810` would not have been seen by that run, and under
`re_validate --timeless` -- which this module's own docstring describes two paragraphs
earlier -- nothing anywhere would be seen. "Whatever the dependencies turn out to be" is the
clause that overreaches: whether the walk happens at all is decided by the dependencies.

**Rating: misleading.**

### 11. `main`: `Raises:` omits the `OSError` from building the log handlers

*(lines 1306-1318; original prose, `3bddc99`)*

> "Raises: SystemExit ... ValueError ... **Exception: whatever ``test()`` raises escapes**"

**What I did.** Ran with `--log /proc/nope`.

**What the code does.**

```
File ".../pds3/pdsdependency.py", line 1380, in main
FileNotFoundError: [Errno 2] No such file or directory: '/proc/nope'
```

Line 1380 is `error_handler = pdslogger.error_handler(path)`, before `logger.open()` and
outside every `try`. `pdslogger.file_handler()` inside the per-volume loop can raise the same
way. An unusable `--log` root therefore ends `main()` in an uncaught `OSError` with no
message and no log, and the `Raises:` block attributes every escaping exception to `test()`.

**Rating: misleading (incomplete `Raises:`).**

### 12. `pds3/__init__`: "Nothing in Python names any of the twelve."

*(lines 30-31; **correction**, `d7bcff3`)*

**What I did.** Grepped every `.py` in the repository for each of the twelve script
basenames.

**What the code does.** Eleven have zero hits. `update_holdings_for_new_metadata.sh` has
one -- line 29 of `pds3/__init__.py`, the sentence immediately before this one. The only
Python that names any of the twelve is the sentence denying that any does. The predecessor
this replaced said "nothing in Python **reaches** them", which is true and which the
correction discarded in favour of a word its own paragraph falsifies. (The rest of the
sentence I confirmed: `tests/holdings_maintenance/__init__.py` refers to them only as
`pds3/*.sh`, which names none of them individually.)

**Rating: misleading (minor).**

### 13. `get_modtime`: "every sibling tool carries the same block one level out"

*(lines 282-283; **correction**, `d7bcff3`)*

> "the block that would skip a backup or " copy" file sits inside the dot-underscore branch
> and after its ``continue``, so it cannot run; **every sibling tool carries the same block
> one level out, where it does.**"

**What I did.** Read the backup block in every module that has one, and counted
`ds_store` / `dot_underscore` occurrences per module.

**What the code does.** Four of the five tool families do carry it exactly one level out of a
dot-underscore branch and reachable: `pdschecksums`:170, `pdsinfoshelf`:244,
`pdslinkshelf`:243, `_archives_common`:178 (and the four pds4 twins). The fifth does not:

```
_indexshelf_common.py: ds_store=0 dot_underscore=0 backup=1
```

`_indexshelf_common` has no `.DS_Store` branch and no dot-underscore branch at all. Its
backup test lives in `run_index_main()`, iterating index tables rather than a directory
listing, and matching `BACKUP_FILENAME` against `pdsf.abspath` rather than a basename. It is
reachable, but it is not "the same block one level out" -- there is no branch there for it to
be outside of. And the three standalone siblings in this package (`re_validate`, `crlf`,
`shelf_consistency_check`) carry no such block at all, so "every sibling tool" is only true
under a reading of "sibling" the paragraph does not give.

**Rating: misleading.**

---

## Claims I could not verify

* **`re_validate` "in batch mode, on whichever volumes have gone longest without one"**
  (`pds3/__init__`). I read the batch-mode machinery in `re_validate.py` -- it reads dated
  log filenames back out of a log root and orders by them -- but I did not run a batch job.
  Doing so needs a log root populated with historical per-volume logs, which I would have had
  to fabricate; a fabricated ordering would not have tested the claim.
* **"each pair keeps the same five tasks and the same command line"** (`pds4/__init__`). I
  measured the tasks (all ten specs expose exactly `initialize`, `reinitialize`, `repair`,
  `update`, `validate`) and the `unit` field, which is what finding-free claim 13 rests on.
  I did not diff each pair's *full* parser, so a spec-added argument on one side only would
  have escaped me.
* **Intent behind the `/volumes/` replacement in `main()`** (finding 4). I can show the
  announced path is not the written path; I cannot tell whether the intended fix is to
  announce the replaced path or to stop replacing. The docstring asserts a relationship that
  does not hold either way, which is what I rate.
* **Whether any real holdings tree has ever exercised `shelf_consistency_check`'s
  substitution.** `find` over both `PDS3_HOLDINGS_DIR` and `PDS4_HOLDINGS_DIR` for
  `-path '*shelves*'` returns nothing, so every claim about the substitution had to be tested
  on trees I built. The docstring says as much, and I confirmed the 0/0 outcome on the real
  pds4 tree, but no claim about the matching layout is tested against production data.

---

## Claims I checked and confirmed

`pdsdependency`

* `TESTS` has 49 rows and names 41 distinct suites; every name it produces is registered, and
  every registered suite is named -- so `test_suite`'s "Every name ``TESTS`` produces is
  registered" holds.
* "That is the majority of them" for `newer=True`: 73 of 117 rules.
* Nothing outside the module constructs a `PdsDependency`; nothing calls `purge_cache()`;
  `COMMANDS_TO_TYPE` is never emptied and appends only what it does not already hold.
* `re_validate` is the only importer, and `pdsdependency.test()` is the last of its five
  per-volume validations.
* `--timeless` reaches `check_newer` (measured: 0 `get_modtime` calls with `check_newer=False`).
* `get_modtime`: a file returns its own mtime and is not cached; a directory's is the max over
  the subtree and is cached; an empty directory and one holding only `.DS_Store` and `._`
  files both return `-1e+99` and are cached; a nonexistent path and a broken symlink both
  raise `FileNotFoundError` from `listdir`. A directory whose only entry is a dated backup
  file is dated by it -- the misplaced block really is dead.
* `main()`'s two rejections for a checksum or archive path cannot fire. `category_` is
  `checksums_ + archives_ + bundletype_`, so a path with either prefix can never have
  `category_ == 'volumes/'`; measured on real directories,
  `checksums-volumes/COCIRS_0xxx` has `is_volset_dir=True` and reaches the category test,
  which refuses it. (For a *nonexistent* checksums path the `is_volume_dir`/`is_volset_dir`
  test refuses it first, because `is_bundleset_dir` ends in `self.isdir` -- so "the category
  test above" is the right attribution only for paths that exist. The conclusion is
  unaffected.)
* The rejection order the docstring gives -- volume/volset, category, existence, volume ID --
  matches the code, and each of those four does fire; measured all four.
* Exit status 1 when anything was logged as an error; `PdsLogger.close()` counts a
  `dot_underscore` at level 40 as an error and `ds_store` at level 10 as not.
* An exception inside a rule is logged three times: twice in `test1`, once in `test_suite`.
* `--log` resolution is character-for-character the same logic as `_common.resolve_log_root()`,
  against this module's own `LOGROOT_ENV`, whose value matches `_common`'s.
* `cumname`: `'999'` turns `COISS_1010` into `COISS_1999`, `'99'` turns `RPX_0001` into
  `RPX_0099`, `'9_9999'` consumes six trailing characters, and the New Horizons branch reads
  `volname[4:8]` -- which is, as written, the fifth through eighth characters --
  so `NHJULO_1001` becomes `NHxxLO_1999`. The branch really is chosen on `nines[0]` alone.
* `messages` markers: group references substituted first, `[x]` truncates in every case
  except a stale file whose message carries `[C]`, `[c]`/`[C]` map to
  initialize/initialize when missing and repair/reinitialize when stale, `[d]` becomes
  `pdsdir.root_`.
* `exceptions` are `fullmatch`ed against the absolute path, and every one of the fourteen
  patterns in the module begins with `.*`.
* `test1` runs substitutions outermost and files innermost; a glob that matches nothing
  returns `(0, 0, 0, 0)` having logged nothing; missing / out-of-date / confirmed are each
  deduplicated per required path across all substitutions, and skipped / invalid are not.
* `main()`'s log handlers really are handed to the suites and really do keep the two
  `Log file` lines out of the per-volume log (`grep -c "Log file"` on it is 0).

`crlf`

* Byte 127 is not counted: a file of 50 `\x7f` and 50 `A` classifies `OK`, not `BINARY`. 157
  of 256 byte values count as non-ASCII, which is 29 + 128 exactly.
* The threshold is strict: 1 non-ASCII character in 100 gives `INVALID`, 2 in 100 gives
  `BINARY`.
* `latin8` decodes all 256 byte values without raising, and `encode` inverts it exactly, so
  the `Raises:` block needs no `UnicodeDecodeError`/`UnicodeEncodeError` and a repair really
  does move no other byte (verified on a file starting `\xa1`). 31 high bytes decode above
  U+00FF and so are counted by being absent from the table rather than mapped to `'x'`; the
  count is the same either way.
* A zero-byte file raises `ZeroDivisionError`; both `ValueError`s fire before the file is
  opened.
* A CR-separated file is one record, reports `INVALID`, and repairs to `a\rb\rc\r\n`.
* `main()`'s summary: `2/2 files invalid`; `1/2 files invalid`; `2 files tested`; nothing for
  one file or none; **nothing at all for a run that repairs two files**; `1/2 files repaired`
  for a run that repairs one. Flags intermixed among paths are accepted. Return is always 0.

`shelf_consistency_check`

* `myshelves-backup` matches the substring test, and everything under it is reported.
* A `shelves/info` subtree of four directories holding no files reports
  `Tests performed: 0`.
* `shelves/<kind>` is replaced at *every* occurrence -- a shelf at
  `E/shelves/info/shelves/info/COISS_0001_info.pickle` maps to `E/holdings/holdings/COISS_0001`.
* The counterpart need only exist: a plain file named `COISS_0001` satisfies an info shelf.
* One misnamed kind costs one error per directory below it (3 directories -> 3 errors), the
  walk is not pruned, and the kind is read from the component below the first `shelves/`.
* A nonexistent root, and no root at all, both print `Tests performed: 0` / `Errors found: 0`
  and exit 0. A real `pds4-holdings` root does the same; `find -path '*shelves*'` returns
  nothing for either holdings tree.
* `SystemExit` is the only thing `main()` can raise.

`pds3/__init__` and `pds4/__init__`

* Ten Python modules beside `__init__`; the five family modules all declare a `ToolSpec` and
  are all in `[project.scripts]`; `pdsdependency` is a console script and `re_validate`,
  `crlf` and `shelf_consistency_check` are not, so "all four are run with ``python -m``
  except ``pdsdependency``" holds.
* `crlf` and `shelf_consistency_check` import nothing from the package; `pdsdependency` and
  `re_validate` both build log paths through `_common.log_paths_for()`.
* `pdslinkshelf` imports `REPAIRS` from `linkshelf_repairs`; `pds4linkshelf` explains why it
  has no counterpart.
* Twelve `.sh` files; `update_holdings_for_new_metadata.sh` runs exactly five distinct tools
  and does so as `python pdsarchives.py` etc., by source file name.
* All ten specs expose the same five tasks. `unit` is `volume`/`bundle` for the archive,
  checksum, info shelf and link shelf pairs and `table` on both sides of the index shelf pair
  -- claim 13 confirmed exactly as written.

---

## Count

**13 findings. 7 of them are in sentences commit `d7bcff3` wrote or rewrote** -- findings 4,
5, 6, 7, 8, 12 and 13. (Finding 8 is a split case: the correction rewrote the predicate of a
sentence whose defective subject it inherited; counted here as a correction sentence because
the correction touched that line and could have caught it.)

Of the remaining six, **three -- findings 1, 2 and 3 -- are defects `d7bcff3`'s commit message
claims to have corrected and did not.** Counting those as the correction pass's product too,
the correction commit is answerable for 10 of 13.
