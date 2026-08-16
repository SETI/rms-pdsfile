# Notes: _properties.py fragment (64 members of class PdsFile)

All line numbers are in /seti/all_repos/rms-pdsfile/src/pdsfile/_properties.py unless
another file is named. "translator" = a `.first()`/`.all()` call on a rules table from
rms-translator (untyped, rule 4). "CACHE" = `cls.CACHE[...]`, typed `Any` by the repo's
own pdscache.pyi (`__getitem__(self, key: Any) -> Any`, src/pdsfile/pdscache.pyi:58).
"shelf" = `shelf_lookup()`/`_get_shelf()` which return unpickled content
(_shelves.py:415-487, final `return shelf[key]`) -> Any.

## Members

- absolute_or_logical_path | str | 296-310: returns `self.abspath` (truthy branch, str) or `self.logical_path` (str, pdsfile.py:475-476)
- all_version_abspaths | dict[int, str \| None] | 2692-2710: slot filled by all_versions() with `{self.version_rank: self.abspath, ...}` (2658, 2682); version_rank is int (pdsfile.py:491), abspath is str but None on a merged dir (pdsfile.py:739)
- all_versions | dict[int, PdsFile] | 2618-2689: dict values are `self` and `cls.from_abspath(...)`/`pdsfiles_for_abspaths(...)` results (2652, 2671-2681), all PdsFile; keys are `version_rank` ints
- all_viewsets | dict[str, PdsViewSet] | 2004-2073: keys are 'default' and keys of VIEWABLES dict literals (`{'default': ...}`, e.g. pds3file/rules/COISS_xxxx.py:811); values stored only when truthy, so PdsViewSet (from_pdsfiles None/empty filtered at 2036-2068)
- alt | str | 1111-1121: returns `self.basename` (str, pdsfile.py:474)
- anchor | Any | 469-489: `self.split[0]` and `self.parent().split[0] + '-' + ...`; split is Any (translator, see split), Any subscript/left-concat -> Any
- bundle_publication_date | Any | 2144-2196: seeded from `self._volume_info[3]` (CACHE -> Any, 2171); fallbacks slice `.date[:10]` which is itself Any
- bundle_version_id | Any | 2199-2224: `self._volume_info[2]` (CACHE -> Any) or ''
- checksum | Any | 1021-1038: `self._volume_info[5] or self._info[3]`; both CACHE/shelf-derived -> Any
- childnames | list[Any] | 702-752: list built by `sort_basenames()` (returns its input elements) over `os_listdir()` whose SHELVES_ONLY branch yields shelf keys (`for key in shelf` over unpickled dict, _local_fs.py:361-370 -> Any), and over `list(shelf.keys())` from `get_indexshelf()` (unpickled, 747-749) -> element type unprovable
- childnames_lc | list[Any] | 755-774: `[c.lower() for c in self.childnames]`; elements Any because childnames elements are Any
- continuous_view_allowed | Any | 2442-2457: `self._view_options_filled[2]`; slot holds `(False, False, False)` or `VIEW_OPTIONS.first(...)` (translator -> Any, 2415-2416)
- data_abspaths | list[str] | 1896-1928: appends elements of `self.linked_abspaths` (list[str], see below) filtered by a comparison (1923-1927)
- data_set_id | Any | 1461-1502: branches: '' literal, `self.volume_data_set_ids[0]` (Any), `self.DATA_SET_ID()` (untyped callable) or `DATA_SET_ID.first(...)` (translator) -> Any
- date | Any | 1124-1147: `self.modtime.strftime(...)` where modtime is Any (shelf-derived `_info[2]`); `Any.strftime` -> Any; '' on miss
- description | Any | 1235-1314: `_description_and_icon_filled[0]`; pair sources include `self._volume_info[:2]` (CACHE), `CACHE['$VOLINFO-'...]` (1306) and `DESCRIPTION_AND_ICON.first(...)` (translator, 1297/1309) -> Any
- exact_archive_url | str | 2312-2350: '' literals or `pdsf.url` (str, see url)
- exact_checksum_url | str | 2353-2387: same shape as exact_archive_url, '' or `pdsf.url`
- exists | bool | 188-221: True/False literals or `cls.os_path_exists()` (all four return paths bool: `os.path.exists`, `key in shelf`, `pdsf.exists and ...`, recursion; _local_fs.py:113-221)
- extension | Any | 520-552: `self.split[2]`; split is Any (translator)
- filename_keylen | Any | 2486-2512: int branch when `FILENAME_KEYLEN` is int (base default 0, pdsfile.py:382), else `self.FILENAME_KEYLEN()` — untyped callable from rule modules -> Any
- filespec | str | 273-293: `self.bundlename_ + self.interior` or `self.bundlename`, all str attrs (pdsfile.py:494-497)
- formatted_size | str | 1150-1175: `formatted_file_size()` returns an f-string (_path_utils.py:340-341); '' on falsy size
- global_anchor | str | 492-517: `(self.parent_logical_path + '/' + self.anchor).replace('/', '-')`; str left operand makes the concatenation str even though anchor is Any, `.replace` -> str
- grid_view_allowed | Any | 2390-2421: `self._view_options_filled[0]`; slot may hold `VIEW_OPTIONS.first(...)` (translator) -> Any
- has_neighbor_rule | bool | 2460-2483: `return bool(parent and self.NEIGHBORS.first(...))`
- height | Any | 1062-1077: `self._info[4][1]`; `_info` shape element is shelf-derived (Any) or literal tuple; union tainted by shelf -> Any
- html_path | str | 377-422: three branches: `child_html_path.rpartition('/')[0]` (str, recursive), `f.read().strip()` (str, 414-415), `self.html_root_ + self.logical_path` (str + str, pdsfile.py:480/476)
- icon_type | Any | 1317-1333: `self._description_and_icon_filled[1]`, same translator/CACHE-derived pair as description
- iconset_closed | PdsViewSet | 2128-2141: `self._iconset_filled[0]`, elements from `pdsviewable.ICON_SET_BY_TYPE` typed `dict[..., PdsViewSet]` (pdsviewable.pyi:26)
- iconset_open | PdsViewSet | 2108-2125: `self._iconset_filled[1]`, same ICON_SET_BY_TYPE source
- index_pdslabel | Any | 642-699: None returns (677, 697) plus `pdsparser.PdsLabel.from_file(...)` (688) — pdsparser ships no py.typed -> Any
- indexshelf_abspath | str | 555-594: '' literal or `self.abspath` passed through three `str.replace()` calls (586-590)
- info_basename | Any | 1575-1629: first source is `INFO_FILE_BASENAMES.first(self.childnames)` (translator, 1604-1605) -> Any; later branches str ('' / basename / EXTRA_README name) and label_basename (Any)
- infoshelf_path_and_key | tuple[str, str] | 2515-2543: `shelf_path_and_key_for_abspath()` returns `(shelf_abspath, key)` both built by `''.join`/`'/'.join` of strs (_shelves.py:544-559); fallback `('', '')` (2539)
- internal_link_info | str \| list[tuple[Any, Any, str]] \| tuple[()] | 1632-1737: str branch `volume_path_ + values` (str + narrowed str, 1711); triples `(recno, basename, abspath)` where recno/basename iterate unpickled shelf values (Any) and abspath is str (`abspath_for_logical_path` returns `_clean_join`/glob match strs, _path_utils.py:354-366; or str-led concatenations, 1725-1732); `[]` at 1675/1702/1713; `()` failure marker at 1690
- is_documents | bool | 258-270: `return self.bundletype_ == 'documents/'`
- is_index | bool | 597-639: slot set True/False (624, 635); uncached second answer `return True` (633)
- is_label | bool | 338-348: returns `self.islabel` (bool)
- is_viewable | bool | 351-374: `basename_is_viewable()` returns False or an `in` test (_sorting.py:197-224)
- isdir | bool | 224-255: True/False literals or `cls.os_path_isdir()` (returns `checksum == ''`, True literals, extension test, or `os.path.isdir`; _local_fs.py:223-293)
- islabel | bool | 313-335: `basename_is_label()` returns `(len(...) > 4) and (... in cls.LBL_EXT)` (_sorting.py:194-195)
- label_abspath | str | 1874-1893: '' or `parent_path + '/' + self.label_basename`; `os.path.split(...)[0]` is str and the str left operand keeps the concatenation str despite label_basename being Any
- label_basename | Any | 1783-1871: guesses come from `rootname + ext` where rootname may be `PRODUCT_LBL_BASENAME_WO_EXT.first(...)` (translator, 1838-1840) -> Any elements; other branches str ('' / `os.path.basename(link_info)`), union -> Any
- lid | Any | 1505-1541: `self.data_set_id + ':' + lid_after_data_set_id` — Any left operand (data_set_id) -> Any; '' otherwise
- lidvid | Any | 1544-1571: `self.lid + "::1.0"` — Any left operand -> Any; '' otherwise
- linked_abspaths | list[str] | 1740-1780: collects the third element of internal_link_info triples (str, see above), or recurses into the label's linked_abspaths, or []
- local_viewset | PdsViewSet \| bool \| None | 1965-2001: slot preset False (merged/index row), `PdsViewSet.from_pdsfiles(self)` returns `PdsViewSet | None` (pdsviewable.pyi:95-99), and a None result is returned as-is (1996-2001) — None is a real return, per its own docstring
- mime_type | str | 1336-1379: branches '' / 'text/plain' literals and `cls.MIME_TYPES_VS_EXT[ext]` from the str->str dict literal (pdsfile.py:260-277)
- modtime | Any | 1002-1018: `self._info[2]`; shelf branch is unpickled (Any); also datetime, None, and the int 0 an index row is born with (pdsfile.py:846) — shelf taint makes it Any
- multipage_view_allowed | Any | 2424-2439: `self._view_options_filled[1]`, translator-derived slot
- opus_format | Any | 1406-1428: `self.OPUS_FORMAT.first(self.logical_path)` stored as it comes (translator) -> Any; stays None on a miss
- opus_id | Any | 1382-1403: `self.OPUS_ID.first(...) or ''` — `Any or str` -> Any
- opus_type | Any | 1431-1458: `self.OPUS_TYPE.first(...) or ''` — Any
- parent_logical_path | str | 777-801: '' or `parent.logical_path` (str)
- size_bytes | Any | 985-999: `self._info[0]`; shelf-derived (Any), `os.path.getsize` int, 0 literals, and None on a merged dir (`_info_filled = [None, ...]`, pdsfile.py:777) — Any
- split | Any | 439-466: `split_basename()` returns match-group tuples, the basename itself, or `self.SPLIT_RULES.first(basename)` (translator, _sorting.py:161-172) -> Any
- url | str | 425-436: returns `self.html_path` (str)
- version_info | (suffix: str \| None) -> tuple[int, str, str] | 2545-2616: docstring and code accept '' and None (2578); returns `(version_rank, version_message, version_id)` = (int arithmetic, str literals/concat, str) at 2616
- version_ranks | Any | 2253-2309: `ranks[key]` where `ranks = cls.CACHE['$RANKS-'...]` (Any) -> stored value unprovable; also [] and a bare-slot None return for nonexistent files (2286-2309)
- viewset | PdsViewSet \| bool | 1931-1962: `viewset_lookup('default')` (PdsViewSet | None) with None converted to False (1958-1959); slot preset False on merged/index row
- viewset_lookup | (self, name: str = 'default') -> PdsViewSet \| None | 2712-2816: returns None (2748, 2801), a cached truthy PdsViewSet (2752), `PdsViewSet.from_pdsfiles(...)` (PdsViewSet | None, 2780/2814), or `PdsViewSet([])` (2816)
- volume_data_set_ids | Any | 2227-2250: `self._volume_info[4]` (CACHE -> Any); merged dir born with '' per docstring 2232-2233
- width | Any | 1041-1059: `self._info[4][0]`, shelf-derived shape -> Any

## Instance attributes

None. _properties.py assigns no public instance attribute: every write is to a
`self._*` lazy slot (all created by `PdsFile.__init__`), plus
`pdsf._all_version_abspaths` written onto sibling objects by `all_versions()`
(2686) — also private.

## Discrepancies

Docstring narrower than what the code proves (declared the provable/broader type):

- 2692-2703 `all_version_abspaths`: docstring "dict: version rank mapped to the absolute path" (str values); code inserts `self.abspath` (2658) which is None on a merged dir (pdsfile.py:739) — declared `dict[int, str | None]`.
- 985-997 `size_bytes`: Returns says "int ... or None on a merged directory"; the shelf branch stores unpickled `file_bytes` (879-883) — declared Any.
- 1002-1016 `modtime`: Returns says datetime/None/int-zero; shelf-derived — declared Any.
- 1041/1062 `width`/`height`: Returns say int; `_info[4]` is shelf-derived — declared Any.
- 1021-1036 `checksum`: Returns says str; both sources are CACHE/shelf (Any) — declared Any.
- 1124-1137 `date`: Returns says str; built by `.strftime` on an Any modtime — declared Any.
- 439-458 `split`: Returns says tuple-or-basename; `SPLIT_RULES.first()` is a translator — declared Any.
- 469-483 `anchor`, 520-545 `extension`: Returns say str; both read `split` (Any) — declared Any.
- 702-727 `childnames`, 755-768 `childnames_lc`: Returns say list of basenames (str); the SHELVES_ONLY listing and the index-shelf keys are unpickled (Any elements) — declared list[Any].
- 1235-1259 `description`, 1317-1330 `icon_type`: Returns say str; translator/CACHE-derived pair — declared Any.
- 1382-1397 `opus_id`: Returns says str; `Any or ''` — declared Any.
- 1406-1422 `opus_format`: Returns says tuple-or-None; raw translator result — declared Any.
- 1431-1451 `opus_type`: Returns says tuple-or-'' ; `Any or ''` — declared Any.
- 1461-1477 `data_set_id`, 1505-1527 `lid`, 1544-1559 `lidvid`: Returns say str; each is (or is concatenated left-of) a translator/CACHE value — declared Any.
- 1575-1596 `info_basename`, 1783-1818 `label_basename`: Returns say str; translator sources (`INFO_FILE_BASENAMES.first`, `PRODUCT_LBL_BASENAME_WO_EXT.first`) — declared Any.
- 2144-2166 `bundle_publication_date`, 2199-2214 `bundle_version_id`: Returns say str; `_volume_info` fields are CACHE-derived — declared Any.
- 2227-2243 `volume_data_set_ids`: Returns says list (or the merged dir's ''); CACHE-derived field — declared Any.
- 2253-2275 `version_ranks`: Returns says list-or-None; `ranks[key]` is a CACHE value, not provably a list — declared Any.
- 2390-2406 `grid_view_allowed`, 2424-2435 `multipage_view_allowed`, 2442-2452 `continuous_view_allowed`: Returns say bool; the stored triple may be a raw `VIEW_OPTIONS.first()` translator result — declared Any.
- 2486-2504 `filename_keylen`: Returns says int; the callable branch invokes an untyped rule-module callable — declared Any.
- 642-670 `index_pdslabel`: Returns says PdsLabel-or-None; pdsparser is untyped — declared Any.
- 1632-1663 `internal_link_info`: Returns says triples of (line number, text, path); the first two elements iterate unpickled shelf values — declared `tuple[Any, Any, str]` elements.

Docstring/code agreements worth confirming (no discrepancy, kept as documented):
- 1964-1989 `local_viewset`: docstring's three-way PdsViewSet/False/None return matches the code (None from `from_pdsfiles` is stored and returned, 1996-2001) — declared `PdsViewSet | bool | None`.
- 2545-2575 `version_info`: docstring says an empty string and None both name the current version; code tests `suffix == '' or suffix is None` (2578) — parameter declared `str | None` even though the JSON signature shows a bare `(suffix)`.
- 1931-1948 `viewset`: "PdsViewSet, or False" — declared `PdsViewSet | bool`.

## Imports needed

- `Any` from typing (already assumed present).
- `PdsViewSet` from pdsfile.pdsviewable (already assumed present).
- No collections.abc names, no `Self` (no member provably returns Self: `all_versions` mixes `self` with `from_abspath` results, declared `dict[int, PdsFile]`), no aliases `_Translator`/`_PdsLogger`/`_PdsTable` used in this fragment.
