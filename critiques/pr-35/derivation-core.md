# Notes: frag-core (class PdsFile core members + instance attrs + module level)

All paths relative to /seti/all_repos/rms-pdsfile/src/pdsfile/ unless absolute.
`P` = pdsfile.py. Rule-table populations verified in pds3file/rules/__init__.py
(`R3`) and pds4file/rules/__init__.py (`R4`); subclass bindings in
pds3file/__init__.py:178-199 and pds4file/__init__.py:149-178.

## Class data members (60)

ASSOCIATIONS | dict[str, _Translator] | None | P:358 None on PdsFile; R3:384/R4:382 a dict keyed by voltype str with translator values; rules copy and extend it (pds3file/rules/COISS_xxxx.py:813)
BUNDLE_DIR_NAME | str | P:316 `'bundles'`
CACHE | Any | P:334 DictionaryCache; _preload.py:573,583 preload can rebind to MemcachedCache; both from pdsfile.pdscache, which this fragment may not import, so Any (true type: `pdscache.DictionaryCache | pdscache.MemcachedCache`)
CATEGORIES | set[str] | P:345 `set(CATEGORY_LIST)`
CATEGORY_LIST | list[str] | P:344 from construct_category_list(), _path_utils.py:100-110 builds list of str
CATEGORY_REGEX | re.Pattern[str] | P:244 re.compile of str pattern
CATEGORY_REGEX_I | re.Pattern[str] | P:245 re.compile of str pattern
DATAFILE_EXTS | set[str] | P:242 set of str literals
DATA_SET_ID | _Translator | None | P:368 None; R3:723/R4:719 NullTranslator
DEFAULT_CACHING | str | P:338 `'dir'`; _preload.py:612,614 rebinds to 'dir'/'all'
DEFAULT_HIGH_LEVEL_ICONS | dict[tuple[str, bool], str] | P:280-305 literal, keys (voltype str, is_bundleset bool), values icon-type str
DESCRIPTION_AND_ICON | _Translator | None | P:357 None; R3:136/R4:138 TranslatorByRegex; rules add translators (COISS_xxxx.py:799)
DICTIONARY_CACHE_LIMIT | int | P:331 `200000`
EXTRA_README_BASENAMES | tuple[str, ...] | P:348 tuple of str literals
FILENAME_KEYLEN | int | P:382 `0`; five rule classes override with ints, and three (COISS_xxxx, RPX_xxxx, COVIMS_0xxx) override with a method — the method overrides are stubbed as such in the rule stubs with type: ignore[override]
FILESPEC_TO_BUNDLESET | _Translator | None | P:380 None; R3:704/R4:700 TranslatorByRegex
FS_IS_CASE_INSENSITIVE | bool | P:321 True; _preload.py:796-800 rebinds bool
INFO_FILE_BASENAMES | _Translator | None | P:360 None; R3:510/R4:508 TranslatorByRegex
LATEST_VERSION_RANKS | list[int] | P:942 list of int literals
LID_AFTER_DSID | _Translator | None | P:367 None; R3:714/R4:710 TranslatorByRegex
LOCAL_HOLDINGS_DIRS | list[str] | None | P:385 None; _path_utils.py:397,406 rebound to list[str] (env var value / realpath results)
LOCAL_PRELOADED | list[str] | P:327 `[]`; _preload.py:636 `CACHE.get_now('$PRELOADED') or []`, :751 appends holdings abspath strings
LOGFILE_TIME_FMT | str | P:250 str literal
LOGGER | _PdsLogger | P:324 pdslogger.NullLogger(); set_logger P:679-684 installs caller's logger; pdslogger untyped -> alias
LOG_ROOT_ | str | None | P:2428 None; _derived_paths.py:378-381 set_log_root writes None or `root.rstrip('/') + '/'`
MEMCACHE_PORT | int | P:330 `0`; _preload.py:579,602 rebinds int
MIME_TYPES_VS_EXT | dict[str, str] | P:260-277 literal str->str
NEIGHBORS | _Translator | None | P:361 None; R3:484/R4:482 TranslatorByRegex
OPUS_FORMAT | _Translator | None | P:371 None; R3:635/R4:631 TranslatorByRegex
OPUS_ID | _Translator | None | P:373 None; R3:677/R4:673 TranslatorByRegex
OPUS_ID_TO_PRIMARY_LOGICAL_PATH | _Translator | None | P:374 None; R3:694/R4:690 TranslatorByRegex
OPUS_ID_TO_SUBCLASS | _Translator | None | P:378 None; R3:685/R4:681 TranslatorByRegex
OPUS_PRODUCTS | _Translator | None | P:372 None; R3:664/R4:660 TranslatorByRegex
OPUS_TYPE | _Translator | None | P:370 None; R3:597/R4:595 TranslatorByRegex
PDS_HOLDINGS | str | P:315 `'holdings'`
PLAIN_TEXT_EXTS | set[str] | P:256-258 set of str literals
PRELOAD_TRIES | int | P:341 `3`
PRODUCT_LBL_BASENAME_WO_EXT | _Translator | None | P:376 None; R4:728 TranslatorByRegex (pds4file/__init__.py:178)
SHELF_ACCESS | dict[str, int] | P:2415 `{}`; _shelves.py:329,359 `SHELF_ACCESS[shelf_path] = SHELF_ACCESS_COUNT` (str key, int value)
SHELF_ACCESS_COUNT | int | P:2418 `0`; _shelves.py:328,358 `+= 1`
SHELF_CACHE | dict[str, Any] | P:2414 `{}`; _shelves.py:360 value is the unpickled shelf object (pickle.load -> Any, used as a dict but unprovable)
SHELF_CACHE_SIZE | int | P:2416 `120`
SHELF_CACHE_SLOP | int | P:2417 `20`
SHELF_NULL_KEY_VALUES | dict[str, Any] | P:2420 `{}`; _shelves.py:356,480 values are `shelf['']` / shelf values -> Any
SHELF_PATH_INFO | dict[str, tuple[str, str]] | P:309-313 literal str -> (prefix, suffix) str pairs
SHELVES_ONLY | bool | P:319 False; use_shelves_only P:640 writes bool
SHELVES_REQUIRED | bool | P:320 False; require_shelves P:660 writes bool
SIBLINGS | _Translator | None | P:362 None; R3:496/R4:494 TranslatorByRegex
SORT_KEY | _Translator | None | P:363 None; R3:526/R4:524 TranslatorByRegex
SORT_ORDER | dict[str, bool | int] | P:395-402 literal: True/False/False/20; sort_* setters P:415-459 store bool and bool-or-int values; also shadowed per instance by those setters with the same type
SPLIT_RULES | _Translator | None | P:364 None; R3:570/R4:568 TranslatorByRegex
SUBCLASSES | dict[str, type[PdsFile]] | P:351 `{}`; P:2459 `SUBCLASSES['default'] = PdsFile`; rule modules register class objects (pds3file/rules/COISS_xxxx.py:846)
VERSIONS | _Translator | None | P:359 None; R3:437/R4:435 TranslatorByRegex
VIEWABLES | dict[str, _Translator] | None | P:366 None; R3:461/R4:459 `{'default': NullTranslator()}`; rules use str-keyed dicts (COISS_xxxx.py:811)
VIEWABLE_ANCHOR_REGEX | re.Pattern[str] | P:247 re.compile of str pattern
VIEWABLE_EXTS | set[str] | P:241 set of str literals
VIEWABLE_VOLTYPES | list[str] | P:239 list of str literals
VIEW_OPTIONS | _Translator | None | P:365 None; R3:474/R4:472 TranslatorByRegex
VOLSET_TRANSLATOR | _Translator | P:354 translator.TranslatorByRegex(...) (rms-translator untyped)
VOLTYPES | list[str] | P:237-238 list of str literals

## Methods, classmethods, properties (31)

bundle_abspath | (self, category: str | None = None) -> str | P:1134-1166 returns '' (no bundlename, or 3-part category) or a concatenated str; TypeError (not a return) on None root_
bundle_pdsfile | (self, category=None, rank=None) -> PdsFile | None | P:975,981 return None; P:973 from_abspath result; P:979 `all_versions()[rank]` (dict of PdsFile, _properties.py:2618); result may be a different subclass than type(self) via child()/cache, so PdsFile not Self
bundleset_abspath | (self, category: str | None = None) -> str | None | P:1188 `return None` when no bundleset; P:1210 str otherwise (asymmetric with bundle_abspath's '')
bundleset_pdsfile | (self, category=None, rank=None) -> PdsFile | None | P:1011-1020 same shape as bundle_pdsfile
child | (self, basename: str, fix_case=True, must_exist=False, caching='default', lifetime: float | None = None, allow_index_row=True) -> PdsFile | P:1444 child_of_index (_index_rows.py returns a PdsFile pseudo-child); P:1503+ `this._complete(...)`; _complete can return a cached object and new_pdsfile switches subclass via SUBCLASSES (P:583-587), so PdsFile not Self
copy | (self) -> Self | P:902-903 `cls = type(self); cls.__new__(cls)` -> provably Self
from_abspath | classmethod (abspath: str, fix_case=False, must_exist=False, caching='default', lifetime: float | None = None) -> PdsFile | P:1819 cached object; P:1902 `this` built by child() chain; subclass switching + shared-cache contents make Self unprovable -> PdsFile
from_lid | classmethod (lid_str: str) -> PdsFile | P:1678 from_path result; P:1684 returns it
from_logical_path | classmethod (path: str, fix_case=False, must_exist=False, caching='default', lifetime: float | None = None) -> PdsFile | None | P:1724 `return None` on empty path (documented); P:1729 cached object; P:1759 child() chain; P:1767 from_abspath fallback
from_path | classmethod (path: Any, must_exist=False, caching='default', lifetime: float | None = None) -> PdsFile | P:2065 `path = str(path)` so any object accepted -> Any; returns _complete/child results and CACHE values (P:2397,2401,2408) -> PdsFile
from_relative_path | (self, path: str, fix_case=False, must_exist=False, caching='default', lifetime: float | None = None) -> PdsFile | P:1930 _complete; P:1939 child() chain -> PdsFile
is_bundle | property -> bool | P:1059 bool(...)
is_bundle_dir | property -> bool | P:1036 bool(...)
is_bundle_file | property -> bool | P:1050 bool(...)
is_bundleset | property -> bool | P:1099 bool(...)
is_bundleset_dir | property -> bool | P:1073 bool(...)
is_bundleset_file | property -> bool | P:1088 bool(...)
is_category_dir | property -> bool | P:1110 `==` comparison
is_logical_path | classmethod (path: str) -> bool | P:2454 `not in` test
new_index_row_pdsfile | (self, filename_key: str, row_dicts: list[dict[Any, Any]]) -> Self | P:830 `this = self.copy()` (copy is provably Self), returned P:889; row_dicts values come from untyped pdstable dicts_by_row (_index_rows.py:343-352), the same flow that made column_names list[Any]. CORRECTED after review round 2: the docstring's "column name to value" claimed dict[str, Any], which is not derivable from the untyped source
new_merged_dir | classmethod (basename: str) -> Self | P:736 `this = cls()`, returned P:806 -> Self
new_pdsfile | (self, key: str | None = None, copypath: bool = False) -> PdsFile | P:583-589 cls may be any entry of SUBCLASSES (a different subclass), so PdsFile not Self
parent | (self, must_exist=False, caching='default', lifetime: float | None = None) -> PdsFile | None | P:1632 `return None` for merged dir (documented); P:1639,1643 from_logical_path/from_abspath results; from_logical_path's None branch unreachable here (split path nonempty check is on `path`, but declared return stays PdsFile | None from the merged branch alone)
require_shelves | classmethod (status: bool = True) -> None | P:643-660 no return
set_easylogger | classmethod () -> None | P:688-698 no return
set_logger | classmethod (logger: _PdsLogger | None = None) -> None | P:664-684 falsy -> NullLogger; pdslogger untyped
sort_dirs_first | (self, dirs_first: bool) -> None | P:418-430 no return
sort_dirs_last | (self, dirs_last: bool) -> None | P:432-444 no return
sort_info_first | (self, info_first: bool | int) -> None | P:446-459 docstring: True/False/1/0 or integer threshold
sort_labels_after | (self, labels_after: bool) -> None | P:404-416 no return
use_shelves_only | classmethod (status: bool = True) -> None | P:622-640 no return

## Instance attributes (25)

basename | str | P:474 ''; P:738,832,1499,1889,2220 str values everywhere
abspath | str | None | P:475 ''; P:739 None (new_merged_dir); P:1498 child_abspath "might be None" (P:1478); str elsewhere (P:835,1888)
logical_path | str | P:476 ''; P:740 basename; P:836,1497,1887 str
disk_ | str | None | P:478 ''; P:742 None (new_merged_dir); P:1854 str (from_abspath)
root_ | str | None | P:479 ''; P:743 None; P:1855 str
html_root_ | str | None | P:480 ''; P:744 None; P:1872-1885 str
category_ | str | P:482 ''; P:746,1577,2259 str
checksums_ | str | P:483 ''; P:747,1584,2116,2151 str
archives_ | str | P:484 ''; P:748,1585,2111,2146 str
bundletype_ | str | P:485 ''; P:749,1586-1590,2121,2257 str
bundleset_ | str | P:487 ''; P:751,1541,1546 str
bundleset | str | P:488 ''; P:752,1542,2180,2299 str
suffix | str | P:489 ''; P:753,1543,1550,2129,2203,2249 str
version_message | str | P:490 ''; P:754; P:1552-1554 from version_info (_properties.py:2577-2616, str in every branch)
version_rank | int | P:491 0; P:755; P:1552 from version_info (int in every branch)
version_id | str | P:492 ''; P:756; P:1554 from version_info (str in every branch)
bundlename_ | str | P:494 ''; P:758,1513,1520,1524,1528 str
bundlename | str | P:495 ''; P:759,1521,2216,2248 str
interior | str | P:497 ''; P:761,837,1502,1506,1514,1525,1529,1547 str
is_index_row | bool | P:499 False; P:763,882 bool
row_dicts | list[dict[Any, Any]] | P:501 []; P:764,883 the new_index_row_pdsfile parameter; runtime values from untyped pdstable (_index_rows.py:343-352). CORRECTED after review round 2, same reasoning as the parameter row above
column_names | list[Any] | P:503 []; P:765,884 copied; only non-empty fill is `[c.name for c in table.info.column_info_list]` (_index_rows.py:347-348) where pdstable is untyped -> element Any, though the docstring means str
permanent | bool | P:506 False; P:767 True; P:1349 True; _preload.py:707 True
is_merged | bool | P:508 False; P:768 True
parent_basename | str | P:887 `this.parent_basename = self.basename` (str); exists on index-row objects only (P:818,886)

(SORT_ORDER is also written per-instance by the four sort_* setters, P:415/429/443/458, with the same dict[str, bool | int] type; it is declared once in the class-member section above and not repeated, since a class body cannot bind the same name twice.)

## Module level: pdsfile.pdsfile (12)

FILE_BYTE_UNITS | list[str] | _path_utils.py:66 list of str literals (re-exported P:170)
HAS_PYLIBMC | bool | _preload.py:54-58 True/False from import try (re-exported P:177)
PATH_EXISTS_CACHE_SIZE | int | _local_fs.py:39 `200` (re-exported P:169)
abspath_for_logical_path | (path: str, cls: type[PdsFile]) -> str | _path_utils.py:344-423; returns _clean_join str (410,421) or matches[0] str (417); raises otherwise
cache_lifetime_for_class | (arg: Any, cls: type[PdsFile] | None = None) -> int | _preload.py:103-148; arg is anything about to be cached (str tested first); every return is one of the int constants
construct_category_list | (voltypes: Collection[str]) -> list[str] | _path_utils.py:71-110; builds list of str. CORRECTED after review round 2: the row originally declared Iterable[str] while noting that a one-shot iterator fails (the input is iterated four times), which is exactly the admitted-but-failing input; Collection[str] is the broadest contract whose every value succeeds at the iteration (the `documents` membership requirement stays a documented ValueError)
formatted_file_size | (size: float) -> str | _path_utils.py:313-342; f-string return; int accepted via numeric tower (docstring: "an int and a float are both accepted")
logical_path_from_abspath | (abspath: str, cls: type[PdsFile]) -> str | _path_utils.py:113-139; returns parts[2] str or raises ValueError
pause_caching | (cls: type[PdsFile]) -> None | _preload.py:166-177; no return
repair_case | (abspath: str, cls: type[PdsFile]) -> str | _path_utils.py:234-311; returns rejoined str
resume_caching | (cls: type[PdsFile]) -> None | _preload.py:179-189; no return
selected_path_from_path | (path: str, cls: type[PdsFile], abspaths: bool = True) -> str | _path_utils.py:425-458; returns path or a conversion, all str

## Preload names (6)

is_preloading | (cls: type[PdsFile]) -> Any | _preload.py:150-164 `return cls.CACHE.get_now('$PRELOADING')`; whatever an external writer stored, or None; cache classes give no provable type -> Any
DEFAULT_FILE_CACHE_LIFETIME | int | _preload.py:97 `12 * 60 * 60`
LONG_FILE_CACHE_LIFETIME | int | _preload.py:98 `7 * 24 * 60 * 60`
SHORT_FILE_CACHE_LIFETIME | int | _preload.py:99 `2 * 24 * 60 * 60`
FOEVER_FILE_CACHE_LIFETIME | int | _preload.py:100 `0` (name misspelled in source; stubbed as spelled)
DICTIONARY_CACHE_LIMIT | int | _preload.py:101 `200000` (distinct from the class attribute of the same name, P:331, also int)

## Discrepancies

- pdsfile.py:466-497 (`__init__` comments) present abspath, disk_, root_ and html_root_ as strings, but new_merged_dir (P:739-744) sets all four path roots to None and child() (P:1478,1498) can leave abspath None; declared `str | None` for those four. logical_path never gets None. The class docstring (P:204-208) acknowledges the three Nones, so the code and the class docstring agree; the attribute comments do not.
- pdsfile.py:826-828: new_index_row_pdsfile docstring says "Returns: PdsFile"; the code returns `self.copy()` (P:830), which is provably `type(self)` -> declared Self (narrower and provable).
- pdsfile.py:726-728 and 898-899: new_merged_dir and copy docstrings likewise say "PdsFile"; both are provably Self (`cls()` at P:736; `type(self).__new__` at P:902-903) -> declared Self.
- pdsfile.py:503-504: column_names comment says "Ordered list of column names" (i.e. str), but the only non-empty assignment (_index_rows.py:347-348) draws from untyped pdstable -> declared list[Any] per the untyped-dependency rule; docstring intent is list[str].
- pdsfile.py:1184: bundleset_abspath returns None for "no bundleset" while bundle_abspath (P:1129-1131) returns '' for "no bundle" -- both documented, but the asymmetry is easy to misread; declared `str | None` vs `str` respectively.
- pdsfile.py:963-966: bundle_pdsfile/bundleset_pdsfile docstrings say the return is the bundle-level object of this file, implying this class; the object comes from from_abspath/all_versions and can be another registered subclass -> declared PdsFile | None, not Self.
- _preload.py:100: constant is spelled FOEVER_FILE_CACHE_LIFETIME (sic) in the source; the stub must use the same spelling.
- child/parent/from_* `lifetime` parameters: declared `int | None`; every in-package call site passes an int or None (e.g. _preload.py:712 lifetime=0), and the docstrings say "in seconds"; a float would also pass through unharmed, so int | None is the narrowest defensible spelling -- flagged in case the assembler prefers `float | None`. CORRECTED after review round 2: the assembled stubs now say float | None, because the value flows unmodified into CACHE.set, which this stub set itself types lifetime: float | None, and the docstrings say only "in seconds"
- CACHE declared Any: the true type is `pdscache.DictionaryCache | pdscache.MemcachedCache` (P:334, _preload.py:573,583); use that union instead if the final stub imports pdsfile.pdscache.

## Imports needed

- `from typing import Any, Self` (assumed present)
- `from collections.abc import Iterable` (construct_category_list)
- `import re` (re.Pattern for CATEGORY_REGEX, CATEGORY_REGEX_I, VIEWABLE_ANCHOR_REGEX)
- aliases `_Translator`, `_PdsLogger` (assumed present); `_PdsTable` not needed by this fragment
