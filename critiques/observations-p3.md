# Observations — after the merge (P3)

Open observations to file as issues and fix after the merge. Nearly all are pre-existing defects found by reading code closely while moving or documenting it, not defects the port introduced. Fixing them is a separate project from finishing the port.

## Correctness

### 3999. `preload()` does not re-root an already-preloaded class, on either flavor

**A second `preload()` call is ignored for the purpose of resolving paths, so a caller
that points the class at a different holdings tree keeps resolving into the first one --
including for paths that lie inside the second.** Measured on both classes, by preloading
a real root, preloading a temporary copy, and then resolving a path that exists only in
the copy:

| | `root_` of a path inside the temporary tree | derived write path |
|---|---|---|
| `Pds4File` | the **real** root | `<real>/archives-bundles/<set>/<set>.tar.gz` |
| `Pds3File` | the **real** root | `<real>/archives-volumes/COUVIS_0xxx/COUVIS_0001.tar.gz` |

`from_abspath()` is given an absolute path under the temporary tree and returns an object
whose `root_` is the real tree, and every derived path -- `archive_paths()`,
`archive_path_and_lskip()`, the checksum and shelf builders -- follows `root_`. So a
caller that believes it has isolated itself has not.

The two flavors differ only in how loudly they fail when the second tree is incomplete.
`Pds3File.preload()` reads `_volinfo` and raises `FileNotFoundError` if it is absent,
which at least stops the caller; `Pds4File.preload()` has no such requirement and returns
normally, so the misdirection is silent.

**What it cost, so the risk is not theoretical.** A test that built a temporary holdings
tree, preloaded it, and called `write_archive()` wrote an 80 MB archive into the shared
PDS4 holdings on the machine where that tree is writable, and failed four CI jobs with
`PermissionError` where it is not. The failure was the lucky outcome. `tests/holdings_maintenance/`
now refuses the write at the point of the call: `readonly_roots.install()` wraps `open`
and the `os` mutators and rejects any target inside a real root, and a tool subprocess
installs the same guard from a `sitecustomize.py` on its `PYTHONPATH`. It was a walk of
both roots first. Measured against a 154 s baseline with no guard at all: walking around
every test cost 52 s, around every module 4 s, and the interception nothing detectable.
Either walk also grows with the size of the holdings, which the interception does not. The guard is a backstop rather than a fix, because
the class still resolves the wrong root.

Consumers preload too. `rms-viewmaster` preloads with a memcache port, and anything that
preloads twice in one process -- a long-running service pointed at a new tree, a script
that switches roots -- inherits this.

**Owner: a future preload PR. Whether the second call should re-root, raise, or be
documented as ignored is a design decision, not an obvious bug fix: re-rooting would
invalidate every cached object built against the first root.**

### 4000. 17 pre-existing bugs/quality issues in the holdings-maintenance tools

**17 pre-existing bugs/quality issues in the holdings-maintenance tools** (1
Critical, 6 Major, 10 Minor) surfaced when PR-06 moved the tools into the
package. None introduced by the move. Captured in full in
`critiques/coderabbit-findings.md` — to be addressed in a maintenance-tools
quality pass (with tests), issue #82, not in a mechanical move PR.

### 4001. `--quiet` prints nothing at all once a log root is configured

**`--quiet` prints nothing at all once a log root is configured.** The flag only
skips `logger.add_handler(pdslogger.stdout_handler)`; the run's own opening `HEADER`
and closing `SUMMARY` lines still reach the terminal, but only as `pdslogger`'s
fallback for a record with no handler anywhere in its ancestry. `--log` or
`PDS_LOG_ROOT` attaches the spec's file handlers at that same outermost level, so
the fallback stops firing and the terminal goes silent. Measured: the same
`pdschecksums --validate --quiet` printed 6 lines with no log root and 0 with one,
by either route. Whether an operator wants a `--quiet` run to be visible at all is
a design question, but it should not depend on an unrelated flag. The guide states
both behaviors. **Owner: whoever next touches the driver's handler setup.**

### 4002. `_get_shelf` discards the exception it is reporting

**`_get_shelf` discards the exception it is reporting.** `_shelves.py`'s
`_get_shelf` raises `OSError(f'Unable to open pickle file: {shelf_path}')`
inside its handler without `from`, so the underlying `UnpicklingError`/`EOFError`
is the new exception's `__context__` rather than its cause.

**Half of this is closed.** The entry was written against
`except Exception as e`, and named two findings: the unused `e` (`F841`) and the
missing `from` (`B904`). PR-23 dropped the binding — the handler now reads a bare
`except Exception:` — so the `F841` is gone and `_shelves.py`'s `per-file-ignores`
entry carries `B904` alone (`pyproject.toml:287`, "x1"). Re-measured at head with
the project configuration and `lint.per-file-ignores = {}`, `--select F841,B904`
over the module reports one finding, the `B904` at `_shelves.py:343` — identical
under the `PATH` ruff 0.15.7 that `pyproject.toml:176` names and under the venv's
0.15.22. The class also moved from `IOError` to `OSError`, which is the
same class under its Python 3 name. The method's own `Raises:` section
(`_shelves.py:317-323`) now describes the residual state exactly, so what is left
is a deliberate, documented gap rather than an oversight.
**Owner: whoever decides between `from err` and `from None` here** — the ratchet
comment records that both change the traceback, which is why PR-23 stopped at the
binding.

### 4003. `_indexshelf_common.load_indexdict()` lets an `EOFError` escape unlogged

**`_indexshelf_common.load_indexdict()` lets an `EOFError` escape unlogged.** A
zero-length shelf file -- what an interrupted or truncated write leaves -- raises
`EOFError` out of `pickle.load`, and `except pickle.PickleError` does not catch it,
so it is the one failure in that function that is neither logged nor converted.
`_linkshelf_common.load_links()` does not have the hole; it catches
`(Exception, KeyboardInterrupt)`. Found by round 1 and measured against a real table
with the shelf path redirected. PR-30a documents it in `Raises:`.
**Owner: PR-30b or a later maintenance-tool PR.**

### 4004. `_recache()` silently downgrades a permanent cache entry to an expiring one

**`_recache()` silently downgrades a permanent cache entry to an expiring
one.** `preload` stores the top-level category entries with `lifetime=0`, so
they never expire. Any lazy property that fills in and then calls
`self._recache()` re-stores the object with `lifetime=None`, which
`DictionaryCache.set()` resolves through `cache_lifetime_for_class` to a
finite value — 7 days for a category object. Measured on `rewrite` @
`807956a`, i.e. *before* PR-15: reading `description` or `iconset_closed` on
the `volumes` object already flips its cache entry from permanent to
expiring. PR-15's `html_path` fix adds `html_path` to that set (14 entries in
a full walk of the limited holdings copy), which is why this is recorded
here rather than earlier — it is pre-existing behavior of the property
pattern, not something the fix introduced, and `MemcachedCache` is unaffected
because its `set()` preserves a previously-defined lifetime. One further
consequence: a downgraded entry also joins `DictionaryCache.keys`, the
trimmable set, so a process that ever exceeds `limit + slop` (220,000) could
evict a category entry — previously impossible for a `lifetime=0` entry.
Whether a long-running process should be able to expire a category entry at
all is a cache-design question for issue #77 phase "b". **Owner:** phase "b".

### 4005. `_shelf_common.next_version_dest()` has no upper bound and no lower guard

**`_shelf_common.next_version_dest()` has no upper bound and no lower guard.**
Measured: with `_v001` through `_v999` present it returns `_v1000`, and with
`_v1000` present as well it returns `_v1000` again, because the `_v???` glob matches
exactly three characters and cannot see a four-digit name -- so `move_old()` then
overwrites the previous `_v1000` silently. Separately, an empty extension makes the
version slice `path[-3:0]`, which is `''`, so the first path the glob matches raises
`ValueError` out of `int()`; with no match it is harmless. Both are documented in
the docstring, neither is fixed. **Owner: a later maintenance-tool PR.**

### 4006. `all_versions` stores `self.abspath` for its own rank without testing it

**`all_versions` stores `self.abspath` for its own rank without testing it.** The
dictionary is seeded with `{self.version_rank: self.abspath}` before anything is
globbed, so an object with no absolute path writes None into `_all_version_abspaths`,
on itself and on every version it finds. The next call takes the remembered-paths
branch and passes that None to `cls.from_abspath()`. A merged directory does not reach
it -- the glob is rooted at a None `root_` and raises TypeError first, which is what
`all_version_abspaths`' docstring records -- so the reachable case is an object built
from a logical path no holdings directory holds.
**Owner: a future pdsfile PR.**

### 4007. `associated_parallel` caches its answer on a different object than the one it was called on

**`associated_parallel` caches its answer on a different object than the one it was
called on.** The caching closure captures the *variable* `self`, which the method
rebinds to this file's latest version whenever the requested volume type differs from
this file's. Both the initialization of `_associated_parallels_filled` and every write
to it then land on that object, and the write-back to the shared cache stores that
object. Verified by running: after two cross-type lookups on a `_v2` bundle, the
dictionary held four entries on the latest-version object and the object called on had
none. So a repeat call on the original object re-does the work. **Owner: a future
pdsfile PR.**

### 4008. `cassini_iss.py`'s two bundles claim the same archive name for one clock block

**`cassini_iss.py`'s two bundles claim the same archive name for one clock
block.** The cruise bundle's archive names are built over `range(29, 46)` and the
Saturn bundle's over `range(45, 89)`, so both produce a `*_145xxxxxxx.tar.gz`.
The module's header comment states the same overlapping bounds, so it may be
deliberate; the `cassini_iss` bundle set is not in this holdings copy, so it could
not be settled here. **Owner: whoever can read a complete PDS4 holdings tree.**

### 4009. `childnames` on an index table caches an `info_basename` derived from a half-built child list

**`childnames` on an index table caches an `info_basename` derived from a half-built
child list.** The index branch calls `sort_basenames(childnames)` with the class
defaults, whose `info_first` threshold makes the sort read `self.info_basename`, which
reads `self.childnames` -- and at that moment `_childnames_filled` still holds the
pre-index list, which for a table is empty. The `_info_basename_filled` that gets
stored and `_recache()`d was therefore derived from the wrong list, and it is not
recomputed afterwards.

Measured on a 3,745-row index: reading `childnames` fills `_info_basename_filled` with
`'COISS_2001_index.lbl'`, which is the answer the *label* rules give and happens to be
right, so the defect is currently invisible. It would not be for a table whose info
basename depends on its own children.
**Owner: a future pdsfile PR.**

### 4010. `find_selected_row_key` has two ordering and type defects

**`find_selected_row_key`'s invalid-flag guard raises `TypeError`, not the
`ValueError` it names.** The statement is
`raise ValueError(f'Invalid flag "{flag}"' % flag)`: the f-string is already
interpolated, so `%` is applied to a string with no conversion. Verified by running
with `flag='bogus'`: `TypeError: not all arguments converted during string
formatting`. Which exception comes out depends on the caller's own text -- a flag
containing `%s` produces the intended `ValueError`, and one containing `%d` produces
a `TypeError` from the conversion instead. The docstring documents all three cases.
**Owner: a future pdsfile PR** -- drop the `% flag`.

**`find_selected_row_key`'s empty-flag return sits ahead of the ambiguity check.**
The `if flag == '': return selection` arm comes before
`if len(child_keys) > 1: raise OSError('Index selection is ambiguous')`, so under the
empty flag an ambiguous selection is accepted as a literal row key rather than
reported. That is the flag `_local_fs.os_path_exists` uses for an index-row path, so
an ambiguous path is answered by building a row that does not exist. It may be
deliberate, since the empty flag means "do not fail"; nothing says so.
**Owner: a future pdsfile PR.**

### 4011. `from_logical_path` skips `must_exist` whenever the deepest cached ancestor has no absolute path

**`from_logical_path` skips `must_exist` whenever the deepest cached ancestor has no
absolute path.** The guard is `if ancestor and ancestor.abspath:`
(`pdsfile.py:1752`), and the fallback below it calls `from_abspath()` with literal
defaults. Merged category directories are permanent cache entries and have no
absolute path, so a preloaded tree takes the fallback for any path whose bundleset
entry has expired or been trimmed. Verified by running: after deleting the
`volumes/coiss_2xxx` cache entry,
`Pds3File.from_logical_path('volumes/COISS_2xxx/NOPE_0001', must_exist=True)`
returns an object rather than raising, and that object's `exists` is False. This is
the same class of defect as observations 4039 and 4039 -- an argument accepted and dropped
-- but here it is conditional on cache state, so it is not reproducible from the
signature alone. **Owner: a future pdsfile PR.**

### 4012. `get_permanent_values` raises `AttributeError` on a dictionary cache

**`get_permanent_values` raises `AttributeError` on a dictionary cache.** Its success
path logs `len(cls.CACHE.permanent_values)`, and `permanent_values` exists only on
`MemcachedCache` -- verified: a `DictionaryCache` has no such attribute. `preload()`
only calls the method when the memcached port is truthy, so the guard exists, but it
is in the caller and the method's own signature and docstring implied none. The
docstring now states the restriction. **Owner: a future pdsfile PR.**

### 4013. `GO_0xxx`'s six description rules never fire, for three reasons

**Six of `GO_0xxx.py`'s description rules are one path component short and never
fire.** `volumes/\w+/RAW_CAL`, `volumes/\w+/GOPEX`, `volumes/\w+/EMCONJ` and
`volumes/\w+/(MOON|EARTH|VENUS|IDA|GASPRA|SL9)` need a second `\w+` to reach a
real logical path such as `volumes/GO_0xxx/GO_0002/RAW_CAL`, because `\w` does
not span a slash; two `REDO` rules need a separator that the real names do not
have. All six return None at runtime and the directories they name fall through
to the generic "Directory". **Owner: whoever next touches `GO_0xxx.py`.**

**`GO_0xxx.py`'s six dead description rules fail for three different reasons, not
one.** Four are a path component short: `volumes/\w+/RAW_CAL` and its siblings need a
second `\w+` to reach `volumes/GO_0xxx/GO_0002/RAW_CAL`. The fifth,
`volumes/\w+/GO_00(0\d|1[0-6])\w+/REDO`, has the right number of components and fails
on the mandatory `\w+` after the volume number. The sixth,
`volumes/\w+/GO_00(1[789]|2\d)REDO`, has no slash before REDO and is looking for a
directory literally named "GO_0018REDO". a since-resolved observation recorded these as one mechanism;
this amends it. Owner: whoever next touches `GO_0xxx.py`.

### 4014. `html_path` raises `IndexError` on an empty merged category

**`html_path` raises `IndexError` on an empty merged category.**
`pdsfile.py`'s `html_path` handles a merged directory (`self.abspath is
None`) with `self.child(self.childnames[0]).html_path`, which indexes an
empty list whenever a category is present in the preload but has no
children. Measured, not hypothesized: **36 of the 1,910 objects** in PR-15's
bug-1 probe do exactly this against the limited holdings copy — every
category that copy does not populate (`archives-bundles`, `bundles` for
Pds3File, `volumes` for Pds4File, the `checksums-archives-*` set, …). The
behavior is identical before and after PR-15, which is why the probe's
before/after comparison is unaffected. The code's own comment already calls
the approach fragile ("Not a great solution but it usually works … This
issue will probably never come up"), so this is a known-shaky path rather
than a surprise; what is new is the measurement of how often it fires.
Fixing it means deciding what a childless merged category's URL *is*, which
is a behavior decision outside PR-15's enumerated list. **Owner:** phase "b"
or a future `pdsfile.py` PR.

### 4015. `iconset_for` raises unless a particular icon happens to be loaded

**`iconset_for`'s terminal lookup assumes an `UNKNOWN` icon set exists.**
`pdsviewable.py`'s `iconset_for` ends with `ICON_SET_BY_TYPE[icon_type,
is_open]`. PR-15 made the priority comparison key on the requested open
state, so any icon type that *wins* the comparison necessarily has a set
under that key and the lookup cannot raise for a winner. The remaining case
is the starting value: if `load_icons()` was never called, or was called on a
tree with no `document_generic` icon, `('UNKNOWN', is_open)` is absent and
the function raises `KeyError` instead of returning anything. That shape is
pre-existing — it is only reachable at all now that the function no longer
raises `NameError` first — and turning it into a graceful return is a new
behavior, not a bug fix. **Owner:** whichever PR next revisits the icon path.

**`iconset_for` raises `KeyError` unless a `document_generic` icon has been loaded
for the open state being asked for.** The fallback type `UNKNOWN` is never checked
for existence -- `_priority_of_icon_type` answers 0 for a missing key rather than
excluding the type -- so the final `ICON_SET_BY_TYPE[icon_type, is_open]`
(`pdsviewable.py:1003`) can fail on the fallback. Verified by running: after loading
a tree holding only `document_cube.png`, both `iconset_for` on a file whose icon
type is `TABLE` and `iconset_for([])` raise `KeyError: ('UNKNOWN', False)`. The
failure is not confined to a caller who forgot to load icons; it reaches a caller
who loaded a partial set. **Owner: a future pdsviewable PR.**

### 4016. `is_preloading()` reads a cache key that nothing in the package ever writes

**`is_preloading()` reads a cache key that nothing in the package ever writes.**
`_preload.py:164` is `return cls.CACHE.get_now('$PRELOADING')`, and `$PRELOADING`
appears nowhere else in `src/` or `tests/`. The call therefore answers `None` for
every caller, which reads as "not preloading" and cannot become anything else
without an external writer. The name is public: it is re-exported by
`preload_and_cache` and by `pdsfile.pdsfile`. Either `preload()` should set the key
around its work or the function should go; both are decisions. `_preload.py` belongs
to PR-29a, so its own docstring is not written here. **Owner: a future preload PR.**

### 4017. `label_basename`'s stem is the empty string for a basename with no extension

**`label_basename`'s stem is the empty string for a basename with no extension.**
`rootname = self.basename[:-len(self.extension)]`, and `len(self.extension)` is zero
for a name the split rules give an empty third part, so the slice is `[:-0]`, which
Python evaluates as `[:0]`. The guessed label names are then the bare label extensions
-- `.lbl` and `.LBL` for PDS3 -- rather than the basename with a label extension. The
`PRODUCT_LBL_BASENAME_WO_EXT` rule short-circuits this wherever it answers, and a
directory is the common case that reaches it, for which no label exists either way. The
docstring states the behavior.
**Owner: a future pdsfile PR.**

### 4018. `link_targets()` filters a unit set's non-directory children out of the target list, where the…

**`link_targets()` filters a unit set's non-directory children out of the
target list, where the two link shelf `main()`s kept them in and skipped them
in the loop.** The blank line between targets is emitted when there is more
than one target, so a unit set holding one unit directory plus a readme file
loses that blank line.

**Measured over the wrong population first.** The original count here — "0 of
54 unit sets have a non-directory child, so no line of the transcript moves" —
covered `volumes`, `calibrated` and pds4 `bundles`, and left out `metadata`,
which is one of the three voltypes a link shelf run is pointed at
(`re_validate.py:44`, and `update_holdings_for_new_metadata.sh:40` runs
`pdslinkshelf --initialize` on `metadata/$VOLSET`). Re-measured over every
category `link_targets` accepts, on both roots: **158 unit sets, 96 with a
non-directory child, 17 where the blank line moves** — every `metadata/*` set
carries an `AAREADME.txt`, and 17 of them hold exactly one unit directory
beside it. So this happens on 17 real targets of a documented workflow in this
tree, not hypothetically.

PR-27 added a 27th transcript scenario for a metadata unit set and enumerated
the two lines it produces as change 13 in `critiques/pr-27-validation.md`. This
is the same trade `pdsarchives.archive_targets()` has made since PR-25.
**Owner: recorded, not open.**

### 4019. `local_basenames[k]` is indexed with a loop variable that escapes two nested loops and a…

**`local_basenames[k]` is indexed with a loop variable that escapes two nested loops
and a directory boundary**, in `pdslinkshelf.generate_links()` and
`pds4linkshelf.generate_links()`. It cannot fire today: the guard above it,
`if obvious_label_basename:`, is truthy only on an iteration that set `k`. It is
recorded because the value being formatted is `obvious_label_basename`'s and the index
is redundant. Found by round 4.
**Owner: a later maintenance-tool PR.**

### 4020. `local_viewset` stores None where every sibling stores False, and that object re-derives forever

**`local_viewset` stores None where every sibling stores False, and that object
re-derives forever.** `PdsViewSet.from_pdsfiles()` returns None when nothing it was
handed is displayable, and `PdsViewable.from_pdsfile()` raises ValueError -- which
`from_pdsfiles` swallows -- for any object whose width is zero. An existing file whose
name is viewable and whose recorded width is zero, which is what
`_repair_width_height` writes for an image PIL could not open, therefore stores None.
The guard at the top of the property is `is not None`, so it never fires and the whole
derivation runs on every access.

`viewset` has the guard `local_viewset` lacks: it converts a None answer to False
before storing. The two properties are written to look symmetric and are not.
Measured: forcing the shape to `(0, 0)` on a real preview file makes `local_viewset`
return None twice with the slot still None. A scan of 2,086,994 viewable entries in
the preview info shelves found no zero-width entry, so reaching it in this tree takes
a PIL failure. The docstring states it.
**Owner: a future pdsfile PR.**

### 4021. `new_merged_dir` leaves seven storage slots unset, and the properties behind them do not…

**`new_merged_dir` leaves seven storage slots unset, and the properties behind them
do not degrade gracefully.** Unset: `_iconset_filled`, `_volume_info_filled`,
`_all_version_abspaths`, `_html_path_filled`, `_description_and_icon_filled`,
`_associated_parallels_filled` and `_index_pdslabel`. `new_index_row_pdsfile`, the
other constructor of the same shape, sets all of them. Verified by running on
`Pds3File.new_merged_dir('volumes')`: `html_path` and `url` raise
`IndexError: list index out of range`, `all_version_abspaths` raises `TypeError`
because `root_` is None (`pdsfile.py:742`), and `iconset_open` reads the icon
directory out of the holdings tree, which is the one thing a merged directory is
built never to do. **Owner: a future pdsfile PR.**

### 4022. `pds4archives` on a bundle raises `RuntimeError: No active exception to reraise`

**`pds4archives` on a bundle raises `RuntimeError: No active exception to
reraise`** — the "no archive paths resolved" branch is a bare `raise` outside
any `except` (`pds4archives.py:214-218`). Reached whenever the tool is pointed
at a bundle in a bundle set whose archives are defined at the set level.
Pinned by `test_pds4_archives.test_initialize_on_a_bundle_raises`.
**Owner: PR-25.**

### 4023. `pds4indexshelf` cannot shelve any PDS4 metadata table that exists today

**`pds4indexshelf` cannot shelve any PDS4 metadata table that exists today.**
Both PDS4 bundle sets fail, one with `FileNotFoundError` and one with
`ValueError: row count mismatch`. Pinned by
`test_pds4_indexshelf.test_initialize_cannot_read_a_pds4_index`.

**Re-scoped by PR-27, which corrected the diagnosis and left it open.** This
entry said `pdstable.PdsTable` is "a PDS3 detached-label reader". It is not:
`PdsTable.__init__` dispatches on `is_pds4_label(label_file)` and builds a
`Pds4TableInfo` for a PDS4 label. There is no wrong reader to replace, and the
two failures are two different things, neither of them in this tool.

* `uranus_occs_earthbased`: the metadata `.csv` files have **no label at all**,
  so `label_abspath` is `''` and the read raises. Shelving them means deciding
  that a PDS4 index shelf is built from the `.csv`'s own header row instead of
  from a label -- a decision about the PDS4 metadata contract. It is also not
  enough on its own: `_index_rows.child_of_index()` builds
  `pdstable.PdsTable(label_file=self.label_abspath, ...)` to turn a shelved row
  number back into a row, so a shelf built without a label could not be read
  back. Any fix spans the tool and the core.
* `cassini_uvis_solarocc_beckerjarmak2023`: `PdsTable` parses its `.xml`
  correctly as PDS4, and the mismatch is real. The label declares an 885-byte
  header and 35 fields; the file's header line is 1,074 bytes and carries 41
  columns. `PdsTable` seeks 885 bytes in, lands inside line 1, and reads 42
  lines where the label says 41. That is a stale label -- a data repair, or a
  `pdstable` change, not a `pdsfile` one.

Corroborating: the PDS4 holdings root has no `_indexshelf-metadata/` directory,
so no PDS4 index shelf has ever been built here either.
**Owner: open -- a PDS4 metadata-contract decision plus a core change, not a
tool repair.**

### 4024. `pds4linkshelf.generate_links()` is case-sensitive in four places, in a function whose link…

**`pds4linkshelf.generate_links()` is case-sensitive in four places, in a function
whose link resolution is not.** All four defeat the label credit that is this tool's
one advantage over the pds3 scan.
- `local_labels = [f for f in local_basenames if '.xml' in f or '.lblx' in f]`
  collects a directory's labels by a lower-case **substring** test, so a label named
  `FOO.XML` is not among them and a `foo.xml.bak` is.
- the credit itself compares `link_text_of(info) == basename` exactly, so a label
  naming `FOO.DAT` does not credit a `foo.dat` on disk.
- a collection inventory is recognized by `basename.startswith('collection')` and
  `endswith('.csv')`, so a `COLLECTION_DATA.CSV` is never read, and every file in that
  directory is then treated as unlisted and its missing-label report suppressed.
- membership is `basename.rpartition('.')[0] in csv_basenames`, exact again.
Every extension test elsewhere in the same function upper-cases first. Found by
rounds 1, 2 and 4, each independently.
**Owner: a later maintenance-tool PR.**

### 4025. `pds4linkshelf.generate_links` iterates a shelved value without checking it is a list

**`pds4linkshelf.generate_links` iterates a shelved value without checking it
is a list.** In the "identify labels for files" loop, a value taken from
`linkinfo_dict` — which starts as a copy of `old_links` — is iterated and each
item's link text read. Every key that reaches that loop is filtered to the
`.xml`/`.lblx` files of the current directory, and every one of those is put
into `linkinfo_dict` with a list value by the loop above and keeps it through
the merge, so a string value is not a state this code can produce or read back.
Unreachable before PR-27 (`AttributeError` on `.linktext`) and unreachable
after it. What it would do after it depends on the string: iterating a `str`
yields one-character strings, so `info[1]` raises `IndexError` on every
character — but a value that was a longer sequence of longer strings would
return a character rather than raising, which is the worse of the two failure
modes and the reason this is written down. An `isinstance` guard would add a
branch no test can reach.
**Owner: open.**

### 4026. `pdsarchives.archive_targets()` raises `AttributeError` on a category-level path

**`pdsarchives.archive_targets()` raises `AttributeError` on a category-level path.**
A path with neither a volume nor a volume set above it, such as `<holdings>/volumes`,
makes `volset_pdsfile()` answer None and nothing checks it before `pdsdir.childnames`
is read. Reproduced against the test holdings: `AttributeError: 'NoneType' object has
no attribute 'childnames'`. `pds4archives.archive_targets()` cannot reach this, since
it returns the path itself.
**Owner: a later maintenance-tool PR.**

### 4027. `pdsdependency` emits its "Steps required" plan in filesystem-enumeration order

**`pdsdependency` emits its "Steps required" plan in filesystem-enumeration
order.** Each dependency rule does `abspaths = glob.glob(pattern)` with no
sort and then iterates it, so the steps a single rule contributes come out in
whatever order the directory happens to enumerate. `glob` does not sort, and
ext4 returns entries in a per-filesystem hash order, so the *same* tree yields
a different plan order on a different machine — which is exactly how this
surfaced: the tool tests passed against both holdings roots on the development
machine and failed on the CI runner, with the two cumulative-table steps
swapped and nothing else changed.

Not a correctness defect — the *set* of steps is identical and the plan works
in any order within a rule — but it makes the output unstable for anyone
diffing two runs, and it is the kind of thing a shared tool core should fix
once. **Owner: Phase 6** (`pdsdependency` stays standalone in PR-25, so
whichever PR touches it next): sort the glob results.

**PR-13 did not change the tool.** It stopped depending on the unspecified
order instead: the step-list golden is compared as a sorted multiset
(`support.check_golden(..., unordered=True)`), which still pins the exact set
and text of every step, while the twelve steps whose position the tool *does*
determine — those from rules whose glob matched a single path — are pinned in
exact order, so a rule reordering its messages still fails the test. When the
tool starts sorting, the test keeps passing and the golden stays valid.

### 4028. `pdsinfoshelf.repair()` logs "content is up to date" on the out-of-date branch

**`pdsinfoshelf.repair()` logs "content is up to date" on the out-of-date branch.**
Where the shelf and the walk agree but the holdings are newer, the first line written
is `!!! Info shelf file content is up to date` and the fourth is
`!!! Info shelf file is out of date %.1f days`. The two say opposite things about the
same run, and only the second is about the dates the branch was entered for.
Identical in `pds4infoshelf`. Found by round 3.
**Owner: a later maintenance-tool PR; changing either line moves log output.**

### 4030. `preload()` warns "Not a directory, ignored" and does not ignore it

**`preload()` warns "Not a directory, ignored" and does not ignore it.** The missing
branch has a `continue` and this one does not, so a category path that exists but is
not a directory falls through to `from_abspath(..., caching='all', lifetime=0)` and
is cached permanently and merged into the category-level merged directory's child
list. Nothing below it is walked, because the directory walker returns on its first
statement for a non-directory, so the cost is a bad entry rather than a traversal.
**Owner: a future pdsfile PR** -- add the `continue`.

### 4031. `re_validate --batch` fails on a path with a space and on no log root at all

**`re_validate` batch mode cannot handle a holdings root whose path contains
a space.** `volume_abspath_from_log()` recovers the volume path from a log's
first record as `parts[-1].strip().split(' ')[-1]` — the last
whitespace-separated token. A path with a space in it is silently truncated to
its final component.

This is not hypothetical on this machine: `/seti/opus/pdsdata/holdings`
resolves to a Dropbox path containing three spaces, and the tool intersects
each log's recovered holdings prefix against the **realpath** of the
command-line root. Measured at PR-25a's head, a log naming the resolved path
yields the prefix `rfrench@rfrench.org/Shared/Shared-OPUS/pdsdata/holdings`,
which matches nothing, so the missing-volume report stays silent whatever the
logs say. PR-25a's B2 fix had to be demonstrated against a synthetic
space-free holdings root for exactly this reason.

The fix is not obvious and is not PR-25a's: the log's first record is written
by `pdslogger` as `Re-validate <abspath>` with no quoting or delimiter, so
recovering the path reliably means changing what is written, which changes a
log format that older logs are already in. Anything that reads existing logs
has to cope with both.

**The same split has a second consequence, in the opposite direction.** Batch
mode holds the holdings roots twice: `resolve_holdings_paths()` returns the
canonicalized, deduplicated list, and that is what the missing-volume report
intersects against — but `get_volume_info()` is called over the raw
`args.volume` entries, so `holdings_info` and everything downstream of it carry
the path *as the user typed it*. Naming one root twice globs it twice, and the
abspath a batch run reports is not the abspath the report compares against.

Identical at PR-25a's base and head; that PR did not introduce it and did not
change it. Iterating the resolved list instead looks like a one-line fix and is
not one: on a machine where the holdings root is a symlink, the canonical path
is a different tree, and `Pds3File.from_abspath` has to recognize it as a
holdings root for `--batch-status` to print anything at all. Which of the two
forms is the right one to carry is the same question as the paragraph above,
and should be settled once for both.
**Owner: open.**

**`re_validate --batch` with no log root at all crashes with a `TypeError`.**
Batch mode reads the existing logs with `get_all_log_info(args.log)`, and
`args.log` is `None` when neither `--log` nor `PDS_LOG_ROOT` is set — that is
what `_common.resolve_log_root` leaves. `os.walk(None)` then raises
`TypeError: expected str, bytes or os.PathLike object, not NoneType`.

Measured at PR-25a's base and at its head, against a holdings directory with
an empty `volumes/`, with `PDS_LOG_ROOT` removed from the environment:

```
$ python -m pdsfile.holdings_maintenance.pds3.re_validate --batch-status <holdings>
base  rc=1  TypeError: expected str, bytes or os.PathLike object, not NoneType
head  rc=1  TypeError: expected str, bytes or os.PathLike object, not NoneType
```

Identical at both, so PR-25a neither introduces nor fixes it; it is recorded
because that PR's review is what found it. Interactive mode is unaffected — it
never reads the log root as a directory to walk.

Not obviously a one-line fix. Batch mode's whole scheduling model is "read the
logs, find what is stale", so with no log tree there is nothing to schedule
from and every volume looks unvalidated. Whether the right behavior is to
refuse with a message, or to treat it as "no logs yet" and validate
everything oldest-first, is a decision about how the launch daemon should
behave on a fresh install, not a defect with one obvious repair.
**Owner: open.**

### 4032. `remove_path()` is called speculatively and its mutation is never undone

**`remove_path()` is called speculatively and its mutation is never undone.** Both
link shelf tools look up a repair for a link, and where the link's text carries a
directory and the first lookup misses they call `LinkInfo.remove_path()`, which
rewrites both `linktext` and `linkname` to the basename **in place**, and try again.
When the second lookup also misses the loop moves on, and nothing restores the text.
The truncated text is then what resolves the link and what is shelved.

Measured by round 3, which instrumented `remove_path` and ran `generate_links` over
every volume of the test holdings that fit a 220-second budget: **493 volumes, 1,412
truncating calls.** VG_2801 alone shelves ten triples whose middle element is not
what the file says -- `GEOMINFO.TXT` wrote `DOCUMENT/POLES.TXT` and the shelf records
`POLES.TXT` -- and at least one resolves to the wrong file: `SOFTINFO.TXT` record 24
wrote `OAL/AAREADME.TXT` and the shelf targets the volume-root `AAREADME.TXT`.

This is why the PR's own prose could not settle on what the middle element of a
triple is: it is the text as written for most links and the basename for a link that
carried a directory and reached the repair table. **Owner: PR-30b, which documents
the two tools, or a later link shelf PR that may fix it.**

### 4034. `TranslatorByRegex.append()` discards the receiver when the argument is a null translator

**`TranslatorByRegex.append()` discards the receiver when the argument is a null
translator.** `X + NullTranslator()` returns the null and throws `X` away; `prepend`
mirrors it. Nothing in the rule modules currently adds a null on the right, so this is
latent -- but it is the same operator the `ASSOCIATIONS` merges depend on, and it is
what makes `ASSOCIATIONS['previews'] += <table>` a replacement rather than an append.
A reader of `+` would not expect either behavior. This lives in the `translator`
package rather than in this repository. Owner: whoever owns `translator`.

### 4035. `version_info`'s rank packing overflows, and its worked example is wrong

**`version_info`'s rank packing overflows once a version part reaches 100, and two
distinct versions then share a rank.** `_v1.100` and `_v2` both rank 20000, because
the rank is `major * 10000 + minor * 100 + micro` with nothing bounding the parts. Two
bundle sets of one stem on either side of that boundary would collide in the rank
dictionaries, and `all_versions()` would log "Duplicate version" and keep whichever it
saw first.

`version_info` also truncates a suffix past its third part, so `_v2.1.3` and
`_v2.1.3.4` share a rank and an id and differ only in the message. **That one is not
reachable through a path**, and round 4 is what established it: `BUNDLESET_PLUS_REGEX`
captures at most `_v[0-9]+\.[0-9]+\.[0-9]+`, so a fourth part never becomes a
`version_rank`. It is reachable only by calling the static method directly. The first
draft of this entry had the two the wrong way round, naming the truncation as the
collision mechanism and the arithmetic as an aside; `all_versions`' docstring made the
same mistake and both are corrected.

Measured, both are latent: a scan of every category directory of the holdings tree
computed the rank of every bundle-set suffix present and found no four-part suffix, no
part at or above 100, and no rank collision within any stem. The docstrings state both
limits. A fix changes what `version_info` returns for inputs it currently accepts, so
it needs a regression test of its own.
**Owner: a future pdsfile PR.**

**`version_info`'s worked-example comment is arithmetically wrong and is left alone.**
The comment above the `_v` branch reads `_v2.1 -> 201000` and `_v2.1.3 -> 201030`;
measured, `version_info('_v2.1')` is 20100 and `version_info('_v2.1.3')` is 20103. Only
the first line, `_v2 -> 20000`, is right. A docstrings-only PR does not touch comment
text, and the docstring immediately below it now states the formula correctly, so a
reader has both a right answer and a wrong one three lines apart. That is the argument
for deleting the comment rather than repairing it: the docstring already carries what
it was for.
**Owner: whoever next edits that function.**

### 4036. `version_ranks` returns `None` for a file that does not exist

**`version_ranks` returns `None` for a file that does not exist.**
`src/pdsfile/_properties.py`, in the `version_ranks` property: the
`if not self.exists:` branch assigned a **local** `version_ranks_filled = []`
where every sibling branch assigns `self._version_ranks_filled`, so the
instance slot stayed `None` and the property returned `None` rather than the
empty list the docstring promises ("a list of the numeric version ranks"). This
is the `F841` that `_properties.py`'s ratchet entry carried. PR-23 deleted the
dead local — behavior-identical, since nothing ever read it — and left a comment
at the site; it did **not** write the instance attribute, because that changes
what the property returns on an existing input. Same shape as observation 4049
(`repair_case`'s `found`). **Owner: phase "b" of issue #77.**

### 4037. A bundle the volume-info tables do not cover gets a description that is only the volume-type…

**A bundle the volume-info tables do not cover gets a description that is only the
volume-type prefix.** `description` prefixes the volume type where the table's
description does not already say it, and the fallback for an uncovered bundle is an
empty description, so the result is the prefix applied to nothing: `'Metadata for '`,
with a trailing space, and `icon_type` of `UNKNOWN`. Measured over 857 bundle and
bundle-set objects, five are uncovered, all under `metadata/RPX_xxxx_v1.0`.

The icon fallbacks do not rescue them either, and for a reason worth stating because it
is the opposite of what the code reads like: both are guarded on `icon_type is None`,
and the uncovered fallback supplies the string `'UNKNOWN'`, not None. The None case is
reached only where the table stores a blank icon column, which the preload converts.
`bundle_publication_date` makes exactly this None-versus-fallback distinction for its
own field and `description` does not.
**Owner: a future pdsfile PR.**

### 4038. Both `opus_prioritizer` implementations have two defects

**Both `opus_prioritizer` implementations sort tuples whose tie-break is a list of
PdsFile objects, and PdsFile has no ordering.**
`GO_0xxx.opus_prioritizer` builds `(priority, sublist)` pairs and calls `sort()`;
`NHxxxx_xxxx.opus_prioritizer` builds `(priority, code, sublist)` triples and does
the same. Where the leading elements tie -- two Galileo copies at one version rank
that are both reprocessed or both superseded, two New Horizons copies at one rank
with the same file code -- the comparison falls through to the lists, then to the
`PdsFile` objects inside them. `PdsFile` defines neither `__lt__` nor `__eq__`
anywhere in `pdsfile.py` or `_properties.py`, so that comparison raises `TypeError`.

The docstrings written here record it as a `Raises:` entry attributed to `sort()`,
which is the widened rule PR-29 established for an exception a `raise` statement
does not produce. Whether it is reachable in practice depends on the data: Galileo's
enumerated supersession list pairs one reprocessed image with one original, which
does not tie. **Owner: whichever PR next touches the prioritizers; the fix is a
third tie-break element, as `NHxxxx_xxxx` already has two.**

**Both `opus_prioritizer` implementations force the alternative heading's
default-selected flag to True.** `alt_header` is built with a literal `True` in its
fifth slot in `GO_0xxx.py` and `NHxxxx_xxxx.py` alike, so a superseded processing or an
alternate downlink is default-selected in OPUS whatever the original heading carried.
The docstrings written here record it. Whether it is intended is not recorded anywhere.
Owner: whichever PR next touches the prioritizers.

### 4039. Constructor options that are accepted and then dropped

**`PdsFile._from_absolute_or_logical_path` drops all four of its options.** The
signature is `(cls, path, fix_case=False, must_exist=False, caching='default',
lifetime=None)` and both branches call the constructor with those four names bound
to literals rather than to the arguments (`pdsfile.py:1950`, with the two calls at
`:1976` and `:1980`). Passing
`must_exist=True` therefore does not make the call insist on anything. Because the
literals equal the declared defaults, no caller passing defaults can tell; a caller
passing anything else is silently ignored. The docstring written here says the
options are dropped, which is accurate and is not the fix. **Owner: a future
pdsfile PR; forwarding them is a behavior change to a method with callers.**

**`PdsFile.parent` accepts `caching` and `lifetime` and passes neither on.** Both
branches call `from_logical_path` or `from_abspath` with `must_exist` alone
(`pdsfile.py:1639` and `:1643`), so the parent is built with whatever caching defaults
those constructors apply. Same shape as a since-resolved observation and same reason for not fixing it
here. **Owner: a future pdsfile PR.**

### 4040. Entry points that raise on inputs they are expected to handle

**`from_path` raises `UnboundLocalError` for a bundle name no preload recorded, and
`from_lid` inherits it.** The rank lookup at `pdsfile.py:2272` raises `KeyError` for
an unrecorded bundle name; the recovery block that follows searches the recorded
bundlesets for one whose pattern the name matches, and assigns `rank` only inside
`if bundleset.startswith(updated_bundleset_prefix):`. When no bundleset matches,
`rank` is never bound, and `:2306` reads it. The `except KeyError` at `:2312` does
not catch that. Verified by running against the real holdings tree with a preload:
`Pds3File.from_path('COISS_9999')` and `Pds3File.from_path('NOSUCH_2001')` both give
`UnboundLocalError: cannot access local variable 'rank'`, and
`Pds3File.from_lid('X:NOSUCH_0001:a:b')` gives the same. The bundle*set* branch
(`:2355`) does raise `KeyError`, so a caller guarding one of the two spellings is
protected and a caller guarding the other is not. Two smaller ones in the same
block: `bundlename.index('_')` at `:2277` raises `ValueError` for a bundle name with
no underscore, and the `[-1]` at `:2272` raises `IndexError` on an empty rank list.
**Owner: a future pdsfile PR.**

**`PdsFile.parent()` raises `ValueError` on a physical category directory.** The
branch test is `if logical_path in cls.CATEGORIES or not self.abspath:`
(`pdsfile.py:1638`). For a physical category directory the parent's logical path is
the empty string, which is not in `CATEGORIES`, and the absolute path is truthy, so
control reaches `from_abspath()` at `:1643` with the holdings directory itself --
which has no logical path, and which `logical_path_from_abspath` refuses. Verified
by running: `Pds3File.from_abspath('<holdings>/volumes').parent()` gives
`ValueError: ('Not compatible with a logical path: ', '<holdings>')`. The *merged*
category directory returns None as intended; it is the physical one that fails.
**Owner: a future pdsfile PR.**

**`from_path('')` hardcodes the PDS3 category.** Every other voltype default in
`from_path` uses `cls.BUNDLE_DIR_NAME`, which is `volumes` on `Pds3File` and `bundles`
on `Pds4File`; the empty-description branch assigns the literal `'volumes'`. Measured,
`Pds4File.from_path('')` returns a logical path of `volumes`, which is not a PDS4
category. The docstring describes what happens rather than what was meant, because
what happens is what a caller gets.
**Owner: a future pdsfile PR.**

**`index_pdslabel` parses a PDS4 index file as its own label, and raises.** The label's
path is guessed by replacing each index extension in this file's path with each label
extension. `str.replace` is a no-op when the substring is absent, so for a class with
more than one index extension the iteration for the extension the path does *not*
carry leaves the path unchanged and hands the index file itself to
`pdsparser.PdsLabel.from_file()`. `Pds3File` has one index extension and one label
extension and never reaches it; `Pds4File` has `('.csv', '.tab')` and
`('.xml', '.lblx')`.

Measured: every PDS4 index in the holdings copy raises
`SyntaxError: missing END statement in <the .csv itself>` out of the property. The
`except OSError` around the parse does not catch it. So the property does not return
None for a PDS4 index; it raises, and there is no path on which a PDS4 index label is
returned at all.

The fix is to skip the substitution where the path does not carry the index extension,
and to break out of both loops on success rather than the inner one. Both change what
the property returns for inputs it currently rejects, so it needs a regression test.
The docstring states the behavior and adds the `Raises:`.
**Owner: a future pdsfile PR.**

**`Pds4File.from_logical_path('bundles').description` raises `TypeError`.**
`pds4file/rules/__init__.py`'s `DESCRIPTION_AND_ICON` is the PDS3 table copied, and
its category-directory entries are the PDS3 ones: `volumes`, `calibrated`,
`diagrams`, `metadata`, `previews`, `documents`. There is no entry for `bundles`,
which is the one category directory a PDS4 reader needs, so nothing matches,
`_description_and_icon_filled` stays None and `_properties.py:1314` subscripts it.
`archives-bundles` and `checksums-bundles` fail the same way, while `previews`,
`metadata` and `diagrams` answer, and `Pds3File.from_logical_path('volumes')`
answers. **This is the only finding in either round that is a live crash rather than
a wrong or dead rule.** Owner: whoever next revises the pds4 default tables.

### 4041. Five defects in `load_icons`

**`load_icons` silently skips every JPEG icon.** The extension test is
`if ext.lower() not in ('.png', 'jpg'): continue` (`pdsviewable.py:872`) — the second
entry has no leading dot, and `os.path.splitext` always supplies one, so no file ever
matches it. The surrounding code plainly expects JPEGs: the nominal-size guess looks
for a `jpg-<n>` directory component sixteen lines above, at `:854`. Verified by running: a
directory holding `document_image.jpg` and `document_label.png` yields only the
`LABEL` icon set. Adding the dot would start loading files that are not loaded today,
which is a behavior change and not an executor's call. **Owner: a future pdsviewable
PR.**

**`load_icons` without a logger stores an unreadable image under the previous
image's dimensions.** The handler is `except Image.UnidentifiedImageError:` followed
by `if logger:`, and the `continue` sits inside that `if` (`pdsviewable.py:880-883`).
With a logger the file is reported and skipped; without one, execution falls through
to `(width, height) = im.size`, where `im` is still the last image successfully
opened. Verified by running: a corrupt `broken.png` beside a valid 50x50 file
produces a `BROKEN` icon set of 50x50 with the corrupt file's path and byte count.
The two-line fix is to dedent the `continue`, which changes what the no-logger path
does. **Owner: a future pdsviewable PR.**

**A second `load_icons` call does not replace the fallback open form of an icon
type.** A closed set is stored under `(icon_name, True)` as a stand-in for a missing
open form, guarded by `if (icon_name, True) not in ICON_SET_BY_TYPE:`
(`pdsviewable.py:930`). The dictionary it tests is module-global, so an entry left
by an *earlier call* blocks the write just as one left by this call does. Verified
by running: loading two directories in turn, each holding only
`document_label.png`, leaves `('LABEL', False)` and `'LABEL'` pointing at the second
directory's set and `('LABEL', True)` still pointing at the first's, checked by
object identity.

The scope is exactly that fallback. A directory read second that *does* hold a
`document_label_open.png` writes `('LABEL', True)` unconditionally at `:925` and
replaces the earlier entry -- verified the same way. So the stale mapping survives
only for a type whose later directory supplies no open icon of its own, and what
survives is an earlier *closed* set standing in for one. Since
`iconset_for(..., is_open=True)` reads that key, such a type goes on being drawn
from the old directory. **Owner: a future pdsviewable PR.**

**`load_icons`'s image-open failure handling has two more holes than a since-resolved observation
recorded.** a since-resolved observation covers the no-logger fall-through. Two further cases:

* If the *first* image the walk reaches is unreadable and there is no logger, `im`
  has never been bound, and `(width, height) = im.size` (`pdsviewable.py:885`)
  raises `UnboundLocalError` rather than mis-sizing anything. Verified by running
  against a tree whose only `.png` is a text file.
* Only `Image.UnidentifiedImageError` is caught (`:880`). A broken symlink, a
  missing file or a permission error propagates out of `load_icons` even with a
  logger. Verified by running: a broken symlink named `document_label.png` gives
  `FileNotFoundError` with a logger supplied.

**Owner: a future pdsviewable PR, together with a since-resolved observation.**

**`load_icons` strips `document_` and `folder_` from anywhere in an icon basename,
not just the front.** `key_base.replace('document_', '')` and the `folder_` line
after it (`pdsviewable.py:907-908`) are `str.replace`, which is not anchored.
Verified by running: `my_document_thing.png` supplies the icon type `MY_THING` and
`x_folder_y.png` supplies `X_Y`. A custom icon named for a folder in the middle of
its name gets a type its author would not predict. **Owner: a future pdsviewable
PR.**

### 4042. Five defects in `re_validate`

**`re_validate.report_missing_volumes()` reports trees the run was not asked about.**
The qualification test, `if not (holdings_abspaths & holdings_for_key): continue`, is
applied once for the whole key, and the loop below it then logs one "Missing volume"
error for **every** tree the key's logs name, filtered by nothing. Demonstrated with
one key holding two logs, one naming `/treeA/holdings` and one `/treeB/holdings`, and
a run validating `/treeA/holdings` alone: both errors are logged. In batch mode those
errors become the error mail, so an operator is told a volume is missing from a tree
this run never looked at. Found by round 1.
**Owner: a later maintenance-tool PR.**

**`re_validate` batch mode can validate one volume twice in one run.**
`find_modified_volumes()` builds the modified set as `holdings_modtimes -
log_modtimes`, a set of `(date, key)` pairs, and then maps each surviving key through
`holdings_dict`. Two holdings trees carrying the same volume at **different** dates
contribute two surviving pairs with one key, so the key appears twice in
`modified_keys` and the same path is looked up twice and scheduled twice.
`holdings_dict[key]` has already collapsed the two trees to whichever was seen last,
so the two schedule entries are identical and the run validates one path twice. Found
by round 1; it is the second half of observation 4031's "the same volume in two trees"
problem, seen from the scheduling side rather than the reporting side.
**Owner: a later maintenance-tool PR; belongs with 107.**

**`re_validate --batch` ends nonzero when its mail relay is unreachable, defeating the
one guarantee it is built around.** The tool exits 0 whatever a validation found,
because a nonzero status would cancel the launch daemon that schedules it. But
`send_email()` is called from the same `finally` block that reaches `sys.exit(0)`, and
nothing catches what it raises: with `send_email` stubbed to raise `OSError`, the
exception propagates out of `run_batch()` and out of `main()` and the process ends in
a traceback with status 1. So the status is insulated from what the run found and not
from whether the report could be sent. Found by round 1.

The exit codes of every other program were standardized on 2026-08-15 -- 0 for a run
that logged no fatal and no error, 1 for one that did -- and **this program was
deliberately left out of that**, for the reason above: its status is a signal to the
scheduler, not a verdict on the data. Whoever fixes the mail-relay path should keep
that property rather than fold this tool into the general rule.
**Owner: a later maintenance-tool PR.**

**`re_validate` dies on one log file that is not valid UTF-8, in one of its two
readers and not the other.** `volume_abspath_from_log()` opens in text mode with the
default encoding, so `readline()` raises `UnicodeDecodeError` on a corrupt log; its
only caller, `report_missing_volumes()`, does not catch it, and a batch run ends
mid-report. The same file is survivable through `get_log_info()`, because
`get_all_log_info()` catches `ValueError` and `UnicodeDecodeError` is a subclass of
it, so that path skips the file and continues. One corrupt log is fatal on one path
and invisible on the other. Both docstrings now say so. Found by round 1.
**Owner: a later maintenance-tool PR.**

**`re_validate.get_log_info()` scans every log record for a string pdslogger never
writes.** The scan is `fatal |= ('| FATAL |' in rec)`, and pdslogger renders a fatal
record as `| CRITICAL |` and a logged exception as `| EXCEPTION |`; "fatal" is a level
alias in `_DEFAULT_LEVEL_NAME_ALIASES` and not a rendered name. Reproduced by writing
a log through a real `PdsLogger` with `error()`, `fatal()` and `exception()` calls:
`| ERROR |`, `| CRITICAL |` and `| EXCEPTION |` are all present and `| FATAL |` is
not.

So the flag `get_log_info()` returns as "had a fatal" is true exactly when the log has
no elapsed time. **The consequence is in the scheduler.** `validate_one_volume()`
catches an exception, logs it through `logger.exception()` and returns a fatal count
to its caller, which prints and mails an error line -- but the log file it wrote
records the failure as `| EXCEPTION |`, so the *next* batch run reads that same log
back as a clean, completed validation with neither an error nor a fatal, and schedules
the volume as though it had passed. The error scan misses the same case, so
`print_batch_status`'s "error logged" note is absent for it too. The three docstrings
that describe the scan now say what it does rather than what it was meant to do. Found
by round 3. **Owner: a later maintenance-tool PR.**

### 4043. Info-shelf sidecars are local-time dependent

**Info-shelf sidecars are local-time dependent.** `pdsinfoshelf` /
`pds4infoshelf` format modification times with
`datetime.fromtimestamp(...).strftime(...)`, so the same tree shelved in two
time zones produces different sidecars. The tests pin `TZ=UTC` in the tool
subprocess environment to make goldens portable; whether the tools themselves
should record UTC is a behavior question for the Phase 6 consolidation.

### 4044. Log paths that are announced, assumed or reported but never written

**`run_index_main` assumes its log path contains the tool's own directory.**
It computes the directory for the per-target handlers as
`logfile.rpartition('/' + spec.progname + '/')[0] + '/' + spec.progname`, which
yields `/pdsindexshelf` if that component is absent. It cannot be absent:
`log_paths_for` is called with `dir=spec.progname`, a non-empty constant, and
`_derived_paths._log_path_for` appends `[subdir.rstrip('/'), '/']` after a log
root that always ends in `/`. This is the two base tools'
`logfile.rpartition('/pdsindexshelf/')[0] + '/pdsindexshelf'` generalized, not
new. It is deliberately not `os.path.split(logfile)[0]`, which the other two
drivers use: `log_path_for_index` builds a path carrying the table's whole
logical path, so splitting would put a copy of the tool's error handler in
every per-table directory. Recorded because the assumption is implicit.
**Owner: open.**

**`pdsdependency` reports a log path it does not write.** Inside its `main()`, the
loop that creates the file handlers rewrites each log path with
`replace('/volumes/', '/')` before opening it, but the rewrite is a loop-local
rebinding; the `logger.info('Log file', ...)` loop a few lines below reports the
*unrewritten* list. So a run prints
`Log file: <root>/logs/pdsdependency/volumes/<volume set>/<volume>_dependency_<tag>.log`
and writes `<root>/logs/pdsdependency/<volume set>/<volume>_dependency_<tag>.log`.
The `volumes/` directory is never created. Found by the PR-32 review, which looked
for the file rather than trusting the line; the guide documents the real path and
warns about the printed one. **Owner: whoever next touches `pdsdependency`'s
logging.**

**`pdsdependency.main()` announces log paths that nothing writes.** The handler loop
rebinds its loop variable, `logfile = logfile.replace('/volumes/', '/')`, and builds
the file handler from the rebound value; the loop that announces the paths then
re-iterates the original `logfiles` list. So a run prints
`Log file: <root>/pdsdependency/volumes/VG_28xx/VG_2810_dependency_<tag>.log` and
writes `<root>/pdsdependency/VG_28xx/VG_2810_dependency_<tag>.log`. Measured by round
4 against a sandbox holdings tree. The announced path does not exist, and an operator
following it finds nothing. **Owner: a later maintenance-tool PR.**

### 4045. Path builders that disagree about the same object

**`PdsFile.bundle_abspath` and `PdsFile.bundleset_abspath` return different things
for the same kind of non-answer.** `bundle_abspath` returns `''` when this file
belongs to no bundle and again when the category is a checksums-of-archives category
(`pdsfile.py:1135`, `:1144`); `bundleset_abspath` returns `None` when this file
belongs to no bundleset (`:1188`). Both are public, both are consumed by
`bundle_pdsfile` and `bundleset_pdsfile`, which test the result for truth and so
cannot tell the two apart -- but a caller that tests `is None` can. The docstrings
written here state each method's own answer. **Owner: a future pdsfile PR.**

**`bundle_abspath` and `os_listdir` disagree about how a `checksums-bundles` file is
named.** The path builder gives `<BUNDLE>_bundles_md5.txt`, because `bundles` is one
of the volume types; the shelf-backed directory listing gives `<BUNDLE>_md5.txt`,
reserving the bare form for `volumes` and `bundles` alike. `_non_checksum_abspath`
reduces the first form and leaves the second naming nothing. Neither test tree holds a
`checksums-bundles` directory, so nothing exercises it. The docstrings describe what
each function does and do not pick a side. **Owner: a future pdsfile PR.**

**Three bundle-set-level directory kinds get a checksum path and an info shelf path
but are excluded from the two methods that ask whether those exist.**
`checksum_path_and_lskip` covers a `checksums_*`, `superseded*` or `*_support`
directory, and `shelf_path_and_lskip` builds an info shelf path for it under its own
name. But `checksum_path_if_exact` recognizes only a bundle directory and an archives
bundle set, and `info_shelf_expected` is `bool(self.bundlename)`, which is empty for
all three. Verified by running on the live directory
`bundles/uranus_occs_earthbased/uranus_occ_support`: `checksum_path_and_lskip()`
returns a real path and `checksum_path_if_exact()` returns `''`;
`shelf_path_and_lskip('info')` returns
`_infoshelf-bundles/uranus_occs_earthbased/uranus_occ_support_info.pickle` and
`info_shelf_expected` is `False`, so `shelf_exists_if_expected()` reports that no
entry is expected for a directory that has its own shelf. **Owner: a future pdsfile
PR** -- one of each pair is wrong and which one is a decision.

### 4046. Rule tables that name a volume set or product that does not exist

**`VG_0xxx.py`'s `opus_type` keys on `.IBQ` while its description and format tables
key on `.IBG`.** `description_and_icon_by_regex` matches `volumes/.*\.IBG` for
"Compressed browse image" and `opus_format` matches `.*\.IBG`, but `opus_type`
matches `volumes/.*/C[0-9]{7}\.IBQ` for the "Small Preview (IBQ)" type. One of the
two spellings cannot be right, and if the files are `.IBG` then the browse product
has no OPUS type. The VG_0xxx volume set is not in this holdings copy, so which
spelling the archive uses could not be settled here. **Owner: whoever can read a
complete holdings tree.**

**`VG_20xx.py`'s `filespec_to_bundleset` returns a volume set name no directory
carries.** The replacement string is `r'VG__20xx'`, with two underscores.
Runtime: `Pds3File.FILESPEC_TO_BUNDLESET.first('VG_2001/x')` returns
`'VG__20xx'`, and the holdings tree has `volumes/VG_20xx`. The docstring written
here describes what the table returns rather than what it was meant to return,
which is why the defect is visible at all. **Owner: whoever next touches the
Voyager rule modules.**

**`FILESPEC_TO_BUNDLESET` answers with a non-existent volume set for three volume
sets that define no override.** With only the default rule in play,
`JNOJIR_1000` gives `JNOJIR_1xxx`, `JNOSRU_0001` gives `JNOSRU_0xxx` and
`RES_0001` gives `RES_0xxx`. The real names are `JNOJIR_xxxx`, `JNOSRU_xxxx` and
`RES_xxxx_prelim`. Eleven modules do define an override; these three need one and
do not have it. **Owner: whoever next touches those three modules.**

**`COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH`'s version tie-break rests on a false
premise.** Its comment says "There is no case where this involves a two-digit version
number, so we can use alphabetic sort". `v1630912046_17.qub` is in COVIMS_0038 in this
holdings copy, and `'_17.qub' < '_9.qub'` under an alphabetic comparison, so a
single-digit sibling would win. No live failure is demonstrable, because only the `_17`
exists for that clock here. The sort key is also `basename[11:]`, which is the
underscore, the version, any sub-observation number and the extension rather than the
version alone. Owner: whoever next touches `COVIMS_0xxx.py`.

**`VGIRIS_xxxx.py`'s description table is `VG_20xx.py`'s, and every entry is
unreachable.** The two tables have identical `ast.unparse` output. Four entries name
bare planet directories, where VGIRIS names them for planet and spacecraft together
(`DATA/JUPITER_VG1`); the other six name `VG1_JUP.DAT`-style files, where VGIRIS holds
`C1547XXX.TAB` and `C1547XXX_{LSB,MSB}.DAT`. Every pattern is anchored at both ends, so
the whole table is dead weight and every VGIRIS path falls through to the defaults.
Owner: whoever next touches the Voyager IRIS modules.

### 4047. Seven defects in `DictionaryCache`

**`DictionaryCache(lifetime=0)` cannot serve `set()` without an explicit
lifetime.** The constructor documents `lifetime` as "default lifetime in
seconds; 0 for no expiration", and `set()` documents `lifetime=None` as "use
the default lifetime". But `set()` tests the default for truthiness
(`pdscache.py:196`, `if self.lifetime:`), so a default of `0` falls through
to `self.lifetime_func(value)`, which is `None` when the cache was built
with a constant — `TypeError: 'NoneType' object is not callable`. Every
caller in this repo passes a lifetime function or a non-zero constant, so
nothing hits it today; it is a trap for the next caller who takes the
docstring at its word. The fix is a `self.lifetime is not None` test, which
is a behavior change to a public class and therefore outside PR-15's
enumerated list. Found because a test fixture built its throwaway cache with
`lifetime=0`. **Owner:** a future pdscache PR, or phase "b".

**`DictionaryCache.set_multi`'s `pause` parameter has never suppressed the
per-key trim, and still does not.** The broken call PR-15 repaired passed
`pause=True` down to `set()`, plainly intending to defer trimming until the
batch finished. `set()`
has no such parameter and never did, so the intent was never expressible;
PR-15 dropped the keyword, which is the literal fix for "passes an
unsupported kwarg". The consequence is that `pause` now governs only the
final explicit `_trim_if_necessary()` call, while each `set()` inside the
loop still trims if the cache is not paused. Honoring the original intent
means either bypassing `resume()`'s trim or giving `set()` a real `pause`
parameter — both are new semantics for a public method, which §6.4 makes an
owner decision rather than an executor's. No caller exists in this repo.
**Owner:** a future pdscache PR, with the owner's read on the intended
semantics.

**`DictionaryCache`'s trim bookkeeping is only ever added to, so one deletion or one
lazy expiry leaves the cache permanently unable to trim.** `self.keys`
(`pdscache.py:175`) is the set the size limit counts, and `set()` adds to it at
`:500`. Nothing removes from it except `_trim` itself (`:221`) and `clear()`
(`:650`). `delete` (`:589`), `__delitem__` (`:609`), `delete_multi` (`:629`) and
`get`'s expiry path all delete the entry and leave the key behind. `_trim` then
evaluates `self.dict[k][1]` for every `k in self.keys` (`:215`) and raises
`KeyError` on the first stale one -- and `_trim` is reached from `set()`,
`set_multi()` and `resume()`, so the failure surfaces on an unrelated later call.

Verified by running: a paused cache holding 40 expiring entries, one `delete()`,
then `resume()` raises `KeyError: 'k0000'`. The read-only path is worse: storing one
entry with a lifetime already past, reading it once with `get()`, and then resuming
raises `KeyError: 'short'` -- a caller that only ever read has broken its own cache.

This is the most consequential thing found in the file, and it is not reached today
only because the preload path never deletes. The fix is a `self.keys.discard(key)`
at each of the four sites, which is a behavior change to a public class. **Owner: a
future pdscache PR.**

**A `DictionaryCache` entry re-stored as permanent goes on counting against the
size limit it is exempt from.** `set()` adds the key to `self.keys` when the entry
expires (`pdscache.py:499-500`) and never removes it when the same key is stored
again with `lifetime=0`. The entry is then filtered out of the trim candidates by
the `is not None` test at `:216` while still being counted by the size test at
`:214`, so the trigger fires and nothing is discarded. Verified by running: one key
set with `lifetime=3600` and then with `lifetime=0` leaves `keys == {'k'}` with the
entry's expiration None, and `_trim()` discards nothing. Same fix and same shape as
a since-resolved observation. **Owner: a future pdscache PR.**

**A `DictionaryCache` built with a bound or class method as its lifetime raises
`TypeError` on the first store that needs the default, and `_preload.py` builds one
that way.** The constructor's test is `type(lifetime).__name__ == 'function'`
(`pdscache.py:177`); a classmethod's type name is `'method'`, so it falls to the
constant branch, and `set()` then evaluates `time.time() + <method>`.
`MemcachedCache` tests `in ('function', 'method')` and accepts the same argument.

This is not hypothetical. `_preload.py:573` and `_preload.py:605` construct
`pdscache.DictionaryCache(lifetime=cls.cache_lifetime, ...)`, and `cache_lifetime`
is a classmethod (`_preload.py:804`). Verified by running: building the cache
exactly as those lines do and calling `set('a', 1)` gives
`TypeError: unsupported operand type(s) for +: 'float' and 'method'`. It is reached
only on the fallback from a memcached cache to a dictionary cache -- the class-level
`CACHE` objects pass the module-level plain function and are fine -- which is why no
test sees it.

The one-line fix is to widen the constructor's test to match `MemcachedCache`'s,
which is a behavior change to a public class. **Owner: a future pdscache PR; this is
the one on this list with a live caller.**

**`int(x + 0.999)` is not a ceiling, and a sub-millisecond lifetime becomes
permanent.** `MemcachedCache` converts lifetimes that way at `pdscache.py:781` and
`:1578`. Measured: `1.0005` gives 1 and `2.0001` gives 2, where a ceiling gives 2 and
3; and `0.0005` gives **0**, which this class reads as never expiring. So a lifetime
function returning a small positive number stores a permanent entry, and the
constant-zero trap of a since-resolved observation extends to any constant below 0.001. **Owner: a
future pdscache PR, with a since-resolved observation.**

**`DictionaryCache` trimming is a no-op whenever the expiring entries are already
at or below the limit, and unconditionally so at `limit=0`.** The threshold test
counts the whole key set, and the slice that selects the discards,
`expirations[:-self.limit]` (`pdscache.py:218`), is taken over the expiring entries
alone. Verified by running: `limit=0` accumulates 500 entries and every trim
discards nothing, because `expirations[:-0]` is the empty slice; and a key set of 31
of which 25 are permanent, with `limit=10`, is over the threshold with 6 candidates
and discards nothing forever. A negative limit inverts the slice and discards the
entries it should keep. a since-resolved observation records the adjacent bookkeeping fault; this is
about the arithmetic. **Owner: a future pdscache PR.**

### 4048. Shelf paths and `SHELVES_ONLY` behave inconsistently

**`shelf_type='index'` builds a path no index shelf occupies.**
`SHELF_PATH_INFO['index']` gives `('_indexshelf-', '_index')`, so
`shelf_path_and_lskip('index')` for a bundle yields
`_indexshelf-<category>/<set>/<bundle>_index.pickle`. Real index shelves are written
one per index **table**, inside a directory named for the bundle, which is what
`indexshelf_abspath` finds; the shelf directory holds directories, not `.pickle`
files. The key is wrong too: a real index shelf is keyed by row selection keys, not
by a table basename. Nothing in `src/` or `tests/` passes `'index'` to any of the
four methods that accept it -- every call site passes `'info'` or `'link'` -- so this
is a latent trap rather than a live fault, and the docstrings now say so rather than
advertising `'index'` as supported. **Owner: a future pdsfile PR.**

**`os_path_isdir` raises `KeyError` under `SHELVES_ONLY` where `os_path_exists`
answers `False`.** The existence test asks `key in shelf`; the directory test
subscripts, `(_, _, _, checksum, _) = shelf[key]`, and `_get_shelf` returns a plain
dict. The handler around it catches `(ValueError, IndexError, OSError)` and not
`KeyError`. Verified by running under `SHELVES_ONLY` on a path that does not exist:
the existence test gives `False` and the directory test raises
`KeyError('NOSUCHDIR')`. `sort_basenames(dirs_first=True)` reaches it. The docstring
now carries the `Raises:` entry and states the asymmetry. **Owner: a future pdsfile
PR** -- either add `KeyError` to the handler or use `.get`.

**`os_path_exists`'s `lru_cache` survives a `SHELVES_ONLY` toggle.** The
decorator on `_local_fs.py`'s `os_path_exists` keys the cache on
`(cls, abspath, force_case_sensitive)` only, while `PdsFile.use_shelves_only`
mutates `SHELVES_ONLY` on the subclasses. An entry computed in one mode is
returned in the other, and nothing clears the cache on the toggle. The
suite's two passes each set the mode once at session start, so it does not
bite there; a long-running consumer that toggles would see it. Pre-existing
and bit-identical across the move — the decorator line is one of the
byte-for-byte segments. **Owner:** phase "b" of issue #77, or whichever PR
next changes cache behavior.

### 4049. Single-component paths crash two helpers

**`sort_logical_paths` raises `KeyError` on any single-component path.** A path with
no slash enters the top-level name set but the loop that fills the child-name table
does not run for it, and the recursive walk immediately reads that table. Verified by
running: `Pds3File.sort_logical_paths(['volumes'])` raises `KeyError: 'volumes'`. A
category-level logical path is an ordinary input for this API. The docstring now
carries the `Raises:` entry. **Owner: a future pdsfile PR.**

**`repair_case` raises `UnboundLocalError` on a single-component path.**
`_path_utils.py`'s `repair_case` assigns `found` only inside
`for k in range(1, len(parts))` but reads it unconditionally after the loop,
so any path that splits into one component skips the assignment:
`repair_case('/', Pds3File)` raises `UnboundLocalError: cannot access local
variable 'found'`. `repair_case('/tmp', Pds3File)` is fine, so only the
filesystem root and an empty-ish path reach it. Pre-existing and moved
byte-for-byte by PR-16; it is not in PR-15's enumerated bug list, and PR-16
is a pure move with no licence to change behavior. The fix is a
`found = True` initialization (a path with nothing to repair *is* found), but
that is a behavior change on a currently-raising input and needs its own test
and PR. **Owner:** PR-23, or whichever PR next edits this file.

### 4050. Six defects in `PdsViewSet`

**`PdsViewSet.small` and `PdsViewSet.medium` raise `AttributeError` whenever their
fallback is reached.** Each looks for a member whose path contains `_small` or
`_med` and, finding none, executes `viewable = viewable.for_frame(200,200)` with
`viewable` bound to `None` (`pdsviewable.py:479`, `:496`). Two faults in one line:
the receiver is the value just tested as false, and `for_frame` is a method of
`PdsViewSet`, not of `PdsViewable`, so `self.for_frame(...)` is what was meant.
Verified by running: a two-member set with no `_small` in either path answers
`AttributeError: 'NoneType' object has no attribute 'for_frame'`. The properties are
public and neither is exercised by any test. The docstrings written here say the
property raises rather than falling back, which is accurate and is not the fix.
**Owner: a future pdsviewable PR; the fix is a behavior change to a public
property.**

**`PdsViewSet.append` given a `PdsViewSet` adds exactly one of its members.** The
recursive branch is `for sub_viewable in viewable.viewables: self.append(sub_viewable);
return`, with the `return` inside the loop (`pdsviewable.py:354-356`), so the first
iteration returns. Which member survives depends on the iteration order of a Python
set, so the result is not even deterministic. Verified by running: appending a
two-member set to an empty one leaves one member. Moving the `return` out of the loop
is a one-line fix, but it changes what a public method does with an input it
currently mishandles silently. **Owner: a future pdsviewable PR.**

**`PdsViewSet.append` given an *empty* `PdsViewSet` puts the set object into the
members and then raises.** a since-resolved observation covers the non-empty case, where the `return`
inside the loop (`pdsviewable.py:354`) leaves all but one member behind. With an
empty set the loop body never runs at all, so control falls past the recursive
branch to `self.viewables.add(viewable)` (`:358`) and then to `if viewable.name:`
(`:361`), which raises `AttributeError`. Verified by running:
`PdsViewSet().append(PdsViewSet())` raises, and the receiving set is left holding a
`PdsViewSet` among its viewables, so every later size lookup on it fails too. The
same one-line fix as a since-resolved observation -- dedenting the `return` out of the `for` and
leaving it inside the `if` -- resolves both cases at once: the loop then appends
every member, and an empty set falls straight through to a `return` that keeps the
set object out of the members. **Owner: a future pdsviewable PR, together with
a since-resolved observation.**

**`PdsViewSet.from_pdsfiles` drops every "full" product but the last.**
`full_viewable = viewable` (`pdsviewable.py:689`) overwrites on each match, and a
viewable named "full" never reaches `viewables.append` (`:691`, the `else` branch),
so a replaced one is not in the set at all rather than merely unindexed. Verified by
running: a group of `x_full.png`, `y_full.jpg` and `z_small.png` yields a set holding
only `y_full.jpg` and `z_small.png`. **Owner: a future pdsviewable PR.**

**`PdsViewable.copy` recomputes the aspect ratios, so a copy of a scaled copy is not
equivalent to it.** The constructor derives both ratios from the width and height it
is given (`pdsviewable.py:94-95`), and `copy` passes the eight stored attributes and
nothing else. A viewable from `for_width()` carries the *source image's* ratios by
design, which is what makes a second scaling of it correct; copying it replaces them
with its own. Verified by running: a 1000x1 source scaled to width 1 has ratios
1000.0 and 0.001, and the copy of that has 1.0 and 1.0. **Owner: a future
pdsviewable PR.**

**`PdsViewSet.append`'s recursive branch keeps an arbitrary one of the nested
set's members, and which one is not deterministic.**
`src/pdsfile/pdsviewable.py`, in `append`:

```python
if isinstance(viewable, PdsViewSet):
    for sub_viewable in viewable.viewables:
        self.append(sub_viewable)
        return
```

The `return` is **inside** the loop, so exactly one member of
`viewable.viewables` is appended and the rest are dropped. `viewables` is a
`set` and `PdsViewable` defines neither `__hash__` nor `__eq__`, so it is
hashed by identity and the set's iteration order depends on where the objects
landed in memory — it varies from one interpreter run to the next. Measured:
appending a two-member `PdsViewSet` and reading back the surviving name gives
`['a']` or `['b']` at random, **five runs on unmodified `rewrite` @ `96e5960`
produced a-b-a-a-b**, and five on the PR-23 branch produced b-b-a-b-a. The
behavior is identical in both trees; it is simply not a function of the input.

PR-23 found this only because it renamed the loop variable (`B020`: the loop
variable shadowed the iterable it walks) and then diffed the two trees'
outputs. The rename is behavior-preserving; the defect is older. Dedenting the
`return` — which is almost certainly the intent — changes what the method does
and needs its own test.

Also worth noting for whoever fixes it: an **empty** nested `PdsViewSet` falls
through the loop and reaches `self.viewables.add(viewable)`, adding the
*viewset* to a set of viewables, and then raises `AttributeError:
'PdsViewSet' object has no attribute 'name'` — identically in both trees.
**Owner: phase "b" of issue #77.**

### 4051. Sixteen defects in `MemcachedCache`

**`MemcachedCache.set_multi` applies one key's lifetime to the whole batch.**
The lifetime-lookup loop assigns to a single `lifetime` local
(`pdscache.py:798-800`), so after it runs, `lifetime` holds whichever key
memcached happened to yield last. The store loop then passes that one value
to `set_local()` for **every** key, overwriting the correct per-key lifetimes
the lookup loop had just written into `local_lifetime_by_key`, and applying
it to keys that were already local as well. PR-15 fixed only the enumerated
defect on the same lines — iterating the dictionary as pairs — because until
that was fixed the method raised before reaching the store loop, and because
correcting the lifetime plumbing is a second, larger behavior change. The
regression test added for the enumerated fix uses a single key, so it does
not pin the batch behavior either way. **Owner:** a future pdscache PR.

**`MemcachedCache.delete_multi` cannot delete anything: its first statement names a
client method that does not exist, and two more faults sit behind it.** The call
opens with `_ = self.mc.del_multi(keys)` (`pdscache.py:1678`). `self.mc` is a
`pylibmc.Client`, and pylibmc's batch delete is `delete_multi`; `del_multi` appears
nowhere in it. Checked against the 1.6.3 source rather than assumed: the C method
table in `src/_pylibmcmodule.h` registers `delete_multi`, `src/pylibmc/client.py`
defines no attribute fallback, and the string `del_multi` occurs in that package
only as a substring of `delete_multi`. So **every** call raises `AttributeError`
immediately, an empty one included, and nothing on the server or in this process is
changed.

Behind that fault sit two more. The local removal the loop would reach is spelled
`_del_local` (`pdscache.py:1685`) and the method this class defines is
`_delete_local` (`pdscache.py:1696`). And the value it would then return compares
`count = len(self) - prev_len` (`pdscache.py:1693`), which any real deletion drives
negative, against `len(keys)`, so only an empty batch could answer `True`. Three
independent faults in fourteen lines, with no caller and no test anywhere in this
repo. **Owner: a future pdscache PR.**

**`MemcachedCache.flush`'s general error path raises before it can report.** In the
`except pylibmc.Error` handler, `keys = mydict.keys()` (`pdscache.py:1185`) is
followed by `keys.sort()` (`:1188`); `dict_keys` has no `sort`, so with a logger
present the handler raises `AttributeError`. The batches written before the failing
one are already on the server, and the failing one and everything after it are left
in the buffer. Without a logger the handler completes and the values in the failing
batch are dropped rather than retried. Ten lines below, the summary counts
`len(self.local_keys_by_lifetime) - len(failures)` (`:1195`), which is a count of
distinct lifetimes, not of items, so the "N items flushed" message is wrong whenever
more than one item shares a lifetime. **Owner: a future pdscache PR.**

**Three `MemcachedCache` log calls are not guarded by a logger test, and two error
paths are guarded by one that changes what they do.** Unguarded: breaking a stale
block (`pdscache.py:898`), losing a race to claim one (`:959`), and the
permanent-value-too-big report (`:1909`). Each raises `AttributeError` on a cache
built with `logger=None`, which is the default. The other two are worse than
unguarded: `unblock`'s refusals read `if not test_pid and self.logger:` and
`if test_pid != self.pid and self.logger:` (`:977`, `:983`), so a cache with no
logger does not refuse — it goes on to clear a block that another process holds.
**Owner: a future pdscache PR.**

**`MemcachedCache.replicate_clear` writes `None` back to the shared clear counter.**
The branch reading `if clear_count is None: # lost from memcache!` responds with
`self.mc.set('$CLEAR_COUNT', clear_count, time=0)` (`pdscache.py:1802-1803`), which
stores the `None` it was just given rather than the count this process knows. The
key is then held at a value no comparison can use, and `was_cleared()`, which
evaluates `clear_count > self.clear_count`, raises `TypeError` from then on.
**Owner: a future pdscache PR.**

**`MemcachedCache.get_multi` restores a lost permanent value and then does not
return it.** The branch at `pdscache.py:1347-1364` notices that a requested key is a
permanent entry the server no longer has, calls `_restore_permanent_to_cache()`, and
breaks -- without adding the recovered value to the result. `get()` handles the same
case at `:1006-1008` by restoring *and* returning it. Verified by running against a
stub client: with `'p'` in `permanent_values` only, `get('p')` answers `'PERM'` and
`get_multi(['p'])` answers `{}`. A caller replacing a loop of `get()` calls with one
`get_multi()`, which is the reason the batch form exists, silently loses exactly the
entries the permanent-value machinery was built to protect. **Owner: a future
pdscache PR.**

**`MemcachedCache.delete` removes the permanent copy and reports that it removed
nothing.** The answer is `status1 or status2` (`pdscache.py:1626`), from the server
and from `_delete_local`, and `_delete_local` deliberately does not touch the
permanent copies. The permanent deletion at `:1506-1507` is not folded in. Verified
by running: with `'p'` in `permanent_values` only, `delete('p')` returns False and
`permanent_values` is empty afterwards. **Owner: a future pdscache PR.**

**`MemcachedCache.clear(block=False)` empties the server with no block held, and
raises `TypeError` if the clear counter has been lost.** `wait_for_unblock('clear')`
(`:1754`) waits for anyone else's block and claims nothing; `flush_all()` (`:1757`)
runs unprotected; only afterwards is this process's ID written to the blocking key,
to be released a moment later. Verified by recording the client calls a
`clear(block=False)` makes: `get`, `get`, `flush_all`, `set_multi`, `get`, `set`.
Separately, `max(self.mc.get('$CLEAR_COUNT'), self.clear_count)` at `:1756` raises
`TypeError` when the server has lost that key -- verified -- which is the same lost
key `was_cleared` and `replicate_clear` already have entries and docstrings for.
**Owner: a future pdscache PR.**

**`MAX_BLOCK_SECONDS` bounds one waiter's patience, not a block's age, and the
clock restarts.** `_wait_for_ok` sets `unblock_time = time.time() + MAX_BLOCK_SECONDS`
at `pdscache.py:877`, when this call first notices the block, so a waiter arriving
at a block that is already hours old still waits the full two minutes. The
assignment is inside the outer loop, and the inner loop exits as soon as the
blocking process merely *changes* (`:892`), so a succession of blockers restarts the
clock and the wait has no bound. Related, and the reason a probe of this hung for
two minutes: a missing `$OK_PID` fails the `blocking_pid in (0, self.pid)` test at
`:873`, so a server that has lost the key reads as blocked by an unknown process to
every caller. `is_blocked` repairs that key; nothing on the waiting path does.
**Owner: a future pdscache PR.**

**`MemcachedCache.set()` can discard the value it was just given and still answer
True.** Unless the cache is paused, `set()` calls `flush()` (`pdscache.py:1470`),
and `flush()` calls `replicate_clear_if_necessary()`. If another process has cleared
the cache since this one last looked, that replication empties every local
dictionary -- including the buffer holding the value `set()` wrote a line earlier --
and `flush()` returns before writing anything. Verified by running against a stub
server: buffer one value, bump the shared clear counter, then `set('new', 'value')`;
the call returns `True`, `clear_count` moves to the new value, the buffer is empty,
`get_local('new')` answers None, and the server never hears of the key. The same
shape applies to `set_multi()`. Both docstrings now say so. **Owner: a future
pdscache PR.**

**`MemcachedCache.get()` can raise `KeyError` on the path that exists to rescue a
lost permanent value.** When the server has lost a permanent entry, `get()` calls
`_restore_permanent_to_cache()` and then returns `self.permanent_values[key]`
(`pdscache.py:1268`). The restore drops a key from `permanent_values` when the
server rejects it as too large (`:1914`), so the subscript that follows can miss.
Verified by running: with the value only in `permanent_values` and the stub server
refusing it as too large, `get('perm')` raises `KeyError: 'perm'` -- while the same
call has just put the value safely in `toobig_dict`, so the *next* read answers it.
`get_multi()` is not affected; it breaks after the restore with no subscript.
**Owner: a future pdscache PR.**

**`MemcachedCache.delete_multi` writes to the server, and can break another
process's block, before it raises.** a since-resolved observation records that the call cannot delete
anything. What it did not record is that the failure is not inert: the first
statement is `self.wait_for_unblock('delete_multi')` (`pdscache.py:1677`), which
reads the blocking key and, after `MAX_BLOCK_SECONDS`, writes it to break the block.
Verified by running against a stub with another process holding the block and the
timeout shortened: the call recorded `get`, `get`, `set('$OK_PID', 0)`, left the
block cleared, and only then raised. In the real code that is preceded by up to a
two-minute wait. A caller who retries the call pays that wait again and strips the
block again. **Owner: a future pdscache PR, with a since-resolved observation.**

**`_restore_permanent_to_cache` logs before it acts, so the no-logger failure
leaves the oversized value neither moved nor dropped.** The order at
`pdscache.py:1909-1914` is warn, then `toobig_dict[k] = v[0]`, then
`del self.permanent_values[k]`. With `logger=None` the unguarded warn raises first.
Verified by running: `toobig_dict` is empty and `permanent_values` still holds the
key afterwards, so the "next lost entry does not try it again" property does not
hold either. Note that `_wait_for_ok` has the opposite ordering -- it writes to the
server and logs afterwards (a since-resolved observation) -- so the two unguarded-logger sites in this
file fail in opposite directions. **Owner: a future pdscache PR, with a since-resolved observation.**

**`MemcachedCache.flush`'s error path calls `.sort()` on `dict_keys`.**
`src/pdsfile/pdscache.py`, inside `flush`'s `except pylibmc.Error` handler:
`keys = mydict.keys()` followed by `keys.sort()` raises
`AttributeError: 'dict_keys' object has no attribute 'sort'`, so the handler
fails with a second, unrelated error before it logs anything about the first —
and `failures += keys` after it never runs either. PR-23 edited the two log
lines that bracket it (the `F541` fixes) and could not repair it: the fix
changes behavior, which §2 forbids here, and no gate can reach it (observation 4207).
The fix is `keys = sorted(mydict.keys())` plus dropping the separate `.sort()`.
**Owner: phase "b" of issue #77.**

**`MemcachedCache.unblock` releases a lock it does not own when no logger is
configured.** `src/pdsfile/pdscache.py`, in `unblock`: both guard clauses put
their `return` **inside** the `if self.logger:` block rather than beside it.
On `rewrite` @ `96e5960`, with the original indentation shown by column:

```
466:        if not test_pid:            # 8
467:            if self.logger:         # 12
468:                self.logger.error(…)# 16
471:                return              # 16  <- inside the logger guard
```

So when `self.logger` is `None`, neither guard returns. Both fall through to
`self.mc.set('$OK_PID', 0, time=0)`, which clears the block — including when
`test_pid` names **another live process**. A caller that constructed its cache
without a logger can therefore release another process's lock and let cache
operations overlap. The second guard (`test_pid != self.pid`) is the dangerous
one; the first merely double-unblocks an already-unblocked cache.

**This is pre-existing and PR-23 did not introduce it.** PR-23's `SIM102`
collapse rewrote the pair as `if not test_pid and self.logger: … return`, which
is **exactly equivalent** to the original for all four combinations of the two
conditions, precisely because the `return` was already inside the inner guard.
The collapse is correct and should stay.

Surfaced by CodeRabbit on PR #118, which reported it as a Critical defect
*introduced by* the collapse. That reading is wrong — but the hazard it
describes is real, and its suggested patch (move each `return` out to the outer
level, keep only the `logger.error` call guarded) is the correct fix. Applying
it changes observable behavior, which §2 permits only in the enumerated PRs, so
PR-23 cannot carry it: `pdscache.py` bug fixes were PR-15's licence (bugs 4 and
5) and that PR has merged.

Not covered by any test: `pylibmc` is not installed in this environment, so the
whole of `MemcachedCache` is dark locally — the same reason PR-15's two
`pdscache` defects survived to be found by reading. This is a third defect of
that family.

**Re-owned (2026-08-07): Phase 6 has ended and PR-28 did not touch
`pdscache.py`.** This entry named it as the nearest PR licensed to change
behavior; that PR's licence covered one identifier in one maintenance tool, and
reaching into the cache from it would have been a behavior change nothing in
that PR's evidence covered. The question is unchanged and unowned.
**Owner (superseded): a PR licensed to change behavior — Phase 6's PR-28
(`errors` fix) was
the nearest, or a dedicated follow-up. It must add a regression test first, per
§2.**

**`DictionaryCache.get_multi` and `MemcachedCache.get_multi` disagree about a
missing key, and the docstring described the behavior neither of them had.**
`DictionaryCache.get_multi` (`pdscache.py:407`) reads each key through `self[key]`
at `:427`, so a key that is absent, expired, or holds `None` raises `KeyError` and
no partial result comes back. `MemcachedCache.get_multi` (`:1309`) omits such a key
and returns the rest. Both carried the same sentence, "Missing keys do not
appear in the returned dictionary", which was true of the second and the opposite of
the first. Verified by running: `DictionaryCache(lifetime=100).get_multi(['k',
'nope'])` raises `KeyError: 'nope'`. Both docstrings now describe what their own
class does, so the divergence is visible instead of hidden, but the two methods still
cannot be swapped. No caller in this repo uses either. **Owner: a future pdscache
PR — which of the two behaviors the shared interface is supposed to have.**

**Two smaller things in `pdscache.py` that no docstring had claimed either way.**
`get()` and `get_now()` unpack the stored object as a `(value, lifetime)` pair
(`pdscache.py:1273` and `:1425`), so any key holding something else raises
`TypeError: cannot unpack non-iterable int object` -- verified on `'$CLEAR_COUNT'`
for both, and reachable for every bookkeeping key and for anything another program
wrote into a shared memcached. And `_trim` writes its "items trimmed" message
whenever the threshold is crossed, including when the count is zero (`:224`),
verified by capturing `('%d items trimmed from DictionaryCache', 0)`. Both are now
documented. **Owner: a future pdscache PR.**

### 4052. Small documented defects the second reads turned up

**Three smaller things in the path helpers and the shelf lookup.**
`construct_category_list` iterates its argument four times, once per prefix
combination, so a one-shot iterator yields only the bare names and then fails the
removals -- verified: a generator gives `ValueError: list.remove(x): x not in list`,
while the same names as a list give the documented `4*n - 3` categories.
`formatted_file_size` chooses its unit before it rounds, so a value that rounds up to
a thousand of its own unit keeps that unit and is written in scientific notation --
verified: 999999 gives `1e+03 KB`, not `1000 KB` and not `1 MB`.
`shelf_path_and_key_for_abspath` and the instance method it mirrors disagree in the
documents tree, where a PdsFile carries no bundle name: the instance method raises
`ValueError` and the classmethod returns a shelf path built from the file's own
basename, which no holdings tree holds. All three are documented; none is fixed.
**Owner: a future pdsfile PR.**

**Two smaller things the second reads turned up, both documented and neither fixed.**
`formatted_file_size` chooses its unit from a logarithm without a floor, so a value
between zero and one drives the unit index negative and indexes the unit list from its
end -- `0.5` returns `500 YB` with no error -- and a positive value below `1e-27`
drives the index past the end of the list and raises `IndexError`. And
`_preload_dir` sets `permanent` on every directory it visits, which nothing in the
package reads; what actually keeps those entries out of the trim is the zero lifetime
they were stored with, which is observation 4126's subject from the other side.
**Owner: a future pdsfile PR.**

### 4053. Splitting a bundle set name that carries a volume type returns parts that do not rejoin into…

**Splitting a bundle set name that carries a volume type returns parts that do not
rejoin into the name, and the branch that would use the regular expression's groups
is unreachable.** Two findings in `split_basename`, both measured.
`COISS_2xxx_previews.tar.gz` gives `('COISS_2xxx', '_previews.tar.gz', '_previews')`,
so concatenating the three parts does not reproduce the input, which the family's
other cases do. And the bundle-name branch returns the regular expression's groups
only where `SPLIT_RULES.first(basename)` answers with the name it was given; every
split rule in the tree answers with a three-element tuple, so that comparison is a
tuple against a string and is never true. Verified:
`SPLIT_RULES.first('COISS_2001_previews.tar.gz')` is
`('COISS_2001_previews.tar', '', '.gz')`. **Owner: a future pdsfile PR.**

### 4054. Target expansion can dereference `None` and rejects a valid directory

**`_shelf_common.expand_selection_targets()` can dereference `None`.**
`pdsdir = pdsf.parent()` is followed immediately by `pdsdir.is_bundle_dir`, so a
path whose PdsFile has no parent gives an `AttributeError` rather than the
documented `SystemExit`. Round 1 could not construct such a path inside a holdings
tree, so it is theoretical. **Owner: a later maintenance-tool PR.**

**`_indexshelf_common.index_targets()` rejects the top-level metadata directory.**
The test is `'/metadata/' not in path` and `os.path.abspath()` leaves no trailing
slash, so `<holdings>/metadata` prints "Not a metadata directory" and exits 1 while
every directory below it is accepted. Measured by round 3. The docstring describes
the test accurately, so this is an observation about the code.
**Owner: PR-30b or a later maintenance-tool PR.**

### 4055. The association and index-row path builders return wrong answers

**`associated_abspaths` re-globs a truncated index-row pattern on the second index
extension.** `pattern` is rebound inside the `for ext in cls.IDX_EXT` loop, so once
the first extension has stripped the row selection key the shortened pattern persists
into the next iteration, where no suffix is found and the glob returns the bare index
file. That path differs from the row's, so the dedup at the end keeps both. `Pds4File`
has two index extensions and so is the class this reaches. The mechanism is certain
from the code; whether a PDS4 association rule actually emits an index-row pattern was
not exercised. **Owner: a future pdsfile PR** -- bind the rewrite to a fresh name.

**`associated_abspaths` filters the data files by `must_exist` and does not filter the
label it adds.** `label_basename` guesses a name for a label whether or not the file
is there, and the label is appended after the existence filter has run, so a call that
asked for existing paths only can return a path that does not exist. **Owner: a future
pdsfile PR.**

**`data_abspath_associated_with_index_row`'s neighbor rewrite replaces every
occurrence of the basename, not the last path component.**
`src/pdsfile/_index_rows.py:489` builds the answer for a missing row as
`abspath.replace(neighbor.basename, self.basename)`, so a basename that also appears
in a parent directory name is substituted there too and the result names a different
directory rather than a sibling file. The `cls.os_path_exists(abspath)` guard on the
next line is what keeps a corrupted path from being returned -- the rewrite is
accepted only if it resolves -- so the failure mode is a missed answer rather than a
wrong one, and a holdings tree whose row basenames never appear as directory
components never sees it. The docstring states the behavior, including that the
replacement is not scoped to the last component. The fix is to rewrite only the final
component, which changes what the method returns for inputs it currently rejects and
so needs its own regression test. Raised by the CodeRabbit re-review; the docstring
documents it and no entry did.
**Owner: a future pdsfile PR.**

**`data_abspath_associated_with_index_row` builds its answer under a hard-coded
`volumes` category.** The line is `parts = [self.bundleset_abspath('volumes')]`, not
`self.bundleset_abspath(cls.BUNDLE_DIR_NAME)`. Measured: `Pds3File.BUNDLE_DIR_NAME` is
`volumes` and `Pds4File.BUNDLE_DIR_NAME` is `bundles`, and a PDS4 holdings tree has no
`volumes` directory at all. So a PDS4 index row is given a path that can never exist,
and `data_pdsfile_for_index_row` returns a PdsFile for it, since it does not test
existence. `get_keys()` in the same method **does** branch on PDS3 versus PDS4, so a
PDS4 row reads the right columns and then puts them in a tree that is not there.
**Owner: a future pdsfile PR.**

### 4056. The open-shelf cache is not trimmed by least-recent use, because its counter is per-subclass

**The open-shelf cache is not trimmed by least-recent use, because its counter is
per-subclass.** `_get_shelf` and `shelf_lookup` do `cls.SHELF_ACCESS_COUNT += 1`,
where `cls` is `type(self)` -- a per-bundleset rule subclass for any real object.
`SHELF_ACCESS_COUNT` is an **int** on `PdsFile`, so `+=` rebinds it onto the calling
class, while `SHELF_CACHE` and `SHELF_ACCESS` are **dicts** mutated in place and so
genuinely shared. Verified by running: after opening one COISS index shelf and then
one COVIMS index shelf, `COISS_xxxx` and `COVIMS_0xxx` each held their own
`SHELF_ACCESS_COUNT` of 1, `PdsFile`'s stayed 0, and both wrote serial 1 into the one
shared `SHELF_ACCESS`. So the trim orders shelves by the activity of whichever class
opened each one, and a shelf just opened by a quiet class can carry a lower serial
than one a busy class opened earlier and be the one discarded. The docstrings now say
this instead of claiming the newest is safe. **Owner: a future pdsfile PR** -- the fix
is to keep the counter somewhere it is not rebound, which is a code change.

### 4057. The PDS3/PDS4 column-name choice fails for the class the PDS4 registry hands out by default

**The PDS3/PDS4 column-name choice fails for the class the PDS4 registry hands out
by default.** `data_abspath_associated_with_index_row` decides with
`cls.__bases__[0].__name__ == 'Pds4File'`. `Pds4File.SUBCLASSES['default']` is
`Pds4File` itself, whose first base is named `'PdsFile'`, so a row in any PDS4 bundle
set without a rule module of its own is read with the PDS3 column-name lists, which
are not the same. Only six PDS4 bundle sets have rule modules. Reachable by
construction; no PDS4 index table in the test holdings exercises it. **Owner: a
future pdsfile PR** -- the fragility was already noted, but not that the default
class is one of the failing cases.

### 4058. The sidecar path is derived two different ways in one module

**The two repair tasks derive the sidecar path differently from the writers that
create it.** `_indexshelf_common.index_repair()` and
`_linkshelf_common.link_repair()` both use `path.replace('.pickle', '.py')`, which
rewrites *every* occurrence, while the writers that produced the file use
`path.rpartition('.')[0] + '.py'`. A shelf path containing `.pickle` anywhere but
its extension therefore gets a sidecar path the writer never wrote, and
`os.path.getmtime` raises `FileNotFoundError` from inside the "content is up to
date" branch. No such path exists in the holdings trees checked.
**Owner: PR-30b or a later maintenance-tool PR.**

**Two different derivations of the sidecar path in one module.** `write_infodict()`
builds it as `info_path.rpartition('.')[0] + '.py'` and `repair()` as
`info_path.replace('.pickle', '.py')`; `_shelves.shelf_lookup()` uses the second form
too. They diverge for any path with `.pickle` in a directory component, which
`replace()` would rewrite. Identical in both info shelf tools. Found by round 1.
**Owner: a later maintenance-tool PR.**

### 4059. Three `show_opus_products` flag quirks

**Two `show_opus_products` flag quirks, both preserved.** `--debug` calls
`traceback.print_exc()` at a point where the `ValueError` it means to show has
already been caught by the `except` clause above it, so there is no active
exception and it prints the string `NoneType: None` — the flag has never shown
a traceback (transcript record `opus/unresolvable-path-debug`). And
`--narrow-table` is read only inside the `if display_table:` branch, so
`--narrow-table --pprint` and `--narrow-table --raw` accept the flag and ignore
it; `--narrow-table` alone works, because none of the three display flags being
set is what turns the table on. Both are base behaviour carried into `main()`
verbatim.
**Owner: open.**

**`show_opus_products --debug` prints no traceback.** `traceback.print_exc()` sits
outside any `except` block -- both handlers have exited by the time control reaches
`if pdsf_inst is None:` -- so the flag prints `NoneType: None` instead of the
traceback its own help text promises. Measured by round 2 on a path that resolves
under neither class. **Owner: a later tool PR.**

**`show_opus_products`'s narrow-table de-duplication guard can never fire.**
`rows` is a list of one-element lists and `opus_type` is a string, so
`if opus_type not in rows` compares a string against lists and is always true. The
guard is harmless, because `res` is a dictionary keyed by OPUS type and its keys are
unique already, but it is dead. **Owner: a later tool PR.**

### 4060. Unreachable rules and dead regular expressions across the rule modules

**Five tables in three modules are defined and never reached.** `VG_28xx.py`
defines `sort_key` and `split_rules` and its class body assigns neither
`SORT_KEY` nor `SPLIT_RULES`. `cassini_iss_fring_mosaics_rsfrench2025.py` and
`cassini_iss_spokes_hedman_hamilton_2024.py` each define `archive_paths` and
`archive_dirs`, with a detailed header comment, and neither class body assigns
`ARCHIVE_PATHS` or `ARCHIVE_DIRS`. observation 4061 records the second pair; this entry
records that the shape repeats. The rule-table checker built for PR-30 cannot see
it, because it tests only that a defined table is named in the docstring, and
both docstrings now say the tables are unreached. **A checker that compared
top-level tables against class-body assignments would catch all five**, and is a
natural extension of `critiques/pr-30/check_rule_tables.py`.
**Owner: whichever PR next extends that checker.**

**`SPLIT_RULES`'s "after sort key" preview rule cannot match what `SORT_KEY`
produces.** `SORT_KEY` emits `_1full`, `_2med`, `_3small` and `_4thumb`; the
split rule written for those spellings is
`(.*)_(1thumb|2small|3med|9full)\.(jpg|png)`. No sort key ever matches it,
although the comment on `SPLIT_RULES` says the rules "must also work for the sort
keys of basenames". Both `rules/__init__.py` modules carry it.
**Owner: whoever next touches the default rule tables.**

**Three dead or mistargeted regular expressions in single modules.**
`COUVIS_8xxx.py`'s last `versions` entry matches `volumes/COVIMS_8xxx.../COUVIS_8001/...`,
naming one mission in the other's module, so COUVIS_8xxx has no cross-version
rule for any directory but `data`. `JNOJNC_xxxx.py` has `JNOJNC _0\d\d\d`, with a
space inside the volume ID, so its global-maps association can never match.
`VG_28xx.py`'s `FRAME_DICT` string literal is missing its closing brace, so the
value would not parse; nothing reads it. **Owner: whoever next touches each.**

**Two regular expressions with unescaped dots, and one with a misplaced
quantifier.** `COCIRS_xxxx.py`'s `split_rules` writes `(.*)\.tar.gz`, where the
second and third dots are wildcards; `RPX_xxxx.py`'s `versions` writes
`volumes/RPX_xxxx*/...` on the *source* side, where `*` quantifies the preceding
`x` rather than globbing. Both happen to match what they were meant to match.
`COUVIS_0xxx.VERSIONS_PATH_AND_KEY` accepts only `_v<digit>`, not the
`_v1.0`/`_v2.1` forms the rest of the package spells `(|_v[0-9\.]+)`.
**Owner: whoever next touches each.**

**`EBROCC_xxxx.py`'s `default_viewables` has an unreachable branch.** Its first
entry, `(r'.*\.lbl', re.I, '')`, is case-insensitive and anchored, so it consumes
every `.LBL`; the `LBL` alternative in the entry below it can never be reached.
**Owner: whoever next touches `EBROCC_xxxx.py`.**

**`COISS_xxxx.py` and `COVIMS_0xxx.py` each carry description rules for an
`extras` directory below a `data` directory, and no volume is laid out that way.**
In the archive `extras` is a sibling of `data`, so `COISS_xxxx.py`'s "Preview image
collection" and "Preview image" entries and `COVIMS_0xxx.py`'s equivalent never fire,
and the browse extras fall through to the default table's "Browse image collection".
Owner: whoever next touches either module.

### 4061. Wrong or unreachable entries in the PDS4 rule tables

**Two pds4 `associations_to_metadata` tables match their data files and return an
empty list.** In `cassini_uvis_solarocc_beckerjarmak2023.py` and
`cassini_iss_fring_mosaics_rsfrench2025.py` the single entry of
`associations_to_metadata` has a full regular expression and `[]` as its output, so
the table matches and produces nothing. That is not the same as a null translator:
the match consumes the path and the lookup stops. Both bundle sets have a
`metadata/` tree in the categories their `archive_paths` tables name.
**Owner: whoever next revises the pds4 rules.**

**Five pds4 association patterns carry a stray `]` in an alternation.**
`cassini_iss.py`, `cassini_vims.py` and `uranus_occs_earthbased.py` all write
`(.*|_[a-z]*])`, whose second alternative requires a literal `]` in the path and
is unreachable behind a leading `.*` in any case. It reads as a typo for
`(.*|_[a-z]*)`. **Owner: whoever next revises the pds4 rules.**

**Two pds4 `associations_to_documents` tables emit regular-expression
metacharacters into a path.** `cassini_uvis_solarocc_beckerjarmak2023.py` and
`cassini_iss_fring_mosaics_rsfrench2025.py` return
`documents/<name>[^/]*` and `documents/<name>[^/]*/.*`, where the replacement is
consumed as a logical path or an fnmatch glob: `[^/]` is a character class
matching a literal `^` or `/`, and `.*` is not a glob. Every other module emits a
plain `documents/<name>/*`. **Owner: whoever next revises the pds4 rules.**

**`uranus_occs_earthbased.py`'s two archive tables disagree about versioned bundle
sets.** `archive_paths` matches `(uranus_occs_earthbased[^/]*)` and so answers for
`uranus_occs_earthbased_v2`; `archive_dirs` matches
`.*archives-(.*/uranus_occs_earthbased)/(.*).tar.gz`, which cannot match the `_v2`
archive it would name. The module's own header comment anticipates the `_v2` case
explicitly. **Owner: whoever next revises the pds4 rules.**

**`Pds4File.FILESPEC_TO_BUNDLESET` maps a spokes file specification to the wrong
bundle set.** `cassini_iss_spokes_hedman-hamilton-2024/data_derived/x/y.fits`
resolves to `cassini_iss`, because the spokes module adds nothing to the table and
`cassini_iss.py`'s `(cassini_iss)_.*` swallows it. The fring bundle set escapes only
because its module is imported later and each module prepends. Either the spokes
module needs a rule or the `cassini_iss` rule needs narrowing. Owner: whoever next
revises the pds4 rules.

**`archive_paths` and `archive_dirs` are defined and never wired in two pds4 rule
modules.** `cassini_iss_fring_mosaics_rsfrench2025.py` and
`cassini_iss_spokes_hedman_hamilton_2024.py` each define both tables, with a header
comment describing the archive split in detail -- four archives for the first, three
for the second -- and neither class body assigns `ARCHIVE_PATHS` or `ARCHIVE_DIRS`.
The other four pds4 rule modules do. Both bundle sets therefore use the empty
archive tables from `pds4file/rules/__init__.py`, and the two tables are unreachable.
**Owner: whoever next revises the pds4 rules.**

### 4065. Two cosmetic defects in the copy scripts' guard messages

**`copy_shelves.sh` reports the wrong path and `copy_documents.sh` names the
wrong script.** The destination-directory guard (`copy_shelves.sh:23-25`) tests
`"$DEST_HOLDINGS/$TYPE"` but prints `Directory does not exist:
'$DEST_HOLDINGS/$TYPE/$VOLSET'`, naming a deeper path than the one that failed
the test; and `copy_documents.sh:9`'s usage line reads `Usage:
copy_documentation.sh ...`, a filename that does not exist. Both predate the
2026-08-16 exit-status change and are visible only on an invalid invocation.
The document-only freeze was lifted for the exit statuses alone, so these are
recorded rather than fixed. **Owner: the owner, if the freeze is lifted
again.**

### 4066. `from_path`'s extension assembly misreads category-suffixed checksum basenames

**`from_path` never recognizes `<unit set>_<type>_md5.txt` as a checksum
file.** `pdsfile.py`'s bundle-set parse builds
`extension = matchobj.group(3) + matchobj.group(4)` -- the combined tail plus
the category group -- so `COISS_0xxx_previews_md5.txt` yields
`_previews_md5.txt_previews`, `endswith('_md5.txt')` fails, and `checksums_`
is never set; the `VOLTYPES` scan then still sets the bundle type, so the
result is a half-classified object. The suffix-free forms
(`<set>_md5.txt`, `<set>.tar.gz`) assemble correctly, which is why the defect
is invisible on the common paths. Identical for PDS3 and, since the
`BUNDLESET_PLUS_REGEX` tail arrived, for PDS4 -- exact parity, which is what
the 2026-08-16 ruling asked of that change. **Owner: whoever next hardens
`from_path`.**

## Structure and duplication

### 4100. `_is_forgiven` has two gaps

**`_is_forgiven` lacks `KeyError`/`re.error` guards** for a malformed future
allowlist entry. Harmless while seeded empty and fail-safe (raises rather than
mis-forgives). Owner: whichever PR first adds allowlist entries (PR-07/PR-08)
may add validation.

**`_is_forgiven` ignores a category's `pr` field.**
`tests/api/test_api_freeze.py::_is_forgiven` never reads `pr`, so §6.1's
"a category activates only from its named PR" is not enforced in code
(pre-existing in the PR-02 checker; the file is frozen post-PR-02). The PR-08
allowlist entry still records `"pr": "PR-08"` for provenance. Owner: a future
checker-hardening PR with owner sign-off.

### 4101. `_local_fs.py`'s `values` list and its `zip` are now visibly dead weight

**`_local_fs.py`'s `values` list and its `zip` are now visibly dead weight.**
In `glob_glob`'s `SHELVES_ONLY` branch, `values = list(shelf.values())` feeds a
`zip(interior_paths[...], values[...])` whose second element the loop body never
uses — which is why PR-23 renamed the loop variable to `_value` and added
`strict=False` rather than deleting anything. Iterating `interior_paths` alone
would be equivalent (the two lists come from the same dict and cannot differ in
length) and would drop one full materialization of every shelf value per call,
but it is a code change rather than a style fix and belongs where the shelf
read paths are being looked at anyway. **Owner: phase "b" of issue #77.**

### 4102. `crlf.test_crlf` keeps its name, and with it the last `PT028` entry that is not…

**`crlf.test_crlf` keeps its name, and with it the last `PT028` entry that is
not `pdsdependency`'s.** `PT028` fires twice on this function, for the `task`
and `threshold` defaults, and only because the name matches pytest's collection
pattern; it is the tool's line-terminator classifier. Measured before deciding:
`grep -rn 'test_crlf\b' --include=*.py .` finds two callers, `crlf.main()` and
`tests/holdings_maintenance/test_crlf.py`, so a rename is mechanically safe
inside this repository.

Not done, for three reasons that are judgement rather than obstacle: it is a
public name on a shipped module; PR-32 is chartered to document `crlf` as a
program, so the tool has a documented surface; and the entry marks a lint false
positive rather than a defect. There is a real cost to keeping it —
`test_crlf.py`'s header documents a live collection trap, that
`from …crlf import test_crlf` makes pytest collect the imported function and
fail it on a missing `filepath` fixture — which a rename would delete outright.
Renaming would take the ratchet to 65 entries / 179 slots.
**Owner: open.**

### 4104. `holdings_sentinel` hard-codes the *name* of the holdings directory

**`holdings_sentinel` hard-codes the *name* of the holdings directory.** The
new `ToolSpec` field carries `'/holdings/'` and `'/pds4-holdings/'`, which is
what five tools already do inline (`pdschecksums`'s command-line path split,
`pdsdependency`'s command-line path split, `pdsinfoshelf`'s command-line path
split, `pds4checksums`'s command-line path split and archives rebuild,
`pds4infoshelf`'s command-line path split and archives rebuild). Each `partition()`s a command-line path on it and
exits with `'Not a holdings subdirectory: '` when the separator is absent, and
the two pds4 tools also rebuild an archives path by concatenating it back.

So a holdings root whose last directory component is not literally `holdings`
or `pds4-holdings` cannot be used with those five tools, whatever
`PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` say. The repo's own roots satisfy it,
which is why nothing has noticed. Recorded because promoting the literal to a
named spec field makes it look like a configuration point, and it is not.
**Owner: whichever PR is willing to change what those five tools accept.**

### 4105. `move_old_links` copies the shelf file twice, to the same destination

**`move_old_links` copies the shelf file twice, to the same destination.** It
runs `shutil.copy(shelf_file, dest)` and then, as its `.pickle` sidecar step,
`shutil.copy(pickle_src, pickle_dest)` — and the shelf file *is* the `.pickle`,
so `pickle_src == shelf_file` and `pickle_dest == dest`. The second copy
overwrites the first with identical bytes. Harmless, and the versioned output
is the `.pickle` and `.py` pair the linkshelf tests already assert; recorded
because the redundancy is only visible with the two flavors' copies merged into
one, and because the obvious "fix" (dropping the sidecar step) would be wrong
if a shelf file ever stops being a `.pickle`.

**Carried into the merged function unchanged**, and now visible as data rather
than as code: `LINK_SHELF.companions` is `('.py', '.pickle')`, and the
`.pickle` entry names the shelf file itself. The `move_old()` docstring says
so. Still a redundant copy; still not worth removing blind.

**Looked at again by PR-27 and left alone.** The link shelf tasks moved into
`_linkshelf_common.py` and still call `move_old(link_path, LINK_SHELF)`; the
redundancy is entirely inside `move_old`, which this PR did not touch. The
reason not to drop the `.pickle` companion is unchanged and is now the thing
the versioned pair is asserted on:
`test_pds3_linkshelf.test_update_versions_the_shelf_file_it_replaces` requires
both a `_v001.pickle` and a `_v001.py` in the log directory, and the `.py` only
gets there through the companion loop. Dropping the `.pickle` entry alone would
be safe today and wrong the moment a shelf file is not a `.pickle`.
**Owner: open.**

### 4106. `PdsFile.child()` looks a cache entry up and throws it away

**`PdsFile.child()` looks a cache entry up and throws it away.**
`src/pdsfile/pdsfile.py`, in `child()`: the comment reads "Create the logical
path and return from cache if available", and the code is a `cls.CACHE[...]`
subscript inside `try/except KeyError: pass` with **no `return`**. The looked-up
object is discarded, so every `child()` call rebuilds an object the cache
already holds. PR-23 could only remove the unused binding, not the defect: the
subscript has an effect (a `DictionaryCache` lookup updates that key's
bookkeeping) and adding the missing `return` is a behavior change — objects
would start coming back from the cache instead of being reconstructed — which
needs its own regression test and its own PR. The subscript is kept as an
expression statement and the comment now says the result is discarded.
**Owner: phase "b" of issue #77.**

### 4107. `pdsinfoshelf.get_info()`'s `checkdict` parameter is never read for its value

**`pdsinfoshelf.get_info()`'s `checkdict` parameter is never read for its value.**
It has exactly one load site in that function, as an argument to the recursive call,
and nothing else. The digest lookup is in `get_info_for_file()`, which is a
**sibling** nested function rather than one nested inside `get_info()`, so its free
`checkdict` binds to `generate_infodict()`'s local and not to this parameter.
Measured two ways: an AST count of the load sites, and a mutated copy in which the
recursive call is handed a decoy dictionary, which leaves every digest unchanged. The
parameter is inert -- the digests still come from the enclosing scope -- rather than
wrong. Identical in `pds4infoshelf`.
**Owner: a later maintenance-tool PR.**

### 4108. `read_archive_info` is still duplicated near-verbatim between the archives twins

**`read_archive_info` is still duplicated near-verbatim between the archives
twins.** 34 statements in `pdsarchives.py`, 31 in `pds4archives.py`, and the
only genuine divergence is the three-line existence guard at
`pdsarchives.read_archive_info`'s existence guard (`logger.critical('File does not exist', tarpath)` then
`return []`). The other two differences — the PdsFile class and the
`info`/`normal` level — are already carried by `ToolSpec`.

PR-25 left it alone under its own rule: sharing it would need a flag whose
only job is to reinstate one side's guard, and forcing either behavior on the
other tool is an observable change. That is a defensible call for one pair,
and the plan's target interface leaves the `read_*` functions in the tool
modules. It is worth revisiting once the other four pairs land and the shape
of the whole family is visible: a `missing_input_action` spec **callable**
(not a boolean) would collapse this without a shrug-flag, if the same shape
recurs.
**Owner: PR-26/PR-27, once five pairs are on the core.**

### 4109. `scripts/dump_public_api.py` trips RUF100 (unused `# noqa: BLE001`)

**`scripts/dump_public_api.py` trips RUF100 (unused `# noqa: BLE001`).** BLE is
not in the ruff `select` set, so the noqa is unused. The file is frozen
post-PR-02 (plan §6.4), so it was ratcheted (`["RUF100"]`) rather than edited.
A later PR could remove the dead noqa (comment-only, freeze-neutral) with owner
sign-off, then drop the ratchet entry.

### 4110. `tests/pds{3,4}file/helper.py` resolve holdings at import time

**`tests/pds{3,4}file/helper.py` resolve holdings at import time.** Each
module does `PDS3_HOLDINGS_DIR = resolve_holdings().pds3_root` at import,
rather than reading the session's `config._pdsfile_holdings`. The two agree
today because the resolver is a pure function of the environment and nothing
mutates it mid-session, but they are two independent resolutions of the same
question. **Owner:** whichever PR restructures `tests/pds{3,4}file/` (the
same one that owns PR-07's `helper.py` double-import note above).

### 4111. Both `rules/__init__.py` modules carry a stale `__all__`

**Both `rules/__init__.py` modules carry a stale `__all__`.**
`pds3file/rules/__init__.py`'s `__all__` lists 24 dataset modules and omits
`JNOSRU_xxxx`; `pds4file/rules/__init__.py`'s lists four of the six modules its
package initializer imports, and one entry carries the comment
`# will resume work on this, currently working on COISS and COVIMS`. Nothing is
broken by either, because neither package uses `from .rules import *`:
`pds3file/__init__.py` names all 25 modules explicitly and `pds4file/__init__.py`
names all six, and the explicit import is what registers each subclass. But
`__all__` is public surface that says something false about the package, and a
future `import *` would silently drop a subclass. **Owner: whichever PR next
touches the two initializers -- PR-30a in the split recorded in the plan.**

### 4112. Dead branches in the index shelf tasks

**Two dead branches in the index shelf tasks, preserved rather than removed.**
`_indexshelf_common.index_initialize` and `index_validate` both test the
dictionary `generate_indexdict()` returned against `None`, and
`generate_indexdict()` either returns a two-tuple or raises, so neither test
can be true. Both flavors carried the same branch before the migration
(`pdsindexshelf.py:224` and `pds4indexshelf.py:221` at `2265393`), so merging
them forced no choice and PR-27 kept both. Contrast the one dead branch PR-27
did remove — a `move_old()` in `pdslinkshelf.initialize` sitting after a guard
that returns when the shelf exists — which only one of the two flavors had, so
the merge had to pick. Removing provably-dead code that both flavors carry is a
cleanup of its own.
**Owner: open.**

**Two of the five index shelf tasks test a value that cannot be what they test
for.** `index_initialize()` and `index_validate()` both guard on
`if <table dict> is None:`, and `generate_indexdict()` returns a dictionary from a
comprehension on every path that returns at all, so neither branch is reachable.
`index_reinitialize()` and `index_repair()` guard on emptiness instead, which is
reachable. The consequence is a real divergence rather than only dead code: a table
with no rows is shelved as an empty dictionary by `index_initialize()` and stops
`index_reinitialize()` before it writes. Measured by stubbing `generate_indexdict`
to return `({}, 0.0)`. **Owner: PR-30b or a later maintenance-tool PR.**

### 4113. Dead code in `pdsdependency`

**`pdsdependency.PdsDependency.get_modtime()`'s backup-file skip is dead code.** The
block that logs "Backup file skipped" and skips a file matching `BACKUP_FILENAME` or
carrying " copy" sits **inside** the dot-underscore branch and **after** that branch's
`continue`, so it can never execute. Confirmed from the AST: the `If` testing
`BACKUP_FILENAME.match(file)` is the third statement of the body of the `If` testing
`'/._' in absfile`, whose second statement is a `Continue`. The four tool families that walk a directory
listing the same way carry the identical block one level out, where it runs:
`pdschecksums`, `pdsinfoshelf`, `pdslinkshelf` and `_archives_common`, and the pds4
twins of the first three. `_indexshelf_common` is not among them -- it has no
`.DS_Store` branch and no dot-underscore branch at all, and tests for a backup file
in `run_index_main()` against a whole absolute path. Found by round 4.

Two consequences. A backup file dates the directory it is in exactly as its original
does, so one stale `X_2024-01-01T00-00-00.tab` beside `X.tab` can make every file
derived from that directory report "out of date". And `BACKUP_FILENAME`, which this
module declares its own copy of just below its imports, has no reachable use. The docstring says so
rather than describing the exclusion as if it worked; the fix is one dedent.
Found by round 2. **Owner: a later maintenance-tool PR.**

**`pdsdependency.main()` carries two rejections that cannot fire.** The
`if pdsf.checksums_:` and `if pdsf.archives_:` branches print "No pdsdependency for
checksum files" and "No pdsdependency for archive files" and exit 1. Neither message
can print: `category_` is `checksums_ + archives_ + bundletype_`, so any path with a
non-empty `checksums_` or `archives_` fails the `pdsdir.category_ != 'volumes/'` test
in the earlier validation loop and exits there. Measured:
`pdsdependency <holdings>/archives-volumes/COISS_2xxx` prints
"not a volume or volume set directory" and exits 1. Found by round 2.
**Owner: a later maintenance-tool PR.**

### 4114. Duplicated table entries, typos and comments that describe the wrong thing

**Duplicated entries in six tables.** `VGISS_xxxx.py`'s `opus_type` repeats a
`GEOMED` line; `CORSS_8xxx.py`'s description table repeats a four-line preview
block; `HSTxx_xxxx.py` repeats an `index/hstfiles` line; both `rules/__init__.py`
modules repeat `volumes/[^/]+`; and `COISS_xxxx.py`'s `opus_type` repeats an
`extras/(tiff|full)` line, which `cassini_iss.py` and `cassini_vims.py` inherit
verbatim. None changes behavior, since a translator takes the first match.
**Owner: cleanup, whenever a PR touches each table.**

**Typos in user-facing description strings.** These are the strings Viewmaster
shows: "Interopolated ousekeeping data" (`COCIRS_xxxx.py`), "Raw imag, FITS" and
"Calibrated imag, FITS" (`NHxxxx_xxxx.py`), "Ring intercept geomemtry" and "Raw
data with anomalies identifed" (`VG_28xx.py`), "Thumbnail obervation diagram"
(`CORSS_8xxx.py`), "Checksum index of indices and metadatas" and "GIF vewable
image" (both `rules/__init__.py` modules). The PR-30 docstrings do not repeat any
of them. **Owner: a small text-only PR; none of these is behavioral.**

**The `cassini_iss_spokes_hedman_hamilton_2024.archive_dirs` comments describe a
collection the lists do not contain.** Both partial-archive entries are headed
`# - all files under document`, and neither list holds a `document` path; they hold
`data_derived`/`browse_derived`, `bundle.lblx`, `context`, `readme.txt`,
`spice_kernels` and `xml_schema`. The comment appears to have come from
`cassini_iss_fring_mosaics_rsfrench2025.py`, whose equivalents do include `document/`.
Owner: whoever next touches the spokes module.

**Eight of `cassini_vims.py`'s tables and five of `uranus_occs_earthbased.py`'s are
byte-identical to `COISS_xxxx.py`'s, and are written for PDS3 paths.**
Comparing the source of each top-level assignment across
`pds3file/rules/COISS_xxxx.py`, `pds4file/rules/cassini_iss.py`,
`pds4file/rules/cassini_vims.py` and `pds4file/rules/uranus_occs_earthbased.py`:
`description_and_icon_by_regex`, `view_options`, `neighbors`, `sort_key` and
`opus_format` are identical in all four; `opus_type`, `opus_products` and
`opus_id_to_primary_logical_path` are identical in the first three.

For `cassini_iss.py` that is unremarkable -- it is the same observations in their
PDS3 locations. For the other two it is not. `cassini_vims.py`'s
`description_and_icon_by_regex` returns "Narrow-angle image, VICAR",
"CISSCAL source code (IDL)" and "ISS Calibration Report"; its `opus_type` files
products under the "Cassini ISS" OPUS category and its
`opus_id_to_primary_logical_path` resolves to `volumes/COISS_1xxx` and
`volumes/COISS_2xxx`. Every one of those patterns keys on `volumes/` or on a
`COISS_*` volume ID, so none of them can fire for a `bundles/cassini_vims` path,
and where one could fire it would return an ISS description for a VIMS product.
`uranus_occs_earthbased.py` carries the same five for a dataset that is not a
Cassini one at all.

The PR-30 docstrings say this rather than describing those tables as VIMS or Uranus
behavior, which is why the record's section 10 calls `cassini_vims.py` the
uncomfortable one. **Owner: whoever next revises the pds4 rules.**

### 4115. Limits and spec fields that constrain nothing

**`pds4archives`'s four `*_LIMITS` constants constrain nothing.** The archive
tools cap their per-file log lines with `{'info': N}` entries --
`LOAD_DIRECTORY_INFO_LIMITS = {'info': 100}` and its three siblings, now one
copy at `_common.py`'s archive `*_LIMITS`. But `pdsarchives` writes those lines through
`logger.info` and `pds4archives` through `logger.normal`
(`pdsarchives`'s `file_log_level` / `pds4archives`'s `file_log_level` carry the level as
`file_log_level`), and **`normal` is not `info`**. Measured directly against
`pdslogger` 3.2.1, four calls under `limits={'info': 2}`:

| Called | Lines emitted | Closing summary |
|---|---|---|
| `logger.info` ×4 | 2, then `Additional INFO messages suppressed` | `2 INFO messages reported of 4 total` |
| `logger.normal` ×4 | all 4 | `4 NORMAL messages` |

So `pdsarchives` caps its per-file lines at 100 per scope and `pds4archives`
emits one line per file with no ceiling, and the three constants
`pds4archives` appears to be governed by are inert. The level difference is
also visible in every log line (`| INFO |` vs `| NORMAL |`) and in the closing
summary, so converging the two is a change to frozen log text, not a cleanup.
PR-25 preserved both sides exactly rather than picking one.
**Owner: needs a decision on whether pds4's per-file logging was meant to be
capped; whichever way it goes, it changes log output.**

**`pds4checksums.GENERATE_CHECKSUMS_LIMITS = {'info': -1}` controls nothing.** That
module writes its per-file lines through `normal()`, so the `info` cap applies only to
the one forced summary line. Measured: a `{'normal': 0}` entry does cap normal-level
messages, so the levels are capped independently and this default is inert. The pds3
constant of the same name is live. Found by round 1.
**Owner: a later maintenance-tool PR.**

**Two `ToolSpec` fields are carried by the checksum and shelf specs and read
by nothing.** `index_ext` is declared for the indexshelf tools, which are not
on the core yet (this is the standing case observation 4204 records). `file_log_level`
is different: it is *accurate* for these four tools — pds3 logs its per-file
lines through `logger.info` and pds4 through `logger.normal` — but their domain
functions hard-code the call rather than reading the spec, because those
functions stayed in the tool modules. So the field states a true fact that the
tool it describes ignores.

Making the domain functions read it is not free: `generate_checksums` and
`generate_infodict` would each need the spec threaded in, which is a bigger
change than PR-26's scope and touches the functions the plan says to leave
alone. Recorded so that a later PR can either wire it up or narrow the field's
documented scope, rather than a sweep finding it and deleting it.
**Owner: open.**

### 4116. Remove the `PDSFILE_TEST_HOLDINGS` selector env var — deferred to PR-11

**Remove the `PDSFILE_TEST_HOLDINGS` selector env var — deferred to PR-11.**
The owner wants the explicit `PDSFILE_TEST_HOLDINGS=full` selector to go away.
It can be replaced without an env var, but not by markers alone: markers pick
*which tests* run (per-item), while *which data tree to preload* is a
session-level choice whose locations are machine-specific (`PDS3/4_HOLDINGS_DIR`
for full; `PDSFILE_TEST_DATA_DIR` for the mini checkout) and so cannot become
markers. Planned end-state, to land with the mini tree in PR-11:
- Infer the flavor: mini when `PDSFILE_TEST_DATA_DIR` resolves to real trees,
  else full when `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR` are set and valid,
  else skip all gracefully.
- Add a `--holdings full|mini` pytest CLI option (parallels `--mode`/`--update`)
  as the explicit override for the "both present" case — a flag, not an env var.
- Then drop `export PDSFILE_TEST_HOLDINGS=full` from
  `scripts/automated_tests/pdsfile_main_test.sh` (full becomes inferred).
- Keep `full_holdings` as the applicability marker (auto-skip under mini); PR-11
  also tags the actual size/volume-count tests with `@pytest.mark.full_holdings`.
PR-09 keeps the explicit-`full` selector as originally spec'd until then.

### 4117. Six lines of commented-out code remain under `src/pdsfile/`, all in `pdscache.py`

**Six lines of commented-out code remain under `src/pdsfile/`, all in
`pdscache.py`.** `src/pdsfile/pdscache.py:699` and `:1009–1013`, both in
`MemcachedCache`, are the `self.mc.get_multi(...)` calls that the live
one-key-at-a-time loops replaced, each under the comment
`# Memcached->get_multi hangs on long lists; individual requests work fine`.
PR-22's dead-code scope is `pdsfile.py` plus the ten modules Phase 5 created,
and `pdscache.py` is neither, so they are out of scope there.

They are also the one case where "commented-out code" and "a comment that
documents behavior" are hard to separate: the commented-out call is the
evidence for the workaround the comment describes, and it sits inside the
`MemcachedCache`/pylibmc support that ground rule 9 protects and that no test
in this repo can exercise. Removing them would need an owner decision rather
than an executor's. **Owner: owner decision, then PR-23 (which is the next PR
to touch `pdscache.py`).**

### 4118. The `docs` extra declares `sphinx>=7` and cannot install Sphinx 7

**The `docs` extra declares `sphinx>=7` and cannot install Sphinx 7.** `myst-parser`
5.1.0, which the same extra pulls in and which `doc_python.mdc` section 3 requires,
declares `sphinx>=8,<10`. The floor the extra can actually resolve is therefore 8.
pip resolves it correctly today: the local tree builds on Sphinx 9.1.0, and the two
hosted lint legs build on 9.1.0 and **8.1.3**, both clean. Those legs were Python
3.13 and 3.10 when this was measured, and the floor is 3.11 now, so the older leg may
resolve differently; the point is unchanged, which is that the declared floor is
looser than the real one. The declared floor is looser than the real one, which matters only to someone
who pins Sphinx and silently gets an older `myst-parser` than this tree was written
against. `pyproject.toml` is otherwise untouched by this PR.
**Owner: a later packaging PR.**

### 4119. The `except AttributeError` round each rule-module import is dead code

**The `except AttributeError` round each rule-module import is dead code.**
`pds3file/__init__.py` and `pds4file/__init__.py` both wrap their
`from .rules import (...)` in a handler whose comment says the error is what a
recursive import of `pdsfile` raises when a rule module is tested on its own. Round
2 traced the handler lines with `sys.settrace` while importing `pdsfile`,
`pdsfile.pds3file.rules.COISS_xxxx` and
`pdsfile.pds4file.rules.uranus_occs_earthbased` first in a fresh interpreter and got
no hits in any of the three, and built a minimal package of the same shape showing
that `import pkg.sub as sub` during a circular import binds from `sys.modules`
rather than raising -- the fallback added in Python 3.7. `pyproject.toml` requires
3.11 or newer, so the mechanism the comment describes cannot occur.

Removing the handler is a code change and was out of PR-30a's scope; the two module
docstrings now say the handler is there and that the mechanism does not occur,
rather than repeating the comment. **Owner: a later cleanup PR, which should decide
whether the tests that import a rule module on its own still need any handler.**

### 4121. The pds3 and pds4 tool twins have already diverged on their mutable defaults, so two of the…

**The pds3 and pds4 tool twins have already diverged on their mutable
defaults, so two of the nine permanent `B006`s are a divergence rather than a
shared-skeleton property.** `pdschecksums.generate_checksums` takes `oldpairs=[]` while
`pds4checksums.py:56` takes `oldpairs=None` and writes `(oldpairs or [])`;
`pdsinfoshelf.generate_infodict` takes `old_infodict={}` while `pds4infoshelf.py:46`
takes `old_infodict=None`. The pds4 side has already adopted the
None-sentinel form that `B006` asks for.

PR-24's exclusion still holds at the two pds3 sites — passing `None`
explicitly raises `TypeError` today and would stop doing so, which is a
behavior change — but the reason given, that the rewrite changes the
signature a frozen tool reports, is one the pds4 twin already contradicts.

This matters because the PR that consolidates these two function pairs into
`_common.py` will have to choose one signature for each. Choosing the pds4
form is the `B006` fix and removes two of the nine.
**Owner: PR-26 (Phase 6).** PR-25 migrated only the archives pair, whose
functions carry no mutable default; both sites are in `pdschecksums.py` and
`pdsinfoshelf.py`, which PR-26 owns.

### 4122. The same constant is defined in nine or ten tool modules

**Ten identical copies of `BACKUP_FILENAME`.** `_common.py` defines it, and so
do all nine tool modules — `pdschecksums`, `pdsinfoshelf`, `pdsindexshelf`,
`pdslinkshelf`, `pdsdependency` and their pds4 counterparts. Measured at PR-26's
head: **one distinct pattern across ten definitions**, character for character:

```
r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d' r'|backup|original)\.[\w.]+$'
```

`_archives_common.load_directory_info` imports the `_common` one; every tool's
own `generate_*` uses its local copy. PR-26 did not consolidate them: the
copies live in the domain functions that stay in the tool modules, and
replacing a module-level constant that nine files define is a sweep of its own,
not a side effect of migrating four `main()`s. The risk it carries is the usual
one for a duplicated constant — nine of the ten can be updated and the tenth
left behind, with no gate that would notice.

**Eight, not ten, from PR-27.** Both index shelf tools defined one and neither
thin module does; the two link shelf tools still do, because each tool's own
`generate_links` reads it. The sweep itself is still owed.
**Owner: open.**

**Nine tool modules still carry a private `LOGROOT_ENV = 'PDS_LOG_ROOT'` and
their own copy of the log-root resolution block.** `pdschecksums.py:24`,
`pdsindexshelf.py:26`, `pdsinfoshelf.py:27`, `pdslinkshelf.py:25`,
`pdsdependency.py:24`, `pds4checksums.py:25`, `pds4indexshelf.py:26`,
`pds4infoshelf.py:27` and `pds4linkshelf.py:26`, each above the same five
lines that read the variable and fall back to `None`.

PR-25a extracted those five lines as `_common.resolve_log_root()` and pointed
`run_main` and `re_validate` at it, so there are two callers today. The other
nine are not this PR's to change — the brief forbids touching another tool
module except where a shared constant moves — and PR-26 and PR-27 retire them
as they migrate each tool onto `run_main`. This entry exists so that the count
is on the record: if either of those PRs lands and the grep still finds nine,
something was missed.

**The count was taken again at `0f5d9ae` and is one, not nine.** The grep returns
one line in `_common.py` and one in `pdsdependency.py` and nothing else, so eight went
as predicted. The ninth is the tool the migration was never going to reach, because
it declares no `ToolSpec` and reaches no driver. a since-resolved observation carries it.
**Owner: recorded, not open.**

**`pdsdependency` is the last module carrying a private `LOGROOT_ENV`, which is the
count a since-resolved observation asked for.** That entry recorded nine tool modules with their own
`LOGROOT_ENV = 'PDS_LOG_ROOT'` and their own copy of the five-line log-root
resolution block, and predicted that PR-26 and PR-27 would retire them as they
migrated each tool onto a shared driver. Measured at `0f5d9ae`,
`grep -rn '^LOGROOT_ENV' --include=*.py src/` returns two lines, one in `_common.py`
and one in `pdsdependency.py`. Eight of the nine are gone. The ninth survived because
`pdsdependency` was never migrated -- it declares no `ToolSpec` and reaches no driver
-- so nothing carried it past. Its inline block is character-for-character the body of
`_common.resolve_log_root()`. **Owner: recorded; amends 106, which can now be closed
against this one file.**

### 4123. The two `move_old_checksums` twins differ in whether their two log lines are forced

**The two `move_old_checksums` twins differ in whether their two log lines are
forced.** `pdschecksums.py:402,405` (at `ab1fa3b`) passes `force=True` to both
`logger.info('Checksum file moved from: ' ...)` and
`logger.info('Checksum file moved to', dest)`; `pds4checksums.py:400,403` (at `ab1fa3b`)
passes neither. `force=True` bypasses the scope's limits, so under a limits
dict that caps `info` the pds3 tool still reports the versioning and the pds4
tool can silently drop it.

Invisible until PR-25, because the pds3 lines were unreachable: `LOGDIRS` was
empty, so the loop that emits them never ran. Now that both tools version, the
divergence is live, and the PR that makes one copy of `move_old_checksums` has
to choose one.

**DECIDED (owner, 2026-08-05): `force=True`.** PR-25 moved
`move_old_checksums` into `_common.py`, so the choice fell here rather than to
PR-26. Versioning a file is a filesystem mutation, and the report of it should
not be droppable by a limits cap; `force=True` is also the spelling that was
already reachable, since the pds3 lines are the ones a run has been emitting
since the `LOGDIRS` fix. **This is a behavior change on the pds4 side**: a
`pds4checksums` run inside a scope that caps `info` now reports the versioning
where before the cap could silence it. Pinned by
`test_common_versioning.py::TestReportingUnderAnInfoCap`, whose control applies
the same `{'info': 0}` cap to a shelf mover that does not force and asserts its
two lines *are* dropped, so the checksum assertion cannot pass by the cap being
inert. Reverting `force=True` in a scratch copy fails exactly that one test.

### 4124. The two shelf-tree fallbacks are written asymmetrically

**The two shelf-tree fallbacks are written asymmetrically.** In
`_local_fs.py`, `os_path_exists`'s "maybe it's in the infoshelf tree" block
probes with `cls.os_path_exists(...)` — the cached, shelf-aware method —
while the parallel block in `os_path_isdir` probes with bare
`os.path.exists(...)`. Both paths are reached only under `SHELVES_ONLY`. The
difference is at least a missed cache and possibly a behavior difference on a
path the shelves know about but the file system does not; deciding which is
correct requires a behavior change, which a move PR may not make. Recorded as
an observation, not a diagnosis. **Owner:** phase "b" of issue #77.

### 4125. Two more near-copies of the preamble exist, and neither is a `setup_run` caller

**Two more near-copies of the preamble exist, and neither is a `setup_run`
caller.** `re_validate.main` (`pds3/re_validate.py`) and
`pdsdependency.main` (`pds3/pdsdependency.py`) each open with the same shape —
build a parser, resolve the log root, build a `PdsLogger`, add the stdout
handler unless `--quiet`, add an error handler under `<log>/<progname>` — and
neither can call `setup_run` as it stands. `re_validate` builds its logger with
a `limits=` argument and has no task flag to refuse; `pdsdependency` interleaves
its own path validation between the two halves, re-inlines
`resolve_log_root`'s body rather than calling it, and carries a second
definition of `LOGROOT_ENV = 'PDS_LOG_ROOT'` beside `_common.py`'s. The
duplicate constant is the part that can drift silently. Out of scope here — this
PR extracted what was identical, not what is merely similar. **Owner: open.**

### 4126. Unreachable and vestigial code in the core

**`PdsFile.from_relative_path`'s empty-path branch is unreachable.** After
`path = path.rstrip('/')` and `parts = path.split('/')`, the guard is
`if len(parts) == 0` (`pdsfile.py:1929`). `''.split('/')` is `['']`, of length
one, so the branch never runs and an empty relative path instead calls
`self.child('')`. **Owner: a future pdsfile PR.**

**`from_path`'s second scanning loop can never take effect.** The loop commented
"among the trailing items of the pseudo-path" reads `part = parts[0].lower()`
(`pdsfile.py:2142`) but pops from the other end, `parts = parts[:-1]` (`:2170`). The
loop before it can only exit by failing to classify `parts[0]`, so this one re-tests
the same element, fails the same way, and breaks on its first iteration every time.
Verified by tracing eight inputs with `sys.settrace`: none of the loop's effect
lines is ever reached. Behaviorally, `from_path('archives/COISS_2xxx')` gives
`archives-volumes/COISS_2xxx` and `from_path('COISS_2xxx/archives')` gives
`volumes/COISS_2xxx/archives`, taking the trailing word as an interior name. Either
the loop should read `parts[-1]` or it should go. **Owner: a future pdsfile PR.**

**`child`'s last `raise ValueError` is unreachable.** `raise ValueError('Cannot
define child from PDS root: ' ...)` sits at `pdsfile.py:1599`, after two blocks
guarded by `if self.category_:` and `if not self.category_:` that are exact
complements and each end in an unconditional `return`. Verified behaviorally: a
blank object routes into the category branch, so `PdsFile().child('volumes')`
succeeds and `PdsFile().child('nonsense')` raises the *voltype* ValueError from
inside that branch rather than this one. **Owner: a future pdsfile PR.**

**`child_of_index`'s cache lookup can never hit.** It builds
`_clean_join(self.abspath, key)` and looks that up as `cls.CACHE[key.lower()]`, but
objects are stored only under `logical_path.lower()`, and the only other keys are the
`$RANKS-`/`$VOLS-`/`$VOLINFO-`/`$PRELOADED` bookkeeping names and the merged category
names. Verified by running: no key in the live cache begins with `/`, the row's own
abspath key is absent, and two identical `child_of_index` calls return distinct
objects. Every index-row request therefore rebuilds the object and re-reads the
table span, including the one each index-row existence test makes. **Owner: a future
pdsfile PR** -- either look up the logical path or drop the branch.

**`archive_logpath` clears a marker the log path never reads.** It copies the object,
sets `checksums_` to `''`, and then rewrites `category_` only inside the
`archives_` branch. The log path is built from `category_`, `bundleset_` and
`bundlename` alone, so the `checksums_` assignment changes nothing: a checksum file
logs under `archives/checksums-volumes/...` rather than under `archives/volumes/...`.
On a `checksums-archives-*` file both markers are set, the archives branch fires, and
the answer still comes entirely from that branch. **Owner: a future pdsfile PR.**

**The pickle rationale for keeping the `class PdsFile` statement in `pdsfile.py` does
not hold for the instances that are actually cached.** The module docstring said that
pickled `PdsFile` instances record `pdsfile.pdsfile` as the class's module, so moving
the statement would invalidate Viewmaster's memcached entries. Pickle records the
module of the **instance's own class**, and every object the package hands out is a
rule subclass: measured, `type(p).__module__` for an ordinary object is
`pdsfile.pds3file.rules.COISS_xxxx`, and the byte string `pdsfile.pdsfile` does not
appear anywhere in `pickle.dumps(p)`. Only an instance of `PdsFile` itself would
record it, and the class docstring says the class is not used directly.

The constraint may still be right for other reasons -- the class attributes the mixins
read are defined in that statement's body -- and the docstring now gives that reason
instead. What is recorded here is that a constraint the plan has treated as
load-bearing since Phase 5 was resting on a claim that does not reproduce, and that
nobody had run `pickle.dumps` on a real object to check it.
**Owner: a future pdsfile PR, if the constraint is ever revisited.**

**`PdsFile.permanent` is written in four places and read in none.** It is
initialized False at `pdsfile.py:506`, set True at `:767` (`new_merged_dir`), at
`:1349` (`_update_ranks_and_vols`) and at `_preload.py:707`, and read nowhere in
`src/` or `tests/`. Its comment says "If True, never to be removed from cache",
which nothing implements: `_complete` has already written the cache entry with an
ordinary lifetime by the time `_update_ranks_and_vols` sets the flag. The
`$RANKS`/`$VOLS` dictionaries themselves really are stored permanently, so the
bookkeeping survives; the objects it points at do not. **Owner: a future pdsfile
PR.**

### 4127. `DictionaryCache.preload_eligible` has no reader

**`DictionaryCache.preload_eligible` has no reader.** It is set True at
`pdscache.py:190`, and no runtime code or test reads it; its only other
appearances are the declaration in `pdscache.pyi` and the docstring that
documents the gap. `MemcachedCache`
has no such attribute, so it is not part of the shared interface either. It is a
public attribute name, so removing it is not free. Same shape as observation 4128.
Scheduled entry 1300 offered PR-35 the alternative of deciding what the stubs
declare; PR-35 decided the stubs declare the runtime surface as it is
(`preload_eligible: bool` in `pdscache.pyi`), because removing the attribute is a
behavior change no stub PR may make. **Owner: a future cleanup PR.**

### 4128. Two exported names are read by nothing

**Two exported names are read by nothing.** `_preload.DICTIONARY_CACHE_LIMIT`
(`_preload.py:101`) is re-exported by `preload_and_cache` and by `pdsfile.pdsfile`,
but every cache in the package is built with `cls.DICTIONARY_CACHE_LIMIT`, a class
attribute defined separately and identically in `pdsfile.py:331`,
`pds3file/__init__.py:169` and `pds4file/__init__.py:143`. Rebinding the module
constant changes nothing. `pdscache.MEMCACHED_LOADED` (`pdscache.py:77`) is read
nowhere; the flag the code actually consults is `_preload.HAS_PYLIBMC`, set by a
second `try: import pylibmc` in a second module. Both names are in the frozen API,
so neither can simply go. Scheduled entry 1301 offered PR-35 the alternative of
deciding what the stubs declare; PR-35 decided the stubs declare both names as they
are (`DICTIONARY_CACHE_LIMIT: int`, `MEMCACHED_LOADED: bool`), because dropping a
frozen name is an API-manifest diff outside the two forgiveness categories.
**Owner: a future cleanup PR.**

### 4129. The two-group `BUNDLESET_PLUS_REGEX` arms and a `None` guard no longer have a caller

**Since `Pds4File.BUNDLESET_PLUS_REGEX` gained the PDS3-shaped tail, both
shipped classes' patterns yield five groups, and three defensive paths are
dead.** `_sorting.py`'s `split_basename()` and `sort_keys()` each branch on
`len(matchobj.groups()) == 2` for a pattern capturing only bundle set +
version; no class defines such a pattern any longer, so the two-group arms are
reachable only from a hypothetical subclass. Likewise the guard
`'' if matchobj.group(2) is None else matchobj.group(2)` in `PdsFile.child()`:
both classes' version groups now capture `''` when empty (PDS3's by an empty
alternative, PDS4's by capturing the whole starred repetition), so the `None`
arm cannot fire. Removing the three is a small cleanup of shared consumer
code; the comments beside the two-group arms already state their status.
**Owner: whoever next touches `_sorting.py` or `child()`.**

### 4130. `src/pdsfile/pds3file/__init__.py`'s alias comment introduces one method instead of eight

**`src/pdsfile/pds3file/__init__.py`'s alias comment introduces one method
instead of eight.** After the `F811` de-duplication removed the seven shadowed
definitions, `# Alias, compatible with old function/property names` sits above
`log_path_for_volset` alone, while its twin `log_path_for_volume` and the alias
properties live below under `# Override functions`. Nothing is wrong — the
comment is still true of the method it introduces — but the two alias groups
would read better merged under one heading. Moving code is not a `ruff check`
fix, so it correctly stayed out of PR-24.

**PR-30a documented both groups where they stand rather than moving anything**
(2026-08-08), since that changes no executable statement. Every one of the
nineteen aliases — thirteen properties and six methods, not the "seven shadowed
definitions plus one" this entry's original framing implies — opens with the
same sentence shape, "The PDS3 name for `bundle...`, whose value it returns", so
the group a member belongs to is legible from the member rather than from the
comment above it, and the class docstring counts them in one place. The
`Raises:` and `Returns:` of each also record where its base member's answer
differs from what the name suggests, which is the thing a merge would not have
supplied. The merge itself is still open, and the two groups are further apart
than when this entry was written, which is an argument for it rather than
against it.

This was scheduled entry 1002, owned by Phase 7 as the phase that owns
docstrings and module structure. Phase 7 documented the aliases and left the
code where it was, correctly: it changed no executable statement anywhere. What
remains is a code move, which no remaining PR of the plan owns, so the entry
belongs after the merge rather than on a schedule. Its line numbers are not
restated here — observation 4405 is the record of what citing them costs, and
the two comments are greppable by their text.
**Owner: a later PR that may move code.**

## Test coverage

### 4200. `show_opus_products --narrow-table` has no test at all

**`show_opus_products --narrow-table` has no test at all.** Replacing
`if not display_narrow_table:` with `if not False:` in the table branch leaves
the three tool-test modules at their full pass count. The flag is exercised by
the out-of-repo tool transcript
(`opus/narrow-table`, byte-identical base to head) and by nothing in the
repository. It is one of PR-13's gaps rather than a PR-28 regression — PR-13
covered the default table, `--pprint` and the opus-type filter, and left this
one — and it is worth a test of its own: the narrow branch builds its rows in a
different shape, with an `if opus_type not in rows` guard comparing a string
against a list of one-element lists, which is always true and so is dead as
written. Deferred 139 records the flag's other quirk, that `--pprint` and
`--raw` accept and ignore it.
**Owner: open.**

### 4201. `show_opus_products` never resolves a PDS4 path in any test

**`show_opus_products` never resolves a PDS4 path in any test.** Commenting out
`Pds4File.preload(pds4_holdings_dir)` leaves
`pytest tests/holdings_maintenance/test_crlf.py
tests/holdings_maintenance/test_show_opus_products.py --mode ns` at its full
pass count. (The measured command also named
`test_shelf_consistency_check.py`, removed with its tool 2026-08-16; none of
its tests touched `Pds4File` or its preload, so the reduced command carries the
same claim.) Every
path the module's tests pass is a PDS3 one, so the second half of the tool's
two-flavor fallback — try `Pds3File`, then `Pds4File`, each by abspath then by
logical path — is exercised only for its failure. The tool tests declare a PDS3
source subset (`subsets.PDS3_VOLUME_SOURCES`) and a PDS4 one exists, so the
missing piece is a fixture that stages both under one tree, not new source
data. Same class as observation 4200: a PR-13 coverage gap in a tool PR-28
restructured but did not otherwise change.
**Owner: open.**

### 4203. `test_pds4file_blackbox.py:138` is a duplicate `parametrize` case

**`test_pds4file_blackbox.py:138` is a duplicate `parametrize` case.**
`PT014` reports it as a duplicate of the case at index 34 — the same
`uranus_occs_earthbased/.../u0_kao_91cm_734nm_radius_six_ingress_100m.xml`
input appears twice in one table. It is permanently excluded in the ratchet
rather than fixed, because removing a case removes a generated test id and
PR-24's gate is an identical id set. Whether the duplicate was meant to be a
different radius or should simply go needs someone who knows the bundle.
**Owner: a test-content PR, not a style PR.**

### 4204. `ToolSpec.extra_arguments` is unexercised in PR-25

**`ToolSpec.extra_arguments` is unexercised in PR-25.** It defaults to `()`,
neither archives tool supplies one, and so `build_arg_parser`'s loop over it
never has a body to run. It is the plan's named hook for the tool-specific
flags (`--archives`, `--infoshelf`), and PR-26 is the PR that needs it.
Recorded so a later coverage or dead-code sweep does not read it as an
oversight — and so that if PR-26 finds the hook is the wrong shape (those
flags also gate chained follow-on steps in `main()`, which a flag-declaration
hook does not reach), replacing it is a deliberate act rather than a surprise.

**Updated 2026-08-05: the unexercised set is now three fields, not one.** On
the owner's ruling ("if a future PR is going to need a field, might as well add
it now") `holdings_sentinel` and `index_ext` joined `ToolSpec`, and neither
archives tool reads either: `holdings_sentinel` belongs to the checksums and
infoshelf tools and `index_ext` to the indexshelf tools. Unlike
`extra_arguments`, these two are *carried* rather than merely defaulted — both
archives specs give their flavor's value — so a sweep sees a value that is
constructed and never read, which is the shape a dead-code check flags. The
`ToolSpec` docstring says so in as many words.
**Owner: PR-26 (Phase 6).**

### 4205. Five measured coverage gaps in the preload machinery, none of which PR-21 may close

**Five measured coverage gaps in the preload machinery, none of which PR-21
may close.** From a `dynamic_context = test_function` coverage run and 19
mutation controls over the moved code:

- **`cache_lifetime` is never executed.** Only its `def` line is covered. It
  is passed as `lifetime=cls.cache_lifetime` by the three `pdscache`
  constructions inside `preload`, and every one of those is on a branch the
  suite does not take, so the lifetime function actually in use is the
  module-level `cache_lifetime_for_class` the class bodies hand to their
  class-level `DictionaryCache`. Mutating `cache_lifetime` to return 0 changes
  nothing.
- **`is_preloading` is never executed and has no caller** anywhere in `src/`,
  `tests/`, `scripts/`, rms-opus or rms-viewmaster. Ground rule 9 keeps it.
- **`cache_category_merged_dirs` can be made a no-op with no effect on the
  suite**, because `preload` caches the same merged directories itself and the
  session fixture always preloads. Its import-time call is a safety net for
  the never-preloaded case, which nothing tests.
- **No test asserts a cache lifetime.** `cache_lifetime_for_class` is reached
  by 116 test functions, but returning "forever" for every argument, or moving
  `DEFAULT_FILE_CACHE_LIFETIME` from 12 h to 13 h, leaves the suite green.
- **No test distinguishes a case-sensitive filesystem from a case-insensitive
  one.** `preload` computes `FS_IS_CASE_INSENSITIVE`; forcing it to the class
  default (`True`) instead of the computed `False` leaves the suite green. The
  flag gates `force_case_sensitive` handling in `_path_utils` and `_local_fs`.

Separately, **30 of `preload`'s 113 statements and 8 of `get_permanent_values`'
21 are never executed** (coverage's own statement set, `def` line included) —
the whole memcached path, the `clear=True` and
`force_reload=True` paths, the already-preloaded early return, and
`get_permanent_values`' bundleset/bundle descent. That is not a gap a test in
this repo can close (it needs a live memcached), and it is recorded so that a
future reader knows what a green full-data run does and does not prove about
`preload`.

PR-21 may not act on any of it — its gate is the pass/fail set, and adding a
test id is movement.
**Owner: unassigned (a future test PR, not Phase 5).**

### 4206. Four parts of the moved OPUS and index-row code are not pinned by the golden tests — measured…

**Four parts of the moved OPUS and index-row code are not pinned by the
golden tests — measured by mutation, not guessed.** PR-19 ran nine mutations
that turn tests red and, deliberately, recorded the ones that do not
(`critiques/phase5-validation.md`, PR-19 §10). Each is 721 passed / 34
skipped, identical to unmutated, in a full-tree copy that asserted it had
imported the mutation:

a. **The `__bases__` sniff's PDS4 branch.** Forced *on*, one test fails;
   forced *off*, nothing does. So the PDS3 side is pinned and the PDS4 side
   is not, on the limited testing copy the goldens are tuned to.
b. **`opus_products`' cross-PDS sibling discovery.** Replacing
   `PdsFile.__subclasses__()` with `[]` — which drops every cross-PDS3/PDS4
   product — changes no outcome. (The *import* that feeds it is pinned:
   deleting the deferred import gives 39 failures. It is the value that is
   not.) `tests/rules/pds3/test_coiss_xxxx.py:54` skips the golden cases that
   would cover this when the pds4 reproj bundles are absent, which is the
   likely cause.
c. **`opus_products`' version ordering.** `new_sublists.sort(...,
   reverse=True)` → ascending changes no outcome, so no golden case has two
   versions of one product.
d. **`data_pdsfile_for_index_row`** — observation 3200, listed here for completeness.

Round 2 of the PR-19 review demonstrated that **(a) is cheap to close**: a
synthetic index-row object with `row_dicts` holding a PDS4-style column name
exercises the branch with no shelf and no PDS4 bundle present, so the test
needs neither the complete holdings set nor the reproj bundles that (b)
waits on. Round 2 ran that probe against the parent tip and against PR-19's
head and got byte-identical answers, which is also an independent check of
the move.

None is a defect in PR-19: all four are properties of the test suite and all
four are equally true on the parent branch. They are the honest answer to
"which parts of this extraction would a regression escape", and (b) is the
one worth acting on first, because cross-PDS product assembly is what OPUS
imports. **Owner: Phase 6** for (a), (c) and (d); (b) additionally depends on
whether the complete holdings set makes those golden cases runnable, so it
belongs with whoever next revisits the pds3/pds4 cross-product goldens.

### 4207. One `MemcachedCache` method has a test; the rest of the class has no gate

**One `MemcachedCache` method has a test; the rest of the class has no gate.**
Measured during PR-23: **28 of the 37** lines that PR changed in `pdscache.py`
are inside `MemcachedCache`, and the full-data suite executes exactly one of
its methods — `set_multi`, because `tests/core/test_pdscache_set_multi.py`
builds an instance with `__new__` and a stub client rather than a connection.
Everything else in the class (`unblock`, `__contains__`, `get_multi`,
`get_now`, `flush`, `clear`, `block`, …) is executed by no test here and by
neither consumer smoke check. Ground rule 9 protects the class (Viewmaster
passes `port=` to `preload`), so it cannot be deleted.

PR-23 closed most of that gap for its own changes with a scratch differential
probe that reuses the same `__new__`-plus-stub technique (see
`critiques/phase5-validation.md`, PR-23 §2), and three changed lines remain
reachable by nothing — `type(port) is str` in `__init__` and the two `F541`
fragments inside `except pylibmc.TooBig` handlers, all of which need
`pylibmc`, which is not a declared dependency. That the probe was easy to
write is the point: **the stub-client technique already in
`tests/core/` generalizes**, and a small `tests/core/test_pdscache_memcached.py`
would give the class a real gate. PR-23 may not add it — its own gate is an
identical test-id set, and a new test id is movement.

It is also why PR-23 freeze-locked the two violations that live there
(`UP031`, `RUF015`) rather than fixing them. Broader than, and related to,
observations 4305 and 4117.
**Owner: phase "b" of issue #77, or whoever revisits the cache layer.**

### 4208. The back-import guard covers the nine mixin modules and not `_path_utils.py`

**The back-import guard covers the nine mixin modules and not `_path_utils.py`.**
`tests/api/test_mixin_import_isolation.py` discovers its subjects from
`PdsFile.__bases__`, which is what makes it pick up a future mixin for free —
and which also means the one private module that is not a mixin is never
probed. `pdsfile.py` imports `_path_utils` at module level exactly as it
imports the mixins, so a module-level `from pdsfile.pdsfile import <name>`
there is the same cycle and is unchecked. (Measured: `_path_utils.py` is clean
today — the same probe run by hand reports `pdsfile.pdsfile` absent.)

a since-resolved observation's wording is "a mixin module must not import `pdsfile.pdsfile` at
import time", so covering `_path_utils` is a **widening** of what was asked
for rather than a gap in what was delivered, and PR-22 did not take it up for
the same reason it did not take up observations 4211 and 4404. The robust form is to
discover every `pdsfile._*.py` module that `pdsfile.py` imports, rather than
every mixin base. **Owner: whichever PR next edits the mixin harness (with
observation 4211).**

### 4209. The maintenance-tool tests run in the `--mode ns` invocation only

**The maintenance-tool tests run in the `--mode ns` invocation only.**
`scripts/automated_tests/pdsfile_main_test.sh` adds
`tests/holdings_maintenance/` to the not-shelves-only pass and deliberately
omits it from the shelves-only pass (recorded as deviation 2 in
`plans/2026-07-25-addendum-holdings-free-marker.md`, owner-accepted
2026-07-26). The justification is that `--mode` flips `use_shelves_only`
inside the pytest process while every tool runs in its own subprocess that
inherits none of it, so the two passes would execute byte-identical work.
**That justification is load-bearing on subprocess invocation and expires
where invocation changes.** PR-28's spec switches the
`shelf_consistency_check` and `show_opus_products` tests to call `main()`
in-process; those tests then run inside the pytest process and *do* observe
`use_shelves_only`, at which point the mode question is live for them and the
single-pass decision must be re-derived rather than inherited. **Owner:
PR-28** (re-derive for the two tools it converts), with **PR-14** noting the
same coupling if it changes how the suite is invoked. a since-resolved observation above is the
related question of what mode a `--mode`-less run selects at all.

**Re-derived by PR-28, and the single pass still holds.** PR-28 converted
`crlf` and the since-removed shelf consistency checker, not
`show_opus_products` (see `plans/2026-08-07-pr-28-deviation-addendum.md`), so
in-process tools now run inside
the pytest process where the original justification assumed none did. The
justification survives on its merits rather than by inheritance: the one
remaining migrated tool imports no PdsFile class at all — `crlf` imports
`argparse` and `sys` — so it cannot read
`use_shelves_only`, and `--mode` cannot change what it does. A second pass
over it would execute byte-identical work, which is what the original
argument claimed for the subprocess case. `support.HOLDINGS_FREE_TOOLS` is
that property written down, and it is asserted by both in-process runners.
The claim expires again if a tool that does read `use_shelves_only` is ever
moved in-process.

**PR-14 note (2026-07-26).** PR-14 leaves
`scripts/automated_tests/pdsfile_main_test.sh` untouched, so the two-pass
split and its `--mode ns`-only tool-test placement are unchanged. It does add
a third invocation, `scripts/run-all-checks.sh`, which runs the whole
`tests/` tree — including `tests/holdings_maintenance/` — once, under
`--mode ns`. That is the same mode the tool tests already ran in, so the
coupling recorded here is unchanged and PR-28 still owns re-deriving it.

### 4211. The new subclass shadowing check names its subjects instead of discovering them

**The new subclass shadowing check names its subjects instead of discovering
them.** `tests/api/test_mixin_collisions.py`'s
`test_no_mixin_is_shadowed_by_a_pdsfile_subclass` is parametrized over the
literal list `[Pds3File, Pds4File]`, so a *third* direct subclass of
`PdsFile` would silently go unchecked — the same narrowness a since-resolved
observation described, one step out. Everything else in that module discovers its
subjects from `PdsFile.__bases__`, which is why every extraction PR inherits
the checks for free.

PR-19 chose the literal list deliberately and the choice is defensible today:
the two subclasses have to be **imported** for `PdsFile.__subclasses__()` to
see them at all, so a discovery-based version would need the same two imports
and could then pass vacuously if an import were dropped — which is exactly
what the test's `assert subclass in PdsFile.__subclasses__()` line exists to
prevent. The robust form is to import the two packages for their side effect,
parametrize over `PdsFile.__subclasses__()`, and keep a separate assertion
that the discovered set is non-empty and contains both. That is a strictly
better test and it is a change to a test file, not to `src/`, so it costs
nothing behaviorally — but it would add or rename ids, and PR-19's gate is an
identical pass/fail set apart from the two ids a since-resolved observation
required.

Round 3 of the PR-19 review added a second half to this entry. The check is
**strict**: it forbids any name a mixin and a subclass both define, and a
future PR that moved into a mixin one of the names `Pds3File`/`Pds4File`
already override would trip it *legitimately*, because that name was shadowed
before the move too. That cannot happen in the rest of Phase 5 — measured, the
34 (`Pds3File`) and 35 (`Pds4File`) such names are class attributes and
translator tables, which the Phase-5 mechanics keep on `PdsFile`, plus
`__init__`, `__repr__` and the four
`use_shelves_only`/`require_shelves`/`set_logger`/`set_easylogger`
classmethods, all of which are on PR-22's explicit stay-list — and the
measurement is recorded in the test's own comment. But whoever generalizes the
check should express the invariant rather than the intersection: what is
actually wrong is a mixin name that is unreachable on the class callers use
*and* was reachable before.
**Owner: PR-20**, or whichever Phase-5 PR next edits the mixin harness.

**PR-20 was directed not to take this up** and did not: the Phase-5
coordinator ruled that observation 4404 (and one since resolved) stay open and that PR-20 build no
new check, which is the scope rule written after PR-17 spent two review
rounds on a voluntarily adopted Deferred item. PR-20 touches no test file at
all. It did re-measure the intersection this entry is about, with its two new
mixins included: empty for `Pds3File`, for `Pds4File` and for all 33 classes
in the hierarchy. **Owner: unchanged — the next Phase-5 PR that edits the
mixin harness.**

### 4212. The shared testing tree carries zero-byte placeholders for every `.tar.gz` and every `*_md5.txt`

**The shared testing tree carries zero-byte placeholders for every `.tar.gz` and
every `*_md5.txt`**, so none of the three programs that read one can be demonstrated
or tested against it as it stands. `pdsarchives --validate` on such a volume ends in
`tarfile.ReadError: empty file`. PR-32's examples were therefore run against a copy
of the tree with the derived products built from scratch, in dependency order, which
is also the only way to show `--initialize` and the versioned copy a `--reinitialize`
leaves behind. Any later measurement of these programs against the shared tree has to
build the products first. **Owner: whoever next documents or tests these programs
against the shared testing tree.**

### 4213. The test holdings hold 6,723 info shelf pickles and no `.py` sidecars at all

**The test holdings hold 6,723 info shelf pickles and no `.py` sidecars at all.**
`_shelves.shelf_lookup()` answers a question about a bundle by reading the sidecar's
second line and has no fallback to the pickle, so that shortcut raises
`FileNotFoundError` against the tree this project tests on. Measured by globbing
`_infoshelf-*/**/*_info.py` under `/seti/opus/pdsdata/holdings`: zero. The published
tree does carry them. Whether the fixture tree should carry sidecars, or
`shelf_lookup()` should fall back, is a question this PR raises and does not answer.
Found by round 3. **Owner: open.**

### 4214. The tests do not pin the maintenance tools' log paths or their values

**The tool tests exercise the log-path builders but do not pin their value,
and coverage cannot see them at all.** The parent plan describes PR-18's
deduplication as "behavior-identical, golden-tested via the tool tests from
PR-13". Measured three ways
(`critiques/phase5-validation.md`, PR-18 §8): a per-test-context coverage run
attributes **no** `tests/holdings_maintenance/` context to any line of
`_derived_paths.py`, because PR-13's harness runs each tool as a subprocess
(`tests/holdings_maintenance/support.py:297`) that in-process coverage does
not follow; the tools nevertheless do call `log_path_for_volume` /
`log_path_for_volset` / `log_path_for_index` unconditionally in `main()`'s
loop, which the log files left in each test tree prove; but **no test in
`tests/holdings_maintenance/` asserts anything about a log filename**, so with
`_log_path_for` deliberately emitting `.LOGWRONG` and a wrong target segment,
four tool-test modules still report 31 passed, exactly as unmutated.

The real regression net is `tests/pds3file/test_pds3file_blackbox.py`'s 41
log-path ids, and PR-18 shows by mutation that it is a live one. Two things
are worth carrying forward anyway. **(a)** A tool test could cheaply assert
the *shape* of the log file it produces — the tools already write it into a
temporary tree the test owns, so the assertion is a `glob` and a regex, and it
would make the tools' own use of the log-path builders a value net rather than
a liveness net. **(b)** More generally, **any future claim of the form "the
tool tests cover X" cannot be checked with in-process coverage**; it needs
either `COVERAGE_PROCESS_START` plumbed into `ToolTree.env` or an assertion on
an artifact. PR-18 chose the artifact, once; a standing answer belongs with the
tests. **Owner: Phase 6**, which is where those tool files are being edited.

**The one piece of code PR-18 changes has no holdings-free coverage at all.**
The hosted lint/no-holdings job runs 80 of the 880 ids and none of them
reaches `_log_path_for`; the whole regression net for the deduplication is
`tests/pds3file/test_pds3file_blackbox.py`'s 41 log-path ids, which need
`PDS3_HOLDINGS_DIR`. So a machine without holdings — which is every stock
GitHub runner, and every contributor the plan's risk table is about — cannot
catch a regression in this code, and the gate that runs there would stay green
through one.

This is a property of the tests rather than of PR-18: `log_path_for_*` is pure
string assembly over `self.disk_`, `self.category_`, `self.bundleset_`,
`self.bundlename`, `self.logical_path` and `cls.LOG_ROOT_`, so it is one of
the easiest things in the package to test without a holdings tree — an
instance built by hand with those six attributes set exercises every branch,
including both `place` values and the `is_index` guard. PR-18 may not add it:
its gate is an identical pass/fail set, and a new test id is movement.

**Owner: Phase 6**, alongside a since-resolved observation, which concerns the same surface from
the other direction — the tool tests run this code but assert nothing about
its output. A single holdings-free test module for the log-path builders would
close both.

**The tool tests contribute no measured coverage unless the run asks for
it.** The suite driver runs `python -m coverage run -m pytest`, and every
maintenance tool runs in a child process, which `coverage run` does not
follow — so what `coverage report` sees of the twelve subprocess-driven tools
is what their imports reach, from 100+ tests that drive far more than that.
Subprocess invocation is load-bearing and cannot be given up (see §2.2 of
`plans/2026-07-25-pr-13-subplan.md`), so the fix is a
`COVERAGE_PROCESS_START` / `sitecustomize` hook in the tests' subprocess
environment. ~~**Owner: PR-14**, which owns CI/coverage correspondence.~~

**CORRECTED 2026-08-17: the fix is built, and the "prohibitive" verdict it
was deferred on measured one configuration and generalized to all of them.**
PR-14's 2026-07-26 deferral recorded an 8.6x slowdown (`8 passed ... in
16.06s` against `138.84s`) and concluded that "the cost is the line tracer
running inside each tool", which is right, and that the cost is therefore
unavoidable, which is not: it is the cost of *that* tracer. Re-measured on
`tests/holdings_maintenance/test_pds3_archives.py` (13 ids), Python 3.12.3,
coverage 7.13.3, against `/seti/opus/pdsdata`, varying only how the children
are measured — pytest's own summary time:

| tool subprocesses | core | branch | pytest summary |
|---|---|---|---|
| uninstrumented | — | — | 10.60s |
| measured | C tracer | yes | 79.68s |
| measured | C tracer | no | 79.94s |
| measured | `sysmon` | yes | 79.26s |
| measured | `sysmon` | no | **12.49s** |

So the 8.6x is real for the C tracer and is **7.5x** here, dropping branch
analysis buys nothing on its own (79.94s), and `COVERAGE_CORE=sysmon` buys
nothing on its own either (79.26s) — because `sys.monitoring` cannot measure
branches on this Python, so coverage warns `Can't use core=sysmon` and falls
back, and in a captured-stderr subprocess nobody sees the warning. Only the
pair is cheap: **1.2x**. And the cost is the tracer, not the subprocesses:
every row runs the same nineteen children — the measured rows each write 20
data files, one per child plus the parent's, and the uninstrumented row runs
the same ids and writes none — so measuring those nineteen adds 1.89s with
`sysmon` and 69.08s with the C tracer.

The trade is therefore not cost against nothing. It is **line-only coverage
at 1.2x against branch coverage plus a permanent blind spot**, and it is
whole-run: `coverage combine` refuses to mix branch data with statement data
(`Can't combine statement coverage data with branch data`), so a run cannot
measure the parent with branches and the children without.

Built by the coverage-mode PR as `scripts/run-all-checks.sh
--coverage-subprocess`: `COVERAGE_PROCESS_START` in `ToolTree.env`, a
`coverage.process_startup()` hook in
`tests/holdings_maintenance/_subprocess_guard/sitecustomize.py` that fails
closed, `parallel` data files and a `coverage combine` step (guarded, because
a holdings root that lacks a declared source subset legitimately produces
zero child data files), and `branch`/`parallel` read from environment
variables substituted into `[tool.coverage.run]` so one config serves both
postures. Measured over the whole suite (1243 ids), like compared with like:

| run | pytest summary | package | tool tree |
|---|---|---|---|
| uninstrumented | 199.02s | — | — |
| `--coverage` (branch, parent only) | 224.34s | 56% | — |
| line-only, parent only (control) | 193.53s | 60% | 34% |
| `--coverage-subprocess` (line-only, 319 children) | 224.76s | **81%** | **78%** |

The 56% → 81% jump is two effects, and the control separates them: 4 points
are the branch denominator leaving, and **21 points are the subprocesses
arriving**. Per module, `pdsarchives.py` goes 16% → 90% and
`_indexshelf_common.py` 11% → 78%.

What is left open is the posture, not the mechanism. The mode is opt-in and
local; the data gate
(`scripts/automated_tests/pdsfile_main_test.sh`) still measures the pytest
process only, and nothing in CI sets `COVERAGE_PROCESS_START`. Whether the
uploaded number should be the line-only one that includes the tools, and what
target it should be held to, is the decision **Owner: PR-37** (Phase 8, "set
codecov targets") still has to make — with the note that the coverage
artifact is uploaded from the 3.13 leg only, so any instrumentation need not
be paid on every leg, and that on a Python without `sys.monitoring` (3.11)
the sysmon request falls back and the mode costs the 7.5x again. PR-28's
conversion of the `crlf` tests to in-process `main()` calls still stands and
is still measured with no subprocess machinery at all. (It left
`show_opus_products` on subprocesses; that half of the original sentence was
a prediction, and `plans/2026-08-07-pr-28-deviation-addendum.md` says why it
did not hold.)

### 4215. Two lines of the preamble are pinned by no test at all

**Two lines of the preamble are pinned by no test at all.** Before this PR no
test drove a driver-backed tool with `--log`, so the handler wiring was pinned
by nothing, in triplicate; `test_driver_setup.py` now pins it. What no test
reaches, measured at `356e055` by deleting each line from `setup_run` and
running `pytest tests/holdings_maintenance` against the full holdings, which
reports the same count green as the unmutated tree:
`spec.pdsfile_cls.set_log_root(args.log)`, whose absence silently empties the
duplicate log tree; and the `if not args.quiet:` guard — `--quiet` is passed to
none of the ten driver-backed tools anywhere in the suite. Both are covered by
this PR's tool-run capture, which is not a thing the repository runs. Also
unreached by any test: the `PDS_LOG_ROOT` fallback arriving at a tool.
`resolve_log_root` itself is unit-tested, but no test sets the variable and
runs one. **Owner: open.**

## Gates, tooling and CI

### 4300. `[tool.pytest.ini_options]` declares no `testpaths`

**`[tool.pytest.ini_options]` declares no `testpaths`.** `python_testing.mdc`
asks for it, and `critiques/deferred-observations.md`'s PR-08 entry already
notes that "whichever PR adds `testpaths`" also owns PR-07's `helper.py`
double-import. Harmless today — every invocation names its paths explicitly,
and `venv/` is in pytest's default `norecursedirs` — so it is a tidiness item,
not a correctness one. Pre-existing since PR-03. **Owner:** the same PR that
restructures `tests/pds{3,4}file/` (see the PR-08 entry above).

### 4301. `check_docstrings.py`'s implicit-receiver rule is wrong for one function in this scope, and the…

**`check_docstrings.py`'s implicit-receiver rule is wrong for one function in this
scope, and the fix was declined rather than taken.**
`COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)` is defined in a class body,
takes no `self`, and is reached off the class at `_opus.py:157` as
`pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)`, so `opus_id` is an
argument the caller supplies. The checker drops the first positional parameter of
any function in a class body that is not a `@staticmethod`, "whatever it is named",
so a `Parameters:` entry for `opus_id` is a P1 and its absence is not a P2. The
argument is documented in prose instead.

PR-29a widened the same rule once already, for a module-level function's `cls`.
Widening it again -- to "drop the first positional only when it is named `self` or
`cls`" -- would reopen the mutation control PR-29a's own record cites, a method
written `def m(this)`, and would put PR-29's 276, PR-29a's 249 and PR-29b's 73 at
risk for one call site. The narrower rule, "drop it unless the name matches the
`N805` ratchet entry that already records this exact function", is a special case
for one file. **Owner: whichever PR next edits the checker; the ratchet's `N805`
row is the standing record that this function exists.**

### 4302. `tests/docs/check_docstrings.py` has no mechanism for a bare `raise`

**`tests/docs/check_docstrings.py` has no mechanism for a bare `raise`.** E1
accepts a `Raises:` entry whose class is raised by name in the body or attributed to a
call, an item read or an unpacking. A bare `raise` with no exception to re-raise
produces a `RuntimeError` that is neither, so documenting it needs a sentence naming
some other call the body makes. `pds4archives.write_archive()` is the one function in
this PR in that position, and its entry attributes the catch rather than the raise. A
`raise` token alongside `unpacking` would close it; the checker is inherited and five
records depend on its numbers, so it is not amended here.
**Owner: a later PR that revises the docstring checkers.**

### 4303. `critiques/pr-29/strip_docstrings.py` cannot answer for a module that was empty

**`critiques/pr-29/strip_docstrings.py` cannot answer for a module that was empty.**
`strip()` replaces a body its removal empties with a single `pass`, so that the tree
stays valid: `node.body = body[1:] or [ast.Pass()]`. A zero-byte module has no body,
the guard above that line never fires, and its stripped tree is `Module(body=[])`; a
module whose whole content is a docstring strips to `Module(body=[Pass()])`. The two
hash differently, and they differ for **any** docstring, so the head hash carries no
information about the change: PR-30a's two new package docstrings, sharing not one
sentence, both hash to `5c04595997820c90`.

PR-30a proved those two files another way -- the head file's entire AST is one string
constant, so it can hold no executable statement -- and left the script alone, since
amending a gate so that it passes is a hard stop and three records depend on its
numbers. The narrowest fix, if one is ever wanted, is to skip the substitution when
the body was already empty. **Owner: whichever PR next documents an empty module.
PR-30b has none; the four remaining `__init__.py` files under
`holdings_maintenance/` are all zero bytes, so PR-30b will meet this twice more.**

### 4304. `run_tests_coverage.sh` at the repo root cannot run

**`run_tests_coverage.sh` at the repo root cannot run.** It invokes
`pytest pdsfile/pds3file/tests/ pdsfile/pds3file/rules/*.py`, paths that
stopped existing when PR-05 moved the package under `src/` and PR-07 moved
the tests to the top-level `tests/` tree. It is one of the `--mode` call
sites PR-14 surveyed (it passes valid modes, so PR-14's `choices` change does
not affect it) and was otherwise left alone. Delete it or update it to the
current layout. **Owner:** whichever PR next touches the root scripts;
PR-37's finalization sweep at the latest.

### 4305. `scripts/gen_ruff_ratchet.py` cannot be exercised against the current tree

**`scripts/gen_ruff_ratchet.py` cannot be exercised against the current
tree.** Its docstring workflow is "re-run this after a shrink and confirm the
diff only removes codes", but it runs `ruff check` with the project config,
whose committed `per-file-ignores` already suppress every violation, so it
emits an empty block. Reproducing a ratchet regeneration therefore requires
clearing the table first, which the script does not do and does not document.
Pre-existing and not touched by PR-16; noted because the ratchet is a
standing §2 gate and PR-23/PR-24 both lean on exactly that workflow when they
shrink the entries to their enumerated freeze-locked sets. **Owner:** PR-23.

### 4306. `src/pdsfile/_version.py` carries a real `RUF022` and no gate can see it

**`src/pdsfile/_version.py` carries a real `RUF022` and no gate can see it.**
The generated file's `__all__` is not sorted, which `ruff check` would report —
but the file is matched by `.gitignore`'s `**/_version.py`, and ruff respects
`.gitignore` by default, so `ruff check src/pdsfile tests scripts` never looks
at it. A lint run over an unpacked sdist, or one passing
`--no-respect-gitignore`, would fail. PR-23 correctly excluded the file from
its scope (generated by setuptools-scm's `write_to`, absent from a fresh
checkout, and not a legitimate ratchet entry), so this is not a PR-23 defect;
it is a gap between what the gate lints and what a consumer receives. Note that
a violation count derived by pointing ruff at `src/pdsfile/*.py` in a tree
where an install has regenerated the file will be one higher than one derived
in a fresh checkout, which is a trap for the next executor.
**Owner: whoever owns packaging/CI hardening (Phase 8).**

### 4307. `support.HOLDINGS_FREE_TOOLS` is a hand-maintained claim, not a derived one

**`support.HOLDINGS_FREE_TOOLS` is a hand-maintained claim, not a derived
one.** It is the set that decides which tools may be driven in-process, and
both `run_tool_in_process()` and `run_tool_without_holdings()` assert against
it — but the assertion only catches a caller naming the wrong tool. It cannot
catch the other direction: if `crlf` ever grows an
import of a PdsFile class, the set is silently wrong and the in-process tests
start resolving temporary-tree paths against the session's preloaded real tree,
which is observation 6607's failure mode with the subprocess boundary removed. The
tool imports nothing but `argparse` and `sys` today. A test that asserts
that — over the module's own import list, not over behaviour — would make the
set self-checking, and is not written here.
**Owner: open.**

### 4308. `test_a_mixin_module_does_not_import_pdsfile_pdsfile`'s 60-second subprocess timeout turns…

**`test_a_mixin_module_does_not_import_pdsfile_pdsfile`'s 60-second subprocess
timeout turns machine load into a test failure.** Each of the nine parametrized
cases spawns an interpreter that imports one mixin module, with
`subprocess.run(..., timeout=60)`. On a machine carrying a load average between 40
and 80 from unrelated work, two of the nine -- `[_index_rows]` and `[_preload]` --
raised `subprocess.TimeoutExpired ... timed out after 60 seconds` in the **base**
tree at `8f8d825`, giving `2 failed, 1099 passed, 34 skipped` where the recorded
baseline is `1101 passed, 34 skipped`. That run took 38m 43s. The same nine cases
pass in 1.64 s when `tests/api/` is run on its own, pass on all four self-hosted CI
legs of this PR's run, and passed when the whole base pass was re-run on a quiet
machine: 4m 49s, `1101 passed, 34 skipped`. The timeout is deliberate --
its comment says it keeps a module that blocks at import time a failure rather than
a hang -- so the question is only whether 60 seconds is the right number for a
machine that is also doing something else. **Owner: a later test PR, if it recurs.**

### 4309. A Sphinx event that fires only when a document was re-read cannot check the source tree

**A Sphinx event that fires only when a document was re-read cannot check the source
tree.** The coverage check first ran from `env-check-consistency`, which
`sphinx/builders/__init__.py` guards with `if updated_docnames:`. Adding a `.py` file
changes no Sphinx source, so an incremental build re-read nothing, the handler never
ran, and `make html` over a tree with a brand-new undocumented module printed `no
targets are out of date` and exited **0** -- the one case the check exists for. The
gate itself was safe, because it runs `make clean` first; a developer's `make html`
loop and any CI that caches `docs/_build` were not. It now runs from
`build-finished`, which fires on every build: the same incremental build prints the
warning and exits **2**. Any later check that reads something outside `docs/`
inherits this trap.

### 4310. The coverage check establishes that a module has a target in the Python domain, which is weaker…

**The coverage check establishes that a module has a target in the Python domain,
which is weaker than establishing that anything of it is published.** An
`automodule` with none of the `:members:` options satisfies it, and so does a bare
`.. py:module::`, and so does a directive on a page outside `docs/api/` -- all three
measured, all three reporting `79 of 79 modules documented` with nothing rendered.
The check's docstring now says so, and `docs/api/index.rst` no longer claims the page
set covers members. observation 4311 is the same limit seen from the other side.

### 4311. The documentation gate counts modules, not members, and five member-level defects pass it

**The documentation gate counts modules, not members, and five member-level defects
pass it.** Each was made and run through the shipped gate: `__all__` narrowed to one
name takes a module's published objects from 6 to 1; dropping `:members:` from one
`automodule` takes `pdscache` from 46 published objects to 0 and leaves the gate's
success line byte-identical to a clean run's; a decorator without `functools.wraps`
replaces a published signature with `(*args, **kwargs)` and deletes its docstring; a
second `automodule` for an already-documented module passes if it carries
`:no-index:` (without it the same edit fails with 47 duplicate-object warnings), and
puts 25 `DictionaryCache` entries on the page titled Tools; and an empty page carried
by the `toctree` is published and appears in the sidebar. Closing these needs an
assertion about published object counts, which is a golden-file gate and a PR of its
own. **Owner: a later documentation PR, if the owner wants it.**

### 4312. Thirty-five of the 78 documented modules are imported by no dependency gate

**Thirty-five of the 78 documented modules are imported by no dependency gate.**
`scripts/check_runtime_imports.py::_module_set()` returns 43 names -- seven fixed top
modules plus the two `rules` packages and their members -- so neither
`pdsfile.holdings_maintenance.*` nor `pdsfile.tools.*` is ever imported without the
`dev` extra present. Demonstrated: `import pytest` added to `pdsarchives.py` leaves
the gate green, ruff clean, and the clean-install gate passing at exit 0; the same
tree with `pytest` unavailable loses **two** modules from the reference (the one with
the import, and one that imports it) and publishes 76 of 78. `.readthedocs.yaml` sets
no `sphinx: fail_on_warning`, so that build succeeds and publishes. observation 3101 is the
live instance of exactly this mechanism, found before the round.
**Owner: a later packaging PR; the cheap fix is to widen `_module_set()`.**

### 4313. Two escape hatches in the coverage check have no guard

**Two escape hatches in the coverage check have no guard.** `_GENERATED_MODULES`
exempts a module by name with nothing asserting that the name is actually generated
or actually absent from disk, so removing a module from its page and adding its name
there is a two-line change that leaves the gate green (demonstrated on
`RES_xxxx`; the same edit on `pdsviewable` fails, but only because five other
docstrings cross-reference `PdsViewSet`). And `_module_names_under` treats every
`.py` file as a module, so a file named `template-example.py` would demand an
`automodule` for `pdsfile...template-example`, a name no directive can document,
with that same exemption set as the only way out. Both are latent: the set holds one
name and no such file exists. **Owner: a later documentation PR.**

### 4314. Two of the gate's three published numbers cannot vary

**Two of the gate's three published numbers cannot vary.** The pass line reads
`N problem lines under -W and M under -n -W`, and under `-W` any `WARNING:` or
`ERROR:` line makes the build exit non-zero, so the success path can only ever
print `0` and `0`. The number that carries information is the coverage line, which
is why the gate requires it and compares the two builds' copies of it. The counts do
carry information on the failure path, where they say how many problems a failing
build reported. This is a property of `-W`, not a defect, and it is recorded so that
nobody reads two zeros as evidence of anything they are not.

### 4315. ~291 data-suite tests pass with no holdings present, and are deliberately not marked…

**~291 data-suite tests pass with no holdings present, and are deliberately
not marked `holdings_free`.** Measured on PR-14's branch by lifting the
blanket skip with a throwaway `tryfirst` plugin that marks every collected
item `holdings_free`, with all four holdings env vars unset:
**315 passed / 387 failed / 122 skipped** — i.e. 291 beyond the 24 the
hosted job ran at the time of the measurement. (PR-15 raised that 24 to 59
by adding 35 genuinely holdings-free tests in `tests/core/`; a re-run of the
forced-marker experiment would collect those same 35 among its passes, so
**the surplus stays 291** and the observation is unchanged.) Grouped by test
*function*: 124 functions have every parametrized case passing, 41 are
**mixed** (some cases pass, some fail) and 126 fail outright. The four
modules involved are `tests/pds{3,4}file/test_pds{3,4}file_blackbox.py`,
`test_pds3file_blackbox_cached.py` and `test_pds3file_whitebox.py`. The
result is not order-dependent: each module run alone yields the same passing
set as it does inside the whole-tree run.

PR-14 did not mark them, for four reasons recorded in §4 of
`critiques/pr-14/validation.md`: they do not build their own inputs (they
concatenate the *resolved* holdings root, which with no holdings is PR-09's
synthetic `/pdsfile-no-holdings/...` placeholder — the test ids contain it,
so they assert against a root that does not exist); the pass/fail split runs
through the middle of parametrize tables, not along module, class or function
lines, so 41 functions cannot be marked at all; nothing pins the
no-filesystem-access property, so a mark is a CI-only tripwire right before
Phase 5 rewrites those very code paths; and the plan's own enumeration of the
subset (§1 G3: "API freeze, tool unit tests, import/collection smoke") does
not include the data suite.

Worth revisiting only together with **issue #92** (move inline
`@parametrize` values into golden files), which is where the tables would be
split into a data-dependent and a path-only half in the first place. #92 is
listed in §9 of the plan as future work outside this effort. **Owner: #92 /
post-merge.**

### 4316. The self-hosted data driver never runs `tests/docs/`, so the documentation gates ride on the hosted job alone

**The self-hosted data driver never runs `tests/docs/`, so the documentation gates
ride on the hosted job alone.** `scripts/automated_tests/pdsfile_main_test.sh`
enumerates the directories of its `--mode ns` pass — `tests/api core
holdings_maintenance pds3file rules/pds3 pds4file rules/pds4` — and `tests/docs/`
is not among them, presumably because the list predates that directory. The
docstring checker and the silent-markup check therefore run in CI only where the
hosted lint job's `run-all-checks.sh` invocation collects the whole tree. Nothing
is uncovered today — the lint job runs on every pull request — but the driver's
enumeration silently excludes any future test directory too, where the gate
script's `pytest tests` cannot. Found by PR-33's round-1 reviewer while checking
the developer guide's CI chapter, which now states the enumeration instead of
calling the driver a superset. **Owner: whichever PR next edits the driver.**

### 4317. The one-colon-directive check does not know `mermaid`, the one directive whose loss is a whole diagram

**The one-colon-directive check does not know `mermaid`, the one directive whose
loss is a whole diagram.** `tests/docs/test_markup.py`'s `_DIRECTIVES` frozenset
enumerates the directive names whose one-colon misspelling (`.. note:` for
`.. note::`) it reports, and `mermaid` is not among them — the list predates the
developer guide, which introduced the repository's first `.. mermaid::` blocks. A
future `.. mermaid:` typo would be parsed as an RST comment and silently delete the
diagram from the built page, and neither Sphinx build, this gate, nor anything else
would report it. The fix is one word in the frozenset, plus whatever other
extension directives the tree has gained by then. Found by PR-33's round-3
reviewer. **Owner: whichever PR next edits the docs gates.**

### 4318. The Markdown gate reads two files, and its directory arguments select nothing

**The Markdown gate reads two files, and its directory arguments select nothing.**
`pymarkdown scan` selects by the `.md` extension and does not recurse into a
directory argument, so of the four scan paths `run-all-checks.sh` passes —
`docs/`, `.cursor/`, `README.md`, `CONTRIBUTING.md` — the two directories
contribute no file: `docs/` holds no `.md` at any depth, and `.cursor/`'s five
Markdown files (four skills' `SKILL.md` plus one `reference.md`) sit two levels
down. The gate prints the selection before scanning and fails on an empty one, so
its true scope — `README.md` and `CONTRIBUTING.md` — is stated on every run
rather than implied by the argument list. Measured with `-r` added: the five
nested files carry **130** findings, of which 95 (`MD041`/`MD003`/`MD022`/`MD026`)
are one artifact — PyMarkdown reads the skills' YAML front-matter block as a
setext heading, which the `front-matter` extension in `[tool.pymarkdown]` would
correct — and the residue is 17 `MD036` + 17 `MD032`, all in `reference.md`,
plus one `MD040` in the run-all-checks skill's `SKILL.md`. Whether the skills
are worth linting is a decision nobody has taken;
`CODE_OF_CONDUCT.md` is likewise outside the selection.
**Owner: a future decision, if the gate's scope is ever widened.**

## Documentation and records

### 4400. `_common.LOGDIRS`'s comment names a caller that does not exist

**`_common.LOGDIRS`'s comment names a caller that does not exist.** It says
"any other tool that versions a file does it in its own `main()`". No other tool
does: `set_log_dirs` is called at `_common.py` and `_shelf_common.py` only, and every
`move_old` caller is one of the eight tools those two drivers serve. Identical at
`80f5e52`, so pre-existing. **Owner: a later maintenance-tool PR; PR-30a changes no
comment whose block it did not move.**

### 4401. `_local_fs.glob_glob()`'s `Raises:` is narrower than its own prose

**`_local_fs.glob_glob()`'s `Raises:` is narrower than its own prose.** It omits the
`AssertionError` its last paragraph describes, and it attributes `OSError` to the
shelf-backed branch alone; with SHELVES_ONLY off, the filesystem branch reaches
`os_listdir` through the case repair and raises there too, which round 4 reproduced
with a `PermissionError` on both the wildcard and the no-wildcard path.
`_local_fs.os_path_exists()` has the same shape of gap for its own unguarded
`os.listdir(parent)`. PR-30a's `Pds4File.archive_dirs()` inherited the narrower claim
and now states the wider one; the two source docstrings are out of scope here.
**Owner: a later PR that revisits `_local_fs.py`.**

### 4404. The mixins' "state contract" docstrings are hand-written, drift, and are mechanically derivable

**The mixins' "state contract" docstrings are hand-written, drift, and are
mechanically derivable.** Each Phase-5 mixin opens with a paragraph naming
the PdsFile attributes, properties and sibling-mixin methods its bodies
reach. That paragraph is the only place a reader can learn what a mixin
depends on, and it is the only part of a mixin module that is *not* checked
by anything: PR-19's rounds 1 and 2 each found the `_IndexRowsMixin` version
wrong or incomplete — round 1 that three names it called lazy properties are
plain instance attributes, round 2 that it omitted two properties, one class
attribute and one write. Both were fixed by deriving the list from the AST
instead of writing it; the derivation is about twenty lines.

`tests/api/test_mixin_collisions.py` cannot catch this: it checks what a
mixin *defines*, never what it *reads*. A read-side check — walk each mixin
module's AST for `self.X` / `cls.X`, and assert every name resolves on
`PdsFile` or on a sibling mixin — would catch both the drifting docstring and
a genuinely stranded attribute, which is the failure mode the whole "class
attributes stay on `PdsFile`" rule exists to prevent and which nothing
currently verifies.

PR-19 did not build it: the mixin harness is a test file it touches only for
a since-resolved observation, and a new check is a new test id, which its gate
forbids beyond the two that observation required. Building a check the plan did not ask for is also the
failure mode PR-17 paid two rounds for. **Owner: PR-22**, which adds the last
and largest mixin (`_PropertiesMixin`) and is where a stranded attribute is
most likely.

**Round 3 of the same review found a third instance**, which is the argument
for treating this as due rather than optional: `_OpusMixin`'s list omitted
`version_rank`, read as `li[0].version_rank`, because the AST walk that
produced the list followed `self.X` and `cls.X` but not an attribute on a
*subscript*. A derivation that runs in a test would have to walk every
`Attribute` node and resolve the root of its value expression, and would have
to scope the claim to PdsFile-side names so `str`, `list` and translator
methods do not swamp it. PR-19's scratch harness now does both and verifies
both docstrings complete in both directions.

Round 4 added the last piece such a check will need: it must exclude the
names the mixin **itself** defines. `_IndexRowsMixin`'s methods call each
other -- `child_of_index` calls `find_selected_row_key` and `get_indexshelf`,
`data_abspath_associated_with_index_row` calls `child_of_index`,
`data_pdsfile_for_index_row` calls it in turn -- so a naive walk reports four
`self.X` reads that are not external dependencies at all. PR-19's docstrings
exclude them, which is why they list no method the mixin defines; an
automated version has to do the same or it will emit four false positives on
this module alone.

Round 2 also noted that `_version` appears in `dir(pdsfile)` on this branch
and not in the manifest. It is a gitignored `setuptools-scm` build artifact
present in the working tree, identical on the parent branch, and not an
effect of any Phase-5 PR. Recorded here so a later round does not re-derive
it; no owner, no action.

### 4405. Two live plan documents cite line numbers inside rule modules, and both were already stale…

**Two live plan documents cite line numbers inside rule modules, and both were
already stale before this PR.** `plans/2026-07-25-modernization-plan.md` cites
`COVIMS_0xxx.py:324` for `OPUS_ID_TO_PRIMARY_LOGICAL_PATH`, which was line 326 at
`c4811d8` and is 377 at head; `plans/2026-08-04-pr-24-subplan.md` cites
`uranus_occs_earthbased.py:535`, `COVIMS_0xxx.py:325`, `COCIRS_xxxx.py:516` and the
two `rules/__init__.py` `__all__` lines. Both are records of a decision already
taken rather than live instructions, so neither is corrected here; observation 6106, which is a live record, is. **Owner: process -- a plan that cites a
line number is a plan that will be wrong, and naming the symbol instead costs
nothing.**

### 4406. `tests/conftest.py`'s `--mode` comment says `s` covers pds3 only

**`tests/conftest.py`'s `--mode` comment says `s` covers pds3 only.** The
comment above `pytest_addoption` reads "'ns' is the default because it is the
broader pass: every test directory runs under it, while 's' covers pds3 only."
The second half is stale: the pds4 shelves-only pass runs and passes
(`tests/pds4file tests/rules/pds4 --mode s` — 123 passed, 31 skipped at the
current baseline), and the developer guide's test-suite chapter and
`CONTRIBUTING.md` both document the three-invocation pattern with a pds4 `s`
pass. The claim was true of the self-hosted CI driver, which runs a pds3-only
`s` pass — a property of that driver, not of the option. Found by PR-34's
round-1 reviewer. **Owner: whichever PR next edits `tests/conftest.py`.**

### 4407. The plan's gate list and compliance schedule have drifted from the tree they govern

**Two rows of `plans/2026-07-25-modernization-plan.md` describe a tree that has
moved on.** §2's validation-gate table has no `stubtest` row, and the sentence
below it gives the enabled set as "ruff-check, pytest, pyroma, api-freeze,
clean-install, sphinx, pymarkdown" — seven flags, where
`scripts/run-all-checks.sh:139` defaults `ENABLE_STUBTEST` to `true` and runs
`python -m mypy.stubtest` at `:585`. The gate arrived with the public-API stubs
and is the thing that checks them, so the omission drops a gate rather than
mislabelling one; and the same sentence names `run-all-checks.sh` as "the single
source of truth for the enabled set", which makes the plan contradict the
authority it cites.

§6.6's progressive-compliance schedule still carries the pre-deviation-(3)
waiver list: its row reads `python.mdc` "modules < 1000 lines" waived for
"`pdsfile.py`, `_properties.py`, `pdscache.py`, and the rule modules". Module
length has been two limits since the owner's 2026-08-07 decision — 1,000 code
lines and 2,000 total — and `pdsfile_overrides.mdc` (3) now enumerates exactly
four waived files: `pdsfile.py`, `_properties.py`,
`holdings_maintenance/pds3/pdsdependency.py` and `pds3file/rules/VG_28xx.py`,
each with its own issue (#141–#144). The row is wrong in both directions: it
still waives `pdscache.py`, which deviation (3) retires by name ("is no longer
waived", at 1,914 total and 937 code); it waives "the rule modules" as a class,
where deviation (3) keeps the list enumerated precisely so that no rule module is
exempted without a decision and only `VG_28xx.py` is on it; and it omits
`pdsdependency.py` entirely.

Neither row is load-bearing on behaviour — the enforced copies are
`run-all-checks.sh` and the overrides file, and both are right — but the §6.6 row
sits directly under the sentence naming the authorities on "what is in force
when", one of which is `pdsfile_overrides.mdc` itself, so a reviewer who reads the
schedule instead of the file it summarises gets the pre-2026-08-07 rule. That is
the one place a stale waiver list can change a verdict. Same class
as observation 4405, and the same cause: a record that describes the tree rather
than instructing it, left behind because nothing re-reads it. Raised by PR-36's
review rounds and left for the owner there, since the plan is a governing
document; recorded here so it is not re-derived.
**Owner: whichever PR next edits the plan — PR-37's finalization sweep is the
natural one.**
