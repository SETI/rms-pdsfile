# PR-29a round 2 — adversarial review of five mixin modules

Files reviewed: `src/pdsfile/_sorting.py`, `_preload.py`, `_associations.py`, `_local_fs.py`,
`_opus.py`. Executable code treated as ground truth; prose on trial.

Everything below was checked against the other end of the relation (`pdsfile.py`,
`_properties.py`, `pdscache.py`, `_path_utils.py`, `_shelves.py`, the rule modules), and
where a claim was cheap to execute it was executed against
`PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`.

Totals: **6 code defects**, **37 prose defects** (P1 to P37).

---

# CODE DEFECTS

## C1. `preload()` hands `DictionaryCache` a bound method as its lifetime function — the exact trap `pdscache.py` documents

**File/symbol:** `_preload.py`, `_PreloadMixin.preload`, code at lines 533-536 and 564-569;
prose at lines 30, 201-202 and 766-767.

**Sentences:**

> (L30) "``cache_lifetime_for_class()`` is the lifetime function every cache built here is given"

> (L201-202) "cache_lifetime is the per-object lifetime function preload hands to a cache it creates, and it delegates to the module-level cache_lifetime_for_class above."

> (L766-767) "The lifetime function every cache built by ``preload()`` is given."

**What the code does.** `preload()` constructs
`pdscache.DictionaryCache(lifetime=cls.cache_lifetime, ...)` (`_preload.py:534` and again in
the memcached-give-up path at `_preload.py:565`). `cls.cache_lifetime` is a **bound
classmethod**, and `DictionaryCache.__init__` recognises a lifetime function only by
`type(lifetime).__name__ == 'function'` (`pdscache.py:177`). A method fails that test, so it
is stored as `self.lifetime` — a *constant* — and `self.lifetime_func` is None. `set()` then
computes `time.time() + <bound method>` (`pdscache.py:487-495`) and raises TypeError on every
store that does not pass an explicit lifetime.

`pdscache.py`'s own module docstring names this exact hazard (lines 36-39): "a bound or class
method counts only for the memcached cache. Handing a dictionary cache a method makes it a
constant, and the first store that needs the default then raises TypeError." And
`pdsfile.py:318` builds the class-level default cache with the *module-level function*
`cache_lifetime_for_class`, which is correct — so the code elsewhere shows the author knew.

Reproduced:

```
type of PdsFile.cache_lifetime: method
lifetime attr: <bound method _PreloadMixin.cache_lifetime of <class ...PdsFile'>>
lifetime_func: None
c.set('x', 'hello') -> TypeError: unsupported operand type(s) for +: 'float' and 'method'
```

The default-lifetime store is not hypothetical: `PdsFile._recache()` (`pdsfile.py:1372`) calls
`cls.CACHE.set(logical_lc, self)` with no lifetime, and every lazy property calls `_recache()`.

**Why it is latent today.** Both construction sites are guarded by
`if not isinstance(cls.CACHE, pdscache.DictionaryCache)` (`_preload.py:533`, `:564`), and the
class-level default CACHE is already a `DictionaryCache`, so the broken cache is normally never
built. It *is* built when a process that currently holds a `MemcachedCache` preloads with
port 0, and on the memcached-connection give-up path — i.e. exactly the deployment
configuration the class docstring says is untested here (L239-242).

**Prose consequence.** All three sentences describe `cache_lifetime` as "the lifetime function"
the cache "is given". For a `DictionaryCache` it is not honoured as a function at all, and the
resulting cache is unusable. A reader relying on those sentences would assume the two
construction sites are equivalent to `pdsfile.py:318`. They are not.

**Confidence: certain** (both the classification and the TypeError reproduced).

---

## C2. `os_path_isdir()` raises `KeyError` where `os_path_exists()` returns False

**File/symbol:** `_local_fs.py`, `_LocalFsMixin.os_path_isdir`, code at lines 231 and 236.

**What the code does.** `os_path_exists` tests membership — `return (key in shelf)`
(`_local_fs.py:167`) — so a key the shelf does not hold answers False. `os_path_isdir` instead
subscripts: `(_, _, _, checksum, _) = shelf[key]` (`_local_fs.py:231`). `_get_shelf()` returns a
plain `dict` (`_shelves.py:305`), so a missing key raises `KeyError`, and `KeyError` is **not**
in the handler `except (ValueError, IndexError, OSError)` at `_local_fs.py:236`.

Reproduced under `SHELVES_ONLY`:

```
exists good: True     isdir good : True
exists bad : False    isdir bad RAISED: KeyError KeyError('NOSUCHDIR')
```

(`bad = .../holdings/volumes/COISS_2xxx/COISS_2001/NOSUCHDIR`)

**Prose consequence.** The docstring at `_local_fs.py:205-214` says "Under SHELVES_ONLY the info
shelf answers ... The same three fallbacks as the existence test follow if that fails" — for a
missing key nothing "follows"; the call raises. The docstring has no `Raises:` section at all.
This also silently breaks `sort_basenames(dirs_first=True)`, whose only filesystem call is
`os_path_isdir` (`_sorting.py:286`).

**Confidence: certain.**

---

## C3. `preload()` is missing a `continue` after "Not a directory, ignored"

**File/symbol:** `_preload.py`, `_PreloadMixin.preload`, lines 726-727.

**What the code does.**

```python
if not cls.os_path_exists(category_abspath):
    cls.LOGGER.warn('Missing category dir: ' + category_abspath)
    continue
if not cls.os_path_isdir(category_abspath):
    cls.LOGGER.warn('Not a directory, ignored: ' + category_abspath)   # no continue
pdsdir = cls.from_abspath(category_abspath, fix_case=False, caching='all', lifetime=0)
```

The message says "ignored" and the path is not ignored: it is constructed, cached permanently
(`lifetime=0`, `caching='all'`), and — per the comment at `:730-731` — merged into the
category-level merged directory's child list.

The docstring (L499-500) does report this, which is the right instinct, but see P16 for the
overstatement in how it reports it.

**Confidence: certain** (the missing `continue` is plain in the source).

---

## C4. `get_permanent_values()` raises `AttributeError` on a `DictionaryCache`

**File/symbol:** `_preload.py`, `_PreloadMixin.get_permanent_values`, line 313.

**What the code does.** The success branch logs
`str(len(cls.CACHE.permanent_values))`. `permanent_values` exists only on `MemcachedCache`
(`pdscache.py:800`); a `DictionaryCache` has no such attribute — verified: its instance
attributes are `dict, keys, lifetime, lifetime_func, limit, logger, pauses, preload_eligible,
slop`. So the whole-success path raises AttributeError on a dictionary cache.

`preload()` only reaches this method when `cls.MEMCACHE_PORT` is truthy (`_preload.py:608-609`),
so the guard exists — but it is in the *caller*, and the method's docstring (L256-276) states no
such restriction, documents no `Raises:`, and its `port` parameter is described as "the
memcached port to preload with" as if any value were fine.

**Confidence: likely** (the attribute's absence is verified; the reachability is via a direct
call, not via `preload()`).

---

## C5. `sort_logical_paths()` raises `KeyError` on any single-component path

**File/symbol:** `_sorting.py`, `_SortingMixin.sort_logical_paths`, lines 452-462 vs 480.

**What the code does.** For a path with no slash, `parts` has one element, so
`for k in range(1, len(parts))` does not execute and no `child_names[path]` entry is created
(`_sorting.py:455-462`). But the name still enters `top_level_names` (`:454`), and
`_append_recursively(key)` immediately does `for name in child_names[path]` (`:480`).

Reproduced: `Pds3File.sort_logical_paths(['volumes'])` → `KeyError: 'volumes'`.

A category-level logical path is an ordinary input for this API. The docstring has no `Raises:`
section.

**Confidence: certain** (reproduced).

---

## C6. `associated_abspaths()` re-globs a truncated index-row pattern on the second index extension

**File/symbol:** `_associations.py`, `associated_abspaths`, lines 268-297.

**What the code does.** `pattern` is rebound *inside* the `for ext in cls.IDX_EXT` loop:

```python
for pattern in patterns:
    for ext in cls.IDX_EXT:
        if f'{ext}/' in pattern:
            parts = pattern.rpartition(ext)
            pattern = parts[0] + parts[1]      # pattern truncated, persists to next ext
            suffix = parts[2][1:]
        else:
            suffix = ''
        ...
        abspaths += test_abspaths
```

`Pds4File.IDX_EXT = ('.csv', '.tab')` (`pds4file/__init__.py:80`). For a pattern such as
`.../x_index.csv/rowkey`, the first iteration strips the row and resolves it through the index;
the second iteration sees `.../x_index.csv` (no `.tab/`), so `suffix = ''` and the glob returns
**the bare index file**, which is appended alongside the row. The two are different paths, so
the dedup at `:316` does not remove it.

The docstring's hedge at L174-176 — "Duplicates are removed at the end, which is what keeps that
invisible in the usual case" — covers the non-index case only; this case is not invisible.

**Confidence: worth checking** (the mechanism is certain from the code; whether a PDS4
`ASSOCIATIONS` entry actually emits an index-row pattern was not exercised).

---

# PROSE DEFECTS

## `_sorting.py`

### P1. The default split is at the LAST period, not the first — `split_basename`, line 101

> "so the default split is at the **first** period rather than the last, and a bundle set name splits before its version suffix instead."

The default rule that catches everything is
`(r'(.*)(\..*)', 0, (r'\1', '', r'\2'))` — `pds3file/rules/__init__.py:485` and
`pds4file/rules/__init__.py:463` — whose first group is greedy, i.e. the *last* period. Both
rule files carry the literal comment `# If all else fails, split at last period`.

Measured:

```
'foo.bar.baz'       -> ('foo.bar', '', '.baz')
'a.b.c.d'           -> ('a.b.c', '', '.d')
'COISS_2001.tar.gz' -> ('COISS_2001.tar', '', '.gz')
```

The "first period" rule is what `sort_sibnames` uses to group siblings
(`_sorting.py:374`, whose own comment reads `# first dot, not last`) — a different mechanism.
The two look to have been conflated.

**Confidence: certain.**

### P2. Split rules are consulted for bundle names too, and "first" applies only there — `split_basename`, lines 104-105

> "A rule module can override the split for its own data set, and the class's split rules are consulted first for every name that is not a bundle set or bundle name."

The code (`_sorting.py:125-151`):

* bundle **set** name (`:128-135`): `SPLIT_RULES` is never consulted.
* bundle **name** (`:138-149`): `test = self.SPLIT_RULES.first(basename)` is consulted **first**,
  and its result is returned when it differs from the input. The inline comment says so:
  `# a split rule overrides the default behavior`.
* everything else (`:151`): `SPLIT_RULES.first()` is the only thing consulted, so "first" is
  vacuous there.

The sentence excludes exactly the one case where "consulted first" has content, and includes the
one case where it has none.

**Confidence: certain.**

### P3. `sort_sibnames` Parameters contradicts its own body — line 345

> "basenames (list): the basenames to sort. It is not modified."

Six lines earlier the same docstring says the opposite (L339-341): "**The list passed in is
appended to** when it was not, so a caller's list can come back one item longer than it went
in". The code appends to the caller's list at `_sorting.py:363-364`.

Measured: caller list `['N1460960868_1.LBL']` came back as
`['N1460960868_1.LBL', 'N1460960868_1.IMG']`.

The identical `Parameters:` line at `sort_basenames` (L227) is correct, because that method does
`basenames = list(basenames)` (`:325`). It appears to have been copied into `sort_sibnames`,
where it is false.

**Confidence: certain** (reproduced).

### P4. Paths of differing depth sort fine — `sort_logical_paths`, line 431

> "**The paths must all have the same number of levels.**"

Measured: `sort_logical_paths(['volumes/COISS_2xxx/COISS_2001/data',
'volumes/COISS_2xxx/COISS_2002'])` returns both, in order, with no warnings and no "overlooked
item" path taken. The tree walk (`_sorting.py:470-485`) descends a child only when it is itself
a key of `child_names`, so mixed depths are handled. The real constraint is the one the *next*
sentence gives correctly: no path may be an ancestor directory of another.

**Confidence: certain** (reproduced).

### P5. `_append_recursively` does not emit "deepest last" — line 471

> "Append one directory's paths to the result, deepest last."

The emission order is the sorted-children order at each level, not depth order. In the measured
case above, the four-level path `volumes/COISS_2xxx/COISS_2001/data` came out **before** the
three-level `volumes/COISS_2xxx/COISS_2002` — deepest first.

**Confidence: likely.**

### P6. `sort_logical_paths` documents no `Raises:` — lines 438-443

Paired with C5. `KeyError` for a single-component path; and `cls.from_logical_path(path)`
(`:458`) can itself raise `ValueError` from `abspath_for_logical_path()` for a path whose first
component is not a category (`_path_utils.py:345-346`).

**Confidence: certain** (the KeyError is reproduced; the ValueError is by inspection).

### P7. `dirs_first`/`dirs_last` is not the only option that reads the filesystem — `sort_basenames`, lines 223-224

> "Sorting by directory-or-file is the one option that reads the filesystem, and it does so once per name."

`apply_info_first` evaluates `self.info_basename` (`_sorting.py:300`), whose implementation
(`_properties.py:922-959`) reads `self.childnames` (→ `os_listdir`), can read
`self.label_basename` (→ `os_path_exists`, `_properties.py:1102`), and can call
`os.path.exists()` directly for a bundleset-level AAREADME (`_properties.py:951`). It is a
cached lazy property, so it costs one read rather than one per name — which is the accurate
statement.

**Confidence: likely.**

### P8. `viewable_childnames`'s order claim does not hold for an index table — lines 539-542

> "The order is the one the child list already carries, which is the class's sort with all four grouping options off, rather than the order ``sort_childnames()`` would give."

True for a directory: `_properties.py:403-407` passes `labels_after=False, dirs_first=False,
dirs_last=False, info_first=False`. But for an index table the list is **overwritten** at
`_properties.py:413` with `self.sort_basenames(childnames)` — the class **defaults**. Measured
`Pds3File.SORT_ORDER` is `{'labels_after': True, 'dirs_first': False, 'dirs_last': False,
'info_first': 20}`, i.e. two of the four are on.

The same claim is what `childnames_by_anchor` and `viewable_childnames_by_anchor` inherit
through "in the child list's order" (L560, L580).

**Confidence: likely.**

### P9. "The four methods that need to probe it" undercounts by six — module docstring line 23; class docstring lines 43-44

> (L23-25) "Nothing here reads the filesystem itself. The four methods that need to probe it -- to tell a directory from a file, or to drop what does not exist -- delegate to ``_LocalFsMixin``."

Four methods reach `_LocalFsMixin` *directly* (`sort_basenames`→`os_path_isdir`;
`logicals_for_abspaths`, `basenames_for_abspaths`, `abspaths_for_logicals`→`os_path_exists`).
But six more probe the filesystem to "drop what does not exist" through the `exists` lazy
property — `abspaths_for_pdsfiles` (`:610`), `logicals_for_pdsfiles` (`:630`),
`basenames_for_pdsfiles` (`:650`), `pdsfiles_for_abspaths` (`:673`), `pdsfiles_for_logicals`
(`:743`), `pdsfiles_for_basenames` (`:816`) — and `exists` calls
`cls.os_path_exists()` (`_properties.py:147`). The clause "to drop what does not exist" is
attached to the wrong four.

**Confidence: worth checking** (the class docstring does list `exists` under "lazy properties
read", so the contract block is internally consistent; the sentence is what misleads).

---

## `_preload.py`

### P10. "Five cases" — there are six — `cache_lifetime_for_class`, line 98

> "Five cases, in the order they are tested."

The body has six branches (`_preload.py:122-138`): str → default; not-an-instance → forever;
no interior → long; isdir + endswith `data` → long; isdir → short; else → default. The same
paragraph then enumerates all six outcomes, so the count contradicts the list under it.

**Confidence: likely.**

### P11. "a tuple with five elements" followed by six — `load_volume_info`, line 334

> "Each entry is a tuple with five elements::"

The block that follows lists six (description / icon_type / version ID / publication date /
list of data set IDs / MD5 checksum), and the code builds a six-tuple:
`volinfo = (parts[1], parts[2], parts[3], parts[4], dsids, md5)` (`_preload.py:436`). The
inheritance path at `:449-451` also assembles a six-tuple.

**Confidence: certain.**

### P12. It is an empty **icon_type** that becomes None, not an empty version ID — `load_volume_info`, line 344

> "A value only containing a string of dashes "-" is replaced by None. So is an empty version ID, but **not** an empty publication date or an empty data set ID, which stay empty strings."

Field indices, confirmed against the real tables: `parts[0]` key, `parts[1]` description,
`parts[2]` **icon_type**, `parts[3]` version ID, `parts[4]` publication date, `parts[5]+` data
set IDs — the header line of `/seti/opus/pdsdata/holdings/_volinfo/COISS_2xxx.txt` states exactly
this order.

The code (`_preload.py:410-415`):

```python
if parts[2] == '' or set(parts[2]) == {'-'}:   # icon_type: empty -> None
    parts[2] = None
if set(parts[3]) == {'-'}:                      # version ID: only dashes -> None
    parts[3] = None
if set(parts[4]) == {'-'}:                      # pub date:   only dashes -> None
    parts[4] = None
```

So the `== ''` special case belongs to `parts[2]`, the icon_type. An empty version ID stays
`''` — `set('')` is `set()`, which never equals `{'-'}`. A real record exercises this:
`JNOSP_xxxx.txt` has `| PDSLINK  |     | ---- |`, i.e. an empty version ID (stays `''`) beside a
dashed publication date (becomes None).

This also makes the entry list at L336 wrong in the other direction: "icon_type or blank for
default" — a blank icon_type is stored as None, not as a blank.

**Confidence: certain.**

### P13. "The values are not used" — two of the four are — `get_permanent_values`, line 267

> "The values are not used. What matters is whether the read succeeds"

`pdsf0 = cls.CACHE[category]` is used: `pdsf0.childnames` drives the bundleset loop
(`_preload.py:290`). `pdsf1 = cls.CACHE[category + '/' + bundleset.lower()]` is used twice:
`pdsf1.childnames` (`:297`) and `pdsf1.logical_path` (`:301`), which builds the next key. Only
the `$RANKS-`/`$VOLS-` reads (`:285-286`) and the bundle-level read (`:304`) are discarded, and
those two are the ones the code marks with `_ =`.

**Confidence: certain.**

### P14. There is no "module tail's call" in this module — class docstring, lines 224-225

> "Every one of those is defined on PdsFile itself rather than only on Pds3File and Pds4File, which is what makes the module tail's call of cache_category_merged_dirs work on the bare class at import time."

`_preload.py` ends at line 777 with `return cache_lifetime_for_class(arg, cls)`; it contains no
module-level call. The bare-class call is at `pdsfile.py:2435`
(`PdsFile.cache_category_merged_dirs()`); the subclass calls are at
`pds3file/__init__.py:273` and `pds4file/__init__.py:237`. The substance of the claim is right,
its location is not — a reader will look for a tail in this module and find none.

**Confidence: likely.**

### P15. Merged directories created at import time do not survive a preload — module docstring, lines 20-21

> "``cache_category_merged_dirs()`` creates them, and it runs at import time so that the entries exist before any preload does."

`preload()` does not call `cache_category_merged_dirs()`. It inlines an **unconditional**
overwrite: `cls.CACHE.set(category, cls.new_merged_dir(category), lifetime=0)` for every
category (`_preload.py:685-686`). `cache_category_merged_dirs()` is the version that skips
existing entries (`:474`). So the import-time entries are discarded and rebuilt by every
preload; they matter for a tree that is *never* preloaded, not for the ordering the sentence
gives.

The related sentence in `cache_category_merged_dirs`'s own docstring (L470-471) — "will not
discard a merged directory a preload has already filled" — is correct about that method but
reads as a general property of the mechanism, which `preload()` does not honour.

**Confidence: worth checking.**

### P16. "walked anyway" overstates what the missing `continue` costs — `preload`, lines 499-500

> "**one that exists but is not a directory is warned about and then walked anyway**, because that branch does not skip it."

Paired with C3. The fall-through does reach `cls.from_abspath(...)` and `_preload_dir(pdsdir,
cls)`, but `_preload_dir` returns at its first statement — `if not pdsdir.isdir: return`
(`_preload.py:650-651`) — so nothing is walked. What actually happens is that a non-directory
category path is constructed, cached permanently (`caching='all', lifetime=0`) and merged into
the category-level merged directory's child list, per the code comment at `:730-731`. That is
the harm a reader should be told about.

**Confidence: likely.**

### P17. `cache_lifetime` described as a working "lifetime function" — lines 201-202, 766-767, and module line 30

See C1. All three sentences present `cls.cache_lifetime` as an equivalent of the module-level
function. It is not equivalent for the class `preload()` actually hands it to.

**Confidence: certain.**

### P18. `get_permanent_values` documents no `Raises:` and no cache-class restriction — lines 256-276

See C4. The docstring's `port (int)` parameter reads as unconstrained; the method's success
path only works on a `MemcachedCache`.

**Confidence: likely.**

---

## `_associations.py`

### P19. `rank=None` means the LATEST version when the category is unchanged — `associated_parallel`, lines 334-335

> "A rank of None means the version this object already has when the volume type is unchanged, and the latest when it is not."

For the category-unchanged branch — which is what `associated_parallel()` with no arguments
takes, since `category` defaults to `self.category_[:-1]` — the code is
(`_associations.py:488-490`):

```python
if category == self.category_[:-1]:
    if rank is None:
        rank = max(self.all_version_abspaths.keys())     # the LATEST
    return _cache_and_return(self.all_versions().get(rank, None))
```

Measured:

```
volumes/COUVIS_8xxx_v1/COUVIS_8001   rank 10000, all ranks [10000, 20000, 20100, 999999]
  associated_parallel()          -> volumes/COUVIS_8xxx/COUVIS_8001    (rank 999999)
  associated_parallel('volumes') -> volumes/COUVIS_8xxx/COUVIS_8001
volumes/COCIRS_0xxx_v2/COCIRS_0012   rank 20000, all ranks [20000, 999999]
  associated_parallel()          -> volumes/COCIRS_0xxx/COCIRS_0012    (rank 999999)
```

The claim *is* right for a *different* category with the same voltype (e.g.
`checksums-volumes`), which reaches `bundle_pdsfile(category, None)` →
`bundle_abspath(category)`, which carries the version suffix over (`pdsfile.py:1127-1128`). But
the most common call — no arguments — returns the latest, which is the opposite of what the
sentence says.

**Confidence: certain** (reproduced).

### P20. The deepest-directory search DOES cache its None; a different path is the uncached one — lines 342-343

> "The one path that returns without caching is the deepest-directory search: it caches what it finds, and returns None uncached when it runs off the top."

Both halves are wrong:

* When the walk runs off the top, `_associations.py:517` is
  `return _cache_and_return(None)` — the None **is** cached, under `(category, rank)` and,
  when `rankstr` is set, under the word too.
* The path that genuinely returns without caching is the category-directory shortcut at
  `_associations.py:427-428` — `if self.is_category_dir: return cls.from_logical_path(category)`
  — which the docstring does not mention. (The `CATEGORIES` miss at `:423-424` is mentioned
  separately at L345.)

**Confidence: certain.**

### P21. Answers are cached on the LATEST-version object, not "on this object" — lines 340 and 364

> (L340) "Answers are cached on this object, under the category and rank asked for"

> (L364) "Record one answer in this object's cache and return it."

`_cache_and_return` is a closure over the *variable* `self`, which `associated_parallel` rebinds
at `_associations.py:441` (`self = self.all_versions()[latest_rank]`) whenever the requested
voltype differs from this file's. Both `_associated_parallels_filled` initialisation (`:444`)
and the writes (`:402-409`) then happen on the latest-version object, and `_recache()` (`:412`)
writes *that* object back.

Measured, on `volumes/COCIRS_0xxx_v2/COCIRS_0012` after two cross-type lookups:

```
after on self:   None
after on latest: {('previews', None): '.../previews/COCIRS_0xxx',
                  ('previews', 999999): '.../previews/COCIRS_0xxx',
                  ('metadata', None): '.../metadata/COCIRS_0xxx',
                  ('metadata', 999999): '.../metadata/COCIRS_0xxx'}
```

The class docstring's "instance attributes WRITTEN `_associated_parallels_filled`, **on self**"
(L61-63) carries the same error.

**Confidence: certain** (reproduced).

### P22. A missing bundle counterpart falls back to the bundleset, it does not yield None — lines 324-326

> "and a file whose bundle has no counterpart at all yields None."

`_associations.py:496-499`:

```python
if not new_root:
    # If there's no volume-level match, try the volset-leve match
    return _cache_and_return(self.bundleset_pdsfile(category, rank))
```

None is only the eventual answer if the bundleset-level lookup also fails (or its result does
not exist, per `_cache_and_return`'s existence test at `:397`). The docstring skips the fallback
entirely.

**Confidence: likely.**

### P23. "without duplicates" does not survive the conversion to logical paths — `associated_logical_paths`, lines 115-116

> "list: the logical paths, without duplicates, in the order ``associated_abspaths()`` produced them."

The dedup at `_associations.py:316` is on **absolute** paths. `logicals_for_abspaths()` strips
the holdings root (`_path_utils.py:103-105`), so two distinct abspaths in two holdings
directories collapse to one logical path, and the result can hold it twice. The same sentence on
`associated_pdsfiles` (L142-143) is safe, because objects map 1:1 onto the deduped abspaths.

**Confidence: worth checking** (the mechanism is certain; whether the association machinery
actually emits two roots for one logical path in a multi-holdings deployment was not exercised).

### P24. `associated_pdsfiles` omits the `ValueError` its sibling documents — lines 145-148

`associated_logical_paths` documents "ValueError: raised by ``logicals_for_abspaths()`` if an
associated path does not lie under a holdings directory" (L121-123). `associated_pdsfiles` goes
through `pdsfiles_for_abspaths()` → `cls.from_abspath(p)` (`_sorting.py:671`), which splits on
the holdings component and raises `ValueError(f'"{cls.PDS_HOLDINGS}" directory not found in:
{abspath}')` at `pdsfile.py:1825`. Same failure, same trigger, documented on one method only.

**Confidence: likely.**

---

## `_local_fs.py`

### P25. `os_path_isdir` does go back through the memoized test — lines 212-214

> "Unlike the existence test this answer is not memoized, and it consults the filesystem directly for its fallbacks rather than going back through the memoized test."

Of the four existence questions `os_path_isdir` asks, two do go back through the memoized test:

* `_local_fs.py:235` — `return bool(cls.os_path_exists(shelf_abspath))` (the covered-directory
  case);
* `_local_fs.py:254` — `if testpath and cls.os_path_exists(testpath)` — the **third fallback**,
  the checksum one, which the sentence explicitly covers.

Only the first two fallbacks (`:245`, `:249`) use `os.path.exists()` directly.

**Confidence: certain.**

### P26. `os_path_isdir` documents no `Raises:` — lines 201-221

See C2. `KeyError` from `shelf[key]` at `:231`, uncaught.

**Confidence: certain.**

### P27. `os_path_exists`'s shelf bullet omits the `documents` exclusion — lines 113-117

> "under SHELVES_ONLY, the info shelf covering the path is consulted"

The condition is `if cls.SHELVES_ONLY and f'{cls.PDS_HOLDINGS}/documents' not in abspath:`
(`_local_fs.py:157`), with the inline comment "If it's for documentation, we don't create shelf
files, we will just use the os.path.exists". A documents path skips bullets 3 *and* the three
fallbacks and goes straight to the filesystem. The docstring never mentions `documents`, even
though `os_listdir`'s docstring does (L286-288) and `os_path_isdir` (`:223`) deliberately lacks
the guard — an asymmetry between the two that neither docstring records.

**Confidence: likely.**

### P28. "memoized for the life of the process" overstates a 200-entry LRU — module docstring, lines 17-18

> "Existence answers are memoized for the life of the process, so a file created or deleted after the first question about it is not noticed."

`PATH_EXISTS_CACHE_SIZE = 200` and the decorator is `functools.lru_cache(maxsize=200)`
(`_local_fs.py:34`, `:102`), so entries are evicted, not kept for the life of the process. In a
single ordinary preload the cache is saturated and thrashing:

```
CacheInfo(hits=10, misses=4688, maxsize=200, currsize=200)
```

The `os_path_exists` docstring hedges this correctly ("up to ``PATH_EXISTS_CACHE_SIZE`` distinct
calls", L121-124); the module docstring does not, and its stated consequence — a stale answer
persisting for the process's life — is materially false at that hit rate.

**Confidence: likely.**

### P29. Checksum files for archives DO carry their volume type — `_non_checksum_abspath`, lines 76-80

> "**Only the volume types that appear in the basename are dropped.** A checksum file for volumes, for bundles or for archives does not carry its volume type in its basename..."

Real files in `/data/pdsdata/holdings/checksums-archives-metadata/` are named
`COCIRS_0xxx_metadata_md5.txt`, `COISS_2001_metadata_md5.txt` — the voltype **is** in the
basename, and `_non_checksum_abspath` reduces them correctly (verified:
`.../checksums-archives-volumes/COISS_2xxx_volumes_md5.txt` →
`.../archives-volumes/COISS_2xxx`). The path builder agrees: `bundleset_abspath` uses
`ext = '_' + parts[-1][:-1] + '_md5.txt'` for every checksums-archives category except volumes
(`pdsfile.py:1183-1187`). Only `checksums-archives-**volumes**` lacks the voltype
(`.../checksums-archives-volumes/COCIRS_0xxx_md5.txt` in the test tree).

"for bundles" is also doubtful in the other direction: `bundle_abspath` builds
`BUNDLE_bundles_md5.txt` for `checksums-bundles` (`pdsfile.py:1132-1141`), which *does* carry
the voltype ('bundles' is in `PdsFile.VOLTYPES`, `pdsfile.py:221-222`) — though `os_listdir`
disagrees and builds `BUNDLE_md5.txt` for it (`_local_fs.py:363`). The docstring picks one side
of a disagreement the code has with itself.

The example given (`.../checksums-volumes/SET/BUNDLE_md5.txt` →
`.../volumes/SET/BUNDLE_md5.txt`) is correct — verified.

**Confidence: likely** (the archives half is certain; the bundles half is worth checking).

### P30. The checksums branch does not "do the same" — `os_listdir`, line 276

> "* a checksums directory does the same against the tree it checksums, except at the category level, where it passes the listing through unchanged;"

It differs on `bundles`. The checksums-archives branch reserves the bare `_md5.txt` for
`volumes` alone (`_local_fs.py:342-345`); the checksums branch gives it to both:
`if voltype == 'volumes' or voltype == 'bundles': return [r + '_md5.txt' ...]`
(`_local_fs.py:363-364`). The two branches also use different file-vs-directory guards —
`.endswith('.txt')` at `:334` vs `.endswith('_md5.txt')` at `:351`.

**Confidence: likely.**

### P31. Only the shelf-backed branch strips trailing slashes — `glob_glob`, line 456

> "Results have any trailing slash removed."

The strip is `return [p.rstrip('/') for p in abspaths]` at `_local_fs.py:565`, on the
shelf-backed path only. The four other returns do not strip: `:474` (no-wildcard),
`:479` and `:505` (`_clean_glob`), and `:510-511` (the category-level shelf-directory
conversion). `_clean_glob` does not strip either (`_path_utils.py:172-186`), and
`glob.glob()` preserves the trailing slash on a pattern that ends in one.

**Confidence: likely.**

### P32. `os_path_exists` reaches something else before `IDX_EXT` — class docstring, lines 56-57

> "IDX_EXT is defined only on Pds3File and Pds4File, so os_path_exists raises AttributeError on a bare PdsFile, before it reaches anything else."

The first statement of the method reads `cls.PDS_HOLDINGS` and can return without touching
`IDX_EXT`: `if f'{cls.PDS_HOLDINGS}/_infoshelf' in abspath: return os.path.exists(abspath)`
(`_local_fs.py:142-143`). So a bare `PdsFile` answers an infoshelf path normally.

**Confidence: likely.**

### P33. `glob_glob` documents no `Raises:` — lines 462-467

The prose mentions `AssertionError` (L458-460) but there is no `Raises:` section, and two
further exceptions escape:

* `cls.shelf_path_and_key_for_abspath(...)` at `:484` is guarded by `except ValueError` only,
  while its own docstring documents `KeyError` as well (`_shelves.py:461-463`). Every other
  caller in this module catches `(ValueError, IndexError, OSError)`.
* `cls._get_shelf(shelf_path)` at `:516` sits outside any handler and raises `OSError` if the
  file is unreadable (`_shelves.py:294-299`).

**Confidence: worth checking.**

### P34. The flag also reaches the existence test — `glob_glob`, line 454

> "The flag reaches the filesystem glob alone."

The no-wildcard shortcut passes it to `os_path_exists`:
`if cls.os_path_exists(abspath, force_case_sensitive):` (`_local_fs.py:473`). Since that
shortcut is the one the docstring highlights two paragraphs earlier as what makes index-row
notation work, the exception matters.

**Confidence: worth checking.**

---

## `_opus.py`

### P35. Almost nothing after the subclass lookup is done on the subclass — `from_opus_id`, lines 116-117

> "The OPUS ID first selects the rule subclass that owns it, through the class's ``OPUS_ID_TO_SUBCLASS`` translator; everything after that is done on that subclass rather than on the class this was called on."

Exactly one thing is read off `pdsfile_class`: `OPUS_ID_TO_PRIMARY_LOGICAL_PATH`
(`_opus.py:149`, `:152`). Everything else uses `cls`:

| line | call |
|---|---|
| 153 | `abspath_for_logical_path(p, cls)` |
| 157 | `cls.glob_glob(pattern, force_case_sensitive=True)` |
| 158 | `cls.os_path_exists(pattern, force_case_sensitive=True)` |
| 167 | `cls.from_abspath(matches[0])` |
| 173 | `cls.pdsfiles_for_abspaths(matches)` |
| 182 | `cls.LOGGER.warn(...)` |

The sentence states the relation backwards. The next sentence ("That subclass supplies
``OPUS_ID_TO_PRIMARY_LOGICAL_PATH``") is the only accurate part of it.

**Confidence: certain.**

### P36. `from_filespec` does read the filesystem, and the same docstring says so — lines 86-88

> "The result is constructed, not verified: nothing here reads the filesystem, so a well-formed specification for a file that does not exist still returns an object."

Contradicted four lines later by its own `Parameters:` entry (L91-93): "fix_case (bool): whether
to correct the capitalization of each component **against the filesystem**."

And it reads the filesystem even with `fix_case=False`. `from_logical_path` either walks with
`child()` — which ends in `_complete()`, whose first act is `if not self.exists`
(`pdsfile.py:1238`, `:1259`), and `exists` calls `cls.os_path_exists()`
(`_properties.py:147`) — or falls back to `abspath_for_logical_path()`, which globs when more
than one holdings directory is hosted (`_path_utils.py:373-377`).

Measured: one `from_filespec()` call added 3 misses to `os_path_exists`'s LRU counter (2 for a
specification naming a nonexistent file).

The conclusion — an object comes back either way — is right; the stated reason is not.

**Confidence: certain** (reproduced).

### P37. The key is not always a five-element tuple — `opus_products`, lines 190 and 243

> (L190) "Each key is a five-element tuple"

> (L243) "dict: the five-element key mapped to its list of sublists of PdsFile objects."

`key = opus_type_for_abspath.get(pdsf.abspath, pdsf.opus_type)` (`_opus.py:352`), and
`opus_type` is `self.OPUS_TYPE.first(self.logical_path) or ''` — the empty **string** when no
rule matches (`_properties.py:809-810`). That is why `if key == '':` at `_opus.py:353` is live
at all, and the docstring itself acknowledges it at L219 ("is still filed, under the empty
key"). The `Returns:` line is the one a reader would act on and it carries the unqualified
claim.

Worth noting alongside it: `opus_prioritizer` in the two rule modules builds its alternate key by
subscripting `header[0..3]` (`pds3file/rules/GO_0xxx.py:783-787`,
`NHxxxx_xxxx.py:525-529`), so an empty-string key reaching a prioritizer would raise — the
`voltype_` guard above it is what prevents that today.

**Confidence: likely.**

---

# Claims checked and found accurate

Recorded so the next round does not re-spend the effort.

* `_opus.py` L56-59: `opus_products` really is the only method in the package that needs the
  `PdsFile` class object; `_index_rows.py:375` uses `cls.__bases__[0].__name__`, and the three
  module-level `import PdsFile` sites are subclass declarations and a re-export.
* `_opus.py` L61-67: both `opus_prioritizer` implementations mutate in place **and**
  `return pdsfile_dict` (`GO_0xxx.py:812`, `NHxxxx_xxxx.py:548`), so the two call sites'
  disagreement is indeed invisible.
* `_opus.py` L69-73: `FILESPEC_TO_BUNDLESET`, `OPUS_ID_TO_SUBCLASS`, `OPUS_PRODUCTS` are all
  `None` on `PdsFile` (`pdsfile.py:356-364`) and `CROSS_PDS3_PDS4_PRODUCTS` is absent from it,
  present on both rule roots.
* `_opus.py` L206-211: the "products that share a version rank are concatenated, then sorted by
  abspath, and the rank order is read off the first file *after* the path sort" chain is exactly
  what `_opus.py:379-400` does. This is a good catch by the docstring, not a defect.
* `_sorting.py` L78-84: `BUNDLENAME_PLUS_REGEX`, `BUNDLESET_PLUS_REGEX`,
  `BUNDLESET_PLUS_REGEX_I` and `LBL_EXT` are indeed subclass-only.
* `_sorting.py` L86-89: `LBL_EXT` carries the dot (`('.lbl',)`, `('.xml', '.lblx')`),
  `VIEWABLE_EXTS` does not (`{'jpg', 'png', ...}`).
* `_sorting.py` L162-163: no name can pass both the `len > 4` test and the no-period path, for
  either subclass's `LBL_EXT`.
* `_preload.py` L246-249: the case-sensitivity test really does compare a `pds4-holdings` path
  against itself and mark the class case-insensitive.
* `_preload.py` L141-151 (`is_preloading`): nothing in the package writes `$PRELOADING`; the
  only other mention is `preload_and_cache.py:15`.
* `_local_fs.py` L123-124: `cls` and the flag really are part of the `lru_cache` key — the
  `@classmethod` wraps the cached function, not the reverse.
* `_local_fs.py` L443: `_clean_glob` really is memoized (`_path_utils.py:145`).
* `_local_fs.py` L451-453: the prefix scan really does fold case only for the stop test
  (`:548-549`) while `bisect_left` is exact (`:540`) — accurately stated.
