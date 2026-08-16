"""Type stubs for ``pdsfile.pds3file.rules.COVIMS_0xxx`` (see the module docstring there).

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
from pdsfile.pdsfile import abspath_for_logical_path as abspath_for_logical_path

# rms-translator ships no py.typed marker, so a Translator cannot be named here.
_Translator = Any

BASENAME_REGEX: re.Pattern[str]
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
view_options: _Translator

class COVIMS_0xxx(Pds3File):
    ASSOCIATIONS: dict[str, _Translator]
    DESCRIPTION_AND_ICON: _Translator
    def FILENAME_KEYLEN(self) -> int: ...  # type: ignore[override]
    LOWER_VERSION_PRIORITIZED: dict[str, str]
    NEIGHBORS: _Translator
    OPUS_FORMAT: _Translator
    OPUS_ID: _Translator
    def OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id: str) -> Pds3File: ...  # type: ignore[misc, override]
    OPUS_PRODUCTS: _Translator
    OPUS_TYPE: _Translator
    VIEWABLES: dict[str, _Translator]
    VIEW_OPTIONS: _Translator
