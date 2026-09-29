# PR-29a round 4 — adversarial read of the five mixin docstrings

Scope: `_sorting.py`, `_preload.py`, `_associations.py`, `_local_fs.py`, `_opus.py`.
Code treated as ground truth; prose on trial. Every "demonstrated" finding below was run
against `/seti/opus/pdsdata/holdings` (and `pds4-holdings`) with the repo venv.

---

## PROSE DEFECTS

### PD-1 — `_preload.py`, module docstring, lines 11–15 — the walk does not stop at the bundle set

> "walks each holdings directory down as far as its bundle sets" … "The walk deliberately
> stops at the bundle set: below that, objects are built on demand."

`_preload_dir` descends *into* a bundle set (line 686 `elif pdsdir.is_bundleset:` falls
through to the child loop at 697), so every **bundle** below it is constructed and cached
with `lifetime=0`. Only below the bundle is anything on demand. Measured after
`Pds3File.preload('/seti/opus/pdsdata/holdings')`:

```
cached entries by slash-depth: {0: 25, 1: 216, 2: 4036}
'volumes/coiss_2xxx/coiss_2001'      in CACHE: True
'volumes/coiss_2xxx/coiss_2001/data' in CACHE: False
```

4036 bundle-level entries are preloaded. This also contradicts two neighbouring
docstrings in the same file: `_preload_dir` (line 664) says "a category directory **and a
bundle set** are descended into", and `get_permanent_values` (line 271) says it reads back
"each bundle inside that" — which only makes sense because bundles are preloaded.
**Confidence: certain.**

### PD-2 — `_preload.py`, module docstring, lines 25–30 — `get_permanent_values()` does not re-read all four kinds

> "The cache holds four kinds of permanent entry … the version ranks per category, the
> directory paths per version, the list of holdings already preloaded, and the bundle
> descriptions read from the `_volinfo` tables. … `get_permanent_values()` re-reads them
> and preloads again if any has gone missing"

The method (lines 300–322) reads exactly `'$RANKS-<category>/'`, `'$VOLS-<category>/'` and
the PdsFile entries for each category / bundle set / bundle. It never reads `'$PRELOADED'`
and never reads any `'$VOLINFO-…'` key. So two of the four kinds named in the preceding
sentence are not re-read, and a memcached that lost only its `$VOLINFO` entries is not
repaired by this call. The method's own docstring (lines 269–272) enumerates the real list
correctly, so the two docstrings contradict each other.
**Confidence: certain.**

### PD-3 — `_preload.py`, `preload()`, lines 524–528 — the non-directory category is neither cached nor merged

> "**One that exists but is not a directory is warned about as ignored and is not
> ignored**: that branch has no skip, so the path is constructed, cached permanently, and
> merged into the category-level merged directory's child list."

The headline (no `continue`, so the path is still constructed) is right. The two
consequences are wrong.

Demonstrated with a synthetic tree holding a regular file named `holdings/previews`:

```
WARNING | Not a directory, ignored: .../fake/holdings/previews
previews in CACHE? True
merged previews is_merged True abspath None      <- still the merged dir, not the file
merged previews childnames []                    <- nothing merged in
merged volumes  childnames ['COISS_2xxx']
```

Why: `_complete()` (pdsfile.py:1284–1286) only writes to the cache when
`'/' in self.logical_path`, and a category-level logical path (`'previews'`) has none — so
the physical object is never cached (pdsfile.py's own `_complete` docstring says as much:
"Three things are never cached … a path *at* category level"). And the merged-parent child
list is appended to only inside `child()` (pdsfile.py:1540–1550), which `_preload_dir`
never reaches because it returns at once on a non-directory — which the same sentence's
last clause correctly says.
**Confidence: certain.**

### PD-4 — `_preload.py`, `_preload_dir()`, lines 666–667 — `permanent` does not prevent trimming

> "Each directory it does visit is marked permanent, so it is never trimmed."

`permanent` is written in exactly four places and **read nowhere** in `src/` or `tests/`:

```
_preload.py:694   pdsdir.permanent = True
pdsfile.py:490    self.permanent = False   # If True, never to be removed from cache
pdsfile.py:748    this.permanent = True
pdsfile.py:1330   self.permanent = True
```

What actually keeps these entries out of the trim is that they were stored with
`lifetime=0` (`from_abspath(..., lifetime=0)`, `child(..., lifetime=0)`), which sets
`expiration=None` and keeps the key out of `DictionaryCache.keys`, the trim candidate set.
The stated causal link ("so it is never trimmed") does not exist. Note the sentence sits
next to `preload()`'s "Everything it caches is permanent", which *is* accurate for the same
reason (the explicit `lifetime=0`) — so the write-only attribute is doing no work here.
**Confidence: certain.**

### PD-5 — `_preload.py`, `load_volume_info()`, lines 363–364 — an empty data set ID does not stay an empty string

> "An empty version ID, an empty publication date and an empty data set ID stay empty
> strings."

True for the version ID and the publication date (`set('') != {'-'}`, so they survive as
`''`). False for the data set ID: `dsids = list(parts[5:])` yields `['']` for an empty
field and lines 447–448 convert that to `[]`, so element 4 of the cached tuple is an empty
*list*, not a list holding an empty string. Measured over the real `_volinfo` tables after
a preload: 724 of 5972 `$VOLINFO-…` entries have `[]`, **zero** have `['']`, e.g.

```
$VOLINFO-coiss_1xxx -> ('Cassini ISS Jupiter image collection', None, '1.0', '2005-06-10', [], '')
```

**Confidence: certain.**

### PD-6 — `_preload.py`, lines 35–37, 207–210 and 509–512 — the TypeError is unreachable in the configuration these docstrings otherwise inventory

> (module) "A memcached cache takes a method as a lifetime function; a dictionary cache
> does not, and stores it as a constant default instead, so the first store into such a
> cache that needs the default raises TypeError."
> (preload) "A dictionary cache is constructed only where the cache in place is not
> already one, and it is given `cache_lifetime()` as its default; that is a class method,
> which such a cache keeps as a constant rather than calling, so its first store that
> needs the default raises TypeError."

The mechanism is real (`DictionaryCache.__init__` tests `type(lifetime).__name__ ==
'function'`, so a bound classmethod lands in `self.lifetime`, and `set()` then evaluates
`time.time() + <method>`). But the guard the same sentence states — "constructed only
where the cache in place is not already one" — means preload never builds that cache here:
`PdsFile`, `Pds3File` and `Pds4File` each bind a `DictionaryCache` at class-definition time
(pdsfile.py:318 etc.) with the **plain function** `cache_lifetime_for_class`. Measured
after a real preload:

```
cache lifetime attr: None  func: <function cache_lifetime_for_class at 0x...>
```

i.e. the class-level cache survived and its lifetime function still works. A default store
after a preload therefore fails, if at all, the *other* way — the AttributeError that
`cache_lifetime_for_class`'s own docstring (lines 112–115) describes for `cls=None`:

```
>>> Pds3File.CACHE.set('xyzzy', 3)
AttributeError: 'int' object has no attribute 'interior'
```

This is also an internal inconsistency: the class docstring (lines 246–252) lists what is
unreachable here — "MemcachedCache, the PRELOAD_TRIES retry loop, pylibmc.Error and
DEFAULT_CACHING = 'all' are reached by no test here" — and `cls.CACHE` can only fail the
`isinstance(..., DictionaryCache)` guard if a MemcachedCache was constructed first. The
TypeError belongs on that unreachable list and is instead presented three times as a live
consequence.
**Confidence: likely.**

### PD-7 — `_preload.py`, `preload()`, line 519 — the rank and version tables are not recreated

> "The walk itself creates the category-level merged directories and the empty rank and
> version tables"

The merged directories are overwritten unconditionally (lines 713–714); the `$RANKS-` and
`$VOLS-` tables are created only where they are missing (lines 720–729, `try: _ =
cls.CACHE[key] except KeyError: cls.CACHE.set(...)`). Since the module docstring makes a
point of the merged dirs being rebuilt "unconditionally, discarding whatever the
import-time call left there", the coordinated verb invites the reader to expect the tables
to be reset too.
**Confidence: worth checking.**

---

### PD-8 — `_sorting.py`, `split_basename()`, lines 100–101 and 123–125 — the third element is not always the extension

> "The parts are an anchor, a suffix and an extension." … "Returns: tuple: the anchor, the
> suffix and the extension, for a name the default split handles."

`Pds3File.BUNDLESET_PLUS_REGEX` has **five** groups (group 3 wraps groups 4 and 5), and
line 142–143 returns `(group(1), group(2)+group(3), group(4))`. Measured:

```
'COISS_2xxx_previews.tar.gz'     -> ('COISS_2xxx', '_previews.tar.gz', '_previews')
'COISS_2xxx_v2_previews_md5.txt' -> ('COISS_2xxx', '_v2_previews_md5.txt', '_previews')
```

The third element is the *volume type*, not an extension, and the three parts no longer
concatenate to the name (the rules file's own contract comment,
`pds3file/rules/__init__.py:471`, says they must). The docstring picks out the bundle-set
branch for special mention ("a bundle set name splits before its version suffix instead")
but describes its result with the same three names as the ordinary branch.
**Confidence: certain.** See CD-1.

### PD-9 — `_sorting.py`, `split_basename()`, lines 110–112 — the bundle-name regex branch never runs

> "A bundle name consults the split rules first, and their answer is returned wherever it
> differs from the name given; otherwise the regular expression's groups are."

`test = self.SPLIT_RULES.first(basename)` always returns a **3-tuple**: every SPLIT_RULES
table in the tree (`pds3file/rules/__init__.py:475`, `pds4file/rules/__init__.py:453`, and
each rule module's `split_rules`, all checked) maps to tuples, and the base table ends with
the catch-all `(r'(.*)', 0, (r'\1', '', ''))`, which matches everything. So `test ==
basename` compares a tuple to a str and is never True, and `BUNDLENAME_PLUS_REGEX`'s groups
are never returned. Measured:

```
'COISS_2001_previews.tar.gz' -> ('COISS_2001_previews.tar', '', '.gz')   # the rules' answer
                                # the regex groups would be ('COISS_2001','_previews','.tar.gz')
```

The neighbouring sentence "which of the two mechanisms wins depends on the kind of name"
(lines 107–108) is wrong the same way for bundle names: the rules always win.
**Confidence: certain.** See CD-2.

### PD-10 — `_sorting.py`, `sort_logical_paths()`, Raises, lines 456–460 — the KeyError condition is over-general

> "KeyError: from the item read `__getitem__()` on the table of child names, **for a path
> with no slash in it**. Such a path becomes a top-level name but gets no entry in that
> table, and the walk subscripts one for every top-level name."

A slashless path only raises when *no other path in the list* supplies that top-level
name's entry. Measured:

```
['volumes']                          -> RAISED KeyError 'volumes'
['volumes', 'volumes/COISS_2xxx']    -> ['volumes/COISS_2xxx', 'volumes']   (no raise)
```

In the second case `'volumes'` gets a `child_names` entry from the deeper path, is treated
as a directory, and comes back as an "overlooked item" — which is the behaviour the
paragraph above (lines 441–447) describes. So the Raises entry and that paragraph describe
the same input differently.
**Confidence: certain.**

### PD-11 — `_sorting.py` line 74 / `_associations.py` line 74 — "defined on PdsFile" for two methods that live in `_PropertiesMixin`

> `_sorting.py`: "other methods called … version_info … All of those are defined on
> PdsFile. Two more come from a sibling mixin: …"
> `_associations.py`: "other methods called _recache, **all_versions**, … All of those are
> defined on PdsFile. Nine more come from sibling mixins: …"

`version_info` is `_properties.py:1496` and `all_versions` is `_properties.py:1545`, both in
`_PropertiesMixin` — not in the `PdsFile` class body. Under the reading the *next* sentence
establishes (a method that comes from a sibling mixin is called out separately), both are
misfiled. Under the other reading ("available on the bare `PdsFile` class rather than only
on `Pds3File`/`Pds4File`", which is how `_preload.py:231` spells it) both are fine. Worth
one clarifying clause, since the same block's "lazy properties read" line implies
`_PropertiesMixin` is deliberately not counted as a sibling.
**Confidence: worth checking.**

---

### PD-12 — `_associations.py`, lines 359–362 and 394–396 — the object is usually *not* written back to the shared cache

> "That object is written back to the shared cache when an answer is recorded."
> "The object is then written back to the shared cache, because the dictionary it just
> changed lives on the object."

`_recache()` (pdsfile.py:1368–1372) writes only when the cache **already holds** an entry
for the object's logical path. Under the default `DEFAULT_CACHING = 'dir'` an ordinary data
file is never cached, so the write-back does nothing. Demonstrated on a real file:

```
p = Pds3File.from_logical_path('volumes/COISS_2xxx/COISS_2001/data/1454725799_1455008789/N1454725799_1.IMG')
in cache before? False
p.associated_parallel('previews') -> previews/.../1454725799_1455008789
in cache after?  False
p2 = from_logical_path(same)  ->  p2 is p? False   p2 filled: None
```

So the answer survives on `p` alone and the next constructor call recomputes it — which
also undercuts `_cache_and_return`'s "None is what gets cached, so a later call gets the
same answer without looking again" (lines 391–393). The claim *is* true for directories
(a bundle directory is cached under `'dir'`), which is what makes it look right in casual
testing. **Confidence: certain.**

### PD-13 — `_associations.py`, `associated_abspaths()`, lines 198–201 — `must_exist=True` can return a path that does not exist

> "must_exist (bool): whether to return only paths that exist. False still globs a pattern
> that holds a wildcard … it changes the answer only for a pattern that names one file."

The own-volume-type block (lines 314–320) appends the label **unconditionally**; only
`data_abspaths` is filtered by `must_exist` (lines 322–327). Demonstrated:

```
p = from_logical_path('volumes/COISS_2xxx/COISS_2001/data/1454725799_1455008789/N9999999999_1.IMG')
p.exists -> False ;  p.label_basename -> 'N9999999999_1.LBL'   (a guess; the file is absent)
p.associated_abspaths('volumes', must_exist=True)
  -> ['/seti/opus/pdsdata/holdings/.../N9999999999_1.LBL']      # does not exist
```

**Confidence: certain.** See CD-3.

### PD-14 — `_associations.py`, `associated_abspaths()`, lines 185–190 — the row-plus-index-file duplication depends on which extension matches

> "It is not invisible for a pattern naming an index row: the pass that recognizes the row
> rewrites the pattern down to the index file itself, and that rewrite persists into the
> next pass, which finds no extension of its own in the shortened pattern and so matches
> the bare index file. The row and the index file are different paths, so the dedup keeps
> both."

This needs a *later* pass, i.e. the matching extension must not be the last in `IDX_EXT`.

* `Pds3File.IDX_EXT = ('.tab',)` — one pass, so there is never a next pass and the bare
  index file is never added. The whole paragraph is inert for PDS3.
* `Pds4File.IDX_EXT = ('.csv', '.tab')` — it happens for a `.csv` row. For a `.tab` row the
  first pass (`'.csv/' not in pattern`) globs the un-rewritten row path, which
  `glob_glob` → `os_path_exists` resolves through its own index-row branch to the same row
  path, and the second pass then dedups against it; the index file is not added.

Stated flatly, the sentence is true only for a `.csv` row on `Pds4File`.
**Confidence: certain** for the `IDX_EXT` values and the `.tab`-first-pass path;
**likely** on whether the two spellings of the row path always dedup.

### PD-15 — `_associations.py`, `associated_parallel()`, lines 364–366 — more than two paths return without caching

> "Two paths return without caching anything, both of them before the caching begins:"

The two cached-answer returns (lines 469–471 and 495–497) also return without recording
anything. The trailing qualifier ("before the caching begins") is what carries the
distinction, but the count as written is wrong.
**Confidence: worth checking.**

---

### PD-16 — `_local_fs.py`, `os_listdir()`, lines 292–302 — the archives bullet omits a category-level passthrough that the checksums bullet flags as its own exception

> "* a checksums directory does the same … **and except at the category level, where it
> passes the listing through unchanged**;
> * an archives directory lists the bundle tree and appends `.tar.gz`, or
> `_<voltype>.tar.gz` outside volumes;"

The archives branch has the identical category-level check (lines 395–398,
`if len(parts) == 1: return results`) and the checksums-archives branch has **none**.
Demonstrated with `SHELVES_ONLY = True` against the real tree:

```
archives-volumes           -> ['HSTJx_xxxx_v1.2', 'COCIRS_0xxx_v3', ...]           n=83  (passthrough)
checksums-volumes          -> ['HSTJx_xxxx_v1.2', 'COCIRS_0xxx_v3', ...]           n=83  (passthrough)
checksums-archives-volumes -> ['HSTJx_xxxx_v1.2_md5.txt', 'COCIRS_0xxx_v3_md5.txt'] n=83  (NOT a passthrough)
```

Attaching the exception to one bullet of three tells the reader the other two lack it; in
fact one has it and one does not.
**Confidence: certain.**

### PD-17 — `_local_fs.py`, `os_listdir()`, line 297 — "lists the bundle tree" is wrong for the case the same sentence is about

> "an archives directory lists the bundle tree and appends `.tar.gz`, or
> `_<voltype>.tar.gz` outside volumes"

`testpath = abspath.replace('/archives-','/')` (line 392) lists the tree being archived —
for `archives-previews` that is the previews tree, not the bundle tree. The clause "outside
volumes" is about exactly those cases. Compare the checksums bullet, which gets this right
("against the tree it checksums").
**Confidence: likely.**

### PD-18 — `_local_fs.py`, `_non_checksum_abspath()`, lines 84–87 — contradicted by `os_listdir()` in the same file

> "The `checksums-volumes` and `checksums-archives-volumes` categories are the ones whose
> files are named that way; a checksum file in any other checksums category carries its
> volume type and does reduce to the path it covers."

`os_listdir`'s checksums branch (line 382) is `if voltype == 'volumes' or voltype ==
'bundles':` → bare `_md5.txt`, and the docstring bullet for it says so ("it reserves the
bare `_md5.txt` for bundles as well as for volumes"). So `checksums-bundles` — the PDS4
category — is a third category naming its files `<bundle>_md5.txt`, and a path under it
hits the same "returns a path that names nothing" trap `_non_checksum_abspath` describes.
Two docstrings in one file disagree about the same rule.
**Confidence: likely** (the test PDS4 tree carries no checksums categories, so this rests on
`os_listdir`'s own naming code rather than on disk).

### PD-19 — `_local_fs.py`, module docstring, lines 7–10 — "every part of this package" is not true

> "Every part of this package that needs to know whether a file exists, whether a path is a
> directory, what a directory contains, or which paths match a wildcard goes through this
> module rather than through `os` and `glob`."

Counter-examples inside `src/pdsfile`, two of them in a file under review in this same PR:

```
_preload.py:766    if os.path.exists(icon_path):
_preload.py:786    if os.path.exists(testfile):          # the case-sensitivity probe
_properties.py:341 if abspath and os.path.exists(abspath):
_properties.py:951 if os.path.exists(self.abspath + '/../' + info_name):   # info_basename
_path_utils.py     glob.glob('/Library/WebServer/Documents/holdings*')
holdings_maintenance/**  os.path.exists / os.listdir throughout
```

The point the sentence is making (the SHELVES_ONLY indirection) survives a narrower claim.
**Confidence: likely.**

### PD-20 — `_local_fs.py`, `os_path_exists()`, lines 110–148 — no `Raises:` section, but it can raise

The index-row branch (lines 154–161) calls `cls.from_abspath()`, which raises `ValueError`
for a path with no holdings component, and `pdsf.child_of_index(..., flag='')`, which
reaches `get_indexshelf()` and can raise `OSError` (index file missing) or `ValueError`
(not an index). The prose promises a bool for all four paths and lists no exception; the
sibling `os_path_isdir()` in the same file does carry a `Raises:` block for its one
uncaught `KeyError`.
**Confidence: worth checking.**

### PD-21 — `_local_fs.py`, `os_listdir()`, line 314 vs 299–302

> "Returns: list: the basenames, **in the order the underlying listing gave them**."

contradicted eleven lines earlier by "puts any AAREADME the real filesystem has in front"
(`return aareadmes + filtered`, line 448).
**Confidence: worth checking.**

---

### PD-22 — `_opus.py`, class docstring, lines 46–52 — `pdsfiles_for_abspaths` is a fourth sibling-mixin method, not a `PdsFile` one

> "other methods called from_abspath, from_logical_path, **pdsfiles_for_abspaths**, and the
> optional opus_prioritizer hook … All of them are defined on PdsFile or on its subclasses.
> **Three** more come from sibling mixins: glob_glob and os_path_exists from _LocalFsMixin,
> shelf_lookup from _ShelfMixin."

`pdsfiles_for_abspaths` is `_SortingMixin.pdsfiles_for_abspaths` (`_sorting.py:681`), called
at `_opus.py:176` and `:346`. `_associations.py`'s class docstring (lines 82–83) lists that
very method under `_SortingMixin` in its sibling-mixin block, so the two files under review
classify the same method two different ways, and the count "Three" should be four.
**Confidence: certain.**

### PD-23 — `_opus.py`, `opus_products()`, lines 200–204 — four of the five example keys do not exist

> ```
> ('Cassini VIMS', 130, 'covims_full',     'Extra Preview (full-size)',  True)
> ('Cassini CIRS', 618, 'cirs_browse_pan', 'Extra Browse Diagram (Pan)', True)
> ('metadata',      40, 'ring_geometry',   'Ring Geometry Index',        True)
> ('browse',        30, 'browse_medium',   'Browse Image (medium)',      True)
> ```

Against the tables:

| docstring | actual |
|---|---|
| `('Cassini VIMS', 130, 'covims_full', 'Extra Preview (full-size)', True)` | `('Cassini VIMS', 130, 'covims_full', 'Extra Preview (full)', False)` — `COVIMS_0xxx.py:148` |
| `('Cassini CIRS', 618, 'cirs_browse_pan', …, True)` | slug is `cocirs_browse_pan` — `COCIRS_xxxx.py:590`; `cirs_browse_pan` appears nowhere |
| `('metadata', 40, 'ring_geometry', …, True)` | PDS3 rank **50**, PDS4 rank 40, **both `False`** — `pds3file/rules/__init__.py:523`, `pds4file/rules/__init__.py:500` |
| `('browse', 30, 'browse_medium', …, True)` | `False` — `pds3file/rules/__init__.py:508` |

Only line 200, `('Cassini ISS', 0, 'coiss_raw', 'Raw Image', True)`, is a verbatim entry
(`COISS_xxxx.py:241`). The uniform `True` in the fifth column looks like the fabricated
part: four of the five real entries are `False`, and `default_checked` is the field a
reader is most likely to take on faith.
**Confidence: likely.**

---

## CODE DEFECTS

### CD-1 — `_sorting.py:142-143` — `split_basename()` returns the wrong group for a PDS3 bundle set

```python
return (matchobj.group(1), matchobj.group(2) + matchobj.group(3),
        matchobj.group(4))
```

`BUNDLESET_PLUS_REGEX` has five groups and group 3 *contains* groups 4 and 5, so this
returns `(stem, version+voltype+archive-suffix, voltype)` — the voltype twice and the
`_md5.txt`/`.tar.gz` ending nowhere. `'COISS_2xxx_previews.tar.gz'` →
`('COISS_2xxx', '_previews.tar.gz', '_previews')`. `group(5)` was presumably meant. The
docstring papers over it by calling the third element "the extension" (PD-8). Low impact —
the value feeds only the sort key, where the duplicated voltype is harmless — but any
caller that trusts "three strings that concatenate to the original basename" is wrong.

### CD-2 — `_sorting.py:148-157` — dead branch in `split_basename()`

`test = self.SPLIT_RULES.first(basename)` is always a tuple, so `if test == basename:`
(tuple vs str) is never True and the `BUNDLENAME_PLUS_REGEX` groups are unreachable. Either
the comparison was meant to be against a rule that *declines* to rewrite (which no rule
table expresses), or the branch should go. Documented as live by PD-9.

### CD-3 — `_associations.py:314-320` — the label ignores `must_exist`

The `label_abspath` is appended with no existence test while the sibling `data_abspaths`
loop three lines later has one, so `associated_abspaths(..., must_exist=True)` can return a
path that is not there (demonstrated in PD-13). `label_basename` returns a *guessed*
basename when the object itself does not exist (`_properties.py:1109-1113`), which is what
makes the guessed path reachable.

### CD-4 — `_preload.py:754-755` — missing `continue` (already flagged in bold by the prose)

```python
if not cls.os_path_isdir(category_abspath):
    cls.LOGGER.warn('Not a directory, ignored: ' + category_abspath)
```

The docstring flags the missing skip, so this is documented rather than hidden; its
description of what happens next is wrong (PD-3). The practical damage is small precisely
*because* the object is not cached and not merged.

### CD-5 — `pdsfile.py:490,748,1330` + `_preload.py:694` — `permanent` is write-only

Four writes, zero reads (PD-4). Either the attribute should be consulted by the trim path
or it should go; as it stands `pdsdir.permanent = True` in `_preload_dir` is a no-op, and
for the category-level directory it is set on an object that is not even in the cache.

---

## Substantial claims checked and found accurate — do not re-spend the effort

**`_preload.py`**
* The DictionaryCache/MemcachedCache lifetime-function asymmetry itself: `DictionaryCache.__init__`
  tests `type(lifetime).__name__ == 'function'`, `MemcachedCache.__init__` tests
  `in ('function','method')`. The described TypeError mechanism is real (only its
  reachability is at issue — PD-6).
* `cache_lifetime_for_class`: six branches in the stated order; `cls=None` really does drop a
  bookkeeping value into the third test — reproduced: `AttributeError: 'int' object has no
  attribute 'interior'`.
* `is_preloading`: `get_now` bypasses the local buffer, and `'$PRELOADING'` is written
  nowhere in the package (only read, `_preload.py:159`).
* `pause_caching` / `resume_caching`: pauses nest on both cache classes; DictionaryCache
  defers trimming, MemcachedCache defers flushing; only the resume that returns the count to
  zero acts.
* `get_permanent_values`: `permanent_values` exists on `MemcachedCache` (line 800) and not on
  `DictionaryCache`, so the whole-success path really does raise AttributeError on a
  dictionary cache; `preload()` guards the call with `if cls.MEMCACHE_PORT`.
* The case-sensitivity probe: reproduced exactly. `Pds3File` at `.../holdings` →
  `FS_IS_CASE_INSENSITIVE False`; `Pds4File` at `.../pds4-holdings` (no `/holdings`
  substring, so the path is compared against itself) → `True`.
* `cache_category_merged_dirs` is called at import time at `pdsfile.py:2435`,
  `pds3file/__init__.py:273` and `pds4file/__init__.py:237`; `preload()` overwrites every
  category unconditionally instead of going through it.
* `cls.__name__ != 'Pds4File'` for `_volinfo`, matching `_index_rows.py:416`'s
  `cls.__bases__[0].__name__ == 'Pds4File'`.
* `load_volume_info`: the six-element tuple, the dash→None rules for icon/version/date, the
  documents/EXTRA_README md5 split, the two-part bundleset reduction and the two alt keys,
  `lifetime=0` on every entry, and the OSError sources.
* The icon URL scheme (`/holdings/_icons`, then `/holdings<n>/_icons`).
* Every name in the class docstring's attribute inventory is on `PdsFile` itself and not
  only on the subclasses (`CATEGORY_LIST`, `VOLTYPES`, `EXTRA_README_BASENAMES`,
  `DICTIONARY_CACHE_LIMIT`, `PRELOAD_TRIES`, `new_merged_dir`, …).
* `preload_and_cache` really does re-export `is_preloading`, `pause_caching`,
  `resume_caching`.

**`_sorting.py`**
* The reach arithmetic in the module and class docstrings: 4 direct (`sort_basenames` +
  `logicals_for_abspaths`, `basenames_for_abspaths`, `abspaths_for_logicals`), 6 through
  `exists`, 3 through one of those six — 12 converters, all verified one by one.
* `basename_is_label`: `.LBL` (4 chars) is not a label; `LBL_EXT` is lowercase on both
  subclasses so the `.lower()` comparison really is case-insensitive; a name with no period
  can never match (the `>4` test excludes `lbl`, `xml`, `lblx`).
* `basename_is_viewable`: `VIEWABLE_EXTS` is dot-less and lowercase; no period → False.
* `sort_basenames`: `dirs_first` wins over `dirs_last`; `info_first` threshold is
  `>= 1 and <= len(basenames)`; the input list is not modified; `-version_info(...)[0]`
  puts the newest first (unsuffixed = rank 999999); `info_basename` is memoized on the
  object so it costs one resolution per sort, and `os_path_isdir` is *not* memoized so it
  really is one filesystem read per name.
* Bare-`PdsFile` behaviour: `split_basename` returns the string unchanged;
  `basename_is_label` raises AttributeError on `LBL_EXT`; `sort_basenames` raises on
  `BUNDLESET_PLUS_REGEX_I` only once it has a name to key.
* `sort_sibnames` really does append to the caller's list and really does group on the
  *first* period; `sort_siblings` collapses duplicate basenames to the last and always
  displaces a same-named sibling with `self`.
* `sort_logical_paths`: the "no path may be a directory of another" behaviour (overlooked
  item, appended alphabetically, warned), the extras check, both warnings gated on
  `cls.LOGGER`, top-level names sorted alphabetically, input iterated twice and not
  modified, and the `ValueError` from `from_logical_path` → `abspath_for_logical_path`.
* `viewable_childnames`' two-case account of `childnames` ordering — verified against
  `_properties.py:388-416` (directory: all four options off; index: class defaults, which is
  what `sort_childnames` would give).
* Every `must_exist` before/after-conversion note on the twelve converters, checked
  individually.

**`_associations.py`**
* `associated_parallel` resolves onto a *different* object when the volume type changes —
  demonstrated on `volumes/COCIRS_0xxx_v2/COCIRS_0401`: the asked object's
  `_associated_parallels_filled` stays `None` and the `_v3` object carries the dict.
* The rank rules: `'latest'` is converted to `None` before the move, word ranks raise
  afterwards because `self.bundletype_` is unchanged by the move, `'previous'` at the oldest
  and `'next'` at the newest clamp, and the answer is also filed under `pdsf.version_rank`
  when `rank is None` (observed key `('previews', 999999)`).
* `ASSOCIATIONS` is `None` on `PdsFile` (TypeError on subscript) and a plain `dict` on the
  subclasses (KeyError for an unknown category) — both reproduced; `IDX_EXT` is absent from
  `PdsFile`, and the `ASSOCIATIONS` lookup does come first.
* The index-row substitution, the checksums/archives recursion with `ValueError` swallowed
  for cumulative metadata, the case-sensitive glob, the parallel-tree fallback when the
  table yields nothing, and the KeyError/OSError drop for a row the index lacks.
* The nine sibling-mixin methods and their four mixins; `_SortingMixin` does not call back.

**`_local_fs.py`**
* The memoization claim, measured: one `Pds3File.preload` of the test tree →
  `CacheInfo(hits=10, misses=4685, maxsize=200, currsize=200)`, i.e. ~23× the cache size, so
  "tens of times that many … evicts throughout" is right; the key includes both the class
  and the flag.
* `os_path_exists` on a bare `PdsFile`: AttributeError for an ordinary path, and the
  `_infoshelf` opening test answers first without touching `IDX_EXT` — both reproduced.
* `os_path_isdir`'s uncaught `KeyError` (the handler catches only ValueError/IndexError/
  OSError), its non-memoization, and the exact split between the two fallbacks that call
  `os.path.exists` directly and the checksum fallback plus the covered-directory case that
  go through the memoized `os_path_exists`.
* `glob_glob`: `_clean_glob` really is `@functools.lru_cache`d (`_path_utils.py:177`), so
  "the memoized filesystem glob" is right; the flag reaches exactly the three call sites
  named and no others; the bisect start is case-sensitive while the stop test folds case;
  the slash-count guard; the `assert len(parts) == 2`; the OSError from `_get_shelf`
  outside any handler (`_shelves.py:333,339`).
* `_non_checksum_abspath`'s `.../checksums-volumes/SET/BUNDLE_md5.txt` →
  `.../volumes/SET/BUNDLE_md5.txt` worked example (apart from PD-18's scope).
* `os_listdir`'s shelf-key prefix rule, the `.DS_Store`/`._` filtering split, the
  `_info.pickle`/`_info.py` reduction, the AAREADME probe, and the FileNotFoundError →
  real-filesystem path that serves the documents tree.

**`_opus.py`**
* `opus_products` is the only method in the package that imports `PdsFile` (deferred, inside
  the body); the sibling-class selection (`__subclasses__`, `family_cls`, first non-family
  sibling, `LOCAL_PRELOADED[0]` else the substituted root) and the all-index suppression.
* The version grouping and the two sorts, including that the sublist order is read off
  `x[0]` *after* the path sort.
* The `opus_prioritizer` disagreement: `from_opus_id` rebinds from the return value,
  `opus_products` discards it — and both implementations in the tree (`GO_0xxx.py:756`,
  `NHxxxx_xxxx.py:498`) mutate in place *and* return the dict, exactly as claimed.
* Five-element OPUS keys are what the tables really hold (only the specific example values
  are wrong — PD-23), and `''` is really filed as a key after an error log.
* `FILESPEC_TO_BUNDLESET`, `OPUS_ID_TO_SUBCLASS`, `OPUS_PRODUCTS` are `None` on `PdsFile`,
  `CROSS_PDS3_PDS4_PRODUCTS` is absent from it, and all four are real tables on both
  subclasses.
