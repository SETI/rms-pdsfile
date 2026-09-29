"""Type stubs for ``pdsfile.pds3file.rules.NHxxxx_xxxx`` (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the runtime public surface. Types are derived from the implementation;
translator tables are ``Any`` because rms-translator ships no py.typed marker.
"""

import re as re
from typing import Any

import translator as translator  # type: ignore[import-untyped]

from pdsfile import pds3file as pds3file
from pdsfile.pds3file import Pds3File

# rms-translator ships no py.typed marker, so a Translator cannot be named here.
_Translator = Any

FILE_CODE_PRIORITY: dict[str, int]
associations_to_documents: _Translator
associations_to_metadata: _Translator
associations_to_previews: _Translator
associations_to_volumes: _Translator
calibrated_viewables: _Translator
default_viewables: _Translator
description_and_icon_by_regex: _Translator
filespec_to_bundleset: _Translator
neighbors: _Translator
opus_id: _Translator
opus_id_to_primary_logical_path: _Translator
opus_products: _Translator
opus_type: _Translator
raw_viewables: _Translator
sort_key: _Translator
split_rules: _Translator
versions: _Translator
view_options: _Translator

class NHxxxx_xxxx(Pds3File):
    ASSOCIATIONS: dict[str, _Translator]
    DESCRIPTION_AND_ICON: _Translator
    FILENAME_KEYLEN: int
    NEIGHBORS: _Translator
    OPUS_ID: _Translator
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH: _Translator
    OPUS_PRODUCTS: _Translator
    OPUS_TYPE: _Translator
    SORT_KEY: _Translator
    SPLIT_RULES: _Translator
    VERSIONS: _Translator
    VIEWABLES: dict[str, _Translator]
    VIEWABLE_TOOLTIPS: dict[str, str]
    VIEW_OPTIONS: _Translator
    def opus_prioritizer(self, pdsfile_dict: dict[Any, Any]) -> dict[Any, Any]: ...
