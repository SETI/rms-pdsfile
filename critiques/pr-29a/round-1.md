# PR-29a adversarial review — round 1

Files under review: `src/pdsfile/_derived_paths.py`, `src/pdsfile/_shelves.py`,
`src/pdsfile/_path_utils.py`, `src/pdsfile/_index_rows.py`.

Executable code treated as ground truth; only docstring prose is on trial. Several
findings were confirmed by executing against `/seti/opus/pdsdata/holdings`; those are
marked "demonstrated" and the command output is summarized inline.

---

## CODE DEFECTS

### C1. `_shelves.py` — the shelf LRU counter is per-subclass, so the shelf just opened can be evicted immediately

`_get_shelf` does `cls.SHELF_ACCESS_COUNT += 1` (`_shelves.py:284` and `_shelves.py:314`)
where `cls` is whatever class the call was made on. `SHELF_ACCESS_COUNT` is an **int**
defined on `PdsFile` (`pdsfile.py:2384`), so `+=` **rebinds it onto the calling class**,
while `SHELF_CACHE` / `SHELF_ACCESS` / `SHELF_NULL_KEY_VALUES` are **dicts** that are
mutated in place and therefore genuinely shared. Callers reach `_get_shelf` through
`cls = type(self)`, which for real objects is a per-bundleset *rule* subclass. Each rule
subclass therefore keeps its own counter, all starting from 0, all writing serial numbers
into one shared `SHELF_ACCESS` dict.

Demonstrated:

```
COISS_xxxx  own SHELF_ACCESS_COUNT = 3      PdsFile.SHELF_ACCESS_COUNT = 0
COVIMS_0xxx own SHELF_ACCESS_COUNT = 1      Pds3File own = None
SHELF_ACCESS: {COISS_2001_index.pickle: 3, COVIMS_0001_index.pickle: 1}
```

The COVIMS shelf was opened *after* the COISS one and carries the *lower* serial. With
`SHELF_CACHE_SIZE = 1, SHELF_CACHE_SLOP = 0`, opening the COVIMS shelf last leaves the
cache holding `['COISS_2001_index.pickle']` — the shelf that had just been opened was the
one discarded.

This directly falsifies `_shelves.py:261-262` (see P10) and undercuts the "so every
subclass shares one cache" framing at `_shelves.py:105-108`. Note that
`_derived_paths.py:47-49` makes exactly this point about `LOG_ROOT_` and `_LOG_TIMETAG`
("each onto the class the call was made on rather than onto PdsFile"), so `_shelves.py`'s
silence here is an asymmetry, not a convention.

Consequence: the cache trim is not LRU at all across subclasses; it evicts by
subclass-local activity. Confidence: **certain**.

### C2. `_index_rows.py:285-289` — `child_of_index`'s cache lookup uses a key kind the cache never holds

```python
new_abspath = _clean_join(self.abspath, key)
try:
    return cls.CACHE[new_abspath.lower()]
```

`self.abspath` is absolute, so the key begins with `/`. Objects are only ever stored in
`CACHE` under `self.logical_path.lower()` (`pdsfile.py:1288`); the only other keys are the
`$RANKS-*` / `$VOLS-*` / `$VOLINFO-*` / `$PRELOADED` bookkeeping keys and the merged
category names. No stored key can begin with `/`.

Demonstrated: after building a row, `row.abspath.lower() in Pds3File.CACHE` is `False`,
`row.logical_path.lower() in Pds3File.CACHE` is `False`, and none of the 28 live cache keys
starts with `/`.

So the `try` at `_index_rows.py:286-289` always raises `KeyError` and always falls
through. Every index-row request rebuilds the object and re-reads the table span, including
the one `_LocalFsMixin.os_path_exists` makes for each index-row existence test
(`_local_fs.py:153`). Confidence: **certain**.

The docstring documents the intent as though it worked; see P26.

### C3. `_index_rows.py:167` — the invalid-flag guard raises the wrong exception type

```python
raise ValueError(f'Invalid flag "{flag}"' % flag)
```

The f-string is already interpolated, and `%` is then applied to a string with no
conversion. Demonstrated: `flag='bogus'` → `TypeError: not all arguments converted during
string formatting`. The docstring correctly identifies this (`_index_rows.py:141-144`), so
it is reported here as a code defect rather than as wording. Confidence: **certain**.

Note the docstring's claim is *not* universal — see P22.

### C4. `_shelves.py:140-217` — `shelf_type='index'` builds a path where no index shelf lives

`SHELF_PATH_INFO['index'] = ('_indexshelf-', '_index')` (`pdsfile.py:294`), so
`shelf_path_and_lskip('index')` for `metadata/COISS_2xxx/COISS_2001` returns

```
.../holdings/_indexshelf-metadata/COISS_2xxx/COISS_2001_index.pickle
```

but index shelves are written one per **index table**, by `indexshelf_abspath`
(`_properties.py:308-330`, writer at `_indexshelf_common.py:133-144`), at

```
.../holdings/_indexshelf-metadata/COISS_2xxx/COISS_2001/COISS_2001_index.pickle
```

(confirmed on disk: `_indexshelf-metadata/COISS_2xxx/` contains *directories*, not
`*_index.pickle` files). Nothing in `src/` or `tests/` ever passes `'index'` to
`shelf_path_and_lskip` / `shelf_path_and_key` / `shelf_lookup` — every call site passes
`'info'` or `'link'` — so this is a latent trap rather than a live bug, but the three
docstrings advertise `'index'` as one of the supported values
(`_shelves.py:159`, `:228`, `:384`, `:453`) without saying the path it produces never
exists. Confidence: **certain** on the path mismatch; **likely** that this should be
called out rather than documented as supported.

### C5. `_index_rows.py:375` — the PDS3/PDS4 discrimination fails for the registered default PDS4 class

```python
if cls.__bases__[0].__name__ == 'Pds4File':
```

`Pds4File.SUBCLASSES['default'] = Pds4File` (`pds4file/__init__.py:215`) and
`Pds4File.__bases__ == (PdsFile,)`. Confirmed: `VOLSET_TRANSLATOR.first('<unregistered>')`
returns `'default'`, and only six PDS4 bundlesets have rule modules. So an index row in any
unregistered PDS4 bundleset is an instance of `Pds4File` itself, whose first base is named
`'PdsFile'`, and it silently gets the **PDS3** column-name tables — which differ (PDS3 adds
`product_id`, `stsci_group_id`, and a different volume-column list). The docstring's
`_index_rows.py:70-75` acknowledges generic fragility but does not say that the class the
registry hands out by default is one of the failing cases. Confidence: **likely** (reachable
by construction; I did not find a live PDS4 index table in the test holdings to exercise it).

### C6. `_derived_paths.py:325-331` — `archive_logpath` clears `checksums_`, which has no effect on the result

`this.checksums_ = ''` (line 326) is dead with respect to the returned path:
`log_path_for_bundle` → `_log_path_for` reads only `category_`, `bundleset_` and
`bundlename` (`_derived_paths.py:501-503`), and `category_` is only rewritten in the
`archives_` branch (line 329). Demonstrated:

```
checksums-volumes/COISS_2xxx/COISS_2001_md5.txt
  -> /logs/archives/checksums-volumes/COISS_2xxx/COISS_2001_targz_<t>_mytask.log
```

The `checksums-` component survives into the log path. Either the assignment is vestigial
or `category_` should also be rewritten for checksum files. Confidence: **certain** that the
assignment is inert; **worth checking** whether the intended behavior is the one the
docstring describes. See P3.

---

## PROSE DEFECTS

### `_derived_paths.py`

**P1. `_derived_paths.py:9-10`, module docstring — `documents` has neither parallel.**

> "``archives-volumes/`` holding one ``.tar.gz`` per bundle, and the same pair exists for
> every other category."

`construct_category_list()` (`_path_utils.py:70-80`) explicitly removes
`checksums-documents`, `archives-documents` and `checksums-archives-documents`. Verified:
`construct_category_list(['volumes','documents'])` →
`['volumes', 'documents', 'archives-volumes', 'checksums-volumes',
'checksums-archives-volumes']`. The `documents` tree has neither member of "the same pair",
and `_shelves.py:503-505` and `_local_fs.py:157` both treat documents as the exception.
Confidence: **certain**.

(Related, same sentence, line 10: "So a file has a checksum file that covers it and an
archive file that contains it" — a bundleset-level file has no archive at all;
`archive_path_and_lskip` raises `ValueError` for it, as this file's own line 225 says.)

**P2. `_derived_paths.py:82-83`, `checksum_path_and_lskip` — it is the bundle type, not the category.**

> "a file under ``volumes/`` or ``bundles/`` gets none, and anything else gets the category
> name without its trailing slash, so a metadata bundle yields ``..._metadata_md5.txt``."

The code is `suffix = '_' + self.bundletype_[:-1]` (line 104), and
`category_ = checksums_ + archives_ + bundletype_` (`pdsfile.py:2225`), so the two differ
whenever `archives_` or `checksums_` is set. Demonstrated: for
`archives-metadata/COISS_2xxx/COISS_2001_metadata.tar.gz` (`category_ =
'archives-metadata/'`, `bundletype_ = 'metadata/'`) the result is
`checksums-archives-metadata/COISS_2xxx_metadata_md5.txt` — `_metadata`, not
`_archives-metadata`. The sibling method's docstring gets this right
(`_derived_paths.py:209-210`: "the volume type before it"). Confidence: **certain**.

**P3. `_derived_paths.py:308-310`, `archive_logpath` — clearing the checksum marker changes nothing.**

> "it is filed by what was archived rather than by the archive: a copy of this
> object is made with its checksum marker cleared, and, if it is an archive file,
> with its archive marker cleared and its category replaced by its bundle type."

The reader is told the copy is normalized so the log is filed by what was archived. In
fact only the `archives_` branch touches `category_`, which is the only thing the log path
reads. See C6 for the demonstration: a checksum file still logs under
`archives/checksums-volumes/...`. Confidence: **certain**.

**P4. `_derived_paths.py:409-410`, `_log_path_for` — the three methods differ in a third way.**

> "The three log_path_for_* methods differ only in the parts that name their
> target and in whether they accept a suffix."

`log_path_for_index` also defaults `dir` to `'index'` rather than to `''`
(`_derived_paths.py:532`), which this file's own line 540-541 calls out as significant
("The subdirectory defaults to ``index`` rather than to nothing"). Demonstrated:
`log_path_for_index(task='t')` → `/logs/index/metadata/...` vs
`log_path_for_index(task='t', dir='')` → `/logs/metadata/...`. Confidence: **certain**.

**P5. `_derived_paths.py:342-346`, `set_log_root` — an empty string is neither "None" nor a directory.**

> "A root is stored with exactly one trailing slash, however many it was given.
> None means there is no default..."

`''.rstrip('/') + '/'` is `'/'`. Demonstrated: `set_log_root('')` leaves
`LOG_ROOT_ == '/'`, i.e. every log path is then built at the filesystem root, not "no
default". The tools normalize `''` to `None` before calling
(`holdings_maintenance/_common.py:167-171`), which is exactly the trap the docstring should
name. Confidence: **likely** (the sentence is not false, but a caller acting on "however
many it was given" plus "None means there is no default" will get this wrong).

### `_shelves.py`

**P6. `_shelves.py:8-9`, module docstring — index shelves are not per-bundle and not keyed by interior path.**

> "A shelf file is a pickled dictionary covering one bundle, or one bundle set of archives,
> and it is keyed by the interior path of each file below that bundle."

True for info and link shelves; false for index shelves, which cover **one index table**
and are keyed by **row selection keys** — as this same docstring says four lines later
(line 16-17). On disk: `_indexshelf-metadata/COISS_2xxx/COISS_2001/` holds
`COISS_2001_index.pickle`, `COISS_2001_moon_summary.pickle`, etc. — four shelves for one
bundle. Writer: `_indexshelf_common.py:133-144` via `indexshelf_abspath`. Confidence:
**certain**. (See also C4.)

**P7. `_shelves.py:114-115`, class docstring — this layer does reach a sibling mixin.**

> "This is the innermost layer: nothing here reaches a sibling mixin, which is
> what lets _LocalFsMixin call into it without a cycle."

`info_shelf_expected` reads `self.is_documents` (`_shelves.py:521`), which is defined on
`_PropertiesMixin` (`_properties.py:171-175`) — a sibling mixin, listed as such by
`_properties.py:105-112`. And the reach is mutual: `_properties.py:105-109` records that it
calls `info_shelf_expected`, `shelf_lookup` and `shelf_path_and_key_for_abspath` *from*
`_ShelfMixin`. The cycle happens to be harmless only because `is_documents` is a pure
attribute read. Confidence: **likely** — the package's convention is to list properties
separately from "other methods", so the enumeration is defensible, but the flat assertion
"nothing here reaches a sibling mixin" plus its causal clause is not.

**P8. `_shelves.py:126-127`, class docstring — three dictionaries are mutated, not four.**

> "The four dictionaries are mutated rather than rebound, so they are reads"

The four dicts named in the "class attributes read" list are `SHELF_ACCESS`, `SHELF_CACHE`,
`SHELF_NULL_KEY_VALUES` and `SHELF_PATH_INFO`. Only the first three are ever mutated
(`_shelves.py:285, 312, 315, 316, 353, 354, 431`); `SHELF_PATH_INFO` is only subscripted
for reading (`:182`, `:471`). Confidence: **likely**.

**P9. `_shelves.py:105-108` + `:125-126`, class docstring — omits where the counter is rebound.**

> "...it is defined on PdsFile itself, so every subclass shares one cache: ...
> SHELF_ACCESS_COUNT issues those serial numbers..."
> "class attributes WRITTEN SHELF_ACCESS_COUNT, which is rebound on every use."

Rebound *onto the calling class*, which is a rule subclass, so the counter is emphatically
**not** shared. See C1. Confidence: **certain**.

**P10. `_shelves.py:261-262`, `_get_shelf` — the just-opened shelf can be the one discarded.**

> "The shelf just opened is the most recently used, so it is never the one discarded."

Demonstrated false (C1): with `SHELF_CACHE_SIZE=1, SLOP=0`, opening a COVIMS shelf after
five COISS accesses leaves the COISS shelf cached and drops the COVIMS one that had just
been opened. Confidence: **certain**.

**P11. `_shelves.py:277-279`, `_get_shelf` — the original exception *is* reported.**

> "The second case replaces the original exception rather than chaining it, so what went
> wrong is not reported."

`raise OSError(...)` inside `except Exception:` sets `__context__` implicitly, and the
default traceback prints the original under "During handling of the above exception,
another exception occurred". Demonstrated. What is missing is only the explicit
`raise ... from e` (i.e. `__cause__`); the diagnosis is not lost. Confidence: **certain**.

**P12. `_shelves.py:160-161`, `shelf_path_and_lskip` — the `bundlename` argument is ignored for archives.**

> "bundlename (str): a bundle below this one to build the path for, with any
> trailing slash ignored. An empty string uses this file's own bundle."

In the `if self.archives_:` branch (lines 184-193) the argument is never referenced — the
path is the bundle set's shelf whatever is passed. Worse, `shelf_path_and_key` then still
returns `''` for the key because `bundlename` is truthy (`:243-244`), so
`shelf_lookup('info', bundlename='X')` on an archive object silently answers about the
bundle *set*, not about `X`. Confidence: **certain** on the behavior; the omission is
actionable because `_properties.py:526` is exactly the "ask about one of my bundles" call
site.

**P13. `_shelves.py:441-442`, `shelf_path_and_key_for_abspath` — it does not always answer the same question.**

> "This answers the same question as ``shelf_path_and_key()`` by taking the path apart
> directly..."

Demonstrated divergence for the documents tree, where `child()` leaves `bundlename` empty
(`pdsfile.py:1493-1496`):

```
documents/COISS_2xxx/COISS-Cheat-Sheet.pdf
  instance : ValueError  Non-archive shelves require bundle names: ...
  classmeth: ('.../_infoshelf-documents/COISS_2xxx/COISS-Cheat-Sheet.pdf_info.pickle', '')
```

One raises; the other returns a path that cannot exist. (`_local_fs.py:157` compensates by
excluding documents before it calls, which is why this has not bitten.) Confidence:
**certain**.

**P14. `_shelves.py:503-505`, `info_shelf_expected` — bundle-set-level *directories* are also excluded.**

> "Four things have none: ... and a bundle-set-level file, including its AAREADME."

The final `return bool(self.bundlename)` (line 534) is False for a bundleset **directory**
in a non-archive category too, e.g. `volumes/COISS_2xxx` — and correctly so, since
non-archive info shelves are per-bundle. A reader working from the enumeration would expect
a bundleset directory to be in the "everything else" case. Confidence: **likely**.

**P15. `_shelves.py:23-25` vs `:102`, module vs class docstring — who holds the cache.**

> module: "``_ShelfMixin`` holds three things: ... a cache of open shelves shared by every
> PdsFile subclass..."
> class: "A mixin of PdsFile; it holds methods only and defines no state of its own."
> class: "The open-shelf cache ... is defined on PdsFile itself"

The two readings of "holds" are in tension in adjacent docstrings for the same class.
Confidence: **worth checking** (low severity).

**P16. `_shelves.py:129`, class docstring — `is_documents` is not lazy.**

> "lazy properties read        is_documents"

`is_documents` (`_properties.py:171-175`) is `return self.bundletype_ == 'documents/'` — no
`_..._filled` slot, no `_recache()`, recomputed on every access. `_properties.py:98-100`
distinguishes exactly this ("none of them lazy in the sense above; they hold no slot"). A
reader told it is lazy would assume the value is cached on the object. Confidence:
**worth checking** (the file's taxonomy may be location-based rather than
laziness-based, in which case this is only a naming collision).

### `_path_utils.py`

**P17. `_path_utils.py:12`, module docstring — three, not four.**

> "Four of the functions convert between the two ways a file is named."

The sentence then names three: `logical_path_from_abspath`, `abspath_for_logical_path`,
`selected_path_from_path` (lines 16-18). The very next paragraph ("The rest are
utilities...") names the other **seven** of the module's ten functions:
`construct_category_list`, `repair_case`, `formatted_file_size`, `_clean_join`,
`_clean_abspath`, `_clean_glob`, `_needs_glob`. 3 + 7 = 10. Confidence: **certain**.

**P18. `_path_utils.py:7`, module docstring — `_clean_glob` holds state.**

> "Nothing here is a method and nothing here holds state."

`_clean_glob` is `@functools.lru_cache(maxsize=_GLOB_CACHE_SIZE)` (line 145) and its own
docstring (lines 149-152) is entirely about the state it holds and the staleness that
follows. Confidence: **likely**.

**P19. `_path_utils.py:59`, `construct_category_list` — `voltypes` is iterated four times.**

> "voltypes: the volume type names, iterated once."

The `for voltype in voltypes` loop is nested inside two two-element loops (lines 71-74), so
it runs four times. This is actionable: demonstrated that passing a generator produces
`['volumes','documents']` only and then dies with
`ValueError: list.remove(x): x not in list` at line 77. Confidence: **certain**.

**P20. `_path_utils.py:87-89`, `logical_path_from_abspath` — only with a trailing slash.**

> "An absolute path that ends at the holdings directory itself yields an empty string"

The partition token is `'/holdings/'`. Demonstrated: `'/a/b/holdings/'` → `''`, but
`'/a/b/holdings'` → `ValueError('Not compatible with a logical path: ', '/a/b/holdings')`.
The sentence as written covers the more natural spelling of "ends at the holdings
directory" and is wrong for it. Confidence: **certain**.

**P21. `_path_utils.py:284-286`, `formatted_file_size` — `%g` switches to exponent form.**

> "Three significant digits are shown, so a size is rounded rather than truncated and
> a large value inside a unit can round up to the next thousand without changing the unit."

Demonstrated: `formatted_file_size(999999)` → `'1e+03 KB'` and `formatted_file_size(999999999)`
→ `'1e+03 MB'`. `f'{x:.3g}'` renders `999.999` as `1e+03` — one significant digit shown, in
scientific notation. A reader would take the sentence to promise `'1000 KB'`. Confidence:
**likely**.

**P22. `_path_utils.py:221-222`, `repair_case` — the "root" read is the literal `/`.**

> "The root directory is read with ``os.listdir()`` instead."

The code is `os.listdir('/')`, hardcoded (line 254), not the root of the path being
repaired. The surrounding prose says the drive is skipped on Windows, but on Windows
`_clean_abspath` yields `C:/...`, `parts[0] == 'C:'`, and `k == 1` then lists `/` — the
current drive's root, which need not be `C:`. Confidence: **worth checking**
(Windows-only; the classifier issue is tracked elsewhere).

### `_index_rows.py`

**P23. `_index_rows.py:61-65`, class docstring — `sort_basenames` is not defined on PdsFile.**

> "other methods called        bundleset_abspath, new_index_row_pdsfile,
>                              parent, sort_basenames, from_abspath
>
> All of them are defined on PdsFile. Two more come from sibling mixins:
> get_indexshelf reaches _ShelfMixin's _get_shelf, and
> data_abspath_associated_with_index_row reaches _LocalFsMixin's os_path_exists."

`sort_basenames` is defined on `_SortingMixin` (`_sorting.py:36`, method at `:206`) — the
same sibling-mixin category the paragraph goes on to enumerate. So "All of them are defined
on PdsFile" is false and "Two more come from sibling mixins" should be three:
`find_selected_row_key` reaches `_SortingMixin`'s `sort_basenames` at `_index_rows.py:229`.
This is not the package's property-vs-method convention at work — `sort_basenames` is a
method and is listed under "other methods called". Two consequences a reader would get
wrong: `sort_basenames` reads `BUNDLESET_PLUS_REGEX_I` and so raises `AttributeError` on a
bare `PdsFile` (`_sorting.py:78-84`), and it reaches `_LocalFsMixin.os_path_isdir`
(`_sorting.py:286`), so the neighbor search in `find_selected_row_key` can touch the
filesystem. Confidence: **certain**.

**P24. `_index_rows.py:130-134`, `find_selected_row_key` — the neighbor fallbacks return the first/last key, not the second/second-to-last.**

> "``'>'`` returns the key that would follow the selection in sorted order, or
> the second-to-last key if the selection would sort last."
> "``'<'`` returns the key that would precede it, or the second key if the
> selection would sort first."

The indices at lines 235 and 239 are into `self.childnames + [selection]`, which contains
the selection. When the selection sorts last, `childnames[-2]` is therefore the **last real
key**; when it sorts first, `childnames[1]` is the **first real key**. A reader takes
"second-to-last key" and "second key" to mean positions in the index's own key list.
Demonstrated on `COISS_2001_index.tab` (3745 keys, first `N1454725799`, last `N1460960370`):

```
'<' on a selection sorting first -> N1454725799   (the FIRST key, not the second)
'>' on a selection sorting last  -> N1460960370   (the LAST key, not the second-to-last)
```

The code's own comments say it correctly ("if it is first, return the second" is about the
augmented list). Confidence: **certain**.

**P25. `_index_rows.py:159-161`, `find_selected_row_key` — the boundary is zero keys, not two.**

> "IndexError: raised by the neighbor lookup ... when the index has fewer than two keys
> and so has no neighbor to return."

The list indexed is `self.childnames + [selection]`, so with **one** real key the augmented
list has two elements and both `childnames[1]` (k==0, `'<'`) and `childnames[-2]`
(k==len-1, `'>'`) are in range and return that one real key. `IndexError` requires
`self.childnames == []`, i.e. **zero** keys. Confidence: **certain**.

**P26. `_index_rows.py:141-144` and `:162-163`, `find_selected_row_key` — the ValueError is reachable.**

> "A flag outside those four raises **TypeError**, not the ValueError the guard is
> written to raise..."
> "ValueError: written for a flag outside the four, and unreachable..."

Demonstrated:

```
flag='bogus' -> TypeError: not all arguments converted during string formatting
flag='%s'    -> ValueError: Invalid flag "%s"
flag='%d'    -> TypeError: %d format: a real number is required, not str
```

Any flag containing exactly one `%s`-style conversion makes the `%` succeed and the
`ValueError` fire as written. "Unreachable" is wrong, and "raises TypeError" is wrong for
that flag. Confidence: **certain**.

**P27. `_index_rows.py:251-252`, `child_of_index` — that lookup can never hit.**

> "An object already in the shared cache under the row's absolute path is returned
> as it is."

See C2: the cache is keyed by lowercased *logical* paths, so an absolute-path key is never
present. The sentence describes a feature that does not operate, and the paragraph two down
("A newly built object is **not** written to the cache, so two calls for the same uncached
row return two objects") reads as though the *uncached* qualifier were meaningful — in fact
*every* row is uncached. Confidence: **certain**.

The same claim appears in the class docstring at `_index_rows.py:77-79`
("child_of_index reads the shared cache but never writes it"), where "reads" implies an
effective read.

**P28. `_index_rows.py:339-341`, `data_abspath_associated_with_index_row` — it does not always return an empty string on failure.**

> "An empty string is the answer for anything that fails: an object that is not an
> index row, a table with no recognizable file specification column, and a missing
> row whose neighbors yield nothing."

The neighbor path calls `parent.child_of_index(self.basename, flag=flag)` (line 424) with no
guard. `find_selected_row_key` raises `OSError` for an ambiguous selection *before* it looks
at the flag (lines 220-222), so the exception propagates. Demonstrated on a real index:

```
row = idx.child_of_index('N145472', flag='')     # accepted, non-existent row
row.data_abspath_associated_with_index_row()
  -> OSError: Index selection is ambiguous: .../COISS_2001_index.tab/N145472
```

`get_indexshelf()` can also raise `OSError`/`ValueError` through the same call, and
`IndexError` is possible from the neighbor lookup on an empty index. The function has no
`Raises:` section at all. Confidence: **certain**.

**P29. `_index_rows.py:441-442`, `data_pdsfile_for_index_row` — the same over-promise, one level up.**

> "It is the object for the path ``data_abspath_associated_with_index_row()``
> works out, so everything that makes that path an empty string makes this None."

True as far as it goes, but the docstring has no `Raises:` section and the sentence is the
only thing said about failure, so it reads as total. Everything in P28 propagates through
this method unchanged. Confidence: **likely**.

**P30. `_index_rows.py:270-276`, `child_of_index` — the `Raises:` list is incomplete.**

Listed: `KeyError`, `OSError`, `ValueError`. Not listed: `TypeError` for a bad `flag`
(C3, reachable through `find_selected_row_key` at line 282) and `IndexError` for an index
with no keys (P25, same call). The `KeyError` entry's reasoning is sound and was verified:
`childnames` for an index is `list(shelf.keys())` (`_properties.py:410-413`), so
`shelf[key]` at line 294 really cannot add a second `KeyError` source. Confidence:
**likely**.

**P31. `_index_rows.py:328-330`, `data_abspath_associated_with_index_row` — the version suffix is dropped.**

> "The path is assembled from this object's own bundle set, in the ``volumes`` category"

`bundleset_abspath('volumes')` (`pdsfile.py:1149-1191`) carries this file's version suffix
over **only when the requested category's voltype matches its own** (lines 1178-1181). For a
row of a `metadata/` index the voltypes differ, so the suffix is dropped and the path names
the most recent version. Demonstrated: for `metadata/COISS_2xxx/...`,
`bundleset_abspath('volumes')` → `.../volumes/COISS_2xxx`; a row of
`metadata/COISS_2xxx_v1.1/...` would likewise point at unversioned `volumes/COISS_2xxx`,
not at `volumes/COISS_2xxx_v1.1`. "this object's own bundle set" reads as though the
version travelled with it. Confidence: **likely**.

---

## Checked and found accurate

Recorded so a later round does not re-derive them.

- `archive_path_and_lskip`'s "**it does not index the path this returns**" (`:213-217`):
  confirmed against the consumer, `pdsarchives.py:105-118`, which uses it as
  `dirpath[lskip:]` for the tar `arcname`; and confirmed numerically that slicing the
  archive path at that offset lands 9 characters (`len('archives-')`) inside the bundle set
  name.
- `dirpath_and_prefix_for_checksum`'s "prepending it to a row's path gives an absolute
  path" (`:172-174`): confirmed against `pdschecksums.py:177-201` (`prefix_ + filepath`) and
  `:266-285` (`abspath[len(prefix_):]`).
- `dirpath_and_prefix_for_archive`'s worked example (`:287-290`): confirmed —
  `archives-volumes/COISS_2xxx/COISS_2001.tar.gz` has `bundlename='COISS_2001'` and
  `interior='COISS_2001.tar.gz'` (`pdsfile.py:1499-1510`), so the pair really is
  `(.../volumes/COISS_2xxx/COISS_2001, .../volumes/COISS_2xxx/)`.
- `checksum_path_and_lskip`'s "everything from it onward is the checksum file's basename":
  confirmed numerically (lskip 58 on a 58-character prefix), including the `'checksums_'`
  vs `'checksums-'` spelling, which is harmless because the lengths match.
- `_pinned_log_timetag`'s whole contract, including "deleted if the value was inherited":
  `PdsFile` defines `_LOG_TIMETAG = None` (`pdsfile.py:238`), so `had_own` is True on
  `PdsFile` and False on every subclass, and the restore is exact in both directions. The
  two-places-one-run motivation is real: `holdings_maintenance/_common.py:262-291`.
- `_log_path_for`'s note that `dir` is kept as `dir` "because callers pass it by that
  keyword": confirmed at `_common.py:355` and `_indexshelf_common.py:550`.
- `checksum_path_if_exact`'s "an existence test on the empty path": confirmed —
  `os_path_exists('')` falls through every branch of `_local_fs.py:142-180` to
  `os.path.exists('')` and returns False.
- `_eval_null_key_record`'s account of the sidecar format and of the `[:-1]`: confirmed
  against the writer, `pdsinfoshelf.py:305-324`. The null-key entry really is line 2,
  because the bundle's own abspath is a strict prefix of every other and the list is sorted.
- `shelf_path_and_lskip`'s "slicing it off a file's own absolute path leaves the interior
  path": confirmed for both branches, including the `+ 1` for the separator and the archive
  branch where `interior` is the `.tar.gz` basename.
- `find_selected_row_key`'s "With an exact match required ... ``''`` then behaves like
  ``'>'``": confirmed — the `flag == ''` early return sits inside `if not exact_match:`.
- `child_of_index`'s "The shelf lookup that follows uses a key that came from the index's
  own key list": confirmed — `childnames` for an index is `list(shelf.keys())`
  (`_properties.py:410-413`).
- `get_keys`'s "the volume column is the **last** one it has, because that loop does not
  stop at its first hit": confirmed (`_index_rows.py:388-390` has no `break`, unlike
  `:379-382`).
- `repair_case`'s `UnboundLocalError` on the root: demonstrated
  (`UnboundLocalError: cannot access local variable 'found'`).
- `formatted_file_size`'s `IndexError` boundary: confirmed — `int(log10(1e27)//3) == 9` and
  `FILE_BYTE_UNITS` has 9 entries, so "1e27 or more" is exactly right.
- `abspath_for_logical_path`'s four-source order and its "source 4 writes an empty list
  when it finds nothing, which leaves the next call to search again": confirmed.
