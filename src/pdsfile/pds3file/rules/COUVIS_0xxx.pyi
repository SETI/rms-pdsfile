"""Type stubs for ``pdsfile.pds3file.rules.COUVIS_0xxx`` (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the runtime public surface. Types are derived from the implementation;
translator tables are ``Any`` because rms-translator ships no py.typed marker.
"""

import os as os
import re as re
from typing import Any

import translator as translator  # type: ignore[import-untyped]

from pdsfile import pds3file as pds3file
from pdsfile.pds3file import Pds3File

# rms-translator ships no py.typed marker, so a Translator cannot be named here.
_Translator = Any

associations_to_documents: _Translator
associations_to_metadata: _Translator
associations_to_previews: _Translator
associations_to_volumes: _Translator
default_viewables: _Translator
description_and_icon_by_regex: _Translator
neighbors: _Translator
opus_format: _Translator
opus_id: _Translator
opus_id_to_primary_logical_path: _Translator
opus_products: _Translator
opus_type: _Translator
sort_key: _Translator
view_options: _Translator

class COUVIS_0xxx(Pds3File):
    ASSOCIATIONS: dict[str, _Translator]
    def DATA_SET_ID(self) -> Any: ...
    DESCRIPTION_AND_ICON: _Translator
    NEIGHBORS: _Translator
    OPUS_FORMAT: _Translator
    OPUS_ID: _Translator
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH: _Translator
    OPUS_PRODUCTS: _Translator
    OPUS_TYPE: _Translator
    SORT_KEY: _Translator
    VERSIONS_PATH_AND_KEY: _Translator
    VIEWABLES: dict[str, _Translator]
    VIEW_OPTIONS: _Translator
