# Notes: frag-sortshelf (_sorting.py, _shelves.py, _index_rows.py)

All members are class-body members of the flattened `class PdsFile`; none is module-level.
`PdsFile` (bare name) is used for object-returning methods rather than `Self`: every such
value either comes from a constructor that dispatches to a looked-up subclass
(`from_abspath`, `from_logical_path`, `child`, `new_index_row_pdsfile`) or from an untyped
cache, so "same class as self/cls" is not provable anywhere in these three files.

## Members

### pdsfile._index_rows
- child_of_index | `(self, selection: str, flag: str = '=') -> PdsFile` | _index_rows.py:272-362; returns `cls.CACHE[...]` (line 328, `pdscache.DictionaryCache`, untyped -> Any branch) or `self.new_index_row_pdsfile(...)` (lines 354, 359; pdsfile.py:808 builds a copy of self, docstring "Returns: PdsFile"). Not provably Self (cache value is whatever was stored), so `PdsFile`.
- data_abspath_associated_with_index_row | `(self) -> str` | _index_rows.py:364-498; every return is `''` (463, 471, 498), `'/'.join(parts)` (480), or `abspath` built by str.replace (489-492). No None path.
- data_pdsfile_for_index_row | `(self) -> PdsFile | None` | _index_rows.py:500-527; `return cls.from_abspath(abspath)` (525) or `return None` (527). `from_abspath` instantiates a looked-up subclass, so `PdsFile`, not `Self`.
- find_selected_row_key | `(self, selection: str, flag: str = '=', exact_match: bool = False) -> str` | _index_rows.py:133-270; all returns are `selection` or elements of `self.childnames` (list of str basenames).
- get_indexshelf | `(self) -> dict[Any, Any]` | _index_rows.py:97-131; returns `cls._get_shelf(...)` (_shelves.py:279-372), a dict rebuilt from `pickle.load` (line 341, 350) -> both keys and values unprovable, hence `dict[Any, Any]` rather than the docstring's `dict` of row key -> row number(s).

### pdsfile._shelves
- close_all_shelves | `@classmethod (cls) -> None` | _shelves.py:402-413; no return statement.
- info_shelf_expected | `@property (self) -> bool` | _shelves.py:560-604; returns False/True literals or `bool(self.bundlename)` (604).
- shelf_exists_if_expected | `(self) -> bool | None` | _shelves.py:606-631; returns True (626), False (628), or falls through to `return None` (631) when no shelf is expected.
- shelf_lookup | `(self, shelf_type: str = 'info', bundlename: str = '') -> Any` | _shelves.py:415-484; returns `cls.SHELF_NULL_KEY_VALUES[...]` (464), `_eval_null_key_record()` output (479, an `eval()` at line 97), or `shelf[key]` (484, unpickled dict) -> all Any.
- shelf_path_and_key | `(self, shelf_id: str = 'info', bundlename: str = '') -> tuple[str, str]` | _shelves.py:245-276; `(abspath, '')` or `(abspath, self.interior)`; abspath is a `''.join` from shelf_path_and_lskip (237), interior is the str interior-path instance attribute (class contract, _shelves.py:146).
- shelf_path_and_key_for_abspath | `@classmethod (cls, abspath: str, shelf_type: str = 'info') -> tuple[str, str]` | _shelves.py:486-558; both elements built by `''.join`/`'/'.join` (541-556).
- shelf_path_and_lskip | `(self, shelf_type: str = 'info', bundlename: str = '') -> tuple[str, int]` | _shelves.py:156-243; abspath via `''.join` (215, 237), lskip via `len()` sums (218, 240).

### pdsfile._sorting
- abspaths_for_basenames | `(self, basenames: Iterable[str], must_exist: bool = False) -> list[str | None]` | _sorting.py:857-879; shortcut branch (876) yields all str, but the general branch returns `[pdsf.abspath for pdsf in pdsfiles]` (879) and abspath is None for a merged-directory child (docstring 863-864: "contributes None"). Param only iterated (comprehension), so Iterable.
- abspaths_for_logicals | `@classmethod (cls, logical_paths: Iterable[str], must_exist: bool = False) -> list[str]` | _sorting.py:784-809; `abspath_for_logical_path` (_path_utils.py:344) returns str or raises.
- abspaths_for_pdsfiles | `@staticmethod (pdsfiles: Iterable[PdsFile], must_exist: bool = False) -> list[str]` | _sorting.py:629-649; both branches filter `p.abspath is not None`, so the None case is excluded and elements are str.
- basename_is_label | `(self, basename: str) -> bool` | _sorting.py:172-195; `and` of two boolean comparisons (195).
- basename_is_viewable | `(self, basename: str | None = None) -> bool` | _sorting.py:197-223; runtime default None (falls back to self.basename); returns False or a membership test.
- basenames_for_abspaths | `@classmethod (cls, abspaths: Iterable[str], must_exist: bool = False) -> list[str]` | _sorting.py:740-758; `os.path.basename` per element.
- basenames_for_logicals | `@classmethod (cls, logical_paths: Iterable[str], must_exist: bool = False) -> list[str]` | _sorting.py:811-832; either `basenames_for_pdsfiles` (str basenames) or `os.path.basename`.
- basenames_for_pdsfiles | `@staticmethod (pdsfiles: Iterable[PdsFile], must_exist: bool = False) -> list[str]` | _sorting.py:671-689; `p.basename` is the str basename attribute.
- childnames_by_anchor | `(self, anchor: str) -> list[str]` | _sorting.py:586-606; appends elements of `self.childnames` (str basenames).
- logicals_for_abspaths | `@classmethod (cls, abspaths: Iterable[str], must_exist: bool = False) -> list[str]` | _sorting.py:714-738; `logical_path_from_abspath` (_path_utils.py:113) returns `parts[2]` of a str.partition -> str, or raises.
- logicals_for_basenames | `(self, basenames: Iterable[str], must_exist: bool = False) -> list[str]` | _sorting.py:881-901; `_clean_join` of strs (898) or `pdsf.logical_path` (901), which is always a str (every object has one, docstring 655-656).
- logicals_for_pdsfiles | `@staticmethod (pdsfiles: Iterable[PdsFile], must_exist: bool = False) -> list[str]` | _sorting.py:651-669; `p.logical_path` str.
- pdsfiles_for_abspaths | `@classmethod (cls, abspaths: Iterable[str], must_exist: bool = False) -> list[PdsFile]` | _sorting.py:693-712; `cls.from_abspath(p)` instantiates a looked-up subclass -> `PdsFile`, not Self.
- pdsfiles_for_basenames | `(self, basenames: Iterable[str], must_exist: bool = False) -> list[PdsFile]` | _sorting.py:836-855; `self.child(b)` (850) returns child objects, class chosen by the child machinery -> `PdsFile`.
- pdsfiles_for_logicals | `@classmethod (cls, logical_paths: Iterable[str], must_exist: bool = False) -> list[PdsFile]` | _sorting.py:762-782; `cls.from_logical_path(p)` -> `PdsFile`.
- sort_basenames | `(self, basenames: Sequence[str], labels_after: bool | None = None, dirs_first: bool | None = None, dirs_last: bool | None = None, info_first: int | None = None) -> list[str]` | _sorting.py:225-348; param needs `len()` (344) and `list()` (346) -> Sequence, not just Iterable; returns the new sorted `list` (346-348). `info_first` is documented as bool-or-int threshold (255-257) and goes through `int(info_first)` (343) -> `int | None` (bool is an int subtype).
- sort_childnames | `(self, labels_after: bool | None = None, dirs_first: bool | None = None) -> list[str]` | _sorting.py:553-569; delegates to sort_basenames over `self.childnames`.
- sort_logical_paths | `@classmethod (cls, logical_paths: Iterable[str]) -> list[str]` | _sorting.py:443-551; param iterated twice + `set()` (485, 532); returns the assembled `sorted_paths` list of str path joins.
- sort_siblings | `(self, siblings: Iterable[PdsFile], labels_after: bool | None = None, dirs_first: bool | None = None, dirs_last: bool | None = None, info_first: int | None = None) -> list[PdsFile]` | _sorting.py:406-441; dict comprehension over siblings once (432); returns the input objects plus self, reordered (441).
- sort_sibnames | `(self, basenames: list[str], labels_after: bool | None = None, dirs_first: bool | None = None, dirs_last: bool | None = None, info_first: int | None = None) -> list[str]` | _sorting.py:350-404; param MUST be a real list: it is mutated via `.append` (386); returns a new list of str.
- split_basename | `(self, basename: str = '') -> Any` | _sorting.py:101-170; returns the unchanged str basename when SPLIT_RULES is None (145), 3-tuples of regex groups (151, 153, 164, 166), or `self.SPLIT_RULES.first(basename)` (159/168, 170) -- SPLIT_RULES is an rms-translator table (untyped, no py.typed) so that branch is Any, and Any absorbs the union.
- viewable_childnames | `(self) -> list[str]` | _sorting.py:571-584; filter of `self.childnames` str basenames.
- viewable_childnames_by_anchor | `(self, anchor: str) -> list[str]` | _sorting.py:608-621; filter of childnames_by_anchor's list[str].

## Instance attributes

Public instance attributes assigned via `self.name = ...` in these three files:

- `column_names` | `list[Any]` | _index_rows.py:347-348 (`self.column_names = [c.name for c in table.info.column_info_list]` inside child_of_index, filled when still empty). Element type flows from untyped rms-pdstable (`c.name`), so only `list` is provable; documented as column names (strings). Note the attribute itself is created elsewhere (read at _index_rows.py:346); this file only refills it.

Non-public, for completeness (not part of the requested list): `_exists_filled` is assigned on the newly built row object (`pdsf._exists_filled`, _index_rows.py:355, 360), not on self. _sorting.py and _shelves.py assign no instance attributes at all (their class docstrings state "instance attributes written none", and the code confirms it).

## Discrepancies

1. `split_basename` (_sorting.py:134-136 vs 144-145, 159-170): the Returns section says `tuple` (anchor, suffix, extension/volume-type), but the code returns the bare str basename when `SPLIT_RULES is None` (line 145 -- the prose at 125-129 does admit this), and the rule-table branch (`SPLIT_RULES.first`, lines 159/168/170) flows through untyped rms-translator. Declared `Any` (the honest union `str | tuple[str, str, str] | Any` collapses to Any).
2. `abspaths_for_basenames` (_sorting.py:870-871 vs 879): the Returns section says "list: the absolute paths", but the non-shortcut branch emits `pdsf.abspath`, which is None for a child with no absolute path (the prose at 863-864 admits "contributes None"). Declared `list[str | None]`.
3. `get_indexshelf` (_index_rows.py:107-108 vs _shelves.py:341): the docstring promises "dict: the row key mapped to a row number or a sequence of row numbers", but the dict comes from `pickle.load` so neither keys nor values are provable. Declared `dict[Any, Any]` (broader, per rule 1).
4. `child_of_index` (_index_rows.py:302 vs 326-330): docstring "Returns: PdsFile" -- kept, but note the first return path is `cls.CACHE[...]`, an untyped `pdscache.DictionaryCache` lookup (pdsfile.py:334), so this is documented intent plus an Any-typed branch, not a provable narrow type; `Self` is not provable on any path.
5. `sort_basenames` / `sort_sibnames` / `sort_siblings` `info_first` (_sorting.py:255-257 etc.): the parameter list gives it no type but describes False/True/int threshold semantics; sibling params are declared `(bool)`. Declared `int | None` (bool is a subtype of int), which is broader than a reader of the `(bool)` pattern might assume.
6. `sort_sibnames` (_sorting.py:366-368): docstring says "basenames (list)" and warns the caller's list is appended to -- the code (386) confirms; declared strictly `list[str]` (an arbitrary Iterable would break at `.append`), unlike the other bulk methods where "list" in the docstring is broadened to `Iterable[str]` because the code only iterates.

## Imports needed

- `from typing import Any` (Self is NOT needed by this fragment)
- `from collections.abc import Iterable, Sequence`
- bare name `PdsFile` (usable inside the class body of the flattened stub)
