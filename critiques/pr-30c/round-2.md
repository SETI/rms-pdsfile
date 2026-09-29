# PR-30c round 2 — adversarial read of the docstrings

Slice: `src/pdsfile/holdings_maintenance/pds3/pdsdependency.py`,
`pds3/crlf.py`, `pds3/shelf_consistency_check.py`, `pds3/__init__.py`,
`pds4/__init__.py`. Work tree at `3bddc99`; base at `0f5d9ae`.

Everything below was run with
`PYTHONPATH=/seti/all_repos/rms-pdsfile-pr30c/work/src`,
`/seti/all_repos/rms-pdsfile/venv/bin/python`,
`PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`,
`PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings`. Scratch trees were built
under the session scratchpad; nothing under `src/`, `tests/`, `scripts/` or
`pyproject.toml` was touched.

Tally: **9 disproved, 5 misleading, 1 code defect.**

---

## Disproved

### D1. `pdsdependency.PdsDependency.__init__`, `glob_pattern` — three patterns do name a volume, and a one-`$` pattern is not always volume-set-wide

> Its first "$" is replaced by the volume set directory name, and a second "$" by
> the volume name, **so a pattern names neither. A pattern with one "$" is
> deliberate rather than incomplete: it is how a rule is written to cover a whole
> volume set at once.**

Imported the module and read every registered rule's `glob_pattern`:

```python
uniq = {id(r): r for v in P.PdsDependency.DEPENDENCY_SUITES.values() for r in v}.values()
collections.Counter(r.glob_pattern.count('$') for r in uniq)   # {2: 109, 1: 8}
sorted({r.glob_pattern for r in uniq if r.glob_pattern.count('$') == 1})
```

The eight one-`$` patterns are:

```
checksums-archives-calibrated/$*_calibrated_md5.txt
checksums-archives-diagrams/$*_diagrams_md5.txt
checksums-archives-metadata/$*_metadata_md5.txt
checksums-archives-previews/$*_previews_md5.txt
checksums-archives-volumes/$*_md5.txt
volumes/$/VG_280[12]/*DATA/*/[PU][SUN][0-9]*.LBL
volumes/$/VG_2803/*RINGS/*DATA/*/R[SUN][0-9]*.LBL
volumes/$/VG_2810/DATA/IS[0-9]_P[0-9][0-9][0-9][0-9]*.LBL
```

Only the first five match the stated explanation. The last three (the three
`vg_28xx` rules, `pdsdependency.py:1206`, `:1218`, `:1230`) have one `$` because
they **hard-code the volume name in the second component**. So:

* "a pattern names neither" is false — three patterns name the volume outright;
* "it is how a rule is written to cover a whole volume set at once" is false for
  3 of the 8, which cover one named volume (two, for `VG_280[12]`).

The consequence a reader would not predict from the docstring: `test1` fills the
first `$` with `pdsdir.volset_[:-1]` and never looks at `$` again, so running the
`vg_28xx` suite against `VG_2801` globs `volumes/VG_28xx/VG_2803/...` and
`volumes/VG_28xx/VG_2810/...` — the rules test a different volume from the one
named on the command line.

### D2. `pdsdependency.PdsDependency.test1` — "four things", five bullets

> Each required file is logged as **one of four things**:
>
>   * skipped, … * an invalid test, … * missing, … * out of date, … * confirmed
>   otherwise.

`sed -n '327,360p' src/pdsfile/holdings_maintenance/pds3/pdsdependency.py`
shows five bullets, and the two sentences that follow confirm five: "The last
three are reported once per required path… The first two are not deduplicated".
Three plus two is five. The count word is wrong.

### D3. `crlf` module docstring and `test_crlf`, `threshold` — DEL is outside printable ASCII and is *not* counted

> …a file is treated as binary when more than one percent of its characters fall
> **outside printable ASCII**, counting carriage return, line feed and tab as
> ASCII.

> A character counts as non-ASCII when it is **outside printable ASCII** and is
> not a carriage return, a line feed or a tab.

`NON_ASCIIS` (crlf.py:41-50) maps `range(32, 128)` to `None`, and 128 is
exclusive of nothing — 0x7F (DEL) is inside that range, so it is deleted by
`translate()` and counted as ASCII. Experiment:

```python
mk('del.txt',  b'\x7f'*50 + b'A'*50 + b'\r\n')   # crlf.test_crlf -> 'OK'
mk('ctrl.txt', b'\x01'*50 + b'A'*50 + b'\r\n')   # crlf.test_crlf -> 'BINARY'
```

A file that is 50 % DEL bytes is classified as text and is a candidate for
rewriting; the identical file built from 0x01 is recognized as binary. DEL is
neither printable ASCII nor CR/LF/TAB, so both sentences are false of it. This is
the only byte value for which they are false.

### D4. `shelf_consistency_check` module docstring — `shelves` is matched as a substring, not as a path component

> A file is examined only if its directory path contains **the component**
> ``shelves``…

`shelf_consistency_check.py:123` is `if 'shelves' not in root: continue` — a
substring test on the whole path string. Two demonstrations, run through
`scc.main()`:

```
tree: <S>/A/myshelves-backup/sub/x.pickle
*** Not a valid shelves directory: <S>/A/myshelves-backup
*** Not a valid shelves directory: <S>/A/myshelves-backup/sub
Tests performed: 2 / Errors found: 2 / rc = 1

tree: <S>/shelves-copy/holdings/volumes/f.txt        (root argument contains "shelves")
*** Not a valid shelves directory: <S>/shelves-copy
*** Not a valid shelves directory: <S>/shelves-copy/holdings
*** Not a valid shelves directory: <S>/shelves-copy/holdings/volumes
Tests performed: 3 / Errors found: 3 / rc = 1
```

This also qualifies the docstring's headline claim that a run over this
repository's holdings layout "walks every directory, examines nothing, and
reports ``Tests performed: 0`` and ``Errors found: 0``". That holds only while no
path component *anywhere under the named root, including the root argument
itself*, contains the four-letter-plus string `shelves`. I did confirm the tree
itself is clean —
`find /seti/opus/pdsdata/holdings -name '*shelves*'` returns nothing (exit 0, no
output) — but a user who names `/backup/shelves-2024/holdings` gets one error per
directory in the tree, not a clean zero.

### D5. `shelf_consistency_check` module docstring — the counterpart need not be a directory

> For ``info`` and ``links``, the trailing ``_info`` or ``_links`` is dropped too
> and **what must exist is the directory that is left**.

Line 168 is `os.path.exists(holdings_path)`, not `os.path.isdir`. Built a tree
where the counterpart is a plain **file**:

```
<S>/F/shelves/info/VS/V_0001_info.pickle
<S>/F/holdings/VS/V_0001                  <- a zero-byte regular file
->  <S>/F/holdings/VS/V_0001
    Tests performed: 1 / Errors found: 0 / rc = 0
```

A file passes the check the docstring says is about a directory.

### D6. `shelf_consistency_check` module docstring — it is not `_info`/`_links` that is dropped

Same sentence. Line 167 is `holdings_path.rpartition('_')[0]`, which drops
everything after the **last** underscore, whatever that is. Two demonstrations:

```
<S>/G/shelves/info/VS/COISS_2001.pickle     (no _info suffix)
<S>/G/holdings/VS/COISS_2001                (exists)
->  *** Extraneous shelf: <S>/G/shelves/info/VS/COISS_2001.pickle
    Tests performed: 1 / Errors found: 1 / rc = 1
```

```
<S>/D/shelves/info/vol/abc.pickle           (no underscore anywhere)
->  *** Extraneous shelf: ...           (holdings_path is the empty string,
                                         which os.path.exists always rejects)
```

A correctly-placed shelf whose basename happens not to end in `_info`/`_links` is
mapped to the wrong holdings path and reported as extraneous; a basename with no
underscore at all maps to `''`.

### D7. `shelf_consistency_check.main` — directories are not counted

> Two summary lines are always printed… **the number of files and directories
> examined**, and the number of errors.

(and the module docstring's "The run prints how many files and directories it
examined".)

`tests` is incremented in exactly two places: once per file inside a valid-kind
directory (line 140) and once per *invalid*-kind directory (line 134).
Directories under a valid kind are never counted:

```
tree: <S>/I/shelves/info/A/B/C           (4 directories under shelves/, zero files)
->  Tests performed: 0 / Errors found: 0 / rc = 0
```

The count is "files examined, plus one per misnamed kind directory".

### D8. `pds4/__init__` — the indexshelf pair's `unit` does not differ

> Every one has a PDS3 twin in the sibling ``pds3`` package, and each pair keeps
> the same five tasks and the same command line. **What differs is the unit a
> target names -- a bundle rather than a volume**…

Compared the two `SPEC` dataclasses field by field for all five pairs:

```
pdsarchives   / pds4archives   : unit='volume' / 'bundle'   (10 fields differ)
pdschecksums  / pds4checksums  : unit='volume' / 'bundle'   ( 6)
pdsindexshelf / pds4indexshelf : unit='table'  / 'table'    ( 5)   <-- same
pdsinfoshelf  / pds4infoshelf  : unit='volume' / 'bundle'   ( 6)
pdslinkshelf  / pds4linkshelf  : unit='volume' / 'bundle'   ( 9)
```

For one of the five pairs the unit is `'table'` on both sides — nothing differs.
`pds4indexshelf`'s own module docstring says so ("Its target is a table rather
than a bundle, which is why ``unit`` is 'table'"), so the package docstring
contradicts a module it points the reader at.

The rest of that sentence is confirmed: all ten `TASKS` dicts have exactly
`initialize, reinitialize, repair, update, validate`, and each pair's `--help`
exposes an identical option set (checked by running `python -m … --help` for all
ten and diffing the extracted `--option` strings).

### D9. `pdsdependency.main` — the checksum/archive rejection is not its own failure

> …each failure ends the run with a message and status 1: a path that is neither
> a volume nor a volume set directory, one outside ``volumes/``, one that does
> not exist, **one under a checksum or archive category**, and a volume whose
> name is not a volume ID.

The two branches that exist for that case —

```python
if pdsf.checksums_:
    print('No pdsdependency for checksum files: ' + path); sys.exit(1)
if pdsf.archives_:
    print('No pdsdependency for archive files: ' + path);  sys.exit(1)
```

— are unreachable. `pdsfile.py:482` and `:2259` define
`category_ = checksums_ + archives_ + bundletype_`, so any path with a non-empty
`checksums_` or `archives_` necessarily fails the earlier
`if pdsdir.category_ != 'volumes/'` test in the first validation loop. Run:

```
$ pdsdependency /seti/opus/pdsdata/holdings/archives-volumes/COISS_2xxx
pdsdependency error: not a volume or volume set directory: archives-volumes/COISS_2xxx
SystemExit 1
```

The message the docstring implies exists never prints. Listing this as a
*distinct* failure alongside "one outside ``volumes/``" tells a reader there are
five rejection sites when there are three that can fire (plus the two dead ones).
See also C1 below — this is the docstring papering over dead code.

For the record, the other rejections in that list do behave as described:
`.../HSTNx_xxxx/HSTN0_9999` prints `No such file or directory:` and exits 1, and
`/etc` raises `ValueError: ('Not compatible with a logical path: ', '/etc')` from
`from_abspath()` — which the `Raises:` section correctly attributes.

---

## Code defect

### C1. `pdsdependency.get_modtime` — the sentence is true only because the code is broken, and does not say so

> **Nothing else is excluded: backup and " copy" files date a directory exactly
> as their originals do.**

This is accurate about behavior. It is accurate because lines 315-321 read:

```python
            if '/._' in absfile:        # log dot-underscore files; ignore dates
                logger.dot_underscore('._* file ignored', absfile)
                continue

                if BACKUP_FILENAME.match(file) or ' copy' in file:
                    logger.error('Backup file skipped', abspath)
                    continue
```

The backup test sits **after a `continue`, inside the dot-underscore branch** —
it can never execute. Its only consumer, the module-level `BACKUP_FILENAME`
regex at `pdsdependency.py:62`, therefore has no live use in the file
(`grep -rn BACKUP_FILENAME` confirms line 319 is its sole reference here). Every
sibling tool runs the identical block at the correct indentation:
`pdschecksums.py:170`, `pdsinfoshelf.py:244`, `pdslinkshelf.py:243`,
`_archives_common.py:178`, `pds4infoshelf.py:252`, `pds4checksums.py:174`,
`pds4linkshelf.py:226`.

So `pdsdependency` alone dates a directory by its backup files, and a stale
`*_2024-01-01T00-00-00.tab` or `foo copy.tab` will make every derived file of
that directory look out of date. The docstring records this as if it were the
design. A `Raises:`/behaviour note is not the right place to launder a bug; the
sentence should say the exclusion is dead code, or the code should be fixed.

---

## Misleading

### M1. `pdsdependency.main` — the volume's log file is attached per *suite*, not "for the duration of that volume"

> The run's own log is opened once and **each volume's log file is attached for
> the duration of that volume**, so a volume's findings are in its own file as
> well as in the run's.

`main()` never attaches the handlers. It passes `local_handlers` to
`test(pdsdir, logger=logger, handlers=local_handlers)`, which passes them to each
`PdsDependency.test_suite()`, which attaches them at
`logger.open(..., handler=handlers)`. `pdslogger.PdsLogger.close()` ends with
`self.remove_handler(*self._local_handlers[-1])`, so they are added and removed
once **per suite**, and are detached between suites.

The visible consequence: the two `logger.info('Log file', logfile)` calls
immediately above `test(...)` in `main()` run while the handlers are detached, so
the line naming a volume's log file is the one line that never appears in that
log file.

### M2. `pdsdependency` module docstring — "It creates nothing"

> It creates nothing and repairs nothing.

True of holdings products, but a run always writes log files.
`_common.log_paths_for()` returns one path when no log root is configured and two
when one is, and `main()` builds a `pdslogger.file_handler(logfile)` plus an
`error_handler(logdir)` for each, in the `logs/` tree parallel to `holdings/`.
`main()`'s own docstring describes those files at length, so the module summary
and the function docstring disagree about whether the tool writes anything.

### M3. `pdsdependency.test` — a suite named by two matching rows runs once

> Run every suite one volume's path selects, in the order the table lists them.

and, in the module docstring, "a volume picks up as many of them as its path
matches". `TranslatorByRegex.all()` (read from the installed `translator`
package) appends `if item not in results`, i.e. it deduplicates. Ran all 49
patterns against every one of the 493 volume directories in
`/seti/opus/pdsdata/holdings/volumes`: four volumes (`GO_0xxx/GO_0020` through
`GO_0023`) name the `body` suite twice, via
`.*/GO_0xxx/GO_00[2-689].*` and `.*/GO_0xxx/GO_00[12][0-9].*`. Those volumes run
`body` once, not twice. Small, but it is the one case where "as many of them as
its path matches" over-counts.

### M4. `pds3/__init__` — "They invoke the tools above as commands"

> The shell scripts here copy, sync and set up holdings trees. **They invoke the
> tools above as commands rather than importing them**, so nothing in Python
> reaches them.

There are 12 shell scripts in the package. Exactly **one**
(`update_holdings_for_new_metadata.sh`, lines 35-40) invokes any tool, and it
does so as `python pdsarchives.py --initialize …` — by source-file name relative
to the current directory, which is neither the console-script name
(`pdsarchives`) nor `python -m`. The other 11 contain no Python invocation at all
(`grep -nE 'python|\.py'` over each finds only `rsync --include` patterns and
`echo` lines in the six `pdsdata-sync-*.sh`, and nothing in
`copy_all_except_metadata.sh`, `copy_documents.sh`, `copy_shelves.sh`,
`create_fake_volumes_for_metadata.sh`, `setup_new_holdings.sh`).

The conclusion "so nothing in Python reaches them" happens to be true —
`grep -rn '\.sh\b' --include=*.py src tests` finds only two comment lines — but
it does not follow from the premise, and the premise generalizes one script to
twelve.

### M5. `shelf_consistency_check` module docstring — "`shelves/<kind>` … is replaced by `holdings`"

Line 152 is `shelf_path.replace('shelves/' + tail, 'holdings')`, which replaces
**every** occurrence in the path, not the one that identified the kind. I was not
able to build a tree that makes this bite (see below), so this is recorded as
imprecision rather than a demonstrated defect.

---

## Claims I could not verify

1. **Whether a `pdsdependency` run actually creates the log files (M2).** I read
   `_common.log_paths_for()` and `pdslogger.file_handler()` rather than running
   the tool on a volume, because a real run writes into the `logs/` tree parallel
   to `/seti/opus/pdsdata/holdings` and I would be modifying the shared holdings
   area. In particular I did **not** establish whether `file_handler` creates
   missing parent directories.
2. **The "replaced everywhere" nuance in M5.** I built
   `<S>/H/shelves/info/a/shelves/info/VS` to get two occurrences of
   `shelves/info` into one path, but the inner `.../a/shelves` directory is
   skipped by `root.endswith('shelves')` and the leaves held no files, so the run
   reported `Tests performed: 0`. I could not construct a case that reaches line
   152 with two occurrences; the claim is neither confirmed nor disproved.
3. **The "out of date" branch on real data.** I exercised it by monkeypatching
   `PdsDependency.get_modtime` in my own process, not by finding a genuinely
   stale source/requirement pair in the holdings tree. The marker substitutions
   the branch performs are therefore confirmed; the branch's *trigger condition*
   (`requirement_modtime < source_modtime` after two recursive directory walks)
   was not exercised end to end.
4. **The dot-underscore exit-status claim in `get_modtime`.** I confirmed each
   link of the chain separately — `pdslogger` maps the `dot_` alias to
   `logging.ERROR` (`_DEFAULT_LEVEL_BY_NAME`, pdslogger line 159); `close()`
   transfers each tier's counters to the tier above; `summarize()` counts
   anything at level >= ERROR as an error; `main()` sets `status = 1` when
   `errors` is non-zero — but I never ran the tool over a tree containing a real
   `._*` file to see status 1 come out.
5. **Whether the `.DS_Store` / dot-underscore checks behave as described on a
   path whose *ancestor* is a dot-underscore directory.** The test is
   `'/._' in absfile` against the joined absolute path, not against `file`, so a
   directory named `._x` would flag everything under it. The docstring says
   "a dot-underscore file". I did not build such a tree.
6. **Windows behaviour of `shelf_consistency_check`.** Both `partition('shelves/')`
   calls use a literal forward slash. On a platform where `os.walk` yields
   backslash-separated roots, `tail` would be the empty string for every
   directory and every one would be reported as an error. Not testable here.
7. **"Modification times of directories are taken recursively, over every file
   below them, and cached."** Verified by reading `get_modtime` and by the
   `MODTIME_DICT` write at line 325; not verified by an end-to-end run showing a
   directory walked once for two rules.
8. **`crlf`'s `OSError` claims.** The `Raises:` entries for a file that cannot be
   read or rewritten are plausible from the two `open()` calls, but I did not
   construct an unreadable/unwritable file (the session runs as the file owner).
9. **`re_validate`'s side of the "five per-volume validations" claim.** I
   confirmed `re_validate` declares exactly five test flags (`--checksums`,
   `--archives`, `--info`, `--links`, `--dependencies`) and that
   `pdsdependency.test(...)` is the last of the seven code blocks in
   `validate_one_volume`. Whether "five" is the right unit of counting for that
   function (seven blocks, five flags) is a judgement I left alone; `re_validate`
   is outside my slice.

---

## Claims I checked and confirmed

The load-bearing ones, so the next reader need not repay them.

* **`TESTS` has 49 rows and names 41 suites between them** — measured:
  `len(P.TESTS.tuples) == 49`; 119 suite mentions across those rows collapse to
  41 distinct names.
* **"Every name ``TESTS`` produces is registered"** (`test_suite`'s `KeyError`
  note) — the 41 distinct names in `TESTS` and the 41 keys of
  `PdsDependency.DEPENDENCY_SUITES` are the same set, in both directions: nothing
  in `TESTS` is unregistered and no suite is registered that `TESTS` never names.
* **"A rule can also require the derived file to be no older than its source.
  That is the majority of them"** — 73 of 117 registered rules have
  `newer=True` (62 %).
* **`test1`'s loop order** — outer loop over substitutions, inner over files.
  A synthetic two-substitution rule over three `.JPG` files on
  `volumes/HSTNx_xxxx/HSTN0_7176` logged
  `_A.jpg, _A.jpg` then `_B.jpg, _B.jpg`, exactly as the docstring says
  ("reports all the missing thumbnails together rather than all four sizes of one
  image together").
* **`test1`'s deduplication rule** — "The last three are reported once per
  required path… The first two are not deduplicated". Measured: a rule whose 3
  matched files all imply one required path logged `Missing file` once and
  `Confirmed` once; a rule with two substitutions logged `Test skipped` twice for
  the same excepted file and `Invalid test` twice for each of the three files.
* **`test1`'s "logged nothing at all -- not even the rule's title"** — the
  `if not abspaths: return (0, 0, 0, 0)` precedes `logger.open`.
* **The four message markers** — measured on a synthetic rule carrying both
  `CMD-c [c] [d]x/\1[x] TAIL` and `CMD-C [C] [d]x/\1[x] TAIL`:
  missing → `CMD-c initialize <root>x/...` and `CMD-C initialize <root>x/...`
  (both cut at `[x]`); stale → `CMD-c repair <root>x/...` (cut) and
  `CMD-C reinitialize <root>x/... TAIL` (`[x]` removed, tail kept). Exactly the
  rule the `messages` parameter states.
* **The `"Newer "` title rewrite** — `'Newer FOO for BAR'` becomes `'Foo for bar'`
  under `check_newer=False` and is unchanged under `True`. `capitalize()` would
  lower an interior capital, but no current title has one: measured over all 117
  rules, zero `"Newer "` titles are altered beyond their first letter.
* **`cumname`'s character positions** — `cumname('COISS_1010', '999')` →
  `'COISS_1999'`; `cumname('RPX_0001', '99')` → `'RPX_0099'`;
  `cumname('NHJULO_1001', 'NH')` → `'NHxxLO_1999'`. `volname[4:8]` is indeed the
  fifth through eighth characters, and the branch is taken on `nines[0] == '9'`
  alone.
* **Class-level state** — exactly three class attributes; `purge_cache` has no
  caller anywhere in `src/` or `tests/`; `COMMANDS_TO_TYPE` is appended to at
  lines 460 and 486 with an `if cmd not in` guard and is never emptied;
  `PdsDependency` is never constructed outside its own module; every one of the
  117 rules has a non-`None` suite and a non-empty title.
* **`TESTS` is consulted in exactly one place** — line 1267, inside `test()`.
* **`TESTS.all()` returns matches in table order** — read
  `TranslatorByRegex.all`: the default `strings_first=False` iterates
  `self.tuples` in order.
* **Every exception pattern begins with a wildcard** — all 20 compiled exception
  patterns start with `.*`, as the `exceptions` parameter claims; and
  `fullmatch` is applied to the absolute path.
* **Every `regex` is given as a string and anchored** — all 117 have a
  `regex_pattern` of the form `^...$`, and none contains a top-level alternation
  that the anchoring would mis-bind.
* **`main()`'s log-root fallback "is the same one" as the shared helper** —
  `pdsdependency.LOGROOT_ENV == _common.LOGROOT_ENV == 'PDS_LOG_ROOT'`, and the
  inline `if args.log == '': try: os.environ[...] except KeyError: None` is
  character-for-character the body of `_common.resolve_log_root()`.
* **`ds_store` is DEBUG and `dot_` is ERROR** — `pdslogger._DEFAULT_LEVEL_BY_NAME`
  lines 158-159.
* **`crlf`'s threshold is strict** — a file that is exactly 1 % non-ASCII
  (`b'\x01' + b'A'*99`) returns `INVALID`, i.e. is treated as text; 2 % returns
  `BINARY`.
* **`crlf`'s `ZeroDivisionError` on a zero-byte file** — reproduced.
* **`crlf`'s "single-byte codec"** — `'latin8'` resolves to `iso8859-14`, decodes
  all 256 byte values, and round-trips them unchanged, so "every byte is one
  character" holds and a repair cannot corrupt a byte.
* **`crlf.main`'s summary matrix** — all six cases reproduced through
  `crlf.main()`: 2 invalid → `2/2 files invalid`; 1 invalid of 2 →
  `1/2 files invalid`; 1 file → no summary; 0 files → no summary; 2 OK →
  `2 files tested`; 2 repaired → **no summary at all**; 1 repaired of 2 →
  `1/2 files repaired`. `--help` exits 0, an unknown option exits 2, and flags
  intermixed among paths are honoured.
* **`crlf`'s CR-only-file paragraph** — `b'a\rb\r'` is one record, verdict
  `INVALID`, and `--repair` yields `b'a\rb\r\r\n'`: one terminator appended, the
  interior CR left alone.
* **`shelf_consistency_check`'s "root that does not exist"** — reports nothing,
  contributes nothing, `rc = 0`.
* **`shelf_consistency_check`'s "one error per directory" paragraph** — the
  `myshelves-backup` tree above shows the parent and its child each reported and
  each counted; the walk is not pruned.
* **`pds3/__init__`'s counting and script claims** — ten non-`__init__` modules
  in the package; the five tool modules each declare `SPEC = _common.ToolSpec(…)`
  and a five-key `TASKS`; all ten pds3+pds4 tools are in `[project.scripts]`
  (pyproject lines 81-91) and `pdsdependency` is too, while `crlf`, `re_validate`
  and `shelf_consistency_check` are not — so "All four are run with ``python -m``
  except ``pdsdependency``" holds. `crlf` and `shelf_consistency_check` import
  only `argparse`, `os`, `sys`. `pdsdependency` and `re_validate` both build log
  paths through `_common.log_paths_for`. `pdslinkshelf.py:65` imports `REPAIRS`
  from `linkshelf_repairs`.
* **`pds4/__init__`'s "each module's docstring says where its own behavior parts
  company with its twin's"** — all five pds4 module docstrings contain an
  explicit PDS3 comparison, and `pds4linkshelf`'s gives the reason there is no
  repair table ("the machinery is in place and the table is empty").
* **`pdsdependency`'s "Nothing here is imported by another tool except
  ``re_validate``, which calls ``test()`` as the last of its five per-volume
  validations"** — `re_validate.py:75` is the only import of the module in
  `src/`, and `re_validate.py:290` is the last validation block in
  `validate_one_volume`.
