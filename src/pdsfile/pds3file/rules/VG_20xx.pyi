"""Type stubs for ``pdsfile.pds3file.rules.VG_20xx`` (see the module docstring there).

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

description_and_icon_by_regex: _Translator
filespec_to_bundleset: _Translator

class VG_20xx(Pds3File):
    DESCRIPTION_AND_ICON: _Translator
