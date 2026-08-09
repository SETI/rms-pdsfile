# Round 3 — second adversarial read of the `holdings_maintenance` shared core

Head verified: `git -C .../work rev-parse HEAD` = `e8af08085655c4bd9c4d46fc9c6f58c4a66b8244`.
Base for classification: `5b3cd2a` (the last commit before the correction commits
`6acfb14`, `bd5b192`, `4a25267`, `e8af080`). Every file was read through
`git show e8af080:<path>`.

Slice: `__init__.py`, `_common.py`, `_archives_common.py`, `_shelf_common.py`,
`_indexshelf_common.py`, `_linkshelf_common.py`, plus the ten tool modules they
describe and `critiques/pr-30a/check_spec_readers.py`.

Everything below was measured, not read: the tools were imported, the specs
introspected, `pdslogger` exercised directly, `LinkInfo.remove_path` instrumented over
493 real volumes, and the log paths built by the real `log_path_for_*` methods.

Tally: **11 disproved claims — 8 introduced by the corrections, 3 missed by the first
read** — plus 2 `Raises:` contracts with uncovered hazards (both missed by the first
read), 3 claims that could not be settled either way, 5 code defects, and one structural
limit in the checker.

---

## Disproved claims

### D1 — `_linkshelf_common.py:18-21` (module docstring). *Correction-introduced.*

> a **list** of ``(record number, link text, path)`` triples, for a file that points
> at others: a label, a catalog file, an index or a document. The middle element is
> the text the file was written with, not a basename: it carries a directory wherever
> the link did

False. `LinkInfo.remove_path()` rewrites `linktext` to the basename **in place**, and
`generate_links` stores `item.linktext` in the triple. In both tools the repair loop is

```python
linkname = repair.first(info.linktext)
if linkname is None:
    if '/' in info.linktext:
        info.remove_path()
        linkname = repair.first(info.linktext)
    if linkname is None:
        continue            # no repair found
```

so the truncation happens *before* it is known whether any repair exists, and is not
undone when the second lookup also misses.

Measured. `LinkInfo.remove_path` was instrumented and `pdslinkshelf.generate_links` run
over every volume of the test holdings that fits in a 220-second budget: **493 volumes,
1412 truncating calls.** Tracking the mutated objects by identity through to the
returned dictionary, VG_2801 alone shelves ten triples whose middle element is not what
the file says:

| file | written | shelved triple |
|---|---|---|
| `GEOMINFO.TXT` | `DOCUMENT/POLES.TXT` | `(126, 'POLES.TXT', '…/VG_2801/DOCUMENT/POLES.TXT')` |
| `CALINFO.TXT` | `DOCUMENT/TUTORIAL.TXT` | `(28, 'TUTORIAL.TXT', …)` |
| `DATAINFO.TXT` | `SOFTWARE/PPSRESAM.FOR` | `(56, 'PPSRESAM.FOR', …)` |
| `SOFTINFO.TXT` | `OAL/AAREADME.TXT` | `(24, 'AAREADME.TXT', '…/VG_2801/AAREADME.TXT')` |

The sentence it replaced said "basename", which was closer to the truth than what
replaced it.

### D2 — `_linkshelf_common.py:434-438` (`load_links` Returns). *Correction-introduced.*

> a list of (record number, link text, absolute path) triples, the middle element
> being the text as written and so carrying a directory wherever the link did

Same disproof as D1: `load_links` returns `str(basename)` straight out of the pickle,
and what was pickled is the possibly-truncated `linktext`.

### D3 — `_linkshelf_common.py:184-186` (`link_text_of`). *Missed by the first read.*

> The tuple's second element is the text rather than the repaired name, so both forms
> report what the file was written with.

The premise is right and the conclusion is not. `remove_path()` sets **both**
`linktext` and `linkname` to the basename — its own docstring three dozen lines above
says so ("Both the text and the name are set to the basename") — so after it fires
neither form reports what the file was written with. Present verbatim at `5b3cd2a`.

### D4 — `_linkshelf_common.py:769-774` (`link_initialize`). *Correction-introduced.*

> Two of the five tasks never rewrite a shelf: this one, which stops at the error
> above, and link_validate(), which writes nothing at all. This is the only one of
> the three that do write that writes without versioning first…

**Four** of the five tasks write, not three. `write_linkdict()` is called by
`link_initialize` (:799), `link_reinitialize` (:841), `link_repair` (:977) and
`link_update` (:1034). Only `link_validate` never writes. Neither reading of "the
three" survives: if the set includes `link_initialize` it has four members, and if it
excludes it then "This is the only one of the three" refers to a set this task is not
in. The sentence it replaced — "It is also the only one that writes without versioning
first" — carried no count and was correct.

### D5 — `_common.py:172-174` (`ToolSpec.handler_factories`). *Correction-introduced.*

> run_main() and _shelf_common.run_selection_main() use the directory of
> the target's own log file, so each target gets its own

The consequent is false, and false in the ordinary case. `log_path_for_bundle` builds
`<root>/<dir>/<category>/<bundleset><version>/<bundlename>…log`, so the *directory* is
the bundle **set**'s, shared by every unit in it — and `run_main`'s whole job is to
expand a unit-set path into its units. Measured with the real method and a log root of
`/tmp/logroot`:

```
COISS_2001 -> /tmp/logroot/pdsarchives/volumes/COISS_2xxx/COISS_2001_archives_…log
   logdir: /tmp/logroot/pdsarchives/volumes/COISS_2xxx
COISS_2002 -> /tmp/logroot/pdsarchives/volumes/COISS_2xxx/COISS_2002_archives_…log
   logdir: /tmp/logroot/pdsarchives/volumes/COISS_2xxx
```

The contrast the entry draws with `run_index_main` ("which is the same directory for
every table it processes") therefore does not separate the drivers: on a single-volset
command line `run_main` also uses one directory for every target. What actually differs
is *how* the directory is obtained — `os.path.split(logfile)[0]` against trimming back
to `<root>/<progname>` — and that difference is real; the "so each target gets its own"
that was hung on it is not.

### D6 — `_common.py:170` and `_common.py:43-45`. *Correction-introduced.*

> setup_run() attaches them once at the log root  …
> all three build their log paths through ``log_paths_for()`` and attach the spec's
> handler factories once per target

Two errors, both stated unconditionally.

* `setup_run` attaches them only `if args.log:` (`_common.py:378-381`). With neither
  `--log` nor `PDS_LOG_ROOT`, `resolve_log_root()` sets `args.log = None` and the field
  is never read. Measured with a counting factory substituted into the spec: no `--log`
  and no `PDS_LOG_ROOT` → **0** factory calls in `setup_run`; with `--log /tmp/logroot`
  → 1.
* The drivers attach them once **per log file**, not once per target:
  `for logfile in logfiles: … local_handlers += [make_handler(logdir) for make_handler
  in spec.handler_factories]`. With a log root configured `logfiles` has two entries in
  two different directories, so the factories run twice per target.

### D7 — `_indexshelf_common.py:270-273` (`load_indexdict` Raises). *Correction-introduced.*

> EOFError: … it escapes without being logged, unlike every other failure here.

The EOFError half is right — measured: a zero-length shelf gives
`EOFError('Ran out of input')` out of `pickle.load` at line 298, the enclosing
`except pickle.PickleError` does not catch it, and the surrounding logger closes with
`(0, 0, 0, 1)`, i.e. nothing was logged. "Unlike every other failure here" is wrong, and
the docstring's own next entry says so: *"OSError: raised by ``open()``… This one is not
caught either."* An `OSError` escapes unlogged on exactly the same terms, as would the
`TypeError` from `len(index_dict)` on a pickle holding a non-sized object. The only
failure that *is* logged is the `PickleError` (measured: a non-pickle file gives
`UnpicklingError`, which is a `PickleError` and is logged through `exception()`).

### D8 — `_indexshelf_common.py:736-739` (`run_index_main` Raises). *Correction-introduced.*

> ValueError: raised by ``log_paths_for()`` for a target that is not an index
> file, since the log path method these tools name checks that. Every path
> index_targets() admits carries the spec's extension and sits under
> metadata/, which is not the same test.

It *is* the same test, and `is_index`'s version of it is strictly weaker, so the
`ValueError` is unreachable through this driver. `_properties.is_index` (`:621-635`)
answers True when the shelf exists **or** when

```python
if '/metadata/' in self.abspath:
    for ext in cls.IDX_EXT:
        if self.abspath.lower().endswith(ext):
            return True
```

with `Pds3File.IDX_EXT == ('.tab',)` and `Pds4File.IDX_EXT == ('.csv', '.tab')`.
`index_targets` admits a path only if `'/metadata/' in path` and
`path.endswith(spec.index_ext)` — **case-sensitively**, and by a case-sensitive glob in
the directory branch. So every admitted path satisfies the `is_index` fallback.

Measured: of the **10,225** `.tab` files under `metadata/` in the test holdings,
**0** answer False to `is_index`.

### D9 — `_common.py:474-481` (`run_main` Raises). *Correction-introduced.*

> SystemExit: from ``sys.exit()``, four ways.

Two problems.

* The list under the count has five items: no task (1), `--help` (0), unclassifiable
  command line (2), non-existent path (1), and the closing status (1 or 0).
* It omits a real exit. `spec.expand_target` is `archive_targets` or `link_targets`,
  and both call `sys.exit(1)` for a path naming checksum files or archive files
  (`_archives_common.reject_checksum_and_archive_paths`,
  `_linkshelf_common.link_targets:1094-1100`). That exit is taken inside `run_main`'s
  own resolution loop, over a path that **does** exist, so it is not the documented
  "command-line path that does not exist". An enumeration that announces its own
  completeness has to cover it.

### D10 — `_archives_common.py:106-113` (`load_directory_info`). *Correction-introduced.*

> ``.DS_Store`` files and dot-underscore files, each logged under a pdslogger level of
> its own so that a message limit can be set on it alone, and backup files … A backup
> file is logged as an **error**, which is the level every other error shares and so
> cannot be capped separately, and which gives the whole run a nonzero exit status.

Each half is individually true, and the contrast they are arranged into is false. A
dot-underscore file also gives the run a nonzero exit status: `pdslogger`'s
`dot_underscore()` logs under the level *name* `'dot_'`, whose *value* is
`logging.ERROR`, and `PdsLogger.summarize()` classifies by value, not by name.

Measured — one `dot_underscore`, one `ds_store` and one `invisible` message in one
level, nothing else:

```
close() -> (0, 1, 1, 3)   # (criticals, errors, warnings, total)
```

One error, contributed by the dot-underscore line. The paragraph the correction
replaced was wrong in a different way (it said all three kinds have their own level);
the replacement fixed that and put a false consequence in its place.

### D11 — `_indexshelf_common.py:711-713` (`run_index_main`). *Missed by the first read.*

> This driver records no log directories, so a superseded index shelf is not
> versioned anywhere

The "so" is false. Nothing anywhere in `_indexshelf_common` calls `_shelf_common.
move_old` — `write_indexdict` opens the file and overwrites it. Populating `LOGDIRS`
would change nothing. `write_indexdict`'s own docstring (`:161-163`) gets this right by
giving both reasons; this one keeps only the reason that is not operative. Present
verbatim at `5b3cd2a` (under the heading "Two consequences of the third reason"); the
correction rewrote the heading around it and left the clause standing.

---

## `Raises:` contracts with hazards no entry covers

### R1 — `_common.setup_run` (`:344-366`). *Missed by the first read.*

Documents `SystemExit` only. `_common.py:372` is
`logger = pdslogger.PdsLogger(spec.logname)`, and `PdsLogger.__init__` raises
`ValueError(f'PdsLogger {name} already exists')` when a logger of that name is already
registered in the process. Measured, in one process, calling `setup_run` twice for the
same spec:

```
ValueError: PdsLogger pds.validation.archives already exists
```

Since all three drivers begin at `setup_run`, and since both flavours of a tool share
one `logname` (`pdsarchives` and `pds4archives` are both `pds.validation.archives`), two
tools of the same kind cannot both be driven from one process. That is a third-party
call raising a non-`raise` exception, which is exactly what the contract is for.

### R2 — `_common.run_main` and `_shelf_common.run_selection_main`. *Missed by the first read.*

Both document `SystemExit` only, and both call something that raises otherwise, before
the `try`:

* `run_main` (`_common.py:497`) — `spec.pdsfile_cls.from_abspath(path)` on an existing
  path outside any holdings tree raises `ValueError`/`OSError`.
* `run_selection_main` (`_shelf_common.py:572`) — `resolve_holdings_paths()`, whose
  *own* `Raises:` documents
  `ValueError` from `from_abspath()` and `OSError` "from the first `from_abspath()`
  call". Neither reaches `run_selection_main`'s contract, which mentions only
  "SystemExit … from the two path helpers on a path they reject."

---

## Claims I could not settle either way

1. `_indexshelf_common.py:16-17` — "Nothing in this package reads the ``.py`` file; it
   is there to be read by a person or by something outside the package."
   I verified that nothing under `src/pdsfile` **opens** the index shelf sidecar.
   `_shelves.py:472` does open a `.py` sidecar, but only under `if shelf_type ==
   'info'`, so it is the info shelf's, not the index shelf's. `pds3/
   shelf_consistency_check.py:92` inspects `.py` *names* inside a `shelves/index/` tree
   and treats anything else as extraneous — it never opens them, and the tree it walks
   is not the `_indexshelf-<category>/` layout `indexshelf_abspath` builds today.
   Whether name-level inspection counts as "reads" is a judgement I cannot make for the
   author.
2. `_common.py:43` — "a logger wired to the tool's log roots" (plural). `setup_run`
   wires handlers at one directory, `<args.log>/<progname>`, and only when `args.log` is
   truthy; the second, parallel place is never wired there. Whether "log roots" is meant
   loosely enough to be true I cannot tell.
3. `_common.py:169` — "Read twice per run". With N targets and a log root configured the
   attribute is read `1 + 2N` times, and with no log root `2N`. Read as "in two places"
   it is true; read as a count it is false. The correction sharpened the sentences
   around it ("once at the log root", "again per target") without resolving it, which
   makes the count reading more inviting than it was.

---

## Code defects (reported, not fixed)

1. **`pds3/pdsarchives.py:240`** — `log_suffix='_links'` on the PDS3 archive tool. Every
   other spec names its own kind (`_md5`, `_info`, `_links`, and `_archives` on
   `pds4archives`). PDS3 archive runs therefore write
   `<volume>_links_<time>_<task>.log`. Identical at `80f5e52`, so pre-existing, not
   introduced here.
2. **`pds3/pdslinkshelf.py` and `pds4/pds4linkshelf.py`, the repair loop** —
   `info.remove_path()` is called speculatively and its mutation is never undone when no
   repair is found, so the link is afterwards resolved against its basename alone and
   can resolve to the wrong file. Measured on VG_2801: `SOFTINFO.TXT` record 24 was
   written `OAL/AAREADME.TXT`; the shelf records the target as
   `…/VG_2801/AAREADME.TXT`, the volume-root file. This is the mechanism behind D1–D3.
3. **`_indexshelf_common.py:528`, `_linkshelf_common.py:942`** —
   `shelf_path.replace('.pickle', '.py')` replaces every occurrence rather than the
   extension. Harmless for the paths built today.
4. **`_indexshelf_common.index_targets`** — the top-level `metadata` directory is
   rejected, because the test is `'/metadata/' not in path` and
   `os.path.abspath('…/holdings/metadata')` carries no trailing slash. Measured:
   `index_targets(SPEC, ['<holdings>/metadata'])` prints "Not a metadata directory" and
   exits 1. The docstring describes the test accurately, so this is a code observation.
5. **`_common.py:429-435`, the `LOGDIRS` comment** — "any other tool that versions a
   file does it in its own `main()`." No other tool does. `set_log_dirs` is called only
   at `_common.py:511` and `_shelf_common.py:595`, and every `move_old` caller is one of
   the eight tools those two drivers serve. Identical at `80f5e52`.

---

## The checker, `critiques/pr-30a/check_spec_readers.py`

It runs clean — `0 findings over 21 fields`, exit 0 — and I re-derived its map
independently; the map it produces is right. Its weakness is not accuracy but scope, and
the answer to "can it pass while the map is wrong" is yes, in five ways.

1. **It checks attribution, never assertion.** D5 and D6 both live inside the
   `handler_factories` entry, which the checker scores as fully correct: the entry names
   `setup_run()`, `run_main()`, `_shelf_common.run_selection_main()` and
   `_indexshelf_common.run_index_main()`, and all four do read the field. Everything the
   entry then says about *where* and *how often* they attach is outside the gate. The
   gate's own docstring is candid that S2 works at module granularity, but that is worth
   restating as: the entries the gate protects are exactly the entries whose interesting
   content it does not read.
2. **S2 is satisfied by one named reader per module.** `pdsfile_cls` is read by nine
   functions across five modules; the entry names four and is silent about
   `_linkshelf_common.validate_links`, `_linkshelf_common.write_linkdict` and
   `_shelf_common.expand_selection_targets`. `logname` is read by twenty functions and
   the entry names four. An entry can therefore name the reader that supports its story
   and stay silent about the reader that would contradict it, and pass.
3. **Bare documented names are not unique references.** `matches()` accepts a dotless
   name against a function of that name in *any* module. This tree has same-named
   functions across modules — `link_targets` in `_linkshelf_common`, `pds3/pdslinkshelf`
   and `pds4/pds4linkshelf`; `initialize`/`reinitialize`/`validate`/`repair`/`update` in
   all ten tool modules — so a bare `run_main()` or `validate()` in an entry is matched
   loosely.
4. **The reader detector is a name filter that today's code happens to satisfy.**
   `derived_readers` records only `ast.Attribute` nodes whose `.value` is an `ast.Name`
   in `('spec', 'SPEC')`. A field read through `s = spec; s.unit`, `self.spec.unit`,
   `getattr(spec, name)`, or a `dataclasses.replace()` copy bound to another name is
   invisible, and S2 then does not fire for that module — silently, because S3 fires
   only when a field is read *nowhere*. No such read exists today, so the gate is
   currently resting on a property of the code rather than checking one.
5. **`CALL_RE` requires literal `()`, so the parenthesis convention is one-directional.**
   The docstring makes parentheses mean "this reads the field", which S1 enforces. The
   converse — an entry that names a genuine reader *without* parentheses, as the
   `logname` entry now does for `read_links` and `move_old` — is never checked. Those
   two are correct as written (neither reads `logname`; verified by AST over all 22
   functions in the six modules that take a `logger`), but nothing in the gate would
   have caught it if they weren't.

One suggestion that is cheap and would close (3) and part of (2): require every
documented reader token to be module-qualified, and report an S2 finding per *function*
rather than per module for fields read in three or fewer places.
