# PR-29a round 3 — adversarial read of the four mixin docstring files

Scope: `src/pdsfile/_derived_paths.py`, `src/pdsfile/_shelves.py`, `src/pdsfile/_path_utils.py`,
`src/pdsfile/_index_rows.py`. Executable code treated as ground truth; prose on trial.
Everything below was checked against the bodies and, where marked, executed against
`/seti/opus/pdsdata/holdings` and `/seti/opus/pdsdata/pds4-holdings`.

---

## PROSE DEFECTS

### P1. `_derived_paths.py` — module docstring, line 13 — a bundle-set-level file has **no** checksum file

> "a file at bundle-set level has a checksum file but no archive, because an archive is
> made of a bundle."

`checksum_path_and_lskip()` has exactly three ways to produce a path (lines 112–131):
`self.archives_`, `self.bundlename`, or a basename matching `checksums_*` / `superseded*` /
`*_support`. A bundle-set-level object in `volumes/` matches none of them and falls into the
`else` at line 132, `raise ValueError('Missing volume name for checksum file: ...')`.

Executed:

```
volumes/COISS_2xxx                       -> ValueError: Missing volume name for checksum file
volumes/COISS_2xxx/AAREADME.txt          -> ValueError: Missing volume name for checksum file
                                            (bundlename='', bundlename_='', is_bundleset_file=True)
documents/COISS_0xxx                     -> ValueError: Missing volume name for checksum file
```

The sentence is true only inside the archives tree (`archives-volumes/COISS_2xxx` →
`checksums-archives-volumes/COISS_2xxx_md5.txt`), which is the `self.archives_` branch. It is
false for every other category — and it is exactly the case the sentence exists to describe.
It also contradicts `checksum_path_and_lskip()`'s own docstring, which correctly enumerates
the three sources of a checksum path and documents the `ValueError` for everything else
(lines 98–100).

**Confidence: certain.**

---

### P2. `_derived_paths.py` — `checksum_path_if_exact`, lines 141 and 144–146 — the "only two kinds" premise and the reason given are both wrong

> "A checksum file covers a whole bundle, or a whole bundle set of archives. Only two kinds of
> object are therefore an exact match for one: a bundle directory, and an archive file's bundle
> set directory. Everything else -- a file inside a bundle, a category directory, a checksum
> file itself -- gets an empty string, **because the checksum file that covers it also covers
> other things**."

`checksum_path_and_lskip()`'s docstring, 60 lines earlier (lines 79–81), says a third kind of
object is exactly covered:

> "For the three kinds of directory that sit under a bundle set without being a bundle -- a
> name starting ``checksums_``, a name starting ``superseded``, or a name ending ``_support``
> -- one covers that directory."

For such a directory the checksum file covers *only* it, so the stated reason is false, yet
`checksum_path_if_exact()` still returns `''`: the guards at lines 165 and 168 test
`self.archives_ and self.is_bundleset_dir` and `self.is_bundle_dir`, and such a directory is
neither an archives object nor a bundle directory.

Live case, executed against the PDS4 tree:

```
bundles/uranus_occs_earthbased/uranus_occ_support
    bundlename=''  bundlename_=''  is_bundle_dir=False  is_bundleset_dir=True  isdir=True
    checksum_path_and_lskip() -> checksums-bundles/uranus_occs_earthbased/uranus_occ_support_md5.txt
    checksum_path_if_exact()  -> ''
```

So the premise sentence, the "only two kinds" claim and the causal explanation are all wrong
for a class of object the sibling docstring in the same class explicitly names. See also C2.

**Confidence: certain** (that the prose is wrong); the code behaviour behind it is C2.

---

### P3. `_derived_paths.py` — `archive_path_and_lskip`, lines 221–223 — "lands in the middle of the bundle set name" fails at the boundary

> "Sliced off the returned archive path instead it lands in the middle of the bundle set name,
> because that path carries an extra ``archives-`` the count does not account for."

The archive path is `root_ + 'archives-' + category_ + bundleset_ + ...` (line 252) and
`lskip = len(root_) + len(category_) + len(bundleset_)` (line 254). The bundle set name occupies
`[R+9+C, R+9+C+B)`; `lskip = R+C+B` falls inside it only when `B >= 9`, and only strictly inside
when `B > 9`. Executed over the PDS3 test tree:

```
GO_0xxx    bundleset_ len= 8  slice = '/GO_0xxx/GO_0002.tar.gz'    <- lands in the category
VG_20xx    bundleset_ len= 8  slice = '/VG_20xx/VG_2001.tar.gz'    <- lands in the category
VG_28xx    bundleset_ len= 8  slice = '/VG_28xx/VG_2801.tar.gz'    <- lands in the category
RPX_xxxx   bundleset_ len= 9  slice = 'RPX_xxxx/RPX_0001.tar.gz'   <- lands at the *start*
COISS_2xxx bundleset_ len=11  slice = 'ISS_2xxx/COISS_2002.tar.gz' <- middle, as documented
```

The load-bearing part of the paragraph ("it does not index the path this returns") is right;
the specific landing site is wrong for four of the bundle sets in this tree. Contrast the
equivalent sentence in `_shelves.shelf_path_and_lskip()` (line 172), which correctly hedges
with "lands somewhere arbitrary".

**Confidence: certain.**

---

### P4. `_derived_paths.py` — `log_path_for_index` Raises, lines 568–570 — the `place` ValueError is reachable and undocumented

> "Raises:
>     ValueError: if this file is not an index file. That check runs before the place option is
>     looked at, so a non-index file is reported as such even when the place option is also wrong."

`log_path_for_index()` delegates to `_log_path_for()` (line 578), which raises
`ValueError('unrecognized place option: ...')` at line 469. Both sibling methods document that
(lines 511–513 and 539–541); this one does not, and a reader is told the only ValueError here
means "not an index file". Executed:

```
metadata/.../COISS_2002_index.tab .log_path_for_index(place='nonsense')
    -> ValueError: unrecognized place option: nonsense
volumes/.../AAREADME.TXT .log_path_for_index(place='nonsense')
    -> ValueError: Not an index file: ...          (ordering claim itself is correct)
```

**Confidence: certain.**

---

### P5. `_derived_paths.py` — `log_path_for_bundle`, line 497 — the path template drops the version the sibling method spells out

> "The path is ``[dir/]category/bundleset/bundlename[_suffix]_time[_task].log``"

The target parts are `[self.category_, self.bundleset_, self.bundlename]` (lines 516–517), and
`bundleset_` is "Bundleset name + suffix + '/'" (`pdsfile.py:471`), so the version travels.
`log_path_for_bundleset()` writes its template as ``category/bundleset<version>`` (line 523) and
adds a paragraph explaining that the version is not the `suffix` argument; the reader who takes
the two templates together will conclude `log_path_for_bundle` drops the version. Executed:

```
volumes/COCIRS_0xxx_v3/COCIRS_0010/AAREADME.TXT .log_path_for_bundle('sfx', task='tk', dir='d')
    -> /tmp/logs/d/volumes/COCIRS_0xxx_v3/COCIRS_0010_sfx_<time>_tk.log
```

**Confidence: likely.**

---

### P6. `_derived_paths.py` — class docstring, lines 39–41 vs line 35 and the block — "owns the two class attributes"

> "The log group builds the path of a log file written about this file, and **owns the two class
> attributes** that decide where logs go and how they are time-stamped."

Two lines above: "A mixin of PdsFile; it holds methods only and **defines no state of its own**"
(line 35). And the block immediately below lists *three* class attributes read: `LOGFILE_TIME_FMT`,
`LOG_ROOT_`, `_LOG_TIMETAG` (lines 47–48) — all three are defined in `pdsfile.py`
(lines 234, 238, 2394), none in this module. Whichever "two" was meant, "owns" contradicts
"defines no state of its own", and the count contradicts the block three lines later.

**Confidence: worth checking** (defensible if "owns" is read as "writes"; `LOG_ROOT_` and
`_LOG_TIMETAG` are indeed the two written).

---

### P7. `_derived_paths.py` line 62 and `_index_rows.py` line 63 — "All of those are defined on PdsFile" while the block lists `_PropertiesMixin` properties

`_derived_paths.py` line 52–53 lists `is_bundle_dir`, `is_bundleset_dir` under "core properties
read" and `is_index` under "lazy properties read", then line 62 says "All of those are defined on
PdsFile. **One more comes from a sibling mixin**: ... `_LocalFsMixin`'s `os_path_exists`."
`is_index` is defined at `_properties.py:333`, i.e. on `_PropertiesMixin` — a sibling mixin.
`_index_rows.py` has the same shape: eight lazy properties, all of them in `_properties.py`,
then "All of them are defined on PdsFile. Three more come from sibling mixins".

This clashes with `_shelves.py` lines 149–151, written in the same change, which treats a
`_PropertiesMixin` property as exactly that: "All of those are defined on PdsFile. One more comes
from a sibling mixin: `info_shelf_expected` reads **`_PropertiesMixin`'s** `is_documents`".

The phrasing matches the package-wide convention in `_sorting.py`, `_preload.py`, `_local_fs.py`
and `_associations.py` (out of scope, all use it while listing lazy properties), so this may be
intentional shorthand. But a reader who checks `is_index` against `_shelves.py`'s usage will find
the two files disagree about what "defined on PdsFile" excludes.

**Confidence: worth checking.**

---

### P8. `_shelves.py` — `shelf_path_and_key_for_abspath`, line 497 — "The filesystem layer excludes the documents tree before it calls"

> "The filesystem layer excludes the documents tree before it calls."

Only `os_path_exists()` does. `_local_fs.py:164` guards with
`if cls.SHELVES_ONLY and f'{cls.PDS_HOLDINGS}/documents' not in abspath:`; the other three entry
points have no such guard — `os_path_isdir` (`_local_fs.py:238` `if cls.SHELVES_ONLY:`),
`os_listdir` (`_local_fs.py:~505` `if cls.SHELVES_ONLY:`) and `glob_glob`
(`_local_fs.py:511` `try: (pattern, key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')`).

Instrumented `shelf_path_and_key_for_abspath` under `use_shelves_only(True)` and recorded the
paths it was handed:

```
os_path_isdir  ('holdings/documents/COISS_0xxx')        -> ['.../documents/COISS_0xxx']
os_listdir     ('holdings/documents/COISS_0xxx')        -> ['.../documents/COISS_0xxx']
os_path_exists ('holdings/documents/COISS_0xxx/Archive-SIS.txt') -> []          (guarded)
glob_glob      ('holdings/documents/COISS_0xxx/*.txt')  -> ['.../documents/COISS_0xxx/*.txt']
```

`_properties.infoshelf_path_and_key` (line 1487) also calls it unconditionally on any abspath,
documents included. And a three-component documents path really does produce the bogus path the
paragraph describes:

```
Pds3File.shelf_path_and_key_for_abspath('.../holdings/documents/COISS_0xxx/Archive-SIS.txt')
    -> ('.../holdings/_infoshelf-documents/COISS_0xxx/Archive-SIS.txt_info.pickle', '')
```

So the mitigating sentence is false, and the divergence it excuses is live.

**Confidence: certain.**

---

### P9. `_shelves.py` — `shelf_path_and_lskip`, lines 176–178 — "directly under `_indexshelf-<category>/`" skips the bundle set level

> "so what this builds for 'index' -- the bundle's own name directly under
> ``_indexshelf-<category>/`` -- names nothing that exists."

The build is `root_ + dir_prefix + category_ + bundleset_ + this_bundlename + file_suffix +
'.pickle'` (lines 236–238), so the bundle set directory is in the path. Executed:

```
metadata/COISS_2xxx/COISS_2002/... .shelf_path_and_lskip('index')
    -> .../holdings/_indexshelf-metadata/COISS_2xxx/COISS_2002_index.pickle
real index shelf on disk
    -> .../holdings/_indexshelf-metadata/COISS_2xxx/COISS_2002/COISS_2002_index.pickle
```

The module docstring defines `<category>` as the tree name (`_indexshelf-<category>/`, line 18),
so "directly under" is wrong by one level. The parallel sentence in
`shelf_path_and_key_for_abspath` ("one directory below the path this builds", lines 502–503) is
accurate.

**Confidence: certain.**

---

### P10. `_shelves.py` — `shelf_path_and_key`, lines 250–253 — "the name reaches neither half of the pair" is false for the key

> "On an archive object the name reaches neither half of the pair: the path is the bundle set's
> shelf, and the key is emptied all the same."

`interior` is *not* empty for an archive file, so the `bundlename` argument does change the key:

```
archives-volumes/COISS_2xxx/COISS_2002.tar.gz
    interior = 'COISS_2002.tar.gz'
    shelf_path_and_key()                      -> (..._infoshelf-archives-volumes/COISS_2xxx_info.pickle,
                                                  'COISS_2002.tar.gz')
    shelf_path_and_key('info','COISS_2002')   -> (same path, '')
```

Lines 272–275 are `if bundlename: return (abspath, '') else: return (abspath, self.interior)`.
The name reaches the key half and flips the answer from "this tar.gz" to "the whole bundle set" —
which is what the rest of the sentence says, so the opening clause contradicts its own tail.

**Confidence: likely** (turns on whether "reaches" means "affects" or "appears in").

---

### P11. `_shelves.py` — `_get_shelf` Returns, line 313 — "keyed by interior path" is not true of index shelves

> "Returns:
>     dict: the shelf contents, keyed by interior path."

`_get_shelf()` is what opens index shelves too: `_index_rows.get_indexshelf()` calls
`cls._get_shelf(self.indexshelf_abspath, log_missing_file=False)` (`_index_rows.py:113`). The
module docstring of this same file says an index shelf "is keyed by row selection keys"
(line 18), and `get_indexshelf()`'s own Returns says "the row key mapped to a row number or a
sequence of row numbers". Verified: the keys of
`_indexshelf-metadata/COISS_2xxx/COISS_2002/COISS_2002_index.pickle` are `N1460960653` etc.,
which are not interior paths.

**Confidence: likely.**

---

### P12. `_shelves.py` — `info_shelf_expected`, lines 553–557 — the four-item enumeration omits the non-bundle directories under a bundle set

> "Four things have none: a checksum file, anything in the documents tree, a category-level
> directory, ... and anything at bundle-set level outside the archives tree -- **the bundle set's
> own directory as well as the files beside it, including its AAREADME**."

The code's final line is `return bool(self.bundlename)` (line 586), so it also returns False for
the three directories that `shelf_path_and_lskip()` in this same class says "get a shelf of their
own under their own name" (lines 164–166): `checksums_*`, `superseded*`, `*_support`. Those are
directories inside the bundle set, not "the bundle set's own directory" and not "files beside it",
so the gloss does not cover them. Executed:

```
bundles/uranus_occs_earthbased/uranus_occ_support
    shelf_path_and_lskip() -> _infoshelf-bundles/uranus_occs_earthbased/uranus_occ_support_info.pickle
    info_shelf_expected    -> False
```

Two docstrings in one file disagree about whether such a directory has an info shelf. See C3.

**Confidence: likely.**

---

### P13. `_shelves.py` — `_get_shelf`, lines 301–303 — "before the file is looked for" is one step off

> "The debug line announcing the open is written before the file is looked for."

The debug line's own guard performs the look-up: `if log_missing_file or os.path.exists(shelf_path):`
(line 329). The line is written before the *raise* (line 332–333), not before the filesystem is
consulted. The consequence stated in the rest of the sentence is correct.

**Confidence: worth checking** (mechanism described one step off).

---

### P14. `_shelves.py` — `shelf_lookup` Raises, lines 445–447 — `NameError` omitted

`_eval_null_key_record()` documents both `SyntaxError` and `NameError` (lines 88–92) as escaping
its `eval()`. `shelf_lookup()`, whose Raises block is otherwise exhaustive and names
`_eval_null_key_record` explicitly, lists only `SyntaxError`. (`_eval_null_key_record` argues
NameError is unreachable for a record the tools wrote, which may be the intent — but then the
same argument retires `SyntaxError` from `shelf_lookup` too, and it is listed.)

**Confidence: worth checking.**

---

### P15. `_index_rows.py` — class docstring, lines 42–43 — "must end in `.tab`" is false for PDS4

> "      filename.tab    is the name of an ASCII table file, which must end in
>                        ".tab";"

Index recognition goes through `indexshelf_abspath` (`_properties.py:308`), which tests
`self.extension not in (*cls.IDX_EXT, *upper)`. `Pds3File.IDX_EXT = ('.tab',)` but
`Pds4File.IDX_EXT = ('.csv', '.tab')` (`pds4file/__init__.py:80`), and every PDS4 index table in
the tree is a `.csv`:

```
pds4-holdings/metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_global_index.csv
    Pds4File.is_index -> True
```

`_local_fs.os_path_exists` also recognises the row notation by looping over `cls.IDX_EXT`, not by
`.tab`. The module docstring's `.../filename.tab/selection` (line 10) reads as an illustration;
the class docstring's "must end in" is a requirement claim, and it is wrong.

**Confidence: certain.**

---

### P16. `_index_rows.py` — `find_selected_row_key`, lines 138–144 and 169–171 — the `''` flag also suppresses the documented `OSError`

> "What happens when nothing matches depends on the flag: ... ``''`` returns the selection itself,
> unchanged."

and

> "Raises:
>     OSError: if the selection is a prefix of more than one key, which makes it ambiguous. The
>     longest-match rule resolves the other direction but not this one."

The `''` return at lines 234–235 sits **before** the ambiguity check at lines 239–241, so `''`
also short-circuits an ambiguous match — a case where something *did* match, so it is not covered
by "when nothing matches", and the OSError entry carries no flag qualification. Executed against a
selection that is a prefix of 76 keys:

```
find_selected_row_key('N14609', flag='=')  -> OSError: Index selection is ambiguous
find_selected_row_key('N14609', flag='<')  -> OSError: Index selection is ambiguous
find_selected_row_key('N14609', flag='>')  -> OSError: Index selection is ambiguous
find_selected_row_key('N14609', flag='')   -> 'N14609'     <- no error
```

This is the case the flag exists for: `_local_fs.os_path_exists` calls
`pdsf.child_of_index(parts[2], flag='')` (`_local_fs.py:159`), and `child_of_index`'s Raises block
inherits the same unqualified OSError claim (line 295).

**Confidence: certain.**

---

### P17. `_index_rows.py` — `find_selected_row_key`, line 144 — "the selection itself, unchanged"

> "* ``''`` returns the selection itself, unchanged."

`selection` has already been rebound by the truncation at lines 189–190, so what comes back is the
truncated selection. Executed on an index whose `filename_keylen` is 11:

```
find_selected_row_key('ZZZZZZZZZZZZZZZ', flag='') -> 'ZZZZZZZZZZZ'
child_of_index('ZZZZZZZZZZZZZZZ', flag='').basename -> 'ZZZZZZZZZZZ'
```

`child_of_index`'s docstring repeats it — "``''`` accepts the selection as given" (line 265).

**Confidence: certain** (that the string differs); "unchanged" may have been meant as "not
resolved to a key".

---

### P18. `_index_rows.py` — `data_abspath_associated_with_index_row`, lines 354–356 — `volumes` is not the bundles tree under PDS4

> "The path is assembled from this object's own bundle set, in the ``volumes`` category, so a row
> of an index that lives somewhere else still points into the bundles tree."

Line 452 is `parts = [self.bundleset_abspath('volumes')]` — a literal, not `cls.BUNDLE_DIR_NAME`.
`Pds4File.BUNDLE_DIR_NAME = 'bundles'` and the PDS4 holdings tree has no `volumes/` at all:

```
Pds4File .../metadata/uranus_occs_earthbased/..._global_index.csv
    bundleset_abspath('volumes') -> /seti/opus/pdsdata/pds4-holdings/volumes/uranus_occs_earthbased
    bundleset_abspath('bundles') -> /seti/opus/pdsdata/pds4-holdings/bundles/uranus_occs_earthbased
    os.path.exists('.../pds4-holdings/volumes') -> False
```

The two halves of the sentence contradict each other for PDS4, and the second half ("points into
the bundles tree") is the one a reader would act on. The vocabulary is fixed elsewhere in the same
change: `_opus.from_filespec`'s docstring says "the category is always the class's
``BUNDLE_DIR_NAME``, so the file this returns is always in the bundles tree". Note the class
docstring of this very mixin goes out of its way to describe the PDS3/PDS4 split in this same
method (lines 74–82) and does not mention this one. See C1.

**Confidence: certain.**

---

### P19. `_index_rows.py` — `data_abspath_associated_with_index_row`, lines 365–367 — "substituting" is a global replace

> "the answer is rewritten by substituting this row's basename for the neighbor's."

Line 468 is `abspath = abspath.replace(neighbor.basename, self.basename)` with no count, so every
occurrence of the neighbor's basename anywhere in the path is rewritten, not just the final
component. Harmless when row keys are long and unique; not what "substituting ... for the
neighbor's" describes if a key also appears as a directory name.

**Confidence: worth checking.**

---

### P20. `_path_utils.py` — `formatted_file_size` Parameters, lines 325–326 — "any non-negative number works" is false on (0, 1)

> "size: the number of bytes. It is compared for truth and used arithmetically, so **any
> non-negative number works**."

`order = int(math.log10(size) // 3) if size else 0` (line 337) goes negative for `0 < size < 1`,
and `FILE_BYTE_UNITS[order]` then indexes from the end of the list — silently, no exception.
Executed:

```
formatted_file_size(0.5)   -> '500 YB'
formatted_file_size(0.001) -> '1 YB'
formatted_file_size(0)     -> '0 bytes'     (as documented)
formatted_file_size(-1)    -> ValueError    (as documented)
```

The Raises block covers negative sizes and `>= 1e27`; the one silently wrong range is the one the
Parameters sentence declares safe. (The `[order]` lookup is the same "item read `__getitem__()`
on that list" the IndexError entry names, so the negative-index case belongs there.)

**Confidence: certain.**

---

## CODE DEFECTS (code is wrong, or the docstring papers over a gap)

### C1. `_index_rows.py:452` — hard-coded `'volumes'` breaks PDS4 index rows

```python
parts = [self.bundleset_abspath('volumes')]
```

should almost certainly be `self.bundleset_abspath(cls.BUNDLE_DIR_NAME)`. For a PDS4 index row
this builds a path under `pds4-holdings/volumes/`, a category that does not exist in a PDS4
holdings tree, so `data_abspath_associated_with_index_row()` returns a path that can never exist
and `data_pdsfile_for_index_row()` returns a `PdsFile` for it (it does not check existence, as its
own docstring says). Note the sibling column-name selection in `get_keys()` *does* branch on
PDS3/PDS4 (line 416), so a PDS4 row reads the right columns and then puts them in the wrong tree.
The docstring at lines 354–356 papers over this by calling the result "the bundles tree" (P18).

**Confidence: certain** that the literal is PDS3-only; **likely** that it is a bug rather than a
deliberate PDS3-only restriction (the method is reachable from `Pds4File` and the tree has PDS4
index tables).

### C2. `_derived_paths.py:159–174` — `checksum_path_if_exact()` misses the third exactly-covered kind

`checksum_path_and_lskip()` produces a checksum path that covers exactly a `checksums_*` /
`superseded*` / `*_support` directory (lines 124–131), but `checksum_path_if_exact()` tests only
`archives_ and is_bundleset_dir` and `is_bundle_dir`, so it returns `''` for those. Live case:
`bundles/uranus_occs_earthbased/uranus_occ_support` (see P2). Either the method should include
the third branch or the docstring should say the omission is deliberate; as written the docstring
asserts a premise ("A checksum file covers a whole bundle, or a whole bundle set of archives") that
its own class contradicts.

**Confidence: likely.**

### C3. `_shelves.py:551–586` — `info_shelf_expected` and `shelf_path_and_lskip` disagree

`shelf_path_and_lskip()` builds `_infoshelf-<category>/<bundleset>/<dirname>_info.pickle` for the
three non-bundle directories under a bundle set (lines 226–240) — "get a shelf of their own under
their own name" per its docstring — while `info_shelf_expected` returns `bool(self.bundlename)`
and so answers False for exactly those objects. Consequently `shelf_exists_if_expected()` returns
`None` ("no entry is expected") for a directory that does have its own shelf. The docstring's
four-item enumeration hides the gap by folding them into "anything at bundle-set level" (P12).

**Confidence: likely** (I could not confirm from the test trees whether the maintenance tools
actually write those shelves — the PDS4 tree here has no `_infoshelf-*` at all).

### C4. `_index_rows.py:234–241` — the `''` early return precedes the ambiguity guard

```python
        # If we have a single match, we're done
        if len(child_keys) == 1:
            return child_keys[0]

        # On failure, return the selection if flag is ''
        if flag == '':
            return selection

        # We disallow multiple matches because this can occur when a key is
        # incomplete
        if len(child_keys) > 1:
            raise OSError('Index selection is ambiguous: ...')
```

Under `flag=''` an ambiguous selection is silently accepted as a literal row key rather than
reported. That is the flag `_local_fs.os_path_exists` uses, so an ambiguous index-row path is
answered by building a non-existent row rather than by raising. Whether that is intended, the
prose (P16) does not say so.

**Confidence: worth checking** (may be deliberate — `''` means "don't fail").

---

## Substantial claims checked and found accurate — do not re-spend the effort

`_derived_paths.py`

* `checksum_path_and_lskip`'s three branches, their order (`archives_` wins over `bundlename`),
  the volume-type insert (`_metadata`, none for `volumes/`/`bundles/`), and the "archive of a
  metadata bundle still yields `..._metadata_md5.txt`" claim. Verified by execution.
* "everything from it onward is the checksum file's basename" — verified for all three branches
  (`len('checksums_') == len('checksums-')` makes it work).
* `archive_path_and_lskip`'s lskip really is the archived directory's prefix length: sliced off
  `dirpath_and_prefix_for_archive()[0]` it yields exactly the bundle name.
* `checksum_path_if_exact`'s "the check is made even when there was no candidate" —
  `os_path_exists('')` returns False; verified both branches against `COCIRS_0xxx`, which has
  real checksum files.
* `archive_path_if_exact`'s four exclusions and the ValueError-swallow.
* `dirpath_and_prefix_for_checksum` — both branches, and "from that object's own category" is
  right, because `archives_ + bundletype_ == category_` for every non-checksum object.
* `archive_logpath` — "only the second rewrite reaches the answer", including the counter-example:
  a checksum file really does log under `archives/checksums-volumes/...` and an archive under
  `archives/volumes/...`. Verified by execution.
* `set_log_root` — `''` is stored as `/` and every path is then built at the filesystem root
  (`/volumes/COISS_2xxx/COISS_2002_<time>.log`); only `None` selects the parallel default.
* `_pinned_log_timetag` — restore-if-own / delete-if-inherited, nesting, and the `__dict__`
  bookkeeping. Verified.
* `_log_path_for` — the assembled template, `target()` being called after `place` validation, the
  `lstrip('_')`/`rstrip('/')` normalisations, and the `place='parallel'` → `disk_ + 'logs/'`
  result. Verified.
* `log_path_for_index` — `dir` defaults to `'index'`, the `is_index` check precedes `place`
  validation, and the `rpartition('.')[0]` template.

`_shelves.py`

* `_eval_null_key_record` — first-colon partition (the modtime's colons really do come later in
  the tool's output format, `pdsinfoshelf.py:319–323`), `[:-1]` dropping the trailing comma,
  `eval('')` → SyntaxError, and the namespace chain for a bare name.
* "the sidecar's second line is the entry for the null key" — the writer sorts by absolute path,
  so the bundle directory's own row (key `''`) is the first entry after the `name = {` line.
* `shelf_path_and_lskip`'s lskip is the *data* path's prefix length, in both the archive and the
  non-archive branch (`abspath[lskip:]` gives `''`, `'data'`, `'COISS_2002.tar.gz'`,
  `'COISS_2002_index.tab'` for the cases tried).
* `_get_shelf`'s cache/serial-number paragraph, including the counter-intuitive part: verified
  that `SHELF_ACCESS_COUNT` rebinds onto the rule subclass and that two different rule subclasses
  each wrote serial number `1` into the one shared `SHELF_ACCESS`.
* "the four dictionaries are genuinely shared, because none of them is ever rebound" — grepped the
  whole repo; the only assignments are the class-body ones in `pdsfile.py`. `Pds3File.SHELF_CACHE
  is PdsFile.SHELF_CACHE` → True.
* `_get_shelf`'s OSError-inside-handler paragraph (`__context__`, no `raise ... from`).
* `shelf_lookup`'s "the sidecar is tried before the shelf, so a bundle whose sidecar is missing
  fails there rather than falling back" — confirmed live: the test tree has `.pickle` files and no
  `.py` sidecars, and `shelf_exists_if_expected()` on a bundle directory returns False for exactly
  that reason.
* `_close_shelf` / `close_all_shelves` keeping `SHELF_NULL_KEY_VALUES`.
* `shelf_exists_if_expected`'s three-valued return and "False comes only from an OSError".
* `shelf_path_and_key_for_abspath`'s 2-vs-3 component split and its ValueError cases, and the
  claim that a documents PdsFile carries no bundle name (verified: `documents/COISS_0xxx` has
  `bundlename=''`, and the instance method raises there).
* "`is_documents` is one comparison of an instance attribute and reaches no further" —
  `_properties.py:172` is `return self.bundletype_ == 'documents/'`.
* "`_PropertiesMixin` calls `info_shelf_expected`, `shelf_lookup` and
  `shelf_path_and_key_for_abspath` from here" — all three verified (`_properties.py:459, 462, 526,
  981, 1487`).

`_path_utils.py`

* `construct_category_list` — 4n−3 = 25, the exact loop order, the generator failure mode, and the
  ValueError when `documents` is absent. Executed.
* `logical_path_from_abspath` — trailing-slash behaviour, first-occurrence split, and the
  two-argument ValueError.
* `repair_case` — trailing-slash preservation across `os.path.abspath`, `found` reset per
  component, `os.listdir('/')` for k==1 vs `cls.os_listdir` afterwards, and the `UnboundLocalError`
  for the root path.
* `_clean_glob` — memoised on all three arguments, shared list object, unsorted order,
  `force_case_sensitive` only biting when `FS_IS_CASE_INSENSITIVE`.
* `formatted_file_size` — 1000-not-1024, `.3g`, `999999 -> '1e+03 KB'`, `0 -> '0 bytes'`,
  ValueError on negative, IndexError at 1e27 (the true threshold is 1e27·(1−4e−15); accurate to
  15 significant figures).
* `abspath_for_logical_path` — the four sources and their order, sources 3 and 4 writing
  `LOCAL_HOLDINGS_DIRS`, source 4's empty list leaving the next call to search again, the
  len==1 no-existence-check shortcut, and the "pick the first anyway" fallback.
* `selected_path_from_path`, `_clean_join`, `_clean_abspath`, `_needs_glob`.
* The module-level state contract: `CATEGORIES`, `FS_IS_CASE_INSENSITIVE` and
  `LOCAL_HOLDINGS_DIRS` are on `PdsFile` only, while `PDS_HOLDINGS`, `_HOLDINGS_ENV` and
  `LOCAL_PRELOADED` are overridden on both subclasses (grepped `pds3file/` and `pds4file/`);
  `is_logical_path` is a `PdsFile` classmethod; `glob_glob`/`os_listdir` are `_LocalFsMixin`
  classmethods; the ten-function count and the three/seven split.

`_index_rows.py`

* `get_indexshelf`'s error interpretation, including the re-raise: confirmed live on a PDS4 index
  whose shelf is absent but whose file exists and is an index — the original OSError comes back.
* `find_selected_row_key`'s four-stage match order, the longest-match rule, and the whole
  flag-guard analysis: `'bogus'` → TypeError, `'%s'` → ValueError, `'%d'` → TypeError. Executed.
* The neighbour fallbacks: a selection that sorts last gives the index's last key under both
  `'<'` and `'>'`; one that sorts first gives the index's first key under both. Executed with
  `'AAAAA'`/`'ZZZZZ'` (both sort last under `sort_basenames`) and `'0000000'`/`'N0000000000'`
  (both sort first). The IndexError analysis ("a single key is enough for either fallback") holds.
* `exact_match=True` making `''` behave like `'>'`.
* `child_of_index` — the cache read always misses (`CACHE` is keyed by lowercased *logical* paths,
  the lookup uses a lowercased *absolute* path), nothing is stored, `row_range = (min, max+1)`,
  `column_names` filled only when empty, `_exists_filled` set both ways, and "the shelf lookup
  that follows uses a key that came from the index's own key list" (`childnames` for an index is
  `list(shelf.keys())`, `_properties.py:411–412`).
* `get_keys` — first file-spec candidate wins (has `break`), **last** volume candidate wins (no
  `break`), `PATH_NAME` exact, all-three-empty when no file spec.
* The `__bases__[0].__name__ == 'Pds4File'` paragraph: a rule subclass's first base really is
  `Pds3File`/`Pds4File` (`COISS_xxxx.__bases__ == (Pds3File,)`,
  `uranus_occs_earthbased.__bases__ == (Pds4File,)`), `Pds4File.__bases__[0].__name__ ==
  'PdsFile'`, and `Pds4File.SUBCLASSES['default'] = Pds4File` (`pds4file/__init__.py:215`), so the
  fallback class really would read PDS3 column names. The two column lists really do differ.
* "`sort_basenames` matches each name against `BUNDLESET_PLUS_REGEX_I`, which only Pds3File and
  Pds4File define" — grepped; `PdsFile` only reads it.
* `data_abspath_associated_with_index_row`'s version claim: the suffix is carried only when the
  target category's voltype equals `self.bundletype_` (`bundleset_abspath`, `pdsfile.py:1174–1177`),
  so a `metadata` row does name the unversioned bundle set.
* `data_pdsfile_for_index_row`'s "returned whether or not the file is there".
