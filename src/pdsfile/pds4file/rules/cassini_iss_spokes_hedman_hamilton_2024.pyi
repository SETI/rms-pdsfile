"""Type stubs for ``pdsfile.pds4file.rules.cassini_iss_spokes_hedman_hamilton_2024`` (see the module docstring there).

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

archive_dirs: _Translator
archive_paths: _Translator
description_and_icon_by_regex: _Translator
neighbors: _Translator
opus_type: _Translator
product_lbl_basename_wo_ext: _Translator
sort_key: _Translator
view_options: _Translator

class cassini_iss_spokes_hedman_hamilton_2024(Pds4File):
    DESCRIPTION_AND_ICON: _Translator
    NEIGHBORS: _Translator
    OPUS_TYPE: _Translator
    PRODUCT_LBL_BASENAME_WO_EXT: _Translator
    SORT_KEY: _Translator
    VIEW_OPTIONS: _Translator
