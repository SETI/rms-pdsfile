# PR-30a, round 2 — adversarial docstring review

Head verified: `git -C /seti/all_repos/rms-pdsfile-pr30a/work rev-parse HEAD` =
`2fd40c43c0e3fba3d4487dab2bb673f80cf36169`. Base tree at `80f5e523`.

Slice: `src/pdsfile/pds3file/__init__.py`, `src/pdsfile/pds4file/__init__.py`,
`src/pdsfile/tools/__init__.py`, `src/pdsfile/tools/show_opus_products.py`.

All measurements were run with
`PYTHONPATH=/seti/all_repos/rms-pdsfile-pr30a/work/src`,
`PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`,
`PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings`,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3). Scratch scripts are under
`.../scratchpad/r2/`.

---

## 1. Claims disproved

### D1 — `pds3file/__init__.py:26-27`: "a dozen" aliases. There are nineteen.

> "so a dozen properties and methods here are one-line aliases forwarding to the
> bundle-named member of the base class"

AST count of `Pds3File`'s body (`t5_ast.py`): 25 functions, of which **19** have a
body that is exactly `return self.<bundle-named member>` or
`return self.<bundle-named method>(...)`:

`log_path_for_volset`, `volset`, `volset_`, `is_volset`, `is_volset_dir`,
`is_volset_file`, `volname`, `volname_`, `is_volume`, `is_volume_dir`,
`is_volume_file`, `log_path_for_volume`, `volset_abspath`, `volset_pdsfile`,
`volume_abspath`, `volume_pdsfile`, `voltype_`, `volume_publication_date`,
`volume_version_id`.

No grouping gives twelve: 13 properties + 6 methods = 19. (The neighbouring claim
in the same sentence, "ten class attributes are second names for the bundle-named
regular expressions above them", *is* right — the ten `VOL*` names at lines
119-128.)

### D2 — `pds4file/__init__.py:26`: same count error.

> "so the dozen aliases ``Pds3File`` needs have no counterpart here"

Nineteen, per D1.

### D3 — `pds3file/__init__.py:19-20`: not every base `None` rule table is filled in.

> "**Which rules apply.** Every rule table the base class leaves as None is filled
> in from ``pds3file.rules``"

`PdsFile.PRODUCT_LBL_BASENAME_WO_EXT = None` (`pdsfile.py:376`) is a rule table —
`_properties.py:1838-1840` reads it — and `Pds3File` never fills it.
Measured (`t6_rules.py`):

```
PRODUCT_LBL_BASENAME_WO_EXT  Pds3File own=False val=NoneType   Pds4File own=True val=TranslatorByRegex
 PRODUCT_LBL_BASENAME_WO_EXT: PdsFile has? True val=None | r3 has? False
```

`pds3file.rules` has no attribute of that name, so the table cannot be filled from
there. The class docstring's matching bullet ("The rule tables, every one of them
taken from ``pds3file.rules``", line 86) is true of what *is* assigned, but the
module docstring's "every rule table the base class leaves as None" is not.

### D4 — `pds3file/__init__.py:29-34`: the list of tools that use the volume vocabulary is missing `pdsdependency`.

> "and the PDS3 maintenance tools write them too: ``pdsarchives`` names
> ``log_path_for_volume`` in its specification and reaches ``volume_pdsfile()`` and
> ``volset_pdsfile()`` to expand a command-line path, and ``re_validate`` reads
> ``volname`` and ``volset_``."

`pdsarchives` is right (`pds3/pdsarchives.py:239`, `:219`, `:223`). What the list
omits is `src/pdsfile/holdings_maintenance/pds3/pdsdependency.py`, which uses four
of the aliases and a fifth spelling:

- `pdsdependency.py:218` — `pdsdir.volset_`
- `pdsdependency.py:221,223` — `pdsdir.volname`
- `pdsdependency.py:1051` — `pdsdir.is_volume_dir and not pdsdir.is_volset_dir`
- `pdsdependency.py:1092` — `pdsf.is_volset_dir`
- `pdsdependency.py:1123` — `_common.log_paths_for(pdsdir, 'log_path_for_volume', …)`

`re_validate` is also under-described: besides `volname` (`:680,799,808,881`) and
`volset_` (`:799,808,881`) it names `log_path_for_volume` at `re_validate.py:70`.

The closing sentence — "The checksum, info shelf and link shelf tools use the
bundle-named methods instead" — checks out: `pdslinkshelf.py:449` and
`pds4linkshelf.py:503` use `_shelf_common.UNIT_LOG_PATH_METHOD`, and
`_shelf_common.py:58-59,583-584` picks `log_path_for_bundle` /
`log_path_for_bundleset` for the checksum and info-shelf tools.

Command: `grep -rn` over `src/pdsfile/holdings_maintenance/` for each alias name.

### D5 — `pds3file/__init__.py:36-38` and `pds4file/__init__.py:29-31`: the order of the three closing statements is not load-bearing.

> "The module ends by doing three things in order, and the order is what makes them
> work"

Measured by building a symlink copy of `src/pdsfile` (`cp -rs`) with only
`pds3file/__init__.py` replaced by a reordered version, then importing it:

| tail order | result |
|---|---|
| rule imports, default registration, merged dirs | `SUBCLASSES n=26`, `default->Pds3File`, `CACHE=25` before preload, `Pds3File.COISS_xxxx("…N1460960868_1.IMG")`, `opus products n=15` |
| default registration, merged dirs, rule imports | `SUBCLASSES n=26`, merged dir readable before preload (`Pds3File-logical("volumes")`, description `<em>PDS volumes</em> in Viewmaster`), same dispatch, `opus n=15` |

Same experiment on `pds4file/__init__.py` (imports before the default
registration): `SUBCLASSES n=7`, `default->Pds4File`,
`Pds4File.uranus_occs_earthbased("…/bundles/uranus_occs_earthbased")`.

Nothing depends on the relative order: no rule module *reads* `SUBCLASSES` (all 31
occurrences under `pds3file/rules/` and `pds4file/rules/` are assignments of the
form `SUBCLASSES['<name>'] = <class>`), and `cache_category_merged_dirs()`
(`_preload.py:490`) reads only `CATEGORY_LIST`, `CATEGORIES` and the class's own
rule tables, all bound in the class body. The one ordering that *is* load-bearing
is the one the code comment states — the rule import must follow the class body —
which is a different claim.

### D6 — `pds3file/__init__.py:40-41` and `pds4file/__init__.py:33-34`: the `AttributeError` handler is not what a recursive import raises.

> "The import is wrapped in a handler for ``AttributeError``, which is what a
> recursive import of ``pdsfile`` raises when a rule module is tested on its own."

The handler never fires. Traced lines 576-578 of `pds3file/__init__.py` and 355-357
of `pds4file/__init__.py` with `sys.settrace` while importing `pdsfile`,
`pdsfile.pds3file.rules.COISS_xxxx` and
`pdsfile.pds4file.rules.uranus_occs_earthbased` as the *first* import in a fresh
interpreter (`t4_trace.py`): `EXCEPT-BRANCH HITS: []` in all three.

The described mechanism cannot occur on a supported Python. A rule module's only
route back into the partially initialised package is
`import pdsfile.pds3file as pds3file` (`COISS_xxxx.py:66`,
`uranus_occs_earthbased.py:99`). Minimal reproduction (`mini/` in the scratchpad,
same package shape) shows that during the circular import
`hasattr(pkg, 'sub') = False` and the `import pkg.sub as sub` **still succeeds**,
binding from `sys.modules` — the fallback added in Python 3.7. `pyproject.toml:10`
declares `requires-python = ">=3.10"`, so the AttributeError the comment describes
is unreachable in every supported interpreter. (The wording is inherited from the
in-code comment at `:577-579`; the docstring promotes it to prose.)

### D7 — `pds3file/__init__.py:78-82`: `BUNDLENAME_PLUS_REGEX` does not admit a version suffix.

> "``BUNDLESET_PLUS_REGEX`` and ``BUNDLENAME_PLUS_REGEX`` extend the plain forms to
> the version suffixes, category suffixes, ``.tar.gz`` and ``_md5.txt`` names that
> appear beside a volume set, each of those parts being optional"

`BUNDLENAME_PLUS_REGEX` (line 109) appends only `(|_[a-z]+)(|_md5\.txt|\.tar\.gz)`.
Measured (`t7_regex.py`):

```
COISS_1001_v1        False      COISS_1001_previews        True
COISS_1001_v1.0      False      COISS_1001_md5.txt         True
COISS_1001_v1.0.1    False      COISS_1001.tar.gz          True
COISS_1001_in_prep   False      COISS_1001_previews.tar.gz True
```

(`COISS_1001_prelim` matches, but only because `_prelim` happens to be an
all-lowercase word that `_[a-z]+` swallows; `_v1`, `_v1.0`, `_v1.0.1`, `_in_prep`,
`_peer_review` and `_lien_resolution` — the other six suffixes
`BUNDLESET_PLUS_REGEX` spells out — do not.) `BUNDLESET_PLUS_REGEX` alone carries
the four kinds of part, and all seventeen probes against it matched as described.

Secondary error in the same sentence: `BUNDLENAME_PLUS_REGEX`'s extensions are the
names beside a **volume**, not "beside a volume set".

### D8 — `pds3file/__init__.py:244-248` and `pds4file/__init__.py:206-210`: "an object with no absolute path" is the wrong test.

> "an object with no absolute path is written as ``Pds3File-logical("...")`` around
> its logical path"

The branch tests `self.abspath is None` (line 254). A blank object has no absolute
path but takes the *second* branch. Measured (`t10_repr.py`):

```
blank repr: Pds3File("")
blank abspath: ''  logical: ''
```

`PdsFile.__init__` sets `self.abspath = ''` (`pdsfile.py:475`), and
`PdsFile.__repr__`'s own docstring (`pdsfile.py:913-917`) calls this trap out
explicitly: "The test is against None specifically, so a blank object, whose
absolute path is the empty string, takes the other branch and prints an empty
absolute path instead." The two subclass docstrings drop that and restate the
claim in the form the base corrects — and each sits ~70 lines below an `__init__`
docstring that is about exactly the blank object.

### D9 — `pds3file/__init__.py:172-174` and `pds4file/__init__.py:159-161`: not every constructor builds a blank object.

> "The constructors are the inherited class methods, and each of them builds a
> blank object this way and then fills it in"

`from_logical_path()` returns a cached object when the cache holds one
(`pdsfile.py:1729`, `return cls.CACHE[path_lc]`) — nothing is constructed.
Measured by wrapping `PdsFile.__init__` with a counter (`t12_init.py`), after a
PDS3 preload:

```
from_logical_path('volumes/COISS_2xxx/COISS_2002') cache-hit: __init__ calls = 0 -> COISS_xxxx
from_logical_path (uncached child):                 __init__ calls = 1
copy():                                             __init__ calls = 0
new_pdsfile():                                      __init__ calls = 1
```

`copy()` (`pdsfile.py:891-907`) and `new_pdsfile()` (`:557-…`) build their returned
object with `cls.__new__(cls)`, never through `__init__`. AST scan of `PdsFile`
(`t11_ctor.py`) shows only `from_abspath` (`:1770`), `from_path` (`:1984`) and
`new_merged_dir` (`:704`) contain `cls()`; `from_lid`, `from_relative_path` and
`from_logical_path` contain neither `cls()` nor `cls.__new__(cls)`.

### D10 — `tools/show_opus_products.py:99-100`: "the other three forms" is wrong, and `--narrow-table` is on the wrong side of it.

> "**The table form is keyed by OPUS type rather than by product category**, so two
> categories of the same type collapse and the later one is what prints. The other
> three forms key on the whole category tuple and show both."

There are three forms, not four (the sentence two lines above says so:
"--narrow-table only changes the shape of the table form"), so "the other three"
cannot be right; and `--narrow-table` given alone is *not* one of the forms that
keys on the category tuple. Line 133 turns `display_table` on when none of
`--table`, `--pprint`, `--raw` is set, and line 204 then takes the
`res[opus_type]` branch. Measured:

```
$ python -m pdsfile.tools.show_opus_products --narrow-table --paths \
      volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1.IMG
| opus_type and its corresponding opus_products |
| coiss_raw                                     |
…
$ python -m pdsfile.tools.show_opus_products --narrow-table --pprint --paths <same>
{('Cassini ISS', 0, 'coiss_raw', 'Raw Image', True): [...
```

Only `--pprint` and `--raw` key on the whole tuple.

### D11 — `tools/show_opus_products.py:111-114`: the `Raises:` section is incomplete on both counts a caller meets first.

> "Raises:
>     KeyError: from the item read ``__getitem__()`` on the environment, if either
>     PDS3_HOLDINGS_DIR or PDS4_HOLDINGS_DIR is unset."

The `KeyError` entry is accurate (lines 139-140, after `parse_args` at 121). Two
other exceptions escape `main()`:

- **`IndexError`**, from the subscript at line 179,
  `[prod_category[2] for prod_category, _ in opus_prod.items()]`, whenever
  `opus_products()` returns a key that is not a 5-tuple. This is not hypothetical:

  ```
  $ python -m pdsfile.tools.show_opus_products --paths \
        volumes/VG_20xx/VG_2001/JUPITER/CALIB/VG1PREJT.LBL
    File ".../show_opus_products.py", line 179, in main
      golden_opus_types = [prod_category[2] for prod_category, _ in opus_prod.items()]
  IndexError: string index out of range
  ```

  A scan of 6674 files across every volume of the test holdings (`t8c.py`) found
  four such paths (`VG_20xx/VG_2001/JUPITER/CALIB/VG1PREJT.LBL`, three under
  `VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/`). The offending key is
  the empty string, mapping to the `documents/VG_20xx/` products. This also
  falsifies "Returns: int: 0, always" for those paths — nothing is returned at all.

- **`SystemExit`**, from `parser.parse_args()` at line 121. The docstring alludes
  to it ("an invalid command line is reported first") without listing it, and the
  repo's own test asserts it:
  `tests/holdings_maintenance/test_show_opus_products.py:229-231`,
  `with pytest.raises(SystemExit) …: show_opus_products.main([...])`, exit code 2.
  Prose in a paragraph does not discharge the `Raises:` contract.

### D12 — `pds3file/__init__.py:14-15`: "an uppercase mission code" is not what the pattern or the tree carries.

> "A PDS3 volume set is an uppercase mission code and a digit-and-x suffix,
> ``COISS_1xxx``"

`BUNDLESET_REGEX` is `^([A-Z][A-Z0-9x]{1,5}_[0-9x]{3}x)$` (line 96) — the character
class admits a lowercase `x` inside the code. Real volume sets in
`/seti/opus/pdsdata/holdings/volumes` use it: `HSTIx_xxxx`, `HSTJx_xxxx`,
`HSTNx_xxxx`, `HSTOx_xxxx`, `HSTUx_xxxx`, `NHxxLO_xxxx`, `NHxxMV_xxxx`
(`t10_repr.py` listing). The volume claim in the same sentence is right:
`BUNDLENAME_REGEX` is `[A-Z][A-Z0-9]{1,5}_[0-9]{4}` with no lowercase admitted.

### D13 — `pds4file/__init__.py:17-19`: `PRODUCT_LBL_BASENAME_WO_EXT` is not an extra beyond the base's tables.

> "Every rule table the base class leaves as None is filled in from
> ``pds4file.rules``, plus three the PDS3 side has no use for:
> ``PRODUCT_LBL_BASENAME_WO_EXT``, ``ARCHIVE_PATHS`` and ``ARCHIVE_DIRS``."

`PRODUCT_LBL_BASENAME_WO_EXT` **is** one of the base's `None` tables
(`pdsfile.py:376`), so it is counted twice: once inside "every rule table the base
class leaves as None", once as one of the "three". Only `ARCHIVE_PATHS` and
`ARCHIVE_DIRS` are genuinely absent from `PdsFile` (measured in `t6_rules.py`:
`ARCHIVE_PATHS: PdsFile has? False`, `ARCHIVE_DIRS: PdsFile has? False`). The
"three the PDS3 side has no use for" part is otherwise sound — the AST diff of the
two class bodies gives exactly `{ARCHIVE_DIRS, ARCHIVE_PATHS,
PRODUCT_LBL_BASENAME_WO_EXT}` as pds4-only, and `grep` finds no reference to any of
them under `pds3file/`.

### D14 — `pds4file/__init__.py:290-316`: `archive_dirs()` has no `Raises:` and can raise.

The body calls `self.glob_glob(pattern, force_case_sensitive=True)` (line 328).
`glob_glob`'s own contract (`_local_fs.py:507-510`) is
`Raises: OSError — raised by _get_shelf() when a shelf file the search has already
located cannot be opened or unpickled. That call sits outside any handler`, plus an
`AssertionError` path documented at `:496-498`. `archive_dirs()` carries no
`Raises:` section at all, and it is a public method that runs under `SHELVES_ONLY`
(measured: `archive_dirs()` on `bundles/uranus_occs_earthbased` under
`use_shelves_only(True)` returns one archive with one directory, so the
shelf-backed branch is live).

---

## 2. Claims I could not verify either way

1. **Whether the `except AttributeError` handler is dead in *every* invocation
   shape (D6).** I traced three import orders and built a minimal reproduction of
   the circular-import pattern; none produced an `AttributeError`, and the
   Python 3.7 `import a.b as c` fallback explains why. I did not run the whole
   `tests/rules/` suite under a tracer, and I cannot rule out some
   pytest/`--import-mode` combination that reaches it. The claim is unsupported by
   anything I could measure; it may still be historically true of Python ≤3.6.

2. **`show_opus_products.py:98-99`, "two categories of the same type collapse and
   the later one is what prints."** The mechanism is right by construction —
   line 205 is `res[opus_type] = pdsf_list` inside a loop over `opus_prod.items()`,
   so a repeat key overwrites and the later assignment wins. But I could not find a
   single real path where it happens: `t8c.py` scanned 6674 files spanning every
   volume in the test holdings and found **zero** with a duplicated
   `prod_category[2]`. Whether the collapse is reachable at all on real data is
   open.

3. **`is_volset_dir` / `is_volset_file` (`pds3file/__init__.py:296,306`) have no
   `Raises:`.** Both forward to `is_bundleset_dir`/`is_bundleset_file`, which read
   `isdir`, which is documented (`_properties.py:232-236`) to raise `KeyError`
   under `SHELVES_ONLY` "for a path the shelf covers and holds no entry for". I
   could not construct such a path at bundle-set level in the test holdings —
   under `use_shelves_only(True)` all four probes (`volumes/COISS_2xxx`,
   `…/COISS_2002`, two absent interiors) answered without raising, because
   bundle-set-level paths are not shelf-covered. So the gap is real in the base's
   documented contract but I could not demonstrate the raise. The same applies to
   the alias's dropped hint: the base's `is_bundleset_dir` docstring at least says
   "Reading it can consult the filesystem or the shelves"; the PDS3 alias says
   nothing.

4. **`volset_pdsfile()` / `volume_pdsfile()` (`:411`, `:448`) have no `Raises:`.**
   `bundle_pdsfile`/`bundleset_pdsfile` (`pdsfile.py:948-1020`) call
   `cls.os_path_exists()` and `cls.from_abspath()`, both of which can raise
   (`ValueError` for an unparseable path, `OSError`/`KeyError` from the shelves).
   The base methods carry no `Raises:` either, so the aliases are faithful to what
   they mirror; I did not force either to raise, so I cannot say whether this is a
   real caller hazard or unreachable in practice.

5. **`show_opus_products.py:19-22`, "rather than importing ``main()`` and calling
   it".** `tests/holdings_maintenance/test_show_opus_products.py:230,236` **does**
   import the module and call `main()` — twice — but only for invocations that
   argparse rejects before either holdings root is read. Whether the sentence is
   meant to cover only the holdings-driving runs is a wording question, so I have
   not counted it as disproved. The rest of the sentence is right:
   `support.run_tool` (`support.py:319`) is
   `[sys.executable, '-m', TOOL_MODULES[tool]] + args`, and `HOLDINGS_FREE_TOOLS`
   (`support.py:62`) is `{'crlf', 'shelf_consistency_check'}` — the tools that are
   driven in process.

6. **`show_opus_products.py:17-19`, "Those caches are keyed by logical path, so a
   session that has preloaded one tree resolves a logical path to that tree
   whatever root a later caller has in mind."** Consistent with
   `from_logical_path` (`pdsfile.py:1729`) trying `cls.CACHE[path_lc]` first,
   and with the same reasoning written into `support.py:56-61`. I did not exercise
   it with two different roots in one interpreter.

7. **`pds3file/__init__.py:17-18`, "three of the five admit a version suffix, a
   category suffix, an archive extension or a checksum basename as well."** Under
   a disjunctive reading ("each of the three admits at least one of these") the
   count is right: `BUNDLESET_PLUS_REGEX`, `BUNDLENAME_PLUS_REGEX` and
   `BUNDLENAME_VERSION`. Under a conjunctive reading it is false for two of the
   three (D7, and `BUNDLENAME_VERSION` which admits only version suffixes). I read
   it as disjunctive and did not count it, but note that the class docstring's
   more specific restatement of the same fact *is* false (D7).

8. **`pds4file/__init__.py:304-305`, "The glob is case-sensitive."** True as far as
   I can tell — `force_case_sensitive=True` is passed, and `glob_glob`'s docstring
   says the shelf-backed search is case-sensitive regardless. I did not construct a
   case-colliding pair on this filesystem to prove it.

9. **`pds4file/__init__.py:303-305`, "a pattern matching nothing on disk contributes
   nothing."** Verified for the non-shelf path. Under `SHELVES_ONLY` the filter is
   the info shelf rather than the disk, so "on disk" is loose; I did not find a
   case where the two disagree.

10. **`pds3file/__init__.py:64-66` / `pds4file/__init__.py:58-59`, "The four setters
    below are overridden for the same reason: the base class writes each attribute
    onto every direct subclass, and these write it onto the class the call names."**
    True of three of the four. `PdsFile.set_easylogger` (`pdsfile.py:688-698`)
    writes no attribute — it calls `child_class.set_easylogger()` — and the
    override writes none either, it calls `cls.set_logger(...)`. The
    `set_easylogger` docstring itself (`:531-534`) describes this correctly, so the
    class-docstring summary is a loose generalisation rather than a plain error. I
    have not counted it.

---

## 3. Verified correct (measured, no defect)

Recorded because the brief asks these four specifically and a "no finding" is a
result.

- **The four setter overrides.** `t2_setters.py` / `t3_easy.py`, with `*` marking
  an attribute owned by the class rather than inherited:
  - `PdsFile.use_shelves_only(True)` → `Pds3File=True*`, `Pds4File=True*`,
    `PdsFile=False*`, `COISS_xxxx=True` (inherited), `cassini_iss=True`
    (inherited). Exactly "every direct subclass, not the class itself, and
    subclasses further down inherit".
  - `Pds3File.use_shelves_only(True)` → `Pds3File=True*` only; `COISS_xxxx` and
    `VGISS_xxxx` inherit `True`; `Pds4File` untouched. Then
    `COISS_xxxx.use_shelves_only(False)` → `COISS_xxxx=False*`,
    `VGISS_xxxx` still `True`. "A call on ``Pds3File`` reaches every volume set and
    a call on one rule subclass reaches that one" — confirmed.
  - Same shape for `require_shelves` on `Pds4File`/`cassini_iss`, and for
    `set_logger`.
  - `PdsFile.set_easylogger()` → `Pds3File=EasyLogger*`, `Pds4File=EasyLogger*`,
    `PdsFile=NullLogger*`, rule subclasses inherit; `'set_easylogger' in
    Pds3File.__dict__` is `True`, `COISS_xxxx.set_easylogger` resolves to
    `Pds3File.set_easylogger`. The recursion does end at the two subclasses.
  - "A cache is unaffected": at import `Pds3File.CACHE.logger is Pds3File.LOGGER`
    is `True`; after `Pds3File.set_logger(L)` the cache still holds the original
    `NullLogger`. `Pds3File.CACHE.lifetime_func is cache_lifetime_for_class` is
    `True`.
- **Per-class `CACHE` / `LOCAL_PRELOADED` / `SUBCLASSES`.** `t13_preload.py`:
  before, all three caches hold 25 entries; after `Pds3File.preload(PDS3)`,
  `Pds3File=10300`, `Pds4File=25`, `LP3=['/seti/opus/pdsdata/holdings']`, `LP4=[]`.
  Cache object identity unchanged on both classes. `SUBCLASSES` 26 vs 7, distinct
  objects.
- **The twelve—nineteen aliases against their base members.** Each `Returns:`
  matches the base definition, including the two that differ on nothing-there:
  `volset_abspath` → `bundleset_abspath` returns `None` when `not self.bundleset`
  (`pdsfile.py:1187-1188`); `volume_abspath` → `bundle_abspath` returns `''` when
  `not self.bundlename` and again for a three-part `checksums-archives-…` category
  (`pdsfile.py:1134-1144`). `voltype_`'s "what is left of ``category_`` once
  checksums- and archives- are taken off" matches `pdsfile.py:2259`
  (`category_ = checksums_ + archives_ + bundletype_`). `log_path_for_volset`
  forwards positionally and `log_path_for_volume` by keyword, as stated.
  `volume_publication_date` and `volume_version_id` match `_properties.py:2144`
  and `:2199`.
- **`Pds4File.archive_paths()` / `archive_dirs()`.** `t9_arch.py`, `t15.py`:
  class-level `ARCHIVE_PATHS`/`ARCHIVE_DIRS` are the empty translators from
  `pds4file/rules/__init__.py:734,741` and return `[]` for everything; the tables
  in use come from the rule subclass. `ARCHIVE_PATHS.all()` is fed
  `self.logical_path` and `ARCHIVE_DIRS.all()` the absolute archive path — both
  tables' patterns are `.*`-anchored so they tolerate either
  (`cassini_iss.py:414-466` and `:475-488`), and both return logical paths.
  Nothing is checked for existence in `archive_paths()`: on a tree with **no**
  `archives-bundles/` directory at all, `bundles/uranus_occs_earthbased` still
  yields
  `/seti/opus/pdsdata/pds4-holdings/archives-bundles/uranus_occs_earthbased/uranus_occs_earthbased.tar.gz`.
  `archive_dirs()` is filtered: the same archive maps to the one directory that
  does exist.
- **Regex and alias counts.** pds3: 5 patterns × 2 twins, 10 `VOL*` aliases. pds4:
  5 patterns, exactly 3 twins (`BUNDLESET_PLUS_REGEX_I`, `BUNDLENAME_PLUS_REGEX_I`,
  `BUNDLENAME_VERSION_I`); `BUNDLESET_REGEX` enumerates **6** bundle sets;
  its "plus" form takes `_vN.N` and `_vN.N.N` and rejects `_v1`, `.tar.gz` and
  `_md5.txt`. `BUNDLENAME_VERSION` (pds3) requires a suffix: `COISS_1001` is
  `False`, all seven suffixed forms `True`.
- **`Pds4File`'s method inventory.** AST: 8 functions, six overrides plus
  `archive_paths`/`archive_dirs` at the end of the class body — "the two methods
  this class adds beyond the overrides" is right.
- **`tools/__init__.py`.** `ls src/pdsfile/tools/` is `__init__.py`,
  `show_opus_products.py` — "the only one" is right, and the module defines
  nothing.
- **`show_opus_products` resolution order, filtering and form selection.** The
  four-way try (`Pds3File` abspath → logical, then `Pds4File`), the
  resolve-then-print two-loop shape, the `--opus-types` warn-and-drop and
  skip-entirely behaviour, and "the first true flag in the order table, pprint,
  raw" all match the code and the runs above.

---

## 4. Defects in the code itself (not the prose) — recorded, not fixed

**C1. `show_opus_products.py:179` raises `IndexError` on real holdings paths.**
`golden_opus_types = [prod_category[2] for prod_category, _ in opus_prod.items()]`
assumes every key of `opus_products()` is a 5-tuple. Four paths in
`/seti/opus/pdsdata/holdings` return a dict keyed by the empty string:

```
'' -> [['documents/VG_20xx/Hanel-etal-1977-SSR.pdf',
        'documents/VG_20xx/Hanel-etal-1977-SSR_OCR.pdf',
        'documents/VG_20xx/PICTURE_BODY.txt',
        'documents/VG_20xx/read_iris.py']]
```

for `volumes/VG_20xx/VG_2001/JUPITER/CALIB/VG1PREJT.LBL` and three files under
`volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/`. The tool dies with
a traceback rather than printing anything. Lines 200 and 235-239 make the same
assumption.

**C2. `show_opus_products.py:163-164`: `--debug` prints nothing useful.**
`traceback.print_exc()` sits outside any `except` block — the two handlers at
lines 155 and 158 have already exited by the time control reaches
`if pdsf_inst is None:`. Measured:

```
$ python -m pdsfile.tools.show_opus_products --debug --paths /no/such/root/x.IMG
NoneType: None
WARNING: Can't instantiate a Pds3File or Pds4File instance with the given path: /no/such/root/x.IMG
```

The `--debug` help text ("Print traceback when there is an exception during pdsfile
instantiation", line 73) is not delivered.

**C3 (adjacent, outside this slice, recorded for completeness).**
`opus_products()` returning a dictionary whose key is `''` rather than a product
category tuple is what C1 trips over. The empty key carries the `documents/`
products of the volume set. Whichever rule produces it is in
`src/pdsfile/_opus.py` / the `VG_20xx` and `VGIRIS_xxxx` rule modules, not in this
PR's slice.
