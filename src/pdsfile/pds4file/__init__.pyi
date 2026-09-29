"""Type stubs for ``pdsfile.pds4file`` (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the public surface frozen in ``tests/api/api_manifest.json``. Types are
derived from the implementation and its docstrings; where the truth is broader
than a single concrete type, the broader type is declared. ``CACHE`` is a union
because ``preload(port=...)`` rebinds it to a ``MemcachedCache``.
"""

# The manifest freezes the imported-module names below as public attributes of
# this package, so the stubs re-export them. rms-pdslogger and rms-translator
# ship no py.typed marker, hence the suppressions and the ``Any`` aliases.
import re as re
from typing import Any

import pdslogger as pdslogger  # type: ignore[import-untyped]

from pdsfile import pdscache as pdscache
from pdsfile.pdscache import DictionaryCache, MemcachedCache
from pdsfile.pdsfile import PdsFile as PdsFile
from pdsfile.preload_and_cache import (
    cache_lifetime_for_class as cache_lifetime_for_class,
)

from . import rules as rules
from .rules import cassini_iss as cassini_iss
from .rules import (
    cassini_iss_fring_mosaics_rsfrench2025 as cassini_iss_fring_mosaics_rsfrench2025,
)
from .rules import (
    cassini_iss_spokes_hedman_hamilton_2024 as cassini_iss_spokes_hedman_hamilton_2024,
)
from .rules import (
    cassini_uvis_solarocc_beckerjarmak2023 as cassini_uvis_solarocc_beckerjarmak2023,
)
from .rules import cassini_vims as cassini_vims
from .rules import uranus_occs_earthbased as uranus_occs_earthbased

# rms-pdslogger and rms-translator ship no py.typed marker, so their
# classes cannot be named here.
_PdsLogger = Any
_Translator = Any

class Pds4File(PdsFile):

    ARCHIVE_DIRS: _Translator
    ARCHIVE_PATHS: _Translator
    ASSOCIATIONS: dict[str, _Translator]
    BUNDLENAME_PLUS_REGEX: re.Pattern[str]
    BUNDLENAME_PLUS_REGEX_I: re.Pattern[str]
    BUNDLENAME_REGEX: re.Pattern[str]
    BUNDLENAME_VERSION: re.Pattern[str]
    BUNDLENAME_VERSION_I: re.Pattern[str]
    BUNDLESET_PLUS_REGEX: re.Pattern[str]
    BUNDLESET_PLUS_REGEX_I: re.Pattern[str]
    BUNDLESET_REGEX: re.Pattern[str]
    BUNDLE_DIR_NAME: str
    CACHE: DictionaryCache | MemcachedCache
    CROSS_PDS3_PDS4_PRODUCTS: _Translator
    DATA_SET_ID: _Translator
    DESCRIPTION_AND_ICON: _Translator
    DICTIONARY_CACHE_LIMIT: int
    FILESPEC_TO_BUNDLESET: _Translator
    IDX_EXT: tuple[str, ...]
    INFO_FILE_BASENAMES: _Translator
    LBL_EXT: tuple[str, ...]
    LID_AFTER_DSID: _Translator
    LOCAL_PRELOADED: list[str]
    LOGGER: _PdsLogger
    NEIGHBORS: _Translator
    OPUS_FORMAT: _Translator
    OPUS_ID: _Translator
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH: _Translator
    OPUS_ID_TO_SUBCLASS: _Translator
    OPUS_PRODUCTS: _Translator
    OPUS_TYPE: _Translator
    PDS_HOLDINGS: str
    PRODUCT_LBL_BASENAME_WO_EXT: _Translator
    SIBLINGS: _Translator
    SORT_KEY: _Translator
    SPLIT_RULES: _Translator
    VERSIONS: _Translator
    VIEWABLES: dict[str, _Translator]
    VIEW_OPTIONS: _Translator
    VOLSET_TRANSLATOR: _Translator
    def archive_dirs(self) -> dict[str, list[str]]: ...
    def archive_paths(self) -> list[str]: ...
    @classmethod
    def require_shelves(cls, status: bool = True) -> None: ...
    @classmethod
    def set_easylogger(cls) -> None: ...
    @classmethod
    def set_logger(cls, logger: _PdsLogger | None = None) -> None: ...
    @classmethod
    def use_shelves_only(cls, status: bool = True) -> None: ...
