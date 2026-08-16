"""Type stubs for ``pdsfile.pds4file.rules`` (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the runtime public surface. Types are derived from the implementation;
translator tables are ``Any`` because rms-translator ships no py.typed marker.
"""

import re as re
from typing import Any

import translator as translator  # type: ignore[import-untyped]

from . import cassini_iss as cassini_iss
from . import (
    cassini_iss_fring_mosaics_rsfrench2025 as cassini_iss_fring_mosaics_rsfrench2025,
)
from . import (
    cassini_iss_fring_mosaics_rsfrench2025_primary_filespec as cassini_iss_fring_mosaics_rsfrench2025_primary_filespec,
)
from . import (
    cassini_iss_spokes_hedman_hamilton_2024 as cassini_iss_spokes_hedman_hamilton_2024,
)
from . import (
    cassini_uvis_solarocc_beckerjarmak2023 as cassini_uvis_solarocc_beckerjarmak2023,
)
from . import (
    cassini_uvis_solarocc_beckerjarmak2023_primary_filespec as cassini_uvis_solarocc_beckerjarmak2023_primary_filespec,
)
from . import cassini_vims as cassini_vims
from . import uranus_occs_earthbased as uranus_occs_earthbased
from . import (
    uranus_occs_earthbased_primary_filespec as uranus_occs_earthbased_primary_filespec,
)

# rms-translator ships no py.typed marker, so a Translator cannot be named here.
_Translator = Any

__all__ = [
    'uranus_occs_earthbased',
    'cassini_iss',
    'cassini_uvis_solarocc_beckerjarmak2023',
    'cassini_vims',
]

ARCHIVE_DIRS: _Translator
ARCHIVE_PATHS: _Translator
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
PRODUCT_LBL_BASENAME_WO_EXT: _Translator
SIBLINGS: _Translator
SORT_KEY: _Translator
SPLIT_RULES: _Translator
VERSIONS: _Translator
VIEWABLES: dict[str, _Translator]
VIEWABLE_TOOLTIPS: dict[str, str]
VIEW_OPTIONS: _Translator
