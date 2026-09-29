# PR-30a, round 4 — adversarial docstring review, second read

Head verified: `git -C /seti/all_repos/rms-pdsfile-pr30a/work rev-parse HEAD` =
`e8af08085655c4bd9c4d46fc9c6f58c4a66b8244`. Base tree at `80f5e523`.

Slice: `src/pdsfile/pds3file/__init__.py`, `src/pdsfile/pds4file/__init__.py`,
`src/pdsfile/tools/__init__.py`, `src/pdsfile/tools/show_opus_products.py`.

Every file was read through `git show e8af080:<path>` / `cat`, not from a cache. All
measurements ran with `PYTHONPATH=/seti/all_repos/rms-pdsfile-pr30a/work/src`,
`PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`,
`PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings`,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3). Scratch scripts are under
`.../scratchpad/r4/`.

Attribution of each finding to **[corrections]** (text written by `37c5fa6`, `4a25267`
or `e8af080`) or **[first read missed]** (text that survived those commits unchanged)
was taken from `git blame` on `e8af080` plus `git diff 9567e57 4a25267`.

Tally: **11 disproved**, 7 of them introduced by the corrections and 4 missed by the
first read. Plus 7 misleading-but-not-false, 3 unverifiable, 4 code defects.

---

## 1. Claims disproved

### D1 — `pds3file/__init__.py:198-199`, `pds4file/__init__.py:178-179`: `new_pdsfile()` does run `__init__`. **[corrections]**

> "``copy()`` and ``new_pdsfile()`` build their result with ``__new__`` and never run
> this at all."

`new_pdsfile()` runs `__init__` on every call. `pdsfile.py:589-591`:

```python
this = cls.__new__(cls)

source = cls()                      # <- this is a full construction
for (key, value) in source.__dict__.items():
```

The `__new__` builds the *returned* object, but the values it is filled with come from
a second object built with `cls()`, which runs `__init__`. Measured by wrapping
`Pds3File.__init__` with a counter (`t4.py`):

| call | `__init__` calls |
|---|---|
| `p.new_pdsfile()` | **1** |
| `p.new_pdsfile(copypath=True)` | **1** |
| `p.copy()` | 0 |

Only `copy()` (`pdsfile.py:902-903`) avoids it. Naming the two together is exactly the
relationship error the brief warns about: the names look alike and only one of them
holds.

### D2 — same two sentences: the reach/do-not-reach split is not a real distinction. **[corrections]**

> "Several of them reach this: ``from_abspath()`` and ``from_path()`` build a blank
> object and fill it in. Several do not: ``from_logical_path()`` answers from the class
> cache where the cache holds the path"

All three constructors are cache-first, and all three build a blank object on a miss.
`from_abspath` reads the cache at `pdsfile.py:1816-1822`; `from_path` at
`pdsfile.py:2074-2077`; `from_logical_path` at `pdsfile.py:1727-1731`. Measured
(`t4.py`, `t5.py`, `t6.py`, `t20.py`):

| call | cold cache | warm cache |
|---|---|---|
| `from_abspath(<abs>)` | 4 | **0** |
| `from_logical_path('volumes/COISS_2xxx/COISS_2001')` | **4** | 0 |
| `from_path('volumes/COISS_2xxx/COISS_2001')` (preloaded) | 1 for an uncached path | **0** |

`from_path` answers from the cache exactly as `from_logical_path` does, and
`from_logical_path` builds four blank objects on a cold cache (it falls through to
`cls.from_abspath(abspath)` at `pdsfile.py:1766`). The docstring puts one on each side
of a line that does not exist.

### D3 — `pds3file/__init__.py:85-86`, `pds4file/__init__.py:74-75`: `set_easylogger()` does write an attribute. **[corrections]**

> "The fourth, ``set_easylogger()``, writes nothing either way and passes the call on;
> the override is where the base's recursion stops."

Measured (`t3.py`): `Pds3File.__dict__['LOGGER']` is a `NullLogger` before
`Pds3File.set_easylogger()` and an `EasyLogger` after. The override at
`pds3file/__init__.py:567` is `cls.set_logger(pdslogger.EasyLogger())`, which writes
`cls.LOGGER` onto the class the call names — the same thing the other three do. The
base version writes nothing *directly*, but calling `PdsFile.set_easylogger()` still
leaves `Pds3File.__dict__['LOGGER']` and `Pds4File.__dict__['LOGGER']` as `EasyLogger`,
because it reaches the overrides.

"and passes the call on" is contradicted by the method's own docstring in the same file,
`pds3file/__init__.py:565-566`: "this override installs the logger on the class it was
called on **instead of passing the call further down**." (Same pair at
`pds4file/__init__.py:74-75` and `:277-279`.)

### D4 — `pds4file/__init__.py:19-20`: three rule tables have no `PdsFile` counterpart, not two. **[corrections]**

> "Two more have no counterpart on ``PdsFile`` at all and are introduced here:
> ``ARCHIVE_PATHS`` and ``ARCHIVE_DIRS``."

`CROSS_PDS3_PDS4_PRODUCTS` is a third. It sits in the same `# Override the rules` block
(`pds4file/__init__.py:154`, and `pds3file/__init__.py:182`), it is a translator read at
run time (`_opus.py:284`: `self.CROSS_PDS3_PDS4_PRODUCTS.all(self.logical_path)`), and
it appears nowhere in `PdsFile`'s MRO. Measured (`t9.py`):

```
any('CROSS_PDS3_PDS4_PRODUCTS' in c.__dict__ for c in PdsFile.__mro__)  ->  False
Upper-case attrs in Pds4File body with NO counterpart anywhere on PdsFile MRO:
  ARCHIVE_DIRS, ARCHIVE_PATHS, ..., CROSS_PDS3_PDS4_PRODUCTS, IDX_EXT, LBL_EXT
```

The regexes, `IDX_EXT` and `LBL_EXT` are not rule tables; `CROSS_PDS3_PDS4_PRODUCTS` is.
The count is three.

The neighbouring claim that `Pds3File` leaves `PRODUCT_LBL_BASENAME_WO_EXT` at None
because `pds3file.rules` has no such table *is* right: base Nones not overridden in
`Pds3File` are `PRODUCT_LBL_BASENAME_WO_EXT`, `LOCAL_HOLDINGS_DIRS`, `LOG_ROOT_` and
`_LOG_TIMETAG` (the last three are not rule tables), and
`hasattr(pds3file.rules, 'PRODUCT_LBL_BASENAME_WO_EXT')` is False against True for
`pds4file.rules`.

### D5 — `pds3file/__init__.py:50-51`, `pds4file/__init__.py:39-40`: every rule module reads `SUBCLASSES`. **[corrections]**

> "Nothing forces the other two into their places: no rule module reads ``SUBCLASSES``"

Each of the 25 PDS3 rule modules ends with

```python
pds3file.Pds3File.SUBCLASSES['COISS_xxxx'] = COISS_xxxx
```

and each of the 6 PDS4 modules with the same on `Pds4File` — an attribute read of
`SUBCLASSES` followed by `__setitem__` on the dict it returns. The same docstring says
so six lines earlier (`:44-45`): "the per-volume-set rule modules are imported, and each
of them adds its own entry to that same registry as it is imported."

The ordering argument the sentence is supporting is sound, but what it needs is the
narrower claim that no rule module reads the **'default' entry**, or that
`SUBCLASSES = {}` is bound in the class body so the dict exists either way. As written
it is false, and it contradicts its own paragraph.

### D6 — `pds4file/__init__.py:342-344`: `archive_dirs()`'s `OSError` is not confined to SHELVES_ONLY. **[corrections]**

> "OSError: raised by ``glob_glob()`` under SHELVES_ONLY, when a shelf file its search
> has already located cannot be opened or read back."

`OSError` also arrives with SHELVES_ONLY **off**, which is `Pds4File`'s default and
what `show_opus_products` explicitly sets for it (`show_opus_products.py:154`,
`Pds4File.use_shelves_only(False)`).

`archive_dirs()` calls `self.glob_glob(pattern, force_case_sensitive=True)`
(`pds4file/__init__.py:360`). With SHELVES_ONLY off that goes to
`_clean_glob(cls, abspath, force_case_sensitive)` (`_local_fs.py:522`), which with
`FS_IS_CASE_INSENSITIVE` True — the class default at `pdsfile.py:321`, held until a
preload probes the filesystem at `_preload.py:796-800` — calls `repair_case()`
(`_path_utils.py:211`). `repair_case()`'s own `Raises:` documents the `OSError`
(`_path_utils.py:260-263`).

Demonstrated (`t14.py`, `t15.py`), with a parent directory made traversable but not
listable:

```
SHELVES_ONLY = False  FS_IS_CASE_INSENSITIVE = True
WILDCARD pattern:     RAISED: PermissionError [Errno 13] ...
                        File ".../_local_fs.py", line 465, in os_listdir
NO-WILDCARD pattern:  RAISED: PermissionError [Errno 13] ...
                        File ".../_local_fs.py", line 214, in os_path_exists
```

Both branches of `glob_glob` reachable from `archive_dirs()` raise it, and the wildcard
branch is real for this method: `cassini_iss` and `cassini_vims` `ARCHIVE_DIRS` emit
patterns such as `.../\3/1\4??xxxxx` (`cassini_iss.py:485`, `cassini_vims.py:466`).

The `AssertionError` entry beside it is correct — `assert len(parts) == 2` after
splitting on the info-shelf prefix, `_local_fs.py:560-561`, SHELVES_ONLY only, silent
under `-O`.

### D7 — `show_opus_products.py:102-103`: the OPUS-type collision does occur, in this holdings copy. **[corrections]**

> "Nothing here prevents the collision; a scan of 6,674 files across every volume of one
> holdings copy produced none."

It produces them. A scan of **4,831** files across every volume of
`/seti/opus/pdsdata/holdings` (`scan_live.py`; up to three files per directory, every
volume of every volume set, shelves-only, preloaded) found **6** files whose
`opus_products()` returns two distinct five-element keys sharing an OPUS type:

```
('Voyager RSS', 11, 'vgrss_occ_inv0_2', '200 m inversion, old pole', True)
('Voyager RSS', 12, 'vgrss_occ_inv0_2', '200 m inversion, old pole', True)
```

on

```
volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_05/RU1P2XDI.LBL
volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_1/RU3P2XDI.TAB
volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_2/RU3P2XDI.TAB
volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_5/RU3P2XDI.LBL
volumes/VG_28xx/VG_2803/U_RINGS/RAWDATA/RU3R1XDE.TAB
volumes/VG_28xx/VG_2803/U_RINGS/SORCDATA/RU3S1XDE.TXT
```

Demonstrated end to end. Table form — one row, and it is the *later* key's list, as the
sentence before predicts:

```
$ python -m pdsfile.tools.show_opus_products \
    --paths volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_05/RU1P2XDI.LBL | grep -c vgrss_occ_inv0_2
1
| vgrss_occ_inv0_2 | volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_05/RU3P1XDI.LBL |
```

pprint form on the same path — both keys:

```
('Voyager RSS', 11, 'vgrss_occ_inv0_2', ...): ['.../KM00_025/RU2P1XDI.LBL', ...
('Voyager RSS', 12, 'vgrss_occ_inv0_2', ...): ['.../KM00_05/RU3P1XDI.LBL', ...
```

The mechanism half of the paragraph is right; the evidence half is wrong, and it is the
half the corrections added. (Note the shape of the error: `37c5fa6` softened this claim
to "nothing observed produces one" on the 31 golden files — which I confirm have no
collision, `scan_golden.py` — and then `e8af080` *hardened* it again with a number.)

### D8 — `pds3file/__init__.py:45-46`, `pds4file/__init__.py:34-35`: the merged directories are not what lets a tree be read before a preload. **[first read missed]**

> "and the merged directory of each category is created, so that a tree can be read
> before any preload has run."

Measured (`t21.py`, `t22.py`). With `Pds3File.CACHE` cleared, so that no merged
directory exists at all:

```
CACHE after clear: 0
from_abspath      with NO merged dirs: Pds3File.COISS_xxxx("/.../volumes/COISS_2xxx/COISS_2001")
from_logical_path with NO merged dirs: Pds3File.COISS_xxxx("/.../volumes/COISS_2xxx/COISS_2001")
```

The tree reads fine without them. For the one path shape they do change, they make the
answer *emptier*:

```
WITH merged dirs:     'volumes' -> Pds3File-logical("volumes")            is_merged=True   childnames=0
WITHOUT merged dirs:  'volumes' -> Pds3File("/.../holdings/volumes")      is_merged=False  childnames=52
```

`cache_category_merged_dirs()`'s own docstring (`_preload.py:493-501`) gives the real
reason — one entry per category whose children are the union across every holdings
directory, "which is what makes several physical trees look like one" — and adds that
`preload()` does not go through it and overwrites every category entry itself. The
"so that" clause states a purpose the code does not serve.

### D9 — `show_opus_products.py:19-22`: the tests do import `main()` and call it. **[first read missed]**

> "which is why the tests under ``tests/holdings_maintenance/`` drive it with
> ``python -m`` in a subprocess against a disposable copy of a holdings tree, rather
> than importing ``main()`` and calling it the way they do for the tools that touch no
> holdings root."

`tests/holdings_maintenance/test_show_opus_products.py:22` is
`from pdsfile.tools import show_opus_products`, and
`test_main_parses_the_argv_it_is_given_and_sys_argv_otherwise` calls it in process,
twice:

```python
show_opus_products.main(['show_opus_products.py', '--paths'])   # line 230
show_opus_products.main()                                        # line 236
```

That test's own docstring names the reason — "A usage error is answered by the parser
before either root is read, so it is the one invocation that reaches main() and comes
back on a machine with no holdings." The claim as written says the tests do not do
this; they do, deliberately, and the docstring's own `Raises: SystemExit` entry
(`:115-117`) is what those two calls assert.

### D10 — `pds3file/__init__.py:33-38`: the per-tool enumeration omits `pdsdependency`'s use of a regex alias. **[first read missed, extended by corrections]**

> "ten class attributes are second names for the bundle-named regular expressions above
> them. They are what a PDS3 caller writes, and three of the PDS3 maintenance tools
> write them too: … ``pdsdependency`` reads ``volset_``, ``volname``, ``is_volume_dir``
> and ``is_volset_dir`` and names ``log_path_for_volume``; …"

The subject "They" covers both the nineteen aliases and the ten regex aliases. The one
place in `src/` outside `pds3file/__init__.py` where any of the ten regex aliases is
read is `holdings_maintenance/pds3/pdsdependency.py:1101`:

```python
if not pdsfile.Pds3File.VOLNAME_REGEX_I.match(basename):
```

A per-name grep of all 29 names across `src/` (`t7`-adjacent, reproduced in the report
body) gives 0 hits for nine of the ten regex aliases and 1 for `VOLNAME_REGEX_I`. Since
the sentence spells out, tool by tool, exactly which members each reads, the omission
reads as "no tool touches the regex aliases", which is false.

(Two rule modules also read a vocabulary alias — `voltype_` at
`pds3file/rules/NHxxxx_xxxx.py:622` and `pds3file/rules/GO_0xxx.py:862`. That does not
contradict "three of the PDS3 maintenance **tools**", but it does undercut the framing
that the vocabulary is a caller-facing façade the package itself does not use.)

### D11 — `pds4file/__init__.py:89-91`: `BUNDLENAME_PLUS_REGEX` adds a lower-case word group too. **[first read missed]**

> "``BUNDLENAME_PLUS_REGEX`` extends the bundle pattern to the ``.tar.gz`` and
> ``_md5.txt`` names that sit beside a bundle."

The pattern (`pds4file/__init__.py:120-121`) is

```python
BUNDLENAME_REGEX.pattern[:-1] + r'(|_[a-z]+)(|_md5\.txt|\.tar\.gz)$'
```

— character for character the PDS3 construction. There are **two** added groups, not
one. Measured (`t10.py`): `cassini_iss_cruise_foo` matches, group `'_foo'`;
`uranus_occ_u0_kao_91cm_bar` matches, group `'_bar'`. The PDS3 docstring names both
groups for the identical suffix ("a lower-case category word **and** an archive or
checksum ending", `pds3file/__init__.py:101-102`); the PDS4 one names only the ending,
so a reader comparing the two concludes the patterns differ where they do not.

---

## 2. Misleading but not false

**M1 — `pds3file/__init__.py:99-100` [corrections].** "``BUNDLESET_PLUS_REGEX`` takes
all four kinds of part, each optional: a version suffix, a category suffix, and a
``.tar.gz`` or ``_md5.txt`` ending." `.tar.gz` and `_md5.txt` are alternatives inside
one group (`(|_md5\.txt|\.tar\.gz)`), so at most three of the four can be present at
once. "each optional" invites the reading that all four can co-occur.

**M2 — `pds3file/__init__.py:101` [corrections].** "``BUNDLENAME_PLUS_REGEX`` takes only
**the last two**." Under the enumeration in the sentence just above, the last two are
`.tar.gz` and `_md5.txt`. What it actually takes is the category word (item 2) plus one
ending (item 3 or 4). The appositive that follows corrects it; the ordinal does not.

**M3 — `pds3file/__init__.py:101` [corrections].** "a lower-case category **word**".
`(|_[a-z]+)` accepts any lower-case word: `COISS_1001_foo` matches (`t8.py`). This is
precisely the difference the paragraph exists to draw — `BUNDLESET_PLUS_REGEX`
enumerates `_calibrated|_diagrams|_metadata|_previews` exactly, `BUNDLENAME_PLUS_REGEX`
enumerates nothing — and calling both "a category suffix"/"a category word" hides it.

**M4 — `show_opus_products.py:120-124` [corrections].** "IndexError … for a file whose
``opus_products()`` returns a key that is **not a five-element tuple**. The key is
subscripted for its OPUS type in three places." The three `[2]` subscripts (lines 189,
210, 247) raise only for a key shorter than three elements. A three- or four-element
tuple would pass all three and raise only in the `--raw` branch at `[3]`/`[4]`
(lines 248-249). The stated class of keys is wider than the stated mechanism. In
practice the only non-five key the contract admits, and the only one observed, is the
empty string (`_opus.py:252-253` "a five-element tuple, or the empty string";
`_opus.py:360-361`), and `''[2]` does raise — so the conclusion survives, the
generalization does not.

**M5 — `show_opus_products.py:93` vs `:41-42` and `:6-7`.** main() says "There are
**three** output forms"; `build_arg_parser` says "the **four** output forms --table,
--narrow-table, --pprint and --raw"; the module docstring lists four ("a table by
default, and can be a narrower table, a pprint dump or the raw dictionary instead").
Each is defensible alone; together they make the reader count twice.

**M6 — `pds3file/__init__.py:51-52`, `pds4file/__init__.py:40-41` [corrections].** "the
merged-directory call reads only what the class body binds."
`cache_category_merged_dirs()` reads `cls.CATEGORY_LIST` (`_preload.py:504`), which is
bound in **`PdsFile`**'s class body (`pdsfile.py:344`), not in `Pds3File`'s or
`Pds4File`'s (`t18.py`: `CATEGORY_LIST bound on: ['PdsFile']`, against
`CACHE bound on: ['Pds3File', 'PdsFile']`). The conclusion — that the call does not
depend on the rule import — holds.

**M7 — `pds4file/__init__.py:87-89` [first read missed].** "its 'plus' form adds the two
forms of version suffix and nothing else, where the PDS3 side's admits an archive
extension and a checksum basename too." The PDS3 side also admits four more version
suffixes (`_in_prep`, `_prelim`, `_peer_review`, `_lien_resolution`) and four category
suffixes, so the named difference is not the whole difference. Separately, the PDS4
group is quantified `*`, not `?`, so it repeats: `cassini_iss_v1.0_v2.0` matches
(`t10.py`).

---

## 3. Claims I attacked and could not break

Measured, not read:

* **Nineteen aliases, thirteen properties and six methods.** `Pds3File.__dict__` holds
  exactly 13 `property` objects and 8 plain functions, of which `__init__` and
  `__repr__` are overrides and the other 6 are one-line forwards (`t1.py`). Every
  forward target exists on `PdsFile` or a mixin; five of them (`bundleset`,
  `bundleset_`, `bundlename`, `bundlename_`, `bundletype_`) are instance attributes set
  in `PdsFile.__init__` rather than class members, which "member of the base class"
  covers (`t2.py`).
* **Ten regex aliases**, five regexes each with a twin on the PDS3 side; five regexes
  with a twin of three of them on the PDS4 side (no `BUNDLESET_REGEX_I`, no
  `BUNDLENAME_REGEX_I` — and nothing in shared code reads either, so no breakage).
* **A volume set's mission code admits a lower-case `x` and a volume's does not.**
  `[A-Z][A-Z0-9x]{1,5}` against `[A-Z][A-Z0-9]{1,5}`. Real in the tree: `HSTUx_xxxx`,
  `NHxxLO_xxxx`, and also `HSTIx_xxxx`, `HSTJx_xxxx`, `HSTNx_xxxx`, `HSTOx_xxxx`,
  `NHxxMV_xxxx`, `VGx_9xxx` (`t7.py`).
* **`COISS_1001_v1` fails `BUNDLENAME_PLUS_REGEX`** and `BUNDLENAME_VERSION` requires
  one of **seven** suffixes, verified against all seven plus negatives (`t8.py`).
* **`BUNDLESET_PLUS_REGEX` takes all four kinds of optional part**, with the
  co-occurrence caveat at M1 (`t8.py`).
* **`Pds3File` leaves `PRODUCT_LBL_BASENAME_WO_EXT` None; only `Pds4File` fills it**
  (`t9.py`).
* **`repr(Pds3File())` is `Pds3File("")`, `repr(Pds4File())` is `Pds4File("")`**;
  `abspath` and `logical_path` are both `''`, not None, so the first branch is not taken
  (`t4.py`).
* **Three setters write onto the class the call names; the base writes onto every direct
  subclass and not onto itself.** `Pds3File.use_shelves_only(True)` → own dict yes,
  `PdsFile`/`Pds4File`/`COISS_xxxx` no, `COISS_xxxx` value True by inheritance;
  `COISS_xxxx.require_shelves(False)` reaches only that class.
  `PdsFile.use_shelves_only(True)` leaves `PdsFile.SHELVES_ONLY` False and sets both
  subclasses (`t18.py`).
* **`CACHE` holds a direct logger reference.** `Pds3File.CACHE.logger` is the same object
  after `set_logger(EasyLogger())` and stays a `NullLogger` (`t18.py`).
* **Exactly three PDS3 maintenance tools use the volume vocabulary**, and each tool's
  member list is right as far as it goes — `pdsarchives` (`:219`, `:223`, `:239`),
  `pdsdependency` (`:218`, `:221`, `:223`, `:1051`, `:1092`, `:1123`), `re_validate`
  (`:70`, `:680`, `:799`, `:808`, `:881`). No hit in `pdschecksums`, `pdsinfoshelf`,
  `pdslinkshelf`, `pdsindexshelf`, `shelf_consistency_check`, `linkshelf_repairs`,
  `crlf`, or any pds4 tool. (Modulo the omission at D10.)
* **The `AttributeError` handler cannot fire on any supported Python.**
  `requires-python = ">=3.10"`. A minimal three-module circular-import repro on 3.12
  (`circ/`) shows `import pkg.sub as sub` binding from `sys.modules` with no
  `AttributeError`. Importing a rule module directly
  (`import pdsfile.pds3file.rules.COISS_xxxx`) leaves all 26 PDS3 and 7 PDS4
  `SUBCLASSES` entries registered, and running a rule module as a script succeeds.
* **The `AssertionError` on `archive_dirs()`** matches `assert len(parts) == 2` at
  `_local_fs.py:561`, is SHELVES_ONLY-only, and is silent under `-O`.
* **`archive_paths()` checks nothing for existence** — it returns
  `.../archives-bundles/uranus_occs_earthbased/uranus_occs_earthbased.tar.gz` although
  `archives-bundles/` does not exist in this holdings copy at all (`t12.py`).
* **`ARCHIVE_DIRS` is fed the absolute archive path** and `ARCHIVE_PATHS` the logical
  path; both results get `root_` prefixed (`pds4file/__init__.py:311`, `:354-355`).
* **`Pds4File` adds exactly two methods beyond the overrides** — `archive_paths` and
  `archive_dirs`; its `__dict__` functions are `__init__`, `__repr__`, `archive_dirs`,
  `archive_paths` and four classmethods (`t18.py`).
* **`Pds3File.SUBCLASSES['default']` is what an unclaimed path resolves to.** A made-up
  `volumes/ZZZZ_1xxx/ZZZZ_1001` gives a bare `Pds3File`; `RES_xxxx` gives the rule
  subclass (`t19.py`). 25 rule modules, 26 keys.
* **`from_filespec` and `from_opus_id`** exist on `_OpusMixin`, so "one of the OPUS
  constructors" is right to be plural.
* **The output-form dispatch**, `--narrow-table` alone giving the wide-form-off table,
  the later category winning a table-form collision, `SystemExit(2)` for a bad command
  line and `SystemExit(0)` for `--help`, `KeyError: 'PDS3_HOLDINGS_DIR'` with the env
  unset, and `IndexError: string index out of range` at
  `show_opus_products.py:189` — all reproduced. The four `''`-key paths are
  `VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.LBL` and `.TAB`, and
  `VG_20xx/VG_2001/JUPITER/CALIB/VG1PREJT.DAT` and `.LBL`.
* **The alias `Returns:` sections match their targets** verbatim in substance for all
  nineteen, and both `log_path_for_*` aliases carry the `ValueError` their target
  documents. No alias forwards to a base member with an undocumented `Raises:` that the
  alias then drops.
* **`tools/__init__.py`**: `show_opus_products.py` is the only tool in the package; the
  module defines nothing.

---

## 4. Could not verify either way

1. **`show_opus_products.py:102-103`, "a scan of 6,674 files".** The population is not
   reconstructible from the tree — the figure appears only in `critiques/pr-30a/round-2.md`
   and `critiques/deferred-observations.md`, and the script that produced it (`t8c.py`)
   is not in the repository. My own enumeration of every volume, taking up to three files
   per directory, gave 4,831 candidates. I cannot say whether the 6,674-file scan really
   found nothing or found something and mis-tested for it; I can say the conclusion it
   is offered for is false (D7). A provenance number a later reader cannot reproduce is
   worth less in a docstring than the mechanism sentence beside it.
2. **`pds3file/__init__.py:516-518`, `volume_publication_date`'s "a modification date is
   the fallback".** The base (`_properties.py:2152-2162`) has three fallbacks tried in
   order plus a None short-circuit that returns `''` without filling the slot. Whether
   compressing that to "a modification date" is an error or a deliberate one-line
   summary for an alias is an editorial call, not a measurement.
3. **`pds3file/__init__.py:34-35`, "``pdsarchives`` names ``log_path_for_volume`` in its
   specification".** Verified textually at `pdsarchives.py:239`
   (`log_path_method='log_path_for_volume'`); I did not run `pdsarchives` against a
   disposable tree to see the log path it produces.

---

## 5. Defects in the code itself (not fixed)

**C1 — `show_opus_products.py:173-174`: `--debug` never prints a traceback.**

```python
if pdsf_inst is None:
    if debug:
        traceback.print_exc()
```

Both `ValueError`s were already handled by the `try/except` at `:163-169`, so no
exception is active when this runs and `traceback.print_exc()` prints `NoneType: None`.
The flag's help text — "Print traceback when there is an exception during pdsfile
instantiation" — is never satisfied. Reproduced:

```
$ python -m pdsfile.tools.show_opus_products --debug --paths not/a/real/path/at/all
NoneType: None
WARNING: Can't instantiate a Pds3File or Pds4File instance with the given path: ...
```

**C2 — `show_opus_products.py:189`: one bad key kills the whole run.**
`golden_opus_types = [prod_category[2] for prod_category, _ in opus_prod.items()]` is
evaluated for every file before any flag is consulted and before anything is printed,
so a single file whose `opus_products()` returns the documented empty-string key aborts
the run and discards the output of every path already resolved. Four real paths in this
holdings copy do it. `_opus.py:361` already detects the condition
(`if key == '': cls.LOGGER.error('Unknown opus_type for', pdsf.abspath)`) and carries
on; the tool does not.

**C3 — `_local_fs.py:471-511`: `glob_glob()`'s `Raises:` is incomplete.** It lists only
the `OSError` from `_get_shelf()`. It omits the `AssertionError` its own prose describes
at `:496-498`, and the `OSError` that `_clean_glob()` → `repair_case()` raises on the
non-SHELVES_ONLY path (`_path_utils.py:211`, documented at `_path_utils.py:260-263`).
This is the truth source D6 depends on: the `archive_dirs()` entry inherited its
"under SHELVES_ONLY" from a `Raises:` block that had nothing else in it.

**C4 — `_local_fs.py:214`: `os_path_exists()`'s `Raises:` omits its own `os.listdir`.**
With `force_case_sensitive` and `FS_IS_CASE_INSENSITIVE` both true the method calls
`os.listdir(parent)` with no handler. Its `Raises:` (`:152-157`) records only the
`ValueError` and `OSError` that come from the index-row branch. Demonstrated at D6.

---

## 6. Note on the correction ratio

7 of the 11 disproved claims (D1-D7) are text the three correction commits wrote, and 4
(D8-D11) are text they left alone. Five of the seven misleading items are also
correction text. The pattern in this slice is that the corrections were right about
*counts* they went and measured — nineteen aliases, seven version suffixes, the
lower-case `x`, `PRODUCT_LBL_BASENAME_WO_EXT`, `repr(Pds3File())` — and wrong about
*relationships and negatives* they asserted without running anything: which constructors
reach `__init__`, whether `set_easylogger` writes, whether any rule module reads
`SUBCLASSES`, whether the `OSError` needs SHELVES_ONLY, and whether the collision has
ever been observed. Every one of those five is falsifiable in under a minute at a
Python prompt.
