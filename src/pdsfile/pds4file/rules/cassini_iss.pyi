"""Type stubs for ``pdsfile.pds4file.rules.cassini_iss`` (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the runtime public surface. Types are derived from the implementation;
translator tables are ``Any`` because rms-translator ships no py.typed marker.
"""

import re as re
from typing import Any

import translator as translator  # type: ignore[import-untyped]

from pdsfile import pds4file as pds4file
from pdsfile.pds4file import Pds4File

# rms-translator ships no py.typed marker, so a Translator cannot be named here.
_Translator = Any

ARCHIVE_PATHS_DICT: dict[str, dict[str, list[str]]]
archive_dirs: _Translator
archive_paths: _Translator
associations_to_bundles: _Translator
associations_to_calibrated: _Translator
associations_to_documents: _Translator
associations_to_metadata: _Translator
associations_to_previews: _Translator
default_viewables: _Translator
description_and_icon_by_regex: _Translator
filespec_to_bundleset: _Translator
neighbors: _Translator
opus_format: _Translator
opus_id: _Translator
opus_id_to_primary_logical_path: _Translator
opus_products: _Translator
opus_type: _Translator
sort_key: _Translator
view_options: _Translator

class cassini_iss(Pds4File):
    ARCHIVE_DIRS: _Translator
    ARCHIVE_PATHS: _Translator
    ASSOCIATIONS: dict[str, _Translator]
    DESCRIPTION_AND_ICON: _Translator
    NEIGHBORS: _Translator
    OPUS_FORMAT: _Translator
    OPUS_ID: _Translator
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH: _Translator
    OPUS_PRODUCTS: _Translator
    OPUS_TYPE: _Translator
    SORT_KEY: _Translator
    VIEWABLES: dict[str, _Translator]
    VIEW_OPTIONS: _Translator
