"""Type stubs for the ``pdsfile`` package (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the public surface frozen in ``tests/api/api_manifest.json``. The
implementation binds most of these names through two star imports; the stubs
re-export every name explicitly so the exported surface is the manifest's,
including ``rules``, which at runtime is the *pds4file* rules package because
the ``pds4file`` star import runs last.
"""

import re as re

import pdslogger as pdslogger  # type: ignore[import-untyped]

from . import pds3file as pds3file
from . import pds4file as pds4file
from . import pdscache as pdscache
from . import pdsfile as pdsfile
from . import pdsviewable as pdsviewable
from . import preload_and_cache as preload_and_cache
from .pds3file import Pds3File as Pds3File
from .pds3file.rules import ASTROM_xxxx as ASTROM_xxxx
from .pds3file.rules import COCIRS_xxxx as COCIRS_xxxx
from .pds3file.rules import COISS_xxxx as COISS_xxxx
from .pds3file.rules import CORSS_8xxx as CORSS_8xxx
from .pds3file.rules import COSP_xxxx as COSP_xxxx
from .pds3file.rules import COUVIS_0xxx as COUVIS_0xxx
from .pds3file.rules import COUVIS_8xxx as COUVIS_8xxx
from .pds3file.rules import COVIMS_0xxx as COVIMS_0xxx
from .pds3file.rules import COVIMS_8xxx as COVIMS_8xxx
from .pds3file.rules import EBROCC_xxxx as EBROCC_xxxx
from .pds3file.rules import GO_0xxx as GO_0xxx
from .pds3file.rules import HSTxx_xxxx as HSTxx_xxxx
from .pds3file.rules import JNOJIR_xxxx as JNOJIR_xxxx
from .pds3file.rules import JNOJNC_xxxx as JNOJNC_xxxx
from .pds3file.rules import JNOSP_xxxx as JNOSP_xxxx
from .pds3file.rules import JNOSRU_xxxx as JNOSRU_xxxx
from .pds3file.rules import NHSP_xxxx as NHSP_xxxx
from .pds3file.rules import NHxxxx_xxxx as NHxxxx_xxxx
from .pds3file.rules import RES_xxxx as RES_xxxx
from .pds3file.rules import RPX_xxxx as RPX_xxxx
from .pds3file.rules import VG_0xxx as VG_0xxx
from .pds3file.rules import VG_20xx as VG_20xx
from .pds3file.rules import VG_28xx as VG_28xx
from .pds3file.rules import VGIRIS_xxxx as VGIRIS_xxxx
from .pds3file.rules import VGISS_xxxx as VGISS_xxxx
from .pds4file import Pds4File as Pds4File
from .pds4file import rules as rules
from .pds4file.rules import cassini_iss as cassini_iss
from .pds4file.rules import (
    cassini_iss_fring_mosaics_rsfrench2025 as cassini_iss_fring_mosaics_rsfrench2025,
)
from .pds4file.rules import (
    cassini_iss_spokes_hedman_hamilton_2024 as cassini_iss_spokes_hedman_hamilton_2024,
)
from .pds4file.rules import (
    cassini_uvis_solarocc_beckerjarmak2023 as cassini_uvis_solarocc_beckerjarmak2023,
)
from .pds4file.rules import cassini_vims as cassini_vims
from .pds4file.rules import uranus_occs_earthbased as uranus_occs_earthbased
from .pdsfile import PdsFile as PdsFile
from .preload_and_cache import cache_lifetime_for_class as cache_lifetime_for_class

__version__: str
