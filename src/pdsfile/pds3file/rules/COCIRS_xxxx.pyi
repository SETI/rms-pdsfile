"""Type stubs for ``pdsfile.pds3file.rules.COCIRS_xxxx`` (see the module docstring there).

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

associations_to_diagrams: _Translator
associations_to_documents: _Translator
associations_to_metadata: _Translator
associations_to_previews: _Translator
associations_to_volumes: _Translator
data_set_id: _Translator
default_viewables: _Translator
description_and_icon_by_regex: _Translator
naif_id: int
name: str
neighbors: _Translator
opus_format: _Translator
opus_id: _Translator
opus_id_to_primary_logical_path: _Translator
opus_products: _Translator
opus_type: _Translator
s_rings_viewables: _Translator
saturn_viewables: _Translator
spice_lookup: dict[int, str]
split_rules: _Translator
versions: _Translator
view_options: _Translator
viewables: dict[str, _Translator]

class COCIRS_xxxx(Pds3File):
    ASSOCIATIONS: dict[str, _Translator]
    DATA_SET_ID: _Translator
    DESCRIPTION_AND_ICON: _Translator
    NEIGHBORS: _Translator
    OPUS_FORMAT: _Translator
    OPUS_ID: _Translator
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH: _Translator
    OPUS_PRODUCTS: _Translator
    OPUS_TYPE: _Translator
    SPLIT_RULES: _Translator
    VERSIONS: _Translator
    VIEWABLES: dict[str, _Translator]
    VIEWABLE_TOOLTIPS: dict[str, str]
    VIEW_OPTIONS: _Translator
