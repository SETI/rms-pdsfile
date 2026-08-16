"""Type stubs for ``pdsfile.pds3file.rules`` (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the runtime public surface. Types are derived from the implementation;
translator tables are ``Any`` because rms-translator ships no py.typed marker.
"""

import re as re
from typing import Any

import translator as translator  # type: ignore[import-untyped]

from . import ASTROM_xxxx as ASTROM_xxxx
from . import COCIRS_xxxx as COCIRS_xxxx
from . import COISS_xxxx as COISS_xxxx
from . import CORSS_8xxx as CORSS_8xxx
from . import COSP_xxxx as COSP_xxxx
from . import COUVIS_0xxx as COUVIS_0xxx
from . import COUVIS_8xxx as COUVIS_8xxx
from . import COVIMS_0xxx as COVIMS_0xxx
from . import COVIMS_8xxx as COVIMS_8xxx
from . import EBROCC_xxxx as EBROCC_xxxx
from . import GO_0xxx as GO_0xxx
from . import HSTxx_xxxx as HSTxx_xxxx
from . import JNOJIR_xxxx as JNOJIR_xxxx
from . import JNOJNC_xxxx as JNOJNC_xxxx
from . import JNOSP_xxxx as JNOSP_xxxx
from . import JNOSRU_xxxx as JNOSRU_xxxx
from . import NHSP_xxxx as NHSP_xxxx
from . import NHxxxx_xxxx as NHxxxx_xxxx
from . import RES_xxxx as RES_xxxx
from . import RPX_xxxx as RPX_xxxx
from . import VG_0xxx as VG_0xxx
from . import VG_20xx as VG_20xx
from . import VG_28xx as VG_28xx
from . import VGIRIS_xxxx as VGIRIS_xxxx
from . import VGISS_xxxx as VGISS_xxxx

# rms-translator ships no py.typed marker, so a Translator cannot be named here.
_Translator = Any

__all__ = [
    'ASTROM_xxxx',
    'COCIRS_xxxx',
    'COISS_xxxx',
    'CORSS_8xxx',
    'COSP_xxxx',
    'COUVIS_0xxx',
    'COUVIS_8xxx',
    'COVIMS_0xxx',
    'COVIMS_8xxx',
    'EBROCC_xxxx',
    'GO_0xxx',
    'HSTxx_xxxx',
    'JNOJIR_xxxx',
    'JNOJNC_xxxx',
    'JNOSP_xxxx',
    'NHSP_xxxx',
    'NHxxxx_xxxx',
    'RES_xxxx',
    'RPX_xxxx',
    'VG_0xxx',
    'VG_20xx',
    'VG_28xx',
    'VGIRIS_xxxx',
    'VGISS_xxxx',
]

ASSOCIATIONS: dict[str, _Translator]
CROSS_PDS3_PDS4_PRODUCTS: _Translator
DATA_SET_ID: _Translator
DESCRIPTION_AND_ICON: _Translator
FILESPEC_TO_BUNDLESET: _Translator
GENERIC_VOLSET_DESC: str
GENERIC_VOLUME_DESC: str
INFO_FILE_BASENAMES: _Translator
LID_AFTER_DSID: _Translator
NEIGHBORS: _Translator
OPUS_FORMAT: _Translator
OPUS_ID: _Translator
OPUS_ID_TO_PRIMARY_LOGICAL_PATH: _Translator
OPUS_ID_TO_SUBCLASS: _Translator
OPUS_PRODUCTS: _Translator
OPUS_TYPE: _Translator
SIBLINGS: _Translator
SORT_KEY: _Translator
SPLIT_RULES: _Translator
VERSIONS: _Translator
VIEWABLES: dict[str, _Translator]
VIEWABLE_TOOLTIPS: dict[str, str]
VIEW_OPTIONS: _Translator
