# PR-30a round 1 — adversarial docstring review

Slice: `holdings_maintenance/{__init__,_common,_archives_common,_shelf_common,
_indexshelf_common,_linkshelf_common}.py`.

Head verified at start: `2fd40c43c0e3fba3d4487dab2bb673f80cf36169`.
Base: `80f5e523fa4d6727f9559b4684fd884cf8dcc94e`.
All line numbers below are the **frozen 2fd40c4** text.

## Tree drift during the review (read this first)

The tree was not frozen. `git rev-parse HEAD` returned `2fd40c4` on my first
command; partway through it returned `03d227f9791824c89ae803a90fc58894ae868d3e`
with an uncommitted modification to `_common.py` and a new untracked
`critiques/pr-30a/check_spec_readers.py`. Of my six files only `_common.py`
changed (`ToolSpec` docstring only — per-field reader names expanded); the other
five are byte-identical to 2fd40c4. I reviewed 2fd40c4 and note per finding
whether the in-flight edit changes the verdict.

By the end of the review HEAD was `bd5b192a914d51790e20697ed7b223376235efec`,
eight commits past `2fd40c4`. Status of the section A findings against that HEAD,
checked at the end:

| finding | at bd5b192 |
|---|---|
| A1 four standalone modules "use nothing here" | **fixed** (`6acfb14`) |
| A7 "only ``index_ext`` differs in value" | **fixed** (`bd5b192`); the replacement paragraph is correct — five fields differ, three reach the module, and `holdings_sentinel`/`file_log_level` are read nowhere in it |
| A2, A3, A4, A5, A6, A8, A9, A10, A11, A12, A13, A14 | **still live**, wording unchanged apart from A3's "among them" softening, which does not remove the counterexample |

Docstrings-only claim verified: ASTs with docstrings stripped are identical
between 80f5e52 and 2fd40c4 for all six files (`__init__.py` differs only
because an empty module body became a docstring). Comment counts dropped in
every file (e.g. `_common` 42→31), so comments were rewritten too.

---

## A. Claims disproved

### A1. `_common.py:20-22` — the four standalone pds3 modules "use nothing here"

> "The four other modules under ``pds3/`` -- ``crlf.py``, ``pdsdependency.py``,
> ``re_validate.py`` and ``shelf_consistency_check.py`` -- parse their own command
> lines and use nothing here."

Two of the four use `_common`:

- `pds3/pdsdependency.py:21` `from pdsfile.holdings_maintenance import _common`;
  `:1123` `_common.log_paths_for(pdsdir, 'log_path_for_volume', ...)`.
- `pds3/re_validate.py:22` imports `_common`; `:70` `_common.log_paths_for(...)`,
  `:477` `_common.LOG_HELP`/`_common.LOGROOT_ENV`, `:511` `_common.QUIET_HELP`,
  `:966` `_common.resolve_log_root(args)`.

`re_validate.py` in particular builds its whole `--log`/`--quiet` help text and
its log-root resolution out of this module. Established by
`grep -n "_common\." pds3/pdsdependency.py pds3/re_validate.py`.

`__init__.py:20` carries the softer version of the same claim ("four modules that
share none of that"), which is also wrong for these two if "that" includes the
shared command-line pieces.

### A2. `_common.py:143` — `handler_factories` "in the log directory of every target"

> "handler_factories: ... Read twice per run: setup_run() attaches them at the log
> root, and each driver attaches them again in the log directory of every target."

False for `run_index_main()`, which attaches them in the **tool's own** log
directory — one directory per log root, the same one for every target.
`_indexshelf_common.py:748-751` deliberately rpartitions the tool subdir back off
the path, and `run_index_main`'s own docstring (`:691-692`) says so: "their
per-target handlers are created in the tool's own log directory rather than in the
target's." The two sentences contradict each other.

Measured, with `PDS_LOG_ROOT`-equivalent set to `/tmp/LOGROOT` and the table
`metadata/HSTUx_xxxx_v1.1/HSTU0_8405/HSTU0_8405_index.tab`:

```
logfile        : /tmp/LOGROOT/pdsindexshelf/metadata/HSTUx_xxxx_v1.1/HSTU0_8405/HSTU0_8405_index_..._repair.log
handler logdir : /tmp/LOGROOT/pdsindexshelf          <- what run_index_main uses
target's dir   : /tmp/LOGROOT/pdsindexshelf/metadata/HSTUx_xxxx_v1.1/HSTU0_8405
```

For comparison, `run_main` on a link shelf target gives handler logdir
`/tmp/LOGROOT/pdslinkshelf/volumes/COCIRS_5xxx`, i.e. the target's own directory.

**The in-flight `_common.py` edit does not fix this** — it still says "attach them
again in the log directory of every target", now naming `run_index_main()`
explicitly, which makes the claim worse.

### A3. `_common.py:93` — `logname`: "every helper that takes an optional logger falls back"

> "logname: ... every helper that takes an optional logger falls back to
> PdsLogger.get_logger() on it."

`_linkshelf_common.read_links(spec, abspath, logger=None)` takes an optional
logger and does not fall back — it never references `logger` at all (its own
docstring at `_linkshelf_common.py:231-233` says so). Established by AST: the
identifier `logger` does not appear anywhere in `read_links`'s body.

`_shelf_common.move_old(path, kind, *, logger=None)` is a second counterexample of
a different shape: it falls back on `kind.logname`, not `spec.logname`.

The in-flight edit softens this to "among them ..." but keeps the universal
"every helper that takes an optional logger falls back to a logger of that name",
so the counterexample stands.

### A4. `_common.py:371-375` — `log_paths_for` documents an unreachable `ValueError`

> "ValueError: from either call to the looked-up method, written ``build()`` here,
> for a place option it does not recognize, ..."

`log_paths_for` hard-codes both places (`_common.py:379-380`):
`build(*args, place='default', **kwargs)` and `build(*args, place='parallel', **kwargs)`.
`_derived_paths._log_path_for:475-480` raises only when `place` is neither of
those two, so this branch cannot fire through `log_paths_for()`. A caller that
supplies `place` in `kwargs` gets `TypeError` (duplicate keyword), not
`ValueError`. The second half of that entry — `ValueError` from
`log_path_for_index` for a non-index file (`_derived_paths.py:590-591`) — is
reachable and correct.

### A5. `_archives_common.py:17-26` — "Three pieces are here" / "The rest is constants"

> "Three pieces are here because both flavors need them and neither differs on
> them: the walk ..., the tarfile member filter ..., and the comparison of the two
> inventories. ... The rest of the module is the constants the two tools share."

The module holds a fourth shared function that is neither one of the three nor a
constant: `reject_checksum_and_archive_paths()` (`_archives_common.py:38`), called
by both flavors — `pds3/pdsarchives.py:217` and `pds4/pds4archives.py:242`.
Established by `grep -rn reject_checksum_and_archive_paths`.

### A6. `_archives_common.py:22-23` — "named ``dirpath`` throughout"

> "The tuples' second element is named ``dirpath`` throughout, and it is an
> interior path rather than a directory."

Contradicted inside this very module. In `load_directory_info`, `dirpath` is the
**walk root, a real directory** — `_archives_common.py:138` `dirpath = pdsdir.abspath`,
`:146` `logger.open('Generating file info', dirpath, ...)`, `:152`
`os.walk(dirpath)`. The tuple's second element there is the unnamed expression
`abspath[lskip:]` (`:151`, `:177`, `:192`). Only `validate_tuples` (`:325`, `:328`)
unpacks it under the name `dirpath`. So the one place the warning is aimed at is
the one place where `dirpath` really does mean a directory.

### A7. `_indexshelf_common.py:21-23` — "only ``index_ext`` differs in value"

> "The two tools differ only in their spec, and among the fields that reach this
> module only ``index_ext`` differs in value, '.tab' against '.csv'."

False. Measured by importing both specs and diffing over the eight fields this
module actually reads (`spec.` occurrences in `_indexshelf_common.py`):

```
handler_factories  pds3=(error_handler,)  pds4=(warning_handler, error_handler)  SAME=False
index_ext          pds3='.tab'            pds4='.csv'                            SAME=False
pdsfile_cls        pds3=Pds3File          pds4=Pds4File                          SAME=False
log_path_method    'log_path_for_index'   'log_path_for_index'                   SAME=True
log_suffix         ''                     ''                                     SAME=True
logname            'pds.validation.indexshelf'  (same)                           SAME=True
progname           'pdsindexshelf'        'pdsindexshelf'                        SAME=True
unit               'table'                'table'                                SAME=True
```

`pdsfile_cls` is read at `:184`, `:652`, `:667`; `handler_factories` at `:755`.
Both reach this module and both differ.

### A8. `_indexshelf_common.py:26-29` — "is written by the former two"

> "``index_initialize()`` and ``index_validate()`` test the fresh table dictionary
> against None ... while ``index_reinitialize()`` and ``index_repair()`` test it for
> emptiness; a table with no rows therefore stops the latter two and is written by
> the former two."

`index_validate()` never writes anything. AST check of the five tasks:

```
index_initialize     write_indexdict=True
index_reinitialize   write_indexdict=True
index_validate       write_indexdict=False   <-
index_repair         write_indexdict=True
index_update         write_indexdict=False
```

An empty table dictionary in `index_validate` is not written; it falls through to
`load_indexdict()` and is compared.

### A9. `_indexshelf_common.py:348-349` — "the one task that never overwrites"

> "A shelf file already in place is logged as an error and nothing is read or
> written, so this is the one task that never overwrites."

Two other tasks never overwrite either: `index_validate` never calls
`write_indexdict` at all, and `index_update` (`:573-578`) writes only when no
shelf exists — an existing shelf is reported at info level and left alone. Same
AST table as A8.

### A10. `_indexshelf_common.py:257-259` — `load_indexdict` `Raises:`

> "pickle.PickleError: from ``load()`` on a shelf file that is not readable as a
> pickle. It is logged through ``exception()`` and re-raised."

A **zero-length** shelf file — the ordinary result of an interrupted or truncated
write — raises `EOFError`, which is not a `PickleError`, is not caught by
`except pickle.PickleError` at `:287`, is therefore not logged, and appears in no
`Raises:` entry. Measured against a real table with the shelf path redirected:

```
missing shelf   -> load_indexdict returns {}            (matches the docstring)
zero-byte shelf -> EOFError | caught by except pickle.PickleError: False
```

(`pickle.load` on a non-empty non-pickle file does give `UnpicklingError`, so the
documented case is real; it is just not the whole contract.)

### A11. `_linkshelf_common.py:973-975` — deleted entries are *not* kept

> "An entry for a file that has since been deleted is therefore kept, and a file
> whose links have changed is not re-read."

The first clause is false; the second is true. Both flavors' `generate_links`
build the result by iterating over the files found by the **current** walk —
`pds3/pdslinkshelf.py:395` and `pds4/pds4linkshelf.py:445`, both `for key in abspaths:`
where `abspaths` is filled at `pds3:151` / `pds4:135` during the walk. A key in
`old_links` whose file is gone never reaches `link_dict`.

Measured on `volumes/COCIRS_5xxx/COCIRS_5402`, seeding `old_links` with an entry
for a nonexistent file:

```
old had ghost   : True
merged has ghost: False
keys dropped from old: ['.../COCIRS_5402/THIS_FILE_WAS_DELETED.LBL']
```

Consequence for the surrounding prose: because the merged dict differs from the
shelf, `link_update` does **not** cancel, and it writes a shelf with the deleted
file's entry removed — the opposite of what the docstring promises.

### A12. `_linkshelf_common.py:18` and `:431` — the triple's second element is not a basename

> `:18`  "a **list** of ``(record number, basename, path)`` triples"
> `:431` "a list of (record number, basename, absolute path) triples"

The second element is `LinkInfo.linktext`, the link text as written, which may
carry a directory. `pds3/pdslinkshelf.py:405` and `pds4/pds4linkshelf.py:455` both
normalize with `new_list.append((item.recno, item.linktext, item.target))`.
`link_text_of`'s own docstring (`_linkshelf_common.py:181-182`) gets this right —
"The tuple's second element is the text rather than the repaired name" — so the
module docstring and `load_links` contradict it.

Measured over 1,842 real link shelves (120 sampled), 431,386 triples: **313 have a
second element containing `/`**, e.g. from `ASTROM_0001_links.pickle`:

```
key 'DATA/EASYDATA/DIONE.LBL' -> (14, 'DATA/SORCDATA/DIONE_TABLE_REV2.TXT',
                                      'DATA/SORCDATA/DIONE_TABLE_REV2.TXT')
```

### A13. `_common.py:150-151` and `_linkshelf_common.py:880-881` — "the files read"

> `_common.py:150` "returning the links found in that unit and the latest
> modification time among the files read."
> `_linkshelf_common.py:880` "the shelf is compared against the newest file the
> scan read"

The value is the max over **every file the walk sees**, taken before any skip test
and regardless of whether the file is ever opened. `pds3/pdslinkshelf.py:130-132`
(and `pds4/pds4linkshelf.py:89-91`):

```python
for basename in files:
    abspath = os.path.join(root, basename)
    latest_mtime = max(latest_mtime, os.path.getmtime(abspath))
    if basename == '.DS_Store': ... continue      # skipped, mtime already counted
```

Only files whose extension is in `EXTS_WO_LABELS` are actually read
(`pds3:169-175`). On `COCIRS_5402` the scan read exactly one file
(`INDEX/OBSINDEX.LBL`, per the log) but `latest_mtime` was the max over both files
in the tree. A `.DS_Store` or a backup file touched today would move the "newest
file the scan read" without anything having been read.

### A14. `_linkshelf_common.py:761-762` — "the one task of the five that never rewrites a shelf"

`link_validate` never writes either. AST check:

```
link_initialize    write_linkdict=True  move_old=False
link_reinitialize  write_linkdict=True  move_old=True
link_validate      write_linkdict=False move_old=False   <-
link_repair        write_linkdict=True  move_old=True
link_update        write_linkdict=True  move_old=True
```

(The second sentence of that paragraph — "the only one that writes without
versioning first" — is correct.)

---

## B. Weaker findings (misleading rather than flatly false)

### B1. `_common.py:36-37` — "setup_run() ... is the whole of what they share"

All three drivers also share `_common.log_paths_for()` (`_common.py:465`,
`_shelf_common.py:585`, `_indexshelf_common.py:739`) and the
`spec.handler_factories` loop; two of the three also share `_common.set_log_dirs()`.

### B2. `_common.py:94-96` — "Every construction of a PdsFile ... goes through it"

Four constructions in the shared modules do not go through `spec.pdsfile_cls`:
`_shelf_common.py:480` `pdsf.child(c)`, `:493` `pdsf.parent()`, `:580`
`pdsdir.child(...)`, `_linkshelf_common.py:1090` `pdsf.child(c)`. They produce
objects of the right class, so the intent survives; the sentence as written does
not.

### B3. `_archives_common.py:102-107` — "each logged under its own level"

`.DS_Store` and dot-underscore files get dedicated pdslogger levels (`ds_store`,
`dot_`), but backup files go to `logger.error` (`:167`), which every other error in
the package shares. A limit can be set on `error`, but not on backup files alone.

### B4. `_linkshelf_common.py:681-683` — "both callers' lists come back sorted"

The only lists that get sorted are the ones present in **both** dictionaries, and
those are deleted from both immediately afterwards (`:731-732`). A caller holding
only the dictionaries cannot reach any sorted list. The mutation claim is true of
the list objects; the "come back" framing is not.

### B5. `_linkshelf_common.py:891-893` — "made before validate_links() would empty them"

`link_repair` never calls `validate_links()`. AST confirms `validate_links` appears
only in `link_validate`. The sentence reads as a sequencing claim about this
function's own body.

### B6. Driver `Raises:` sections omit `setup_run()`'s other exits

`setup_run` documents three `SystemExit` statuses and all three are real (measured:
missing task → 1, `--help` → 0, unparseable command line → 2). But:

- `_common.py:434-440` (`run_main`) names only the path-not-found exit and the
  closing exit — no mention of `setup_run`'s exits at all, including "Missing task".
- `_indexshelf_common.py:710-715` (`run_index_main`) names `index_targets` and the
  closing exit — same omission.
- `_shelf_common.py:556-559` (`run_selection_main`) names the missing-task exit but
  not `--help` (0) or the parse error (2).

### B7. `__init__.py:27-28` — "a parallel place under the root"

Measured: with a log root set, `place='default'` is the path **under the root** and
`place='parallel'` is the fixed `logs/` tree beside holdings. So the extra path a
log root produces is the *default* place, and the word "parallel" in `__init__.py`
names the opposite thing from the `place='parallel'` option twenty lines away in
`_common.log_paths_for`. The set of two paths described is correct; the vocabulary
inverts the code's.

---

## C. Claims I could not verify either way

1. **`_common.py:120-123`, `file_log_level`: "they render different level names,
   produce different closing summaries".** I confirmed both `info` and `normal`
   exist on `PdsLogger` and that only `info` is capped by the `{'info': N}` entries
   in `_archives_common`, but I did not produce a side-by-side run of a pds3 and a
   pds4 archive tool to compare rendered level names and closing summaries.

2. **`_indexshelf_common.py:691-692` and `:695-698`, the "three reasons" and "two
   consequences".** These are causal claims ("two consequences of the third
   reason"). Each individual fact is true — the driver records no log directories,
   and it alone passes `logger=` to its tasks (`:768`, against `_common.py:490` and
   `_shelf_common.py:618`) — but neither follows from where the handlers are
   created, and I could not settle whether the causal framing is meant literally.

3. **`_common.py:105-107`, `holdings_sentinel` "acts on ... the checksum, info shelf
   and link shelf tools".** Both readers confirmed
   (`_shelf_common.py:390`, `_linkshelf_common.py:326`). But `locate_nonlocal_link`
   is reached only via `pds{3,4}linkshelf`'s `generate_links` on a link that is not
   local; I did not construct a case that actually enters it for both flavors, only
   for pds3.

4. **`_indexshelf_common.py:710-715`, `run_index_main`'s `Raises:`.** `log_paths_for`
   can raise `ValueError` from `log_path_for_index` for a PdsFile that is not an
   index file, and `index_targets` admits any `/metadata/`-resident file with the
   right extension. I could not find a `.tab` file under `metadata/` in the test
   holdings for which `is_index` is False, so I could not show the gap is reachable.

5. **`_shelf_common.py:203-206`, `move_old`'s `Raises:`.** `FileNotFoundError` from a
   missing companion is confirmed reachable by reading. But `next_version_dest()`
   can raise `ValueError` (measured: a `_vabc.pickle` in the log directory, or an
   empty `ext`), and `shutil.copy(path, dest)` can raise if a `LOGDIRS` entry does
   not exist. Neither is in `Raises:`. Whether a driver can leave a nonexistent
   directory in `LOGDIRS` depends on whether `pdslogger.file_handler` creates it
   first; I did not settle that.

6. **`_linkshelf_common.py:28-30`, "Inside a run a link is a ``LinkInfo`` object".**
   Measured: both flavors normalize every `LinkInfo` to a tuple before returning
   from `generate_links` (`pds3:400-408`, `pds4:450-458`), so no function in
   `_linkshelf_common` other than `read_links` and `link_text_of` ever sees one.
   Whether the sentence is meant to describe this module or the tool modules I
   could not decide.

7. **`_indexshelf_common.py:14-16`, "Both are written together and both are re-dated
   together, so a caller reading either gets the same answer".** The writing and
   re-dating are confirmed. "A caller reading either gets the same answer" is a
   claim about consumers of the `.py` sidecar, and I found no code in this repo
   that reads a `_linkshelf`/`_indexshelf` `.py` sidecar at all, so I could not
   check it.

8. **`_common.py:69-70`, "how a missing archive file is reported" differs between the
   flavors.** Plausible from the two tool modules but I did not diff their
   missing-archive paths.

---

## D. Defects in the code (not the prose) — recorded, not fixed

### D1. `pds3/pdsarchives.py:240` — wrong `log_suffix`

```python
log_suffix='_links',        # pdsarchives
```

`pds4/pds4archives.py:260` has `log_suffix='_archives'`. The PDS3 archive tool
names its log files `<volume>_links_<time>[_task].log` — the link shelf tool's
suffix. Pre-existing (present at `80f5e52`). Not a file collision, because the log
directory is `spec.progname` (`pdsarchives` vs `pdslinkshelf`), but the basename is
wrong. Measured: `pdsarchives.SPEC.log_suffix == '_links'`.

### D2. `_indexshelf_common.py:283` / `load_indexdict` — `EOFError` on a truncated shelf

A zero-length shelf file raises `EOFError` out of `pickle.load`, which
`except pickle.PickleError` (`:287`) does not catch, so it is neither logged nor
converted; it escapes `load_indexdict` unlogged while every other failure in the
function is logged. `_linkshelf_common.load_links` does not have this hole — it
catches `(Exception, KeyboardInterrupt)`.

### D3. `_indexshelf_common.py:511` and `_linkshelf_common.py:929` — `str.replace` on a path

```python
shelf_pypath = shelf_path.replace('.pickle', '.py')
link_pypath  = link_path.replace('.pickle', '.py')
```

`str.replace` rewrites every occurrence. A shelf whose path contains `.pickle`
anywhere but the extension gets a wrong sidecar path, and `os.path.getmtime` then
raises `FileNotFoundError` from inside the "content is up to date" branch. The
neighbouring writers use `rpartition('.')[0] + '.py'` (`_indexshelf_common.py:200`,
`_linkshelf_common.py:623`), so the two halves of the same pair disagree on how the
sidecar path is derived.

### D4. `_shelf_common.py:169-176` — `next_version_dest` collides above 999

Documented in the docstring, so it is not hidden, but it is real. Measured: with
`_v001`..`_v999` present, the function returns `_v1000` — and returns `_v1000`
again after `_v1000` exists, because the `_v???` glob cannot match a four-digit
name. `move_old` then silently overwrites the previous `_v1000`.

### D5. `_shelf_common.py:491-497` — `expand_selection_targets` can dereference `None`

`pdsdir = pdsf.parent()` followed by `pdsdir.is_bundle_dir`. For a file with no
parent PdsFile this is an `AttributeError` rather than the documented `SystemExit`.
I did not construct such a path inside a holdings tree, so this is theoretical.

---

## E. Claims checked and confirmed (so the next round need not redo them)

Per-field reader map in `ToolSpec` — every entry except `logname` (A3),
`pdsfile_cls` (B2) and `handler_factories` (A2) matches
`grep -rn 'spec\.<field>'` exactly, including the "and nowhere else" claims for
`index_ext` (one reader) and `expand_target` (one reader), the four readers of
`file_log_level`, the five readers of `generate_links`, the single reader of
`link_target_regex`, and the `_shelf_common`-only readers of the three messages.

"No tool module reads its own spec": confirmed — no `SPEC.<field>` access anywhere
under `pds3/` or `pds4/`; the tool modules only pass `SPEC` down.

"All ten specs set all twelve required fields": confirmed by reading all ten
declarations. "For all five pds4 tools [progname] is the pds3 tool's name":
confirmed (`pdsarchives`, `pdschecksums`, `pdsindexshelf`, `pdsinfoshelf`,
`pdslinkshelf`).

`_indexshelf_common.py:11` "They import nothing from `_shelf_common.py`" — true
(neither index shelf tool nor this module imports it). `_shelf_common.py:24` "The
archive tools and the index shelf tools use nothing here" — true.
`_shelf_common.py:22` link shelf tools take `LINKSHELF_LOGNAME` and
`UNIT_LOG_PATH_METHOD` — true. `:19-20` info shelf tools use `modtimes_agree`,
checksum tools use `hashfile` — true. `:54-59` `Pds3File.log_path_for_volume` /
`log_path_for_volset` are aliases — true.

`__init__.py` "Eleven modules are console scripts" — pyproject lists exactly
eleven, over eleven distinct modules. "The five `_*_common.py` modules" — five.
"This module is a namespace and defines nothing" — true.

Which drivers exit and which return: AST — `run_main` 0 returns / 2 `sys.exit`;
`run_index_main` 0 returns / 1 `sys.exit`; `run_selection_main` 1 return / 0
`sys.exit`. `RunResult` field readers match the four `main()` bodies.

Arithmetic and boundaries, all measured:

- `modtimes_agree`: `.999999` apart → True; exactly 1s → False; two `''` → True;
  `''` vs a real time → False; aware vs naive → falls back to string compare →
  False; `None, None` → True. Format `'%Y-%m-%d %H:%M:%S.%f'` confirmed at
  `pds3/pdsinfoshelf.py:66`; sentinel `''` at `:91`/`:178`.
- `validate_tuples`: delta 0.999 → valid, 1.0 → valid, 1.0001 → invalid. Interior
  path differing alone → valid.
- `next_version_dest`: empty dir → `_v001`; empty `ext` with a match → `ValueError`
  on an empty slice; empty `ext` with no match → fine; `_vabc` → `ValueError`.
- Tenth-of-a-day threshold: `86400/10 == 8640.0`; 2 days → "2.0 days", 30 minutes →
  "30.0 minutes" (real `index_repair` runs).
- "Older of the two": with a stale pickle and a fresh sidecar, `index_repair`
  reported the *pickle's* date and touched both. Equal times → "repair canceled".
- `write_linkdict` `../` arithmetic, round-tripped through `load_links`: same set →
  `../COCIRS_5403/INDEX/X.FMT`; same category → `../../COCIRS_6xxx/...`; other
  category → `../../../metadata/...`; inside the unit → `INDEX/OBSINDEX.TAB`.
  `lskip` from `shelf_path_and_lskip('link')` is exactly `len(dirpath)+1`, so
  `prefix == dirpath + '/'`. Sidecar name line: `COCIRS_5402_links = {`.
- `locate_nonlocal_link` termination: instrumented `os.listdir` shows the walk lists
  the start directory, then the unit directory, then stops — it never lists the
  bundleset directory.
- `load_directory_info`: root tuple first with `(interior='', 0, 0)`; `.DS_Store`,
  `._*`, `*_backup.*` and `* copy*` excluded; invisibles kept; the walk **does**
  descend into a `._` directory (`sub/._hidden_dir/inside.txt` is in the result).
- `move_old`: with `LOGDIRS` empty, nothing happens; with two entries, the original
  stays, and each destination gets `X_links_v001.pickle` and `X_links_v001.py`.
- `read_links`: a three-line `^STRUCTURE = (A.FMT,\n B.FMT,\n C.FMT)` gives three
  `is_target=True` links across records, then `D.TXT` with `is_target=False`.
- `resolve_holdings_paths` / `expand_selection_targets`: outside holdings → exit 1;
  `checksums-` → exit 1; unit name standing in for `COISS_2001.tar.gz` → resolved;
  archive unit set stays whole; non-archive unit set → 72 unit directories, no
  readme; deep file → exit 1. `OSError` really does come from the *first*
  `from_abspath` (traceback shows `_shelf_common.py:411`).
- `build_arg_parser` with a `task_help` missing `'repair'` → `KeyError: 'repair'`.
- `resolve_log_root`: `''` with no env → `None`; `''` with env → the env value;
  an explicit value survives.
- `validate_indexdict`'s `logger.error('not in shelf: %s', key)` is **not** a bug:
  `pdslogger.log` treats a lone extra arg as a filepath only when the message has
  no `%`/`{`, so these format correctly.
- `WRITE_ARCHIVE_LIMITS = {'info': -1, 'dot_': 100}` is **not** a typo:
  `PdsLogger.dot_underscore` logs under the level name `'dot_'`.
