"""Type stubs for ``pdsfile.pds3file.rules.COSP_xxxx`` (see the module docstring there).

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

associations_to_documents: _Translator
filespec_to_bundleset: _Translator
info_file_basenames: _Translator

class COSP_xxxx(Pds3File):
    ASSOCIATIONS: dict[str, _Translator]
    INFO_FILE_BASENAMES: _Translator
