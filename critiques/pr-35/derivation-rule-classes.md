# Notes: the rule-module stubs (36 modules, 31 classes)

The rule stubs were generated from the measured runtime surface by a script whose
type tables fail loudly on any name they have no entry for. Three kinds of members
exist, and only the third needed per-member derivation:

* **Translator tables** (200 class members, plus the module-level tables): every
  one is an rms-translator object, and rms-translator ships no py.typed marker, so
  every one is the commented alias `_Translator` (= `Any`) by rule 4.
* **Uniform data members**: `ASSOCIATIONS: dict[str, _Translator]` (built by
  `.copy()` of the base dict plus translator `+=`), `VIEWABLES: dict[str,
  _Translator]` (dict literals keyed by viewable name), `VIEWABLE_TOOLTIPS:
  dict[str, str]`, `FILENAME_KEYLEN: int` where it is an int literal, and the
  per-module one-offs typed at their definitions (`spice_lookup: dict[int, str]`,
  VG_28xx's eighteen `*_DICT`/`KIND`/`ICON`/`NEXT` names which are triple-quoted
  **strings**, `FILE_CODE_PRIORITY: dict[str, int]`, `ARCHIVE_PATHS_DICT: dict[str,
  dict[str, list[str]]]`, `PRIMARY_FILESPEC_LIST: list[str]`, the
  `uranus_occs_earthbased` build-loop leftovers, `BASENAME_REGEX:
  re.Pattern[str]`).
* **The seven hand-derived methods**, rows below.

## Method members

- COISS_xxxx.FILENAME_KEYLEN | (self) -> int | COISS_xxxx.py:820-835: two return
  statements, the literals 0 and 11. Overrides the base's `int` attribute, hence
  `type: ignore[override]`.
- RPX_xxxx.FILENAME_KEYLEN | (self) -> int | RPX_xxxx.py:272-289: two return
  statements, the literals 9 and 0. Same override pattern.
- COVIMS_0xxx.FILENAME_KEYLEN | (self) -> int | COVIMS_0xxx.py:437-456: returns
  `len(match.group(1) + match.group(2))` or the literal 0; `len()` is int. Same
  override pattern.
- COUVIS_0xxx.DATA_SET_ID | (self) -> Any | COUVIS_0xxx.py:309-362: the guard
  paths return `''`, but the main path returns `row.row_dicts[0]['DATA_SET_ID']`
  — content of an untyped pdstable row dictionary, the same flow that makes the
  base `data_set_id` property Any. Declared `Any` by rule 4. CORRECTED after
  review round 1: the generated stub said `str` (the docstring's claim), which is
  not derivable. Overrides a base data attribute, but that attribute is declared
  `_Translator | None` (`Any | None`), which any override satisfies, so no
  `type: ignore[override]` is needed.
- GO_0xxx.opus_prioritizer | (self, pdsfile_dict: dict[Any, Any]) -> dict[Any,
  Any] | GO_0xxx.py:819-901: mutates and returns the same dictionary; its keys
  are five-element tuples or `''` and its values lists of lists of PdsFile per the
  docstring, but both flow from the untyped opus_products machinery, so the
  element types are not provable — `dict[Any, Any]` both ways.
- NHxxxx_xxxx.opus_prioritizer | (self, pdsfile_dict: dict[Any, Any]) ->
  dict[Any, Any] | NHxxxx_xxxx.py (same shape as GO_0xxx's; the module docstring
  names these two as the only prioritizers).
- COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH | (opus_id: str) -> PdsFile |
  COVIMS_0xxx.py:387-436: a plain function in the class body (no decorator, no
  self — reached off the class), hence `type: ignore[misc]`. Every return is
  `Pds3File.from_logical_path(...)` on a nonempty literal from
  `LOWER_VERSION_PRIORITIZED` or `Pds3File.from_abspath(...)` on a glob match;
  the stubs declare those delegates `PdsFile | None` (None only for the empty
  path, unreachable here) and `PdsFile`, so the provable return is `PdsFile`.
  CORRECTED after review round 1: the generated stub said `Pds3File`, which is
  narrower than the delegates' declared types — the same alias-narrower-than-base
  shape as the round's Major 1.
