"""Type stubs for ``pdsfile.pds3file`` (see the module docstring there).

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
from .rules import ASTROM_xxxx as ASTROM_xxxx
from .rules import COCIRS_xxxx as COCIRS_xxxx
from .rules import COISS_xxxx as COISS_xxxx
from .rules import CORSS_8xxx as CORSS_8xxx
from .rules import COSP_xxxx as COSP_xxxx
from .rules import COUVIS_0xxx as COUVIS_0xxx
from .rules import COUVIS_8xxx as COUVIS_8xxx
from .rules import COVIMS_0xxx as COVIMS_0xxx
from .rules import COVIMS_8xxx as COVIMS_8xxx
from .rules import EBROCC_xxxx as EBROCC_xxxx
from .rules import GO_0xxx as GO_0xxx
from .rules import HSTxx_xxxx as HSTxx_xxxx
from .rules import JNOJIR_xxxx as JNOJIR_xxxx
from .rules import JNOJNC_xxxx as JNOJNC_xxxx
from .rules import JNOSP_xxxx as JNOSP_xxxx
from .rules import JNOSRU_xxxx as JNOSRU_xxxx
from .rules import NHSP_xxxx as NHSP_xxxx
from .rules import NHxxxx_xxxx as NHxxxx_xxxx
from .rules import RES_xxxx as RES_xxxx
from .rules import RPX_xxxx as RPX_xxxx
from .rules import VG_0xxx as VG_0xxx
from .rules import VG_20xx as VG_20xx
from .rules import VG_28xx as VG_28xx
from .rules import VGIRIS_xxxx as VGIRIS_xxxx
from .rules import VGISS_xxxx as VGISS_xxxx

# rms-pdslogger and rms-translator ship no py.typed marker, so their
# classes cannot be named here.
_PdsLogger = Any
_Translator = Any

class Pds3File(PdsFile):
    ASSOCIATIONS: dict[str, _Translator]
    BUNDLENAME_PLUS_REGEX: re.Pattern[str]
    BUNDLENAME_PLUS_REGEX_I: re.Pattern[str]
    BUNDLENAME_REGEX: re.Pattern[str]
    BUNDLENAME_REGEX_I: re.Pattern[str]
    BUNDLENAME_VERSION: re.Pattern[str]
    BUNDLENAME_VERSION_I: re.Pattern[str]
    BUNDLESET_PLUS_REGEX: re.Pattern[str]
    BUNDLESET_PLUS_REGEX_I: re.Pattern[str]
    BUNDLESET_REGEX: re.Pattern[str]
    BUNDLESET_REGEX_I: re.Pattern[str]
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
    SIBLINGS: _Translator
    SORT_KEY: _Translator
    SPLIT_RULES: _Translator
    VERSIONS: _Translator
    VIEWABLES: dict[str, _Translator]
    VIEW_OPTIONS: _Translator
    VOLNAME_PLUS_REGEX: re.Pattern[str]
    VOLNAME_PLUS_REGEX_I: re.Pattern[str]
    VOLNAME_REGEX: re.Pattern[str]
    VOLNAME_REGEX_I: re.Pattern[str]
    VOLNAME_VERSION: re.Pattern[str]
    VOLNAME_VERSION_I: re.Pattern[str]
    VOLSET_PLUS_REGEX: re.Pattern[str]
    VOLSET_PLUS_REGEX_I: re.Pattern[str]
    VOLSET_REGEX: re.Pattern[str]
    VOLSET_REGEX_I: re.Pattern[str]
    VOLSET_TRANSLATOR: _Translator
    @property
    def is_volset(self) -> bool: ...
    @property
    def is_volset_dir(self) -> bool: ...
    @property
    def is_volset_file(self) -> bool: ...
    @property
    def is_volume(self) -> bool: ...
    @property
    def is_volume_dir(self) -> bool: ...
    @property
    def is_volume_file(self) -> bool: ...
    def log_path_for_volset(self, suffix: str = '', task: str = '', dir: str = '',
                            place: str = 'default') -> str: ...
    def log_path_for_volume(self, suffix: str = '', task: str = '', dir: str = '',
                            place: str = 'default') -> str: ...
    @classmethod
    def require_shelves(cls, status: bool = True) -> None: ...
    @classmethod
    def set_easylogger(cls) -> None: ...
    @classmethod
    def set_logger(cls, logger: _PdsLogger | None = None) -> None: ...
    @classmethod
    def use_shelves_only(cls, status: bool = True) -> None: ...
    @property
    def volname(self) -> str: ...
    @property
    def volname_(self) -> str: ...
    @property
    def volset(self) -> str: ...
    @property
    def volset_(self) -> str: ...
    def volset_abspath(self, category: str | None = None) -> str | None: ...
    def volset_pdsfile(self, category: str | None = None,
                       rank: int | None = None) -> PdsFile | None: ...
    @property
    def voltype_(self) -> str: ...
    def volume_abspath(self, category: str | None = None) -> str: ...
    def volume_pdsfile(self, category: str | None = None,
                       rank: int | None = None) -> PdsFile | None: ...
    @property
    def volume_publication_date(self) -> str: ...
    @property
    def volume_version_id(self) -> str: ...
