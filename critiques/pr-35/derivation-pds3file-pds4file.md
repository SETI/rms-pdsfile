# Notes: Pds3File / Pds4File own-body stub fragments

All file paths below are absolute; `pds3file/__init__.py` = `/seti/all_repos/rms-pdsfile/src/pdsfile/pds3file/__init__.py`, `pds4file/__init__.py` = `/seti/all_repos/rms-pdsfile/src/pdsfile/pds4file/__init__.py`, `pdsfile.py` = `/seti/all_repos/rms-pdsfile/src/pdsfile/pdsfile.py`.

## Pds3File (73 members)

ASSOCIATIONS | dict[str, _Translator] | pds3file/__init__.py:179 = rules.ASSOCIATIONS; pds3file/rules/__init__.py:384 is a dict of str keys ('volumes', 'previews', ...) to TranslatorByRegex/NullTranslator values
BUNDLENAME_PLUS_REGEX | re.Pattern[str] | pds3file/__init__.py:144 re.compile of a str pattern
BUNDLENAME_PLUS_REGEX_I | re.Pattern[str] | pds3file/__init__.py:146 re.compile
BUNDLENAME_REGEX | re.Pattern[str] | pds3file/__init__.py:142 re.compile
BUNDLENAME_REGEX_I | re.Pattern[str] | pds3file/__init__.py:143 re.compile
BUNDLENAME_VERSION | re.Pattern[str] | pds3file/__init__.py:147 re.compile
BUNDLENAME_VERSION_I | re.Pattern[str] | pds3file/__init__.py:152 re.compile
BUNDLESET_PLUS_REGEX | re.Pattern[str] | pds3file/__init__.py:133 re.compile
BUNDLESET_PLUS_REGEX_I | re.Pattern[str] | pds3file/__init__.py:140 re.compile
BUNDLESET_REGEX | re.Pattern[str] | pds3file/__init__.py:131 re.compile
BUNDLESET_REGEX_I | re.Pattern[str] | pds3file/__init__.py:132 re.compile
BUNDLE_DIR_NAME | str | pds3file/__init__.py:127 str literal 'volumes'
CACHE | DictionaryCache | pds3file/__init__.py:170 pdscache.DictionaryCache(...) (first-party class, pdsfile.pdscache)
CROSS_PDS3_PDS4_PRODUCTS | _Translator | pds3file/__init__.py:194 = rules.CROSS_PDS3_PDS4_PRODUCTS, a TranslatorByRegex (untyped rms-translator)
DATA_SET_ID | _Translator | pds3file/__init__.py:189 = rules.DATA_SET_ID; pds3file/rules/__init__.py:723 NullTranslator (untyped rms-translator)
DESCRIPTION_AND_ICON | _Translator | pds3file/__init__.py:178 TranslatorByRegex
DICTIONARY_CACHE_LIMIT | int | pds3file/__init__.py:169 int literal 200000
FILESPEC_TO_BUNDLESET | _Translator | pds3file/__init__.py:199 TranslatorByRegex
IDX_EXT | tuple[str, ...] | pds3file/__init__.py:201 ('.tab',)
INFO_FILE_BASENAMES | _Translator | pds3file/__init__.py:181 TranslatorByRegex
LBL_EXT | tuple[str, ...] | pds3file/__init__.py:202 ('.lbl',)
LID_AFTER_DSID | _Translator | pds3file/__init__.py:188 TranslatorByRegex
LOCAL_PRELOADED | list[str] | pds3file/__init__.py:174 = []; /seti/all_repos/rms-pdsfile/src/pdsfile/_preload.py:751 appends holdings abspath strings, :636 reloads the same list from the cache
LOGGER | _PdsLogger | pds3file/__init__.py:166 pdslogger.NullLogger() (untyped rms-pdslogger)
NEIGHBORS | _Translator | pds3file/__init__.py:182 TranslatorByRegex
OPUS_FORMAT | _Translator | pds3file/__init__.py:192 TranslatorByRegex
OPUS_ID | _Translator | pds3file/__init__.py:195 TranslatorByRegex
OPUS_ID_TO_PRIMARY_LOGICAL_PATH | _Translator | pds3file/__init__.py:196 TranslatorByRegex
OPUS_ID_TO_SUBCLASS | _Translator | pds3file/__init__.py:198 TranslatorByRegex
OPUS_PRODUCTS | _Translator | pds3file/__init__.py:193 TranslatorByRegex
OPUS_TYPE | _Translator | pds3file/__init__.py:191 TranslatorByRegex
PDS_HOLDINGS | str | pds3file/__init__.py:126 str literal 'holdings'
SIBLINGS | _Translator | pds3file/__init__.py:183 TranslatorByRegex
SORT_KEY | _Translator | pds3file/__init__.py:184 TranslatorByRegex
SPLIT_RULES | _Translator | pds3file/__init__.py:185 TranslatorByRegex
SUBCLASSES | dict[str, type[Pds3File]] | pds3file/__init__.py:175 = {}; :586 assigns Pds3File under 'default'; every rule module assigns its Pds3File subclass (e.g. pds3file/rules/ASTROM_xxxx.py:58)
VERSIONS | _Translator | pds3file/__init__.py:180 TranslatorByRegex
VIEWABLES | dict[str, _Translator] | pds3file/__init__.py:187 = rules.VIEWABLES; pds3file/rules/__init__.py:461 {'default': NullTranslator()}
VIEW_OPTIONS | _Translator | pds3file/__init__.py:186 TranslatorByRegex
VOLNAME_PLUS_REGEX | re.Pattern[str] | pds3file/__init__.py:160 alias of BUNDLENAME_PLUS_REGEX
VOLNAME_PLUS_REGEX_I | re.Pattern[str] | pds3file/__init__.py:161 alias
VOLNAME_REGEX | re.Pattern[str] | pds3file/__init__.py:158 alias
VOLNAME_REGEX_I | re.Pattern[str] | pds3file/__init__.py:159 alias
VOLNAME_VERSION | re.Pattern[str] | pds3file/__init__.py:162 alias
VOLNAME_VERSION_I | re.Pattern[str] | pds3file/__init__.py:163 alias
VOLSET_PLUS_REGEX | re.Pattern[str] | pds3file/__init__.py:156 alias of BUNDLESET_PLUS_REGEX
VOLSET_PLUS_REGEX_I | re.Pattern[str] | pds3file/__init__.py:157 alias
VOLSET_REGEX | re.Pattern[str] | pds3file/__init__.py:154 alias
VOLSET_REGEX_I | re.Pattern[str] | pds3file/__init__.py:155 alias
VOLSET_TRANSLATOR | _Translator | not in the class body; base default at pdsfile.py:354 and every pds3 rule module rebinds it on Pds3File to a TranslatorByRegex sum (e.g. pds3file/rules/ASTROM_xxxx.py:49-50), which is how it lands in the class's own dict
is_volset | bool | pds3file/__init__.py:330 returns is_bundleset; pdsfile.py:1099 `bool(...)`
is_volset_dir | bool | pds3file/__init__.py:341 returns is_bundleset_dir; pdsfile.py:1073 `bool(...)`
is_volset_file | bool | pds3file/__init__.py:351 returns is_bundleset_file; pdsfile.py:1088 `bool(...)`
is_volume | bool | pds3file/__init__.py:384 returns is_bundle; pdsfile.py:1059 `bool(...)`
is_volume_dir | bool | pds3file/__init__.py:395 returns is_bundle_dir; pdsfile.py:1036 `bool(...)`
is_volume_file | bool | pds3file/__init__.py:405 returns is_bundle_file; pdsfile.py:1050 `bool(...)`
log_path_for_volset | (self, suffix: str = '', task: str = '', dir: str = '', place: str = 'default') -> str | pds3file/__init__.py:257 forwards to log_path_for_bundleset; /seti/all_repos/rms-pdsfile/src/pdsfile/_derived_paths.py:558 -> _log_path_for, :502 returns ''.join(parts)
log_path_for_volume | (self, suffix: str = '', task: str = '', dir: str = '', place: str = 'default') -> str | pds3file/__init__.py:415 forwards to log_path_for_bundle; _derived_paths.py:530, :502 returns ''.join(parts)
require_shelves | classmethod (cls, status: bool = True) -> None | pds3file/__init__.py:241 assigns cls.SHELVES_REQUIRED, no return; base pdsfile.py:643 same signature
set_easylogger | classmethod (cls) -> None | pds3file/__init__.py:573 calls cls.set_logger, no return; base pdsfile.py:688 same signature
set_logger | classmethod (cls, logger: _PdsLogger | None = None) -> None | pds3file/__init__.py:552 accepts a pdslogger logger or falsy, assigns cls.LOGGER, no return; base pdsfile.py:664 same signature
use_shelves_only | classmethod (cls, status: bool = True) -> None | pds3file/__init__.py:221 assigns cls.SHELVES_ONLY, no return; base pdsfile.py:622 same signature
volname | str | pds3file/__init__.py:362 returns bundlename, an instance attribute always assigned str (pdsfile.py:495, 1521, 2216)
volname_ | str | pds3file/__init__.py:373 returns bundlename_ (pdsfile.py:494, 1520)
volset | str | pds3file/__init__.py:308 returns bundleset (pdsfile.py:488, 1542, 2180)
volset_ | str | pds3file/__init__.py:319 returns bundleset_ (pdsfile.py:487, 1541)
volset_abspath | (self, category: str | None = None) -> str | None | pds3file/__init__.py:439 forwards to bundleset_abspath; pdsfile.py:1188 returns None when no bundleset, :1210 returns str
volset_pdsfile | (self, category: str | None = None, rank: int | None = None) -> PdsFile | None | pds3file/__init__.py:456 forwards to bundleset_pdsfile; pdsfile.py:1010 from_abspath, :1012/:1018 return None, :1016 all_versions()[rank] whose values are only provably PdsFile (_properties.py:2642)
voltype_ | str | pds3file/__init__.py:512 returns bundletype_ (pdsfile.py:485, 749, 1586)
volume_abspath | (self, category: str | None = None) -> str | pds3file/__init__.py:474 forwards to bundle_abspath; pdsfile.py:1135/:1144 return '', :1165 returns str
volume_pdsfile | (self, category: str | None = None, rank: int | None = None) -> PdsFile | None | pds3file/__init__.py:493 forwards to bundle_pdsfile; pdsfile.py:975/:981 return None, :973 from_abspath, :979 all_versions()[rank]
volume_publication_date | Any | pds3file/__init__.py:525 returns bundle_publication_date verbatim, which _properties.py:2171-2193 returns as the raw CACHE-derived `_volume_info[3]` whenever that field is truthy (only the three fallbacks slice `[:10]`), so the type is the base property's Any. CORRECTED after review round 1: this row originally claimed every path returns a str, which is false against the code, and the stub said `str` on an alias whose base says Any
volume_version_id | Any | pds3file/__init__.py:537 returns bundle_version_id verbatim; _properties.py:2216-2220 fills the slot with '' or the raw CACHE-derived `_volume_info[2]`, which is not provably str. CORRECTED after review round 1, same defect as the row above

## Pds4File (47 members)

ARCHIVE_DIRS | _Translator | pds4file/__init__.py:181 = rules.ARCHIVE_DIRS, TranslatorByRegex
ARCHIVE_PATHS | _Translator | pds4file/__init__.py:180 = rules.ARCHIVE_PATHS; pds4file/rules/__init__.py:734 TranslatorByRegex([])
ASSOCIATIONS | dict[str, _Translator] | pds4file/__init__.py:150; pds4file/rules/__init__.py:382 dict of str to translators
BUNDLENAME_PLUS_REGEX | re.Pattern[str] | pds4file/__init__.py:131 re.compile
BUNDLENAME_PLUS_REGEX_I | re.Pattern[str] | pds4file/__init__.py:133 re.compile
BUNDLENAME_REGEX | re.Pattern[str] | pds4file/__init__.py:126 re.compile
BUNDLENAME_VERSION | re.Pattern[str] | pds4file/__init__.py:134 re.compile
BUNDLENAME_VERSION_I | re.Pattern[str] | pds4file/__init__.py:137 re.compile
BUNDLESET_PLUS_REGEX | re.Pattern[str] | pds4file/__init__.py:121 re.compile
BUNDLESET_PLUS_REGEX_I | re.Pattern[str] | pds4file/__init__.py:124 re.compile
BUNDLESET_REGEX | re.Pattern[str] | pds4file/__init__.py:115 re.compile
BUNDLE_DIR_NAME | str | pds4file/__init__.py:112 'bundles'
CACHE | DictionaryCache | pds4file/__init__.py:144 pdscache.DictionaryCache(...)
CROSS_PDS3_PDS4_PRODUCTS | _Translator | pds4file/__init__.py:165 TranslatorByRegex
DATA_SET_ID | _Translator | pds4file/__init__.py:160; pds4file/rules/__init__.py:719 NullTranslator
DESCRIPTION_AND_ICON | _Translator | pds4file/__init__.py:149 TranslatorByRegex
DICTIONARY_CACHE_LIMIT | int | pds4file/__init__.py:143 200000
FILESPEC_TO_BUNDLESET | _Translator | pds4file/__init__.py:170 TranslatorByRegex
IDX_EXT | tuple[str, ...] | pds4file/__init__.py:175 ('.csv', '.tab')
INFO_FILE_BASENAMES | _Translator | pds4file/__init__.py:152 TranslatorByRegex
LBL_EXT | tuple[str, ...] | pds4file/__init__.py:176 ('.xml', '.lblx')
LID_AFTER_DSID | _Translator | pds4file/__init__.py:159 TranslatorByRegex
LOCAL_PRELOADED | list[str] | pds4file/__init__.py:172 = []; filled by _preload.py:751 with holdings abspath strings
LOGGER | _PdsLogger | pds4file/__init__.py:140 pdslogger.NullLogger()
NEIGHBORS | _Translator | pds4file/__init__.py:153 TranslatorByRegex
OPUS_FORMAT | _Translator | pds4file/__init__.py:163 TranslatorByRegex
OPUS_ID | _Translator | pds4file/__init__.py:166 TranslatorByRegex
OPUS_ID_TO_PRIMARY_LOGICAL_PATH | _Translator | pds4file/__init__.py:167 TranslatorByRegex
OPUS_ID_TO_SUBCLASS | _Translator | pds4file/__init__.py:169 TranslatorByRegex
OPUS_PRODUCTS | _Translator | pds4file/__init__.py:164 TranslatorByRegex
OPUS_TYPE | _Translator | pds4file/__init__.py:162 TranslatorByRegex
PDS_HOLDINGS | str | pds4file/__init__.py:111 'pds4-holdings'
PRODUCT_LBL_BASENAME_WO_EXT | _Translator | pds4file/__init__.py:178 TranslatorByRegex
SIBLINGS | _Translator | pds4file/__init__.py:154 TranslatorByRegex
SORT_KEY | _Translator | pds4file/__init__.py:155 TranslatorByRegex
SPLIT_RULES | _Translator | pds4file/__init__.py:156 TranslatorByRegex
SUBCLASSES | dict[str, type[Pds4File]] | pds4file/__init__.py:173 = {}; :385 assigns Pds4File under 'default'; pds4 rule modules assign their Pds4File subclasses
VERSIONS | _Translator | pds4file/__init__.py:151 TranslatorByRegex
VIEWABLES | dict[str, _Translator] | pds4file/__init__.py:158; pds4file/rules/__init__.py:459 {'default': NullTranslator()}
VIEW_OPTIONS | _Translator | pds4file/__init__.py:157 TranslatorByRegex
VOLSET_TRANSLATOR | _Translator | not in the class body; base default at pdsfile.py:354, rebound on Pds4File by its rule modules the way the pds3 side does it
archive_dirs | (self) -> dict[str, list[str]] | pds4file/__init__.py:327-379: keys are the str elements of archive_paths(), values built by summing glob_glob() lists, and glob_glob returns lists of abspath strings (/seti/all_repos/rms-pdsfile/src/pdsfile/_local_fs.py:523/:525/:528 et al.)
archive_paths | (self) -> list[str] | pds4file/__init__.py:298-325: `self.root_ + p` for p in ARCHIVE_PATHS.all(logical_path); root_ is str (pdsfile.py:479) and TranslatorByRegex.all with str replacement templates returns a list of str (venv translator/__init__.py:446-487 with expand's regex.sub); the rule tables hold str templates (e.g. pds4file/rules/cassini_vims.py:379+)
require_shelves | classmethod (cls, status: bool = True) -> None | pds4file/__init__.py:220 assigns cls.SHELVES_REQUIRED, no return
set_easylogger | classmethod (cls) -> None | pds4file/__init__.py:286 calls cls.set_logger, no return
set_logger | classmethod (cls, logger: _PdsLogger | None = None) -> None | pds4file/__init__.py:265 assigns cls.LOGGER, no return
use_shelves_only | classmethod (cls, status: bool = True) -> None | pds4file/__init__.py:200 assigns cls.SHELVES_ONLY, no return

## Instance attributes

None. Neither pds3file/__init__.py nor pds4file/__init__.py assigns any `self.name = ...`; both `__init__` bodies are only `super().__init__()` (pds3file/__init__.py:218, pds4file/__init__.py:197). All instance state comes from the base class.

## Discrepancies

- volset_pdsfile — pds3file/__init__.py:467-469 docstring says "Pds3File: the volume-set-level object, or None". The base bundleset_pdsfile (pdsfile.py:985-1020) builds via `type(self).from_abspath()` (which would be a Pds3File), but its rank branch returns `pdsf.all_versions()[rank]`, and all_versions (_properties.py:2618-2642) is only provably `dict` of PdsFile values. Declared `PdsFile | None` (broader, per rule 1).
- volume_pdsfile — pds3file/__init__.py:504-506 docstring says "Pds3File: ... or None"; same reasoning via bundle_pdsfile (pdsfile.py:948-983, rank branch at :979). Declared `PdsFile | None`.
- VOLSET_TRANSLATOR — the member list attributes it to the class's own body, but neither __init__.py assigns it; it becomes an own-dict attribute only because every rule module rebinds it onto the class at import time (e.g. pds3file/rules/ASTROM_xxxx.py:49-50). Type is the same `_Translator` as the base's pdsfile.py:354 default, so nothing changes in the stub, but the provenance is worth knowing.
- No other docstring/code disagreements found: volume_abspath's "empty string" and volset_abspath's "or None" asymmetry is real in the code (pdsfile.py:1135 vs :1188) and both docstrings state it correctly.

## Imports needed

- `import re` (for `re.Pattern[str]`)
- `from pdsfile.pdscache import DictionaryCache` (CACHE on both classes)
- `PdsFile` by bare name (base class, already in the enclosing stub)
- aliases `_Translator`, `_PdsLogger` (assumed defined)
- Nothing from `collections.abc`; `Self` not needed (no member returns self or a cls() instance)
